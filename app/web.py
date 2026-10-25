import asyncio, hashlib, hmac, io, json, logging, os, time
from datetime import timedelta
from urllib.parse import parse_qsl
from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.database.engine import engine, SessionFactory
from app.database.models import Base, User, Book, BookPage, ReadingSession, Quiz, QuizQuestion, QuizAttempt, Gift, GiftOrder, Referral, CoinTransaction, AdminAuditLog
from app.services.reading_service import start_reading, remaining_seconds, source_for_session
from app.services.quiz_service import create_quiz, submit_answers
from app.services.ai_service import AIError
from app.services.gift_service import create_order, update_order_status
from app.services.coin_service import change_coins
from app.services.notification_service import broadcast
from app.bot import create_bot
from app.database.models import utcnow

logger = logging.getLogger(__name__)
_bg_tasks: set = set()

settings = get_settings()
app = FastAPI(title='Kitobxon WebApp', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
app.mount('/static', StaticFiles(directory='app/static'), name='static')

async def _run_bot_forever():
    """Telegram botni WebApp bilan bir jarayonda ishga tushiradi (RUN_BOT=true bo‘lganda)."""
    from aiogram import Dispatcher
    from app.handlers import start, registration
    from app.middlewares.database import DatabaseMiddleware
    while True:
        bot = create_bot()
        try:
            dp = Dispatcher()
            dp.update.middleware(DatabaseMiddleware())
            for router in (start.router, registration.router): dp.include_router(router)
            logger.info('Telegram bot (polling) ishga tushdi')
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), handle_signals=False)
            return
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception('Bot to‘xtadi, 10 soniyadan keyin qayta ishga tushadi')
            await asyncio.sleep(10)
        finally:
            await bot.session.close()

async def _keep_alive():
    """Render bepul tarifi 15 daqiqa trafik bo‘lmasa uxlatadi. O‘z ommaviy manzilimizga so‘rov yuborib turamiz."""
    url = (os.getenv('RENDER_EXTERNAL_URL') or os.getenv('KEEPALIVE_URL') or '').rstrip('/')
    if not url: return
    import aiohttp
    await asyncio.sleep(60)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as http:
        while True:
            try:
                async with http.get(url + '/health') as r: logger.info('keep-alive: %s', r.status)
            except Exception as e: logger.warning('keep-alive xatosi: %s', e)
            await asyncio.sleep(8 * 60)

@app.on_event('startup')
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    if settings.database_url.startswith('sqlite') and (settings.run_bot or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER')):
        logger.warning('DIQQAT: bulutda SQLite ishlatilmoqda, serverni qayta ishga tushirganda ma’lumotlar o‘chib ketadi. DATABASE_URL ga PostgreSQL manzilini qo‘ying.')
    if settings.run_bot:
        t = asyncio.create_task(_run_bot_forever()); _bg_tasks.add(t); t.add_done_callback(_bg_tasks.discard)
    t = asyncio.create_task(_keep_alive()); _bg_tasks.add(t); t.add_done_callback(_bg_tasks.discard)

@app.api_route('/health', methods=['GET', 'HEAD'])
async def health():
    return {'ok': True}

async def db():
    async with SessionFactory() as session:
        yield session

def telegram_user(init_data: str):
    if not init_data:
        raise HTTPException(401, 'Telegram WebApp orqali kiring.')
    vals = dict(parse_qsl(init_data, keep_blank_values=True))
    received = vals.pop('hash', None)
    if not received:
        raise HTTPException(401, 'Telegram ma’lumotlari tasdiqlanmadi.')
    secret = hmac.new(b'WebAppData', settings.bot_token.encode(), hashlib.sha256).digest()
    check = '\n'.join(f'{k}={v}' for k, v in sorted(vals.items()))
    expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise HTTPException(401, 'Telegram imzosi noto‘g‘ri.')
    if vals.get('auth_date') and time.time() - int(vals['auth_date']) > 86400:
        raise HTTPException(401, 'Telegram sessiyasi eskirgan. WebAppni qayta oching.')
    try: return json.loads(vals['user'])
    except Exception: raise HTTPException(401, 'Telegram foydalanuvchisi topilmadi.')

async def current_user(request: Request, session: AsyncSession = Depends(db)):
    init_data = request.headers.get('X-Telegram-Init-Data', '')
    tg = telegram_user(init_data)
    telegram_id = int(tg['id'])
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user and telegram_id in settings.admin_ids:
        # Admin can open the WebApp without completing ordinary-user registration.
        # Synthetic contact/address fields are used only to satisfy the existing User schema.
        first_name = str(tg.get('first_name') or 'Administrator')[:80]
        last_name = str(tg.get('last_name') or 'Admin')[:80]
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            phone=f'admin-{telegram_id}',
            region='Administrator',
            district='Administrator',
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    if not user:
        request.state.telegram_user = tg
        return None
    if user.is_banned: raise HTTPException(403, 'Hisobingiz bloklangan.')
    request.state.telegram_user = tg
    return user

def admin_check(request: Request, user: User):
    if not user or user.telegram_id not in settings.admin_ids:
        raise HTTPException(403, 'Faqat administrator uchun.')

@app.get('/', response_class=HTMLResponse)
async def home():
    with open('app/static/index.html', encoding='utf-8') as f: return f.read()

@app.get('/api/me')
async def me(request: Request, user=Depends(current_user), session: AsyncSession=Depends(db)):
    tg=request.state.telegram_user
    if not user: return {'registered':False,'telegram':{'id':tg['id'],'first_name':tg.get('first_name',''),'last_name':tg.get('last_name','')}}
    return {'registered':True,'user':{'id':user.id,'first_name':user.first_name,'last_name':user.last_name,'coins':user.coins,'total_pages':user.total_pages,'region':user.region,'district':user.district},'is_admin':user.telegram_id in settings.admin_ids}

@app.post('/api/register')
async def register(payload: dict, request: Request, session: AsyncSession=Depends(db)):
    tg=telegram_user(request.headers.get('X-Telegram-Init-Data',''))
    tid=int(tg['id'])
    existing=await session.scalar(select(User).where(User.telegram_id==tid))
    if existing: return {'ok':True}
    phone=str(payload.get('phone','')).strip()
    if len(phone)<7: raise HTTPException(400,'Telefon raqamini to‘g‘ri kiriting.')
    if await session.scalar(select(User).where(User.phone==phone)): raise HTTPException(409,'Bu telefon raqami avval ro‘yxatdan o‘tgan.')
    inviter=None
    try: inviter=int(payload.get('referral_id') or 0)
    except: inviter=0
    referrer=await session.scalar(select(User).where(User.telegram_id==inviter)) if inviter else None
    u=User(telegram_id=tid,first_name=str(tg.get('first_name','Foydalanuvchi'))[:80],last_name=str(tg.get('last_name',''))[:80],phone=phone,region=str(payload.get('region',''))[:100],district=str(payload.get('district',''))[:100],referred_by_id=referrer.id if referrer else None)
    session.add(u); await session.flush()
    if referrer:
        r=Referral(inviter_id=referrer.id,invitee_id=u.id,registration_rewarded=True); session.add(r)
        if settings.referral_reward_on and settings.referral_reward_at=='registration':
            await change_coins(session,referrer.id,settings.coins_per_referral_registration,'referral_registration_reward','Do‘st ro‘yxatdan o‘tdi',f'referral-register:{u.id}','referral',u.id)
    await session.commit(); return {'ok':True}

@app.get('/api/books')
async def books(search: str='', user=Depends(current_user), session: AsyncSession=Depends(db)):
    if not user: raise HTTPException(428,'Avval ro‘yxatdan o‘ting.')
    rows=(await session.scalars(select(Book).where(Book.is_active.is_(True),Book.title.ilike(f'%{search}%')).order_by(Book.title).limit(100))).all()
    return [{'id':b.id,'title':b.title,'author':b.author,'description':b.description,'total_pages':b.total_pages} for b in rows]

@app.get('/api/books/{book_id}/pages/{page}')
async def page(book_id:int,page:int,user=Depends(current_user),session:AsyncSession=Depends(db)):
    if not user: raise HTTPException(428,'Avval ro‘yxatdan o‘ting.')
    b=await session.get(Book,book_id)
    if not b or not b.is_active or page<1 or page>b.total_pages: raise HTTPException(404,'Sahifa topilmadi.')
    p=await session.scalar(select(BookPage).where(BookPage.book_id==book_id,BookPage.page_number==page))
    return {'book_id':book_id,'page':page,'total_pages':b.total_pages,'content':p.content if p else 'Bu sahifa matni hali administrator tomonidan kiritilmagan.'}

@app.post('/api/reading/start')
async def reading_start(payload:dict,user=Depends(current_user),session:AsyncSession=Depends(db)):
    if not user: raise HTTPException(428,'Avval ro‘yxatdan o‘ting.')
    try: r=await start_reading(session,user.id,int(payload['book_id']),int(payload.get('page_count',1)),settings.min_seconds_per_page); await session.commit(); return {'id':r.id,'minimum_seconds':r.minimum_seconds,'started_at':r.started_at.isoformat()}
    except ValueError as e: await session.rollback(); raise HTTPException(400,str(e))

@app.get('/api/reading/active')
async def active_reading(user=Depends(current_user),session:AsyncSession=Depends(db)):
    if not user: raise HTTPException(428,'Avval ro‘yxatdan o‘ting.')
    r=await session.scalar(select(ReadingSession).where(ReadingSession.user_id==user.id,ReadingSession.status=='active'))
    if not r:return {'active':False}
    b=await session.get(Book,r.book_id)
    return {'active':True,'id':r.id,'book_id':r.book_id,'book_title':b.title if b else '', 'page_count':r.page_count,'remaining_seconds':await remaining_seconds(r)}

@app.post('/api/reading/{reading_id}/quiz')
async def reading_quiz(reading_id:int,user=Depends(current_user),session:AsyncSession=Depends(db)):
    if not user: raise HTTPException(428,'Avval ro‘yxatdan o‘ting.')
    try:
        q,questions=await create_quiz(session,reading_id,user.id); await session.commit()
        return {'quiz_id':q.id,'questions':[{'id':x.id,'question':x.question,'options':json.loads(x.options_json)} for x in questions]}
    except ValueError as e: await session.rollback(); raise HTTPException(400,str(e))
    except AIError as e:
        await session.rollback(); logger.error('AI xatosi (reading_id=%s): %s | sabab: %r',reading_id,e,e.__cause__)
        raise HTTPException(502,str(e))
    except Exception as e:
        await session.rollback(); logger.exception('Quiz yaratishda xatolik (reading_id=%s)',reading_id)
        raise HTTPException(502,'AI test yarata olmadi. Birozdan keyin qayta urinib ko‘ring.')

@app.post('/api/quizzes/{quiz_id}/submit')
async def quiz_submit(quiz_id:int,payload:dict,user=Depends(current_user),session:AsyncSession=Depends(db)):
    if not user: raise HTTPException(428,'Avval ro‘yxatdan o‘ting.')
    try:
        selected={int(k):int(v) for k,v in payload.get('answers',{}).items()}; correct,passed,coins=await submit_answers(session,quiz_id,user.id,selected); await session.commit(); return {'correct':correct,'passed':passed,'coins_awarded':coins,'needed':settings.quiz_pass_score}
    except Exception as e: await session.rollback(); raise HTTPException(400,str(e))

@app.get('/api/gifts')
async def gifts(user=Depends(current_user),session:AsyncSession=Depends(db)):
    if not user: raise HTTPException(428,'Avval ro‘yxatdan o‘ting.')
    rows=(await session.scalars(select(Gift).where(Gift.is_active.is_(True)).order_by(Gift.price))).all()
    return [{'id':g.id,'name':g.name,'description':g.description,'price':g.price,'stock':g.stock} for g in rows]

@app.post('/api/gifts/{gift_id}/order')
async def order_gift(gift_id:int,user=Depends(current_user),session:AsyncSession=Depends(db)):
    if not user: raise HTTPException(428,'Avval ro‘yxatdan o‘ting.')
    try: o=await create_order(session,user.id,gift_id); await session.commit(); return {'ok':True,'order_id':o.id,'status':o.status}
    except Exception as e: await session.rollback(); raise HTTPException(400,str(e))

@app.get('/api/leaderboard')
async def leaderboard(user=Depends(current_user),session:AsyncSession=Depends(db)):
    if not user: raise HTTPException(428,'Avval ro‘yxatdan o‘ting.')
    rows=(await session.scalars(select(User).where(User.is_banned.is_(False)).order_by(User.coins.desc(),User.total_pages.desc()).limit(50))).all()
    return [{'rank':i+1,'name':u.first_name,'coins':u.coins,'pages':u.total_pages,'me':u.id==user.id} for i,u in enumerate(rows)]

@app.get('/api/referrals')
async def referrals(request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    if not user: raise HTTPException(428,'Avval ro‘yxatdan o‘ting.')
    count=await session.scalar(select(func.count(Referral.id)).where(Referral.inviter_id==user.id))
    return {'count':count or 0,'telegram_id':user.telegram_id,'bot_username':settings.bot_username,'coins_per_registration':settings.coins_per_referral_registration,'coins_per_quiz':settings.coins_per_referral_first_passed_quiz}

@app.get('/api/transactions')
async def transactions(user=Depends(current_user),session:AsyncSession=Depends(db)):
    if not user: raise HTTPException(428,'Avval ro‘yxatdan o‘ting.')
    rows=(await session.scalars(select(CoinTransaction).where(CoinTransaction.user_id==user.id).order_by(CoinTransaction.created_at.desc()).limit(50))).all()
    return [{'amount':x.amount,'reason':x.reason,'created_at':x.created_at.isoformat()} for x in rows]

@app.get('/api/admin/overview')
async def admin_overview(request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user)
    return {'users':await session.scalar(select(func.count(User.id))),'books':await session.scalar(select(func.count(Book.id))),'gifts':await session.scalar(select(func.count(Gift.id))),'orders':await session.scalar(select(func.count(GiftOrder.id)).where(GiftOrder.status=='pending'))}

@app.get('/api/admin/gifts')
async def admin_gifts(request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user); rows=(await session.scalars(select(Gift).order_by(Gift.id.desc()))).all()
    return [{'id':g.id,'name':g.name,'description':g.description,'price':g.price,'stock':g.stock,'is_active':g.is_active} for g in rows]

@app.post('/api/admin/gifts')
async def admin_add_gift(payload:dict,request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user)
    try: price=int(payload['price']); stock=int(payload.get('stock',0))
    except: raise HTTPException(400,'Narx va son raqam bo‘lishi kerak.')
    if price<0 or stock<0: raise HTTPException(400,'Narx va son manfiy bo‘lmasin.')
    g=Gift(name=str(payload.get('name','')).strip(),description=str(payload.get('description','')).strip(),price=price,stock=stock,is_active=True)
    if not g.name: raise HTTPException(400,'Sovg‘a nomi kerak.')
    session.add(g); await session.commit(); return {'ok':True,'id':g.id}

@app.patch('/api/admin/gifts/{gift_id}')
async def admin_edit_gift(gift_id:int,payload:dict,request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user); g=await session.get(Gift,gift_id)
    if not g: raise HTTPException(404,'Sovg‘a topilmadi.')
    for key in ('name','description','price','stock','is_active'):
        if key in payload: setattr(g,key,payload[key])
    await session.commit(); return {'ok':True}

@app.delete('/api/admin/gifts/{gift_id}')
async def admin_delete_gift(gift_id:int,request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user); g=await session.get(Gift,gift_id)
    if not g: raise HTTPException(404,'Sovg‘a topilmadi.')
    orders=await session.scalar(select(func.count(GiftOrder.id)).where(GiftOrder.gift_id==gift_id))
    if orders: g.is_active=False; await session.commit(); return {'ok':True,'hidden':True,'message':'Buyurtma tarixi borligi sababli sovg‘a yashirildi.'}
    await session.delete(g); await session.commit(); return {'ok':True,'deleted':True}

@app.get('/api/admin/orders')
async def admin_orders(request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user); rows=(await session.scalars(select(GiftOrder).order_by(GiftOrder.created_at.desc()).limit(100))).all(); out=[]
    for o in rows:
        u=await session.get(User,o.user_id); g=await session.get(Gift,o.gift_id)
        out.append({'id':o.id,'created_at':o.created_at.isoformat(),'phone':u.phone if u and not u.phone.startswith('admin-') else '','user':u.first_name if u else '—','gift':g.name if g else 'O‘chirilgan sovg‘a','price':o.price_each,'status':o.status})
    return out

@app.post('/api/admin/orders/{order_id}/{status}')
async def admin_order_status(order_id:int,status:str,request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user)
    try: await update_order_status(session,order_id,status); await session.commit(); return {'ok':True}
    except Exception as e: await session.rollback(); raise HTTPException(400,str(e))

@app.get('/api/admin/books')
async def admin_books(request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user); rows=(await session.scalars(select(Book).order_by(Book.id.desc()))).all()
    return [{'id':b.id,'title':b.title,'author':b.author,'description':b.description,'total_pages':b.total_pages,'is_active':b.is_active} for b in rows]

@app.post('/api/admin/books')
async def admin_add_book(payload:dict,request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user)
    try: pages=int(payload['total_pages'])
    except: raise HTTPException(400,'Sahifalar sonini kiriting.')
    b=Book(title=str(payload.get('title','')).strip(),author=str(payload.get('author','')).strip(),description=str(payload.get('description','')).strip(),total_pages=pages,is_active=True)
    if not b.title or pages<1: raise HTTPException(400,'Kitob nomi va sahifalar soni kerak.')
    session.add(b); await session.commit(); return {'ok':True,'id':b.id}

@app.patch('/api/admin/books/{book_id}')
async def admin_edit_book(book_id:int,payload:dict,request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user); b=await session.get(Book,book_id)
    if not b: raise HTTPException(404,'Kitob topilmadi.')
    for key in ('title','author','description','is_active'):
        if key in payload:setattr(b,key,payload[key])
    await session.commit(); return {'ok':True}

@app.delete('/api/admin/books/{book_id}')
async def admin_delete_book(book_id:int,request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user); b=await session.get(Book,book_id)
    if not b: raise HTTPException(404,'Kitob topilmadi.')
    b.is_active=False; await session.commit(); return {'ok':True}

@app.put('/api/admin/books/{book_id}/pages/{page_number}')
async def admin_page(book_id:int,page_number:int,payload:dict,request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user); b=await session.get(Book,book_id)
    if not b or not 1<=page_number<=b.total_pages: raise HTTPException(404,'Kitob yoki sahifa topilmadi.')
    p=await session.scalar(select(BookPage).where(BookPage.book_id==book_id,BookPage.page_number==page_number))
    if p:p.content=str(payload.get('content',''))
    else:session.add(BookPage(book_id=book_id,page_number=page_number,content=str(payload.get('content',''))))
    await session.commit(); return {'ok':True}

@app.post('/api/admin/books/upload-pdf')
async def upload_pdf(request:Request, file:UploadFile=File(...), title:str=Form(...), author:str=Form(''), description:str=Form(''), user=Depends(current_user), session:AsyncSession=Depends(db)):
    admin_check(request,user)
    if not file.filename or not file.filename.lower().endswith('.pdf'): raise HTTPException(400,'Faqat PDF fayl yuklang.')
    raw=await file.read()
    if len(raw)>20*1024*1024: raise HTTPException(413,'PDF hajmi 20 MB dan oshmasin.')
    try:
        from pypdf import PdfReader
        import io
        reader=PdfReader(io.BytesIO(raw)); texts=[(p.extract_text() or '').strip() for p in reader.pages]
    except Exception as e: raise HTTPException(400,'PDF faylni o‘qib bo‘lmadi.')
    if not texts: raise HTTPException(400,'PDF ichida sahifalar topilmadi.')
    b=Book(title=title.strip(),author=author.strip(),description=description.strip(),total_pages=len(texts),is_active=True); session.add(b); await session.flush()
    for i,content in enumerate(texts,1): session.add(BookPage(book_id=b.id,page_number=i,content=content or f'{i}-sahifada matn ajratib olinmadi.'))
    await session.commit(); return {'ok':True,'id':b.id,'pages':len(texts)}


# ---------------------------------------------------------------- admin panel
def _audit(session, user, action, target_type, target_id, details=''):
    session.add(AdminAuditLog(admin_telegram_id=user.telegram_id, action=action, target_type=target_type, target_id=str(target_id), details=details[:1000]))

def _user_row(u: User):
    return {'id':u.id,'telegram_id':u.telegram_id,'name':f'{u.first_name} {u.last_name}'.strip(),'first_name':u.first_name,'phone':'' if u.phone.startswith('admin-') else u.phone,'region':u.region,'district':u.district,'coins':u.coins,'pages':u.total_pages,'is_banned':u.is_banned,'is_admin':u.telegram_id in settings.admin_ids,'created_at':u.created_at.isoformat()}

@app.get('/api/admin/stats')
async def admin_stats(request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user)
    now=utcnow(); today=now.replace(hour=0,minute=0,second=0,microsecond=0)
    cnt=lambda q: session.scalar(q)
    created=(await session.scalars(select(User.created_at).where(User.created_at>=today-timedelta(days=6)))).all()
    days=[]
    for i in range(6,-1,-1):
        d=today-timedelta(days=i)
        days.append({'date':d.date().isoformat(),'count':sum(1 for c in created if d<=c<d+timedelta(days=1))})
    return {
        'users':await cnt(select(func.count(User.id))) or 0,
        'banned':await cnt(select(func.count(User.id)).where(User.is_banned.is_(True))) or 0,
        'new_today':await cnt(select(func.count(User.id)).where(User.created_at>=today)) or 0,
        'active_week':await cnt(select(func.count(User.id)).where(User.last_activity_at>=now-timedelta(days=7))) or 0,
        'books':await cnt(select(func.count(Book.id))) or 0,
        'active_books':await cnt(select(func.count(Book.id)).where(Book.is_active.is_(True))) or 0,
        'gifts':await cnt(select(func.count(Gift.id))) or 0,
        'pending_orders':await cnt(select(func.count(GiftOrder.id)).where(GiftOrder.status=='pending')) or 0,
        'approved_orders':await cnt(select(func.count(GiftOrder.id)).where(GiftOrder.status=='approved')) or 0,
        'coins_total':await cnt(select(func.coalesce(func.sum(User.coins),0))) or 0,
        'pages_total':await cnt(select(func.coalesce(func.sum(User.total_pages),0))) or 0,
        'quizzes':await cnt(select(func.count(QuizAttempt.id))) or 0,
        'quizzes_passed':await cnt(select(func.count(QuizAttempt.id)).where(QuizAttempt.passed.is_(True))) or 0,
        'registrations':days,
    }

@app.get('/api/admin/users')
async def admin_users(request:Request,search:str='',banned:bool|None=None,limit:int=30,offset:int=0,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user)
    limit=max(1,min(limit,100)); offset=max(0,offset)
    q=select(User)
    s=search.strip()
    if s:
        like=f'%{s}%'
        cond=(User.first_name.ilike(like))|(User.last_name.ilike(like))|(User.phone.ilike(like))
        if s.isdigit(): cond=cond|(User.telegram_id==int(s))
        q=q.where(cond)
    if banned is not None: q=q.where(User.is_banned.is_(banned))
    total=await session.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows=(await session.scalars(q.order_by(User.created_at.desc()).limit(limit).offset(offset))).all()
    return {'total':total,'items':[_user_row(u) for u in rows]}

@app.post('/api/admin/users/{user_id}/ban')
async def admin_ban(user_id:int,payload:dict,request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user); t=await session.get(User,user_id)
    if not t: raise HTTPException(404,'Foydalanuvchi topilmadi.')
    banned=bool(payload.get('banned',True))
    if banned and t.telegram_id in settings.admin_ids: raise HTTPException(400,'Administratorni bloklab bo‘lmaydi.')
    t.is_banned=banned; _audit(session,user,'ban' if banned else 'unban','user',t.id)
    await session.commit(); return {'ok':True,'is_banned':banned}

@app.post('/api/admin/users/{user_id}/coins')
async def admin_user_coins(user_id:int,payload:dict,request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user)
    try: amount=int(payload['amount'])
    except Exception: raise HTTPException(400,'Tanga miqdori butun son bo‘lishi kerak.')
    if amount==0: raise HTTPException(400,'Miqdor 0 bo‘lmasin.')
    if abs(amount)>1_000_000: raise HTTPException(400,'Miqdor juda katta.')
    reason=str(payload.get('reason','')).strip()[:250] or 'Administrator tuzatishi'
    try:
        t=await session.get(User,user_id)
        if not t: raise ValueError('Foydalanuvchi topilmadi.')
        await change_coins(session,t.id,amount,'admin_adjustment',reason,f'admin-web:{user.telegram_id}:{t.id}:{time.time_ns()}')
        _audit(session,user,'coins','user',t.id,f'{amount}; {reason}')
        await session.commit(); await session.refresh(t); return {'ok':True,'coins':t.coins}
    except Exception as e: await session.rollback(); raise HTTPException(400,str(e))

async def _run_broadcast(ids, text, admin_tid):
    bot=create_bot()
    try:
        sent,failed=await broadcast(bot,ids,text)
        try: await bot.send_message(admin_tid,f'📣 Xabar yuborildi: {sent} ta yetkazildi, {failed} ta xato.')
        except Exception: pass
    except Exception: logger.exception('Broadcast failed')
    finally: await bot.session.close()

@app.post('/api/admin/broadcast')
async def admin_broadcast(payload:dict,request:Request,user=Depends(current_user),session:AsyncSession=Depends(db)):
    admin_check(request,user)
    text=str(payload.get('text','')).strip()
    if not text: raise HTTPException(400,'Xabar matnini kiriting.')
    if len(text)>4000: raise HTTPException(400,'Xabar 4000 belgidan oshmasin.')
    ids=list((await session.scalars(select(User.telegram_id).where(User.is_banned.is_(False)))).all())
    _audit(session,user,'broadcast','users','all',f'recipients={len(ids)}'); await session.commit()
    task=asyncio.create_task(_run_broadcast(ids,text,user.telegram_id)); _bg_tasks.add(task); task.add_done_callback(_bg_tasks.discard)
    return {'ok':True,'recipients':len(ids)}
