/* Clwydian Academy — the training salon's staff day sheet (/staff/).
 *
 * Sign in with the staff password; the session is an HttpOnly cookie this script cannot read.
 * The day is a LIST grouped by learner. Every change goes through a dialog — status, move,
 * resize — and is sent with the booking's version number, so a change made on a stale screen is
 * refused by the server rather than overwriting somebody else's. A move or a resize is checked
 * by the same rule that offers slots to clients; if it is refused, the reason is shown.
 * No drag and drop in this release.
 */
(function () {
  "use strict";
  var root = document.getElementById("salon-staff");
  if (!root) return;
  var API = "/api/salon/staff";
  var day = null, date = null;
  var STATUS = { held: "Awaiting deposit", confirmed: "Confirmed", arrived: "Arrived", in_progress: "In progress", completed: "Completed", no_show: "Did not arrive", cancelled: "Cancelled" };
  var DO = { arrived: "Mark arrived", in_progress: "Start", completed: "Complete", no_show: "Did not arrive", cancelled: "Cancel booking", confirmed: "Undo — back to confirmed" };
  var DAYS = [["mon", "Mon"], ["tue", "Tue"], ["wed", "Wed"], ["thu", "Thu"], ["fri", "Fri"], ["sat", "Sat"], ["sun", "Sun"]];

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
  function toMinutes(s) { var m = /^(\d{1,2}):(\d{2})$/.exec(s || ""); return m ? Number(m[1]) * 60 + Number(m[2]) : NaN; }
  function addDays(iso, n) { var d = new Date(iso + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }
  function longDate(iso) { return new Date(iso + "T00:00:00Z").toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }); }
  function call(body) {
    return fetch(API, { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, credentials: "same-origin", body: JSON.stringify(body) })
      .then(function (r) { return r.json().then(function (j) { j.httpStatus = r.status; return j; }); })
      .catch(function () { return { ok: false, code: "network", message: "Could not reach the server. Check the connection and try again." }; });
  }
  function field(id, label, type, value, extra) {
    var input = type === "select" ? el("select", { id: id }) : el("input", Object.assign({ id: id, type: type }, extra || {}));
    if (type !== "select") input.value = value === undefined || value === null ? "" : value;
    return { input: input, wrap: el("div", { class: "salon-field" }, [el("label", { for: id, text: label }), input]) };
  }
  function options(select, list, current) {
    list.forEach(function (o) { var op = el("option", { value: o[0], text: o[1] }); if (o[0] === current) op.selected = true; select.appendChild(op); });
  }
  function nameOf(list, id) { var x = list.filter(function (s) { return s.id === id; })[0]; return x ? x.name : id; }

  /** A modal dialog with a heading, a body, an error line and two buttons. `onOk(err)` returns a
   *  promise of the server's answer; the dialog closes only if the answer is ok. */
  function dialog(title, body, okLabel, onOk, danger) {
    var err = el("p", { class: "salon-error", role: "alert" });
    var d = el("dialog", { class: "salon-dialog", "aria-labelledby": "salon-dlg-h" });
    var ok = okLabel ? el("button", { type: "button", class: "salon-btn" + (danger ? " is-danger" : ""), text: okLabel }) : null;
    var close = el("button", { type: "button", class: "salon-btn is-quiet", text: okLabel ? "Cancel" : "Close", on: { click: function () { d.close(); } } });
    d.appendChild(el("h2", { id: "salon-dlg-h", text: title }));
    body.forEach(function (n) { d.appendChild(n); });
    d.appendChild(err);
    d.appendChild(el("div", { class: "salon-row" }, [ok, close]));
    d.addEventListener("close", function () { d.remove(); });
    if (ok) ok.addEventListener("click", function () {
      err.textContent = "";
      var p = onOk(err);
      if (!p) return;
      ok.textContent = "One moment…";
      p.then(function (r) {
        ok.textContent = okLabel;
        if (r.ok) { d.close(); load(date); return; }
        if (r.httpStatus === 401) { d.close(); return signIn("Your session has ended. Please sign in again."); }
        err.textContent = r.message || "That did not work.";
        if (r.code === "stale") load(date, true);
      });
    });
    document.body.appendChild(d);
    d.showModal();
    return d;
  }

  // ---- sign in -----------------------------------------------------------------------------------
  function signIn(message) {
    root.textContent = "";
    var pw = field("staff-pw", "Staff password", "password", "", { autocomplete: "current-password" });
    var err = el("p", { class: "salon-error", role: "alert", text: message || "" });
    var go = el("button", { type: "button", class: "salon-btn", text: "Sign in" });
    function submit() {
      err.textContent = "";
      if (!pw.input.value) { err.textContent = "Enter the staff password."; pw.input.focus(); return; }
      call({ action: "login", password: pw.input.value }).then(function (r) {
        if (r.ok) return load(null);
        err.textContent = r.code === "unavailable" ? "The day sheet is not set up yet (" + (r.reason || "unavailable") + "). " + (r.message || "")
          : r.httpStatus === 429 ? "Too many wrong attempts. Wait fifteen minutes and try again." : "That password is not right.";
        pw.input.focus();
      });
    }
    go.addEventListener("click", submit);
    pw.input.addEventListener("keydown", function (e) { if (e.key === "Enter") submit(); });
    root.appendChild(el("div", { style: "max-width:26rem" }, [pw.wrap, el("div", { class: "salon-row" }, [go]), err]));
    pw.input.focus();
  }

  // ---- the day -------------------------------------------------------------------------------------
  function load(d, quiet) {
    if (!quiet) { root.textContent = ""; root.appendChild(el("p", { text: "Loading…" })); }
    call({ action: "day", date: d || undefined }).then(function (r) {
      if (r.httpStatus === 401) return signIn("");
      if (!r.ok) {
        var why = { "no-staff-password": "the staff password has not been set", "no-store": "the booking database is not connected", "store-error": "the booking database did not answer" }[r.reason] || r.reason || "unavailable";
        root.textContent = ""; root.appendChild(el("p", { class: "salon-error", text: "The day sheet is not set up yet: " + why + "." })); return;
      }
      day = r; date = r.date; draw();
    });
  }
  function serviceName(id) { return nameOf(day.services, id); }
  function levelName(id) { return nameOf(day.levels, id); }

  function draw() {
    root.textContent = "";
    var pick = field("staff-date", "Date", "date", date);
    pick.input.addEventListener("change", function () { if (pick.input.value) load(pick.input.value); });
    root.appendChild(el("div", { class: "salon-toolbar" }, [
      el("button", { type: "button", class: "salon-btn is-quiet is-small", text: "← Previous day", on: { click: function () { load(addDays(date, -1)); } } }),
      pick.wrap,
      el("button", { type: "button", class: "salon-btn is-quiet is-small", text: "Next day →", on: { click: function () { load(addDays(date, 1)); } } }),
      el("button", { type: "button", class: "salon-btn is-quiet is-small", text: "Today", on: { click: function () { load(day.today); } } }),
      el("button", { type: "button", class: "salon-btn is-quiet is-small", text: "Learners", on: { click: roster } }),
      el("button", { type: "button", class: "salon-btn is-quiet is-small", text: "Record a patch test", on: { click: patchDialog } }),
      el("button", { type: "button", class: "salon-btn is-quiet is-small", text: "Model register", on: { click: modelsDialog } }),
      el("button", { type: "button", class: "salon-btn is-quiet is-small", text: "Sign out", on: { click: function () { call({ action: "logout" }).then(function () { signIn(""); }); } } }),
    ]));
    root.appendChild(el("h2", { text: longDate(date), tabindex: "-1", id: "staff-day-h" }));
    var live = day.bookings.filter(function (b) { return ["cancelled"].indexOf(b.status) < 0; });
    root.appendChild(el("p", { class: "salon-hint", text: live.length + (live.length === 1 ? " appointment" : " appointments") + (day.encryption ? "" : " · consultation answers cannot be opened: the encryption key is not set") }));
    if (!day.students.length) root.appendChild(el("p", { class: "salon-notice", text: "No learners have been added yet, so nothing can be booked. Use “Learners” to add them." }));
    var groups = day.students.map(function (s) { return { id: s.id, title: s.name, sub: levelName(s.level) + (s.active === false ? " · not active" : "") }; });
    day.bookings.forEach(function (b) { if (!groups.some(function (g) { return g.id === b.studentId; })) groups.push({ id: b.studentId, title: "Learner no longer on the list", sub: "" }); });
    groups.forEach(function (g) {
      var list = day.bookings.filter(function (b) { return b.studentId === g.id; });
      var sec = el("section", { class: "salon-group" }, [el("h2", {}, [g.title + " ", el("small", { text: g.sub })])]);
      if (!list.length) sec.appendChild(el("p", { class: "salon-empty", text: "Nothing booked." }));
      list.forEach(function (b) { sec.appendChild(card(b)); });
      root.appendChild(sec);
    });
  }

  function card(b) {
    var flags = [];
    if (b.deposit > 0) flags.push([b.depositPaid ? "Deposit £" + b.deposit + " paid" : "Deposit £" + b.deposit + " NOT paid", !b.depositPaid]);
    if (b.needsRefund) flags.push(["Paid after the slot was released — refund needed", true]);
    if (b.under16) flags.push(["Under 16 · guardian: " + (b.guardian || "none recorded"), !b.guardian]);
    if (b.patchProduct) flags.push(["Patch test on record: " + b.patchProduct, false]);
    if (b.patchFor) flags.push(["Patch test for: " + b.patchFor, false]);
    var actions = b.next.map(function (to) {
      return el("button", { type: "button", class: "salon-btn is-small" + (to === "cancelled" || to === "no_show" ? " is-danger" : ""), text: DO[to] || to, on: { click: function () { statusDialog(b, to); } } });
    });
    if (["held", "confirmed", "arrived", "in_progress"].indexOf(b.status) >= 0) {
      actions.push(el("button", { type: "button", class: "salon-btn is-quiet is-small", text: "Move", on: { click: function () { moveDialog(b); } } }));
      actions.push(el("button", { type: "button", class: "salon-btn is-quiet is-small", text: "Change length", on: { click: function () { resizeDialog(b); } } }));
    }
    if (b.hasConsultation) actions.push(el("button", { type: "button", class: "salon-btn is-quiet is-small", text: "Consultation answers", on: { click: function () { consultation(b); } } }));
    var contact = [b.client.email, b.client.phone].filter(Boolean).join(" · ");
    return el("article", { class: "salon-card", "data-status": b.status }, [
      el("h3", {}, [clock(b.start) + "–" + clock(b.end) + " · " + serviceName(b.serviceId), el("span", { class: "salon-status", text: STATUS[b.status] || b.status })]),
      el("p", {}, [el("strong", { text: b.client.name }), " · " + contact]),
      el("p", { class: "salon-hint", text: b.id + " · £" + b.price + " · " + b.minutes + " min (" + b.segments.map(function (s) { return s.kind + " " + s.minutes; }).join(", ") + ")" }),
      flags.length ? el("ul", { class: "salon-flags" }, flags.map(function (f) { return el("li", { class: f[1] ? "is-warn" : null, text: f[0] }); })) : null,
      el("div", { class: "salon-row", style: "margin-top:0.6rem" }, actions),
    ]);
  }

  // ---- dialogs --------------------------------------------------------------------------------------
  function statusDialog(b, to) {
    var text = { cancelled: "Cancel this booking? The time becomes free. A deposit already paid is NOT refunded automatically.",
      no_show: "Record that the client did not arrive?", completed: b.patchFor ? "Complete this patch test? This records the test, dated now, for the client's email address." : "Mark this appointment completed?" }[to]
      || "Change this booking to “" + (STATUS[to] || to) + "”?";
    dialog((DO[to] || to) + " — " + b.client.name, [el("p", { text: clock(b.start) + " · " + serviceName(b.serviceId) }), el("p", { text: text })], DO[to] || "Confirm",
      function () { return call({ action: "status", id: b.id, v: b.v, status: to }); }, to === "cancelled" || to === "no_show");
  }
  function moveDialog(b) {
    var d = field("mv-date", "Date", "date", b.date), t = field("mv-time", "Start time", "time", clock(b.start), { step: "300" });
    var who = field("mv-who", "Learner (same level only)", "select");
    options(who.input, day.students.filter(function (s) { return s.level === b.level && s.active !== false; }).map(function (s) { return [s.id, s.name]; }), b.studentId);
    dialog("Move — " + b.client.name, [el("p", { text: serviceName(b.serviceId) + ", " + b.minutes + " minutes, " + levelName(b.level) }), d.wrap, t.wrap, who.wrap,
      el("p", { class: "salon-hint", text: "The move is checked against opening times, the learner, chairs, basins, supervisor checks and the patch-test window. Tell the client: no message is sent." })],
      "Move", function (err) {
        var start = toMinutes(t.input.value);
        if (!d.input.value || isNaN(start)) { err.textContent = "Choose a date and a start time."; return null; }
        if (start % 5) { err.textContent = "Start times are in steps of five minutes."; t.input.focus(); return null; }
        return call({ action: "move", id: b.id, v: b.v, toDate: d.input.value, toStart: start, toStudent: who.input.value });
      });
  }
  function resizeDialog(b) {
    var m = field("rs-min", "Total length in minutes", "number", b.minutes, { step: "5", min: "5" });
    dialog("Change length — " + b.client.name, [el("p", { text: "Now " + clock(b.start) + "–" + clock(b.end) + " (" + b.minutes + " minutes). The change is made to the last working part of the appointment." }), m.wrap],
      "Change length", function (err) {
        var n = Number(m.input.value);
        if (!n || n % 5) { err.textContent = "Enter a length in steps of five minutes."; m.input.focus(); return null; }
        return call({ action: "resize", id: b.id, v: b.v, minutes: n });
      });
  }
  function consultation(b) {
    call({ action: "consultation", id: b.id }).then(function (r) {
      var c = r.consultation || {};
      dialog("Consultation answers — " + b.client.name, r.ok
        ? [el("p", {}, [el("strong", { text: "Previous reaction: " }), c.reaction ? "Yes" : "No"]), el("p", {}, [el("strong", { text: "Allergies, skin or scalp: " }), c.notes || "Nothing given"]),
           el("p", { class: "salon-hint", text: "Health information, given with the client's consent. This look has been logged on the booking." })]
        : [el("p", { class: "salon-error", text: r.message || "Could not open the answers." })], null);
      if (r.ok) load(date, true);
    });
  }
  function patchDialog() {
    var e = field("pt-email", "Client's email address", "email", ""), p = field("pt-product", "Product", "select"), d = field("pt-date", "Date of the test", "date", day.today, { max: day.today });
    options(p.input, day.products.map(function (x) { return [x, x]; }));
    dialog("Record a patch test", [el("p", { class: "salon-hint", text: "For a test done in the salon that was not booked as a patch-test appointment. A booked one is recorded when you complete it." }), e.wrap, p.wrap, d.wrap],
      "Record", function (err) {
        if (!/^\S+@\S+\.\S+$/.test(e.input.value.trim()) || !d.input.value) { err.textContent = "Enter the client's email address and the date of the test."; return null; }
        return call({ action: "patch-add", email: e.input.value.trim(), product: p.input.value, testedOn: d.input.value });
      });
  }
  function modelsDialog() {
    call({ action: "models" }).then(function (r) {
      var rows = (r.models || []).slice().reverse().map(function (m) { return el("p", {}, [el("strong", { text: m.name }), " · " + m.email + " · " + (m.interests.join(", ") || "anything") + (m.days ? " · " + m.days : "")]); });
      dialog("Model register (" + rows.length + ")", rows.length ? rows : [el("p", { text: r.ok ? "Nobody has joined yet." : (r.message || "Unavailable.") })], null);
    });
  }
  function roster() {
    var list = day.students.map(function (s) { return JSON.parse(JSON.stringify(s)); });
    var box = el("div");
    function row(s, i) {
      var n = field("ro-name-" + i, "Name", "text", s.name), l = field("ro-level-" + i, "Level", "select");
      options(l.input, day.levels.map(function (x) { return [x.id, x.name]; }), s.level);
      n.input.addEventListener("input", function () { s.name = n.input.value; });
      l.input.addEventListener("change", function () { s.level = l.input.value; });
      var act = el("input", { type: "checkbox", id: "ro-act-" + i }); act.checked = s.active !== false;
      act.addEventListener("change", function () { s.active = act.checked; });
      var daysBox = el("div", { class: "salon-row", style: "margin-top:0.3rem" }, DAYS.map(function (d) {
        var c = el("input", { type: "checkbox", id: "ro-" + i + "-" + d[0] }); c.checked = !s.days || s.days.indexOf(d[0]) >= 0;
        c.addEventListener("change", function () { s.days = DAYS.map(function (x) { return x[0]; }).filter(function (k) { return box.querySelector("#ro-" + i + "-" + k).checked; }); });
        return el("label", { for: "ro-" + i + "-" + d[0], style: "display:inline-flex;gap:0.3rem;align-items:center;min-height:44px" }, [c, d[1]]);
      }));
      return el("div", { style: "border-bottom:1px solid var(--line);padding-bottom:0.8rem" }, [
        el("div", { class: "salon-roster" }, [n.wrap, l.wrap, el("label", { for: "ro-act-" + i, style: "display:inline-flex;gap:0.4rem;align-items:center;min-height:54px" }, [act, "Active"])]), daysBox]);
    }
    function redraw() { box.textContent = ""; list.forEach(function (s, i) { box.appendChild(row(s, i)); }); }
    redraw();
    var add = el("button", { type: "button", class: "salon-btn is-quiet is-small", text: "Add a learner", on: { click: function () { list.push({ name: "", level: day.levels[0].id, days: ["mon", "tue", "wed", "thu", "fri"], active: true }); redraw(); } } });
    dialog("Learners", [el("p", { class: "salon-hint", text: "Names are shown on this day sheet only — never on the public site. To remove a learner, untick Active." }), box, el("div", { class: "salon-row" }, [add])],
      "Save learners", function (err) {
        if (list.some(function (s) { return !String(s.name || "").trim(); })) { err.textContent = "Every learner needs a name."; return null; }
        return call({ action: "students-save", v: day.studentsV, list: list });
      });
  }

  load(null);
})();
