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


def save(img, name, q=88, max_kb=380):
    p = OUT / name
    while True:
        img.save(p, quality=q, optimize=True, progressive=True, subsampling='4:2:0')
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


# ------------------------------------------------------------------ 01 portada
def cover():
    """Suburban at native resolution (1280 px), black lacquer, headlight on, teal backlight.
    Output: full anamorphic plate 1920x808 (photo 1:1 on the right, faded into the night)."""
    src = Image.open(SRC / 'tulum-suburban.jpg').convert('RGB')
    a = to_f(src)
    h, w = a.shape[:2]                     # 785 x 1280
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    L = lum(a)
    yy = np.mgrid[0:h, 0:w][0] / h
    truck = poly_mask(w, h, [(241, 476), (257, 457), (330, 432), (450, 402), (492, 402), (600, 408), (704, 417),
                             (770, 455), (836, 497), (960, 508), (1092, 531), (1112, 562), (1120, 640), (1117, 720),
                             (1103, 785), (690, 785), (680, 772), (535, 774), (528, 760), (320, 754), (314, 785),
                             (224, 785), (206, 704), (197, 640), (198, 560)], 1.6)
    sky = blur((((b - r) > 0.08) & (b > 0.40) | ((L > 0.62) & ((a.max(-1) - a.min(-1)) < 0.2) & (yy < 0.62))).astype(np.float32), 4)
    sky *= (1 - truck)
    leafy = blur(((g > r * 1.0) & (g > b * 0.92) & (L < 0.75)).astype(np.float32), 2.5) * (1 - truck)
    ground = np.clip((yy - 0.80) / 0.06, 0, 1) * (1 - truck)

    # refine the body mask: inside the polygon, drop clearly green (tree) pixels
    treeish = ((g > r * 1.06) & (g > b * 1.0) & (L > 0.16)).astype(np.float32)
    truck = blur(np.clip(truck - blur(treeish, 1.0) * 1.2, 0, 1), 1.2)
    # 1 · body: black lacquer curve (microcontrast first, at native size)
    sharp = unsharp(a, 1.4, 70, 2)
    body = tone(sharp, LACQUER_STOPS, keep=0.10, sat=0.25, exposure=0.98, gamma=1.55)
    glass = np.maximum(poly_mask(w, h, [(505, 414), (704, 419), (768, 456), (832, 496), (690, 502), (520, 500)], 3),
                       poly_mask(w, h, [(222, 522), (250, 472), (330, 442), (450, 414), (520, 414), (556, 470),
                                        (540, 534), (222, 542)], 3))
    body = body * (1 - glass[..., None]) + (blur_rgb(body, 2.5) * 0.32) * glass[..., None]
    # 2 · jungle: a soft, out-of-focus night mass (shallow depth of field)
    env = tone(a, NIGHT_STOPS, keep=0.05, sat=0.2, exposure=0.72, gamma=1.5)
    env = env * (1 - sky[..., None]) + (DEEP * 0.9)[None, None, :] * sky[..., None]
    env = blur_rgb(env, 9) * 0.78
    env *= (1 - 0.5 * np.clip(1 - yy / 0.55, 0, 1))[..., None]
    # 3 · teal backlight haze behind the roof (separates the black truck from the black jungle)
    haze = gauss(h, w, 660, 440, 560, 120)
    env = env + (TEAL * 0.58)[None, None, :] * haze[..., None]
    # 4 · ground goes to night, except the light pool
    gnd = np.clip((yy - 0.79) / 0.05, 0, 1)
    env = env * (1 - 0.6 * gnd[..., None])
    out = env * (1 - truck[..., None]) + body * truck[..., None]
    # thin teal rim on the roof line where the haze wraps the body
    rim = gauss(h, w, 600, 410, 330, 10) * truck
    out = out + (TEAL * 0.5)[None, None, :] * rim[..., None]

    # 5 · plate: neutralised (no characters, reads as an unlit plate)
    plate = poly_mask(w, h, [(992, 689), (1061, 689), (1061, 748), (992, 748)], 2.5)
    pl = blur_rgb(out, 6) * 0.25 + DEEP * 0.4
    out = out * (1 - plate[..., None]) + pl * plate[..., None]
    # 6 · practicals: DRL strip, headlamp glow, warm light pool on the road, spill on chrome
    drl = gauss(h, w, 798, 573, 62, 3.2) + 0.7 * gauss(h, w, 840, 600, 4, 28) * (yy > 0.72)
    lamp = gauss(h, w, 790, 560, 70, 18)
    bloom = gauss(h, w, 800, 570, 190, 46)
    out = out + ARENA[None, None, :] * np.clip(drl, 0, 1)[..., None] * 0.95 \
        + (GOLD * 0.9)[None, None, :] * lamp[..., None] * 0.55 \
        + (GOLD * 0.8)[None, None, :] * bloom[..., None] * 0.22
    pool = gauss(h, w, 1020, 800, 360, 46) * (1 - blur(truck, 10) * 0.9)
    out = out + (GOLD * 0.55)[None, None, :] * pool[..., None] * 0.55
    spill = gauss(h, w, 960, 600, 200, 70) * truck
    out = out * (1 + 0.3 * spill[..., None])

    # 8 · composite on the 2.39 plate, photo 1:1 on the right
    FW, FH = 1920, 808
    frame = np.zeros((FH, FW, 3), np.float32)
    fy = np.linspace(0, 1, FH)[:, None, None]
    fx = np.linspace(0, 1, FW)[None, :, None]
    frame[:] = DEEP * (1 - fy) * 0.9 + NIGHT * fy * 0.95
    frame = frame * (0.92 + 0.08 * fx)
    SHIFT = 80                             # photo slides right; its last 80 px fall outside the plate
    ox, oy = FW - w + SHIFT, FH - h        # 720, 23
    vis = w - SHIFT
    ramp = np.clip(np.arange(vis) / 520, 0, 1) ** 1.6
    top = np.clip(np.arange(h) / 60, 0, 1) ** 1.2
    alpha = (ramp[None, :] * top[:, None])[..., None]
    region = frame[oy:oy + h, ox:ox + vis]
    frame[oy:oy + h, ox:ox + vis] = out[:, :vis] * alpha + region * (1 - alpha)
    # vignette (derived deep teal only as vignette)
    v = radial(FH, FW, FW * 0.70, FH * 0.62, FW * 0.75, FH * 1.0, 0.9)
    frame = frame * (0.70 + 0.30 * v[..., None])
    frame = grain(frame, 0.016)
    print('cover: DRL core at frame', ox + 798, oy + 573, '-> canvas y', 136 + oy + 573)
    save(to_im(frame), 'n01-suburban-noche.jpg', q=88)


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
    # 08 · chauffeur opening the V-Class door (discreet reception)
    a = crop_scale('chauffeur-vclass.jpg', (200, 56, 1400, 1066), (960, 808))
    o = day_grade(a)
    h, w = o.shape[:2]
    o = o * (0.90 + 0.10 * radial(h, w, w * 0.55, h * 0.45, w * 0.9, h * 0.9, 1.0)[..., None])
    save(to_im(grain(o, 0.012)), 'd08-chofer-dia.jpg')
    # 09 · guest stepping out of the V-Class
    a = crop_scale('hero.jpg', (190, 188, 1322, 1141), (960, 808))
    o = day_grade(a)
    h, w = o.shape[:2]
    o = o * (0.90 + 0.10 * radial(h, w, w * 0.5, h * 0.45, w * 0.9, h * 0.9, 1.0)[..., None])
    save(to_im(grain(o, 0.012)), 'd09-invitada-dia.jpg')
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
    a = crop_scale('premium-sprinter.jpg', (0, 60, 1000, 606), (1000, 546))
    o = tone(a, NIGHT_STOPS, keep=0.30, sat=0.5, exposure=1.9, gamma=0.9)
    save(to_im(grain(o, 0.014)), 'n11-sprinter.jpg')


# ------------------------------------------------------------------ 14 · chofer al volante (noche)
def volante():
    a = to_f(Image.open(SRC / 'chauffeur.jpg').convert('RGB'))   # 1000 x 760, native
    h, w = a.shape[:2]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    L = lum(a)
    yy, xx = np.mgrid[0:h, 0:w]
    yy = yy / h
    xx = xx / w
    zone = poly_mask(w, h, [(300, 0), (1000, 0), (1000, 150), (700, 140), (560, 150), (420, 120), (330, 60)], 6)
    win = blur((((g > r * 1.0) & (g > b * 0.95)) | (L > 0.55)).astype(np.float32) * zone, 3)
    win = np.clip((win - 0.3) / 0.4, 0, 1)
    o = tone(a, NIGHT_STOPS, keep=0.40, sat=0.55, exposure=0.80, gamma=1.12)
    night = np.ones_like(a) * (DEEP * 0.7 + NIGHT * 0.3)
    bk = Image.new('RGB', (w, h), (0, 0, 0))
    dr = ImageDraw.Draw(bk)
    for (bx, by, br, col, k) in [(820, 60, 26, (201, 165, 92), .26), (905, 105, 14, (4, 101, 103), .8), (640, 70, 18, (201, 165, 92), .22)]:
        dr.ellipse([bx - br, by - br, bx + br, by + br], fill=tuple(int(v * k) for v in col))
    night = night + to_f(bk.filter(ImageFilter.GaussianBlur(4)))
    o = o * (1 - win[..., None]) + night * win[..., None]
    # instrument glow (teal) and a warm key on the hands
    o = o + (TEAL * 0.55)[None, None, :] * gauss(h, w, 800, 300, 160, 70)[..., None]
    o = dodge(o, [(700, 250, 70, 0.25), (860, 300, 60, 0.25)])
    o = o * (0.62 + 0.38 * radial(h, w, w * 0.62, h * 0.42, w * 0.85, h * 0.9, 0.9)[..., None])
    save(to_im(grain(o, 0.016)), 'n14-volante-noche.jpg')


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


if __name__ == '__main__':
    jobs = sys.argv[1:] or ['cover', 'mesas', 'day_photos', 'volante', 'bokeh', 'grano']
    for j in jobs:
        globals()[j]()
