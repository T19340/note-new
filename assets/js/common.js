/* ============================================================
   note-new · 그림 공통 엔진 (모든 값은 #note-data에서 계산)
   ============================================================ */
(function(){
'use strict';
Object.assign(CL,{ink:'#0A0A0A',ink2:'#2A2A2A',mute:'#6E6E6E',grid:'#ECECEC',axis:'#6E6E6E'});
const C = {asset:'#5B5B5B', liab:'#2D7EAA', eq:'#ED8936', up:'#0A0A0A', down:'#C53030', bal:'#A9A9A9',
  a1:'#5B5B5B', a2:'#7E7E7E', a3:'#A3A3A3', a4:'#C6C6C6', l1:'#2D7EAA', l2:'#6FA8C9', e1:'#ED8936', e2:'#F5B57C'};
const D = JSON.parse(document.getElementById('note-data').textContent);
function N(v, dec){
  const neg = v < 0; const a = Math.abs(v);
  const s = (dec ? a.toFixed(dec) : Math.round(a).toString()).split('.');
  s[0] = s[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  return (neg ? '−' : '') + s.join('.');
}
function P(v, dec){ return (v < 0 ? '−' : '') + Math.abs(v*100).toFixed(dec === undefined ? 1 : dec) + '%'; }
function el(id){ return document.getElementById(id); }
window.RSM = {C, D, N, P, el};

/* ---------- 공통: 카드 퀴즈 ---------- */
function Quiz(o){
  const grid = el(o.grid), fb = el(o.fb), ro = el(o.ro);
  let sel = -1; const res = o.items.map(() => null), picks = o.items.map(() => null);
  const lab = a => (o.labels && o.labels[a]) || a;
  function feedback(i){
    const it = o.items[i], ok = res[i];
    let h = (ok ? '<span class="yes">✓ 맞습니다.</span> ' : '<span class="no">✗ 아닙니다.</span> ')
      + (ok ? '' : '고른 답: ' + lab(picks[i]) + '. ') + '정답: <b>' + lab(it.a) + '</b>. ' + it.why;
    if (o.extra) h += o.extra(it);
    return h;
  }
  function draw(){
    grid.innerHTML = '';
    o.items.forEach((it, i) => {
      const d = document.createElement('div');
      d.className = 'qcard' + (i === sel ? ' sel' : '') + (res[i] === true ? ' right' : '') + (res[i] === false ? ' wrong' : '');
      d.innerHTML = '<b>' + it.t + '</b>' + (it.k ? '<span class="qk">' + it.k + '</span>' : '');
      d.addEventListener('click', () => {
        sel = i; draw();
        fb.innerHTML = res[i] === null ? '고른 카드: <b>' + it.t + '</b>. 아래에서 답을 누르세요.' : feedback(i);
      });
      grid.appendChild(d);
    });
    const n = res.filter(x => x !== null).length, r = res.filter(x => x === true).length;
    ro.innerHTML = '<span class="k">맞힌 수</span> ' + r + ' · <span class="k">풀어 본 수</span> ' + n + ' · <span class="k">전체</span> ' + o.items.length;
  }
  document.querySelectorAll(o.btnSel).forEach(b => b.addEventListener('click', () => {
    if (sel < 0) { fb.innerHTML = '먼저 카드를 하나 고르세요.'; return; }
    const pk = b.getAttribute('data-a'); picks[sel] = pk; res[sel] = (pk === o.items[sel].a);
    draw(); fb.innerHTML = feedback(sel);
  }));
  el(o.reset).addEventListener('click', () => { sel = -1; res.fill(null); picks.fill(null); fb.innerHTML = '카드를 하나 고르세요.'; draw(); });
  draw();
}
window.RSM.Quiz = Quiz;


/* ---------- 공통: 사용자 눈금 축 (큰 수를 지수표기 없이) ---------- */
function axes2(F, o){
  const c = F.ctx; c.save();
  const xs = [], ys = [];
  for (let i = Math.ceil(F.xr[0] / o.sx - 1e-9); i * o.sx <= F.xr[1] + 1e-9; i++) xs.push(i * o.sx);
  for (let i = Math.ceil(F.yr[0] / o.sy - 1e-9); i * o.sy <= F.yr[1] + 1e-9; i++) ys.push(i * o.sy);
  c.strokeStyle = CL.grid; c.lineWidth = 1;
  xs.forEach(x => { c.beginPath(); c.moveTo(F.X(x), F.pad.t); c.lineTo(F.X(x), F.pad.t + F.ph); c.stroke(); });
  ys.forEach(y => { c.beginPath(); c.moveTo(F.pad.l, F.Y(y)); c.lineTo(F.pad.l + F.pw, F.Y(y)); c.stroke(); });
  c.strokeStyle = CL.axis; c.lineWidth = 1.2; c.beginPath();
  c.moveTo(F.pad.l, F.pad.t + F.ph); c.lineTo(F.pad.l + F.pw, F.pad.t + F.ph);
  c.moveTo(F.pad.l, F.pad.t); c.lineTo(F.pad.l, F.pad.t + F.ph); c.stroke();
  c.font = '10.5px ui-monospace,Consolas,monospace'; c.fillStyle = CL.mute;
  c.textAlign = 'center'; c.textBaseline = 'top';
  xs.forEach(x => { const t = o.fx ? o.fx(x) : String(x); if (t) c.fillText(t, F.X(x), F.pad.t + F.ph + 5); });
  c.textAlign = 'right'; c.textBaseline = 'middle';
  ys.forEach(y => { const t = o.fy ? o.fy(y) : String(y); if (t) c.fillText(t, F.pad.l - 5, F.Y(y)); });
  c.fillStyle = CL.ink2; c.font = '600 11px ui-monospace,Consolas,monospace';
  if (o.xlab) { c.textAlign = 'right'; c.textBaseline = 'bottom'; c.fillText(o.xlab, F.pad.l + F.pw, F.pad.t + F.ph - 4); }
  if (o.ylab) { c.textAlign = 'left'; c.textBaseline = 'top'; c.fillText(o.ylab, F.pad.l + 6, F.pad.t + 2); }
  c.restore();
}
window.RSM.axes2 = axes2;

/* ---------- 공통: 폭포(다리) 그림 ---------- */
function waterfall(cv, steps, o){
  o = o || {};
  let run = 0, lo = 0, hi = 0;
  const bars = steps.map(s => {
    let a, b;
    if (s.type === 'bal') { a = 0; b = s.v; run = s.v; }
    else { a = run; b = run + s.v; run = b; }
    lo = Math.min(lo, a, b); hi = Math.max(hi, a, b);
    return {s, a, b};
  });
  const pad = (hi - lo) * 0.14 || 1;
  const F = new VZ.Frame(cv, [0, steps.length], [lo - (lo < 0 ? pad : 0), hi + pad], {l: 62, r: 12, t: 18, b: 40});
  F.clear();
  const c = F.ctx;
  // 가로 눈금
  const st = VZ.niceStep([F.yr[0], F.yr[1]]);
  c.save(); c.font = '10.5px ui-monospace,Consolas,monospace'; c.fillStyle = CL.mute; c.textAlign = 'right'; c.textBaseline = 'middle';
  for (let y = Math.ceil(F.yr[0] / st) * st; y <= F.yr[1]; y += st) {
    c.strokeStyle = CL.grid; c.beginPath(); c.moveTo(F.pad.l, F.Y(y)); c.lineTo(F.pad.l + F.pw, F.Y(y)); c.stroke();
    c.fillText(N(y), F.pad.l - 5, F.Y(y));
  }
  c.strokeStyle = CL.axis; c.lineWidth = 1.2; c.beginPath(); c.moveTo(F.pad.l, F.Y(0)); c.lineTo(F.pad.l + F.pw, F.Y(0)); c.stroke();
  c.restore();
  bars.forEach((B, i) => {
    const x0 = F.X(i + 0.18), x1 = F.X(i + 0.82), y0 = F.Y(Math.max(B.a, B.b)), y1 = F.Y(Math.min(B.a, B.b));
    const isBal = B.s.type === 'bal';
    c.save();
    c.fillStyle = isBal ? C.bal : (B.s.v >= 0 ? C.up : C.down);
    if (B.s.ghost) c.globalAlpha = 0.18;
    c.fillRect(x0, y0, x1 - x0, Math.max(1.5, y1 - y0));
    c.restore();
    if (i < bars.length - 1 && !B.s.ghost) {
      c.save(); c.strokeStyle = '#9A9A9A'; c.setLineDash([3, 3]); c.beginPath();
      c.moveTo(x1, F.Y(B.b)); c.lineTo(F.X(i + 1.18), F.Y(B.b)); c.stroke(); c.restore();
    }
    // 값
    c.save(); c.font = '600 11px ui-monospace,Consolas,monospace'; c.textAlign = 'center';
    c.fillStyle = isBal ? CL.ink2 : (B.s.v >= 0 ? CL.ink : C.down);
    if (B.s.ghost) c.fillStyle = '#BBBBBB';
    const txt = isBal ? N(B.s.v) : (B.s.v >= 0 ? '+' : '') + N(B.s.v);
    const top = Math.min(y0, y1);
    if (B.b >= B.a || isBal && B.s.v >= 0) { c.textBaseline = 'bottom'; c.fillText(txt, (x0 + x1) / 2, top - 3); }
    else { c.textBaseline = 'top'; c.fillText(txt, (x0 + x1) / 2, Math.max(y0, y1) + 3); }
    c.restore();
    // 라벨
    c.save(); c.font = '11px system-ui,sans-serif'; c.fillStyle = CL.ink2; c.textAlign = 'center'; c.textBaseline = 'top';
    B.s.lab.split('\n').forEach((ln, k) => c.fillText(ln, (x0 + x1) / 2, F.pad.t + F.ph + 6 + k * 13));
    c.restore();
  });
  return F;
}
window.RSM.waterfall = waterfall;

})();
