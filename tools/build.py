"""Generate every HTML page of kaoticproduction.com.

    python tools/build.py

Links, e-mail and the trailer id live in tools/config.py. Text lives here,
English and Turkish side by side (t(en, tr)). Privacy and support pages are
ported from the old site (tools/legal/*.html, copied unchanged from
ufukpamuk.github.io/reverdo-gizlilik) and only re-wrapped in the new design.
"""
import html
import json
import os
import re
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")
LEGAL = os.path.join(ROOT, "tools", "legal")
VERSION = "20261021c"   # cache-buster for css/js
YEAR = "2026"

PAGES = {
    "home": {"en": "/", "tr": "/tr/"},
    "reverdo": {"en": "/reverdo/", "tr": "/tr/reverdo/"},
    "presskit": {"en": "/reverdo/presskit/", "tr": "/tr/reverdo/presskit/"},
    "privacy": {"en": "/reverdo/privacy/", "tr": "/reverdo/gizlilik/"},
    "support": {"en": "/reverdo/support/", "tr": "/reverdo/destek/"},
}

E = html.escape


def mail(subject=None, addr=None):
    s = f"?subject={subject.replace(' ', '%20')}" if subject else ""
    return f"mailto:{addr or C.CONTACT_EMAIL}{s}"


# ------------------------------------------------------------------ icons
ICONS = {
    "pc": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2.5" y="3.5" width="19" height="13" rx="2.5"/><path d="M8 20.5h8M12 16.5v4"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="2.5" width="12" height="19" rx="3"/><path d="M10.5 18.5h3"/></svg>',
    "play": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M5 3.8v16.4a1 1 0 0 0 1.5.86l14-8.2a1 1 0 0 0 0-1.72l-14-8.2A1 1 0 0 0 5 3.8z"/><path d="M5.4 3.6l9.4 9.2M5.4 20.4l9.4-8.6" stroke-width="1.6"/></svg>',
    "playfill": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 4.6v14.8a1.2 1.2 0 0 0 1.8 1l12-7.4a1.2 1.2 0 0 0 0-2L8.8 3.6A1.2 1.2 0 0 0 7 4.6z"/></svg>',
    "pause": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M6 4h4v16H6zM14 4h4v16h-4z"/></svg>',
    "globe": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9.5"/><path d="M2.5 12h19M12 2.5c2.8 3 2.8 16 0 19M12 2.5c-2.8 3-2.8 16 0 19"/></svg>',
    "menu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    "prev": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>',
    "next": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>',
    "close": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>',
    "leaf": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 19c0-8 5-13 15-14-1 10-6 15-14 15"/><path d="M5 19c3-4 6-7 10-10"/></svg>',
    "heart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" aria-hidden="true"><path d="M12 20s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.2a4.3 4.3 0 0 1 7.5 2.6C19.5 15.4 12 20 12 20z"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7.5 3v5.5c0 4.6-3.2 8.2-7.5 9.5-4.3-1.3-7.5-4.9-7.5-9.5V6z"/><path d="M8.8 12.2l2.2 2.2 4.4-4.6"/></svg>',
    "offline": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M2.5 9a14 14 0 0 1 19 0M5.5 12.4a9.5 9.5 0 0 1 13 0M8.6 15.6a5 5 0 0 1 6.8 0"/><circle cx="12" cy="19" r="1.2" fill="currentColor"/><path d="M3.5 3.5l17 17"/></svg>',
    "eye": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 12s3.5-6.5 9.5-6.5S21.5 12 21.5 12s-3.5 6.5-9.5 6.5S2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/></svg>',
    "gift": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" aria-hidden="true"><rect x="3.5" y="8.5" width="17" height="12" rx="2"/><path d="M12 8.5v12M3.5 12.5h17M12 8.5S10.5 4 8 4.5 7.5 8.5 12 8.5zM12 8.5s1.5-4.5 4-4 .5 4-4 4z"/></svg>',
    "chat": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" aria-hidden="true"><path d="M4 5.5h16v10H9l-5 4z"/></svg>',
    "map": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" aria-hidden="true"><path d="M3 6l6-2.5 6 2.5 6-2.5v14.5L15 20.5 9 18l-6 2.5z"/><path d="M9 3.5V18M15 6v14.5"/></svg>',
    "users": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.5-3.6 3.2-5.5 6.5-5.5s6 1.9 6.5 5.5"/><circle cx="17" cy="9" r="2.6"/><path d="M16.5 14.6c2.6.1 4.5 1.8 5 4.9"/></svg>',
    "lang": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 5h10M8 3v2c0 5-2.5 8.5-5 10M5.5 9c1.2 2.6 3.4 4.6 6 5.6"/><path d="M12.5 21l4.5-10 4.5 10M14 17.5h6"/></svg>',
    "download": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3.5v12M7 10.5l5 5 5-5M4 20.5h16"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="M3.5 6.5l8.5 6.5 8.5-6.5"/></svg>',
    "youtube": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M21.6 7.2a2.6 2.6 0 0 0-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4a2.6 2.6 0 0 0-1.8 1.8C2 8.8 2 12 2 12s0 3.2.4 4.8a2.6 2.6 0 0 0 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4a2.6 2.6 0 0 0 1.8-1.8c.4-1.6.4-4.8.4-4.8s0-3.2-.4-4.8zM10 15V9l5.2 3z"/></svg>',
}
SPARK = '<svg class="spark {c}" viewBox="0 0 100 100" aria-hidden="true"><path fill="currentColor" d="M50 2Q57 43 98 50Q57 57 50 98Q43 57 2 50Q43 43 50 2Z"/></svg>'


def icon(n):
    return ICONS[n]


# ------------------------------------------------------------------ images
_dims = {}


def dims(path):
    if path not in _dims:
        with Image.open(path) as im:
            _dims[path] = im.size
    return _dims[path]


def avail(name):
    ws = []
    for f in os.listdir(IMG):
        m = re.fullmatch(re.escape(name) + r"-(\d+)\.(jpg|png)", f)
        if m:
            ws.append((int(m.group(1)), m.group(2)))
    ws.sort()
    if not ws:
        raise SystemExit("missing image " + name)
    return ws


def src(name, w=None, ext=None):
    ws = avail(name)
    if w is None:
        w, e = ws[-1]
    else:
        e = dict(ws)[w]
    return f"/assets/img/{name}-{w}.{ext or e}"


def pic(name, alt, sizes="100vw", cls="", lazy=True, high=False, maxw=None):
    """<picture> with AVIF + WebP sources and a JPEG/PNG fallback."""
    ws = avail(name)
    if maxw:
        ws = [x for x in ws if x[0] <= maxw] or ws[:1]
    ext = ws[0][1]
    fb_w = ws[-1][0] if len(ws) < 3 else ws[-2][0]
    w, h = dims(os.path.join(IMG, f"{name}-{fb_w}.{ext}"))
    def ss(e):
        return ", ".join(f"/assets/img/{name}-{x}.{e} {x}w" for x, _ in ws)
    attrs = f' class="{cls}"' if cls else ""
    load = ' loading="lazy" decoding="async"' if lazy else (' fetchpriority="high"' if high else "")
    return (f'<picture><source type="image/avif" srcset="{ss("avif")}" sizes="{sizes}">'
            f'<source type="image/webp" srcset="{ss("webp")}" sizes="{sizes}">'
            f'<img src="/assets/img/{name}-{fb_w}.{ext}" srcset="{ss(ext)}" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{E(alt)}"{attrs}{load}></picture>')


# ------------------------------------------------------------------ text
def T(lang):
    return lambda en, tr: en if lang == "en" else tr


RELEASE = {
    "en": ("Coming January 2027", "Türkiye, on phones: early December 2026"),
    "tr": ("Ocak 2027'de geliyor", "Türkiye'de telefonlarda: Aralık 2026 başı"),
}

SHOT_ALT = {
    "01-before-after-coast": ("Before and after: a grey, littered beach and the same beach clean and green",
                              "Önce ve sonra: gri, çöplerle dolu sahil ve aynı sahilin temiz, yeşil hâli"),
    "02-paris-ada": ("Ada in front of the Eiffel Tower in Paris", "Ada, Paris'te Eyfel Kulesi'nin önünde"),
    "03-sultanahmet": ("Sultanahmet Square in Istanbul, seen from above", "Yukarıdan İstanbul'daki Sultanahmet Meydanı"),
    "04-tour-boat": ("A tour boat sails past the beach while litter is cleaned up", "Çöpler toplanırken sahilin önünden tur teknesi geçiyor"),
    "05-taj-mahal": ("The Taj Mahal and its gardens from above", "Yukarıdan Tac Mahal ve bahçeleri"),
    "06-octopus-grab": ("The octopus-grab excavator at the car scrapyard", "Araba hurdalığında ahtapot kepçeli iş makinesi"),
    "07-giza": ("The Pyramids of Giza and the Sphinx", "Giza Piramitleri ve Sfenks"),
    "08-ice-cream-van": ("Children at the ice-cream van in the fountain park", "Fıskiyeli Park'ta dondurma arabasının başındaki çocuklar"),
    "09-mine-cart": ("A mine cart ride through the glowing crystal cave", "Işıldayan kristal mağarada maden vagonu yolculuğu"),
    "10-eiffel-tower": ("The Eiffel Tower and the gardens of the Champ de Mars", "Eyfel Kulesi ve Champ de Mars bahçeleri"),
}
STILL_ALT = {
    "concert": ("A light show over the stage at the concert ground", "Konser alanında sahnenin üstünde ışık gösterisi"),
    "swans": ("Swans on a clean forest pond", "Temiz orman göletinde kuğular"),
    "coast-green": ("The beach after cleaning: grass, flowers and visitors are back", "Temizlenen sahil: çimen, çiçekler ve ziyaretçiler geri döndü"),
    "submarine": ("The cleanup submarine collecting litter under water", "Su altında çöp toplayan temizlik denizaltısı"),
    "ice-cream": ("The ice-cream van visits the park", "Dondurma arabası parka geliyor"),
    "fountain": ("A rainbow over the fountain in the park", "Parktaki fıskiyenin üstünde gökkuşağı"),
    "sultanahmet-park": ("The park between Hagia Sophia and the Blue Mosque at sunset, clean and green",
                         "Ayasofya ile Sultanahmet Camii arasındaki park gün batımında, temiz ve yeşil"),
    "campus-caps": ("Graduation caps fly over the clean campus", "Temizlenen kampüste mezuniyet kepleri havaya uçuyor"),
    "ada-beach": ("Ada celebrating on the beach", "Ada sahilde kutlama yapıyor"),
}

SHOT_LABEL = {
    "01-before-after-coast": ("Before / after: the beach", "Önce / sonra: sahil"), "02-paris-ada": ("Ada in Paris", "Ada Paris'te"),
    "03-sultanahmet": ("Sultanahmet Square", "Sultanahmet Meydanı"), "04-tour-boat": ("Tour boat", "Tur teknesi"),
    "05-taj-mahal": ("Taj Mahal", "Tac Mahal"), "06-octopus-grab": ("Octopus-grab excavator", "Ahtapot kepçe"),
    "07-giza": ("Pyramids of Giza", "Giza Piramitleri"), "08-ice-cream-van": ("Ice-cream van", "Dondurma arabası"),
    "09-mine-cart": ("Mine cart", "Maden vagonu"), "10-eiffel-tower": ("Eiffel Tower", "Eyfel Kulesi"),
}

MAPS = [
    ("Beach", "Sahil"), ("Fountain Park", "Fıskiyeli Park"), ("Industrial Zone", "Sanayi Bölgesi"),
    ("Funfair", "Lunapark"), ("Train Station", "Tren İstasyonu"), ("Concert Ground", "Konser Alanı"),
    ("Forest Pond", "Orman Göleti"), ("Car Scrapyard", "Araba Hurdalığı"), ("Campsite", "Kamp Alanı"),
    ("City Street", "Şehir Sokağı"), ("Campus", "Kampüs"), ("Underwater Habitat", "Sualtı Habitatı"),
    ("Blocked Dam", "Tıkanmış Baraj"), ("Toxic Swamp", "Zehirli Bataklık"), ("Ancient Mine", "Antik Maden Mağarası"),
    ("Seaside Promenade", "Deniz Kordonu"),
]
LANDMARKS = [("Sultanahmet Square", "Sultanahmet Meydanı"), ("Eiffel Tower", "Eyfel Kulesi"),
             ("Pyramids of Giza", "Giza Piramitleri"), ("Taj Mahal", "Tac Mahal")]
LANGS = {
    "en": "English, Turkish, German, Spanish, French, Portuguese, Russian, Japanese, Chinese, Hindi and Arabic",
    "tr": "Türkçe, İngilizce, Almanca, İspanyolca, Fransızca, Portekizce, Rusça, Japonca, Çince, Hintçe ve Arapça",
}


# ------------------------------------------------------------------ store buttons
def stores(lang, light=False, only=None):
    t = T(lang)
    items = [
        ("steam", C.STEAM_URL, "pc", t("Wishlist on", "İstek listene ekle"), "Steam"),
        ("appstore", C.APP_STORE_URL, "phone", t("Download on the", "İndir"), "App Store"),
        ("play", C.GOOGLE_PLAY_URL, "play", t("Get it on", "İndir"), "Google Play"),
    ]
    out = []
    for key, url, ic, live, name in items:
        if only and key not in only:
            continue
        cls = "store light" if light else "store"
        if url:
            out.append(f'<a class="{cls}" href="{E(url)}" rel="noopener">{icon(ic)}<span><small>{live}</small><span>{name}</span></span></a>')
        else:
            soon = t("Coming soon", "Yakında")
            out.append(f'<div class="{cls} soon" role="group" aria-label="{name}: {soon}">{icon(ic)}<span><small>{soon}</small><span>{name}</span></span></div>')
    return '<div class="stores">' + "".join(out) + "</div>"


# ------------------------------------------------------------------ page shell
def head(lang, key, title, desc, og_image, theme, extra_head="", jsonld=None, noindex=False):
    path = PAGES[key][lang] if key else None
    url = C.SITE_URL + path if path else C.SITE_URL + "/404.html"
    alts = ""
    if key:
        alts = (f'<link rel="canonical" href="{url}">'
                f'<link rel="alternate" hreflang="en" href="{C.SITE_URL}{PAGES[key]["en"]}">'
                f'<link rel="alternate" hreflang="tr" href="{C.SITE_URL}{PAGES[key]["tr"]}">'
                f'<link rel="alternate" hreflang="x-default" href="{C.SITE_URL}{PAGES[key]["en"]}">')
    if theme == "game":
        icons = ('<link rel="icon" href="/reverdo/favicon-32.png" sizes="32x32" type="image/png">'
                 '<link rel="apple-touch-icon" href="/reverdo/apple-touch-icon.png">')
        color = "#1d4426"
    else:
        icons = ('<link rel="icon" href="/favicon.svg" type="image/svg+xml">'
                 '<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">'
                 '<link rel="apple-touch-icon" href="/apple-touch-icon.png">'
                 '<link rel="manifest" href="/site.webmanifest">')
        color = "#0d1016"
    ld = ""
    if jsonld:
        ld = '<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"
    locale = "en_US" if lang == "en" else "tr_TR"
    alt_locale = "tr_TR" if lang == "en" else "en_US"
    robots = '<meta name="robots" content="noindex">' if noindex else ""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="{color}">
<meta name="referrer" content="strict-origin-when-cross-origin">
{robots}{alts}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Kaotic Production">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{C.SITE_URL}{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{locale}">
<meta property="og:locale:alternate" content="{alt_locale}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{E(title)}">
<meta name="twitter:description" content="{E(desc)}">
<meta name="twitter:image" content="{C.SITE_URL}{og_image}">
{icons}
<link rel="preload" href="/assets/fonts/nunito-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css?v={VERSION}">
{extra_head}{ld}
</head>
"""


def lang_switch(lang, key):
    other = "tr" if lang == "en" else "en"
    label = "Türkçe" if other == "tr" else "English"
    short = "TR" if other == "tr" else "EN"
    return (f'<a class="lang" href="{PAGES[key][other]}" hreflang="{other}" lang="{other}" '
            f'aria-label="{label}">{icon("globe")}<span>{short}</span></a>')


def lang_hint(lang, key):
    if lang != "en":
        return ""
    return (f'<div class="lang-hint" lang="tr"><div class="wrap"><span>Bu sayfanın Türkçesi de var.</span>'
            f'<a href="{PAGES[key]["tr"]}" hreflang="tr">Türkçe sayfaya geç</a>'
            f'<button type="button" aria-label="Kapat">&times;</button></div></div>')


def header(lang, key, theme, overlay=False):
    t = T(lang)
    p = PAGES
    if theme == "studio":
        brand = (f'<a class="brand brand-k" href="{p["home"][lang]}"><img src="/assets/brand/kaotic-logo-dark-bg.svg" width="150" height="53" alt="Kaotic Production"></a>')
        h = p["home"][lang]
        links = [(h + "#games", t("Games", "Oyunlar")), (h + "#about", t("About", "Hakkımızda")),
                 (h + "#contact", t("Contact", "İletişim")), (p["presskit"][lang], t("Press", "Basın"))]
    else:
        brand = (f'<a class="brand" href="{p["reverdo"][lang]}"><img src="/assets/img/reverdo-icon-96.png" width="38" height="38" alt="">'
                 f'<span lang="en">Reverdo<span class="sub">Kaotic Production</span></span></a>')
        g = p["reverdo"][lang]
        links = [(g + "#features", t("Features", "Özellikler")), (g + "#maps", t("Maps", "Haritalar")),
                 (g + "#gallery", t("Screenshots", "Görseller")), (g + "#faq", t("FAQ", "SSS")),
                 (p["presskit"][lang], t("Press kit", "Basın kiti")), (p["home"][lang], "Studio" if lang == "en" else "Stüdyo")]
    cur = p[key][lang] if key else None
    def a(href, text):
        ac = ' aria-current="page"' if href == cur else ""
        return f'<a href="{href}"{ac}>{text}</a>'
    nav = "".join(a(h_, x) for h_, x in links)
    cls = "site-header overlay" if overlay else "site-header"
    return f"""<a class="skip" href="#main">{t("Skip to content", "İçeriğe geç")}</a>
{lang_hint(lang, key) if key else ""}
<header class="{cls}"><div class="wrap"><div class="bar">{brand}<nav class="nav" aria-label="{t("Main", "Ana menü")}">{nav}</nav>{lang_switch(lang, key) if key else ""}
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="mnav" aria-label="{t("Menu", "Menü")}">{icon("menu")}</button></div>
<nav class="mobile-nav" id="mnav" aria-label="{t("Main", "Ana menü")}">{nav}</nav></div></header>
"""


def footer(lang, key, theme="game"):
    t = T(lang)
    if theme == "studio":
        flogo = '<img class="logo" src="/assets/brand/kaotic-logo-dark-bg.svg" width="240" height="85" alt="Kaotic Production">'
    else:
        flogo = ('<picture><source srcset="/assets/brand/kaotic-logo-dark-bg.svg" media="(prefers-color-scheme: dark)">'
                 '<img class="logo" src="/assets/brand/kaotic-logo-light-bg.svg" width="240" height="85" alt="Kaotic Production"></picture>')
    p = PAGES
    other = "tr" if lang == "en" else "en"
    langs = (f'<li><a href="{p[key]["en"] if key else "/"}" hreflang="en" lang="en">English</a></li>'
             f'<li><a href="{p[key]["tr"] if key else "/tr/"}" hreflang="tr" lang="tr">Türkçe</a></li>')
    return f"""<footer class="site-footer"><div class="wrap">
<div class="cols">
<div>{flogo}
<p>{t("An independent game studio from Istanbul.", "İstanbul'dan bağımsız bir oyun stüdyosu.")}<br><a href="{mail()}">{C.CONTACT_EMAIL}</a></p></div>
<div><h3>Reverdo</h3><ul>
<li><a href="{p["reverdo"][lang]}">{t("Game page", "Oyun sayfası")}</a></li>
<li><a href="{p["presskit"][lang]}">{t("Press kit", "Basın kiti")}</a></li>
<li><a href="{p["support"][lang]}">{t("Support", "Destek")}</a></li>
<li><a href="{p["privacy"][lang]}">{t("Privacy policy", "Gizlilik politikası")}</a></li></ul></div>
<div><h3>{t("Studio", "Stüdyo")}</h3><ul>
<li><a href="{p["home"][lang]}">{t("Home", "Ana sayfa")}</a></li>
<li><a href="{p["home"][lang]}#about">{t("About", "Hakkımızda")}</a></li>
<li><a href="{p["home"][lang]}#contact">{t("Contact", "İletişim")}</a></li></ul></div>
<div><h3>{t("Language", "Dil")}</h3><ul>{langs}</ul></div>
</div>
<div class="fine"><span>&copy; {YEAR} Kaotic Production &middot; {t("Istanbul, Türkiye", "İstanbul, Türkiye")}</span><span>{t("This site uses no cookies and no trackers.", "Bu sitede çerez ve izleyici yok.")}</span></div>
</div></footer>
"""


def page(lang, key, theme, title, desc, og, body, overlay=False, jsonld=None, extra_body="", noindex=False):
    return (head(lang, key, title, desc, og, theme, jsonld=jsonld, noindex=noindex)
            + f'<body class="{theme}">\n' + header(lang, key, theme, overlay)
            + f'<main id="main">\n{body}\n</main>\n' + footer(lang, key, theme) + extra_body
            + f'<script src="/assets/js/site.js?v={VERSION}" defer></script>\n</body>\n</html>\n')


ORG = {
    "@type": "Organization", "@id": C.SITE_URL + "/#org", "name": "Kaotic Production",
    "url": C.SITE_URL + "/", "logo": C.SITE_URL + "/assets/brand/kaotic-emblem-512.png",
    "email": C.PRESS_EMAIL, "contactPoint": [{"@type": "ContactPoint", "contactType": "customer support", "email": C.CONTACT_EMAIL}, {"@type": "ContactPoint", "contactType": "press", "email": C.PRESS_EMAIL}], "founder": {"@type": "Person", "name": "Ufuk Pamuk"},
    "address": {"@type": "PostalAddress", "addressLocality": "Istanbul", "addressCountry": "TR"},
}


# ================================================================== HOME
def home(lang):
    t = T(lang)
    rel = RELEASE[lang]
    body = f"""
<section class="k-hero" aria-labelledby="hero-h">
<div class="k-media">
<picture>
<source media="(max-width: 719px)" type="image/avif" srcset="/assets/img/studio-emblem-480.avif 480w, /assets/img/studio-emblem-800.avif 800w, /assets/img/studio-emblem-980.avif 980w" sizes="100vw">
<source media="(max-width: 719px)" type="image/webp" srcset="/assets/img/studio-emblem-480.webp 480w, /assets/img/studio-emblem-800.webp 800w, /assets/img/studio-emblem-980.webp 980w" sizes="100vw">
<source media="(max-width: 719px)" srcset="/assets/img/studio-emblem-480.jpg 480w, /assets/img/studio-emblem-800.jpg 800w, /assets/img/studio-emblem-980.jpg 980w" sizes="100vw">
<source type="image/avif" srcset="/assets/img/studio-cover-960.avif 960w, /assets/img/studio-cover-1440.avif 1440w, /assets/img/studio-cover-2000.avif 2000w" sizes="100vw">
<source type="image/webp" srcset="/assets/img/studio-cover-960.webp 960w, /assets/img/studio-cover-1440.webp 1440w, /assets/img/studio-cover-2000.webp 2000w" sizes="100vw">
<img src="/assets/img/studio-cover-1440.jpg" srcset="/assets/img/studio-cover-960.jpg 960w, /assets/img/studio-cover-1440.jpg 1440w, /assets/img/studio-cover-2000.jpg 2000w" sizes="100vw" width="2000" height="1116" alt="{t("Kaotic Production emblem: a steel K in front of a golden starburst, and the words Kaotic Production", "Kaotic Production amblemi: altın bir patlamanın önünde çelik bir K ve Kaotic Production yazısı")}" fetchpriority="high">
</picture>
<div class="k-glow" aria-hidden="true"></div>
<div class="k-sparks" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
</div>
<div class="wrap k-copy">
<p class="eyebrow">{t("Independent game studio · Istanbul", "Bağımsız oyun stüdyosu · İstanbul")}</p>
<h1 id="hero-h"><span class="visually-hidden">Kaotic Production: </span>{t('Fun, colourful, <span class="hl">meaningful</span> games.', 'Eğlenceli, renkli, <span class="hl">anlamlı</span> oyunlar.')}</h1>
<p class="lead">{t("Kaotic Production is a small independent studio from Istanbul. We make cheerful games for all ages, with a little message inside. Our first game, Reverdo, is on its way.",
                  "Kaotic Production, İstanbul'dan küçük ve bağımsız bir oyun stüdyosu. Her yaştan oyuncu için, içinde küçük bir mesaj taşıyan neşeli oyunlar yapıyoruz. İlk oyunumuz Reverdo yolda.")}</p>
<div class="ctas"><a class="btn" href="{PAGES["reverdo"][lang]}">{t("Meet Reverdo", "Reverdo'yu tanı")}</a><a class="btn ghost" href="#contact">{t("Get in touch", "Bize yazın")}</a></div>
</div>
</section>

<section class="featured" id="games" aria-labelledby="games-h">
<div class="wrap">
<p class="eyebrow">{t("Our first game", "İlk oyunumuz")}</p>
<article class="feature-card">
<div class="bg">{pic("keyart", "", "(min-width: 1500px) 1440px, 100vw")}</div>
<div class="body">
<h2 id="games-h" class="visually-hidden">Reverdo</h2>
{pic("reverdo-wordmark", "Reverdo", "(min-width: 900px) 420px, 82vw", cls="logo")}
<p>{t("Clean up grey, littered places and watch every corner turn green again! 20 maps from a beach to Istanbul's Sultanahmet, the Eiffel Tower and the Taj Mahal, with machines, storms and maps that come alive.",
      "Gri ve çöplerle dolu yerleri temizle, her köşenin yeniden yeşerdiğini izle! Sahilden Sultanahmet'e, Eyfel Kulesi'nden Tac Mahal'e 20 harita, iş makineleri, fırtınalar ve canlanan haritalar.")}</p>
<div class="meta"><span class="chip sun">{rel[0]}</span><span class="chip">PC (Steam)</span><span class="chip">iPhone &amp; iPad</span><span class="chip">Android</span></div>
<div class="actions"><a class="btn" href="{PAGES["reverdo"][lang]}">{t("Explore the game", "Oyunu keşfet")}</a><a class="btn ghost" href="{PAGES["presskit"][lang]}">{t("Press kit", "Basın kiti")}</a></div>
</div>
</article>
</div>
<ul class="showcase" aria-label="{t("Reverdo screenshots", "Reverdo ekran görüntüleri")}">
<li>{pic("still-sultanahmet-park", STILL_ALT["sultanahmet-park"][lang == "tr"], "(min-width: 1200px) 17vw, 70vw", maxw=1280)}</li>
<li>{pic("shot-10-eiffel-tower", SHOT_ALT["10-eiffel-tower"][lang == "tr"], "(min-width: 1200px) 17vw, 70vw", maxw=1280)}</li>
<li>{pic("still-swans", STILL_ALT["swans"][lang == "tr"], "(min-width: 1200px) 17vw, 70vw", maxw=1280)}</li>
<li>{pic("shot-07-giza", SHOT_ALT["07-giza"][lang == "tr"], "(min-width: 1200px) 17vw, 70vw", maxw=1280)}</li>
<li>{pic("still-concert", STILL_ALT["concert"][lang == "tr"], "(min-width: 1200px) 17vw, 70vw", maxw=1280)}</li>
<li>{pic("shot-01-before-after-coast", SHOT_ALT["01-before-after-coast"][lang == "tr"], "(min-width: 1200px) 17vw, 70vw", maxw=1280)}</li>
</ul>
</section>

<section class="about" id="about" aria-labelledby="about-h">
<div class="wrap">
<div class="grid">
<div>
<p class="eyebrow">{t("About the studio", "Stüdyo hakkında")}</p>
<h2 id="about-h">{t("Organised chaos, colourful results.", "Düzenli bir kaos, rengârenk sonuçlar.")}</h2>
<p class="lead">{t("Kaotic Production was founded in Istanbul by Ufuk Pamuk. We're a tiny team, so every detail gets our attention: the colours, the sounds and the little moments that make you smile.",
                  "Kaotic Production, Ufuk Pamuk tarafından İstanbul'da kuruldu. Küçük bir ekibiz; bu yüzden her ayrıntıyla tek tek ilgileniyoruz: renkler, sesler ve insanı gülümseten küçük anlar.")}</p>
<p class="muted">{t("We want our games to be easy to pick up, kind to play and fair to the people who play them. Reverdo, a game about cleaning up the world and watching it turn green again, is the first one.",
                   "Oyunlarımızın kolay başlanan, keyifle oynanan ve oyuncusuna karşı adil oyunlar olmasını istiyoruz. Dünyayı temizleyip yeniden yeşerdiğini izlediğin Reverdo bunların ilki.")}</p>
</div>
<ul class="facts">
<li><b>{t("Based in", "Merkez")}</b><span>{t("Istanbul, Türkiye", "İstanbul, Türkiye")}</span></li>
<li><b>{t("Founder", "Kurucu")}</b><span>Ufuk Pamuk</span></li>
<li><b>{t("First game", "İlk oyun")}</b><span><a href="{PAGES["reverdo"][lang]}">Reverdo</a></span></li>
<li><b>{t("Platforms", "Platformlar")}</b><span>PC (Steam), iOS, Android</span></li>
</ul>
</div>
<div class="values">
<div class="value"><div class="ic" style="background:#ff5b3a">{icon("users")}</div><h3>{t("For everyone", "Herkes için")}</h3>
<p>{t("No violence, no chat, nothing to worry about: games the whole family can enjoy together.", "Şiddet yok, sohbet yok, endişelenecek bir şey yok: bütün ailenin birlikte keyifle oynayabileceği oyunlar.")}</p></div>
<div class="value"><div class="ic" style="background:#2f8f5b">{icon("shield")}</div><h3>{t("Fair play", "Adil oyun")}</h3>
<p>{t("No paid lucky draws. Rewards are fixed, and the whole game can be played without paying.", "Parayla şans kutusu yok. Ödüller belli; oyunun tamamı para ödemeden oynanabilir.")}</p></div>
<div class="value"><div class="ic" style="background:#3f7fd0">{icon("leaf")}</div><h3>{t("A little meaning", "Biraz da anlam")}</h3>
<p>{t("Gentle stories with something to say, like caring for nature and the places we share.", "Doğaya ve paylaştığımız yerlere özen göstermek gibi, söyleyecek bir sözü olan yumuşak hikâyeler.")}</p></div>
</div>
</div>
</section>

<section class="contact" id="contact" aria-labelledby="contact-h">
<div class="wrap">
<div class="contact-card">
{SPARK.format(c="a")}{SPARK.format(c="c")}
<p class="eyebrow" style="color:#ffc23d">{t("Contact", "İletişim")}</p>
<h2 id="contact-h">{t("Say hello!", "Merhaba deyin!")}</h2>
<p>{t("Questions, ideas, press or business: we read every message.", "Soru, öneri, basın ya da iş birliği: her mesajı okuyoruz.")}</p>
<a class="mail" href="{mail()}">{C.CONTACT_EMAIL}</a>
<p style="margin-top:-8px">{t("Press and business", "Basın ve iş birliği")}: <a href="{mail(None, C.PRESS_EMAIL)}" style="color:#fff;font-weight:800">{C.PRESS_EMAIL}</a></p>
<div class="links"><a href="{PAGES["presskit"][lang]}">{t("Reverdo press kit", "Reverdo basın kiti")}</a><a href="{PAGES["support"][lang]}">{t("Player support", "Oyuncu desteği")}</a></div>
</div>
</div>
</section>
"""
    ld = {"@context": "https://schema.org", "@graph": [
        ORG,
        {"@type": "WebSite", "@id": C.SITE_URL + "/#site", "url": C.SITE_URL + "/", "name": "Kaotic Production",
         "publisher": {"@id": C.SITE_URL + "/#org"}, "inLanguage": ["en", "tr"]},
    ]}
    title = t("Kaotic Production · Fun, colourful, meaningful games", "Kaotic Production · Eğlenceli, renkli, anlamlı oyunlar")
    desc = t("Kaotic Production is an independent game studio from Istanbul making fun, colourful, meaningful games. Our first game: Reverdo.",
             "Kaotic Production, İstanbul'dan eğlenceli, renkli ve anlamlı oyunlar yapan bağımsız bir oyun stüdyosu. İlk oyunumuz: Reverdo.")
    return page(lang, "home", "studio", title, desc, "/assets/img/og-studio.jpg", body, jsonld=ld)


# ================================================================== REVERDO
def faq_items(lang):
    t = T(lang)
    rel = RELEASE[lang]
    p = PAGES
    req = t(
        """<div class="table-scroll"><table class="spec"><thead><tr><th scope="col"></th><th scope="col">Minimum</th><th scope="col">Recommended</th></tr></thead><tbody>
<tr><th scope="row">OS</th><td>Windows 10 64-bit</td><td>Windows 10/11 64-bit</td></tr>
<tr><th scope="row">Processor</th><td>Dual-core 2.5 GHz</td><td>Quad-core 3.0 GHz</td></tr>
<tr><th scope="row">Memory</th><td>4 GB RAM</td><td>8 GB RAM</td></tr>
<tr><th scope="row">Graphics</th><td>OpenGL 3.3, 1 GB VRAM (Intel HD 520 / GT 730 / R7 240)</td><td>2 GB VRAM (GTX 960 / RX 560 / Iris Xe)</td></tr>
<tr><th scope="row">Storage</th><td>1 GB</td><td>1 GB (SSD recommended)</td></tr></tbody></table></div>""",
        """<div class="table-scroll"><table class="spec"><thead><tr><th scope="col"></th><th scope="col">En düşük</th><th scope="col">Önerilen</th></tr></thead><tbody>
<tr><th scope="row">İşletim sistemi</th><td>Windows 10 64-bit</td><td>Windows 10/11 64-bit</td></tr>
<tr><th scope="row">İşlemci</th><td>Çift çekirdek 2,5 GHz</td><td>Dört çekirdek 3,0 GHz</td></tr>
<tr><th scope="row">Bellek</th><td>4 GB RAM</td><td>8 GB RAM</td></tr>
<tr><th scope="row">Ekran kartı</th><td>OpenGL 3.3, 1 GB (Intel HD 520 / GT 730 / R7 240)</td><td>2 GB (GTX 960 / RX 560 / Iris Xe)</td></tr>
<tr><th scope="row">Depolama</th><td>1 GB</td><td>1 GB (SSD önerilir)</td></tr></tbody></table></div>""")
    return [
        (t("When does Reverdo come out?", "Reverdo ne zaman çıkıyor?"),
         t(f"<p>Reverdo launches in Türkiye on iPhone and Android in early December 2026, then worldwide on Steam, the App Store and Google Play in January 2027.</p>",
           f"<p>Reverdo, Aralık 2026 başında Türkiye'de iPhone ve Android'de çıkıyor. Ocak 2027'de ise tüm dünyada Steam, App Store ve Google Play'de.</p>")),
        (t("Which platforms is it on?", "Hangi platformlarda var?"),
         t("<p>Windows PC on Steam, iPhone and iPad on the App Store, and Android phones and tablets on Google Play. On PC it is Windows only for now.</p>",
           "<p>Steam'de Windows bilgisayar, App Store'da iPhone ve iPad, Google Play'de Android telefon ve tabletler. Bilgisayarda şimdilik yalnızca Windows.</p>")),
        (t("How much does it cost?", "Fiyatı ne kadar?"),
         t(f"<p><strong>Steam: {C.STEAM_PRICE_EN}, buy once.</strong> No ads and no in-app purchases; everything is earned by playing.</p><p><strong>Phones: free to play.</strong> It offers optional in-app purchases (gem packs, machine packs, the Green Pass, and Reverdo Pro to play without ads) and contains ads: optional rewarded ads and one ad when a map is finished. The whole game can be played without buying anything.</p>",
           f"<p><strong>Steam: {C.STEAM_PRICE}, bir kez alırsın.</strong> Reklam yok, uygulama içi satın alma yok; her şey oynayarak kazanılır.</p><p><strong>Telefon: ücretsiz.</strong> İsteğe bağlı uygulama içi satın almalar (elmas paketleri, makine paketleri, Yeşil Pass, reklamsız oynamak için Reverdo Pro) ve reklamlar içerir: isteğe bağlı ödüllü reklamlar ve her harita bitince tek bir ara reklam. Oyunun tamamı satın alma yapmadan oynanabilir.</p>")),
        (t("Which languages does it support?", "Hangi dilleri destekliyor?"),
         t(f"<p>11 languages: {LANGS['en']}. You can pick one in Settings.</p>", f"<p>11 dil: {LANGS['tr']}. Ayarlar'dan seçilir.</p>")),
        (t("Can I play offline?", "İnternetsiz oynanır mı?"),
         t("<p>Yes. Reverdo plays offline and needs no account. On phones, the optional ads and purchases need a connection.</p>",
           "<p>Evet. Reverdo internetsiz oynanır ve hesap gerektirmez. Telefonda isteğe bağlı reklamlar ve satın almalar için bağlantı gerekir.</p>")),
        (t("Is it suitable for children?", "Çocuklar için uygun mu?"),
         t(f"<p>Reverdo is made for all ages: no violence, no chat and no account. On phones the game asks for a birth year once, on first launch. Players under 13 get a parent question before every real-money purchase and only see non-personalised, age-appropriate ads. Details are in the <a href=\"{p['privacy']['en']}\">privacy policy</a>.</p>",
           f"<p>Reverdo her yaşa uygun: şiddet yok, sohbet yok, hesap gerekmiyor. Telefonda oyun ilk açılışta doğum yılını bir kez sorar. 13 yaş altında gerçek parayla yapılan her satın almadan önce ebeveyn sorusu çıkar; çocuklara yalnızca kişiselleştirilmemiş ve yaşa uygun reklam gösterilir. Ayrıntılar <a href=\"{p['privacy']['tr']}\">gizlilik politikasında</a>.</p>")),
        (t("Can I use a controller?", "Oyun koluyla oynanır mı?"),
         t("<p>On PC you can play with keyboard or a controller, with rebindable keys. On phones and tablets there are touch controls.</p>",
           "<p>Bilgisayarda klavye ya da oyun koluyla oynayabilirsin; tuşlar değiştirilebilir. Telefon ve tablette dokunmatik kontroller var.</p>")),
        (t("What are the PC system requirements?", "Bilgisayar sistem gereksinimleri neler?"), req),
        (t("Are there accessibility options?", "Erişilebilirlik seçenekleri var mı?"),
         t("<p>Yes: colour-blind-friendly markers, reduced motion and slow reading. On phones there are also large buttons and a left-handed layout.</p>",
           "<p>Evet: renk körlüğü dostu işaretler, hareketi azaltma ve yavaş okuma. Telefonda ayrıca büyük düğmeler ve solak düzen var.</p>")),
        (t("I need help with the game.", "Oyunla ilgili yardıma ihtiyacım var."),
         t(f"<p>Visit the <a href=\"{p['support']['en']}\">support page</a> or write to <a href=\"{mail()}\">{C.CONTACT_EMAIL}</a>.</p>",
           f"<p><a href=\"{p['support']['tr']}\">Destek sayfasına</a> bakın ya da <a href=\"{mail()}\">{C.CONTACT_EMAIL}</a> adresine yazın.</p>")),
    ]


def trailer_box(lang, cls=""):
    t = T(lang)
    yt = (C.YOUTUBE_ID_TR or C.YOUTUBE_ID_EN) if lang == "tr" else C.YOUTUBE_ID_EN
    poster = pic(f"trailer-poster-{lang}", t("Reverdo trailer poster: the beach before and after cleaning", "Reverdo fragman kapağı: sahilin temizlikten önceki ve sonraki hâli"), "(min-width: 1240px) 1180px, 100vw")
    if yt:
        return (f'<div class="trailer {cls}" data-yt="{E(yt)}" data-title="{t("Reverdo trailer", "Reverdo fragmanı")}">{poster}'
                f'<button type="button" aria-label="{t("Play the trailer (loads YouTube)", "Fragmanı oynat (YouTube yüklenir)")}"><span class="play">{icon("playfill")}</span></button>'
                f'<p class="note">{t("Playing loads the video from YouTube (youtube-nocookie.com).", "Oynatınca video YouTube’dan (youtube-nocookie.com) yüklenir.")}</p></div>')
    return (f'<div class="trailer {cls}">{poster}<span class="soon">{icon("youtube")}{t("Trailer coming soon on YouTube", "Fragman yakında YouTube’da")}</span></div>')


def reverdo(lang):
    t = T(lang)
    tr = lang == "tr"
    rel = RELEASE[lang]
    p = PAGES
    maps_tags = "".join(f"<li>{E(m[tr])}</li>" for m in MAPS) + "".join(f'<li class="star">{E(m[tr])}</li>' for m in LANDMARKS)
    gallery_items = [("shot-01-before-after-coast", SHOT_ALT["01-before-after-coast"][tr], True)]
    for s in ["05-taj-mahal", "02-paris-ada", "03-sultanahmet", "06-octopus-grab", "07-giza", "04-tour-boat",
              "08-ice-cream-van", "09-mine-cart", "10-eiffel-tower"]:
        gallery_items.append(("shot-" + s, SHOT_ALT[s][tr], False))
    for st in ["concert", "swans", "fountain", "submarine", "campus-caps"]:
        gallery_items.append(("still-" + st, STILL_ALT[st][tr], False))
    gal = ""
    for name, alt, wide in gallery_items:
        li = '<li class="wide">' if wide else "<li>"
        gal += (f'{li}<a href="/assets/img/{name}-1920.jpg" data-full="/assets/img/{name}-1920.webp">'
                f'{pic(name, alt, "(min-width: 1240px) 780px, (min-width: 720px) 66vw, 100vw" if wide else "(min-width: 1240px) 380px, (min-width: 720px) 33vw, 50vw", maxw=1280)}</a></li>')
    faq = "".join(f"<details><summary>{q}</summary><div>{a}</div></details>" for q, a in faq_items(lang))

    body = f"""
<section class="g-hero" aria-labelledby="hero-h">
<div class="media">
{pic("hero-poster", "", "100vw", lazy=False, high=True)}
<video data-hero muted loop playsinline preload="none" aria-hidden="true" tabindex="-1" data-xl="/assets/video/reverdo-hero-1440" data-large="/assets/video/reverdo-hero-1080" data-small="/assets/video/reverdo-hero-720" poster="/assets/img/hero-poster-1920.jpg"></video>
</div>
<div class="wrap inner">
{pic("reverdo-wordmark", "Reverdo", "(min-width: 900px) 560px, 92vw", cls="logo", lazy=False)}
<h1 id="hero-h">{t("Clean it up, watch it bloom.", "Temizle, yeniden yeşert.")}</h1>
<p class="sub">{t("Clean up grey, littered places and watch every corner turn green again! 20 maps from a beach to Istanbul's Sultanahmet, the Eiffel Tower and the Taj Mahal. A calm, colourful cleanup game for all ages.",
                  "Gri ve çöplerle dolu yerleri temizle, her köşenin yeniden yeşerdiğini izle! Sahilden Sultanahmet'e, Eyfel Kulesi'nden Tac Mahal'e 20 harita. Sakin, renkli ve her yaşa uygun bir temizlik oyunu.")}</p>
<div class="when"><span class="chip sun">{rel[0]}</span><span class="chip">{rel[1]}</span></div>
{stores(lang)}
</div>
<button class="media-ctl" type="button" hidden data-play="{t("Play background video", "Arka plan videosunu oynat")}" data-pause="{t("Pause background video", "Arka plan videosunu durdur")}"><span class="i-pause">{icon("pause")}</span><span class="i-play" style="display:none">{icon("playfill")}</span><span class="lbl">{t("Pause background video", "Arka plan videosunu durdur")}</span></button>
</section>

<div class="ribbon"><div class="wrap"><ul>
<li>{icon("map")} {t("20 maps", "20 harita")}</li><li>{icon("users")} {t("Play as Ada or Ege", "Ada ya da Ege ile oyna")}</li>
<li>{icon("lang")} {t("11 languages", "11 dil")}</li><li>{icon("heart")} {t("For all ages", "Her yaşa uygun")}</li><li>{icon("offline")} {t("Plays offline", "İnternetsiz oynanır")}</li>
</ul></div></div>

<section class="g-section" id="trailer" aria-labelledby="trailer-h">
<div class="wrap">
<div class="head center"><p class="eyebrow">{t("Trailer", "Fragman")}</p><h2 id="trailer-h">{t("From grey to green in one minute", "Bir dakikada griden yeşile")}</h2></div>
{trailer_box(lang)}
</div>
</section>

<section class="g-section alt" id="features" aria-label="{t("Features", "Özellikler")}">
<div class="wrap rows">

<div class="row">
<div class="text">
<p class="eyebrow">{t("Clean &amp; green", "Temizle ve yeşert")}</p>
<h2>{t("Every corner comes back to life", "Temizlediğin her köşe canlanıyor")}</h2>
<p>{t("A grey beach buried in litter… Grab your vacuum and start cleaning! Every corner you clear comes back to life: grass grows, flowers bloom, birds return and people come back to the park.",
      "Gri ve çöplerle dolu bir sahil… Süpürgeni al ve temizlemeye başla! Temizlediğin her köşe yeniden canlanıyor: çimen çıkıyor, çiçekler açıyor, kuşlar geri geliyor, insanlar parka dönüyor.")}</p>
<p>{t("When a map is 100% clean, a short before/after film shows how far it has come. Save and share the before/after picture.",
      "Harita %100 temiz olunca kısa bir önce/sonra filmi ne kadar değiştiğini gösteriyor. Önce/sonra resmini kaydet ve paylaş.")}</p>
</div>
<div class="shot">{pic("shot-01-before-after-coast", SHOT_ALT["01-before-after-coast"][tr], "(min-width: 900px) 620px, 100vw")}
{pic("still-coast-green", STILL_ALT["coast-green"][tr], "(min-width: 900px) 280px, 44vw", cls="float", maxw=1280)}</div>
</div>

<div class="row flip" id="maps">
<div class="text">
<p class="eyebrow">{t("World tour", "Dünya turu")}</p>
<h2>{t("20 maps, from the beach to the pyramids", "20 harita: sahilden piramitlere")}</h2>
<p>{t("Start on a grey beach, then clean a funfair, a train station, a forest pond, an underwater habitat and an ancient mine, all the way to world landmarks: Istanbul's Sultanahmet Square, the Eiffel Tower, the Pyramids of Giza and the Taj Mahal. Every map has its own music, ambience, people and little stories.",
      "Gri bir sahilden başla; lunaparkı, tren istasyonunu, orman göletini, sualtı habitatını ve antik madeni temizle, dünyanın simge yerlerine kadar git: Sultanahmet Meydanı, Eyfel Kulesi, Giza Piramitleri ve Tac Mahal. Her haritanın kendi müziği, ortam sesleri, insanları ve küçük hikâyeleri var.")}</p>
<ul class="tags" aria-label="{t("All 20 maps", "20 haritanın hepsi")}">{maps_tags}</ul>
</div>
<div class="mosaic">
<figure>{pic("still-sultanahmet-park", STILL_ALT["sultanahmet-park"][tr], "(min-width: 900px) 320px, 46vw", maxw=1280)}<figcaption>{LANDMARKS[0][tr]}</figcaption></figure>
<figure>{pic("shot-10-eiffel-tower", SHOT_ALT["10-eiffel-tower"][tr], "(min-width: 900px) 320px, 46vw", maxw=1280)}<figcaption>{LANDMARKS[1][tr]}</figcaption></figure>
<figure>{pic("shot-07-giza", SHOT_ALT["07-giza"][tr], "(min-width: 900px) 320px, 46vw", maxw=1280)}<figcaption>{LANDMARKS[2][tr]}</figcaption></figure>
<figure>{pic("shot-05-taj-mahal", SHOT_ALT["05-taj-mahal"][tr], "(min-width: 900px) 320px, 46vw", maxw=1280)}<figcaption>{LANDMARKS[3][tr]}</figcaption></figure>
</div>
</div>

<div class="row">
<div class="text">
<p class="eyebrow">{t("Your hero", "Kahramanın")}</p>
<h2>{t("Play as Ada or Ege", "Ada ya da Ege ile oyna")}</h2>
<p>{t("Dress Ada or Ege with hats, outfits, colourful vacuums and trails. Holidays and seasonal events decorate the maps.",
      "Ada'yı ya da Ege'yi şapkalar, kıyafetler, renkli süpürgeler ve izlerle giydir. Bayramlarda ve mevsim etkinliklerinde haritalar süsleniyor.")}</p>
<p>{t("Find historic artifacts hidden across the maps, complete the sets, unlock costumes, and turn what you collect into benches, birdhouses and solar lamps.",
      "Haritalarda saklı tarihi eserleri bul, setleri tamamla, kostümleri aç; topladığın malzemelerle bank, kuş evi ve güneş enerjili lamba yap.")}</p>
</div>
<div class="duo">
<figure class="ada">{pic("portrait-ada", t("Ada celebrating in the Taj Mahal gardens", "Ada, Tac Mahal bahçesinde kutlama yapıyor"), "(min-width: 900px) 300px, 46vw")}<figcaption>Ada</figcaption></figure>
<figure class="ege">{pic("portrait-ege", t("Ege celebrating in front of the Eiffel Tower", "Ege, Eyfel Kulesi'nin önünde kutlama yapıyor"), "(min-width: 900px) 300px, 46vw")}<figcaption>Ege</figcaption></figure>
</div>
</div>

<div class="row flip">
<div class="text">
<p class="eyebrow">{t("Machines", "Makineler")}</p>
<h2>{t("Machines for the big jobs", "Büyük işler için makineler")}</h2>
<p>{t("Upgrade your vacuum and grow your bag. For heavy work, take the controls. Machines gain new parts as they level up, and you can see it.",
      "Süpürgeni güçlendir, çantanı büyüt. Ağır işlerde makinenin başına geç. Makineler seviye atladıkça yeni parçalar kazanıyor ve bu görünüyor.")}</p>
<ul class="tags">
<li>{t("Octopus-grab excavator", "Ahtapot kepçeli iş makinesi")}</li><li>Clean-Bot</li><li>{t("Push scrubber", "İtmeli süpürge")}</li><li>{t("Sponge mop", "Süngerli paspas")}</li>
<li>{t("Sea-cleaning boat", "Deniz temizleme teknesi")}</li><li>{t("Cleanup submarine", "Temizlik denizaltısı")}</li><li>{t("Metal detector", "Metal dedektörü")}</li></ul>
</div>
<div class="shot">{pic("shot-06-octopus-grab", SHOT_ALT["06-octopus-grab"][tr], "(min-width: 900px) 620px, 100vw")}
{pic("still-submarine", STILL_ALT["submarine"][tr], "(min-width: 900px) 280px, 44vw", cls="float", maxw=1280)}</div>
</div>

<div class="row">
<div class="text">
<p class="eyebrow">{t("Life returns", "Hayat geri dönüyor")}</p>
<h2>{t("Grandpa Tosbi and animal friends", "Tosbi Dede ve hayvan dostları")}</h2>
<p>{t("Tosbi, a wise old sea turtle, travels with you. Free a hedgehog caught in plastic rings or a turtle tangled in a net.",
      "Yaşlı deniz kaplumbağası Tosbi Dede yolculuk boyunca sana eşlik ediyor. Plastik halkalara takılmış kirpiyi, ağa dolanmış kaplumbağayı kurtar.")}</p>
<p>{t("As the maps get cleaner they fill with life: swans return to the pond, an ice-cream van visits the park, a tour boat sails past the beach and an excursion train pulls into the station.",
      "Haritalar temizlendikçe hayat doluyor: kuğular göle dönüyor, parka dondurma arabası geliyor, sahilin önünden tur teknesi geçiyor, istasyona gezi treni yanaşıyor.")}</p>
</div>
<div class="shot">{pic("still-swans", STILL_ALT["swans"][tr], "(min-width: 900px) 620px, 100vw")}
{pic("still-ice-cream", STILL_ALT["ice-cream"][tr], "(min-width: 900px) 280px, 44vw", cls="float", maxw=1280)}</div>
</div>

<div class="row flip">
<div class="text">
<p class="eyebrow">{t("Living maps", "Canlı haritalar")}</p>
<h2>{t("Storms, crises and big moments", "Fırtınalar, krizler ve büyük anlar")}</h2>
<ul class="ticks">
<li>{t("Crises: a tipped oil cart, spilled rubble, gulls raiding the bins. Beat the clock!", "Krizler: devrilen yağ arabası, dökülen moloz, çöpe dalan martılar. Süre bitmeden yetiş!")}</li>
<li>{t("Rain, the lodos wind and desert sandstorms: the wind blows fresh litter onto ground you've cleaned.", "Sağanak, lodos ve çölde kum fırtınası: rüzgâr temizlediğin yerlere yeni çöp taşıyor.")}</li>
<li>{t("Signature moments: a fountain show in the park, fireworks at the funfair, fireflies at the camp, baby turtles on the beach.", "İmza anları: parkta su gösterisi, lunaparkta havai fişek, kampta ateş böcekleri, sahilde yavru kaplumbağalar.")}</li>
<li>{t("Something every day: a daily cleanup, a login streak, weekly events and seasonal decorations.", "Her gün bir şey: günün temizliği, giriş serisi, haftalık etkinlikler ve mevsim süsleri.")}</li>
</ul>
</div>
<div class="shot">{pic("still-concert", STILL_ALT["concert"][tr], "(min-width: 900px) 620px, 100vw")}
{pic("shot-04-tour-boat", SHOT_ALT["04-tour-boat"][tr], "(min-width: 900px) 280px, 44vw", cls="float", maxw=1280)}</div>
</div>

</div>
</section>

<section class="g-section" id="family" aria-labelledby="family-h">
<div class="wrap">
<div class="head center"><p class="eyebrow">{t("For all ages", "Her yaşa uygun")}</p><h2 id="family-h">{t("Made for the whole family", "Bütün aile için")}</h2>
<p class="lead" style="margin:0 auto">{t("A calm game you can hand to anyone, from kids to grandparents.", "Çocuktan dedeye herkesin eline gönül rahatlığıyla verebileceğin sakin bir oyun.")}</p></div>
<div class="cards three">
<div class="card"><div class="ic">{icon("chat")}</div><h3>{t("No violence, no chat", "Şiddet yok, sohbet yok")}</h3><p>{t("Nothing scary and no strangers to talk to. No account needed.", "Korkutucu bir şey yok, yabancılarla konuşma yok. Hesap gerekmiyor.")}</p></div>
<div class="card"><div class="ic sky">{icon("offline")}</div><h3>{t("Plays offline", "İnternetsiz oynanır")}</h3><p>{t("No connection needed to play. Your progress stays on your own device.", "Oynamak için internet gerekmez. İlerlemen kendi cihazında kalır.")}</p></div>
<div class="card"><div class="ic sun">{icon("shield")}</div><h3>{t("Age-appropriate", "Yaşa uygun")}</h3><p>{t("On phones the game asks for a birth year once. Under-13s get a parent question before every real-money purchase and only see non-personalised, age-appropriate ads.", "Telefonda oyun doğum yılını bir kez sorar. 13 yaş altında gerçek parayla yapılan her satın almadan önce ebeveyn sorusu çıkar; yalnızca kişiselleştirilmemiş, yaşa uygun reklam gösterilir.")}</p></div>
<div class="card"><div class="ic berry">{icon("eye")}</div><h3>{t("Accessible", "Erişilebilir")}</h3><p>{t("Colour-blind-friendly markers, reduced motion and slow reading. On phones: large buttons and a left-handed layout.", "Renk körlüğü dostu işaretler, hareketi azaltma ve yavaş okuma. Telefonda büyük düğmeler ve solak düzen.")}</p></div>
<div class="card"><div class="ic sun">{icon("gift")}</div><h3>{t("Fair rewards", "Adil ödüller")}</h3><p>{t("Green Pass rewards are fixed, with no random drops. The whole game can be played without buying anything.", "Yeşil Pass'ta ödüller sabit; şansa bağlı ödül yok. Oyunun tamamı satın alma yapmadan oynanabilir.")}</p></div>
<div class="card"><div class="ic sky">{icon("lang")}</div><h3>{t("11 languages", "11 dil")}</h3><p>{LANGS[lang]}.</p></div>
</div>
</div>
</section>

<section class="g-section alt" id="editions" aria-labelledby="ed-h">
<div class="wrap">
<div class="head center"><p class="eyebrow">{t("Two ways to play", "İki şekilde oyna")}</p><h2 id="ed-h">{t("Pick your edition", "Sürümünü seç")}</h2></div>
<div class="editions">
<div class="edition pc">
<div class="top">{icon("pc")}<h3>{t("Steam · Windows PC", "Steam · Windows bilgisayar")}</h3></div>
<p class="price">{t(C.STEAM_PRICE_EN + " · buy once, it's all yours", C.STEAM_PRICE + " · bir kez al, hepsi senin")}</p>
<ul class="ticks">
<li>{t("No ads and no in-app purchases", "Reklam yok, uygulama içi satın alma yok")}</li>
<li>{t("Everything is earned by playing; both tracks of the Green Pass unlock through play", "Her şey oynayarak kazanılır; Yeşil Pass'ın iki şeridi de oynayarak açılır")}</li>
<li>{t("Keyboard and controller support, rebindable keys", "Klavye ve oyun kolu desteği, değiştirilebilir tuşlar")}</li>
<li>{t("Coming January 2027", "Ocak 2027'de geliyor")}</li>
</ul>
{stores(lang, light=True, only=["steam"])}
</div>
<div class="edition">
<div class="top">{icon("phone")}<h3>{t("iPhone, iPad &amp; Android", "iPhone, iPad ve Android")}</h3></div>
<p class="price">{t("Free to play", "Ücretsiz")}</p>
<ul class="ticks">
<li>{t("Touch controls made for phones: joystick, Sweep and Run buttons", "Telefon için dokunmatik kontroller: joystick, Süpür ve Koş düğmeleri")}</li>
<li>{t("Optional purchases: gem packs, machine packs, the Green Pass and Reverdo Pro", "İsteğe bağlı satın almalar: elmas paketleri, makine paketleri, Yeşil Pass ve Reverdo Pro")}</li>
<li>{t("Optional rewarded ads and one ad when a map is finished; Reverdo Pro removes the between-map ads", "İsteğe bağlı ödüllü reklamlar ve harita bitince tek bir ara reklam; Reverdo Pro ara reklamları kaldırır")}</li>
<li>{t("Türkiye: early December 2026 · worldwide: January 2027", "Türkiye: Aralık 2026 başı · tüm dünya: Ocak 2027")}</li>
</ul>
{stores(lang, light=True, only=["appstore", "play"])}
</div>
</div>
</div>
</section>

<section class="g-section deep" id="gallery" aria-labelledby="gal-h">
<div class="wrap">
<div class="head"><p class="eyebrow">{t("Screenshots", "Ekran görüntüleri")}</p><h2 id="gal-h">{t("Take a look around", "Biraz etrafa bak")}</h2>
<p class="muted">{t("All images are taken from the game. Tap one to see it larger.", "Görüntülerin hepsi oyunun kendisinden. Büyük görmek için birine dokun.")}</p></div>
<ul class="gallery" data-lightbox>{gal}</ul>
</div>
</section>

<section class="g-section" id="faq" aria-labelledby="faq-h">
<div class="wrap">
<div class="head center"><p class="eyebrow">{t("FAQ", "SSS")}</p><h2 id="faq-h">{t("Questions & answers", "Sık sorulan sorular")}</h2></div>
<div class="faq">{faq}</div>
</div>
</section>

<section class="g-section alt closing" aria-labelledby="end-h">
<div class="wrap">
{pic("reverdo-badge", "", "132px", cls="badge", maxw=256)}
<h2 id="end-h">{t("Make the world green!", "Dünyayı yeşert!")}</h2>
<p class="lead" style="margin:0 auto">{t("Coming January 2027 to Steam, the App Store and Google Play. In Türkiye, on phones from early December 2026.", "Ocak 2027'de Steam, App Store ve Google Play'de. Türkiye'de telefonlarda Aralık 2026 başından itibaren.")}</p>
{stores(lang, light=True)}
<p style="margin-top:22px"><a href="{p["presskit"][lang]}">{t("Press kit", "Basın kiti")}</a> &middot; <a href="{mail("Reverdo")}">{C.CONTACT_EMAIL}</a></p>
</div>
</section>
"""
    lightbox = f"""<dialog class="lightbox" aria-label="{t("Screenshot viewer", "Görsel görüntüleyici")}">
<div class="lb-top"><span class="lb-count" aria-live="polite"></span><button class="close" type="button" aria-label="{t("Close", "Kapat")}">{icon("close")}</button></div>
<div class="stage"><img alt=""></div>
<button class="prev" type="button" aria-label="{t("Previous", "Önceki")}">{icon("prev")}</button>
<button class="next" type="button" aria-label="{t("Next", "Sonraki")}">{icon("next")}</button>
<p class="lb-cap"></p>
</dialog>
"""
    game_ld = {
        "@context": "https://schema.org",
        "@type": "VideoGame",
        "@id": C.SITE_URL + "/reverdo/#game",
        "name": "Reverdo",
        "alternateName": "Reverdo: Clean & Green" if not tr else "Reverdo: Dünyayı Yeşert",
        "url": C.SITE_URL + p["reverdo"][lang],
        "description": t("A calm, colourful cleanup game for all ages: clean up grey, littered places and watch every corner turn green again across 20 maps.",
                         "Her yaşa uygun, sakin ve renkli bir temizlik oyunu: gri ve çöplerle dolu yerleri temizle, 20 haritada her köşenin yeniden yeşerdiğini izle."),
        "image": [C.SITE_URL + "/assets/img/og-reverdo.jpg", C.SITE_URL + src("shot-01-before-after-coast", 1920, "jpg")],
        "screenshot": [C.SITE_URL + src("shot-" + s, 1920, "jpg") for s in ["01-before-after-coast", "02-paris-ada", "05-taj-mahal", "07-giza"]],
        "genre": ["Casual", "Simulation", "Cleaning"],
        "gamePlatform": ["PC", "iOS", "Android"],
        "operatingSystem": "Windows 10, iOS, Android",
        "applicationCategory": "Game",
        "playMode": "SinglePlayer",
        "numberOfPlayers": {"@type": "QuantitativeValue", "value": 1},
        "inLanguage": ["en", "tr", "de", "es", "fr", "pt", "ru", "ja", "zh", "hi", "ar"],
        "author": {"@id": C.SITE_URL + "/#org"},
        "publisher": ORG,
        "audience": {"@type": "PeopleAudience", "suggestedMinAge": 3},
    }
    if C.YOUTUBE_ID_EN:
        game_ld["trailer"] = {"@type": "VideoObject", "name": "Reverdo trailer",
                              "embedUrl": "https://www.youtube-nocookie.com/embed/" + C.YOUTUBE_ID_EN,
                              "thumbnailUrl": C.SITE_URL + src("trailer-poster-en", 1920, "jpg"),
                              "description": "Reverdo trailer", "uploadDate": "2026-10-24"}
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": re.sub("<[^>]+>", "", q),
         "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", a)).strip()}}
        for q, a in faq_items(lang) if "table" not in a]}
    title = t("Reverdo · Clean it up, watch it bloom", "Reverdo · Temizle, yeniden yeşert")
    desc = t("Clean up grey, littered places and watch every corner turn green again! 20 maps from a beach to Sultanahmet, the Eiffel Tower and the Taj Mahal. Coming January 2027 to Steam, iOS and Android.",
             "Gri ve çöplerle dolu yerleri temizle, her köşenin yeniden yeşerdiğini izle! Sahilden Sultanahmet'e, Eyfel'den Tac Mahal'e 20 harita. Ocak 2027'de Steam, iOS ve Android'de.")
    return page(lang, "reverdo", "game", title, desc, "/assets/img/og-reverdo.jpg", body, overlay=True,
                jsonld=[game_ld, faq_ld], extra_body=lightbox)


# ================================================================== PRESS KIT
def presskit(lang):
    t = T(lang)
    tr = lang == "tr"
    p = PAGES
    zip_path = os.path.join(ROOT, "reverdo", "presskit", "reverdo-presskit.zip")
    zmb = os.path.getsize(zip_path) / 1e6 if os.path.exists(zip_path) else 0
    zsize = (f"{zmb:.0f} MB" if not tr else f"{zmb:.0f} MB")
    shots = ""
    for s in ["01-before-after-coast", "02-paris-ada", "03-sultanahmet", "04-tour-boat", "05-taj-mahal",
              "06-octopus-grab", "07-giza", "08-ice-cream-van", "09-mine-cart", "10-eiffel-tower"]:
        shots += (f'<li><a href="/assets/img/shot-{s}-1920.jpg" download="reverdo-{s}.jpg">'
                  f'{pic("shot-" + s, SHOT_ALT[s][tr], "(min-width: 960px) 260px, 46vw", maxw=640)}'
                  f'{SHOT_LABEL[s][tr]} · 1920×1080</a></li>')
    files = "/reverdo/presskit/files/"
    logos = [
        ("reverdo-logo-wordmark.png", "/assets/img/reverdo-wordmark-400.webp", t("Reverdo logo (transparent PNG)", "Reverdo logosu (saydam PNG)"), ""),
        ("reverdo-logo-badge.png", "/assets/img/reverdo-badge-256.webp", t("Reverdo badge (PNG, 1024 px)", "Reverdo rozeti (PNG, 1024 px)"), ""),
        ("reverdo-icon-512.png", "/assets/img/reverdo-icon-192.webp", t("App icon (PNG, 512 px)", "Uygulama simgesi (PNG, 512 px)"), ""),
        ("kaotic-logo-dark-bg.svg", "/assets/brand/kaotic-logo-dark-bg.svg", t("Kaotic Production logo, for dark backgrounds (SVG)", "Kaotic Production logosu, koyu zemin için (SVG)"), " darkbg"),
        ("kaotic-logo-light-bg.svg", "/assets/brand/kaotic-logo-light-bg.svg", t("Kaotic Production logo, for light backgrounds (SVG)", "Kaotic Production logosu, açık zemin için (SVG)"), ""),
        ("kaotic-emblem.svg", "/assets/brand/kaotic-emblem.svg", t("Kaotic Production emblem (SVG; PNG up to 2048 px in the ZIP)", "Kaotic Production amblemi (SVG; 2048 px'e kadar PNG'ler ZIP'te)"), " darkbg"),
        ("kaotic-logo-white.svg", "/assets/brand/kaotic-logo-white.svg", t("Logo, white (SVG)", "Logo, beyaz (SVG)"), " darkbg"),
        ("kaotic-logo-black.svg", "/assets/brand/kaotic-logo-black.svg", t("Logo, black (SVG)", "Logo, siyah (SVG)"), ""),
        ("kaotic-favicon.svg", "/assets/brand/kaotic-favicon.svg", t("App icon / favicon (SVG)", "Uygulama simgesi / favicon (SVG)"), ""),
    ]
    logo_html = "".join(f'<li class="logo-tile{c}"><a href="{files}{f}" download><img src="{prev}" alt="" loading="lazy">{label}</a></li>' for f, prev, label, c in logos)
    art = [("reverdo-keyart-3840x1240.jpg", "keyart", t("Key art, no text (3840×1240)", "Ana görsel, yazısız (3840×1240)")),
           ("reverdo-capsule-920x430.jpg", None, t("Capsule with logo (920×430)", "Logolu kapsül (920×430)")),
           ("reverdo-capsule-600x900.jpg", None, t("Vertical capsule (600×900)", "Dikey kapsül (600×900)"))]
    art_html = ""
    for f, preview, label in art:
        im = pic(preview, "", "(min-width: 960px) 260px, 46vw", maxw=960) if preview else f'<img src="{files}{f}" alt="" loading="lazy" style="object-fit:contain;background:#1d4426">'
        art_html += f'<li><a href="{files}{f}" download>{im}{label}</a></li>'
    yt = C.YOUTUBE_ID_EN
    video = (f'<p><a href="https://www.youtube.com/watch?v={E(yt)}" rel="noopener">{t("Reverdo trailer on YouTube", "YouTube’da Reverdo fragmanı")}</a></p>' if yt
             else f'<p>{t("Trailer (about 1 minute, English and Turkish): coming soon on YouTube. Need it earlier? Write to us and we will send a download link.", "Fragman (yaklaşık 1 dakika, İngilizce ve Türkçe): yakında YouTube’da. Daha önce mi lazım? Bize yazın, indirme bağlantısı gönderelim.")}</p>')
    video += f'<p><a href="/assets/video/reverdo-hero-720.mp4" download="reverdo-gameplay-loop-720p.mp4">{t("Short gameplay loop (10 s, silent, 720p MP4)", "Kısa oynanış döngüsü (10 sn, sessiz, 720p MP4)")}</a></p>'

    body = f"""
<div class="wrap pk-head">
<p class="eyebrow">{t("Press kit", "Basın kiti")}</p>
<h1 style="font-size:clamp(2.2rem,5vw,3.6rem)">Reverdo</h1>
<p class="lead">{t("Everything you need to write about Reverdo: facts, text, screenshots, logos and contact. All images come from the game and may be used for coverage.",
                  "Reverdo hakkında yazmak için gereken her şey: bilgiler, metinler, ekran görüntüleri, logolar ve iletişim. Görsellerin hepsi oyunun kendisinden; haber ve yazılarda kullanılabilir.")}</p>
</div>
<div class="wrap pk-grid">
<aside class="factsheet" aria-labelledby="fs-h">
<h2 id="fs-h" style="font-size:1.3rem">{t("Factsheet", "Bilgi kartı")}</h2>
<dl>
<dt>{t("Developer &amp; publisher", "Geliştirici ve yayıncı")}</dt><dd>Kaotic Production<br><span class="muted">{t("Istanbul, Türkiye", "İstanbul, Türkiye")}</span></dd>
<dt>{t("Release date", "Çıkış tarihi")}</dt><dd>{t("Türkiye (iOS, Android): early December 2026", "Türkiye (iOS, Android): Aralık 2026 başı")}<br>{t("Worldwide (Steam, iOS, Android): January 2027", "Tüm dünya (Steam, iOS, Android): Ocak 2027")}</dd>
<dt>{t("Platforms", "Platformlar")}</dt><dd>Windows PC (Steam)<br>iPhone &amp; iPad (App Store)<br>Android (Google Play)</dd>
<dt>{t("Price", "Fiyat")}</dt><dd>{t(f"Steam: {C.STEAM_PRICE_EN}, no ads, no in-app purchases", f"Steam: {C.STEAM_PRICE}, reklamsız, uygulama içi satın almasız")}<br>{t("Mobile: free to play with optional in-app purchases", "Telefon: ücretsiz, isteğe bağlı uygulama içi satın almalar")}</dd>
<dt>{t("Genre", "Tür")}</dt><dd>{t("Casual, relaxing cleanup game", "Rahatlatıcı, sakin bir temizlik oyunu")}</dd>
<dt>{t("Players", "Oyuncu")}</dt><dd>{t("Single-player", "Tek oyunculu")}</dd>
<dt>{t("Languages", "Diller")}</dt><dd>{LANGS[lang]}</dd>
<dt>{t("Engine", "Oyun motoru")}</dt><dd>Godot 4</dd>
<dt>{t("Website", "Web sitesi")}</dt><dd><a href="{p["reverdo"][lang]}">kaoticproduction.com{p["reverdo"][lang]}</a></dd>
<dt>{t("Press contact", "Basın iletişimi")}</dt><dd><a href="{mail("Reverdo press", C.PRESS_EMAIL)}">{C.PRESS_EMAIL}</a></dd>
</dl>
<a class="btn" href="/reverdo/presskit/reverdo-presskit.zip" download>{icon("download")}{t("Download all", "Hepsini indir")} (ZIP, {zsize})</a>
</aside>
<div class="pk-main">
<ul class="pk-toc">
<li><a href="#description">{t("Description", "Tanıtım")}</a></li><li><a href="#history">{t("History", "Hikâyesi")}</a></li>
<li><a href="#features">{t("Features", "Özellikler")}</a></li><li><a href="#videos">{t("Videos", "Videolar")}</a></li>
<li><a href="#images">{t("Images", "Görseller")}</a></li><li><a href="#logos">{t("Logos", "Logolar")}</a></li>
<li><a href="#team">{t("Team", "Ekip")}</a></li><li><a href="#contact">{t("Contact", "İletişim")}</a></li></ul>

<section id="description"><h2>{t("Description", "Tanıtım")}</h2>
<p>{t("<strong>Reverdo</strong> is a calm, colourful cleanup game where you collect and recycle litter to make the world green again.",
      "<strong>Reverdo</strong>, çöpleri toplayıp geri dönüştürerek dünyayı yeniden yeşerttiğin sakin, renkli ve keyifli bir temizlik oyunu.")}</p>
<p>{t("A grey beach buried in litter… Grab your vacuum and start cleaning! Every corner you clear comes back to life: grass grows, flowers bloom, birds return and people come back to the park. When a map is 100% clean, a short before/after film shows how far it has come. From a beach to Istanbul's Sultanahmet Square, the Eiffel Tower, the Pyramids of Giza and the Taj Mahal, players clean 20 maps with their own music, people and little stories.",
      "Gri ve çöplerle dolu bir sahil… Süpürgeni al ve temizlemeye başla! Temizlediğin her köşe yeniden canlanıyor: çimen çıkıyor, çiçekler açıyor, kuşlar geri geliyor, insanlar parka dönüyor. Harita %100 temiz olunca kısa bir önce/sonra filmi ne kadar değiştiğini gösteriyor. Sahilden Sultanahmet Meydanı'na, Eyfel Kulesi'nden Giza Piramitleri'ne ve Tac Mahal'e kadar, her birinin kendi müziği, insanları ve küçük hikâyeleri olan 20 harita temizleniyor.")}</p>
</section>

<section id="history"><h2>{t("History", "Hikâyesi")}</h2>
<p>{t("Reverdo started in 2026 as a small 2D prototype about cleaning up a beach, called <em>Kıyı</em> (Turkish for “shore”). As it grew into a 3D game that travels from a beach to world landmarks, it was renamed Reverdo: “re” (again) + “verde” (green), a place turning green again. It is the first game by Kaotic Production, an independent studio from Istanbul founded by Ufuk Pamuk.",
      "Reverdo, 2026'da bir sahili temizlemeyi anlatan <em>Kıyı</em> adlı küçük bir 2D prototip olarak başladı. Sahilden dünyanın simge yerlerine uzanan bir 3D oyuna dönüşünce adı Reverdo oldu: “re” (yeniden) + “verde” (yeşil), yani yeniden yeşeren yer. Ufuk Pamuk'un İstanbul'da kurduğu bağımsız stüdyo Kaotic Production'ın ilk oyunu.")}</p>
</section>

<section id="features"><h2>{t("Features", "Özellikler")}</h2>
<ul class="ticks">
<li>{t("Clean up litter and watch grey places turn green, with a before/after film at the end of every map", "Çöpleri topla, gri yerlerin yeşermesini izle; her haritanın sonunda önce/sonra filmi")}</li>
<li>{t("20 maps, including Sultanahmet Square, the Eiffel Tower, the Pyramids of Giza and the Taj Mahal", "Sultanahmet Meydanı, Eyfel Kulesi, Giza Piramitleri ve Tac Mahal dahil 20 harita")}</li>
<li>{t("Play as Ada or Ege, with hats, outfits, colourful vacuums and trails", "Şapkalar, kıyafetler, renkli süpürgeler ve izlerle Ada ya da Ege olarak oyna")}</li>
<li>{t("Machines that level up: octopus-grab excavator, Clean-Bot, push scrubber, sponge mop, sea-cleaning boat, cleanup submarine and metal detector", "Seviye atlayan makineler: ahtapot kepçe, Clean-Bot, itmeli süpürge, süngerli paspas, deniz temizleme teknesi, temizlik denizaltısı ve metal dedektörü")}</li>
<li>{t("Living maps: tour boats, ice-cream vans, crises, rain, the lodos wind and desert sandstorms", "Canlı haritalar: tur tekneleri, dondurma arabaları, krizler, sağanak, lodos ve kum fırtınası")}</li>
<li>{t("Grandpa Tosbi the sea turtle, animals to rescue, historic artifacts to collect and upcycling", "Deniz kaplumbağası Tosbi Dede, kurtarılacak hayvanlar, toplanacak tarihi eserler ve ileri dönüşüm")}</li>
<li>{t("For all ages: no violence, no chat, no account; plays offline", "Her yaşa uygun: şiddet yok, sohbet yok, hesap yok; internetsiz oynanır")}</li>
<li>{t("Accessibility: colour-blind-friendly markers, reduced motion, slow reading", "Erişilebilirlik: renk körlüğü dostu işaretler, hareketi azaltma, yavaş okuma")}</li>
<li>{t("11 languages", "11 dil")}</li>
</ul>
</section>

<section id="videos"><h2>{t("Videos", "Videolar")}</h2>
{trailer_box(lang)}
<div style="margin-top:16px">{video}</div>
</section>

<section id="images"><h2>{t("Images", "Görseller")}</h2>
<p><a href="/reverdo/presskit/reverdo-presskit.zip" download>{t("Download all screenshots, art and logos as a ZIP", "Tüm ekran görüntülerini, görselleri ve logoları ZIP olarak indir")} ({zsize})</a></p>
<ul class="dl-grid">{shots}</ul>
<h3 style="margin-top:28px">{t("Key art", "Ana görseller")}</h3>
<ul class="dl-grid">{art_html}</ul>
</section>

<section id="logos"><h2>{t("Logos &amp; icons", "Logolar ve simgeler")}</h2>
<ul class="dl-grid">{logo_html}</ul>
</section>

<section id="team"><h2>{t("Team", "Ekip")}</h2>
<p><strong>Ufuk Pamuk</strong> · {t("Founder, game design and development", "Kurucu, oyun tasarımı ve geliştirme")}</p>
<p class="muted">{t("Kaotic Production is an independent game studio from Istanbul making fun, colourful, meaningful games for all ages. Reverdo is its first game.",
                   "Kaotic Production, İstanbul'dan her yaşa uygun eğlenceli, renkli ve anlamlı oyunlar yapan bağımsız bir oyun stüdyosu. Reverdo ilk oyunu.")}</p>
</section>

<section id="contact"><h2>{t("Contact", "İletişim")}</h2>
<p>{t("Press, interviews, review keys and business:", "Basın, röportaj, inceleme anahtarı ve iş birliği:")} <a href="{mail("Reverdo press", C.PRESS_EMAIL)}"><strong>{C.PRESS_EMAIL}</strong></a></p>
<p>{t("Player support", "Oyuncu desteği")}: <a href="{mail()}">{C.CONTACT_EMAIL}</a></p>
<p class="muted">{t("Studio website", "Stüdyo sitesi")}: <a href="{p["home"][lang]}">kaoticproduction.com</a></p>
</section>
</div>
</div>
"""
    title = t("Reverdo press kit · Kaotic Production", "Reverdo basın kiti · Kaotic Production")
    desc = t("Reverdo press kit: factsheet, description, screenshots, logos and contact for press.",
             "Reverdo basın kiti: bilgi kartı, tanıtım metni, ekran görüntüleri, logolar ve basın iletişimi.")
    return page(lang, "presskit", "game", title, desc, "/assets/img/og-reverdo.jpg", body)


# ================================================================== LEGAL (ported)
def _old(name):
    return open(os.path.join(LEGAL, name), encoding="utf-8").read()


def _fix_links(s):
    s = s.replace('href="index.html#', 'href="/reverdo/gizlilik/#').replace('href="en.html#', 'href="/reverdo/privacy/#')
    s = s.replace('href="index.html"', 'href="/reverdo/gizlilik/"').replace('href="en.html"', 'href="/reverdo/privacy/"')
    s = s.replace("kaoticproduction09@gmail.com", C.CONTACT_EMAIL)
    return s


def legal_page(lang, key, crumbs, h1, sub, inner, title, desc, switch):
    t = T(lang)
    body = f"""<div class="legal-hero"><div class="wrap">
<p class="crumbs"><a href="{PAGES["reverdo"][lang]}">Reverdo</a> / {crumbs}</p>
<h1>{h1}</h1><p>{sub}</p></div></div>
<div class="wrap"><div class="legal">
{inner}
<div class="switch">{switch}</div>
</div></div>"""
    return page(lang, key, "game", title, desc, "/assets/img/og-reverdo.jpg", body)


def privacy(lang):
    t = T(lang)
    src_html = _old("index.html" if lang == "tr" else "en.html")
    main = re.search(r"<main>(.*)</main>", src_html, re.S).group(1)
    hero = re.search(r'<div class="hero">\s*<h1>(.*?)</h1>\s*<p>(.*?)</p>\s*</div>', main, re.S)
    h1, sub = hero.group(1), hero.group(2)
    main = main.replace(hero.group(0), "")
    main = _fix_links(main)
    other = "tr" if lang == "en" else "en"
    switch = (f'<a class="btn leaf" href="{PAGES["support"][lang]}">{t("Support and FAQ", "Destek ve sık sorulanlar")}</a>'
              f'<a class="btn ghost" href="{PAGES["privacy"][other]}" hreflang="{other}" lang="{other}">{"Türkçe" if other == "tr" else "English"}</a>')
    desc = re.search(r'<meta name="description" content="(.*?)">', src_html).group(1)
    if lang == "en":
        desc = "Reverdo's privacy policy: what stays on your device, ads, purchases and children's privacy."
    return legal_page(lang, "privacy", h1, h1, sub, main, f"Reverdo · {h1}", desc, switch)


def support(lang):
    t = T(lang)
    src_html = _old("support.html")
    main = re.search(r"<main>(.*)</main>", src_html, re.S).group(1)
    secs = re.findall(r'<section class="card[^"]*" lang="(tr|en)"[^>]*>.*?</section>', main, re.S)
    blocks = re.findall(r'(<section class="card[^"]*" lang="(?:tr|en)"[^>]*>.*?</section>)', main, re.S)
    mine = [b for b in blocks if f'lang="{lang}"' in b.split(">", 1)[0]]
    inner = "\n".join(re.sub(r' lang="(tr|en)"', "", re.sub(r' id="en"', "", b), count=1) for b in mine)
    inner = inner.replace("<h2>Support (English)</h2>", "<h2>Contact</h2>").replace('class="card faq"', 'class="card qa"')
    inner = _fix_links(inner)
    h1 = t("Support", "Destek")
    sub = t(f'Reverdo · <a href="{mail()}">{C.CONTACT_EMAIL}</a>', f'Reverdo, Dünyayı Yeniden Yeşert · <a href="{mail()}">{C.CONTACT_EMAIL}</a>')
    other = "tr" if lang == "en" else "en"
    switch = (f'<a class="btn leaf" href="{PAGES["privacy"][lang]}">{t("Privacy policy", "Gizlilik politikası")}</a>'
              f'<a class="btn ghost" href="{PAGES["support"][other]}" hreflang="{other}" lang="{other}">{"Türkçe" if other == "tr" else "English"}</a>')
    desc = t("Reverdo support: contact and frequently asked questions.", "Reverdo destek: iletişim ve sık sorulan sorular.")
    return legal_page(lang, "support", h1, h1, sub, inner, f"Reverdo · {h1}", desc, switch)


# ================================================================== 404 + meta files
def notfound():
    body = """<div class="wrap nf"><div>
<p class="big">404</p>
<h1 style="font-size:clamp(1.8rem,4vw,2.6rem)">Page not found <span class="muted" lang="tr">· Sayfa bulunamadı</span></h1>
<p class="lead" style="margin:0 auto">This page may have moved. <span lang="tr">Bu sayfa taşınmış olabilir.</span></p>
<div class="ctas"><a class="btn" href="/">Home</a><a class="btn ghost" href="/tr/" lang="tr" hreflang="tr">Ana sayfa</a><a class="btn ghost" href="/reverdo/">Reverdo</a></div>
</div></div>"""
    return page("en", None, "studio", "Page not found · Kaotic Production", "Page not found.", "/assets/img/og-studio.jpg", body, noindex=True)


def sitemap():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for key, ls in PAGES.items():
        for lang in ("en", "tr"):
            out.append(f"<url><loc>{C.SITE_URL}{ls[lang]}</loc><lastmod>2026-10-24</lastmod>"
                       f'<xhtml:link rel="alternate" hreflang="en" href="{C.SITE_URL}{ls["en"]}"/>'
                       f'<xhtml:link rel="alternate" hreflang="tr" href="{C.SITE_URL}{ls["tr"]}"/>'
                       f'<xhtml:link rel="alternate" hreflang="x-default" href="{C.SITE_URL}{ls["en"]}"/></url>')
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def write(rel, text):
    path = os.path.join(ROOT, rel.lstrip("/").replace("/", os.sep))
    if path.endswith(os.sep) or rel.endswith("/"):
        path = os.path.join(path, "index.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    for lang in ("en", "tr"):
        write(PAGES["home"][lang], home(lang))
        write(PAGES["reverdo"][lang], reverdo(lang))
        write(PAGES["presskit"][lang], presskit(lang))
        write(PAGES["privacy"][lang], privacy(lang))
        write(PAGES["support"][lang], support(lang))
    write("/404.html", notfound())
    write("/sitemap.xml", sitemap())
    write("/robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {C.SITE_URL}/sitemap.xml\n")
    write("/CNAME", "kaoticproduction.com\n")
    write("/.nojekyll", "")
    write("/site.webmanifest", json.dumps({
        "name": "Kaotic Production", "short_name": "Kaotic", "start_url": "/", "display": "browser",
        "background_color": "#0d1016", "theme_color": "#0d1016",
        "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}]}, indent=1) + "\n")
    print("built")


if __name__ == "__main__":
    main()
