"""cpd.py — everything on the site that comes from _data/cpd-2027.json.

Imported by build.py. Nothing here types a date: the calendar page, the "Next start" and
"2027 dates" rows on each CPD course page, and the Course/CourseInstance JSON-LD are all
rendered from the data file, in both languages. Change the data, rebuild, run
scripts/check_dates.py.

Welsh strings in T["cy"] and in CY_UNIT / CY_TEXT are machine-written and unreviewed
(CLAUDE.md "Bilingual"); every one is listed in REPORT 03 under WELSH FOR REVIEW.
"""
import datetime, json, os, re

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
CY_UNIT["UNHB374"] = "Lliwio a Goleuo"

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
        "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
CY_ONES = ["dim", "un", "dau", "tri", "pedwar", "pump", "chwech", "saith", "wyth", "naw", "deg"]
# Welsh numerals before a noun (the forms used in "chwe dydd Llun")
CY_BEFORE_NOUN = {1: "un", 2: "dau", 3: "tri", 4: "pedwar", 5: "pum", 6: "chwe", 7: "saith", 8: "wyth", 9: "naw", 10: "deg"}

def number_word(n, loc, before_noun=False):
    if loc == "cy":
        if before_noun and n in CY_BEFORE_NOUN: return CY_BEFORE_NOUN[n]
        return CY_ONES[n] if 0 <= n <= 10 else str(n)
    if n < 20: return ONES[n]
    if n < 100: return TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else "")
    return str(n)


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


# ---------------------------------------------------------------- {{cpd:...}} tokens in fragments and metadata

def _unit_cohorts(data, unit):
    return sorted([c for c in data["cohorts"] if c["unit"] == unit], key=lambda c: c["dates"][0])

def _pound(n):
    return f"&pound;{n:,}" if isinstance(n, int) else f"&pound;{n}"

def token(name, loc, data):
    """Resolve one {{cpd:NAME}} token. Unknown tokens raise — a typo must fail the build."""
    t = T[loc]; strands = {s["id"]: s for s in data["strands"]}; tf = data["tariff"]
    parts = name.split(":")
    key, arg = parts[0], (parts[1] if len(parts) > 1 else None)
    cap = key[:1].isupper(); key = key[0].lower() + key[1:]
    def out(v):
        v = str(v); return (v[:1].upper() + v[1:]) if cap else v
    if arg and arg.upper() in {c["unit"] for c in data["cohorts"]}:
        cs = _unit_cohorts(data, arg.upper()); c = cs[0]; st = strands[c["strand"]]
        if key == "price": return out(_pound(c["price"]))
        if key == "priceRaw": return out(c["price"])          # bare number, for JSON-LD
        if key == "level": return out(c["level"])
        if key == "glh": return out(c["glh"])
        if key == "ndays": return out(c["days"])
        if key == "days": return out(days_label(c, st, loc))
        if key == "daysWord":
            wd = st["weekday"] + ("s" if c["days"] != 1 else "") if loc == "en" else st["weekday_cy"].replace("Dydd ", "dydd ")
            return out(f"{number_word(c['days'], loc, before_noun=True)} {wd}")
        if key == "ndaysWord": return out(number_word(c["days"], loc))
        if key == "start": return out(long_date(c["dates"][0], loc))
        if key == "startShort":
            dd = _d(c["dates"][0]); return out(f"{dd.day} {MONTHS[loc][dd.month - 1]}")
        if key == "end": return out(long_date(c["dates"][-1], loc))
        if key == "starts":   # every cohort's first day, "6 January and 28 July"
            ds = [f"{_d(x['dates'][0]).day} {MONTHS[loc][_d(x['dates'][0]).month - 1]}" for x in cs]
            j = " and " if loc == "en" else " a "
            return out(j.join(ds) if len(ds) < 3 else ", ".join(ds[:-1]) + j + ds[-1])
        if key == "strand": return out(f"{t['strand']} {st['id']}")
        if key == "weekday": return out(st["weekday"] + "s" if loc == "en" else st["weekday_cy"])
        if key == "hours": return out(st["hours"])
        if key == "title": return out(title(c, loc))
        raise KeyError(f"cpd token {name!r}: unknown field {key!r}")
    if key == "seats": return out(data["seats_per_cohort"])
    if key == "seatsWord": return out(number_word(data["seats_per_cohort"], loc))
    if key == "units": return out(len({c["unit"] for c in data["cohorts"]}))
    if key == "unitsWord": return out(number_word(len({c["unit"] for c in data["cohorts"]}), loc))
    if key == "ndates": return out(sum(len(c["dates"]) for c in data["cohorts"]))
    if key == "ndatesWord": return out(number_word(sum(len(c["dates"]) for c in data["cohorts"]), loc))
    if key == "cohorts": return out(len(data["cohorts"]))
    if key == "cohortsWord": return out(number_word(len(data["cohorts"]), loc))
    if key == "minPrice": return out(_pound(min(c["price"] for c in data["cohorts"])))
    if key == "maxPrice": return out(_pound(max(c["price"] for c in data["cohorts"])))
    if key == "minDays": return out(number_word(min(c["days"] for c in data["cohorts"]), loc))
    if key == "minGlh": return out(min(c["glh"] for c in data["cohorts"]))
    if key == "maxGlh": return out(max(c["glh"] for c in data["cohorts"]))
    if key == "maxDays": return out(number_word(max(c["days"] for c in data["cohorts"]), loc))
    if key == "termEnd":
        dd = _d(data["term"]["last_day"]); return out(f"{MONTHS[loc][dd.month - 1]} {dd.year}")
    if key == "termLabel": return out(data["term"]["label_" + loc])
    if key == "strandDays":
        names = [st["weekday"] + "s" if loc == "en" else st["weekday_cy"] for st in data["strands"]]
        return out((" and " if loc == "en" else " a ").join(names))
    if key == "fixed": return out(f"&pound;{tf['fixed']:.2f}")
    if key == "perGlh": return out(f"&pound;{tf['per_glh']:.3f}")
    if key == "roundTo": return out(f"&pound;{tf['round_to']}")
    if key == "anchors":
        return out((" and " if loc == "en" else " a ").join(a.replace("£", "&pound;") for a in tf["anchors"]))
    if key == "kit": return out(_pound(50))
    if key.startswith("tier"):
        i = int(arg) - 1; tier = data["team_discounts"][i]
        if key == "tierPct": return out(tier["pct"])
        if key == "tierFrom": return out(tier["from"])
        if key == "tierTo": return out(tier["to"])
        if key == "tierFromWord": return out(number_word(tier["from"], loc))
        if key == "tierRange":
            return out(f"{tier['from']}&ndash;{tier['to']}" if tier["from"] != tier["to"] else str(tier["from"]))
    if key == "calendarList": return calendar_list(loc, data)
    if key == "priceList": return price_list(loc, data)
    if key == "calendarUrl": return CAL[loc]["path"]
    raise KeyError(f"cpd token {name!r} is not defined")

TOKEN_RE = re.compile(r"\{\{cpd:([A-Za-z0-9:_-]+)\}\}")
FEE_RE = re.compile(r"\{\{fee:([A-Za-z0-9_-]+)\}\}")
FEES_PATH = os.path.join(REPO, "_data", "fees.json")

# Figures in _data/fees.json that are sums of money (rendered as "&pound;4,500"); the rest are counts.
FEE_MONEY = {"nvq", "deposit", "instalment", "funded", "bundle_l2_l3", "employer_sponsored", "react_support",
             "react_remainder", "cpd_day_min", "cpd_day_max", "relaxing_per_week_under",
             "market_saving_min", "market_saving_max", "market_day_min", "market_day_max"}
FEE_ALIAS = {"fee": "nvq", "react": "react_support"}

def fee_value(key, fees):
    """One figure by its _data/fees.json key, or one of the two derived figures."""
    if key == "react_remainder":                       # what a learner still pays after ReAct+ support
        return fees["nvq"] - fees["react_support"]
    if key == "react_instalments":                     # ...and in how many instalments, after the deposit
        n, rest = divmod(fee_value("react_remainder", fees) - fees["deposit"], fees["instalment"])
        if rest or n < 1:
            raise ValueError("fees.json: (nvq - react_support - deposit) is not a whole number of instalments — "
                             "the ReAct+ sentences on /funding/ no longer add up; change the figures or the copy")
        return n
    if key.startswith("_") or key not in fees:
        raise KeyError(f"fee token: {key!r} is not in _data/fees.json")
    return fees[key]

def fee_token(name, loc):
    """{{fee:<name>}} — a figure from _data/fees.json. <name> is the JSON key in camelCase
    (barberingWeeks -> barbering_weeks; `fee` and `react` are short for nvq and react_support),
    plus reactRemainder and reactInstalments, which are derived. Suffixes:
        (none)  money as &pound;4,500, counts as 8        Raw    4500 (for JSON-LD prices)
        Word    the number spelled out: eight / wyth      WordN  spelled out as it stands before a
                                                                 noun in Welsh: chwe mis, pum rhandaliad
    A capital initial capitalises the result. An unknown name fails the build."""
    with open(FEES_PATH, encoding="utf-8") as f:
        fees = json.load(f)
    cap = name[:1].isupper(); base = name[0].lower() + name[1:]
    form = next((s for s in ("WordN", "Word", "Raw") if base.endswith(s)), "")
    if form: base = base[:-len(form)]
    key = FEE_ALIAS.get(base) or re.sub(r"(?<=[a-z0-9])([A-Z])", lambda m: "_" + m.group(1).lower(), base)
    key = {"bundle_l2l3": "bundle_l2_l3"}.get(key, key)
    try:
        v = fee_value(key, fees)
    except KeyError:
        raise KeyError(f"fee token {name!r} is not defined")
    if form == "Word": out = number_word(v, loc)
    elif form == "WordN": out = number_word(v, loc, before_noun=True)
    elif form == "Raw": out = str(v)
    else: out = _pound(v) if key in FEE_MONEY else str(v)
    return (out[:1].upper() + out[1:]) if cap else out

STAT_RE = re.compile(r"\{\{stat:([a-z_]+):([A-Za-z]+)\}\}")
STATS_PATH = os.path.join(REPO, "_data", "statistics.json")

def stat_token(key, field, loc):
    """{{stat:<key>:<field>}} — an industry statistic and its citation from _data/statistics.json.
    Fields: headline, card, sentence, clause, source; a capital initial capitalises the first letter."""
    with open(STATS_PATH, encoding="utf-8") as f:
        stats = json.load(f)
    if key not in stats:
        raise KeyError(f"stat token {key!r} is not in _data/statistics.json")
    cap = field[:1].isupper(); f = field[0].lower() + field[1:]
    st = stats[key]
    if f == "headline": v = st["headline"]
    elif f == "source": v = st["source"][loc]
    elif f in ("card", "sentence", "clause"): v = st[loc][f]
    else: raise KeyError(f"stat token field {field!r} is not defined")
    v = v.replace("&", "&amp;").replace("'", "&rsquo;").replace("—", "&mdash;").replace("−", "&minus;")
    return (v[:1].upper() + v[1:]) if cap else v

def render(text, loc):
    if "{{stat:" in text:
        text = STAT_RE.sub(lambda m: stat_token(m.group(1), m.group(2), loc), text)
    if "{{cpd:" in text:
        data = load()
        text = TOKEN_RE.sub(lambda m: token(m.group(1), loc, data), text)
    if "{{fee:" in text:
        text = FEE_RE.sub(lambda m: fee_token(m.group(1), loc), text)
    return text

def calendar_list(loc, data):
    """Every cohort in date order as meta rows: date range -> unit, title, level, days, price."""
    t = T[loc]; strands = {s["id"]: s for s in data["strands"]}
    rows = []
    for c in sorted(data["cohorts"], key=lambda c: c["dates"][0]):
        st = strands[c["strand"]]
        href = page_for(c, loc)
        name = f'<a href="{href}">{title(c, loc)}</a>' if href else title(c, loc)
        when = long_date(c["dates"][0], loc, weekday=True) if len(c["dates"]) == 1 else f"{long_date(c['dates'][0], loc, weekday=True)} &ndash; {long_date(c['dates'][-1], loc)}"
        rows.append(f'<div class="meta-row"><dt>{when}</dt><dd>{c["unit"]} &middot; {name} <small>{level_label(c, loc)} &middot; {days_label(c, st, loc)} &middot; {t["strand"]} {st["id"]} &middot; {_pound(c["price"])} {t["per_seat"]}</small></dd></div>')
    return '<div class="meta-panel">\n<dl>\n' + "\n".join(rows) + "\n</dl>\n</div>"

def price_list(loc, data):
    """One row per unit: GLH -> the tariff arithmetic -> the price."""
    t = T[loc]; tf = data["tariff"]; seen = set(); rows = []
    for c in sorted(data["cohorts"], key=lambda c: c["price"]):
        if c["unit"] in seen: continue
        seen.add(c["unit"])
        base = round((tf["fixed"] + tf["per_glh"] * c["glh"]) / tf["round_to"]) * tf["round_to"]
        extra = f" + {_pound(c['price'] - base)}" if c["price"] != base else ""
        href = page_for(c, loc)
        name = f'<a href="{href}">{title(c, loc)}</a>' if href else title(c, loc)
        rows.append(f'<div class="meta-row"><dt>{c["unit"]}</dt><dd>{name} &middot; <strong>{_pound(c["price"])}</strong> {t["per_seat"]} <small>{level_label(c, loc)} &middot; {c["glh"]} {t["glh"]}: &pound;{tf["fixed"]:.2f} + &pound;{tf["per_glh"]:.3f} &times; {c["glh"]} = &pound;{tf["fixed"] + tf["per_glh"] * c["glh"]:.2f} &rarr; {_pound(base)}{extra}</small></dd></div>')
    return '<div class="meta-panel">\n<dl>\n' + "\n".join(rows) + "\n</dl>\n</div>"
