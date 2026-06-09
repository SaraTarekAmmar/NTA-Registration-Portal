/* Admin auth utilities — non-enforcing helpers for reading session state */
(function () {
  var ADMIN_TOKEN_KEY = "admin_token";

  function parseJwt(token) {
    try {
      return JSON.parse(atob(token.split(".")[1]));
    } catch (e) {
      return null;
    }
  }

  function getToken() {
    return sessionStorage.getItem(ADMIN_TOKEN_KEY);
  }

  function getPayload() {
    var t = getToken();
    return t ? parseJwt(t) : null;
  }

  function isExpired() {
    var p = getPayload();
    if (!p) return true;
    return p.exp ? Math.floor(Date.now() / 1000) >= p.exp : false;
  }

  function isAuthenticated() {
    return !!getToken() && !isExpired();
  }

  function logout() {
    sessionStorage.removeItem(ADMIN_TOKEN_KEY);
    window.location.replace("admin-login.html");
  }

  window.AdminAuth = {
    getToken: getToken,
    getPayload: getPayload,
    isAuthenticated: isAuthenticated,
    isExpired: isExpired,
    logout: logout,
    parseJwt: parseJwt,
    getName: function () {
      var p = getPayload();
      return p ? (p.name || p.email || "") : "";
    },
    getRole: function () {
      var p = getPayload();
      return p ? (p.role || "") : "";
    }
  };
})();
