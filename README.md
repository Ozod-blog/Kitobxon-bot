# Kitobxon Bot

Async Telegram bot project with registration, book pages, reading timers, AI quiz generation, coin ledger, referrals, leaderboard, gift reservations and a button-based admin panel. Python 3.12 recommended.

## Windows (PowerShell)

1. Install Python 3.12 from the official Python website and enable PATH.
2. Open this folder in PowerShell.
3. Create environment: `py -3.12 -m venv .venv`
4. Activate: `.\.venv\Scripts\Activate.ps1`
5. Install: `python -m pip install --upgrade pip` then `pip install -r requirements.txt`
6. Copy configuration: `Copy-Item .env.example .env`
7. Edit `.env`: set `BOT_TOKEN`, `BOT_USERNAME`, `ADMIN_IDS` (comma-separated Telegram numeric IDs), and the selected AI API key.
8. Run database migration: `alembic upgrade head`
9. Start: `python -m app.main`
10. Tests: `pytest -q`

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process Bypass` in that terminal, then activate again.

## Linux

1. Install Python 3.12 and venv support using your distribution package manager.
2. `python3.12 -m venv .venv`
3. `source .venv/bin/activate`
4. `python -m pip install --upgrade pip`
5. `pip install -r requirements.txt`
6. `cp .env.example .env` and edit it with your bot token, admin IDs and AI key.
7. `alembic upgrade head`
8. `python -m app.main`
9. `pytest -q`

## Environment

`AI_PROVIDER=gemini` or `openai`; provide the matching API key. AI generation intentionally refuses to invent questions when selected page text is absent. Default quiz rewards are 10 coins, reading time 30 seconds/page, quiz size 5, pass score 4. Configure via `.env`.

## WebApp interface and administrator access

All main menus are inside the WebApp. In Telegram, users send `/start`; new users complete registration in the bot (first name, last name, own Telegram contact, region, district), then receive the `📚 Kitobxon WebApp` button. Existing users and admins receive the same button immediately. Set `WEBAPP_URL` to the current public HTTPS/ngrok address in `.env`; update it whenever ngrok changes the URL.

The WebApp uses a large fixed bottom navigation bar. The admin panel appears inside the Profile section only for Telegram IDs listed in `ADMIN_IDS`. Run the bot and WebApp as separate processes, both from the project root and using the same `.env` and `DATABASE_URL`.

## Important limitations

This deliverable is a starter implementation and has **not** been fully verified as production-ready. In particular:
- The quiz flow is implemented as sequential inline questions and submits results once; it still needs runtime integration tests with the selected AI SDK versions.
- Admin paneli tugmalar orqali ishlaydi, lekin kitob/sovg‘ani tahrirlash yoki o‘chirish, foydalanuvchini qidirish, referral sozlamalarini UI orqali o‘zgartirish, rasmli broadcast va to‘liq faoliyat tarixini ko‘rish hali qo‘shilmagan.
- Current schema bootstrap uses `create_all` at bot startup as a convenience; Alembic migration is included but should be the production source of schema changes.
- SQLite `with_for_update()` does not provide row-level locks. For multi-process or high concurrency, PostgreSQL and atomic conditional updates are recommended.
- Referral reward timing supports registration and first passed quiz through code/config, but the env name and behavior should be reviewed before production.
- Syntax tekshiruvi bajarilgan. Bu muhitda internet bo‘lmagani uchun bog‘liqliklarni o‘rnatib pytest/integratsion testlarni bajarish imkoni bo‘lmadi. Haqiqiy Telegram yoki AI API kalitlari loyihaga kiritilmagan.
- This project must receive a security and integration review before public production deployment.

Never commit `.env` or actual secrets.


## PDF kitob yuklash va o‘qish
1. `requirements.txt` ichidagi yangi `pypdf` kutubxonasini o‘rnating: `pip install -r requirements.txt`.
2. Administrator sifatida botda `/start` bosing, so‘ng `🛠 Admin paneli` → `➕ PDF kitob yuklash` ni tanlang.
3. Kitob nomi, muallif, tavsifni yuboring; keyin PDF faylni Telegram hujjati sifatida yuboring.
4. Bot PDF matnini ajratib, sahifalarini bazaga saqlaydi. Foydalanuvchilar `📚 Kitoblar` tugmasi orqali sahifalarni ko‘radi.

Eslatma: skaner qilingan, faqat rasmli PDF-lardan pypdf matn ajrata olmaydi; bunday fayllarga OCR funksiyasi alohida kerak. Fayl uchun 20 MB limit qo‘yilgan. PDF matni sahifalarga ajratiladi; asl PDF hujjati foydalanuvchiga alohida fayl sifatida yuborilmaydi.

## WebApp (brauzer va Telegram ichida)

Loyiha endi FastAPI asosidagi WebApp interfeysini ham o‘z ichiga oladi. Botning mavjud `app/main.py` fayli Telegram bot sifatida qoladi; WebApp alohida ishga tushadi.

1. `.env` faylida `BOT_TOKEN`, `BOT_USERNAME`, `ADMIN_IDS`, `DATABASE_URL` va AI kalitini sozlang.
2. Virtual muhitni faollashtiring va `pip install -r requirements.txt` bajaring.
3. Loyihaning ildiz papkasida ishga tushiring:
   ```bash
   uvicorn app.web:app --host 0.0.0.0 --port 8000
   ```
4. Sinash uchun lokal brauzerda `http://127.0.0.1:8000` ochish mumkin, ammo Telegram imzosi bilan autentifikatsiya sababli haqiqiy funksiyalarni Telegram WebApp ichida ochish kerak.
5. Internetdan HTTPS manzil (masalan, serverdagi domen) tayyorlab, BotFather orqali botning Web App menyusiga shu manzilni ulang.

WebAppda bosh sahifa, kitoblar, sahifalarni o‘qish, vaqt bilan o‘qish sessiyasi, AI viktorina, tanga balansi va tarixi, sovg‘alar buyurtmasi, referral, reyting, admin kitob/sahifa boshqaruvi, PDF matnini sahifalarga ajratish, sovg‘alarni boshqarish va buyurtmalarni tasdiqlash mavjud. Ro‘yxatdan o‘tish Telegram bot ichida amalga oshadi. PDF faqat matnini ajratish mumkin bo‘lgan sahifalarda avtomatik to‘ldiriladi; skanerlangan PDF uchun OCR qo‘shilmagan.

Eslatma: WebApp va bot bitta `DATABASE_URL` bazasidan foydalanishi kerak. Dastlabki tekshiruv sintaksis/import tekshiruvidir; deploydan oldin haqiqiy Telegram bot, HTTPS, AI kalitlari va buyurtma jarayonini end-to-end sinovdan o‘tkazing.
