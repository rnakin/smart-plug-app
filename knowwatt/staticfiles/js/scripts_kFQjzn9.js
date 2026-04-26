// ═══════════════════════════════════════════════════════════════════════════
// SHARED JAVASCRIPT FOR KNOWWATT APPLICATION
// ═══════════════════════════════════════════════════════════════════════════

// ── Auth ──────────────────────────────────────────────────────────────────────
const token = localStorage.getItem('access');
if (!token) window.location = '/login/';

fetch('/auth/me/', { headers: { 'Authorization': 'Bearer ' + token } })
  .then(res => { if (res.status === 401) { localStorage.clear(); window.location = '/login/'; } return res.json(); })
  .then(data => {
    if (!data?.username) return;
    document.getElementById('avatar-initials').textContent = data.username.slice(0,1).toUpperCase();
    document.getElementById('username').textContent = data.username;
  }).catch(() => {});

// ── Theme ─────────────────────────────────────────────────────────────────────
function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  html.setAttribute('data-theme', isDark ? 'light' : 'dark');
  localStorage.setItem('theme', isDark ? 'light' : 'dark');
}
document.documentElement.setAttribute('data-theme', localStorage.getItem('theme') || 'dark');

// ── API helpers ───────────────────────────────────────────────────────────────
async function apiGet(url) {
  const res = await fetch(url, { headers: { 'Authorization': 'Bearer ' + token } });
  if (res.status === 401) { localStorage.clear(); window.location = '/login/'; }
  return res.json();
}
async function apiPost(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
    body: JSON.stringify(body),
  });
  return { ok: res.ok, status: res.status, data: await res.json() };
}

// ── Page initialization (called on each page load) ─────────────────────────────
// Each page has its own initialization function defined in its template

// ── Shared state ──────────────────────────────────────────────────────────────
let houses = [], currentPlugs = [], activeHouseId = null, activeHouseName = '', activeHouseRole = '';

function setActiveHouse(id, name, role) {
  activeHouseId = id; activeHouseName = name; activeHouseRole = role;
  loadPlugs(); loadAlertPills(); loadEnergyStats();
}

// ── Alert badge ───────────────────────────────────────────────────────────────
async function refreshAlertBadge() {
  if (!activeHouseId) return;
  try {
    const data = await apiGet(`/api/houses/${activeHouseId}/alerts/events/?status=pending&limit=1`);
    const badge = document.getElementById('alert-badge');
    if (data.total > 0) { badge.style.display = 'block'; badge.textContent = data.total > 9 ? '9+' : data.total; }
    else badge.style.display = 'none';
  } catch (e) {}
}
setInterval(refreshAlertBadge, 30000);

// ══════════════════════════════════════════════════════════════════
// PAGE: HOME
// ══════════════════════════════════════════════════════════════════
async function loadHouses() {
  try {
    houses = await apiGet('/api/houses/');
    renderHouseTabs();
    if (houses.length > 0) {
      const h = houses[0];
      setActiveHouse(h.id, h.house_name, h.role);
    } else {
      document.getElementById('live-status').textContent = 'ยังไม่มีบ้าน — เพิ่มบ้านเพื่อเริ่มต้น';
    }
  } catch (e) {
    document.getElementById('live-status').textContent = 'ไม่สามารถเชื่อมต่อได้';
  }
}

function renderHouseTabs() {
  const container = document.getElementById('house-row').parentElement;
  // Remove existing htabs (but keep the htab-add button)
  container.querySelectorAll('.htab').forEach(t => t.remove());
  const addBtn = container.querySelector('.htab-add');
  houses.forEach((h, i) => {
    const tab = document.createElement('div');
    tab.className = 'htab' + (i === 0 ? ' active' : '');
    tab.dataset.id = h.id;
    tab.textContent = (h.emoji || '🏠') + ' ' + h.house_name;
    tab.onclick = function() { selectHouseTab(h.id, h.house_name, h.role, this); };
    container.insertBefore(tab, addBtn);
  });
}

function selectHouseTab(id, name, role, el) {
  document.querySelectorAll('#page-home .htab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  setActiveHouse(id, name, role);
}

async function loadPlugs() {
  if (!activeHouseId) return;
  try {
    currentPlugs = await apiGet(`/api/houses/${activeHouseId}/plugs/`);
    renderDigitalTwin();
    document.getElementById('house-role-badge').textContent = { owner:'เจ้าของ', admin:'ผู้ดูแล', member:'สมาชิก', guest:'แขก' }[activeHouseRole] || activeHouseRole;
  } catch (e) {}
}

// ── Digital Twin ──────────────────────────────────────────────────────────────
let twinEditMode = false;
let selectedPlugForDrawer = null;
const roomTints = {
  'ครัว':'rgba(255,130,0,.055)', 'ห้องนอน':'rgba(100,100,255,.055)',
  'ห้องนั่งเล่น':'rgba(0,180,100,.055)', 'ห้องน้ำ':'rgba(0,180,255,.055)',
  'ระเบียง':'rgba(60,200,60,.055)', 'ห้องซัก':'rgba(0,200,220,.055)',
  'ห้องทำงาน':'rgba(160,100,255,.055)', 'โรงรถ':'rgba(160,160,160,.055)',
};
const roomEmoji = {
  'ครัว':'🍳','ห้องนอน':'🛏','ห้องนั่งเล่น':'🛋','ห้องน้ำ':'🚿',
  'ระเบียง':'🌿','ห้องซัก':'🫧','ห้องทำงาน':'💻','โรงรถ':'🚗',
};
const riskLabel = { high:'สูง', medium:'ปานกลาง', low:'ต่ำ' };
const riskClass = { high:'r-high', medium:'r-med', low:'r-low' };

// Rooms are stored in localStorage per house: { houseId: [{id,name,emoji,x,y,w,h}] }
function getRoomStore() {
  try { return JSON.parse(localStorage.getItem('twin-rooms') || '{}'); } catch { return {}; }
}
function saveRoomStore(store) {
  localStorage.setItem('twin-rooms', JSON.stringify(store));
}
function getHouseRooms() {
  if (!activeHouseId) return [];
  return getRoomStore()[activeHouseId] || [];
}
function saveHouseRooms(rooms) {
  const store = getRoomStore();
  store[activeHouseId] = rooms.map(r => ({ id: r.id, name: r.name, emoji: r.emoji, x: r.x, y: r.y, w: r.w, h: r.h }));
  saveRoomStore(store);
}

let twinRooms = []; // [{id, name, emoji, x, y, w, h, plugs:[]}]

function buildTwinRooms() {
  const savedRooms = getHouseRooms();
  // Group plugs by location
  const groups = {};
  currentPlugs.forEach(plug => {
    const loc = plug.location || 'ไม่ระบุ';
    if (!groups[loc]) groups[loc] = [];
    groups[loc].push(plug);
  });

  const canvas = document.getElementById('twin-canvas');
  const cw = canvas.clientWidth || 800;
  const cols = 3, pad = 20;
  const w = Math.floor((cw - pad * (cols + 1)) / cols);
  const h = 175;

  // Merge saved rooms + rooms from plug locations
  const allRoomNames = new Set([
    ...savedRooms.map(r => r.name),
    ...Object.keys(groups),
  ]);

  let idx = 0;
  twinRooms = Array.from(allRoomNames).map(name => {
    const saved = savedRooms.find(r => r.name === name);
    const col = idx % cols, row = Math.floor(idx / cols);
    idx++;
    return {
      id: saved ? saved.id : 'room-' + name.replace(/\s/g,'_') + '-' + Date.now(),
      name,
      emoji: roomEmoji[name] || '🏠',
      x: saved ? saved.x : pad + col * (w + pad),
      y: saved ? saved.y : pad + row * (h + pad),
      w: saved ? saved.w : w,
      h: saved ? saved.h : h,
      plugs: groups[name] || [],
    };
  });
}

function renderDigitalTwin() {
  buildTwinRooms();
  saveHouseRooms(twinRooms);
  const canvas = document.getElementById('twin-canvas');
  canvas.querySelectorAll('.room-block').forEach(e => e.remove());
  const empty = document.getElementById('twin-empty');
  empty.classList.toggle('hide', twinRooms.length > 0);
  twinRooms.forEach(r => renderTwinRoom(r, canvas));
  document.getElementById('sb-p').textContent = currentPlugs.length;
}

function renderTwinRoom(r, canvas) {
  const el = document.createElement('div');
  el.className = 'room-block';
  el.id = r.id;
  el.style.cssText = `left:${r.x}px;top:${r.y}px;width:${r.w}px;height:${r.h}px;`;
  if (roomTints[r.name]) el.style.background = roomTints[r.name];

  const plugsHTML = r.plugs.map(p => {
    const isOn = p.is_on;
    const isOnline = p.online_status === 'online';
    const cls = !isOnline ? 'off' : isOn ? 'on' : 'off';
    const emoji = p.device_emoji || '';
    const deviceLabel = p.device_name ? `<div class="pwatt" style="color:var(--text3);font-size:7px;">${p.device_name}</div>` : '';
    return `
      <div class="plug-node ${cls}" onclick="openPlugDetailDrawer('${p.id}')">
        <div class="pico">${emoji}<div class="pring"></div></div>
        <div class="pname">${p.name}</div>
        ${deviceLabel}
        <div class="pwatt">${isOn && p.current_power_w != null ? p.current_power_w.toFixed(0)+'W' : '—'}</div>
        <div class="ptip">${p.name}${p.device_name ? ' · '+p.device_name : ''} · ${p.plug_code}</div>
      </div>`;
  }).join('');

  el.innerHTML = `
    <div class="rbar${twinEditMode ? ' editable' : ''}" data-id="${r.id}">
      <div class="rlabel"><span class="em">${r.emoji}</span><span>${r.name}</span></div>
      <div class="ract" style="opacity:1;">
        <button class="ract-btn" onclick="event.stopPropagation();openRoomConfig('${r.id}')" title="ตั้งค่าห้อง">⚙</button>
        <button class="ract-btn del" onclick="event.stopPropagation();deleteRoom('${r.id}')" title="ลบห้อง">✕</button>
      </div>
    </div>
    <div class="rbody">
      ${plugsHTML}
    </div>
    <div class="rresize" data-r="${r.id}"></div>`;
  canvas.appendChild(el);
  makeTwinDrag(el, r);
  makeTwinResize(el, r);
}

async function apiPatch(url, body) {
  const res = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
    body: JSON.stringify(body),
  });
  return { ok: res.ok, data: await res.json() };
}

function deleteRoom(roomId) {
  const room = twinRooms.find(r => r.id === roomId);
  if (!room) return;
  if (room.plugs.length > 0 && !confirm(`ลบห้อง "${room.name}"? ปลั๊กในห้องจะถูกย้ายไปที่ "ไม่ระบุ"`)) return;
  // Move plugs to 'ไม่ระบุ' via PATCH
  const movePromises = room.plugs.map(p =>
    apiPatch(`/api/houses/${activeHouseId}/plugs/${p.id}/`, { location: '' }).catch(() => {})
  );
  Promise.all(movePromises).then(() => {
    twinRooms = twinRooms.filter(r => r.id !== roomId);
    saveHouseRooms(twinRooms);
    loadPlugs();
  });
}

// ── Room Config ───────────────────────────────────────────────────────────────
let _configRoomId = null;

function openRoomConfig(roomId) {
  const room = twinRooms.find(r => r.id === roomId);
  if (!room) return;
  _configRoomId = roomId;
  document.getElementById('d-room-config-title').textContent = room.emoji + ' ' + room.name;
  document.getElementById('room-config-name').value = room.name;
  // List plugs in this room
  const plugsDiv = document.getElementById('room-config-plugs');
  if (room.plugs.length === 0) {
    plugsDiv.innerHTML = '<div style="font-size:12px;color:var(--text3);padding:8px 0;">ยังไม่มีปลั๊กในห้องนี้</div>';
  } else {
    plugsDiv.innerHTML = room.plugs.map(p => `
      <div style="display:flex;align-items:center;gap:8px;padding:8px 10px;background:var(--surface3);border-radius:8px;">
        <span style="font-size:16px;">${p.device_emoji || ''}</span>
        <div style="flex:1;">
          <div style="font-size:12px;font-weight:500;">${p.name}</div>
          ${p.device_name ? `<div style="font-size:10px;color:var(--text3);">${p.device_name}</div>` : ''}
        </div>
        <div style="width:8px;height:8px;border-radius:50%;background:${p.is_on ? 'var(--accent)' : 'var(--text3)'};" title="${p.is_on ? 'เปิด' : 'ปิด'}"></div>
      </div>`).join('');
  }
  openTwinDrawer('d-room-config');
}

function saveRoomConfig() {
  const newName = document.getElementById('room-config-name').value.trim();
  if (!newName) return;
  const room = twinRooms.find(r => r.id === _configRoomId);
  if (!room) return;
  const oldName = room.name;
  if (newName === oldName) { closeTwinDrawer(); return; }
  // Rename: update room + PATCH all plugs in this room
  room.name = newName;
  room.emoji = roomEmoji[newName] || room.emoji;
  saveHouseRooms(twinRooms);
  const patches = room.plugs.map(p =>
    apiPatch(`/api/houses/${activeHouseId}/plugs/${p.id}/`, { location: newName }).catch(() => {})
  );
  Promise.all(patches).then(() => { closeTwinDrawer(); loadPlugs(); });
}

function deleteRoomFromConfig() {
  if (_configRoomId) { closeTwinDrawer(); deleteRoom(_configRoomId); }
}

function makeTwinDrag(el, r) {
  const bar = el.querySelector('.rbar');
  bar.addEventListener('mousedown', e => {
    if (!twinEditMode || e.target.closest('.ract')) return;
    e.preventDefault();
    const sx = e.clientX, sy = e.clientY, ox = r.x, oy = r.y;
    el.classList.add('dragging');
    const mv = e => { r.x = Math.max(0, ox + e.clientX - sx); r.y = Math.max(0, oy + e.clientY - sy); el.style.left = r.x + 'px'; el.style.top = r.y + 'px'; };
    const up = () => { el.classList.remove('dragging'); saveHouseRooms(twinRooms); document.removeEventListener('mousemove', mv); document.removeEventListener('mouseup', up); };
    document.addEventListener('mousemove', mv);
    document.addEventListener('mouseup', up);
  });
}

function makeTwinResize(el, r) {
  const handle = el.querySelector('.rresize');
  handle.addEventListener('mousedown', e => {
    if (!twinEditMode) return;
    e.preventDefault(); e.stopPropagation();
    const sx = e.clientX, sy = e.clientY, sw = r.w, sh = r.h;
    const mv = e => { r.w = Math.max(140, sw + e.clientX - sx); r.h = Math.max(110, sh + e.clientY - sy); el.style.width = r.w + 'px'; el.style.height = r.h + 'px'; };
    const up = () => { saveHouseRooms(twinRooms); document.removeEventListener('mousemove', mv); document.removeEventListener('mouseup', up); };
    document.addEventListener('mousemove', mv);
    document.addEventListener('mouseup', up);
  });
}

function toggleTwinEdit() {
  twinEditMode = !twinEditMode;
  document.getElementById('btn-edit').classList.toggle('on', twinEditMode);
  document.getElementById('twin-mode-lbl').textContent = twinEditMode ? 'EDIT MODE — ลากห้องได้เลย' : 'VIEW MODE';
  renderDigitalTwin();
}

function autoArrangeTwin() {
  // Clear saved positions so they recalculate
  const store = getRoomStore();
  if (activeHouseId) delete store[activeHouseId];
  saveRoomStore(store);
  twinRooms = [];
  renderDigitalTwin();
}

// ── Room Drawer ───────────────────────────────────────────────────────────────
function openTwinDrawer(id) {
  closeTwinDrawer();
  document.getElementById('twin-overlay').classList.add('open');
  document.getElementById(id).classList.add('open');
}
function closeTwinDrawer() {
  document.getElementById('twin-overlay').classList.remove('open');
  document.querySelectorAll('#d-add-room,#d-move-plug,#d-plug-detail,#d-room-config').forEach(d => d.classList.remove('open'));
}
function openAddRoomDrawer() {
  _selectedRoomType = null;
  const inp = document.getElementById('custom-room-name');
  inp.value = '';
  inp.dataset.auto = '';
  document.querySelectorAll('#d-add-room .ropt').forEach(o => o.style.borderColor = '');
  openTwinDrawer('d-add-room');
}

let _selectedRoomType = null;

function selectRoomType(name, emoji, el) {
  _selectedRoomType = { name, emoji };
  // Highlight selected
  document.querySelectorAll('#d-add-room .ropt').forEach(o => o.style.borderColor = '');
  el.style.borderColor = 'var(--accent)';
  // Fill name field
  const inp = document.getElementById('custom-room-name');
  if (!inp.value || inp.dataset.auto === '1') {
    inp.value = name;
    inp.dataset.auto = '1';
  }
}

function addRoomFromDrawer(name, emoji) {
  // Double-click: instantly create with this type (use custom name if filled)
  const inp = document.getElementById('custom-room-name');
  const finalName = inp.value.trim() || name;
  closeTwinDrawer();
  _addRoom(finalName, roomEmoji[finalName] || emoji);
}

function addRoomConfirm() {
  const inp = document.getElementById('custom-room-name');
  const name = inp.value.trim();
  if (!name) { inp.focus(); return; }
  const emoji = (_selectedRoomType && _selectedRoomType.name === name) ? _selectedRoomType.emoji : (roomEmoji[name] || '🏠');
  closeTwinDrawer();
  _addRoom(name, emoji);
}
function _addRoom(name, emoji) {
  if (twinRooms.find(r => r.name === name)) {
    alert(`ห้อง "${name}" มีอยู่แล้ว`); return;
  }
  const canvas = document.getElementById('twin-canvas');
  const cw = canvas.clientWidth || 800;
  const cols = 3, pad = 20;
  const w = Math.floor((cw - pad * (cols + 1)) / cols);
  const h = 175;
  const idx = twinRooms.length;
  const col = idx % cols, row = Math.floor(idx / cols);
  twinRooms.push({
    id: 'room-' + name.replace(/\s/g,'_') + '-' + Date.now(),
    name, emoji,
    x: pad + col * (w + pad),
    y: pad + row * (h + pad),
    w, h,
    plugs: [],
  });
  saveHouseRooms(twinRooms);
  renderDigitalTwin();
}

// ── Plug Detail Drawer ────────────────────────────────────────────────────────
function openPlugDetailDrawer(plugId) {
  const p = currentPlugs.find(x => x.id === plugId);
  if (!p) return;
  selectedPlugForDrawer = p;
  document.getElementById('dd-plug-title').textContent = (p.device_emoji || '') + ' ' + p.name;
  document.getElementById('dd-power').innerHTML = (p.current_power_w != null ? p.current_power_w.toFixed(0) : '—') + '<span class="dmu">W</span>';
  document.getElementById('dd-status').textContent = p.online_status === 'online' ? '🟢 ออนไลน์' : '⚫ ออฟไลน์';
  document.getElementById('dd-device').textContent = p.device_name ? (p.device_emoji || '') + ' ' + p.device_name : '— ไม่มีอุปกรณ์';
  const risk = p.device_risk;
  document.getElementById('dd-risk').innerHTML = risk ? `<span class="risk ${riskClass[risk]}">${riskLabel[risk]}</span>` : '—';
  document.getElementById('dd-code').textContent = p.plug_code;
  document.getElementById('dd-room').textContent = p.location || 'ไม่ระบุ';
  const tog = document.getElementById('dd-tog');
  const sw = document.getElementById('dd-sw');
  const st = document.getElementById('dd-st');
  tog.classList.toggle('on', p.is_on);
  sw.classList.toggle('on', p.is_on);
  st.textContent = p.is_on ? 'เปิดอยู่' : 'ปิดอยู่';
  openTwinDrawer('d-plug-detail');
}

async function togglePlugFromDrawer() {
  if (!selectedPlugForDrawer) return;
  const p = selectedPlugForDrawer;
  const { ok, data } = await apiPost(`/api/houses/${activeHouseId}/plugs/${p.id}/control/`, { action: p.is_on ? 'off' : 'on' });
  if (ok) {
    p.is_on = data.is_on;
    openPlugDetailDrawer(p.id); // refresh drawer
    renderDigitalTwin();
  }
}

// ── Move Plug Drawer ──────────────────────────────────────────────────────────
function openMovePlugDrawer() {
  if (!selectedPlugForDrawer) return;
  document.getElementById('d-move-plug-title').textContent = `ย้าย "${selectedPlugForDrawer.name}"`;
  const list = document.getElementById('move-room-list');
  list.innerHTML = twinRooms.map(r => `
    <div class="popt" onclick="movePlugToRoom('${r.name}')">
      <div class="popt-em">${r.emoji}</div>
      <div class="popt-info">
        <div class="popt-nm">${r.name}</div>
        <div class="popt-ds">${r.plugs.length} ปลั๊ก</div>
      </div>
      ${selectedPlugForDrawer.location === r.name ? '<span style="color:var(--accent);font-size:11px;">● ปัจจุบัน</span>' : ''}
    </div>`).join('');
  openTwinDrawer('d-move-plug');
}

async function movePlugToRoom(roomName) {
  if (!selectedPlugForDrawer) return;
  const p = selectedPlugForDrawer;
  const res = await fetch(`/api/houses/${activeHouseId}/plugs/${p.id}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
    body: JSON.stringify({ location: roomName }),
  });
  if (res.ok) {
    p.location = roomName;
    closeTwinDrawer();
    await loadPlugs();
  }
}

async function quickTogglePlug(plugId, currentState) {
  const { ok, data } = await apiPost(`/api/houses/${activeHouseId}/plugs/${plugId}/control/`, { action: currentState ? 'off' : 'on' });
  if (ok) {
    const plug = currentPlugs.find(p => p.id === plugId);
    if (plug) plug.is_on = data.is_on;
    renderDigitalTwin();
  }
}

async function togglePlug(plugId, currentState, event) {
  event.stopPropagation();
  await quickTogglePlug(plugId, currentState);
}

async function loadAlertPills() {
  if (!activeHouseId) return;
  try {
    const data = await apiGet(`/api/houses/${activeHouseId}/alerts/events/?status=pending&limit=3`);
    const zone = document.getElementById('alerts-zone');
    zone.innerHTML = '';
    document.getElementById('qs-alerts').textContent = data.total || '0';
    document.getElementById('sb-alerts').textContent = `${data.total || '0'} รายการ`;
    document.getElementById('live-status').textContent = data.total > 0 ? `มีการแจ้งเตือน ${data.total} รายการ` : 'ทุกอย่างปกติดี ✓';
    (data.results || []).forEach(ev => {
      const pill = document.createElement('div');
      pill.className = 'apill warn';
      pill.innerHTML = `<span>⚠️</span><span class="apill-txt">${ev.title}</span><span class="apill-act" onclick="acknowledgeAlert('${ev.id}',this)">รับทราบ →</span>`;
      zone.appendChild(pill);
    });
    refreshAlertBadge();
  } catch (e) {}
}

async function acknowledgeAlert(eventId, el) {
  const { ok } = await apiPost(`/api/houses/${activeHouseId}/alerts/events/${eventId}/action/`, { action: 'acknowledge' });
  if (ok) { el.closest('.apill').remove(); loadAlertPills(); }
}

async function loadEnergyStats() {
  if (!activeHouseId) return;
  try {
    const data = await apiGet(`/api/houses/${activeHouseId}/energy/dashboard/`);
    document.getElementById('qs-power').textContent = data.current_power_w?.toFixed(0) || '0';
    document.getElementById('sb-w').textContent = `${data.current_power_w?.toFixed(0) || '0'} W`;
    document.getElementById('sb-kwh').textContent = `${data.today_kwh?.toFixed(2) || '0'} kWh`;
    document.getElementById('qs-online').textContent = data.plugs?.filter(p => p.is_on).length || '0';
  } catch (e) {}
}

// ── Add Home ──────────────────────────────────────────────────────────────────
let displayAddHomePopup = false, selectedEmoji = '🏠', map = null, marker = null;

function selectEmoji(em) {
  selectedEmoji = em;
  document.getElementById('house_emoji').value = em;
  document.querySelectorAll('.emoji-btn').forEach(btn => {
    const match = btn.textContent.trim() === em;
    btn.style.borderColor = match ? 'var(--accent)' : 'var(--border)';
    btn.style.background  = match ? 'var(--accent-dim)' : 'var(--surface2)';
  });
}

function toggleAddHomePopup() {
  displayAddHomePopup = !displayAddHomePopup;
  document.getElementById('add-home-popup').style.display = displayAddHomePopup ? 'flex' : 'none';
  document.getElementById('popup-overlay').style.display  = displayAddHomePopup ? 'block' : 'none';
  if (displayAddHomePopup) {
    ['house_name','address','lat','lng'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('popup-error').textContent = '';
    document.getElementById('coords-display').textContent = 'คลิกบนแผนที่เพื่อปักหมุด';
    selectEmoji('🏠');
    setTimeout(initMap, 100);
  }
}

async function addHomeCommit() {
  const houseName = document.getElementById('house_name').value.trim();
  const address   = document.getElementById('address').value.trim();
  const lat       = document.getElementById('lat').value;
  const lng       = document.getElementById('lng').value;
  const emoji     = document.getElementById('house_emoji').value || '🏠';
  const errorEl   = document.getElementById('popup-error');
  const btn       = document.getElementById('add-home-btn');
  errorEl.textContent = '';
  if (!houseName) { errorEl.textContent = 'กรุณากรอกชื่อบ้าน'; return; }
  if (!address)   { errorEl.textContent = 'กรุณากรอกที่อยู่'; return; }
  btn.disabled = true; btn.textContent = 'กำลังเพิ่ม…';
  const { ok, data } = await apiPost('/api/houses/', { house_name: houseName, address, lat: lat ? parseFloat(lat) : null, long: lng ? parseFloat(lng) : null, emoji });
  btn.disabled = false; btn.textContent = 'เพิ่มบ้าน';
  if (ok) {
    houses.push(data);
    renderHouseTabs();
    toggleAddHomePopup();
    setActiveHouse(data.id, data.house_name, data.role);
    document.querySelectorAll('#page-home .htab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('#page-home .htab')[houses.length - 1]?.classList.add('active');
  } else {
    errorEl.textContent = data.error || 'เกิดข้อผิดพลาด';
  }
}

function initMap() {
  if (map) { map.invalidateSize(); return; }
  map = L.map('map').setView([13.7563, 100.5018], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap contributors' }).addTo(map);
  map.on('click', e => {
    const { lat, lng } = e.latlng;
    if (marker) marker.setLatLng(e.latlng); else marker = L.marker(e.latlng).addTo(map);
    document.getElementById('lat').value = lat.toFixed(6);
    document.getElementById('lng').value = lng.toFixed(6);
    document.getElementById('coords-display').textContent = `📍 ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
    document.getElementById('coords-display').style.color = 'var(--accent)';
  });
  if (navigator.geolocation) navigator.geolocation.getCurrentPosition(pos => map.setView([pos.coords.latitude, pos.coords.longitude], 14));
}

// ── Add Plug ──────────────────────────────────────────────────────────────────
function openAddPlugModal() {
  if (!activeHouseId) { alert('กรุณาเลือกบ้านก่อน'); return; }
  if (['member','guest'].includes(activeHouseRole)) { alert('เฉพาะเจ้าของหรือผู้ดูแลเท่านั้น'); return; }
  ['plug_code','plug_name'].forEach(id => document.getElementById(id).value = '');
  // Populate room dropdown
  const sel = document.getElementById('plug_location');
  sel.innerHTML = '<option value="">— ไม่ระบุ —</option>' +
    twinRooms.map(r => `<option value="${r.name}">${r.emoji} ${r.name}</option>`).join('');
  document.getElementById('plug-error').textContent = '';
  document.getElementById('add-plug-popup').style.display = 'flex';
  document.getElementById('plug-overlay').style.display   = 'block';
}
function closeAddPlugModal() {
  document.getElementById('add-plug-popup').style.display = 'none';
  document.getElementById('plug-overlay').style.display   = 'none';
}
async function addPlugCommit() {
  const plug_code = document.getElementById('plug_code').value.trim();
  const name      = document.getElementById('plug_name').value.trim();
  const location  = document.getElementById('plug_location').value.trim();
  const errorEl   = document.getElementById('plug-error');
  const btn       = document.getElementById('add-plug-btn');
  errorEl.textContent = '';
  if (!plug_code) { errorEl.textContent = 'กรุณากรอกรหัสปลั๊ก'; return; }
  if (!name)      { errorEl.textContent = 'กรุณากรอกชื่อปลั๊ก'; return; }
  btn.disabled = true; btn.textContent = 'กำลังเพิ่ม…';
  const { ok, data } = await apiPost(`/api/houses/${activeHouseId}/plugs/`, { plug_code, name, location });
  btn.disabled = false; btn.textContent = 'เพิ่มปลั๊ก';
  if (ok) { currentPlugs.push(data); renderDigitalTwin(); closeAddPlugModal(); }
  else errorEl.textContent = data.error || 'เกิดข้อผิดพลาด';
}

// ══════════════════════════════════════════════════════════════════
// PAGE: DASHBOARD
// ══════════════════════════════════════════════════════════════════
async function loadDashboardPage() {
  if (!activeHouseId) return;
  document.getElementById('dash-house-name').textContent = activeHouseName;
  try {
    const data = await apiGet(`/api/houses/${activeHouseId}/energy/dashboard/`);
    document.getElementById('dash-total-plugs').textContent = data.plug_count || '0';
    document.getElementById('dash-on-plugs').textContent    = data.plugs?.filter(p => p.is_on).length || '0';
    document.getElementById('dash-power').innerHTML         = `${data.current_power_w?.toFixed(0) || '0'}<span class="stat-unit">W</span>`;
    document.getElementById('dash-today').innerHTML         = `${data.today_kwh?.toFixed(2) || '0'}<span class="stat-unit">kWh</span>`;

    const list = document.getElementById('dash-plug-list');
    if (data.plugs && data.plugs.length > 0) {
      list.innerHTML = data.plugs.map(p => `
        <div style="background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:16px;">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
            <div style="font-size:13px; font-weight:600; color:var(--text);">${p.plug_name}</div>
            <div style="width:8px; height:8px; border-radius:50%; background:${p.is_on ? 'var(--accent)' : 'var(--text3)'};" title="${p.is_on ? 'เปิด' : 'ปิด'}"></div>
          </div>
          <div style="font-size:11px; color:var(--text3); margin-bottom:10px;">${p.location || 'ไม่ระบุตำแหน่ง'}</div>
          <div style="font-size:22px; font-weight:700; color:var(--accent); font-family:'DM Mono',monospace;">${p.power_w?.toFixed(0) || '0'}<span style="font-size:12px; font-weight:400; color:var(--text2); margin-left:3px;">W</span></div>
          ${p.recorded_at ? `<div style="font-size:10px; color:var(--text3); margin-top:4px;">อัพเดท ${new Date(p.recorded_at).toLocaleTimeString('th-TH')}</div>` : ''}
          <button onclick="togglePlugById('${p.plug_id}', ${p.is_on})"
            style="width:100%; margin-top:10px; padding:7px; border:none; border-radius:8px; font-size:12px; font-weight:600; cursor:pointer; font-family:'DM Sans',sans-serif;
                   background:${p.is_on ? 'var(--accent)' : 'var(--surface2)'}; color:${p.is_on ? '#000' : 'var(--text2)'}; border:1px solid ${p.is_on ? 'transparent' : 'var(--border)'};">
            ${p.is_on ? '⚡ เปิดอยู่ — คลิกเพื่อปิด' : '○ ปิดอยู่ — คลิกเพื่อเปิด'}
          </button>
        </div>
      `).join('');
    } else {
      list.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:40px; color:var(--text3);">ยังไม่มีปลั๊กในบ้านนี้</div>';
    }
  } catch (e) {}
}

async function togglePlugById(plugId, currentState) {
  const { ok, data } = await apiPost(`/api/houses/${activeHouseId}/plugs/${plugId}/control/`, { action: currentState ? 'off' : 'on' });
  if (ok) loadDashboardPage();
}

// ══════════════════════════════════════════════════════════════════
// PAGE: ENERGY
// ══════════════════════════════════════════════════════════════════
let energyChart = null;

async function loadEnergyPage() {
  if (!activeHouseId) return;
  document.getElementById('energy-house-name').textContent = activeHouseName;
  const period = document.getElementById('energy-period').value;

  try {
    const dash = await apiGet(`/api/houses/${activeHouseId}/energy/dashboard/`);
    document.getElementById('kpi-today').innerHTML  = `${dash.today_kwh?.toFixed(2) || '0'}<span class="stat-unit">kWh</span>`;
    document.getElementById('kpi-week').innerHTML   = `${dash.week_kwh?.toFixed(2) || '0'}<span class="stat-unit">kWh</span>`;
    document.getElementById('kpi-month').innerHTML  = `${dash.month_kwh?.toFixed(2) || '0'}<span class="stat-unit">kWh</span>`;
    document.getElementById('kpi-power').innerHTML  = `${dash.current_power_w?.toFixed(0) || '0'}<span class="stat-unit">W</span>`;

    const devList = document.getElementById('top-devices-list');
    if (dash.top_devices?.length > 0) {
      const maxKwh = Math.max(...dash.top_devices.map(d => d.total_kwh));
      devList.innerHTML = dash.top_devices.map(d => `
        <div style="padding:10px 16px; display:flex; align-items:center; gap:10px; border-bottom:1px solid var(--border);">
          <div style="flex:1;">
            <div style="font-size:13px; font-weight:500; color:var(--text);">${d.device_name}</div>
            <div style="height:4px; background:var(--surface3); border-radius:2px; margin-top:4px; overflow:hidden;">
              <div style="height:100%; width:${maxKwh > 0 ? (d.total_kwh/maxKwh*100).toFixed(0) : 0}%; background:var(--accent); border-radius:2px;"></div>
            </div>
          </div>
          <div style="font-size:13px; font-weight:600; color:var(--accent); font-family:'DM Mono',monospace;">${d.total_kwh.toFixed(3)} kWh</div>
        </div>
      `).join('');
    } else {
      devList.innerHTML = '<div style="padding:20px; text-align:center; color:var(--text3); font-size:13px;">ยังไม่มีข้อมูล</div>';
    }
  } catch (e) {}

  try {
    const today = new Date(), start = new Date(today);
    start.setDate(today.getDate() - (period === 'monthly' ? 180 : period === 'weekly' ? 84 : 30));
    const summary = await apiGet(`/api/houses/${activeHouseId}/energy/summary/?period=${period}&start=${start.toISOString().split('T')[0]}&end=${today.toISOString().split('T')[0]}`);
    renderEnergyChart(summary, period);
  } catch (e) {}

  try {
    const byPlug = await apiGet(`/api/houses/${activeHouseId}/energy/by-plug/`);
    const plugDiv = document.getElementById('plug-breakdown');
    if (byPlug.length > 0) {
      const maxKwh = Math.max(...byPlug.map(p => p.total_kwh));
      plugDiv.innerHTML = byPlug.map(p => `
        <div style="padding:12px 16px; display:flex; align-items:center; gap:12px; border-bottom:1px solid var(--border);">
          <div style="font-size:18px;"></div>
          <div style="flex:1;">
            <div style="font-size:13px; font-weight:500; color:var(--text);">${p.plug_name}</div>
            <div style="font-size:11px; color:var(--text3);">${p.location || 'ไม่ระบุ'} · เฉลี่ย ${p.avg_power_w.toFixed(0)}W · สูงสุด ${p.peak_power_w.toFixed(0)}W</div>
            <div style="height:4px; background:var(--surface3); border-radius:2px; margin-top:5px; overflow:hidden;">
              <div style="height:100%; width:${maxKwh > 0 ? (p.total_kwh/maxKwh*100).toFixed(0) : 0}%; background:var(--accent2); border-radius:2px;"></div>
            </div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:13px; font-weight:600; color:var(--accent2); font-family:'DM Mono',monospace;">${p.total_kwh.toFixed(3)}</div>
            <div style="font-size:10px; color:var(--text3);">kWh</div>
          </div>
        </div>
      `).join('');
    } else {
      plugDiv.innerHTML = '<div style="padding:20px; text-align:center; color:var(--text3); font-size:13px;">ยังไม่มีข้อมูล</div>';
    }
  } catch (e) {}
}

function renderEnergyChart(data, period) {
  const ctx = document.getElementById('energy-chart').getContext('2d');
  if (energyChart) energyChart.destroy();
  const labels = data.map(d => {
    const dt = new Date(d.period);
    if (period === 'monthly') return dt.toLocaleDateString('th-TH', { month: 'short', year: '2-digit' });
    if (period === 'weekly')  return dt.toLocaleDateString('th-TH', { day: 'numeric', month: 'short' });
    return dt.toLocaleDateString('th-TH', { day: 'numeric', month: 'short' });
  });
  energyChart = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{ label: 'kWh', data: data.map(d => d.total_kwh), backgroundColor: 'rgba(0,217,139,0.25)', borderColor: 'rgba(0,217,139,0.8)', borderWidth: 1.5, borderRadius: 4 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#888898', font: { size: 11 } } }, y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#888898', font: { size: 11 } } } } }
  });
}

function exportEnergy(fmt) {
  if (!activeHouseId) return;
  const today = new Date().toISOString().split('T')[0];
  const start = new Date(Date.now() - 30*24*60*60*1000).toISOString().split('T')[0];
  window.open(`/api/houses/${activeHouseId}/energy/export/?format=${fmt}&start=${start}&end=${today}`, '_blank');
}

// ══════════════════════════════════════════════════════════════════
// PAGE: ALERTS
// ══════════════════════════════════════════════════════════════════
async function loadAlertsPage() {
  if (!activeHouseId) return;
  document.getElementById('alerts-house-name').textContent = activeHouseName;
  const statusFilter = document.getElementById('alert-status-filter').value;
  const url = statusFilter === 'all'
    ? `/api/houses/${activeHouseId}/alerts/events/?limit=50`
    : `/api/houses/${activeHouseId}/alerts/events/?status=${statusFilter}&limit=50`;

  try {
    const data = await apiGet(url);
    const list = document.getElementById('alerts-list');

    if (!data.results || data.results.length === 0) {
      list.innerHTML = `<div style="text-align:center; padding:60px; color:var(--text3);">
        <div style="font-size:40px; margin-bottom:12px;">🔔</div>
        <p>ไม่มีการแจ้งเตือน</p>
      </div>`;
      return;
    }

    const statusLabel = { pending:'รอดำเนินการ', acknowledged:'รับทราบแล้ว', snoozed:'เลื่อนแจ้งเตือน', dismissed:'ยกเลิกแล้ว', auto_resolved:'ระบบดำเนินการแล้ว' };
    const statusColor = { pending:'var(--warn)', acknowledged:'var(--accent)', snoozed:'var(--accent2)', dismissed:'var(--text3)', auto_resolved:'var(--text3)' };

    list.innerHTML = data.results.map(ev => `
      <div style="background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:16px; margin-bottom:10px;">
        <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:12px;">
          <div style="flex:1;">
            <div style="font-size:14px; font-weight:600; color:var(--text); margin-bottom:4px;">${ev.title}</div>
            <div style="font-size:12px; color:var(--text2); margin-bottom:8px;">${ev.message}</div>
            <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
              <span style="font-size:11px; padding:2px 8px; border-radius:20px; background:${statusColor[ev.status]}22; color:${statusColor[ev.status]};">${statusLabel[ev.status] || ev.status}</span>
              ${ev.plug_name ? `<span style="font-size:11px; color:var(--text3);"> ${ev.plug_name}</span>` : ''}
              ${ev.device_name ? `<span style="font-size:11px; color:var(--text3);">📱 ${ev.device_name}</span>` : ''}
              <span style="font-size:11px; color:var(--text3);">${new Date(ev.triggered_at).toLocaleString('th-TH')}</span>
            </div>
          </div>
          ${ev.status === 'pending' ? `
          <div style="display:flex; flex-direction:column; gap:6px; flex-shrink:0;">
            <button onclick="alertAction('${ev.id}','acknowledge')" style="padding:5px 10px; background:var(--accent); border:none; border-radius:6px; color:#000; font-size:11px; font-weight:600; cursor:pointer; font-family:'DM Sans',sans-serif;">รับทราบ</button>
            <button onclick="alertAction('${ev.id}','snooze')" style="padding:5px 10px; background:var(--surface2); border:1px solid var(--border); border-radius:6px; color:var(--text2); font-size:11px; cursor:pointer; font-family:'DM Sans',sans-serif;">เลื่อน 30 นาที</button>
            ${ev.plug_id ? `<button onclick="alertAction('${ev.id}','auto_off')" style="padding:5px 10px; background:rgba(255,77,106,.1); border:1px solid rgba(255,77,106,.2); border-radius:6px; color:var(--danger); font-size:11px; cursor:pointer; font-family:'DM Sans',sans-serif;">ปิดทันที</button>` : ''}
          </div>` : ''}
        </div>
      </div>
    `).join('');
  } catch (e) {
    document.getElementById('alerts-list').innerHTML = '<div style="text-align:center; padding:40px; color:var(--danger);">เกิดข้อผิดพลาดในการโหลดข้อมูล</div>';
  }
}

async function alertAction(eventId, action) {
  const body = action === 'snooze' ? { action, snooze_minutes: 30 } : { action };
  const { ok } = await apiPost(`/api/houses/${activeHouseId}/alerts/events/${eventId}/action/`, body);
  if (ok) { loadAlertsPage(); refreshAlertBadge(); loadAlertPills(); }
}

// ── Init ──────────────────────────────────────────────────────────────────────
loadHouses();

// ══════════════════════════════════════════════════════════════════
// PAGE: HOUSE MANAGEMENT
// ══════════════════════════════════════════════════════════════════
async function loadManagePage() {
  if (!activeHouseId) {
    document.getElementById('manage-content').innerHTML = '<div style="text-align:center;padding:40px;color:var(--text3);">กรุณาเลือกบ้านก่อน</div>';
    return;
  }
  document.getElementById('manage-house-name').textContent = activeHouseName;
  const content = document.getElementById('manage-content');
  content.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text3);">กำลังโหลด...</div>';

  try {
    const [houseData, members] = await Promise.all([
      apiGet(`/api/houses/${activeHouseId}/`),
      apiGet(`/api/houses/${activeHouseId}/users/`),
    ]);

    const isOwner = activeHouseRole === 'owner';
    const isAdmin = activeHouseRole === 'admin';
    const canManage = isOwner || isAdmin;

    const roleLabel = { owner:'เจ้าของ', admin:'ผู้ดูแล', member:'สมาชิก', guest:'แขก' };
    const roleBadgeColor = { owner:'var(--accent)', admin:'var(--accent2)', member:'var(--text2)', guest:'var(--text3)' };

    content.innerHTML = `
      ${isOwner ? `
      <div class="card" style="margin-bottom:16px;">
        <div class="card-header"><div class="card-title">⚙️ ตั้งค่าบ้าน</div></div>
        <div style="padding:16px;display:flex;flex-direction:column;gap:12px;">
          <div style="display:flex;gap:8px;flex-wrap:wrap;" id="manage-emoji-picker">
            ${Array.from("🏠🏡🏢🏣🏤🏥🏦🏨🏩🏪🏫🏬🏭🏯🏰").map(em =>
              `<button class="emoji-btn" onclick="selectManageEmoji('${em}')" style="font-size:20px;background:var(--surface2);border:1.5px solid ${houseData.emoji===em?'var(--accent)':'var(--border)'};border-radius:8px;width:36px;height:36px;cursor:pointer;display:flex;align-items:center;justify-content:center;">${em}</button>`
            ).join('')}
          </div>
          <input type="hidden" id="manage-emoji" value="${houseData.emoji||'🏠'}">
          <div>
            <label style="font-size:11px;font-weight:500;color:var(--text2);text-transform:uppercase;letter-spacing:.4px;display:block;margin-bottom:6px;">ชื่อบ้าน</label>
            <input id="manage-house-name-input" type="text" class="modal-input" value="${houseData.house_name}">
          </div>
          <div>
            <label style="font-size:11px;font-weight:500;color:var(--text2);text-transform:uppercase;letter-spacing:.4px;display:block;margin-bottom:6px;">ที่อยู่</label>
            <input id="manage-address" type="text" class="modal-input" value="${houseData.address}">
          </div>
          <div style="display:flex;gap:8px;">
            <div style="flex:1;">
              <label style="font-size:11px;font-weight:500;color:var(--text2);text-transform:uppercase;letter-spacing:.4px;display:block;margin-bottom:6px;">Latitude</label>
              <input id="manage-lat" type="number" step="any" class="modal-input" value="${houseData.lat||''}">
            </div>
            <div style="flex:1;">
              <label style="font-size:11px;font-weight:500;color:var(--text2);text-transform:uppercase;letter-spacing:.4px;display:block;margin-bottom:6px;">Longitude</label>
              <input id="manage-lng" type="number" step="any" class="modal-input" value="${houseData.long||''}">
            </div>
          </div>
          <p id="manage-house-msg" style="font-size:12px;min-height:16px;margin:0;"></p>
          <div style="display:flex;gap:8px;">
            <button onclick="saveHouseSettings()" class="modal-btn-primary" style="padding:10px;flex:2;">บันทึก</button>
            <button onclick="deleteHouseConfirm()" style="flex:1;padding:10px;background:rgba(255,77,106,.1);border:1px solid rgba(255,77,106,.3);border-radius:10px;color:var(--danger);font-size:13px;font-weight:600;cursor:pointer;font-family:'DM Sans',sans-serif;">🗑 ลบบ้าน</button>
          </div>
        </div>
      </div>` : ''}

      <div class="card" style="margin-bottom:16px;">
        <div class="card-header">
          <div class="card-title">👥 สมาชิก (${members.length} คน)</div>
          ${canManage ? `<button onclick="showInviteForm()" class="tbtn primary" style="font-size:12px;padding:6px 12px;">+ เชิญสมาชิก</button>` : ''}
        </div>
        <div id="invite-form" style="display:none;padding:12px 16px;border-bottom:1px solid var(--border);background:var(--surface2);">
          <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:flex-end;">
            <div style="flex:2;min-width:180px;">
              <label style="font-size:11px;color:var(--text2);display:block;margin-bottom:4px;">อีเมลสมาชิก</label>
              <input id="invite-email" type="email" class="modal-input" placeholder="email@example.com">
            </div>
            <div style="flex:1;min-width:120px;">
              <label style="font-size:11px;color:var(--text2);display:block;margin-bottom:4px;">บทบาท</label>
              <select id="invite-role" class="modal-input" style="cursor:pointer;">
                ${isOwner ? '<option value="admin">ผู้ดูแล</option>' : ''}
                <option value="member">สมาชิก</option>
                <option value="guest">แขก</option>
              </select>
            </div>
            <button onclick="inviteMember()" class="modal-btn-primary" style="padding:10px 16px;flex-shrink:0;">เชิญ</button>
          </div>
          <p id="invite-msg" style="font-size:12px;min-height:16px;margin:6px 0 0;"></p>
        </div>
        <div style="padding:8px 0;">
          ${members.map(m => `
            <div style="display:flex;align-items:center;gap:12px;padding:10px 16px;border-bottom:1px solid var(--border);">
              <div style="width:36px;height:36px;border-radius:50%;background:var(--surface3);display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:600;color:var(--text2);">${m.username.slice(0,1).toUpperCase()}</div>
              <div style="flex:1;">
                <div style="font-size:13px;font-weight:500;color:var(--text);">${m.username}</div>
                <div style="font-size:11px;color:var(--text3);">${m.email}</div>
              </div>
              <span style="font-size:11px;padding:2px 8px;border-radius:20px;background:${roleBadgeColor[m.role]}22;color:${roleBadgeColor[m.role]};">${roleLabel[m.role]||m.role}</span>
              ${canManage && m.role !== 'owner' ? `
              <div style="display:flex;gap:6px;">
                <select onchange="updateMemberRole('${m.user_id}', this.value)" style="padding:4px 8px;background:var(--surface2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:11px;cursor:pointer;font-family:'DM Sans',sans-serif;">
                  ${isOwner ? `<option value="admin" ${m.role==='admin'?'selected':''}>ผู้ดูแล</option>` : ''}
                  <option value="member" ${m.role==='member'?'selected':''}>สมาชิก</option>
                  <option value="guest" ${m.role==='guest'?'selected':''}>แขก</option>
                </select>
                ${isOwner ? `<button onclick="transferOwnership('${m.user_id}','${m.username}')" style="padding:4px 8px;background:var(--accent-dim);border:1px solid var(--accent);border-radius:6px;color:var(--accent);font-size:10px;cursor:pointer;font-family:'DM Sans',sans-serif;" title="โอนความเป็นเจ้าของ">👑</button>` : ''}
                <button onclick="removeMember('${m.user_id}','${m.username}')" style="padding:4px 8px;background:rgba(255,77,106,.1);border:1px solid rgba(255,77,106,.2);border-radius:6px;color:var(--danger);font-size:11px;cursor:pointer;font-family:'DM Sans',sans-serif;">ลบ</button>
              </div>` : ''}
            </div>
          `).join('')}
        </div>
      </div>
    `;
  } catch(e) {
    document.getElementById('manage-content').innerHTML = '<div style="text-align:center;padding:40px;color:var(--danger);">เกิดข้อผิดพลาด</div>';
  }
}

function selectManageEmoji(em) {
  document.getElementById('manage-emoji').value = em;
  document.querySelectorAll('#manage-emoji-picker .emoji-btn').forEach(btn => {
    const match = btn.textContent.trim() === em;
    btn.style.borderColor = match ? 'var(--accent)' : 'var(--border)';
    btn.style.background = match ? 'var(--accent-dim)' : 'var(--surface2)';
  });
}

async function saveHouseSettings() {
  const house_name = document.getElementById('manage-house-name-input').value.trim();
  const address = document.getElementById('manage-address').value.trim();
  const lat = document.getElementById('manage-lat').value;
  const lng = document.getElementById('manage-lng').value;
  const emoji = document.getElementById('manage-emoji').value;
  const msg = document.getElementById('manage-house-msg');
  msg.style.color = 'var(--danger)'; msg.textContent = '';
  if (!house_name) { msg.textContent = 'กรุณากรอกชื่อบ้าน'; return; }
  const res = await fetch(`/api/houses/${activeHouseId}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
    body: JSON.stringify({ house_name, address, lat: lat ? parseFloat(lat) : null, long: lng ? parseFloat(lng) : null, emoji }),
  });
  const data = await res.json();
  if (res.ok) {
    msg.style.color = 'var(--accent)'; msg.textContent = 'บันทึกสำเร็จ';
    activeHouseName = house_name;
    document.getElementById('manage-house-name').textContent = house_name;
    const h = houses.find(x => x.id === activeHouseId);
    if (h) { h.house_name = house_name; h.emoji = emoji; renderHouseTabs(); }
  } else {
    msg.textContent = data.error || 'เกิดข้อผิดพลาด';
  }
}

async function deleteHouseConfirm() {
  if (!confirm('ลบบ้าน "' + activeHouseName + '"? การกระทำนี้ไม่สามารถย้อนกลับได้')) return;
  const res = await fetch(`/api/houses/${activeHouseId}/`, {
    method: 'DELETE',
    headers: { 'Authorization': 'Bearer ' + token },
  });
  if (res.ok) {
    houses = houses.filter(h => h.id !== activeHouseId);
    activeHouseId = null; activeHouseName = ''; activeHouseRole = '';
    renderHouseTabs();
    if (houses.length > 0) setActiveHouse(houses[0].id, houses[0].house_name, houses[0].role);
    showPage('home');
  }
}

function showInviteForm() {
  const f = document.getElementById('invite-form');
  f.style.display = f.style.display === 'none' ? 'block' : 'none';
}

async function inviteMember() {
  const email = document.getElementById('invite-email').value.trim();
  const role = document.getElementById('invite-role').value;
  const msg = document.getElementById('invite-msg');
  msg.style.color = 'var(--danger)'; msg.textContent = '';
  if (!email) { msg.textContent = 'กรุณากรอกอีเมล'; return; }
  const { ok, data } = await apiPost(`/api/houses/${activeHouseId}/users/invite/`, { email, role });
  if (ok) {
    msg.style.color = 'var(--accent)'; msg.textContent = 'เชิญ ' + email + ' สำเร็จ';
    document.getElementById('invite-email').value = '';
    setTimeout(loadManagePage, 1000);
  } else {
    msg.textContent = data.error || 'เกิดข้อผิดพลาด';
  }
}

async function removeMember(userId, username) {
  if (!confirm('ลบ ' + username + ' ออกจากบ้านนี้?')) return;
  const { ok, data } = await apiPost(`/api/houses/${activeHouseId}/users/manage/`, { action: 'remove', user_id: userId });
  if (ok) loadManagePage();
  else alert(data.error || 'เกิดข้อผิดพลาด');
}

async function updateMemberRole(userId, newRole) {
  const { ok, data } = await apiPost(`/api/houses/${activeHouseId}/users/manage/`, { action: 'update_role', user_id: userId, role: newRole });
  if (!ok) { alert(data.error || 'เกิดข้อผิดพลาด'); loadManagePage(); }
}

async function transferOwnership(userId, username) {
  if (!confirm('โอนความเป็นเจ้าของบ้านให้ ' + username + '? คุณจะกลายเป็นผู้ดูแลแทน')) return;
  const { ok, data } = await apiPost(`/api/houses/${activeHouseId}/transfer/`, { user_id: userId });
  if (ok) {
    activeHouseRole = 'admin';
    const h = houses.find(x => x.id === activeHouseId);
    if (h) h.role = 'admin';
    loadManagePage();
  } else {
    alert(data.error || 'เกิดข้อผิดพลาด');
  }
}

// ══════════════════════════════════════════════════════════════════
// PAGE: MY HOUSES
// ══════════════════════════════════════════════════════════════════
async function loadMyHousesPage() {
  const content = document.getElementById('myhouses-content');
  content.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text3);">กำลังโหลด...</div>';
  try {
    const myHouses = await apiGet('/api/houses/');
    if (myHouses.length === 0) {
      content.innerHTML = '<div style="text-align:center;padding:60px;color:var(--text3);"><div style="font-size:40px;margin-bottom:12px;">🏠</div><p>คุณยังไม่ได้เป็นสมาชิกบ้านใด</p></div>';
      return;
    }
    const roleLabel = { owner:'เจ้าของ', admin:'ผู้ดูแล', member:'สมาชิก', guest:'แขก' };
    const roleBadgeColor = { owner:'var(--accent)', admin:'var(--accent2)', member:'var(--text2)', guest:'var(--text3)' };

    const houseDetails = await Promise.all(myHouses.map(async h => {
      try {
        const members = await apiGet(`/api/houses/${h.id}/users/`);
        const owner = members.find(m => m.role === 'owner');
        return { ...h, members, owner };
      } catch { return { ...h, members: [], owner: null }; }
    }));

    content.innerHTML = houseDetails.map(h => `
      <div class="card" style="margin-bottom:16px;">
        <div style="padding:16px;">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
            <div style="font-size:32px;">${h.emoji||'🏠'}</div>
            <div style="flex:1;">
              <div style="font-size:16px;font-weight:700;color:var(--text);">${h.house_name}</div>
              <div style="font-size:12px;color:var(--text3);">📍 ${h.address}</div>
            </div>
            <span style="font-size:11px;padding:3px 10px;border-radius:20px;background:${roleBadgeColor[h.role]}22;color:${roleBadgeColor[h.role]};">${roleLabel[h.role]||h.role}</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:6px;font-size:12px;color:var(--text2);margin-bottom:12px;">
            ${h.owner ? '<div>👑 เจ้าของ: <strong style="color:var(--text);">' + h.owner.username + '</strong> (' + h.owner.email + ')</div>' : ''}
            <div>👥 สมาชิก ${h.members.length} คน</div>
            ${h.lat && h.long ? '<div>🗺️ พิกัด: ' + parseFloat(h.lat).toFixed(4) + ', ' + parseFloat(h.long).toFixed(4) + '</div>' : ''}
            <div>📅 สร้างเมื่อ: ${new Date(h.created_at).toLocaleDateString('th-TH',{year:'numeric',month:'long',day:'numeric'})}</div>
          </div>
          <div style="border-top:1px solid var(--border);padding-top:10px;">
            <div style="font-size:11px;color:var(--text3);margin-bottom:6px;">สมาชิกทั้งหมด</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px;">
              ${h.members.map(m =>
                '<div style="display:flex;align-items:center;gap:6px;padding:4px 10px;background:var(--surface2);border-radius:20px;font-size:11px;">' +
                '<div style="width:20px;height:20px;border-radius:50%;background:var(--surface3);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:600;">' + m.username.slice(0,1).toUpperCase() + '</div>' +
                '<span style="color:var(--text);">' + m.username + '</span>' +
                '<span style="color:' + roleBadgeColor[m.role] + ';font-size:10px;">' + (roleLabel[m.role]||m.role) + '</span>' +
                '</div>'
              ).join('')}
            </div>
          </div>
          ${h.role !== 'owner' ?
            '<div style="margin-top:12px;"><button onclick="leaveHouse(\'' + h.id + '\',\'' + h.house_name.replace(/'/g,"\\'") + '\')" style="padding:8px 16px;background:rgba(255,77,106,.1);border:1px solid rgba(255,77,106,.3);border-radius:8px;color:var(--danger);font-size:12px;font-weight:600;cursor:pointer;font-family:\'DM Sans\',sans-serif;">ออกจากบ้านนี้</button></div>' :
            '<div style="margin-top:12px;"><button onclick="setActiveHouse(\'' + h.id + '\',\'' + h.house_name.replace(/'/g,"\\'") + '\',\'owner\');showPage(\'manage\');loadManagePage();" style="padding:8px 16px;background:var(--accent-dim);border:1px solid var(--accent);border-radius:8px;color:var(--accent);font-size:12px;font-weight:600;cursor:pointer;font-family:\'DM Sans\',sans-serif;">⚙️ จัดการบ้าน</button></div>'
          }
        </div>
      </div>
    `).join('');
  } catch(e) {
    content.innerHTML = '<div style="text-align:center;padding:40px;color:var(--danger);">เกิดข้อผิดพลาด</div>';
  }
}

async function leaveHouse(houseId, houseName) {
  if (!confirm('ออกจากบ้าน "' + houseName + '"?')) return;
  const { ok, data } = await apiPost(`/api/houses/${houseId}/leave/`, {});
  if (ok) {
    houses = houses.filter(h => h.id !== houseId);
    if (activeHouseId === houseId) {
      activeHouseId = null; activeHouseName = ''; activeHouseRole = '';
      if (houses.length > 0) setActiveHouse(houses[0].id, houses[0].house_name, houses[0].role);
    }
    renderHouseTabs();
    loadMyHousesPage();
  } else {
    alert(data.error || 'เกิดข้อผิดพลาด');
  }
}

// ══════════════════════════════════════════════════════════════════
// PAGE: ACCOUNT
// ══════════════════════════════════════════════════════════════════
async function loadAccountPage() {
  try {
    const me = await apiGet('/auth/me/');
    document.getElementById('acc-username').value = me.username || '';
    document.getElementById('acc-email').value = me.email || '';
    document.getElementById('account-sub').textContent = me.username || '';
    ['acc-cur-pw','acc-new-pw','acc-confirm-pw'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('acc-profile-msg').textContent = '';
    document.getElementById('acc-pw-msg').textContent = '';
  } catch(e) {}
}

async function saveProfile() {
  const username = document.getElementById('acc-username').value.trim();
  const email = document.getElementById('acc-email').value.trim();
  const msg = document.getElementById('acc-profile-msg');
  msg.style.color = 'var(--danger)'; msg.textContent = '';
  if (!username) { msg.textContent = 'กรุณากรอกชื่อผู้ใช้'; return; }
  if (!email) { msg.textContent = 'กรุณากรอกอีเมล'; return; }
  const res = await fetch('/auth/me/update/', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
    body: JSON.stringify({ username, email }),
  });
  const data = await res.json();
  if (res.ok) {
    msg.style.color = 'var(--accent)'; msg.textContent = 'บันทึกสำเร็จ';
    document.getElementById('avatar-initials').textContent = username.slice(0,1).toUpperCase();
    document.getElementById('username').textContent = username;
    document.getElementById('account-sub').textContent = username;
  } else {
    msg.textContent = (Array.isArray(data.error) ? data.error.join(', ') : data.error) || 'เกิดข้อผิดพลาด';
  }
}

async function changePassword() {
  const current_password = document.getElementById('acc-cur-pw').value;
  const new_password = document.getElementById('acc-new-pw').value;
  const confirm_pw = document.getElementById('acc-confirm-pw').value;
  const msg = document.getElementById('acc-pw-msg');
  msg.style.color = 'var(--danger)'; msg.textContent = '';
  if (!current_password) { msg.textContent = 'กรุณากรอกรหัสผ่านปัจจุบัน'; return; }
  if (!new_password) { msg.textContent = 'กรุณากรอกรหัสผ่านใหม่'; return; }
  if (new_password !== confirm_pw) { msg.textContent = 'รหัสผ่านใหม่ไม่ตรงกัน'; return; }
  const res = await fetch('/auth/me/update/', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
    body: JSON.stringify({ current_password, new_password }),
  });
  const data = await res.json();
  if (res.ok) {
    msg.style.color = 'var(--accent)'; msg.textContent = 'เปลี่ยนรหัสผ่านสำเร็จ';
    ['acc-cur-pw','acc-new-pw','acc-confirm-pw'].forEach(id => document.getElementById(id).value = '');
  } else {
    msg.textContent = (Array.isArray(data.error) ? data.error.join(', ') : data.error) || 'เกิดข้อผิดพลาด';
  }
}

async function doLogout() {
  const refresh = localStorage.getItem('refresh');
  if (refresh) {
    await fetch('/auth/logout/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
      body: JSON.stringify({ refresh }),
    }).catch(() => {});
  }
  localStorage.clear();
  window.location = '/login/';
}

// ── WebSocket for Real-time Plug Updates ─────────────────────────────────────────
// Store WebSocket connections per plug
const plugWebSockets = {};

function connectPlugWebSocket(plugCode) {
  if (plugWebSockets[plugCode]) {
    // Already connected
    return;
  }
  
  const ws = new WebSocket(`ws://${window.location.host}/ws/plug/${plugCode}/`);
  
  ws.onopen = function() {
    console.log(`WebSocket connected for plug ${plugCode}`);
  };
  
  ws.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log('Plug update received:', data);
    
    if (data.type === 'plug.update') {
      handlePlugUpdate(plugCode, data);
    }
  };
  
  ws.onclose = function() {
    console.log(`WebSocket closed for plug ${plugCode} — retrying in 3s`);
    delete plugWebSockets[plugCode];
    setTimeout(() => connectPlugWebSocket(plugCode), 3000);
  };
  
  ws.onerror = function(err) {
    console.error(`WebSocket error for plug ${plugCode}:`, err);
  };
  
  plugWebSockets[plugCode] = ws;
}

function handlePlugUpdate(plugCode, data) {
  // Find the plug card in the DOM
  const plugCard = document.querySelector(`[data-plug-code="${plugCode}"]`);
  if (!plugCard) return;
  
  if (data.event === 'nfc_scan' && data.known) {
    // Known device detected
    const deviceNameEl = plugCard.querySelector('.device-name');
    const deviceTypeEl = plugCard.querySelector('.device-type');
    const nfcStatusEl = plugCard.querySelector('.nfc-status');
    
    if (deviceNameEl) deviceNameEl.textContent = data.device_name || '—';
    if (nfcStatusEl) {
      nfcStatusEl.textContent = 'อุปกรณ์ตรวจพบ';
      nfcStatusEl.className = 'nfc-status status-green';
    }
    
    // Refresh plug data from server
    loadPlugs();
  }
  
  if (data.event === 'nfc_scan' && !data.known) {
    // Unknown tag detected
    const nfcStatusEl = plugCard.querySelector('.nfc-status');
    
    if (nfcStatusEl) {
      nfcStatusEl.textContent = 'แท็กไม่รู้จัก — กรุณาลงทะเบียน';
      nfcStatusEl.className = 'nfc-status status-orange';
    }
  }
  
  if (data.event === 'nfc_removed') {
    // Tag removed
    const deviceNameEl = plugCard.querySelector('.device-name');
    const deviceTypeEl = plugCard.querySelector('.device-type');
    const nfcStatusEl = plugCard.querySelector('.nfc-status');
    
    if (deviceNameEl) deviceNameEl.textContent = '—';
    if (deviceTypeEl) deviceTypeEl.textContent = '—';
    if (nfcStatusEl) {
      nfcStatusEl.textContent = 'ไม่มีอุปกรณ์';
      nfcStatusEl.className = 'nfc-status status-gray';
    }
    
    // Refresh plug data from server
    loadPlugs();
  }
}

// Initialize WebSocket connections when house changes
document.addEventListener('houseChanged', async function() {
  // Close existing WebSocket connections
  Object.values(plugWebSockets).forEach(ws => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.close();
    }
  });
  
  // Get current plugs and connect WebSockets for each
  const res = await fetch(`/api/houses/${activeHouseId}/plugs/`, {
    headers: { 'Authorization': 'Bearer ' + token }
  });
  if (res.ok) {
    const plugs = await res.json();
    plugs.forEach(p => {
      if (p.plug_code) {
        connectPlugWebSocket(p.plug_code);
      }
    });
  }
});

// Also connect on initial load
if (activeHouseId) {
  (async () => {
    const res = await fetch(`/api/houses/${activeHouseId}/plugs/`, {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    if (res.ok) {
      const plugs = await res.json();
      plugs.forEach(p => {
        if (p.plug_code) {
          connectPlugWebSocket(p.plug_code);
        }
      });
    }
  })();
}
