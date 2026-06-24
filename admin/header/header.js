(function () {
  (function () {
    if (document.getElementById('ntaSbCss')) return;
    if (document.querySelector('link[href*="header/header.css"]')) return;
    var l = document.createElement('link');
    l.id = 'ntaSbCss';
    l.rel = 'stylesheet';
    l.href = '/admin/header/header.css?v=8';
    document.head.appendChild(l);
  })();

  function ic(path) {
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + path + '</svg>';
  }

  function navItem(href, page, icon, label, cur) {
    var cls = 'nta-sidebar__item' + (cur === page ? ' active' : '');
    return '<a href="' + href + '" class="' + cls + '" data-page="' + page + '">' +
      icon + '<span class="nta-sidebar__item-lbl">' + label + '</span></a>';
  }

  function navLbl(t) { return '<div class="nta-sidebar__nav-lbl">' + t + '</div>'; }
  function divider() { return '<div class="nta-sidebar__divider"></div>'; }

  function buildSidebar(page, name, roleLabel) {
    var ICONS = {
      home:    ic('<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>'),
      cands:   ic('<circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>'),
      train:   ic('<path d="M17 20H7m10 0v-2a3 3 0 00-5.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>'),
      attend:  ic('<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18M9 16l2 2 4-4"/>'),
      courses: ic('<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>'),
      lock:    ic('<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/>'),
      admit:   ic('<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>'),
      flow:    ic('<path d="M4 6h16M4 12h8m-8 6h16"/>'),
      shield:  ic('<path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>'),
      chart:   ic('<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'),
      user:    ic('<path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
      logout:  ic('<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>'),
    };

    var onerr = "this.style.display='none';this.nextElementSibling.style.display='flex'";

    var nav = navLbl('الرئيسية') +
      navItem('admin-dashboard.html', 'admin', ICONS.home, 'لوحة التحكم', page) +
      divider() +
      navLbl('الأفراد') +
      navItem('admin-candidates.html', 'admin-candidates', ICONS.cands, 'المرشحون', page) +
      navItem('admin-trainees.html',   'admin-trainees',   ICONS.train, 'المتدربون', page) +
      divider() +
      navLbl('الإدارة') +
      navItem('admin-courses.html',            'admin-courses',      ICONS.courses,'البرامج والدورات', page) +
      navItem('admin-quiz-results.html',       'quiz-results',       ICONS.chart,  'نتائج الاختبارات', page);

    return '<aside class="nta-sidebar">' +
      '<div class="nta-sidebar__brand">' +
        '<a href="admin-dashboard.html" class="nta-sidebar__logo-link">' +
          '<img src="images/NTA-Logo1.png" alt="" class="nta-sidebar__logo-img" id="ntaLogoImg" onerror="' + onerr + '">' +
          '<span class="nta-sidebar__logo-fallback">NTA</span>' +
          '<div class="nta-sidebar__logo-text">' +
            '<span class="nta-sidebar__logo-main">NTA</span>' +
            '<span class="nta-sidebar__logo-sub">NATIONAL TRAINING ACADEMY</span>' +
            '<span class="nta-sidebar__logo-ar">الأكاديمية الوطنية للتدريب</span>' +
          '</div>' +
        '</a>' +
      '</div>' +
      '<nav class="nta-sidebar__nav" aria-label="قائمة الإدارة">' + nav + '</nav>' +
      '<div class="nta-sidebar__footer">' +
        '<div class="nta-sidebar__bottom-row">' +
          '<button type="button" class="nta-sidebar__logout" id="logoutBtn">' +
            ICONS.logout + 'تسجيل الخروج' +
          '</button>' +
          '<button type="button" class="nta-sidebar__theme-btn" id="themeToggle" aria-label="تبديل المظهر" title="تبديل المظهر">' +
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>' +
          '</button>' +
        '</div>' +
      '</div>' +
    '</aside>';
  }

  document.addEventListener('DOMContentLoaded', function () {
    var container = document.getElementById('ntaHeader');
    if (!container) return;

    var session = {};
    var tok = localStorage.getItem('admin_token');
    if (tok) {
      try {
        var _b64 = tok.split('.')[1].replace(/-/g, "+").replace(/_/g, "/");
        var p = JSON.parse(decodeURIComponent(atob(_b64).split("").map(function (c) {
          return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
        }).join("")));
        session = { token: tok, role: p.role, name: p.name || p.email || '' };
      } catch (e) {}
    }
    // SECURITY FIX: Removed ntaTrainee fallback. The admin portal must only accept
    // admin_token. If no valid admin token exists, the sidebar will not render,
    // and the page-level role check will redirect to admin-login.html.
    if (session.role !== 'admin') return;

    var page = document.body.getAttribute('data-page') || '';
    container.innerHTML = buildSidebar(page, session.name, 'مدير النظام');

    var logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn && !logoutBtn.dataset.ntaBound) {
      logoutBtn.dataset.ntaBound = '1';
      logoutBtn.addEventListener('click', function () {
        localStorage.removeItem('admin_token');
        window.location.href = 'admin-login.html';
      });
    }

    if (window.NTATheme && typeof window.NTATheme.bindAllToggles === 'function') {
      window.NTATheme.bindAllToggles();
    }

    setupMobileNav(container);
  });

  function setupMobileNav(container) {
    if (document.getElementById('ntaNavToggle')) return;
    var btn = document.createElement('button');
    btn.id = 'ntaNavToggle';
    btn.className = 'nta-nav-toggle';
    btn.type = 'button';
    btn.setAttribute('aria-label', 'فتح القائمة');
    btn.setAttribute('aria-expanded', 'false');
    btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
    var backdrop = document.createElement('div');
    backdrop.id = 'ntaNavBackdrop';
    backdrop.className = 'nta-nav-backdrop';
    document.body.appendChild(btn);
    document.body.appendChild(backdrop);
    function setOpen(open) {
      document.body.classList.toggle('nta-nav-open', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    btn.addEventListener('click', function () { setOpen(!document.body.classList.contains('nta-nav-open')); });
    backdrop.addEventListener('click', function () { setOpen(false); });
    if (container) container.addEventListener('click', function (e) { if (e.target.closest('a')) setOpen(false); });
    window.addEventListener('keydown', function (e) { if (e.key === 'Escape') setOpen(false); });
  }

  window.authenticatedFetch = function (url, options) {
    options = options || {};
    // SECURITY FIX: Only use admin_token. Never fall back to ntaTrainee.
    var token = localStorage.getItem('admin_token');
    var headers = Object.assign({}, options.headers || {});
    if (token) headers.Authorization = 'Bearer ' + token;
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }
    return fetch(url, Object.assign({}, options, { headers: headers })).then(function (res) {
      if (res.status === 401) {
        localStorage.removeItem('admin_token');
        window.location.href = 'admin-login.html';
        return Promise.reject('Session expired');
      }
      return res;
    });
  };
})();
