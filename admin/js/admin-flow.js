/* Admin navigation helpers */
(function () {
  var ADMIN_PAGES = {
    dashboard:  "admin-dashboard.html",
    candidates: "admin-candidates.html",
    profile:    "admin-candidate-profile.html",
    trainees:   "admin-trainees.html",
    courses:    "admin-courses.html",
    review:     "admin-stage-review.html",
    final:      "admin-final.html",
    permissions:"admin-permissions.html",
    login:      "admin-login.html"
  };

  function goTo(page, params) {
    var base = ADMIN_PAGES[page] || page;
    if (params) {
      var qs = Object.keys(params)
        .filter(function (k) { return params[k] !== undefined && params[k] !== null; })
        .map(function (k) { return encodeURIComponent(k) + "=" + encodeURIComponent(params[k]); })
        .join("&");
      if (qs) base += "?" + qs;
    }
    window.location.href = base;
  }

  function replace(page, params) {
    var base = ADMIN_PAGES[page] || page;
    if (params) {
      var qs = Object.keys(params)
        .filter(function (k) { return params[k] !== undefined && params[k] !== null; })
        .map(function (k) { return encodeURIComponent(k) + "=" + encodeURIComponent(params[k]); })
        .join("&");
      if (qs) base += "?" + qs;
    }
    window.location.replace(base);
  }

  function getParam(key) {
    try {
      return new URLSearchParams(window.location.search).get(key);
    } catch (e) {
      var match = window.location.search.match(
        new RegExp("[?&]" + encodeURIComponent(key) + "=([^&]*)")
      );
      return match ? decodeURIComponent(match[1]) : null;
    }
  }

  function openProfile(candidateId) {
    goTo("profile", { id: candidateId });
  }

  function openReview(candidateId, stage) {
    var p = { id: candidateId };
    if (stage) p.stage = stage;
    goTo("review", p);
  }

  window.AdminFlow = {
    goTo: goTo,
    replace: replace,
    getParam: getParam,
    openProfile: openProfile,
    openReview: openReview,
    pages: ADMIN_PAGES
  };
})();
