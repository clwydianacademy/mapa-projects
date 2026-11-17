#!/usr/bin/env python3
"""
check_links.py — every root-relative href / src / srcset in the built tree resolves to a file.

    python3 scripts/check_links.py ["site"]

Exit 0 = clean. Exit 1 = broken references (listed, with the page they are on). Exit 2 = no dir.
Fragments (#…) and query strings are ignored; a directory URL must contain index.html;
protocol-relative and absolute URLs are not checked (that is the PM's live check, not ours).

Also checks the redirects in <root>/vercel.json (written by build.py from _data/redirects.json):
every redirect must be a 301 to a page that exists, and no built page may still sit at a
redirected URL. A link to a retired URL is already a broken reference, so it is caught above.
"""
import json, os, re, sys

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

def check_redirects(root):
    path = os.path.join(root, "vercel.json")
    if not os.path.exists(path):
        return [], 0
    problems = []
    with open(path, encoding="utf-8") as f:
        rules = json.load(f).get("redirects", [])
    for r in rules:
        src, dst = r.get("source", ""), r.get("destination", "")
        if r.get("statusCode") != 301:
            problems.append(("vercel.json", f"{src}: statusCode is {r.get('statusCode')}, expected 301"))
        if not dst.startswith("/") or not resolve(root, dst):
            problems.append(("vercel.json", f"{src} redirects to {dst}, which is not a built page"))
        built = os.path.join(root, src.strip("/"), "index.html")
        if src.strip("/") and os.path.exists(built):
            problems.append(("vercel.json", f"{src} is redirected, but a built page is still there: {os.path.relpath(built, root)}"))
    return problems, len(rules)

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "site"
    if not os.path.isdir(root):
        print(f"check_links: no such directory: {root}"); return 2
    broken, refs = check(root)
    bad_redirects, n_redirects = check_redirects(root)
    broken = broken + bad_redirects
    if not broken:
        print(f"check_links: {refs} internal references checked — 0 broken; {n_redirects} redirect rules, all to built pages."); return 0
    print(f"check_links: {refs} internal references checked — {len(broken)} broken\n")
    for page, u in broken:
        print(f"  {page}  ->  {u}")
    print("\nFAIL — fix the source fragment or the registry, then rebuild.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
