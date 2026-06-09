/* Editor auth utilities — non-enforcing helpers for reading session state */
(function () {
  var EDITOR_TOKEN_KEY = "editor_token";

  function parseJwt(token) {
    try {
      return JSON.parse(atob(token.split(".")[1]));
    } catch (e) {
      return null;
    }
  }

  function getToken() {
    return sessionStorage.getItem(EDITOR_TOKEN_KEY);
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
    sessionStorage.removeItem(EDITOR_TOKEN_KEY);
    window.location.replace("editor-login.html");
  }

  window.EditorAuth = {
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
