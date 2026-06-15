/**
 * Coordinator Auth Guard
 * Checks coordinator_token in localStorage, verifies role, redirects if invalid.
 * Exposes window.coordinatorAuth with .fetch() wrapper.
 */
(function () {
  var TOKEN_KEY = "coordinator_token";
  var LOGIN_PAGE = "coordinator-login.html";

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

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function isLoginPage() {
    return location.pathname.indexOf("coordinator-login") !== -1;
  }

  function redirectToLogin() {
    if (!isLoginPage()) {
      location.href = LOGIN_PAGE;
    }
  }

  function check() {
    var token = getToken();
    if (!token) { redirectToLogin(); return null; }
    var payload = parseJwt(token);
    if (!payload || payload.role !== "coordinator") {
      localStorage.removeItem(TOKEN_KEY);
      redirectToLogin();
      return null;
    }
    // Check expiry
    if (payload.exp && Date.now() / 1000 > payload.exp) {
      localStorage.removeItem(TOKEN_KEY);
      redirectToLogin();
      return null;
    }
    return payload;
  }

  function authFetch(url, opts) {
    opts = opts || {};
    var token = getToken();
    var headers = Object.assign({"Content-Type": "application/json"}, opts.headers || {});
    if (token) headers["Authorization"] = "Bearer " + token;
    return fetch(url, Object.assign({}, opts, { headers: headers }));
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    location.href = LOGIN_PAGE;
  }

  // Run guard on non-login pages
  var payload = null;
  if (!isLoginPage()) {
    payload = check();
  }

  window.coordinatorAuth = {
    TOKEN_KEY: TOKEN_KEY,
    getToken: getToken,
    parseJwt: parseJwt,
    check: check,
    fetch: authFetch,
    logout: logout,
    payload: payload,
  };
})();
