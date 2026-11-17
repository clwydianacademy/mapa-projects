/* Clwydian Academy training salon — the words, in both languages.
 *
 * feasible() and the handlers answer with a CODE; this file turns a code into a sentence. One
 * place, so the reason a client reads when a slot is refused is the same sentence wherever it
 * is refused. The Welsh is machine-written and unreviewed — see prompts/RELAY.md, WELSH FOR REVIEW.
 */
"use strict";
const { CONTACT } = require("./email");

const REASON = {
  "bad-request":        { en: "Something in that request was not right. Please start again.", cy: "Roedd rhywbeth o'i le yn y cais hwnnw. Dechreuwch eto, os gwelwch yn dda." },
  "unknown-service":    { en: "We do not recognise that service.", cy: "Nid ydym yn adnabod y gwasanaeth hwnnw." },
  "unknown-level":      { en: "We do not recognise that learner level.", cy: "Nid ydym yn adnabod y lefel dysgwr honno." },
  "out-of-term":        { en: "The salon is open in term time only, and that date is outside term.", cy: "Mae'r salon ar agor yn ystod y tymor yn unig, ac mae'r dyddiad hwnnw y tu allan i'r tymor." },
  "closed-date":        { en: "The salon is closed on that date.", cy: "Mae'r salon ar gau ar y dyddiad hwnnw." },
  "closed-day":         { en: "The salon does not open on that day of the week.", cy: "Nid yw'r salon yn agor ar y diwrnod hwnnw o'r wythnos." },
  "outside-hours":      { en: "That appointment would not fit inside the salon session. Please pick an earlier time.", cy: "Ni fyddai'r apwyntiad hwnnw'n ffitio o fewn sesiwn y salon. Dewiswch amser cynharach." },
  "too-soon":           { en: "That is too soon — we need at least {hours} hours' notice.", cy: "Mae hynny'n rhy fuan — mae angen o leiaf {hours} awr o rybudd arnom." },
  "too-far":            { en: "We are only booking up to {days} days ahead.", cy: "Dim ond hyd at {days} diwrnod ymlaen llaw yr ydym yn archebu." },
  "age-missing":        { en: "Please tell us whether the person having the service is under 16.", cy: "Dywedwch wrthym a yw'r person sy'n cael y gwasanaeth o dan 16 oed." },
  "under16-chemical":   { en: "We cannot offer permanent or quasi-permanent colour, bleach or relaxer to anyone under 16.", cy: "Ni allwn gynnig lliw parhaol na chwasi-barhaol, cannydd nac ymlaciwr i unrhyw un o dan 16 oed." },
  "guardian-consent":   { en: "Someone under 16 needs a parent or guardian's consent for this service.", cy: "Mae angen caniatâd rhiant neu warcheidwad ar rywun o dan 16 oed ar gyfer y gwasanaeth hwn." },
  "patch-none":         { en: "This service needs a patch test with us first, at least {hours} hours before your appointment. We could not find one for that email address.", cy: "Mae angen prawf patsh gyda ni yn gyntaf ar gyfer y gwasanaeth hwn, o leiaf {hours} awr cyn eich apwyntiad. Ni allem ddod o hyd i un ar gyfer y cyfeiriad e-bost hwnnw." },
  "patch-too-recent":   { en: "Your patch test has to be at least {hours} hours before the appointment. Please pick a later time.", cy: "Rhaid i'ch prawf patsh fod o leiaf {hours} awr cyn yr apwyntiad. Dewiswch amser diweddarach." },
  "patch-expired":      { en: "Your patch test for this product is more than {months} months old, so you need a new one first.", cy: "Mae eich prawf patsh ar gyfer y cynnyrch hwn dros {months} mis oed, felly mae angen un newydd arnoch yn gyntaf." },
  "skill-level":        { en: "That service is not offered at that learner level.", cy: "Nid yw'r gwasanaeth hwnnw'n cael ei gynnig ar y lefel dysgwr honno." },
  "skill-not-signed-off": { en: "That learner has not been signed off for this service yet.", cy: "Nid yw'r dysgwr hwnnw wedi'i gymeradwyo ar gyfer y gwasanaeth hwn eto." },
  "student-unknown":    { en: "That time is no longer available. Please pick another.", cy: "Nid yw'r amser hwnnw ar gael mwyach. Dewiswch un arall." },
  "student-level-changed": { en: "That time is no longer available. Please pick another.", cy: "Nid yw'r amser hwnnw ar gael mwyach. Dewiswch un arall." },
  "student-not-in":     { en: "That learner is not in the salon that day.", cy: "Nid yw'r dysgwr hwnnw yn y salon y diwrnod hwnnw." },
  "student-busy":       { en: "Someone has just taken that time. Please pick another.", cy: "Mae rhywun newydd gymryd yr amser hwnnw. Dewiswch un arall." },
  "no-chair":           { en: "Every chair is taken at that time. Please pick another.", cy: "Mae pob cadair wedi'i chymryd bryd hynny. Dewiswch amser arall." },
  "no-basin":           { en: "The basins are taken at that time. Please pick another.", cy: "Mae'r basnau wedi'u cymryd bryd hynny. Dewiswch amser arall." },
  "no-supervisor":      { en: "The supervisor is checking another learner's work at that time. Please pick another.", cy: "Mae'r goruchwyliwr yn gwirio gwaith dysgwr arall bryd hynny. Dewiswch amser arall." },
  "supervisor-ratio":   { en: "The salon is at its supervised limit at that time. Please pick another.", cy: "Mae'r salon ar ei derfyn goruchwylio bryd hynny. Dewiswch amser arall." },
  "stale":              { en: "That booking was changed by someone else. Reload and try again.", cy: "Newidiwyd yr archeb honno gan rywun arall. Ail-lwythwch a rhowch gynnig arall arni." },
  "not-found":          { en: "We could not find that booking.", cy: "Ni allem ddod o hyd i'r archeb honno." },
  "bad-transition":     { en: "That booking cannot be changed to that status.", cy: "Ni ellir newid yr archeb honno i'r statws hwnnw." },
  "details":            { en: "Please check your details — something is missing.", cy: "Gwiriwch eich manylion — mae rhywbeth ar goll." },
  "consent-terms":      { en: "Please agree to the booking terms to continue.", cy: "Cytunwch i'r telerau archebu i barhau." },
  "consent-health":     { en: "We can only keep your consultation answers with your consent. Please tick the box, or email us instead.", cy: "Dim ond gyda'ch caniatâd y gallwn gadw eich atebion ymgynghori. Ticiwch y blwch, neu e-bostiwch ni yn lle hynny." },
  "consultation-needed": { en: "Because of what you have told us, we need to talk to you before booking this service. Please email " + CONTACT + ".", cy: "Oherwydd yr hyn rydych wedi'i ddweud wrthym, mae angen i ni siarad â chi cyn archebu'r gwasanaeth hwn. E-bostiwch " + CONTACT + "." },
  "rate":               { en: "Too many requests. Please wait a few minutes and try again.", cy: "Gormod o geisiadau. Arhoswch ychydig funudau a rhowch gynnig arall arni." },
  "unavailable":        { en: "Online booking is not available right now. Please email " + CONTACT + " and we will book you in.", cy: "Nid yw archebu ar-lein ar gael ar hyn o bryd. E-bostiwch " + CONTACT + " ac fe wnawn ni eich archebu." },
  "signin":             { en: "Please sign in.", cy: "Mewngofnodwch, os gwelwch yn dda." },
};

function say(code, lang, detail) {
  const row = REASON[code] || REASON.unavailable;
  let text = row[lang === "cy" ? "cy" : "en"];
  for (const k of Object.keys(detail || {})) text = text.split("{" + k + "}").join(String(detail[k]));
  return text;
}

const MONTHS = {
  en: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
  cy: ["Ionawr", "Chwefror", "Mawrth", "Ebrill", "Mai", "Mehefin", "Gorffennaf", "Awst", "Medi", "Hydref", "Tachwedd", "Rhagfyr"],
};
const DAYS = {
  en: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
  cy: ["Dydd Sul", "Dydd Llun", "Dydd Mawrth", "Dydd Mercher", "Dydd Iau", "Dydd Gwener", "Dydd Sadwrn"],
};
function longDate(iso, lang) {
  const l = lang === "cy" ? "cy" : "en";
  const d = new Date(iso + "T00:00:00Z");
  return `${DAYS[l][d.getUTCDay()]} ${d.getUTCDate()} ${MONTHS[l][d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

/** The confirmation email. Fixed text plus the booking's own facts; nothing the client typed
 *  except their name is repeated back. */
function confirmation(booking, serviceName, levelName, policy, clock) {
  const cy = booking.lang === "cy";
  const when = longDate(booking.date, booking.lang) + ", " + clock(booking.start) + "–" + clock(booking.start + booking.minutes);
  const paid = booking.deposit > 0;
  const lines = cy ? [
    "Helo " + booking.client.name + ",",
    "",
    "Mae eich apwyntiad yn salon hyfforddi Clwydian Academy wedi'i gadarnhau.",
    "",
    "Cyfeirnod: " + booking.id,
    "Gwasanaeth: " + serviceName,
    "Gyda: " + levelName + ", dan oruchwyliaeth",
    "Pryd: " + when,
    "Pris: £" + booking.price + (paid ? " (blaendal o £" + booking.deposit + " wedi'i dalu; £" + (booking.price - booking.deposit) + " i'w dalu ar y diwrnod)" : ""),
    "",
    "Mae dysgwyr yn cymryd mwy o amser na steilydd cymwysedig, ac mae goruchwyliwr yn gwirio'r gwaith. Caniatewch yr amser llawn a ddangosir uchod.",
    "",
    "I newid neu ganslo, e-bostiwch " + CONTACT + " o leiaf " + policy.cancel_window_hours + " awr ymlaen llaw.",
    "",
    "Clwydian Academy CBC",
  ] : [
    "Hello " + booking.client.name + ",",
    "",
    "Your appointment at the Clwydian Academy training salon is confirmed.",
    "",
    "Reference: " + booking.id,
    "Service: " + serviceName,
    "With: " + levelName + ", supervised",
    "When: " + when,
    "Price: £" + booking.price + (paid ? " (£" + booking.deposit + " deposit paid; £" + (booking.price - booking.deposit) + " to pay on the day)" : ""),
    "",
    "Learners take longer than a qualified stylist, and a supervisor checks the work. Please allow the full time shown above.",
    "",
    "To change or cancel, email " + CONTACT + " at least " + policy.cancel_window_hours + " hours beforehand.",
    "",
    "Clwydian Academy CBC",
  ];
  return {
    subject: cy ? "Eich apwyntiad salon — " + booking.id : "Your salon appointment — " + booking.id,
    text: lines.join("\n"),
  };
}

module.exports = { say, REASON, longDate, confirmation };
