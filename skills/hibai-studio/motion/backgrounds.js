/* HibAI backgrounds — drawn live in code, so they stay sharp at any size and move.
   One file for both the dashboard previews and the video engine (split screens, full-screen visuals).

   HBG.draw(ctx, style, t, W, H, opts)
     style: black · white · whitegrid · gradient · blur · topo · grid · ribbon · glow · orbit · mesh · warp · shapes · brand · color · image
     t: seconds (animation) · W, H: size in px
     opts: {brand: true|false  (use the user's colours or the original look),
            pal: {bg, ink, acc, clay},  color: '#hex' (style "color"),  img: Image (style "image"),  frame: Image/canvas (style "blur") }
   HBG.list → [{v, n}] the styles with their Darija names. */
(function () {
  const G = typeof window !== 'undefined' ? window : globalThis;
  const hx = h => { h = String(h || '#000').replace('#', ''); if (h.length === 3) h = h.split('').map(c => c + c).join(''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); };
  const rgba = (h, a) => { const c = hx(h); return `rgba(${c[0]},${c[1]},${c[2]},${a})`; };
  const mix = (a, b, k) => { const A = hx(a), B = hx(b); return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * k).toString(16).padStart(2, '0')).join(''); };
  const lum = h => { const c = hx(h); return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255; };
  /* smooth 2-D noise (value noise with quintic fade) — deterministic */
  const P = new Uint8Array(512); (function () { const p = [...Array(256).keys()]; let s = 7; for (let i = 255; i > 0; i--) { s = (s * 16807) % 2147483647; const j = s % (i + 1); [p[i], p[j]] = [p[j], p[i]]; } for (let i = 0; i < 512; i++) P[i] = p[i & 255]; })();
  const fade = x => x * x * x * (x * (x * 6 - 15) + 10), lerp = (a, b, k) => a + (b - a) * k;
  const hash = (x, y) => P[(P[x & 255] + y) & 255] / 255;
  const noise = (x, y) => { const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = fade(xf), v = fade(yf);
    return lerp(lerp(hash(xi, yi), hash(xi + 1, yi), u), lerp(hash(xi, yi + 1), hash(xi + 1, yi + 1), u), v); };
  const fbm = (x, y) => noise(x, y) * 0.6 + noise(x * 2.1 + 5.2, y * 2.1 + 1.3) * 0.3 + noise(x * 4.3 + 9.1, y * 4.3 + 3.7) * 0.1;

  const DEF = { bg: '#101828', ink: '#F5F7FA', acc: '#F2B33D', clay: '#C98B18' };
  function colors(style, o) {
    const p = Object.assign({}, DEF, o.pal || {}), brand = o.brand !== false;
    const orig = { topo: ['#050505', '#FFFFFF'], grid: ['#141414', '#FFFFFF'], ribbon: ['#1A1A1A', '#FF5A2E'], glow: ['#070A1C', '#2B3BFF'],
      orbit: ['#040817', '#FFFFFF'], mesh: ['#1B0B33', '#9B5CFF'], warp: ['#E9E9EA', '#000000'], shapes: ['#22C55E', '#3B82F6'],
      whitegrid: ['#F4F4F2', '#000000'], gradient: [p.bg, p.acc], brand: [p.bg, p.acc] };
    if (!brand && orig[style]) return { bg: orig[style][0], fg: orig[style][1], acc: orig[style][1], p };
    const dark = lum(p.bg) < 0.5;
    return { bg: p.bg, fg: dark ? '#FFFFFF' : '#000000', acc: p.acc, clay: p.clay || mix(p.acc, '#000000', 0.25), p };
  }

  function topo(X, t, W, H, c, density) {
    const cols = 72, rows = Math.round(cols * H / W), sx = W / cols, sy = H / rows, f = [], drift = t * 0.035;
    for (let j = 0; j <= rows; j++) { f[j] = []; for (let i = 0; i <= cols; i++) f[j][i] = fbm(i * 0.055 + drift, j * 0.055 - drift * 0.6); }
    X.lineWidth = Math.max(1, W / 540); X.lineJoin = 'round';
    const levels = density || 8;   /* 7 contour lines (was 10 — 30% calmer, HibAI feedback) */
    for (let L = 1; L < levels; L++) { const lv = 0.18 + L * (0.64 / levels); X.strokeStyle = rgba(c.fg, 0.16 + 0.34 * (L % 3 === 0 ? 1 : 0.55)); X.beginPath();
      for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
        const a = f[j][i], b = f[j][i + 1], d = f[j + 1][i], e = f[j + 1][i + 1], x = i * sx, y = j * sy;
        const idx = (a > lv) | ((b > lv) << 1) | ((e > lv) << 2) | ((d > lv) << 3); if (idx === 0 || idx === 15) continue;
        const T = [x + sx * (lv - a) / (b - a), y], R = [x + sx, y + sy * (lv - b) / (e - b)], B = [x + sx * (lv - d) / (e - d), y + sy], Lt = [x, y + sy * (lv - a) / (d - a)];
        const seg = { 1: [Lt, T], 2: [T, R], 3: [Lt, R], 4: [R, B], 5: [Lt, T, R, B], 6: [T, B], 7: [Lt, B], 8: [B, Lt], 9: [B, T], 10: [T, R, B, Lt], 11: [B, R], 12: [R, Lt], 13: [R, T], 14: [T, Lt] }[idx];
        for (let k = 0; k < seg.length; k += 2) { X.moveTo(seg[k][0], seg[k][1]); X.lineTo(seg[k + 1][0], seg[k + 1][1]); } }
      X.stroke(); }
  }
  function gridLines(X, W, H, step, col, warp, t) {
    X.strokeStyle = col; X.lineWidth = Math.max(1, W / 720);
    const dx = (x, y) => warp ? Math.sin(y / H * 5 + t * 0.6) * warp * W : 0, dy = (x, y) => warp ? Math.sin(x / W * 4 - t * 0.5) * warp * H * 0.6 : 0;
    for (let x = 0; x <= W + step; x += step) { X.beginPath(); for (let y = 0; y <= H; y += step / 3) { const px = x + dx(x, y), py = y + dy(x, y); y ? X.lineTo(px, py) : X.moveTo(px, py); } X.stroke(); }
    for (let y = 0; y <= H + step; y += step) { X.beginPath(); for (let x = 0; x <= W; x += step / 3) { const px = x + dx(x, y), py = y + dy(x, y); x ? X.lineTo(px, py) : X.moveTo(px, py); } X.stroke(); }
  }
  const blob = (X, x, y, r, col, a) => { const g = X.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, rgba(col, a)); g.addColorStop(1, rgba(col, 0)); X.fillStyle = g; X.fillRect(x - r, y - r, r * 2, r * 2); };

  const HBG = {};
  HBG.list = [{ v: 'black', n: 'كحل' }, { v: 'white', n: 'بيض' }, { v: 'whitegrid', n: 'بيض بشبكة' }, { v: 'gradient', n: 'تدرّج' }, { v: 'blur', n: 'ضبابي' },
    { v: 'topo', n: 'خطوط طوبو' }, { v: 'grid', n: 'شبكة' }, { v: 'ribbon', n: 'شريط مضوي' }, { v: 'glow', n: 'ضو من تحت' }, { v: 'orbit', n: 'مدارات' },
    { v: 'mesh', n: 'ميش ملوّن' }, { v: 'warp', n: 'شبكة ملوية' }, { v: 'shapes', n: 'أشكال' }, { v: 'brand', n: 'خليط البراند' }, { v: 'color', n: 'لون واحد' }, { v: 'image', n: 'صورة ديالي' }];
  HBG.draw = function (X, style, t, W, H, o) {
    o = o || {}; const c = colors(style, o), u = Math.min(W, H);
    X.save();
    switch (style) {
      case 'black': X.fillStyle = '#060606'; X.fillRect(0, 0, W, H); blob(X, W / 2, H * 0.42, u * 0.9, '#FFFFFF', 0.05); break;
      case 'white': X.fillStyle = '#F7F7F5'; X.fillRect(0, 0, W, H); blob(X, W / 2, H * 0.4, u, '#FFFFFF', 0.8); break;
      case 'whitegrid': X.fillStyle = c.bg === '#F4F4F2' ? '#F4F4F2' : (lum(c.p.bg) > 0.5 ? c.p.bg : '#F4F4F2'); X.fillRect(0, 0, W, H);
        blob(X, W / 2, H * 0.45, u * 0.95, '#FFFFFF', 0.9); gridLines(X, W, H, u / 9, 'rgba(0,0,0,0.10)'); blob(X, W / 2, H * 0.45, u * 0.55, '#FFFFFF', 0.55); break;
      case 'gradient': { const g = X.createLinearGradient(0, 0, W * 0.3, H); g.addColorStop(0, c.p.bg); g.addColorStop(0.55, mix(c.p.bg, c.acc, 0.45)); g.addColorStop(1, c.acc);
        X.fillStyle = g; X.fillRect(0, 0, W, H); blob(X, W * (0.3 + 0.1 * Math.sin(t * 0.4)), H * 0.25, u * 0.8, '#FFFFFF', 0.12); break; }
      case 'blur': if (o.frame) { X.filter = `blur(${Math.round(u / 18)}px) brightness(0.8)`; X.drawImage(o.frame, -W * 0.1, -H * 0.1, W * 1.2, H * 1.2); X.filter = 'none'; }
        else { X.fillStyle = '#8C8A90'; X.fillRect(0, 0, W, H); blob(X, W * 0.3, H * 0.4, u * 0.7, '#D4C3B0', 0.9); blob(X, W * 0.72, H * 0.66, u * 0.75, '#5E5B6E', 0.9); }
        X.fillStyle = 'rgba(0,0,0,0.18)'; X.fillRect(0, 0, W, H); break;
      case 'topo': X.fillStyle = c.bg; X.fillRect(0, 0, W, H); topo(X, t, W, H, c); break;
      case 'grid': X.fillStyle = c.bg; X.fillRect(0, 0, W, H); blob(X, W / 2, H * 0.45, u * 0.8, c.fg, 0.10); gridLines(X, W, H, u / 10, rgba(c.fg, 0.13)); break;
      case 'ribbon': { X.fillStyle = c.bg; X.fillRect(0, 0, W, H); const y0 = H * 0.5, a = H * 0.08;
        for (let k = 0; k < 3; k++) { X.beginPath(); X.lineCap = 'round'; X.lineWidth = u * (0.14 - k * 0.04); X.strokeStyle = rgba(c.acc, 0.22 + k * 0.25);
          X.shadowColor = c.acc; X.shadowBlur = u * 0.12; for (let i = 0; i <= 40; i++) { const x = -W * 0.1 + i / 40 * W * 1.2, y = y0 + Math.sin(i / 40 * Math.PI * 1.6 + t * 0.8) * a - (i / 40) * H * 0.12;
            i ? X.lineTo(x, y) : X.moveTo(x, y); } X.stroke(); } X.shadowBlur = 0; break; }
      case 'glow': { const g = X.createLinearGradient(0, 0, 0, H); g.addColorStop(0, mix(c.bg, '#000000', 0.5)); g.addColorStop(1, c.bg); X.fillStyle = g; X.fillRect(0, 0, W, H);
        const y = H * (0.78 + 0.02 * Math.sin(t * 0.7)); X.save(); X.translate(W / 2, y); X.scale(1.8, 0.45); blob(X, 0, 0, u * 0.62, c.acc, 0.95); X.restore(); break; }
      case 'orbit': { const g = X.createLinearGradient(0, 0, 0, H); g.addColorStop(0, mix(c.bg, '#000000', 0.55)); g.addColorStop(1, mix(c.bg, c.acc, 0.25)); X.fillStyle = g; X.fillRect(0, 0, W, H);
        [[W * 0.95, H * 0.1, u * 0.62, 0.35], [W * 0.05, H * 0.92, u * 0.7, -0.28]].forEach(([cx, cy, r, sp], k) => { X.strokeStyle = rgba(c.fg, 0.35); X.lineWidth = Math.max(1.2, u / 400);
          X.beginPath(); X.arc(cx, cy, r, 0, 7); X.stroke(); for (let d = 0; d < 2; d++) { const an = t * sp + d * 1.4 + k, x = cx + Math.cos(an) * r, y = cy + Math.sin(an) * r, s = u * 0.022;
            X.save(); X.translate(x, y); X.rotate(Math.PI / 4); X.fillStyle = '#FFFFFF'; X.shadowColor = '#FFFFFF'; X.shadowBlur = s * 2; X.fillRect(-s, -s, s * 2, s * 2); X.restore(); } }); break; }
      case 'mesh': X.fillStyle = mix(c.bg, '#000000', 0.3); X.fillRect(0, 0, W, H);
        blob(X, W * (0.3 + 0.12 * Math.sin(t * 0.5)), H * (0.28 + 0.06 * Math.cos(t * 0.4)), u * 0.95, c.acc, 0.85);
        blob(X, W * (0.75 + 0.1 * Math.cos(t * 0.45)), H * (0.72 + 0.05 * Math.sin(t * 0.5)), u * 0.9, c.clay || c.acc, 0.75);
        blob(X, W * 0.5, H * 0.5, u * 0.6, '#FFFFFF', 0.10); break;
      case 'warp': { const light = lum(c.bg) > 0.5; X.fillStyle = light ? c.bg : '#E9E9EA'; X.fillRect(0, 0, W, H);
        blob(X, W / 2, H / 2, u * 0.9, '#FFFFFF', 0.8); gridLines(X, W, H, u / 9, 'rgba(0,0,0,0.28)', 0.025, t); break; }
      case 'shapes': X.fillStyle = c.bg; X.fillRect(0, 0, W, H); { const r = u * 0.42, y = H * (0.5 + 0.02 * Math.sin(t * 0.8)), g = X.createLinearGradient(W / 2 - r, y - r, W / 2 + r, y + r);
        g.addColorStop(0, c.acc); g.addColorStop(1, mix(c.acc, '#FFFFFF', 0.35)); X.fillStyle = g; X.shadowColor = 'rgba(0,0,0,0.35)'; X.shadowBlur = u * 0.08; X.beginPath(); X.arc(W / 2, y, r, 0, 7); X.fill(); X.shadowBlur = 0;
        X.fillStyle = rgba(c.fg, 0.9); X.save(); X.translate(W * 0.82, H * 0.16); X.rotate(t * 0.4); X.fillRect(-u * 0.04, -u * 0.04, u * 0.08, u * 0.08); X.restore();
        X.beginPath(); X.arc(W * 0.16, H * 0.84 + Math.sin(t) * u * 0.02, u * 0.05, 0, 7); X.fill(); } break;
      case 'brand': { const g = X.createLinearGradient(0, H, W, 0); g.addColorStop(0, c.p.bg); g.addColorStop(0.6, mix(c.p.bg, c.acc, 0.5)); g.addColorStop(1, c.acc); X.fillStyle = g; X.fillRect(0, 0, W, H);
        topo(X, t, W, H, { fg: '#FFFFFF' }, 7); blob(X, W * 0.7, H * 0.28, u * 0.6, '#FFFFFF', 0.18); break; }
      case 'color': X.fillStyle = o.color || c.acc; X.fillRect(0, 0, W, H); blob(X, W / 2, H * 0.4, u, '#FFFFFF', 0.12); break;
      case 'image': if (o.img && o.img.naturalWidth) { const s = Math.max(W / o.img.naturalWidth, H / o.img.naturalHeight); X.drawImage(o.img, (W - o.img.naturalWidth * s) / 2, (H - o.img.naturalHeight * s) / 2, o.img.naturalWidth * s, o.img.naturalHeight * s); }
        else { X.fillStyle = '#2A2A2E'; X.fillRect(0, 0, W, H); } break;
      default: X.fillStyle = c.bg; X.fillRect(0, 0, W, H);
    }
    X.restore();
  };
  G.HBG = HBG;
})();
