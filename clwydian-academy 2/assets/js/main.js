/* Clwydian Academy — progressive enhancement (no dependencies) */
(function () {
  "use strict";

  // Sticky header state
  var header = document.querySelector(".site-header");
  var onScroll = function () {
    if (header) header.classList.toggle("is-scrolled", window.scrollY > 8);
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  // Mobile navigation
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  // Scroll reveals
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            en.target.classList.add("is-in");
            io.unobserve(en.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
    );
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("is-in"); });
  }

  // Enquiry form — progressive enhancement over a plain POST to /api/enquiry.
  // Without JavaScript the browser posts the form and follows the redirect; with it we post in
  // the background and show the result inline. Also stamps the time-to-submit check, preselects
  // the enquiry type from ?enquiry=, and surfaces ?error= after a no-JS round trip.
  var form = document.getElementById("interest-form");
  if (form) {
    var cy = (document.documentElement.lang || "").indexOf("cy") === 0;
    var stamp = form.querySelector('[name="ts"]');
    if (stamp) stamp.value = String(Date.now());
    var params = new URLSearchParams(window.location.search);
    var pre = params.get("enquiry");
    var sel = form.querySelector('[name="enquiry"]');
    if (pre && sel && sel.querySelector('option[value="' + pre + '"]')) sel.value = pre;
    var errBox = document.getElementById("form-error");
    var okBox = document.getElementById("form-ok");
    var say = function (box, text) {
      if (!box) return;
      if (text) box.textContent = text;
      box.hidden = false;
      box.setAttribute("tabindex", "-1");
      box.focus();
    };
    var messages = {
      rate: cy ? "Gormod o ymholiadau o'r cyfeiriad hwn — rhowch gynnig arall mewn ychydig funudau." : "Too many enquiries from this address — please try again in a few minutes.",
      config: cy ? "Nid yw'r ffurflen wedi'i chysylltu eto. E-bostiwch ni'n uniongyrchol." : "The form is not connected yet. Please email us directly.",
      send: cy ? "Ni allem anfon eich ymholiad. Rhowch gynnig arall, neu e-bostiwch ni." : "We could not send your enquiry. Please try again, or email us.",
      fields: cy ? "Gwiriwch y meysydd sydd wedi'u marcio a rhowch gynnig arall." : "Please check the highlighted fields and try again.",
    };
    if (params.get("error")) say(errBox, messages[params.get("error")] || messages.fields);
    if (window.fetch && window.FormData) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var btn = form.querySelector('button[type="submit"]');
        if (btn) btn.disabled = true;
        if (errBox) errBox.hidden = true;
        fetch(form.action, { method: "POST", body: new FormData(form), headers: { Accept: "application/json" } })
          .then(function (r) { return r.json().then(function (j) { return { status: r.status, body: j }; }); })
          .then(function (r) {
            if (r.body && r.body.ok) {
              form.reset();
              if (stamp) stamp.value = String(Date.now());
              say(okBox);
            } else {
              var code = (r.body && r.body.error) || "fields";
              say(errBox, messages[code] || messages.fields);
            }
          })
          .catch(function () { form.submit(); })   // network failure: let the browser do it
          .then(function () { if (btn) btn.disabled = false; });
      });
    }
  }
})();
