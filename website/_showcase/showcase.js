/* Clwydian Academy — showcase enhancements (no dependencies).
   Nothing here is needed to read the page: without it a before-and-after pair is two pictures
   side by side and "View larger" is an ordinary link to the picture. */
(function () {
  "use strict";

  // Before and after: an ordinary range input drives the wipe, so it works with a mouse, a
  // finger, the arrow keys, Home and End, and is announced by a screen reader in words.
  document.querySelectorAll("[data-ba]").forEach(function (figure) {
    var range = figure.querySelector(".ba-range");
    var stage = figure.querySelector(".ba-stage");
    if (!range || !stage) return;
    figure.classList.add("ba-on");
    var say = function () {
      var v = Number(range.value);
      stage.style.setProperty("--pos", v + "%");
      range.setAttribute("aria-valuetext", v + "% " + range.dataset.before + ", " + (100 - v) + "% " + range.dataset.after);
    };
    range.addEventListener("input", say);
    say();
  });

  // Lightbox: the native <dialog>, which brings focus trapping, Escape and the backdrop with it.
  var box = document.getElementById("sc-lightbox");
  if (box && typeof box.showModal === "function") {
    var img = box.querySelector("img");
    var cap = box.querySelector("p");
    var opener = null;
    document.addEventListener("click", function (e) {
      var link = e.target.closest && e.target.closest("[data-lightbox]");
      if (!link) return;
      e.preventDefault();
      opener = link;
      img.src = link.getAttribute("href");
      img.alt = link.dataset.caption || "";
      cap.textContent = link.dataset.caption || "";
      box.showModal();
    });
    box.addEventListener("click", function (e) {
      if (e.target === box || (e.target.closest && e.target.closest("[data-lightbox-close]"))) box.close();
    });
    box.addEventListener("close", function () { img.removeAttribute("src"); if (opener) opener.focus(); });
  }
})();
