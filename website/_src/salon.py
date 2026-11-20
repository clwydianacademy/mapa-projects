"""The training salon's pages, rendered from _data/salon/policy.json in both languages.

    /salon/  /salon/prices/  /salon/models/  /salon/terms/   and their /cy/salon/ mirrors

These are MARKETING pages. Booking happens on the salon's own booking site (policy "booking_url"),
which is a separate repository and Vercel project; every "Book" control here is a link to it.

THE SWITCH. is_public() reads "public" in the policy. While it is false, build.py builds none of
this and adds no nav item — the deployed site is exactly what it was (Mark, 17 Nov 2026: nothing
public until VTCT approval and the signed lease).

NOTHING UNCONFIRMED IS PUBLISHED. A value in the policy written {"todo_pm": true, "value": X} is a
placeholder; {"pm_draft": "central scenario", "value": X} is the PM's draft. While any of either
remain, confirmed() is False and build.py builds every salon page noindex and leaves it out of
the sitemap. On the pages a placeholder is never printed — the reader sees "to be confirmed" —
and a draft is printed under a visible "Draft" notice (printable(), draft_notice()).

The Welsh here is machine-written and unreviewed: every string is listed in prompts/RELAY.md
under WELSH FOR REVIEW.
"""
import html, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA_PATH = os.path.join(REPO, "_data", "salon", "policy.json")

PATHS = {
    "home":   {"en": "/salon/",        "cy": "/cy/salon/"},
    "prices": {"en": "/salon/prices/", "cy": "/cy/salon/prisiau/"},
    "models": {"en": "/salon/models/", "cy": "/cy/salon/modelau/"},
    "terms":  {"en": "/salon/terms/",  "cy": "/cy/salon/telerau/"},
}
HOME = {"en": "/", "cy": "/cy/"}
PRIVACY = {"en": "/privacy/", "cy": "/cy/preifatrwydd/"}

def raw():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)

def is_todo(node):
    return isinstance(node, dict) and node.get("todo_pm") is True

def is_draft(node):
    return isinstance(node, dict) and isinstance(node.get("pm_draft"), str)

def val(node):
    """The value with every wrapper stripped, all the way down. For arithmetic and for printing a
    value that printable() has already allowed."""
    if is_todo(node) or is_draft(node):
        return val(node["value"])
    if isinstance(node, list):
        return [val(x) for x in node]
    if isinstance(node, dict):
        return {k: val(v) for k, v in node.items() if not k.startswith("_")}
    return node

def printable(node):
    """May this value be shown to a reader? A PLACEHOLDER (todo_pm) never — nor anything with a
    placeholder inside it. The PM's DRAFT may, because the page says it is a draft."""
    if is_todo(node):
        return False
    if is_draft(node):
        return printable(node["value"])
    if isinstance(node, list):
        return all(printable(x) for x in node)
    if isinstance(node, dict):
        return all(printable(v) for v in node.values())
    return True

def paths(node, kind=None, path=""):
    """Every unconfirmed path in the policy: kind "todo", "draft" or None for both. The same walk
    as unconfirmed() in site/api/_lib/salon/policy.js."""
    out = []
    if is_todo(node) or is_draft(node):
        if kind is None or (kind == "todo") == is_todo(node):
            out.append(path)
        return out + paths(node["value"], kind, path)
    if isinstance(node, list):
        for i, v in enumerate(node):
            out += paths(v, kind, path + "." + (v["id"] if isinstance(v, dict) and "id" in v else str(i)))
    elif isinstance(node, dict):
        for k, v in node.items():
            out += paths(v, kind, path + "." + k if path else k)
    return out

def todo_paths(node):
    return paths(node, "todo")

def draft_paths(node):
    return paths(node, "draft")

def confirmed(policy=None):
    """Nothing in the policy is a placeholder or a draft."""
    return not paths(policy if policy is not None else raw())

# ------------------------------------------------------------------------------------------------
# Strings. One dictionary, both languages. The booking journey's script has no words of its own:
# it reads JOURNEY from the page.
# ------------------------------------------------------------------------------------------------
T = {'tbc': {'en': 'To be confirmed', 'cy': 'I&rsquo;w gadarnhau'},
 'home': {'en': 'Home', 'cy': 'Hafan'},
 'salon': {'en': 'Our Salon', 'cy': 'Ein Salon'},
 'prices': {'en': 'Prices', 'cy': 'Prisiau'},
 'book': {'en': 'Book online', 'cy': 'Archebu ar-lein'},
 'models': {'en': 'Be a model', 'cy': 'Bod yn fodel'},
 'terms': {'en': 'Booking terms', 'cy': 'Telerau archebu'},
 'eyebrow': {'en': 'Clwydian Academy training salon', 'cy': 'Salon hyfforddi Clwydian Academy'},
 'soon_h': {'en': 'Opening soon', 'cy': 'Yn agor yn fuan'},
 'soon_p': {'en': 'We are still confirming the salon&rsquo;s opening dates, opening times and prices, so online booking is not open yet. Email <a '
                  'href="mailto:{email}">{email}</a> and we will tell you when it is.',
            'cy': 'Rydym yn dal i gadarnhau dyddiadau agor, oriau agor a phrisiau&rsquo;r salon, felly nid yw archebu ar-lein ar agor eto. E-bostiwch <a '
                  'href="mailto:{email}">{email}</a> ac fe rown wybod i chi pan fydd.'},
 'home_h1': {'en': 'Hair by our learners, checked by an educator.', 'cy': 'Gwallt gan ein dysgwyr, wedi&rsquo;i wirio gan addysgwr.'},
 'home_lede': {'en': 'The training salon is where Clwydian Academy learners work on real clients in St Asaph. You choose a Level 2 or a Level 3 learner, you are told '
                     'the real length of the appointment, and an educator checks the work before you leave.',
               'cy': 'Y salon hyfforddi yw lle mae dysgwyr Clwydian Academy yn gweithio ar gleientiaid go iawn yn Llanelwy. Rydych yn dewis dysgwr Lefel 2 neu Lefel 3, '
                     'cewch wybod gwir hyd yr apwyntiad, ac mae addysgwr yn gwirio&rsquo;r gwaith cyn i chi adael.'},
 'how_h': {'en': 'How it works', 'cy': 'Sut mae&rsquo;n gweithio'},
 'how': {'en': [('Choose a service and a level',
                 'Core services are offered by Level 2 and Level 3 learners. Creative cutting, creative colour, colour correction and occasion hair are Level 3 only.'),
                ('Allow the time',
                 'A learner takes longer than a qualified stylist &mdash; that is the point of a training salon. We tell you the real length of your appointment before '
                 'you book, not the length a salon would quote.'),
                ('An educator checks the work', 'Every appointment starts with a consultation with the educator and ends with the educator checking the work.'),
                ('Colour needs an allergy alert test first',
                 'For colour and lightening you need a free allergy alert test (patch test) with us at least {patch_hours} hours before your appointment. It is valid '
                 'for {patch_months} months, for the same product.')],
         'cy': [('Dewiswch wasanaeth a lefel',
                 'Cynigir gwasanaethau craidd gan ddysgwyr Lefel 2 a Lefel 3. Lefel 3 yn unig yw torri creadigol, lliwio creadigol, cywiro lliw a gwallt achlysur.'),
                ('Caniatewch yr amser',
                 'Mae dysgwr yn cymryd mwy o amser na steilydd cymwysedig &mdash; dyna bwrpas salon hyfforddi. Rydym yn dweud wrthych wir hyd eich apwyntiad cyn i chi '
                 'archebu, nid yr hyd y byddai salon yn ei ddyfynnu.'),
                ('Mae addysgwr yn gwirio&rsquo;r gwaith',
                 'Mae pob apwyntiad yn dechrau gydag ymgynghoriad gyda&rsquo;r addysgwr ac yn gorffen gyda&rsquo;r addysgwr yn gwirio&rsquo;r gwaith.'),
                ('Mae angen prawf rhybudd alergedd cyn lliwio',
                 'Ar gyfer lliwio a goleuo mae angen prawf rhybudd alergedd (prawf patsh) am ddim gyda ni o leiaf {patch_hours} awr cyn eich apwyntiad. Mae&rsquo;n '
                 'ddilys am {patch_months} mis, ar gyfer yr un cynnyrch.')]},
 'open_h': {'en': 'When the salon is open', 'cy': 'Pryd mae&rsquo;r salon ar agor'},
 'open_p': {'en': 'The salon opens in term time only.', 'cy': 'Mae&rsquo;r salon ar agor yn ystod y tymor yn unig.'},
 'open_days': {'en': 'Salon days', 'cy': 'Diwrnodau salon'},
 'open_terms': {'en': 'Terms', 'cy': 'Tymhorau'},
 'cta_prices': {'en': 'See prices and times', 'cy': 'Gweld prisiau ac amseroedd'},
 'cta_book': {'en': 'Book an appointment', 'cy': 'Archebu apwyntiad'},
 'cta_models': {'en': 'Join the model register', 'cy': 'Ymuno &acirc;&rsquo;r gofrestr modelau'},
 'where_h': {'en': 'Where', 'cy': 'Ble'},
 'where_p': {'en': 'St Asaph, Denbighshire. The address will be published here before the salon opens.',
             'cy': 'Llanelwy, Sir Ddinbych. Cyhoeddir y cyfeiriad yma cyn i&rsquo;r salon agor.'},
 'prices_h1': {'en': 'Prices and how long to allow', 'cy': 'Prisiau a faint o amser i&rsquo;w ganiat&aacute;u'},
 'prices_lede': {'en': 'Level 3 learners charge our stylist price; Level 2 learners charge less. The times are the real length of the appointment with that learner, '
                       'including time with the educator.',
                 'cy': 'Mae dysgwyr Lefel 3 yn codi ein pris steilydd; mae dysgwyr Lefel 2 yn codi llai. Yr amseroedd yw gwir hyd yr apwyntiad gyda&rsquo;r dysgwr '
                       'hwnnw, gan gynnwys amser gyda&rsquo;r addysgwr.'},
 'draft_h': {'en': 'Draft', 'cy': 'Drafft'},
 'draft_p': {'en': 'The times, deposits and concession shown here are a draft and have not been confirmed. They may change before the salon opens.',
             'cy': 'Drafft yw&rsquo;r amseroedd, y blaendaliadau a&rsquo;r consesiwn a ddangosir yma ac nid ydynt wedi&rsquo;u cadarnhau. Gallant newid cyn i&rsquo;r '
                   'salon agor.'},
 'from': {'en': 'from', 'cy': 'o'},
 'time_tbc': {'en': 'time to be confirmed', 'cy': 'amser i&rsquo;w gadarnhau'},
 'consult_note': {'en': 'Free consultation first', 'cy': 'Ymgynghoriad am ddim yn gyntaf'},
 'hair_h': {'en': 'What your hair adds', 'cy': 'Beth mae eich gwallt yn ei ychwanegu'},
 'conc_h': {'en': 'Concession', 'cy': 'Consesiwn'},
 'conc_p': {'en': '{percent}% off cutting and styling &mdash; not colour &mdash; on {days}, for: {who}. Tell us when you book, and bring proof on the day.',
            'cy': '{percent}% oddi ar dorri a steilio &mdash; nid lliwio &mdash; ar {days}, ar gyfer: {who}. Dywedwch wrthym wrth archebu, a dewch &acirc; phrawf ar y '
                  'diwrnod.'},
 'test_h': {'en': 'Before colour', 'cy': 'Cyn lliwio'},
 'test_p': {'en': 'A free allergy alert test in the salon at least {patch_hours} hours before any colour. A free consultation before balayage, creative colour and '
                  'colour correction.',
            'cy': 'Prawf rhybudd alergedd am ddim yn y salon o leiaf {patch_hours} awr cyn unrhyw liwio. Ymgynghoriad am ddim cyn balayage, lliwio creadigol a chywiro '
                  'lliw.'},
 'service': {'en': 'Service', 'cy': 'Gwasanaeth'},
 'not_offered': {'en': 'Not offered at this level', 'cy': 'Heb ei gynnig ar y lefel hon'},
 'patch_note': {'en': 'Allergy alert test needed', 'cy': 'Angen prawf rhybudd alergedd'},
 'deposit_h': {'en': 'Deposit', 'cy': 'Blaendal'},
 'deposit_p': {'en': 'A deposit is paid by card when you book: {cutting} for cutting and styling, {colour} for colour and technical services (never more than the '
                     'price). It comes off your bill on the day. It is kept if you cancel with less than {cancel} hours&rsquo; notice or do not arrive.',
               'cy': 'Telir blaendal &acirc; cherdyn wrth archebu: {cutting} ar gyfer torri a steilio, {colour} ar gyfer lliwio a gwasanaethau technegol (byth yn fwy '
                     'na&rsquo;r pris). Mae&rsquo;n dod oddi ar eich bil ar y diwrnod. Fe&rsquo;i cedwir os byddwch yn canslo gyda llai na {cancel} awr o rybudd neu os '
                     'na fyddwch yn cyrraedd.'},
 'deposit_tbc': {'en': 'A deposit is paid by card when you book and comes off your bill on the day. The amount is to be confirmed.',
                 'cy': 'Telir blaendal &acirc; cherdyn wrth archebu, ac mae&rsquo;n dod oddi ar eich bil ar y diwrnod. Mae&rsquo;r swm i&rsquo;w gadarnhau.'},
 'models_h1': {'en': 'Be a model for our learners', 'cy': 'Byddwch yn fodel i&rsquo;n dysgwyr'},
 'models_lede': {'en': 'Learners need people to practise on and to be assessed on. Join the register and we will email you when a learner needs a model.',
                 'cy': 'Mae angen pobl ar ddysgwyr i ymarfer arnynt ac i gael eu hasesu arnynt. Ymunwch &acirc;&rsquo;r gofrestr ac fe anfonwn e-bost atoch pan fydd '
                       'angen model ar ddysgwr.'},
 'models_what': {'en': 'For an assessment, a cut or blow-dry is free. For colour you pay the cost of the product only, {lo} to {hi}. A {deposit} deposit holds your '
                       'place and is refunded when you attend. Joining the register commits you to nothing.',
                 'cy': 'Ar gyfer asesiad, mae toriad neu chwythsychu am ddim. Ar gyfer lliwio rydych yn talu cost y cynnyrch yn unig, {lo} i {hi}. Mae blaendal o '
                       '{deposit} yn cadw eich lle ac yn cael ei ad-dalu pan fyddwch yn mynychu. Nid yw ymuno &acirc;&rsquo;r gofrestr yn eich ymrwymo i ddim.'},
 'models_tbc': {'en': 'What a model session costs will be published here before the register is used. Joining commits you to nothing.',
                'cy': 'Cyhoeddir yma beth mae sesiwn fodel yn ei gostio cyn i&rsquo;r gofrestr gael ei defnyddio. Nid yw ymuno yn eich ymrwymo i ddim.'},
 'terms_h1': {'en': 'Booking terms', 'cy': 'Telerau archebu'},
 'terms_draft': {'en': 'Draft. These terms have not been approved yet and no booking can be made under them.',
                 'cy': 'Drafft. Nid yw&rsquo;r telerau hyn wedi&rsquo;u cymeradwyo eto ac ni ellir gwneud archeb oddi tanynt.'},
 'terms_sections': {'en': [('Who you are booking with', 'The training salon is run by Clwydian Academy CBC. Services are carried out by learners under supervision.'),
                           ('Time', 'Learners take longer than a qualified stylist. The length shown when you book is the time to allow.'),
                           ('Prices', 'The price you are shown when you book is the price you pay. Prices include VAT where it applies.'),
                           ('Deposit', '{deposit}'),
                           ('Changing or cancelling',
                            'Email {email} at least {cancel} hours before your appointment and we will move it or refund your deposit. With less notice, or if you do '
                            'not arrive, the deposit is kept.'),
                           ('If we have to move or cancel',
                            'This is a training salon: a learner&rsquo;s availability, or what a learner needs for an assessment, may mean we have to move your '
                            'appointment. If we do, we will offer another time or refund your deposit in full.'),
                           ('Allergy alert tests and consultations',
                            'Colour and lightening services need an allergy alert test (patch test) with us at least {patch_hours} hours before the appointment and no '
                            'more than {patch_months} months before it, for the same product. Without one, the service cannot go ahead. Balayage and colour correction '
                            'need a consultation first. Both are free.'),
                           ('Adults only', 'Every client must be {age} or over. We may ask for proof of age. We do not take bookings for anyone under {age}.'),
                           ('Your information',
                            'We keep your name and contact details to manage your booking. Consultation and allergy answers are health information: we keep them only '
                            'with your consent, encrypted, and only supervising staff can read them. See our <a href="{privacy}">privacy notice</a>.')],
                    'cy': [('Gyda phwy rydych yn archebu',
                            'Mae&rsquo;r salon hyfforddi yn cael ei redeg gan Clwydian Academy CBC. Cyflawnir gwasanaethau gan ddysgwyr dan oruchwyliaeth.'),
                           ('Amser',
                            'Mae dysgwyr yn cymryd mwy o amser na steilydd cymwysedig. Yr hyd a ddangosir wrth archebu yw&rsquo;r amser i&rsquo;w ganiat&aacute;u.'),
                           ('Prisiau',
                            'Y pris a ddangosir i chi wrth archebu yw&rsquo;r pris a dalwch. Mae&rsquo;r prisiau&rsquo;n cynnwys TAW lle mae&rsquo;n berthnasol.'),
                           ('Blaendal', '{deposit}'),
                           ('Newid neu ganslo',
                            'E-bostiwch {email} o leiaf {cancel} awr cyn eich apwyntiad ac fe symudwn ef neu ad-dalu eich blaendal. Gyda llai o rybudd, neu os na '
                            'fyddwch yn cyrraedd, cedwir y blaendal.'),
                           ('Os oes rhaid i ni symud neu ganslo',
                            'Salon hyfforddi yw hwn: gall argaeledd dysgwr, neu&rsquo;r hyn sydd ei angen ar ddysgwr ar gyfer asesiad, olygu bod rhaid i ni symud eich '
                            'apwyntiad. Os gwnawn, byddwn yn cynnig amser arall neu&rsquo;n ad-dalu eich blaendal yn llawn.'),
                           ('Profion rhybudd alergedd ac ymgynghoriadau',
                            'Mae angen prawf rhybudd alergedd (prawf patsh) gyda ni ar gyfer gwasanaethau lliwio a goleuo, o leiaf {patch_hours} awr cyn yr apwyntiad a '
                            'dim mwy na {patch_months} mis cyn hynny, ar gyfer yr un cynnyrch. Hebddo, ni all y gwasanaeth fynd rhagddo. Mae angen ymgynghoriad yn '
                            'gyntaf ar gyfer balayage a chywiro lliw. Mae&rsquo;r ddau am ddim.'),
                           ('Oedolion yn unig',
                            'Rhaid i bob cleient fod yn {age} oed neu h&#375;n. Gallwn ofyn am brawf oedran. Nid ydym yn derbyn archebion ar gyfer unrhyw un o dan {age} '
                            'oed.'),
                           ('Eich gwybodaeth',
                            'Rydym yn cadw eich enw a&rsquo;ch manylion cyswllt i reoli eich archeb. Gwybodaeth iechyd yw atebion ymgynghori ac alergedd: dim ond '
                            'gyda&rsquo;ch caniat&acirc;d y cadwn hwy, wedi&rsquo;u hamgryptio, a dim ond staff goruchwylio all eu darllen. Gweler ein <a '
                            'href="{privacy}">hysbysiad preifatrwydd</a>.')]},
 'adults_h': {'en': 'Adults only', 'cy': 'Oedolion yn unig'},
 'adults_p': {'en': 'The training salon is for adults: every client must be {age} or over.',
              'cy': 'Mae&rsquo;r salon hyfforddi ar gyfer oedolion: rhaid i bob cleient fod yn {age} oed neu h&#375;n.'},
 'hair_p': {'en': 'Prices are for short, fine, natural hair. Longer, thicker or previously coloured hair can add to the price. You are shown the exact price and the '
                  'length of the appointment before you pay anything.',
            'cy': 'Mae&rsquo;r prisiau ar gyfer gwallt byr, main, naturiol. Gall gwallt hirach, mwy trwchus neu wallt sydd wedi&rsquo;i liwio o&rsquo;r blaen ychwanegu '
                  'at y pris. Dangosir yr union bris a hyd yr apwyntiad i chi cyn i chi dalu dim.'},
 'models_join': {'en': 'To join the model register, email <a href="mailto:{email}">{email}</a> with your name and what you would like done.',
                 'cy': 'I ymuno &acirc;&rsquo;r gofrestr modelau, e-bostiwch <a href="mailto:{email}">{email}</a> gyda&rsquo;ch enw a&rsquo;r hyn yr hoffech ei gael.'}}
DAYS = {"en": {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday", "fri": "Friday", "sat": "Saturday", "sun": "Sunday"},
        "cy": {"mon": "Dydd Llun", "tue": "Dydd Mawrth", "wed": "Dydd Mercher", "thu": "Dydd Iau", "fri": "Dydd Gwener", "sat": "Dydd Sadwrn", "sun": "Dydd Sul"}}
MONTHS = {"en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
          "cy": ["Ionawr", "Chwefror", "Mawrth", "Ebrill", "Mai", "Mehefin", "Gorffennaf", "Awst", "Medi", "Hydref", "Tachwedd", "Rhagfyr"]}

# ------------------------------------------------------------------------------------------------
def t(key, loc, **kw):
    s = T[key][loc]
    if not isinstance(s, str):
        # Two entries in T once shared the key "terms"; Python kept the second (a list) and the
        # sub-navigation printed it. A label must be a string — stop the build if it is not.
        raise SystemExit(f"build: salon.py: T[{key!r}][{loc!r}] is not a string — is the key defined twice?")
    for k, v in kw.items():
        s = s.replace("{" + k + "}", str(v))
    return s

def esc(s):
    return html.escape(str(s), quote=True)

def duration(minutes, loc):
    h, m = divmod(int(minutes), 60)
    hw, mw = ("awr", "mun") if loc == "cy" else ("h", "min")
    if not h: return f"{m} {mw}"
    return f"{h} {hw}" if not m else f"{h} {hw} {m} {mw}"

def round_up5(n):
    return int(-(-(n - 1e-9) // 5) * 5)

def long_date(iso, loc):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {MONTHS[loc][m - 1]} {y}"

def crumbs(loc, *trail):
    """trail: (label, href or None) — the last has no link."""
    items = [f'<li><a href="{HOME[loc]}">{t("home", loc)}</a></li>']
    for label, href in trail:
        items.append(f'<li><a href="{href}">{label}</a></li>' if href else f'<li aria-current="page">{label}</li>')
    label = "Breadcrumb" if loc == "en" else "Briwsion bara"
    return f'<nav class="crumbs" aria-label="{label}"><ol>{"".join(items)}</ol></nav>'

def hero(loc, trail, h1, lede):
    return f'''<section class="page-hero salon-hero">
  <div class="wrap">
    {crumbs(loc, *trail)}
    <p class="eyebrow mt-2">{t("eyebrow", loc)}</p>
    <h1>{h1}</h1>
    <p class="lede">{lede}</p>
  </div>
</section>
'''

def soon(loc, site):
    return f'''<div class="salon-notice" role="note">
      <h2>{t("soon_h", loc)}</h2>
      <p>{t("soon_p", loc, email=site["email"])}</p>
    </div>'''


def is_public(policy=None):
    """The switch. False means: build nothing of the salon, anywhere."""
    return (policy if policy is not None else raw()).get("public") is True

def money(n):
    return "&pound;" + (str(int(n)) if float(n) == int(n) else f"{n:.2f}")

def round_half_up(x):
    return int(x + 0.5)

def l3_price(s):
    return val(s["stylist_price"])

def l2_price(policy, s):
    """Level 2 = the stylist price less the category's percentage, to the nearest whole pound."""
    pct = policy["pricing"]["l2_percent_off"][s["category"]]
    return round_half_up(val(s["stylist_price"]) * (100 - pct) / 100)

def minutes_for(policy, s, level):
    """base minutes x the level's factor for the category, rounded up to five, plus educator time."""
    factor = val(policy["levels"][level]["factors"])[s["category"]]
    return round_up5(val(s["base_minutes"]) * factor) + val(policy["educator"]["minutes"])

def draft_notice(loc):
    """Shown wherever a draft figure is printed, for as long as the policy holds any draft."""
    if not draft_paths(raw()):
        return ""
    return f"""<div class="salon-notice salon-draft" role="note">
      <h2>{t("draft_h", loc)}</h2>
      <p>{t("draft_p", loc)}</p>
    </div>"""

def deposit_text(p, loc):
    d = p["deposit"]
    if not (printable(d["cutting"]) and printable(d["colour"])):
        return t("deposit_tbc", loc)
    return t("deposit_p", loc, cutting=money(val(d["cutting"])), colour=money(val(d["colour"])), cancel=p["cancel_window_hours"])

def book_link(loc, cls="btn btn-salon"):
    return f'<a class="{cls}" href="{raw()["booking_url"]}">{t("cta_book", loc)}</a>'

def subnav(loc, current):
    links = []
    for key in ("home", "prices", "models", "terms"):
        label = t("salon" if key == "home" else key, loc)
        cur = ' aria-current="page"' if key == current else ""
        links.append(f'<a href="{PATHS[key][loc]}"{cur}>{label}</a>')
    links.append(f'<a href="{raw()["booking_url"]}">{t("book", loc)}</a>')
    return f'<nav class="salon-subnav" aria-label="{t("salon", loc)}"><div class="wrap">{"".join(links)}</div></nav>\n'

# ------------------------------------------------------------------------------------------------
def home_body(loc, site):
    p = raw()
    how = "".join(f'<li class="step"><h3>{h}</h3><p>{body.replace("{patch_hours}", str(p["patch_test"]["min_hours"])).replace("{patch_months}", str(p["patch_test"]["max_months"]))}</p></li>'
                  for h, body in T["how"][loc])
    op = p["opening"]
    if not printable(op["sessions"]) or not printable(op["terms"]):
        opening = f'<p><strong>{t("tbc", loc)}.</strong></p>'
    else:
        days = "".join(f'<div class="meta-row"><dt>{DAYS[loc][d]}</dt><dd>{", ".join(x["open"] + "&ndash;" + x["close"] for x in ss)}</dd></div>'
                       for d, ss in val(op["sessions"]).items() if ss)
        terms = "".join(f'<div class="meta-row"><dt>{long_date(x["from"], loc)}</dt><dd>&ndash; {long_date(x["to"], loc)}</dd></div>' for x in val(op["terms"]))
        opening = f'<div class="meta-panel"><h3>{t("open_days", loc)}</h3><dl>{days}</dl><h3 class="mt-2">{t("open_terms", loc)}</h3><dl>{terms}</dl></div>'
    notice = "" if confirmed(p) else soon(loc, site)
    return subnav(loc, "home") + hero(loc, [(t("salon", loc), None)], t("home_h1", loc), t("home_lede", loc)) + f"""
<section class="section section--tight" style="padding-top:0">
  <div class="wrap">
    {notice}
    <div class="split" style="align-items:start">
      <div>
        <h2 class="salon-h2">{t("how_h", loc)}</h2>
        <ol class="steps mt-2">{how}</ol>
      </div>
      <div>
        <h2 class="salon-h2">{t("open_h", loc)}</h2>
        <p class="mt-1">{t("open_p", loc)}</p>
        <div class="mt-2">{opening}</div>
        <h2 class="salon-h2 mt-3">{t("where_h", loc)}</h2>
        <p class="mt-1">{t("where_p", loc)}</p>
        <p class="mt-1">{t("adults_p", loc, age=p["adults_only"]["minimum_age"])}</p>
        <p class="hero-actions mt-3">
          {book_link(loc)}
          <a class="btn btn-outline" href="{PATHS["prices"][loc]}">{t("cta_prices", loc)}</a>
          <a class="btn btn-outline" href="{PATHS["models"][loc]}">{t("cta_models", loc)}</a>
        </p>
      </div>
    </div>
  </div>
</section>
"""

def prices_body(loc, site):
    p = raw()
    lv = ("l2", "l3")
    head = "".join(f'<th scope="col">{esc(p["levels"][l]["name"][loc])}</th>' for l in lv)
    na = f'<td class="salon-na"><span class="sr-only">{t("not_offered", loc)}</span><span aria-hidden="true">&mdash;</span></td>'
    def time(s, l):
        ok = printable(s["base_minutes"]) and printable(p["levels"][l]["factors"]) and printable(p["educator"]["minutes"])
        return f'<small>{duration(minutes_for(p, s, l), loc) if ok else t("time_tbc", loc)}</small>'
    sections = []
    for gid, gname in p["groups"].items():
        rows = []
        for s in p["services"]:
            if s["group"] != gid:
                continue
            notes = []
            if s.get("consultation_first"): notes.append(t("consult_note", loc))
            if s.get("patch_test"): notes.append(t("patch_note", loc))
            note = f'<small>{" &middot; ".join(notes)}</small>' if notes else ""
            priced = printable(s["stylist_price"])
            frm = t("from", loc) + " " if s.get("price_from") else ""
            # Level 2: not offered for a Level 3 service; "to be confirmed" where the price or its rule is undecided
            if s.get("l3_only"):
                c2 = na
            elif not priced or s.get("l2_rule_confirmed") is False:
                c2 = f'<td><b>{t("tbc", loc)}</b></td>'
            else:
                c2 = f'<td><b>{money(l2_price(p, s))}</b>{time(s, "l2")}</td>'
            c3 = f'<td><b>{frm}{money(l3_price(s))}</b>{time(s, "l3")}</td>' if priced else f'<td><b>{t("tbc", loc)}</b></td>'
            rows.append(f'<tr><th scope="row">{esc(s["name"][loc])}{note}</th>{c2}{c3}</tr>')
        if rows:
            sections.append(f"""<h2 class="salon-h2 mt-3">{esc(gname[loc])}</h2>
    <div class="salon-table-wrap" tabindex="0" role="region" aria-label="{esc(gname[loc])}">
    <table class="salon-prices">
      <thead><tr><th scope="col">{t("service", loc)}</th>{head}</tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
    </div>""")
    c = p["concession"]
    if printable(c["percent"]) and printable(c["days"]) and printable(c["who"]):
        conc = t("conc_p", loc, percent=val(c["percent"]), days=", ".join(DAYS[loc][d] for d in val(c["days"])), who=", ".join(val(c["who"])[loc]))
    else:
        conc = t("tbc", loc) + "."
    notice = "" if confirmed(p) else soon(loc, site)
    return subnav(loc, "prices") + hero(loc, [(t("salon", loc), PATHS["home"][loc]), (t("prices", loc), None)], t("prices_h1", loc), t("prices_lede", loc)) + f"""
<section class="section section--tight" style="padding-top:0">
  <div class="wrap">
    {notice}
    {draft_notice(loc)}
    {"".join(sections)}
    <h2 class="salon-h2 mt-3">{t("hair_h", loc)}</h2>
    <p class="mt-1 measure">{t("hair_p", loc)}</p>
    <h2 class="salon-h2 mt-3">{t("conc_h", loc)}</h2>
    <p class="mt-1 measure">{conc}</p>
    <h2 class="salon-h2 mt-3">{t("deposit_h", loc)}</h2>
    <p class="mt-1 measure">{deposit_text(p, loc)}</p>
    <h2 class="salon-h2 mt-3">{t("test_h", loc)}</h2>
    <p class="mt-1 measure">{t("test_p", loc, patch_hours=p["patch_test"]["min_hours"])}</p>
    <h2 class="salon-h2 mt-3">{t("adults_h", loc)}</h2>
    <p class="mt-1 measure">{t("adults_p", loc, age=p["adults_only"]["minimum_age"])}</p>
    <p class="hero-actions mt-3">{book_link(loc)}</p>
  </div>
</section>
"""

def models_body(loc, site):
    p = raw()
    m = p["models"]
    what = (t("models_what", loc, lo=money(val(m["colour_product_cost"])[0]), hi=money(val(m["colour_product_cost"])[1]), deposit=money(val(m["refundable_deposit"])))
            if printable(m) else t("models_tbc", loc))
    return subnav(loc, "models") + hero(loc, [(t("salon", loc), PATHS["home"][loc]), (t("models", loc), None)], t("models_h1", loc), t("models_lede", loc)) + f"""
<section class="section section--tight" style="padding-top:0">
  <div class="wrap">
    {draft_notice(loc) if printable(m) else ""}
    <p class="measure">{what}</p>
    <p class="measure mt-1">{t("adults_p", loc, age=p["adults_only"]["minimum_age"])}</p>
    <p class="measure mt-2">{t("models_join", loc, email=site["email"])}</p>
  </div>
</section>
"""

def terms_body(loc, site):
    p = raw()
    fill = {"deposit": deposit_text(p, loc), "email": f'<a href="mailto:{site["email"]}">{site["email"]}</a>', "cancel": p["cancel_window_hours"],
            "patch_hours": p["patch_test"]["min_hours"], "patch_months": p["patch_test"]["max_months"], "privacy": PRIVACY[loc], "age": p["adults_only"]["minimum_age"]}
    parts = []
    for h, body in T["terms_sections"][loc]:
        for k, v in fill.items():
            body = body.replace("{" + k + "}", str(v))
        parts.append(f'<h2 class="salon-h2 mt-3">{h}</h2>\n    <p class="mt-1 measure">{body}</p>')
    draft = f'<div class="salon-notice" role="note"><p><strong>{t("terms_draft", loc)}</strong></p></div>' if not printable(p["terms_approved"]) or not val(p["terms_approved"]) else ""
    return subnav(loc, "terms") + hero(loc, [(t("salon", loc), PATHS["home"][loc]), (t("terms", loc), None)], t("terms_h1", loc), "") + f"""
<section class="section section--tight" style="padding-top:0">
  <div class="wrap">
    {draft}
    {"".join(parts)}
    <p class="hero-actions mt-3">{book_link(loc)}</p>
  </div>
</section>
"""

BODIES = {"salon": home_body, "salon-prices": prices_body, "salon-models": models_body, "salon-terms": terms_body}

def body(kind, loc, site):
    return BODIES[kind](loc, site)

def jsonld(kind, loc, domain, org, site):
    """HairSalon structured data on the salon's front page, tied to the academy's own Organization.

    The tie is `department` on the academy (an Organization names its department), not the other
    way round: the property that points from a department up to its organisation is banned
    site-wide by scripts/check_claims.py, because for the ACADEMY it would assert a parent — see
    CLAUDE.md, "The entity". Town only: no street address until the premises are confirmed, and no
    opening hours until the PM confirms them.
    """
    if kind != "salon":
        return []
    salon_id = domain + "/salon/#salon"
    p = raw()
    salon = {
        "@context": "https://schema.org", "@type": "HairSalon", "@id": salon_id,
        "name": "Clwydian Academy Training Salon" if loc == "en" else "Salon Hyfforddi Clwydian Academy",
        "description": ("Training salon in St Asaph, North Wales: hair services by Clwydian Academy learners, under supervision, in term time."
                        if loc == "en" else "Salon hyfforddi yn Llanelwy, Gogledd Cymru: gwasanaethau gwallt gan ddysgwyr Clwydian Academy, dan oruchwyliaeth, yn ystod y tymor."),
        "url": domain + PATHS["home"][loc],
        "image": org["image"], "email": site["email"], "address": org["address"],
        "knowsLanguage": ["en", "cy"],
    }
    op = p["opening"]
    if printable(op["sessions"]):
        names = {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday", "fri": "Friday", "sat": "Saturday", "sun": "Sunday"}
        salon["openingHoursSpecification"] = [{"@type": "OpeningHoursSpecification", "dayOfWeek": "https://schema.org/" + names[d], "opens": x["open"], "closes": x["close"]}
                                              for d, ss in val(op["sessions"]).items() for x in ss]
    link = {"@context": "https://schema.org", "@type": org["@type"], "@id": org["@id"], "department": {"@id": salon_id}}
    return [salon, link]
