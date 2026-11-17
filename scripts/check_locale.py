#!/usr/bin/env python3
"""
check_locale.py — the English and Welsh sites are mirrors.

    python3 scripts/check_locale.py ["site"]

For every page except /404.html:
  * <html lang> is en-GB outside /cy/ and cy inside it
  * the head carries hreflang en, cy and x-default; x-default equals en
  * the counterpart named by hreflang exists, and its own hreflang points straight back
  * the header language switch points at the same counterpart
  * the primary nav has the same number of links in both languages
  * sitemap.xml lists the page (unless noindex) and its counterpart
  * the canonical is self-referential on HOST, and every og:url, hreflang href and sitemap
    <loc> uses HOST — never the apex, never http
Exit 0 = clean, 1 = problems, 2 = no dir.
"""
import os, re, sys

HOST = "https://www.clwydianacademy.co.uk"   # the one canonical host; the apex 301s here at Vercel
DOMAIN = HOST

def pages(root):
    out = {}
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if fn.endswith(".html"):
                rel = "/" + os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/")
                url = rel[:-len("index.html")] if rel.endswith("/index.html") else rel
                out[url] = open(os.path.join(dirpath, fn), encoding="utf-8", errors="replace").read()
    return out

def strip(u):
    return u[len(DOMAIN):] if u and u.startswith(DOMAIN) else u

def check(root):
    problems = []
    site = pages(root)
    sm_path = os.path.join(root, "sitemap.xml")
    sitemap = None
    if os.path.exists(sm_path):
        sm_text = open(sm_path, encoding="utf-8").read()
        for u in re.findall(r'(?:<loc>|href=")(https?://[^<"]+)', sm_text):
            if not u.startswith(HOST + "/"):
                problems.append(f"sitemap.xml: {u} is not on {HOST}")
        sitemap = set(strip(u) for u in re.findall(r"<loc>(.*?)</loc>", sm_text))
    for url, html in sorted(site.items()):
        if url == "/404.html":
            continue
        is_cy = url.startswith("/cy/")
        head = html.split("</head>", 1)[0]
        lang = re.search(r'<html lang="([^"]+)"', html)
        want = "cy" if is_cy else "en-GB"
        if not lang or lang.group(1) != want:
            problems.append(f"{url}: <html lang> is {lang.group(1) if lang else 'missing'}, expected {want}")
        canon = re.search(r'<link rel="canonical" href="([^"]+)">', head)
        if not canon or canon.group(1) != HOST + url:
            problems.append(f"{url}: canonical is {canon.group(1) if canon else 'missing'}, expected {HOST + url}")
        og = re.search(r'<meta property="og:url" content="([^"]+)">', head)
        if not og or og.group(1) != HOST + url:
            problems.append(f"{url}: og:url is {og.group(1) if og else 'missing'}, expected {HOST + url}")
        for k, v in re.findall(r'<link rel="alternate" hreflang="([\w-]+)" href="([^"]+)">', head):
            if not v.startswith(HOST + "/"):
                problems.append(f"{url}: hreflang {k} href {v} is not on {HOST}")
        alts = dict((k, strip(v)) for k, v in re.findall(r'<link rel="alternate" hreflang="([\w-]+)" href="([^"]+)">', head))
        for k in ("en", "cy", "x-default"):
            if k not in alts:
                problems.append(f"{url}: no hreflang {k}")
        if alts.get("x-default") != alts.get("en"):
            problems.append(f"{url}: x-default {alts.get('x-default')} != en {alts.get('en')}")
        me, other = ("cy", "en") if is_cy else ("en", "cy")
        if alts.get(me) != url:
            problems.append(f"{url}: hreflang {me} is {alts.get(me)}, not itself")
        twin = alts.get(other)
        if twin not in site:
            problems.append(f"{url}: counterpart {twin} does not exist"); continue
        twin_head = site[twin].split("</head>", 1)[0]
        back = dict((k, strip(v)) for k, v in re.findall(r'<link rel="alternate" hreflang="([\w-]+)" href="([^"]+)">', twin_head))
        if back.get(me) != url:
            problems.append(f"{url}: counterpart {twin} points its hreflang {me} at {back.get(me)}")
        sw = re.search(r'class="lang-switch" href="([^"]+)"', html)
        if not sw or sw.group(1) != twin:
            problems.append(f"{url}: language switch goes to {sw.group(1) if sw else 'nowhere'}, hreflang says {twin}")
        nav = lambda h: len(re.findall(r"<a ", re.search(r'<nav class="site-nav".*?</nav>', h, re.S).group(0)))
        if nav(html) != nav(site[twin]):
            problems.append(f"{url}: {nav(html)} nav links vs {nav(site[twin])} on {twin}")
        if sitemap is not None and 'name="robots" content="noindex' not in head:
            for u in (url, twin):
                if u not in sitemap:
                    problems.append(f"{u}: not in sitemap.xml")
    if sitemap is not None:
        for u in sorted(sitemap):
            if u not in site:
                problems.append(f"sitemap.xml lists {u}, which is not a built page")
    return problems, len(site)

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "site"
    if not os.path.isdir(root):
        print(f"check_locale: no such directory: {root}"); return 2
    problems, n = check(root)
    if not problems:
        print(f"check_locale: {n} pages — every EN page has a CY mirror and back, navs match, sitemap complete, one host ({HOST})."); return 0
    print(f"check_locale: {n} pages — {len(problems)} problem(s)\n")
    for p in problems: print("  ", p)
    print("\nFAIL — fix pages.json / build.py, then rebuild.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
