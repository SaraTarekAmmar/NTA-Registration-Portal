/**
 * Resolve CSS custom properties for chart libraries (ECharts, Chart.js).
 * Load after theme.js on pages that render charts.
 */
(function (global) {
  function cssVar(name) {
    var n = name.indexOf("--") === 0 ? name : "--" + name;
    return getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  }

  function cssVarList(names) {
    return names.map(cssVar);
  }

  global.NTAThemeColors = {
    cssVar: cssVar,
    cssVarList: cssVarList,
  };
})(typeof window !== "undefined" ? window : this);
