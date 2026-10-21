"""Kaotic Production logo set (pure SVG paths, no font needed at runtime).

Emblem: gold rim, golden starburst of sharp rays, a silver blade arc and a
faceted steel-blue "K". Wordmark: hand-built serif capitals "KAOTIC" (flat
silver tones, gold edge) + "PRODUCTION" in spaced Nunito caps (OFL, outlined).
Favicon: simplified K + rays that still reads at 16 px.

    python tools/make_brand.py        (needs fonttools)
Writes assets/brand/*.svg and /favicon.svg. PNG/ICO exports: tools/shoot.py brand
"""
import math
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = r"E:\ÇÖP TOPLAMA OYUNU\native3d\assets\fonts\Nunito.ttf"
OUT = os.path.join(ROOT, "assets", "brand")

GOLD = "#D9A93E"
GOLD_LT = "#F6D77C"
GOLD_DK = "#9C6E1C"
NAVY = "#131A27"
NAVY_DK = "#0C111B"
STEEL = "#4F7FAA"
STEEL_LT = "#9CC1E0"
STEEL_DK = "#2B4B6C"
SILVER_LT = "#F1F3F7"
SILVER = "#C3CAD5"


def poly(pts, fill):
    return f'<path fill="{fill}" d="M' + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + 'Z"/>'


# ------------------------------------------------------------------ emblem
def rays(cx, cy, spec, light=GOLD_LT, dark=GOLD):
    """spec: list of (angle_deg, length, half_width). Two-tone rays (bevel)."""
    out = []
    for ang, length, hw in spec:
        a = math.radians(ang)
        tip = (cx + length * math.cos(a), cy + length * math.sin(a))
        n = (-math.sin(a), math.cos(a))
        b1 = (cx + hw * n[0], cy + hw * n[1])
        b2 = (cx - hw * n[0], cy - hw * n[1])
        out.append(poly([(cx, cy), b1, tip], dark))
        out.append(poly([(cx, cy), tip, b2], light))
    return "".join(out)


RAY_SPEC = [  # angle (0 = right, -90 = up), length, half width at base
    (-90, 205, 36), (-56, 215, 32), (-124, 215, 32), (-27, 205, 28), (-153, 205, 28),
    (-4, 185, 22), (-176, 185, 22),
]
OUT_RAYS = [(-90, 262, 15), (-56, 262, 12), (-124, 262, 12)]
RCX, RCY = 262, 214


def k_shape(x0, y0, h, tones=(STEEL_LT, STEEL, STEEL_DK), edge=GOLD, edge_w=4.0):
    """Bold faceted K. Origin top-left of the cap box, height h (width ~0.94 h)."""
    s = h / 100.0
    def P(pts):
        return [(x0 + x * s, y0 + y * s) for x, y in pts]
    lt, md, dk = tones
    parts = [
        poly(P([(0, 0), (14, 0), (14, 100), (0, 100)]), lt),            # stem, light facet
        poly(P([(14, 0), (28, 0), (28, 100), (14, 100)]), md),          # stem, mid facet
        poly(P([(28, 46), (66, 0), (90, 0), (40, 58)]), lt),            # upper arm
        poly(P([(40, 58), (90, 0), (90, 6), (46, 62)]), dk),
        poly(P([(36, 52), (54, 40), (94, 100), (70, 100)]), md),        # lower leg
        poly(P([(28, 64), (36, 52), (70, 100), (52, 100)]), dk),
    ]
    outline = P([(0, 0), (28, 0), (28, 46), (66, 0), (90, 0), (90, 6), (54, 40), (94, 100), (52, 100),
                 (28, 64), (28, 100), (0, 100)])
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in outline) + "Z"
    stroke = (f'<path d="{d}" fill="none" stroke="{edge}" stroke-width="{edge_w}" stroke-linejoin="round"/>'
              if edge else "")
    return "".join(parts) + stroke


SHARDS = ([(150, 150), (176, 136), (172, 164)], [(366, 136), (394, 150), (370, 166)],
          [(96, 236), (122, 224), (118, 250)], [(408, 222), (432, 238), (404, 246)])


def emblem_body(mono=None):
    """Inner content of the 512x512 emblem (may overflow slightly: rays, blade)."""
    out = []
    if not mono:
        out.append(f'<circle cx="256" cy="256" r="228" fill="{NAVY}"/>')
        out.append(rays(RCX, RCY, RAY_SPEC))
        out += [poly(p, GOLD_LT) for p in SHARDS]
        out.append(f'<path fill="{NAVY_DK}" d="M32.3 300 A228 228 0 0 0 479.7 300 Z"/>')
        out.append('<path fill="none" stroke="#25324b" stroke-width="2" d="M66 330 A192 192 0 0 0 446 330"/>')
        out.append(f'<circle cx="256" cy="256" r="230" fill="none" stroke="{GOLD}" stroke-width="22"/>')
        out.append(f'<circle cx="256" cy="256" r="240" fill="none" stroke="{GOLD_LT}" stroke-width="3"/>')
        out.append(f'<circle cx="256" cy="256" r="219" fill="none" stroke="{GOLD_DK}" stroke-width="3"/>')
        out.append(rays(RCX, RCY, OUT_RAYS))
        out.append(f'<path fill="{SILVER_LT}" d="M-8 316 Q256 262 520 316 Q256 284 -8 316Z"/>')
        out.append(f'<path fill="{SILVER}" d="M-8 316 Q256 286 520 316 Q256 296 -8 316Z"/>')
        out.append(k_shape(160, 142, 218))
    else:
        m = mono
        kd = k_shape(160, 142, 218, edge="#000", edge_w=18)
        kd = kd[kd.rindex('<path d="'):]
        out.append('<mask id="kgap" maskUnits="userSpaceOnUse" x="-20" y="-40" width="560" height="580">'
                   '<rect x="-20" y="-40" width="560" height="580" fill="#fff"/>' + kd.replace('fill="none"', 'fill="#000"') + '</mask>')
        out.append('<g mask="url(#kgap)">')
        out.append(rays(RCX, RCY, RAY_SPEC, m, m))
        out += [poly(p, m) for p in SHARDS]
        out.append(f'<circle cx="256" cy="256" r="230" fill="none" stroke="{m}" stroke-width="22"/>')
        out.append(rays(RCX, RCY, OUT_RAYS, m, m))
        # punch the K and blade out of the rays with a background-coloured gap
        out.append(f'<path fill="{m}" d="M-8 316 Q256 262 520 316 Q256 284 -8 316Z"/>')
        out.append('</g>')
        out.append(k_shape(160, 142, 218, tones=(m, m, m), edge=None))
    return "".join(out)


def emblem_svg(mono=None):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-12 -30 536 556" role="img" aria-label="Kaotic Production">'
            f"{emblem_body(mono)}</svg>")


def favicon_svg():
    """Simplified: dark disc, gold ring, 7 bold rays, big K. Reads at 16 px."""
    spec = [(-90, 226, 34), (-52, 214, 28), (-128, 214, 28), (-18, 190, 24), (-162, 190, 24)]
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
            f'<circle cx="256" cy="256" r="254" fill="{NAVY}"/>'
            + rays(256, 250, spec) +
            f'<circle cx="256" cy="256" r="236" fill="none" stroke="{GOLD}" stroke-width="34"/>'
            + k_shape(128, 106, 300, edge=GOLD_LT, edge_w=12) + "</svg>")


# ------------------------------------------------------------------ wordmark
def serif_caps():
    """KAOTIC drawn as serif capitals, cap height 100. List of (path d, advance)."""
    T, t, S = 19, 8, 6  # thick stroke, thin stroke, serif height
    def R(x, y, w, h):
        return f"M{x} {y}h{w}v{h}h{-w}Z"
    def D(x1, y1, x2, y2, w):
        return f"M{x1} {y1}L{x1 + w} {y1}L{x2 + w} {y2}L{x2} {y2}Z"
    k = R(6, 0, T, 100) + R(0, 0, 32, S) + R(0, 100 - S, 32, S)
    k += D(63, 0, 25, 50, t + 3) + R(54, 0, 30, S)
    k += "M27 42L42 42L82 100L63 100Z" + R(58, 100 - S, 32, S)
    a = D(37, 0, 7, 100, t) + "M31 0L47 0L81 100L62 100Z" + R(17, 63, 50, 7)
    a += R(-1, 100 - S, 26, S) + R(53, 100 - S, 36, S)
    o = ("M45 0C70 0 90 22 90 50C90 78 70 100 45 100C20 100 0 78 0 50C0 22 20 0 45 0Z"
         "M45 6C32 6 21 24 21 50C21 76 32 94 45 94C58 94 69 76 69 50C69 24 58 6 45 6Z")
    tt = R(0, 0, 78, t + 2) + R(0, 0, 5, 22) + R(73, 0, 5, 22) + R(29.5, 0, T, 100) + R(20, 100 - S, 38, S)
    i = R(7, 0, T, 100) + R(0, 0, 33, S) + R(0, 100 - S, 33, S)
    c = ("M48 0C64 0 76 5 84 12L84 32L78 32C74 16 63 6 48 6C33 6 21 24 21 50C21 76 33 94 48 94"
         "C64 94 75 84 80 68L86 70C80 88 66 100 47 100C21 100 0 78 0 50C0 22 21 0 48 0Z")
    return [(k, 90), (a, 88), (o, 90), (tt, 78), (i, 33), (c, 86)]


def nunito_caps(text, size, tracking, weight=800):
    f = instantiateVariableFont(TTFont(FONT), {"wght": weight})
    gs, cmap, hmtx = f.getGlyphSet(), f.getBestCmap(), f["hmtx"]
    s = size / f["head"].unitsPerEm
    pen = SVGPathPen(gs)
    x = 0.0
    for ch in text:
        g = cmap[ord(ch)]
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, 0)))
        x += hmtx[g][0] * s + tracking
    return pen.getCommands(), x - tracking


def wordmark_group(x, y, cap, theme):
    """KAOTIC over PRODUCTION, top-left (x, y), cap height `cap`."""
    if theme == "dark":
        top, bot, edge, sub = SILVER_LT, SILVER, GOLD, "#B3BCC9"
    elif theme == "light":
        top, bot, edge, sub = "#2E3850", "#161C29", GOLD_DK, "#4A5468"
    else:
        top = bot = sub = theme
        edge = None
    s = cap / 100.0
    gap = 10
    xs, ds = 0, []
    for d, w in serif_caps():
        ds.append(f'<path transform="translate({xs:.1f} 0)" d="{d}"/>')
        xs += w + gap
    width = (xs - gap) * s
    letters = "".join(ds)
    g = f'<g transform="translate({x:.1f} {y:.1f}) scale({s:.4f})">'
    if edge:
        cid = "wmhalf" + theme
        g += (f'<clipPath id="{cid}"><rect x="-10" y="-10" width="{xs + 20}" height="58"/></clipPath>'
              f'<g fill="{bot}" stroke="{edge}" stroke-width="{3.2 / s:.2f}" stroke-linejoin="round" paint-order="stroke">{letters}</g>'
              f'<g fill="{top}" clip-path="url(#{cid})">{letters}</g>')
    else:
        g += f'<g fill="{top}">{letters}</g>'
    g += "</g>"
    psize = cap * 0.36
    _, w0 = nunito_caps("PRODUCTION", psize, 0)
    dp, _ = nunito_caps("PRODUCTION", psize, (width - w0) / 9)
    py = y + cap * 1.56
    g += f'<path fill="{sub}" transform="translate({x:.1f} {py:.1f})" d="{dp}"/>'
    return g, width


def lockup_svg(theme):
    E = 220                      # emblem size in the lockup
    mono = None if theme in ("dark", "light") else theme
    cap = 70
    wx = E + 36
    wy = (E - cap * 1.56) / 2 + 2
    wm, w = wordmark_group(wx, wy, cap, theme)
    total = wx + w + 8
    sc = E / 536
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total:.0f} {E}" role="img" aria-label="Kaotic Production">'
            f'<g transform="scale({sc:.5f}) translate(12 30)">{emblem_body(mono)}</g>{wm}</svg>')


def main():
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        if old.startswith("kaotic-"):
            os.remove(os.path.join(OUT, old))
    files = {
        "kaotic-emblem.svg": emblem_svg(),
        "kaotic-emblem-white.svg": emblem_svg("#FFFFFF"),
        "kaotic-logo-dark-bg.svg": lockup_svg("dark"),
        "kaotic-logo-light-bg.svg": lockup_svg("light"),
        "kaotic-logo-white.svg": lockup_svg("#FFFFFF"),
        "kaotic-logo-black.svg": lockup_svg("#151A24"),
        "kaotic-favicon.svg": favicon_svg(),
    }
    for n, s in files.items():
        open(os.path.join(OUT, n), "w", encoding="utf-8").write(s)
    open(os.path.join(ROOT, "favicon.svg"), "w", encoding="utf-8").write(files["kaotic-favicon.svg"])
    print("brand svgs:", ", ".join(files))


if __name__ == "__main__":
    main()
