(function () {
  var EDITOR_TOKEN_KEY = "editor_token";

  function parseJwt(token) {
    try {
      var base64Payload = token.split(".")[1];
      return JSON.parse(atob(base64Payload));
    } catch (e) {
      return null;
    }
  }

  function requireEditor() {
    var token = sessionStorage.getItem(EDITOR_TOKEN_KEY);
    if (!token) {
      window.location.replace("editor-login.html");
      return;
    }
    var payload = parseJwt(token);
    if (!payload || payload.role !== "editor") {
      sessionStorage.removeItem(EDITOR_TOKEN_KEY);
      window.location.replace("editor-login.html");
      return;
    }
    var now = Math.floor(Date.now() / 1000);
    if (payload.exp && payload.exp < now) {
      sessionStorage.removeItem(EDITOR_TOKEN_KEY);
      window.location.replace("editor-login.html");
      return;
    }
  }

  requireEditor();

  window.editorAuth = {
    getToken: function () {
      return sessionStorage.getItem(EDITOR_TOKEN_KEY);
    },
    logout: function () {
      sessionStorage.removeItem(EDITOR_TOKEN_KEY);
      window.location.replace("editor-login.html");
    },
    fetch: function (url, options) {
      options = options || {};
      var token = sessionStorage.getItem(EDITOR_TOKEN_KEY);
      var headers = Object.assign({ "Content-Type": "application/json" }, options.headers || {});
      if (token) headers["Authorization"] = "Bearer " + token;
      return fetch(url, Object.assign({}, options, { headers: headers })).then(function (res) {
        if (res.status === 401 || res.status === 403) {
          sessionStorage.removeItem(EDITOR_TOKEN_KEY);
          window.location.replace("editor-login.html");
          return Promise.reject("Session expired or unauthorized");
        }
        return res;
      });
    }
  };
})();
