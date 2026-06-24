(function () {
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
      navItem('editor-admission-scenarios.html', 'admission-scenarios', icons.scenarios, 'سيناريوهات القبول', activePage);
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
  window.initUISelects = window.initUISelects || function () {};
  window.initUIMenus = window.initUIMenus || function () {};
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
