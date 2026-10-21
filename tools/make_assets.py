"""Build the site's images, fonts, hero clip poster and press-kit zip.

Sources are the game's store art (E:\\ÇÖP TOPLAMA OYUNU\\docs\\store) and the
Steam trailer. Run only when the art changes:

    python tools/make_assets.py          (needs Pillow and fonttools+brotli)

Every picture is written as AVIF + WebP + JPEG (or PNG when it has
transparency) in a few widths, for <picture>/srcset.
"""
import io
import os
import shutil
import subprocess
import zipfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = r"E:\ÇÖP TOPLAMA OYUNU"
STORE = os.path.join(GAME, "docs", "store")
TRAILER = os.path.join(STORE, "trailer", "reverdo-steam-en.mp4")
FFMPEG = r"C:\Users\pc\AppData\Local\KiyiDevTools\ffmpeg\ffmpeg.exe"
IMG = os.path.join(ROOT, "assets", "img")
CACHE = os.path.join(ROOT, "tools", "_cache")
PRESS = os.path.join(ROOT, "reverdo", "presskit")

SHOTS = [
    "01-before-after-coast", "02-paris-ada", "03-sultanahmet", "04-tour-boat",
    "05-taj-mahal", "06-octopus-grab", "07-giza", "08-ice-cream-van",
    "09-mine-cart", "10-eiffel-tower",
]
# stills taken from the Steam trailer (all game footage, no text cards)
FRAMES = {
    "ege-paris": 12.8, "ada-taj": 15.3, "ada-beach": 50.4, "submarine": 24.3,
    "swans": 44.5, "fountain": 45.5, "ice-cream": 47.0, "concert": 53.5,
    "campus-caps": 27.8, "coast-green": 2.3, "sultanahmet-park": 37.6,
}
W3 = (640, 1280, 1920)


def save_set(im, name, widths, alpha=False, q=(52, 76, 80)):
    """Write name-<w>.avif/.webp/.jpg|.png for each width."""
    out = []
    for w in widths:
        if w > im.width:
            w = im.width
        h = round(im.height * w / im.width)
        r = im.resize((w, h), Image.LANCZOS) if w != im.width else im.copy()
        base = os.path.join(IMG, f"{name}-{w}")
        if alpha:
            r = r.convert("RGBA")
            r.save(base + ".avif", quality=q[0] + 8)
            r.save(base + ".webp", quality=q[1] + 6, method=6)
            r.save(base + ".png", optimize=True)
        else:
            r = r.convert("RGB")
            r.save(base + ".avif", quality=q[0])
            r.save(base + ".webp", quality=q[1], method=6)
            r.save(base + ".jpg", quality=q[2], optimize=True, progressive=True)
        out.append(w)
    return out


def grab(t, path):
    if not os.path.exists(path):
        subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t),
                        "-i", TRAILER, "-frames:v", "1", path], check=True)
    return Image.open(path)


def fonts():
    from fontTools import subset
    src = os.path.join(GAME, "native3d", "assets", "fonts", "Nunito.ttf")
    dst = os.path.join(ROOT, "assets", "fonts", "nunito-var.woff2")
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt", "case", "lnum", "tnum"]
    opts.name_IDs = ["*"]
    f = subset.load_font(src, opts)
    s = subset.Subsetter(opts)
    s.populate(unicodes=list(range(0x20, 0x7F)) + list(range(0xA0, 0x180))
               + [0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026,
                  0x20AC, 0x20BA, 0x2122, 0x2190, 0x2192, 0x2193, 0x2212, 0x00D7, 0x2009])
    s.subset(f)
    subset.save_font(f, dst, opts)
    shutil.copy(os.path.join(GAME, "native3d", "assets", "fonts", "Nunito-OFL.txt"),
                os.path.join(ROOT, "assets", "fonts", "Nunito-OFL.txt"))
    print("font", os.path.getsize(dst))


def images():
    os.makedirs(IMG, exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)
    for s in SHOTS:
        save_set(Image.open(os.path.join(STORE, "steam", "screenshots", s + ".jpg")), "shot-" + s, W3)
    for name, t in FRAMES.items():
        im = grab(t, os.path.join(CACHE, f"frame-{name}.png"))
        save_set(im, "still-" + name, W3)
    # Ada and Ege portraits (4:5) cut from the stills
    ege = Image.open(os.path.join(CACHE, "frame-ege-paris.png")).crop((236, 0, 1100, 1080))
    ada = Image.open(os.path.join(CACHE, "frame-ada-taj.png")).crop((900, 0, 1764, 1080))
    save_set(ege, "portrait-ege", (432, 864))
    save_set(ada, "portrait-ada", (432, 864))
    # key art (Steam library hero, no text)
    save_set(Image.open(os.path.join(STORE, "steam", "library_hero_3840x1240.png")), "keyart", (960, 1920, 2880))
    # game wordmark (transparent)
    lg = Image.open(os.path.join(STORE, "steam", "library_logo_1280x720.png"))
    lg = lg.crop(lg.getbbox())
    save_set(lg, "reverdo-wordmark", (400, 800, 1200), alpha=True)
    badge = Image.open(os.path.join(GAME, "native3d", "assets", "reverdo-logo.png"))
    save_set(badge, "reverdo-badge", (256, 512), alpha=True)
    icon = Image.open(os.path.join(STORE, "play", "app_icon_512x512.png")).convert("RGBA")
    save_set(icon, "reverdo-icon", (96, 192, 512), alpha=True)
    icon.resize((180, 180), Image.LANCZOS).convert("RGB").save(
        os.path.join(ROOT, "reverdo", "apple-touch-icon.png"), optimize=True)
    icon.resize((32, 32), Image.LANCZOS).save(os.path.join(ROOT, "reverdo", "favicon-32.png"), optimize=True)
    # trailer posters
    for lang in ("en", "tr"):
        save_set(Image.open(os.path.join(STORE, "trailer", f"poster-steam-{lang}.png")), f"trailer-poster-{lang}", (960, 1920))
    # hero clip poster = first frame of the loop
    clip = os.path.join(ROOT, "assets", "video", "reverdo-hero-720.mp4")
    p = os.path.join(CACHE, "hero-first.png")
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", clip,
                    "-frames:v", "1", p], check=True)
    save_set(Image.open(p), "hero-poster", (640, 1280), q=(45, 70, 72))
    # Reverdo share image 1200x630: key art + wordmark
    ka = Image.open(os.path.join(STORE, "steam", "library_hero_3840x1240.png")).convert("RGB")
    scale = 630 / ka.height
    ka = ka.resize((round(ka.width * scale), 630), Image.LANCZOS)
    x0 = (ka.width - 1200) // 2
    og = ka.crop((x0, 0, x0 + 1200, 630))
    shade = Image.new("RGBA", og.size, (0, 0, 0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(shade)
    for y in range(630):
        a = int(max(0, (y - 250) / 380) * 150)
        d.line([(0, y), (1200, y)], fill=(16, 40, 18, a))
    og = Image.alpha_composite(og.convert("RGBA"), shade)
    lw = lg.resize((760, round(lg.height * 760 / lg.width)), Image.LANCZOS)
    og.alpha_composite(lw, ((1200 - lw.width) // 2, 630 - lw.height - 70))
    og.convert("RGB").save(os.path.join(IMG, "og-reverdo.jpg"), quality=84, optimize=True, progressive=True)


def presskit():
    files = os.path.join(PRESS, "files")
    os.makedirs(files, exist_ok=True)
    lg = Image.open(os.path.join(STORE, "steam", "library_logo_1280x720.png"))
    lg.crop(lg.getbbox()).save(os.path.join(files, "reverdo-logo-wordmark.png"), optimize=True)
    shutil.copy(os.path.join(GAME, "native3d", "assets", "reverdo-logo.png"), os.path.join(files, "reverdo-logo-badge.png"))
    shutil.copy(os.path.join(STORE, "play", "app_icon_512x512.png"), os.path.join(files, "reverdo-icon-512.png"))
    for n in ("kaotic-wordmark-ink.svg", "kaotic-wordmark-cream.svg", "kaotic-mark.svg"):
        shutil.copy(os.path.join(ROOT, "assets", "brand", n), os.path.join(files, n))
    for n in ("kaotic-wordmark-ink.png", "kaotic-wordmark-cream.png", "kaotic-mark-512.png"):
        p = os.path.join(ROOT, "assets", "brand", n)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(files, n))
    # key art as high quality JPEG (the PNG is 10+ MB)
    Image.open(os.path.join(STORE, "steam", "library_hero_3840x1240.png")).convert("RGB").save(
        os.path.join(files, "reverdo-keyart-3840x1240.jpg"), quality=90, optimize=True)
    Image.open(os.path.join(STORE, "steam", "header_capsule_920x430.png")).convert("RGB").save(
        os.path.join(files, "reverdo-capsule-920x430.jpg"), quality=90, optimize=True)
    Image.open(os.path.join(STORE, "steam", "library_capsule_600x900.png")).convert("RGB").save(
        os.path.join(files, "reverdo-capsule-600x900.jpg"), quality=90, optimize=True)
    zpath = os.path.join(PRESS, "reverdo-presskit.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for s in SHOTS:
            z.write(os.path.join(STORE, "steam", "screenshots", s + ".jpg"), f"reverdo-presskit/screenshots/reverdo-{s}.jpg")
        for n in sorted(os.listdir(files)):
            sub = "logos" if ("logo" in n or "kaotic" in n or "icon" in n) else "art"
            z.write(os.path.join(files, n), f"reverdo-presskit/{sub}/{n}")
        z.writestr("reverdo-presskit/README.txt",
                   "Reverdo press kit - Kaotic Production\r\n"
                   "https://kaoticproduction.com/reverdo/presskit/\r\n\r\n"
                   "All screenshots and art are taken from the game (1.27-1.28).\r\n"
                   "You may use them to write about Reverdo. Please do not alter the logos.\r\n")
    print("zip", os.path.getsize(zpath))


if __name__ == "__main__":
    import sys
    what = sys.argv[1:] or ["fonts", "images", "presskit"]
    if "fonts" in what:
        fonts()
    if "images" in what:
        images()
    if "presskit" in what:
        presskit()
