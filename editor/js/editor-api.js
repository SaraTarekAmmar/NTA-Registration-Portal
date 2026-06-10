/* Editor API client — authenticated fetch with JSON helpers */
(function () {
  var EDITOR_TOKEN_KEY = "editor_token";
  var BASE = "/api";

  function getToken() {
    return sessionStorage.getItem(EDITOR_TOKEN_KEY);
  }

  function authHeaders(extra) {
    var h = Object.assign({ "Content-Type": "application/json" }, extra || {});
    var t = getToken();
    if (t) h["Authorization"] = "Bearer " + t;
    return h;
  }

  function handleResponse(res) {
    if (res.status === 401 || res.status === 403) {
      sessionStorage.removeItem(EDITOR_TOKEN_KEY);
      window.location.replace("editor-login.html");
      return Promise.reject(new Error("Session expired or unauthorized"));
    }
    return res;
  }

  function request(method, path, body, extraHeaders) {
    var opts = {
      method: method,
      headers: authHeaders(extraHeaders)
    };
    if (body !== undefined && body !== null) {
      opts.body = JSON.stringify(body);
    }
    return fetch(BASE + path, opts).then(handleResponse).catch(function (err) {
      if (err && err.message === "Session expired or unauthorized") return Promise.reject(err);
      console.error("API request failed:", err);
      return Promise.reject(err);
    });
  }

  window.EditorAPI = {
    get: function (path, extraHeaders) {
      return request("GET", path, null, extraHeaders);
    },
    post: function (path, body, extraHeaders) {
      return request("POST", path, body, extraHeaders);
    },
    put: function (path, body, extraHeaders) {
      return request("PUT", path, body, extraHeaders);
    },
    patch: function (path, body, extraHeaders) {
      return request("PATCH", path, body, extraHeaders);
    },
    del: function (path, extraHeaders) {
      return request("DELETE", path, null, extraHeaders);
    },
    /* Upload multipart form data — does NOT set Content-Type (browser sets boundary) */
    upload: function (path, formData, extraHeaders) {
      var headers = Object.assign({}, extraHeaders || {});
      var t = getToken();
      if (t) headers["Authorization"] = "Bearer " + t;
      return fetch(BASE + path, { method: "POST", headers: headers, body: formData })
        .then(handleResponse)
        .catch(function (err) {
          if (err && err.message === "Session expired or unauthorized") return Promise.reject(err);
          console.error("Upload failed:", err);
          return Promise.reject(err);
        });
    },
    fetch: function (url, options) {
      options = options || {};
      var headers = authHeaders(options.headers);
      return fetch(url, Object.assign({}, options, { headers: headers }))
        .then(handleResponse);
    }
  };
})();
