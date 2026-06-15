/**
 * Coordinator Sidebar Layout
 * Injects the sidebar navigation into #coordinatorSidebar.
 * Same visual pattern as editor-layout.js but with coordinator nav items.
 */
(function () {
  var page = document.body.getAttribute("data-page") || "";

  function ic(inner) {
    return '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + inner + "</svg>";
  }

  var ICONS = {
    dashboard: ic('<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>'),
    attendance: ic('<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>'),
    permissions: ic('<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>'),
    logout: ic('<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>'),
  };

  function navItem(href, key, icon, label, activePage) {
    var cls = activePage === key ? "sidebar__link sidebar__link--active" : "sidebar__link";
    return '<a href="' + href + '" class="' + cls + '" data-page="' + key + '">' +
      '<span class="sidebar__icon">' + icon + "</span>" +
      '<span class="sidebar__label">' + label + "</span>" +
      "</a>";
  }

  function buildSidebar(activePage) {
    var userName = "";
    try {
      if (window.coordinatorAuth && window.coordinatorAuth.payload) {
        userName = window.coordinatorAuth.payload.name || window.coordinatorAuth.payload.email || "";
      }
    } catch (e) {}

    var html = "";
    html += '<aside class="sidebar" id="sidebarNav">';
    html += '  <div class="sidebar__brand">';
    html += '    <img src="/images/nta-logo.png" alt="NTA" class="sidebar__logo" onerror="this.style.display=\'none\'">';
    html += '    <div>';
    html += '      <div class="sidebar__brand-title">الأكاديمية الوطنية</div>';
    html += '      <div class="sidebar__brand-sub">بوابة المنسّق</div>';
    html += '    </div>';
    html += '  </div>';

    html += '  <nav class="sidebar__nav">';
    html += '    <div class="sidebar__section-label">الرئيسية</div>';
    html += navItem("coordinator-dashboard.html", "dashboard", ICONS.dashboard, "لوحة التحكم", activePage);
    html += '    <div class="sidebar__section-label" style="margin-top:1.2rem;">الإدارة</div>';
    html += navItem("coordinator-attendance.html", "attendance", ICONS.attendance, "الحضور والغياب", activePage);
    html += navItem("coordinator-permissions.html", "permissions", ICONS.permissions, "الإذونات", activePage);
    html += "  </nav>";

    html += '  <div class="sidebar__footer">';
    if (userName) {
      html += '    <div class="sidebar__user">';
      html += '      <div class="sidebar__user-avatar">' + (userName.charAt(0) || "م") + "</div>";
      html += '      <div class="sidebar__user-info">';
      html += '        <div class="sidebar__user-name">' + userName + "</div>";
      html += '        <div class="sidebar__user-role">منسّق</div>';
      html += "      </div>";
      html += "    </div>";
    }

    // Theme toggle
    html += '    <button id="themeToggle" class="sidebar__theme-btn" title="تبديل المظهر">';
    html += '      <svg class="theme-icon-dark" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="18" height="18"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>';
    html += '      <svg class="theme-icon-light" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="18" height="18"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>';
    html += "    </button>";

    html += '    <button class="sidebar__logout-btn" onclick="window.coordinatorAuth.logout()">';
    html += '      <span class="sidebar__icon">' + ICONS.logout + "</span>";
    html += '      <span class="sidebar__label">تسجيل الخروج</span>';
    html += "    </button>";
    html += "  </div>";
    html += "</aside>";

    return html;
  }

  var container = document.getElementById("coordinatorSidebar");
  if (container) {
    container.innerHTML = buildSidebar(page);
  }

  // Theme toggle binding
  setTimeout(function () {
    var btn = document.getElementById("themeToggle");
    if (btn && window.NTATheme) {
      btn.addEventListener("click", function () {
        window.NTATheme.toggle();
      });
    }
  }, 100);
})();
