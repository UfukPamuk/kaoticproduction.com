"""Headless Chrome helper (Chrome DevTools Protocol, needs `websocket-client`).

    python tools/shoot.py brand              # logo PNGs, favicons, og-studio.jpg
    python tools/shoot.py pages OUTDIR       # full-page screenshots 1440 + 390
    (pages expects the site served at http://127.0.0.1:8765/)
"""
import base64
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

import websocket
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9333
BASE = "http://127.0.0.1:8765"


class Tab:
    def __init__(self):
        self.prof = tempfile.mkdtemp(prefix="kshoot")
        self.proc = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
                                      f"--user-data-dir={self.prof}", "--hide-scrollbars", "--no-first-run",
                                      "--autoplay-policy=no-user-gesture-required", "about:blank"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
                page = [t for t in tabs if t["type"] == "page"][0]
                break
            except Exception:
                time.sleep(.25)
        self.ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=60, suppress_origin=True)
        self.n = 0
        self.call("Page.enable")
        self.call("Runtime.enable")

    def call(self, method, **params):
        self.n += 1
        my = self.n
        self.ws.send(json.dumps({"id": my, "method": method, "params": params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == my:
                if "error" in m:
                    raise RuntimeError(method + ": " + str(m["error"]))
                return m.get("result", {})

    def wait_load(self, timeout=20):
        end = time.time() + timeout
        while time.time() < end:
            r = self.call("Runtime.evaluate", expression="document.readyState", returnByValue=True)
            if r["result"].get("value") == "complete":
                return
            time.sleep(.2)

    def go(self, url, width, height, mobile=False, scheme="light", dpr=1):
        self.call("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=dpr, mobile=mobile)
        self.call("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": scheme}])
        self.call("Page.navigate", url=url)
        time.sleep(.4)
        self.wait_load()
        # scroll through so lazy images load, then back to top
        self.call("Runtime.evaluate", awaitPromise=True, expression="""(async()=>{document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager');const h=document.documentElement.scrollHeight;
            for(let y=0;y<h;y+=500){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,60));}
            window.scrollTo(0,0);await new Promise(r=>setTimeout(r,500));
            await Promise.race([new Promise(r=>setTimeout(r,5000)),Promise.all([...document.images].map(i=>i.complete?0:new Promise(r=>{i.onload=i.onerror=r;})))]);})()""")
        time.sleep(1.2)

    def shot(self, path, full=True, clip=None, fmt="png"):
        if full and not clip:
            m = self.call("Page.getLayoutMetrics")
            w = m["cssContentSize"]["width"]
            h = m["cssContentSize"]["height"]
            clip = {"x": 0, "y": 0, "width": w, "height": h, "scale": 1}
        args = {"format": fmt, "captureBeyondViewport": True}
        if clip:
            args["clip"] = clip
        if fmt == "jpeg":
            args["quality"] = 82
        r = self.call("Page.captureScreenshot", **args)
        data = base64.b64decode(r["data"])
        with open(path, "wb") as f:
            f.write(data)
        return path

    def close(self):
        try:
            self.call("Browser.close")
        except Exception:
            pass
        self.proc.wait(timeout=10)


BRAND_SVGS = ["kaotic-emblem", "kaotic-emblem-white", "kaotic-logo-dark-bg", "kaotic-logo-light-bg",
              "kaotic-logo-white", "kaotic-logo-black", "kaotic-favicon"]


def brand():
    """Rasterise assets/brand/*.svg to PNG sizes, favicons and touch icons."""
    b = os.path.join(ROOT, "assets", "brand")
    cache = os.path.join(ROOT, "tools", "_cache")
    os.makedirs(cache, exist_ok=True)
    page = os.path.join(cache, "brand.html")
    imgs = "".join(f'<div><img id="{n}" src="file:///{b.replace(os.sep, "/")}/{n}.svg" style="width:2048px;display:block"></div>' for n in BRAND_SVGS)
    open(page, "w", encoding="utf-8").write(f'<!doctype html><html><body style="margin:0;background:transparent">{imgs}</body></html>')
    tab = Tab()
    big = {}
    try:
        tab.call("Emulation.setDefaultBackgroundColorOverride", color={"r": 0, "g": 0, "b": 0, "a": 0})
        tab.go("file:///" + page.replace("\\", "/"), 2100, 1200)
        for n in BRAND_SVGS:
            r = tab.call("Runtime.evaluate", returnByValue=True,
                         expression=f"(()=>{{const b=document.getElementById('{n}').getBoundingClientRect();return [b.x,b.y+scrollY,b.width,b.height]}})()")
            x, y, w, h = r["result"]["value"]
            p = os.path.join(cache, n + "-2048.png")
            tab.shot(p, clip={"x": x, "y": y, "width": w, "height": h, "scale": 1})
            big[n] = p
    finally:
        tab.close()
    for n, p in big.items():
        im = Image.open(p).convert("RGBA")
        if n == "kaotic-favicon":
            for sz in (180, 192, 512):
                im.resize((sz, sz), Image.LANCZOS).save(os.path.join(b, f"{n}-{sz}.png"), optimize=True)
            im.resize((180, 180), Image.LANCZOS).save(os.path.join(ROOT, "apple-touch-icon.png"), optimize=True)
            im.resize((192, 192), Image.LANCZOS).save(os.path.join(ROOT, "icon-192.png"), optimize=True)
            im.resize((512, 512), Image.LANCZOS).save(os.path.join(ROOT, "icon-512.png"), optimize=True)
            im.resize((32, 32), Image.LANCZOS).save(os.path.join(ROOT, "favicon-32.png"), optimize=True)
            im.save(os.path.join(ROOT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
            continue
        for w in (512, 1024, 2048):
            h = round(im.height * w / im.width)
            im.resize((w, h), Image.LANCZOS).save(os.path.join(b, f"{n}-{w}.png"), optimize=True)
    print("brand ok")


PAGES = [
    ("home-en", "/"), ("home-tr", "/tr/"), ("reverdo-en", "/reverdo/"), ("reverdo-tr", "/tr/reverdo/"),
    ("presskit-en", "/reverdo/presskit/"), ("presskit-tr", "/tr/reverdo/presskit/"),
    ("privacy-en", "/reverdo/privacy/"), ("gizlilik-tr", "/reverdo/gizlilik/"),
    ("support-en", "/reverdo/support/"), ("destek-tr", "/reverdo/destek/"), ("404", "/404.html"),
]


def pages(out, only=None, scheme="light"):
    os.makedirs(out, exist_ok=True)
    tab = Tab()
    try:
        for name, path in PAGES:
            if only and name not in only:
                continue
            sizes = os.environ.get("KSHOOT_SIZES", "1440x900,390x844").split(",")
            for size in sizes:
                w, h = map(int, size.split("x"))
                mob = w < 768
                label = "phone" if mob else f"desktop{w}"
                tab.go(BASE + path, w, h, mobile=mob, scheme=scheme)
                # no horizontal overflow check
                r = tab.call("Runtime.evaluate", returnByValue=True,
                             expression="[document.documentElement.scrollWidth, window.innerWidth]")
                sw, iw = r["result"]["value"]
                flag = "" if sw <= iw else f"  !! horizontal overflow {sw}>{iw}"
                p = os.path.join(out, f"{name}-{label}{'-dark' if scheme == 'dark' else ''}.png")
                tab.shot(p)
                print(p, flag)
    finally:
        tab.close()


def weight(only=None):
    """Bytes transferred: on load (desktop 1440 and phone 390) and after scrolling the whole page."""
    tab = Tab()
    rows = []
    try:
        tab.call("Network.enable")
        tab.call("Network.setCacheDisabled", cacheDisabled=True)
        for name, path in PAGES:
            if only and name not in only:
                continue
            res = {}
            for label, w, h, mob in (("desktop", 1440, 900, False), ("phone", 390, 844, True)):
                sizes, urls = {}, {}
                def pump(seconds):
                    end = time.time() + seconds
                    tab.ws.settimeout(0.3)
                    while time.time() < end:
                        try:
                            m = json.loads(tab.ws.recv())
                        except Exception:
                            continue
                        meth = m.get("method")
                        if meth == "Network.requestWillBeSent":
                            urls[m["params"]["requestId"]] = m["params"]["request"]["url"]
                        elif meth == "Network.loadingFinished":
                            sizes[m["params"]["requestId"]] = m["params"]["encodedDataLength"]
                        elif meth == "Network.dataReceived":
                            pass
                    tab.ws.settimeout(60)
                tab.call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=(3 if mob else 1), mobile=mob)
                tab.call("Page.navigate", url=BASE + path)
                pump(6)
                def total(video):
                    return sum(v for k, v in sizes.items() if (".mp4" in urls.get(k, "") or ".webm" in urls.get(k, "")) == video)
                first = total(False)
                tab.call("Runtime.evaluate", expression="""(async()=>{const h=document.documentElement.scrollHeight;
                    for(let y=0;y<h;y+=400){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,120));}})()""")
                pump(12)
                res[label] = (first, total(False), total(True))
            rows.append((name, res))
            d, p_ = res["desktop"], res["phone"]
            print(f"{name:13s} desktop: load {d[0]/1024:7.0f} KB, full {d[1]/1024:7.0f} KB, video {d[2]/1024:6.0f} KB | "
                  f"phone(3x): load {p_[0]/1024:7.0f} KB, full {p_[1]/1024:7.0f} KB, video {p_[2]/1024:6.0f} KB")
    finally:
        tab.close()


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "brand":
        brand()
    elif cmd == "weight":
        weight(sys.argv[2:] or None)
    elif cmd == "pages":
        args = sys.argv[3:]
        scheme = "dark" if "--dark" in args else "light"
        only = [a for a in args if not a.startswith("--")]
        pages(sys.argv[2], only or None, scheme)
