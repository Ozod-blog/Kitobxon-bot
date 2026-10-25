/* Kitobxon WebApp */
const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();
const initData = tg?.initData || '';

/* ---------- helpers ---------- */
const $ = (s, r = document) => r.querySelector(s);
const esc = (s = '') => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = n => String(n ?? 0).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
const MONTHS = ['yan', 'fev', 'mar', 'apr', 'may', 'iyn', 'iyl', 'avg', 'sen', 'okt', 'noy', 'dek'];
const fmtDate = iso => { const d = new Date(iso); return isNaN(d) ? '' : `${d.getDate()}-${MONTHS[d.getMonth()]}`; };
const initial = s => (String(s || '?').trim()[0] || '?').toUpperCase();
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { } },
};
const haptic = (t = 'light') => { try { tg?.HapticFeedback?.impactOccurred(t); } catch { } };
const notify = t => { try { tg?.HapticFeedback?.notificationOccurred(t); } catch { } };

/* ---------- icons ---------- */
const P = {
  home: '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
  book: '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 21V5"/><path d="M9 8h6"/>',
  gift: '<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M5 12v8a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-8M12 8v13"/><path d="M12 8c-1.5-4-6-4-5-1 .5 1.5 3 1 5 1zm0 0c1.500-4 6-4 5-1-.5 1.500-3 1-5 1z"/>',
  trophy: '<path d="M8 4h8v6a4 4 0 0 1-8 0zM8 6H4v1a4 4 0 0 0 4 4M16 6h4v1a4 4 0 0 1-4 4M12 14v4M8 21h8M9 18h6"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  back: '<path d="m15 18-6-6 6-6"/>',
  next: '<path d="m9 18 6-6-6-6"/>',
  close: '<path d="M6 6l12 12M18 6 6 18"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.500-3.500"/>',
  check: '<path d="m5 12.500 4.500 4.500L19 7"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/>',
  share: '<path d="M12 16V4m0 0L8 8m4-4 4 4M5 13v6a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-6"/>',
  users: '<circle cx="9" cy="8" r="3.500"/><path d="M2.500 20a6.500 6.500 0 0 1 13 0M16 4.500a3.500 3.500 0 0 1 0 7M18 14.500a6.500 6.500 0 0 1 3.500 5.500"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M19.400 15a1.700 1.700 0 0 0 .3 1.800l.1.100a2 2 0 1 1-2.800 2.800l-.1-.1a1.700 1.700 0 0 0-1.800-.3 1.700 1.700 0 0 0-1 1.500V21a2 2 0 1 1-4 0v-.1a1.700 1.700 0 0 0-1.100-1.500 1.700 1.700 0 0 0-1.800.3l-.1.1a2 2 0 1 1-2.800-2.800l.1-.1a1.700 1.700 0 0 0 .3-1.800 1.700 1.700 0 0 0-1.500-1H3a2 2 0 1 1 0-4h.1a1.700 1.700 0 0 0 1.500-1.100 1.700 1.700 0 0 0-.3-1.800l-.1-.1a2 2 0 1 1 2.800-2.800l.1.100a1.700 1.700 0 0 0 1.800.3H9a1.700 1.700 0 0 0 1-1.500V3a2 2 0 1 1 4 0v.1a1.700 1.700 0 0 0 1 1.500 1.700 1.700 0 0 0 1.800-.3l.1-.1a2 2 0 1 1 2.800 2.800l-.1.100a1.700 1.700 0 0 0-.3 1.800V9a1.700 1.700 0 0 0 1.500 1H21a2 2 0 1 1 0 4h-.1a1.700 1.700 0 0 0-1.500 1z"/>',
  brain: '<path d="M9 4a3 3 0 0 0-3 3v.5A3 3 0 0 0 4 10.500 3 3 0 0 0 5 13a3 3 0 0 0 1 4.500A3 3 0 0 0 9 20a3 3 0 0 0 3-3V7a3 3 0 0 0-3-3zM15 4a3 3 0 0 1 3 3v.5a3 3 0 0 1 2 3 3 3 0 0 1-1 2.500 3 3 0 0 1-1 4.500A3 3 0 0 1 15 20a3 3 0 0 1-3-3"/>',
  up: '<path d="M12 19V5m0 0-6 6m6-6 6 6"/>',
  down: '<path d="M12 5v14m0 0-6-6m6 6 6-6"/>',
  text: '<path d="M4 20 10 5l6 15M6.500 15h7M16 12h4m-2-2v4"/>',
  box: '<path d="m3 7 9-4 9 4v10l-9 4-9-4zM3 7l9 4 9-4M12 11v10"/>',
  file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5"/>',
};
const ico = (n, cls = '') => `<svg class="i ${cls}" viewBox="0 0 24 24" aria-hidden="true">${P[n] || ''}</svg>`;
const coin = (cls = '') => `<span class="coin ${cls}" aria-hidden="true"></span>`;

/* ---------- api ---------- */
async function api(path, opts = {}) {
  const r = await fetch(path, { ...opts, headers: { 'Content-Type': 'application/json', 'X-Telegram-Init-Data': initData, ...opts.headers } });
  let d = {};
  try { d = await r.json(); } catch { }
  if (!r.ok) throw Error(typeof d.detail === 'string' ? d.detail : 'Xatolik yuz berdi. Qayta urinib ko‘ring.');
  return d;
}
const post = (p, body = {}) => api(p, { method: 'POST', body: JSON.stringify(body) });

/* ---------- toast ---------- */
let toastTimer;
function toast(text, err = false) {
  const t = $('#toast');
  t.className = 'toast' + (err ? ' err' : '');
  t.textContent = text;
  requestAnimationFrame(() => t.classList.add('show'));
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 3800);
  notify(err ? 'error' : 'success');
}
const fail = e => toast(e.message || 'Xatolik yuz berdi', true);

/* ---------- theme ---------- */
function applyTheme() {
  const dark = tg?.colorScheme ? tg.colorScheme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  try { tg?.setHeaderColor?.(dark ? '#0b1411' : '#f3f6f3'); tg?.setBackgroundColor?.(dark ? '#0b1411' : '#f3f6f3'); } catch { }
}
applyTheme();
tg?.onEvent?.('themeChanged', applyTheme);

/* ---------- state ---------- */
const state = { mode: 'user', apage: 'menu', me: null, tab: 'home', books: [], gifts: [], reader: null, quiz: null };
const TABS = [
  ['home', 'Bosh sahifa', 'home'],
  ['books', 'Kitoblar', 'book'],
  ['gifts', 'Sovg‘alar', 'gift'],
  ['board', 'Reyting', 'trophy'],
  ['profile', 'Profil', 'user'],
];
const view = () => $('#view');
const setCoins = n => { if (state.me?.user) state.me.user.coins = n; };

function renderNav() {
  const admin = state.mode === 'admin';
  const list = admin ? ADMIN_TABS : TABS;
  const cur = admin ? adminTabOf(state.apage) : state.tab;
  $('#nav').innerHTML = list.map(([id, label, icon]) =>
    `<button class="tab" data-act="${admin ? 'apage' : 'tab'}" data-id="${id}" ${cur === id ? 'aria-current="page"' : ''}>${ico(icon)}<span>${label}</span></button>`).join('');
}

function skeleton(kind = 'list') {
  if (kind === 'home') return `<div class="skel" style="height:34px;width:55%;margin:6px 0 18px"></div><div class="skel" style="height:190px;border-radius:24px"></div><div class="skel" style="height:22px;width:40%;margin:28px 0 12px"></div><div class="row" style="gap:14px"><div class="skel" style="width:112px;height:150px"></div><div class="skel" style="width:112px;height:150px"></div><div class="skel" style="width:112px;height:150px"></div></div>`;
  return `<div class="skel" style="height:34px;width:50%;margin:6px 0 18px"></div>` + Array.from({ length: 4 }, () => '<div class="skel" style="height:104px;margin-bottom:12px"></div>').join('');
}

function appbar(title, sub = '') {
  const u = state.me?.user;
  return `<div class="appbar"><div>${sub ? `<div class="sub">${esc(sub)}</div>` : ''}<h1>${esc(title)}</h1></div>${u ? `<div class="coin-pill" aria-label="Balans">${coin()}<span class="num" data-coins>${fmt(u.coins)}</span></div>` : ''}</div>`;
}

function empty(icon, title, text) {
  return `<div class="empty"><div class="ic">${ico(icon)}</div><b>${esc(title)}</b><p>${esc(text)}</p></div>`;
}

async function show(tab) {
  state.tab = tab;
  renderNav();
  closeOverlay();
  const v = view();
  v.classList.remove('no-nav');
  $('#nav').hidden = false;
  v.innerHTML = skeleton(tab === 'home' ? 'home' : 'list');
  window.scrollTo(0, 0);
  tg?.BackButton?.hide();
  try {
    await ({ home: loadHome, books: loadBooks, gifts: loadGifts, board: loadBoard, profile: loadProfile }[tab])();
  } catch (e) {
    v.innerHTML = appbar('Xatolik') + empty('close', 'Ma’lumot yuklanmadi', e.message);
  }
}

async function refreshMe() {
  try { state.me = await api('/api/me'); } catch { }
  document.querySelectorAll('[data-coins]').forEach(e => e.textContent = fmt(state.me?.user?.coins));
}

/* ---------- covers ---------- */
const cover = b => `<div class="cover c${b.id % 6}"><span class="t">${esc(b.title)}</span><span class="a">${esc(b.author)}</span></div>`;

/* ---------- HOME ---------- */
async function loadHome() {
  const u = state.me.user;
  const [books, gifts, active] = await Promise.all([
    api('/api/books').catch(() => []),
    api('/api/gifts').catch(() => []),
    api('/api/reading/active').catch(() => ({ active: false })),
  ]);
  state.books = books; state.gifts = gifts;

  const target = gifts.filter(g => g.stock > 0).sort((a, b) => a.price - b.price).find(g => g.price > u.coins) || null;
  const affordable = gifts.filter(g => g.stock > 0 && g.price <= u.coins);
  let goal = '';
  if (target) {
    const pct = Math.min(100, Math.round(u.coins / target.price * 100));
    goal = `<div class="goal"><div class="top"><span>Keyingi sovg‘a: <b>${esc(target.name)}</b></span><span class="num">yana ${fmt(target.price - u.coins)}</span></div><div class="bar"><i style="width:${pct}%"></i></div></div>`;
  } else if (affordable.length) {
    goal = `<button class="goal" data-act="tab" data-id="gifts" style="width:100%;text-align:left"><div class="top"><span><b>${affordable.length} ta sovg‘ani</b> hozir olishingiz mumkin</span><span>${ico('next')}</span></div><div class="bar"><i style="width:100%"></i></div></button>`;
  }

  const cont = active.active ? `
    <button class="card continue" data-act="resume">
      <span class="ring">${ico('book')}</span>
      <span class="grow"><b class="ellipsis" style="display:block">${esc(active.book_title)}</b>
      <span class="muted small">${active.page_count} sahifa · ${active.remaining_seconds > 0 ? `testgacha ${active.remaining_seconds} soniya` : 'test tayyor'}</span></span>
      <span class="btn sm soft">Davom etish</span>
    </button>` : '';

  view().innerHTML = `
    ${appbar(`Salom, ${u.first_name}`, 'Bugun nima o‘qiymiz?')}
    <section class="hero">
      <div class="label">Sizning balansingiz</div>
      <div class="balance">${coin('lg')}<span class="num" data-coins>${fmt(u.coins)}</span><small>tanga</small></div>
      ${goal}
    </section>
    ${cont}
    <div class="section-title"><h2>Kitoblar</h2><button class="link" data-act="tab" data-id="books">Hammasi</button></div>
    ${books.length ? `<div class="shelf">${books.slice(0, 8).map(b => `<button class="book" data-act="book" data-id="${b.id}">${cover(b)}<div class="meta ellipsis">${esc(b.title)}</div></button>`).join('')}</div>`
      : `<div class="card">${empty('book', 'Hozircha kitob yo‘q', 'Administrator kitob qo‘shgach shu yerda ko‘rinadi.')}</div>`}
    <div class="section-title"><h2>Tanga ishlash</h2></div>
    <div class="stack">
      <div class="card row"><span class="avatar">${ico('book')}</span><div class="grow"><b>O‘qing</b><p class="muted small">Kitobdan sahifalarni tanlab o‘qing.</p></div></div>
      <div class="card row"><span class="avatar">${ico('brain')}</span><div class="grow"><b>Testdan o‘ting</b><p class="muted small">AI savollariga javob bering va tanga oling.</p></div></div>
      <div class="card row"><span class="avatar">${ico('users')}</span><div class="grow"><b>Do‘stlarni taklif qiling</b><p class="muted small">Har bir do‘st uchun qo‘shimcha tanga.</p></div><button class="btn sm soft" data-act="tab" data-id="profile">Ochish</button></div>
    </div>`;
}

/* ---------- BOOKS ---------- */
let searchTimer;
async function loadBooks() {
  view().innerHTML = `${appbar('Kitoblar', 'Kutubxona')}
    <label class="search">${ico('search')}<input id="q" type="search" placeholder="Nom bo‘yicha qidirish" autocomplete="off"></label>
    <div id="booklist"></div>`;
  $('#q').addEventListener('input', e => { clearTimeout(searchTimer); searchTimer = setTimeout(() => renderBooks(e.target.value.trim()), 300); });
  await renderBooks('');
}
async function renderBooks(q) {
  const box = $('#booklist'); if (!box) return;
  try {
    const list = await api('/api/books?search=' + encodeURIComponent(q));
    if (!q) state.books = list;
    list.forEach(b => { if (!state.books.find(x => x.id === b.id)) state.books.push(b); });
    box.innerHTML = list.length ? `<div class="book-list">${list.map(b => `
      <button class="card book-row" data-act="book" data-id="${b.id}">
        ${cover(b)}
        <div><h3>${esc(b.title)}</h3><div class="muted small" style="margin-top:3px">${esc(b.author)}</div>
        ${b.description ? `<p class="desc">${esc(b.description)}</p>` : ''}
        <div style="margin-top:10px"><span class="chip">${ico('file').replace('class="i ', 'style="width:14px;height:14px" class="i ')}${b.total_pages} sahifa</span></div></div>
      </button>`).join('')}</div>` : empty('search', q ? 'Hech narsa topilmadi' : 'Hozircha kitob yo‘q', q ? 'Boshqa nom bilan qidirib ko‘ring.' : 'Administrator kitob qo‘shgach shu yerda ko‘rinadi.');
  } catch (e) { box.innerHTML = empty('close', 'Yuklanmadi', e.message); }
}

function openBook(id) {
  const b = state.books.find(x => x.id === id); if (!b) return;
  let n = Math.min(5, b.total_pages);
  const html = `
    <div class="row" style="align-items:flex-start;gap:16px;margin-top:6px"><div style="width:92px;flex:none">${cover(b)}</div>
      <div><h2>${esc(b.title)}</h2><p class="muted">${esc(b.author)}</p><div style="margin-top:8px"><span class="chip">${b.total_pages} sahifa</span></div></div></div>
    ${b.description ? `<p class="muted" style="margin-top:14px">${esc(b.description)}</p>` : ''}
    <p style="margin-top:18px;font-weight:650">Nechta sahifa o‘qiysiz?</p>
    <div class="stepper"><button data-step="-1" aria-label="Kamaytirish">−</button><output id="stepn">${n}</output><button data-step="1" aria-label="Ko‘paytirish">+</button></div>
    <p class="muted small" style="text-align:center">1 dan ${b.total_pages} gacha. O‘qib bo‘lgach AI test ochiladi.</p>`;
  const s = sheet({ body: html, actions: [{ label: 'O‘qishni boshlash', cls: 'btn block', id: 'go' }] });
  s.el.addEventListener('click', e => {
    const st = e.target.closest('[data-step]');
    if (st) { n = Math.max(1, Math.min(b.total_pages, n + Number(st.dataset.step))); $('#stepn', s.el).textContent = n; haptic(); }
  });
  s.on('go', async btn => {
    btn.disabled = true;
    try {
      const r = await post('/api/reading/start', { book_id: b.id, page_count: n });
      s.close();
      openReader({ sessionId: r.id, bookId: b.id, title: b.title, total: n, seconds: r.minimum_seconds });
    } catch (e) {
      btn.disabled = false; fail(e);
      if (/faol|active|davom/i.test(e.message)) { s.close(); resumeReading(); }
    }
  });
}

/* ---------- READER ---------- */
async function resumeReading() {
  try {
    const a = await api('/api/reading/active');
    if (!a.active) { toast('Faol o‘qish topilmadi', true); return show('home'); }
    openReader({ sessionId: a.id, bookId: a.book_id, title: a.book_title, total: a.page_count, seconds: a.remaining_seconds });
  } catch (e) { fail(e); }
}

function openOverlay(html) {
  const o = $('#overlay'); o.hidden = false; o.innerHTML = `<div class="inner">${html}</div>`;
  $('#nav').hidden = true;
  tg?.BackButton?.show();
  tg?.BackButton?.offClick?.(onBack); tg?.BackButton?.onClick?.(onBack);
  return o;
}
function closeOverlay() {
  const o = $('#overlay'); o.hidden = true; o.innerHTML = '';
  if (state.reader?.timer) clearInterval(state.reader.timer);
  state.reader = null; state.quiz = null;
}
function onBack() {
  if (state.mode === 'admin') { state.apage === 'menu' ? exitAdmin() : showAdmin('menu'); return; }
  if (!$('#overlay').hidden) { closeOverlay(); show(state.tab); }
}
tg?.BackButton?.onClick?.(onBack);

function openReader({ sessionId, bookId, title, total, seconds }) {
  closeOverlay();
  const fs = store.get('fs', 18);
  state.reader = { sessionId, bookId, title, total, page: 1, cache: {}, deadline: Date.now() + seconds * 1000, totalSecs: Math.max(seconds, 1), fs };
  openOverlay(`
    <div class="topbar"><button class="icon-btn" data-act="reader-close" aria-label="Orqaga">${ico('back')}</button>
      <div class="ttl"><b class="ellipsis" style="display:block">${esc(title)}</b><span id="rd-info"></span></div>
      <button class="icon-btn" data-act="font-down" aria-label="Matnni kichraytirish">${ico('text')}</button>
      <button class="icon-btn" data-act="font-up" aria-label="Matnni kattalashtirish" style="font-weight:800;font-size:18px">A+</button></div>
    <div class="progress"><i id="rd-prog"></i></div>
    <div class="reader-body" id="rd-body"></div>
    <div class="reader-foot">
      <button class="icon-btn" id="rd-prev" data-act="page-prev" aria-label="Oldingi sahifa">${ico('back')}</button>
      <button class="btn timer-btn wait" id="rd-quiz" data-act="quiz"><i class="fill" id="rd-fill" style="width:0"></i><span id="rd-quiz-label"></span></button>
      <button class="icon-btn" id="rd-next" data-act="page-next" aria-label="Keyingi sahifa">${ico('next')}</button>
    </div>`);
  loadReaderPage();
  tickTimer();
  state.reader.timer = setInterval(tickTimer, 500);
}
function tickTimer() {
  const r = state.reader; if (!r) return;
  const left = Math.max(0, Math.ceil((r.deadline - Date.now()) / 1000));
  const btn = $('#rd-quiz'); if (!btn) return;
  const label = $('#rd-quiz-label');
  if (left > 0) {
    btn.classList.add('wait');
    const m = Math.floor(left / 60), s = String(left % 60).padStart(2, '0');
    label.textContent = `Test ${m}:${s} dan keyin`;
    $('#rd-fill').style.width = (100 - left / r.totalSecs * 100) + '%';
  } else {
    if (btn.classList.contains('wait')) { notify('success'); }
    btn.classList.remove('wait');
    $('#rd-fill').style.width = '0';
    label.textContent = 'Testni boshlash';
  }
}
/* PDF dan olingan matnni chiroyli abzaslarga ajratadi: qator uzilishlarini birlashtiradi,
   so‘z ko‘chirishlarini tuzatadi, sarlavha va dialoglarni ajratadi. */
function formatPage(raw) {
  const lines = String(raw || '').replace(/\r/g, '').replace(/\u00ad/g, '').split('\n').map(l => l.replace(/\s+/g, ' ').trim());
  const lens = lines.filter(Boolean).map(l => l.length).sort((a, b) => a - b);
  const full = lens.length ? lens[Math.floor(lens.length * 0.8)] : 0;
  const blocks = [];
  let cur = '', last = 0, head = false;
  const isUpper = l => l.length <= 90 && /[A-ZА-ЯЁ]/.test(l) && l === l.toUpperCase() && !/^\d+$/.test(l);
  const flush = () => { if (cur) blocks.push(cur); cur = ''; head = false; };
  lines.forEach(line => {
    if (!line) { flush(); return; }
    if (isUpper(line)) { if (!head) { flush(); head = true; } cur = cur ? cur + ' ' + line : line; last = line.length; return; }
    if (head) flush();
    if (cur) {
      const dialogue = /^[–—]\s?\S/.test(line);
      const endsSentence = /[.!?…»”"]$/.test(cur);
      if (dialogue || (endsSentence && last < full * 0.72)) flush();
    }
    if (!cur) cur = line;
    else if (/\s?-$/.test(cur) && /^[a-zʻʼ‘’'а-яёўқғҳ]/.test(line)) cur = cur.replace(/\s?-$/, '') + line;
    else cur += ' ' + line;
    last = line.length;
  });
  flush();
  return blocks.filter(b => !/^\d{1,4}$/.test(b)).map(b => {
    const isHeading = b.length <= 90 && /[A-ZА-ЯЁ]/.test(b) && b === b.toUpperCase();
    return isHeading ? `<h3>${esc(b)}</h3>` : `<p>${esc(b)}</p>`;
  }).join('') || '<p class="muted">Bu sahifada matn yo‘q.</p>';
}

async function loadReaderPage() {
  const r = state.reader; if (!r) return;
  const body = $('#rd-body');
  $('#rd-info').textContent = `${r.page} / ${r.total} sahifa`;
  $('#rd-prog').style.width = (r.page / r.total * 100) + '%';
  $('#rd-prev').disabled = r.page <= 1;
  $('#rd-next').disabled = r.page >= r.total;
  body.style.setProperty('--fs', r.fs + 'px');
  if (!r.cache[r.page]) {
    body.innerHTML = `<div class="skel" style="height:18px;width:30%;margin-bottom:18px"></div>` + Array.from({ length: 6 }, (_, i) => `<div class="skel" style="height:16px;margin-bottom:12px;width:${100 - (i % 3) * 9}%"></div>`).join('');
    try { r.cache[r.page] = (await api(`/api/books/${r.bookId}/pages/${r.page}`)).content; }
    catch (e) { body.innerHTML = empty('close', 'Sahifa ochilmadi', e.message); return; }
  }
  if (!state.reader) return;
  body.innerHTML = `<div class="pgno">${r.page}-sahifa</div><div class="pg">${formatPage(r.cache[r.page])}</div>`;
  body.scrollTop = 0;
}
function turn(d) {
  const r = state.reader; if (!r) return;
  const p = r.page + d; if (p < 1 || p > r.total) return;
  r.page = p; haptic(); loadReaderPage();
}
function setFont(d) {
  const r = state.reader; if (!r) return;
  r.fs = Math.max(14, Math.min(26, r.fs + d)); store.set('fs', r.fs);
  $('#rd-body').style.setProperty('--fs', r.fs + 'px');
}

/* ---------- QUIZ ---------- */
async function startQuiz() {
  const r = state.reader; if (!r) return;
  const btn = $('#rd-quiz');
  if (btn.classList.contains('wait')) { toast('O‘qish vaqti hali tugamadi. Biroz kuting.', true); return; }
  btn.classList.add('wait');
  try {
    const q = await post(`/api/reading/${r.sessionId}/quiz`);
    closeOverlay();
    state.quiz = { id: q.quiz_id, questions: q.questions, idx: 0, answers: {} };
    renderQuestion();
  } catch (e) { btn.classList.remove('wait'); fail(e); }
}
function renderQuestion() {
  const z = state.quiz; const q = z.questions[z.idx]; const last = z.idx === z.questions.length - 1;
  const sel = z.answers[q.id];
  openOverlay(`
    <div class="topbar"><button class="icon-btn" data-act="quiz-close" aria-label="Chiqish">${ico('close')}</button>
      <div class="ttl"><b>AI viktorina</b><span>${z.idx + 1} / ${z.questions.length} savol</span></div></div>
    <div style="padding:0 18px"><div class="dots">${z.questions.map((_, i) => `<i class="${i < z.idx ? 'done' : i === z.idx ? 'cur' : ''}"></i>`).join('')}</div></div>
    <div class="quiz-body"><h2>${esc(q.question)}</h2>
      <div class="opts" role="radiogroup">${q.options.map((o, j) => `<button class="opt" role="radio" aria-checked="${sel === j}" data-act="opt" data-j="${j}"><span class="ltr">${'ABCDEFG'[j] || j + 1}</span><span>${esc(o)}</span></button>`).join('')}</div></div>
    <div class="quiz-foot"><button class="btn block" id="qnext" data-act="qnext" ${sel === undefined ? 'disabled' : ''}>${last ? 'Javoblarni yuborish' : 'Keyingi savol'}</button></div>`);
}
async function submitQuiz() {
  const z = state.quiz; const btn = $('#qnext'); btn.disabled = true;
  try {
    const r = await post(`/api/quizzes/${z.id}/submit`, { answers: z.answers });
    const total = z.questions.length;
    const pct = Math.round(r.correct / total * 100);
    await refreshMe();
    notify(r.passed ? 'success' : 'warning');
    openOverlay(`<div class="result ${r.passed ? 'pass' : 'fail'}">
      <div class="score-ring pop" style="--p:${pct}"><b>${r.correct}<small>/${total}</small></b></div>
      <h2>${r.passed ? 'Ajoyib natija!' : 'Deyarli bo‘ldi'}</h2>
      <p class="muted">${r.passed ? 'Testdan muvaffaqiyatli o‘tdingiz.' : `O‘tish uchun kamida ${r.needed || total} ta to‘g‘ri javob kerak edi. Siz ${r.correct} ta topdingiz. Kitobni qayta o‘qib, yangi test topshiring.`}</p>
      ${r.passed && r.coins_awarded ? `<div class="reward pop">${coin('lg')}+${r.coins_awarded} tanga</div>` : ''}
      <div class="stack" style="width:100%;max-width:340px;margin-top:22px"><button class="btn block" data-act="done">${r.passed ? 'Bosh sahifaga' : 'Kitoblarga qaytish'}</button></div></div>`);
    state.quiz = { passed: r.passed };
  } catch (e) { btn.disabled = false; fail(e); }
}

/* ---------- GIFTS ---------- */
async function loadGifts() {
  const list = await api('/api/gifts'); state.gifts = list;
  const coins = state.me.user.coins;
  view().innerHTML = appbar('Sovg‘alar', 'Tangalarni almashtiring') + (list.length ? `<div class="gift-grid">${list.map(g => {
    const out = g.stock < 1, can = coins >= g.price;
    return `<article class="card gift">
      <div class="pic">${ico('gift')}</div>
      <div><h3>${esc(g.name)}</h3>${g.description ? `<p class="muted small" style="margin-top:3px">${esc(g.description)}</p>` : ''}</div>
      <div class="price">${coin()}<span class="num">${fmt(g.price)}</span></div>
      <div class="need">${out ? 'Omborda qolmagan' : can ? `Omborda ${g.stock} ta` : `Yana ${fmt(g.price - coins)} tanga kerak`}</div>
      ${!out && !can ? `<div class="bar on-card"><i style="width:${Math.round(coins / g.price * 100)}%"></i></div>` : ''}
      <button class="btn sm ${can && !out ? '' : 'ghost'}" ${out || !can ? 'disabled' : ''} data-act="gift" data-id="${g.id}">Buyurtma</button>
    </article>`;
  }).join('')}</div>` : empty('gift', 'Sovg‘alar hozircha yo‘q', 'Yangi sovg‘alar qo‘shilganda shu yerda ko‘rinadi.'));
}
async function orderGift(id) {
  const g = state.gifts.find(x => x.id === id); if (!g) return;
  const ok = await confirmSheet({ title: 'Buyurtmani tasdiqlang', text: `“${g.name}” uchun ${fmt(g.price)} tanga balansingizdan ushlab turiladi. Buyurtma rad etilsa, tangalar qaytariladi.`, ok: 'Buyurtma berish' });
  if (!ok) return;
  try {
    await post(`/api/gifts/${id}/order`);
    toast('Buyurtma qabul qilindi');
    await refreshMe(); loadGifts();
  } catch (e) { fail(e); }
}

/* ---------- LEADERBOARD ---------- */
async function loadBoard() {
  const list = await api('/api/leaderboard');
  const row = x => `<div class="rank-row ${x.me ? 'me' : ''}"><span class="n">${x.rank}</span><span class="avatar">${esc(initial(x.name))}</span><div class="grow"><b class="ellipsis" style="display:block">${esc(x.name)}${x.me ? ' (siz)' : ''}</b><span class="muted small">${fmt(x.pages)} sahifa</span></div><span class="row" style="gap:6px;font-weight:750">${coin()}<span class="num">${fmt(x.coins)}</span></span></div>`;
  let podium = '';
  if (list.length >= 3) {
    const [a, b, c] = list;
    const pod = (x, cls) => `<div class="pod ${cls}"><div class="medal">${x.rank}</div><div class="nm ellipsis">${esc(x.name)}</div><div class="pts">${fmt(x.coins)} tanga</div></div>`;
    podium = `<div class="podium">${pod(b, 'second')}${pod(a, 'first')}${pod(c, 'third')}</div>`;
  }
  const rest = list.length >= 3 ? list.slice(3) : list;
  view().innerHTML = appbar('Reyting', 'Eng faol kitobxonlar') + (list.length ? podium + `<div class="stack">${rest.map(row).join('')}</div>` : empty('trophy', 'Reyting bo‘sh', 'Birinchi bo‘lib tanga to‘plang.'));
}

/* ---------- PROFILE ---------- */
const REASONS = {
  quiz_reward: 'Testdan o‘tish uchun',
  referral_registration: 'Do‘st taklifi',
  referral_registration_reward: 'Do‘st taklifi',
  referral_quiz_reward: 'Do‘stingiz birinchi testdan o‘tdi',
  gift_reservation: 'Sovg‘a buyurtmasi',
  gift_refund: 'Buyurtma uchun qaytarilgan tanga',
  admin_adjustment: 'Administrator tuzatishi',
};
async function loadProfile() {
  const [a, r, t] = await Promise.all([api('/api/me'), api('/api/referrals'), api('/api/transactions')]);
  state.me = a; const u = a.user;
  const link = `https://t.me/${r.bot_username}?start=ref_${r.telegram_id}`;
  state.refLink = link;
  view().innerHTML = `
    <div class="profile-head"><div class="avatar xl">${esc(initial(u.first_name))}</div>
      <div><h1>${esc(u.first_name)} ${esc(u.last_name)}</h1><p class="muted">${esc([u.region, u.district].filter(x => x && x !== 'Administrator').join(', '))}</p></div></div>
    <div class="stats">
      <div class="card stat"><b class="num">${fmt(u.coins)}</b><span>tanga</span></div>
      <div class="card stat"><b class="num">${fmt(u.total_pages)}</b><span>sahifa</span></div>
      <div class="card stat"><b class="num">${fmt(r.count)}</b><span>do‘st</span></div>
    </div>
    <div class="section-title"><h2>Do‘stlarni taklif qiling</h2></div>
    <div class="card stack">
      <p class="muted small">Do‘stingiz ro‘yxatdan o‘tsa — ${fmt(r.coins_per_registration)} tanga, birinchi testdan o‘tsa — yana ${fmt(r.coins_per_quiz)} tanga.</p>
      <div class="row" style="gap:8px"><input class="input" id="reflink" readonly value="${esc(link)}" aria-label="Taklif havolasi"><button class="icon-btn" data-act="copy" aria-label="Nusxalash" style="flex:none">${ico('copy')}</button></div>
      <button class="btn block" data-act="share">${ico('share')}Do‘stga yuborish</button>
    </div>
    ${a.is_admin ? `<div class="section-title"><h2>Boshqaruv</h2></div><button class="card row" style="width:100%;text-align:left" data-act="admin-enter"><span class="avatar">${ico('gear')}</span><div class="grow"><b>Admin paneli</b><p class="muted small">Statistika, foydalanuvchilar, kitoblar, sovg‘alar</p></div>${ico('next')}</button>` : ''}
    <div class="section-title"><h2>Tanga tarixi</h2></div>
    <div class="card" style="padding:4px 16px">${t.length ? t.map(x => `<div class="tx ${x.amount > 0 ? 'pos' : 'neg'}"><span class="ic">${ico(x.amount > 0 ? 'up' : 'down')}</span><div class="grow"><div>${esc(REASONS[x.reason] || x.reason)}</div><div class="muted small">${fmtDate(x.created_at)}</div></div><b class="num">${x.amount > 0 ? '+' : ''}${fmt(x.amount)}</b></div>`).join('') : empty('clock', 'Hali amallar yo‘q', 'Test topshirib birinchi tangangizni oling.')}</div>`;
}

/* ---------- sheets ---------- */
function sheet({ title = '', body = '', actions = [] }) {
  const root = $('#sheet-root');
  const back = document.createElement('div'); back.className = 'sheet-back';
  back.innerHTML = `<div class="sheet" role="dialog" aria-modal="true"><div class="grab"></div>${title ? `<h2>${esc(title)}</h2>` : ''}${body}<div class="actions ${actions.length === 2 ? 'two' : ''}">${actions.map(a => `<button class="${a.cls || 'btn block'}" data-sid="${a.id}">${esc(a.label)}</button>`).join('')}</div></div>`;
  root.appendChild(back);
  const handlers = {};
  const api_ = {
    el: back, on(id, fn) { handlers[id] = fn; }, close() { back.remove(); },
  };
  back.addEventListener('click', e => {
    if (e.target === back) { api_.close(); api_.onCancel?.(); return; }
    const b = e.target.closest('[data-sid]');
    if (b) handlers[b.dataset.sid]?.(b);
  });
  return api_;
}
function confirmSheet({ title, text, ok = 'Tasdiqlash', danger = false }) {
  return new Promise(res => {
    const s = sheet({ title, body: `<p class="muted" style="margin-top:6px">${esc(text)}</p>`, actions: [{ id: 'no', label: 'Bekor qilish', cls: 'btn ghost' }, { id: 'yes', label: ok, cls: 'btn ' + (danger ? 'danger' : '') }] });
    s.on('no', () => { s.close(); res(false); });
    s.on('yes', () => { s.close(); res(true); });
    s.onCancel = () => res(false);
  });
}
function formSheet({ title, fields, ok = 'Saqlash' }) {
  return new Promise(res => {
    const body = `<div class="stack" style="margin-top:12px">${fields.map(f => `<label class="field"><span>${esc(f.label)}</span>${f.type === 'textarea' ? `<textarea class="input" id="f_${f.name}" placeholder="${esc(f.ph || '')}">${esc(f.value ?? '')}</textarea>` : `<input class="input" id="f_${f.name}" type="${f.type || 'text'}" ${f.accept ? `accept="${f.accept}"` : ''} placeholder="${esc(f.ph || '')}" value="${esc(f.value ?? '')}" ${f.min !== undefined ? `min="${f.min}"` : ''} ${f.type === 'number' ? 'inputmode="numeric"' : ''}>`}</label>`).join('')}</div>`;
    const s = sheet({ title, body, actions: [{ id: 'no', label: 'Bekor qilish', cls: 'btn ghost' }, { id: 'yes', label: ok }] });
    s.on('no', () => { s.close(); res(null); });
    s.on('yes', () => { const v = {}; fields.forEach(f => { const el = $('#f_' + f.name, s.el); v[f.name] = f.type === 'file' ? el.files[0] : el.value.trim(); }); s.close(); res(v); });
    s.onCancel = () => res(null);
  });
}

/* ---------- events ---------- */
const actions = {
  tab: d => { haptic(); show(d.id); },
  book: d => openBook(Number(d.id)),
  gift: d => orderGift(Number(d.id)),
  resume: () => resumeReading(),
  'reader-close': () => { closeOverlay(); show(state.tab); },
  'page-prev': () => turn(-1),
  'page-next': () => turn(1),
  'font-up': () => setFont(1),
  'font-down': () => setFont(-1),
  quiz: () => startQuiz(),
  'quiz-close': async () => { if (await confirmSheet({ title: 'Testni to‘xtatasizmi?', text: 'Javoblaringiz saqlanmaydi. Test uchun o‘qishni qaytadan boshlash kerak bo‘lishi mumkin.', ok: 'Chiqish', danger: true })) { closeOverlay(); show('books'); } },
  opt: (d) => { const z = state.quiz; const q = z.questions[z.idx]; z.answers[q.id] = Number(d.j); haptic(); document.querySelectorAll('.opt').forEach(o => o.setAttribute('aria-checked', o.dataset.j === d.j)); $('#qnext').disabled = false; },
  qnext: () => { const z = state.quiz; if (z.idx < z.questions.length - 1) { z.idx++; renderQuestion(); } else submitQuiz(); },
  done: () => { const passed = state.quiz?.passed; closeOverlay(); show(passed ? 'home' : 'books'); },
  copy: async () => { try { await navigator.clipboard.writeText(state.refLink); toast('Havola nusxalandi'); } catch { $('#reflink').select(); toast('Havolani qo‘lda nusxalang', true); } },
  share: () => {
    const url = `https://t.me/share/url?url=${encodeURIComponent(state.refLink)}&text=${encodeURIComponent('Kitobxon botida kitob o‘qib tanga yig‘ing va sovg‘alar oling!')}`;
    tg?.openTelegramLink ? tg.openTelegramLink(url) : window.open(url, '_blank');
  },
};
document.addEventListener('click', e => {
  const el = e.target.closest('[data-act]');
  if (!el || el.closest('.sheet-back')) return;
  actions[el.dataset.act]?.(el.dataset, el);
});

/* ---------- init ---------- */
async function init() {
  try {
    state.me = await api('/api/me');
    if (!state.me.registered) {
      $('#nav').hidden = true;
      view().innerHTML = `<div class="welcome"><div class="logo">${ico('book')}</div><h1>Kitobxonga xush kelibsiz</h1>
        <p>Kitob o‘qing, AI testdan o‘ting va tangalarni sovg‘alarga almashtiring. Boshlash uchun botda ro‘yxatdan o‘ting.</p>
        <div class="card" style="text-align:left"><b>Qanday boshlanadi?</b><p class="muted small" style="margin-top:6px">Botga qayting, /start bosing, ism, telefon raqami va manzilingizni kiriting. So‘ng WebApp tugmasini qayta oching.</p></div>
        <button class="btn block" onclick="window.Telegram?.WebApp?.close()">Botga qaytish</button></div>`;
      return;
    }
    show('home');
  } catch (e) {
    $('#nav').hidden = true;
    view().innerHTML = `<div class="welcome"><div class="logo">${ico('close')}</div><h1>Ochilmadi</h1><p>${esc(e.message)}</p><button class="btn block" onclick="location.reload()">Qayta urinish</button></div>`;
  }
}
init();
