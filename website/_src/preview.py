#!/usr/bin/env python3
"""Create a double-clickable local preview of the built site.

Rewrites root-absolute URLs (/assets/..., /courses/) into relative ones,
and points directory links at their index.html so file:// browsing works.
The production folder is untouched.
"""
import os, re, shutil

SITE = "/sessions/practical-exciting-tesla/mnt/outputs/clwydian-academy"
PREV = "/sessions/practical-exciting-tesla/mnt/outputs/clwydian-academy-preview"

BADGE = ('<div style="position:fixed;bottom:14px;left:14px;z-index:999;'
         'background:#1c2a45;color:#f7f5f2;font:600 11px/1 -apple-system,sans-serif;'
         'letter-spacing:.09em;padding:8px 13px;border-radius:999px;opacity:.85;'
         'pointer-events:none">LOCAL PREVIEW</div>')

def rewrite(html, depth):
    prefix = "../" * depth

    def fix(m):
        attr, val = m.group(1), m.group(2)
        if not val.startswith("/") or val.startswith("//"):
            return m.group(0)
        path, _, frag = val.partition("#")
        if path == "/":
            path = "index.html"
        elif path.endswith("/"):
            path = path.lstrip("/") + "index.html"
        else:
            path = path.lstrip("/")
        out = prefix + path + (("#" + frag) if frag else "")
        return f'{attr}="{out}"'

    html = re.sub(r'(href|src|data)="([^"]*)"', fix, html)
    return html.replace("<body>", "<body>\n" + BADGE, 1)

shutil.copytree(SITE, PREV, dirs_exist_ok=True)

for root, _, files in os.walk(PREV):
    for f in files:
        if not f.endswith(".html"):
            continue
        p = os.path.join(root, f)
        depth = os.path.relpath(p, PREV).count(os.sep)
        src = open(p).read()
        open(p, "w").write(rewrite(src, depth))
        print(f"preview: {os.path.relpath(p, PREV)} (depth {depth})")

print("\npreview ready:", PREV)
