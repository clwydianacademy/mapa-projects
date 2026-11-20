# Booking engine inventory — source for the Clwydian Academy training salon

**Written 17 November 2026, Step 1 of the salon brief. Read-only on the source.**

Source: `clwydianacademy/charlotte-eleanor-booking` at commit `fd5505f` — 300 tracked files.
Target: this repository, `site/` (Vercel root directory), branch `feat/salon`.

The source is a booking and round-planning system for **one mobile hairdresser driving between
villages**. The salon is the opposite shape: **many students working at once in one room**, each
needing a chair, sometimes a basin, and a supervisor's check. So this inventory sorts every file
into three piles:

| Decision | Files | Meaning |
|---|---|---|
| **KEEP** | 5 | Ported in substance (re-typed as CommonJS, renamed, no source branding). |
| **CHANGE** | 44 | The idea or pattern is reused; the code is rewritten for the salon. |
| **REMOVE** | 251 | Not carried over: travel, drive time, villages/zones, round planning, franchise dispatch, mobile CRM, SMS, push, the stylist app, source branding and source process files. |

**It is a one-off copy.** No shared code, no submodule, no package, no import path between the
repositories. Nothing in `site/` may contain the source's name, domain, colour (`#4e1622`),
photographs, people's names or telephone numbers — `scripts/check_claims.py` is extended to fail
the build if any of them appears.

---

## 1. What the source is, technically

| | Source | Salon build in this repo |
|---|---|---|
| **Dependencies** | None. `package.json` has no `dependencies` block; every integration is `fetch` against a REST API. | None. Same rule. |
| **Module system** | ESM (`"type": "module"`), Node pinned `24.x` through `engines`. | CommonJS, because `site/` has no `package.json` and `site/api/enquiry.js` is CommonJS. Uses nothing newer than Node 18. The Node version is whatever the Vercel project is set to. |
| **Build** | None — no bundler, no transpiler. `node server.js` for local dev. | Functions: none. Pages: `website/_src/build.py`, as for the rest of the site. |
| **Hosting** | Its own Vercel project, 64 functions, 3 crons, strict CSP in `vercel.json`. | The academy's existing Vercel project. 6 new functions (7 with `enquiry`) — under the 12-function limit of Vercel's Hobby plan, which matters if that is the plan in use. No crons in Release 1. |
| **Layout** | `src/app.js` owns the logic; `api/*.js` are four-line shells. | `site/api/_lib/salon/` owns the logic (Vercel does not deploy underscore-prefixed folders as functions); `site/api/salon/*.js` are thin shells. |

## 2. Environment variables

Source (`.env.example`), and what the salon needs instead. **None of the source's values are
reused — the salon gets its own Upstash database, its own Stripe keys and its own staff password.**

| Source variable | Purpose | Salon |
|---|---|---|
| `KV_REST_API_URL`, `KV_REST_API_TOKEN` | Upstash Redis over REST — the diary. The one hard dependency. | **Needed, new values** — a new academy database. Same two names (they are what Vercel's Upstash integration sets). |
| `STRIPE_SECRET_KEY` | Checkout Sessions. Absent: bookings still save, deposit unpaid. | **Needed** (test mode first). Absent: the journey says so and gives `hello@`. |
| `STRIPE_WEBHOOK_SECRET` | Verifies the webhook. Absent: nothing can ever be marked paid. | **Needed.** Same behaviour. |
| `STAFF_PASSPHRASE` | Staff sign-in and the HMAC key for session tokens. | Renamed **`STAFF_PASSWORD`** per the brief. |
| `RESEND_API_KEY`, `EMAIL_PROVIDER`, `EMAIL_FROM`, `EMAIL_REPLY_TO`, `BREVO_API_KEY` | Email; Brevo by default. | `RESEND_API_KEY` only — **already set** in the academy's Vercel project. Sender `hello@clwydianacademy.co.uk`. No Brevo. |
| `SITE_URL`, `SITE_HOST` | Return address after Checkout. | Not needed: the return host is allow-listed in code (the academy's domain and Vercel previews). |
| `BOOKING_OPEN` | Unset means the public journey is closed. | Replaced by a stricter gate: the journey is closed while **any** `TODO_PM` remains in `_data/salon/policy.json`, and by `SALON_BOOKING_OPEN`. |
| — | — | **New: `SALON_DATA_KEY`** — 32 random bytes, base64. Encrypts consultation and allergy answers (AES-256-GCM). Absent: bookings that need a consultation are refused, never stored in clear. |
| `GOOGLE_MAPS_API_KEY`, `MAPS_API_KEY`, `ADDRESS_API_KEY` | Drive times, the map, address lookup. | REMOVE — travel. |
| `SMS_ENABLED`, `SMS_SENDER` | Texts through Brevo. | REMOVE. |
| `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` | Web push to the stylist app. | REMOVE. |
| `META_PIXEL_ID`, `META_CAPI_TOKEN`, `META_TEST_EVENT_CODE` | Advertising conversion signal. | REMOVE. |
| `TENANT`, `TRADER_*`, `CONTACT_PHONE` | Which franchise round, and its identity. | REMOVE — franchise dispatch; and the academy site carries no telephone number. |
| `STRIPE_CONNECTED_ACCOUNT`, `STRIPE_APPLICATION_FEE_PERCENT` | Franchise royalty through Stripe Connect. | REMOVE — and must stay removed: money routed to or through the Group would be a related-party flow. |
| `CRON_SECRET`, `BOOKING_LINK_SECRET` | Reminder crons; signed confirmation links. | REMOVE for Release 1 (no crons, no signed links). |
| `BOOKING_DATA_FILE`, `PORT` | Local file store; dev server port. | Tests use an in-memory store. |

## 3. Stripe webhook handling in the source

- **Raw body.** `api/stripe-webhook.js` is the one function written as a Web Handler
  (`export async function POST(request)`), so `await request.text()` is the unparsed body. Stripe
  signs exact bytes; a re-serialised object never verifies.
- **Verification by hand** (`src/webhook.js`, `verifySignature`): parse `t=` and every `v1=`,
  reject outside a 300-second tolerance, HMAC-SHA256 over `"<t>." + body` with the signing secret,
  compare with `timingSafeEqual` **after a length check** (it throws on unequal lengths, which
  would turn a bad signature into a 500).
- **Record before answering.** The work happens before the 200; a failure returns 500 so Stripe
  retries for three days. (Answering first would need `waitUntil` from a package.)
- **De-dupe twice**, each remembered 7 days: by `stripe-event:<event.id>` and by
  `stripe-occurrence:<type>:<object.id>`.
- **Events handled:** `checkout.session.completed`, `checkout.session.async_payment_succeeded`
  and `_failed`, `payment_intent.succeeded` and `.payment_failed`, `checkout.session.expired`,
  `charge.refunded`, `charge.dispute.created`.
- **Money law:** nothing outside this handler may set a payment to paid. The client returning to
  the success URL is a hint.
- **Late payment:** if the hold lapsed and someone else took the slot, the booking is re-checked
  with the feasibility rule; if it no longer fits it is flagged and refunded rather than
  double-booked. Unmatched payments go to an `unreconciled` list.

**Salon build:** all of the above is kept, reduced to deposit paid / session expired / refunded.
One open point: the target is CommonJS, so the webhook reads the request stream rather than a Web
`Request`. Vercel documents that `req.body` is parsed only when read, which leaves the stream
intact, but **that has to be proven on a preview deployment with a Stripe test event** before
anyone relies on it. If it fails, it fails closed — a bad signature marks nothing paid.

## 4. The write lock in the source

`KvStore.update` / `updateMany` in `src/store.js`:

1. `SET <key>:lock <uuid> NX PX 5000` — try to take a 5-second lock; up to 40 attempts, 50 ms apart.
2. Read the key(s), run a **synchronous** mutate function, write back.
3. `DEL <key>:lock` in a `finally`.

`Diary.add` runs `whyNot()` **inside** step 2, on the bookings read under the lock, so the check
that counts is made on current data. `updateMany` locks on the first key only, by design, so
closures and bookings share one lock.

**Two things change in the salon build:**

- **The lock is only released by its owner.** The source deletes the lock key without checking it
  still holds its own token. If a writer overruns 5 seconds, its lock expires, a second writer
  takes it, and the first writer's `finally` then deletes the *second* writer's lock. The salon
  store releases with a compare-and-delete, and refuses to write if it no longer holds the lock.
- **One key per day, with a version.** The source keeps the whole diary in one `bookings` array,
  read and rewritten on every booking. A salon with several students fills faster, so each day is
  its own key carrying a version number that goes up on every write; each booking carries its own
  version too, so a staff move made on a stale screen is refused instead of overwriting.

## 5. Storage keys in the source

| Key | Holds | Salon |
|---|---|---|
| `bookings` | Every booking, one array | → `salon:day:<date>` `{ v, bookings[] }` |
| `bookings:lock`, `<key>:lock` | Write locks | → `salon:day:<date>:lock` |
| `versions` | Per-date counters bumped by closures/kept days | → the `v` on each day and each booking |
| `stripe-event:<id>`, `stripe-occurrence:<type>:<id>` | Webhook de-dupe, 7-day expiry | → `salon:evt:<id>` |
| `unreconciled` | Payments that matched no booking | → `salon:unreconciled` |
| `rl:<key>`, `login-fail:<id>` | Rate limits | → `salon:rl:<key>` |
| `clients`, `series`, `conflicts`, `closures`, `kept`, `enquiries` | Client CRM, standing appointments and their conflicts, days off, kept days, enquiries | REMOVE |
| `travel-cache`, `geo:postcodes` | Drive-time and postcode caches | REMOVE |
| `push-subscriptions`, `magic:<hash>`, `audit:<date>` | Push, magic links, audit log | REMOVE |
| — | — | New: `salon:ref:<id>` (booking reference → date), `salon:students`, `salon:patch:<hash>` (patch-test record, keyed by a hash of the client's email), `salon:models` (model-call register) |

All salon keys are prefixed `salon:` so the database can never be confused with the source's,
even by accident of configuration.

## 6. Existing tests in the source

- `npm test` = `node test/shape.mjs && node test/run.js`, about one second, no dependencies.
- `test/run.js` — 18,420 lines, roughly 685 cases on its own small runner. The case that matters
  most is **"offer and save agree"**: every slot the offer engine produces must pass the save-time
  check.
- `test/shape.mjs` — repository guards (no dependencies block, published documents exist, no
  real-looking phone numbers, append-only relay file).
- `test/clockwalk.mjs` — re-runs the suite on simulated days to prove fixtures do not depend on
  the calendar.
- `tools/*-harness.mjs` — headless-Chrome checks of the real pages (target sizes, contrast,
  request bodies), because source-reading tests stayed green through every front-end defect.

None are copied: they pin the mobile rules. `scripts/test_salon_rules.js` is new and keeps the
two disciplines — a pass and a fail case for every rule, and *every offered slot passes the
save-time check*.

## 7. Where the source contradicts the brief, or the target's rules do

Raised with the PM in the Step 1 report; listed here so they are not lost.

1. **Telephone.** The brief says a degraded endpoint should show "call/email hello@". This
   repository's rules (PM decision, 17 Nov 2026) put **no telephone number** on the site, and
   `check_claims.py` fails the build on one. The salon pages say **email only**.
2. **Personal names.** The same decision bans personal names on the site. So the public journey
   offers "any student" or a **level**, never a named student. Student names exist only in the
   database and on the password-protected staff sheet.
3. **Patch test.** The source's rule is a *home kit posted to a first-colour client, 48 hours of
   lead time*. The brief's rule is different and stricter — a recorded test at least 48 hours
   before and no more than 12 months old, **for the same product**. It is built new; nothing of
   the home-kit chain is carried over.
4. **One worker vs many.** The source's feasibility rule assumes one person and a drive between
   every pair of jobs. The salon rule shares its discipline (one synchronous function, called for
   offers and again under the lock) and none of its content.
5. **Under-16s.** The source has no age rule. The brief's is built new.
6. **Brevo.** The source defaults to Brevo for email and uses it for SMS. The salon uses the
   academy's existing Resend setup and sends no texts.
7. **Premises.** This repository's rules say the St Asaph premises are not yet taken and the
   registered office is a residential address that must not be rolled out. So the salon's
   structured data carries the town only — no street address, no opening hours — until the PM
   supplies them.
8. **Provenance.** The code being copied belongs to the business the academy is held at arm's
   length from. A one-off transfer of software between the two is itself a related-party
   matter; whether it needs a written licence or assignment is a question for the PM, not
   something the code can settle.

---

## 8. Every file


### Engine — `src/`

| File | Decision | Purpose | What happens in the salon build |
|---|---|---|---|
| `src/app.js` | **CHANGE** | All 64 request handlers in one 5,376-line module (book, availability, quote, diary, staff-*, series, clients, sick day, earlier-slot offers, crons). | Not copied. The five public handlers and one staff handler are rewritten small, one per file, CommonJS. Everything mobile (geocode, set-off texts, zone days, standing series, client CRM, sick-day rebooking, numbers) is dropped. |
| `src/audit.js` | **REMOVE** | Append-only who-did-what, one key per day. | Release 1 stamps `by`/`at` on each status change instead. Worth revisiting. |
| `src/auth.js` | **CHANGE** | Signed staff token (HMAC over payload, keyed on the passphrase), cookie, `requireStaff`. | Kept for `/staff/`. Env name becomes `STAFF_PASSWORD`. Cookie renamed. No user database, no roles. |
| `src/availability.js` | **CHANGE** | `findAvailability()` walks days x 5-minute starts and keeps what `whyNot()` passes; `routeForDay()` builds the driving order. | Offer loop kept in shape; `routeForDay` and every travel precompute removed. |
| `src/birthday.js` | **REMOVE** | Client birthdays (MM-DD). | Mobile CRM. |
| `src/bookinglink.js` | **REMOVE** | Signed per-booking link token. | Not in Release 1 (confirmation is by email). |
| `src/bookingpage.js` | **REMOVE** | Server-rendered signed confirmation page. | Not in Release 1. |
| `src/brief.js` | **REMOVE** | What the stylist reads before knocking on the door. | Mobile. |
| `src/capacity.js` | **REMOVE** | Minutes of sellable day for the month bar and utilisation. | Not needed in Release 1. |
| `src/catalogue.js` | **CHANGE** | Loader over the tenant catalogue: lookup maps, `hasColour()`, which questions a visit asks. | Replaced by `_data/salon/policy.json` (services, tiers, prices) — configuration stays readable by a non-coder, which is the source's law 5. |
| `src/claims.js` | **REMOVE** | Enumerates stale SMS reminder claims. | SMS. |
| `src/config.js` | **CHANGE** | `keyStatus()` (a placeholder is not a credential — rejects `[SENSITIVE]`, too-short, wrong prefix), trader identity, booking-open switch. | `keyStatus` idea kept for the degrade checks. Trader identity and tenant plumbing removed (the academy is the only operator). |
| `src/confirm.js` | **CHANGE** | Exactly-once confirmation send claimed under the lock. | The claim-under-lock idea is kept inside the webhook path; file not copied. |
| `src/conversion.js` | **REMOVE** | Meta Conversions API signal. | No advertising signal on the academy site. |
| `src/daystate.js` | **REMOVE** | Open / kept-for-regulars / booked-out day states. | Replaced by term dates + opening sessions in policy.json. |
| `src/durations.js` | **REMOVE** | Measured service durations from progress taps. | Later release, if wanted. |
| `src/email.js` | **CHANGE** | Confirmation / reminder / receipt emails, Brevo (default) or Resend. | Resend only, via the academy's existing key and `hello@` sender. Confirmation only in Release 1. |
| `src/feasible.js` | **CHANGE** | `whyNot()` — the single scheduling rule, used for offers and again inside the write lock. Also `blocksSlot()` (a lapsed hold stops blocking on read, no cron). | The PATTERN is kept exactly (one synchronous rule, two callers, hold-lapses-on-read). The CONTENT is replaced: no drive chain, no home-by, no base; instead segments needing student/chair/basin/supervisor-check, term dates, skill gating, age rules. |
| `src/geocode.js` | **REMOVE** | Postcode -> coordinate / address list (Ideal Postcodes). | Travel. |
| `src/gsm7.js` | **REMOVE** | GSM-7 alphabet check for SMS. | SMS. |
| `src/kits.js` | **REMOVE** | Home patch-test kit posted/done record. | Mobile-only. |
| `src/leadtime.js` | **REMOVE** | Skin-test lead time as a postal chain (home kit). | Mobile-only. The salon patch test is done in the salon and recorded. |
| `src/magic.js` | **REMOVE** | Magic-link sign-in. | One shared staff password in Release 1. |
| `src/mask.js` | **KEEP** | Masks a recipient before it reaches a log line. | Ported (three lines). |
| `src/notify.js` | **REMOVE** | Channel routing (email vs SMS). | Email only. |
| `src/numbers.js` | **REMOVE** | Franchisee business figures. | Franchise. |
| `src/operator.js` | **REMOVE** | Tells the operator a booking arrived (push). | Push; franchise dispatch. |
| `src/payments.js` | **CHANGE** | Stripe Checkout Session by raw `fetch` (form-encoded), `toPence`, return-URL allowlist, derived paid/outstanding, refund. | Kept: raw REST, idempotency key, `expires_at` matched to the hold, metadata on the PaymentIntent, host allowlist. Removed: Connect application fee / franchise royalty, saved-card mandate, balance phase. Allowlist host changes to the academy's. |
| `src/permissions.js` | **REMOVE** | Role -> capability table. | Franchise. |
| `src/places.js` | **REMOVE** | Loader for villages, base, working days, zones. | Villages/zones. |
| `src/progress.js` | **REMOVE** | Four-step job progress (set off / arrived / started / done). | Replaced by booking status on the staff sheet. |
| `src/push.js` | **REMOVE** | Web Push by hand (VAPID). | Stylist PWA. |
| `src/quote.js` | **CHANGE** | Choices -> minutes + price + gates. Additive adders, shared finish, deposit bands, patch-test / colour-correction / over-long gates. | Additive rule and gate idea kept. Home-kit lead-time chain, setup-per-visit and 'visiting on its own' supplement removed. Level duration factor, price-per-tier and age gates added. Deposit becomes a % with a cap from policy.json. |
| `src/ramp.js` | **REMOVE** | New-unit target ramp. | Franchise. |
| `src/ratelimit.js` | **KEEP** | Store-backed counters: sign-in failures and per-IP limits. | Ported small: staff sign-in and booking POSTs. |
| `src/receipt.js` | **REMOVE** | Exactly-once receipt when finished and paid. | No balance payments online. |
| `src/retention.js` | **REMOVE** | Deletes audit days older than 12 months. | Goes with audit.js. (A retention job for consultation data is a TODO_PM.) |
| `src/series.js` | **REMOVE** | Standing appointments materialised as real bookings. | Mobile CRM; not in Release 1. |
| `src/sms.js` | **REMOVE** | Client texts through Brevo. | SMS / Brevo. |
| `src/store.js` | **CHANGE** | FileStore + KvStore (Upstash REST) behind one interface; `update`/`updateMany` under a `SET NX PX 5000` lock; `Diary`, `Closures`, `KeptDays`, `Enquiries`; `SlotTakenError`. | Upstash-over-fetch and the lock are kept. Changed: (1) the lock is released only by its owner (the source `DEL`s unconditionally, so a slow writer can delete the next writer's lock); (2) one key per DAY with a version number instead of the whole diary in one `bookings` key; (3) no `clients`, `closures`, `kept`, `series`, `conflicts` keys; (4) no silent file fallback in production (same as source). |
| `src/tenants/_template/catalogue.js` | **REMOVE** | Services, prices, base minutes, questions and adders. (invented template) | Franchise template. |
| `src/tenants/_template/identity.js` | **REMOVE** | Operator name, logo, references, sender. | Source branding. |
| `src/tenants/_template/places.js` | **REMOVE** | Villages, base address, working days, zone plan. | Villages/zones. |
| `src/tenants/charlotte/catalogue.js` | **CHANGE** | Services, prices, base minutes, questions and adders. | Structure reused for policy.json; NO price, wording or number is carried over — every salon figure is a TODO_PM placeholder. |
| `src/tenants/charlotte/identity.js` | **REMOVE** | Operator name, logo, references, sender. | Source branding. |
| `src/tenants/charlotte/places.js` | **REMOVE** | Villages, base address, working days, zone plan. | Villages/zones. |
| `src/tenants/index.js` | **REMOVE** | Selects the tenant (round) for a deployment. | Franchise dispatch. |
| `src/terms.js` | **CHANGE** | Statutory consumer notices as one structured source. | Not copied — the salon terms are a built page (`/salon/terms/`), wording TODO_PM. |
| `src/time.js` | **KEEP** | Calendar-date and minutes-past-midnight helpers in Europe/London; `hoursUntil` between real instants (DST-safe). | Ported as-is in substance: the 48 h patch-test rule depends on it. |
| `src/travel.js` | **REMOVE** | Drive times: Google Routes matrix, cache, budget guard, fallback estimate. | Travel. |
| `src/users.js` | **REMOVE** | People on a round, invitations, roles. | Franchise. |
| `src/webhook.js` | **CHANGE** | `verifySignature()` by hand (HMAC-SHA256 over `t.payload`, 300 s tolerance, length check before `timingSafeEqual`), event de-dupe, the only code allowed to mark money paid. | Verification and de-dupe kept. Handles deposit paid / session expired / refunded only. Late payment after a lapsed hold: re-run the feasibility rule, else flag for refund — kept. |

### Vercel functions — `api/`

| File | Decision | Purpose | What happens in the salon build |
|---|---|---|---|
| `api/audit-retention.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Audit cron. |
| `api/audit.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Audit log. |
| `api/auth-request.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/auth-verify.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/availability.js` | **CHANGE** | 4-line Vercel shell -> `handlers`. Slots for a quote. | Rewritten as `site/api/salon/availability.js`. |
| `api/b.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Signed confirmation page. |
| `api/birthdays.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/book.js` | **CHANGE** | 4-line Vercel shell -> `handlers`. Writes a booking under the lock; starts Checkout. | Rewritten as `site/api/salon/book.js`. |
| `api/catalogue.js` | **CHANGE** | 4-line Vercel shell -> `handlers`. Serves the service list. | Folded into `salon/quote` (GET). |
| `api/client-search.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/client-update.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/client.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/confirmations.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Cron retry sweep — later release. |
| `api/conflict-dismiss.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/conflict-resolve.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/conflicts.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/contact.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Operator details for the page. |
| `api/diary.js` | **CHANGE** | 4-line Vercel shell -> `handlers`. Day sheet data. | Folded into `salon/staff`. |
| `api/due.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/earlier-accept.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/earlier-candidates.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/earlier-offer.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/enquiries.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | As above. |
| `api/enquiry-done.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | As above. |
| `api/enquiry.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Target already has its own `api/enquiry.js`. |
| `api/geocode.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Travel. |
| `api/kit-posted.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Home kit. |
| `api/login.js` | **CHANGE** | 4-line Vercel shell -> `handlers`. Staff sign-in. | Folded into `salon/staff`. |
| `api/logout.js` | **CHANGE** | 4-line Vercel shell -> `handlers`. Staff sign-out. | Folded into `salon/staff`. |
| `api/maps-key.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Travel/map. |
| `api/month.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Month grid. |
| `api/numbers.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Franchise. |
| `api/progress.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Job progress. |
| `api/purge.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Client erasure — needs a salon equivalent (TODO_PM). |
| `api/push-key.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/push-subscribe.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/push-unsubscribe.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/quote.js` | **CHANGE** | 4-line Vercel shell -> `handlers`. Price and length for chosen services. | Rewritten as `site/api/salon/quote.js`. |
| `api/rebook.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Rebook panel — later release. |
| `api/receipts.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Receipts. |
| `api/reminder-claims.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | SMS. |
| `api/reminders.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Cron; SMS/email reminders — later release. |
| `api/series-create.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/series-end.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/series-list.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/series-top-up.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/sick-day-undo.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/sick-day.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Mobile CRM / standing appointments / earlier-slot offers / push. |
| `api/skin-test-done.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Replaced by a patch-test record on the staff sheet. |
| `api/sms-probe.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | SMS. |
| `api/staff-book.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Staff-side booking — later release. |
| `api/staff-cancel.js` | **CHANGE** | 4-line Vercel shell -> `handlers`. Cancel a booking. | Folded into `salon/staff`. |
| `api/staff-close.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Day closures — policy.json term dates in Release 1. |
| `api/staff-import.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Diary import. |
| `api/staff-keep.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Kept days. |
| `api/staff-move.js` | **CHANGE** | 4-line Vercel shell -> `handlers`. Move a booking (re-checked under the lock). | Folded into `salon/staff`. |
| `api/staff-no-show.js` | **CHANGE** | 4-line Vercel shell -> `handlers`. Mark no-show. | Folded into `salon/staff`. |
| `api/staff-open.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | As staff-close. |
| `api/stripe-webhook.js` | **CHANGE** | 4-line Vercel shell -> `handlers`. Web Handler reading the raw body for signature verification. | Target is CommonJS with no package.json, so it reads the request stream instead of a Web `Request` — to be proven on a Vercel preview. |
| `api/user-invite.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Franchise. |
| `api/user-update.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Franchise. |
| `api/users.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Franchise. |
| `api/week.js` | **REMOVE** | 4-line Vercel shell -> `handlers`. | Week view. |
| `api/whoami.js` | **CHANGE** | 4-line Vercel shell -> `handlers`. Who is signed in. | Folded into `salon/staff`. |

### Front end — `public/`

| File | Decision | Purpose | What happens in the salon build |
|---|---|---|---|
| `public/app/icon-180.png` | **REMOVE** | Stylist PWA (shell, manifest, icons, service worker). | Mobile stylist app. |
| `public/app/icon-192.png` | **REMOVE** | Stylist PWA (shell, manifest, icons, service worker). | Mobile stylist app. |
| `public/app/icon-512.png` | **REMOVE** | Stylist PWA (shell, manifest, icons, service worker). | Mobile stylist app. |
| `public/app/icon-maskable-512.png` | **REMOVE** | Stylist PWA (shell, manifest, icons, service worker). | Mobile stylist app. |
| `public/app/icon.svg` | **REMOVE** | Stylist PWA (shell, manifest, icons, service worker). | Mobile stylist app. |
| `public/app/index.html` | **REMOVE** | Stylist PWA (shell, manifest, icons, service worker). | Mobile stylist app. |
| `public/app/manifest.webmanifest` | **REMOVE** | Stylist PWA (shell, manifest, icons, service worker). | Mobile stylist app. |
| `public/app/sw.js` | **REMOVE** | Stylist PWA (shell, manifest, icons, service worker). | Mobile stylist app. |
| `public/assets/address-picker.js` | **REMOVE** | Address entry. | Travel / mobile app / mobile CRM. |
| `public/assets/alarm.js` | **REMOVE** | 'Due in ten minutes' on the round. | Travel / mobile app / mobile CRM. |
| `public/assets/app.css` | **CHANGE** | Design system for booking and staff pages (plum/brass tokens, 19px base, 54px targets). | NOT copied. Salon pages use the academy's `main.css` plus a small `salon.css` with its own accent. The 54px / contrast / not-colour-alone rules are kept as requirements. |
| `public/assets/book.js` | **CHANGE** | One question per screen; price and length visible throughout; Continue never disabled; focus moves to each new heading. | Journey pattern and accessibility rules kept; rewritten without address/village steps, with who/level, patch-test, age and consent steps, bilingual. |
| `public/assets/booking-ref.js` | **KEEP** | Sanitises a booking reference from a URL. | Ported inline. |
| `public/assets/confirmed.js` | **CHANGE** | Reads `?ref=`; never claims payment the server has not confirmed. | Rule kept. |
| `public/assets/contact.js` | **REMOVE** | Fills tenant identity into pages. | Travel / mobile app / mobile CRM. |
| `public/assets/diary.js` | **CHANGE** | Day sheet, add-appointment form, map view, month grid. | Only the day list, status changes and move are rebuilt; grouped by student. |
| `public/assets/directions.js` | **REMOVE** | Directions. | Travel / mobile app / mobile CRM. |
| `public/assets/due.js` | **REMOVE** | Lateness wording on the round. | Travel / mobile app / mobile CRM. |
| `public/assets/elapsed.js` | **REMOVE** | Time-on-job. | Travel / mobile app / mobile CRM. |
| `public/assets/fonts.css` | **REMOVE** | Self-hosted Poppins. | Academy uses its own fonts. |
| `public/assets/fonts/OFL.txt` | **REMOVE** | Poppins font file / licence. | Source branding. |
| `public/assets/fonts/poppins-400-latin-ext.woff2` | **REMOVE** | Poppins font file / licence. | Source branding. |
| `public/assets/fonts/poppins-400-latin.woff2` | **REMOVE** | Poppins font file / licence. | Source branding. |
| `public/assets/fonts/poppins-500-latin-ext.woff2` | **REMOVE** | Poppins font file / licence. | Source branding. |
| `public/assets/fonts/poppins-500-latin.woff2` | **REMOVE** | Poppins font file / licence. | Source branding. |
| `public/assets/fonts/poppins-600-latin-ext.woff2` | **REMOVE** | Poppins font file / licence. | Source branding. |
| `public/assets/fonts/poppins-600-latin.woff2` | **REMOVE** | Poppins font file / licence. | Source branding. |
| `public/assets/fonts/poppins-700-latin-ext.woff2` | **REMOVE** | Poppins font file / licence. | Source branding. |
| `public/assets/fonts/poppins-700-latin.woff2` | **REMOVE** | Poppins font file / licence. | Source branding. |
| `public/assets/img/logo-paper.svg` | **REMOVE** | Source logo artwork. | Source branding — must not reach `site/`. |
| `public/assets/img/logo-stack-paper.svg` | **REMOVE** | Source logo artwork. | Source branding — must not reach `site/`. |
| `public/assets/img/logo.svg` | **REMOVE** | Source logo artwork. | Source branding — must not reach `site/`. |
| `public/assets/img/mark.svg` | **REMOVE** | Source logo artwork. | Source branding — must not reach `site/`. |
| `public/assets/livemap.js` | **REMOVE** | Google map. | Travel / mobile app / mobile CRM. |
| `public/assets/map.js` | **REMOVE** | SVG round map. | Travel / mobile app / mobile CRM. |
| `public/assets/money.js` | **KEEP** | Pence to pounds in the browser. | Ported inline. |
| `public/assets/month.js` | **REMOVE** | Month grid sentence. | Travel / mobile app / mobile CRM. |
| `public/assets/nav.js` | **REMOVE** | Hand-off to a map app. | Travel / mobile app / mobile CRM. |
| `public/assets/offline.js` | **REMOVE** | Offline day cache. | Travel / mobile app / mobile CRM. |
| `public/assets/outbox.js` | **REMOVE** | Offline outbox. | Travel / mobile app / mobile CRM. |
| `public/assets/paging.js` | **CHANGE** | Which days a page of availability shows. | Replaced by the 14-day strip. |
| `public/assets/paint.js` | **REMOVE** | Map paint detection. | Travel / mobile app / mobile CRM. |
| `public/assets/phone.js` | **REMOVE** | Dial links. | Travel / mobile app / mobile CRM. |
| `public/assets/placelink.js` | **REMOVE** | Location links. | Travel / mobile app / mobile CRM. |
| `public/assets/progress.js` | **REMOVE** | Job progress words. | Travel / mobile app / mobile CRM. |
| `public/assets/push.js` | **REMOVE** | Push subscribe. | Travel / mobile app / mobile CRM. |
| `public/assets/safe-next.js` | **REMOVE** | Safe post-login redirect. | Single page; no redirect. |
| `public/assets/staff.js` | **CHANGE** | Sign-in page script. | Folded into `/staff/`. |
| `public/assets/standing.js` | **REMOVE** | Standing client notes. | Travel / mobile app / mobile CRM. |
| `public/assets/status.js` | **CHANGE** | One status vocabulary for every screen. | Idea kept: one status list in the engine, labels in the page. |
| `public/assets/stylist.css` | **REMOVE** | Stylist app styles. | Travel / mobile app / mobile CRM. |
| `public/assets/stylist.js` | **REMOVE** | Stylist app. | Travel / mobile app / mobile CRM. |
| `public/book/confirmed/index.html` | **CHANGE** | Landing page after Checkout. | Folded into `/salon/book/?ref=` — the page says 'paid' only when the server does. |
| `public/book/index.html` | **CHANGE** | Client booking journey shell. | Built by build.py as `/salon/book/` in EN and CY with academy chrome. |
| `public/diary/index.html` | **CHANGE** | Staff day sheet shell. | Rebuilt as `/staff/`. |
| `public/privacy/index.html` | **REMOVE** | Source client privacy notice. | Academy has its own `/privacy/`; a salon section is TODO_PM. |
| `public/privacy/staff/index.html` | **REMOVE** | Source staff privacy notice. | Not applicable. |
| `public/robots.txt` | **REMOVE** | Source robots. | Target's is generated by build.py. |
| `public/staff/index.html` | **CHANGE** | Staff sign-in page. | Folded into `/staff/`. |
| `public/terms/index.html` | **CHANGE** | Source booking terms. | New page `/salon/terms/`; no wording carried over. |

### Tests — `test/`

| File | Decision | Purpose | What happens in the salon build |
|---|---|---|---|
| `test/clockwalk.mjs` | **REMOVE** | Runs the suite once per simulated day. | New tests take `now` as an argument instead. |
| `test/number-guard.mjs` | **REMOVE** | Phone-number matcher for the shape guard. | Target bans telephone numbers outright already. |
| `test/relay-guard.mjs` | **REMOVE** | Append-only check on the relay file. | Source process. |
| `test/run.js` | **CHANGE** | The suite: 18,420 lines, roughly 685 cases, own tiny runner, no dependencies. Includes 'offer and save agree'. | Not copied (it pins the mobile rules). `scripts/test_salon_rules.js` is new, on `node:test`, and keeps the two ideas that matter: every rule has a pass and a fail case, and every offered slot is re-checked by the save path. |
| `test/shape.mjs` | **CHANGE** | Repository shape guards (no dependencies block, published-doc paths, phone-number shapes, append-only relay). | Target equivalents are `scripts/check_*.py`; the name/colour/domain guard is added to `check_claims.py`. |

### Developer tools — `tools/`

| File | Decision | Purpose | What happens in the salon build |
|---|---|---|---|
| `tools/a11y-harness.mjs` | **REMOVE** | Developer tool: accessibility measured in headless Chrome. | Not copied. The target has Playwright available; the journey is checked with it (54px targets, focus, no console errors). |
| `tools/arrival-gap.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/audit-purge.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/balance-proof.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/book-harness.mjs` | **REMOVE** | Developer tool: public journey, reading the POST body. | Not copied. The target has Playwright available; the journey is checked with it (54px targets, focus, no console errors). |
| `tools/browser-harness.mjs` | **REMOVE** | Developer tool: shared headless-Chrome plumbing. | Not copied. The target has Playwright available; the journey is checked with it (54px targets, focus, no console errors). |
| `tools/cdp.mjs` | **REMOVE** | Developer tool: DevTools protocol plumbing. | Not copied. The target has Playwright available; the journey is checked with it (54px targets, focus, no console errors). |
| `tools/deeplink-harness.mjs` | **REMOVE** | Developer tool: deep links into the journey. | Not copied. The target has Playwright available; the journey is checked with it (54px targets, focus, no console errors). |
| `tools/diarymap-harness-page.js` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/diarymap-harness.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/form-harness-page.js` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/form-harness.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/import-diary.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/journey-measure.mjs` | **REMOVE** | Developer tool: target sizes/contrast on each journey step. | Not copied. The target has Playwright available; the journey is checked with it (54px targets, focus, no console errors). |
| `tools/kv-export.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/make-icons.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/make-vapid-keys.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/map-harness-page.js` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/map-harness.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/meta-capi-probe.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/numbers-check.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/rebook-harness-page.js` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/rebook-harness.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/seed-demo-day.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/setoff-harness.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/shell-fingerprint.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/shot-harness.mjs` | **REMOVE** | Developer tool: screenshots. | Not copied. The target has Playwright available; the journey is checked with it (54px targets, focus, no console errors). |
| `tools/sms-probe.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |
| `tools/stale-reminder-claims.mjs` | **REMOVE** | Developer tool: round / map / SMS / import / PWA tooling. | Mobile-only or source-only. |

### Root, configuration, documents

| File | Decision | Purpose | What happens in the salon build |
|---|---|---|---|
| `.claude/agents/build-reviewer.md` | **REMOVE** | Agent rules/skills for the source repo. | Source process. The client-data rule (invented people in fixtures, Ofcom drama numbers) is followed in the new tests. |
| `.claude/rules/client-data.md` | **REMOVE** | Agent rules/skills for the source repo. | Source process. The client-data rule (invented people in fixtures, Ofcom drama numbers) is followed in the new tests. |
| `.claude/rules/engine.md` | **REMOVE** | Agent rules/skills for the source repo. | Source process. The client-data rule (invented people in fixtures, Ofcom drama numbers) is followed in the new tests. |
| `.claude/rules/frontend.md` | **REMOVE** | Agent rules/skills for the source repo. | Source process. The client-data rule (invented people in fixtures, Ofcom drama numbers) is followed in the new tests. |
| `.claude/rules/payments.md` | **REMOVE** | Agent rules/skills for the source repo. | Source process. The client-data rule (invented people in fixtures, Ofcom drama numbers) is followed in the new tests. |
| `.claude/rules/testing.md` | **REMOVE** | Agent rules/skills for the source repo. | Source process. The client-data rule (invented people in fixtures, Ofcom drama numbers) is followed in the new tests. |
| `.claude/settings.json` | **REMOVE** | Agent rules/skills for the source repo. | Source process. The client-data rule (invented people in fixtures, Ofcom drama numbers) is followed in the new tests. |
| `.claude/skills/verify/SKILL.md` | **REMOVE** | Agent rules/skills for the source repo. | Source process. The client-data rule (invented people in fixtures, Ofcom drama numbers) is followed in the new tests. |
| `.env.example` | **CHANGE** | Every env var with warnings. | See the env table below. |
| `.gitignore` | **REMOVE** | Ignores data/ and .env. |  |
| `APP-MOCKUP.html` | **REMOVE** | Source planning/spec document (APP-MOCKUP.html). | Source business; read for the inventory only. |
| `BRIEF.html` | **REMOVE** | Source planning/spec document (BRIEF.html). | Source business; read for the inventory only. |
| `CLAUDE.md` | **REMOVE** | Source planning/spec document (CLAUDE.md). | Source business; read for the inventory only. |
| `DEPLOY.md` | **REMOVE** | Source planning/spec document (DEPLOY.md). | Source business; read for the inventory only. |
| `FRANCHISE.md` | **REMOVE** | Source planning/spec document (FRANCHISE.md). | Source business; read for the inventory only. |
| `PLAN.md` | **REMOVE** | Source planning/spec document (PLAN.md). | Source business; read for the inventory only. |
| `PLATFORM.md` | **REMOVE** | Source planning/spec document (PLATFORM.md). | Source business; read for the inventory only. |
| `README.md` | **REMOVE** | Source planning/spec document (README.md). | Source business; read for the inventory only. |
| `SPEC.md` | **REMOVE** | Source planning/spec document (SPEC.md). | Source business; read for the inventory only. |
| `consultation/CE-CF-01-online-consultation.html` | **CHANGE** | Online consultation form (hair history, allergies, medical questions). | Questions inform the salon consultation step; the form itself, its code and branding are not copied. Answers are encrypted at rest in the salon build. |
| `docs/ADVERTISING.md` | **REMOVE** | Source operations doc (ADVERTISING). | Source business. |
| `docs/CHARLOTTE-MENTIONS.md` | **REMOVE** | Source operations doc (CHARLOTTE-MENTIONS). | Source business. |
| `docs/CLAIMS-AUDIT.md` | **REMOVE** | Source operations doc (CLAIMS-AUDIT). | Source business. |
| `docs/INSTALL-ON-HER-PHONE.md` | **REMOVE** | Source operations doc (INSTALL-ON-HER-PHONE). | Source business. |
| `docs/ONBOARDING-A-UNIT.md` | **REMOVE** | Source operations doc (ONBOARDING-A-UNIT). | Source business. |
| `docs/REFILL-MEASURE.md` | **REMOVE** | Source operations doc (REFILL-MEASURE). | Source business. |
| `docs/REHEARSAL-AND-DEMO.md` | **REMOVE** | Source operations doc (REHEARSAL-AND-DEMO). | Source business. |
| `docs/SMS-GO-LIVE.md` | **REMOVE** | Source operations doc (SMS-GO-LIVE). | Source business. |
| `docs/privacy-notice-client.md` | **REMOVE** | Source operations doc (privacy-notice-client). | Source business. |
| `docs/privacy-notice-staff.md` | **REMOVE** | Source operations doc (privacy-notice-staff). | Source business. |
| `package.json` | **CHANGE** | `type: module`, Node 24.x pin, no dependencies block. | Target has no package.json and its functions are CommonJS. Zero dependencies is kept. |
| `run.sh` | **REMOVE** | Launches a task prompt. | Source process. |
| `server.js` | **REMOVE** | Local dev server dispatching to the same handlers. | Tests call the handlers directly; the built site is previewed with the target's `preview.py`. |
| `skills-lock.json` | **REMOVE** | Agent skill lock. |  |
| `vercel.json` | **CHANGE** | CSP and security headers, noindex headers for staff paths, three crons, redirect / -> /book/. | Target `vercel.json` is GENERATED by build.py (redirects only). Release 1 adds `X-Robots-Tag: noindex` headers for `/staff/` and `/api/` through the generator; no crons. |

### Task prompts — `prompts/`

| File | Decision | Purpose | What happens in the salon build |
|---|---|---|---|
| `prompts/00-kickoff.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/01-diary-auth.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/01b-chained-travel.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/02-stripe-webhook.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/02b-manual-bookings.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/02c-booking-horizon.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/02d-pricing-and-packages.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/02e-days-off.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/03-balance-payment.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/04-job-lifecycle.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/04b-repeat-bookings.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/05-emails.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/06-stylist-app.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/07-offline-and-calendar.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/08-notifications-and-launch.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/09-go-live.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/10-tenant-config.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/11-identity-and-users.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/12-franchisee-numbers.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/13-employees-in-the-diary.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/14-skills-and-assignment.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/15-employee-app.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/16-network-console.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/17-design-system.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/17b-desktop-shell.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/18-day-states.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/19-map-paint-and-floor.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/20-marks-forks.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/21-dark-console-and-money.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/22-bookable-month.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/BUSINESS-CONTEXT.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/DECIDE-codeonly.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/HANDOVER-COWORK.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/NEW-COWORK-SESSION.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/NEW-SESSION.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/NEXT-COMMAND.txt` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/PASTES.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/PLAN-07sep.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/QUEUE-06sep-afternoon.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/QUEUE-06sep-evening.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/QUEUE-06sep-sms.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/QUEUE-06sep.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/QUEUE-07sep-afternoon.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/QUEUE-07sep-big.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/QUEUE-07sep-housekeeping.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/QUEUE-07sep-long.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/QUEUE-07sep-night.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/QUEUE-07sep-pins.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/QUEUE.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/RELAY.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/RESTART-CODER.txt` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/evidence/ORIENTATION-22sep.md` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/evidence/codeonly-order.mjs` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/evidence/codeonly-scanner.mjs` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
| `prompts/evidence/refill-measure.mjs` | **REMOVE** | Task brief / queue / relay / evidence from the source build. | Source process and history; contains the source business's names. |
