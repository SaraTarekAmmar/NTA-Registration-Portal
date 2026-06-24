(function () {
  var EDITOR_TOKEN_KEY = "editor_token";

  function parseJwt(token) {
    try {
      var base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
      return JSON.parse(decodeURIComponent(atob(base64).split("").map(function (c) {
        return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
      }).join("")));
    } catch (e) {
      return null;
    }
  }

  function requireEditor() {
    var token = localStorage.getItem(EDITOR_TOKEN_KEY);
    if (!token) {
      window.location.replace("editor-login.html");
      return;
    }
    var payload = parseJwt(token);
    if (!payload || payload.role !== "editor") {
      localStorage.removeItem(EDITOR_TOKEN_KEY);
      window.location.replace("editor-login.html");
      return;
    }
    var now = Math.floor(Date.now() / 1000);
    if (payload.exp && payload.exp < now) {
      localStorage.removeItem(EDITOR_TOKEN_KEY);
      window.location.replace("editor-login.html");
      return;
    }
  }

  function buildHeaders(options) {
    options = options || {};
    var headers = Object.assign({}, options.headers || {});
    var token = localStorage.getItem(EDITOR_TOKEN_KEY);
    if (token) headers.Authorization = "Bearer " + token;
    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }
    return headers;
  }

  requireEditor();

  window.editorAuth = {
    getToken: function () {
      return localStorage.getItem(EDITOR_TOKEN_KEY);
    },
    logout: function () {
      localStorage.removeItem(EDITOR_TOKEN_KEY);
      window.location.replace("editor-login.html");
    },
    fetch: function (url, options) {
      options = options || {};
      return fetch(url, Object.assign({}, options, { headers: buildHeaders(options) })).then(function (res) {
        if (res.status === 401 || res.status === 403) {
          localStorage.removeItem(EDITOR_TOKEN_KEY);
          window.location.replace("editor-login.html");
          return Promise.reject("Session expired or unauthorized");
        }
        return res;
      });
    }
  };
})();
