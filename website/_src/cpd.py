"""cpd.py — everything on the site that comes from _data/cpd-2027.json.

Imported by build.py. Nothing here types a date: the calendar page, the "Next start" and
"2027 dates" rows on each CPD course page, and the Course/CourseInstance JSON-LD are all
rendered from the data file, in both languages. Change the data, rebuild, run
scripts/check_dates.py.

Welsh strings in T["cy"] and in CY_UNIT / CY_TEXT are machine-written and unreviewed
(CLAUDE.md "Bilingual"); every one is listed in REPORT 03 under WELSH FOR REVIEW.
"""
import datetime, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA_PATH = os.path.join(REPO, "_data", "cpd-2027.json")

DOMAIN = None            # set by configure()
CAL = None               # the calendar page's registry entry, set by configure()

def configure(domain, calendar_page):
    global DOMAIN, CAL
    DOMAIN, CAL = domain, calendar_page

def load():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "cy": ["Ionawr", "Chwefror", "Mawrth", "Ebrill", "Mai", "Mehefin", "Gorffennaf", "Awst", "Medi", "Hydref", "Tachwedd", "Rhagfyr"],
}
WEEKDAYS = {
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "cy": ["Dydd Llun", "Dydd Mawrth", "Dydd Mercher", "Dydd Iau", "Dydd Gwener", "Dydd Sadwrn", "Dydd Sul"],
}

# Course names in Welsh, taken from the live Welsh CPD hub cards where one exists.
CY_UNIT = {
    "UHB205": "Llacio a Llyfnhau",
    "UHB204": "Permio a Gwead Modern",
    "UHB206": "Estyniadau Gwallt",
    "UNHB385": "Ymgynghori a Manwerthu",
    "UNHB379": "Busnes Salon",
    "UV21577": "Ymwybyddiaeth Canser y Croen",
    "UNHB374": "Lliwio a Goleuo",                      # no Welsh page yet — drafted
}
# Assessment / client-requirement / price-note strings appear in the data in English only.
CY_TEXT = {
    "Portfolio and an external multiple-choice paper": "Portffolio a phapur amlddewis allanol",
    "Portfolio": "Portffolio",
    "Portfolio, a unit paper and an overarching paper": "Portffolio, papur uned a phapur trosfwaol",
    "Knowledge only": "Gwybodaeth yn unig",
    "Three clients at different stages of regrowth, plus a fourth to fill gaps": "Tri chleient ar wahanol gamau aildyfiant, a phedwerydd i lenwi bylchau",
    "Models across the winding techniques taught": "Modelau ar draws y technegau dirwyn a ddysgir",
    "One observation on a client who already has extensions fitted": "Un arsylwad ar gleient sydd eisoes ag estyniadau wedi&rsquo;u gosod",
    "Clients for consultation and retail evidence": "Cleientiaid ar gyfer tystiolaeth ymgynghori a manwerthu",
    "None — no prior qualification needed": "Dim — dim angen cymhwyster blaenorol",
    "A skin test booked and recorded before every client session": "Prawf croen wedi&rsquo;i archebu a&rsquo;i gofnodi cyn pob sesiwn cleient",
    "All three observations take place in a real working environment": "Mae&rsquo;r tri arsylwad yn digwydd mewn amgylchedd gwaith go iawn",
    "includes brand-partner hair and kit": "yn cynnwys gwallt a phecyn y brand partner",
}

T = {
    "en": dict(
        crumb_home="Home", crumb_courses="Courses", crumb="CPD Calendar 2027",
        eyebrow="CPD masterclasses &middot; January &ndash; July 2027 &middot; St Asaph",
        h1="The 2027 CPD calendar.",
        lede="Two strands, ten cohorts, every date fixed. Each cohort is capped at ten seats. Prices come from one published tariff, not a negotiation.",
        enquire="Enquire / reserve a seat", strand="Strand", teaching_days="teaching days",
        level="Level", award="Award", glh="GLH", seats="seats per cohort",
        starts="Starts", ends="ends", dates="Dates", price="Price", per_seat="per seat",
        assessment="Assessment", requirement="What you bring", details="Course details",
        no_page="Course page to follow &mdash; see CPD masterclasses",
        closures_h="Academy closures", closures_p="No cohort meets on these days; the dates above already skip them.",
        week_commencing="Week commencing",
        tariff_h="How every price is set", tariff_eyebrow="The tariff",
        tariff_p1="Every seat price on this page is one formula: <strong>&pound;{fixed} + &pound;{per_glh} &times; guided learning hours</strong>, rounded to the nearest &pound;{round_to}.",
        tariff_p2="It is anchored on two published prices &mdash; {anchors} &mdash; and Hair Extensions carries a &pound;50 supplement for brand-partner hair and kit.",
        team_h="Team rates", team_p="Book from one salon, gym or clinic and the whole booking is discounted:",
        team_row="{a}&ndash;{b} people: {pct}% off", team_row_one="{a} people (a whole cohort): {pct}% off",
        cta_h="Pick a date. Then tell us.", cta_p="Register your interest with the cohort you want and we will confirm the seat.",
        register="Register interest", next_start="Next start", dates_row="2027 dates",
        full_calendar="Full calendar, closures and tariff:", calendar_link="CPD calendar 2027",
        cohort="Cohort", strand_short="Strand",
    ),
    "cy": dict(
        crumb_home="Hafan", crumb_courses="Cyrsiau", crumb="Calendr DPP 2027",
        eyebrow="Dosbarthiadau meistr DPP &middot; Ionawr &ndash; Gorffennaf 2027 &middot; Llanelwy",
        h1="Calendr DPP 2027.",
        lede="Dau linyn, deg carfan, pob dyddiad wedi&rsquo;i bennu. Mae pob carfan wedi&rsquo;i chapio ar ddeg sedd. Daw&rsquo;r prisiau o un tariff cyhoeddedig, nid o drafodaeth.",
        enquire="Holi / cadw sedd", strand="Llinyn", teaching_days="diwrnod dysgu",
        level="Lefel", award="Dyfarniad", glh="GLH", seats="sedd y garfan",
        starts="Yn dechrau", ends="yn gorffen", dates="Dyddiadau", price="Pris", per_seat="y sedd",
        assessment="Asesu", requirement="Beth i ddod gyda chi", details="Manylion y cwrs",
        no_page="Tudalen cwrs i ddilyn &mdash; gweler dosbarthiadau meistr DPP",
        closures_h="Dyddiau cau&rsquo;r academi", closures_p="Nid oes carfan yn cyfarfod ar y dyddiau hyn; mae&rsquo;r dyddiadau uchod eisoes yn eu hepgor.",
        week_commencing="Wythnos yn dechrau",
        tariff_h="Sut mae pob pris yn cael ei osod", tariff_eyebrow="Y tariff",
        tariff_p1="Un fformiwla yw pob pris sedd ar y dudalen hon: <strong>&pound;{fixed} + &pound;{per_glh} &times; oriau dysgu dan arweiniad</strong>, wedi&rsquo;i dalgrynnu i&rsquo;r &pound;{round_to} agosaf.",
        tariff_p2="Mae wedi&rsquo;i angori ar ddau bris cyhoeddedig &mdash; {anchors} &mdash; ac mae Estyniadau Gwallt yn cario atodiad o &pound;50 am wallt a phecyn y brand partner.",
        team_h="Cyfraddau t&icirc;m", team_p="Archebwch o un salon, campfa neu glinig a chaiff yr archeb gyfan ei gostwng:",
        team_row="{a}&ndash;{b} o bobl: {pct}% i ffwrdd", team_row_one="{a} o bobl (carfan gyfan): {pct}% i ffwrdd",
        cta_h="Dewiswch ddyddiad. Yna dywedwch wrthym.", cta_p="Cofrestrwch eich diddordeb gyda&rsquo;r garfan rydych ei heisiau a byddwn yn cadarnhau&rsquo;r sedd.",
        register="Cofrestru diddordeb", next_start="Dechrau nesaf", dates_row="Dyddiadau 2027",
        full_calendar="Calendr llawn, dyddiau cau a thariff:", calendar_link="Calendr DPP 2027",
        cohort="Carfan", strand_short="Llinyn",
    ),
}
CONTACT = {"en": "/contact/#register", "cy": "/cy/cysylltu/#register"}
HUB = {"en": "/courses/cpd-courses/", "cy": "/cy/cyrsiau/cyrsiau-dpp/"}

def _d(s):
    return datetime.date.fromisoformat(s)

def long_date(s, loc, weekday=False):
    d = _d(s)
    core = f"{d.day} {MONTHS[loc][d.month - 1]} {d.year}"
    return f"{WEEKDAYS[loc][d.weekday()]} {core}" if weekday else core

def date_run(dates, loc):
    """'11, 18, 25 January · 1, 8, 15, 22 February · 1 March 2027' — one year, months grouped."""
    groups, order = {}, []
    for s in dates:
        d = _d(s); k = (d.year, d.month)
        if k not in groups:
            groups[k] = []; order.append(k)
        groups[k].append(str(d.day))
    parts = [f"{', '.join(groups[k])} {MONTHS[loc][k[1] - 1]}" for k in order]
    return " &middot; ".join(parts) + f" {order[-1][0]}"

def title(c, loc):
    return c["title_en"].replace("&", "&amp;") if loc == "en" else CY_UNIT[c["unit"]]

def text(s, loc):
    return s.replace("&", "&amp;") if loc == "en" else CY_TEXT.get(s, s)

def level_label(c, loc):
    t = T[loc]
    return f"{t['level']} {c['level']} ({t['award']})" if c.get("award") else f"{t['level']} {c['level']}"

def days_label(c, strand, loc):
    n = c["days"]
    if loc == "en":
        wd = strand["weekday"]
        return f"{n} {wd}s" if n != 1 else f"1 {wd}"
    wd = strand["weekday_cy"].replace("Dydd ", "dydd ")
    return f"{n} {wd}"

def page_for(c, loc):
    return c.get("page_en") if loc == "en" else c.get("page_cy")

def cohorts_for(data, page):
    """Cohorts whose page_en is this page's EN path, in date order."""
    return sorted([c for c in data["cohorts"] if c.get("page_en") == page["en"]["path"]], key=lambda c: c["dates"][0])

# ---------------------------------------------------------------- calendar page

def calendar_body(loc, page):
    data = load(); t = T[loc]; strands = {s["id"]: s for s in data["strands"]}; tf = data["tariff"]
    out = [f'''<section class="page-hero">
  <svg class="hero-ridge" viewBox="0 0 900 300" aria-hidden="true" fill="none" stroke-linecap="round">
    <path d="M-20,190 C210,60 460,250 920,90" stroke="#574463" stroke-width="2.5"/>
    <path d="M-20,235 C230,120 480,290 920,140" stroke="#c2a14d" stroke-width="2"/>
  </svg>
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="{'/' if loc == 'en' else '/cy/'}">{t['crumb_home']}</a></li><li><a href="{'/courses/' if loc == 'en' else '/cy/cyrsiau/'}">{t['crumb_courses']}</a></li><li aria-current="page">{t['crumb']}</li></ol></nav>
    <p class="eyebrow mt-2">{t['eyebrow']}</p>
    <h1>{t['h1']}</h1>
    <p class="lede">{t['lede']}</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="{CONTACT[loc]}">{t['enquire']} <span class="arr">&rarr;</span></a>
    </div>
  </div>
</section>

<section class="section section--tight" style="padding-top:0">
  <div class="wrap grid grid-2" style="align-items:start">''']
    for s in data["strands"]:
        cohorts = sorted([c for c in data["cohorts"] if c["strand"] == s["id"]], key=lambda c: c["dates"][0])
        wd = s["weekday"] + "s" if loc == "en" else s["weekday_cy"]
        out.append(f'''    <div>
      <p class="eyebrow">{t['strand']} {s['id']} &middot; {wd} &middot; {s['hours']}</p>
      <h2 style="font-size:clamp(1.4rem,2.4vw,1.9rem)">{s['teaching_days']} {t['teaching_days']} &middot; {data['seats_per_cohort']} {t['seats']}</h2>
      <div class="grid" style="gap:1rem;margin-top:1rem">''')
        for c in cohorts:
            href = page_for(c, loc)
            name = f'<a href="{href}">{title(c, loc)}</a>' if href else title(c, loc)
            link = f'<a href="{href}">{t["details"]} <span class="arr">&rarr;</span></a>' if href else f'<a href="{HUB[loc]}">{t["no_page"]} <span class="arr">&rarr;</span></a>'
            note = f' <small>({text(c["price_note_en"], loc)})</small>' if c.get("price_note_en") else ""
            out.append(f'''        <article class="card">
          <span class="card-kicker">{c['unit']} &middot; {level_label(c, loc)} &middot; {c['glh']} {t['glh']} &middot; {days_label(c, s, loc)}</span>
          <h3>{name}</h3>
          <p><strong>{t['starts']} {long_date(c['dates'][0], loc, weekday=True)}</strong>{(' &middot; ' + t['ends'] + ' ' + long_date(c['dates'][-1], loc)) if len(c['dates']) > 1 else ''}</p>
          <p><strong>{t['dates']}:</strong> {date_run(c['dates'], loc)}</p>
          <p><strong>{t['price']}:</strong> &pound;{c['price']} {t['per_seat']}{note}</p>
          <p><strong>{t['assessment']}:</strong> {text(c['assessment_en'], loc)}<br><strong>{t['requirement']}:</strong> {text(c['requirement_en'], loc)}</p>
          <span class="card-cta">{link}</span>
        </article>''')
        out.append('''      </div>
    </div>''')
    out.append('''  </div>
</section>

<section class="section on-dark section--tight">
  <img class="watermark" src="/assets/img/seal.svg" alt="" aria-hidden="true">
  <div class="wrap split">
    <div class="reveal">''')
    anchors = (' ' + ('and' if loc == 'en' else 'a') + ' ').join(a.replace('£', '&pound;') for a in tf['anchors'])
    out.append(f'''      <p class="eyebrow">{t['tariff_eyebrow']}</p>
      <h2>{t['tariff_h']}</h2>
      <p>{t['tariff_p1'].format(fixed=f"{tf['fixed']:.2f}", per_glh=f"{tf['per_glh']:.3f}", round_to=tf['round_to'])}</p>
      <p class="mt-1">{t['tariff_p2'].format(anchors=anchors)}</p>
      <h3 class="mt-1" style="font-size:1.15rem">{t['team_h']}</h3>
      <p>{t['team_p']}</p>
      <ul class="feature-list">''')
    for tier in data["team_discounts"]:
        row = t["team_row_one"].format(a=tier["from"], pct=tier["pct"]) if tier["from"] == tier["to"] else t["team_row"].format(a=tier["from"], b=tier["to"], pct=tier["pct"])
        out.append(f"        <li>{row}</li>")
    out.append(f'''      </ul>
    </div>
    <div class="reveal" style="--d:.12s">
      <h2 style="font-size:clamp(1.4rem,2.4vw,1.9rem)">{t['closures_h']}</h2>
      <p>{t['closures_p']}</p>
      <ul class="feature-list">''')
    for c in data["closures"]:
        if "date" in c:
            out.append(f"        <li>{long_date(c['date'], loc, weekday=True)} &mdash; {c[loc]}</li>")
        else:
            out.append(f"        <li>{t['week_commencing']} {long_date(c['week_commencing'], loc)} &mdash; {c[loc]}</li>")
    out.append(f'''      </ul>
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="wrap cta-banner on-navy reveal">
    <img class="watermark" src="/assets/img/seal.svg" alt="" aria-hidden="true">
    <h2>{t['cta_h']}</h2>
    <p class="lede">{t['cta_p']}</p>
    <div class="hero-actions mt-2">
      <a class="btn btn-gold" href="{CONTACT[loc]}">{t['register']} <span class="arr">&rarr;</span></a>
    </div>
  </div>
</section>
''')
    return "\n".join(out)

# ---------------------------------------------------------------- course-page rows

def date_rows(loc, page):
    data = load(); t = T[loc]; strands = {s["id"]: s for s in data["strands"]}
    cohorts = cohorts_for(data, page)
    if not cohorts:
        return ""
    today = datetime.date.today()
    upcoming = [c for c in cohorts if _d(c["dates"][0]) >= today]
    nxt = upcoming[0] if upcoming else cohorts[-1]
    s = strands[nxt["strand"]]
    cal = CAL[loc]["path"]
    rows = [f'<div class="meta-row"><dt>{t["next_start"]}</dt><dd>{long_date(nxt["dates"][0], loc, weekday=True)} '
            f'<small>{t["strand_short"]} {s["id"]} &middot; {days_label(nxt, s, loc)} &middot; &pound;{nxt["price"]} {t["per_seat"]} &middot; {data["seats_per_cohort"]} {t["seats"]}</small></dd></div>']
    if len(cohorts) == 1:
        runs = date_run(cohorts[0]["dates"], loc)
    else:
        runs = " &middot; ".join(f'{t["cohort"]} {i + 1} ({t["strand_short"]} {c["strand"]}): {date_run(c["dates"], loc)}' for i, c in enumerate(cohorts))
    rows.append(f'<div class="meta-row"><dt>{t["dates_row"]}</dt><dd>{runs} <small>{t["full_calendar"]} <a href="{cal}">{t["calendar_link"]}</a></small></dd></div>')
    return "\n          ".join(rows)

# ---------------------------------------------------------------- JSON-LD

def _place():
    return {"@type": "Place", "name": "Clwydian Academy, St Asaph",
            "address": {"@type": "PostalAddress", "addressLocality": "St Asaph", "addressRegion": "Denbighshire", "addressCountry": "GB"}}

def _offer(c, url):
    return {"@type": "Offer", "category": "Paid", "price": str(c["price"]), "priceCurrency": "GBP",
            "availability": "https://schema.org/InStock", "url": DOMAIN + url}

def _instance(c, data, url):
    return {"@type": "CourseInstance", "courseMode": "Blended", "startDate": c["dates"][0], "endDate": c["dates"][-1],
            "courseWorkload": f"PT{c['glh']}H", "location": _place(),
            "maximumAttendeeCapacity": data["seats_per_cohort"], "offers": _offer(c, url)}

def enrich(jsonld, loc, page):
    """Course pages: replace the Course block's single hasCourseInstance with the data's cohorts."""
    data = load()
    cohorts = cohorts_for(data, page)
    if not cohorts:
        return jsonld
    url = page[loc]["path"]
    for block in jsonld:
        if block.get("@type") == "Course":
            block["hasCourseInstance"] = [_instance(c, data, url) for c in cohorts]
            block["offers"] = _offer(cohorts[0], url)
    return jsonld

def calendar_jsonld(loc, page):
    data = load(); t = T[loc]
    url = page[loc]["path"]
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": t["crumb_home"], "item": DOMAIN + ("/" if loc == "en" else "/cy/")},
        {"@type": "ListItem", "position": 2, "name": t["crumb_courses"], "item": DOMAIN + ("/courses/" if loc == "en" else "/cy/cyrsiau/")},
        {"@type": "ListItem", "position": 3, "name": t["crumb"], "item": DOMAIN + url}]}
    courses, seen = [], {}
    for c in sorted(data["cohorts"], key=lambda c: c["dates"][0]):
        u = c["unit"]
        href = page_for(c, loc)          # per cohort — never carried from the previous iteration
        if u not in seen:
            cid = DOMAIN + (href + "#course" if href else url + "#" + u.lower())
            seen[u] = {"@context": "https://schema.org", "@type": "Course", "@id": cid,
                       "name": f"{title(c, loc).replace('&amp;', '&')} ({'VTCT' if loc == 'en' else 'VTCT'} {u})",
                       "inLanguage": loc, "provider": {"@id": DOMAIN + "/#organization"},
                       "url": DOMAIN + (href or url), "offers": _offer(c, href or url), "hasCourseInstance": []}
            courses.append(seen[u])
        seen[u]["hasCourseInstance"].append(_instance(c, data, href or url))
    return courses + [crumbs]
