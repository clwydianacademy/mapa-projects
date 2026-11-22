#!/usr/bin/env python3
"""Assemble the Clwydian Academy static site from body fragments + shared chrome, in two locales.

    python3 website/_src/build.py                    # writes into site/
    python3 scripts/check_claims.py "site"

Every fact in ORG and the chrome below must agree with /CLAUDE.md. The body fragments in
pages/ and the page-specific JSON-LD in jsonld/ were extracted from the deployed HTML in
Brief 01 (extract.py); the registry in pages.json says which fragment goes where, in which
language, with which title and description.

Output goes to `site` — the Vercel root directory. Nothing is written for
GitHub Pages (no CNAME, no .nojekyll); that hosting is dead.
"""
import datetime, json, os, subprocess, sys
import html as html_mod

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cpd   # everything rendered from _data/cpd-2027.json
import salon # the training salon's pages, rendered from _data/salon/policy.json
import showcase # the three-path home page, learner work, Find us, the statutory footer — behind its own switch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "site")
DOMAIN = "https://www.clwydianacademy.co.uk"   # canonical host; the apex 301s here at Vercel
LOCALES = ("en", "cy")
SITE = cpd.site()   # _data/site.json: the one contact address, the company number, the registered office

# Organization — one block, both languages: the live homepage block of 11 Sep 2026 plus the
# current legalName and Companies House identifier (COWORK VERIFICATION 01, decision 2).
# No parentOrganization, no OLD legalName: see CLAUDE.md "The entity".
# Privacy (PM decision, 17 Nov 2026): the organisation only — no telephone, no founder or Person,
# no personal profile links. scripts/check_claims.py fails the build if any of them returns.
ORG = {
    "@context": "https://schema.org",
    "@type": "EducationalOrganization",
    "@id": DOMAIN + "/#organization",
    "name": "Clwydian Academy",
    "alternateName": "Clwydian Academy CBC",
    "legalName": "Clwydian Academy CBC",
    "description": "Fast-track vocational hairdressing and barbering academy in St Asaph, North Wales. VTCT-standard NVQ diplomas, CPD masterclasses and Welsh-framework apprenticeships, with fully funded routes for eligible learners.",
    "url": DOMAIN + "/",
    "logo": DOMAIN + "/assets/img/seal-512.png",
    "image": DOMAIN + "/assets/img/og-image.png",
    "email": SITE["email"],
    "foundingDate": "2026",
    "identifier": {"@type": "PropertyValue", "propertyID": "Companies House", "value": SITE["company_number"]},
    "knowsLanguage": ["en", "cy"],
    "address": {"@type": "PostalAddress", "addressLocality": "St Asaph", "addressRegion": "Denbighshire", "addressCountry": "GB"},
    "areaServed": ["North Wales", "Denbighshire", "Conwy", "Flintshire", "Wrexham", "Chester", "Cheshire", "North West England"],
}

# Primary navigation: one list, both languages. A page's "nav" in pages.json is the EN path.
NAV = [
    {"en": ("/courses/", "Courses"),               "cy": ("/cy/cyrsiau/", "Cyrsiau")},
    {"en": ("/apprenticeships/", "Apprenticeships"), "cy": ("/cy/prentisiaethau/", "Prentisiaethau")},
    {"en": ("/funding/", "Fees &amp; Funding"),    "cy": ("/cy/ffioedd-a-chyllid/", "Ffioedd a Chyllid")},
    {"en": ("/for-salons/", "For Salons"),         "cy": ("/cy/i-salonau/", "I Salonau")},
    {"en": ("/about/", "About"),                   "cy": ("/cy/amdanom/", "Amdanom")},
    {"en": ("/guides/", "Guides"),                 "cy": ("/cy/canllawiau/", "Canllawiau")},
    {"en": ("/contact/", "Contact"),               "cy": ("/cy/cysylltu/", "Cysylltu")},
]

# The training salon's nav item. Added to NAV only while the salon is public — see salon.is_public().
SALON_NAV = {"en": ("/salon/", "Our Salon"), "cy": ("/cy/salon/", "Ein Salon")}
SALON_ON = salon.is_public()      # build() may force this on for a preview build in a scratch folder

# The showcase switch (_data/showcase.json). Off: this file builds exactly what it built before
# showcase.py existed. A preview build forces it on, like the salon's.
WORK_NAV = {"en": ("/work/", "Learner Work"), "cy": ("/cy/gwaith/", "Gwaith Dysgwyr")}
SHOWCASE_ON = showcase.is_public()
PREVIEW = False

def nav_items():
    extra = ([SALON_NAV] if SALON_ON else []) + ([WORK_NAV] if SHOWCASE_ON else [])
    if not extra:
        return NAV
    at = next(i for i, item in enumerate(NAV) if item["en"][0] == "/for-salons/") + 1
    return NAV[:at] + extra + NAV[at:]

def is_showcase(page):
    return str(page.get("generated") or "").startswith("showcase")

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
                 ("/courses/cpd-calendar/", "CPD calendar 2027"),
                 ("/funding/", "Fees &amp; Funding")],
        academy_label="Academy",
        academy=[("/about/", "About &amp; Mission"),
                 ("/apprenticeships/", "Apprenticeships"),
                 ("/for-salons/", "For Salons"),
                 ("/guides/", "Guides"),
                 ("/contact/", "Contact")],
        visit_label="Visit &amp; Contact",
        address=("St Asaph", "Denbighshire, North Wales"),
        legal={
            "plain": "&copy; 2026 Clwydian Academy CBC — a community benefit company, constituted as a Community Interest Company.",
            "registered": "&copy; 2026 Clwydian Academy CBC (Cwmni Buddiant Cymunedol) &middot; Company no. " + SITE["company_number"] + " &middot; Registered office: " + SITE["registered_office"]["en"] + ".",
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
                 ("/cy/cyrsiau/calendr-dpp/", "Calendr DPP 2027"),
                 ("/cy/ffioedd-a-chyllid/", "Ffioedd a Chyllid")],
        academy_label="Yr Academi",
        academy=[("/cy/amdanom/", "Amdanom a&rsquo;n Cenhadaeth"),
                 ("/cy/prentisiaethau/", "Prentisiaethau"),
                 ("/cy/i-salonau/", "I Salonau"),
                 ("/cy/canllawiau/", "Canllawiau"),
                 ("/cy/cysylltu/", "Cysylltu")],
        visit_label="Ymweld a Chysylltu",
        address=("Llanelwy (St Asaph)", "Sir Ddinbych, Gogledd Cymru"),
        legal={
            "plain": "&copy; 2026 Clwydian Academy CBC — cwmni budd cymunedol, wedi&rsquo;i gyfansoddi fel Cwmni Buddiannau Cymunedol.",
            "registered": "&copy; 2026 Clwydian Academy CBC (Cwmni Buddiant Cymunedol) &middot; Rhif cwmni " + SITE["company_number"] + " &middot; Swyddfa gofrestredig: " + SITE["registered_office"]["cy"] + ".",
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

def is_salon(page):
    return str(page.get("generated") or "").startswith("salon")

def hidden(page):
    """Not to be indexed: a page marked noindex, and EVERY salon page while any value in
    _data/salon/policy.json is still a placeholder — nothing unconfirmed goes out to a search engine."""
    return bool(page.get("noindex")) or (is_salon(page) and not salon.confirmed())

def head(page, loc, jsonld):
    c, me = CHROME[loc], page[loc]
    if SHOWCASE_ON and page["key"] in showcase.META:
        title, desc = showcase.META[page["key"]][loc]
        me = dict(me, title=title, desc=desc)
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
    if hidden(page):
        lines.append('<meta name="robots" content="noindex, nofollow">')
    lines.append(f'<link rel="canonical" href="{url}">')
    if page.get("cy") and SHOWCASE_ON:
        lines += showcase.hreflang_links(page, DOMAIN)       # en-GB, cy, x-default: checked both ways at the end of the build
    elif page.get("cy"):
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
    ]
    if SHOWCASE_ON:
        # The faces come from our own origin (showcase.css): no request to a font service.
        lines += ['<link rel="preload" href="/assets/fonts/inter-400-700.woff2" as="font" type="font/woff2" crossorigin>',
                  '<link rel="preload" href="/assets/fonts/fraunces-600.woff2" as="font" type="font/woff2" crossorigin>',
                  '<link rel="stylesheet" href="/assets/css/main.css">',
                  '<link rel="stylesheet" href="/assets/css/showcase.css">']
    else:
        lines += ['<link rel="preconnect" href="https://fonts.googleapis.com">',
                  '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
                  f'<link href="{FONTS}" rel="stylesheet">',
                  '<link rel="stylesheet" href="/assets/css/main.css">']
    lines += [
        # without JavaScript the menu button cannot open the menu: show the links instead
        '<noscript><link rel="stylesheet" href="/assets/css/nojs.css"></noscript>',
    ]
    if is_salon(page):
        lines.append('<link rel="stylesheet" href="/assets/css/salon.css">')
    lines.append(ld(ORG))
    lines += [ld(block) for block in jsonld]
    lines.append('<script src="/assets/js/main.js" defer></script>')
    if SHOWCASE_ON:
        lines.append('<script src="/assets/js/showcase.js" defer></script>')
    lines.append("</head>")
    return "\n".join(lines)

def header(page, loc):
    c = CHROME[loc]
    links = []
    for item in nav_items():
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
    if SHOWCASE_ON:
        # The statutory line on EVERY page, and the one address, both from _data/site.json.
        c = dict(c, address=tuple(showcase.address_text(loc, SITE).split(", ", 1)),
                 legal={k: '<span class="sc-legal">' + showcase.legal_line(loc, SITE) + "</span>" for k in c["legal"]})
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
          <a href="mailto:{SITE["email"]}">{SITE["email"]}</a>
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

def lastmod(page, loc, fallback):
    """Date of the last commit touching this page's sources; the build date if none.
    Sources are the fragment and JSON-LD, plus the CPD data and cpd.py for pages that render from them."""
    if is_showcase(page) or (SHOWCASE_ON and page["key"] == "home"):
        paths = showcase.SOURCES
    elif is_salon(page):
        paths = [salon.DATA_PATH, os.path.join(HERE, "salon.py")]
    elif page.get("generated"):
        paths = [cpd.DATA_PATH, os.path.join(HERE, "cpd.py")]
    else:
        paths = [os.path.join("pages", loc, page["key"] + ".html"), os.path.join("jsonld", loc, page["key"] + ".json")]
        if page.get("cpd_unit"):
            paths += [cpd.DATA_PATH, os.path.join(HERE, "cpd.py")]
    try:
        out = subprocess.run(["git", "--no-optional-locks", "log", "-1", "--format=%cI", "--", *paths],
                             cwd=HERE, capture_output=True, text=True, check=True).stdout.strip()
        return out[:10] if out else fallback
    except (subprocess.CalledProcessError, FileNotFoundError):
        return fallback

def read(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()

def write(rel, text):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:   # LF on every OS
        f.write(text)

def redirects(pages):
    """_data/redirects.json -> vercel.json in the deployed folder: one permanent 301 per retired URL.

    Each URL is listed with and without its trailing slash, so both forms redirect whatever
    Vercel's trailing-slash setting is. A redirect whose target is not a built page, or whose
    source is still a page in the registry, fails the build. A built page left behind at a
    retired URL is deleted, so a retired page cannot linger in the deployed folder."""
    with open(os.path.join(REPO, "_data", "redirects.json"), encoding="utf-8") as f:
        wanted = json.load(f)["redirects"]
    live = {p[loc]["path"] for p in pages for loc in LOCALES if p.get(loc)}
    rules = []
    for r in wanted:
        src, dst = r["from"], r["to"]
        if not (src.startswith("/") and src.endswith("/") and len(src) > 1):
            sys.exit(f"build: redirects.json: 'from' must look like /old-page/ — got {src!r}")
        if src in live:
            sys.exit(f"build: redirects.json: {src} is still a page in pages.json — remove the page or the redirect")
        if dst not in live:
            sys.exit(f"build: redirects.json: {src} redirects to {dst}, which is not a built page")
        for form in (src.rstrip("/"), src):
            rules.append({"source": form, "destination": dst, "statusCode": 301})
        stale = os.path.join(OUT, out_path(src))
        if os.path.exists(stale):
            os.remove(stale)
            try: os.rmdir(os.path.dirname(stale))
            except OSError: pass
            print("removed retired page", out_path(src))
    write("vercel.json", json.dumps({"redirects": rules}, indent=2) + "\n")
    return len(wanted)

def build():
    if not os.path.isdir(OUT):
        sys.exit(f"build: output directory missing: {OUT}")
    # Vercel names each serverless function by its path from the repository root and refuses a
    # name with a space in it (invalid_function_name). That is why this folder is `site` and not
    # `clwydian-academy 2`: the deployment of 17 Nov 2026 failed on exactly this.
    for dirpath, _dirs, files in os.walk(os.path.join(OUT, "api")):
        for fn in files:
            rel = os.path.relpath(os.path.join(dirpath, fn), REPO).replace(os.sep, "/")
            if " " in rel:
                sys.exit(f"build: {rel!r} contains a space — Vercel will refuse to deploy this function")
    pages = json.loads(read("pages.json"))
    if SALON_ON and not os.path.exists(os.path.join(OUT, "assets", "css", "salon.css")):
        sys.exit("build: /assets/css/salon.css is missing — the salon pages load it")
    cpd.configure(DOMAIN, next(p for p in pages if p.get("generated") == "cpd-calendar"))
    urls = {"en": [], "cy": []}
    built = {}
    if SHOWCASE_ON:
        missing = showcase.legal_todos(SITE)
        if missing and not PREVIEW:
            sys.exit("build: the showcase cannot be public: _data/site.json legal." + ", legal.".join(missing)
                     + " is still TODO_PM — the trading disclosure would be incomplete on every page")
        showcase.copy_assets(OUT)
    else:
        showcase.remove_assets(OUT)
    for page in pages:
        for loc in LOCALES:
            if not page.get(loc):
                continue
            if is_salon(page) and not SALON_ON:
                # THE SWITCH IS OFF: the page is not built, and one left over from an earlier
                # build is removed, so the deployed folder holds no trace of the salon.
                stale = os.path.join(OUT, out_path(page[loc]["path"]))
                if os.path.exists(stale):
                    os.remove(stale)
                    try: os.removedirs(os.path.dirname(stale))
                    except OSError: pass
                    print("removed (salon not public)", out_path(page[loc]["path"]))
                continue
            if is_showcase(page) and not SHOWCASE_ON:
                stale = os.path.join(OUT, out_path(page[loc]["path"]))
                if os.path.exists(stale):
                    os.remove(stale)
                    try: os.removedirs(os.path.dirname(stale))
                    except OSError: pass
                    print("removed (showcase not public)", out_path(page[loc]["path"]))
                continue
            if is_showcase(page):
                body, jsonld = showcase.work_body(loc, SITE), []
            elif SHOWCASE_ON and page["key"] == "home":
                body = showcase.home_body(loc, SITE)
                jsonld = json.loads(read("jsonld", loc, "home.json"))
            elif is_salon(page):
                body = salon.body(page["generated"], loc, SITE)
                jsonld = salon.jsonld(page["generated"], loc, DOMAIN, ORG, SITE)
                if SHOWCASE_ON and page["generated"] == "salon":
                    body += showcase.find_us(loc, SITE)
                    jsonld = showcase.hairsalon_ld(loc, DOMAIN, ORG, SITE)
            elif page.get("generated") == "cpd-calendar":
                body = cpd.calendar_body(loc, page)
                jsonld = cpd.calendar_jsonld(loc, page)
            else:
                body = read("pages", loc, page["key"] + ".html")
                raw_ld = read("jsonld", loc, page["key"] + ".json")
                if "{{" in raw_ld:                             # tokens in structured data render as plain text, not entities
                    raw_ld = html_mod.unescape(cpd.render(raw_ld, loc))
                jsonld = json.loads(raw_ld)
            if "<!-- cpd-dates -->" in body:
                body = body.replace("<!-- cpd-dates -->", cpd.date_rows(loc, page))
                jsonld = cpd.enrich(jsonld, loc, page)
            body = cpd.render(body, loc)                       # {{cpd:...}} facts from the data file
            page = dict(page, **{loc: dict(page[loc], title=cpd.render(page[loc]["title"], loc), desc=cpd.render(page[loc]["desc"], loc))})
            if SHOWCASE_ON:
                # The questions and answers stay on the page as plain, visible content. Their
                # FAQPage markup goes: Google ended FAQ rich results on 7 May 2026.
                jsonld = [b for b in (jsonld if isinstance(jsonld, list) else [jsonld]) if b.get("@type") != "FAQPage"]
                showcase.check_ld([ORG] + list(jsonld), page[loc]["path"])
            html = head(page, loc, jsonld) + "\n" + header(page, loc) + "\n" + body + footer(page, loc)
            if SHOWCASE_ON:
                # Two accessibility faults in the shared chrome, put right with the showcase: the
                # footer's headings skipped a level (h4 straight after h2; now h2), and the brand link's accessible
                # name did not contain the words it shows.
                foot = html.index('<footer class="site-footer">')
                html = html[:foot] + html[foot:].replace("<h4>", '<h2 class="footer-h">').replace("</h4>", "</h2>")
                html = html.replace(f'aria-label="{CHROME[loc]["home_label"]}"', 'aria-label="Clwydian Academy &middot; CBC &mdash; ' + ("home" if loc == "en" else "hafan") + '"')
            if SHOWCASE_ON:
                built[page[loc]["path"]] = html
            rel = out_path(page[loc]["path"])
            write(rel, html)
            if not hidden(page):
                urls[loc].append(page)
            print("built", rel)

    if SHOWCASE_ON:
        showcase.check_hreflang(pages, built, DOMAIN)
    today = datetime.date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for loc in LOCALES:
        for page in urls[loc]:
            en, cy = DOMAIN + page["en"]["path"], DOMAIN + page["cy"]["path"]
            sm += [f'  <url><loc>{DOMAIN + page[loc]["path"]}</loc><lastmod>{lastmod(page, loc, today)}</lastmod><priority>{page["priority"]}</priority>',
                   f'    <xhtml:link rel="alternate" hreflang="{"en-GB" if SHOWCASE_ON else "en"}" href="{en}"/>',
                   f'    <xhtml:link rel="alternate" hreflang="cy" href="{cy}"/>',
                   f'    <xhtml:link rel="alternate" hreflang="x-default" href="{en}"/>',
                   "  </url>"]
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    if SALON_ON:
        todo, draft = salon.todo_paths(salon.raw()), salon.draft_paths(salon.raw())
        print(f"salon: ON — {len(todo)} placeholder(s) and {len(draft)} draft value(s): salon pages are "
              + ("noindex and out of the sitemap" if todo or draft else "indexed"))
    else:
        print("salon: OFF — no salon page and no nav item built (\"public\" is false in _data/salon/policy.json)")
    if SHOWCASE_ON:
        todo = showcase.legal_todos(SITE)
        print("showcase: ON" + (" (PREVIEW)" if PREVIEW else "") + " — hreflang pairs checked on " + str(len(built)) + " pages"
              + (f"; STILL TODO_PM before it can be public: legal.{', legal.'.join(todo)}" if todo else "")
              + ("" if showcase.address_confirmed(SITE) else "; the unit and postcode are TODO_PM (park and town shown)"))
    else:
        print("showcase: OFF — the home page, footer and fonts are main's; no /work/ page (\"public\" is false in _data/showcase.json)")
    n = sum(len(v) for v in urls.values())
    r = redirects(pages)
    print(f"built sitemap.xml ({n} urls), robots.txt, vercel.json ({r} redirected urls)")

if __name__ == "__main__":
    # `build.py --salon-preview DIR`: copy the deployed folder to DIR and build THERE with the salon
    # switched on. For looking at the salon pages, and for scripts/test_salon_pages.js, without
    # putting anything into the folder that is deployed. DIR must not be inside the repository.
    if len(sys.argv) == 3 and sys.argv[1] == "--salon-preview":
        import shutil
        target = os.path.abspath(sys.argv[2])
        if target == OUT or target.startswith(REPO + os.sep):
            sys.exit("build: --salon-preview must write outside the repository")
        shutil.copytree(OUT, target, dirs_exist_ok=True)
        OUT, SALON_ON = target, True
    elif len(sys.argv) == 3 and sys.argv[1] == "--preview":
        # `build.py --preview DIR`: everything ON — the salon and the showcase — in a scratch folder.
        import shutil
        target = os.path.abspath(sys.argv[2])
        if target == OUT or target.startswith(REPO + os.sep):
            sys.exit("build: --preview must write outside the repository")
        shutil.copytree(OUT, target, dirs_exist_ok=True)
        OUT, SALON_ON, SHOWCASE_ON, PREVIEW = target, True, True, True
    elif len(sys.argv) > 1:
        sys.exit("usage: build.py [--salon-preview DIR | --preview DIR]")
    build()
