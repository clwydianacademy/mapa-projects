#!/usr/bin/env python3
"""Assemble the Clwydian Academy static site from body fragments + shared chrome."""
import json, os, datetime

SRC = "/sessions/practical-exciting-tesla/mnt/outputs/_src/pages"
OUT = "/sessions/practical-exciting-tesla/mnt/outputs/clwydian-academy"
DOMAIN = "https://clwydianacademy.co.uk"

ORG = {
    "@context": "https://schema.org",
    "@type": "EducationalOrganization",
    "@id": DOMAIN + "/#organization",
    "name": "Clwydian Academy",
    "alternateName": "Charlotte Eleanor Academy CIC",
    "legalName": "Charlotte Eleanor Academy C.I.C.",
    "description": "Fast-track vocational hairdressing academy in Deeside, North Wales. VTCT-standard NVQ Level 2 and Level 3 training for adults in six months, free for eligible Welsh adults through the Personal Learning Account.",
    "url": DOMAIN + "/",
    "logo": DOMAIN + "/assets/img/seal-512.png",
    "image": DOMAIN + "/assets/img/og-image.png",
    "email": "markp@charlotteeleanorgroup.uk",
    "telephone": "+447714198743",
    "foundingDate": "2026",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "Deeside Industrial Park",
        "addressLocality": "Deeside",
        "addressRegion": "Flintshire",
        "addressCountry": "GB",
    },
    "areaServed": ["North Wales", "Flintshire", "Wrexham", "Chester", "Cheshire", "Merseyside", "North West England"],
    "parentOrganization": {"@type": "Organization", "name": "Charlotte Eleanor Group"},
    "sameAs": [],
}

NAV = [
    ("/courses/", "Courses"),
    ("/funding/", "Fees &amp; Funding"),
    ("/for-salons/", "For Salons"),
    ("/about/", "About"),
    ("/funders/", "Funders"),
    ("/contact/", "Contact"),
]

def head(p):
    lines = [
        '<!doctype html>',
        '<html lang="en-GB">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{p['title']}</title>",
        f'<meta name="description" content="{p["desc"]}">',
    ]
    if p.get("noindex"):
        lines.append('<meta name="robots" content="noindex, nofollow">')
    url = DOMAIN + p["path"]
    lines += [
        f'<link rel="canonical" href="{url}">',
        '<meta name="theme-color" content="#574463">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Clwydian Academy">',
        f'<meta property="og:title" content="{p["title"]}">',
        f'<meta property="og:description" content="{p["desc"]}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{DOMAIN}/assets/img/og-image.png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:image:alt" content="Clwydian Academy — fast-track hairdressing training in North Wales">',
        '<meta property="og:locale" content="en_GB">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{p["title"]}">',
        f'<meta name="twitter:description" content="{p["desc"]}">',
        f'<meta name="twitter:image" content="{DOMAIN}/assets/img/og-image.png">',
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
        '<link rel="icon" href="/favicon.ico" sizes="32x32">',
        '<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">',
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=IBM+Plex+Mono:wght@500&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">',
        '<link rel="stylesheet" href="/assets/css/main.css">',
        f'<script type="application/ld+json">{json.dumps(ORG, separators=(",", ":"))}</script>',
    ]
    for ld in p.get("jsonld", []):
        lines.append(f'<script type="application/ld+json">{json.dumps(ld, separators=(",", ":"))}</script>')
    lines += ['<script src="/assets/js/main.js" defer></script>', "</head>"]
    return "\n".join(lines)

def header(p):
    links = []
    for href, label in NAV:
        cur = ' aria-current="page"' if p.get("nav") == href else ""
        links.append(f'<a href="{href}"{cur}>{label}</a>')
    links.append('<a class="btn btn-primary btn-sm" href="/contact/#register">Register interest</a>')
    nav = "\n      ".join(links)
    return f'''<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap header-bar">
    <a class="brand" href="/" aria-label="Clwydian Academy — home">
      <img class="brand-seal" src="/assets/img/seal.svg" alt="" width="42" height="42">
      <span class="brand-text">
        <span class="brand-name">Clwydian</span>
        <span class="brand-sub">Academy&nbsp;&middot;&nbsp;CBC</span>
      </span>
    </a>
    <button class="nav-toggle" aria-expanded="false" aria-controls="site-nav" aria-label="Menu">
      <span></span><span></span><span></span>
    </button>
    <nav class="site-nav" id="site-nav" aria-label="Primary">
      {nav}
    </nav>
  </div>
</header>
<main id="main">'''

FOOTER = f'''</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-brand">
        <a class="brand" href="/" aria-label="Clwydian Academy — home">
          <img class="brand-seal" src="/assets/img/seal.svg" alt="" width="42" height="42">
          <span class="brand-text">
            <span class="brand-name">Clwydian</span>
            <span class="brand-sub" style="color:var(--gold)">Academy&nbsp;&middot;&nbsp;CBC</span>
          </span>
        </a>
        <p>Fast-track vocational hairdressing training in Deeside — named for the Clwydian Range, built for career-changers across North Wales and the border counties.</p>
      </div>
      <nav class="footer-col" aria-label="Courses">
        <h4>Courses</h4>
        <ul>
          <li><a href="/courses/nvq-level-2-hairdressing/">NVQ Level 2 Hairdressing</a></li>
          <li><a href="/courses/nvq-level-3-hairdressing/">NVQ Level 3 Hairdressing</a></li>
          <li><a href="/courses/cpd-courses/">CPD for Professionals</a></li>
          <li><a href="/funding/">Fees &amp; PLA Funding</a></li>
        </ul>
      </nav>
      <nav class="footer-col" aria-label="Academy">
        <h4>Academy</h4>
        <ul>
          <li><a href="/about/">About &amp; Mission</a></li>
          <li><a href="/for-salons/">For Salons</a></li>
          <li><a href="/funders/">Funders &amp; Partners</a></li>
          <li><a href="/contact/">Contact</a></li>
        </ul>
      </nav>
      <div class="footer-col">
        <h4>Visit &amp; Contact</h4>
        <address>
          Deeside Industrial Park<br>
          Deeside, Flintshire<br>
          North Wales<br>
          <a href="mailto:markp@charlotteeleanorgroup.uk">markp@charlotteeleanorgroup.uk</a><br>
          <a href="tel:+447714198743">07714 198743</a>
        </address>
      </div>
    </div>
    <div class="footer-legal">
      <span>&copy; 2026 Clwydian Academy. Clwydian Academy is the trading name of Charlotte Eleanor Academy C.I.C., a Community Interest Company — part of the Charlotte Eleanor Group.</span>
      <span><a href="/privacy/">Privacy</a></span>
    </div>
  </div>
</footer>
</body>
</html>'''

def crumbs_ld(items):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": DOMAIN + u}
            for i, (n, u) in enumerate(items)
        ],
    }

def course_ld(name, url, desc, price_note, level):
    return {
        "@context": "https://schema.org",
        "@type": "Course",
        "@id": DOMAIN + url + "#course",
        "name": name,
        "description": desc,
        "provider": {"@id": DOMAIN + "/#organization"},
        "url": DOMAIN + url,
        "educationalCredentialAwarded": name.split("—")[0].strip(),
        "coursePrerequisites": "Open to adults aged 19+. No prior hairdressing experience required." if level == 2 else "NVQ Level 2 Hairdressing or equivalent qualification / salon experience.",
        "offers": [
            {"@type": "Offer", "category": "Paid", "price": "4500", "priceCurrency": "GBP", "description": "Self-funded place"},
            {"@type": "Offer", "category": "Free", "price": "0", "priceCurrency": "GBP", "description": price_note},
        ],
        "hasCourseInstance": {
            "@type": "CourseInstance",
            "courseMode": "Blended",
            "courseWorkload": "P6M",
            "courseSchedule": {"@type": "Schedule", "repeatFrequency": "Weekly", "repeatCount": 26},
            "location": {"@type": "Place", "name": "Clwydian Academy, Deeside", "address": {"@type": "PostalAddress", "addressLocality": "Deeside", "addressRegion": "Flintshire", "addressCountry": "GB"}},
        },
    }

FAQ_FUNDING = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {"@type": "Question", "name": "Is hairdressing training really free in Wales?", "acceptedAnswer": {"@type": "Answer", "text": "Yes — for eligible learners. The Welsh Government's Personal Learning Account (PLA) programme pays 100% of course fees for Welsh residents aged 19 or over who earn under £34,303 a year or are at risk in their current role, with funding paid directly to the training provider. Clwydian Academy's £4,500 fast-track NVQ courses sit within the annual PLA cap, so eligible learners pay nothing. PLA drawdown is subject to the academy's Medr registration, which follows VTCT centre approval."}},
        {"@type": "Question", "name": "Am I eligible for PLA funding?", "acceptedAnswer": {"@type": "Answer", "text": "The core criteria: you live in Wales, you are 19 or older, and you earn under £34,303 a year (or are employed but at risk). You must not be enrolled in other full-time education. We check eligibility with you before you apply — register your interest and we will walk you through it."}},
        {"@type": "Question", "name": "I live in England — can I still train at Clwydian Academy?", "acceptedAnswer": {"@type": "Answer", "text": "Absolutely. The academy sits on the North Wales / Cheshire border minutes from Chester, and self-funded places are £4,500 — matching the most credible VTCT-accredited fast-track providers in the North West and undercutting London academies by £5,000–£13,000 for the same qualification level."}},
        {"@type": "Question", "name": "How long does it take to qualify?", "acceptedAnswer": {"@type": "Answer", "text": "Six months. Cohorts train in intensive two-day-a-week practical blocks at the Deeside academy, with theory delivered through our digital learning environment around your life — compared with two to four years on a traditional apprenticeship route."}},
        {"@type": "Question", "name": "What qualification do I leave with?", "acceptedAnswer": {"@type": "Answer", "text": "Courses lead to nationally recognised VTCT (NVQ) qualifications at Level 2 or Level 3 in Hairdressing. VTCT is the UK's leading awarding body for hair and beauty. Clwydian Academy's VTCT Approved Centre application is in progress ahead of the founding cohort, and every course also includes our Commercial Resilience Module covering the business skills of self-employment."}},
        {"@type": "Question", "name": "When does the first cohort start?", "acceptedAnswer": {"@type": "Answer", "text": "Founding-cohort recruitment opens in late 2026, with training beginning in early 2027. Places run in cohorts of ten, so registering interest early secures your place in the queue."}},
    ],
}

PAGES = [
    dict(src="home.html", path="/", out="index.html", nav=None,
         title="Clwydian Academy | Hairdressing Training in Deeside, North Wales",
         desc="Qualified in six months, not four years. Fast-track NVQ Level 2 & 3 hairdressing for adults in Deeside — free for eligible Welsh adults via the PLA.",
         jsonld=[{"@context": "https://schema.org", "@type": "WebSite", "name": "Clwydian Academy", "url": DOMAIN + "/", "publisher": {"@id": DOMAIN + "/#organization"}}]),
    dict(src="courses.html", path="/courses/", out="courses/index.html", nav="/courses/",
         title="Hairdressing Courses in North Wales | Clwydian Academy",
         desc="Fast-track NVQ Level 2 & 3 hairdressing diplomas plus CPD in barbering, colour and extensions. Six-month adult courses in Deeside, North Wales.",
         jsonld=[crumbs_ld([("Home", "/"), ("Courses", "/courses/")])]),
    dict(src="nvq2.html", path="/courses/nvq-level-2-hairdressing/", out="courses/nvq-level-2-hairdressing/index.html", nav="/courses/",
         title="Fast-Track NVQ Level 2 Hairdressing Course | Clwydian Academy",
         desc="Beginner to qualified hairdresser in six months. VTCT-standard NVQ Level 2 diploma in Deeside — £4,500 or free for eligible Welsh adults via the PLA.",
         jsonld=[course_ld("NVQ Level 2 Diploma in Hairdressing — Fast-Track", "/courses/nvq-level-2-hairdressing/",
                           "Intensive six-month fast-track hairdressing course for adults: two-day-a-week live-model practical blocks in Deeside plus online theory, leading to a VTCT NVQ Level 2 qualification.",
                           "Free for eligible Welsh adults through the Welsh Government Personal Learning Account (PLA)", 2),
                 crumbs_ld([("Home", "/"), ("Courses", "/courses/"), ("NVQ Level 2 Hairdressing", "/courses/nvq-level-2-hairdressing/")])]),
    dict(src="nvq3.html", path="/courses/nvq-level-3-hairdressing/", out="courses/nvq-level-3-hairdressing/index.html", nav="/courses/",
         title="NVQ Level 3 Hairdressing Course, North Wales | Clwydian Academy",
         desc="Step up to senior stylist: fast-track NVQ Level 3 hairdressing in Deeside — advanced colour, cutting and client leadership. £4,500 or free via the PLA.",
         jsonld=[course_ld("NVQ Level 3 Diploma in Hairdressing — Fast-Track", "/courses/nvq-level-3-hairdressing/",
                           "Six-month advanced hairdressing programme for qualified stylists: creative cutting, colour correction, technical services and commercial client leadership, leading to a VTCT NVQ Level 3 qualification.",
                           "Free for eligible Welsh adults through the Welsh Government Personal Learning Account (PLA)", 3),
                 crumbs_ld([("Home", "/"), ("Courses", "/courses/"), ("NVQ Level 3 Hairdressing", "/courses/nvq-level-3-hairdressing/")])]),
    dict(src="cpd.html", path="/courses/cpd-courses/", out="courses/cpd-courses/index.html", nav="/courses/",
         title="CPD Courses — Barbering, Colour & Extensions | Clwydian Academy",
         desc="Short CPD courses for qualified hairdressers in North Wales: barbering, advanced colouring and hair extensions. One-to-five-day intensives at Deeside.",
         jsonld=[crumbs_ld([("Home", "/"), ("Courses", "/courses/"), ("CPD Courses", "/courses/cpd-courses/")])]),
    dict(src="funding.html", path="/funding/", out="funding/index.html", nav="/funding/",
         title="Free Hairdressing Courses in Wales — PLA Funding | Clwydian Academy",
         desc="Eligible Welsh adults train free: the Personal Learning Account pays 100% of fees for learners 19+ earning under £34,303. Eligibility explained.",
         jsonld=[FAQ_FUNDING, crumbs_ld([("Home", "/"), ("Fees & Funding", "/funding/")])]),
    dict(src="salons.html", path="/for-salons/", out="for-salons/index.html", nav="/for-salons/",
         title="Apprentice Training for Salons | Clwydian Academy",
         desc="75% of salons say recruitment is getting harder. Clwydian Academy trains your apprentices for you in Deeside — plus CPD for your team.",
         jsonld=[crumbs_ld([("Home", "/"), ("For Salons", "/for-salons/")])]),
    dict(src="about.html", path="/about/", out="about/index.html", nav="/about/",
         title="About Clwydian Academy — A Community Interest Company",
         desc="A Net-Zero academy with a locked social mission: retraining adults in Flintshire and the border region into skilled self-employment. Meet the team.",
         jsonld=[crumbs_ld([("Home", "/"), ("About", "/about/")])]),
    dict(src="funders.html", path="/funders/", out="funders/index.html", nav="/funders/",
         title="Funders & Partners — Business Plan | Clwydian Academy",
         desc="For grant assessors, lenders and partners: the Charlotte Eleanor Group business plan and investment case, governance structure and social-impact model behind Clwydian Academy.",
         jsonld=[crumbs_ld([("Home", "/"), ("Funders & Partners", "/funders/")])]),
    dict(src="contact.html", path="/contact/", out="contact/index.html", nav="/contact/",
         title="Contact & Register Interest | Clwydian Academy",
         desc="Register interest in the founding cohort, ask about PLA eligibility, or arrange apprentice training for your salon. Deeside, North Wales.",
         jsonld=[{"@context": "https://schema.org", "@type": "ContactPage", "name": "Contact Clwydian Academy", "url": DOMAIN + "/contact/"}, crumbs_ld([("Home", "/"), ("Contact", "/contact/")])]),
    dict(src="privacy.html", path="/privacy/", out="privacy/index.html", nav=None,
         title="Privacy Policy | Clwydian Academy",
         desc="How Clwydian Academy (Charlotte Eleanor Academy CIC) collects, uses and protects your personal information.",
         jsonld=[]),
    dict(src="404.html", path="/404.html", out="404.html", nav=None, noindex=True,
         title="Page Not Found | Clwydian Academy",
         desc="The page you were looking for has moved or no longer exists.",
         jsonld=[]),
]

def build():
    today = datetime.date.today().isoformat()
    urls = []
    for p in PAGES:
        body = open(os.path.join(SRC, p["src"])).read()
        html = head(p) + "\n" + header(p) + "\n" + body + "\n" + FOOTER
        out = os.path.join(OUT, p["out"])
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w").write(html)
        if not p.get("noindex"):
            pr = "1.0" if p["path"] == "/" else ("0.9" if "courses" in p["path"] or p["path"] == "/funding/" else "0.6")
            urls.append((DOMAIN + p["path"], pr))
        print("built", p["out"])

    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, pr in urls:
        sm.append(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod><priority>{pr}</priority></url>")
    sm.append("</urlset>")
    open(os.path.join(OUT, "sitemap.xml"), "w").write("\n".join(sm))

    open(os.path.join(OUT, "robots.txt"), "w").write(
        f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    open(os.path.join(OUT, "CNAME"), "w").write("clwydianacademy.co.uk\n")
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    print("built sitemap.xml, robots.txt, CNAME, .nojekyll")

if __name__ == "__main__":
    build()
