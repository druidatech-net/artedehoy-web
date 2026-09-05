/* Animación de formación del logo Arte de Hoy — piezas originales de Carola.
   Generado por DruidaTech (Gustavo) 26/8/2026. El final es logocompleto exacto. */
(() => {
const cont = document.getElementById('logoAnim');
if(!cont) return;
const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
const META = {"W": 372, "H": 370, "cx": 181.2184503288663, "cy": 181.78715841922025, "pieces": [{"n": "rojo", "x": 59, "y": 1, "w": 307, "h": 280, "cx": 211.6, "cy": 138.2, "hex": "#d64830", "rmax": 162.6}, {"n": "celeste", "x": 1, "y": 37, "w": 213, "h": 289, "cx": 110.4, "cy": 186.4, "hex": "#7ec1d4", "rmax": 158.0}, {"n": "verde", "x": 17, "y": 127, "w": 262, "h": 235, "cx": 133.3, "cy": 246.0, "hex": "#369746", "rmax": 160.1}, {"n": "violeta", "x": 80, "y": 156, "w": 255, "h": 208, "cx": 212.8, "cy": 257.1, "hex": "#a76da1", "rmax": 134.7}, {"n": "amarillo", "x": 166, "y": 130, "w": 197, "h": 179, "cx": 265.7, "cy": 210.0, "hex": "#f5d055", "rmax": 105.7}], "words": [{"y": 37.83783783783784, "h": 18.91891891891892, "x0": 29.03225806451613, "x1": 67.20430107526882}, {"y": 51.75675675675676, "h": 8.91891891891892, "x0": 28.225806451612907, "x1": 69.35483870967742}, {"y": 63.108108108108105, "h": 13.783783783783784, "x0": 30.107526881720432, "x1": 61.29032258064516}]};
const ROOT = 'assets/img/logo-anim/';
const FILES = {rojo:'rojo.png', verde:'verde.png', amarillo:'amarillo.png',
  celeste:'celeste.png', violeta:'violeta.png', base:'manchas-completas.png',
  residuos:'residuos.png', ink_text:'ink-text.png', ink_rings:'ink-rings.png'};
const IW = META.W, IH = META.H, CX = META.cx, CY = META.cy;
const WORDS = META.words;
const ORDER = ["rojo","verde","amarillo","celeste","violeta"];
const P = {}; META.pieces.forEach(p => P[p.n] = p);

// ---- estructura ----
const mk = (tag, css) => { const e = document.createElement(tag); if(css) e.style.cssText = css; return e; };
const tintcv = mk('canvas', 'position:absolute;inset:-18%;width:136%;height:136%;pointer-events:none');
tintcv.width = 200; tintcv.height = 199;
const truth = mk('canvas', 'position:absolute;inset:0;width:100%;height:100%');
truth.width = IW; truth.height = IH;
const partcv = mk('canvas', 'position:absolute;inset:-30%;width:160%;height:160%;pointer-events:none');
const pen = mk('div', 'position:absolute;width:7px;height:7px;border-radius:50%;opacity:0;pointer-events:none;background:#fffdf7;box-shadow:0 0 8px 2px rgba(255,250,240,.95),0 0 20px 6px rgba(214,168,90,.45);transform:translate(-50%,-50%)');
cont.appendChild(tintcv); cont.appendChild(truth);

const IM = {};
const NAMES = [...ORDER, 'base', 'residuos', 'ink_text', 'ink_rings'];
for(const n of NAMES){ const im = new Image(); im.src = ROOT + FILES[n]; IM[n] = im; }

const FLY = {};
for(const n of ORDER){
  const p = P[n];
  const d = mk('div', `position:absolute;left:${p.x/IW*100}%;top:${p.y/IH*100}%;width:${p.w/IW*100}%;height:${p.h/IH*100}%;opacity:0;will-change:transform,opacity,filter`);
  const im = new Image(); im.src = ROOT + FILES[n]; im.alt = '';
  im.style.cssText = 'width:100%;height:100%;display:block';
  d.appendChild(im); cont.appendChild(d); FLY[n] = d;
}
const INK = {};
for(const key of ['ink_rings', 'ink_text']){
  const w = mk('div', 'position:absolute;inset:0');
  const cv = mk('canvas', 'position:absolute;inset:0;width:100%;height:100%');
  cv.width = IW; cv.height = IH;
  const im = new Image(); im.src = ROOT + FILES[key]; im.alt = '';
  im.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;visibility:hidden';
  w.appendChild(cv); w.appendChild(im); cont.appendChild(w);
  INK[key] = {cv, ctx: cv.getContext('2d'), img: im};
}
cont.appendChild(partcv); cont.appendChild(pen);
const mask = document.createElement('canvas'); mask.width = IW; mask.height = IH;
const mctx = mask.getContext('2d');
const trctx = truth.getContext('2d'), tctx = tintcv.getContext('2d'), pctx = partcv.getContext('2d');

const clamp = x => x<0?0:x>1?1:x;
const cubicOut = x => 1-Math.pow(1-x,3);
const sine = x => .5-.5*Math.cos(Math.PI*x);
const springSettle = x => x>=1?1:1+Math.pow(1-x,2)*Math.sin(x*Math.PI*2.2)*.05*(1-x);
const hexRGB = h => [parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)];
function makeSprites(hex){
  const [r,g,b] = hexRGB(hex);
  return [9,6,3].map(R => {
    const c = document.createElement('canvas'); c.width = c.height = R*2+4;
    const x = c.getContext('2d');
    const gr = x.createRadialGradient(R+2,R+2,0,R+2,R+2,R);
    gr.addColorStop(0,`rgba(${r},${g},${b},1)`); gr.addColorStop(.75,`rgba(${r},${g},${b},.95)`); gr.addColorStop(1,`rgba(${r},${g},${b},0)`);
    x.fillStyle = gr; x.beginPath(); x.arc(R+2,R+2,R,0,7); x.fill();
    return c; });
}
META.pieces.forEach(p => p.sprites = makeSprites(p.hex));

const SPLAT_T = {rojo:500, verde:970, amarillo:1350, celeste:1650, violeta:2320};
const WRITE = [[3450,4450],[4300,4750],[4650,5450]];
const RING_T = [5200,6150];
const FIN_T = 6350, T_END = 7500;
let particles = [], shakes = [], t0 = 0, raf = 0, lifted = false;

function stampTruth(n){
  mctx.drawImage(IM[n], P[n].x, P[n].y);
  if(n === 'rojo') mctx.drawImage(IM.residuos, 0, 0);
  trctx.clearRect(0,0,IW,IH);
  trctx.drawImage(mask,0,0);
  trctx.globalCompositeOperation = 'source-in';
  trctx.drawImage(IM.base,0,0);
  trctx.globalCompositeOperation = 'source-over';
}
function drawPieceFly(n, t){
  const p = P[n], el = FLY[n], ts = SPLAT_T[n], last = (n === 'violeta');
  if(t < ts){ el.style.opacity = 0; return; }
  const e = t - ts;
  if(!p._st){ p._st = true; stampTruth(n); spawnSplat(p, last); }
  if(e > 700){ if(!p._off){ p._off = true; el.style.opacity = 0; el.style.transform = 'none'; el.style.filter = 'none'; } return; }
  const fly = clamp(e / (last ? 170 : 140));
  const ang = Math.atan2(p.cy - CY, p.cx - CX);
  const dist = (1 - cubicOut(fly)) * 6;
  const s = springSettle(clamp(e/520));
  const sq = 1 + (last ? .08 : .06) * (1 - clamp(e/300));
  el.style.opacity = e < 260 ? 1 : String(1 - clamp((e-260)/420));
  el.style.filter = `blur(${(1-fly)*5}px) saturate(${1 + .15*(1 - clamp(e/700))})`;
  el.style.transform = `translate(${-Math.cos(ang)*dist}%,${-Math.sin(ang)*dist}%) rotate(${ang}rad) scale(${sq*s},${(2-sq)*s}) rotate(${-ang}rad)`;
}
function drawText(t){
  const L = INK.ink_text; if(L.done) return;
  const ctx = L.ctx;
  if(t > WRITE[2][1] + 120){ L.done = true; L.cv.style.display = 'none'; L.img.style.visibility = 'visible'; return; }
  if(t < WRITE[0][0]){ ctx.clearRect(0,0,IW,IH); return; }
  ctx.clearRect(0,0,IW,IH);
  let tip = null;
  for(let i = 0; i < 3; i++){
    const [a,b] = WRITE[i]; const p = clamp((t-a)/(b-a)); if(p <= 0) continue;
    const wd = WORDS[i];
    const x0 = wd.x0/100*IW, x1 = wd.x1/100*IW, R = wd.h/100*IH*.5;
    const bandT = (wd.y - wd.h/2)/100*IH, bandH = wd.h/100*IH;
    const xt = x0 + (x1-x0)*sine(p);
    ctx.save(); ctx.beginPath(); ctx.rect(0,bandT,IW,bandH); ctx.clip();
    ctx.beginPath(); ctx.rect(x0-R*.6, bandT-2, (xt-x0)+R*.9, bandH+4);
    ctx.fillStyle = '#fff'; ctx.filter = 'blur(4px)'; ctx.fill();
    ctx.restore();
    if(p < 1) tip = {x: xt/IW, y: wd.y/100};
    else if(i === 2 && p >= 1) tip = null;
  }
  ctx.globalCompositeOperation = 'source-in';
  ctx.drawImage(L.img,0,0);
  ctx.globalCompositeOperation = 'source-over';
  if(tip){ const r = cont.getBoundingClientRect();
    pen.style.opacity = 1;
    pen.style.left = (tip.x*r.width)+'px'; pen.style.top = (tip.y*r.height)+'px';
  } else pen.style.opacity = 0;
}
function drawRings(t){
  const L = INK.ink_rings; if(L.done) return;
  const ctx = L.ctx;
  const p = clamp((t - RING_T[0]) / (RING_T[1] - RING_T[0]));
  if(p <= 0){ ctx.clearRect(0,0,IW,IH); return; }
  if(p >= 1 && t > RING_T[1] + 80){ L.done = true; L.cv.style.display = 'none'; L.img.style.visibility = 'visible'; pen.style.opacity = 0; return; }
  ctx.clearRect(0,0,IW,IH);
  const a0 = -Math.PI/2, a1 = a0 + Math.PI*2*cubicOut(p);
  ctx.save(); ctx.beginPath(); ctx.moveTo(CX,CY); ctx.arc(CX,CY,IW,a0,a1); ctx.closePath();
  ctx.fillStyle = '#fff'; ctx.fill(); ctx.restore();
  ctx.globalCompositeOperation = 'source-in';
  ctx.drawImage(L.img,0,0);
  ctx.globalCompositeOperation = 'source-over';
  if(p < 1){ const r = cont.getBoundingClientRect();
    const rad = .30*r.width;
    pen.style.opacity = .9;
    pen.style.left = (CX/IW*r.width + Math.cos(a1)*rad)+'px';
    pen.style.top  = (CY/IH*r.height + Math.sin(a1)*rad)+'px'; }
}
function spawnSplat(p, last){
  const r = cont.getBoundingClientRect();
  const scale = r.width/IW;
  const cx = p.cx*scale, cy = p.cy*scale;
  const offX = partcv.clientWidth*.5 - r.width*.5, offY = partcv.clientHeight*.5 - r.height*.5;
  const ang = Math.atan2(p.cy - CY, p.cx - CX);
  const n = last ? 20 : (9 + Math.random()*4 | 0);
  for(let i = 0; i < n; i++){
    const cls = i < 2 ? 0 : (i < 6 ? 1 : 2);
    const a = ang + (Math.random()-.5)*1.22;
    const sp = (cls===0?170:cls===1?290:470) * (.7+Math.random()*.6) * scale;
    particles.push({x:cx+offX, y:cy+offY, vx:Math.cos(a)*sp, vy:Math.sin(a)*sp-55*scale,
      sp:p.sprites[cls], life:0, max:.5+Math.random()*.35, sc:.55+Math.random()*.75});
  }
  const [rr,gg,bb] = hexRGB(p.hex);
  const g = tctx.createRadialGradient(p.cx/IW*200, p.cy/IH*199, 4, p.cx/IW*200, p.cy/IH*199, 86);
  g.addColorStop(0,`rgba(${rr},${gg},${bb},.07)`); g.addColorStop(1,`rgba(${rr},${gg},${bb},0)`);
  tctx.fillStyle = g; tctx.fillRect(0,0,200,199);
  const k = ORDER.indexOf(p.n);
  shakes.push({t:performance.now(), amp:(last?7:2.5+k*.6), dir:ang+Math.PI/2, seed:Math.random()*9});
}
function stepParticles(dt){
  const g = 1500, drag = Math.pow(.90, dt*60);
  pctx.clearRect(0,0,partcv.width,partcv.height);
  particles = particles.filter(pt => {
    pt.life += dt; if(pt.life > pt.max) return false;
    pt.vx *= drag; pt.vy = pt.vy*drag + g*dt*(partcv.width/700);
    pt.x += pt.vx*dt; pt.y += pt.vy*dt;
    const f = 1 - pt.life/pt.max;
    pctx.globalAlpha = Math.min(1, f*2);
    const s = pt.sp.width*pt.sc*(1+(1-f)*.15);
    pctx.drawImage(pt.sp, pt.x-s/2, pt.y-s/2, s, s);
    return true; });
  pctx.globalAlpha = 1;
}
function stageShake(now){
  let dx = 0, dy = 0;
  shakes = shakes.filter(s => {
    const e = (now - s.t)/1000; if(e > .42) return false;
    const a = s.amp*Math.exp(-e/.06)*Math.sin(e*52+s.seed);
    dx += Math.cos(s.dir)*a; dy += Math.sin(s.dir)*a; return true; });
  return {dx,dy};
}
function finale(t){
  const e = t - FIN_T; if(e < 0) return;
  tintcv.style.opacity = String(1 - clamp(e/1100));
  if(!lifted && e > 150){ lifted = true; cont.classList.add('lift'); }
  if(e > 900) cont.classList.add('float');
}
let lastNow = 0;
function frame(now){
  const t = now - t0, dt = Math.min(.05, (now-lastNow)/1000 || 16); lastNow = now;
  for(const n of ORDER) drawPieceFly(n, t);
  drawText(t); drawRings(t);
  stepParticles(dt);
  const {dx,dy} = stageShake(now);
  cont.style.transform = `translate(${dx.toFixed(2)}px,${dy.toFixed(2)}px)`;
  finale(t);
  if(t < T_END) raf = requestAnimationFrame(frame);
  else finish();
}
function finish(){
  cancelAnimationFrame(raf);
  mctx.clearRect(0,0,IW,IH);
  for(const n of ORDER){ mctx.drawImage(IM[n], P[n].x, P[n].y);
    FLY[n].style.opacity = 0; FLY[n].style.transform = 'none'; FLY[n].style.filter = 'none'; }
  mctx.drawImage(IM.residuos,0,0);
  trctx.clearRect(0,0,IW,IH); trctx.drawImage(mask,0,0);
  trctx.globalCompositeOperation = 'source-in'; trctx.drawImage(IM.base,0,0);
  trctx.globalCompositeOperation = 'source-over';
  for(const k of ['ink_rings','ink_text']){ const L = INK[k]; L.done = true;
    L.cv.style.display = 'none'; L.img.style.visibility = 'visible'; }
  particles = []; pctx.clearRect(0,0,partcv.width,partcv.height);
  pen.style.opacity = 0;
  cont.style.transform = 'none';
  cont.classList.add('lift'); cont.classList.add('float');
  tintcv.style.opacity = '0';
}
function start(){
  if(RM){ finish(); return; }
  const r = cont.getBoundingClientRect();
  partcv.width = r.width*1.6; partcv.height = r.height*1.6;
  t0 = performance.now(); lastNow = t0;
  raf = requestAnimationFrame(frame);
}
let loaded = 0;
for(const n of NAMES){ const im = IM[n];
  const go = () => { if(++loaded === NAMES.length) start(); };
  im.complete ? go() : im.addEventListener('load', go);
}
})();
