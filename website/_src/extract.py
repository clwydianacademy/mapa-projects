#!/usr/bin/env python3
"""extract.py — pull the source of truth out of the deployed HTML.

Brief 01 (September 2026): the generator was abandoned in July and the August edits went
straight into the deployed files in `clwydian-academy 2`. This script reads those files and
writes everything build.py needs to reproduce them:

    pages/<locale>/<key>.html   the body fragment — the contents of <main id="main">
    jsonld/<locale>/<key>.json  page-specific JSON-LD blocks (the Organization block is
                                build.py's, so it is skipped here)
    pages.json                  the registry: paths, titles, descriptions, nav item,
                                sitemap priority, footer legal-line variant, per locale

Rerunnable and deterministic. It changes nothing in `clwydian-academy 2`.
Run it only when the deployed HTML has been edited by hand and the source must catch up —
the normal direction of travel is the other way (edit source, run build.py).
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SITE = os.path.join(REPO, "clwydian-academy 2")
DOMAIN = "https://www.clwydianacademy.co.uk"   # canonical host; the apex 301s here at Vercel

# Registry order = the order the deployed sitemap listed the English pages, then 404.
ORDER = ["/", "/courses/", "/courses/nvq-level-2-hairdressing/", "/courses/nvq-level-3-hairdressing/",
         "/courses/cpd-courses/", "/funding/", "/for-salons/", "/about/", "/funders/", "/contact/",
         "/privacy/", "/courses/nvq-level-2-barbering/", "/courses/hair-extensions-course/",
         "/courses/perming-course/", "/courses/hair-relaxing-course/", "/courses/consultation-retail-cpd/",
         "/courses/salon-business-course/", "/courses/skin-cancer-awareness/", "/apprenticeships/",
         "/404.html"]

def key_of(url):
    if url == "/": return "home"
    if url == "/404.html": return "404"
    return url.rstrip("/").split("/")[-1]

def read(url):
    p = os.path.join(SITE, url.lstrip("/")) if url.endswith(".html") \
        else os.path.join(SITE, url.strip("/"), "index.html")
    return open(p, encoding="utf-8").read()

def field(s, rx):
    m = re.search(rx, s, re.S)
    return m.group(1) if m else None

def parse(url):
    h = read(url)
    head = field(h, r"<head>(.*?)</head>")
    d = {
        "title": field(head, r"<title>(.*?)</title>"),
        "desc": field(head, r'<meta name="description" content="(.*?)">'),
        "noindex": 'name="robots" content="noindex' in head,
        "canonical": field(head, r'<link rel="canonical" href="(.*?)">'),
        "alt": dict(re.findall(r'<link rel="alternate" hreflang="([\w-]+)" href="(.*?)">', head)),
    }
    lds = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', head, re.S):
        obj = json.loads(m.group(1))
        if obj.get("@type") == "EducationalOrganization":
            continue
        lds.append(obj)
    d["jsonld"] = lds
    hdr = field(h, r'<body>(.*?)<main id="main">')
    cur = re.findall(r'<a href="([^"]+)" aria-current="page">', hdr)
    d["nav"] = cur[0] if cur else None
    d["switch"] = field(hdr, r'class="lang-switch" href="([^"]+)"')
    d["body"] = field(h, r'<main id="main">(.*?)</main>').strip("\n") + "\n"
    foot = h[h.find("</main>"):]
    d["legal"] = "registered" if "17330962" in foot else "plain"
    # things the generator derives from title/desc — report where the live page disagrees
    d["notes"] = []
    for prop, want in (("og:title", d["title"]), ("twitter:title", d["title"]),
                       ("og:description", d["desc"]), ("twitter:description", d["desc"])):
        got = field(head, rf'(?:property|name)="{prop}" content="(.*?)">')
        if got != want:
            d["notes"].append(f'{prop} on {url} differs from its source: {got!r}')
    return d

def strip_domain(u):
    return u[len(DOMAIN):] if u and u.startswith(DOMAIN) else u

def main():
    prio = dict(re.findall(r"<loc>(.*?)</loc><lastmod>.*?</lastmod><priority>(.*?)</priority>",
                           open(os.path.join(SITE, "sitemap.xml"), encoding="utf-8").read()))
    registry, notes = [], []
    for url in ORDER:
        en = parse(url)
        key = key_of(url)
        entry = {"key": key, "nav": en["nav"], "noindex": en["noindex"],
                 "priority": prio.get(DOMAIN + url), "legal": en["legal"],
                 "en": {"path": url, "title": en["title"], "desc": en["desc"]}, "cy": None}
        notes += en["notes"]
        write(os.path.join(HERE, "pages", "en", key + ".html"), en["body"])
        write(os.path.join(HERE, "jsonld", "en", key + ".json"),
              json.dumps(en["jsonld"], indent=2, ensure_ascii=False) + "\n")
        cy_url = strip_domain(en["alt"].get("cy"))
        if cy_url:
            cy = parse(cy_url)
            entry["cy"] = {"path": cy_url, "title": cy["title"], "desc": cy["desc"]}
            notes += cy["notes"]
            if cy["legal"] != en["legal"]:
                notes.append(f"legal-line variant differs between {url} and {cy_url}")
            if strip_domain(cy["alt"].get("en")) != url or cy["switch"] != url or en["switch"] != cy_url:
                notes.append(f"hreflang / language-switch mismatch between {url} and {cy_url}")
            write(os.path.join(HERE, "pages", "cy", key + ".html"), cy["body"])
            write(os.path.join(HERE, "jsonld", "cy", key + ".json"),
                  json.dumps(cy["jsonld"], indent=2, ensure_ascii=False) + "\n")
        registry.append(entry)
        print(f"extracted {key:26} en={url}  cy={cy_url}")
    write(os.path.join(HERE, "pages.json"), json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    print(f"\n{len(registry)} pages in registry")
    if notes:
        print("\nLive pages that the generator will normalise (each must be named in the REPORT):")
        for n in notes: print("  -", n)

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:   # LF on every OS
        f.write(text)

if __name__ == "__main__":
    sys.exit(main())
