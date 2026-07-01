/**
 * Course Details Page Logic — NTA Registration Portal
 * Fetches real data from the backend and populates the UI.
 */
(function () {
  /* ── 1. Lucide Icons ── */
  if (window.lucide) window.lucide.createIcons();

  /* ── 2. Course ID from URL ── */
  const urlParams = new URLSearchParams(window.location.search);
  const courseId  = parseInt(urlParams.get('id'));

  if (!courseId) {
    window.location.href = 'courses.html';
    return;
  }

  /* ── 3. State ── */
  let currentCourse = null;
  let currentSessions = [];
  let sessionDates = [];
  let expandedId = null;
  let DONE_MATERIALS = new Set();

  /* ── 4. Element refs ── */
  const courseTitleEl    = document.getElementById('courseTitle');
  const breadcrumbActive = document.getElementById('breadcrumbActive');
  const permissionsBtn   = document.getElementById('permissionsBtn');
  const quizBtn          = document.getElementById('quizBtn');

  // Progress banner
  const progressValue    = document.getElementById('progressValue');
  const progressFill     = document.getElementById('progressFill');
  const progressLabel    = document.getElementById('progressLabel');
  const statWeeks        = document.getElementById('statWeeks');
  const statSessions     = document.getElementById('statSessions');
  const statLevel        = document.getElementById('statLevel');

  // Sidebar info card
  const infoLevel        = document.getElementById('infoLevel');
  const infoDuration     = document.getElementById('infoDuration');
  const infoSessions     = document.getElementById('infoSessions');
  const infoStatus       = document.getElementById('infoStatus');
  function cleanLabel(str) {
    if (!str) return '';
    // Remove 'course_N_' prefix and replace underscores with spaces
    return str.replace(/course_\d+_/g, '').replace(/_/g, ' ').trim();
  }

  /* ── 6. SVG Icons ── */
  const S = (d, sw) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${sw || 2}" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`;
  const ICON = {
    pdf:     S('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>'),
    video:   S('<circle cx="12" cy="12" r="10"/><polygon points="10,8 16,12 10,16 10,8"/>'),
    code:    S('<polyline points="16,18 22,12 16,6"/><polyline points="8,6 2,12 8,18"/>'),
    quiz:    S('<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>'),
    check:   S('<polyline points="20,6 9,17 4,12"/>', 2.5),
    lock:    S('<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>'),
    ring:    S('<circle cx="12" cy="12" r="10"/>'),
    ext:     S('<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/>'),
    chkRing: S('<circle cx="12" cy="12" r="10"/><polyline points="20,6 9,17 4,12"/>'),
    chev:    S('<polyline points="6,9 12,15 18,9"/>'),
  };

  const TYPE_MAP = {
    pdf:   { label: 'PDF',   openLabel: 'فتح PDF',      btnCls: 'btn-pdf',   iconCls: 'mi-pdf'   },
    video: { label: 'فيديو', openLabel: 'مشاهدة',       btnCls: 'btn-video', iconCls: 'mi-video' },
    code:  { label: 'كود',   openLabel: 'تنزيل الملفات', btnCls: 'btn-code',  iconCls: 'mi-code'  },
    quiz:  { label: 'اختبار', openLabel: 'بدء الاختبار',  btnCls: 'btn-quiz',  iconCls: 'mi-quiz'  },
  };

  /* ── 7. Data Fetching ── */
  async function loadCourseDetails() {
    try {
      const response = await window.authenticatedFetch(`/api/trainee/course/${courseId}/details`);
      if (!response.ok) throw new Error('Failed to fetch course details');
      
      const data = await response.json();
      currentCourse   = data.course;
      currentSessions = data.sessions;
      
      // Update UI
      renderMetadata(data.course);
      renderProgress(data.progress, data.course);
      renderAnnouncements(data.announcements);
      renderTimeline(data.sessions);
      renderCurriculum(data.sessions);
      
      // Load Assignments
      loadAssignments();
      
      // Update Calendar
      sessionDates = currentSessions
        .map(s => s.session_date ? { date: new Date(s.session_date), topic: s.topic } : null)
        .filter(d => d !== null);
      
      const now = new Date();
      buildCalendar(now.getFullYear(), now.getMonth());

      if (window.lucide) window.lucide.createIcons();
    } catch (error) {
      console.error('Error loading course:', error);
      if (courseTitleEl) courseTitleEl.textContent = 'تعذّر تحميل الدورة';
    }
  }

  async function loadAssignments() {
    const assignmentsList = document.getElementById('assignments-list');
    if (!assignmentsList) return;

    try {
      const res = await window.authenticatedFetch(`/api/assignments/course/${courseId}`);
      const assignments = await res.json();
      
      const sessionRaw = localStorage.getItem('ntaTrainee');
      const trainee = sessionRaw ? JSON.parse(sessionRaw) : null;
      const traineeId = trainee ? trainee.id : null;

      if (assignments.length === 0) {
        assignmentsList.innerHTML = '<p class="assign-empty">لا توجد تكليفات لهذه الدورة.</p>';
        return;
      }

      let html = '';
      for (const a of assignments) {
        let submission = null;
        if (traineeId) {
          const sRes = await window.authenticatedFetch(`/api/assignments/my-submission/${a.id}/${traineeId}`);
          submission = await sRes.json();
        }

        const deadline = new Date(a.deadline);
        const isPast = deadline < new Date();
        
        let statusHtml = '';
        if (submission) {
          if (submission.status === 'graded') {
            statusHtml = `<span class="assign-status status-graded">مقيّم: ${submission.grade}/${a.max_grade}</span>`;
          } else {
            statusHtml = '<span class="assign-status status-submitted">تم التسليم</span>';
          }
        } else {
          statusHtml = isPast ? '<span class="assign-status assign-status--overdue">فات الموعد</span>' : '<span class="assign-status status-pending">لم يتم التسليم</span>';
        }

        html += `
          <div class="assignment-card">
            <div class="assign-header">
              <div>
                <h3 class="assign-title">${a.title}</h3>
                <p class="assign-deadline">الموعد النهائي: ${deadline.toLocaleString('ar-EG')}</p>
              </div>
              ${statusHtml}
            </div>
            <p class="assign-desc">${a.description || ''}</p>
            <div class="assign-actions">
              ${a.file_path ? `<a href="/${a.file_path}" target="_blank" class="btn-assign btn-download"><i data-lucide="download"></i> تحميل التعليمات</a>` : ''}
              ${(!submission || submission.status !== 'graded') && !isPast ? `
                <label class="btn-assign btn-upload" style="cursor:pointer;">
                  <i data-lucide="upload"></i> ${submission ? 'تحديث التسليم' : 'رفع التسليم'}
                  <input type="file" style="display:none;" onchange="handleAssignmentUpload(event, ${a.id})">
                </label>
              ` : ''}
              ${submission && submission.feedback ? `
                <div class="assign-feedback">
                  <p class="assign-feedback__label">ملاحظات المدرب:</p>
                  <p class="assign-feedback__text">${submission.feedback}</p>
                </div>
              ` : ''}
            </div>
          </div>
        `;
      }
      assignmentsList.innerHTML = html;
      if (window.lucide) window.lucide.createIcons();
    } catch (err) {
      console.error('Error loading assignments:', err);
      assignmentsList.innerHTML = '<p class="assign-error">فشل تحميل التكليفات.</p>';
    }
  }

  window.handleAssignmentUpload = async (event, assignmentId) => {
    const file = event.target.files[0];
    if (!file) return;

    const sessionRaw = localStorage.getItem('ntaTrainee');
    const trainee = sessionRaw ? JSON.parse(sessionRaw) : null;
    if (!trainee || !trainee.id) {
      alert('يجب تسجيل الدخول أولاً');
      return;
    }

    const formData = new FormData();
    formData.append('assignment_id', assignmentId);
    formData.append('file', file);

    try {
      const res = await fetch('/api/assignments/submit', {
        method: 'POST',
        headers: trainee.token ? { Authorization: 'Bearer ' + trainee.token } : {},
        body: formData
      });
      if (res.ok) {
        alert('تم رفع التكليف بنجاح');
        loadAssignments();
      } else {
        const err = await res.json();
        alert('فشل الرفع: ' + (err.detail || 'خطأ غير معروف'));
      }
    } catch (err) {
      console.error('Upload error:', err);
      alert('حدث خطأ أثناء الرفع');
    }
  };

  function renderMetadata(course) {
    const cleanTitle = cleanLabel(course.title);
    courseTitleEl.textContent    = cleanTitle;
    breadcrumbActive.textContent = cleanTitle;
    document.title               = cleanTitle + ' - الأكاديمية الوطنية للتدريب';

    if (statWeeks)    statWeeks.textContent    = (course.duration_weeks || '—') + ' أسابيع';
    if (statSessions) statSessions.textContent = (course.total_sessions || '—') + ' جلسة';
    if (statLevel)    statLevel.textContent    = course.skill_level || '—';

    if (infoLevel)    infoLevel.textContent    = course.skill_level || '—';
    if (infoDuration) infoDuration.textContent = course.duration_weeks ? course.duration_weeks + ' أسابيع' : '—';
    if (infoSessions) infoSessions.textContent = course.total_sessions ? course.total_sessions + ' جلسة' : '—';
    
    if (infoStatus) {
      const statusMap = {
        'Ongoing'   : { label: 'جاري',   cls: 'cd-status--ongoing'  },
        'Upcoming'  : { label: 'قادم',   cls: 'cd-status--upcoming' },
        'Completed' : { label: 'مكتمل', cls: 'cd-status--done'     },
      };
      const s = statusMap[course.status] || { label: course.status || '—', cls: '' };
      infoStatus.textContent = s.label;
      infoStatus.className   = 'cd-info-item__val cd-status-badge ' + s.cls;
    }

    if (course.has_active_quiz) {
      quizBtn.classList.add('active-quiz-pulse');
      quizBtn.onclick = () => window.open('exam.html?course_id=' + course.id, '_blank');
    } else {
      quizBtn.style.opacity = '0.55';
    }

    permissionsBtn.onclick = () => {
      window.location.href = `trainee-permissions.html?course_id=${course.id}&course_name=${encodeURIComponent(cleanTitle)}`;
    };
  }

  function renderProgress(progress, course) {
    const pct = progress.percentage || 0;
    const completed = Math.round((pct / 100) * (course.total_sessions || 1));
    
    if (progressValue) progressValue.textContent = pct + '%';
    if (progressFill)  progressFill.style.width  = pct + '%';
    if (progressLabel) progressLabel.textContent = `تم إنجاز ${completed} من أصل ${course.total_sessions || 0} جلسة تدريبية`;
  }

  function renderAnnouncements(alerts) {
    const container = document.getElementById('announcementsList');
    if (!container) return;

    if (!alerts || alerts.length === 0) {
      container.innerHTML = '<p class="cd-announcement__body" style="text-align:center;padding:1rem;opacity:0.6;">لا توجد تنبيهات حالية</p>';
      return;
    }

    container.innerHTML = alerts.map(alert => {
      const date = new Date(alert.created_at).toLocaleDateString('ar-EG', { day: 'numeric', month: 'long' });
      return `
        <div class="cd-announcement">
          <div class="cd-announcement__top">
            <h4 class="cd-announcement__title">${cleanLabel(alert.title)}</h4>
            ${alert.target_type === 'global' ? '<span class="cd-badge">عام</span>' : ''}
          </div>
          <div class="cd-announcement__footer">
            <i data-lucide="clock"></i>
            <span>${date}</span>
          </div>
        </div>`;
    }).join('');
  }

  function renderTimeline(sessions) {
    const container = document.querySelector('.cd-timeline');
    if (!container) return;

    const upcoming = sessions
      .filter(s => s.session_date && new Date(s.session_date) >= new Date().setHours(0,0,0,0))
      .sort((a, b) => new Date(a.session_date) - new Date(b.session_date));

    if (upcoming.length === 0) {
      container.innerHTML = '<p class="cd-timeline-sub" style="text-align:center;padding:1rem;">لا توجد مواعيد قادمة</p>';
      return;
    }

    container.innerHTML = upcoming.map((sess, idx) => {
      const d = new Date(sess.session_date);
      const isToday = d.toDateString() === new Date().toDateString();
      
      return `
        <div class="cd-timeline-item ${idx > 0 ? 'cd-timeline-item--dim' : ''}">
          <div class="cd-timeline-dot ${isToday ? 'cd-timeline-dot--urgent' : ''}"></div>
          <div class="cd-timeline-content">
            <p class="cd-timeline-date ${isToday ? 'cd-timeline-date--urgent' : ''}">${isToday ? 'اليوم' : d.toLocaleDateString('ar-EG', { day: 'numeric', month: 'long' })}</p>
            <h4 class="cd-timeline-title">${cleanLabel(sess.topic)}</h4>
            <p class="cd-timeline-sub">جلسة تدريبية</p>
          </div>
        </div>`;
    }).join('');
  }

  /* ── 8. Curriculum Rendering ── */
  function renderCurriculum(sessions) {
    const container = document.getElementById('mat-root-inner');
    if (!container) return;

    if (!sessions || sessions.length === 0) {
      container.innerHTML = '<div class="cd-empty-state"><p>لا يوجد منهج متاح لهذه الدورة حالياً</p></div>';
      return;
    }

    const WEEKS = sessions.map((sess, idx) => {
      let mats = [];
      let derivedTopic = sess.topic; // Default to DB topic
      
      if (sess.materials) {
        const rawPath = sess.materials.file_path || sess.materials.slides;
        if (rawPath) {
          const rawFileName = rawPath.split('/').pop();
          const ext = rawFileName.split('.').pop().toLowerCase();
          
          // 1. Strip system prefixes (category_id_timestamp_ or timestamp_)
          let cleanName = rawFileName;
          const parts = rawFileName.split('_');
          
          // Case A: new naming {timestamp}_{original} -> parts[0] is timestamp
          // Case B: old naming {cat}_{id}_{ts}_{original} -> parts[3] is original
          if (parts.length >= 4 && isNaN(parts[0])) {
            cleanName = parts.slice(3).join('_');
          } else if (parts.length >= 2 && !isNaN(parts[0])) {
            cleanName = parts.slice(1).join('_');
          }
          
          // Remove extension
          cleanName = cleanName.replace(new RegExp(`\\.${ext}$`, 'i'), '');
          
          // 2. Extract Session info and Topic from cleanName
          // Pattern: "Session1_Topic" or "Session 1 Topic" or just "Topic"
          let displayName = cleanLabel(cleanName);
          
          // If the name starts with "Session X", extract the rest as the topic
          const sessionMatch = displayName.match(/Session\s*(\d+)\s*(.*)/i);
          if (sessionMatch) {
            const sNum = sessionMatch[1];
            const sText = sessionMatch[2].replace(/^[:\-\s]+/, '').trim();
            if (sText) {
              derivedTopic = `Session ${sNum}: ${sText}`;
              displayName = sText; // Material name becomes just the topic
            } else {
              // It's just "Session X", use course title as fallback topic
              derivedTopic = `Session ${sNum}: ${cleanLabel(currentCourse.title)}`;
              displayName = cleanLabel(currentCourse.title);
            }
          } else {
            // No "Session X" in filename, use the filename itself as topic
            derivedTopic = `Session ${idx + 1}: ${displayName}`;
          }

          let type = 'pdf';
          let label = 'مستند';
          if (['mp4', 'webm', 'mov'].includes(ext)) type = 'video';
          if (['doc', 'docx'].includes(ext)) { type = 'pdf'; label = 'Word'; }
          if (['ppt', 'pptx'].includes(ext)) { type = 'pdf'; label = 'PowerPoint'; }
          if (['txt'].includes(ext)) { type = 'pdf'; label = 'نصي'; }

          mats.push({ 
            id: `s${sess.id}-file`, 
            type: type, 
            name: `course: ${displayName}`, 
            meta: `محاضرة: ${derivedTopic}`, 
            dur: label, 
            url: rawPath, 
            detail: `عرض أو تحميل ملف: ${rawFileName}`
          });
        }

        if (Array.isArray(sess.materials.links)) {
          sess.materials.links.forEach((lnk, i) => {
            let type = (lnk.title && (lnk.title.includes('فيديو') || lnk.title.toLowerCase().includes('video'))) ? 'video' : 'ext';
            mats.push({ 
              id: `s${sess.id}-link${i}`, 
              type: type, 
              name: cleanLabel(lnk.title) || 'رابط خارجي', 
              meta: 'موارد إضافية', 
              dur: 'رابط', 
              url: lnk.url, 
              detail: 'رابط خارجي لمورد مفيد.' 
            });
          });
        }
      }
      // 3. Add Quiz if present
      if (sess.quiz) {
        let quizStatusLabel = 'اختبار الجلسة';
        let quizType = 'quiz';
        let detail = 'اختبار تقييمي لمحتوى الجلسة.';
        let icon = ICON.quiz;
        
        if (sess.quiz.status === 'LOCKED') {
           quizStatusLabel = 'الاختبار مغلق حالياً';
           detail = 'سيفتح الاختبار في موعد الجلسة.';
        } else if (sess.quiz.status === 'EXPIRED') {
           quizStatusLabel = 'انتهى وقت الاختبار';
           detail = 'انتهت الـ 24 ساعة المتاحة للتقديم.';
        }

        mats.push({
          id: `q-${sess.quiz.id}`,
          type: 'quiz',
          name: quizStatusLabel,
          meta: 'تقييم ذكي',
          dur: sess.quiz.status === 'AVAILABLE' ? 'متاح الآن' : (sess.quiz.status === 'LOCKED' ? 'مغلق' : 'انتهى'),
          url: sess.quiz.status === 'AVAILABLE' ? `exam.html?course_id=${currentCourse.id}&session_id=${sess.id}&quiz_id=${sess.quiz.id}` : '#',
          detail: detail,
          status: sess.quiz.status
        });
      }

      return { num: idx + 1, title: cleanLabel(derivedTopic), materials: mats };
    });

    let html = '';
    WEEKS.forEach(week => {
      const wd = week.materials.filter(m => DONE_MATERIALS.has(m.id)).length;
      const wt = week.materials.length;
      const wp = wt ? Math.round((wd / wt) * 100) : 0;

      html += `
        <div class="week-block">
          <div class="week-head">
            <span class="week-badge">الأسبوع ${week.num}</span>
            <span class="week-title">${week.title}</span>
            <span class="week-frac">${wd}/${wt}</span>
          </div>
          <div class="week-bar-row">
            <div class="week-bar-track"><div class="week-bar-fill" style="width:${wp}%"></div></div>
            <span class="week-bar-pct">${wp}%</span>
          </div>
          <div class="week-timeline">`;

      week.materials.forEach((mat, i) => {
        const isDone = DONE_MATERIALS.has(mat.id);
        const isExp = expandedId === mat.id;
        const t = TYPE_MAP[mat.type];
        
        html += `
          <div class="tl-spine">
            <div class="tl-dot ${isDone ? 'is-done' : (isExp ? 'is-active' : '')}"></div>
            ${i < week.materials.length - 1 ? `<div class="tl-line ${isDone ? 'is-done' : ''}"></div>` : ''}
          </div>
          <div class="tl-row">
            <div class="mat-card ${isDone ? 'is-done' : ''} ${isExp ? 'is-expanded' : ''} ${mat.status === 'LOCKED' ? 'is-locked' : ''} ${mat.status === 'EXPIRED' ? 'is-expired' : ''}" onclick="${mat.status === 'LOCKED' ? '' : `window.matToggle('${mat.id}')`}">
              <div class="mat-body">
                <div class="mat-icon ${t.iconCls} ${mat.status === 'LOCKED' ? 'mi-locked' : ''}">${mat.status === 'LOCKED' ? ICON.lock : ICON[mat.type]}</div>
                <div class="mat-info">
                  <div class="mat-name">${mat.name}</div>
                  <div class="mat-meta">${mat.meta}</div>
                  <div class="mat-tags">
                    <span class="mat-tag tag-type">${t.label}</span>
                    <span class="mat-tag tag-dur">${mat.dur}</span>
                    ${isDone ? '<span class="mat-tag tag-done">مكتمل</span>' : ''}
                  </div>
                </div>
                <div class="mat-right">
                  <div class="mat-status ${isDone ? 'ms-done' : 'ms-idle'}">${isDone ? ICON.check : (mat.status === 'LOCKED' ? ICON.lock : ICON.ring)}</div>
                  <div class="mat-chevron ${isExp ? 'open' : ''}">${ICON.chev}</div>
                </div>
              </div>
            </div>
            ${isExp ? `
              <div class="mat-panel open">
                <div class="mat-panel-inner">
                  <p class="mat-detail">${mat.detail}</p>
                  <div class="mat-actions">
                    ${mat.status === 'EXPIRED' ? `
                       <button class="btn btn-expired" disabled>${ICON.lock} انتهى الوقت</button>
                    ` : `
                       <button class="btn ${t.btnCls}" onclick="window.matOpen(event,'${mat.url}')">${mat.type === 'quiz' ? ICON.quiz : ICON.ext} ${t.openLabel}</button>
                    `}
                    ${mat.type !== 'quiz' ? `
                    <button class="btn btn-mark ${isDone ? 'marked' : ''}" onclick="window.matMark(event,'${mat.id}')">
                      ${isDone ? ICON.check + ' مكتمل' : ICON.chkRing + ' تسجيل الإتمام'}
                    </button>
                    ` : ''}
                  </div>
                </div>
              </div>` : ''}
          </div>`;
      });
      html += `</div></div>`;
    });
    container.innerHTML = html;
  }

  /* ── 8. Window Actions ── */
  window.matToggle = (id) => {
    expandedId = expandedId === id ? null : id;
    renderCurriculum(currentSessions);
    if (window.lucide) window.lucide.createIcons();
  };

  window.matOpen = (e, url) => {
    e.stopPropagation();
    window.open(url && url !== '#' ? url : '#', '_blank');
  };

  window.matMark = (e, id) => {
    e.stopPropagation();
    if (DONE_MATERIALS.has(id)) return;
    DONE_MATERIALS.add(id);
    renderCurriculum(currentSessions);
    if (window.lucide) window.lucide.createIcons();
  };

  /* ── 9. Calendar Logic ── */
  function buildCalendar(year, month) {
    const calDays = document.getElementById('calDays');
    const calMonthLabel = document.getElementById('calMonthLabel');
    if (!calDays) return;

    const monthNames = ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'];
    calMonthLabel.textContent = monthNames[month] + ' ' + year;

    const today = new Date();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const sessionMap = new Map();
    sessionDates.forEach(s => {
      if (s.date.getFullYear() === year && s.date.getMonth() === month) {
        sessionMap.set(s.date.getDate(), s.topic);
      }
    });

    calDays.innerHTML = '';
    for (let i = 0; i < firstDay; i++) {
      const el = document.createElement('div');
      el.className = 'cd-cal-day cd-cal-day--empty';
      calDays.appendChild(el);
    }

    for (let d = 1; d <= daysInMonth; d++) {
      const el = document.createElement('div');
      let cls = 'cd-cal-day';
      if (today.getFullYear() === year && today.getMonth() === month && today.getDate() === d) cls += ' cd-cal-day--today';
      if (sessionMap.has(d)) {
        cls += ' cd-cal-day--event';
        el.title = sessionMap.get(d);
      }
      el.className = cls;
      el.textContent = d;
      calDays.appendChild(el);
    }
  }

  // Calendar Nav
  document.getElementById('calPrevBtn')?.addEventListener('click', () => {
    let now = new Date(breadcrumbActive.dataset.year || new Date().getFullYear(), breadcrumbActive.dataset.month || new Date().getMonth());
    now.setMonth(now.getMonth() - 1);
    breadcrumbActive.dataset.year = now.getFullYear();
    breadcrumbActive.dataset.month = now.getMonth();
    buildCalendar(now.getFullYear(), now.getMonth());
  });
  document.getElementById('calNextBtn')?.addEventListener('click', () => {
    let now = new Date(breadcrumbActive.dataset.year || new Date().getFullYear(), breadcrumbActive.dataset.month || new Date().getMonth());
    now.setMonth(now.getMonth() + 1);
    breadcrumbActive.dataset.year = now.getFullYear();
    breadcrumbActive.dataset.month = now.getMonth();
    buildCalendar(now.getFullYear(), now.getMonth());
  });

  /* ── 10. Init ── */
  loadCourseDetails();

})();
