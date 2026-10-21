"""Kaotic Production logo: wordmark + mark as pure SVG paths (no font needed).

Letters are taken from Nunito (OFL, the game's font) at its heaviest weight and
turned into outlines with fontTools, so the logo looks the same everywhere.
The "i" of "kaotic" is a dotless i with a little spark for its dot.

Run with a Python that has fonttools:  python tools/make_brand.py
Writes assets/brand/*.svg
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

CORAL = "#FF5B3A"
SUN = "#FFC23D"
INK = "#1A1530"
CREAM = "#FFF7EA"


def load(weight):
    f = instantiateVariableFont(TTFont(FONT), {"wght": weight})
    return f, f.getGlyphSet(), f.getBestCmap(), f["hmtx"]


def text_path(text, weight, size, x0, baseline, tracking=0.0):
    """Return (svg path d, advance width in px) for text set at `size` px."""
    f, gs, cmap, hmtx = load(weight)
    upm = f["head"].unitsPerEm
    s = size / upm
    pen = SVGPathPen(gs)
    x = x0
    for ch in text:
        g = cmap[ord(ch)]
        tp = TransformPen(pen, (s, 0, 0, -s, x, baseline))
        gs[g].draw(tp)
        x += hmtx[g][0] * s + tracking * size
    return pen.getCommands(), x - x0 - tracking * size


def glyph_bounds(ch, weight, size):
    f, gs, cmap, hmtx = load(weight)
    from fontTools.pens.boundsPen import BoundsPen
    bp = BoundsPen(gs)
    gs[cmap[ord(ch)]].draw(bp)
    s = size / f["head"].unitsPerEm
    xmin, ymin, xmax, ymax = bp.bounds
    return xmin * s, ymin * s, xmax * s, ymax * s, hmtx[cmap[ord(ch)]][0] * s


def sparkle(cx, cy, r, rot=0.0, waist=0.28):
    """Four-point sparkle with curved (concave) sides, as a path."""
    pts = []
    for k in range(4):
        a = math.radians(rot + k * 90)
        tip = (cx + r * math.cos(a), cy + r * math.sin(a))
        pts.append(tip)
    d = "M%.2f %.2f" % pts[0]
    for k in range(4):
        p1 = pts[(k + 1) % 4]
        # control point pulled toward the centre makes the concave side
        a = math.radians(rot + k * 90 + 45)
        c = (cx + r * waist * math.cos(a), cy + r * waist * math.sin(a))
        d += " Q%.2f %.2f %.2f %.2f" % (c[0], c[1], p1[0], p1[1])
    return d + "Z"


def wordmark(text_fill="currentColor", sub_fill="currentColor"):
    """Horizontal lockup: 'kaotic' with a spark i-dot, 'PRODUCTION' under it."""
    size = 100
    base = 100
    # "kaot" + dotless i + "c"
    d1, w1 = text_path("kaot", 1000, size, 0, base, -0.01)
    ib = glyph_bounds("ı", 1000, size)
    x_i = w1 - 0.01 * size
    d2, wi = text_path("ı", 1000, size, x_i, base)
    x_c = x_i + ib[4] - 0.01 * size
    d3, wc = text_path("c", 1000, size, x_c, base)
    total = x_c + wc
    # spark over the i
    icx = x_i + (ib[0] + ib[2]) / 2
    spark_main = sparkle(icx + 2, 22, 21, rot=-12)
    spark_small = sparkle(icx + 25, 4, 8.5, rot=8)
    # PRODUCTION, tracked to the width of "kaotic"
    psize = 25.5
    _, pw = text_path("PRODUCTION", 900, psize, 0, 0, 0)
    n = len("PRODUCTION") - 1
    track = (total - 4 - pw) / n / psize
    dp, _ = text_path("PRODUCTION", 900, psize, 2, base + 36, track)
    h = base + 44
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -12 {total + 6:.0f} {h + 12:.0f}" '
        f'role="img" aria-label="Kaotic Production">'
        f'<path fill="{text_fill}" d="{d1}{d2}{d3}"/>'
        f'<path fill="{CORAL}" d="{spark_main}"/>'
        f'<path fill="{SUN}" d="{spark_small}"/>'
        f'<path fill="{sub_fill}" d="{dp}"/>'
        "</svg>"
    )
    return svg, total + 6, h + 12


def mark_svg(bg=INK, fg=CREAM, rounded=True, pad=0):
    """Square app-icon style mark: a heavy 'k' with the spark."""
    S = 512
    f, gs, cmap, hmtx = load(1000)
    xmin, ymin, xmax, ymax, adv = glyph_bounds("k", 1000, 400)
    kw = xmax - xmin
    kh = ymax - ymin
    x0 = (S - kw) / 2 - xmin - 34
    base = (S + kh) / 2 + 6
    dk, _ = text_path("k", 1000, 400, x0, base)
    sp1 = sparkle(384, 140, 72, rot=-12)
    sp2 = sparkle(454, 68, 27, rot=8)
    r = 112 if rounded else 0
    rect = f'<rect x="{pad}" y="{pad}" width="{S - 2 * pad}" height="{S - 2 * pad}" rx="{r}" fill="{bg}"/>' if bg else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}">'
        f"{rect}"
        f'<path fill="{fg}" d="{dk}"/>'
        f'<path fill="{CORAL}" d="{sp1}"/>'
        f'<path fill="{SUN}" d="{sp2}"/>'
        "</svg>"
    )


def main():
    os.makedirs(OUT, exist_ok=True)
    svg, w, h = wordmark()
    open(os.path.join(OUT, "kaotic-wordmark.svg"), "w", encoding="utf-8").write(svg)
    for name, fill in (("kaotic-wordmark-ink.svg", INK), ("kaotic-wordmark-cream.svg", CREAM)):
        s, _, _ = wordmark(fill, fill)
        open(os.path.join(OUT, name), "w", encoding="utf-8").write(s)
    open(os.path.join(OUT, "kaotic-mark.svg"), "w", encoding="utf-8").write(mark_svg())
    # favicon: follows the browser's light/dark theme is not needed: the ink
    # tile reads on both, so one file.
    open(os.path.join(ROOT, "favicon.svg"), "w", encoding="utf-8").write(mark_svg())
    print("wordmark", round(w), "x", round(h))


if __name__ == "__main__":
    main()
