/* Clwydian Academy — the training salon booking journey.
 *
 * One question per screen. The price and the real length of the appointment are on screen before
 * any payment. This script has no words of its own: every string comes from the page
 * (#salon-data, written by website/_src/salon.py), so English and Welsh are the same code.
 *
 * Rules it keeps:
 *   - Continue is NEVER disabled. If something is missing it says what, and puts the cursor there.
 *   - Focus moves to the heading of each new step.
 *   - A choice is a real <button aria-pressed>, and the selected one is marked by more than colour.
 *   - It never says "booked" or "paid" on its own word: the server's answer decides.
 *   - If the engine cannot take bookings, it says so and gives the email address.
 */
(function () {
  "use strict";
  var root = document.getElementById("salon-book");
  var dataEl = document.getElementById("salon-data");
  if (!root || !dataEl) return;
  var D = JSON.parse(dataEl.textContent), S = D.t;
  var API = "/api/salon/";
  var cfg = null;
  var st = { serviceId: null, age: null, answers: {}, addons: [], concession: null, quotes: null, patch: null, patchEmail: "", reaction: null, who: null,
             from: null, days: null, next: null, date: null, slot: null,
             name: "", email: "", phone: "", guardianName: "", guardianOk: false, notes: "", health: false, terms: false, forProduct: null };
  var step = "service";

  // ---- small helpers ---------------------------------------------------------------------------
  function fill(s, o) { return String(s).replace(/\{(\w+)\}/g, function (_, k) { return o && o[k] !== undefined ? o[k] : "{" + k + "}"; }); }
  function el(tag, attrs, kids) {
    var n = document.createElement(tag), k;
    for (k in attrs || {}) {
      if (k === "text") n.textContent = attrs[k];
      else if (k === "on") for (var e in attrs.on) n.addEventListener(e, attrs.on[e]);
      else if (attrs[k] !== null && attrs[k] !== undefined && attrs[k] !== false) n.setAttribute(k, attrs[k] === true ? "" : attrs[k]);
    }
    (kids || []).forEach(function (c) { if (c) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return n;
  }
  function clock(m) { return ("0" + Math.floor(m / 60)).slice(-2) + ":" + ("0" + (m % 60)).slice(-2); }
  function dur(m) {
    var h = Math.floor(m / 60), r = m % 60;
    return !h ? fill(S.minutes, { m: r }) : !r ? fill(S.hours, { h: h }) : fill(S.hours_minutes, { h: h, m: r });
  }
  function money(n) { return "£" + (Math.round(n) === n ? n : Number(n).toFixed(2)); }
  function longDate(iso) { var d = new Date(iso + "T00:00:00Z"); return D.days[d.getUTCDay()] + " " + d.getUTCDate() + " " + D.months[d.getUTCMonth()]; }
  function service() { return cfg.services.filter(function (s) { return s.id === st.serviceId; })[0] || null; }
  function levelName(id) { var l = cfg.levels.filter(function (x) { return x.id === id; })[0]; return l ? l.name[D.lang] : id; }
  function addDays(iso, n) { var d = new Date(iso + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }
  function mailLink() { return el("a", { href: "mailto:" + D.email, text: D.email }); }
  /** A sentence with the email address in it as a real link. */
  function withEmail(text) {
    var p = el("p"), parts = String(text).split("{email}");
    parts.forEach(function (part, i) { p.appendChild(document.createTextNode(part)); if (i < parts.length - 1) p.appendChild(mailLink()); });
    return p;
  }
  function api(method, path, body) {
    return fetch(API + path, { method: method, headers: body ? { "Content-Type": "application/json", Accept: "application/json" } : { Accept: "application/json" },
      body: body ? JSON.stringify(body) : undefined, credentials: "same-origin" })
      .then(function (r) { return r.json().then(function (j) { j.httpStatus = r.status; return j; }); })
      .catch(function () { return { ok: false, code: "unavailable", reason: "error", message: fill(S.error, { email: D.email }) }; });
  }

  // ---- the frame every step is drawn in ------------------------------------------------------------
  function stepsNow() {
    var s = service(), list = ["service", "age"];
    if (s && s.patchProduct) list.push("patch");
    if (s && s.chemical) list.push("reaction");
    if (s) s.questions.forEach(function (q) { list.push("q:" + q); });
    if (s && s.addons.length) list.push("extras");
    if (s && s.concession && st.age === "adult") list.push("concession");
    return list.concat(["who", "when", "details", "review"]);
  }
  /** Anything that changes the price or who can do it throws away what was worked out from it. */
  function stale() { st.quotes = null; st.days = null; st.slot = null; }
  function chooseService(id) {
    st.serviceId = id; st.answers = {}; st.addons = []; st.concession = null; st.who = null; st.date = null; st.patch = null; st.reaction = null; stale();
    if (!service().isPatchTest && !service().isConsultation) st.forProduct = null;
  }
  function choicesQuery() {
    return { serviceId: st.serviceId, answers: st.answers, addons: st.addons, concession: st.concession === true };
  }
  function show(name, build) {
    step = name;
    var list = stepsNow(), n = list.indexOf(name) + 1;
    root.textContent = "";
    if (cfg && cfg.state.placeholders) root.appendChild(el("p", { class: "salon-banner", text: S.placeholder_banner }));
    if (n > 0) root.appendChild(el("p", { class: "salon-step-n", text: fill(S.step, { n: n, of: list.length }) }));
    var err = el("p", { class: "salon-error", role: "alert", id: "salon-err" });
    var h = build(err);
    root.appendChild(err);
    if (h) { h.setAttribute("tabindex", "-1"); h.focus(); }
    window.scrollTo(0, Math.max(0, root.getBoundingClientRect().top + window.pageYOffset - 90));
  }
  function nav(err, onNext, nextLabel) {
    var list = stepsNow(), i = list.indexOf(step);
    return el("div", { class: "salon-row" }, [
      i > 0 ? el("button", { type: "button", class: "salon-btn is-quiet", text: S.back, on: { click: function () { go(list[i - 1]); } } }) : null,
      el("button", { type: "button", class: "salon-btn", text: nextLabel || S.next, on: { click: function () { err.textContent = ""; onNext(); } } }),
    ]);
  }
  function missing(err, text, focusEl) { err.textContent = text; if (focusEl) focusEl.focus(); }
  function advance() { var list = stepsNow(); go(list[list.indexOf(step) + 1]); }
  /** A group of choice buttons; returns the list element. */
  function choices(items, current, onPick) {
    var ul = el("ul", { class: "salon-choices" });
    items.forEach(function (it) {
      var b = el("button", { type: "button", class: "salon-choice", "aria-pressed": String(it.value === current) }, [
        el("b", { text: it.label }), it.detail ? el("small", { text: it.detail }) : null, it.detail2 ? el("small", { text: it.detail2 }) : null]);
      b.addEventListener("click", function () {
        // one answer per screen, even where the choices are drawn in several groups
        Array.prototype.forEach.call(root.querySelectorAll(".salon-choice"), function (x) { x.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", "true"); onPick(it.value);
      });
      ul.appendChild(el("li", {}, [b]));
    });
    return ul;
  }
  function blocked(title, body, buttonLabel, onButton) {
    show("blocked", function () {
      var h = el("h2", { text: title });
      root.appendChild(h); root.appendChild(withEmail(body));
      root.appendChild(el("div", { class: "salon-row" }, [el("button", { type: "button", class: "salon-btn", text: buttonLabel, on: { click: onButton } })]));
      return h;
    });
  }
  function closed(reason, message) {
    root.textContent = "";
    var h = el("h2", { text: S.closed_h, tabindex: "-1" });
    var box = el("div", { class: "salon-notice" }, [h, el("p", { text: message || S.closed_reason[reason] || S.closed_reason.error }), withEmail(S.closed_p)]);
    root.appendChild(box);
  }

  // ---- the steps -------------------------------------------------------------------------------------
  var STEPS = {
    service: function () {
      show("service", function (err) {
        var h = el("h2", { text: S.service_h }); root.appendChild(h);
        Object.keys(cfg.groups).forEach(function (g) {
          var list = cfg.services.filter(function (s) { return s.group === g; });
          if (!list.length) return;
          root.appendChild(el("h3", { text: cfg.groups[g][D.lang] }));
          root.appendChild(choices(list.map(function (s) {
            var lo = s.levels[0], hi = s.levels[s.levels.length - 1];
            return { value: s.id, label: s.name[D.lang], detail2: s.note ? s.note[D.lang] : "",
              detail: !lo ? "" : lo.from === 0 && hi.from === 0 ? "" : fill(S.from_price, { price: money(lo.from) }) };
          }), st.serviceId, function (v) { if (v !== st.serviceId) chooseService(v); }));
        });
        root.appendChild(nav(err, function () {
          if (!st.serviceId) return missing(err, S.service_missing, root.querySelector(".salon-choice"));
          var s = service();
          if (s.isPatchTest && !st.forProduct) st.forProduct = Object.keys(cfg.products)[0];
          if (s.isConsultation && !st.forProduct) { var first = cfg.services.filter(function (x) { return x.consultFirst; })[0]; st.forProduct = first ? "consult:" + first.id : null; }
          if (s.quoteOnly) return needConsult(s.id);            // priced in person: the only thing to book is the consultation
          advance();
        }));
        return h;
      });
    },
    age: function () {
      show("age", function (err) {
        var h = el("h2", { text: S.age_h }); root.appendChild(h);
        root.appendChild(choices([{ value: "adult", label: S.age_adult }, { value: "u16", label: S.age_u16, detail: S.age_guardian }, { value: "u12", label: S.age_u12, detail: S.age_guardian }],
          st.age, function (v) { st.age = v; if (v !== "adult") st.concession = null; stale(); }));
        root.appendChild(nav(err, function () {
          if (!st.age) return missing(err, S.age_missing, root.querySelector(".salon-choice"));
          var s = service(), back = function () { go("service"); };
          if (st.age === "adult" && s.childrenOnly) return blocked(S.age_service_h, S.children_only, S.choose_other, back);
          if (st.age !== "adult" && s.restricted) return blocked(S.age_blocked_h, S.age_blocked_p, S.choose_other, back);
          if (st.age === "u16" && cfg.age.under16.indexOf(s.id) < 0) return blocked(S.age_service_h, S.age_service_u16, S.choose_other, back);
          if (st.age === "u12" && cfg.age.under12.indexOf(s.id) < 0) return blocked(S.age_service_h, S.age_service_u12, S.choose_other, back);
          advance();
        }));
        return h;
      });
    },
    question: function (qid) {
      show("q:" + qid, function (err) {
        var q = cfg.questions[qid], s = service();
        var h = el("h2", { text: q.ask[D.lang] }); root.appendChild(h);
        root.appendChild(choices(q.options.map(function (o) {
          // an answer the lowest level cannot take is still offered — it just needs a more experienced learner
          var low = s.levels.length && o.levels.indexOf(s.levels[0].id) < 0;
          return { value: o.id, label: o.label[D.lang], detail: low ? S.q_l3 : "" };
        }), st.answers[qid], function (v) { st.answers[qid] = v; st.who = null; stale(); }));
        root.appendChild(nav(err, function () {
          if (!st.answers[qid]) return missing(err, S.q_missing, root.querySelector(".salon-choice"));
          advance();
        }));
        return h;
      });
    },
    extras: function () {
      show("extras", function (err) {
        var s = service();
        var h = el("h2", { text: S.extras_h }); root.appendChild(h);
        root.appendChild(el("p", { text: S.extras_p }));
        var ul = el("ul", { class: "salon-choices" });
        s.addons.forEach(function (a) {
          var ps = cfg.levels.map(function (l) { return a.prices[l.id]; }).filter(function (x) { return x !== undefined; });
          var lo = Math.min.apply(null, ps), hi = Math.max.apply(null, ps);
          var needs = s.levels.length && a.prices[s.levels[0].id] === undefined;
          // a tick box in all but name: several may be pressed at once
          var b = el("button", { type: "button", class: "salon-choice is-multi", "aria-pressed": String(st.addons.indexOf(a.id) >= 0) }, [
            el("b", { text: a.name[D.lang] }), el("small", { text: lo === hi ? fill(S.extra_price, { price: money(lo) }) : fill(S.extra_range, { lo: money(lo), hi: money(hi) }) }),
            needs ? el("small", { text: S.extra_from_l3 }) : null]);
          b.addEventListener("click", function () {
            var i = st.addons.indexOf(a.id);
            if (i >= 0) st.addons.splice(i, 1); else st.addons.push(a.id);
            b.setAttribute("aria-pressed", String(i < 0)); st.who = null; stale();
          });
          ul.appendChild(el("li", {}, [b]));
        });
        root.appendChild(ul);
        root.appendChild(nav(err, advance));
        return h;
      });
    },
    concession: function () {
      show("concession", function (err) {
        var c = cfg.concession;
        var h = el("h2", { text: S.conc_h }); root.appendChild(h);
        root.appendChild(el("ul", {}, c.who[D.lang].map(function (w) { return el("li", { text: w }); })));
        root.appendChild(el("p", { text: fill(S.conc_p, { percent: c.percent, days: c.days.map(function (d) { return D.days[["sun", "mon", "tue", "wed", "thu", "fri", "sat"].indexOf(d)]; }).join(", ") }) }));
        root.appendChild(choices([{ value: false, label: S.conc_no }, { value: true, label: S.conc_yes }], st.concession, function (v) { st.concession = v; stale(); }));
        root.appendChild(nav(err, function () {
          if (st.concession === null) return missing(err, S.conc_missing, root.querySelector(".salon-choice"));
          advance();
        }));
        return h;
      });
    },
    patch: function () {
      show("patch", function (err) {
        var s = service(), product = cfg.products[s.patchProduct][D.lang];
        var h = el("h2", { text: fill(S.patch_h, { months: cfg.rules.patchMaxMonths }) }); root.appendChild(h);
        root.appendChild(el("p", { text: fill(S.patch_p, { product: product, hours: cfg.rules.patchMinHours }) }));
        var emailField = field("salon-patch-email", S.patch_email_h, "email", st.patchEmail || st.email, null, "email");
        emailField.wrap.hidden = st.patch !== true;
        root.appendChild(choices([{ value: true, label: S.patch_yes }, { value: false, label: S.patch_no }], st.patch, function (v) { st.patch = v; emailField.wrap.hidden = v !== true; stale(); }));
        root.appendChild(emailField.wrap);
        root.appendChild(nav(err, function () {
          if (st.patch === null) return missing(err, S.patch_missing, root.querySelector(".salon-choice"));
          if (st.patch === false) return needPatch();
          var v = emailField.input.value.trim();
          if (!/^\S+@\S+\.\S+$/.test(v)) { emailField.input.setAttribute("aria-invalid", "true"); return missing(err, S.patch_email_missing, emailField.input); }
          st.patchEmail = v; if (!st.email) st.email = v; st.days = null;
          advance();
        }));
        return h;
      });
    },
    reaction: function () {
      show("reaction", function (err) {
        var h = el("h2", { text: S.reaction_h }); root.appendChild(h);
        root.appendChild(el("p", { class: "salon-hint", text: S.reaction_p }));
        root.appendChild(choices([{ value: false, label: S.no }, { value: true, label: S.yes }], st.reaction, function (v) { st.reaction = v; }));
        root.appendChild(nav(err, function () {
          if (st.reaction === null) return missing(err, S.reaction_missing, root.querySelector(".salon-choice"));
          if (st.reaction) return blocked(S.reaction_blocked_h, S.reaction_blocked_p, S.choose_other, function () { st.reaction = null; go("service"); });
          advance();
        }));
        return h;
      });
    },
    who: function () {
      if (!st.quotes) {
        root.textContent = ""; root.appendChild(el("p", { text: S.loading }));
        return api("POST", "quote", Object.assign({ lang: D.lang }, choicesQuery())).then(function (r) {
          if (!r.ok) return r.code === "unavailable" ? closed(r.reason, null) : blocked(S.closed_h, r.message || S.error, S.choose_other, function () { go("service"); });
          st.quotes = r.levels; STEPS.who();
        });
      }
      show("who", function (err) {
        var h = el("h2", { text: S.who_h }); root.appendChild(h);
        root.appendChild(el("p", { text: S.who_p }));
        var okLevels = st.quotes.filter(function (q) { return q.ok; });
        if (st.quotes.some(function (q) { return q.code === "needs-higher-level"; })) root.appendChild(el("p", { class: "salon-notice", text: S.who_higher }));
        var items = okLevels.map(function (l) {
          return { value: l.level, label: levelName(l.level), detail: fill(S.who_detail, { time: dur(l.minutes), price: l.price ? money(l.price) : "" }).replace(/ — $/, ""),
            detail2: l.minutes > l.qualifiedMinutes ? fill(S.who_qualified, { time: dur(l.qualifiedMinutes) }) : "" };
        });
        if (okLevels.length > 1) items.unshift({ value: "any", label: S.who_any, detail: fill(S.who_any_detail, { from: money(okLevels[0].price) }) });
        if (st.who && st.who !== "any" && !okLevels.some(function (l) { return l.level === st.who; })) st.who = null;
        root.appendChild(choices(items, st.who, function (v) { st.who = v; st.days = null; st.slot = null; }));
        root.appendChild(nav(err, function () {
          if (!st.who) return missing(err, S.who_missing, root.querySelector(".salon-choice"));
          advance();
        }));
        return h;
      });
    },
    when: function () {
      if (!st.days) return loadDays(st.from, function () { STEPS.when(); });
      show("when", function (err) {
        var h = el("h2", { text: S.when_h }); root.appendChild(h);
        root.appendChild(el("p", { text: S.when_p }));
        if (st.next) {
          root.appendChild(el("div", { class: "salon-row" }, [el("button", { type: "button", class: "salon-btn is-quiet",
            text: fill(S.next_available, { when: longDate(st.next.date) + ", " + clock(st.next.start) }),
            on: { click: function () { st.date = st.next.date; if (!st.days.some(function (d) { return d.date === st.next.date; })) { st.days = null; st.from = st.next.date; } st.slot = null; STEPS.when(); } } })]));
        } else { root.appendChild(withEmail(S.none_available)); }
        var strip = el("ul", { class: "salon-days" });
        st.days.forEach(function (d) {
          var dt = new Date(d.date + "T00:00:00Z");
          var b = el("button", { type: "button", class: "salon-day", "aria-pressed": String(d.date === st.date), "data-full": d.fullness }, [
            el("span", { text: D.days[dt.getUTCDay()].replace(/^Dydd /, "").slice(0, 3) }), el("b", { text: dt.getUTCDate() + " " + D.months[dt.getUTCMonth()].slice(0, 3) }), el("em", { text: S[d.fullness] })]);
          b.setAttribute("aria-label", longDate(d.date) + " — " + S[d.fullness]);
          b.addEventListener("click", function () { st.date = d.date; st.slot = null; STEPS.when(); });
          strip.appendChild(el("li", {}, [b]));
        });
        root.appendChild(strip);
        root.appendChild(el("div", { class: "salon-row" }, [
          el("button", { type: "button", class: "salon-btn is-quiet is-small", text: S.earlier, on: { click: function () { loadDays(addDays(st.days[0].date, -cfg.rules.stripDays), STEPS.when); } } }),
          el("button", { type: "button", class: "salon-btn is-quiet is-small", text: S.later, on: { click: function () { loadDays(addDays(st.days[0].date, cfg.rules.stripDays), STEPS.when); } } })]));
        var day = st.days.filter(function (d) { return d.date === st.date; })[0];
        if (day) {
          root.appendChild(el("h3", { text: longDate(day.date), id: "salon-day-h", tabindex: "-1" }));
          if (!day.slots.length) root.appendChild(el("p", { text: day.fullness === "closed" ? S.closed : S.day_full }));
          else ["morning", "afternoon"].forEach(function (period) {
            var list = day.slots.filter(function (x) { return x.period === period; });
            root.appendChild(el("h3", { text: S[period] }));
            if (!list.length) return root.appendChild(el("p", { class: "salon-hint", text: S["no_" + period] }));
            var ul = el("ul", { class: "salon-slots" });
            list.forEach(function (x) {
              var b = el("button", { type: "button", class: "salon-slot", "aria-pressed": String(st.slot && st.slot.start === x.start) }, [
                el("b", { text: clock(x.start) }), el("small", { text: fill(S.slot_detail, { start: clock(x.start), end: clock(x.end), level: levelName(x.level), price: x.price ? money(x.price) + (x.concession ? " (" + S.conc_applied + ")" : "") : S.sum_price + " £0" }) })]);
              b.addEventListener("click", function () {
                st.slot = x;
                Array.prototype.forEach.call(root.querySelectorAll(".salon-slot"), function (o) { o.setAttribute("aria-pressed", "false"); });
                b.setAttribute("aria-pressed", "true");
              });
              ul.appendChild(el("li", {}, [b]));
            });
            root.appendChild(ul);
          });
        }
        root.appendChild(nav(err, function () {
          if (!st.date || !st.slot) return missing(err, S.when_missing, root.querySelector(".salon-slot") || root.querySelector(".salon-day"));
          advance();
        }));
        return day ? root.querySelector("#salon-day-h") : h;
      });
    },
    details: function () {
      show("details", function (err) {
        var s = service();
        var h = el("h2", { text: S.details_h }); root.appendChild(h);
        var name = field("salon-name", S.name, "text", st.name, null, "name");
        var email = field("salon-email", S.email, "email", st.email, S.email_hint, "email");
        var phone = field("salon-phone", S.phone, "tel", st.phone, S.phone_hint, "tel");
        [name, email, phone].forEach(function (f) { root.appendChild(f.wrap); });
        var gName = null, gOk = null, notes = null, health = null;
        if (st.age !== "adult") {
          root.appendChild(el("h3", { text: S.guardian_h }));
          gName = field("salon-guardian", S.guardian_name, "text", st.guardianName, null, "name"); root.appendChild(gName.wrap);
          gOk = check("salon-guardian-ok", S.guardian_confirm, st.guardianOk); root.appendChild(gOk.wrap);
        }
        if (s.chemical) {
          notes = field("salon-notes", S.notes, "textarea", st.notes, S.notes_hint); root.appendChild(notes.wrap);
          health = check("salon-health", S.consent_health, st.health); root.appendChild(health.wrap);
        }
        var terms = check("salon-terms", S.consent_terms, st.terms); root.appendChild(terms.wrap);
        root.appendChild(el("p", {}, [el("a", { href: D.terms, target: "_blank", rel: "noopener", text: S.terms_link })]));
        root.appendChild(nav(err, function () {
          st.name = name.input.value.trim(); st.email = email.input.value.trim(); st.phone = phone.input.value.trim();
          if (gName) { st.guardianName = gName.input.value.trim(); st.guardianOk = gOk.input.checked; }
          if (notes) { st.notes = notes.input.value.trim(); st.health = health.input.checked; }
          st.terms = terms.input.checked;
          [name, email].forEach(function (f) { f.input.removeAttribute("aria-invalid"); });
          if (st.name.length < 2) { name.input.setAttribute("aria-invalid", "true"); return missing(err, S.missing_name, name.input); }
          if (!/^\S+@\S+\.\S+$/.test(st.email)) { email.input.setAttribute("aria-invalid", "true"); return missing(err, S.missing_email, email.input); }
          if (gName && (st.guardianName.length < 2 || !st.guardianOk)) return missing(err, S.missing_guardian, st.guardianName.length < 2 ? gName.input : gOk.input);
          if (health && !st.health) return missing(err, S.missing_health, health.input);
          if (!st.terms) return missing(err, S.missing_terms, terms.input);
          advance();
        }));
        return h;
      });
    },
    review: function () {
      show("review", function (err) {
        var s = service(), x = st.slot;
        var h = el("h2", { text: x.deposit > 0 ? S.review_h : S.review_h_free }); root.appendChild(h);
        var rows = [[S.sum_service, s.name[D.lang]], [S.sum_who, fill(S.supervised, { level: levelName(x.level) })],
          [S.sum_when, longDate(st.date) + ", " + clock(x.start) + "–" + clock(x.end)],
          [S.sum_length, x.minutes > x.qualifiedMinutes ? fill(S.length_honest, { time: dur(x.minutes), qualified: dur(x.qualifiedMinutes) }) : fill(S.length_same, { time: dur(x.minutes) })]];
        if (st.addons.length) rows.push([S.sum_extras, s.addons.filter(function (a) { return st.addons.indexOf(a.id) >= 0; }).map(function (a) { return a.name[D.lang]; }).join(", ")]);
        rows.push([S.sum_price, money(x.price) + (x.concession ? " (" + S.conc_applied + ")" : "")]);
        if (st.concession && !x.concession) rows.push([S.conc_h, S.conc_not_today]);
        if (x.deposit > 0) { rows.push([S.sum_deposit, money(x.deposit)]); rows.push([S.sum_balance, money(x.price - x.deposit)]); }
        root.appendChild(el("dl", { class: "salon-summary" }, rows.map(function (r) { return el("div", {}, [el("dt", { text: r[0] }), el("dd", { text: r[1] })]); })));
        if (x.deposit > 0) root.appendChild(el("p", { class: "salon-hint", text: fill(S.pay_note, { minutes: 30 }) }));
        var busy = false;
        root.appendChild(nav(err, function () {
          if (busy) return;                          // a second press does nothing; the button is never disabled
          busy = true;
          var btn = root.querySelector(".salon-row .salon-btn:not(.is-quiet)"), label = btn.textContent;
          btn.textContent = S.paying;
          api("POST", "book", { serviceId: st.serviceId, who: st.who, date: st.date, start: x.start, s: x.s, age: st.age, lang: D.lang, forProduct: st.forProduct,
            answers: st.answers, addons: st.addons, concession: st.concession === true,
            client: { name: st.name, email: st.email, phone: st.phone }, guardian: st.age !== "adult" ? { name: st.guardianName, confirmed: st.guardianOk } : null,
            consultation: s.chemical ? { reaction: st.reaction, notes: st.notes } : null, consent: { terms: st.terms, health: st.health }, website: "" })
            .then(function (r) {
              busy = false; btn.textContent = label;
              if (r.ok && r.checkout) { window.location.assign(r.checkout); return; }
              if (r.ok) return result({ ref: r.ref, status: r.status });
              if (r.code === "unavailable") return closed(r.reason, null);
              err.textContent = r.message || fill(S.error, { email: D.email });
              if (r.code === "consultation-first") return needConsult(st.serviceId);
              if (r.httpStatus === 409) { st.days = null; st.slot = null; }      // the slot went: availability must be read again
              err.setAttribute("tabindex", "-1"); err.focus();
            });
        }, x.deposit > 0 ? fill(S.pay, { amount: money(x.deposit) }) : S.confirm));
        return h;
      });
    },
  };

  function field(id, label, type, value, hint, autocomplete) {
    var input = type === "textarea" ? el("textarea", { id: id, rows: "3" }) : el("input", { id: id, type: type, autocomplete: autocomplete || null });
    input.value = value || "";
    if (hint) input.setAttribute("aria-describedby", id + "-hint");
    var wrap = el("div", { class: "salon-field" }, [el("label", { for: id, text: label }), input, hint ? el("span", { class: "salon-hint", id: id + "-hint", text: hint }) : null]);
    return { wrap: wrap, input: input };
  }
  function check(id, label, checked) {
    var input = el("input", { id: id, type: "checkbox" }); input.checked = Boolean(checked);
    return { wrap: el("div", { class: "salon-check" }, [input, el("label", { for: id, text: label })]), input: input };
  }
  function switchTo(test, forProduct) {
    if (!test) return closed("error");
    chooseService(test.id); st.forProduct = forProduct;
    go(st.age ? "who" : "age");
  }
  function needPatch() {
    var product = service().patchProduct;
    blocked(S.patch_none_h, fill(S.patch_none_p, { hours: cfg.rules.patchMinHours }), S.patch_book, function () {
      switchTo(cfg.services.filter(function (s) { return s.isPatchTest; })[0], product);
    });
  }
  function needConsult(serviceId) {
    blocked(S.consult_h, S.consult_p, S.consult_book, function () {
      switchTo(cfg.services.filter(function (s) { return s.isConsultation; })[0], "consult:" + serviceId);
    });
  }
  function loadDays(from, then) {
    root.textContent = ""; root.appendChild(el("p", { text: S.loading }));
    var guardian = st.age !== "adult";
    var q = "availability?serviceId=" + encodeURIComponent(st.serviceId) + "&who=" + encodeURIComponent(st.who) + "&age=" + st.age
      + "&guardianConsent=" + (guardian ? "true" : "false") + "&lang=" + D.lang + (from ? "&from=" + from : "") + (st.patchEmail ? "&email=" + encodeURIComponent(st.patchEmail) : "")
      + "&answers=" + encodeURIComponent(JSON.stringify(st.answers)) + "&addons=" + encodeURIComponent(st.addons.join(",")) + "&concession=" + (st.concession === true ? "true" : "false");
    api("GET", q).then(function (r) {
      if (!r.ok) {
        if (r.code === "patch-none") return needPatch();
        if (r.code === "consultation-first" || r.code === "quote-only") return needConsult(st.serviceId);
        if (r.code === "unavailable") return closed(r.reason, null);
        return blocked(S.closed_h, r.message || S.error, S.choose_other, function () { go("service"); });
      }
      st.days = r.days; st.next = r.next; st.from = r.from;
      if (!st.date || !r.days.some(function (d) { return d.date === st.date; })) { var first = r.days.filter(function (d) { return d.slots.length; })[0]; st.date = first ? first.date : null; }
      then();
    });
  }
  function go(name) { if (/^q:/.test(name)) STEPS.question(name.slice(2)); else if (STEPS[name]) STEPS[name](); }

  // ---- coming back from the payment page -------------------------------------------------------------
  function result(r, tries) {
    root.textContent = "";
    var again = el("div", { class: "salon-row" }, [el("a", { class: "salon-btn is-quiet", href: D.book, text: S.start_again })]);
    var h;
    if (r.status === "confirmed") {
      h = el("h2", { text: S.done_h, tabindex: "-1" }); root.appendChild(el("div", { class: "salon-notice" }, [h, el("p", { text: fill(S.done_p, { ref: r.ref }) })]));
    } else if (r.status === "held") {
      h = el("h2", { text: S.held_h, tabindex: "-1" }); root.appendChild(h); root.appendChild(el("p", { text: fill(S.held_p, { ref: r.ref }) }));
      if ((tries || 0) < 20) setTimeout(function () { lookup(r.ref, (tries || 0) + 1); }, 3000);
    } else {
      h = el("h2", { text: S.expired_h, tabindex: "-1" }); root.appendChild(h); root.appendChild(el("p", { text: S.expired_p })); root.appendChild(again);
    }
    if (!tries) h.focus();
  }
  function lookup(ref, tries) {
    api("GET", "book?ref=" + encodeURIComponent(ref) + "&lang=" + D.lang).then(function (r) {
      if (r.ok) return result(r, tries);
      root.textContent = ""; root.appendChild(withEmail(S.unknown_ref));
    });
  }

  // ---- start -------------------------------------------------------------------------------------------
  root.appendChild(el("p", { text: S.loading }));
  var params = new URLSearchParams(window.location.search), ref = params.get("ref");
  if (ref && /^CAS-[0-9A-F]{8}$/.test(ref)) {
    if (params.get("back") === "cancelled") {
      root.textContent = "";
      var hc = el("h2", { text: S.cancelled_h, tabindex: "-1" });
      root.appendChild(hc); root.appendChild(el("p", { text: S.cancelled_p }));
      root.appendChild(el("div", { class: "salon-row" }, [el("a", { class: "salon-btn", href: D.book, text: S.start_again })]));
      hc.focus();
    } else lookup(ref, 0);
    return;
  }
  api("GET", "quote").then(function (r) {
    if (!r.ok || !r.state) return closed("error");
    cfg = r;
    if (!r.state.open) return closed(r.state.reason);
    var want = params.get("service");
    if (want && cfg.services.some(function (s) { return s.id === want; })) st.serviceId = want;
    STEPS.service();
  });
})();
