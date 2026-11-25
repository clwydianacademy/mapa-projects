#!/usr/bin/env python3
"""make_hero_images.py — resize the homepage hero photograph into the responsive set.

    python scripts/make_hero_images.py        # needs Pillow:  pip install Pillow

Reads the two masters in `site/assets/img/` (never modified):
    hero-training.jpg          2880 x 1920  landscape, desktop and tablet
    hero-training-mobile.jpg   1160 x 1450  portrait crop, phones (max-width 700px)
and writes hero-training-<width>.jpg/.webp and hero-training-mobile-<width>.jpg/.webp beside
them. The <picture> element in website/_src/pages/{en,cy}/home.html lists these files; if you
change WIDTHS, change the srcset there too (check_links.py fails on a file that is missing).
Run it again only when a master photograph is replaced.

    python scripts/make_hero_images.py --import DIR

makes the SHOWCASE photographs instead: see import_photos() below and _data/photos.json.
"""
import os, sys
try:
    from PIL import Image
except ImportError:
    sys.exit("make_hero_images: Pillow is not installed — run: pip install Pillow")

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site", "assets", "img")
WIDTHS = {"hero-training": (960, 1440, 1920, 2560), "hero-training-mobile": (480, 800, 1160)}

PHOTOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_data", "photos.json")
SHOWCASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "website", "_showcase", "photos")
BANNED_IN_NAMES = ("charlotte", "eleanor", "ce-", "logo", "mark")

def import_photos(src):
    """`--import DIR`: make the showcase photographs listed in _data/photos.json from the masters in DIR.

    Each is re-encoded from its PIXELS ALONE (so no EXIF, GPS, ICC comment or thumbnail survives),
    under its published name, as JPEG and WebP at every listed width. Nothing is ever upscaled.
    The sizes go into website/_showcase/photos/manifest.json, which is where the build reads the
    width and height it writes on every <img>. Only the listed files are read: a logo, a mark or
    anything else in DIR is never touched."""
    import json
    with open(PHOTOS, encoding="utf-8") as f:
        wanted = json.load(f)["photos"]
    os.makedirs(SHOWCASE, exist_ok=True)
    manifest = {}
    for ph in wanted:
        stem = ph["stem"]
        if any(b in stem.lower() for b in BANNED_IN_NAMES):
            sys.exit(f"make_hero_images: {stem!r} is not a name to publish under")
        opened = Image.open(os.path.join(src, ph["from"] + ".jpg"))
        master = Image.new("RGB", opened.size)
        master.paste(opened.convert("RGB"))               # pixels only: every tag and profile is left behind
        sizes = []
        for w in ph["widths"]:
            if w > master.width:
                sys.exit(f"make_hero_images: {stem} asked for {w}px from a {master.width}px master — never upscale")
            h = round(master.height * w / master.width)
            im = master if w == master.width else master.resize((w, h), Image.LANCZOS)
            for ext, opts in ((".jpg", dict(quality=74, optimize=True, progressive=True)),
                              (".webp", dict(quality=72, method=6))):
                out = os.path.join(SHOWCASE, f"{stem}-{w}{ext}")
                im.save(out, **opts)
                if Image.open(out).getexif():
                    sys.exit(f"make_hero_images: {os.path.basename(out)} still carries EXIF")
            sizes.append([w, h])
            print(f"{stem}-{w}  {w} x {h}  jpg {os.path.getsize(os.path.join(SHOWCASE, f'{stem}-{w}.jpg')) // 1024} KB"
                  f"  webp {os.path.getsize(os.path.join(SHOWCASE, f'{stem}-{w}.webp')) // 1024} KB")
        manifest[stem] = sizes
    with open(os.path.join(SHOWCASE, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=1); f.write("\n")
    return 0

def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--import":
        return import_photos(sys.argv[2])
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
