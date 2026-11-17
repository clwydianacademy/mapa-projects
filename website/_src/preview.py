#!/usr/bin/env python3
"""Create a double-clickable local preview of the built site.

    python website/_src/preview.py [built-dir] [preview-dir]

Rewrites root-absolute URLs (/assets/..., /courses/) into relative ones,
and points directory links at their index.html so file:// browsing works.
The production folder is untouched.

Defaults are relative to the repository, so it runs the same from any directory on any OS:
built-dir = <repo>/clwydian-academy 2, preview-dir = <repo>/_preview (git-ignored).
The enquiry form cannot send from a file:// preview - it needs the /api/enquiry function.
"""
import os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SITE = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(REPO, "clwydian-academy 2")
PREV = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(REPO, "_preview")

BADGE = ('<div style="position:fixed;bottom:14px;left:14px;z-index:999;'
         'background:#1c2a45;color:#f7f5f2;font:600 11px/1 -apple-system,sans-serif;'
         'letter-spacing:.09em;padding:8px 13px;border-radius:999px;opacity:.85;'
         'pointer-events:none">LOCAL PREVIEW</div>')

def relative(val, prefix):
    """One root-absolute URL -> a relative one that works from file://."""
    if not val.startswith("/") or val.startswith("//"):
        return val
    path, _, frag = val.partition("#")
    path, _, query = path.partition("?")      # a query string means nothing to file://
    if path == "/":
        path = "index.html"
    elif path.endswith("/"):
        path = path.lstrip("/") + "index.html"
    else:
        path = path.lstrip("/")
    return prefix + path + (("#" + frag) if frag else "")

def rewrite(html, depth):
    prefix = "../" * depth
    html = re.sub(r'\b(href|src|data|poster)="([^"]*)"',
                  lambda m: f'{m.group(1)}="{relative(m.group(2), prefix)}"', html)
    def srcset(m):
        out = []
        for cand in m.group(1).split(","):
            parts = cand.strip().split()
            if parts:
                out.append(" ".join([relative(parts[0], prefix)] + parts[1:]))
        return 'srcset="' + ", ".join(out) + '"'
    html = re.sub(r'\bsrcset="([^"]*)"', srcset, html)
    return html.replace("<body>", "<body>\n" + BADGE, 1)

def main():
    if not os.path.isdir(SITE):
        print(f"preview: no built site at {SITE}"); return 2
    if os.path.commonpath([SITE, PREV]) == SITE:
        print("preview: the preview directory must not be inside the built site"); return 2
    if os.path.isdir(PREV):
        shutil.rmtree(PREV)
    shutil.copytree(SITE, PREV)
    n = 0
    for root, _dirs, files in os.walk(PREV):
        for f in files:
            if not f.endswith(".html"):
                continue
            p = os.path.join(root, f)
            depth = os.path.relpath(p, PREV).count(os.sep)
            with open(p, encoding="utf-8") as fh:
                src = fh.read()
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(rewrite(src, depth))
            n += 1
    print(f"preview ready: {n} pages in {PREV}")
    print("open", os.path.join(PREV, "index.html"))
    return 0

if __name__ == "__main__":
    sys.exit(main())
