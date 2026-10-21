"""Reverdo hero loop from native 2560x1440 game captures (no digital zoom).

Shots are filmed with tests/capture_trailer.gd under Godot's Movie Maker at
2560x1440 (see the header of this file's history / report), cut by
docs/store/trailer/tools/cut_shots.py into E:/trailer-work-1440/clips/en.
This joins wide, slow camera moves and writes 1440p, 1080p and 720p loops
(H.264 MP4 + VP9 WebM, silent, 30 fps) and matching posters.

    python tools/make_hero_clip.py
"""
import os
import subprocess

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = r"C:\Users\pc\AppData\Local\KiyiDevTools\ffmpeg\ffmpeg.exe"
CLIPS = r"E:\trailer-work-1440\clips\en"
OUT = os.path.join(ROOT, "assets", "video")
IMG = os.path.join(ROOT, "assets", "img")
CACHE = os.path.join(ROOT, "tools", "_cache")

# (clip, start s, end s): wide crane/dolly moves only
SHOTS = [
    ("sultan_crane", 3.0, 5.8),
    ("taj_rise", 3.2, 5.8),
    ("paris_crane", 2.2, 4.8),
    ("giza_crane", 2.0, 4.8),
]

TAGS = ["-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]

SIZES = {  # name: (width, height, x264 crf, x264 maxrate, vp9 bitrate)
    "1440": (2560, 1440, 21, "12M", "8M"),
    "1080": (1920, 1080, 20, "9M", "5.5M"),
    "720": (1280, 720, 21, "4M", "2.6M"),
}


def ff(*args):
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def main():
    os.makedirs(CACHE, exist_ok=True)
    inputs, fc, labels = [], "", ""
    for i, (clip, a, b) in enumerate(SHOTS):
        inputs += ["-i", os.path.join(CLIPS, clip + ".avi")]
        fc += f"[{i}:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=30[s{i}];"
        labels += f"[s{i}]"
    # Movie Maker writes full-range BT.601 JPEG frames: convert to limited-range
    # BT.709 (browsers refuse to decode full-range VP9 here; colours stay right)
    fc += (f"{labels}concat=n={len(SHOTS)}:v=1:a=0,"
           "scale=in_range=pc:out_range=tv:in_color_matrix=bt601:out_color_matrix=bt709,format=yuv420p[v]")
    master = os.path.join(CACHE, "hero-master-1440.mp4")
    ff(*inputs, "-filter_complex", fc, "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "8", *TAGS, master)
    for name, (w, h, crf, maxrate, vbr) in SIZES.items():
        vf = ["-vf", f"scale={w}:{h}:flags=lanczos"] if w != 2560 else []
        mp4 = os.path.join(OUT, f"reverdo-hero-{name}.mp4")
        ff("-i", master, *vf, "-an", "-c:v", "libx264", "-preset", "veryslow", "-crf", str(crf),
           "-maxrate", maxrate, "-bufsize", str(int(maxrate[:-1]) * 2) + "M", "-profile:v", "high",
           "-pix_fmt", "yuv420p", *TAGS, "-movflags", "+faststart", mp4)
        webm = os.path.join(OUT, f"reverdo-hero-{name}.webm")
        log = os.path.join(CACHE, f"vp9-{name}")
        common = [*vf, "-an", "-c:v", "libvpx-vp9", "-b:v", vbr, "-row-mt", "1", "-pix_fmt", "yuv420p", *TAGS, "-passlogfile", log]
        ff("-i", master, *common, "-pass", "1", "-deadline", "good", "-cpu-used", "4", "-f", "null", "NUL")
        ff("-i", master, *common, "-pass", "2", "-deadline", "good", "-cpu-used", "2", webm)
        print(name, os.path.getsize(mp4) // 1024, "KB mp4,", os.path.getsize(webm) // 1024, "KB webm")
    first = os.path.join(CACHE, "hero-first-1440.png")
    ff("-i", master, "-frames:v", "1", first)
    im = Image.open(first).convert("RGB")
    for old in os.listdir(IMG):
        if old.startswith("hero-poster-"):
            os.remove(os.path.join(IMG, old))
    for w in (640, 1280, 1920, 2560):
        r = im.resize((w, w * 9 // 16), Image.LANCZOS) if w != im.width else im
        b = os.path.join(IMG, f"hero-poster-{w}")
        r.save(b + ".avif", quality=52)
        r.save(b + ".webp", quality=78, method=6)
        r.save(b + ".jpg", quality=82, optimize=True, progressive=True)
    for old in ("reverdo-hero-360.mp4", "reverdo-hero-360.webm"):
        p = os.path.join(OUT, old)
        if os.path.exists(p):
            os.remove(p)
    print("posters ok")


if __name__ == "__main__":
    main()
