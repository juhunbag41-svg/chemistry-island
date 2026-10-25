# -*- coding: utf-8 -*-
"""화학 섬 이야기용 픽셀아트 스프라이트 생성 스크립트.
이 폴더의 PNG 파일과 manifest.js 는 모두 이 스크립트가 만든 결과물이다. (외부 이미지 사용 없음)
실행: python make_sprites.py
"""
import os, math, random, struct, zlib, json

HERE = os.path.dirname(os.path.abspath(__file__))


def hexc(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def mix(c, t, f):
    return tuple(int(c[i] + (t[i] - c[i]) * f) for i in range(3)) + (255,)


def lit(c, f):
    return mix(c, (255, 255, 255, 255), f)


def drk(c, f):
    return mix(c, (0, 0, 0, 255), f)


class Img:
    def __init__(s, w, h):
        s.w, s.h = w, h
        s.p = [[None] * w for _ in range(h)]

    def set(s, x, y, c):
        if 0 <= x < s.w and 0 <= y < s.h:
            s.p[y][x] = (hexc(c) if isinstance(c, str) else c)

    def get(s, x, y):
        if 0 <= x < s.w and 0 <= y < s.h:
            return s.p[y][x]
        return None

    def rect(s, x, y, w, h, c):
        for j in range(h):
            for i in range(w):
                s.set(x + i, y + j, c)

    def ell(s, cx, cy, rx, ry, c):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1:
                    s.set(x, y, c)

    def paste(s, o, ox, oy):
        for y in range(o.h):
            for x in range(o.w):
                if o.p[y][x] is not None:
                    s.set(ox + x, oy + y, o.p[y][x])

    def mask(s):
        m = Img(s.w, s.h)
        for y in range(s.h):
            for x in range(s.w):
                if s.p[y][x] is not None:
                    m.p[y][x] = (1, 1, 1, 255)
        return m

    def outline(s, f=0.55):
        res = [row[:] for row in s.p]
        for y in range(s.h):
            for x in range(s.w):
                if s.p[y][x] is None:
                    for dx, dy in ((-1, 0), (0, -1), (1, 0), (0, 1)):
                        n = s.get(x + dx, y + dy)
                        if n is not None:
                            res[y][x] = drk(n, f)
                            break
        s.p = res

    def save(s, path):
        raw = b''.join(b'\x00' + bytes(v for px in row for v in (px if px else (0, 0, 0, 0))) for row in s.p)

        def ch(t, d):
            c = struct.pack('>I', len(d)) + t + d
            return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
        with open(path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', s.w, s.h, 8, 6, 0, 0, 0))
                    + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b''))


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def pack(items, width):
    x = y = rowh = 0
    placed = {}
    for name, im in items:
        if x + im.w > width:
            x = 0
            y += rowh
            rowh = 0
        placed[name] = [x, y, im.w, im.h]
        x += im.w
        rowh = max(rowh, im.h)
    atlas = Img(width, y + rowh)
    for name, im in items:
        r = placed[name]
        atlas.paste(im, r[0], r[1])
    return atlas, placed


# ------------------------------------------------------------------ 팔레트
GRASS = [("#82d46c", "#72c45c", "#9be585", "#5fb458"), ("#7ecf68", "#6ebf58", "#97e081", "#5aaf55"),
         ("#86d870", "#76c860", "#a0ea8a", "#64b85c"), ("#7bcd66", "#6bbd56", "#94de7f", "#58ad52"),
         ("#8ddc76", "#7bcc64", "#a8f092", "#68bc5e"), ("#88d772", "#78c75e", "#a2e98c", "#62b65a"),
         ("#91df7a", "#80cf68", "#aef298", "#6cc062"), ("#8bda74", "#7aca62", "#a6ec90", "#66ba5c")]


# ------------------------------------------------------------------ 타일
def tile_grass(v):
    rnd = random.Random(100 + v)
    base, d1, l1, d2 = [hexc(c) for c in GRASS[v]]
    im = Img(16, 16)
    im.rect(0, 0, 16, 16, base)
    for y in range(16):
        for x in range(16):
            if BAYER[(y + v) % 4][(x + 2 * v) % 4] < 3:
                im.set(x, y, d1)
    for _ in range(7):
        im.set(rnd.randrange(16), rnd.randrange(16), l1)
    for _ in range(2 + v % 2):
        x, y = rnd.randrange(1, 13), rnd.randrange(3, 14)
        im.set(x, y + 1, d2)
        im.set(x + 1, y, d2)
        im.set(x + 2, y + 1, d2)
        im.set(x + 1, y + 1, l1)
    return im


def tile_sand(v):
    rnd = random.Random(200 + v)
    pal = [("#f4e1a4", "#e8cf8c", "#fff3c9", "#d9bb78"), ("#f2dfa0", "#e6cd88", "#fff0c2", "#d6b874"),
           ("#f6e4a9", "#ead292", "#fff8d8", "#dcc07c"), ("#f3e0a2", "#e7ce8a", "#fff1c6", "#d8ba76")][v]
    base, d1, l1, d2 = [hexc(c) for c in pal]
    im = Img(16, 16)
    im.rect(0, 0, 16, 16, base)
    for y in range(16):
        for x in range(16):
            if BAYER[(y + v) % 4][(x + v) % 4] < 2:
                im.set(x, y, d1)
    for _ in range(5):
        im.set(rnd.randrange(16), rnd.randrange(16), l1)
    for _ in range(3):
        im.set(rnd.randrange(16), rnd.randrange(16), d2)
    y = 3 + v * 3
    im.rect(2 + v, y, 4, 1, d1)
    im.rect(9 - v, y + 6, 3, 1, d1)
    return im


def tile_snow(v):
    rnd = random.Random(300 + v)
    base, d1, l1 = hexc("#f6faff"), hexc("#dcebfa"), hexc("#ffffff")
    im = Img(16, 16)
    im.rect(0, 0, 16, 16, base)
    for y in range(16):
        for x in range(16):
            if BAYER[(y + v) % 4][(x + v) % 4] < 3:
                im.set(x, y, d1)
    for _ in range(4):
        im.set(rnd.randrange(16), rnd.randrange(16), l1)
    for _ in range(2):
        im.set(rnd.randrange(16), rnd.randrange(16), hexc("#c3d9ee"))
    return im


def tile_path(v, center):
    rnd = random.Random(400 + v + (10 if center else 0))
    base = hexc("#e6c99a" if center else "#dfbf8f")
    d1 = hexc("#d6b080" if center else "#cfa876")
    l1 = hexc("#f2dcb4" if center else "#ecd3a8")
    pb = hexc("#b58a5a")
    im = Img(16, 16)
    im.rect(0, 0, 16, 16, base)
    for y in range(16):
        for x in range(16):
            if BAYER[(y + v) % 4][(x + 2 * v) % 4] < (2 if center else 3):
                im.set(x, y, d1)
    for _ in range(4):
        im.set(rnd.randrange(16), rnd.randrange(16), l1)
    for _ in range(2 + (0 if center else 1)):
        x, y = rnd.randrange(1, 14), rnd.randrange(1, 14)
        im.set(x, y, pb)
        im.set(x + 1, y, d1)
        im.set(x, y - 1, l1)
    return im


def tile_plaza(v):
    rnd = random.Random(500 + v)
    base = hexc("#e6e0d0" if v == 0 else "#e9e3d3")
    grout, lt, dk = hexc("#c9c2ae"), hexc("#f4efe2"), hexc("#d3ccb8")
    im = Img(16, 16)
    im.rect(0, 0, 16, 16, base)
    im.rect(0, 7, 16, 1, grout)
    im.rect(0, 15, 16, 1, grout)
    im.rect(7 if v == 0 else 4, 0, 1, 8, grout)
    im.rect(15 if v == 0 else 11, 8, 1, 8, grout)
    for _ in range(6):
        im.set(rnd.randrange(16), rnd.randrange(16), dk)
    im.rect(1, 1, 4, 1, lt)
    im.rect(9, 9, 4, 1, lt)
    return im


def tile_deck(v):
    base, line, lt, dk = hexc("#cf9a62"), hexc("#a8743f"), hexc("#e2b282"), hexc("#8a5a30")
    im = Img(16, 16)
    im.rect(0, 0, 16, 16, base)
    for i in (3, 7, 11, 15):
        im.rect(0, i, 16, 1, line)
    off = 6 if v else 0
    im.rect(2 + off, 1, 5, 1, lt)
    im.rect(8 - off // 2, 5, 5, 1, lt)
    im.rect(4, 9, 5, 1, lt)
    im.rect(10, 13, 4, 1, lt)
    im.set(1 + off, 2, dk)
    im.set(13, 10, dk)
    im.set(5, 6, dk)
    return im


def tile_water(kind, v, f):
    pal = {"sea": ("#58bfe0", "#4aaed0", "#7dd3ec", "#a6e6f5"),
           "river": ("#6fd0ea", "#5cbcd8", "#8fe0f2", "#b4eef9")}[kind]
    base, dark, light, hl = [hexc(c) for c in pal]
    im = Img(16, 16)
    for y in range(16):
        for x in range(16):
            w = math.sin(2 * math.pi * (x + 4 * f) / 16 + 2 * math.pi * 2 * y / 16 + v * 1.7)
            w2 = math.sin(2 * math.pi * (x - 4 * f) / 16 * 2 + 2 * math.pi * y / 16 * 3 + v)
            c = base
            if w > .88:
                c = hl
            elif w > .62:
                c = light
            elif w2 < -.9 or w < -.88:
                c = dark
            im.set(x, y, c)
    return im


def tile_pond(f):
    base, hl, crack = hexc("#c4ecfb"), hexc("#ffffff"), hexc("#9ed6ee")
    im = Img(16, 16)
    im.rect(0, 0, 16, 16, base)
    for y in range(16):
        for x in range(16):
            if BAYER[y % 4][x % 4] < 2:
                im.set(x, y, hexc("#b6e3f6"))
    im.rect(2 + f, 4, 5, 1, hl)
    im.rect(8, 10 + (f % 2), 5, 1, hl)
    for i in range(4):
        im.set(5 + i % 2, 8 + i, crack)
    im.set(12, 3, hl)
    return im


# ------------------------------------------------------------------ 식생·바위
def shade_blob(mask, pal, seed, bias=0.0, strength=0.9):
    rnd = random.Random(seed)
    pts = [(x, y) for y in range(mask.h) for x in range(mask.w) if mask.p[y][x]]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    cx, cy, hw, hh = (x0 + x1) / 2, (y0 + y1) / 2, max(1, (x1 - x0) / 2), max(1, (y1 - y0) / 2)
    out = Img(mask.w, mask.h)
    n = len(pal)
    for (x, y) in pts:
        nx, ny = (x - cx) / hw, (y - cy) / hh
        b = 0.5 - 0.5 * (0.55 * nx + 0.8 * ny) * strength + bias
        b -= 0.22 * max(0, ny - 0.25)
        b += (BAYER[y % 4][x % 4] / 16 - 0.5) * 0.30
        idx = max(0, min(n - 1, int(b * n)))
        out.p[y][x] = pal[idx]
    return out


def clumps(im, pal, seed, count):
    rnd = random.Random(seed)
    pts = [(x, y) for y in range(im.h) for x in range(im.w) if im.p[y][x]]
    for _ in range(count):
        px, py = rnd.choice(pts)
        for dx, dy in ((2, 0), (2, 1), (1, 2), (0, 2)):
            if im.get(px + dx, py + dy):
                im.set(px + dx, py + dy, pal[0])
        for dx, dy in ((0, 0), (1, -1)):
            if im.get(px + dx, py + dy):
                im.set(px + dx, py + dy, pal[-1])


FOL = [hexc(c) for c in ("#245f3f", "#2f7d4a", "#3f9b55", "#58b866", "#7ed07a", "#a6e69a")]
FOL2 = [hexc(c) for c in ("#2a6a4a", "#378a58", "#49a863", "#66c473", "#8cdc88", "#b4f0a6")]


def canopy(variant):
    shapes = {0: [(15, 13, 11), (8, 16, 8), (22, 16, 8), (15, 8, 8)],
              1: [(15, 12, 12), (7, 16, 8), (23, 16, 8), (11, 7, 8), (20, 7, 8)],
              2: [(14, 12, 10), (8, 15, 7), (21, 15, 7), (14, 7, 7)]}[variant % 3]
    m = Img(30, 28)
    for cx, cy, r in shapes:
        m.ell(cx, cy, r, r, (1, 1, 1, 255))
    pal = FOL if variant % 2 == 0 else FOL2
    im = shade_blob(m, pal, 11 + variant)
    clumps(im, pal, 21 + variant, 9)
    return im


def canopy_fruit(variant):
    im = canopy(variant)
    rnd = random.Random(77 + variant)
    pts = [(x, y) for y in range(4, im.h - 4) for x in range(4, im.w - 4) if im.p[y][x]]
    for _ in range(6):
        px, py = rnd.choice(pts)
        im.set(px, py, hexc("#d93a4a"))
        im.set(px + 1, py, hexc("#ff6b6b"))
        im.set(px, py + 1, hexc("#a82838"))
        im.set(px + 1, py + 1, hexc("#d93a4a"))
    return im


def canopy_outlined(im):
    im.outline(0.55)
    return im


def trunk():
    im = Img(12, 16)
    br = [hexc(c) for c in ("#4a2f1f", "#6b4429", "#8a5a34", "#a8723f")]
    widths = [4] * 10 + [5, 6, 6, 8, 8, 8]
    rnd = random.Random(5)
    for y, w in enumerate(widths):
        x0 = 6 - w // 2
        for i in range(w):
            c = br[3] if i == 0 else br[2] if i < w - 2 else br[1] if i < w - 1 else br[0]
            if w <= 4 and i == w - 1:
                c = br[1]
            im.set(x0 + i, y, c)
    for _ in range(4):
        im.set(6 + rnd.randrange(-1, 2), rnd.randrange(0, 10), br[0])
    im.outline(0.5)
    return im


def pine(snow):
    im = Img(26, 34)
    base = [hexc(c) for c in ("#1f5a3a", "#2b7b4e", "#3a9a62", "#58b97a")]
    cx = 13
    for i in range(3):
        y0 = 1 + i * 9
        for r in range(11):
            y = y0 + r
            hw = 1 + int(r * (0.62 + 0.12 * i))
            for x in range(cx - hw, cx + hw + 1):
                t = (x - (cx - hw)) / max(1, 2 * hw)
                c = base[3] if t < .25 else base[2] if t < .55 else base[1] if t < .85 else base[0]
                if (x + y) % 5 == 0:
                    c = lit(c, .08)
                im.set(x, y, c)
            if snow and r < 3:
                for x in range(cx - hw, cx + hw + 1):
                    if (x + r) % 4 != 3:
                        im.set(x, y, hexc("#f2f8ff") if x < cx + hw - 1 else hexc("#cfe0f2"))
    im.outline(0.55)
    return im


def rock(v):
    m = Img(16, 13)
    for cx, cy, rx, ry in [[(8, 8, 7, 5), (5, 7, 4, 4), (11, 8, 4, 4)], [(8, 8, 7, 4), (6, 6, 5, 4)],
                          [(7, 8, 6, 5), (11, 9, 4, 3), (5, 6, 3, 3)]][v % 3]:
        m.ell(cx, cy, rx, ry, (1, 1, 1, 255))
    pal = [hexc(c) for c in ("#5d6570", "#79828d", "#99a2ad", "#bcc4cd", "#e1e6eb")]
    im = shade_blob(m, pal, 31 + v)
    rnd = random.Random(40 + v)
    for _ in range(3):
        x, y = rnd.randrange(3, 13), rnd.randrange(2, 7)
        if im.get(x, y):
            im.set(x, y, hexc("#6aa860"))
            if im.get(x + 1, y):
                im.set(x + 1, y, hexc("#82c474"))
    im.outline(0.5)
    return im


def bush(v):
    m = Img(16, 13)
    for cx, cy, r in ((8, 8, 5), (4, 9, 4), (12, 9, 4), (8, 5, 4)):
        m.ell(cx, cy, r, r, (1, 1, 1, 255))
    im = shade_blob(m, FOL, 50 + v)
    clumps(im, FOL, 60 + v, 4)
    if v:
        for (x, y) in ((4, 7), (10, 6), (8, 9), (12, 9)):
            im.set(x, y, hexc("#ff6b8a"))
            im.set(x + 1, y, hexc("#ffa0b8"))
    im.outline(0.55)
    return im


def tuft(s):
    im = Img(12, 10)
    cols = [hexc("#4aa040"), hexc("#62b84c"), hexc("#7ccf5a"), hexc("#a0e47e")]
    for bx, h in ((3, 5), (6, 8), (9, 6)):
        for r in range(h):
            dx = int(round(s * (r / h) ** 1.4 * 1.6))
            y = 9 - r
            c = cols[0] if r < 2 else cols[1] if r < h - 2 else cols[2] if r < h - 1 else cols[3]
            im.set(bx + dx, y, c)
            if r < 2:
                im.set(bx + dx + 1, y, cols[0])
    return im


PFL = {"pink": ("#ff7aa8", "#ffb0cc", "#d94a78"), "white": ("#ffffff", "#f0f0f8", "#c8c8d8"),
       "yellow": ("#ffd84a", "#fff08a", "#d8a820"), "orange": ("#ff9a5a", "#ffc08a", "#d87030"), "purple": ("#b58cff", "#d6c0ff", "#8a64d8"),
       "blue": ("#7ab4ff", "#b0d4ff", "#4a84d8")}


def pflower(color, s, big=False):
    c, hi, lo = [hexc(x) for x in PFL[color]]
    im = Img(10 if not big else 12, 12 if not big else 14)
    st = hexc("#3f9a3f")
    bx = 5 if not big else 6
    top = 3 if not big else 3
    for r in range(8):
        dx = int(round(s * (r / 8) ** 1.4 * 1.4))
        im.set(bx - dx * 0 + dx, im.h - 1 - r, st)
    hx = bx + int(round(s * 1.4))
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        im.set(hx + dx, top + dy, c)
    im.set(hx - 1, top - 1, hi)
    im.set(hx + 1, top + 1, lo)
    im.set(hx, top, hexc("#ffe27a"))
    im.set(bx + int(round(s * .5)) - 1, im.h - 4, hexc("#5cb85c"))
    return im


def cane(s):
    im = Img(14, 20)
    cols = [hexc("#5cb04a"), hexc("#7ccf5a"), hexc("#a0e47e")]
    for bx, h in ((3, 14), (7, 18), (11, 12)):
        for r in range(h):
            dx = int(round(s * (r / h) ** 1.4 * 1.4))
            im.set(bx + dx, 19 - r, cols[1] if r % 5 else cols[0])
        tx = bx + int(round(s * 1.4))
        for dy in range(3):
            im.set(tx, 19 - h - dy, hexc("#e8a0b0"))
        im.set(tx + 1, 19 - h - 1, hexc("#f4c8d4"))
    return im


# ------------------------------------------------------------------ 해변·장식물
def shell(v):
    im = Img(8, 6)
    c1, c2 = [(hexc("#fff0f4"), hexc("#f4b8c8")), (hexc("#fff6e0"), hexc("#e8c888")), (hexc("#eaf6ff"), hexc("#a8cce8"))][v]
    for x, y in ((2, 3), (3, 2), (4, 2), (5, 3)):
        im.set(x, y, c1)
    for x in range(2, 6):
        im.set(x, 4, c2)
    im.set(3, 3, c2)
    im.set(4, 3, c1)
    im.outline(0.35)
    return im


def starfish():
    im = Img(9, 9)
    c, d = hexc("#f08a5c"), hexc("#c85a3a")
    for x, y in ((4, 1), (3, 2), (4, 2), (5, 2), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3), (7, 3), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4),
                 (2, 5), (3, 5), (5, 5), (6, 5), (1, 6), (2, 6), (6, 6), (7, 6)):
        im.set(x, y, c)
    for x, y in ((4, 3), (4, 4), (3, 5), (5, 5)):
        im.set(x, y, d)
    im.set(4, 2, hexc("#ffb088"))
    im.outline(0.45)
    return im


def driftwood():
    im = Img(14, 5)
    for x in range(14):
        for y in range(1, 4):
            im.set(x, y, hexc("#b8946a") if y == 1 else hexc("#9a784f") if y == 2 else hexc("#7a5a38"))
    im.set(3, 2, hexc("#5a3f26"))
    im.set(9, 1, hexc("#5a3f26"))
    im.outline(0.4)
    return im


def seaweed():
    im = Img(8, 10)
    for i, (x, y) in enumerate(((3, 9), (3, 8), (4, 7), (4, 6), (3, 5), (3, 4), (4, 3), (4, 2))):
        im.set(x, y, hexc("#2f8a5a") if i % 2 else hexc("#3fa56e"))
        im.set(x + 1, y, hexc("#5fc88a"))
    return im


def mushroom(v):
    im = Img(8, 8)
    cap = hexc("#d93a3a") if v == 0 else hexc("#b8844a")
    for x, y in ((2, 3), (3, 2), (4, 2), (5, 2), (6, 3), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4)):
        im.set(x, y, cap)
    for x, y in ((3, 3), (5, 3)):
        im.set(x, y, hexc("#ffffff") if v == 0 else hexc("#e6c898"))
    for y in (5, 6):
        for x in (3, 4, 5):
            im.set(x, y, hexc("#f2e6cc"))
    im.outline(0.45)
    return im


def fern(s):
    im = Img(14, 10)
    c = [hexc("#2f8a4a"), hexc("#49a863"), hexc("#7ccf7a")]
    for i, (dx, dy) in enumerate(((-1, -1), (-1, 0), (-1, 1), (0, -1), (1, -1), (1, 0), (1, 1))):
        for r in range(1, 6):
            x = 7 + dx * r + (int(round(s * r / 6)) if dy < 0 else 0)
            y = 9 - r * (2 if dy < 0 else 1) // (1 if dx else 2) - (0 if dx else 0)
            im.set(x, y, c[1] if r % 2 else c[0])
    for r in range(1, 8):
        im.set(7 + int(round(s * r / 8)), 9 - r, c[2] if r % 2 else c[1])
    return im


def clover():
    im = Img(8, 6)
    c = [hexc("#3f9a3f"), hexc("#5cb85c")]
    for x, y in ((1, 2), (2, 1), (2, 2), (3, 2), (4, 2), (5, 1), (5, 2), (6, 2), (3, 3), (4, 3), (3, 4)):
        im.set(x, y, c[(x + y) % 2])
    return im


def pebbles(v):
    im = Img(8, 4)
    g1, g2 = hexc("#9aa3ad"), hexc("#c4ccd4")
    pts = [((1, 1), (2, 1), (1, 2), (2, 2), (5, 2), (6, 2)), ((2, 1), (3, 1), (2, 2), (3, 2), (5, 0), (6, 0), (6, 1))][v]
    for x, y in pts:
        im.set(x, y, g1)
    im.set(pts[0][0], pts[0][1], g2)
    im.outline(0.4)
    return im


def lilypad(v):
    im = Img(12, 8)
    g1, g2 = hexc("#4ab868"), hexc("#7ed89a")
    for y in range(1, 7):
        for x in range(1, 11):
            if ((x - 5.5) / 5) ** 2 + ((y - 3.5) / 2.8) ** 2 <= 1 and not (x >= 6 and y == 3):
                im.set(x, y, g1 if (x + y) % 3 else g2)
    if v:
        for x, y in ((5, 2), (6, 2), (5, 3), (4, 2)):
            im.set(x, y, hexc("#ffb0cc"))
        im.set(5, 2, hexc("#ffe27a"))
    return im


def water_rock():
    im = Img(12, 9)
    m = Img(12, 9)
    m.ell(6, 5, 5, 3.5, (1, 1, 1, 255))
    pal = [hexc(c) for c in ("#5d6570", "#79828d", "#99a2ad", "#bcc4cd", "#e1e6eb")]
    im = shade_blob(m, pal, 99)
    im.outline(0.5)
    return im


def reeds(s):
    im = Img(10, 16)
    cols = [hexc("#4a9a3a"), hexc("#6cbc4c")]
    for bx, h in ((2, 11), (5, 15), (8, 10)):
        for r in range(h):
            dx = int(round(s * (r / h) ** 1.3 * 1.3))
            im.set(bx + dx, 15 - r, cols[r % 2])
        tx = bx + int(round(s * 1.3))
        im.set(tx, 15 - h, hexc("#8a5a34"))
        im.set(tx, 15 - h - 1, hexc("#a8743f"))
    return im


def flowerbed():
    im = Img(16, 14)
    soil = [hexc("#8a5a34"), hexc("#a8743f"), hexc("#6a4424")]
    for y in range(14):
        for x in range(16):
            if ((x - 7.5) / 8) ** 2 + ((y - 7) / 6.5) ** 2 <= 1:
                im.set(x, y, soil[(x + 2 * y) % 5 == 0 and 2 or (x * y) % 7 == 0 and 0 or 1])
    for x, y in ((1, 6), (2, 4), (13, 5), (12, 8), (3, 10), (11, 11), (6, 11), (8, 2)):
        im.set(x, y, hexc("#3f9a3f"))
        im.set(x + 1, y, hexc("#5cb85c"))
    for x, y, c in ((3, 4, "#ff7aa8"), (7, 3, "#ffd84a"), (11, 5, "#ffffff"), (5, 8, "#b58cff"), (10, 8, "#ff7aa8"), (8, 6, "#ffd84a"), (4, 10, "#ffffff"), (9, 10, "#b58cff")):
        im.rect(x - 1, y, 3, 1, hexc(c))
        im.set(x, y - 1, hexc(c))
        im.set(x, y + 1, hexc(c))
        im.set(x, y, hexc("#ffe27a"))
    return im


# ------------------------------------------------------------------ 건물
def shingle_roof(im, ox, oy, rc, kind):
    rl, rd, rdd = lit(rc, .2), drk(rc, .2), drk(rc, .42)
    im.rect(ox - 4, oy + 4, 88, 24, rc)
    for r in range(6):
        yy = oy + 4 + r * 4
        tint = lit(rc, .10 - r * .035)
        im.rect(ox - 4, yy, 88, 3, tint)
        im.rect(ox - 4, yy + 3, 88, 1, rd)
        for i in range(0, 88, 8):
            im.rect(ox - 4 + i + (r % 2) * 4, yy, 1, 3, rd)
            im.set(ox - 4 + i + (r % 2) * 4 + 2, yy, lit(rc, .28))
    im.rect(ox - 4, oy + 2, 88, 2, rdd)
    im.rect(ox - 4, oy + 4, 88, 1, rl)
    im.rect(ox - 4, oy + 27, 88, 3, rdd)
    im.rect(ox - 5, oy + 6, 1, 22, rd)
    im.rect(ox + 84, oy + 6, 1, 22, rdd)


def building(kind):
    im = Img(96, 88)
    ox, oy = 8, 16
    P = lambda x, y, w, h, c: im.rect(ox + x, oy + y, w, h, hexc(c) if isinstance(c, str) else c)
    cfg = {"home": ("#fbe9c4", "#c9573f", "#e8d3a0", "#7a4a2a", "#6fae5a"),
           "kitchen": ("#fff0d2", "#e19a2c", "#f0d9a8", "#b8601c", "#e8802a"),
           "workshop": ("#d9e0ea", "#4f84c0", "#b8c4d6", "#4a5a78", "#8a98b0"),
           "shop": ("#f7ecd3", "#3f9f5c", "#e4d2a6", "#5a7a3a", "#3f9f5c")}[kind]
    W, RC, WD, TR, AC = [hexc(c) for c in cfg]
    # 벽
    P(4, 26, 72, 38, W)
    for i in range(0, 72, 6):
        P(4 + i, 26, 1, 38, WD)
    P(4, 26, 2, 38, lit(W, .5))
    P(74, 26, 2, 38, drk(W, .14))
    P(4, 57, 72, 1, hexc("#d6c3a0"))
    P(4, 58, 72, 6, hexc("#b8a688"))
    for i in range(0, 72, 8):
        P(4 + i, 58, 1, 6, hexc("#9a8a70"))
        P(8 + i, 61, 4, 1, hexc("#cbbba0"))
    # 창문
    shut = drk(RC, .1) if kind != "workshop" else hexc("#6b7a98")
    for wx in (12, 52):
        P(wx - 2, 36, 20, 18, shut)
        P(wx - 2, 36, 20, 1, lit(shut, .3))
        P(wx, 38, 16, 14, "#ffffff")
        P(wx + 1, 39, 14, 6, "#6fa8cf")
        P(wx + 1, 45, 14, 6, "#4e8bb8")
        P(wx + 7, 39, 2, 12, "#ffffff")
        P(wx + 1, 44, 14, 2, "#ffffff")
        P(wx + 2, 40, 3, 1, "#cfe8ff")
        P(wx + 9, 46, 2, 1, "#8cbfe0")
        P(wx - 1, 52, 18, 3, "#8a5a34")
        P(wx, 51, 16, 2, "#a8743f")
        P(wx + 1, 49, 3, 3, "#ff7aa8")
        P(wx + 6, 49, 3, 3, "#ffd84a")
        P(wx + 11, 49, 3, 3, "#b58cff")
        P(wx + 2, 52, 12, 1, "#4aa04a")
    # 문
    P(30, 38, 20, 26, "#5a3a22")
    P(32, 40, 16, 24, "#8a5a34")
    P(32, 40, 16, 1, "#a8743f")
    P(34, 42, 12, 9, "#a8743f")
    P(34, 53, 12, 9, "#a8743f")
    P(34, 42, 12, 1, "#c08850")
    P(34, 53, 12, 1, "#c08850")
    P(43, 54, 2, 2, "#ffd84a")
    P(28, 62, 24, 3, "#cdbb98")
    P(30, 64, 20, 1, "#a89878")
    P(33, 65, 14, 3, "#c0504d")
    P(34, 66, 12, 1, "#e08a7a")
    # 지붕
    shingle_roof(im, ox, oy, RC, kind)
    P(4, 30, 72, 3, mix(W, (0, 0, 0, 255), .17))
    # 건물별 개성
    if kind == "home":
        P(62, -8, 9, 14, "#a8553c")
        P(62, -8, 9, 3, "#7a3a28")
        P(63, -5, 2, 9, "#c4745a")
        P(34, 10, 20, 17, W)
        P(38, 14, 12, 9, "#6fa8cf")
        P(43, 14, 2, 9, "#ffffff")
        P(33, 7, 22, 4, drk(RC, .3))
        P(35, 5, 18, 3, drk(RC, .15))
        rnd = random.Random(3)
        for _ in range(26):
            im.set(ox + 66 + rnd.randrange(10), oy + 40 + rnd.randrange(22), hexc("#3f9a3f") if rnd.random() < .6 else hexc("#6fcf6a"))
        P(25, 44, 3, 5, "#ffd84a")
    elif kind == "kitchen":
        P(60, -10, 11, 16, "#b8643c")
        P(60, -10, 11, 3, "#8a4424")
        P(61, -6, 2, 10, "#d48a5c")
        for i, c in enumerate((hexc("#ffffff"), hexc("#d3d3dc"), hexc("#bfbfca"))):
            im.ell(ox + 65 + i * 2, oy - 14 - i * 4, 3 - i * .3, 2.5, c)
        for i in range(0, 28, 4):
            P(26 + i, 34, 4, 5, "#e8802a" if (i // 4) % 2 == 0 else "#fff0d0")
        P(26, 38, 28, 1, "#b8601c")
        P(18, 40, 2, 8, "#8a5a34")
        for dx, c in ((0, "#5aa84a"), (3, "#d93a3a")):
            P(16 + dx, 48, 3, 4, c)
    elif kind == "workshop":
        P(64, -6, 5, 12, "#7a869e")
        P(62, -8, 9, 3, "#5a6680")
        for ang in range(8):
            a = ang * math.pi / 4
            im.set(ox + 40 + int(round(math.cos(a) * 8)), oy + 16 + int(round(math.sin(a) * 8)), hexc("#cfd6e0"))
        im.ell(ox + 40, oy + 16, 6, 6, hexc("#aab4c4"))
        im.ell(ox + 40, oy + 16, 2.5, 2.5, drk(RC, .3))
        P(-6, 50, 9, 13, "#8a5a34")
        P(-6, 53, 9, 1, "#4a4a52")
        P(-6, 58, 9, 1, "#4a4a52")
        P(-5, 50, 2, 13, "#a8743f")
        P(76, 40, 3, 22, "#8c96a8")
        P(76, 40, 3, 2, "#aab4c4")
    else:
        for i in range(0, 80, 8):
            P(i, 30, 8, 7, "#3f9f5c" if (i // 8) % 2 == 0 else "#f4fff4")
            P(i, 36, 8, 2, "#2f7a48" if (i // 8) % 2 == 0 else "#d8ead8")
        P(64, -6, 7, 13, "#a8744a")
        P(64, -6, 7, 3, "#7a5030")
        P(78, 50, 10, 13, "#a8743f")
        P(78, 54, 10, 1, "#7a5030")
        P(80, 47, 3, 3, "#ff6b6b")
        P(84, 48, 3, 2, "#ffd84a")
        P(-4, 52, 8, 11, "#8a5a34")
        P(-3, 50, 6, 3, "#6fcf6a")
    im.outline(0.5)
    return im


# ------------------------------------------------------------------ 캐릭터
FR = ["idle0", "idle1", "w0", "w1", "w2", "w3", "blink", "reach", "adjust", "wave", "wave2", "count", "count2", "lookL", "lookR"]
FW, FH, AX, AY = 16, 36, 8, 35


def character(dr, frame, pal):
    im = Img(FW, FH)
    tag = Img(FW, FH)
    skin, hair, top, bottom = [hexc(pal[k]) for k in ("skin", "hair", "top", "bottom")]
    coat = hexc(pal["coat"]) if pal.get("coat") else None
    arm = coat or top
    sw, b = 0, 0
    pose, blink, lk, mouth = "", False, 0, False
    if frame == "idle1":
        b = 1
    elif frame in ("w0", "w1", "w2", "w3"):
        k = int(frame[1])
        sw, b = [0, 1, 0, -1][k], k % 2
    elif frame == "blink":
        blink = True
    elif frame in ("reach", "adjust", "wave", "wave2", "count", "count2"):
        pose = frame
    elif frame == "lookL":
        lk = -1
    elif frame == "lookR":
        lk = 1

    def R(lx, ly, w, h, c, t="x"):
        im.rect(AX + lx, AY + ly, w, h, c)
        tag.rect(AX + lx, AY + ly, w, h, (ord(t), 0, 0, 255))

    dark = hexc("#4a3326")
    R(-3, -5 - (1 if sw > 0 else 0), 3, 5, bottom, "L")
    R(1, -5 - (1 if sw < 0 else 0), 3, 5, bottom, "L")
    R(-3, -1, 3, 1, dark, "S")
    R(1, -1, 3, 1, dark, "S")
    R(-4, -12 - b, 8, 8, top, "C")
    if coat:
        R(-5, -12 - b, 10, 11, coat, "C")
        R(-1, -11 - b, 2, 10, hexc("#e0e0ea"), "C")
    R(-6, -11 - b + (1 if sw > 0 else 0), 2, 6, arm, "C")
    R(-6, -6 - b, 2, 2, skin, "K")
    if pose == "adjust":
        R(5, -18 - b, 2, 7, arm, "C")
        R(4, -20 - b, 3, 2, skin, "K")
    elif pose in ("wave", "wave2"):
        w = 1 if pose == "wave2" else 0
        R(5, -24 - b - w, 2, 9, arm, "C")
        R(5, -26 - b - w, 2, 2, skin, "K")
    elif pose == "reach":
        R(4, -13 - b, 2, 5, arm, "C")
        R(4, -15 - b, 2, 2, skin, "K")
    elif pose in ("count", "count2"):
        o = 1 if pose == "count2" else 0
        R(4, -10 - b + o, 2, 5, arm, "C")
        R(4, -6 - b + o, 2, 2, skin, "K")
    else:
        R(4, -11 - b + (1 if sw < 0 else 0), 2, 6, arm, "C")
        R(4, -6 - b, 2, 2, skin, "K")
    R(-5, -20 - b, 10, 8, skin, "K")
    R(-4, -21 - b, 8, 1, skin, "K")
    eyec = hexc("#2a1c14")

    def eye(ex, ey):
        if blink:
            R(ex, ey + 1, 1, 1, eyec, "E")
        else:
            R(ex, ey, 1, 2, eyec, "E")
    blush = hexc("#ff9aa2")
    if dr == 3:
        R(-5, -22 - b, 10, 10, hair, "H")
    else:
        R(-5, -22 - b, 10, 3, hair, "H")
        R(-4, -23 - b, 8, 1, hair, "H")
        if dr == 0:
            R(-5, -19 - b, 2, 4, hair, "H")
            R(3, -19 - b, 2, 4, hair, "H")
            eye(-3 + lk, -16 - b)
            eye(2 + lk, -16 - b)
            R(-4, -14 - b, 2, 1, blush, "B")
            R(2, -14 - b, 2, 1, blush, "B")
        elif dr == 2:
            R(-5, -19 - b, 3, 6, hair, "H")
            eye(2, -16 - b)
            R(2, -14 - b, 2, 1, blush, "B")
        else:
            R(2, -19 - b, 3, 6, hair, "H")
            eye(-3, -16 - b)
            R(-4, -14 - b, 2, 1, blush, "B")
        if pal.get("glasses"):
            gl = (60, 60, 80, 255)
            R(-4, -17 - b, 3, 3, gl, "G")
            R(1, -17 - b, 3, 3, gl, "G")
            if not blink:
                R(-3, -16 - b, 1, 1, hexc("#cfe8ff"), "G")
                R(2, -16 - b, 1, 1, hexc("#cfe8ff"), "G")
    if pal.get("hat") == "top":
        R(-6, -24 - b, 12, 2, hexc("#2a2c36"), "T")
        R(-4, -31 - b, 8, 7, hexc("#2a2c36"), "T")
        R(-4, -26 - b, 8, 1, hexc("#d4a93a"), "T")
    if pal.get("hat") == "band":
        R(-5, -21 - b, 10, 2, hexc("#d94a4a"), "T")
    # 가장자리 음영: 오른쪽·아래가 다른 재질이면 어둡게, 머리카락/모자는 위쪽 하이라이트
    base = [row[:] for row in im.p]
    for y in range(FH):
        for x in range(FW):
            c = base[y][x]
            if c is None:
                continue
            t = chr(tag.p[y][x][0]) if tag.p[y][x] else "x"
            if t in ("C", "L", "K", "H") and c[:3] != (60, 60, 80):
                right = tag.get(x + 1, y)
                down = tag.get(x, y + 1)
                rt = chr(right[0]) if right else None
                dt = chr(down[0]) if down else None
                if rt != t and rt in (None, "x", "K", "C", "L", "S", "H", "T", "E", "B", "G") and t in ("C", "L", "K"):
                    im.p[y][x] = drk(c, .16)
                if dt != t and dt is None and t in ("C", "L", "K"):
                    im.p[y][x] = drk(c, .12)
            if t == "H":
                up = tag.get(x, y - 1)
                if up is None:
                    im.p[y][x] = lit(c, .22)
            if t == "T" and tag.get(x, y - 1) is None:
                im.p[y][x] = lit(c, .25)
    im.outline(0.5)
    return im


PAL_PLAYER = ["#e86a6a", "#4a9ee0", "#6bc16b", "#f0b840", "#b17ae0"]


def char_sheet(pal):
    sheet = Img(FW * len(FR), FH * 4)
    for d in range(4):
        for i, fr in enumerate(FR):
            sheet.paste(character(d, fr, pal), i * FW, d * FH)
    return sheet


# ------------------------------------------------------------------ 실행
def main():
    manifest = {"files": {}, "rects": {}, "chars": {"fw": FW, "fh": FH, "ax": AX, "ay": AY, "frames": FR}}

    def emit(key, fname, atlas, rects):
        atlas.save(os.path.join(HERE, fname))
        manifest["files"][key] = fname
        manifest["rects"][key] = rects

    items = []
    for v in range(8):
        items.append(("grass%d" % v, tile_grass(v)))
    for v in range(4):
        items.append(("sand%d" % v, tile_sand(v)))
    for v in range(4):
        items.append(("snow%d" % v, tile_snow(v)))
    for v in range(3):
        items.append(("path%d" % v, tile_path(v, False)))
    for v in range(3):
        items.append(("pathC%d" % v, tile_path(v, True)))
    for v in range(2):
        items.append(("plaza%d" % v, tile_plaza(v)))
    for v in range(2):
        items.append(("deck%d" % v, tile_deck(v)))
    a, r = pack(items, 256)
    emit("tiles", "tiles.png", a, r)

    items = []
    for kind in ("sea", "river"):
        for v in range(4):
            for f in range(4):
                items.append(("%s_%d_%d" % (kind, v, f), tile_water(kind, v, f)))
    for f in range(4):
        items.append(("pond_%d" % f, tile_pond(f)))
    a, r = pack(items, 256)
    emit("water", "water.png", a, r)

    items = []
    items.append(("trunk", trunk()))
    for v in range(3):
        items.append(("canopy%d" % v, canopy_outlined(canopy(v))))
        items.append(("canopyF%d" % v, canopy_outlined(canopy_fruit(v))))
    items.append(("pine0", pine(False)))
    items.append(("pine1", pine(True)))
    for v in range(3):
        items.append(("rock%d" % v, rock(v)))
    for v in range(2):
        items.append(("bush%d" % v, bush(v)))
    for s in (-1, 0, 1):
        items.append(("tuft%d" % (s + 1), tuft(s)))
        items.append(("cane%d" % (s + 1), cane(s)))
        items.append(("reeds%d" % (s + 1), reeds(s)))
        items.append(("fern%d" % (s + 1), fern(s)))
        for col in PFL:
            items.append(("pf_%s_%d" % (col, s + 1), pflower(col, s)))
            items.append(("pfb_%s_%d" % (col, s + 1), pflower(col, s, True)))
    for v in range(3):
        items.append(("shell%d" % v, shell(v)))
    items += [("starfish", starfish()), ("driftwood", driftwood()), ("seaweed", seaweed()), ("clover", clover()),
              ("mush0", mushroom(0)), ("mush1", mushroom(1)), ("pebble0", pebbles(0)), ("pebble1", pebbles(1)),
              ("lily0", lilypad(0)), ("lily1", lilypad(1)), ("wrock", water_rock()), ("bed", flowerbed())]
    a, r = pack(items, 256)
    emit("objects", "objects.png", a, r)

    items = [(k, building(k)) for k in ("home", "kitchen", "workshop", "shop")]
    a, r = pack(items, 192)
    emit("buildings", "buildings.png", a, r)

    for i, c in enumerate(PAL_PLAYER):
        sheet = char_sheet({"skin": "#ffd9b8", "hair": "#7a4a2a", "top": c, "bottom": "#3d5a80"})
        manifest["files"]["player%d" % i] = "char_player%d.png" % i
        sheet.save(os.path.join(HERE, "char_player%d.png" % i))
    sheet = char_sheet({"skin": "#f6d5b5", "hair": "#d8d8e0", "top": "#3a5aa0", "bottom": "#3a3a48", "coat": "#ffffff", "glasses": 1, "hat": "top"})
    manifest["files"]["dalton"] = "char_dalton.png"
    sheet.save(os.path.join(HERE, "char_dalton.png"))
    sheet = char_sheet({"skin": "#f0c49a", "hair": "#4a3a2a", "top": "#d98a4a", "bottom": "#4a3a2a", "hat": "band"})
    manifest["files"]["keeper"] = "char_keeper.png"
    sheet.save(os.path.join(HERE, "char_keeper.png"))

    with open(os.path.join(HERE, "manifest.js"), "w", encoding="utf-8") as f:
        f.write("// make_sprites.py 가 생성한 파일입니다.\nwindow.SPR_MANIFEST=" + json.dumps(manifest, ensure_ascii=False) + ";\n")
    print("done:", sorted(manifest["files"].values()))


# ================================================================== 2차 개선(v2)
# 아래 정의는 위의 같은 이름 함수를 덮어쓴다. (타일·물·나무·캐릭터)
import sys


def vnoise(x, y, seed):
    """타일 경계와 무관한 연속 값 노이즈(0~1)."""
    def h(ix, iy):
        n = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xffffffff
        n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
        return ((n ^ (n >> 16)) & 0xffff) / 65535.0
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = h(ix, iy), h(ix + 1, iy)
    c, d = h(ix, iy + 1), h(ix + 1, iy + 1)
    return (a + (b - a) * fx) + ((c + (d - c) * fx) - (a + (b - a) * fx)) * fy


def tile_grass(v):
    rnd = random.Random(1000 + v)
    base, d1, l1, d2, l2 = [hexc(c) for c in ("#80d16a", "#74c660", "#93dc7e", "#62b65a", "#a8eb92")]
    im = Img(16, 16)
    im.rect(0, 0, 16, 16, base)
    for y in range(16):
        for x in range(16):
            if BAYER[y % 4][x % 4] < 2:
                im.set(x, y, d1)
    for _ in range(4):
        im.set(rnd.randrange(16), rnd.randrange(16), l1)
    for _ in range(3):
        im.set(rnd.randrange(16), rnd.randrange(16), d2)
    for _ in range(1 + v % 3):
        x, y = rnd.randrange(2, 12), rnd.randrange(3, 13)
        im.set(x, y + 1, d2)
        im.set(x + 1, y, d2)
        im.set(x + 2, y + 1, d2)
        im.set(x + 1, y + 1, l2)
    if v == 11:
        x, y = rnd.randrange(3, 12), rnd.randrange(3, 12)
        im.set(x, y, hexc("#ffffff"))
        im.set(x, y + 1, hexc("#5cb85c"))
    return im


WFR = 8


def tile_water(kind, v, f):
    pal = {"sea": ("#58bfe0", "#46a9cf", "#7ad2ec", "#b4eefa"),
           "river": ("#6fd0ea", "#58b8d6", "#90e2f4", "#c2f2fb")}[kind]
    base, dark, light, hl = [hexc(c) for c in pal]
    comps = [(1, 1, 1), (2, -1, -1), (1, 3, 1), (3, 2, -2), (2, 3, 1)]
    im = Img(16, 16)
    for y in range(16):
        for x in range(16):
            val = 0.0
            for i, (a, b, m) in enumerate(comps):
                val += math.sin(2 * math.pi * (a * x + b * y) / 16 + v * 1.9 + i * 2.3 + 2 * math.pi * m * f / WFR)
            val /= len(comps)
            c = base
            if val > .52:
                c = hl
            elif val > .30:
                c = light
            elif val < -.46:
                c = dark
            im.set(x, y, c)
    return im


FOL3 = [hexc(c) for c in ("#3a5f2a", "#4f7d34", "#6a9a40", "#88b852", "#a8d46c", "#c8ea8c")]


def blob(circles, size, pal, seed, clump):
    m = Img(*size)
    for cx, cy, r in circles:
        m.ell(cx, cy, r, r, (1, 1, 1, 255))
    im = shade_blob(m, pal, seed)
    clumps(im, pal, seed + 3, clump)
    return im


def add_fruit(im, seed, n=5):
    rnd = random.Random(seed)
    pts = [(x, y) for y in range(3, im.h - 3) for x in range(3, im.w - 3) if im.p[y][x]]
    for _ in range(n):
        px, py = rnd.choice(pts)
        im.set(px, py, hexc("#d93a4a"))
        im.set(px + 1, py, hexc("#ff6b6b"))
        im.set(px, py + 1, hexc("#a82838"))
        im.set(px + 1, py + 1, hexc("#d93a4a"))
    return im


def canopy_small(v, fruit=False):
    circles = [[(10, 9, 8), (5, 11, 5), (15, 11, 5)], [(10, 9, 7), (6, 11, 5), (15, 10, 6), (10, 5, 5)]][v % 2]
    im = blob(circles, (22, 20), FOL if v % 2 == 0 else FOL2, 300 + v, 4)
    if fruit:
        add_fruit(im, 500 + v, 4)
    im.outline(0.55)
    return im


def canopy_tall(v):
    circles = [(11, 13, 8), (11, 7, 7), (11, 19, 8), (7, 15, 5), (15, 16, 5)] if v % 2 == 0 else [(11, 14, 7), (11, 8, 6), (11, 21, 7), (8, 12, 5)]
    im = blob(circles, (24, 32), FOL2 if v % 2 == 0 else FOL, 350 + v, 7)
    im.outline(0.55)
    return im


def canopy_big(v, fruit=False):
    im = canopy(v)
    if fruit:
        add_fruit(im, 520 + v, 6)
    return im


def trunk_h(h):
    im = Img(12, h)
    br = [hexc(c) for c in ("#4a2f1f", "#6b4429", "#8a5a34", "#a8723f")]
    widths = [4] * (h - 6) + [5, 6, 6, 8, 8, 8]
    rnd = random.Random(5 + h)
    for y, w in enumerate(widths):
        x0 = 6 - w // 2
        for i in range(w):
            c = br[3] if i == 0 else br[2] if i < w - 2 else br[1] if i < w - 1 else br[0]
            if w <= 4 and i == w - 1:
                c = br[1]
            im.set(x0 + i, y, c)
    for _ in range(max(2, h // 4)):
        im.set(6 + rnd.randrange(-1, 2), rnd.randrange(0, h - 6), br[0])
    im.outline(0.5)
    return im


def pine_n(snow, tiers):
    H = 6 + tiers * 9
    im = Img(26, H)
    base = [hexc(c) for c in ("#1f5a3a", "#2b7b4e", "#3a9a62", "#58b97a")]
    cx = 13
    for i in range(tiers):
        y0 = 1 + i * 9
        for r in range(11):
            y = y0 + r
            if y >= H - 1:
                break
            hw = 1 + int(r * (0.62 + 0.12 * i))
            hw = min(hw, 12)
            for x in range(cx - hw, cx + hw + 1):
                t = (x - (cx - hw)) / max(1, 2 * hw)
                c = base[3] if t < .25 else base[2] if t < .55 else base[1] if t < .85 else base[0]
                if (x + y) % 5 == 0:
                    c = lit(c, .08)
                im.set(x, y, c)
            if snow and r < 3:
                for x in range(cx - hw, cx + hw + 1):
                    if (x + r) % 4 != 3:
                        im.set(x, y, hexc("#f2f8ff") if x < cx + hw - 1 else hexc("#cfe0f2"))
    im.outline(0.55)
    return im


def bush(v):
    m = Img(16, 13)
    for cx, cy, r in ((8, 8, 5), (4, 9, 4), (12, 9, 4), (8, 5, 4)):
        m.ell(cx, cy, r, r, (1, 1, 1, 255))
    pal = [FOL, FOL2, FOL3, FOL][v % 4]
    im = shade_blob(m, pal, 50 + v)
    clumps(im, pal, 60 + v, 4)
    if v % 4 == 1:
        for (x, y) in ((4, 7), (10, 6), (8, 9), (12, 9)):
            im.set(x, y, hexc("#ff6b8a"))
            im.set(x + 1, y, hexc("#ffa0b8"))
    if v % 4 == 3:
        for (x, y) in ((3, 7), (9, 5), (7, 9), (12, 8)):
            im.set(x, y, hexc("#ffffff"))
            im.set(x + 1, y, hexc("#fff0a0"))
    im.outline(0.55)
    return im


def tuft(s, shape=0):
    im = Img(12, 10)
    cols = [hexc("#4aa040"), hexc("#62b84c"), hexc("#7ccf5a"), hexc("#a0e47e")]
    blades = ((3, 5), (6, 8), (9, 6)) if shape == 0 else ((2, 4), (5, 7), (7, 5), (10, 6))
    for bx, h in blades:
        for r in range(h):
            dx = int(round(s * (r / h) ** 1.4 * 1.6))
            y = 9 - r
            c = cols[0] if r < 2 else cols[1] if r < h - 2 else cols[2] if r < h - 1 else cols[3]
            im.set(bx + dx, y, c)
            if r < 2:
                im.set(bx + dx + 1, y, cols[0])
    return im


def pflower(color, s, big=False, shape=0):
    c, hi, lo = [hexc(x) for x in PFL[color]]
    im = Img(10 if not big else 12, 12 if not big else 14)
    st = hexc("#3f9a3f")
    bx = 5 if not big else 6
    top = 3
    for r in range(8):
        dx = int(round(s * (r / 8) ** 1.4 * 1.4))
        im.set(bx + dx, im.h - 1 - r, st)
    hx = bx + int(round(s * 1.4))
    if shape == 0:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            im.set(hx + dx, top + dy, c)
        im.set(hx - 1, top - 1, hi)
        im.set(hx + 1, top + 1, lo)
    else:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if abs(dx) + abs(dy) < 3:
                    im.set(hx + dx, top + dy, c if (dx + dy) % 2 else hi)
        im.set(hx + 1, top + 1, lo)
    im.set(hx, top, hexc("#ffe27a"))
    im.set(bx + int(round(s * .5)) - 1, im.h - 4, hexc("#5cb85c"))
    return im


# ------------------------------------------------------------------ 캐릭터 v2
FR = ["idle0", "idle1", "w0", "w1", "w2", "w3", "blink", "reach", "adjust", "wave", "wave2", "count", "count2", "lookL", "lookR", "talk0", "talk1"]
FW, FH, AX, AY = 24, 44, 12, 43
FEET = AY - 1


def mirror(im):
    out = Img(im.w, im.h)
    for y in range(im.h):
        for x in range(im.w):
            p = im.p[y][x]
            if p is not None:
                nx = 2 * AX - x
                if 0 <= nx < im.w:
                    out.p[y][nx] = p
    return out


# ------------------------------------------------------------------ 실내 타일 (바닥·벽·창·출입구)
ROOMS = {
    "home": dict(floor=("#dba868", "#c99552", "#e8bd80", "#a87a40"), wallA="#f6e7c6", wallB="#ecd9b2", cap="#fff3d6", wain="#c28a52", wainD="#9a6a3c", kind="wood", curtain="#e8909a"),
    "kitchen": dict(floor=("#f3e8d2", "#e6d5b4", "#fbf4e4", "#cdbb98"), wallA="#fbf0c8", wallB="#f2e2a8", cap="#fffbe6", wain="#f6f6f0", wainD="#c8cec8", kind="tile", curtain="#f0b060"),
    "workshop": dict(floor=("#a98c68", "#97795a", "#bba078", "#6f5640"), wallA="#cdd6e2", wallB="#bcc7d6", cap="#e6edf5", wain="#6b5a48", wainD="#4a3c30", kind="dark", curtain="#7a96c0"),
    "shop": dict(floor=("#e8c894", "#d8b480", "#f2dcae", "#b8935c"), wallA="#f4dfcd", wallB="#ead0ba", cap="#fff1e4", wain="#6aa070", wainD="#4a8052", kind="vert", curtain="#6aa070"),
}


def _seed(room, v, salt=0):
    return zlib.crc32(room.encode()) + v * 977 + salt


def floor_tile(room, v):
    cfg = ROOMS[room]
    base, dk, lt, gap = [hexc(c) for c in cfg["floor"]]
    rnd = random.Random(_seed(room, v))
    im = Img(16, 16)
    kind = cfg["kind"]
    if kind in ("wood", "dark"):
        for r in range(4):
            y0 = r * 4
            tone = [base, lit(base, .05), drk(base, .05), lit(base, .02)][(v + r * 2 + rnd.randrange(2)) % 4]
            im.rect(0, y0, 16, 4, tone)
            im.rect(0, y0, 16, 1, lit(tone, .10))
            im.rect(0, y0 + 3, 16, 1, gap if kind == "wood" else drk(base, .38))
            jx = rnd.randrange(2, 14)
            im.rect(jx, y0, 1, 3, drk(tone, .22))
            im.set(jx + 1, y0, lit(tone, .10))
            for _ in range(1 + (v + r) % 2):
                gx, gy = rnd.randrange(0, 11), y0 + 1 + rnd.randrange(2)
                im.rect(gx, gy, rnd.randrange(3, 6), 1, drk(tone, .07) if rnd.random() < .6 else lit(tone, .06))
        if v % 6 == 2:
            kx, ky = rnd.randrange(3, 12), rnd.randrange(1, 12)
            im.rect(kx, ky, 2, 2, drk(base, .22))
            im.set(kx, ky, drk(base, .35))
        if kind == "dark" and v == 5:
            for y in range(16):
                for x in range(16):
                    if ((x - 8) / 5.5) ** 2 + ((y - 8) / 3.5) ** 2 <= 1 and im.p[y][x]:
                        im.set(x, y, drk(im.p[y][x], .16))
    elif kind == "tile":
        for y in range(16):
            for x in range(16):
                c = base if ((x // 8) + (y // 8)) % 2 == 0 else dk
                if x % 8 == 7 or y % 8 == 7:
                    c = gap
                elif x % 8 == 0 or y % 8 == 0:
                    c = lit(c, .3) if (x % 8 == 0 and y % 8 == 0) else lit(c, .08)
                im.set(x, y, c)
        for _ in range(3 + v % 3):
            im.set(rnd.randrange(16), rnd.randrange(16), drk(base, .12))
    else:
        for b in range(2):
            x0 = b * 8
            tone = [base, lit(base, .05), drk(base, .04)][(v + b * 2 + rnd.randrange(2)) % 3]
            im.rect(x0, 0, 8, 16, tone)
            im.rect(x0, 0, 1, 16, lit(tone, .10))
            im.rect(x0 + 7, 0, 1, 16, gap)
            jy = rnd.randrange(3, 13)
            im.rect(x0, jy, 7, 1, gap)
            im.rect(x0, jy + 1, 7, 1, lit(tone, .10))
            for _ in range(2):
                gx, gy = x0 + 2 + rnd.randrange(4), rnd.randrange(0, 10)
                im.rect(gx, gy, 1, rnd.randrange(3, 6), drk(tone, .07))
    return im


def wall_up(room, v):
    cfg = ROOMS[room]
    A, B, cap = hexc(cfg["wallA"]), hexc(cfg["wallB"]), hexc(cfg["cap"])
    im = Img(16, 16)
    im.rect(0, 0, 16, 3, cap)
    im.rect(0, 2, 16, 1, drk(cap, .14))
    im.rect(0, 3, 16, 1, drk(A, .48))
    im.rect(0, 4, 16, 12, A)
    im.rect(0, 4, 16, 2, drk(A, .07))
    if room in ("home", "shop"):
        for x in range(0, 16, 4):
            im.rect(x, 6, 1, 10, B)
        if v:
            im.set(6, 10, drk(A, .16))
            im.set(7, 11, drk(A, .16))
            im.set(5, 11, drk(A, .16))
    elif room == "kitchen":
        for y in range(6, 16):
            for x in range(16):
                if BAYER[y % 4][x % 4] < 2:
                    im.set(x, y, B)
        if v:
            im.set(10, 9, hexc("#e8b860"))
    else:
        for x in (7, 15):
            im.rect(x, 6, 1, 10, B)
        im.rect(0, 11, 16, 1, B)
        if v:
            im.set(3, 8, drk(A, .3))
            im.set(12, 13, drk(A, .3))
    return im


def wall_lo(room, v):
    cfg = ROOMS[room]
    A, B, wain, wainD = hexc(cfg["wallA"]), hexc(cfg["wallB"]), hexc(cfg["wain"]), hexc(cfg["wainD"])
    im = Img(16, 16)
    im.rect(0, 0, 16, 8, A)
    if room in ("home", "shop"):
        for x in range(0, 16, 4):
            im.rect(x, 0, 1, 8, B)
    elif room == "kitchen":
        for y in range(0, 8):
            for x in range(16):
                if BAYER[y % 4][x % 4] < 2:
                    im.set(x, y, B)
    else:
        for x in (7, 15):
            im.rect(x, 0, 1, 8, B)
    im.rect(0, 8, 16, 1, lit(wain, .35))
    im.rect(0, 9, 16, 4, wain)
    if room == "kitchen":
        for r in range(2):
            y = 9 + r * 2
            im.rect(0, y + 1, 16, 1, wainD)
            off = 4 if r else 0
            for x in range(off, 16, 8):
                im.rect(x, y, 1, 2, wainD)
        im.rect(0, 9, 16, 1, lit(wain, .1))
    else:
        for x in range(0, 16, 8):
            im.rect(x, 9, 1, 4, wainD)
            im.rect(x + 1, 9, 1, 4, lit(wain, .12))
        im.rect(0, 12, 16, 1, wainD)
        if room == "workshop":
            for x in (3, 11):
                im.set(x, 10, hexc("#b8c0cc"))
    im.rect(0, 13, 16, 3, drk(wain, .22))
    im.rect(0, 13, 16, 1, lit(drk(wain, .22), .2))
    im.rect(0, 15, 16, 1, drk(wain, .55))
    return im


def side_wall(room, part):
    cfg = ROOMS[room]
    cap, A = hexc(cfg["cap"]), hexc(cfg["wallA"])
    face = drk(A, .22)
    h = {"top": 16, "mid": 16, "bot": 21}[part]
    im = Img(8, h)
    im.rect(0, 0, 3, h, cap)
    im.rect(2, 0, 1, h, drk(cap, .14))
    im.rect(3, 0, 1, h, drk(A, .48))
    im.rect(4, 0, 4, 16 if part != "bot" else 16, face)
    im.rect(4, 0, 1, 16, drk(face, .1))
    if part == "top":
        im.rect(0, 0, 8, 3, cap)
        im.rect(0, 2, 8, 1, drk(cap, .14))
        im.rect(3, 3, 5, 1, drk(A, .48))
    if part == "bot":
        im.rect(0, 16, 8, 5, cap)
        im.rect(0, 20, 8, 1, drk(A, .48))
        im.rect(0, 19, 8, 1, drk(cap, .14))
    return im


def bot_cap(room):
    cfg = ROOMS[room]
    cap, A = hexc(cfg["cap"]), hexc(cfg["wallA"])
    im = Img(16, 5)
    im.rect(0, 0, 16, 4, cap)
    im.rect(0, 3, 16, 1, drk(cap, .14))
    im.rect(0, 4, 16, 1, drk(A, .48))
    return im


def door_post(side):
    im = Img(4, 10)
    c = [hexc(x) for x in ("#6a4424", "#8a5a34", "#a8743f")]
    im.rect(0, 0, 4, 10, c[1])
    im.rect(0 if side == "L" else 3, 0, 1, 10, c[2])
    im.rect(3 if side == "L" else 0, 0, 1, 10, c[0])
    im.outline(0.5)
    return im


def threshold():
    im = Img(16, 5)
    im.rect(0, 0, 16, 4, hexc("#d9cdb2"))
    im.rect(0, 0, 16, 1, hexc("#efe6d0"))
    im.rect(0, 3, 16, 1, hexc("#b8a98a"))
    im.rect(0, 4, 16, 1, hexc("#6a5a46"))
    return im


def mat():
    im = Img(14, 12)
    im.rect(0, 0, 14, 12, hexc("#b8423f"))
    im.rect(1, 1, 12, 10, hexc("#d65a52"))
    im.rect(2, 2, 10, 8, hexc("#b8423f"))
    im.rect(3, 3, 8, 6, hexc("#e8806a"))
    im.rect(4, 4, 6, 4, hexc("#d65a52"))
    for x in range(1, 13, 2):
        im.set(x, 11, hexc("#f0c0a8"))
    im.outline(0.45)
    return im


def window(room, night):
    cfg = ROOMS[room]
    cur = hexc(cfg["curtain"])
    im = Img(28, 24)
    fr, frd = hexc("#f4ead6"), hexc("#b8a888")
    im.rect(2, 0, 24, 20, frd)
    im.rect(3, 1, 22, 18, fr)
    if night:
        top, bot = hexc("#1e2d66"), hexc("#34478a")
    else:
        top, bot = hexc("#8fd2f0"), hexc("#d4f0fb")
    for y in range(4, 18):
        t = (y - 4) / 13
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,)
        im.rect(5, y, 18, 1, c)
    if night:
        for x, y in ((8, 6), (17, 8), (12, 12), (20, 5)):
            im.set(x, y, hexc("#fff6c8"))
        im.rect(18, 6, 3, 3, hexc("#f4f0d0"))
        im.set(19, 6, hexc("#34478a"))
    else:
        im.rect(8, 7, 6, 2, hexc("#ffffff"))
        im.rect(10, 6, 4, 1, hexc("#ffffff"))
        im.rect(16, 10, 5, 2, hexc("#f4fbff"))
    im.rect(13, 4, 2, 14, fr)
    im.rect(5, 10, 18, 2, fr)
    im.rect(0, 19, 28, 3, frd)
    im.rect(0, 19, 28, 1, hexc("#e8dcc0"))
    im.rect(0, 22, 28, 1, drk(frd, .3))
    im.rect(3, 1, 4, 18, cur)
    im.rect(21, 1, 4, 18, cur)
    im.rect(3, 1, 1, 18, lit(cur, .25))
    im.rect(21, 1, 1, 18, lit(cur, .25))
    for x in (5, 23):
        im.rect(x, 3, 1, 15, drk(cur, .2))
    im.outline(0.5)
    return im


def squash(im, tag, remove):
    """발 아래 행은 그대로 두고 지정한 행을 지워 캐릭터 키를 줄인다(건물 문과의 비율 조정)."""
    out_i, out_t = Img(im.w, im.h), Img(tag.w, tag.h)
    o = im.h - 1
    for r in range(im.h - 1, -1, -1):
        if r in remove:
            continue
        out_i.p[o] = im.p[r][:]
        out_t.p[o] = tag.p[r][:]
        o -= 1
    return out_i, out_t


def character(dr, frame, pal):
    if dr == 2:
        return mirror(character(1, frame, pal))
    im, tag = Img(FW, FH), Img(FW, FH)
    skin, hair, top, bottom = [hexc(pal[k]) for k in ("skin", "hair", "top", "bottom")]
    coat = hexc(pal["coat"]) if pal.get("coat") else None
    arm = coat or top
    sw = b = 0
    pose = ""
    blink = talk = False
    lk = 0
    if frame == "idle1":
        b = 1
    elif frame in ("w0", "w1", "w2", "w3"):
        k = int(frame[1])
        sw, b = [0, 1, 0, -1][k], k % 2
    elif frame == "blink":
        blink = True
    elif frame in ("reach", "adjust", "wave", "wave2", "count", "count2"):
        pose = frame
    elif frame == "lookL":
        lk = -1
    elif frame == "lookR":
        lk = 1
    elif frame in ("talk0", "talk1"):
        talk = True
        b = int(frame[-1])

    def R(lx, ly, w, h, c, t="x"):
        im.rect(AX + lx, FEET + ly, w, h, c)
        tag.rect(AX + lx, FEET + ly, w, h, (ord(t), 0, 0, 255))

    shoe = hexc("#4a3326")
    belt = drk(bottom, .25)
    eyec, blushc, mouthc = hexc("#2a1c14"), hexc("#ff9aa2"), hexc("#c8665a")
    frame_c = hexc("#4a3628")
    lens_c = hexc("#e4f1fb")
    is_d = bool(pal.get("glasses"))
    long_coat = coat is not None

    def eye(ex, ey):
        if blink:
            R(ex, ey + 2, 2, 1, eyec, "E")
        else:
            R(ex, ey, 2, 3, eyec, "E")
            R(ex, ey, 1, 1, hexc("#ffffff"), "E")

    def hat():
        h = pal.get("hat")
        if h == "top":
            hc = hexc("#2a2c36")
            R(-9, -30 - b, 18, 2, hc, "T")
            R(-5, -37 - b, 10, 7, hc, "T")
            R(-5, -32 - b, 10, 1, hexc("#d4a93a"), "T")
            R(-5, -37 - b, 1, 5, lit(hc, .18), "T")
        elif h == "band":
            R(-8, -27 - b, 16, 2, hexc("#d94a4a"), "T")
            R(-8, -25 - b, 2, 3, hexc("#d94a4a"), "T")

    def goggles(side=False):
        if not pal.get("goggles"):
            return
        R(-8, -27 - b, 16, 1, hexc("#6a4a2a"), "T")
        rim, glass = hexc("#c89a3a"), hexc("#bfe8f5")
        xs = (-6, 2) if not side else (-6, -1)
        for x0 in xs[: (2 if not side else 1)]:
            R(x0, -30 - b, 5, 4, rim, "T")
            R(x0 + 1, -29 - b, 3, 2, glass, "T")
            R(x0 + 1, -29 - b, 1, 1, hexc("#ffffff"), "T")

    def legs_fb():
        ldy = -1 if sw > 0 else 0
        rdy = -1 if sw < 0 else 0
        R(-4, -6 + ldy, 4, 4, bottom, "L")
        R(-4, -3 + ldy, 4, 1, lit(bottom, .15), "L")
        R(-5, -2 + ldy, 5, 3, shoe, "S")
        R(1, -6 + rdy, 4, 4, bottom, "L")
        R(1, -3 + rdy, 4, 1, lit(bottom, .15), "L")
        R(1, -2 + rdy, 5, 3, shoe, "S")

    def torso_fb(back=False):
        R(-5, -16 - b, 10, 10 + b, top, "C")
        R(-5, -7, 10, 1, belt, "C")
        if long_coat:
            R(-6, -16 - b, 12, 13 + b, coat, "C")
            R(-6, -4, 12, 1, drk(coat, .2), "C")
            if back:
                R(0, -14 - b, 1, 10 + b, drk(coat, .14), "C")
            else:
                R(-1, -16 - b, 2, 11 + b, hexc("#3a5aa0"), "C")
                R(0, -14 - b, 1, 1, hexc("#d4a93a"), "C")
                R(0, -11 - b, 1, 1, hexc("#d4a93a"), "C")
        elif not back:
            R(-2, -16 - b, 4, 1, lit(top, .5), "C")
            R(-1, -15 - b, 2, 1, skin, "K")
            R(2, -12 - b, 3, 3, drk(top, .1), "C")
            R(2, -12 - b, 3, 1, lit(top, .3), "C")
            R(0, -13 - b, 1, 1, lit(top, .4), "C")
            R(0, -10 - b, 1, 1, lit(top, .4), "C")
            if pal.get("apron"):
                R(-4, -13 - b, 8, 7 + b, hexc(pal["apron"]), "C")
                R(-4, -14 - b, 1, 1, hexc(pal["apron"]), "C")
                R(3, -14 - b, 1, 1, hexc(pal["apron"]), "C")
        else:
            R(-3, -16 - b, 6, 1, drk(top, .12), "C")

    def arms_fb():
        ady_l, ady_r = sw, -sw
        R(-7, -15 - b + ady_l, 2, 6, arm, "C")
        R(-7, -9 - b + ady_l, 2, 2, skin, "K")
        if pose == "adjust":
            R(5, -22 - b, 2, 9, arm, "C")
            R(4, -24 - b, 3, 2, skin, "K")
        elif pose in ("wave", "wave2"):
            w = 1 if pose == "wave2" else 0
            R(6, -27 - b - w, 2, 11, arm, "C")
            R(6, -29 - b - w, 2, 2, skin, "K")
        elif pose == "reach":
            R(5, -18 - b, 2, 7, arm, "C")
            R(5, -20 - b, 2, 2, skin, "K")
        elif pose in ("count", "count2"):
            o = 1 if pose == "count2" else 0
            R(5, -13 - b + o, 2, 5, arm, "C")
            R(5, -9 - b + o, 2, 2, skin, "K")
        else:
            R(5, -15 - b + ady_r, 2, 6, arm, "C")
            R(5, -9 - b + ady_r, 2, 2, skin, "K")

    def head_fb(back=False):
        for r in range(12):
            y = -28 + r
            if r == 0:
                x0, x1 = -5, 4
            elif r in (1, 11):
                x0, x1 = -6, 5
            else:
                x0, x1 = -7, 6
            R(x0, y - b, x1 - x0 + 1, 1, skin, "K")
        if back:
            for r in range(12):
                y = -29 + r
                x0, x1 = (-5, 4) if r == 0 else (-8, 7)
                if r == 11:
                    x0, x1 = -6, 5
                R(x0, y - b, x1 - x0 + 1, 1, hair, "H")
            R(-8, -26 - b, 2, 6, hair, "H")
            R(6, -26 - b, 2, 6, hair, "H")
            return
        R(-5, -29 - b, 10, 1, hair, "H")
        R(-7, -28 - b, 14, 1, hair, "H")
        R(-8, -27 - b, 16, 2, hair, "H")
        if is_d:
            R(-8, -25 - b, 2, 7, hair, "H")
            R(6, -25 - b, 2, 7, hair, "H")
        else:
            R(-7, -25 - b, 14, 1, hair, "H")
            R(-7, -24 - b, 4, 1, hair, "H")
            R(1, -24 - b, 6, 1, hair, "H")
            R(-8, -25 - b, 2, 6, hair, "H")
            R(6, -25 - b, 2, 6, hair, "H")
        if is_d:
            for x0 in (-5, 1):
                R(x0, -24 - b, 4, 5, frame_c, "G")
                R(x0 + 1, -23 - b, 2, 3, lens_c, "G")
            R(-1, -22 - b, 2, 1, frame_c, "G")
            eye(-4 + lk, -23 - b)
            eye(2 + lk, -23 - b)
            R(-3, -20 - b, 6, 2, hexc("#e8e8f0"), "M")
        else:
            eye(-4 + lk, -23 - b)
            eye(2 + lk, -23 - b)
            R(-6, -20 - b, 2, 1, blushc, "B")
            R(4, -20 - b, 2, 1, blushc, "B")
        if talk:
            R(-1, -18 - b, 2, 2, hexc("#7a2a2a"), "E")
        elif not is_d:
            R(-1, -18 - b, 2, 1, mouthc, "E")

    def legs_side():
        a = -2 * sw
        R(0 - a, -6, 3, 4, drk(bottom, .15), "L")
        R(0 - a, -2, 4, 3, drk(shoe, .15), "S")
        la = -1 if sw != 0 else 0
        R(-3 + a, -6 + la, 3, 4, bottom, "L")
        R(-4 + a, -2 + la, 5, 3, shoe, "S")

    def torso_side():
        R(-4, -16 - b, 8, 10 + b, top, "C")
        R(-4, -7, 8, 1, belt, "C")
        if long_coat:
            R(-5, -16 - b, 10, 13 + b, coat, "C")
            R(-5, -4, 10, 1, drk(coat, .2), "C")
            R(-5, -16 - b, 1, 13 + b, hexc("#3a5aa0"), "C")
        else:
            R(-4, -16 - b, 2, 1, lit(top, .5), "C")
            R(-1, -12 - b, 3, 3, drk(top, .1), "C")
            if pal.get("apron"):
                R(-5, -13 - b, 2, 7 + b, hexc(pal["apron"]), "C")

    def arms_side():
        ax = -sw * 2
        R(-1 - ax, -15 - b, 2, 6, drk(arm, .22), "C")
        R(-1 - ax, -9 - b, 2, 2, drk(skin, .12), "K")
        if pose == "adjust":
            R(-3, -22 - b, 2, 9, arm, "C")
            R(-5, -24 - b, 3, 2, skin, "K")
        elif pose in ("wave", "wave2"):
            w = 1 if pose == "wave2" else 0
            R(-2, -27 - b - w, 2, 11, arm, "C")
            R(-2, -29 - b - w, 2, 2, skin, "K")
        elif pose == "reach":
            R(-4, -15 - b, 5, 2, arm, "C")
            R(-6, -15 - b, 2, 2, skin, "K")
        elif pose in ("count", "count2"):
            o = 1 if pose == "count2" else 0
            R(-4, -12 - b + o, 5, 2, arm, "C")
            R(-6, -12 - b + o, 2, 2, skin, "K")
        else:
            R(-1 + ax, -15 - b, 2, 6, arm, "C")
            R(-1 + ax, -9 - b, 2, 2, skin, "K")

    def head_side():
        for r in range(12):
            y = -28 + r
            if r == 0:
                x0, x1 = -4, 3
            elif r in (1, 11):
                x0, x1 = -5, 4
            else:
                x0, x1 = -6, 5
            R(x0, y - b, x1 - x0 + 1, 1, skin, "K")
        R(-5, -29 - b, 10, 1, hair, "H")
        R(-6, -28 - b, 12, 1, hair, "H")
        R(-7, -27 - b, 14, 2, hair, "H")
        R(0, -25 - b, 7, 8, hair, "H")
        if is_d:
            R(0, -25 - b, 7, 8, hair, "H")
        else:
            R(-6, -25 - b, 4, 1, hair, "H")
            R(-6, -24 - b, 2, 1, hair, "H")
        R(-7, -20 - b, 1, 2, drk(skin, .06), "K")
        R(0, -22 - b, 2, 3, drk(skin, .12), "K")
        if is_d:
            R(-5, -24 - b, 4, 5, frame_c, "G")
            R(-4, -23 - b, 2, 3, lens_c, "G")
            R(-1, -22 - b, 3, 1, frame_c, "G")
            R(-6, -20 - b, 3, 2, hexc("#e8e8f0"), "M")
        R(-4, -23 - b, 2, 3, eyec, "E") if not blink else R(-4, -21 - b, 2, 1, eyec, "E")
        if not blink:
            R(-4, -23 - b, 1, 1, hexc("#ffffff"), "E")
        if not is_d:
            R(-5, -20 - b, 2, 1, blushc, "B")
        if talk:
            R(-5, -18 - b, 2, 2, hexc("#7a2a2a"), "E")
        elif not is_d:
            R(-5, -18 - b, 2, 1, mouthc, "E")

    if dr == 1:
        arms_far = True
        legs_side()
        torso_side()
        arms_side()
        head_side()
        hat()
        goggles(side=True)
    else:
        back = dr == 3
        legs_fb()
        torso_fb(back)
        arms_fb()
        head_fb(back)
        hat()
        goggles()
    im, tag = squash(im, tag, [FEET - 5, FEET - 4, FEET - 11])
    base = [row[:] for row in im.p]
    for y in range(FH):
        for x in range(FW):
            c = base[y][x]
            if c is None:
                continue
            t = chr(tag.p[y][x][0]) if tag.p[y][x] else "x"
            if t in ("C", "L", "K", "H", "T"):
                right, down = tag.get(x + 1, y), tag.get(x, y + 1)
                rt = chr(right[0]) if right else None
                dt = chr(down[0]) if down else None
                if t in ("C", "L", "K") and rt != t:
                    im.p[y][x] = drk(c, .15)
                elif t in ("C", "L", "K") and dt is None:
                    im.p[y][x] = drk(c, .10)
                up, left = tag.get(x, y - 1), tag.get(x - 1, y)
                if t in ("H", "T") and up is None:
                    im.p[y][x] = lit(c, .22)
                elif t in ("C", "K") and (up is None or left is None) and t != "K":
                    im.p[y][x] = lit(c, .10)
    im.outline(0.5)
    return im


def char_sheet(pal):
    sheet = Img(FW * len(FR), FH * 4)
    for d in range(4):
        for i, fr in enumerate(FR):
            sheet.paste(character(d, fr, pal), i * FW, d * FH)
    return sheet


PAL_PLAYER = ["#e86a6a", "#4a9ee0", "#6bc16b", "#f0b840", "#b17ae0"]


def main():
    manifest = {"files": {}, "rects": {}, "chars": {"fw": FW, "fh": FH, "ax": AX, "ay": AY, "frames": FR}}

    def emit(key, fname, atlas, rects):
        atlas.save(os.path.join(HERE, fname))
        manifest["files"][key] = fname
        manifest["rects"][key] = rects

    items = []
    for v in range(12):
        items.append(("grass%d" % v, tile_grass(v)))
    for v in range(4):
        items.append(("sand%d" % v, tile_sand(v)))
    for v in range(4):
        items.append(("snow%d" % v, tile_snow(v)))
    for v in range(3):
        items.append(("path%d" % v, tile_path(v, False)))
    for v in range(3):
        items.append(("pathC%d" % v, tile_path(v, True)))
    for v in range(2):
        items.append(("plaza%d" % v, tile_plaza(v)))
    for v in range(2):
        items.append(("deck%d" % v, tile_deck(v)))
    a, r = pack(items, 256)
    emit("tiles", "tiles.png", a, r)

    items = []
    for kind in ("sea", "river"):
        for v in range(4):
            for f in range(WFR):
                items.append(("%s_%d_%d" % (kind, v, f), tile_water(kind, v, f)))
    for f in range(4):
        items.append(("pond_%d" % f, tile_pond(f)))
    a, r = pack(items, 256)
    emit("water", "water.png", a, r)

    items = [("trunk", trunk_h(16)), ("trunkS", trunk_h(12))]
    for v in range(3):
        items.append(("canopy%d" % v, canopy_outlined(canopy(v))))
        items.append(("canopyF%d" % v, canopy_outlined(canopy_big(v, True))))
    for v in range(2):
        items.append(("canopyS%d" % v, canopy_small(v)))
        items.append(("canopyFS%d" % v, canopy_small(v, True)))
        items.append(("canopyT%d" % v, canopy_tall(v)))
    items.append(("pine0", pine_n(False, 3)))
    items.append(("pine1", pine_n(True, 3)))
    items.append(("pineS0", pine_n(False, 2)))
    items.append(("pineS1", pine_n(True, 2)))
    for v in range(3):
        items.append(("rock%d" % v, rock(v)))
    for v in range(4):
        items.append(("bush%d" % v, bush(v)))
    for s in (-1, 0, 1):
        for shp in (0, 1):
            items.append(("tuft%d_%d" % (shp, s + 1), tuft(s, shp)))
        items.append(("cane%d" % (s + 1), cane(s)))
        items.append(("reeds%d" % (s + 1), reeds(s)))
        items.append(("fern%d" % (s + 1), fern(s)))
        for col in PFL:
            for shp in (0, 1):
                items.append(("pf%d_%s_%d" % (shp, col, s + 1), pflower(col, s, False, shp)))
            items.append(("pfb_%s_%d" % (col, s + 1), pflower(col, s, True)))
    for v in range(3):
        items.append(("shell%d" % v, shell(v)))
    items += [("starfish", starfish()), ("driftwood", driftwood()), ("seaweed", seaweed()), ("clover", clover()),
              ("mush0", mushroom(0)), ("mush1", mushroom(1)), ("pebble0", pebbles(0)), ("pebble1", pebbles(1)),
              ("lily0", lilypad(0)), ("lily1", lilypad(1)), ("wrock", water_rock()), ("bed", flowerbed())]
    a, r = pack(items, 256)
    emit("objects", "objects.png", a, r)

    items = [(k, building(k)) for k in ("home", "kitchen", "workshop", "shop")]
    a, r = pack(items, 192)
    emit("buildings", "buildings.png", a, r)

    items = []
    for room in ROOMS:
        for v in range(6):
            items.append(("floor_%s_%d" % (room, v), floor_tile(room, v)))
        for v in range(2):
            items.append(("wallUp_%s_%d" % (room, v), wall_up(room, v)))
            items.append(("wallLo_%s_%d" % (room, v), wall_lo(room, v)))
        for part in ("top", "mid", "bot"):
            items.append(("side_%s_%s" % (room, part), side_wall(room, part)))
        items.append(("botCap_%s" % room, bot_cap(room)))
        items.append(("win_day_%s" % room, window(room, False)))
        items.append(("win_night_%s" % room, window(room, True)))
    items += [("doorL", door_post("L")), ("doorR", door_post("R")), ("threshold", threshold()), ("mat", mat())]
    a, r = pack(items, 256)
    emit("interior", "interior.png", a, r)

    pal_p = {"skin": "#ffd9b8", "hair": "#7a4a2a", "bottom": "#3d5a80", "goggles": 1}
    sheets = {}
    for i, c in enumerate(PAL_PLAYER):
        sheets["player%d" % i] = char_sheet(dict(pal_p, top=c))
    sheets["dalton"] = char_sheet({"skin": "#f6d5b5", "hair": "#e4e4ee", "top": "#e8eef6", "bottom": "#3a3a48", "coat": "#f7f7fb", "glasses": 1, "hat": "top"})
    sheets["keeper"] = char_sheet({"skin": "#f0c49a", "hair": "#4a3a2a", "top": "#d98a4a", "bottom": "#5a4a3a", "hat": "band", "apron": "#8a5a34"})
    for k, sh in sheets.items():
        fname = "char_%s.png" % k
        manifest["files"][k] = fname
        sh.save(os.path.join(HERE, fname))
    if "--preview" in sys.argv:
        pv = Img(FW * 7 * 1, FH * 4)
        pv = Img(FW * len(FR), FH * 4 * 2)
        pv.paste(sheets["dalton"], 0, 0)
        pv.paste(sheets["player0"], 0, FH * 4)
        up = Img(pv.w * 4, pv.h * 4)
        for y in range(pv.h):
            for x in range(pv.w):
                p = pv.p[y][x]
                if p:
                    for dy in range(4):
                        for dx in range(4):
                            up.p[y * 4 + dy][x * 4 + dx] = p
        up.save(sys.argv[sys.argv.index("--preview") + 1])

    with open(os.path.join(HERE, "manifest.js"), "w", encoding="utf-8") as f:
        f.write("// make_sprites.py 가 생성한 파일입니다.\nwindow.SPR_MANIFEST=" + json.dumps(manifest, ensure_ascii=False) + ";\n")
    print("done:", sorted(manifest["files"].values()))


if __name__ == "__main__":
    main()
