#!/usr/bin/env python3
"""v3: exactitud POR CONSTRUCCIÓN. w = max(matte estético, w mínimo de gama).
La tinta absorbe sombras/residuos; las manchas vuelan limpias; la suma = original."""
import numpy as np, json, os, sys
from PIL import Image

# Uso:  python3 descomponer-logo.py <logo.png> <carpeta-de-salida>
SRC = sys.argv[1] if len(sys.argv) > 1 else "logo.png"
OUT = sys.argv[2] if len(sys.argv) > 2 else "salida"
PZ = f"{OUT}/piezas"; os.makedirs(PZ, exist_ok=True)
for f in os.listdir(PZ):
    if f.endswith(".png"): os.remove(f"{PZ}/{f}")

img = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float64)
H, W = img.shape[:2]
mn = img.min(axis=2); mx = img.max(axis=2); chroma = mx - mn

# ---- A. alpha exterior ----
cand = mn > 232
bg = np.zeros((H, W), bool)
bg[0, :] = cand[0, :]; bg[-1, :] = cand[-1, :]
bg[:, 0] |= cand[:, 0]; bg[:, -1] |= cand[:, -1]
while True:
    d = bg.copy()
    d[1:, :] |= bg[:-1, :]; d[:-1, :] |= bg[1:, :]
    d[:, 1:] |= bg[:, :-1]; d[:, :-1] |= bg[:, 1:]
    d &= cand
    if d.sum() == bg.sum(): break
    bg = d
alpha = np.where(bg, 0.0, 255.0)
for _ in range(2):
    p = np.pad(alpha, 1, mode="edge")
    alpha = sum(p[dy:dy+H, dx:dx+W] for dy in range(3) for dx in range(3)) / 9.0
A = alpha / 255.0
Image.fromarray(np.dstack([img, alpha]).astype(np.uint8)).save(f"{OUT}/master.png")

# ---- B. matte estético estricto (texto/aros blancos y grises neutros) ----
c_lo, c_hi = 8.0, 30.0
w_est = np.clip((c_hi - chroma) / (c_hi - c_lo), 0, 1)
w_est = w_est * w_est * (3 - 2 * w_est)
w_est *= A
# compuerta: nada de tinta pegada al borde exterior (esos son flecos de acuarela)
near_bg = (A < 0.5)
for _ in range(4):
    z = near_bg.copy()
    z[1:, :] |= near_bg[:-1, :]; z[:-1, :] |= near_bg[1:, :]
    z[:, 1:] |= near_bg[:, :-1]; z[:, :-1] |= near_bg[:, 1:]
    near_bg = z
w_est[near_bg] = 0.0

# ---- C. inpaint sobre zona generosa (tinta + sombras + halo) ----
zone = w_est > 0.03
for _ in range(8):
    z = zone.copy()
    z[1:, :] |= zone[:-1, :]; z[:-1, :] |= zone[1:, :]
    z[:, 1:] |= zone[:, :-1]; z[:, :-1] |= zone[:, 1:]
    zone = z
zone &= (A > 0.1)
unknown = zone.copy()
known = (~unknown) & (A > 0.1)
fill = img.copy(); fill[unknown] = 0
k = known.astype(np.float64); it = 0
while unknown.any() and it < 600:
    it += 1
    pk = np.pad(k, 1); pr = np.pad(fill * k[..., None], ((1,1),(1,1),(0,0)))
    nk = sum(pk[dy:dy+H, dx:dx+W] for dy in range(3) for dx in range(3))
    nr = sum(pr[dy:dy+H, dx:dx+W] for dy in range(3) for dx in range(3))
    newly = unknown & (nk > 0)
    if not newly.any(): break
    fill[newly] = nr[newly] / nk[newly, None]
    k[newly] = 1; unknown[newly] = False
fill[unknown] = img[unknown]  # rincones aislados: se quedan como estaban
sm = fill.copy()
for _ in range(8):
    p = np.pad(sm, ((1,1),(1,1),(0,0)), mode="edge")
    sm = sum(p[dy:dy+H, dx:dx+W] for dy in range(3) for dx in range(3)) / 9.0
fill[zone] = sm[zone]
print(f"[C] inpaint {it} iter, sin rellenar {unknown.sum()} px")

# ---- D0. fuera de la tinta estética, las piezas llevan su píxel REAL ----
revert = (w_est < 0.02) & (A > 0.02)
fill[revert] = img[revert]

# ---- D. w mínimo de gama => exactitud por construcción ----
d_up = img - fill                       # componente que exige tinta clara
d_dn = fill - img                       # tinta oscura
with np.errstate(divide="ignore", invalid="ignore"):
    need_up = np.where(d_up > 0, d_up / np.maximum(255.0 - fill, 1e-6), 0)
    need_dn = np.where(d_dn > 0, d_dn / np.maximum(fill, 1e-6), 0)
w_min = np.maximum(need_up, need_dn).max(axis=2)
w_min = np.clip(w_min, 0, 1) * (A > 0.02)
w_fin = np.clip(np.maximum(w_est, w_min * 1.02), 0, 1)   # 2% de margen para el redondeo
w = w_fin[..., None]
ink_rgb = np.where(w > 1e-4, (img - fill * (1 - w)) / np.maximum(w, 1e-4), 0)
ink_rgb = np.clip(ink_rgb, 0, 255)
ink_a = np.clip(w_fin * 255, 0, 255)    # sobre el diseño; fuera A~0 el matte ya es 0

# ---- E. verificación con simulación uint8 (como compone el navegador) ----
fill8 = fill.round(); inka8 = ink_a.round(); inkrgb8 = ink_rgb.round()
a8 = inka8 / 255.0
recon = fill8 * (1 - a8[..., None]) + inkrgb8 * a8[..., None]
diff = np.abs(recon - img) * (A[..., None] > 0.5)
print(f"[E] reconstrucción uint8: max={diff.max():.2f} media={diff.mean():.4f} p99.9={np.percentile(diff[A>0.5],99.9):.2f}")

# ---- F. clusters de color (igual que v1, sobre img original) ----
den = np.maximum(chroma, 1e-6)
rr, gg, bb = img[...,0], img[...,1], img[...,2]
h_r = ((gg - bb) / den) % 6; h_g = (bb - rr) / den + 2; h_b = (rr - gg) / den + 4
hue = np.where(mx == rr, h_r, np.where(mx == gg, h_g, h_b)) * 60.0
colorful = (chroma >= 14) & (A > 0.1)
CENTERS = np.array([5, 28, 52, 120, 165, 205, 250, 315], float)
def circdist(h, c): d = np.abs(h - c) % 360; return np.minimum(d, 360 - d)
for _ in range(4):
    dists = np.stack([circdist(hue, c) for c in CENTERS])
    lab = dists.argmin(axis=0)
    for i in range(len(CENTERS)):
        m = colorful & (lab == i)
        if m.sum() > 500:
            ang = np.deg2rad(hue[m]); wgt = chroma[m]
            CENTERS[i] = np.rad2deg(np.arctan2((np.sin(ang)*wgt).sum(), (np.cos(ang)*wgt).sum())) % 360
dists = np.stack([circdist(hue, c) for c in CENTERS])
labels = dists.argmin(axis=0); labels[~colorful] = 255
K = len(CENTERS)
onehot = np.zeros((K, H, W))
for i in range(K): onehot[i] = (labels == i).astype(float)
for _ in range(3):
    for i in range(K):
        p = np.pad(onehot[i], 2)
        onehot[i] = sum(p[dy:dy+H, dx:dx+W] for dy in range(5) for dx in range(5))
labels_s = onehot.argmax(axis=0); support = onehot.max(axis=0)
labels = np.where(A > 0.02, np.where(support > 0, labels_s, labels), 255).astype(np.uint8)
rest = (labels == 255) & (A > 0.02)
if rest.any(): labels[rest] = dists[:, rest].argmin(axis=0)

# ---- G. tinta: caligrafía vs aros ----
ys, xs = np.mgrid[0:H, 0:W]
mass = w_est * A
cy = (ys * mass).sum() / mass.sum(); cx = (xs * mass).sum() / mass.sum()
r = np.hypot(xs - cx, ys - cy)
R_SPLIT = 185.0
ink_text_a = np.where(r < R_SPLIT, inka8, 0)
ink_ring_a = np.where(r >= R_SPLIT, inka8, 0)

# ---- H. export (RGB en cero donde alpha 0 => PNG chico) ----
def save_rgba(rgb, a, path):
    m = (a > 0)[..., None]
    out = np.dstack([rgb * m, a]).astype(np.uint8)
    Image.fromarray(out).save(path, optimize=True)

meta = {"W": W, "H": H, "cx": float(cx), "cy": float(cy), "r_split": R_SPLIT, "pieces": []}
for i in range(K):
    m = (labels == i) & (A > 0.02)
    a_i = np.where(m, alpha, 0).round()
    save_rgba(fill8, a_i, f"{PZ}/color_{i}.png")
    src_m = m & (chroma >= 14)
    avg = img[src_m].mean(axis=0) if src_m.sum() else img[m].mean(axis=0)
    cyi = ys[m].mean(); cxi = xs[m].mean()
    ang = float(np.degrees(np.arctan2(cyi - cy, cxi - cx)) % 360)
    meta["pieces"].append({"i": i, "hue": round(float(CENTERS[i]), 1), "px": int(m.sum()),
        "hex": "#%02x%02x%02x" % tuple(int(v) for v in avg),
        "cx_pct": round(float(cxi / W * 100), 2), "cy_pct": round(float(cyi / H * 100), 2), "ang": round(ang)})
save_rgba(inkrgb8, ink_text_a, f"{PZ}/ink_text.png")
save_rgba(inkrgb8, ink_ring_a, f"{PZ}/ink_rings.png")
tb = np.where(ink_text_a > 30)
meta["text_bbox_pct"] = [round(float(tb[1].min()/W*100),1), round(float(tb[0].min()/H*100),1),
                         round(float(tb[1].max()/W*100),1), round(float(tb[0].max()/H*100),1)]
json.dump(meta, open(f"{PZ}/meta.json", "w"), indent=1)

# ---- I. lámina de control ----
def on_dark(rgb, a):
    base = np.zeros((H, W, 3)) + [20, 16, 19]
    af = (a / 255.0)[..., None]
    return np.clip(base * (1 - af) + rgb * af, 0, 255).astype(np.uint8)
comp_rgb = np.zeros((H, W, 3)); comp_a = np.zeros((H, W))
order = list(range(K))
for i in order:
    p = np.asarray(Image.open(f"{PZ}/color_{i}.png")).astype(np.float64)
    af = p[..., 3] / 255.0
    comp_rgb = comp_rgb * (1 - af[..., None]) + p[..., :3] * af[..., None]
    comp_a = af + comp_a * (1 - af)
for nm in ["ink_text", "ink_rings"]:
    p = np.asarray(Image.open(f"{PZ}/{nm}.png")).astype(np.float64)
    af = p[..., 3] / 255.0
    comp_rgb = comp_rgb * (1 - af[..., None]) + p[..., :3] * af[..., None]
    comp_a = af + comp_a * (1 - af)
final_diff = np.abs(comp_rgb - img) * (comp_a[..., None] > 0.5)
print(f"[I] APILADO REAL (como el navegador): max={final_diff.max():.2f} media={final_diff.mean():.4f}")
fd = final_diff.max(axis=2)
idx = np.argsort(fd.ravel())[-6:][::-1]
for j in idx:
    yy, xx = divmod(int(j), W)
    print(f"    diff {fd[yy,xx]:6.1f} en ({xx},{yy}) img={img[yy,xx].astype(int)} A={A[yy,xx]:.2f} w={w_fin[yy,xx]:.2f} lab={labels[yy,xx]} compA={comp_a[yy,xx]:.2f}")
tiles = [
    on_dark(np.asarray(Image.open(f"{PZ}/ink_text.png")).astype(float)[...,:3], ink_text_a),
    on_dark(np.asarray(Image.open(f"{PZ}/ink_rings.png")).astype(float)[...,:3], ink_ring_a),
    on_dark(comp_rgb, comp_a * 255),
    np.clip(final_diff.max(axis=2) * 20, 0, 255).astype(np.uint8)[..., None].repeat(3, 2),
]
sheet = Image.new("RGB", (W * 2, H * 2), (12, 10, 12))
for idx, t in enumerate(tiles):
    sheet.paste(Image.fromarray(t), ((idx % 2) * W, (idx // 2) * H))
sheet.resize((W, H)).save(f"{OUT}/SHEET3.png")
sizes = {f: os.path.getsize(f"{PZ}/{f}") // 1024 for f in sorted(os.listdir(PZ)) if f.endswith(".png")}
print("[H] KB:", sizes, "TOTAL:", sum(sizes.values()), "KB")
print(json.dumps(meta["pieces"], indent=0))
