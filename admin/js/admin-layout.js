/* Admin layout utilities — sets active nav chip and exposes page helpers */
(function () {
  var ADMIN_TOKEN_KEY = "admin_token";

  function getPayload() {
    try {
      var t = localStorage.getItem(ADMIN_TOKEN_KEY);
      return t ? JSON.parse(atob(t.split(".")[1])) : null;
    } catch (e) { return null; }
  }

  /* Highlight the active nav chip in header.js based on data-page attribute */
  function markActive() {
    var page = document.body.getAttribute("data-page");
    if (!page) return;
    var chips = document.querySelectorAll(".nta-header__chip[data-page]");
    for (var i = 0; i < chips.length; i++) {
      chips[i].classList.toggle("active", chips[i].getAttribute("data-page") === page);
    }
  }

  /* Set the <title> and the header section label */
  function setTitle(title) {
    if (title) document.title = title + " - الأكاديمية الوطنية للتدريب";
    var lbl = document.getElementById("headerSectionLabel");
    if (lbl && title) lbl.textContent = title;
  }

  /* Inject user name from JWT into an element by ID */
  function renderUserName(elementId) {
    var el = document.getElementById(elementId);
    if (!el) return;
    var p = getPayload();
    el.textContent = p ? (p.name || p.email || "مدير") : "مدير";
  }

  /* Show a page-level toast notification */
  function showToast(msg, type) {
    type = type || "success";
    var ct = document.getElementById("toastContainer");
    if (!ct) {
      ct = document.createElement("div");
      ct.id = "toastContainer";
      ct.className = "toast-container";
      ct.style.cssText = "position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;display:flex;flex-direction:column;gap:0.5rem";
      document.body.appendChild(ct);
    }
    var t = document.createElement("div");
    t.className = "toast toast--" + type;
    t.textContent = msg;
    ct.appendChild(t);
    setTimeout(function () {
      t.style.opacity = "0";
      t.style.transition = "opacity 0.3s";
      setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 300);
    }, 3500);
  }

  document.addEventListener("DOMContentLoaded", function () {
    markActive();
  });

  window.AdminLayout = {
    markActive: markActive,
    setTitle: setTitle,
    renderUserName: renderUserName,
    showToast: showToast
  };
})();
