#!/usr/bin/env python3
"""Genera artedehoy-reveal.html: animación de formación real del logo con las piezas exactas."""
import numpy as np, json, base64, pathlib, sys
from PIL import Image

# Uso:  python3 generar-animacion.py <carpeta-con-las-piezas>
SP = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
PZ = SP / "piezas"
meta = json.load(open(PZ / "meta.json"))
W, H = meta["W"], meta["H"]

# ---- bandas Y de las 3 palabras (desde la tinta real) ----
it = np.asarray(Image.open(PZ / "ink_text.png"))[..., 3].astype(float)
rows = it.sum(axis=1)
y0, y1 = meta["text_y"] if "text_y" in meta else (int(np.argmax(rows > rows.max()*0.03)), 0)
nz = np.where(rows > rows.max() * 0.03)[0]
y0, y1 = int(nz.min()), int(nz.max())
# minimos locales para partir en 3 palabras
seg = rows[y0:y1]
third = len(seg) // 3
m1 = y0 + third//2 + int(np.argmin(seg[third//2: third + third//2]))
m2 = y0 + third + third//2 + int(np.argmin(seg[third + third//2: 2*third + third//2]))
bands = [(y0, m1), (m1, m2), (m2, y1)]
words = []
for (a, b) in bands:
    band = it[a:b]
    cols = band.sum(axis=0)
    cnz = np.where(cols > cols.max() * 0.04)[0]
    words.append({"y": (a + b) / 2 / H * 100, "h": (b - a) / H * 100,
                  "x0": cnz.min() / W * 100, "x1": cnz.max() / W * 100})
print("bandas:", [(round(w['y']), round(w['x0']), round(w['x1'])) for w in words])

# ---- radio máximo de cada mancha desde su centroide (para la máscara-blob) ----
for p in meta["pieces"]:
    a = np.asarray(Image.open(PZ / f"color_{p['i']}.png"))[..., 3]
    ys, xs = np.where(a > 25)
    cxp, cyp = p["cx_pct"] * W / 100, p["cy_pct"] * H / 100
    d = np.hypot(xs - cxp, ys - cyp)
    p["rmax_pct"] = round(float(np.percentile(d, 99.8) / W * 100) + 1.5, 1)
print("rmax:", [(p['i'], p['rmax_pct']) for p in meta["pieces"]])

def b64(name):
    return "data:image/png;base64," + base64.b64encode((PZ / name).read_bytes()).decode()

PIECES_JS = json.dumps([{**p} for p in meta["pieces"]])
WORDS_JS = json.dumps(words)
IMGS = {f"color_{i}": b64(f"color_{i}.png") for i in range(8)}
IMGS["ink_text"] = b64("ink_text.png"); IMGS["ink_rings"] = b64("ink_rings.png")

html = r'''<title>Arte de Hoy</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500&display=swap">
<style>
  :root{ --ground:#0B0A09; --ink:#f2ede6; --muted:#8d8378; }
  *{box-sizing:border-box}
  html,body{height:100%}
  body{margin:0; background:var(--ground); color:var(--ink);
    font-family:"Poppins",system-ui,sans-serif; overflow:hidden;
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    min-height:100dvh; gap:clamp(14px,2.6vh,30px)}
  #wrap{position:relative}
  #stage{position:relative; width:min(88vw,66vh,600px); aspect-ratio:894/836; will-change:transform}
  #tintcv,#partcv{position:absolute; pointer-events:none}
  #tintcv{inset:-18%; width:136%; height:136%}
  #partcv{inset:-25%; width:150%; height:150%}
  .pieceW{position:absolute; inset:0; will-change:transform}
  .pieceW canvas,.pieceW img{position:absolute; inset:0; width:100%; height:100%; display:block}
  .pieceW img{visibility:hidden}
  #pulse{position:absolute; inset:-30%; border-radius:50%; pointer-events:none; opacity:0;
    background:radial-gradient(circle, rgba(255,252,245,.55) 0%, rgba(255,252,245,0) 62%)}
  #pen{position:absolute; width:8px; height:8px; border-radius:50%; opacity:0; pointer-events:none;
    background:#fffdf7; box-shadow:0 0 10px 3px rgba(255,250,235,.85), 0 0 26px 8px rgba(255,240,210,.35);
    transform:translate(-50%,-50%)}
  #vig{position:fixed; inset:0; pointer-events:none;
    background:radial-gradient(115% 115% at 50% 46%, transparent 46%, rgba(0,0,0,.5) 100%)}
  #grain{position:fixed; inset:0; pointer-events:none; opacity:.05; mix-blend-mode:overlay}
  #kicker{font-size:clamp(11px,1.4vw,13px); font-weight:500; text-transform:uppercase;
    color:var(--muted); letter-spacing:.5em; padding-left:.5em; opacity:0}
  #controls{position:fixed; bottom:20px; left:0; right:0; display:flex; justify-content:center; z-index:5}
  #replay{appearance:none; cursor:pointer; font-family:inherit; font-size:13px; color:var(--muted);
    background:transparent; border:1px solid rgba(141,131,120,.35); border-radius:999px;
    padding:8px 18px; display:inline-flex; align-items:center; gap:8px; opacity:0; transition:.25s;
    pointer-events:none}
  #replay.on{opacity:1; pointer-events:auto}
  #replay:hover,#replay:focus-visible{color:var(--ink); border-color:rgba(242,237,230,.5); outline:none}
  #replay:focus-visible{box-shadow:0 0 0 3px rgba(242,237,230,.25)}
  #replay svg{width:13px; height:13px}
  @media (prefers-reduced-motion: reduce){
    .pieceW img{visibility:visible !important}
    .pieceW canvas,#pen,#partcv,#tintcv{display:none !important}
    #kicker{opacity:1 !important; letter-spacing:.24em}
    #replay{display:none}
  }
</style>

<div id="vig"></div><div id="grain"></div>
<div id="wrap">
  <div id="stage" aria-label="Logo de Arte de Hoy formándose: la caligrafía se escribe, los aros se dibujan y ocho salpicaduras de acuarela completan el logo original.">
    <canvas id="tintcv"></canvas>
    <div id="pulse"></div>
    <!--LAYERS-->
    <canvas id="partcv"></canvas>
    <div id="pen"></div>
  </div>
</div>
<p id="kicker">Academia de arte</p>
<div id="controls">
  <button id="replay" type="button">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v4h4"/></svg>
    Repetir
  </button>
</div>

<script>
(() => {
const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
const PIECES = __PIECES__;
const WORDS  = __WORDS__;
const IW = __W__, IH = __H__, CX = __CX__, CY = __CY__;
const ORDER = [0,3,1,6,2,4,7,5];               // zigzag; el 5 (celeste, la más grande) remata
const stage = document.getElementById('stage');
const pen = document.getElementById('pen');
const pulse = document.getElementById('pulse');
const kicker = document.getElementById('kicker');
const replayB = document.getElementById('replay');

// ---- grain de taller (estático) ----
(function(){ const c=document.createElement('canvas'); c.width=c.height=128;
  const x=c.getContext('2d'), d=x.createImageData(128,128);
  for(let i=0;i<d.data.length;i+=4){ const v=110+Math.random()*70|0; d.data[i]=d.data[i+1]=d.data[i+2]=v; d.data[i+3]=255; }
  x.putImageData(d,0,0);
  document.getElementById('grain').style.background='url('+c.toDataURL()+')';
})();

// ---- capas: cada pieza = wrapper con canvas (animación) + img (estado final exacto) ----
const layers = {};   // key -> {wrap, cv, ctx, img, ready}
const stack = ['color_0','color_1','color_2','color_3','color_4','color_5','color_6','color_7','ink_rings','ink_text'];
const SRC = __IMGS__;
const HALF = 2;      // resolución de canvas = imagen/HALF
for (const key of stack){
  const w = document.createElement('div'); w.className='pieceW'; w.dataset.k=key;
  const cv = document.createElement('canvas'); cv.width=IW/HALF; cv.height=IH/HALF;
  const im = new Image(); im.src = SRC[key]; im.alt='';
  w.appendChild(cv); w.appendChild(im);
  stage.insertBefore(w, document.getElementById('partcv'));
  layers[key] = {wrap:w, cv, ctx:cv.getContext('2d'), img:im};
}

const tintcv = document.getElementById('tintcv'), tctx = tintcv.getContext('2d');
tintcv.width = 200; tintcv.height = 187;
const partcv = document.getElementById('partcv'), pctx = partcv.getContext('2d');

// ---- utilidades ----
const clamp = x => x<0?0:x>1?1:x;
const expoOut = x => x>=1?1:1-Math.pow(2,-10*x);
const cubicOut = x => 1-Math.pow(1-x,3);
const sine = x => .5-.5*Math.cos(Math.PI*x);
function springSettle(x){        // 1 sola oscilación amortiguada, termina EXACTO en 1
  if(x>=1) return 1;
  return 1 + Math.pow(1-x,2)*Math.sin(x*Math.PI*2.2)*0.05*(1-x);
}
function blobR(base, th, s){     // radio con ruido angular (semilla fija por pieza)
  return base*(1 + .20*Math.sin(3*th+s) + .12*Math.sin(7*th+s*1.7) + .07*Math.sin(11*th+s*2.6));
}
function hexRGB(h){ return [parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)]; }

// sprites de gota (pre-render, 3 tamaños por pieza)
function makeSprites(hex){
  const [r,g,b]=hexRGB(hex);
  return [10,6,3].map(R=>{
    const c=document.createElement('canvas'); c.width=c.height=R*2+4;
    const x=c.getContext('2d');
    const gr=x.createRadialGradient(R+2,R+2,0,R+2,R+2,R);
    gr.addColorStop(0,`rgba(${r},${g},${b},1)`);
    gr.addColorStop(.75,`rgba(${r},${g},${b},.95)`);
    gr.addColorStop(1,`rgba(${r},${g},${b},0)`);
    x.fillStyle=gr; x.beginPath(); x.arc(R+2,R+2,R,0,7); x.fill();
    return c;
  });
}
PIECES.forEach(p=>p.sprites=makeSprites(p.hex));

// ---- TIMELINE (ms) ----
const SPLAT_T = [3250,3720,4120,4450,4720,4940,5120,5560];
const T_END = 8200;
let particles=[], shakes=[], t0=0, raf=0, done=false;

function pieceState(idx, t){     // progreso de una mancha
  const k = ORDER.indexOf(idx);
  const ts = SPLAT_T[k];
  const last = (k===7);
  if(t < ts) return null;
  const e = t - ts;
  const fly = clamp(e/(last?170:140));
  // máscara: 60% de una, 92% en 90ms, sangrado a 100% en 400ms más
  let mr;
  if(e<=90) mr = .60 + .32*expoOut(e/90);
  else      mr = .92 + .08*cubicOut(clamp((e-90)/(last?520:400)));
  const dry = clamp((e-450)/500);            // secado: borde 8px -> 0
  const wet = 1-dry;
  return {e, fly, mr, dry, wet, last, k, ts};
}

function drawPiece(p, st){
  const L = layers['color_'+p.i];
  if(st.e > 1100 && L.done){ return; }
  const ctx=L.ctx, w=IW/HALF, h=IH/HALF;
  if(st.e > 1100 && !L.done){                 // secó: promover al PNG exacto
    L.done=true; L.cv.style.display='none'; L.img.style.visibility='visible';
    L.wrap.style.transform='none';
    return;
  }
  ctx.clearRect(0,0,w,h);
  // máscara-blob que invade como agua
  const cx=p.cx_pct/100*w, cy=p.cy_pct/100*h;
  const base=p.rmax_pct/100*w*st.mr, seed=p.i*13.7;
  ctx.save();
  ctx.filter = st.dry<1 ? `blur(${(8*(1-st.dry))/HALF+ .01}px)` : 'none';
  ctx.beginPath();
  for(let a=0;a<=64;a++){ const th=a/64*Math.PI*2, r=blobR(base,th,seed);
    const x=cx+Math.cos(th)*r, y=cy+Math.sin(th)*r;
    a?ctx.lineTo(x,y):ctx.moveTo(x,y); }
  ctx.closePath(); ctx.fillStyle='#fff'; ctx.fill();
  ctx.restore();
  ctx.globalCompositeOperation='source-in';
  ctx.filter = st.wet>0 ? `saturate(${1+.14*st.wet}) brightness(${1+.05*st.wet})` : 'none';
  ctx.drawImage(L.img,0,0,w,h);
  ctx.filter='none';
  ctx.globalCompositeOperation='source-over';
  // vuelo radial + squash direccional (una sola oscilación)
  const ang=Math.atan2(p.cy_pct-CY/IH*100, p.cx_pct-CX/IW*100);
  const dist=(1-cubicOut(st.fly))*4.5;        // % del stage
  const s=springSettle(clamp(st.e/560));
  const sq=1+(st.last?.08:.06)*(1-clamp(st.e/300));
  L.wrap.style.transform =
    `translate(${-Math.cos(ang)*dist}%,${-Math.sin(ang)*dist}%) `+
    `rotate(${ang}rad) scale(${sq*s},${(2-sq)*s}) rotate(${-ang}rad)`;
}

// ---- escritura de la caligrafía (punta de pluma que lidera) ----
const WRITE = [[350,1350],[1200,1650],[1550,2350]];   // Arte / de / hoy
function drawText(t){
  const L=layers['ink_text']; if(L.done) return;
  const ctx=L.ctx, w=IW/HALF, h=IH/HALF;
  if(t>WRITE[2][1]+120){ L.done=true; L.cv.style.display='none'; L.img.style.visibility='visible'; pen.style.opacity=0; return; }
  ctx.clearRect(0,0,w,h);
  let tip=null;
  for(let i=0;i<3;i++){
    const [a,b]=WRITE[i]; const p=clamp((t-a)/(b-a)); if(p<=0) continue;
    const wd=WORDS[i];
    const x0=wd.x0/100*w, x1=wd.x1/100*w, R=wd.h/100*h*.5;
    const bandT=(wd.y-wd.h/2)/100*h, bandH=wd.h/100*h;
    const ease=sine(p);
    const xt=x0+(x1-x0)*ease;
    ctx.save(); ctx.beginPath();
    ctx.rect(0,bandT,w,bandH); ctx.clip();      // cada palabra SOLO en su renglón
    ctx.beginPath();
    ctx.rect(x0-R*.6, bandT-2, (xt-x0)+R*.9, bandH+4);
    ctx.fillStyle='#fff'; ctx.filter='blur(6px)'; ctx.fill();
    ctx.restore();
    if(p<1) tip={x:xt/w, y:wd.y/100};
    else if(i===2 && p>=1) tip=null;
  }
  ctx.globalCompositeOperation='source-in';
  ctx.drawImage(L.img,0,0,w,h);
  ctx.globalCompositeOperation='source-over';
  if(tip){ const r=stage.getBoundingClientRect();
    pen.style.opacity=1;
    pen.style.left=(tip.x*r.width)+'px'; pen.style.top=(tip.y*r.height)+'px';
  } else pen.style.opacity=0;
}

// ---- aros: barrido cónico con cabeza de pincel ----
const RING_T=[2100,3050];
function drawRings(t){
  const L=layers['ink_rings']; if(L.done) return;
  const ctx=L.ctx, w=IW/HALF, h=IH/HALF;
  const p=clamp((t-RING_T[0])/(RING_T[1]-RING_T[0]));
  if(p<=0){ ctx.clearRect(0,0,w,h); return; }
  if(p>=1 && t>RING_T[1]+80){ L.done=true; L.cv.style.display='none'; L.img.style.visibility='visible'; return; }
  ctx.clearRect(0,0,w,h);
  const cx=CX/HALF, cy=CY/HALF;
  const a0=-Math.PI/2, a1=a0+Math.PI*2*cubicOut(p);
  ctx.save(); ctx.beginPath(); ctx.moveTo(cx,cy);
  ctx.arc(cx,cy,w, a0, a1); ctx.closePath();
  ctx.fillStyle='#fff'; ctx.fill(); ctx.restore();
  ctx.globalCompositeOperation='source-in';
  ctx.drawImage(L.img,0,0,w,h);
  ctx.globalCompositeOperation='source-over';
  if(p<1){ const r=stage.getBoundingClientRect();
    const rad=.30*r.width;
    pen.style.opacity=.9;
    pen.style.left=(CX/IW*r.width+Math.cos(a1)*rad)+'px';
    pen.style.top =(CY/IH*r.height+Math.sin(a1)*rad)+'px';
  }
}

// ---- partículas, tinte ambiente, sacudida ----
function spawnSplat(p, last){
  const r=stage.getBoundingClientRect();
  const scale=r.width/IW;
  const cx=(p.cx_pct/100*IW)*scale + partcv.width*0/1, cy=(p.cy_pct/100*IH)*scale;
  const offX=partcv.clientWidth*0.5-r.width*0.5, offY=partcv.clientHeight*0.5-r.height*0.5;
  const ang=Math.atan2(p.cy_pct-CY/IH*100, p.cx_pct-CX/IW*100);
  const n=last?22:(10+Math.random()*4|0);
  for(let i=0;i<n;i++){
    const cls=i<2?0:(i<6?1:2);
    const a=ang+(Math.random()-.5)*1.22;
    const sp=(cls===0? 190:cls===1? 320:520)*(.7+Math.random()*.6)*scale;
    particles.push({x:cx+offX, y:cy+offY, vx:Math.cos(a)*sp, vy:Math.sin(a)*sp-60*scale,
      cls, sp:p.sprites[cls], life:0, max:.55+Math.random()*.35, sc:.6+Math.random()*.8});
  }
  // tinte ambiente con memoria
  const [rr,gg,bb]=hexRGB(p.hex);
  const g=tctx.createRadialGradient(p.cx_pct*2, p.cy_pct*1.87, 4, p.cx_pct*2, p.cy_pct*1.87, 88);
  g.addColorStop(0,`rgba(${rr},${gg},${bb},.10)`); g.addColorStop(1,`rgba(${rr},${gg},${bb},0)`);
  tctx.fillStyle=g; tctx.fillRect(0,0,200,187);
  // sacudida perpendicular
  const k=ORDER.indexOf(p.i);
  shakes.push({t:performance.now(), amp:(last?8:3+k*.55), dir:ang+Math.PI/2, seed:Math.random()*9});
}
function stepParticles(dt){
  const g=1650, drag=Math.pow(.90,dt*60);
  pctx.clearRect(0,0,partcv.width,partcv.height);
  particles=particles.filter(pt=>{
    pt.life+=dt; if(pt.life>pt.max) return false;
    pt.vx*=drag; pt.vy=pt.vy*drag+g*dt* (partcv.width/900);
    pt.x+=pt.vx*dt; pt.y+=pt.vy*dt;
    const f=1-pt.life/pt.max;
    pctx.globalAlpha=Math.min(1,f*2);
    const s=pt.sp.width*pt.sc*(1+(1-f)*.15);
    pctx.drawImage(pt.sp, pt.x-s/2, pt.y-s/2, s, s);
    return true;
  });
  pctx.globalAlpha=1;
}
function stageShake(now){
  let dx=0,dy=0;
  shakes=shakes.filter(s=>{
    const e=(now-s.t)/1000; if(e>.42) return false;
    const a=s.amp*Math.exp(-e/0.06)*Math.sin(e*52+s.seed);
    dx+=Math.cos(s.dir)*a; dy+=Math.sin(s.dir)*a; return true;
  });
  return {dx,dy};
}

// ---- clímax + cierre ----
function finale(t){
  const e=t-SPLAT_T[7];
  if(e<0) return;
  const p1=clamp(e/500);
  pulse.style.opacity=(p1<1? .10*Math.sin(Math.PI*p1) : 0);
  const st=1.015-.015*cubicOut(clamp((e-80)/700));
  stage.style.scale=String(Math.max(1,st).toFixed(4));
  if(e>600){
    const p2=clamp((e-600)/900);
    kicker.style.opacity=p2;
    kicker.style.letterSpacing=(0.5-0.26*cubicOut(p2))+'em';
    kicker.style.paddingLeft=(0.5-0.26*cubicOut(p2))+'em';
  }
  if(e>1400) replayB.classList.add('on');
}

// ---- bucle principal ----
let lastNow=0;
function frame(now){
  const t=now-t0, dt=Math.min(.05,(now-lastNow)/1000||16); lastNow=now;
  drawText(t);
  drawRings(t);
  for(const p of PIECES){
    const st=pieceState(p.i,t);
    if(st){ if(!p._sp){ p._sp=true; spawnSplat(p, st.last); } drawPiece(p,st); }
  }
  stepParticles(dt);
  const {dx,dy}=stageShake(now);
  stage.style.transform=`translate(${dx.toFixed(2)}px,${dy.toFixed(2)}px)`;
  finale(t);
  if(t<T_END){ if(!noloop) raf=requestAnimationFrame(frame); }
  else finish();
}
function finish(){
  done=true; cancelAnimationFrame(raf);
  for(const k of stack){ const L=layers[k]; L.done=true; L.cv.style.display='none';
    L.img.style.visibility='visible'; L.wrap.style.transform='none'; }
  particles=[]; pctx.clearRect(0,0,partcv.width,partcv.height);
  pen.style.opacity=0; pulse.style.opacity=0;
  stage.style.transform='none'; stage.style.scale='1';
  kicker.style.opacity=1; kicker.style.letterSpacing='.24em'; kicker.style.paddingLeft='.24em';
  replayB.classList.add('on');
}
function reset(){
  cancelAnimationFrame(raf); done=false;
  replayB.classList.remove('on');
  tctx.clearRect(0,0,200,187);
  particles=[]; shakes=[];
  kicker.style.opacity=0; kicker.style.letterSpacing='.5em';
  stage.style.scale='1'; stage.style.transform='none'; pulse.style.opacity=0;
  for(const k of stack){ const L=layers[k]; L.done=false;
    L.cv.style.display='block'; L.img.style.visibility='hidden';
    L.ctx.clearRect(0,0,IW/HALF,IH/HALF); L.wrap.style.transform='none'; }
  PIECES.forEach(p=>p._sp=false);
  const r=stage.getBoundingClientRect();
  partcv.width=r.width*1.5; partcv.height=r.height*1.5;
}
let noloop=false;
function play(){
  if(RM){ finish(); return; }
  reset();
  t0=performance.now(); lastNow=t0;
  raf=requestAnimationFrame(frame);
}
window.__still = ms => { reset(); t0=performance.now()-ms; lastNow=performance.now()-16;
  noloop=true; frame(performance.now()); noloop=false; };
stage.addEventListener('click',()=>{ if(!done) finish(); });
replayB.addEventListener('click',play);
let loaded=0;
for(const k of stack){ const im=layers[k].img;
  const go=()=>{ if(++loaded===stack.length) play(); };
  im.complete?go():im.addEventListener('load',go);
}
})();
</script>'''

html = (html
  .replace("__PIECES__", PIECES_JS)
  .replace("__WORDS__", WORDS_JS)
  .replace("__W__", str(W)).replace("__H__", str(H))
  .replace("__CX__", str(round(meta["cx"], 1))).replace("__CY__", str(round(meta["cy"], 1)))
  .replace("__IMGS__", json.dumps(IMGS)))

layers_html = "\n".join([])  # las capas se crean por JS
html = html.replace("<!--LAYERS-->", layers_html)
out = SP / "artedehoy-reveal.html"
out.write_text(html)
print("HTML:", out, round(len(html)/1024), "KB")
