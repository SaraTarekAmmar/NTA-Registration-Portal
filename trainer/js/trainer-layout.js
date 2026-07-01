/**
 * Trainer Sidebar Layout — mirrors the admin/editor/coordinator nta-sidebar shell.
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
    dashboard: ic('<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>'),
    trainees: ic('<path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>'),
    quiz: ic('<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>'),
    tickets: ic('<path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/>'),
    logout: ic('<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>')
  };

  function navItem(href, key, icon, label, activePage) {
    var cls = 'nta-sidebar__item' + (activePage === key ? ' active' : '');
    return '<a href="' + href + '" class="' + cls + '" data-page="' + key + '">' + icon + '<span class="nta-sidebar__item-lbl">' + label + '</span></a>';
  }

  function buildSidebar(activePage) {
    var userName = '';
    try {
      var s = JSON.parse(localStorage.getItem('ntaTrainer') || '{}');
      userName = s.name || s.full_name_ar || s.email || '';
    } catch (e) {}
    var onerr = "this.style.display='none';this.nextElementSibling.style.display='flex'";
    var nav = '<div class="nta-sidebar__nav-lbl">الرئيسية</div>' +
      navItem('trainer-dashboard.html', 'dashboard', ICONS.dashboard, 'لوحة التحكم', activePage) +
      '<div class="nta-sidebar__divider"></div>' +
      '<div class="nta-sidebar__nav-lbl">التدريب</div>' +
      navItem('view trainees/view-trainees.html', 'trainees', ICONS.trainees, 'المتدربون', activePage) +
      navItem('generate quiz/generate-quiz.html', 'quiz', ICONS.quiz, 'توليد اختبار', activePage) +
      navItem('trainer-tickets.html', 'tickets', ICONS.tickets, 'مركز التذاكر', activePage);

    var html = '<aside class="nta-sidebar"><div class="nta-sidebar__brand"><a href="trainer-dashboard.html" class="nta-sidebar__logo-link"><img src="/images/NTA-Logo1.png" alt="" class="nta-sidebar__logo-img" id="ntaLogoImg" onerror="' + onerr + '"><span class="nta-sidebar__logo-fallback">NTA</span><div class="nta-sidebar__logo-text"><span class="nta-sidebar__logo-main">NTA</span><span class="nta-sidebar__logo-sub">بوابة المدرب</span><span class="nta-sidebar__logo-ar">الأكاديمية الوطنية للتدريب</span></div></a></div><nav class="nta-sidebar__nav" aria-label="قائمة المدرب">' + nav + '</nav><div class="nta-sidebar__footer">';
    if (userName) html += '<div class="nta-sidebar__user"><div class="nta-sidebar__avatar">' + (userName.charAt(0) || 'م') + '</div><div class="nta-sidebar__user-info"><div class="nta-sidebar__user-name">' + userName + '</div><div class="nta-sidebar__user-role-lbl">مدرب</div></div></div>';
    html += '<div class="nta-sidebar__bottom-row"><button type="button" class="nta-sidebar__logout" id="trainerLogoutBtn">' + ICONS.logout + 'تسجيل الخروج</button><button type="button" class="nta-sidebar__theme-btn" id="themeToggle" aria-label="تبديل المظهر" title="تبديل المظهر"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg></button></div></div></aside>';
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
    if (container) container.innerHTML = buildSidebar(document.body.getAttribute('data-page') || '');
    var logoutBtn = document.getElementById('trainerLogoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', function () { localStorage.removeItem('ntaTrainer'); window.location.replace('/index.html'); });
    if (window.NTATheme && typeof window.NTATheme.bindAllToggles === 'function') window.NTATheme.bindAllToggles();
    setupMobileNav(container);
  });

  // Authenticated fetch helper (was previously defined in header/header.js).
  window.authenticatedFetch = function (url, options) {
    options = options || {};
    var session = {};
    try { session = JSON.parse(localStorage.getItem('ntaTrainer') || '{}'); } catch (e) {}
    var headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
    if (session.token) headers['Authorization'] = 'Bearer ' + session.token;
    return fetch(url, Object.assign({}, options, { headers: headers })).then(function (res) {
      if (res.status === 401) {
        localStorage.removeItem('ntaTrainer');
        window.location.replace('/index.html');
        return Promise.reject('Session expired');
      }
      return res;
    });
  };
})();
