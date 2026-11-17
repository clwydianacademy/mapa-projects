"""The training salon's pages, rendered from _data/salon/policy.json in both languages.

    /salon/  /salon/prices/  /salon/book/  /salon/models/  /salon/terms/   and /cy/salon/...
    /staff/  (English only, noindex — the day sheet; it is an application, not a page of copy)

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
ENGINE_COPY = os.path.join(REPO, "site", "api", "_lib", "salon", "policy.json")

PATHS = {
    "home":   {"en": "/salon/",        "cy": "/cy/salon/"},
    "prices": {"en": "/salon/prices/", "cy": "/cy/salon/prisiau/"},
    "book":   {"en": "/salon/book/",   "cy": "/cy/salon/archebu/"},
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

def copy_for_engine():
    """The engine cannot read _data/ at run time: give it a byte-for-byte copy."""
    with open(DATA_PATH, encoding="utf-8") as f:
        text = f.read()
    os.makedirs(os.path.dirname(ENGINE_COPY), exist_ok=True)
    with open(ENGINE_COPY, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

# ------------------------------------------------------------------------------------------------
# Strings. One dictionary, both languages. The booking journey's script has no words of its own:
# it reads JOURNEY from the page.
# ------------------------------------------------------------------------------------------------
T = {
    "tbc":            {"en": "To be confirmed", "cy": "I&rsquo;w gadarnhau"},
    "home":           {"en": "Home", "cy": "Hafan"},
    "salon":          {"en": "Training salon", "cy": "Salon hyfforddi"},
    "prices":         {"en": "Prices", "cy": "Prisiau"},
    "book":           {"en": "Book", "cy": "Archebu"},
    "models":         {"en": "Be a model", "cy": "Bod yn fodel"},
    "terms":          {"en": "Booking terms", "cy": "Telerau archebu"},
    "eyebrow":        {"en": "Clwydian Academy training salon", "cy": "Salon hyfforddi Clwydian Academy"},
    "soon_h":         {"en": "Opening soon", "cy": "Yn agor yn fuan"},
    "soon_p":         {"en": "We are still confirming the salon&rsquo;s opening dates, opening times and prices, so online booking is not open yet. Email <a href=\"mailto:{email}\">{email}</a> and we will tell you when it is.",
                       "cy": "Rydym yn dal i gadarnhau dyddiadau agor, oriau agor a phrisiau&rsquo;r salon, felly nid yw archebu ar-lein ar agor eto. E-bostiwch <a href=\"mailto:{email}\">{email}</a> ac fe rown wybod i chi pan fydd."},
    "home_h1":        {"en": "Hair by our learners, checked by a supervisor.", "cy": "Gwallt gan ein dysgwyr, wedi&rsquo;i wirio gan oruchwyliwr."},
    "home_lede":      {"en": "The training salon is where Clwydian Academy learners work on real clients in St Asaph. You pay a learner price, you choose how experienced your learner is, and a supervisor checks the work before you leave.",
                       "cy": "Y salon hyfforddi yw lle mae dysgwyr Clwydian Academy yn gweithio ar gleientiaid go iawn yn Llanelwy. Rydych yn talu pris dysgwr, yn dewis pa mor brofiadol yw eich dysgwr, ac mae goruchwyliwr yn gwirio&rsquo;r gwaith cyn i chi adael."},
    "how_h":          {"en": "How it works", "cy": "Sut mae&rsquo;n gweithio"},
    "how": {
        "en": [("Choose a service and a level", "Each service is offered by learners at different stages of their training. The earlier the stage, the lower the price."),
               ("Allow the time", "A learner takes longer than a qualified stylist &mdash; that is the point of a training salon. We tell you the real length of your appointment before you book, not the length a salon would quote."),
               ("An educator checks the work", "Every appointment starts with a consultation with the educator and ends with the educator checking the work."),
               ("Colour needs an allergy alert test first", "For colour and lightening you need a free allergy alert test (patch test) with us at least {patch_hours} hours before your appointment. It is valid for {patch_months} months, for the same product.")],
        "cy": [("Dewiswch wasanaeth a lefel", "Cynigir pob gwasanaeth gan ddysgwyr ar wahanol gamau o&rsquo;u hyfforddiant. Po gynharaf y cam, yr isaf yw&rsquo;r pris."),
               ("Caniatewch yr amser", "Mae dysgwr yn cymryd mwy o amser na steilydd cymwysedig &mdash; dyna bwrpas salon hyfforddi. Rydym yn dweud wrthych wir hyd eich apwyntiad cyn i chi archebu, nid yr hyd y byddai salon yn ei ddyfynnu."),
               ("Mae addysgwr yn gwirio&rsquo;r gwaith", "Mae pob apwyntiad yn dechrau gydag ymgynghoriad gyda&rsquo;r addysgwr ac yn gorffen gyda&rsquo;r addysgwr yn gwirio&rsquo;r gwaith."),
               ("Mae angen prawf rhybudd alergedd cyn lliwio", "Ar gyfer lliwio a goleuo mae angen prawf rhybudd alergedd (prawf patsh) am ddim gyda ni o leiaf {patch_hours} awr cyn eich apwyntiad. Mae&rsquo;n ddilys am {patch_months} mis, ar gyfer yr un cynnyrch.")],
    },
    "open_h":         {"en": "When the salon is open", "cy": "Pryd mae&rsquo;r salon ar agor"},
    "open_p":         {"en": "The salon opens in term time only.", "cy": "Mae&rsquo;r salon ar agor yn ystod y tymor yn unig."},
    "open_days":      {"en": "Salon days", "cy": "Diwrnodau salon"},
    "open_terms":     {"en": "Terms", "cy": "Tymhorau"},
    "cta_prices":     {"en": "See prices and times", "cy": "Gweld prisiau ac amseroedd"},
    "cta_book":       {"en": "Book an appointment", "cy": "Archebu apwyntiad"},
    "cta_models":     {"en": "Join the model register", "cy": "Ymuno &acirc;&rsquo;r gofrestr modelau"},
    "where_h":        {"en": "Where", "cy": "Ble"},
    "where_p":        {"en": "St Asaph, Denbighshire. The address will be published here before the salon opens.", "cy": "Llanelwy, Sir Ddinbych. Cyhoeddir y cyfeiriad yma cyn i&rsquo;r salon agor."},
    "prices_h1":      {"en": "Prices and how long to allow", "cy": "Prisiau a faint o amser i&rsquo;w ganiat&aacute;u"},
    "prices_lede":    {"en": "&ldquo;From&rdquo; prices for each stage of training. The times are the real length of the appointment with that learner, including fifteen minutes with the educator.",
                       "cy": "Prisiau &ldquo;o&rdquo; ar gyfer pob cam o&rsquo;r hyfforddiant. Yr amseroedd yw gwir hyd yr apwyntiad gyda&rsquo;r dysgwr hwnnw, gan gynnwys pymtheg munud gyda&rsquo;r addysgwr."},
    "draft_h":        {"en": "Draft prices", "cy": "Prisiau drafft"},
    "draft_p":        {"en": "These prices and times are a draft and have not been confirmed. They may change before the salon opens.",
                       "cy": "Drafft yw&rsquo;r prisiau a&rsquo;r amseroedd hyn ac nid ydynt wedi&rsquo;u cadarnhau. Gallant newid cyn i&rsquo;r salon agor."},
    "from":           {"en": "from", "cy": "o"},
    "time_tbc":       {"en": "time to be confirmed", "cy": "amser i&rsquo;w gadarnhau"},
    "consult_note":   {"en": "Free consultation first", "cy": "Ymgynghoriad am ddim yn gyntaf"},
    "finish_note":    {"en": "Includes a basic blow-dry finish", "cy": "Yn cynnwys gorffeniad chwythsychu sylfaenol"},
    "extras_h":       {"en": "Extras", "cy": "Ychwanegion"},
    "extra":          {"en": "Extra", "cy": "Ychwanegiad"},
    "hair_h":         {"en": "What your hair adds", "cy": "Beth mae eich gwallt yn ei ychwanegu"},
    "hair_colour_p":  {"en": "Colour prices start from short, fine, natural hair. Longer, thicker or previously coloured hair adds to the price, and we tell you the exact figure before you book.",
                       "cy": "Mae prisiau lliwio&rsquo;n dechrau o wallt byr, main, naturiol. Mae gwallt hirach, mwy trwchus neu wallt sydd wedi&rsquo;i liwio o&rsquo;r blaen yn ychwanegu at y pris, a dywedwn y ffigur union wrthych cyn i chi archebu."},
    "hair_l3_p":      {"en": "Hair with box dye or bleach on it, and going three shades or more lighter, is Level 3 work and is not offered with a Level 2 learner.",
                       "cy": "Gwaith Lefel 3 yw gwallt &acirc; lliw o focs neu gannydd arno, a mynd dri arlliw neu fwy yn oleuach, ac ni chaiff ei gynnig gyda dysgwr Lefel 2."},
    "answer":         {"en": "Your hair", "cy": "Eich gwallt"},
    "not_at":         {"en": "Not at this level", "cy": "Ddim ar y lefel hon"},
    "conc_h":         {"en": "Concession", "cy": "Consesiwn"},
    "conc_p":         {"en": "{percent}% off cutting and styling &mdash; not colour &mdash; on {days}, for: {who}. Tell us when you book, and bring proof on the day.",
                       "cy": "{percent}% oddi ar dorri a steilio &mdash; nid lliwio &mdash; ar {days}, ar gyfer: {who}. Dywedwch wrthym wrth archebu, a dewch &acirc; phrawf ar y diwrnod."},
    "u16_h":          {"en": "Under 16", "cy": "O dan 16 oed"},
    "u16_p":          {"en": "Children under 12: the children&rsquo;s cut. Ages 12 to 15: gents and children&rsquo;s cuts, at those prices. A parent or guardian must be present. No permanent or quasi-permanent colour, bleach or relaxer under 16.",
                       "cy": "Plant o dan 12 oed: y toriad plant. 12 i 15 oed: toriadau dynion a phlant, am y prisiau hynny. Rhaid i riant neu warcheidwad fod yn bresennol. Dim lliw parhaol na chwasi-barhaol, cannydd nac ymlaciwr o dan 16 oed."},
    "test_h":         {"en": "Before colour", "cy": "Cyn lliwio"},
    "test_p":         {"en": "A free allergy alert test at least {patch_hours} hours before any colour. A free consultation before balayage and colour correction.",
                       "cy": "Prawf rhybudd alergedd am ddim o leiaf {patch_hours} awr cyn unrhyw liwio. Ymgynghoriad am ddim cyn balayage a chywiro lliw."},
    "service":        {"en": "Service", "cy": "Gwasanaeth"},
    "not_offered":    {"en": "Not offered at this level", "cy": "Heb ei gynnig ar y lefel hon"},
    "free":           {"en": "Free", "cy": "Am ddim"},
    "patch_note":     {"en": "Allergy alert test needed", "cy": "Angen prawf rhybudd alergedd"},
    "u16_note":       {"en": "Not available under 16", "cy": "Ddim ar gael o dan 16 oed"},
    "deposit_h":      {"en": "Deposit", "cy": "Blaendal"},
    "deposit_p":      {"en": "A deposit is paid by card when you book: {cutting} for cutting and styling, {colour} for colour and technical services (never more than the price). It comes off your bill on the day. It is kept if you cancel with less than {cancel} hours&rsquo; notice or do not arrive.",
                       "cy": "Telir blaendal &acirc; cherdyn wrth archebu: {cutting} ar gyfer torri a steilio, {colour} ar gyfer lliwio a gwasanaethau technegol (byth yn fwy na&rsquo;r pris). Mae&rsquo;n dod oddi ar eich bil ar y diwrnod. Fe&rsquo;i cedwir os byddwch yn canslo gyda llai na {cancel} awr o rybudd neu os na fyddwch yn cyrraedd."},
    "deposit_tbc":    {"en": "A deposit is paid by card when you book and comes off your bill on the day. The amount is to be confirmed.",
                       "cy": "Telir blaendal &acirc; cherdyn wrth archebu, ac mae&rsquo;n dod oddi ar eich bil ar y diwrnod. Mae&rsquo;r swm i&rsquo;w gadarnhau."},
    "book_h1":        {"en": "Book an appointment", "cy": "Archebu apwyntiad"},
    "book_lede":      {"en": "One question at a time. You will see the price and the real length of the appointment before you pay anything.",
                       "cy": "Un cwestiwn ar y tro. Fe welwch y pris a gwir hyd yr apwyntiad cyn i chi dalu dim."},
    "nojs":           {"en": "Online booking needs JavaScript. To book without it, email <a href=\"mailto:{email}\">{email}</a>.",
                       "cy": "Mae angen JavaScript ar gyfer archebu ar-lein. I archebu hebddo, e-bostiwch <a href=\"mailto:{email}\">{email}</a>."},
    "models_h1":      {"en": "Be a model for our learners", "cy": "Byddwch yn fodel i&rsquo;n dysgwyr"},
    "models_lede":    {"en": "Learners need people to practise on and to be assessed on. Join the register and we will email you when a learner needs a model for something you are interested in.",
                       "cy": "Mae angen pobl ar ddysgwyr i ymarfer arnynt ac i gael eu hasesu arnynt. Ymunwch &acirc;&rsquo;r gofrestr ac fe anfonwn e-bost atoch pan fydd angen model ar ddysgwr ar gyfer rhywbeth sydd o ddiddordeb i chi."},
    "models_what":    {"en": "For an assessment, a cut or blow-dry is free. For colour you pay the cost of the product only, {lo} to {hi}. A {deposit} deposit holds your place and is refunded when you attend. Joining the register commits you to nothing.",
                       "cy": "Ar gyfer asesiad, mae toriad neu chwythsychu am ddim. Ar gyfer lliwio rydych yn talu cost y cynnyrch yn unig, {lo} i {hi}. Mae blaendal o {deposit} yn cadw eich lle ac yn cael ei ad-dalu pan fyddwch yn mynychu. Nid yw ymuno &acirc;&rsquo;r gofrestr yn eich ymrwymo i ddim."},
    "models_tbc":     {"en": "What a model session costs will be published here before the register is used. Joining commits you to nothing.",
                       "cy": "Cyhoeddir yma beth mae sesiwn fodel yn ei gostio cyn i&rsquo;r gofrestr gael ei defnyddio. Nid yw ymuno yn eich ymrwymo i ddim."},
    "terms_h1":       {"en": "Booking terms", "cy": "Telerau archebu"},
    "terms_draft":    {"en": "Draft. These terms have not been approved yet and no booking can be made under them.", "cy": "Drafft. Nid yw&rsquo;r telerau hyn wedi&rsquo;u cymeradwyo eto ac ni ellir gwneud archeb oddi tanynt."},
    "terms_sections": {
        "en": [
            ("Who you are booking with", "The training salon is run by Clwydian Academy CBC. Services are carried out by learners under supervision."),
            ("Time", "Learners take longer than a qualified stylist. The length shown when you book is the time to allow."),
            ("Prices", "The price you are shown when you book is the price you pay. Prices include VAT where it applies."),
            ("Deposit", "{deposit}"),
            ("Changing or cancelling", "Email {email} at least {cancel} hours before your appointment and we will move it or refund your deposit. With less notice, or if you do not arrive, the deposit is kept."),
            ("If we have to move or cancel", "This is a training salon: a learner&rsquo;s availability, or what a learner needs for an assessment, may mean we have to move your appointment. If we do, we will offer another time or refund your deposit in full."),
            ("Allergy alert tests and consultations", "Colour and lightening services need an allergy alert test (patch test) with us at least {patch_hours} hours before the appointment and no more than {patch_months} months before it, for the same product. Without one, the service cannot go ahead. Balayage and colour correction need a consultation first. Both are free."),
            ("Under 16", "We do not carry out permanent or quasi-permanent colour, bleach or relaxer on anyone under 16. Other services for someone under 16 are limited to those on our price list, and a parent or guardian must consent and be present."),
            ("Your information", "We keep your name and contact details to manage your booking. Consultation and allergy answers are health information: we keep them only with your consent, encrypted, and only supervising staff can read them. See our <a href=\"{privacy}\">privacy notice</a>."),
        ],
        "cy": [
            ("Gyda phwy rydych yn archebu", "Mae&rsquo;r salon hyfforddi yn cael ei redeg gan Clwydian Academy CBC. Cyflawnir gwasanaethau gan ddysgwyr dan oruchwyliaeth."),
            ("Amser", "Mae dysgwyr yn cymryd mwy o amser na steilydd cymwysedig. Yr hyd a ddangosir wrth archebu yw&rsquo;r amser i&rsquo;w ganiat&aacute;u."),
            ("Prisiau", "Y pris a ddangosir i chi wrth archebu yw&rsquo;r pris a dalwch. Mae&rsquo;r prisiau&rsquo;n cynnwys TAW lle mae&rsquo;n berthnasol."),
            ("Blaendal", "{deposit}"),
            ("Newid neu ganslo", "E-bostiwch {email} o leiaf {cancel} awr cyn eich apwyntiad ac fe symudwn ef neu ad-dalu eich blaendal. Gyda llai o rybudd, neu os na fyddwch yn cyrraedd, cedwir y blaendal."),
            ("Os oes rhaid i ni symud neu ganslo", "Salon hyfforddi yw hwn: gall argaeledd dysgwr, neu&rsquo;r hyn sydd ei angen ar ddysgwr ar gyfer asesiad, olygu bod rhaid i ni symud eich apwyntiad. Os gwnawn, byddwn yn cynnig amser arall neu&rsquo;n ad-dalu eich blaendal yn llawn."),
            ("Profion rhybudd alergedd ac ymgynghoriadau", "Mae angen prawf rhybudd alergedd (prawf patsh) gyda ni ar gyfer gwasanaethau lliwio a goleuo, o leiaf {patch_hours} awr cyn yr apwyntiad a dim mwy na {patch_months} mis cyn hynny, ar gyfer yr un cynnyrch. Hebddo, ni all y gwasanaeth fynd rhagddo. Mae angen ymgynghoriad yn gyntaf ar gyfer balayage a chywiro lliw. Mae&rsquo;r ddau am ddim."),
            ("O dan 16 oed", "Nid ydym yn rhoi lliw parhaol na chwasi-barhaol, cannydd nac ymlaciwr ar unrhyw un o dan 16 oed. Mae gwasanaethau eraill i rywun o dan 16 oed wedi&rsquo;u cyfyngu i&rsquo;r rhai ar ein rhestr brisiau, a rhaid i riant neu warcheidwad gydsynio a bod yn bresennol."),
            ("Eich gwybodaeth", "Rydym yn cadw eich enw a&rsquo;ch manylion cyswllt i reoli eich archeb. Gwybodaeth iechyd yw atebion ymgynghori ac alergedd: dim ond gyda&rsquo;ch caniat&acirc;d y cadwn hwy, wedi&rsquo;u hamgryptio, a dim ond staff goruchwylio all eu darllen. Gweler ein <a href=\"{privacy}\">hysbysiad preifatrwydd</a>."),
        ],
    },
}
DAYS = {"en": {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday", "fri": "Friday", "sat": "Saturday", "sun": "Sunday"},
        "cy": {"mon": "Dydd Llun", "tue": "Dydd Mawrth", "wed": "Dydd Mercher", "thu": "Dydd Iau", "fri": "Dydd Gwener", "sat": "Dydd Sadwrn", "sun": "Dydd Sul"}}
MONTHS = {"en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
          "cy": ["Ionawr", "Chwefror", "Mawrth", "Ebrill", "Mai", "Mehefin", "Gorffennaf", "Awst", "Medi", "Hydref", "Tachwedd", "Rhagfyr"]}

# What the booking journey says. Plain text (the script sets textContent), so no entities here.
JOURNEY = {
    "en": {
        "loading": "Loading…", "step": "Step {n} of {of}", "back": "Back", "next": "Continue", "change": "Change",
        "closed_h": "Online booking is not available right now",
        "closed_p": "Please email {email} and we will book you in.",
        "closed_reason": {"not-confirmed": "The salon's opening dates and prices are still being confirmed.", "not-open": "The salon is not taking bookings yet.",
                          "no-store": "Our booking system is not reachable at the moment.", "error": "Something went wrong at our end."},
        "service_h": "What would you like done?", "service_missing": "Please choose a service.",
        "age_h": "How old is the person having this service?", "yes": "Yes", "no": "No", "age_missing": "Please choose one.",
        "age_adult": "16 or over", "age_u16": "12 to 15", "age_u12": "Under 12", "age_guardian": "A parent or guardian must be present.",
        "age_service_h": "We do not offer this service at that age",
        "age_service_u16": "For ages 12 to 15 we offer gents and children's cuts. Please choose one of those.",
        "age_service_u12": "For children under 12 we offer the children's cut. Please choose that.",
        "children_only": "The children's cut is for children under 12. Please choose a different service.",
        "q_missing": "Please choose one.", "q_l3": "Level 3 or above",
        "extras_h": "Would you like to add anything?", "extras_p": "Choose any that you want, or none. The price of an extra depends on your learner's level.",
        "extra_price": "+{price}", "extra_range": "+{lo} to +{hi}", "extra_from_l3": "Level 3 or above",
        "conc_h": "Do any of these apply to you?", "conc_p": "{percent}% off cutting and styling on {days}. Please bring proof on the day.",
        "conc_yes": "Yes, one of these applies to me", "conc_no": "No", "conc_missing": "Please choose yes or no.", "conc_applied": "concession applied", "conc_not_today": "The concession does not apply on this day.",
        "consult_h": "This needs a free consultation first",
        "consult_p": "Before this service an educator needs to see your hair and agree a plan and a price with you. The consultation is free and takes about half an hour. Once it is done you can book the service.",
        "consult_book": "Book a free consultation",
        "who_higher": "From what you have told us about your hair, this needs a more experienced learner, so Level 2 is not offered.",
        "sum_extras": "Extras", "from_price": "from {price}",
        "age_blocked_h": "We cannot offer this service to anyone under 16",
        "age_blocked_p": "Permanent and quasi-permanent colour, bleach and relaxer are not carried out on anyone under 16. Please choose a different service.",
        "choose_other": "Choose a different service",
        "patch_h": "Have you had an allergy alert test (patch test) with us for this in the last {months} months?",
        "patch_p": "This service uses: {product}. You need a free allergy alert test with us at least {hours} hours before your appointment. A test for a different product does not count.",
        "patch_yes": "Yes, I have", "patch_no": "No, not yet", "patch_missing": "Please choose one.",
        "patch_email_h": "Which email address did you book the test with?", "patch_email_missing": "Please enter the email address you used.",
        "patch_none_h": "You need an allergy alert test first",
        "patch_none_p": "It takes about ten minutes and is free. Book it now; once it is done you can book this service for {hours} hours or more afterwards.",
        "patch_book": "Book a free allergy alert test",
        "reaction_h": "Have you ever reacted to hair colour, a patch test, or a hair or skin product?",
        "reaction_p": "For example itching, a rash, swelling or burning. Your answer is health information. We only keep it if you agree, on the last step.",
        "reaction_missing": "Please answer yes or no.",
        "reaction_blocked_h": "We need to talk to you before booking this",
        "reaction_blocked_p": "Because you have had a reaction before, a supervisor needs to speak to you before this service is booked. Please email {email}.",
        "who_h": "Who would you like?",
        "who_p": "Learners at an earlier stage cost less and take longer. Every learner works under supervision.",
        "who_any": "Any learner — first available", "who_any_detail": "From {from}. Time and price depend on the learner; you will see both for each time.",
        "who_detail": "About {time} — {price}", "who_qualified": "A qualified stylist would take about {time}.", "who_missing": "Please choose who you would like.",
        "when_h": "When would you like to come?", "when_p": "Choose a day, then a time.",
        "full": "Full", "few": "A few", "lots": "Lots", "closed": "Closed",
        "next_available": "Next available: {when}", "none_available": "Nothing is available in the next few weeks. Please email {email}.",
        "earlier": "Earlier days", "later": "Later days", "morning": "Morning", "afternoon": "Afternoon",
        "no_morning": "Nothing in the morning.", "no_afternoon": "Nothing in the afternoon.", "day_full": "Nothing left on this day. Please choose another day.",
        "slot_detail": "{start} to {end} — {level} — {price}", "when_missing": "Please choose a day and a time.",
        "details_h": "Your details", "name": "Your name", "email": "Email address", "email_hint": "We send your confirmation here.",
        "phone": "Mobile number (optional)", "phone_hint": "Only used if we need to reach you about this appointment.",
        "guardian_h": "Parent or guardian", "guardian_name": "Parent or guardian's name",
        "guardian_confirm": "I am the parent or guardian of the person having this service, I consent to it, and I will be present.",
        "notes": "Allergies, skin or scalp conditions we should know about (optional)", "notes_hint": "Health information. Kept encrypted, and only read by supervising staff.",
        "consent_health": "I agree to Clwydian Academy keeping my answers about reactions, allergies and skin conditions so that this service can be carried out safely.",
        "consent_terms": "I have read and agree to the booking terms.", "terms_link": "Read the booking terms",
        "missing_name": "Please enter your name.", "missing_email": "Please enter a valid email address.", "missing_guardian": "Please enter the parent or guardian's name and tick the consent box.",
        "missing_health": "Please tick the box to let us keep your health answers, or email us instead.", "missing_terms": "Please tick the box to agree to the booking terms.",
        "review_h": "Check and pay your deposit", "review_h_free": "Check and confirm",
        "sum_service": "Service", "sum_who": "With", "sum_when": "When", "sum_length": "Allow", "sum_price": "Price", "sum_deposit": "Deposit to pay now", "sum_balance": "To pay on the day",
        "supervised": "{level}, supervised",
        "length_honest": "{time}. A qualified stylist would take about {qualified}; a learner takes longer, and an educator checks the work.",
        "length_same": "{time}, including time with the educator.",
        "pay": "Pay {amount} deposit", "confirm": "Confirm booking", "paying": "One moment…",
        "pay_note": "You will go to our card payment page. Your time is held for {minutes} minutes while you pay.",
        "placeholder_banner": "TEST DATA — these prices, times and dates are placeholders that have not been confirmed.",
        "done_h": "You are booked in", "done_p": "Your reference is {ref}. We have emailed your confirmation.",
        "held_h": "We are waiting for your payment to be confirmed", "held_p": "This usually takes a few seconds. Your reference is {ref}. This page will update; you do not need to pay again.",
        "expired_h": "That booking was not completed", "expired_p": "No payment was confirmed and the time has been released. You can start again.",
        "cancelled_h": "Payment was not completed", "cancelled_p": "You have not been charged. Your time is held for a few more minutes — or start again.",
        "start_again": "Start again", "unknown_ref": "We could not find that booking. Please email {email}.",
        "hours": "{h} h", "minutes": "{m} min", "hours_minutes": "{h} h {m} min",
        "error": "Something went wrong at our end. Please try again, or email {email}.",
    },
    "cy": {
        "loading": "Yn llwytho…", "step": "Cam {n} o {of}", "back": "Yn ôl", "next": "Parhau", "change": "Newid",
        "closed_h": "Nid yw archebu ar-lein ar gael ar hyn o bryd",
        "closed_p": "E-bostiwch {email} ac fe wnawn ni eich archebu.",
        "closed_reason": {"not-confirmed": "Mae dyddiadau agor a phrisiau'r salon yn dal i gael eu cadarnhau.", "not-open": "Nid yw'r salon yn derbyn archebion eto.",
                          "no-store": "Nid oes modd cyrraedd ein system archebu ar hyn o bryd.", "error": "Aeth rhywbeth o'i le ar ein hochr ni."},
        "service_h": "Beth hoffech chi ei gael?", "service_missing": "Dewiswch wasanaeth.",
        "age_h": "Faint yw oed y person sy'n cael y gwasanaeth hwn?", "yes": "Ydw", "no": "Nac ydw", "age_missing": "Dewiswch un.",
        "age_adult": "16 oed neu hŷn", "age_u16": "12 i 15 oed", "age_u12": "O dan 12 oed", "age_guardian": "Rhaid i riant neu warcheidwad fod yn bresennol.",
        "age_service_h": "Nid ydym yn cynnig y gwasanaeth hwn ar yr oedran hwnnw",
        "age_service_u16": "Ar gyfer 12 i 15 oed rydym yn cynnig toriadau dynion a phlant. Dewiswch un o'r rheini.",
        "age_service_u12": "Ar gyfer plant o dan 12 oed rydym yn cynnig y toriad plant. Dewiswch hwnnw.",
        "children_only": "Mae'r toriad plant ar gyfer plant o dan 12 oed. Dewiswch wasanaeth gwahanol.",
        "q_missing": "Dewiswch un.", "q_l3": "Lefel 3 neu uwch",
        "extras_h": "Hoffech chi ychwanegu unrhyw beth?", "extras_p": "Dewiswch unrhyw rai yr hoffech, neu ddim un. Mae pris ychwanegiad yn dibynnu ar lefel eich dysgwr.",
        "extra_price": "+{price}", "extra_range": "+{lo} i +{hi}", "extra_from_l3": "Lefel 3 neu uwch",
        "conc_h": "A oes unrhyw un o'r rhain yn berthnasol i chi?", "conc_p": "{percent}% oddi ar dorri a steilio ar {days}. Dewch â phrawf ar y diwrnod.",
        "conc_yes": "Oes, mae un o'r rhain yn berthnasol i mi", "conc_no": "Nac oes", "conc_missing": "Dewiswch oes neu nac oes.", "conc_applied": "consesiwn wedi'i gymhwyso", "conc_not_today": "Nid yw'r consesiwn yn berthnasol ar y diwrnod hwn.",
        "consult_h": "Mae angen ymgynghoriad am ddim yn gyntaf ar gyfer hyn",
        "consult_p": "Cyn y gwasanaeth hwn mae angen i addysgwr weld eich gwallt a chytuno ar gynllun a phris gyda chi. Mae'r ymgynghoriad am ddim ac yn cymryd tua hanner awr. Ar ôl ei wneud gallwch archebu'r gwasanaeth.",
        "consult_book": "Archebu ymgynghoriad am ddim",
        "who_higher": "O'r hyn rydych wedi'i ddweud wrthym am eich gwallt, mae angen dysgwr mwy profiadol ar gyfer hyn, felly ni chynigir Lefel 2.",
        "sum_extras": "Ychwanegion", "from_price": "o {price}",
        "age_blocked_h": "Ni allwn gynnig y gwasanaeth hwn i unrhyw un o dan 16 oed",
        "age_blocked_p": "Ni roddir lliw parhaol na chwasi-barhaol, cannydd nac ymlaciwr ar unrhyw un o dan 16 oed. Dewiswch wasanaeth gwahanol.",
        "choose_other": "Dewis gwasanaeth gwahanol",
        "patch_h": "Ydych chi wedi cael prawf rhybudd alergedd (prawf patsh) gyda ni ar gyfer hyn yn ystod y {months} mis diwethaf?",
        "patch_p": "Mae'r gwasanaeth hwn yn defnyddio: {product}. Mae angen prawf rhybudd alergedd am ddim gyda ni o leiaf {hours} awr cyn eich apwyntiad. Nid yw prawf ar gyfer cynnyrch gwahanol yn cyfrif.",
        "patch_yes": "Ydw", "patch_no": "Nac ydw, ddim eto", "patch_missing": "Dewiswch un.",
        "patch_email_h": "Pa gyfeiriad e-bost a ddefnyddioch i archebu'r prawf?", "patch_email_missing": "Rhowch y cyfeiriad e-bost a ddefnyddioch.",
        "patch_none_h": "Mae angen prawf rhybudd alergedd arnoch yn gyntaf",
        "patch_none_p": "Mae'n cymryd tua deng munud ac mae am ddim. Archebwch ef nawr; ar ôl ei wneud gallwch archebu'r gwasanaeth hwn ar gyfer {hours} awr neu fwy wedyn.",
        "patch_book": "Archebu prawf rhybudd alergedd am ddim",
        "reaction_h": "Ydych chi erioed wedi adweithio i liw gwallt, prawf patsh, neu gynnyrch gwallt neu groen?",
        "reaction_p": "Er enghraifft cosi, brech, chwyddo neu losgi. Gwybodaeth iechyd yw eich ateb. Dim ond os cytunwch, ar y cam olaf, y byddwn yn ei gadw.",
        "reaction_missing": "Atebwch ydw neu nac ydw.",
        "reaction_blocked_h": "Mae angen i ni siarad â chi cyn archebu hyn",
        "reaction_blocked_p": "Gan eich bod wedi cael adwaith o'r blaen, mae angen i oruchwyliwr siarad â chi cyn archebu'r gwasanaeth hwn. E-bostiwch {email}.",
        "who_h": "Pwy hoffech chi?",
        "who_p": "Mae dysgwyr ar gam cynharach yn costio llai ac yn cymryd mwy o amser. Mae pob dysgwr yn gweithio dan oruchwyliaeth.",
        "who_any": "Unrhyw ddysgwr — y cyntaf sydd ar gael", "who_any_detail": "O {from}. Mae'r amser a'r pris yn dibynnu ar y dysgwr; fe welwch y ddau ar gyfer pob amser.",
        "who_detail": "Tua {time} — {price}", "who_qualified": "Byddai steilydd cymwysedig yn cymryd tua {time}.", "who_missing": "Dewiswch pwy hoffech chi.",
        "when_h": "Pryd hoffech chi ddod?", "when_p": "Dewiswch ddiwrnod, yna amser.",
        "full": "Llawn", "few": "Ychydig", "lots": "Digon", "closed": "Ar gau",
        "next_available": "Y nesaf sydd ar gael: {when}", "none_available": "Nid oes dim ar gael yn yr wythnosau nesaf. E-bostiwch {email}.",
        "earlier": "Diwrnodau cynharach", "later": "Diwrnodau diweddarach", "morning": "Bore", "afternoon": "Prynhawn",
        "no_morning": "Dim byd yn y bore.", "no_afternoon": "Dim byd yn y prynhawn.", "day_full": "Dim ar ôl ar y diwrnod hwn. Dewiswch ddiwrnod arall.",
        "slot_detail": "{start} i {end} — {level} — {price}", "when_missing": "Dewiswch ddiwrnod ac amser.",
        "details_h": "Eich manylion", "name": "Eich enw", "email": "Cyfeiriad e-bost", "email_hint": "Anfonwn eich cadarnhad yma.",
        "phone": "Rhif ffôn symudol (dewisol)", "phone_hint": "Dim ond os bydd angen i ni gysylltu â chi am yr apwyntiad hwn y caiff ei ddefnyddio.",
        "guardian_h": "Rhiant neu warcheidwad", "guardian_name": "Enw'r rhiant neu'r gwarcheidwad",
        "guardian_confirm": "Fi yw rhiant neu warcheidwad y person sy'n cael y gwasanaeth hwn, rwy'n cydsynio iddo, a byddaf yn bresennol.",
        "notes": "Alergeddau, cyflyrau croen neu groen y pen y dylem wybod amdanynt (dewisol)", "notes_hint": "Gwybodaeth iechyd. Fe'i cedwir wedi'i hamgryptio, a dim ond staff goruchwylio sy'n ei darllen.",
        "consent_health": "Rwy'n cytuno i Clwydian Academy gadw fy atebion am adweithiau, alergeddau a chyflyrau croen er mwyn gallu cyflawni'r gwasanaeth hwn yn ddiogel.",
        "consent_terms": "Rwyf wedi darllen y telerau archebu ac yn cytuno iddynt.", "terms_link": "Darllen y telerau archebu",
        "missing_name": "Rhowch eich enw.", "missing_email": "Rhowch gyfeiriad e-bost dilys.", "missing_guardian": "Rhowch enw'r rhiant neu'r gwarcheidwad a thiciwch y blwch cydsynio.",
        "missing_health": "Ticiwch y blwch i adael i ni gadw eich atebion iechyd, neu e-bostiwch ni yn lle hynny.", "missing_terms": "Ticiwch y blwch i gytuno i'r telerau archebu.",
        "review_h": "Gwirio a thalu eich blaendal", "review_h_free": "Gwirio a chadarnhau",
        "sum_service": "Gwasanaeth", "sum_who": "Gyda", "sum_when": "Pryd", "sum_length": "Caniatewch", "sum_price": "Pris", "sum_deposit": "Blaendal i'w dalu nawr", "sum_balance": "I'w dalu ar y diwrnod",
        "supervised": "{level}, dan oruchwyliaeth",
        "length_honest": "{time}. Byddai steilydd cymwysedig yn cymryd tua {qualified}; mae dysgwr yn cymryd mwy o amser, ac mae addysgwr yn gwirio'r gwaith.",
        "length_same": "{time}, gan gynnwys amser gyda'r addysgwr.",
        "pay": "Talu blaendal o {amount}", "confirm": "Cadarnhau'r archeb", "paying": "Un eiliad…",
        "pay_note": "Byddwch yn mynd i'n tudalen talu â cherdyn. Cedwir eich amser am {minutes} munud tra byddwch yn talu.",
        "placeholder_banner": "DATA PRAWF — mae'r prisiau, yr amseroedd a'r dyddiadau hyn yn rhai dros dro sydd heb eu cadarnhau.",
        "done_h": "Rydych wedi'ch archebu", "done_p": "Eich cyfeirnod yw {ref}. Rydym wedi anfon eich cadarnhad drwy e-bost.",
        "held_h": "Rydym yn aros i'ch taliad gael ei gadarnhau", "held_p": "Fel arfer mae hyn yn cymryd ychydig eiliadau. Eich cyfeirnod yw {ref}. Bydd y dudalen hon yn diweddaru; nid oes angen i chi dalu eto.",
        "expired_h": "Ni chwblhawyd yr archeb honno", "expired_p": "Ni chadarnhawyd unrhyw daliad ac mae'r amser wedi'i ryddhau. Gallwch ddechrau eto.",
        "cancelled_h": "Ni chwblhawyd y taliad", "cancelled_p": "Nid ydych wedi cael eich codi. Cedwir eich amser am ychydig funudau eto — neu dechreuwch eto.",
        "start_again": "Dechrau eto", "unknown_ref": "Ni allem ddod o hyd i'r archeb honno. E-bostiwch {email}.",
        "hours": "{h} awr", "minutes": "{m} mun", "hours_minutes": "{h} awr {m} mun",
        "error": "Aeth rhywbeth o'i le ar ein hochr ni. Rhowch gynnig arall arni, neu e-bostiwch {email}.",
    },
}
MODELS = {
    "en": {"name": "Your name", "email": "Email address", "interests": "What are you interested in? (optional)", "days": "Days or times that suit you (optional)",
           "consent": "I agree to Clwydian Academy keeping these details to contact me about being a model. I can ask for them to be deleted at any time.",
           "send": "Join the register", "sending": "One moment…", "missing_name": "Please enter your name.", "missing_email": "Please enter a valid email address.",
           "missing_consent": "Please tick the box so that we may keep your details.", "done_h": "Thank you — you are on the register",
           "done_p": "We will email you when a learner needs a model.", "error": "That did not send. Please email {email} instead."},
    "cy": {"name": "Eich enw", "email": "Cyfeiriad e-bost", "interests": "Beth sydd o ddiddordeb i chi? (dewisol)", "days": "Diwrnodau neu amseroedd sy'n gyfleus i chi (dewisol)",
           "consent": "Rwy'n cytuno i Clwydian Academy gadw'r manylion hyn i gysylltu â mi ynglŷn â bod yn fodel. Gallaf ofyn iddynt gael eu dileu unrhyw bryd.",
           "send": "Ymuno â'r gofrestr", "sending": "Un eiliad…", "missing_name": "Rhowch eich enw.", "missing_email": "Rhowch gyfeiriad e-bost dilys.",
           "missing_consent": "Ticiwch y blwch er mwyn i ni gael cadw eich manylion.", "done_h": "Diolch — rydych ar y gofrestr",
           "done_p": "Anfonwn e-bost atoch pan fydd angen model ar ddysgwr.", "error": "Ni anfonwyd hynny. E-bostiwch {email} yn lle hynny."},
}

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

def levels(policy):
    """The levels that are switched on, lowest first."""
    on = [l for l, v in policy["levels"].items() if val(v["enabled"]) is not False]
    return sorted(on, key=lambda l: policy["levels"][l]["rank"])

def minutes_for(policy, service, level):
    """The same arithmetic as quote() in site/api/_lib/salon/quote.js, with no extras:
    base minutes x the level's factor for the category, rounded up to five, plus the educator's
    minutes. scripts/test_salon_rules.js runs both and fails if they disagree anywhere."""
    factor = val(policy["levels"][level]["factors"])[service["category"]]
    e = policy["educator"]
    return round_up5(val(service["base_minutes"]) * factor) + val(e["consultation_minutes"]) + val(e["final_check_minutes"])

def offered(policy, service, level):
    return level in levels(policy) and level in val(service["prices"]) and not (level == "l2" and val(service.get("l2_allowed", True)) is False)

def money(n):
    return "&pound;" + (str(int(n)) if float(n) == int(n) else f"{n:.2f}")

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

def draft_notice(loc):
    """Shown wherever a PM draft figure is printed, for as long as the policy holds any draft."""
    if not draft_paths(raw()):
        return ""
    return f'''<div class="salon-notice salon-draft" role="note">
      <h2>{t("draft_h", loc)}</h2>
      <p>{t("draft_p", loc)}</p>
    </div>'''

def deposit_text(p, loc):
    d = p["deposit"]
    if not (printable(d["cutting"]) and printable(d["colour"])):
        return t("deposit_tbc", loc)
    return t("deposit_p", loc, cutting=money(val(d["cutting"])), colour=money(val(d["colour"])), cancel=p["cancel_window_hours"])

def subnav(loc, current):
    links = []
    for key in ("home", "prices", "book", "models", "terms"):
        label = t("salon" if key == "home" else key, loc)
        cur = ' aria-current="page"' if key == current else ""
        links.append(f'<a href="{PATHS[key][loc]}"{cur}>{label}</a>')
    label = "Salon" if loc == "en" else "Salon"
    return f'<nav class="salon-subnav" aria-label="{label}"><div class="wrap">{"".join(links)}</div></nav>\n'

# ------------------------------------------------------------------------------------------------
def home_body(loc, site):
    p = raw()
    how = "".join(f'<li class="step"><h3>{h}</h3><p>{body.replace("{patch_hours}", str(p["patch_test"]["min_hours"])).replace("{patch_months}", str(p["patch_test"]["max_months"]))}</p></li>'
                  for h, body in T["how"][loc])
    op = p["opening"]
    if not printable(op["sessions"]) or not printable(op["terms"]):
        opening = f'<p><strong>{t("tbc", loc)}.</strong></p>'
    else:
        days = "".join(f'<div class="meta-row"><dt>{DAYS[loc][d]}</dt><dd>{", ".join(s["open"] + "&ndash;" + s["close"] for s in ss)}</dd></div>'
                       for d, ss in val(op["sessions"]).items() if ss)
        terms = "".join(f'<div class="meta-row"><dt>{long_date(x["from"], loc)}</dt><dd>&ndash; {long_date(x["to"], loc)}</dd></div>' for x in val(op["terms"]))
        opening = f'<div class="meta-panel"><h3>{t("open_days", loc)}</h3><dl>{days}</dl><h3 class="mt-2">{t("open_terms", loc)}</h3><dl>{terms}</dl></div>'
    notice = "" if confirmed(p) else soon(loc, site)
    return subnav(loc, "home") + hero(loc, [(t("salon", loc), None)], t("home_h1", loc), t("home_lede", loc)) + f'''
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
        <p class="hero-actions mt-3">
          <a class="btn btn-salon" href="{PATHS["book"][loc]}">{t("cta_book", loc)}</a>
          <a class="btn btn-outline" href="{PATHS["prices"][loc]}">{t("cta_prices", loc)}</a>
          <a class="btn btn-outline" href="{PATHS["models"][loc]}">{t("cta_models", loc)}</a>
        </p>
      </div>
    </div>
  </div>
</section>
'''

def prices_body(loc, site):
    p = raw()
    lv = levels(p)
    head = "".join(f'<th scope="col">{esc(p["levels"][l]["name"][loc])}</th>' for l in lv)
    def cell(prices_node, time=None, plus=False):
        """One level's cell: a price (never a placeholder) and, for a service, an honest time."""
        out = []
        for l in lv:
            prices = val(prices_node)
            if l not in prices:
                out.append(f'<td class="salon-na"><span class="sr-only">{t("not_offered", loc)}</span><span aria-hidden="true">&mdash;</span></td>')
                continue
            # the figure for THIS level may be a placeholder inside a draft table
            node = prices_node["value"] if (is_draft(prices_node) or is_todo(prices_node)) else prices_node
            if is_todo(prices_node) or not printable(node.get(l)):
                price = t("tbc", loc)
            elif plus:
                price = "+" + money(prices[l])
            else:
                price = t("free", loc) if prices[l] == 0 else t("from", loc) + " " + money(prices[l])
            small = f"<small>{time(l)}</small>" if time else ""
            out.append(f"<td><b>{price}</b>{small}</td>")
        return "".join(out)
    sections = []
    for gid, gname in p["groups"].items():
        rows = []
        for s in p["services"]:
            if s["group"] != gid:
                continue
            notes = []
            if s.get("note"): notes.append(esc(s["note"][loc]))
            if s.get("includes_finish"): notes.append(t("finish_note", loc))
            if s.get("consultation_first"): notes.append(t("consult_note", loc))
            if s.get("patch_test_product"): notes.append(t("patch_note", loc))
            if s.get("chemical") in p["age"]["restricted_chemicals"]: notes.append(t("u16_note", loc))
            note = f'<small>{" &middot; ".join(notes)}</small>' if notes else ""
            def time(l, s=s):
                ok = printable(s["base_minutes"]) and printable(p["levels"][l]["factors"]) and printable(p["educator"])
                return duration(minutes_for(p, s, l), loc) if ok else t("time_tbc", loc)
            only = {l: v for l, v in val(s["prices"]).items() if offered(p, s, l)}
            node = dict(s["prices"], value=only) if (is_draft(s["prices"]) or is_todo(s["prices"])) else only
            rows.append(f'<tr><th scope="row">{esc(s["name"][loc])}{note}</th>{cell(node, time)}</tr>')
        if rows:
            sections.append(f'''<h2 class="salon-h2 mt-3">{esc(gname[loc])}</h2>
    <div class="salon-table-wrap" tabindex="0" role="region" aria-label="{esc(gname[loc])}">
    <table class="salon-prices">
      <thead><tr><th scope="col">{t("service", loc)}</th>{head}</tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
    </div>''')
    # extras
    rows = [f'<tr><th scope="row">{esc(a["name"][loc])}</th>{cell(a["prices"], None, True)}</tr>' for a in p["addons"].values() if isinstance(a, dict)]
    extras = f'''<h2 class="salon-h2 mt-3">{t("extras_h", loc)}</h2>
    <div class="salon-table-wrap" tabindex="0" role="region" aria-label="{t("extras_h", loc)}">
    <table class="salon-prices">
      <thead><tr><th scope="col">{t("extra", loc)}</th>{head}</tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
    </div>'''
    # what the hair adds
    rows = []
    for qid, q in p["questions"].items():
        if not isinstance(q, dict):
            continue
        for o in q["options"]:
            if all(v == 0 for v in val(o["add"]).values()):
                continue
            # a yes/no question reads as its own label ("Is your hair longer than shoulder length?")
            label = esc(q["ask"][loc]) if qid == "long_hair" else f'{esc(o["label"][loc])}<small>{esc(q["ask"][loc])}</small>'
            rows.append(f'<tr><th scope="row">{label}</th>{cell(o["add"], None, True)}</tr>')
    hair = f'''<h2 class="salon-h2 mt-3">{t("hair_h", loc)}</h2>
    <p class="mt-1 measure">{t("hair_colour_p", loc)}</p>
    <p class="mt-1 measure">{t("hair_l3_p", loc)}</p>
    <div class="salon-table-wrap" tabindex="0" role="region" aria-label="{t("hair_h", loc)}">
    <table class="salon-prices">
      <thead><tr><th scope="col">{t("answer", loc)}</th>{head}</tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
    </div>'''
    c = p["concession"]
    if printable(c["percent"]) and printable(c["days"]) and printable(c["who"]):
        conc = t("conc_p", loc, percent=val(c["percent"]), days=", ".join(DAYS[loc][d] for d in val(c["days"])), who=", ".join(val(c["who"])[loc]))
    else:
        conc = t("tbc", loc) + "."
    notice = "" if confirmed(p) else soon(loc, site)
    return subnav(loc, "prices") + hero(loc, [(t("salon", loc), PATHS["home"][loc]), (t("prices", loc), None)], t("prices_h1", loc), t("prices_lede", loc)) + f'''
<section class="section section--tight" style="padding-top:0">
  <div class="wrap">
    {notice}
    {draft_notice(loc)}
    {"".join(sections)}
    {extras}
    {hair}
    <h2 class="salon-h2 mt-3">{t("conc_h", loc)}</h2>
    <p class="mt-1 measure">{conc}</p>
    <h2 class="salon-h2 mt-3">{t("deposit_h", loc)}</h2>
    <p class="mt-1 measure">{deposit_text(p, loc)}</p>
    <h2 class="salon-h2 mt-3">{t("test_h", loc)}</h2>
    <p class="mt-1 measure">{t("test_p", loc, patch_hours=p["patch_test"]["min_hours"])}</p>
    <h2 class="salon-h2 mt-3">{t("u16_h", loc)}</h2>
    <p class="mt-1 measure">{t("u16_p", loc)}</p>
    <p class="hero-actions mt-3"><a class="btn btn-salon" href="{PATHS["book"][loc]}">{t("cta_book", loc)}</a></p>
  </div>
</section>
'''

def app_data(obj):
    """JSON for a <script type="application/json"> block: safe inside HTML."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")

def book_body(loc, site):
    strings = dict(JOURNEY[loc])
    data = {"lang": loc, "email": site["email"], "terms": PATHS["terms"][loc], "book": PATHS["book"][loc], "t": strings,
            "days": [DAYS[loc][d] for d in ("sun", "mon", "tue", "wed", "thu", "fri", "sat")], "months": MONTHS[loc]}
    return subnav(loc, "book") + hero(loc, [(t("salon", loc), PATHS["home"][loc]), (t("book", loc), None)], t("book_h1", loc), t("book_lede", loc)) + f'''
<section class="section section--tight" style="padding-top:0">
  <div class="wrap">
    <noscript><div class="salon-notice"><p>{t("nojs", loc, email=site["email"])}</p></div></noscript>
    <div id="salon-book" class="salon-app" aria-live="polite"></div>
    <script type="application/json" id="salon-data">{app_data(data)}</script>
  </div>
</section>
'''

def models_body(loc, site):
    p = raw()
    groups = {k: v[loc] for k, v in p["groups"].items() if k != "test"}
    data = {"lang": loc, "email": site["email"], "t": MODELS[loc], "groups": groups}
    m = p["models"]
    what = (t("models_what", loc, lo=money(val(m["colour_product_cost"])[0]), hi=money(val(m["colour_product_cost"])[1]), deposit=money(val(m["refundable_deposit"])))
            if printable(m) else t("models_tbc", loc))
    return subnav(loc, "models") + hero(loc, [(t("salon", loc), PATHS["home"][loc]), (t("models", loc), None)], t("models_h1", loc), t("models_lede", loc)) + f'''
<section class="section section--tight" style="padding-top:0">
  <div class="wrap">
    {draft_notice(loc) if printable(p["models"]) else ""}
    <p class="measure">{what}</p>
    <noscript><div class="salon-notice mt-2"><p>{t("nojs", loc, email=site["email"])}</p></div></noscript>
    <div id="salon-models" class="salon-app mt-2" aria-live="polite"></div>
    <script type="application/json" id="salon-data">{app_data(data)}</script>
  </div>
</section>
'''

def terms_body(loc, site):
    p = raw()
    fill = {"deposit": deposit_text(p, loc), "email": f'<a href="mailto:{site["email"]}">{site["email"]}</a>', "cancel": p["cancel_window_hours"],
            "patch_hours": p["patch_test"]["min_hours"], "patch_months": p["patch_test"]["max_months"], "privacy": PRIVACY[loc]}
    parts = []
    for h, body in T["terms_sections"][loc]:
        for k, v in fill.items():
            body = body.replace("{" + k + "}", str(v))
        parts.append(f'<h2 class="salon-h2 mt-3">{h}</h2>\n    <p class="mt-1 measure">{body}</p>')
    draft = f'<div class="salon-notice" role="note"><p><strong>{t("terms_draft", loc)}</strong></p></div>' if not printable(p["terms_approved"]) or not val(p["terms_approved"]) else ""
    return subnav(loc, "terms") + hero(loc, [(t("salon", loc), PATHS["home"][loc]), (t("terms", loc), None)], t("terms_h1", loc), "") + f'''
<section class="section section--tight" style="padding-top:0">
  <div class="wrap">
    {draft}
    {"".join(parts)}
  </div>
</section>
'''

def staff_body(loc, site):
    return '''<section class="section section--tight">
  <div class="wrap">
    <h1 class="salon-h1">Salon day sheet</h1>
    <noscript><div class="salon-notice"><p>The day sheet needs JavaScript.</p></div></noscript>
    <div id="salon-staff" class="salon-app salon-staff" aria-live="polite"></div>
  </div>
</section>
'''

BODIES = {"salon": home_body, "salon-prices": prices_body, "salon-book": book_body, "salon-models": models_body,
          "salon-terms": terms_body, "salon-staff": staff_body}
ASSETS = {"salon-book": ["/assets/js/salon-book.js"], "salon-models": ["/assets/js/salon-models.js"], "salon-staff": ["/assets/js/salon-staff.js"]}

def body(kind, loc, site):
    return BODIES[kind](loc, site)

def scripts(kind):
    return ASSETS.get(kind, [])

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
        salon["openingHoursSpecification"] = [{"@type": "OpeningHoursSpecification", "dayOfWeek": "https://schema.org/" + names[d], "opens": s["open"], "closes": s["close"]}
                                              for d, ss in val(op["sessions"]).items() for s in ss]
    link = {"@context": "https://schema.org", "@type": org["@type"], "@id": org["@id"], "department": {"@id": salon_id}}
    return [salon, link]
