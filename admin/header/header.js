(function () {
  document.addEventListener("DOMContentLoaded", function () {
    // Nuke the old header.html from cache
    if (window.caches) {
      caches.keys().then(function (names) {
        names.forEach(function (name) {
          caches.delete(name);
        });
      });
    }

    var container = document.getElementById("ntaHeader");
    if (!container) return;

    // Always inject HTML directly — never fetch header.html
    container.innerHTML =
      '<header class="nta-header">' +
      '<a href="index.html" class="nta-header__logo">' +
      '<img src="images/logo2.png" alt="" class="nta-header__logo-img" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">' +
      '<span class="nta-header__logo-fallback">NTA</span>' +
      '<div class="nta-header__logo-text">' +
      '<span class="nta-header__logo-main">NTA</span>' +
      '<span class="nta-header__logo-sub">NATIONAL TRAINING ACADEMY</span>' +
      '<span class="nta-header__logo-ar">الأكاديمية الوطنية للتدريب</span>' +
      "</div></a>" +
      '<div class="nta-header__center">' +
      '<span class="nta-header__section-label" id="headerSectionLabel">إدارة المهارات</span>' +
      '<nav class="nta-header__nav">' +
      '<a href="index.html" class="nta-header__chip" data-page="login" id="headerHomeChip">' +
      '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="17" height="17"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 11l9-7 9 7M5 12h14v7a2 2 0 01-2 2H7a2 2 0 01-2-2z"/></svg>' +
      "<span>الرئيسية</span></a>" +
      '<a href="courses.html?filter=my" class="nta-header__chip" data-page="courses" id="headerCoursesChip" style="display:none">' +
      '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="17" height="17"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h10M4 18h7"/></svg>' +
      "<span>دوراتي</span></a>" +
      '<a href="profile.html" class="nta-header__chip" data-page="profile" id="headerProfileChip" style="display:none">' +
      '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="17" height="17"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM4 21a8 8 0 0116 0"/></svg>' +
      "<span>الملف الشخصي</span></a>" +
      '<a href="admin-candidates.html" class="nta-header__chip" data-page="admin-candidates" id="headerUsersChip" style="display:none">' +
      '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="17" height="17"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>' +
      "<span>قائمة المرشحين</span></a>" +
      '<a href="admin-trainees.html" class="nta-header__chip" data-page="admin-trainees" id="headerAttendanceChip" style="display:none">' +
      '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="17" height="17"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>' +
      "<span>قائمة المتدربين</span></a>" +
      '<a href="admin-permissions.html" class="nta-header__chip" data-page="admin-permissions" id="headerPermissionsChip" style="display:none">' +
      '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="17" height="17"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>' +
      "<span>الإذونات</span></a>" +
      "</nav></div>" +
      '<div class="nta-header__actions">' +
      '<a href="index.html#loginCard" class="nta-header__btn nta-header__btn--login" id="headerLoginBtn">' +
      '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="18" height="18"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>' +
      "<span>تسجيل الدخول</span></a>" +
      '<button type="button" class="nta-header__btn nta-header__btn--logout" id="logoutBtn">تسجيل الخروج</button>' +
      '<button type="button" class="nta-header__theme" id="themeToggle" aria-label="تبديل الوضع">' +
      '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>' +
      "</button></div></header>";

    var page = document.body.getAttribute("data-page");
    var session = {};
    // Support new separated tokens first, fall back to legacy ntaTrainee
    var adminToken = sessionStorage.getItem("admin_token");
    if (adminToken) {
      try {
        var ap = JSON.parse(atob(adminToken.split(".")[1]));
        session = { token: adminToken, role: ap.role };
      } catch(e) {}
    }
    if (!session.token) {
      try {
        session = JSON.parse(sessionStorage.getItem("ntaTrainee") || "{}");
      } catch (e) {}
    }

    var isTrainee = session.role === "trainee";
    var isAdmin = session.role === "admin";
    var isEditor = session.role === "editor";
    var isLoggedIn = isTrainee || isAdmin || isEditor;

    var loginBtn = document.getElementById("headerLoginBtn");
    var logoutBtn = document.getElementById("logoutBtn");
    var sectionLabel = document.getElementById("headerSectionLabel");
    var homeChip = document.getElementById("headerHomeChip");
    var coursesChip = document.getElementById("headerCoursesChip");
    var profileChip = document.getElementById("headerProfileChip");
    var usersChip = document.getElementById("headerUsersChip");
    var permissionsChip = document.getElementById("headerPermissionsChip");
    var attendanceChip = document.getElementById("headerAttendanceChip");

    if (loginBtn) loginBtn.style.display = isLoggedIn ? "none" : "inline-flex";
    if (logoutBtn)
      logoutBtn.style.display = isLoggedIn ? "inline-flex" : "none";

    if (isAdmin) {
      if (homeChip) {
        homeChip.href = "admin-dashboard.html";
        homeChip.setAttribute("data-page", "admin");
        var s = homeChip.querySelector("span");
        if (s) s.textContent = "لوحة التحكم";
      }
      if (usersChip) usersChip.style.display = "inline-flex";
      if (permissionsChip) permissionsChip.style.display = "inline-flex";
      if (attendanceChip) attendanceChip.style.display = "inline-flex";
      if (sectionLabel) sectionLabel.textContent = "لوحة التحكم";
    } else if (isEditor) {
      if (homeChip) {
        homeChip.href = "admin-courses.html";
        homeChip.setAttribute("data-page", "admin-courses");
        var se = homeChip.querySelector("span");
        if (se) se.textContent = "الدورات";
      }
      // Show recommendations for editors too
      if (attendanceChip) {
          attendanceChip.href = "recommendations.html";
          attendanceChip.setAttribute("data-page", "recommendations");
          var sa = attendanceChip.querySelector("span");
          if (sa) sa.textContent = "التوصيات";
          attendanceChip.style.display = "inline-flex";
      }
      if (sectionLabel) sectionLabel.textContent = "إدارة الدورات";
    } else if (isTrainee) {
      if (homeChip) {
        homeChip.href = "courses.html";
        homeChip.setAttribute("data-page", "courses-all");
        var st = homeChip.querySelector("span");
        if (st) st.textContent = "الدورات";
      }
      if (coursesChip) coursesChip.style.display = "inline-flex";
      if (profileChip) profileChip.style.display = "inline-flex";
      if (sectionLabel) sectionLabel.textContent = "إدارة المهارات";
    }

    // Highlight active chip
    if (page) {
      var allChips = container.querySelectorAll(".nta-header__chip");
      for (var i = 0; i < allChips.length; i++) {
        allChips[i].classList.toggle(
          "active",
          allChips[i].getAttribute("data-page") === page,
        );
      }
    }

    if (window.NTATheme && typeof window.NTATheme.bindAllToggles === "function") {
      window.NTATheme.bindAllToggles();
    }

    // Logout
    if (logoutBtn && !logoutBtn.dataset.ntaLogoutBound) {
      logoutBtn.dataset.ntaLogoutBound = "1";
      logoutBtn.addEventListener("click", function () {
        try {
          sessionStorage.removeItem("admin_token");
          sessionStorage.removeItem("ntaTrainee");
        } catch (e) {}
        window.location.href = "admin-login.html";
      });
    }
  });

  window.authenticatedFetch = function (url, options) {
    options = options || {};
    var token = sessionStorage.getItem("admin_token");
    if (!token) {
      try { token = JSON.parse(sessionStorage.getItem("ntaTrainee") || "{}").token; } catch(e) {}
    }
    var headers = Object.assign(
      { "Content-Type": "application/json" },
      options.headers || {},
    );
    if (token) headers["Authorization"] = "Bearer " + token;
    return fetch(url, Object.assign({}, options, { headers: headers })).then(
      function (res) {
        if (res.status === 401) {
          sessionStorage.removeItem("admin_token");
          sessionStorage.removeItem("ntaTrainee");
          window.location.href = "admin-login.html";
          return Promise.reject("Session expired");
        }
        return res;
      },
    );
  };
})();
