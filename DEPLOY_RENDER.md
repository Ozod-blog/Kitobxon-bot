# Render'ga joylash (bepul tarif)

Bot va WebApp bitta Render xizmatida ishlaydi (`RUN_BOT=true`). Alohida bot jarayoni kerak emas.

## 1. Bepul Postgres baza oching (MUHIM)
Render bepul xizmatining fayl tizimi **doimiy emas**: har qayta ishga tushganda `kitobxon.db` (SQLite) o‘chib ketadi, barcha foydalanuvchilar va tangalar yo‘qoladi. Shuning uchun tashqi baza kerak.
Render'ning o‘z bepul Postgres'i 30 kundan keyin o‘chadi, shuning uchun **Neon** (neon.tech) yoki **Supabase** ishlating:
1. neon.tech da loyiha yarating, "Connection string" ni nusxalang (`postgresql://...`).
2. Shu manzil `DATABASE_URL` bo‘ladi. Kod `postgresql://` ni o‘zi `asyncpg` ga moslaydi.

## 2. Kodni GitHub'ga yuklang
`.env` faylini yuklamang (`.gitignore` da bor).

## 3. Render'da xizmat yarating
New → Blueprint (render.yaml ni topadi) yoki New → Web Service:
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.web:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

Environment o‘zgaruvchilari: `BOT_TOKEN`, `BOT_USERNAME`, `ADMIN_IDS`, `DATABASE_URL`, `GEMINI_API_KEY`, `RUN_BOT=true`, `PYTHON_VERSION=3.12.8`.
`AI_MODEL` ni bo‘sh qoldiring.

## 4. WEBAPP_URL
Birinchi deploydan keyin Render manzil beradi: `https://nom.onrender.com`. Uni `WEBAPP_URL` ga yozing va qayta deploy qiling.
BotFather → botingiz → Menu Button / Web App manzilini ham shu URL ga o‘zgartiring.

## 5. Server uxlamasligi uchun
Bepul tarif 15 daqiqa trafik bo‘lmasa servisni uxlatadi, bot esa uxlaganda javob bermaydi. Ikki qatlam himoya:
1. **Ichki:** kod o‘zi har 8 daqiqada `RENDER_EXTERNAL_URL/health` ga so‘rov yuboradi (Render buni avtomatik beradi).
2. **Tashqi (tavsiya):** uptimerobot.com yoki cron-job.org da bepul monitor oching: `https://nom.onrender.com/health`, har 5 daqiqada. Servis tasodifan uxlab qolsa yoki qayta ishga tushsa, uni darrov uyg‘otadi.

Bepul tarifda oyiga 750 soat bor, bitta xizmat 24/7 ishlasa ~744 soat sarflaydi: sig‘adi, lekin bitta xizmatdan ortig‘ini bepul ishlatib bo‘lmaydi.

## 6. Ehtiyot bo‘ling
- Bot **bitta joyda** ishlashi kerak. Kompyuteringizda `python -m app.main` ni o‘chiring, aks holda Telegram "terminated by other getUpdates request" xatosini beradi.
- Foydalanuvchilar sonini bilish va zaxira uchun Neon'dagi bazadan vaqti-vaqti bilan nusxa oling.

---

# Railway'ga joylash (uxlamaydi, lekin pullik)

Railway'da xizmat uxlab qolmaydi, shuning uchun keep-alive kerak emas. Kod o'zgarmaydi: `railway.json` va `.python-version` tayyor.

**Narx:** yangi hisobga **bir martalik $5 sinov krediti** beriladi (muddati Railway'ning free trial sahifasida). Kredit tugagach yoki muddat o'tgach, Free tarifga ($1/oy kredit) yoki Hobby tarifga ($5/oy) o'tish kerak bo'ladi. Joriy shartlarni railway.com/pricing da tekshiring.

**Baza:** loyiha endi PostgreSQL uchun mo'ljallangan (`asyncpg`). SQLite faqat lokal sinov uchun.

1. Kodni GitHub'ga yuklang (`.env` siz).
2. railway.com → New Project → Deploy from GitHub repo.
3. Shu loyihada **+ New → Database → PostgreSQL** qo'shing. Baza fayl tizimi o'chib ketmaydigan hajmda saqlanadi.
4. Bot xizmatida Variables bo'limiga yozing:
   - `BOT_TOKEN`, `BOT_USERNAME`, `ADMIN_IDS`, `GEMINI_API_KEY`
   - `RUN_BOT` = `true`
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` (bazaning o'z o'zgaruvchisiga havola; kod `postgresql://` ni o'zi moslaydi)
   - `AI_MODEL` ni bo'sh qoldiring
5. Xizmat → Settings → Networking → **Generate Domain**. Hosil bo'lgan `https://....up.railway.app` manzilini `WEBAPP_URL` ga yozing va BotFather'dagi Web App manzilini ham shunga o'zgartiring.
6. Kompyuteringizda botni o'chiring (bitta joyda ishlashi kerak).
