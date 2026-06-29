(function () {
  // The sidebar markup uses the shared `.nta-sidebar` classes and the layout/
  // animation rules for `.editor-main` live in admin/header/header.css. Inject it
  // (once) so editor pages render the fixed sidebar and the main content fades in
  // instead of staying at opacity:0 with an unstyled, full-height sidebar.
  (function () {
    if (document.getElementById('ntaSbCss')) return;
    if (document.querySelector('link[href*="header/header.css"]')) return;
    var l = document.createElement('link');
    l.id = 'ntaSbCss';
    l.rel = 'stylesheet';
    l.href = '/admin/header/header.css?v=8';
    document.head.appendChild(l);
  })();

  var EDITOR_TOKEN_KEY = "editor_token";

  function ic(path) {
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + path + '</svg>';
  }
  function navItem(href, page, icon, label, cur) {
    return '<a href="' + href + '" class="nta-sidebar__item' + (cur === page ? ' active' : '') + '" data-page="' + page + '">' + icon + '<span class="nta-sidebar__item-lbl">' + label + '</span></a>';
  }
  function buildSidebar(activePage) {
    var icons = {
      home: ic('<path d="M3 12l9-9 9 9M5 10v10h14V10"/>'),
      courses: ic('<path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M4 4.5A2.5 2.5 0 016.5 2H20v20H6.5A2.5 2.5 0 014 19.5z"/>'),
      materials: ic('<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/>'),
      sessions: ic('<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>'),
      flow: ic('<path d="M4 6h16M4 12h8m-8 6h16"/>'),
      exams: ic('<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>'),
      tickets: ic('<path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/>'),
      scenarios: ic('<circle cx="4" cy="6" r="1.5"/><circle cx="4" cy="12" r="1.5"/><circle cx="4" cy="18" r="1.5"/><path d="M8 6h12M8 12h12M8 18h12"/>'),
      logout: ic('<path d="M17 16l4-4-4-4M21 12H7"/><path d="M13 16v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>')
    };
    var onerr = "this.style.display='none';this.nextElementSibling.style.display='flex'";
    var nav =
      navItem('editor-dashboard.html', 'dashboard', icons.home, 'لوحة التحكم', activePage) +
      navItem('editor-courses.html', 'courses', icons.courses, 'الدورات', activePage) +
      navItem('editor-materials.html', 'materials', icons.materials, 'المواد التعليمية', activePage) +
      navItem('editor-sessions.html', 'sessions', icons.sessions, 'الجلسات', activePage) +
      navItem('editor-registration-builder.html?v=' + Date.now(), 'registration-builder', icons.flow, 'مسار التسجيل', activePage) +
      navItem('editor-admission-builder.html', 'admission-builder', icons.exams, 'مسار القبول', activePage) +
      navItem('editor-tickets.html', 'tickets', icons.tickets, 'مركز التذاكر', activePage);
    return '<aside class="nta-sidebar"><div class="nta-sidebar__brand"><a href="editor-dashboard.html" class="nta-sidebar__logo-link"><img src="/images/NTA-Logo1.png" alt="" class="nta-sidebar__logo-img" onerror="' + onerr + '"><span class="nta-sidebar__logo-fallback">NTA</span><div class="nta-sidebar__logo-text"><span class="nta-sidebar__logo-main">NTA</span><span class="nta-sidebar__logo-sub">NATIONAL TRAINING ACADEMY</span><span class="nta-sidebar__logo-ar">الأكاديمية الوطنية للتدريب</span></div></a></div><nav class="nta-sidebar__nav" aria-label="قائمة المحرر">' + nav + '</nav><div class="nta-sidebar__footer"><div class="nta-sidebar__bottom-row"><button type="button" class="nta-sidebar__logout" id="editorLogoutBtn">' + icons.logout + 'تسجيل الخروج</button><button type="button" class="nta-sidebar__theme-btn" id="themeToggle" aria-label="تبديل المظهر" title="تبديل المظهر">☼</button></div></div></aside>';
  }
  function setupMobileNav(container) {
    if (document.getElementById("ntaNavToggle")) return;
    var btn = document.createElement("button");
    btn.id = "ntaNavToggle";
    btn.className = "nta-nav-toggle";
    btn.type = "button";
    btn.setAttribute("aria-label", "فتح القائمة");
    btn.innerHTML = '☰';
    var backdrop = document.createElement("div");
    backdrop.id = "ntaNavBackdrop";
    backdrop.className = "nta-nav-backdrop";
    document.body.appendChild(btn);
    document.body.appendChild(backdrop);
    function setOpen(open) { document.body.classList.toggle("nta-nav-open", open); }
    btn.addEventListener("click", function () { setOpen(!document.body.classList.contains("nta-nav-open")); });
    backdrop.addEventListener("click", function () { setOpen(false); });
    if (container) container.addEventListener("click", function (e) { if (e.target.closest("a")) setOpen(false); });
  }
  function loadCourseFormEnhancements() {
    if (!document.getElementById('basicInfoForm') || document.getElementById('editorCourseFormEnhancements')) return;
    var script = document.createElement('script');
    script.id = 'editorCourseFormEnhancements';
    script.src = 'js/editor-course-form.js?v=4';
    document.body.appendChild(script);
  }
  window.showEditorToast = window.showEditorToast || function (msg) { alert(msg); };
  window.editorConfirm = window.editorConfirm || function () { return Promise.resolve(confirm('تأكيد؟')); };
  // ── Custom UI Select / UI Menu widgets ──────────────────────────────
  // Real implementation (was previously a no-op, leaving every custom
  // dropdown — e.g. the course pickers on the admission/registration
  // builders — dead). Uses capture-phase delegation so it also works for
  // widgets injected at runtime and inside containers that stopPropagation.
  function closeAllUISelects(except) {
    document.querySelectorAll('.ui-select__menu:not([hidden])').forEach(function (menu) {
      var sel = menu.closest('.ui-select');
      if (sel === except) return;
      menu.setAttribute('hidden', '');
      var t = sel && sel.querySelector('.ui-select__trigger');
      if (t) t.setAttribute('aria-expanded', 'false');
      if (sel) sel.classList.remove('is-open');
    });
  }
  function closeAllUIMenus(except) {
    document.querySelectorAll('.ui-menu__content:not([hidden])').forEach(function (c) {
      if (c.closest('.ui-menu') === except) return;
      c.setAttribute('hidden', '');
    });
  }
  document.addEventListener('click', function (e) {
    var trigger = e.target.closest && e.target.closest('.ui-select__trigger');
    if (trigger) {
      e.preventDefault();
      var sel = trigger.closest('.ui-select');
      var menu = sel.querySelector('.ui-select__menu');
      var willOpen = menu.hasAttribute('hidden');
      closeAllUISelects(sel); closeAllUIMenus();
      if (willOpen) { menu.removeAttribute('hidden'); trigger.setAttribute('aria-expanded', 'true'); sel.classList.add('is-open'); }
      else { menu.setAttribute('hidden', ''); trigger.setAttribute('aria-expanded', 'false'); sel.classList.remove('is-open'); }
      return;
    }
    var option = e.target.closest && e.target.closest('.ui-select__option');
    if (option) {
      e.preventDefault();
      var os = option.closest('.ui-select');
      var input = os.querySelector('input');
      var valueEl = os.querySelector('.ui-select__value');
      var val = option.getAttribute('data-value') || '';
      var labelSpan = option.querySelector('span:not(.ui-select__check)') || option;
      var label = labelSpan.textContent.trim();
      if (valueEl) { valueEl.textContent = label; valueEl.classList.toggle('is-placeholder', val === ''); }
      os.querySelectorAll('.ui-select__option').forEach(function (o) { o.removeAttribute('aria-selected'); o.classList.remove('is-selected'); });
      option.setAttribute('aria-selected', 'true'); option.classList.add('is-selected');
      closeAllUISelects();
      if (input) { input.value = val; input.dispatchEvent(new Event('change', { bubbles: true })); }
      return;
    }
    var menuTrigger = e.target.closest && e.target.closest('.ui-menu__trigger');
    if (menuTrigger) {
      e.preventDefault();
      var content = menuTrigger.closest('.ui-menu').querySelector('.ui-menu__content');
      var willShow = content && content.hasAttribute('hidden');
      closeAllUIMenus(); closeAllUISelects();
      if (content) { if (willShow) content.removeAttribute('hidden'); else content.setAttribute('hidden', ''); }
      return;
    }
    closeAllUISelects(); closeAllUIMenus();
  }, true);

  function initUISelects(scope) {
    var root = (scope && scope.querySelectorAll) ? scope : document;
    var list = (root.classList && root.classList.contains('ui-select')) ? [root] : root.querySelectorAll('.ui-select');
    [].forEach.call(list, function (sel) {
      var input = sel.querySelector('input');
      var valueEl = sel.querySelector('.ui-select__value');
      if (!input || !valueEl) return;
      var cur = sel.querySelector('.ui-select__option[data-value="' + (input.value || '') + '"]');
      if (cur) {
        var sp = cur.querySelector('span:not(.ui-select__check)') || cur;
        valueEl.textContent = sp.textContent.trim();
        valueEl.classList.toggle('is-placeholder', !input.value);
      }
    });
  }
  function initUIMenus() { /* interactions handled via delegation above */ }
  window.initUISelects = initUISelects;
  window.initUIMenus = initUIMenus;
  document.addEventListener("DOMContentLoaded", function () {
    var container = document.getElementById("editorSidebar");
    if (container) container.innerHTML = buildSidebar(document.body.getAttribute("data-page") || "");
    var logoutBtn = document.getElementById("editorLogoutBtn");
    if (logoutBtn) logoutBtn.addEventListener("click", function () { localStorage.removeItem(EDITOR_TOKEN_KEY); window.location.replace("editor-login.html"); });
    if (window.NTATheme && typeof window.NTATheme.bindAllToggles === "function") window.NTATheme.bindAllToggles();
    setupMobileNav(container);
    loadCourseFormEnhancements();
    window.initUISelects();
    window.initUIMenus();
  });
})();
