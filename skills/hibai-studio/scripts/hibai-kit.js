/* HibAI kit — real-asset scenes for talking-head reels (loaded by compose.html after moves-compose.js).
   Every function draws on the engine canvas X at time t, in the theme colours (ACC/INK/BG) and fonts (FONT / LATIN_FONT).
   Assets live in <work>/assets/ (42_web_assets.py: logos, icons, screenshots · the user's own files).

   HK.load(['logo-claude.svg', 'shot-x.png', …])           preload images (call once at the top of your scene script)
   HK.appear(t, s, e, fn, dy)                               fade/slide a block in at s and out at e
   HK.browser(t, {img, R, url, zoom, hl})                   screenshot in a browser window · zoom in → highlight → zoom out (spotlight)
   HK.phoneShot(t, {img, s, e, cx, y, w})                   screenshot inside a phone, rising
   HK.versus(t, {s, e, y, left:{icon, ok}, right:{icon, ok}})   ✓ vs ✗ tiles (app vs website, before vs after)
   HK.flow(t, {s, e, y, from, to, items})                   files/icons flying from one tile to another along an arc, then ✓
   HK.orbit(t, {s, e, cx, cy, center, items})               a logo in the middle, icons orbiting (depth moment)
   HK.desktopApp(t, {s, e, R, brand, name, tabs, active, clickAt, title, progress})   a desktop app window rebuilt in code
   HK.pointer(x, y, click)                                  mouse pointer, click 0..1 = press + ripple
   HK.tint(file, x, y, size, colour) · HK.img(file, x, y, w, h)
   Layouts: R_DOWN → keep visuals in y 160–600 · R_LOWER → y 160–1180 · x always 70–1010 (safe zone). */
(function () {
  const G = window, IMGS = {};
  const E = k => 1 - Math.pow(1 - Math.min(1, Math.max(0, k)), 3);
  const EIO = k => { k = Math.min(1, Math.max(0, k)); return k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; };
  const P = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));
  const L = (a, b, k) => a + (b - a) * k;
  const acc = () => (typeof ACC !== 'undefined' ? ACC : '#FF5C8A');
  const bg = () => (typeof BG !== 'undefined' ? BG : '#111111');
  const lat = () => (typeof LATIN_FONT !== 'undefined' ? LATIN_FONT : 'Inter');
  const RR = (x, y, w, h, r) => { X.beginPath(); X.roundRect(x, y, w, h, r); };
  const SH = (b, oy, a) => { X.shadowColor = 'rgba(0,0,0,' + a + ')'; X.shadowBlur = b; X.shadowOffsetY = oy; };
  const NS = () => { X.shadowColor = 'transparent'; X.shadowBlur = 0; X.shadowOffsetY = 0; };
  const HK = {};
  HK.ease = { out: E, inOut: EIO };
  HK.load = list => list.forEach(f => { if (IMGS[f]) return; const i = new Image(); i.src = 'assets/' + f; IMGS[f] = i; });
  const ok = f => { const i = IMGS[f] || (HK.load([f]), IMGS[f]); return i && i.complete && i.naturalWidth ? i : null; };
  HK.img = (f, x, y, w, h) => { const i = ok(f); if (i) X.drawImage(i, x, y, w, h); };
  const TC = document.createElement('canvas');
  HK.tint = (f, x, y, s, col) => { const i = ok(f); if (!i) return; TC.width = TC.height = Math.ceil(s); const g = TC.getContext('2d');
    g.clearRect(0, 0, s, s); g.drawImage(i, 0, 0, s, s); g.globalCompositeOperation = 'source-in'; g.fillStyle = col; g.fillRect(0, 0, s, s);
    g.globalCompositeOperation = 'source-over'; X.drawImage(TC, x, y, s, s); };
  HK.appear = (t, s, e, fn, dy) => { if (t < s || t > e) return; const a = Math.min(E((t - s) / 0.4), 1 - E((t - (e - 0.25)) / 0.25));
    X.save(); X.globalAlpha *= a; X.translate(0, (1 - a) * (dy == null ? 40 : dy)); fn(a); X.restore(); };
  const check = (x, y, r, k, good) => { X.fillStyle = good ? '#22C55E' : '#EF4444'; X.beginPath(); X.arc(x, y, r * k, 0, 7); X.fill();
    X.strokeStyle = '#FFFFFF'; X.lineWidth = r * 0.22 * k; X.lineCap = 'round'; X.lineJoin = 'round'; X.beginPath();
    if (good) { X.moveTo(x - r * .42 * k, y + r * .02 * k); X.lineTo(x - r * .1 * k, y + r * .34 * k); X.lineTo(x + r * .45 * k, y - r * .3 * k); }
    else { X.moveTo(x - r * .34 * k, y - r * .34 * k); X.lineTo(x + r * .34 * k, y + r * .34 * k); X.moveTo(x + r * .34 * k, y - r * .34 * k); X.lineTo(x - r * .34 * k, y + r * .34 * k); }
    X.stroke(); };
  HK.check = check;
  HK.pointer = (x, y, click) => { const s = 1 - 0.15 * Math.sin((click || 0) * Math.PI); X.save(); X.translate(x, y); X.scale(s, s);
    X.fillStyle = '#111'; X.strokeStyle = '#fff'; X.lineWidth = 4; X.beginPath(); X.moveTo(0, 0); X.lineTo(0, 52); X.lineTo(14, 40); X.lineTo(26, 64);
    X.lineTo(36, 59); X.lineTo(24, 36); X.lineTo(42, 36); X.closePath(); X.stroke(); X.fill(); X.restore();
    if (click > 0 && click < 1) { X.strokeStyle = 'rgba(255,255,255,' + (1 - click) + ')'; X.lineWidth = 6; X.beginPath(); X.arc(x, y, 20 + 60 * click, 0, 7); X.stroke(); } };

  /* Spotlight browser. zoom: {s, e, cx, cy, scale} (times in seconds, centre in screenshot pixels) — zooms in at s, back out at e.
     hl: {x, y, w, h, at, style:'rect'|'circle'|'underline'} — drawn on at «at» in the accent colour. */
  HK.browser = (t, o) => { const R = o.R || { x: 80, y: 250, w: 920, h: 900 }, H = 56, i = ok(o.img);
    X.save(); X.direction = 'ltr'; SH(50, 22, .35); X.fillStyle = '#FFFFFF'; RR(R.x, R.y, R.w, R.h, 26); X.fill(); NS();
    X.fillStyle = '#EDEBE6'; RR(R.x, R.y, R.w, H, 26); X.fill(); X.fillRect(R.x, R.y + H - 20, R.w, 20);
    ['#FF5F57', '#FEBC2E', '#28C840'].forEach((c, j) => { X.fillStyle = c; X.beginPath(); X.arc(R.x + 30 + j * 24, R.y + H / 2, 7, 0, 7); X.fill(); });
    X.fillStyle = '#FFFFFF'; RR(R.x + 110, R.y + 12, R.w - 140, H - 24, 10); X.fill();
    X.fillStyle = '#6B6B6B'; X.font = '500 22px ' + lat(); X.textAlign = 'left'; X.textBaseline = 'middle'; X.fillText(o.url || '', R.x + 130, R.y + H / 2 + 1);
    const vx = R.x, vy = R.y + H, vw = R.w, vh = R.h - H; X.beginPath(); X.rect(vx, vy, vw, vh); X.clip();
    if (i) { const z = o.zoom, zk = z ? EIO(P(t, z.s, z.s + .9) - P(t, z.e - .6, z.e)) : 0, base = vw / i.naturalWidth;
      const sc = base * (z ? L(1, z.scale || 2.2, zk) : 1), cx = z ? L(i.naturalWidth / 2, z.cx, zk) : i.naturalWidth / 2, cy = z ? L(vh / 2 / base, z.cy, zk) : vh / 2 / base;
      const ox = vx + vw / 2 - cx * sc, oy = vy + vh / 2 - cy * sc; X.drawImage(i, ox, oy, i.naturalWidth * sc, i.naturalHeight * sc);
      const h = o.hl; if (h) { const k = EIO(P(t, h.at, h.at + .5)) * (z ? 1 - P(t, z.e - .6, z.e) : 1); if (k > 0) {
        const bx = ox + h.x * sc - 10, by = oy + h.y * sc - 10, bw = h.w * sc + 20, bh = h.h * sc + 20; X.strokeStyle = acc(); X.lineWidth = 7; X.lineCap = 'round';
        if (h.style === 'underline') { X.beginPath(); X.moveTo(bx, by + bh + 6); X.lineTo(bx + bw * k, by + bh + 6); X.stroke(); }
        else if (h.style === 'circle') { X.beginPath(); X.ellipse(bx + bw / 2, by + bh / 2, bw * .62, bh * .9, 0, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * k); X.stroke(); }
        else { const per = 2 * (bw + bh); X.setLineDash([per * k, per]); RR(bx, by, bw, bh, 14); X.stroke(); X.setLineDash([]); } } } }
    X.restore(); };

  HK.phoneShot = (t, o) => HK.appear(t, o.s, o.e, () => { const k = E((t - o.s) / .45), i = ok(o.img), w = o.w || 420;
    const h = i ? Math.min(w * i.naturalHeight / i.naturalWidth, o.maxH || 960) : 900, x = (o.cx || 540) - w / 2, y = (o.y || 230) + (1 - k) * 120;
    X.fillStyle = '#0B0B0F'; SH(50, 22, .45); RR(x - 16, y - 16, w + 32, h + 32, 56); X.fill(); NS();
    X.save(); RR(x, y, w, h, 42); X.clip(); if (i) X.drawImage(i, x, y, w, w * i.naturalHeight / i.naturalWidth); X.restore(); }, 80);

  HK.versus = (t, o) => HK.appear(t, o.s, o.e, () => { const y = o.y || 560;
    [[o.left, 300, o.left.at || o.s], [o.right, 780, o.right.at || o.s + .3]].forEach(([side, x, s]) => {
      const k = E((t - s) / .3), S = 300 * (.8 + .2 * k); X.save(); X.globalAlpha *= k;
      X.fillStyle = '#FFFFFF'; SH(40, 14, .3); RR(x - S / 2, y - S / 2, S, S, 48); X.fill(); NS();
      if (side.logo) HK.img(side.icon, x - S * .3, y - S * .3, S * .6, S * .6); else HK.tint(side.icon, x - S * .3, y - S * .3, S * .6, bg());
      if (!side.ok) { X.strokeStyle = '#EF4444'; X.lineWidth = 12; X.lineCap = 'round'; const q = P(t, s + .15, s + .45);
        X.beginPath(); X.moveTo(x - S * .38, y + S * .38); X.lineTo(x - S * .38 + S * .76 * q, y + S * .38 - S * .76 * q); X.stroke(); }
      X.fillStyle = '#FFFFFF'; X.beginPath(); X.arc(x + S * .36, y - S * .36, 48, 0, 7); X.fill(); check(x + S * .36, y - S * .36, 40, k, !!side.ok); X.restore(); }); });

  HK.flow = (t, o) => HK.appear(t, o.s, o.e, () => { const y = o.y || 390, A = { x: 250, y }, B = { x: 830, y }, top = y - 210;
    X.fillStyle = '#FFFFFF'; SH(30, 10, .3); RR(A.x - 90, A.y - 90, 180, 180, 36); X.fill(); RR(B.x - 90, B.y - 90, 180, 180, 36); X.fill(); NS();
    (o.from.logo ? HK.img : (f, x, yy, w) => HK.tint(f, x, yy, w, bg()))(o.from.icon, A.x - 60, A.y - 60, 120, 120);
    (o.to.logo ? HK.img : (f, x, yy, w) => HK.tint(f, x, yy, w, bg()))(o.to.icon, B.x - 60, B.y - 60, 120, 120);
    X.strokeStyle = 'rgba(255,255,255,.35)'; X.lineWidth = 4; X.setLineDash([12, 12]); X.lineDashOffset = -t * 60;
    X.beginPath(); X.moveTo(A.x + 100, A.y); X.quadraticCurveTo(540, top, B.x - 100, B.y); X.stroke(); X.setLineDash([]);
    (o.items || []).forEach((f, j) => { for (let r = 0; r < 2; r++) { const q = (t - o.s - .2 - j * .22 - r * .66) / .9; if (q < 0 || q > 1) continue;
      const e = EIO(q), x = (1 - e) * (1 - e) * (A.x + 100) + 2 * (1 - e) * e * 540 + e * e * (B.x - 100), yy = (1 - e) * (1 - e) * A.y + 2 * (1 - e) * e * top + e * e * B.y;
      X.fillStyle = acc(); RR(x - 34, yy - 34, 68, 68, 18); X.fill(); HK.tint(f, x - 24, yy - 24, 48, '#FFFFFF'); } });
    const dk = o.doneAt || (o.e - .7); if (t > dk) check(B.x + 70, B.y - 70, 34, E((t - dk) / .3), true); });

  HK.orbit = (t, o) => HK.appear(t, o.s, o.e, () => { const cx = o.cx || 540, cy = o.cy || 380, rx = o.rx || 330, ry = o.ry || 120, k = E((t - o.s) / .5);
    X.save(); X.translate(cx, cy); X.scale(.85 + .15 * k, .85 + .15 * k); X.translate(-cx, -cy);
    X.fillStyle = 'rgba(255,255,255,.08)'; X.beginPath(); X.arc(cx, cy, 150, 0, 7); X.fill();
    X.fillStyle = '#FFFFFF'; SH(40, 16, .3); X.beginPath(); X.arc(cx, cy, 112, 0, 7); X.fill(); NS(); HK.img(o.center, cx - 70, cy - 70, 140, 140);
    X.strokeStyle = 'rgba(255,255,255,.25)'; X.lineWidth = 3; X.setLineDash([10, 12]); X.beginPath(); X.ellipse(cx, cy, rx, ry, 0, 0, 7); X.stroke(); X.setLineDash([]);
    (o.items || []).forEach((f, j, all) => { const an = (t - o.s) * 1.4 + j * Math.PI * 2 / all.length, x = cx + Math.cos(an) * rx, y = cy + Math.sin(an) * ry,
      kk = E((t - o.s - .28 - j * .18) / .3), s = 86 * kk; X.fillStyle = acc(); SH(24, 8, .3); RR(x - s / 2 - 14, y - s / 2 - 14, s + 28, s + 28, 26); X.fill(); NS();
      if (kk > .05) HK.tint(f, x - s / 2 + 4, y - s / 2 + 4, s - 8, '#FFFFFF'); });
    X.restore(); });

  /* desktop app rebuilt in code: sidebar tabs, the pointer clicks «clickTab» at clickAt, then the main area shows title / progress.
     o: {s, e, R, brand (logo file), name, tabs:['Chat','Code'], startTab, clickTab, clickAt, before:'How can I help you today?',
         after:'Setting up…', done:'Ready', progress:{s, e}, light:{bg,side,ink,muted,accent}} */
  HK.desktopApp = (t, o) => { if (t < o.s || t > o.e) return; const R = o.R || { x: 80, y: 250, w: 920, h: 900 };
    const c = Object.assign({ bg: '#FAF9F5', side: '#F0EEE6', ink: '#1F1E1D', muted: '#6B6A66', sel: '#E6E2D6', accent: '#D97757' }, o.light || {});
    const sl = 1 - E((t - o.s) / .45), a = Math.min(1, 1 - E((t - (o.e - .25)) / .25)); X.save(); X.globalAlpha *= a; X.translate(sl * 1100, 0); X.direction = 'ltr';
    SH(50, 22, .35); X.fillStyle = c.bg; RR(R.x, R.y, R.w, R.h, 26); X.fill(); NS(); X.fillStyle = c.side; RR(R.x, R.y, 250, R.h, 26); X.fill(); X.fillRect(R.x + 226, R.y, 24, R.h);
    if (o.brand) HK.img(o.brand, R.x + 30, R.y + 34, 44, 44); X.fillStyle = c.ink; X.font = '600 34px ' + lat(); X.textAlign = 'left'; X.textBaseline = 'middle'; X.fillText(o.name || '', R.x + 86, R.y + 57);
    const tabs = o.tabs || ['Chat', 'Code'], clicked = o.clickAt != null && t >= o.clickAt + .1, act = clicked ? o.clickTab : (o.startTab || tabs[0]);
    tabs.forEach((n, j) => { const y = R.y + 150 + j * 78, sel = n === act; if (sel) { X.fillStyle = c.sel; RR(R.x + 18, y - 30, 214, 60, 14); X.fill(); }
      X.fillStyle = sel ? c.ink : c.muted; X.font = (sel ? '600 ' : '500 ') + '30px ' + lat(); X.fillText(n, R.x + 44, y); });
    X.fillStyle = c.ink; X.font = '600 46px ' + lat(); X.textAlign = 'center'; const mx = R.x + 585;
    if (!clicked || !o.progress) { X.fillText(o.before || '', mx, R.y + 420); X.fillStyle = '#FFFFFF'; X.strokeStyle = '#DDD9CE'; X.lineWidth = 2; RR(R.x + 300, R.y + 520, 570, 110, 22); X.fill(); X.stroke(); }
    else { const ip = P(t, o.progress.s, o.progress.e), done = t >= o.progress.e + .05; X.fillText(done ? (o.done || 'Ready') : (o.after || 'Setting up…'), mx, R.y + 380);
      X.fillStyle = c.sel; RR(R.x + 330, R.y + 470, 510, 24, 12); X.fill(); X.fillStyle = c.accent; RR(R.x + 330, R.y + 470, 510 * EIO(ip), 24, 12); X.fill();
      X.fillStyle = c.muted; X.font = '500 28px ' + lat(); X.fillText(Math.round(ip * 100) + '%', mx, R.y + 540); if (done) check(mx, R.y + 660, 56, E((t - o.progress.e) / .3), true); }
    if (o.clickAt != null && t < o.clickAt + .45) { const j = Math.max(0, tabs.indexOf(o.clickTab)), pk = EIO(P(t, o.clickAt - .65, o.clickAt));
      HK.pointer(L(R.x + 700, R.x + 110, pk), L(R.y + 700, R.y + 150 + j * 78, pk), P(t, o.clickAt, o.clickAt + .2)); }
    X.restore(); };
  G.HK = HK;
})();
