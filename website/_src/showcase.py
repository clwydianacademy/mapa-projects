#!/usr/bin/env python3
"""The showcase: the three-path home page, the learner-work gallery, the Find us block, the
statutory footer line and the HairSalon structured data.

Everything here is behind ONE switch, `"public"` in _data/showcase.json, and is built only when
it is true (or by `build.py --preview DIR`, into a scratch folder). With the switch off the site
is byte for byte what it is without this file: no page, no stylesheet, no photograph.

Three rules this module enforces, each of which stops the build:

  1. A PHOTOGRAPH THAT IS STOCK IS NEVER PASSED OFF AS A LEARNER'S WORK. _data/photos.json marks
     every imported picture `stock`; its alt text describes the hair and may not say learner,
     student, our, client or academy.
  2. A BEFORE-AND-AFTER PAIR IS A TESTIMONIAL (CAP Code 3.47-3.50). A pair in _data/work.json is
     not published without the reference and date of its signed consent, the originals on file,
     and confirmation that the hair was not retouched. See validate_pairs().
  3. THE TRADING DISCLOSURE IS COMPLETE BEFORE THE SWITCH GOES ON. See legal_todos().

Welsh in this file is machine-written and unreviewed: every string is listed in prompts/RELAY.md
under WELSH FOR REVIEW.
"""
import datetime, json, os, re, shutil, sys

import salon

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
ASSETS = os.path.join(REPO, "website", "_showcase")
SWITCH_PATH = os.path.join(REPO, "_data", "showcase.json")
PHOTOS_PATH = os.path.join(REPO, "_data", "photos.json")
WORK_PATH = os.path.join(REPO, "_data", "work.json")
SOURCES = [SWITCH_PATH, PHOTOS_PATH, WORK_PATH, os.path.join(REPO, "_data", "site.json"), os.path.join(HERE, "showcase.py")]

WORK = {"en": "/work/", "cy": "/cy/gwaith/"}
HOME = {"en": "/", "cy": "/cy/"}
COURSES = {"en": "/courses/", "cy": "/cy/cyrsiau/"}
APPRENTICE = {"en": "/apprenticeships/", "cy": "/cy/prentisiaethau/"}
CONTACT = {"en": "/contact/", "cy": "/cy/cysylltu/"}


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def is_public():
    """The switch. False means: build nothing of the showcase, anywhere."""
    return _load(SWITCH_PATH).get("public") is True


def is_todo(node):
    return isinstance(node, dict) and node.get("todo_pm") is True


# ------------------------------------------------------------------------------------------------
# The trading disclosure, and the one address
# ------------------------------------------------------------------------------------------------

def legal_todos(site):
    """The statutory values that are still missing. The showcase cannot be public while any is."""
    legal = site["legal"]
    return [key for key in ("registered_in", "registered_office") if is_todo(legal[key]) or not legal[key].get("value")]


def legal_line(loc, site, tbc=False):
    """Regs 24-25 of the 2015 Regulations, on every page: the registered name, that it is a limited
    company, the part of the United Kingdom it is registered in, its number and its registered
    office. A value that is still TODO_PM is LEFT OUT rather than guessed — and the build will
    not let the showcase go public until none is (legal_todos). On a PREVIEW build only
    (`tbc`), the gap is shown as a visible [TBC] so whoever is reviewing sees what is missing."""
    legal = site["legal"]
    name, number = legal["registered_name"], legal["company_number"]
    mark = '<strong class="sc-tbc-mark">[TBC]</strong>' if tbc else None
    where = (mark if is_todo(legal["registered_in"]) else legal["registered_in"]["value"])
    office = (mark if is_todo(legal["registered_office"]) else legal["registered_office"]["value"])
    office = office[loc] if isinstance(office, dict) else office
    if loc == "en":
        parts = [f"{name} is {legal['status']['en']}"
                 + (f", registered in {where}" if where else "") + f". Company number {number}."]
        if office:
            parts.append(f"Registered office: {office}.")
    else:
        parts = [f"Mae {name} yn {legal['status']['cy']}"
                 + (f", wedi&rsquo;i gofrestru yn {where}" if where else "") + f". Rhif cwmni {number}."]
        if office:
            parts.append(f"Swyddfa gofrestredig: {office}.")
    return "&copy; 2026 " + " ".join(parts)


def address_text(loc, site):
    """The one address string. The unit and postcode are shown only once they are confirmed."""
    a = site["salon_address"]
    return a["confirmed_part"][loc] if is_todo(a) else a["value"][loc]


def address_confirmed(site):
    return not is_todo(site["salon_address"])


def find_us(loc, site):
    a = site["salon_address"]
    f = a["find_us"]["value"][loc]
    s = S[loc]
    tbc = f'<p class="sc-tbc">{s["find_tbc"]}</p>' if is_todo(a) or is_todo(a["find_us"]) else ""
    return f'''<section class="section sc-find" id="find-us" aria-labelledby="find-us-h">
  <div class="wrap">
    <div class="split">
      <div class="reveal">
        <p class="eyebrow">{s["find_eyebrow"]}</p>
        <h2 id="find-us-h">{s["find_h"]}</h2>
        <address class="sc-address">Clwydian Academy<br>{address_text(loc, site).replace(", ", "<br>")}</address>
        {tbc}
        <p><a class="btn btn-outline" href="{CONTACT[loc]}">{s["find_contact"]}</a></p>
      </div>
      <dl class="sc-find-list reveal" style="--d:.08s">
        <div><dt>{s["find_road"]}</dt><dd>{f["road"]}</dd></div>
        <div><dt>{s["find_parking"]}</dt><dd>{f["parking"]}</dd></div>
        <div><dt>{s["find_transport"]}</dt><dd>{f["transport"]}</dd></div>
      </dl>
    </div>
  </div>
</section>
'''


# ------------------------------------------------------------------------------------------------
# Photographs
# ------------------------------------------------------------------------------------------------

CLAIMS_IN_ALT = re.compile(r"\b(learner|student|our|client|academy|dysgwr|dysgwyr|myfyri|ein\b|cleient|academi)", re.I)


def photos():
    data = _load(PHOTOS_PATH)
    out = {}
    for ph in data["photos"]:
        for loc in ("en", "cy"):
            alt = ph["alt"][loc]
            if ph.get("stock") and CLAIMS_IN_ALT.search(alt):
                sys.exit(f"showcase: the alt text of the stock photograph {ph['stem']} ({loc}) claims it as somebody's work: {alt!r}")
            if len(alt) < 12:
                sys.exit(f"showcase: {ph['stem']} ({loc}) has no real alt text")
        out[ph["stem"]] = ph
    return out


def manifest():
    return _load(os.path.join(ASSETS, "photos", "manifest.json"))


def picture(stem, loc, sizes, cls="", eager=False):
    """A <picture>: WebP first, JPEG behind it, every width listed, width and height on the <img>."""
    ph, dims = photos()[stem], manifest()[stem]
    base = "/assets/img/photos/" + stem
    srcset = lambda ext: ", ".join(f"{base}-{w}.{ext} {w}w" for w, _h in dims)
    w, h = dims[0]
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<picture{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}>'
            f'<source type="image/webp" srcset="{srcset("webp")}" sizes="{sizes}">'
            f'<img src="{base}-{w}.jpg" srcset="{srcset("jpg")}" sizes="{sizes}" width="{w}" height="{h}" '
            f'alt="{salon.esc(ph["alt"][loc])}" {load} decoding="async"></picture>')


def copy_assets(out):
    """Put the showcase's stylesheet, script, fonts and photographs into the built folder."""
    for sub, dst in (("photos", "assets/img/photos"), ("fonts", "assets/fonts")):
        target = os.path.join(out, dst)
        os.makedirs(target, exist_ok=True)
        for name in sorted(os.listdir(os.path.join(ASSETS, sub))):
            if name == "manifest.json":
                continue
            shutil.copyfile(os.path.join(ASSETS, sub, name), os.path.join(target, name))
    shutil.copyfile(os.path.join(ASSETS, "showcase.css"), os.path.join(out, "assets", "css", "showcase.css"))
    shutil.copyfile(os.path.join(ASSETS, "showcase.js"), os.path.join(out, "assets", "js", "showcase.js"))
    work_src = os.path.join(ASSETS, "work")
    if os.path.isdir(work_src):
        os.makedirs(os.path.join(out, "assets", "img", "work"), exist_ok=True)
        for name in sorted(os.listdir(work_src)):
            shutil.copyfile(os.path.join(work_src, name), os.path.join(out, "assets", "img", "work", name))


def remove_assets(out):
    """The switch is off: nothing of the showcase stays in the built folder."""
    for rel in ("assets/img/photos", "assets/img/work", "assets/fonts"):
        shutil.rmtree(os.path.join(out, rel), ignore_errors=True)
    for rel in ("assets/css/showcase.css", "assets/js/showcase.js"):
        try: os.remove(os.path.join(out, rel))
        except FileNotFoundError: pass


# ------------------------------------------------------------------------------------------------
# Learner work: the pairs, and the rule about publishing one
# ------------------------------------------------------------------------------------------------

PAIR_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LOOKS_LIKE_A_NAME = re.compile(r"\b(by|gan)\s+[A-Z][a-z]+", re.U)


SLUG = re.compile(r"^(?:sample-)?learner-[a-z0-9]{2,8}$")
MONTH = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")


def validate_portfolios(work, today=None, preview=False):
    """A learner's portfolio page. No names — the slug is a code — and it is published only with the
    learner's own signed, dated consent. SAMPLE data is for previews: a public build refuses it."""
    today = today or datetime.date.today().isoformat()
    course_ids = {c["id"] for c in work["courses"]}
    badge_ids = {b["id"] for b in work["badges"]}
    seen = set()
    for i, pf in enumerate(work.get("portfolios", [])):
        who = f"work.json: portfolio {pf.get('slug', '#' + str(i + 1))!r}"
        def refuse(why):
            sys.exit(f"showcase: {who} cannot be published — {why}")
        slug = str(pf.get("slug", ""))
        if not SLUG.match(slug): refuse("its slug must be 'learner-' and a code of 2 to 8 letters or digits (never a name)")
        if slug in seen: refuse("its slug is used twice")
        seen.add(slug)
        if pf.get("sample") is True and not slug.startswith("sample-"): refuse("it is sample data, so its slug must start 'sample-'")
        if slug.startswith("sample-") and pf.get("sample") is not True: refuse("a 'sample-' slug must be marked \"sample\": true")
        if pf.get("sample") is True and not preview: refuse("it is SAMPLE data, which is built in previews only: remove it before the showcase is public")
        if any(k in pf for k in ("name", "learner", "learnerName", "firstName", "surname")): refuse("it names a person: no learner names")
        if not str(pf.get("consentRef", "")).strip(): refuse("it has no consentRef: the learner's own signed consent to a public portfolio")
        date = str(pf.get("consentDate", ""))
        try: datetime.date.fromisoformat(date)
        except ValueError: refuse("its consentDate is not a date (YYYY-MM-DD)")
        if date > today: refuse(f"its consentDate ({date}) is in the future")
        if pf.get("course") not in course_ids: refuse(f"its course is not one of {sorted(course_ids)}")
        if not MONTH.match(str(pf.get("started", ""))): refuse("'started' must be a month, YYYY-MM")
        for a in pf.get("achievements", []):
            if a.get("badge") not in badge_ids: refuse(f"an achievement's badge is not one of {sorted(badge_ids)}")
            if not MONTH.match(str(a.get("date", ""))): refuse("an achievement's date must be a month, YYYY-MM")
            for loc in ("en", "cy"):
                if len(str(a.get(loc, ""))) < 6: refuse(f"an achievement has no {loc} wording")
                if LOOKS_LIKE_A_NAME.search(a[loc]): refuse(f"an achievement's {loc} wording appears to name somebody")
    for pair in work.get("pairs", []):
        if pair.get("portfolio") and pair["portfolio"] not in seen:
            sys.exit(f"showcase: work.json: pair {pair.get('id')!r} belongs to a portfolio that does not exist: {pair['portfolio']!r}")
    return work.get("portfolios", [])


def validate_pairs(work, today=None, files=None, preview=False):
    """Refuse a before-and-after pair that could not be stood behind. Returns the pairs.

    `files` is the set of file names available (defaults to what is in website/_showcase/work/)."""
    today = today or datetime.date.today().isoformat()
    if files is None:
        d = os.path.join(ASSETS, "work")
        files = set(os.listdir(d)) if os.path.isdir(d) else set()
    course_ids = {c["id"] for c in work["courses"]}
    badge_ids = {b["id"] for b in work["badges"]}
    seen = set()
    for i, pair in enumerate(work.get("pairs", [])):
        who = f"work.json: pair {pair.get('id', '#' + str(i + 1))!r}"
        def refuse(why):
            sys.exit(f"showcase: {who} cannot be published — {why}")
        if not PAIR_ID.match(str(pair.get("id", ""))): refuse("it has no id (lower-case letters, digits and hyphens)")
        if pair["id"] in seen: refuse("its id is used twice")
        seen.add(pair["id"])
        if not str(pair.get("consentRef", "")).strip(): refuse("it has no consentRef: the reference of the signed consent form on file")
        date = str(pair.get("consentDate", ""))
        try: datetime.date.fromisoformat(date)
        except ValueError: refuse("its consentDate is not a date (YYYY-MM-DD): the consent must be signed AND dated")
        if date > today: refuse(f"its consentDate ({date}) is in the future")
        if pair.get("originalsKept") is not True: refuse("originalsKept is not true: the untouched originals must be on file")
        if pair.get("ownClient") is not True: refuse("ownClient is not true: only the salon's own clients may be shown")
        if pair.get("hairRetouched") is not False: refuse("hairRetouched is not false: the hair may not be retouched in either picture")
        if pair.get("afterOnlyEdited") is not False: refuse("afterOnlyEdited is not false: nothing may be done to the 'after' that was not done to the 'before'")
        if pair.get("course") not in course_ids: refuse(f"its course is not one of {sorted(course_ids)}")
        for b in pair.get("badges", []):
            if b not in badge_ids: refuse(f"its badge {b!r} is not one of {sorted(badge_ids)}")
        for loc in ("en", "cy"):
            alt = (pair.get("alt") or {}).get(loc, "")
            if len(alt) < 12: refuse(f"it has no {loc} description of the hair")
            if LOOKS_LIKE_A_NAME.search(alt): refuse(f"its {loc} description appears to name somebody: no learner or client names")
        if any(k in pair for k in ("learner", "learnerName", "name", "client", "clientName")): refuse("it names a person: no learner or client names")
        if pair.get("sample") is True:
            if not preview: refuse("it is SAMPLE data, which is built in previews only: remove it before the showcase is public")
            if not pair["id"].startswith("sample-") or pair.get("ext") != "svg": refuse("sample data must have an id starting 'sample-' and a drawn panel (ext 'svg'), never a photograph")
        elif pair["id"].startswith("sample-") or pair.get("ext", "jpg") != "jpg": refuse("only sample data may be called 'sample-' or use a drawn panel")
        for side in ("before", "after"):
            fn = f"{pair['id']}-{side}.{pair.get('ext', 'jpg')}"
            if fn not in files: refuse(f"{fn} is not in website/_showcase/work/")
        if not (isinstance(pair.get("width"), int) and isinstance(pair.get("height"), int)): refuse("it has no width and height (of both pictures, which must be the same size)")
    return work.get("pairs", [])


def pair_html(pair, work, loc):
    """One before-and-after pair. Without JavaScript the two pictures sit side by side; with it the
    range input — an ordinary, keyboard-operable slider — wipes between them."""
    s = S[loc]
    course = next(c for c in work["courses"] if c["id"] == pair["course"])
    badges = "".join(f'<span class="sc-badge">{next(b for b in work["badges"] if b["id"] == bid)[loc]}</span>' for bid in pair.get("badges", []))
    base = "/assets/img/work/" + pair["id"]
    ext = pair.get("ext", "jpg")
    sample = f'<span class="sc-badge sc-badge--sample">{s["sample"]}</span>' if pair.get("sample") else ""
    w, h = pair["width"], pair["height"]
    alt = salon.esc(pair["alt"][loc])
    return f'''<figure class="ba" data-ba data-course="{course["id"]}">
      <div class="ba-stage" style="aspect-ratio:{w}/{h}">
        <img class="ba-img ba-after" src="{base}-after.{ext}" width="{w}" height="{h}" alt="{s["after"]}: {alt}" loading="lazy" decoding="async">
        <div class="ba-clip"><img class="ba-img ba-before" src="{base}-before.{ext}" width="{w}" height="{h}" alt="{s["before"]}: {alt}" loading="lazy" decoding="async"></div>
        <span class="ba-tag ba-tag--before" aria-hidden="true">{s["before"]}</span>
        <span class="ba-tag ba-tag--after" aria-hidden="true">{s["after"]}</span>
        <span class="ba-handle" aria-hidden="true"></span>
      </div>
      <label class="ba-label" for="ba-{pair["id"]}">{s["ba_label"]}</label>
      <input class="ba-range" id="ba-{pair["id"]}" type="range" min="0" max="100" value="50" step="1" aria-valuetext="{s["ba_half"]}" data-before="{s["before"]}" data-after="{s["after"]}">
      <figcaption>{sample}<span class="sc-badge sc-badge--course">{course[loc]}</span>{badges}
        <a class="ba-zoom" href="{base}-after.{ext}" data-lightbox data-caption="{alt}">{s["zoom"]}</a></figcaption>
    </figure>'''


# ------------------------------------------------------------------------------------------------
# Words. English and Welsh side by side; Welsh machine-written, for native review.
# ------------------------------------------------------------------------------------------------

S = {
    "en": {
        "eyebrow": "St Asaph &middot; North Wales",
        "h1": "<span>Train here.</span> <span>Be styled here.</span> <span>See the work.</span>",
        "lede": "A hairdressing and barbering academy, the training salon inside it, and the work its learners produce &mdash; under one roof in St Asaph.",
        "paths_label": "Three ways in",
        "p1_k": "The academy", "p1_h": "Train with us", "p1_p": "Hairdressing and barbering diplomas, CPD and apprenticeships.",
        "p2_k": "The academy salon", "p2_h": "Book the salon", "p2_p": "Cuts and colour by supervised learners, at learner prices.",
        "p3_k": "Learner work", "p3_h": "See learner work", "p3_p": "Before and after, by course and by level. Opening 2027.",
        "ac_eyebrow": "The academy",
        "ac_h": "A working salon is the classroom",
        "ac_p1": "Learners at Clwydian Academy train on the salon floor from the start: real clients, real appointments, and a qualified educator beside them who checks each stage before the next one begins.",
        "ac_p2": "We teach NVQ diplomas in hairdressing and barbering, CPD masterclasses for working stylists, and apprenticeships with salons across North Wales.",
        "ac_cta1": "See the courses", "ac_cta2": "Apprenticeships",
        "sa_eyebrow": "The academy salon",
        "sa_h": "Good hair, patiently done",
        "sa_p1": "Every appointment in our salon is carried out by a Level&nbsp;2 or Level&nbsp;3 learner. A qualified educator supervises throughout and checks the work at each stage.",
        "sa_p2": "It takes longer than a high-street salon, and it costs less. You choose the level when you book, and you see the price and the time to allow before you confirm. Adults only, in term time.",
        "sa_cta1": "Prices by learner level", "sa_cta2": "About the salon",
        "t_cut": "Cutting and styling", "t_colour": "Colour", "t_curl": "Styling and finishing", "t_gents": "Gents and barbering",
        "illus": "The photographs on this page are for illustration. They are not the work of academy learners &mdash; that work will appear on the learner work page, with each person&rsquo;s signed consent.",
        "wk_eyebrow": "Learner work",
        "wk_h": "The proof is in the before and after",
        "wk_p": "From 2027 this is where our learners&rsquo; work will be shown: real clients of the academy salon, photographed before and after, unretouched, by course and by level.",
        "wk_cta": "How the gallery will work",
        "soon": "Coming 2027",
        "soon_p": "The first learner work will appear here when the salon opens.",
        "find_eyebrow": "Find us", "find_h": "St Asaph Business Park", "find_contact": "Contact us",
        "find_road": "By road", "find_parking": "Parking", "find_transport": "Public transport",
        "find_tbc": "The unit number and full postcode will be added here once they are confirmed.",
        "areas": "Our learners and clients come from St Asaph, Rhyl, Rhuddlan, Bodelwyddan, Denbigh and across North Wales.",
        # the work page
        "w_h1": "Learner work",
        "w_lede": "Hair by the learners of Clwydian Academy, on real clients of the academy salon &mdash; shown before and after, by course and by level.",
        "w_crumb": "Learner work",
        "w_filter": "Browse by course",
        "w_all": "All courses",
        "w_level": "Level", "w_cpd": "For working stylists",
        "w_empty_h": "Coming 2027",
        "w_empty_p": "Work from this course will appear here once its first learners are in the salon.",
        "sample": "Sample",
        "sample_note": "This is sample data, made up to show how a portfolio page will work. It is not a real learner, the panels are not photographs, and it is not built on the public site.",
        "pf_h1": "Learner portfolio", "pf_started": "training began", "pf_level": "learner",
        "pf_ach_h": "Units and competitions", "pf_work_h": "Work", "pf_none": "No work has been added yet.",
        "pf_consent": "This page is published with the learner&rsquo;s own consent, and each picture with the client&rsquo;s. Neither is named.",
        "pf_back": "All learner work", "pf_list_h": "Learner portfolios", "pf_open": "Open portfolio",
        "before": "Before", "after": "After",
        "ba_label": "Slide to compare before and after",
        "ba_half": "Half before, half after",
        "zoom": "View larger",
        "close": "Close",
        "w_rules_h": "Before and after, honestly",
        "w_rules": ["Every person shown is a client of our own salon who has given signed, dated consent for these photographs to be used.",
                    "The hair is never retouched &mdash; not in the before, and not in the after.",
                    "Nothing is done to the after picture that is not done to the before: same crop, same light correction, or none.",
                    "We keep the original, untouched files for every picture we publish.",
                    "No learner is named. Work is shown by course and level, not by person."],
        "w_photo_h": "How the work is photographed",
        "w_photo": ["The same chair, the same wall and the same light for both pictures.",
                    "Dry hair, front, side and back, at eye level.",
                    "The before is taken at the consultation, before anything is done.",
                    "No filters, no ring-light glare, no smoothing."],
        "w_badge_h": "What the badges mean",
        "w_badge_q": "The work was assessed as part of a qualification unit.",
        "w_badge_c": "The work was entered in a competition.",
        "w_port_h": "A portfolio for every learner",
        "w_port_p": "Each learner builds a private portfolio of their own work as they train, to take to interviews and into employment. Only work with the client&rsquo;s consent is shown here, and never under the learner&rsquo;s name.",
        "w_cta_h": "Would you like your hair done by a learner?",
        "w_cta_p": "Appointments are supervised by a qualified educator and priced by the learner&rsquo;s level.",
    },
    "cy": {
        "eyebrow": "Llanelwy &middot; Gogledd Cymru",
        "h1": "<span>Hyfforddwch yma.</span> <span>Cewch eich steilio yma.</span> <span>Gwelwch y gwaith.</span>",
        "lede": "Academi trin gwallt a barbro, y salon hyfforddi y tu mewn iddi, a&rsquo;r gwaith y mae ei dysgwyr yn ei gynhyrchu &mdash; dan un to yn Llanelwy.",
        "paths_label": "Tair ffordd i mewn",
        "p1_k": "Yr academi", "p1_h": "Hyfforddwch gyda ni", "p1_p": "Diplomâu trin gwallt a barbro, DPP a phrentisiaethau.",
        "p2_k": "Salon yr academi", "p2_h": "Archebu&rsquo;r salon", "p2_p": "Torri a lliwio gan ddysgwyr dan oruchwyliaeth, am brisiau dysgwyr.",
        "p3_k": "Gwaith dysgwyr", "p3_h": "Gweld gwaith dysgwyr", "p3_p": "Cyn ac ar &ocirc;l, fesul cwrs a fesul lefel. Yn agor yn 2027.",
        "ac_eyebrow": "Yr academi",
        "ac_h": "Salon go iawn yw&rsquo;r ystafell ddosbarth",
        "ac_p1": "Mae dysgwyr Clwydian Academy yn hyfforddi ar lawr y salon o&rsquo;r cychwyn: cleientiaid go iawn, apwyntiadau go iawn, ac addysgwr cymwysedig wrth eu hymyl sy&rsquo;n gwirio pob cam cyn i&rsquo;r nesaf ddechrau.",
        "ac_p2": "Rydym yn addysgu diplomâu NVQ mewn trin gwallt a barbro, dosbarthiadau meistr DPP i steilwyr sy&rsquo;n gweithio, a phrentisiaethau gyda salonau ledled Gogledd Cymru.",
        "ac_cta1": "Gweld y cyrsiau", "ac_cta2": "Prentisiaethau",
        "sa_eyebrow": "Salon yr academi",
        "sa_h": "Gwallt da, wedi&rsquo;i wneud yn amyneddgar",
        "sa_p1": "Mae pob apwyntiad yn ein salon yn cael ei gynnal gan ddysgwr Lefel&nbsp;2 neu Lefel&nbsp;3. Mae addysgwr cymwysedig yn goruchwylio drwy gydol yr amser ac yn gwirio&rsquo;r gwaith ar bob cam.",
        "sa_p2": "Mae&rsquo;n cymryd mwy o amser na salon ar y stryd fawr, ac mae&rsquo;n costio llai. Chi sy&rsquo;n dewis y lefel wrth archebu, a byddwch yn gweld y pris a&rsquo;r amser i&rsquo;w ganiat&aacute;u cyn cadarnhau. Oedolion yn unig, yn ystod y tymor.",
        "sa_cta1": "Prisiau fesul lefel dysgwr", "sa_cta2": "Am y salon",
        "t_cut": "Torri a steilio", "t_colour": "Lliw", "t_curl": "Steilio a gorffen", "t_gents": "Dynion a barbro",
        "illus": "Mae&rsquo;r ffotograffau ar y dudalen hon at ddibenion darlunio. Nid gwaith dysgwyr yr academi ydynt &mdash; bydd y gwaith hwnnw&rsquo;n ymddangos ar dudalen gwaith y dysgwyr, gyda chaniat&acirc;d llofnodedig pob person.",
        "wk_eyebrow": "Gwaith dysgwyr",
        "wk_h": "Mae&rsquo;r prawf yn y cyn ac ar &ocirc;l",
        "wk_p": "O 2027 ymlaen, dyma lle bydd gwaith ein dysgwyr yn cael ei ddangos: cleientiaid go iawn salon yr academi, wedi&rsquo;u tynnu cyn ac ar &ocirc;l, heb eu hatgyffwrdd, fesul cwrs a fesul lefel.",
        "wk_cta": "Sut bydd yr oriel yn gweithio",
        "soon": "Yn dod yn 2027",
        "soon_p": "Bydd gwaith cyntaf y dysgwyr yn ymddangos yma pan fydd y salon yn agor.",
        "find_eyebrow": "Dod o hyd i ni", "find_h": "Parc Busnes Llanelwy", "find_contact": "Cysylltu &acirc; ni",
        "find_road": "Ar y ffordd", "find_parking": "Parcio", "find_transport": "Trafnidiaeth gyhoeddus",
        "find_tbc": "Bydd rhif yr uned a&rsquo;r cod post llawn yn cael eu hychwanegu yma ar &ocirc;l eu cadarnhau.",
        "areas": "Daw ein dysgwyr a&rsquo;n cleientiaid o Lanelwy, y Rhyl, Rhuddlan, Bodelwyddan, Dinbych a ledled Gogledd Cymru.",
        "w_h1": "Gwaith dysgwyr",
        "w_lede": "Gwallt gan ddysgwyr Clwydian Academy, ar gleientiaid go iawn salon yr academi &mdash; wedi&rsquo;i ddangos cyn ac ar &ocirc;l, fesul cwrs a fesul lefel.",
        "w_crumb": "Gwaith dysgwyr",
        "w_filter": "Pori fesul cwrs",
        "w_all": "Pob cwrs",
        "w_level": "Lefel", "w_cpd": "I steilwyr sy&rsquo;n gweithio",
        "w_empty_h": "Yn dod yn 2027",
        "w_empty_p": "Bydd gwaith o&rsquo;r cwrs hwn yn ymddangos yma unwaith y bydd ei ddysgwyr cyntaf yn y salon.",
        "sample": "Sampl",
        "sample_note": "Data sampl yw hwn, wedi&rsquo;i greu i ddangos sut bydd tudalen bortffolio&rsquo;n gweithio. Nid dysgwr go iawn mohono, nid ffotograffau yw&rsquo;r paneli, ac nid yw&rsquo;n cael ei adeiladu ar y wefan gyhoeddus.",
        "pf_h1": "Portffolio dysgwr", "pf_started": "dechreuodd yr hyfforddiant", "pf_level": "dysgwr",
        "pf_ach_h": "Unedau a chystadlaethau", "pf_work_h": "Gwaith", "pf_none": "Nid oes gwaith wedi&rsquo;i ychwanegu eto.",
        "pf_consent": "Cyhoeddir y dudalen hon gyda chaniat&acirc;d y dysgwr ei hun, a phob llun gyda chaniat&acirc;d y cleient. Nid yw&rsquo;r naill na&rsquo;r llall yn cael ei enwi.",
        "pf_back": "Holl waith y dysgwyr", "pf_list_h": "Portffolios dysgwyr", "pf_open": "Agor y portffolio",
        "before": "Cyn", "after": "Ar &ocirc;l",
        "ba_label": "Llithrwch i gymharu cyn ac ar &ocirc;l",
        "ba_half": "Hanner cyn, hanner ar &ocirc;l",
        "zoom": "Gweld yn fwy",
        "close": "Cau",
        "w_rules_h": "Cyn ac ar &ocirc;l, yn onest",
        "w_rules": ["Mae pob person a ddangosir yn gleient i&rsquo;n salon ni ein hunain sydd wedi rhoi caniat&acirc;d llofnodedig, wedi&rsquo;i ddyddio, i&rsquo;r ffotograffau hyn gael eu defnyddio.",
                    "Nid yw&rsquo;r gwallt byth yn cael ei atgyffwrdd &mdash; nid yn y llun cyn, nac yn y llun ar &ocirc;l.",
                    "Ni wneir dim i&rsquo;r llun ar &ocirc;l nad yw&rsquo;n cael ei wneud i&rsquo;r llun cyn: yr un tocio, yr un cywiriad golau, neu ddim o gwbl.",
                    "Rydym yn cadw&rsquo;r ffeiliau gwreiddiol, heb eu cyffwrdd, ar gyfer pob llun a gyhoeddwn.",
                    "Nid oes unrhyw ddysgwr yn cael ei enwi. Dangosir gwaith fesul cwrs a lefel, nid fesul person."],
        "w_photo_h": "Sut mae&rsquo;r gwaith yn cael ei dynnu",
        "w_photo": ["Yr un gadair, yr un wal a&rsquo;r un golau ar gyfer y ddau lun.",
                    "Gwallt sych, o&rsquo;r tu blaen, o&rsquo;r ochr ac o&rsquo;r cefn, ar lefel y llygad.",
                    "Tynnir y llun cyn yn yr ymgynghoriad, cyn i unrhyw beth gael ei wneud.",
                    "Dim hidlwyr, dim llacharedd golau cylch, dim llyfnhau."],
        "w_badge_h": "Beth mae&rsquo;r bathodynnau&rsquo;n ei olygu",
        "w_badge_q": "Aseswyd y gwaith fel rhan o uned gymhwyster.",
        "w_badge_c": "Cyflwynwyd y gwaith mewn cystadleuaeth.",
        "w_port_h": "Portffolio i bob dysgwr",
        "w_port_p": "Mae pob dysgwr yn adeiladu portffolio preifat o&rsquo;i waith ei hun wrth hyfforddi, i fynd ag ef i gyfweliadau ac i gyflogaeth. Dim ond gwaith gyda chaniat&acirc;d y cleient a ddangosir yma, a byth dan enw&rsquo;r dysgwr.",
        "w_cta_h": "Hoffech chi i ddysgwr wneud eich gwallt?",
        "w_cta_p": "Mae apwyntiadau dan oruchwyliaeth addysgwr cymwysedig ac wedi&rsquo;u prisio yn &ocirc;l lefel y dysgwr.",
    },
}

# Titles and descriptions while the showcase is on. One line each; the towns are named once.
META = {
    "home": {
        "en": ("Hairdressing Academy &amp; Training Salon in St Asaph | Clwydian Academy",
               "A hairdressing and barbering academy in St Asaph with its own training salon, for learners and clients from Rhyl, Rhuddlan, Bodelwyddan, Denbigh and across North Wales."),
        "cy": ("Academi Trin Gwallt a Salon Hyfforddi yn Llanelwy | Clwydian Academy",
               "Academi trin gwallt a barbro yn Llanelwy gyda&rsquo;i salon hyfforddi ei hun, i ddysgwyr a chleientiaid o&rsquo;r Rhyl, Rhuddlan, Bodelwyddan, Dinbych a ledled Gogledd Cymru."),
    },
    "salon": {
        "en": ("Hairdresser &amp; Barber in St Asaph | Clwydian Academy Salon",
               "Cuts, colour and barbering by supervised learners at learner prices, in term time, at St Asaph Business Park &mdash; a short drive from Rhyl, Rhuddlan, Bodelwyddan and Denbigh."),
        "cy": ("Triniwr Gwallt a Barbwr yn Llanelwy | Salon Clwydian Academy",
               "Torri, lliwio a barbro gan ddysgwyr dan oruchwyliaeth am brisiau dysgwyr, yn ystod y tymor, ym Mharc Busnes Llanelwy &mdash; taith fer o&rsquo;r Rhyl, Rhuddlan, Bodelwyddan a Dinbych."),
    },
    "salon-prices": {
        "en": ("Hair Salon Prices by Learner Level, St Asaph | Clwydian Academy Salon",
               "What a cut or colour costs with a Level 2 or Level 3 learner at the Clwydian Academy salon in St Asaph, how long to allow, and how each price is worked out."),
        "cy": ("Prisiau Salon Gwallt fesul Lefel Dysgwr, Llanelwy | Salon Clwydian Academy",
               "Faint mae torri neu liwio&rsquo;n ei gostio gyda dysgwr Lefel 2 neu Lefel 3 yn salon Clwydian Academy yn Llanelwy, faint o amser i&rsquo;w ganiat&aacute;u, a sut y cyfrifir pob pris."),
    },
    "work": {
        "en": ("Learner Work: Before &amp; After Hair | Clwydian Academy, St Asaph",
               "Before-and-after hair by the learners of Clwydian Academy in St Asaph, on real clients of the academy salon, by course and level. Opening 2027."),
        "cy": ("Gwaith Dysgwyr: Gwallt Cyn ac Ar &Ocirc;l | Clwydian Academy, Llanelwy",
               "Gwallt cyn ac ar &ocirc;l gan ddysgwyr Clwydian Academy yn Llanelwy, ar gleientiaid go iawn salon yr academi, fesul cwrs a lefel. Yn agor yn 2027."),
    },
}


# ------------------------------------------------------------------------------------------------
# The home page
# ------------------------------------------------------------------------------------------------

def soon_cards(loc, n=3):
    s = S[loc]
    return "".join(f'''<div class="sc-soon reveal" style="--d:{i * 0.07:.2f}s"><span class="sc-soon-mark" aria-hidden="true"></span>
          <p class="sc-soon-h">{s["soon"]}</p><p>{s["soon_p"]}</p></div>''' for i in range(n))


def home_body(loc, site):
    s = S[loc]
    sp = salon.PATHS
    path = lambda n, href, key: f'''<a class="sc-path" href="{href}">
        <span class="sc-path-k">0{n} &middot; {s[key + "_k"]}</span>
        <span class="sc-path-h">{s[key + "_h"]}</span>
        <span class="sc-path-p">{s[key + "_p"]}</span>
        <span class="sc-path-go" aria-hidden="true">&rarr;</span>
      </a>'''
    tile = lambda stem, key, d: f'''<figure class="sc-tile reveal" style="--d:{d}s">{picture(stem, loc, "(max-width: 700px) 50vw, 25vw")}
          <figcaption>{s[key]}</figcaption></figure>'''
    return f'''<section class="sc-hero">
  <div class="sc-hero-media">
    <picture>
      <source media="(max-width: 700px)" type="image/webp" srcset="{", ".join(f"/assets/img/photos/showcase-hero-portrait-{w}.webp {w}w" for w, _ in manifest()["showcase-hero-portrait"])}" sizes="100vw">
      <source media="(max-width: 700px)" srcset="{", ".join(f"/assets/img/photos/showcase-hero-portrait-{w}.jpg {w}w" for w, _ in manifest()["showcase-hero-portrait"])}" sizes="100vw">
      <source type="image/webp" srcset="{", ".join(f"/assets/img/photos/showcase-hero-{w}.webp {w}w" for w, _ in manifest()["showcase-hero"])}" sizes="100vw">
      <img src="/assets/img/photos/showcase-hero-1440.jpg" srcset="{", ".join(f"/assets/img/photos/showcase-hero-{w}.jpg {w}w" for w, _ in manifest()["showcase-hero"])}" sizes="100vw" width="{manifest()["showcase-hero"][1][0]}" height="{manifest()["showcase-hero"][1][1]}" alt="{salon.esc(photos()["showcase-hero"]["alt"][loc])}" fetchpriority="high" decoding="async">
    </picture>
  </div>
  <div class="wrap sc-hero-inner">
    <p class="eyebrow">{s["eyebrow"]}</p>
    <h1>{s["h1"]}</h1>
    <p class="lede">{s["lede"]}</p>
  </div>
  <nav class="wrap sc-paths" aria-label="{s["paths_label"]}">
      {path(1, COURSES[loc], "p1")}
      {path(2, sp["home"][loc], "p2")}
      {path(3, WORK[loc], "p3")}
  </nav>
</section>

<section class="section" id="academy" aria-labelledby="academy-h">
  <div class="wrap">
    <div class="split">
      <div class="reveal">
        <p class="eyebrow">{s["ac_eyebrow"]}</p>
        <h2 id="academy-h">{s["ac_h"]}</h2>
        <p class="lede">{s["ac_p1"]}</p>
        <p>{s["ac_p2"]}</p>
        <p class="sc-actions"><a class="btn btn-primary" href="{COURSES[loc]}">{s["ac_cta1"]}</a> <a class="btn btn-outline" href="{APPRENTICE[loc]}">{s["ac_cta2"]}</a></p>
      </div>
      <div class="sc-frame reveal" style="--d:.08s">{picture("academy-styles-01", loc, "(max-width: 880px) 100vw, 50vw")}</div>
    </div>
  </div>
</section>

<section class="section on-navy sc-salon" id="salon" aria-labelledby="salon-h">
  <div class="wrap">
    <div class="sc-salon-head reveal">
      <p class="eyebrow">{s["sa_eyebrow"]}</p>
      <h2 id="salon-h">{s["sa_h"]}</h2>
      <p class="lede">{s["sa_p1"]}</p>
      <p>{s["sa_p2"]}</p>
      <p class="sc-actions"><a class="btn btn-gold" href="{sp["prices"][loc]}">{s["sa_cta1"]}</a> <a class="btn btn-ghost-light" href="{sp["home"][loc]}">{s["sa_cta2"]}</a></p>
    </div>
    <div class="sc-tiles">
      {tile("salon-cut-01", "t_cut", 0)}
      {tile("salon-colour-01", "t_colour", .06)}
      {tile("salon-curl-01", "t_curl", .12)}
      {tile("salon-gents-01", "t_gents", .18)}
    </div>
    <p class="sc-illus">{s["illus"]}</p>
  </div>
</section>

<section class="section" id="work" aria-labelledby="work-h">
  <div class="wrap">
    <div class="section-head reveal">
      <p class="eyebrow">{s["wk_eyebrow"]}</p>
      <h2 id="work-h">{s["wk_h"]}</h2>
      <p class="lede measure">{s["wk_p"]}</p>
    </div>
    <div class="sc-soon-grid">{soon_cards(loc)}</div>
    <p class="sc-actions center"><a class="btn btn-outline" href="{WORK[loc]}">{s["wk_cta"]}</a></p>
  </div>
</section>

{find_us(loc, site)}
<section class="section--tight sc-areas"><div class="wrap"><p class="center">{s["areas"]}</p></div></section>
'''


# ------------------------------------------------------------------------------------------------
# The learner-work page
# ------------------------------------------------------------------------------------------------

MONTHS_CY = ["Ionawr", "Chwefror", "Mawrth", "Ebrill", "Mai", "Mehefin", "Gorffennaf", "Awst", "Medi", "Hydref", "Tachwedd", "Rhagfyr"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def month(ym, loc):
    y, m = ym.split("-")
    return f"{(MONTHS_EN if loc == 'en' else MONTHS_CY)[int(m) - 1]} {y}"


def portfolio_path(slug, loc):
    return f"{WORK[loc]}{slug}/"


def portfolio_label(pf, work, loc):
    """What a portfolio is called, since it cannot be called by a name."""
    course = next(c for c in work["courses"] if c["id"] == pf["course"])
    return f'{course[loc]} {S[loc]["pf_level"]} &middot; {S[loc]["pf_started"]} {month(pf["started"], loc)}'


def portfolio_pages(preview=False):
    """The page registry entries for the portfolios — one EN/CY pair each — so they get the same
    chrome, hreflang check and sitemap treatment as every other page. Sample pages are noindex."""
    work = _load(WORK_PATH)
    out = []
    for pf in validate_portfolios(work, preview=preview):
        label = lambda loc: re.sub(r"&\w+;", "-", portfolio_label(pf, work, loc))
        out.append({"key": "work-" + pf["slug"], "nav": "/work/", "noindex": pf.get("sample") is True, "priority": "0.5", "legal": "plain",
                    "generated": "showcase-portfolio", "slug": pf["slug"],
                    "en": {"path": portfolio_path(pf["slug"], "en"), "title": f"Learner Portfolio: {label('en')} | Clwydian Academy",
                           "desc": "Work by one learner of Clwydian Academy in St Asaph, on real clients of the academy salon, shown with their consent."},
                    "cy": {"path": portfolio_path(pf["slug"], "cy"), "title": f"Portffolio Dysgwr: {label('cy')} | Clwydian Academy",
                           "desc": "Gwaith gan un o ddysgwyr Clwydian Academy yn Llanelwy, ar gleientiaid go iawn salon yr academi, wedi&rsquo;i ddangos gyda&rsquo;u caniat&acirc;d."}})
    return out


def portfolio_body(slug, loc, site, preview=False):
    s = S[loc]
    work = _load(WORK_PATH)
    pf = next(p for p in validate_portfolios(work, preview=preview) if p["slug"] == slug)
    pairs = [p for p in validate_pairs(work, preview=preview) if p.get("portfolio") == slug]
    badge = {b["id"]: b[loc] for b in work["badges"]}
    ach = "".join(f'<li><span class="sc-badge">{badge[a["badge"]]}</span> <span>{a[loc]}</span> <time datetime="{a["date"]}">{month(a["date"], loc)}</time></li>' for a in pf.get("achievements", []))
    note = f'<p class="sc-sample-note" role="note"><strong>{s["sample"]}.</strong> {s["sample_note"]}</p>' if pf.get("sample") else ""
    gallery = ('<div class="ba-grid">' + "".join(pair_html(p, work, loc) for p in pairs) + "</div>") if pairs else f'<p>{s["pf_none"]}</p>'
    return f'''<section class="page-hero">
  <div class="wrap">
    {salon.crumbs(loc, (s["w_crumb"], WORK[loc]), (s["pf_h1"], None))}
    <p class="eyebrow mt-2">{s["wk_eyebrow"]}</p>
    <h1>{s["pf_h1"]}</h1>
    <p class="lede">{portfolio_label(pf, work, loc)}</p>
    {note}
  </div>
</section>

<section class="section">
  <div class="wrap">
    <h2>{s["pf_ach_h"]}</h2>
    <ul class="sc-achievements">{ach}</ul>
    <h2 class="mt-3">{s["pf_work_h"]}</h2>
    {gallery}
    <p class="sc-illus sc-illus--light">{s["pf_consent"]}</p>
    <p class="sc-actions"><a class="btn btn-outline" href="{WORK[loc]}">&larr; {s["pf_back"]}</a></p>
  </div>
</section>
<dialog class="sc-lightbox" id="sc-lightbox" aria-label="{s["zoom"]}"><button type="button" class="sc-lightbox-close" data-lightbox-close aria-label="{s["close"]}">&times;</button><img alt=""><p></p></dialog>
'''


def work_body(loc, site, preview=False):
    s = S[loc]
    work = _load(WORK_PATH)
    folios = validate_portfolios(work, preview=preview)
    pairs = validate_pairs(work, preview=preview)
    folio_cards = "".join(f'''<a class="sc-folio" href="{portfolio_path(pf["slug"], loc)}">{'<span class="sc-badge sc-badge--sample">' + s["sample"] + '</span>' if pf.get("sample") else ""}
        <span class="sc-folio-h">{portfolio_label(pf, work, loc)}</span><span class="sc-folio-go">{s["pf_open"]} &rarr;</span></a>''' for pf in folios)
    folio_section = f'''<section class="sc-folios" id="portfolios" aria-labelledby="portfolios-h"><header><h2 id="portfolios-h">{s["pf_list_h"]}</h2></header>
      <div class="sc-folio-grid">{folio_cards}</div></section>''' if folios else ""
    chips = [f'<a class="chip" href="#{c["id"]}">{c[loc]}</a>' for c in work["courses"]]
    sections = []
    for c in work["courses"]:
        mine = [p for p in pairs if p["course"] == c["id"]]
        level = f'{s["w_level"]} {c["level"]}' if c["level"] else s["w_cpd"]
        inner = ('<div class="ba-grid">' + "".join(pair_html(p, work, loc) for p in mine) + "</div>") if mine else \
            f'''<div class="sc-soon-grid"><div class="sc-soon"><span class="sc-soon-mark" aria-hidden="true"></span>
          <p class="sc-soon-h">{s["w_empty_h"]}</p><p>{s["w_empty_p"]}</p></div></div>'''
        sections.append(f'''<section class="sc-course reveal" id="{c["id"]}" aria-labelledby="{c["id"]}-h">
      <header><h2 id="{c["id"]}-h">{c[loc]}</h2><span class="sc-badge sc-badge--course">{level}</span></header>
      {inner}
    </section>''')
    li = lambda items: "".join(f"<li>{x}</li>" for x in items)
    badge = {b["id"]: b[loc] for b in work["badges"]}
    return f'''<section class="page-hero">
  <div class="wrap">
    {salon.crumbs(loc, (s["w_crumb"], None))}
    <p class="eyebrow mt-2">{s["wk_eyebrow"]}</p>
    <h1>{s["w_h1"]}</h1>
    <p class="lede">{s["w_lede"]}</p>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <nav class="sc-filter" aria-label="{s["w_filter"]}">{"".join(chips)}</nav>
    {"".join(sections)}
    {folio_section}
  </div>
</section>

<section class="section on-heather">
  <div class="wrap">
    <div class="grid grid-2 sc-notes">
      <div class="reveal"><h2>{s["w_rules_h"]}</h2><ul class="feature-list">{li(s["w_rules"])}</ul></div>
      <div class="reveal" style="--d:.08s"><h2>{s["w_photo_h"]}</h2><ul class="feature-list">{li(s["w_photo"])}</ul></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="grid grid-2 sc-notes">
      <div class="reveal"><h2>{s["w_badge_h"]}</h2>
        <dl class="sc-badges"><div><dt><span class="sc-badge">{badge["qualification"]}</span></dt><dd>{s["w_badge_q"]}</dd></div>
        <div><dt><span class="sc-badge">{badge["competition"]}</span></dt><dd>{s["w_badge_c"]}</dd></div></dl></div>
      <div class="reveal" style="--d:.08s"><h2>{s["w_port_h"]}</h2><p>{s["w_port_p"]}</p></div>
    </div>
  </div>
</section>

<section class="section--tight cta-banner">
  <div class="wrap center">
    <h2>{s["w_cta_h"]}</h2>
    <p class="lede">{s["w_cta_p"]}</p>
    <p class="sc-actions"><a class="btn btn-gold" href="{salon.PATHS["prices"][loc]}">{s["sa_cta1"]}</a> <a class="btn btn-ghost-light" href="{salon.PATHS["home"][loc]}">{s["sa_cta2"]}</a></p>
  </div>
</section>
<dialog class="sc-lightbox" id="sc-lightbox" aria-label="{s["zoom"]}"><button type="button" class="sc-lightbox-close" data-lightbox-close aria-label="{s["close"]}">&times;</button><img alt=""><p></p></dialog>
'''


# ------------------------------------------------------------------------------------------------
# HairSalon structured data
# ------------------------------------------------------------------------------------------------

DAY_NAMES = {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday", "fri": "Friday", "sat": "Saturday", "sun": "Sunday"}


def hairsalon_ld(loc, domain, org, site):
    """HairSalon — the most specific type there is for it, and no additionalType.

    One address, from _data/site.json. While the unit and postcode are TODO_PM the block carries
    the locality and region only: a made-up street line in structured data is a false statement
    to a search engine. Opening hours are term-time hours, so each term is its own
    OpeningHoursSpecification with validFrom and validThrough; none is written until the PM has
    confirmed both the sessions and the term dates. NO review and NO aggregateRating, ever: a
    business may not mark up testimonials it collected itself."""
    p = salon.raw()
    a = site["salon_address"]
    address = {"@type": "PostalAddress", "addressLocality": "St Asaph", "addressRegion": "Denbighshire", "addressCountry": "GB"}
    if not is_todo(a):
        address.update({"streetAddress": a["value"]["street"], "postalCode": a["value"]["postcode"]})
    block = {
        "@context": "https://schema.org", "@type": "HairSalon", "@id": domain + "/salon/#salon",
        "name": "Clwydian Academy Salon" if loc == "en" else "Salon Clwydian Academy",
        "description": ("Training salon in St Asaph, North Wales: cuts, colour and barbering by Clwydian Academy learners, supervised by qualified educators, in term time."
                        if loc == "en" else "Salon hyfforddi yn Llanelwy, Gogledd Cymru: torri, lliwio a barbro gan ddysgwyr Clwydian Academy, dan oruchwyliaeth addysgwyr cymwysedig, yn ystod y tymor."),
        "url": domain + salon.PATHS["home"][loc],
        "image": org["image"], "email": site["email"], "address": address,
        "knowsLanguage": ["en", "cy"],
    }
    if not is_todo(a["geo"]):
        block["geo"] = {"@type": "GeoCoordinates", **a["geo"]["value"]}
    prices = [salon.l2_price(p, sv) for sv in p["services"] if salon.printable(sv["stylist_price"]) and sv.get("category") in p["pricing"]["l2_percent_off"]]
    prices += [salon.l3_price(sv) for sv in p["services"] if salon.printable(sv["stylist_price"])]
    if prices and not salon.draft_paths(p):
        block["priceRange"] = f"£{min(prices)}–£{max(prices)}"
    op = p["opening"]
    if salon.printable(op["sessions"]) and salon.printable(op["terms"]):
        block["openingHoursSpecification"] = [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": "https://schema.org/" + DAY_NAMES[d],
             "opens": x["open"], "closes": x["close"], "validFrom": term["from"], "validThrough": term["to"]}
            for term in salon.val(op["terms"]) for d, ss in salon.val(op["sessions"]).items() for x in ss]
    link = {"@context": "https://schema.org", "@type": org["@type"], "@id": org["@id"], "department": {"@id": block["@id"]}}
    return [block, link]


BANNED_LD = ("review", "aggregateRating", "additionalType")
BANNED_TYPES = ("FAQPage",)


def check_ld(blocks, where):
    """No review markup on our own testimonials, no additionalType, and no FAQPage: Google ended
    FAQ rich results on 7 May 2026, so questions and answers are plain visible content only."""
    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in BANNED_LD: sys.exit(f"showcase: {where}: structured data carries {k!r}")
                if k == "@type" and v in BANNED_TYPES: sys.exit(f"showcase: {where}: structured data is a {v}")
                walk(v)
        elif isinstance(node, list):
            for v in node: walk(v)
    walk(blocks)


# ------------------------------------------------------------------------------------------------
# hreflang: one map, three links, both ways
# ------------------------------------------------------------------------------------------------

def hreflang_links(page, domain):
    """en-GB, cy and x-default, from the page registry — the one slug map. A page with one
    language has no alternates; the build check below refuses that for anything indexable."""
    en, cy = domain + page["en"]["path"], domain + page["cy"]["path"]
    return [f'<link rel="alternate" hreflang="en-GB" href="{en}">',
            f'<link rel="alternate" hreflang="cy" href="{cy}">',
            f'<link rel="alternate" hreflang="x-default" href="{en}">']


def check_hreflang(pages, built, domain):
    """Fails the build on a missing or one-way pair. `built` maps a path to its written HTML."""
    paths = [p[loc]["path"] for p in pages for loc in ("en", "cy") if p.get(loc)]
    if len(paths) != len(set(paths)):
        sys.exit("showcase: hreflang: two pages in pages.json share a path")
    for page in pages:
        if page.get("noindex") and not page.get("cy"):
            continue                          # the 404 page: one language, never indexed, no alternates
        if not (page.get("en") and page.get("cy")):
            sys.exit(f"showcase: hreflang: {page['key']} has no {'Welsh' if page.get('en') else 'English'} page — every page is a pair")
        want = hreflang_links(page, domain)
        for loc in ("en", "cy"):
            html = built.get(page[loc]["path"])
            if html is None:
                continue                      # not built (a switch is off): nothing to check
            for link in want:
                if link not in html:
                    sys.exit(f"showcase: hreflang: {page[loc]['path']} is missing {link}")
            if f'<link rel="canonical" href="{domain}{page[loc]["path"]}">' not in html:
                sys.exit(f"showcase: hreflang: {page[loc]['path']} does not name itself as canonical")
            if len(re.findall(r'rel="alternate" hreflang=', html)) != 3:
                sys.exit(f"showcase: hreflang: {page[loc]['path']} carries alternates beyond the three")
