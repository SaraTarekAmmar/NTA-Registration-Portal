/* Injects the Editor sidebar and wires up shared utilities */
(function () {
  var EDITOR_TOKEN_KEY = "editor_token";

  function getEditorName() {
    try {
      var token = sessionStorage.getItem(EDITOR_TOKEN_KEY);
      if (!token) return "";
      var p = JSON.parse(atob(token.split(".")[1]));
      return p.name || p.email || "";
    } catch (e) { return ""; }
  }

  function buildSidebar(activePage) {
    var nav = [
      { href: "editor-dashboard.html", page: "dashboard", icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>', label: "لوحة التحكم" },
      { href: "editor-courses.html", page: "courses", icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>', label: "الدورات" },
      { href: "editor-materials.html", page: "materials", icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>', label: "المواد التعليمية" },
      { href: "editor-sessions.html", page: "sessions", icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>', label: "الجلسات" },
      { href: "editor-exams.html", page: "exams", icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>', label: "الاختبارات" },
    ];

    var html = '<div class="editor-sidebar">';
    html += '<a href="editor-dashboard.html" class="editor-sidebar__logo">';
    html += '<img src="/images/logo2.png" class="editor-sidebar__logo-img" alt="" onerror="this.style.display=\'none\'">';
    html += '<div><div class="editor-sidebar__logo-text">الأكاديمية الوطنية</div><span class="editor-sidebar__logo-role">Editor</span></div>';
    html += '</a>';
    html += '<nav class="editor-nav" aria-label="قائمة المحرر">';

    nav.forEach(function (item) {
      var cls = "editor-nav__item" + (item.page === activePage ? " active" : "");
      html += '<a href="' + item.href + '" class="' + cls + '"' + (item.page === activePage ? ' aria-current="page"' : '') + '>';

      html += '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">' + item.icon + '</svg>';
      html += item.label + '</a>';
    });

    html += '<div class="editor-nav__divider"></div>';
    html += '<button type="button" class="editor-nav__item editor-nav__item--danger" id="editorLogoutBtn" aria-label="تسجيل الخروج">';
    html += '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>';
    html += 'تسجيل الخروج</button>';
    html += '</nav></div>';
    return html;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var sidebarContainer = document.getElementById("editorSidebar");
    if (sidebarContainer) {
      var activePage = document.body.getAttribute("data-page") || "";
      sidebarContainer.innerHTML = buildSidebar(activePage);
    }

    var logoutBtn = document.getElementById("editorLogoutBtn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", function () {
        sessionStorage.removeItem(EDITOR_TOKEN_KEY);
        window.location.replace("editor-login.html");
      });
    }
  });

  /* Toast utility */
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

  /* Confirm modal utility */
  window.editorConfirm = function (opts) {
    return new Promise(function (resolve) {
      var overlay = document.createElement("div");
      overlay.className = "editor-modal-overlay";
      overlay.innerHTML =
        '<div class="editor-modal" role="dialog" aria-modal="true" aria-labelledby="editorConfirmTitle">' +
        '<h2 class="editor-modal__title" id="editorConfirmTitle">' + (opts.title || "تأكيد") + '</h2>' +
        '<div class="editor-modal__body">' + (opts.body || "") + '</div>' +
        '<div class="editor-modal__actions">' +
        '<button type="button" class="btn btn--secondary" id="editorConfirmCancel">' + (opts.cancelLabel || "إلغاء") + '</button>' +
        '<button type="button" class="btn ' + (opts.danger ? "btn--danger" : "btn--primary") + '" id="editorConfirmOk">' + (opts.okLabel || "تأكيد") + '</button>' +
        '</div></div>';
      document.body.appendChild(overlay);

      function keyHandler(e) {
        if (e.key === "Escape") close(false);
      }

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
