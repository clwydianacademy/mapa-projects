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
  var st = { serviceId: null, under16: null, patch: null, patchEmail: "", reaction: null, who: null,
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
  function money(n) { return "£" + n; }
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
  var ORDER = ["service", "age", "patch", "reaction", "who", "when", "details", "review"];
  function stepsNow() {
    var s = service();
    return ORDER.filter(function (k) {
      if (k === "patch") return s && s.patchProduct;
      if (k === "reaction") return s && s.chemical;
      return true;
    });
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
            return { value: s.id, label: s.name[D.lang],
              detail: lo.price === hi.price ? (lo.price ? money(lo.price) : "") : money(lo.price) + "–" + money(hi.price) };
          }), st.serviceId, function (v) {
            if (v !== st.serviceId) { st.serviceId = v; st.who = null; st.slot = null; st.date = null; st.days = null; st.patch = null; st.reaction = null; if (!service().isPatchTest) st.forProduct = null; }
          }));
        });
        root.appendChild(nav(err, function () {
          if (!st.serviceId) return missing(err, S.service_missing, root.querySelector(".salon-choice"));
          if (service().isPatchTest && !st.forProduct) st.forProduct = Object.keys(cfg.products)[0];
          advance();
        }));
        return h;
      });
    },
    age: function () {
      show("age", function (err) {
        var h = el("h2", { text: S.age_h }); root.appendChild(h);
        root.appendChild(choices([{ value: false, label: S.no }, { value: true, label: S.yes }], st.under16, function (v) { st.under16 = v; st.days = null; st.slot = null; }));
        root.appendChild(nav(err, function () {
          if (st.under16 === null) return missing(err, S.age_missing, root.querySelector(".salon-choice"));
          if (st.under16 && !service().under16) return blocked(S.age_blocked_h, S.age_blocked_p, S.choose_other, function () { go("service"); });
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
        root.appendChild(choices([{ value: true, label: S.patch_yes }, { value: false, label: S.patch_no }], st.patch, function (v) { st.patch = v; emailField.wrap.hidden = v !== true; st.days = null; }));
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
      show("who", function (err) {
        var s = service();
        var h = el("h2", { text: S.who_h }); root.appendChild(h);
        root.appendChild(el("p", { text: S.who_p }));
        var items = s.levels.map(function (l) {
          return { value: l.id, label: levelName(l.id), detail: fill(S.who_detail, { time: dur(l.minutes), price: l.price ? money(l.price) : "" }).replace(/ — $/, ""),
            detail2: l.minutes > l.qualifiedMinutes ? fill(S.who_qualified, { time: dur(l.qualifiedMinutes) }) : "" };
        });
        if (s.levels.length > 1) items.unshift({ value: "any", label: S.who_any, detail: fill(S.who_any_detail, { from: money(s.levels[0].price) }) });
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
                el("b", { text: clock(x.start) }), el("small", { text: fill(S.slot_detail, { start: clock(x.start), end: clock(x.end), level: levelName(x.level), price: x.price ? money(x.price) : S.sum_price + " £0" }) })]);
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
        if (st.under16) {
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
        var s = service(), x = st.slot, lv = s.levels.filter(function (l) { return l.id === x.level; })[0];
        var h = el("h2", { text: x.deposit > 0 ? S.review_h : S.review_h_free }); root.appendChild(h);
        var rows = [[S.sum_service, s.name[D.lang]], [S.sum_who, fill(S.supervised, { level: levelName(x.level) })],
          [S.sum_when, longDate(st.date) + ", " + clock(x.start) + "–" + clock(x.end)],
          [S.sum_length, lv && x.minutes > lv.qualifiedMinutes ? fill(S.length_honest, { time: dur(x.minutes), qualified: dur(lv.qualifiedMinutes) }) : fill(S.length_same, { time: dur(x.minutes) })],
          [S.sum_price, money(x.price)]];
        if (x.deposit > 0) { rows.push([S.sum_deposit, money(x.deposit)]); rows.push([S.sum_balance, money(x.price - x.deposit)]); }
        root.appendChild(el("dl", { class: "salon-summary" }, rows.map(function (r) { return el("div", {}, [el("dt", { text: r[0] }), el("dd", { text: r[1] })]); })));
        if (x.deposit > 0) root.appendChild(el("p", { class: "salon-hint", text: fill(S.pay_note, { minutes: 30 }) }));
        var busy = false;
        root.appendChild(nav(err, function () {
          if (busy) return;                          // a second press does nothing; the button is never disabled
          busy = true;
          var btn = root.querySelector(".salon-row .salon-btn:not(.is-quiet)"), label = btn.textContent;
          btn.textContent = S.paying;
          api("POST", "book", { serviceId: st.serviceId, who: st.who, date: st.date, start: x.start, s: x.s, under16: st.under16, lang: D.lang, forProduct: st.forProduct,
            client: { name: st.name, email: st.email, phone: st.phone }, guardian: st.under16 ? { name: st.guardianName, confirmed: st.guardianOk } : null,
            consultation: s.chemical ? { reaction: st.reaction, notes: st.notes } : null, consent: { terms: st.terms, health: st.health }, website: "" })
            .then(function (r) {
              busy = false; btn.textContent = label;
              if (r.ok && r.checkout) { window.location.assign(r.checkout); return; }
              if (r.ok) return result({ ref: r.ref, status: r.status });
              if (r.code === "unavailable") return closed(r.reason, null);
              err.textContent = r.message || fill(S.error, { email: D.email });
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
  function needPatch() {
    var product = service().patchProduct;
    blocked(S.patch_none_h, fill(S.patch_none_p, { hours: cfg.rules.patchMinHours }), S.patch_book, function () {
      var test = cfg.services.filter(function (s) { return s.isPatchTest; })[0];
      if (!test) return closed("error");
      st.serviceId = test.id; st.forProduct = product; st.who = null; st.slot = null; st.days = null; st.patch = null; st.reaction = null;
      go("who");
    });
  }
  function loadDays(from, then) {
    root.textContent = ""; root.appendChild(el("p", { text: S.loading }));
    var q = "availability?serviceId=" + encodeURIComponent(st.serviceId) + "&who=" + encodeURIComponent(st.who) + "&under16=" + (st.under16 ? "true" : "false")
      + "&guardianConsent=" + (st.under16 ? "true" : "false") + "&lang=" + D.lang + (from ? "&from=" + from : "") + (st.patchEmail ? "&email=" + encodeURIComponent(st.patchEmail) : "");
    api("GET", q).then(function (r) {
      if (!r.ok) {
        if (r.code === "patch-none") return needPatch();
        if (r.code === "unavailable") return closed(r.reason, null);
        return blocked(S.closed_h, r.message || S.error, S.choose_other, function () { go("service"); });
      }
      st.days = r.days; st.next = r.next; st.from = r.from;
      if (!st.date || !r.days.some(function (d) { return d.date === st.date; })) { var first = r.days.filter(function (d) { return d.slots.length; })[0]; st.date = first ? first.date : null; }
      then();
    });
  }
  function go(name) { if (STEPS[name]) STEPS[name](); }

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
