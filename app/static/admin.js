/* Kitobxon WebApp — admin panel (alohida bo'lim). app.js dan keyin yuklanadi. */
Object.assign(P, {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.500"/><rect x="14" y="3" width="7" height="7" rx="1.500"/><rect x="3" y="14" width="7" height="7" rx="1.500"/><rect x="14" y="14" width="7" height="7" rx="1.500"/>',
  chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  send: '<path d="M21 3 10 14M21 3l-7 18-4-7-7-4z"/>',
  ban: '<circle cx="12" cy="12" r="9"/><path d="m5.600 5.600 12.800 12.800"/>',
  upload: '<path d="M12 16V4m0 0L8 8m4-4 4 4M4 15v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16zM13.500 6.500l4 4"/>',
  out: '<path d="M10 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h5M15 8l4 4-4 4M19 12H9"/>',
  wallet: '<path d="M4 7a2 2 0 0 1 2-2h12v4M4 7v10a2 2 0 0 0 2 2h14V9H6a2 2 0 0 1-2-2zM16 14h2"/>',
});

const ADMIN_TABS = [
  ['menu', 'Menyu', 'grid'],
  ['stats', 'Statistika', 'chart'],
  ['users', 'A‘zolar', 'users'],
  ['orders', 'Buyurtmalar', 'box'],
  ['exit', 'Asosiy', 'home'],
];
const TAB_OF = { stats: 'stats', users: 'users', orders: 'orders' };
const adminTabOf = p => TAB_OF[p] || 'menu';

function enterAdmin() { showAdmin('menu'); }
function exitAdmin() {
  state.mode = 'user';
  delete document.documentElement.dataset.mode;
  show('home');
}

async function showAdmin(page = 'menu') {
  if (state.mode !== 'admin') { state.mode = 'admin'; document.documentElement.dataset.mode = 'admin'; }
  state.apage = page;
  closeOverlay(); renderNav();
  $('#nav').hidden = false;
  view().classList.remove('no-nav');
  view().innerHTML = skeleton('list');
  window.scrollTo(0, 0);
  tg?.BackButton?.show();
  try { await APAGES[page](); }
  catch (e) { view().innerHTML = abar('Xatolik') + empty('close', 'Sahifa ochilmadi', e.message); }
}

function abar(title, sub = 'Admin paneli', right = '') {
  const back = state.apage !== 'menu';
  return `<div class="appbar"><div class="row" style="gap:12px;min-width:0">
    ${back ? `<button class="icon-btn" data-act="apage" data-id="menu" aria-label="Menyuga qaytish">${ico('back')}</button>` : ''}
    <div style="min-width:0"><div class="sub">${esc(sub)}</div><h1>${esc(title)}</h1></div></div>${right}</div>`;
}
const aload = () => '<div class="skel" style="height:120px;margin-bottom:12px"></div><div class="skel" style="height:120px"></div>';
const badge = n => n ? `<span class="badge">${fmt(n)}</span>` : '';

/* ---------- menyu ---------- */
const MENU = [
  ['stats', 'Statistika', 'Umumiy ko‘rsatkichlar', 'chart'],
  ['users', 'Foydalanuvchilar', 'Qidirish va boshqarish', 'users'],
  ['books', 'Kitoblarni boshqarish', 'Tahrirlash, yashirish', 'book'],
  ['addpdf', 'Kitob qo‘shish', 'PDF fayldan', 'upload'],
  ['giftadd', 'Sovg‘a qo‘shish', 'Yangi sovg‘a', 'plus'],
  ['gifts', 'Sovg‘alarni boshqarish', 'Narx, ombor, holat', 'gift'],
  ['orders', 'Buyurtmalar', 'Tasdiqlash va rad etish', 'box', 'pending_orders'],
  ['coins', 'Tangalarni boshqarish', 'Qo‘shish yoki ayirish', 'wallet'],
  ['broadcast', 'Xabar yuborish', 'Barcha foydalanuvchilarga', 'send'],
  ['banned', 'Banlangan foydalanuvchilar', 'Blokdan chiqarish', 'ban', 'banned'],
];
const APAGES = {};
APAGES.menu = async () => {
  const st = await api('/api/admin/stats').catch(() => ({}));
  view().innerHTML = abar('Boshqaruv', 'Admin paneli', `<button class="btn sm soft" data-act="apage" data-id="exit">${ico('out')}Chiqish</button>`) + `
    <div class="amini">
      <div><b class="num">${fmt(st.users)}</b><span>foydalanuvchi</span></div>
      <div><b class="num">${fmt(st.new_today)}</b><span>bugun qo‘shildi</span></div>
      <div><b class="num">${fmt(st.pending_orders)}</b><span>yangi buyurtma</span></div>
    </div>
    <div class="menu-grid">${MENU.map(([id, t, d, ic, key]) => `
      <button class="menu-tile" data-act="apage" data-id="${id}"><span class="mi">${ico(ic)}${badge(st[key])}</span><b>${t}</b><small>${d}</small></button>`).join('')}
    </div>
    <button class="card row" style="width:100%;text-align:left;margin-top:14px" data-act="apage" data-id="exit"><span class="avatar">${ico('home')}</span><div class="grow"><b>Asosiy menyu</b><p class="muted small">Foydalanuvchi paneliga qaytish</p></div>${ico('next')}</button>`;
};

/* ---------- statistika ---------- */
APAGES.stats = async () => {
  const s = await api('/api/admin/stats');
  const max = Math.max(1, ...s.registrations.map(d => d.count));
  const rate = s.quizzes ? Math.round(s.quizzes_passed / s.quizzes * 100) : 0;
  const WD = ['Yak', 'Dush', 'Sesh', 'Chor', 'Pay', 'Jum', 'Shan'];
  const wd = iso => WD[new Date(iso + 'T00:00:00').getDay()];
  view().innerHTML = abar('Statistika') + `
    <div class="kpis">
      <div class="card kpi"><b class="num">${fmt(s.users)}</b><span>Foydalanuvchilar</span></div>
      <div class="card kpi"><b class="num">${fmt(s.active_week)}</b><span>7 kunda faol</span></div>
      <div class="card kpi"><b class="num">${fmt(s.new_today)}</b><span>Bugun qo‘shilgan</span></div>
      <div class="card kpi"><b class="num" style="color:${s.banned ? 'var(--danger)' : 'inherit'}">${fmt(s.banned)}</b><span>Banlangan</span></div>
    </div>
    <div class="section-title"><h2>Yangi foydalanuvchilar</h2><span class="muted small">oxirgi 7 kun</span></div>
    <div class="card"><div class="chart">${s.registrations.map(d => `<div class="col"><span class="v num">${d.count}</span><i style="height:${Math.max(4, d.count / max * 100)}%"></i><span class="d">${wd(d.date)}</span></div>`).join('')}</div></div>
    <div class="section-title"><h2>Faollik</h2></div>
    <div class="kpis">
      <div class="card kpi"><b class="num">${fmt(s.pages_total)}</b><span>O‘qilgan sahifalar</span></div>
      <div class="card kpi"><b class="num">${fmt(s.coins_total)}</b><span>Muomaladagi tangalar</span></div>
      <div class="card kpi"><b class="num">${fmt(s.quizzes)}</b><span>Topshirilgan testlar</span></div>
      <div class="card kpi"><b class="num">${rate}%</b><span>Testdan o‘tganlar</span></div>
    </div>
    <div class="section-title"><h2>Kontent</h2></div>
    <div class="kpis">
      <div class="card kpi"><b class="num">${fmt(s.active_books)}<small class="muted" style="font-size:16px">/${fmt(s.books)}</small></b><span>Faol kitoblar</span></div>
      <div class="card kpi"><b class="num">${fmt(s.gifts)}</b><span>Sovg‘alar</span></div>
      <div class="card kpi"><b class="num" style="color:${s.pending_orders ? 'var(--gold-deep)' : 'inherit'}">${fmt(s.pending_orders)}</b><span>Kutilayotgan buyurtma</span></div>
      <div class="card kpi"><b class="num">${fmt(s.approved_orders)}</b><span>Tasdiqlangan buyurtma</span></div>
    </div>`;
};

/* ---------- foydalanuvchilar ---------- */
function userListPage({ title, mode, banned, hint, placeholder = 'Ism, telefon yoki Telegram ID' }) {
  return async () => {
    view().innerHTML = abar(title) + (hint ? `<p class="muted small" style="margin:-6px 2px 14px">${hint}</p>` : '') +
      `<label class="search">${ico('search')}<input id="uq" type="search" placeholder="${placeholder}" autocomplete="off"></label>
       <div id="ucount" class="muted small" style="margin:0 2px 10px"></div><div id="ulist" class="stack"></div><div id="umore"></div>`;
    const ctx = { q: '', offset: 0, items: [] };
    const load = async (reset) => {
      if (reset) { ctx.offset = 0; ctx.items = []; $('#ulist').innerHTML = '<div class="skel" style="height:70px"></div><div class="skel" style="height:70px"></div>'; }
      const qs = new URLSearchParams({ search: ctx.q, limit: 30, offset: ctx.offset });
      if (banned !== undefined) qs.set('banned', banned);
      const r = await api('/api/admin/users?' + qs);
      ctx.items = ctx.items.concat(r.items); ctx.offset = ctx.items.length;
      state.ausers = ctx.items;
      $('#ucount').textContent = r.total ? `Jami: ${fmt(r.total)} ta` : '';
      $('#ulist').innerHTML = ctx.items.length ? ctx.items.map(u => userRow(u, mode)).join('')
        : empty(banned ? 'ban' : 'users', banned ? 'Banlangan foydalanuvchi yo‘q' : 'Hech kim topilmadi', banned ? 'Bloklangan foydalanuvchilar shu yerda ko‘rinadi.' : 'Boshqa so‘z bilan qidirib ko‘ring.');
      $('#umore').innerHTML = ctx.items.length < r.total ? '<button class="btn ghost block" style="margin-top:12px" data-act="a-more">Yana yuklash</button>' : '';
    };
    ctx.load = load; state.actx = ctx; state.aumode = mode;
    $('#uq').addEventListener('input', e => { clearTimeout(searchTimer); searchTimer = setTimeout(() => { ctx.q = e.target.value.trim(); load(true).catch(fail); }, 300); });
    await load(true);
  };
}
function userRow(u, mode) {
  const sub = [u.phone, u.region].filter(Boolean).join(' · ');
  return `<div class="card urow" data-act="a-user" data-id="${u.id}" role="button" tabindex="0">
    <span class="avatar">${esc(initial(u.first_name))}</span>
    <div class="grow"><b class="ellipsis" style="display:block">${esc(u.name)}${u.is_banned ? ' <span class="chip bad">Ban</span>' : ''}${u.is_admin ? ' <span class="chip">Admin</span>' : ''}</b>
      <span class="muted small ellipsis" style="display:block">${esc(sub || 'ID ' + u.telegram_id)}</span></div>
    ${mode === 'banned' ? `<button class="btn sm soft" data-act="a-unban" data-id="${u.id}">Blokdan chiqarish</button>`
      : `<span class="row" style="gap:6px;font-weight:750">${coin()}<span class="num">${fmt(u.coins)}</span></span>`}
  </div>`;
}
APAGES.users = userListPage({ title: 'Foydalanuvchilar', mode: 'users' });
APAGES.banned = userListPage({ title: 'Banlangan foydalanuvchilar', mode: 'banned', banned: true });
APAGES.coins = userListPage({ title: 'Tangalarni boshqarish', mode: 'coins', hint: 'Foydalanuvchini toping va tanga qo‘shing yoki ayiring.' });

function findUser(id) { return (state.ausers || []).find(x => x.id === id); }
function reloadUsers() { state.actx?.load(true).catch(fail); }

function openUser(id) {
  const u = findUser(id); if (!u) return;
  if (state.aumode === 'coins') return coinSheet(u);
  const rows = [['Telegram ID', u.telegram_id], ['Telefon', u.phone || '—'], ['Hudud', [u.region, u.district].filter(Boolean).join(', ') || '—'], ['Tangalar', fmt(u.coins)], ['O‘qilgan sahifalar', fmt(u.pages)], ['Ro‘yxatdan o‘tgan', fmtDate(u.created_at)]];
  const s = sheet({
    title: u.name,
    body: `${u.is_banned ? '<span class="chip bad" style="margin:6px 0">Banlangan</span>' : ''}<div class="kv">${rows.map(([k, v]) => `<div><span class="muted">${k}</span><b class="num">${esc(String(v))}</b></div>`).join('')}</div>`,
    actions: [{ id: 'coins', label: 'Tanga qo‘shish yoki ayirish', cls: 'btn block' },
      ...(u.is_admin ? [] : [{ id: 'ban', label: u.is_banned ? 'Blokdan chiqarish' : 'Foydalanuvchini bloklash', cls: 'btn block ' + (u.is_banned ? 'soft' : 'danger-soft') }])],
  });
  s.on('coins', () => { s.close(); coinSheet(u); });
  s.on('ban', () => { s.close(); toggleBan(u); });
}
async function toggleBan(u) {
  const ban = !u.is_banned;
  if (ban && !await confirmSheet({ title: `${u.name} bloklansinmi?`, text: 'Bloklangan foydalanuvchi bot va WebApp’dan foydalana olmaydi. Keyin blokdan chiqarishingiz mumkin.', ok: 'Bloklash', danger: true })) return;
  try { await post(`/api/admin/users/${u.id}/ban`, { banned: ban }); toast(ban ? 'Foydalanuvchi bloklandi' : 'Blokdan chiqarildi'); reloadUsers(); } catch (e) { fail(e); }
}
function coinSheet(u) {
  let sign = 1;
  const s = sheet({
    title: 'Tangalarni o‘zgartirish',
    body: `<p class="muted" style="margin-top:4px">${esc(u.name)} · hozirgi balans <b class="num">${fmt(u.coins)}</b></p>
      <div class="seg" style="margin:14px 0 4px"><button data-sign="1" aria-selected="true">Qo‘shish</button><button data-sign="-1" aria-selected="false">Ayirish</button></div>
      <div class="stack" style="margin-top:10px">
        <label class="field"><span>Miqdor</span><input class="input" id="c_amt" type="number" inputmode="numeric" min="1" placeholder="Masalan, 50"></label>
        <label class="field"><span>Sabab</span><input class="input" id="c_reason" placeholder="Masalan, tanlov g‘olibi"></label></div>`,
    actions: [{ id: 'no', label: 'Bekor qilish', cls: 'btn ghost' }, { id: 'ok', label: 'Saqlash' }],
  });
  s.el.addEventListener('click', e => {
    const b = e.target.closest('[data-sign]'); if (!b) return;
    sign = Number(b.dataset.sign); s.el.querySelectorAll('[data-sign]').forEach(x => x.setAttribute('aria-selected', x === b));
  });
  s.on('no', () => s.close());
  s.on('ok', async btn => {
    const n = Math.abs(parseInt($('#c_amt', s.el).value, 10));
    if (!n) return toast('Miqdorni kiriting', true);
    btn.disabled = true;
    try {
      const r = await post(`/api/admin/users/${u.id}/coins`, { amount: sign * n, reason: $('#c_reason', s.el).value.trim() });
      s.close(); toast(`Yangi balans: ${fmt(r.coins)} tanga`); reloadUsers();
    } catch (e) { btn.disabled = false; fail(e); }
  });
}

/* ---------- kitoblar ---------- */
APAGES.books = async () => {
  const list = await api('/api/admin/books'); state.abooks = list;
  view().innerHTML = abar('Kitoblarni boshqarish') + `
    <div class="row" style="gap:8px;margin-bottom:12px"><button class="btn sm grow" data-act="apage" data-id="addpdf">${ico('upload')}PDF qo‘shish</button><button class="btn sm soft grow" data-act="a-addbook">${ico('plus')}Qo‘lda qo‘shish</button></div>
    <label class="search">${ico('search')}<input id="bq" type="search" placeholder="Kitob nomi yoki muallif" autocomplete="off"></label>
    <div id="blist" class="stack"></div>`;
  const draw = q => {
    const r = state.abooks.filter(b => !q || (b.title + ' ' + b.author).toLowerCase().includes(q.toLowerCase()));
    $('#blist').innerHTML = r.map(b => `<div class="card admin-item"><div class="row" style="align-items:flex-start"><div style="width:44px;flex:none">${cover(b)}</div>
      <div class="grow"><b>${esc(b.title)}</b><div class="muted small">${esc(b.author)} · ${b.total_pages} sahifa</div></div><span class="chip ${b.is_active ? 'ok' : 'warn'}">${b.is_active ? 'Faol' : 'Yashirin'}</span></div>
      <div class="acts"><button class="btn sm soft" data-act="a-bookedit" data-id="${b.id}">${ico('edit')}Tahrirlash</button><button class="btn sm soft" data-act="a-page" data-id="${b.id}" data-total="${b.total_pages}">Sahifa matni</button><button class="btn sm ghost" data-act="a-booktoggle" data-id="${b.id}" data-on="${!b.is_active}">${b.is_active ? 'Yashirish' : 'Faollashtirish'}</button></div></div>`).join('') || empty('book', 'Kitob topilmadi', 'PDF yuklab birinchi kitobni qo‘shing.');
  };
  draw('');
  $('#bq').addEventListener('input', e => draw(e.target.value.trim()));
};
async function adminAddBook() {
  const v = await formSheet({ title: 'Yangi kitob', fields: [{ name: 'title', label: 'Nomi' }, { name: 'author', label: 'Muallif' }, { name: 'description', label: 'Tavsif', type: 'textarea' }, { name: 'pages', label: 'Sahifalar soni', type: 'number', min: 1 }] });
  if (!v) return;
  try { await post('/api/admin/books', { title: v.title, author: v.author, description: v.description, total_pages: v.pages }); toast('Kitob qo‘shildi'); showAdmin('books'); } catch (e) { fail(e); }
}
async function adminEditBook(id) {
  const b = state.abooks.find(x => x.id === id); if (!b) return;
  const v = await formSheet({ title: 'Kitobni tahrirlash', fields: [{ name: 'title', label: 'Nomi', value: b.title }, { name: 'author', label: 'Muallif', value: b.author }, { name: 'description', label: 'Tavsif', type: 'textarea', value: b.description }] });
  if (!v) return;
  try { await api(`/api/admin/books/${id}`, { method: 'PATCH', body: JSON.stringify(v) }); toast('Saqlandi'); showAdmin('books'); } catch (e) { fail(e); }
}
async function adminPage(id, total) {
  const v = await formSheet({ title: 'Sahifa matni', fields: [{ name: 'n', label: `Sahifa raqami (1–${total})`, type: 'number', value: '1', min: 1 }, { name: 'content', label: 'Matn', type: 'textarea' }] });
  if (!v) return;
  const n = Number(v.n);
  if (!n || n < 1 || n > total) return toast('Sahifa raqami noto‘g‘ri', true);
  try { await api(`/api/admin/books/${id}/pages/${n}`, { method: 'PUT', body: JSON.stringify({ content: v.content }) }); toast('Sahifa saqlandi'); } catch (e) { fail(e); }
}

APAGES.addpdf = async () => {
  view().innerHTML = abar('Kitob qo‘shish', 'PDF fayldan') + `
    <div id="pdfform" class="stack">
      <label class="drop" id="drop" for="pdffile">${ico('upload')}<b id="dropt">PDF faylni tanlang</b><span class="muted small" id="drops">20 MB gacha. Har bir sahifa matni alohida o‘qiladi.</span></label>
      <input id="pdffile" type="file" accept="application/pdf" hidden>
      <label class="field"><span>Kitob nomi</span><input class="input" id="pt" placeholder="Masalan, O‘tkan kunlar"></label>
      <label class="field"><span>Muallif</span><input class="input" id="pa" placeholder="Muallif ismi"></label>
      <label class="field"><span>Tavsif</span><textarea class="input" id="pd" placeholder="Kitob haqida qisqacha"></textarea></label>
      <div id="pprog" class="bar on-card" hidden><i style="width:0"></i></div>
      <button class="btn block" id="pgo" data-act="a-pdfgo">${ico('upload')}Yuklash</button>
    </div>`;
  $('#pdffile').addEventListener('change', e => {
    const f = e.target.files[0]; if (!f) return;
    $('#dropt').textContent = f.name; $('#drops').textContent = (f.size / 1048576).toFixed(1) + ' MB';
    $('#drop').classList.add('has');
    if (!$('#pt').value) $('#pt').value = f.name.replace(/\.pdf$/i, '').replace(/[_-]+/g, ' ');
  });
};
function uploadPdf() {
  const f = $('#pdffile').files[0], title = $('#pt').value.trim();
  if (!f) return toast('PDF faylni tanlang', true);
  if (!title) return toast('Kitob nomini kiriting', true);
  if (f.size > 20 * 1048576) return toast('PDF hajmi 20 MB dan oshmasin', true);
  const fd = new FormData(); fd.append('file', f); fd.append('title', title); fd.append('author', $('#pa').value.trim()); fd.append('description', $('#pd').value.trim());
  const btn = $('#pgo'), bar = $('#pprog'); btn.disabled = true; bar.hidden = false; btn.textContent = 'Yuklanmoqda…';
  const x = new XMLHttpRequest();
  x.open('POST', '/api/admin/books/upload-pdf'); x.setRequestHeader('X-Telegram-Init-Data', initData);
  x.upload.onprogress = e => { if (e.lengthComputable) bar.firstElementChild.style.width = Math.min(95, e.loaded / e.total * 95) + '%'; };
  x.onload = () => {
    let d = {}; try { d = JSON.parse(x.responseText); } catch { }
    if (x.status >= 200 && x.status < 300) {
      bar.firstElementChild.style.width = '100%'; notify('success');
      $('#pdfform').innerHTML = `<div class="card" style="text-align:center;padding:30px 20px"><div class="avatar xl" style="margin:0 auto 14px;background:var(--ok);">${ico('check')}</div><h2>Kitob qo‘shildi</h2><p class="muted" style="margin-top:6px">“${esc(title)}” · ${d.pages} sahifa</p></div>
        <button class="btn block" data-act="apage" data-id="addpdf">Yana kitob qo‘shish</button><button class="btn soft block" data-act="apage" data-id="books">Kitoblarni boshqarish</button>`;
    } else { btn.disabled = false; btn.innerHTML = `${ico('upload')}Yuklash`; bar.hidden = true; fail(Error(typeof d.detail === 'string' ? d.detail : 'PDF yuklanmadi')); }
  };
  x.onerror = () => { btn.disabled = false; btn.innerHTML = `${ico('upload')}Yuklash`; bar.hidden = true; fail(Error('Tarmoq xatosi. Qayta urinib ko‘ring.')); };
  x.send(fd);
}

/* ---------- sovg'alar ---------- */
APAGES.giftadd = async () => {
  view().innerHTML = abar('Sovg‘a qo‘shish') + `<div class="stack">
    <label class="field"><span>Sovg‘a nomi</span><input class="input" id="gn" placeholder="Masalan, Daftar to‘plami"></label>
    <label class="field"><span>Tavsif</span><textarea class="input" id="gd" placeholder="Sovg‘a haqida qisqacha"></textarea></label>
    <div class="row" style="gap:10px;align-items:flex-start"><label class="field grow"><span>Narxi (tanga)</span><input class="input" id="gp" type="number" inputmode="numeric" min="0" placeholder="200"></label>
    <label class="field grow"><span>Ombordagi soni</span><input class="input" id="gs" type="number" inputmode="numeric" min="0" placeholder="10"></label></div>
    <button class="btn block" data-act="a-giftsave">${ico('plus')}Sovg‘ani qo‘shish</button></div>`;
};
APAGES.gifts = async () => {
  const list = await api('/api/admin/gifts'); state.agifts = list;
  view().innerHTML = abar('Sovg‘alarni boshqarish') + `<button class="btn sm block" style="margin-bottom:12px" data-act="apage" data-id="giftadd">${ico('plus')}Sovg‘a qo‘shish</button>
    <div class="stack">${list.map(g => `<div class="card admin-item"><div class="row"><span class="avatar" style="background:var(--gold-soft);color:var(--gold-deep)">${ico('gift')}</span><div class="grow"><b>${esc(g.name)}</b><div class="muted small">${fmt(g.price)} tanga · omborda ${g.stock}</div></div><span class="chip ${g.is_active ? 'ok' : 'warn'}">${g.is_active ? 'Faol' : 'Yashirin'}</span></div>
      <div class="acts"><button class="btn sm soft" data-act="a-editgift" data-id="${g.id}">${ico('edit')}Tahrirlash</button><button class="btn sm ghost" data-act="a-gifttoggle" data-id="${g.id}" data-on="${!g.is_active}">${g.is_active ? 'Yashirish' : 'Faollashtirish'}</button><button class="btn sm danger-soft" data-act="a-giftdel" data-id="${g.id}">O‘chirish</button></div></div>`).join('') || empty('gift', 'Sovg‘a yo‘q', 'Birinchi sovg‘ani qo‘shing.')}</div>`;
};
async function adminEditGift(id) {
  const g = state.agifts.find(x => x.id === id); if (!g) return;
  const v = await formSheet({ title: 'Sovg‘ani tahrirlash', fields: [{ name: 'name', label: 'Nomi', value: g.name }, { name: 'description', label: 'Tavsif', type: 'textarea', value: g.description }, { name: 'price', label: 'Narxi (tanga)', type: 'number', value: g.price }, { name: 'stock', label: 'Ombordagi soni', type: 'number', value: g.stock }] });
  if (!v) return;
  try { await api(`/api/admin/gifts/${id}`, { method: 'PATCH', body: JSON.stringify({ name: v.name, description: v.description, price: Number(v.price), stock: Number(v.stock) }) }); toast('Saqlandi'); showAdmin('gifts'); } catch (e) { fail(e); }
}

/* ---------- buyurtmalar ---------- */
let orderFilter = 'pending';
APAGES.orders = async () => {
  const list = await api('/api/admin/orders'); state.aorders = list;
  const drawOrders = () => {
    const r = list.filter(o => orderFilter === 'all' || o.status === orderFilter);
    const st = { pending: ['warn', 'Kutilmoqda'], approved: ['ok', 'Tasdiqlangan'], rejected: ['bad', 'Rad etilgan'] };
    $('#olist').innerHTML = r.map(o => { const [c, l] = st[o.status] || ['', o.status]; return `<div class="card admin-item"><div class="row" style="align-items:flex-start"><div class="grow"><b>#${o.id} · ${esc(o.gift)}</b><div class="muted small">${esc(o.user)}${o.phone ? ' · ' + esc(o.phone) : ''}</div><div class="muted small">${fmt(o.price)} tanga · ${fmtDate(o.created_at)}</div></div><span class="chip ${c}">${l}</span></div>
      ${o.status === 'pending' ? `<div class="acts"><button class="btn sm" data-act="a-order" data-id="${o.id}" data-s="approved">${ico('check')}Tasdiqlash</button><button class="btn sm danger-soft" data-act="a-order" data-id="${o.id}" data-s="rejected">Rad etish</button></div>` : ''}</div>`; }).join('') || empty('box', 'Buyurtma yo‘q', 'Bu holatdagi buyurtmalar shu yerda ko‘rinadi.');
  };
  const f = [['pending', 'Kutilmoqda'], ['approved', 'Tasdiqlangan'], ['rejected', 'Rad etilgan'], ['all', 'Hammasi']];
  view().innerHTML = abar('Buyurtmalar') + `<div class="seg" id="ofilter">${f.map(([id, l]) => `<button data-of="${id}" aria-selected="${orderFilter === id}">${l}${id === 'pending' ? ' ' + list.filter(o => o.status === 'pending').length : ''}</button>`).join('')}</div><div id="olist" class="stack"></div>`;
  $('#ofilter').addEventListener('click', e => {
    const b = e.target.closest('[data-of]'); if (!b) return;
    orderFilter = b.dataset.of; $('#ofilter').querySelectorAll('button').forEach(x => x.setAttribute('aria-selected', x === b)); drawOrders();
  });
  drawOrders();
};

/* ---------- xabar yuborish ---------- */
APAGES.broadcast = async () => {
  const st = await api('/api/admin/stats');
  const n = st.users - st.banned;
  view().innerHTML = abar('Xabar yuborish', 'Barcha foydalanuvchilarga') + `<div class="stack">
    <div class="card row"><span class="avatar">${ico('users')}</span><div class="grow"><b class="num">${fmt(n)} ta qabul qiluvchi</b><p class="muted small">Banlangan foydalanuvchilarga yuborilmaydi.</p></div></div>
    <label class="field"><span>Xabar matni</span><textarea class="input" id="bt" maxlength="4000" style="min-height:160px" placeholder="Foydalanuvchilarga yuboriladigan xabarni yozing"></textarea></label>
    <div class="muted small" style="text-align:right;margin-top:-4px"><span id="bcount">0</span> / 4000</div>
    <div id="bprev" hidden><div class="muted small" style="margin:0 2px 6px">Foydalanuvchi shunday ko‘radi</div><div class="bubble" id="bbub"></div></div>
    <button class="btn block" data-act="a-bsend" data-n="${n}">${ico('send')}Xabarni yuborish</button></div>`;
  $('#bt').addEventListener('input', e => {
    const t = e.target.value; $('#bcount').textContent = t.length;
    $('#bprev').hidden = !t.trim(); $('#bbub').textContent = t;
  });
};
async function sendBroadcast(n) {
  const text = $('#bt').value.trim();
  if (!text) return toast('Xabar matnini kiriting', true);
  if (!await confirmSheet({ title: `${fmt(n)} kishiga yuborilsinmi?`, text: 'Xabar yuborilgach, uni qaytarib bo‘lmaydi. Yuborish tugagach sizga botda natija keladi.', ok: 'Yuborish' })) return;
  try {
    const r = await post('/api/admin/broadcast', { text });
    toast(`Yuborish boshlandi: ${fmt(r.recipients)} ta qabul qiluvchi`);
    $('#bt').value = ''; $('#bcount').textContent = '0'; $('#bprev').hidden = true;
  } catch (e) { fail(e); }
}

/* ---------- harakatlar ---------- */
const reloadPage = () => showAdmin(state.apage);
Object.assign(actions, {
  'admin-enter': enterAdmin,
  apage: d => { haptic(); d.id === 'exit' ? exitAdmin() : showAdmin(d.id); },
  'a-user': d => openUser(Number(d.id)),
  'a-unban': async d => { const u = findUser(Number(d.id)); if (u) toggleBan(u); },
  'a-more': async () => { try { state.actx.load(false); } catch (e) { fail(e); } },
  'a-addbook': adminAddBook,
  'a-bookedit': d => adminEditBook(Number(d.id)),
  'a-page': d => adminPage(Number(d.id), Number(d.total)),
  'a-booktoggle': async d => { try { await api(`/api/admin/books/${d.id}`, { method: 'PATCH', body: JSON.stringify({ is_active: d.on === 'true' }) }); toast(d.on === 'true' ? 'Kitob faollashtirildi' : 'Kitob yashirildi'); reloadPage(); } catch (e) { fail(e); } },
  'a-pdfgo': uploadPdf,
  'a-giftsave': async () => {
    const name = $('#gn').value.trim(); if (!name) return toast('Sovg‘a nomini kiriting', true);
    try { await post('/api/admin/gifts', { name, description: $('#gd').value.trim(), price: Number($('#gp').value || 0), stock: Number($('#gs').value || 0) }); toast('Sovg‘a qo‘shildi'); showAdmin('gifts'); } catch (e) { fail(e); }
  },
  'a-editgift': d => adminEditGift(Number(d.id)),
  'a-gifttoggle': async d => { try { await api(`/api/admin/gifts/${d.id}`, { method: 'PATCH', body: JSON.stringify({ is_active: d.on === 'true' }) }); reloadPage(); } catch (e) { fail(e); } },
  'a-giftdel': async d => { if (!await confirmSheet({ title: 'Sovg‘ani o‘chirasizmi?', text: 'Buyurtma tarixi bo‘lsa, sovg‘a o‘chirilmay, yashiriladi.', ok: 'O‘chirish', danger: true })) return; try { const r = await api(`/api/admin/gifts/${d.id}`, { method: 'DELETE' }); toast(r.message || 'Sovg‘a o‘chirildi'); reloadPage(); } catch (e) { fail(e); } },
  'a-order': async d => { try { await post(`/api/admin/orders/${d.id}/${d.s}`); toast(d.s === 'approved' ? 'Buyurtma tasdiqlandi' : 'Buyurtma rad etildi'); reloadPage(); } catch (e) { fail(e); } },
  'a-bsend': d => sendBroadcast(Number(d.n)),
});
