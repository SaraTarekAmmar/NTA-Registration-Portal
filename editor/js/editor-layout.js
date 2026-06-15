(function () {
  var EDITOR_TOKEN_KEY = "editor_token";

  (function () {
    if (document.getElementById('ntaSbCss')) return;
    if (document.querySelector('link[href*="header/header.css"]')) return;
    var l = document.createElement('link');
    l.id = 'ntaSbCss';
    l.rel = 'stylesheet';
    l.href = '/admin/header/header.css?v=5';
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

  function buildSidebar(activePage, name) {
    var ICONS = {
      home:     ic('<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>'),
      courses:  ic('<path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>'),
      materials:ic('<path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>'),
      sessions: ic('<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>'),
      flow:     ic('<path d="M4 6h16M4 12h8m-8 6h16"/>'),
      exams:    ic('<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>'),
      planning: ic('<path d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 0a2 2 0 012-2h2a2 2 0 012 2v10a2 2 0 01-2 2h-2a2 2 0 01-2-2"/>'),
      user:     ic('<path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
      logout:   ic('<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>'),
    };

    var onerr = "this.style.display='none';this.nextElementSibling.style.display='flex'";

    var nav =
      navItem('editor-dashboard.html', 'dashboard',  ICONS.home,      'لوحة التحكم',    activePage) +
      navItem('editor-courses.html',   'courses',    ICONS.courses,   'الدورات',         activePage) +
      navItem('editor-materials.html', 'materials',  ICONS.materials, 'المواد التعليمية',activePage) +
      navItem('editor-sessions.html',  'sessions',   ICONS.sessions,  'الجلسات',         activePage) +
      navItem('editor-flow-builder.html', 'flow-builder', ICONS.flow,  'تدفق التسجيل',    activePage);

    return '<aside class="nta-sidebar">' +
      '<div class="nta-sidebar__brand">' +
        '<a href="editor-dashboard.html" class="nta-sidebar__logo-link">' +
          '<img src="/images/NTA-Logo1.png" alt="" class="nta-sidebar__logo-img" id="ntaLogoImg" onerror="' + onerr + '">' +
          '<span class="nta-sidebar__logo-fallback">NTA</span>' +
          '<div class="nta-sidebar__logo-text">' +
            '<span class="nta-sidebar__logo-main">NTA</span>' +
            '<span class="nta-sidebar__logo-sub">NATIONAL TRAINING ACADEMY</span>' +
            '<span class="nta-sidebar__logo-ar">الأكاديمية الوطنية للتدريب</span>' +
          '</div>' +
        '</a>' +
      '</div>' +
      '<nav class="nta-sidebar__nav" aria-label="قائمة المحرر">' + nav + '</nav>' +
      '<div class="nta-sidebar__footer">' +
        '<div class="nta-sidebar__bottom-row">' +
          '<button type="button" class="nta-sidebar__logout" id="editorLogoutBtn">' +
            ICONS.logout + 'تسجيل الخروج' +
          '</button>' +
          '<button type="button" class="nta-sidebar__theme-btn" id="themeToggle" aria-label="تبديل المظهر" title="تبديل المظهر">' +
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>' +
          '</button>' +
        '</div>' +
      '</div>' +
    '</aside>';
  }

  function loadCourseFormEnhancements() {
    if (!document.getElementById('basicInfoForm')) return;
    if (document.getElementById('editorCourseFormEnhancements')) return;
    var script = document.createElement('script');
    script.id = 'editorCourseFormEnhancements';
    script.src = 'js/editor-course-form.js?v=4';
    document.body.appendChild(script);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var container = document.getElementById("editorSidebar");
    if (container) {
      var token = localStorage.getItem(EDITOR_TOKEN_KEY);
      var name = '';
      if (token) {
        try {
          var p = JSON.parse(atob(token.split('.')[1]));
          name = p.name || p.email || '';
        } catch (e) {}
      }
      var activePage = document.body.getAttribute("data-page") || "";
      container.innerHTML = buildSidebar(activePage, name);
    }

    var logoutBtn = document.getElementById("editorLogoutBtn");
    if (logoutBtn && !logoutBtn.dataset.ntaBound) {
      logoutBtn.dataset.ntaBound = '1';
      logoutBtn.addEventListener("click", function () {
        localStorage.removeItem(EDITOR_TOKEN_KEY);
        window.location.replace("editor-login.html");
      });
    }

    if (window.NTATheme && typeof window.NTATheme.bindAllToggles === "function") {
      window.NTATheme.bindAllToggles();
    }

    setupMobileNav(container);
    loadCourseFormEnhancements();
  });

  function setupMobileNav(container) {
    if (document.getElementById("ntaNavToggle")) return;
    var btn = document.createElement("button");
    btn.id = "ntaNavToggle";
    btn.className = "nta-nav-toggle";
    btn.type = "button";
    btn.setAttribute("aria-label", "فتح القائمة");
    btn.setAttribute("aria-expanded", "false");
    btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
    var backdrop = document.createElement("div");
    backdrop.id = "ntaNavBackdrop";
    backdrop.className = "nta-nav-backdrop";
    document.body.appendChild(btn);
    document.body.appendChild(backdrop);
    function setOpen(open) {
      document.body.classList.toggle("nta-nav-open", open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    }
    btn.addEventListener("click", function () { setOpen(!document.body.classList.contains("nta-nav-open")); });
    backdrop.addEventListener("click", function () { setOpen(false); });
    if (container) container.addEventListener("click", function (e) { if (e.target.closest("a")) setOpen(false); });
    window.addEventListener("keydown", function (e) { if (e.key === "Escape") setOpen(false); });
  }

  window.showEditorToast = function (msg, type) {
    type = type || "success";
    var container = document.getElementById("editorToastContainer");
    if (!container) {
      container = document.createElement("div");
      container.id = "editorToastContainer";
      container.className = "editor-toast-container";
      document.body.appendChild(container);
    }
    var toast = document.createElement("div");
    toast.className = "editor-toast editor-toast--" + type;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(function () {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 0.3s";
      setTimeout(function () { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 300);
    }, 3500);
  };

  window.editorConfirm = function (opts) {
    return new Promise(function (resolve) {
      var overlay = document.createElement("div");
      overlay.className = "editor-modal-overlay";
      overlay.innerHTML =
        '<div class="editor-modal" role="dialog" aria-modal="true" aria-labelledby="editorConfirmTitle">' +
        '<h2 class="editor-modal__title" id="editorConfirmTitle">' + (opts.title || "تأكيد") + "</h2>" +
        '<div class="editor-modal__body">' + (opts.body || "") + "</div>" +
        '<div class="editor-modal__actions">' +
        '<button type="button" class="btn btn--secondary" id="editorConfirmCancel">' + (opts.cancelLabel || "إلغاء") + "</button>" +
        '<button type="button" class="btn ' + (opts.danger ? "btn--danger" : "btn--primary") + '" id="editorConfirmOk">' + (opts.okLabel || "تأكيد") + "</button>" +
        "</div></div>";
      document.body.appendChild(overlay);

      function keyHandler(e) { if (e.key === "Escape") close(false); }
      function close(result) {
        document.removeEventListener("keydown", keyHandler);
        document.body.removeChild(overlay);
        resolve(result);
      }

      overlay.querySelector("#editorConfirmCancel").addEventListener("click", function () { close(false); });
      overlay.querySelector("#editorConfirmOk").addEventListener("click", function () { close(true); });
      overlay.addEventListener("click", function (e) { if (e.target === overlay) close(false); });
      document.addEventListener("keydown", keyHandler);
      overlay.querySelector("#editorConfirmOk").focus();
    });
  };
})();
