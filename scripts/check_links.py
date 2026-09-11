#!/usr/bin/env python3
"""
check_links.py — every root-relative href / src / srcset in the built tree resolves to a file.

    python3 scripts/check_links.py ["clwydian-academy 2"]

Exit 0 = clean. Exit 1 = broken references (listed, with the page they are on). Exit 2 = no dir.
Fragments (#…) and query strings are ignored; a directory URL must contain index.html;
protocol-relative and absolute URLs are not checked (that is the PM's live check, not ours).
"""
import os, re, sys

REF_RE = re.compile(r'\b(?:href|src|poster|data)="([^"]+)"')
SRCSET_RE = re.compile(r'\bsrcset="([^"]+)"')

def resolve(root, url):
    path = url.split("#", 1)[0].split("?", 1)[0]
    p = os.path.join(root, path.lstrip("/"))
    if path.endswith("/"):
        p = os.path.join(p, "index.html")
    return os.path.exists(p)

def check(root):
    broken, refs = [], 0
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".html"):
                continue
            page = "/" + os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/")
            html = open(os.path.join(dirpath, fn), encoding="utf-8", errors="replace").read()
            urls = REF_RE.findall(html)
            for ss in SRCSET_RE.findall(html):
                urls += [c.strip().split()[0] for c in ss.split(",") if c.strip()]
            for u in urls:
                if not u.startswith("/") or u.startswith("//"):
                    continue
                refs += 1
                if not resolve(root, u):
                    broken.append((page, u))
    return sorted(set(broken)), refs

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "clwydian-academy 2"
    if not os.path.isdir(root):
        print(f"check_links: no such directory: {root}"); return 2
    broken, refs = check(root)
    if not broken:
        print(f"check_links: {refs} internal references checked — 0 broken."); return 0
    print(f"check_links: {refs} internal references checked — {len(broken)} broken\n")
    for page, u in broken:
        print(f"  {page}  ->  {u}")
    print("\nFAIL — fix the source fragment or the registry, then rebuild.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
