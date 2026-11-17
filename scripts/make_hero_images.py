#!/usr/bin/env python3
"""make_hero_images.py — resize the homepage hero photograph into the responsive set.

    python scripts/make_hero_images.py        # needs Pillow:  pip install Pillow

Reads the two masters in `clwydian-academy 2/assets/img/` (never modified):
    hero-training.jpg          2880 x 1920  landscape, desktop and tablet
    hero-training-mobile.jpg   1160 x 1450  portrait crop, phones (max-width 700px)
and writes hero-training-<width>.jpg/.webp and hero-training-mobile-<width>.jpg/.webp beside
them. The <picture> element in website/_src/pages/{en,cy}/home.html lists these files; if you
change WIDTHS, change the srcset there too (check_links.py fails on a file that is missing).
Run it again only when a master photograph is replaced.
"""
import os, sys
try:
    from PIL import Image
except ImportError:
    sys.exit("make_hero_images: Pillow is not installed — run: pip install Pillow")

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "clwydian-academy 2", "assets", "img")
WIDTHS = {"hero-training": (960, 1440, 1920, 2560), "hero-training-mobile": (480, 800, 1160)}

def main():
    for stem, widths in WIDTHS.items():
        master = Image.open(os.path.join(IMG, stem + ".jpg")).convert("RGB")
        for w in widths:
            h = round(master.height * w / master.width)
            im = master.resize((w, h), Image.LANCZOS)
            for ext, opts in ((".jpg", dict(quality=72, optimize=True, progressive=True)),
                              (".webp", dict(quality=70, method=6))):
                out = os.path.join(IMG, f"{stem}-{w}{ext}")
                im.save(out, **opts)
                print(f"{os.path.basename(out):36} {w} x {h}  {os.path.getsize(out) // 1024:4d} KB")
    return 0

if __name__ == "__main__":
    sys.exit(main())
