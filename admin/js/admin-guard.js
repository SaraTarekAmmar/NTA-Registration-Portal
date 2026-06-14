(function () {
  var ADMIN_TOKEN_KEY = "admin_token";

  function parseJwt(token) {
    try {
      var base64Payload = token.split(".")[1];
      return JSON.parse(atob(base64Payload));
    } catch (e) {
      return null;
    }
  }

  function requireAdmin() {
    var token = localStorage.getItem(ADMIN_TOKEN_KEY);
    if (!token) {
      window.location.replace("admin-login.html");
      return;
    }
    var payload = parseJwt(token);
    if (!payload || !["admin", "superadmin"].includes(payload.role)) {
      localStorage.removeItem(ADMIN_TOKEN_KEY);
      window.location.replace("admin-login.html");
      return;
    }
    var now = Math.floor(Date.now() / 1000);
    if (payload.exp && payload.exp < now) {
      localStorage.removeItem(ADMIN_TOKEN_KEY);
      window.location.replace("admin-login.html");
      return;
    }
  }

  function buildHeaders(options) {
    options = options || {};
    var headers = Object.assign({}, options.headers || {});
    var token = localStorage.getItem(ADMIN_TOKEN_KEY);
    if (token) headers.Authorization = "Bearer " + token;
    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }
    return headers;
  }

  requireAdmin();

  window.adminAuth = {
    getToken: function () {
      return localStorage.getItem(ADMIN_TOKEN_KEY);
    },
    logout: function () {
      localStorage.removeItem(ADMIN_TOKEN_KEY);
      window.location.replace("admin-login.html");
    },
    fetch: function (url, options) {
      options = options || {};
      return fetch(url, Object.assign({}, options, { headers: buildHeaders(options) })).then(function (res) {
        if (res.status === 401 || res.status === 403) {
          localStorage.removeItem(ADMIN_TOKEN_KEY);
          window.location.replace("admin-login.html");
          return Promise.reject("Session expired or unauthorized");
        }
        return res;
      });
    }
  };
})();
