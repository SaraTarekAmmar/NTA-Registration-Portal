/**
 * Trainee Sidebar Layout — matches the admin/editor/coordinator/trainer nta-sidebar shell.
 * Builds the fixed sidebar into #ntaHeader and preserves the trainee session helpers.
 */
(function () {
  (function () {
    if (document.getElementById('ntaSbCss')) return;
    if (document.querySelector('link[href*="header/header.css"]')) return;
    var l = document.createElement('link');
    l.id = 'ntaSbCss';
    l.rel = 'stylesheet';
    l.href = 'header/header.css?v=9';
    document.head.appendChild(l);
  })();

  function ic(inner) {
    return '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + inner + '</svg>';
  }

  var ICONS = {
    courses: ic('<path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M4 4.5A2.5 2.5 0 016.5 2H20v20H6.5A2.5 2.5 0 014 19.5z"/>'),
    mine: ic('<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>'),
    admissions: ic('<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7l-3 3-1.5-1.5"/>'),
    profile: ic('<path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>'),
    permissions: ic('<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>'),
    tickets: ic('<path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/>'),
    logout: ic('<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>')
  };

  // The courses page sets data-page to available/enrolled based on the ?filter param.
  function syncCoursesDataPage() {
    try {
      var file = (window.location.pathname || '').split('/').pop() || '';
      if (file !== 'courses.html') return;
      var params = new URLSearchParams(window.location.search || '');
      document.body.setAttribute('data-page', params.get('filter') === 'my' ? 'enrolled-courses' : 'available-courses');
    } catch (e) {}
  }

  function navItem(href, keys, icon, label, active) {
    var isActive = keys.indexOf(active) !== -1;
    return '<a href="' + href + '" class="nta-sidebar__item' + (isActive ? ' active' : '') + '" data-page="' + keys[0] + '">' + icon + '<span class="nta-sidebar__item-lbl">' + label + '</span></a>';
  }

  function buildSidebar(activePage) {
    var userName = '';
    try {
      var s = JSON.parse(localStorage.getItem('ntaTrainee') || '{}');
      userName = s.name || s.full_name_ar || s.fullName || s.email || '';
    } catch (e) {}
    var onerr = "this.style.display='none';this.nextElementSibling.style.display='flex'";
    var nav = '<div class="nta-sidebar__nav-lbl">الرئيسية</div>' +
      navItem('courses.html', ['available-courses', 'courses'], ICONS.courses, 'الدورات المتاحة', activePage) +
      navItem('courses.html?filter=my', ['enrolled-courses'], ICONS.mine, 'دوراتي', activePage) +
      '<div class="nta-sidebar__divider"></div>' +
      '<div class="nta-sidebar__nav-lbl">حسابي</div>' +
      navItem('profile.html', ['profile'], ICONS.profile, 'الملف الشخصي', activePage) +
      navItem('trainee-permissions.html', ['permissions'], ICONS.permissions, 'الإذونات', activePage) +
      navItem('user-tickets.html', ['tickets'], ICONS.tickets, 'مركز التذاكر', activePage);

    var html = '<aside class="nta-sidebar"><div class="nta-sidebar__brand"><a href="courses.html" class="nta-sidebar__logo-link"><img src="images/NTA-Logo1.png" alt="" class="nta-sidebar__logo-img" id="ntaLogoImg" onerror="' + onerr + '"><span class="nta-sidebar__logo-fallback">NTA</span><div class="nta-sidebar__logo-text"><span class="nta-sidebar__logo-main">NTA</span><span class="nta-sidebar__logo-sub">بوابة المتدرب</span><span class="nta-sidebar__logo-ar">الأكاديمية الوطنية للتدريب</span></div></a></div><nav class="nta-sidebar__nav" aria-label="قائمة المتدرب">' + nav + '</nav><div class="nta-sidebar__footer">';
    if (userName) html += '<div class="nta-sidebar__user"><div class="nta-sidebar__avatar">' + (userName.charAt(0) || 'م') + '</div><div class="nta-sidebar__user-info"><div class="nta-sidebar__user-name">' + userName + '</div><div class="nta-sidebar__user-role-lbl">متدرب</div></div></div>';
    html += '<div class="nta-sidebar__bottom-row"><button type="button" class="nta-sidebar__logout" id="traineeLogoutBtn">' + ICONS.logout + 'تسجيل الخروج</button><button type="button" class="nta-sidebar__theme-btn" id="themeToggle" aria-label="تبديل المظهر" title="تبديل المظهر"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg></button></div></div></aside>';
    return html;
  }

  function setupMobileNav(container) {
    if (document.getElementById('ntaNavToggle')) return;
    var btn = document.createElement('button');
    btn.id = 'ntaNavToggle';
    btn.className = 'nta-nav-toggle';
    btn.type = 'button';
    btn.setAttribute('aria-label', 'فتح القائمة');
    btn.innerHTML = '☰';
    var backdrop = document.createElement('div');
    backdrop.id = 'ntaNavBackdrop';
    backdrop.className = 'nta-nav-backdrop';
    document.body.appendChild(btn);
    document.body.appendChild(backdrop);
    function setOpen(open) { document.body.classList.toggle('nta-nav-open', open); }
    btn.addEventListener('click', function () { setOpen(!document.body.classList.contains('nta-nav-open')); });
    backdrop.addEventListener('click', function () { setOpen(false); });
    if (container) container.addEventListener('click', function (e) { if (e.target.closest('a')) setOpen(false); });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var container = document.getElementById('ntaHeader');
    if (!container) return;
    syncCoursesDataPage();
    container.innerHTML = buildSidebar(document.body.getAttribute('data-page') || '');
    var logoutBtn = document.getElementById('traineeLogoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', function () {
      try { localStorage.removeItem('ntaTrainee'); } catch (e) {}
      window.location.href = 'index.html';
    });
    if (window.NTATheme && typeof window.NTATheme.bindAllToggles === 'function') window.NTATheme.bindAllToggles();
    setupMobileNav(container);
  });

  // Global helper for authenticated API calls (trainee session).
  window.authenticatedFetch = function (url, options) {
    options = options || {};
    var session = {};
    try { session = JSON.parse(localStorage.getItem('ntaTrainee') || '{}'); } catch (e) {}
    var headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
    if (session.token) headers['Authorization'] = 'Bearer ' + session.token;
    return fetch(url, Object.assign({}, options, { headers: headers })).then(function (res) {
      if (res.status === 401) {
        localStorage.removeItem('ntaTrainee');
        window.location.href = 'index.html';
        return Promise.reject('Session expired');
      }
      return res;
    });
  };
})();
