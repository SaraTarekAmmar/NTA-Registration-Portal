(function () {
  (function ensureSidebarCss() {
    if (document.getElementById("ntaSbCss")) return;
    if (document.querySelector('link[href*="header/header.css"]')) return;

    var link = document.createElement("link");
    link.id = "ntaSbCss";
    link.rel = "stylesheet";
    link.href = "/header/header.css?v=4";
    document.head.appendChild(link);
  })();

  function icon(path) {
    return (
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
      path +
      "</svg>"
    );
  }

  function navLabel(text) {
    return '<div class="nta-sidebar__nav-lbl">' + text + "</div>";
  }

  function divider() {
    return '<div class="nta-sidebar__divider"></div>';
  }

  function navItem(href, page, iconSvg, label, currentPage) {
    var cls = "nta-sidebar__item" + (currentPage === page ? " active" : "");
    return (
      '<a href="' +
      href +
      '" class="' +
      cls +
      '" data-page="' +
      page +
      '">' +
      iconSvg +
      '<span class="nta-sidebar__item-lbl">' +
      label +
      "</span></a>"
    );
  }

  function readSession() {
    try {
      return JSON.parse(sessionStorage.getItem("ntaTrainee") || "{}");
    } catch (error) {
      return {};
    }
  }

  function isAllowedRole(role) {
    return (
      role === "admission_manager" ||
      role === "committee_member" ||
      role === "admin"
    );
  }

  function roleLabel(role) {
    if (role === "committee_member") return "عضو لجنة";
    if (role === "admin") return "مدير النظام";
    return "مدير القبول";
  }

  function currentRelativeHref() {
    return window.location.pathname + window.location.search;
  }

  function contextualNav(page, icons) {
    if (page === "admission-profile") {
      return navItem(
        currentRelativeHref(),
        "admission-profile",
        icons.user,
        "ملف المتقدم",
        page,
      );
    }

    if (page === "admission-review") {
      return navItem(
        currentRelativeHref(),
        "admission-review",
        icons.flow,
        "مراجعة المراحل",
        page,
      );
    }

    return "";
  }

  function buildSidebar(page, roleText) {
    var icons = {
      home: icon(
        '<path d="M3 12l2-2m0 0 7-7 7 7M5 10v10a1 1 0 0 0 1 1h3m10-11 2 2m-2-2v10a1 1 0 0 1-1 1h-3m-6 0a1 1 0 0 0 1-1v-4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v4a1 1 0 0 0 1 1m-6 0h6"/>',
      ),
      cands: icon(
        '<circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>',
      ),
      flow: icon('<path d="M4 6h16M4 12h8m-8 6h16"/>'),
      user: icon(
        '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
      ),
      tickets: icon(
        '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>',
      ),
      logout: icon(
        '<path d="M17 16l4-4m0 0-4-4m4 4H7m6 4v1a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3h4a3 3 0 0 1 3 3v1"/>',
      ),
    };

    var onError =
      "this.style.display='none';this.nextElementSibling.style.display='flex'";

    var nav =
      navLabel("الرئيسية") +
      navItem("/candidates.html", "candidates", icons.home, "لوحة القبول", page) +
      divider() +
      navLabel("المتابعة") +
      navItem(
        "/candidates.html",
        "candidates",
        icons.cands,
        "قائمة المرشحين",
        page,
      ) +
      contextualNav(page, icons) +
      navItem(
        "/tickets/tickets.html",
        "tickets",
        icons.tickets,
        "مركز التذاكر",
        page,
      );

    return (
      '<aside class="nta-sidebar">' +
      '<div class="nta-sidebar__brand">' +
      '<a href="/candidates.html" class="nta-sidebar__logo-link">' +
      '<img src="/images/NTA-Logo1.png" alt="" class="nta-sidebar__logo-img" id="ntaLogoImg" onerror="' +
      onError +
      '">' +
      '<span class="nta-sidebar__logo-fallback">NTA</span>' +
      '<div class="nta-sidebar__logo-text">' +
      '<span class="nta-sidebar__logo-main">NTA</span>' +
      '<span class="nta-sidebar__logo-sub">NATIONAL TRAINING ACADEMY</span>' +
      '<span class="nta-sidebar__logo-ar">الأكاديمية الوطنية للتدريب</span>' +
      "</div></a>" +
      '<div class="nta-sidebar__role"><span class="nta-sidebar__role-dot"></span>' +
      roleText +
      "</div>" +
      "</div>" +
      '<nav class="nta-sidebar__nav" aria-label="قائمة مركز القبول">' +
      nav +
      "</nav>" +
      '<div class="nta-sidebar__footer">' +
      '<div class="nta-sidebar__bottom-row">' +
      '<button type="button" class="nta-sidebar__logout" id="logoutBtn">' +
      icons.logout +
      "تسجيل الخروج" +
      "</button>" +
      '<button type="button" class="nta-sidebar__theme-btn" id="themeToggle" aria-label="تبديل المظهر" title="تبديل المظهر">' +
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364-.707-.707M6.343 6.343l-.707-.707m12.728 0-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0z"/></svg>' +
      "</button>" +
      "</div></div></aside>"
    );
  }

  document.addEventListener("DOMContentLoaded", function () {
    var container = document.getElementById("ntaHeader");
    if (!container) return;

    var session = readSession();
    if (!isAllowedRole(session.role)) return;

    var page = document.body.getAttribute("data-page") || "";
    container.innerHTML = buildSidebar(page, roleLabel(session.role));

    var logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn && !logoutBtn.dataset.ntaBound) {
      logoutBtn.dataset.ntaBound = "1";
      logoutBtn.addEventListener("click", function () {
        sessionStorage.removeItem("ntaTrainee");
        window.location.href = "/index.html";
      });
    }

    if (
      window.NTATheme &&
      typeof window.NTATheme.bindAllToggles === "function"
    ) {
      window.NTATheme.bindAllToggles();
    }

    setupMobileNav(container);
  });

  function setupMobileNav(container) {
    if (document.getElementById("ntaNavToggle")) return;

    var btn = document.createElement("button");
    btn.id = "ntaNavToggle";
    btn.className = "nta-nav-toggle";
    btn.type = "button";
    btn.setAttribute("aria-label", "فتح القائمة");
    btn.setAttribute("aria-expanded", "false");
    btn.innerHTML =
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';

    var backdrop = document.createElement("div");
    backdrop.id = "ntaNavBackdrop";
    backdrop.className = "nta-nav-backdrop";

    document.body.appendChild(btn);
    document.body.appendChild(backdrop);

    function setOpen(open) {
      document.body.classList.toggle("nta-nav-open", open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    }

    btn.addEventListener("click", function () {
      setOpen(!document.body.classList.contains("nta-nav-open"));
    });

    backdrop.addEventListener("click", function () {
      setOpen(false);
    });

    if (container) {
      container.addEventListener("click", function (event) {
        if (event.target.closest("a")) setOpen(false);
      });
    }

    window.addEventListener("keydown", function (event) {
      if (event.key === "Escape") setOpen(false);
    });
  }

  window.authenticatedFetch = function (url, options) {
    options = options || {};

    var session = readSession();
    var token = session.token;
    var headers = Object.assign({}, options.headers || {});

    if (token) {
      headers.Authorization = "Bearer " + token;
    }

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    return fetch(url, Object.assign({}, options, { headers: headers })).then(
      function (response) {
        if (response.status === 401) {
          sessionStorage.removeItem("ntaTrainee");
          window.location.href = "/index.html";
          return Promise.reject("Session expired");
        }

        return response;
      },
    );
  };
})();
