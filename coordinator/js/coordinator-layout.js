/**
 * Coordinator Sidebar Layout
 * Injects the sidebar navigation into #coordinatorSidebar.
 * Same visual pattern as editor-layout.js but with coordinator nav items.
 */
(function () {
  (function () {
    if (document.getElementById('ntaSbCss')) return;
    if (document.querySelector('link[href*="header/header.css"]')) return;
    var l = document.createElement('link');
    l.id = 'ntaSbCss';
    l.rel = 'stylesheet';
    l.href = '/admin/header/header.css?v=7';
    document.head.appendChild(l);
  })();

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
    var cls = 'nta-sidebar__item' + (activePage === key ? ' active' : '');
    return '<a href="' + href + '" class="' + cls + '" data-page="' + key + '">' +
      icon + '<span class="nta-sidebar__item-lbl">' + label + '</span></a>';
  }

  function buildSidebar(activePage) {
    var userName = "";
    try {
      if (window.coordinatorAuth && window.coordinatorAuth.payload) {
        userName = window.coordinatorAuth.payload.name || window.coordinatorAuth.payload.email || "";
      }
    } catch (e) {}

    var onerr = "this.style.display='none';this.nextElementSibling.style.display='flex'";

    var nav = '<div class="nta-sidebar__nav-lbl">الرئيسية</div>' +
      navItem("coordinator-dashboard.html", "dashboard", ICONS.dashboard, "لوحة التحكم", activePage) +
      '<div class="nta-sidebar__divider"></div>' +
      '<div class="nta-sidebar__nav-lbl">الإدارة</div>' +
      navItem("coordinator-attendance.html", "attendance", ICONS.attendance, "الحضور والغياب", activePage) +
      navItem("coordinator-permissions.html", "permissions", ICONS.permissions, "الإذونات", activePage);

    var html = '<aside class="nta-sidebar">' +
      '<div class="nta-sidebar__brand">' +
        '<a href="coordinator-dashboard.html" class="nta-sidebar__logo-link">' +
          '<img src="/images/NTA-Logo1.png" alt="" class="nta-sidebar__logo-img" id="ntaLogoImg" onerror="' + onerr + '">' +
          '<span class="nta-sidebar__logo-fallback">NTA</span>' +
          '<div class="nta-sidebar__logo-text">' +
            '<span class="nta-sidebar__logo-main">NTA</span>' +
            '<span class="nta-sidebar__logo-sub">بوابة المنسّق</span>' +
            '<span class="nta-sidebar__logo-ar">الأكاديمية الوطنية للتدريب</span>' +
          '</div>' +
        '</a>' +
      '</div>' +
      '<nav class="nta-sidebar__nav" aria-label="قائمة المنسّق">' + nav + '</nav>' +
      '<div class="nta-sidebar__footer">';

    if (userName) {
      html += '<div class="nta-sidebar__user">' +
        '<div class="nta-sidebar__avatar">' + (userName.charAt(0) || "م") + '</div>' +
        '<div class="nta-sidebar__user-info">' +
          '<div class="nta-sidebar__user-name">' + userName + '</div>' +
          '<div class="nta-sidebar__user-role-lbl">منسّق</div>' +
        '</div>' +
      '</div>';
    }

    html += '<div class="nta-sidebar__bottom-row">' +
      '<button type="button" class="nta-sidebar__logout" onclick="window.coordinatorAuth.logout()">' +
        ICONS.logout + 'تسجيل الخروج' +
      '</button>' +
      '<button type="button" class="nta-sidebar__theme-btn" id="themeToggle" aria-label="تبديل المظهر" title="تبديل المظهر">' +
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>' +
      '</button>' +
    '</div></div></aside>';

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
