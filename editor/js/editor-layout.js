(function () {
  var EDITOR_TOKEN_KEY = "editor_token";

  /* -- Inject sidebar CSS -- */
  (function () {
    if (document.getElementById('ntaSbCss')) return;
    if (document.querySelector('link[href*="header/header.css"]')) return;
    var l = document.createElement('link');
    l.id = 'ntaSbCss';
    l.rel = 'stylesheet';
    l.href = '/admin/header/header.css?v=4';
    document.head.appendChild(l);
  })();

  /* -- SVG icon helper -- */
  function ic(path) {
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + path + '</svg>';
  }

  function navItem(href, page, icon, label, cur) {
    var cls = 'nta-sidebar__item' + (cur === page ? ' active' : '');
    return '<a href="' + href + '" class="' + cls + '" data-page="' + page + '">' +
      icon + '<span class="nta-sidebar__item-lbl">' + label + '</span></a>';
  }

  function buildSidebar(activePage, name) {
    var ICONS = {
      home:     ic('<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>'),
      courses:  ic('<path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>'),
      materials:ic('<path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>'),
      sessions: ic('<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>'),
      exams:    ic('<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>'),
      planning: ic('<path d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 0a2 2 0 012-2h2a2 2 0 012 2v10a2 2 0 01-2 2h-2a2 2 0 01-2-2"/>'),
      user:     ic('<path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
      logout:   ic('<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>'),
    };

    var onerr = "this.style.display='none';this.nextElementSibling.style.display='flex'";

    var nav =
      navItem('editor-dashboard.html', 'dashboard',  ICONS.home,      'لوحة التحكم',    activePage) +
      navItem('editor-courses.html',   'courses',    ICONS.courses,   'الدورات',         activePage) +
      navItem('editor-materials.html', 'materials',  ICONS.materials, 'المواد التعليمية',activePage) +
      navItem('editor-sessions.html',  'sessions',   ICONS.sessions,  'الجلسات',         activePage) +
      navItem('editor-exams.html',     'exams',      ICONS.exams,     'الاختبارات',      activePage) +
      navItem('editor-planning.html',  'planning',   ICONS.planning,  'التخطيط',         activePage);

    return '<aside class="nta-sidebar">' +
      '<div class="nta-sidebar__brand">' +
        '<a href="editor-dashboard.html" class="nta-sidebar__logo-link">' +
          '<img src="/images/NTA-Logo1.png" alt="" class="nta-sidebar__logo-img" id="ntaLogoImg" onerror="' + onerr + '">' +
          '<span class="nta-sidebar__logo-fallback">NTA</span>' +
          '<div class="nta-sidebar__logo-text">' +
            '<span class="nta-sidebar__logo-main">NTA</span>' +
            '<span class="nta-sidebar__logo-sub">NATIONAL TRAINING ACADEMY</span>' +
            '<span class="nta-sidebar__logo-ar">الأكاديمية الوطنية للتدريب</span>' +
          '</div>' +
        '</a>' +
      '</div>' +
      '<nav class="nta-sidebar__nav" aria-label="قائمة المحرر">' + nav + '</nav>' +
      '<div class="nta-sidebar__footer">' +
        '<div class="nta-sidebar__bottom-row">' +
          '<button type="button" class="nta-sidebar__logout" id="editorLogoutBtn">' +
            ICONS.logout + 'تسجيل الخروج' +
          '</button>' +
          '<button type="button" class="nta-sidebar__theme-btn" id="themeToggle" aria-label="تبديل المظهر" title="تبديل المظهر">' +
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>' +
          '</button>' +
        '</div>' +
      '</div>' +
    '</aside>';
  }

  function apiFetch(url, options) {
    options = options || {};
    var token = localStorage.getItem(EDITOR_TOKEN_KEY);
    var headers = Object.assign({}, options.headers || {});
    if (token) headers.Authorization = 'Bearer ' + token;
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }
    return fetch(url, Object.assign({}, options, { headers: headers })).then(function (res) {
      if (res.status === 401 || res.status === 403) {
        localStorage.removeItem(EDITOR_TOKEN_KEY);
        window.location.replace('editor-login.html');
        throw new Error('Session expired or unauthorized');
      }
      return res;
    });
  }

  function checkOk(res) {
    if (res.ok) return res;
    return res.json().catch(function () { return {}; }).then(function (body) {
      throw new Error(body.detail || body.message || 'Request failed');
    });
  }

  function escapeHtml(value) {
    return String(value || '').replace(/[&<>"]/g, function (ch) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[ch];
    });
  }

  function formatFileSize(bytes) {
    bytes = Number(bytes) || 0;
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  }

  function setCourseFormBusy(isBusy) {
    document.querySelectorAll('#step1 button, #step2 button, #step3 button, #step4 button, #step5 button').forEach(function (btn) {
      btn.disabled = !!isBusy;
    });
  }

  function installCourseFormPersistence() {
    if (!document.getElementById('basicInfoForm') || typeof window.submitCourse !== 'function') return;
    if (window.__ntaCoursePersistenceInstalled) return;
    window.__ntaCoursePersistenceInstalled = true;

    function refreshLinkedData() {
      var id = window.courseId;
      if (!id) return;

      apiFetch('/api/sessions?course_id=' + encodeURIComponent(id))
        .then(checkOk)
        .then(function (res) { return res.json(); })
        .then(function (list) {
          window.sessions = (Array.isArray(list) ? list : []).map(function (s) {
            return {
              id: s.id,
              title: s.title_ar || s.title || '',
              date: s.scheduled_date || ''
            };
          });
          if (typeof window.renderSessions === 'function') window.renderSessions();
        })
        .catch(function () { showEditorToast('تعذّر تحميل جلسات الدورة.', 'error'); });

      apiFetch('/api/materials/' + encodeURIComponent(id))
        .then(checkOk)
        .then(function (res) { return res.json(); })
        .then(function (list) {
          window.materials = (Array.isArray(list) ? list : []).map(function (m) {
            return {
              id: m.id,
              name: m.file_name || m.filename || 'ملف',
              size: formatFileSize(m.file_size),
              type: m.file_type || '',
              path: m.file_path || ''
            };
          });
          if (typeof window.renderMaterials === 'function') window.renderMaterials();
        })
        .catch(function () { showEditorToast('تعذّر تحميل مواد الدورة.', 'error'); });
    }

    function saveSessions(courseId) {
      var list = (window.sessions || []).filter(function (s) { return s.title || s.date || s.id; });
      return Promise.all(list.map(function (s, index) {
        var body = {
          course_id: Number(courseId),
          session_number: index + 1,
          title: s.title || ('Session ' + (index + 1)),
          title_ar: s.title || ('الجلسة ' + (index + 1)),
          scheduled_date: s.date || null,
          duration_minutes: 90,
          location: null,
          notes: null,
          status: 'scheduled'
        };
        return apiFetch(s.id ? '/api/sessions/' + encodeURIComponent(s.id) : '/api/sessions', {
          method: s.id ? 'PUT' : 'POST',
          body: JSON.stringify(body)
        }).then(checkOk);
      }));
    }

    function saveMaterials(courseId) {
      var pending = (window.materials || []).filter(function (m) { return m.file && !m.id; });
      return Promise.all(pending.map(function (m) {
        var form = new FormData();
        form.append('file', m.file);
        form.append('course_id', courseId);
        form.append('category', 'supporting');
        form.append('description', '');
        return apiFetch('/api/materials', { method: 'POST', body: form }).then(checkOk);
      }));
    }

    window.submitCourse = function (status) {
      var payload = {
        title: document.getElementById('titleEn').value.trim() || document.getElementById('titleAr').value.trim(),
        title_ar: document.getElementById('titleAr').value.trim(),
        description: document.getElementById('description').value.trim(),
        duration_weeks: parseInt(document.getElementById('durationWeeks').value, 10) || null,
        total_sessions: parseInt(document.getElementById('totalSessions').value, 10) || (window.sessions || []).length || null,
        status: status,
        short_name: '',
        classification: '',
        image_url: null,
        skill_level: null,
        is_public: true,
        stages: null,
        batch_data: null
      };

      var method = window.courseId ? 'PUT' : 'POST';
      var url = window.courseId ? '/api/courses/' + encodeURIComponent(window.courseId) : '/api/courses';
      setCourseFormBusy(true);
      apiFetch(url, { method: method, body: JSON.stringify(payload) })
        .then(checkOk)
        .then(function (res) { return res.json(); })
        .then(function (data) {
          window.courseId = data.id;
          return Promise.all([saveSessions(data.id), saveMaterials(data.id)]).then(function () { return data; });
        })
        .then(function () {
          var msg = status === 'published' ? 'تم نشر الدورة وحفظ الجلسات والمواد بنجاح.' : 'تم حفظ المسودة والجلسات والمواد بنجاح.';
          showEditorToast(msg, 'success');
          setTimeout(function () { window.location.replace('editor-courses.html'); }, 1200);
        })
        .catch(function (err) {
          setCourseFormBusy(false);
          showEditorToast(err.message || 'حدث خطأ أثناء الحفظ.', 'error');
        });
    };

    window.removeSession = function (idx) {
      var item = (window.sessions || [])[idx];
      if (!item) return;
      editorConfirm({
        title: 'حذف الجلسة؟',
        body: 'هل تريد حذف هذه الجلسة؟',
        okLabel: 'حذف الجلسة',
        cancelLabel: 'إلغاء',
        danger: true
      }).then(function (ok) {
        if (!ok) return;
        var action = item.id ? apiFetch('/api/sessions/' + encodeURIComponent(item.id), { method: 'DELETE' }).then(checkOk) : Promise.resolve();
        action.then(function () {
          window.sessions.splice(idx, 1);
          if (typeof window.renderSessions === 'function') window.renderSessions();
        }).catch(function () { showEditorToast('تعذّر حذف الجلسة.', 'error'); });
      });
    };

    window.removeMaterial = function (idx) {
      var item = (window.materials || [])[idx];
      if (!item) return;
      editorConfirm({
        title: 'حذف المادة؟',
        body: 'هل تريد حذف <strong>' + escapeHtml(item.name) + '</strong>؟ لا يمكن التراجع عن هذا الإجراء.',
        okLabel: 'حذف المادة',
        cancelLabel: 'إلغاء',
        danger: true
      }).then(function (ok) {
        if (!ok) return;
        var action = item.id ? apiFetch('/api/materials/' + encodeURIComponent(item.id), { method: 'DELETE' }).then(checkOk) : Promise.resolve();
        action.then(function () {
          window.materials.splice(idx, 1);
          if (typeof window.renderMaterials === 'function') window.renderMaterials();
        }).catch(function () { showEditorToast('تعذّر حذف المادة.', 'error'); });
      });
    };

    setTimeout(refreshLinkedData, 0);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var container = document.getElementById("editorSidebar");
    if (container) {
      var token = localStorage.getItem(EDITOR_TOKEN_KEY);
      var name = '';
      if (token) {
        try {
          var p = JSON.parse(atob(token.split('.')[1]));
          name = p.name || p.email || '';
        } catch (e) {}
      }
      var activePage = document.body.getAttribute("data-page") || "";
      container.innerHTML = buildSidebar(activePage, name);
    }

    var logoutBtn = document.getElementById("editorLogoutBtn");
    if (logoutBtn && !logoutBtn.dataset.ntaBound) {
      logoutBtn.dataset.ntaBound = '1';
      logoutBtn.addEventListener("click", function () {
        localStorage.removeItem(EDITOR_TOKEN_KEY);
        window.location.replace("editor-login.html");
      });
    }

    if (window.NTATheme && typeof window.NTATheme.bindAllToggles === "function") {
      window.NTATheme.bindAllToggles();
    }

    installCourseFormPersistence();
  });

  /* -- Toast utility (preserved) -- */
  window.showEditorToast = function (msg, type) {
    type = type || "success";
    var container = document.getElementById("editorToastContainer");
    if (!container) {
      container = document.createElement("div");
      container.id = "editorToastContainer";
      container.className = "editor-toast-container";
      document.body.appendChild(container);
    }
    var toast = document.createElement("div");
    toast.className = "editor-toast editor-toast--" + type;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(function () {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 0.3s";
      setTimeout(function () { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 300);
    }, 3500);
  };

  /* -- Confirm modal utility (preserved) -- */
  window.editorConfirm = function (opts) {
    return new Promise(function (resolve) {
      var overlay = document.createElement("div");
      overlay.className = "editor-modal-overlay";
      overlay.innerHTML =
        '<div class="editor-modal" role="dialog" aria-modal="true" aria-labelledby="editorConfirmTitle">' +
        '<h2 class="editor-modal__title" id="editorConfirmTitle">' + (opts.title || "تأكيد") + "</h2>" +
        '<div class="editor-modal__body">' + (opts.body || "") + "</div>" +
        '<div class="editor-modal__actions">' +
        '<button type="button" class="btn btn--secondary" id="editorConfirmCancel">' + (opts.cancelLabel || "إلغاء") + "</button>" +
        '<button type="button" class="btn ' + (opts.danger ? "btn--danger" : "btn--primary") + '" id="editorConfirmOk">' + (opts.okLabel || "تأكيد") + "</button>" +
        "</div></div>";
      document.body.appendChild(overlay);

      function keyHandler(e) { if (e.key === "Escape") close(false); }
      function close(result) {
        document.removeEventListener("keydown", keyHandler);
        document.body.removeChild(overlay);
        resolve(result);
      }

      overlay.querySelector("#editorConfirmCancel").addEventListener("click", function () { close(false); });
      overlay.querySelector("#editorConfirmOk").addEventListener("click", function () { close(true); });
      overlay.addEventListener("click", function (e) { if (e.target === overlay) close(false); });
      document.addEventListener("keydown", keyHandler);
      overlay.querySelector("#editorConfirmOk").focus();
    });
  };
})();
