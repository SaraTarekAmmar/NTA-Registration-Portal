(function () {
  var EDITOR_TOKEN_KEY = "editor_token";

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

  function refreshLinkedData() {
    var id = window.courseId;
    if (!id) return;

    apiFetch('/api/sessions?course_id=' + encodeURIComponent(id))
      .then(checkOk)
      .then(function (res) { return res.json(); })
      .then(function (list) {
        window.sessions = (Array.isArray(list) ? list : []).map(function (s) {
          var d = s.session_date || s.scheduled_date || '';
          return {
            id: s.id,
            title: s.topic || s.title_ar || s.title || '',
            date: typeof d === 'string' ? d.slice(0, 10) : ''
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

  function buildCoursePayload(status) {
    return {
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
  }

  function buildSessionPayloads(courseId) {
    return (window.sessions || []).filter(function (s) {
      return s.title || s.date || s.id;
    }).map(function (s, index) {
      return {
        id: s.id || null,
        course_id: Number(courseId || window.courseId || 0),
        session_number: index + 1,
        title: s.title || ('Session ' + (index + 1)),
        title_ar: s.title || ('الجلسة ' + (index + 1)),
        scheduled_date: s.date || null,
        duration_minutes: 90,
        location: null,
        notes: null,
        status: 'scheduled'
      };
    });
  }

  function saveCourseAndSessions(status) {
    var body = {
      course_id: window.courseId ? Number(window.courseId) : null,
      course: buildCoursePayload(status),
      sessions: buildSessionPayloads(window.courseId)
    };
    return apiFetch('/api/courses/save-with-sessions', {
      method: 'POST',
      body: JSON.stringify(body)
    }).then(checkOk).then(function (res) { return res.json(); });
  }

  function saveMaterials(courseId) {
    var pending = (window.materials || []).filter(function (m) { return m.file && !m.id; });
    return pending.reduce(function (chain, m) {
      return chain.then(function () {
        var form = new FormData();
        form.append('file', m.file);
        form.append('course_id', courseId);
        form.append('category', 'supporting');
        form.append('description', '');
        return apiFetch('/api/materials', { method: 'POST', body: form }).then(checkOk);
      });
    }, Promise.resolve());
  }

  function rollbackNewCourse(courseId) {
    if (!courseId) return Promise.resolve();
    return apiFetch('/api/courses/' + encodeURIComponent(courseId), { method: 'DELETE' }).then(checkOk).catch(function () {});
  }

  function install() {
    if (!document.getElementById('basicInfoForm') || typeof window.submitCourse !== 'function') return;
    if (window.__ntaCourseFormEnhancementsInstalled) return;
    window.__ntaCourseFormEnhancementsInstalled = true;

    window.submitCourse = function (status) {
      var wasNewCourse = !window.courseId;
      var savedCourseId = null;
      setCourseFormBusy(true);
      saveCourseAndSessions(status)
        .then(function (data) {
          savedCourseId = data.id;
          window.courseId = data.id;
          return saveMaterials(data.id).then(function () { return data; });
        })
        .then(function () {
          var action = status === 'published' ? 'published' : 'draft';
          window.location.replace('editor-final.html?action=' + action + '&id=' + (savedCourseId || ''));
        })
        .catch(function (err) {
          var cleanup = wasNewCourse && savedCourseId ? rollbackNewCourse(savedCourseId) : Promise.resolve();
          cleanup.then(function () {
            setCourseFormBusy(false);
            showEditorToast(err.message || 'حدث خطأ أثناء الحفظ.', 'error');
          });
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

    refreshLinkedData();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', install);
  } else {
    install();
  }
})();
