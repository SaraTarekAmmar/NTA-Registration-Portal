/* Editor navigation helpers */
(function () {
  var EDITOR_PAGES = {
    dashboard: "editor-dashboard.html",
    courses:   "editor-courses.html",
    course:    "editor-course-form.html",
    materials: "editor-materials.html",
    sessions:  "editor-sessions.html",
    exams:     "editor-exams.html",
    final:     "editor-courses.html",
    login:     "editor-login.html"
  };

  function goTo(page, params) {
    var base = EDITOR_PAGES[page] || page;
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
    var base = EDITOR_PAGES[page] || page;
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

  function openCourseForm(courseId) {
    goTo("course", courseId ? { id: courseId } : undefined);
  }

  window.EditorFlow = {
    goTo: goTo,
    replace: replace,
    getParam: getParam,
    openCourseForm: openCourseForm,
    pages: EDITOR_PAGES
  };
})();
