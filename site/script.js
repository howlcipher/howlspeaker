"use strict";
(() => {
  const button = document.getElementById("theme-toggle");
  let dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  try {
    const stored = localStorage.getItem("howlspeaker-theme");
    if (stored === "dark" || stored === "light") dark = stored === "dark";
  } catch (_) { /* The page works when storage is unavailable. */ }
  const apply = () => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    button.setAttribute("aria-pressed", String(dark));
  };
  button.hidden = false;
  apply();
  button.addEventListener("click", () => {
    dark = !dark;
    apply();
    try { localStorage.setItem("howlspeaker-theme", dark ? "dark" : "light"); }
    catch (_) { /* Theme persistence is optional. */ }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      const menu = document.querySelector(".ecosystem[open]");
      if (menu) {
        menu.open = false;
        menu.querySelector("summary").focus();
      }
    }
  });
})();
