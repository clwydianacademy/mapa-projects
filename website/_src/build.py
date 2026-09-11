#!/usr/bin/env python3
"""Assemble the Clwydian Academy static site from body fragments + shared chrome, in two locales.

    python3 website/_src/build.py                    # writes into clwydian-academy 2/
    python3 scripts/check_claims.py "clwydian-academy 2"

Every fact in ORG and the chrome below must agree with /CLAUDE.md. The body fragments in
pages/ and the page-specific JSON-LD in jsonld/ were extracted from the deployed HTML in
Brief 01 (extract.py); the registry in pages.json says which fragment goes where, in which
language, with which title and description.

Output goes to `clwydian-academy 2` — the Vercel root directory. Nothing is written for
GitHub Pages (no CNAME, no .nojekyll); that hosting is dead.
"""
import datetime, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "clwydian-academy 2")
DOMAIN = "https://clwydianacademy.co.uk"
LOCALES = ("en", "cy")

# Organization — one block, both languages, identical to the live homepage on 11 Sep 2026.
# No parentOrganization, no old legalName: see CLAUDE.md "The entity".
ORG = {
    "@context": "https://schema.org",
    "@type": "EducationalOrganization",
    "@id": DOMAIN + "/#organization",
    "name": "Clwydian Academy",
    "alternateName": "Clwydian Academy CBC",
    "description": "Fast-track vocational hairdressing and barbering academy in St Asaph, North Wales. VTCT-standard NVQ diplomas, CPD masterclasses and Welsh-framework apprenticeships, with fully funded routes for eligible learners.",
    "url": DOMAIN + "/",
    "logo": DOMAIN + "/assets/img/seal-512.png",
    "image": DOMAIN + "/assets/img/og-image.png",
    "email": "markp@charlotteeleanorgroup.uk",
    "telephone": "+447714198743",
    "foundingDate": "2026",
    "knowsLanguage": ["en", "cy"],
    "address": {"@type": "PostalAddress", "addressLocality": "St Asaph", "addressRegion": "Denbighshire", "addressCountry": "GB"},
    "areaServed": ["North Wales", "Denbighshire", "Conwy", "Flintshire", "Wrexham", "Chester", "Cheshire", "North West England"],
    "founder": [
        {"@type": "Person", "name": "Mark Parker", "jobTitle": "Chief Executive Officer", "sameAs": "https://www.linkedin.com/in/mark-parker-07a885316"},
        {"@type": "Person", "name": "Charlotte Roberts", "jobTitle": "Director of the Academy"},
    ],
    "sameAs": ["https://www.linkedin.com/in/mark-parker-07a885316"],
}

# Primary navigation: one list, both languages. A page's "nav" in pages.json is the EN path.
NAV = [
    {"en": ("/courses/", "Courses"),               "cy": ("/cy/cyrsiau/", "Cyrsiau")},
    {"en": ("/apprenticeships/", "Apprenticeships"), "cy": ("/cy/prentisiaethau/", "Prentisiaethau")},
    {"en": ("/funding/", "Fees &amp; Funding"),    "cy": ("/cy/ffioedd-a-chyllid/", "Ffioedd a Chyllid")},
    {"en": ("/for-salons/", "For Salons"),         "cy": ("/cy/i-salonau/", "I Salonau")},
    {"en": ("/about/", "About"),                   "cy": ("/cy/amdanom/", "Amdanom")},
    {"en": ("/funders/", "Funders"),               "cy": ("/cy/cyllidwyr/", "Cyllidwyr")},
    {"en": ("/contact/", "Contact"),               "cy": ("/cy/cysylltu/", "Cysylltu")},
]

# Every locale-specific string in the chrome. Welsh strings are machine-written and
# unreviewed (CLAUDE.md "Bilingual") — any change here goes under WELSH FOR REVIEW.
CHROME = {
    "en": dict(
        html_lang="en-GB", og_locale="en_GB",
        og_image_alt="Clwydian Academy — fast-track hairdressing training in North Wales",
        home="/", home_label="Clwydian Academy — home",
        skip="Skip to content", menu="Menu", nav_label="Primary",
        switch_label="Cymraeg",
        register=("/contact/#register", "Register interest"),
        tagline="Fast-track vocational hairdressing training in St Asaph — named for the Clwydian Range, built for career-changers across North Wales and the border counties.",
        courses_label="Courses",
        courses=[("/courses/nvq-level-2-hairdressing/", "NVQ Level 2 Hairdressing"),
                 ("/courses/nvq-level-2-barbering/", "NVQ Level 2 Barbering"),
                 ("/courses/nvq-level-3-hairdressing/", "NVQ Level 3 Hairdressing"),
                 ("/courses/cpd-courses/", "CPD for Professionals"),
                 ("/funding/", "Fees &amp; Funding")],
        academy_label="Academy",
        academy=[("/about/", "About &amp; Mission"),
                 ("/apprenticeships/", "Apprenticeships"),
                 ("/for-salons/", "For Salons"),
                 ("/funders/", "Funders &amp; Partners"),
                 ("/contact/", "Contact")],
        visit_label="Visit &amp; Contact",
        address=("St Asaph", "Denbighshire, North Wales"),
        legal={
            "plain": "&copy; 2026 Clwydian Academy CBC — a community benefit company, constituted as a Community Interest Company.",
            "registered": "&copy; 2026 Clwydian Academy CBC (Cwmni Buddiant Cymunedol) &middot; Company no. 17330962 &middot; Registered office: 2 Bod Hyfryd, Rhes-y-Cae, Holywell CH8 8JG.",
        },
        privacy=("/privacy/", "Privacy"),
    ),
    "cy": dict(
        html_lang="cy", og_locale="cy_GB",
        og_image_alt="Clwydian Academy — hyfforddiant trin gwallt carlam yng Ngogledd Cymru",
        home="/cy/", home_label="Clwydian Academy — hafan",
        skip="Neidio i&rsquo;r cynnwys", menu="Dewislen", nav_label="Prif ddewislen",
        switch_label="English",
        register=("/cy/cysylltu/#register", "Cofrestru diddordeb"),
        tagline="Hyfforddiant trin gwallt galwedigaethol carlam yn Llanelwy — wedi&rsquo;i enwi ar &ocirc;l Bryniau Clwyd, ac wedi&rsquo;i adeiladu ar gyfer pobl sy&rsquo;n newid gyrfa ledled Gogledd Cymru a&rsquo;r gororau.",
        courses_label="Cyrsiau",
        courses=[("/cy/cyrsiau/trin-gwallt-nvq-lefel-2/", "Trin Gwallt NVQ Lefel 2"),
                 ("/cy/cyrsiau/barbro-nvq-lefel-2/", "Barbro NVQ Lefel 2"),
                 ("/cy/cyrsiau/trin-gwallt-nvq-lefel-3/", "Trin Gwallt NVQ Lefel 3"),
                 ("/cy/cyrsiau/cyrsiau-dpp/", "DPP i Weithwyr Proffesiynol"),
                 ("/cy/ffioedd-a-chyllid/", "Ffioedd a Chyllid")],
        academy_label="Yr Academi",
        academy=[("/cy/amdanom/", "Amdanom a&rsquo;n Cenhadaeth"),
                 ("/cy/prentisiaethau/", "Prentisiaethau"),
                 ("/cy/i-salonau/", "I Salonau"),
                 ("/cy/cyllidwyr/", "Cyllidwyr a Phartneriaid"),
                 ("/cy/cysylltu/", "Cysylltu")],
        visit_label="Ymweld a Chysylltu",
        address=("Llanelwy (St Asaph)", "Sir Ddinbych, Gogledd Cymru"),
        legal={
            "plain": "&copy; 2026 Clwydian Academy CBC — cwmni budd cymunedol, wedi&rsquo;i gyfansoddi fel Cwmni Buddiannau Cymunedol.",
            "registered": "&copy; 2026 Clwydian Academy CBC (Cwmni Buddiant Cymunedol) &middot; Rhif cwmni 17330962 &middot; Swyddfa gofrestredig: 2 Bod Hyfryd, Rhes-y-Cae, Treffynnon CH8 8JG.",
        },
        privacy=("/cy/preifatrwydd/", "Preifatrwydd"),
    ),
}

FONTS = ("https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600"
         "&family=IBM+Plex+Mono:wght@500&family=Inter:wght@400;500;600&family=Jost:wght@400;600&display=swap")

def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "</script>"

def other(loc):
    return "cy" if loc == "en" else "en"

def out_path(path):
    return path.lstrip("/") if path.endswith(".html") else path.strip("/") + "/index.html" if path != "/" else "index.html"

def head(page, loc, jsonld):
    c, me = CHROME[loc], page[loc]
    url = DOMAIN + me["path"]
    lines = [
        "<!doctype html>",
        f'<html lang="{c["html_lang"]}">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{me['title']}</title>",
        f'<meta name="description" content="{me["desc"]}">',
    ]
    if page.get("noindex"):
        lines.append('<meta name="robots" content="noindex, nofollow">')
    lines.append(f'<link rel="canonical" href="{url}">')
    if page.get("cy"):
        lines += [
            f'<link rel="alternate" hreflang="en" href="{DOMAIN}{page["en"]["path"]}">',
            f'<link rel="alternate" hreflang="cy" href="{DOMAIN}{page["cy"]["path"]}">',
            f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}{page["en"]["path"]}">',
        ]
    lines += [
        '<meta name="theme-color" content="#574463">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Clwydian Academy">',
        f'<meta property="og:title" content="{me["title"]}">',
        f'<meta property="og:description" content="{me["desc"]}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{DOMAIN}/assets/img/og-image.png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{c["og_image_alt"]}">',
        f'<meta property="og:locale" content="{c["og_locale"]}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{me["title"]}">',
        f'<meta name="twitter:description" content="{me["desc"]}">',
        f'<meta name="twitter:image" content="{DOMAIN}/assets/img/og-image.png">',
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
        '<link rel="icon" href="/favicon.ico" sizes="32x32">',
        '<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">',
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        f'<link href="{FONTS}" rel="stylesheet">',
        '<link rel="stylesheet" href="/assets/css/main.css">',
        ld(ORG),
    ]
    lines += [ld(block) for block in jsonld]
    lines += ['<script src="/assets/js/main.js" defer></script>', "</head>"]
    return "\n".join(lines)

def header(page, loc):
    c = CHROME[loc]
    links = []
    for item in NAV:
        href, label = item[loc]
        cur = ' aria-current="page"' if page.get("nav") == item["en"][0] else ""
        links.append(f'<a href="{href}"{cur}>{label}</a>')
    o = other(loc)
    if page.get(o):
        links.append(f'<a class="lang-switch" href="{page[o]["path"]}" lang="{o}" hreflang="{o}">{c["switch_label"]}</a>')
    links.append(f'<a class="btn btn-primary btn-sm" href="{c["register"][0]}">{c["register"][1]}</a>')
    nav = "\n      ".join(links)
    return f'''<body>
<a class="skip-link" href="#main">{c["skip"]}</a>
<header class="site-header">
  <div class="wrap header-bar">
    <a class="brand" href="{c["home"]}" aria-label="{c["home_label"]}">
      <img class="brand-seal" src="/assets/img/seal.svg" alt="" width="42" height="42">
      <span class="brand-divider" aria-hidden="true"></span>
      <span class="brand-text">
        <span class="brand-name">Clwydian</span>
        <span class="brand-sub">Academy&nbsp;&middot;&nbsp;CBC</span>
      </span>
    </a>
    <button class="nav-toggle" aria-expanded="false" aria-controls="site-nav" aria-label="{c["menu"]}">
      <span></span><span></span><span></span>
    </button>
    <nav class="site-nav" id="site-nav" aria-label="{c["nav_label"]}">
      {nav}
    </nav>
  </div>
</header>
<main id="main">'''

def footer(page, loc):
    c = CHROME[loc]
    li = lambda items: "\n".join(f'          <li><a href="{h}">{l}</a></li>' for h, l in items)
    return f'''</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-brand">
        <a class="brand" href="{c["home"]}" aria-label="{c["home_label"]}">
          <img class="brand-seal" src="/assets/img/seal.svg" alt="" width="42" height="42">
          <span class="brand-divider" aria-hidden="true"></span>
          <span class="brand-text">
            <span class="brand-name">Clwydian</span>
            <span class="brand-sub" style="color:var(--gold)">Academy&nbsp;&middot;&nbsp;CBC</span>
          </span>
        </a>
        <p>{c["tagline"]}</p>
      </div>
      <nav class="footer-col" aria-label="{c["courses_label"]}">
        <h4>{c["courses_label"]}</h4>
        <ul>
{li(c["courses"])}
        </ul>
      </nav>
      <nav class="footer-col" aria-label="{c["academy_label"]}">
        <h4>{c["academy_label"]}</h4>
        <ul>
{li(c["academy"])}
        </ul>
      </nav>
      <div class="footer-col">
        <h4>{c["visit_label"]}</h4>
        <address>
          {c["address"][0]}<br>
          {c["address"][1]}<br>
          <a href="mailto:markp@charlotteeleanorgroup.uk">markp@charlotteeleanorgroup.uk</a><br>
          <a href="tel:+447714198743">07714 198743</a>
        </address>
      </div>
    </div>
    <div class="footer-legal">
      <span>{c["legal"][page.get("legal", "plain")]}</span>
      <span><a href="{c["privacy"][0]}">{c["privacy"][1]}</a></span>
    </div>
  </div>
</footer>
</body>
</html>
'''

def read(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()

def write(rel, text):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def build():
    if not os.path.isdir(OUT):
        sys.exit(f"build: output directory missing: {OUT}")
    pages = json.loads(read("pages.json"))
    urls = {"en": [], "cy": []}
    for page in pages:
        for loc in LOCALES:
            if not page.get(loc):
                continue
            body = read("pages", loc, page["key"] + ".html")
            jsonld = json.loads(read("jsonld", loc, page["key"] + ".json"))
            html = head(page, loc, jsonld) + "\n" + header(page, loc) + "\n" + body + footer(page, loc)
            rel = out_path(page[loc]["path"])
            write(rel, html)
            if not page.get("noindex"):
                urls[loc].append(page)
            print("built", rel)

    today = datetime.date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for loc in LOCALES:
        for page in urls[loc]:
            en, cy = DOMAIN + page["en"]["path"], DOMAIN + page["cy"]["path"]
            sm += [f'  <url><loc>{DOMAIN + page[loc]["path"]}</loc><lastmod>{today}</lastmod><priority>{page["priority"]}</priority>',
                   f'    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>',
                   f'    <xhtml:link rel="alternate" hreflang="cy" href="{cy}"/>',
                   f'    <xhtml:link rel="alternate" hreflang="x-default" href="{en}"/>',
                   "  </url>"]
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    n = sum(len(v) for v in urls.values())
    print(f"built sitemap.xml ({n} urls), robots.txt")

if __name__ == "__main__":
    build()
