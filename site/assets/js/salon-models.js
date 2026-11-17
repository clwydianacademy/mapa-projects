/* Clwydian Academy — the training salon's model register form.
 * Drawn by script so that, without JavaScript, the page shows the email address instead of a form
 * that cannot send. Every string comes from the page (#salon-data). The button is never disabled:
 * it says what is missing and puts the cursor there. */
(function () {
  "use strict";
  var root = document.getElementById("salon-models"), dataEl = document.getElementById("salon-data");
  if (!root || !dataEl) return;
  var D = JSON.parse(dataEl.textContent), S = D.t;
  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    for (var k in attrs || {}) { if (k === "text") n.textContent = attrs[k]; else if (attrs[k] !== null && attrs[k] !== false) n.setAttribute(k, attrs[k]); }
    (kids || []).forEach(function (c) { if (c) n.appendChild(c); });
    return n;
  }
  function field(id, label, type, auto) {
    var input = el("input", { id: id, type: type, autocomplete: auto || null });
    return { input: input, wrap: el("div", { class: "salon-field" }, [el("label", { for: id, text: label }), input]) };
  }
  function check(id, label, value) {
    var input = el("input", { id: id, type: "checkbox", value: value || null });
    return { input: input, wrap: el("div", { class: "salon-check" }, [input, el("label", { for: id, text: label })]) };
  }
  var name = field("model-name", S.name, "text", "name"), email = field("model-email", S.email, "email", "email"), days = field("model-days", S.days, "text");
  var interests = Object.keys(D.groups).map(function (g) { return check("model-int-" + g, D.groups[g], g); });
  var consent = check("model-consent", S.consent);
  var err = el("p", { class: "salon-error", role: "alert" });
  var send = el("button", { type: "button", class: "salon-btn", text: S.send });
  var group = el("fieldset", { style: "border:0;padding:0;margin:1rem 0 0" }, [el("legend", { text: S.interests, style: "font-weight:600" })].concat(interests.map(function (i) { return i.wrap; })));
  [name.wrap, email.wrap, group, days.wrap, consent.wrap, el("div", { class: "salon-row" }, [send]), err].forEach(function (n) { root.appendChild(n); });
  var busy = false;
  function fail(text, focus) { err.textContent = text; if (focus) focus.focus(); }
  function mailFail() {
    err.textContent = "";
    S.error.split("{email}").forEach(function (part, i, all) {
      err.appendChild(document.createTextNode(part));
      if (i < all.length - 1) err.appendChild(el("a", { href: "mailto:" + D.email, text: D.email }));
    });
  }
  send.addEventListener("click", function () {
    if (busy) return;
    err.textContent = "";
    if (name.input.value.trim().length < 2) return fail(S.missing_name, name.input);
    if (!/^\S+@\S+\.\S+$/.test(email.input.value.trim())) return fail(S.missing_email, email.input);
    if (!consent.input.checked) return fail(S.missing_consent, consent.input);
    busy = true; send.textContent = S.sending;
    fetch("/api/salon/models", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, credentials: "same-origin",
      body: JSON.stringify({ name: name.input.value.trim(), email: email.input.value.trim(), days: days.input.value.trim(), lang: D.lang, consent: true, website: "",
        interests: interests.filter(function (i) { return i.input.checked; }).map(function (i) { return i.input.value; }) }) })
      .then(function (r) { return r.json(); })
      .then(function (r) {
        busy = false; send.textContent = S.send;
        if (!r.ok) return r.code === "details" || r.code === "consent-terms" || r.code === "rate" ? fail(r.message) : mailFail();
        root.textContent = "";
        var h = el("h2", { text: S.done_h, tabindex: "-1" });
        root.appendChild(el("div", { class: "salon-notice" }, [h, el("p", { text: S.done_p })]));
        h.focus();
      })
      .catch(function () { busy = false; send.textContent = S.send; mailFail(); });
  });
})();
