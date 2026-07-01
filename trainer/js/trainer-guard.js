(function () {
  var TRAINER_TOKEN_KEY = "ntaTrainer";

  function readTrainerSession() {
    var raw = localStorage.getItem(TRAINER_TOKEN_KEY);
    if (!raw) return null;
    try {
      var session = JSON.parse(raw);
      if (session && typeof session === "object") return session;
    } catch (e) {}
    if (raw.split(".").length === 3) return { token: raw };
    return null;
  }

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

  function requireTrainer() {
    var session = readTrainerSession();
    if (!session) {
      redirectToLogin();
      return;
    }
    try {
      var token = session.token;
      if (!token) {
        redirectToLogin();
        return;
      }
      var payload = parseJwt(token);
      if (!payload || payload.role !== "trainer") {
        localStorage.removeItem(TRAINER_TOKEN_KEY);
        redirectToLogin();
        return;
      }
      var now = Math.floor(Date.now() / 1000);
      if (payload.exp && payload.exp < now) {
        localStorage.removeItem(TRAINER_TOKEN_KEY);
        redirectToLogin();
        return;
      }
    } catch (e) {
      localStorage.removeItem(TRAINER_TOKEN_KEY);
      redirectToLogin();
    }
  }

  function redirectToLogin() {
    var currentPath = window.location.pathname || '';
    var redirectUrl = 'index.html';
    if (currentPath.includes('/view trainees/') || currentPath.includes('/generate quiz/')) {
      redirectUrl = '../' + redirectUrl;
    }
    window.location.replace(redirectUrl);
  }

  requireTrainer();
})();
