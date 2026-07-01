/**
 * NTA shared theme (dark default, light via html.light-mode).
 * Load synchronously in <head> before stylesheets to reduce flash.
 */
(function (global) {
  var STORAGE_KEY = "nta-theme";
  var LIGHT = "light";
  var DARK = "dark";

  var SUN_PATH =
    "M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z";
  var MOON_PATH =
    "M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z";

  function getStored() {
    try {
      var v = localStorage.getItem(STORAGE_KEY);
      return v === LIGHT ? LIGHT : DARK;
    } catch (e) {
      return DARK;
    }
  }

  function isLight() {
    return getStored() === LIGHT;
  }

  function apply(theme) {
    var light = theme === LIGHT;
    document.documentElement.classList.toggle("light-mode", light);
    if (document.body) {
      document.body.classList.toggle("light-mode", light);
    }
    try {
      var event = new CustomEvent("nta-theme-changed", { detail: { theme: theme, isLight: light } });
      window.dispatchEvent(event);
    } catch (e) {}
  }

  function updateThemeIcon() {
    var label = isLight() ? "Switch to dark mode" : "Switch to light mode";
    document.querySelectorAll("#themeToggle, #ntaThemeFab").forEach(function (btn) {
      var path = btn.querySelector("path");
      if (path) path.setAttribute("d", isLight() ? MOON_PATH : SUN_PATH);
      btn.setAttribute("aria-label", label);
      btn.setAttribute("title", label);
    });
  }

  function toggle() {
    var next = isLight() ? DARK : LIGHT;
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch (e) {}
    apply(next);
    updateThemeIcon();
    return next;
  }

  function findThemeButton(target) {
    if (!target || !target.closest) return null;
    return target.closest("#themeToggle, #ntaThemeFab, .nta-header__theme");
  }

  function ensureFloatingToggle() {
    if (document.querySelector("#themeToggle, #ntaThemeFab")) {
      return;
    }
    if (!document.body) return;

    var fab = document.createElement("button");
    fab.type = "button";
    fab.id = "ntaThemeFab";
    fab.className = "nta-theme-fab";
    fab.setAttribute("aria-label", "Toggle theme");
    fab.innerHTML =
      '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="22" height="22">' +
      '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="' +
      SUN_PATH +
      '"/></svg>';
    document.body.appendChild(fab);
    updateThemeIcon();
  }

  function bindAllToggles() {
    var headerBtn = document.getElementById("themeToggle");
    var fab = document.getElementById("ntaThemeFab");

    if (headerBtn) {
      if (fab) fab.remove();
    } else {
      ensureFloatingToggle();
    }
    updateThemeIcon();
  }

  function watchHeader() {
    var headerRoot = document.getElementById("ntaHeader");
    if (!headerRoot || typeof MutationObserver === "undefined") return;
    var observer = new MutationObserver(function () {
      bindAllToggles();
    });
    observer.observe(headerRoot, { childList: true, subtree: true });
  }

  function onThemeClick(e) {
    var btn = findThemeButton(e.target);
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    toggle();
  }

  // Apply before first paint
  apply(getStored());

  // Single delegated handler — works after header fetch/replace (trainee & trainer pages)
  document.addEventListener("click", onThemeClick, true);

  document.addEventListener("DOMContentLoaded", function () {
    apply(getStored());
    bindAllToggles();
    watchHeader();
  });

  global.NTATheme = {
    getStored: getStored,
    isLight: isLight,
    apply: apply,
    toggle: toggle,
    bindAllToggles: bindAllToggles,
    updateThemeIcon: updateThemeIcon,
  };
})(typeof window !== "undefined" ? window : this);
