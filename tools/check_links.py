"""Static checks for the built site: broken links/images, anchors, basics.

    python tools/check_links.py
Exit code 1 if anything is broken.
"""
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"tools", ".git"}


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs, self.ids, self.h1, self.imgs_no_alt, self.lang = [], [], 0, [], None
        self.dup = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        if "id" in a:
            if a["id"] in self.ids:
                self.dup.append(a["id"])
            self.ids.append(a["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "img" and "alt" not in a:
            self.imgs_no_alt.append(a.get("src"))
        for k in ("href", "src", "poster", "data-full"):
            if a.get(k) and not (tag == "link" and a.get("rel") in ("canonical", "alternate")) and not (tag == "meta"):
                self.refs.append((tag, k, a[k]))
        for k in ("srcset",):
            if a.get(k):
                for part in a[k].split(","):
                    self.refs.append((tag, k, part.strip().split(" ")[0]))
        for k in ("data-large", "data-small"):
            if a.get(k):
                for ext in ("mp4", "webm"):
                    self.refs.append((tag, k, a[k] + "." + ext))


def local_path(url, base_dir):
    u = urlparse(url)
    path = unquote(u.path)
    if path.startswith("/"):
        f = os.path.join(ROOT, path.lstrip("/"))
    else:
        f = os.path.normpath(os.path.join(base_dir, path))
    if path.endswith("/") or os.path.isdir(f):
        f = os.path.join(f, "index.html")
    return f, u.fragment


def main():
    pages = []
    for d, ds, fs in os.walk(ROOT):
        ds[:] = [x for x in ds if x not in SKIP_DIRS]
        for f in fs:
            if f.endswith(".html"):
                pages.append(os.path.join(d, f))
    parsed = {}
    for p in pages:
        h = P()
        h.feed(open(p, encoding="utf-8").read())
        parsed[os.path.normpath(p)] = h
    errors, external = [], set()
    for p, h in parsed.items():
        rel = os.path.relpath(p, ROOT)
        if not h.lang:
            errors.append(f"{rel}: no <html lang>")
        if h.h1 != 1:
            errors.append(f"{rel}: {h.h1} <h1> elements")
        if h.dup:
            errors.append(f"{rel}: duplicate ids {h.dup}")
        if h.imgs_no_alt:
            errors.append(f"{rel}: img without alt {h.imgs_no_alt}")
        for tag, k, url in h.refs:
            if url.startswith(("mailto:", "tel:", "data:", "javascript:")):
                continue
            if url.startswith(("http://", "https://", "//")):
                if "kaoticproduction.com" not in url:
                    external.add(url)
                continue
            if url.startswith("#"):
                if url[1:] and url[1:] not in h.ids:
                    errors.append(f"{rel}: missing anchor {url}")
                continue
            f, frag = local_path(url, os.path.dirname(p))
            if not os.path.exists(f):
                errors.append(f"{rel}: broken {k}={url}")
            elif frag and f.endswith(".html"):
                t = parsed.get(os.path.normpath(f))
                if t and frag not in t.ids:
                    errors.append(f"{rel}: missing anchor {url}")
    # sitemap and hreflang targets
    sm = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
    for u in set(re.findall(r'https://kaoticproduction\.com(/[^"<]*)', sm)):
        f, _ = local_path(u, ROOT)
        if not os.path.exists(f):
            errors.append(f"sitemap: missing {u}")
    for p in pages:
        for u in re.findall(r'hreflang="[^"]+" href="https://kaoticproduction\.com(/[^"]*)"', open(p, encoding="utf-8").read()):
            f, _ = local_path(u, ROOT)
            if not os.path.exists(f):
                errors.append(f"{os.path.relpath(p, ROOT)}: hreflang target missing {u}")
    print(f"{len(pages)} pages checked")
    print("external links:", *sorted(external), sep="\n  ")
    if errors:
        print("ERRORS:", *errors, sep="\n  ")
        sys.exit(1)
    print("OK: no broken links, images or anchors")


if __name__ == "__main__":
    main()
