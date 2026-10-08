"""Noche americana · grading pipeline for the Serendipity fleet photos (final direction).

Writes derivatives into ../assets (max 1920 px wide, JPG, < 400 KB). Not needed to view
the deck: index.html only references the finished files. Re-run to regenerate:
    python3 tools/grade.py            (all)
    python3 tools/grade.py cover mesas (some)

Rules:
- never upscale beyond the native resolution of the source;
- night grade = "noche americana": deep teal shadows, teal light, gold/sand practicals;
- day grade   = "día dorado": dark teal shadows, sand/gold highlights, no blue sky;
- local dodge on skin so the grade never buries darker skin tones.
"""
import sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / 'images'
OUT = Path(__file__).resolve().parent.parent / 'assets'
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(11)


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


NIGHT = hexc('00272B')   # Dark Teal (brand)
TEAL = hexc('046567')    # Teal (brand)
GOLD = hexc('C9A55C')
ARENA = hexc('F3EEE4')
INK = hexc('000E10')     # derived: deepest shadow (vignette only)
DEEP = hexc('00181B')    # derived: night shadow


def to_f(im):
    return np.asarray(im.convert('RGB')).astype(np.float32) / 255.0


def to_im(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


def lum(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def gmap(L, stops):
    xs = np.array([s[0] for s in stops], np.float32)
    out = np.zeros(L.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(L, xs, [s[1][c] for s in stops])
    return out


def blur(mask, r):
    m = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(m).astype(np.float32) / 255.0


def blur_rgb(a, r):
    return to_f(to_im(a).filter(ImageFilter.GaussianBlur(r)))


def radial(h, w, cx, cy, rx, ry, p=2.0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    return np.clip(1 - d, 0, 1) ** p


def gauss(h, w, cx, cy, rx, ry):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) / 2)


def poly_mask(w, h, pts, feather=2.0):
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return blur(np.asarray(m).astype(np.float32) / 255.0, feather)


def grain(a, amount=0.02):
    h, w = a.shape[:2]
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    n = 0.65 * n + 0.35 * to_f(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)))[..., 0] * 0
    L = lum(a)[..., None]
    wgt = 0.55 + 0.9 * np.clip(1 - np.abs(L - 0.4) * 1.8, 0.15, 1)
    return a + n[..., None] * amount * wgt


def unsharp(a, radius=1.2, percent=60, threshold=2):
    return to_f(to_im(a).filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold)))


def desat(a, s):
    L = lum(a)[..., None]
    return L + (a - L) * s


def save(img, name, q=82, max_kb=380):
    # the deck uses WebP: the .jpg names below are kept only as labels
    name = name.rsplit('.', 1)[0] + '.webp'
    p = OUT / name
    while True:
        img.save(p, 'WEBP', quality=q, method=6)
        kb = p.stat().st_size / 1024
        if kb <= max_kb or q <= 60:
            break
        q -= 3
    print(f'{name:34s} {img.size[0]}x{img.size[1]}  {kb:4.0f} KB  q={q}')


# ------------------------------------------------------------------ grades
NIGHT_STOPS = [
    (0.00, INK),
    (0.12, DEEP),
    (0.28, NIGHT),
    (0.48, NIGHT * 0.35 + TEAL * 0.65),
    (0.68, TEAL * 0.30 + GOLD * 0.70),
    (0.86, GOLD * 0.40 + ARENA * 0.60),
    (1.00, ARENA),
]

LACQUER_STOPS = [   # black lacquer: shadows to near black, speculars to sand/gold
    (0.00, INK * 0.6),
    (0.18, INK),
    (0.34, DEEP * 1.05),
    (0.52, NIGHT * 0.7 + TEAL * 0.3),
    (0.70, TEAL * 0.15 + GOLD * 0.85),
    (0.86, GOLD * 0.35 + ARENA * 0.65),
    (1.00, ARENA),
]

DAY_STOPS = [       # día dorado: dark teal shadows, warm neutral mids, sand-gold highlights
    (0.00, NIGHT * 0.6),
    (0.14, NIGHT * 0.9 + TEAL * 0.1),
    (0.34, NIGHT * 0.25 + TEAL * 0.45 + hexc('6E6A58') * 0.30),
    (0.56, hexc('9A8F74')),
    (0.76, GOLD * 0.35 + ARENA * 0.65),
    (0.90, ARENA * 0.96 + GOLD * 0.04),
    (1.00, ARENA),
]


def tone(a, stops, keep=0.2, sat=0.5, exposure=1.0, gamma=1.0):
    L = lum(a)
    Ld = np.clip((L * exposure) ** gamma, 0, 1)
    mapped = gmap(Ld, stops)
    orig = np.clip(a * exposure, 0, 1) ** gamma
    orig = desat(orig, sat)
    return mapped * (1 - keep) + orig * keep


def dodge(a, spots):
    """local skin lift (x, y, r, amount) in pixel coords: multiplicative, soft gaussian."""
    h, w = a.shape[:2]
    for (x, y, r, k) in spots:
        m = gauss(h, w, x, y, r, r * 1.25)
        a = a * (1 + k * m[..., None])
    return a


# ------------------------------------------------------------------ 01 portada (Suburban High Country del cliente)
def smooth(x, lo, hi):
    x = np.clip((x - lo) / (hi - lo), 0, 1)
    return x * x * (3 - 2 * x)


def cover_hc():
    """Client's 2576 px Suburban High Country, daylight -> real day-for-night.
    One global grade over the whole photo (no cut-out): the car keeps its own reflections,
    its shadow on the pavers and the trees behind it. Only soft gradients, no hard masks."""
    src = Image.open(ORIG / 'suburban-high-country.jpg').convert('RGB')      # 2576 x 1448
    a = to_f(src)
    h, w = a.shape[:2]
    K = w / 2000.0                                                           # coords measured on a 2000 px preview
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    yn, xn = yy / h, xx / w
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    L = lum(a)
    chroma = a.max(-1) - a.min(-1)

    # 1 · day-for-night: about two stops under, cool (teal) balance, greens pulled down
    o = desat(a, 0.50)
    green = smooth(g - np.maximum(r, b), 0.02, 0.12)[..., None]
    o = o * (1 - 0.35 * green)                                               # foliage reads dark, not lush
    o = o * np.array([0.78, 0.96, 1.00], np.float32)                         # moonlight balance
    o = np.clip(o * 0.62, 0, 1) ** 1.22
    o = o * 0.62 + tone(a, NIGHT_STOPS, keep=0.0, sat=0.0, exposure=0.66, gamma=1.25) * 0.38

    # 2 · the sunlit pavers are the giveaway: compress them (soft mask, warm + bright + low chroma, lower half)
    pav = smooth(L, 0.42, 0.78) * smooth(yn, 0.50, 0.60) * smooth(r - b, 0.0, 0.06) * (1 - smooth(chroma, 0.18, 0.30))
    o = o * (1 - 0.55 * pav[..., None])
    # 3 · graduated darkening: tree canopy at the top, ground at the bottom, vignette around the car
    o = o * (1 - 0.55 * smooth(1 - yn, 0.55, 1.0))[..., None]
    o = o * (1 - 0.35 * smooth(yn, 0.80, 1.0))[..., None]
    v = radial(h, w, 1080 * K, 640 * K, 1150 * K, 700 * K, 0.8)
    o = o * (0.55 + 0.45 * v[..., None])

    # 4 · plate neutralised (no characters)
    plate = poly_mask(w, h, [(x * K, y * K) for x, y in [(1514, 686), (1608, 686), (1608, 768), (1514, 768)]], 3)
    o = o * (1 - plate[..., None]) + (blur_rgb(o, 8) * 0.55) * plate[..., None]
    # 5 · practicals, kept small: the LED strip lit, a faint glow, a faint warm pool ahead of the bumper
    hx, hy = 1215 * K, 525 * K
    zone = gauss(h, w, hx, hy, 110 * K, 22 * K)
    led = smooth(L, 0.55, 0.85) * zone
    o = o + ARENA[None, None, :] * led[..., None] * 0.55
    o = o + (GOLD * 0.85)[None, None, :] * gauss(h, w, hx, hy, 70 * K, 16 * K)[..., None] * 0.30
    o = o + (GOLD * 0.6)[None, None, :] * gauss(h, w, 1820 * K, 940 * K, 380 * K, 60 * K)[..., None] * 0.10
    o = unsharp(np.clip(o, 0, 1), 1.2, 40, 2)

    # 6 · composite: car lower right; the scenery falls off into darkness like light does at night
    s = 0.508
    p = to_f(to_im(o).resize((round(w * s), round(h * s)), Image.LANCZOS))
    ph, pw = p.shape[:2]
    FW, FH = 1920, 808
    ox, oy = round(1866 - 1690 * K * s), round(798 - 975 * K * s)
    fy = np.linspace(0, 1, FH)[:, None, None]
    frame = np.zeros((FH, FW, 3), np.float32)
    frame[:] = DEEP * (0.45 + 0.20 * fy)                                     # deep shadow, a touch lighter low
    x0, x1 = max(ox, 0), min(ox + pw, FW)
    y0, y1 = max(oy, 0), min(oy + ph, FH)
    crop = p[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    ch, cw = crop.shape[:2]
    car_l = 315 * K * s                                                      # the car starts here inside the photo
    fl = smooth(np.arange(cw, dtype=np.float32), 0, car_l + 14)[None, :]
    ft = smooth(np.arange(ch, dtype=np.float32), 0, 150)[:, None]
    al = (fl * ft)[..., None]
    frame[y0:y1, x0:x1] = crop * al + frame[y0:y1, x0:x1] * (1 - al)
    fv = radial(FH, FW, FW * 0.72, FH * 0.60, FW * 0.80, FH * 1.05, 0.8)
    frame = frame * (0.72 + 0.28 * fv[..., None])
    frame = grain(frame, 0.014)
    fdx, fdy = ox + hx * s, oy + hy * s
    print(f'cover_hc: headlamp at frame ({fdx:.0f}, {fdy:.0f}) -> slide y {136 + fdy:.0f}, --p {100 * fdx / FW:.2f}%')
    save(to_im(frame), 'n01-suburban-hc.jpg', q=88)


# ------------------------------------------------------------------ 10 mesas vip
def mesas():
    """Trio in the V-Class -> night ride. Windows go to night (luminance-derived soft mask, no polygons),
    bokeh in the glass, key light on every face, dodge on the right guest, base closes to Dark Teal."""
    src = Image.open(SRC / 'luxury-vclass.jpg').convert('RGB')          # 1600 x 963
    s = 0.80
    im = src.resize((int(src.width * s), int(src.height * s)), Image.LANCZOS)   # 1280 x 770 (downscale)
    a = to_f(im)
    h, w = a.shape[:2]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    L = lum(a)
    S = s
    # window mask: bright or green pixels inside generous window zones, then closed and feathered
    zones = np.zeros((h, w), np.float32)
    for pts in ([(0, 90), (95, 120), (110, 360), (100, 760), (0, 790)],
                [(425, 228), (1050, 228), (1050, 420), (425, 430)],
                [(1395, 110), (1600, 70), (1600, 560), (1390, 540)]):
        zones = np.maximum(zones, poly_mask(w, h, [(x * S, y * S) for x, y in pts], 1))
    green = (g > r * 1.02) & (g > b * 1.04)
    bright = L > 0.44
    raw = ((green | bright) & (zones > 0.5)).astype(np.float32)
    guard = radial(h, w, 766 * S, 338 * S, 74 * S, 100 * S, 0.5)          # centre guest's face only
    raw = raw * (1 - np.clip(guard * 3, 0, 1) * (L < 0.62))
    m = blur(raw, 3.0)
    m = np.clip((m - 0.40) / 0.22, 0, 1)
    win = blur(m, 2.0) * (zones > 0.1)

    graded = tone(a, NIGHT_STOPS, keep=0.50, sat=0.66, exposure=0.64, gamma=1.2)
    hi = np.clip((lum(graded) - 0.32) / 0.4, 0, 1)[..., None]
    graded = graded * (1 - 0.5 * hi) + np.clip(graded * np.array([1.10, 1.0, 0.80]), 0, 1) * 0.5 * hi
    # warm practical from the roof light
    warm = radial(h, w, w * 0.50, h * 0.12, w * 0.60, h * 0.60, 1.0)
    graded = graded * (1 + 0.20 * warm[..., None]) + (GOLD * 0.04)[None, None, :] * warm[..., None]
    # faces: bring back natural skin from the source, then key light + dodge (right guest most)
    for (fx, fy, rx, ry, k) in [(370, 245, 120, 150, 0.36), (765, 335, 100, 130, 0.36), (1225, 255, 130, 165, 0.68)]:
        m2 = radial(h, w, fx * S, fy * S, rx * S, ry * S, 0.9)
        orig = np.clip(a * 0.92, 0, 1)
        graded = graded * (1 - k * m2[..., None]) + orig * (k * m2[..., None])
    graded = dodge(graded, [(372 * S, 240 * S, 95 * S, 0.14), (762 * S, 330 * S, 85 * S, 0.18),
                            (1215 * S, 250 * S, 95 * S, 0.95), (1205 * S, 335 * S, 70 * S, 0.30)])
    # night windows: deep teal, soft defocused practicals (bokeh drawn at 2x, then blurred)
    night = np.ones_like(a) * (DEEP * 0.70 + NIGHT * 0.30)
    yyw = np.mgrid[0:h, 0:w][0] / h
    night = night + (TEAL * 0.10)[None, None, :] * np.clip(1 - np.abs(yyw - 0.40) / 0.22, 0, 1)[..., None]
    bk = Image.new('RGB', (w * 2, h * 2), (0, 0, 0))
    dr = ImageDraw.Draw(bk)
    spots = [(480, 300, 34, (201, 165, 92), .34), (575, 345, 14, (243, 238, 228), .22), (905, 296, 28, (201, 165, 92), .30),
             (975, 350, 12, (4, 101, 103), .75), (1455, 236, 38, (201, 165, 92), .30), (1525, 420, 18, (201, 165, 92), .22),
             (1475, 330, 10, (4, 101, 103), .8), (32, 300, 28, (201, 165, 92), .26), (40, 560, 14, (4, 101, 103), .7)]
    for (bx, by, br, col, k) in spots:
        X, Y, R = bx * S * 2, by * S * 2, br * S * 2
        k *= 0.8
        dr.ellipse([X - R, Y - R, X + R, Y + R], fill=tuple(int(v * k) for v in col),
                   outline=tuple(int(v * k * 1.3) for v in col), width=max(2, int(R * 0.10)))
    bk = bk.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3.6))
    night = night + to_f(bk)
    graded = graded * (1 - win[..., None]) + night * win[..., None]
    # side vignette (night falls off from the cabin light)
    xx = np.mgrid[0:h, 0:w][1] / w
    graded *= (0.78 + 0.22 * np.clip(1 - np.abs(xx - 0.55) / 0.6, 0, 1))[..., None]
    # vignette top, then close the base to solid Dark Teal (no photo behind the credits row)
    yy = np.mgrid[0:h, 0:w][0] / h
    graded *= (1 - 0.42 * np.clip(1 - yy / 0.18, 0, 1))[..., None]
    graded = grain(graded, 0.016)
    print('mesas: size', w, h)
    save(to_im(graded), 'n10-vclass-noche.jpg', q=88)
    to_im(win).save(Path(__file__).parent / 'dbg-win.png')


# ------------------------------------------------------------------ día dorado (light slides)
def day_grade(a, sky_top=0.40, keep=0.42):
    h, w = a.shape[:2]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    L = lum(a)
    yy = np.mgrid[0:h, 0:w][0] / h
    lim = np.clip((sky_top - yy) / 0.08, 0, 1)
    chroma = a.max(-1) - a.min(-1)
    cloud = (L > 0.42) & (chroma < 0.10) & (g <= r * 1.04)          # grey cloud, not foliage
    sky = blur((((b - r) > 0.05) & (b > 0.45) | ((L > 0.74) & (chroma < 0.14)) | cloud).astype(np.float32), 3) * lim
    out = tone(a, DAY_STOPS, keep=keep, sat=0.55, exposure=1.0, gamma=1.06)
    hi = np.clip((lum(out) - 0.45) / 0.4, 0, 1)[..., None]
    out = out * (1 - 0.35 * hi) + np.clip(out * np.array([1.06, 1.0, 0.88]), 0, 1) * 0.35 * hi
    haze = ARENA * (0.95 + 0.05 * yy[..., None]) + (GOLD * 0.05) * (1 - yy[..., None])
    out = out * (1 - sky[..., None]) + haze * sky[..., None]
    return out


def crop_scale(name, box, size):
    im = Image.open(SRC / name).convert('RGB').crop(box)
    if im.size != size:
        assert size[0] <= im.size[0], 'never upscale'
        im = im.resize(size, Image.LANCZOS)
    return to_f(im)


def day_photos():
    # 15 · Suburban cabin, symmetrical, warm
    a = crop_scale('suburban-interior.jpg', (76, 0, 1324, 1050), (960, 808))
    o = tone(a, DAY_STOPS, keep=0.42, sat=0.5, exposure=1.10, gamma=1.0)
    hi = np.clip((lum(o) - 0.4) / 0.4, 0, 1)[..., None]
    o = o * (1 - 0.4 * hi) + np.clip(o * np.array([1.07, 1.0, 0.86]), 0, 1) * 0.4 * hi
    h, w = o.shape[:2]
    win = blur(((lum(a) > 0.62)).astype(np.float32), 3)
    o = o * (1 - 0.6 * win[..., None]) + (ARENA * 0.96)[None, None, :] * 0.6 * win[..., None]
    o = o + (GOLD * 0.10)[None, None, :] * gauss(h, w, w * 0.5, h * 0.12, w * 0.4, h * 0.2)[..., None]
    save(to_im(grain(o, 0.012)), 'd15-cabina-dia.jpg')
    # 11 · fleet triptych (1056 x 576 each, shown at 528 x 288)
    a = crop_scale('tulum-suburban.jpg', (150, 209, 1206, 785), (1056, 576))
    save(to_im(grain(day_grade(a, 0.30), 0.012)), 'd11-suv.jpg')
    a = crop_scale('arrival-cta.jpg', (0, 150, 1056, 726), (1056, 576))
    save(to_im(grain(day_grade(a, 0.36), 0.012)), 'd11-van.jpg')


# ------------------------------------------------------------------ 16 · bokeh (testimonio)
def bokeh():
    a = to_f(Image.open(SRC / 'ondemand-experience.jpg').convert('RGB'))   # night, warm
    o = tone(a, NIGHT_STOPS, keep=0.45, sat=0.7, exposure=0.85, gamma=1.1)
    im = to_im(o).filter(ImageFilter.GaussianBlur(14))
    im = im.resize((1920, int(1920 * im.height / im.width)), Image.BICUBIC)   # pure defocus: no detail to lose
    top = (im.height - 808) // 2
    im = im.crop((0, top, 1920, top + 808)).filter(ImageFilter.GaussianBlur(10))
    o = to_f(im)
    h, w = o.shape[:2]
    o = o * (0.55 + 0.45 * radial(h, w, w * 0.5, h * 0.5, w * 0.75, h * 1.1, 1.2)[..., None])
    save(to_im(grain(o, 0.014)), 'n16-bokeh.jpg')


# ------------------------------------------------------------------ grain tile (normal blend, PDF-safe)
def grano():
    n = rng.normal(0, 1, (256, 256)).astype(np.float32)
    n = (n + np.roll(n, 1, 0) * 0.35 + np.roll(n, 1, 1) * 0.35) / 1.25
    alpha = np.clip(np.abs(n) * 22, 0, 255).astype(np.uint8)
    rgb = np.where(n[..., None] > 0, np.array([243, 238, 228]), np.array([0, 14, 16])).astype(np.uint8)
    Image.fromarray(np.dstack([rgb, alpha]), 'RGBA').save(OUT / 'grano.png', optimize=True)
    print('grano.png', (OUT / 'grano.png').stat().st_size // 1024, 'KB')


# ------------------------------------------------------------------ fotos nuevas del cliente (originales/)
ORIG = OUT / 'originales'


def patch(img, src_box, dst_xy, feather=6):
    """copy a small patch over a distraction (soft edges)."""
    piece = img.crop(src_box)
    m = Image.new('L', piece.size, 0)
    ImageDraw.Draw(m).rectangle([feather, feather, piece.width - feather, piece.height - feather], fill=255)
    img.paste(piece, dst_xy, m.filter(ImageFilter.GaussianBlur(feather / 2)))
    return img


def nuevas():
    # 08 · chofer de Serendipity en la zona de ascenso de CUN (día dorado)
    im = Image.open(ORIG / 'chofer-aeropuerto-cancun.jpg').convert('RGB')     # 1000 x 1333
    im = patch(im, (578, 862, 668, 912), (578, 908))                           # papel en el piso
    a = to_f(im.crop((0, 300, 1000, 1142)).resize((960, 808), Image.LANCZOS))
    a = np.clip(a, 0, 1) ** 0.82                                                # abre sombras antes del grade
    o = day_grade(a, sky_top=0.22, keep=0.45)
    h, w = o.shape[:2]
    o = dodge(o, [(470, 230, 70, 0.14)])
    o = o * (0.90 + 0.10 * radial(h, w, w * 0.48, h * 0.45, w * 0.9, h * 0.9, 1.0)[..., None])
    save(to_im(grain(o, 0.012)), 'd08-chofer-cun.jpg')

    # 11 · Sprinter real de noche, puerta abierta (tarjeta de flota 1056 x 576)
    im = Image.open(ORIG / 'sprinter-noche.jpg').convert('RGB')                # 2000 x 1333
    a = to_f(im.crop((300, 250, 1700, 1014)).resize((1056, 576), Image.LANCZOS))
    o = tone(a, NIGHT_STOPS, keep=0.55, sat=0.8, exposure=1.85, gamma=0.80)
    save(to_im(grain(o, 0.012)), 'n11-sprinter-noche.jpg')

    # 14 · chofer de Serendipity al volante (blanco y negro -> noche americana)
    im = Image.open(ORIG / 'chofer-serendipity-volante.jpg').convert('RGB')    # 2000 x 1126
    a = to_f(im.crop((150, 0, 1632, 1126)).resize((1000, 760), Image.LANCZOS))
    h, w = a.shape[:2]
    L = lum(a)
    zone = poly_mask(w, h, [(500, 20), (1000, 0), (1000, 470), (840, 480), (610, 430), (580, 200)], 14)
    win = blur((L > 0.50).astype(np.float32) * zone, 10)
    soft = blur_rgb(a, 9) * 0.38                                               # ventana desenfocada y de noche
    a2 = a * (1 - win[..., None]) + soft * win[..., None]
    o = tone(a2, NIGHT_STOPS, keep=0.45, sat=0.0, exposure=1.08, gamma=0.94)
    o = dodge(o, [(400, 205, 120, 0.30), (520, 560, 90, 0.12)])                # cara y mano
    o = o + (TEAL * 0.30)[None, None, :] * gauss(h, w, 820, 200, 240, 160)[..., None]
    o = o * (0.74 + 0.26 * radial(h, w, w * 0.42, h * 0.40, w * 0.9, h * 0.95, 0.9)[..., None])
    save(to_im(grain(o, 0.014)), 'n14-chofer-noche.jpg')

    # 09 · invitada a bordo de la Suburban, puerta abierta (día dorado)
    im = Image.open(ORIG / 'suburban-invitada.jpg').convert('RGB')             # 2000 x 1333
    a = to_f(im.crop((370, 0, 1954, 1333)).resize((960, 808), Image.LANCZOS))
    a = np.clip(a, 0, 1) ** 0.78                                                # abre el interior antes del grade
    o = day_grade(a, sky_top=0.30, keep=0.45)
    h, w = o.shape[:2]
    o = dodge(o, [(450, 400, 120, 0.30)])                                      # la invitada
    o = o * (0.90 + 0.10 * radial(h, w, w * 0.45, h * 0.50, w * 0.9, h * 0.9, 1.0)[..., None])
    save(to_im(grain(o, 0.012)), 'd09-suburban-invitada.jpg')

    # 11 · van estándar con chofer de Serendipity (tarjeta de flota)
    im = Image.open(ORIG / 'van-estandar-chofer.jpg').convert('RGB')           # 2000 x 1405
    a = to_f(im.crop((0, 150, 2000, 1241)).resize((1056, 576), Image.LANCZOS))
    save(to_im(grain(day_grade(a, 0.28), 0.012)), 'd11-estandar.jpg')

    # 12 · la Sprinter esperando en el acceso (fondo atmosférico de "Durante el festival, estamos ahí")
    im = Image.open(ORIG / 'sprinter-noche.jpg').convert('RGB')
    a = to_f(im.crop((0, 230, 2000, 1072)).resize((1920, 808), Image.LANCZOS))
    o = tone(a, NIGHT_STOPS, keep=0.45, sat=0.7, exposure=1.45, gamma=0.88)
    o = blur_rgb(o, 7)                                                          # desenfocada: atmósfera, no detalle
    save(to_im(grain(o, 0.012)), 'n12-sprinter-acceso.jpg')

if __name__ == '__main__':
    jobs = sys.argv[1:] or ['cover_hc', 'mesas', 'day_photos', 'bokeh', 'grano', 'nuevas']
    for j in jobs:
        globals()[j]()
