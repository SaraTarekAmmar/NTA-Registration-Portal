const MAX = 20;

let state = {
  courseId: new URLSearchParams(window.location.search).get("course_id"),
  courseName:
    new URLSearchParams(window.location.search).get("course_name") ||
    "الدورة التدريبية",
  sessions: [],
  targetId: "",
  processing: false,
  activeIdx: null,
  quiz: null,
  showPreview: false,

  // Validation state
  submitted: false, // flipped to true on first Generate click
  submittedEntryIds: [], // snapshot of entry IDs at last Generate click
  // → only these entries show inline errors
  errors: [],

  entries: [
    {
      id: Date.now(),
      sourceSessionId: "",
      type: "mcq",
      count: 5,
      difficulty: "medium",
      materials: [],
    },
  ],
};

/* ─── Boot ───────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", init);

async function init() {
  renderStaticStructure();
  if (state.courseId) {
    await fetchSessions(state.courseId);
  } else if (window.GENERATE_QUIZ_DUMMY) {
    state.sessions = window.GENERATE_QUIZ_DUMMY.sessions;
    updateTargetSelectOptions();
  }
  render();
}

async function fetchSessions(id) {
  try {
    const r = await window.authenticatedFetch(`/api/courses/${id}/sessions`);
    if (r.ok) {
      const d = await r.json();
      state.sessions = d.sessions || [];

      // Ensure each session has some mock materials if none exist (for demo purposes)
      state.sessions.forEach((s) => {
        if (!s.materials || s.materials.length === 0) {
          s.materials = [
            { id: `m1_${s.id}`, name: "ملخص المحاضرة.pdf", type: "pdf" },
            { id: `m2_${s.id}`, name: "رسم توضيحي للعمليات.png", type: "img" },
            { id: `m3_${s.id}`, name: "نصوص تدريبية إضافية.txt", type: "txt" },
          ];
        }
      });
    } else {
      if (window.GENERATE_QUIZ_DUMMY) {
        state.sessions = window.GENERATE_QUIZ_DUMMY.sessions;
      }
    }
  } catch (e) {
    console.error("fetchSessions:", e);
    if (window.GENERATE_QUIZ_DUMMY) {
      state.sessions = window.GENERATE_QUIZ_DUMMY.sessions;
    }
  }
  updateTargetSelectOptions();
}

/* ─── Validation ─────────────────────────────────────── */
function calculateTotal() {
  return state.entries.reduce((s, e) => s + (parseInt(e.count) || 0), 0);
}

/**
 * Full validation — returns { key, message }[]
 * key is used to link banner items to DOM fields
 */
function runValidation() {
  const errors = [];
  const total = calculateTotal();

  if (!state.targetId)
    errors.push({ key: "target", message: "يجب اختيار الجلسة المستهدفة" });

  state.entries.forEach((entry, idx) => {
    if (!entry.sourceSessionId)
      errors.push({
        key: `entry-source-${entry.id}`,
        message: `المجموعة ${idx + 1}: يجب تحديد جلسة المصدر`,
      });
  });

  if (total === 0)
    errors.push({ key: "counter", message: "يجب إضافة أسئلة قبل البدء" });
  else if (total > MAX)
    errors.push({
      key: "counter",
      message: `تجاوزت الحد الأقصى بـ ${total - MAX} سؤال — قلّل العدد`,
    });
  else if (total < MAX)
    errors.push({
      key: "counter",
      message: `يجب أن يكون الإجمالي ${MAX} سؤالاً بالضبط (متبقي ${MAX - total})`,
    });

  return errors;
}

/**
 * Should we show an error for this field right now?
 *
 * Rules:
 *  - Never before the first Generate click (submitted = false)
 *  - For "target": show if submitted and the error exists
 *  - For an entry source: show only if that entry was present on last Generate click
 *    New entries added after are always clean.
 *  - For "counter": always show after submit if present
 */
function shouldShowError(key) {
  if (!state.submitted) return false;
  if (!state.errors.some((e) => e.key === key)) return false;

  if (key.startsWith("entry-source-")) {
    const entryId = parseInt(key.replace("entry-source-", ""));
    return state.submittedEntryIds.includes(entryId);
  }

  return true;
}

/* ─── Entry Mutations ────────────────────────────────── */
function addEntry(e) {
  if (e) e.preventDefault();
  const total = calculateTotal();
  if (total >= MAX) return;

  state.entries.push({
    id: Date.now(),
    sourceSessionId: "",
    type: "mcq",
    count: Math.min(5, MAX - total),
    difficulty: "medium",
    materials: [],
  });

  // Re-run validation so counters stay accurate,
  // but do NOT update submittedEntryIds → new entry stays clean
  if (state.submitted) state.errors = runValidation();

  render();
}

function removeEntry(e, id) {
  if (e) e.preventDefault();
  if (state.entries.length <= 1) return;

  state.entries = state.entries.filter((en) => en.id !== id);
  state.submittedEntryIds = state.submittedEntryIds.filter((sid) => sid !== id);

  if (state.submitted) state.errors = runValidation();

  render();
}

function updateEntry(id, field, value) {
  state.entries = state.entries.map((e) => {
    if (e.id === id) {
      const updated = { ...e, [field]: value };
      if (field === "sourceSessionId") updated.materials = [];
      return updated;
    }
    return e;
  });

  // Real-time clearing: re-validate silently; shouldShowError() controls what renders
  if (state.submitted) state.errors = runValidation();

  if (field === "sourceSessionId") {
    render();
  } else {
    renderStatus();
  }
}

function updateCount(id, raw, el) {
  const num = Math.max(1, parseInt(raw) || 1);
  const other = state.entries
    .filter((e) => e.id !== id)
    .reduce((s, e) => s + (parseInt(e.count) || 0), 0);
  const clamped = Math.min(num, MAX - other || 1);

  state.entries = state.entries.map((e) =>
    e.id === id ? { ...e, count: clamped } : e,
  );
  if (el) el.value = clamped;

  popRingNum();

  if (state.submitted) state.errors = runValidation();
  renderStatus();
}

function popRingNum() {
  const el = document.getElementById("ringNum");
  if (!el) return;
  el.classList.remove("pop");
  void el.offsetWidth;
  el.classList.add("pop");
}

/* ─── Submit ─────────────────────────────────────────── */
async function handleGenerate(e) {
  if (e) e.preventDefault();

  // Snapshot which entries exist right now — they become "validated"
  state.submitted = true;
  state.submittedEntryIds = state.entries.map((en) => en.id);
  state.errors = runValidation();

  if (state.errors.length) {
    renderStatus();
    shakeCard();
    focusFirstError();
    return;
  }

  await generate();
}

function shakeCard() {
  const card = document.querySelector(".main-card");
  if (!card) return;
  card.style.animation = "none";
  void card.offsetWidth;
  card.style.animation = "shake 0.45s ease";
  card.addEventListener(
    "animationend",
    () => {
      card.style.animation = "";
    },
    { once: true },
  );
}

function focusFirstError() {
  if (!state.errors.length) return;
  const { key } = state.errors[0];

  if (key === "target") {
    scrollAndFocus("targetSessionSelect", null);
  } else if (key.startsWith("entry-source-")) {
    const id = key.replace("entry-source-", "");
    scrollAndFocus(`select-source-${id}`, `entry-source-wrap-${id}`);
  } else if (key === "counter") {
    document
      .getElementById("footerBarContainer")
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

function scrollAndFocus(focusId, pulseId) {
  const el = document.getElementById(focusId);
  if (!el) return;
  el.scrollIntoView({ behavior: "smooth", block: "center" });
  setTimeout(() => {
    el.focus?.();
    if (pulseId) pulseField(pulseId);
  }, 300);
}

function pulseField(wrapperId) {
  const el = document.getElementById(wrapperId);
  if (!el) return;
  el.classList.add("field-pulse-error");
  setTimeout(() => {
    el.classList.remove("field-pulse-error");
  }, 900);
}

function jumpToError(key) {
  if (key === "target") {
    scrollAndFocus("targetSessionSelect", "targetSelectWrapper");
  } else if (key.startsWith("entry-source-")) {
    const id = key.replace("entry-source-", "");
    scrollAndFocus(`select-source-${id}`, `entry-source-wrap-${id}`);
  } else if (key === "counter") {
    document
      .getElementById("footerBarContainer")
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

/* ─── Generate ───────────────────────────────────────── */
async function generate() {
  state.processing = true;
  state.quiz = null;
  renderStatus();

  let all = [];
  try {
    for (let i = 0; i < state.entries.length; i++) {
      state.activeIdx = i;
      renderStatus();

      const entry = state.entries[i];
      
      // Resolve material IDs to actual paths/names
      const session = state.sessions.find(s => s.id == entry.sourceSessionId);
      const resolvedMaterials = entry.materials.map(mid => {
        const mat = session?.materials?.find(m => m.id === mid);
        return mat ? (mat.path || mat.name) : mid;
      });

      const payload = {
        course_id: state.courseId,
        target_session_id: state.targetId,
        source_session_id: entry.sourceSessionId,
        type: entry.type,
        difficulty: entry.difficulty,
        count: entry.count,
        materials: resolvedMaterials,
        courseName: state.courseName,
        groupId: `AI_QUIZ_${state.courseId}_${Date.now()}_${i}`,
      };

      console.log(`[DISPATCH] Group ${i+1} payload:`, payload);

      const dispatchPayload = {
        service: "Quiz Engine",
        endpoint: "/generate-quiz",
        data: payload
      };

      const res = await window.authenticatedFetch("/api/ai/dispatch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dispatchPayload),
      });

      const data = await res.json();
      console.log(`[RESPONSE] Group ${i+1}:`, data);

      if (res.ok) {
        all = [...all, ...(data.questions || [])];
      } else {
        showToast(`خطأ في توليد أسئلة المجموعة ${i + 1}: ${data.detail || "Error"}`, "error");
        break;
      }
    }

    if (all.length) {
      state.quiz = { questions: all };
      state.showPreview = true;
      showToast(`تم توليد ${all.length} سؤالاً بنجاح`, "success");
    }
  } catch {
    showToast("حدث خطأ تقني أثناء التوليد — حاول مرة أخرى", "error");
  } finally {
    state.processing = false;
    state.activeIdx = null;
    renderStatus();
  }
}

/* ─── Toast ──────────────────────────────────────────── */
let _toastTimer = null;

function showToast(message, type = "info") {
  document.getElementById("toastNotification")?.remove();
  if (_toastTimer) clearTimeout(_toastTimer);

  const icons = {
    success: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
    error: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
    info: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
  };
  const toastType = type === "success" || type === "error" ? type : "info";

  const toast = document.createElement("div");
  toast.id = "toastNotification";
  toast.className = `gq-toast gq-toast--${toastType}`;
  toast.innerHTML = `<span style="flex-shrink:0">${icons[toastType] || icons.info}</span><span>${message}</span>`;
  document.body.appendChild(toast);

  requestAnimationFrame(() =>
    requestAnimationFrame(() => {
      toast.classList.add("is-visible");
    }),
  );

  _toastTimer = setTimeout(
    () => {
      toast.classList.remove("is-visible");
      setTimeout(() => toast.remove(), 300);
    },
    type === "error" ? 5000 : 3000,
  );
}

/* ─── Render: Static Shell ───────────────────────────── */
function renderStaticStructure() {
  document.getElementById("root").innerHTML = `
    <div class="page">
      <div class="container">

        <header class="header fade-up">
          <div class="header-left">
            <button type="button" class="back-btn glass" onclick="window.history.back()">
              <i data-lucide="arrow-right" style="width:20px;height:20px"></i>
            </button>
            <div>
              <div class="header-title">مولّد الاختبارات الذكي</div>
              <div class="header-sub">توليد اختبار آلي للدورة: <span>${state.courseName}</span></div>
            </div>
          </div>
          <div class="status-pill glass">
            <div class="status-dot-wrap">
              <div class="status-dot-ping"></div>
              <div class="status-dot"></div>
            </div>
            <span class="status-label">محرك الذكاء الاصطناعي متصل</span>
          </div>
        </header>

        <div class="main-card glass fade-up delay-2">
          <div class="card-head">
            <div class="card-head-icon">
              <i data-lucide="settings-2" style="width:20px;height:20px"></i>
            </div>
            <div>
              <div class="card-head-title">إعدادات الاختبار</div>
              <div class="card-head-sub">الإجمالي يجب أن يساوي ${MAX} سؤالاً بالضبط لتفعيل التوليد</div>
            </div>
          </div>

          <div id="validationBannerContainer"></div>

          <div class="target-row">
            <label class="lbl">الجلسة المستهدفة</label>
            <div id="targetSelectWrapper" style="max-width:420px">
              <div class="select-wrap" id="targetSelectInner">
                <select
                  id="targetSessionSelect"
                  onchange="state.targetId = this.value; if(state.submitted){ state.errors = runValidation(); renderStatus(); }"
                >
                  <option value="">اختر الجلسة المستهدفة...</option>
                </select>
              </div>
              <div id="targetErrMsg"></div>
            </div>
          </div>

          <div>
            <div class="entries-header">
              <span class="lbl" style="margin-bottom:0">هيكل مجموعات الأسئلة</span>
              <button type="button" id="addEntryBtn" class="add-btn" onclick="addEntry(event)">
                <i data-lucide="plus" style="width:13px;height:13px"></i> إضافة مجموعة
              </button>
            </div>
            <div id="entriesListContainer"></div>
          </div>

          <div id="footerBarContainer" class="footer-bar fade-up delay-3"></div>
        </div>

      </div>
      <div id="overlayContainer"></div>
      <div id="previewContainer"></div>
    </div>
  `;
  if (window.lucide) window.lucide.createIcons();
}

function updateTargetSelectOptions() {
  const select = document.getElementById("targetSessionSelect");
  if (!select) return;
  select.innerHTML =
    `<option value="">اختر الجلسة المستهدفة...</option>` +
    state.sessions
      .map(
        (s) =>
          `<option value="${s.id}" ${state.targetId == s.id ? "selected" : ""}>${s.topic}</option>`,
      )
      .join("");
}

/* ─── Render: Full (structure changed) ───────────────── */
function render() {
  renderEntries();
  renderStatus();
}

/* ─── Render: Entries ────────────────────────────────── */
function renderEntries() {
  const container = document.getElementById("entriesListContainer");
  if (!container) return;
  const total = calculateTotal();

  container.innerHTML = state.entries
    .map((entry, idx) => {
      const sourceKey = `entry-source-${entry.id}`;
      const showSrcErr = shouldShowError(sourceKey);

      return `
      <div class="entry-card${total > MAX ? " entry-over" : ""}" id="entryCard-${entry.id}">
        <div class="entry-num">#${idx + 1}</div>

        ${
          state.entries.length > 1
            ? `
          <button type="button" class="delete-btn" title="حذف المجموعة"
            onclick="removeEntry(event, ${entry.id})">
            <i data-lucide="trash-2" style="width:15px;height:15px"></i>
          </button>
        `
            : ""
        }

        <div class="entry-grid">

          <div id="entry-source-wrap-${entry.id}" class="${showSrcErr ? "field-err" : ""}">
            <label class="lbl">المحتوى المصدر</label>
            <div class="select-wrap">
              <select
                id="select-source-${entry.id}"
                onchange="updateEntry(${entry.id}, 'sourceSessionId', this.value)"
              >
                <option value="">اختر الجلسة...</option>
                ${state.sessions
                  .map(
                    (s) =>
                      `<option value="${s.id}" ${entry.sourceSessionId == s.id ? "selected" : ""}>${s.topic}</option>`,
                  )
                  .join("")}
              </select>
            </div>
            ${
              showSrcErr
                ? `
              <div class="err-msg">
                <i data-lucide="alert-circle" style="width:11px;height:11px;flex-shrink:0"></i>
                يجب اختيار جلسة مصدر
              </div>
            `
                : ""
            }
          </div>

          <div>
            <label class="lbl">نوع الأسئلة</label>
            <div class="select-wrap">
              <select onchange="updateEntry(${entry.id}, 'type', this.value)">
                <option value="mcq"        ${entry.type === "mcq" ? "selected" : ""}>اختيار من متعدد</option>
                <option value="true_false" ${entry.type === "true_false" ? "selected" : ""}>صح أو خطأ</option>
                <option value="written"    ${entry.type === "written" ? "selected" : ""}>إجابة مكتوبة</option>
                <option value="mixed"      ${entry.type === "mixed" ? "selected" : ""}>مختلط (AI يختار)</option>
              </select>
            </div>
          </div>

          <div>
            <label class="lbl">عدد الأسئلة</label>
            <input
              type="number" min="1" max="${MAX}" value="${entry.count}"
              onchange="updateCount(${entry.id}, this.value, this)"
              oninput="updateCount(${entry.id}, this.value, this)"
            />
          </div>

          <div>
            <label class="lbl">مستوى الصعوبة</label>
            <div class="select-wrap">
              <select onchange="updateEntry(${entry.id}, 'difficulty', this.value)">
                <option value="easy"   ${entry.difficulty === "easy" ? "selected" : ""}>سهل</option>
                <option value="medium" ${entry.difficulty === "medium" ? "selected" : ""}>متوسط</option>
                <option value="hard"   ${entry.difficulty === "hard" ? "selected" : ""}>صعب</option>
              </select>
            </div>
          </div>

          <div id="entry-materials-wrap-${entry.id}" class="materials-row">
            <label class="lbl">المواد المختارة</label>
            <select
              id="select-materials-${entry.id}"
              class="materials-multiselect"
              multiple
              onchange="updateMaterials(${entry.id}, this)"
            >
              ${(() => {
                const session = state.sessions.find(s => s.id == entry.sourceSessionId);
                if (!session || !session.materials || session.materials.length === 0) {
                  return `<option disabled>اختر جلسة أولاً</option>`;
                }
                return session.materials.map(m =>
                  `<option value="${m.id}" ${entry.materials.includes(m.id) ? 'selected' : ''}>${m.name}</option>`
                ).join('');
              })()}
            </select>
          </div>

        </div>
      </div>
    `;
    })
    .join("");

  if (window.lucide) window.lucide.createIcons();
}

/* ─── Render: Status (never wipes entry inputs) ──────── */
function renderStatus() {
  const total = calculateTotal();

  /* 1 ─ Validation banner */
  const bannerEl = document.getElementById("validationBannerContainer");
  if (bannerEl) {
    const visible = state.errors.filter((e) => shouldShowError(e.key));
    bannerEl.innerHTML = visible.length
      ? `
      <div class="val-banner">
        <span class="val-icon">
          <i data-lucide="alert-circle" style="width:16px;height:16px"></i>
        </span>
        <ul class="val-list">
          ${visible
            .map(
              (err) => `
            <li onclick="jumpToError('${err.key}')" style="cursor:pointer" title="انقر للانتقال">
              ${err.message}
            </li>
          `,
            )
            .join("")}
        </ul>
      </div>
    `
      : "";
  }

  /* 2 ─ Target inline error */
  const targetErrEl = document.getElementById("targetErrMsg");
  const targetInnerEl = document.getElementById("targetSelectInner");
  const showTargetErr = shouldShowError("target");

  if (targetErrEl) {
    targetErrEl.innerHTML = showTargetErr
      ? `
      <div class="err-msg">
        <i data-lucide="alert-circle" style="width:11px;height:11px;flex-shrink:0"></i>
        يجب اختيار الجلسة المستهدفة
      </div>
    `
      : "";
  }
  targetInnerEl?.classList.toggle("field-err", showTargetErr);

  /* 3 ─ Entry source inline errors (surgical — never wipes inputs) */
  state.entries.forEach((entry) => {
    const key = `entry-source-${entry.id}`;
    const show = shouldShowError(key);
    const wrapEl = document.getElementById(`entry-source-wrap-${entry.id}`);
    if (!wrapEl) return;

    wrapEl.classList.toggle("field-err", show);

    let errDiv = wrapEl.querySelector(".err-msg");
    if (show && !errDiv) {
      errDiv = document.createElement("div");
      errDiv.className = "err-msg";
      errDiv.innerHTML = `
        <i data-lucide="alert-circle" style="width:11px;height:11px;flex-shrink:0"></i>
        يجب اختيار جلسة مصدر
      `;
      wrapEl.appendChild(errDiv);
    } else if (!show && errDiv) {
      errDiv.remove();
    }
  });

  /* 4 ─ Overflow flash on entry cards */
  state.entries.forEach((entry) => {
    document
      .getElementById(`entryCard-${entry.id}`)
      ?.classList.toggle("entry-over", total > MAX);
  });

  /* 5 ─ Add button disabled at MAX */
  const addBtn = document.getElementById("addEntryBtn");
  if (addBtn) addBtn.disabled = total >= MAX;

  /* 6 ─ Footer: counter + generate */
  const footerEl = document.getElementById("footerBarContainer");
  if (footerEl) {
    footerEl.innerHTML = `
      ${renderCircularCounter(total)}
      <button type="button" class="gen-btn"
        ${state.processing ? "disabled" : ""}
        onclick="handleGenerate(event)">
        <i data-lucide="sparkles" style="width:19px;height:19px"></i>
        ابدأ التوليد الذكي
      </button>
    `;
  }

  /* 7 ─ Overlay + Preview */
  document.getElementById("overlayContainer").innerHTML = state.processing
    ? renderOverlay()
    : "";
  document.getElementById("previewContainer").innerHTML = state.showPreview
    ? renderPreview()
    : "";

  if (window.lucide) window.lucide.createIcons();
}

/* ─── Render: Circular Counter ───────────────────────── */
function renderCircularCounter(total) {
  const R = 26;
  const CIRC = 2 * Math.PI * R;
  const dash = Math.min(total / MAX, 1) * CIRC;
  const over = total > MAX,
    exact = total === MAX;
  const cs = over ? "c-over" : exact ? "c-exact" : "c-ok";

  const sub = over
    ? `تجاوزت الحد بـ ${total - MAX} سؤال`
    : exact
      ? "ممتاز! الاختبار مكتمل"
      : total === 0
        ? `أضف ${MAX} سؤالاً`
        : `متبقي ${MAX - total} سؤال`;

  return `
    <div class="counter-wrap ${over ? "c-over" : exact ? "c-exact" : ""}">
      <div class="ring-wrap">
        <svg width="64" height="64" viewBox="0 0 64 64">
          <circle class="ring-track" cx="32" cy="32" r="${R}"/>
          <circle class="ring-fill ${cs}" cx="32" cy="32" r="${R}"
            stroke-dasharray="${dash} ${CIRC}" stroke-dashoffset="0"/>
        </svg>
        <div class="ring-center">
          <span class="ring-num ${cs}" id="ringNum">${total}</span>
          <span class="ring-denom">/${MAX}</span>
        </div>
      </div>
      <div class="counter-info">
        <div class="counter-title">إجمالي الأسئلة</div>
        <div class="counter-sub ${over ? "c-over" : exact ? "c-exact" : ""}">${sub}</div>
      </div>
    </div>
  `;
}

/* ─── Render: Overlay ────────────────────────────────── */
function renderOverlay() {
  return `
    <div class="overlay">
      <div class="overlay-card">
        <div class="spinner-wrap">
          <i data-lucide="brain" style="width:34px;height:34px"></i>
          <div class="spinner-ring"></div>
        </div>
        <div class="overlay-title">جاري تجهيز الاسئلة...</div>
        <div class="overlay-sub">
          جاري معالجة المجموعة <strong>${state.activeIdx + 1}</strong> من ${state.entries.length}
        </div>
        <div class="progress-track">
          <div class="progress-fill"
            style="width:${((state.activeIdx + 1) / state.entries.length) * 100}%">
          </div>
        </div>
        <div class="overlay-note">يرجى عدم إغلاق هذه النافظة</div>
      </div>
    </div>
  `;
}

/* ─── Render: Preview ────────────────────────────────── */
function renderPreview() {
  if (!state.quiz) return "";
  return `
    <div class="preview-overlay">
      <div class="preview-modal">
        <div class="preview-head">
          <div class="preview-head-left">
            <div class="preview-head-icon preview-head-icon--indigo">
              <i data-lucide="check-square" style="width:24px;height:24px"></i>
            </div>
            <div>
              <div class="preview-head-title preview-head-title--lg">معاينة الاختبار المُولَّد</div>
              <div class="preview-head-sub">راجع الأسئلة وقم بتأكيدها قبل النشر النهائي للمتدربين.</div>
            </div>
          </div>
          <button type="button" class="close-btn"
            onclick="state.showPreview=false; renderStatus()">
            <i data-lucide="x" style="width:24px;height:24px"></i>
          </button>
        </div>

        <div class="preview-body">
          ${state.quiz.questions
            .map(
              (q, i) => `
            <div class="q-card q-card--preview" style="animation-delay:${i * 0.05}s">
              
              <div class="q-actions">
                <button type="button" class="action-link action-link--ghost" onclick="regenerateQuestion(${i})">
                  <i data-lucide="refresh-cw" style="width:12px;height:12px"></i>
                  إعادة توليد
                </button>
              </div>

              <div class="q-top">
                <div class="q-num q-num--accent">${i + 1}</div>
                <div class="q-body">
                  <div class="q-meta">
                    <span class="badge ${q.type === "mcq" ? "badge-blue" : "badge-green"}">
                      ${q.type === "mcq" ? "اختيار من متعدد" : "صح أو خطأ"}
                    </span>
                    <span class="badge badge-slate">${(q.difficulty || "medium").toUpperCase()}</span>
                  </div>
                  <div class="q-text q-text--preview">${q.question}</div>
                  
                  ${
                    q.type === "mcq" && q.options
                      ? `
                    <div class="options-grid">
                      ${Object.entries(q.options)
                        .map(
                          ([k, v]) => `
                        <div class="option-item ${k === q.answer ? "correct" : ""}">
                          <div class="option-key">${k}</div>
                          <span>${v}</span>
                        </div>
                      `,
                        )
                        .join("")}
                    </div>
                  `
                      : ""
                  }
                  
                  ${
                    q.type === "true_false"
                      ? `
                    <div class="tf-row">
                      ${["True", "False"]
                        .map(
                          (v) => `
                        <div class="tf-item ${String(q.answer).toLowerCase() === v.toLowerCase() ? "correct" : ""}">
                          ${v === "True" ? "صح" : "خطأ"}
                        </div>
                      `,
                        )
                        .join("")}
                    </div>
                  `
                      : ""
                  }

                  ${
                    q.explanation
                      ? `
                    <div class="q-explain">
                      <div class="q-explain-head">
                        <i data-lucide="info" style="width:13px;height:13px"></i>
                        <span class="q-explain-lbl">تفسير الذكاء الاصطناعي</span>
                      </div>
                      <div class="q-explain-text q-explain-text--italic">${q.explanation}</div>
                    </div>
                  `
                      : ""
                  }
                </div>
              </div>
            </div>
          `,
            )
            .join("")}
        </div>

        <div class="preview-foot">
          <button type="button" class="btn-ghost preview-foot__btn"
            onclick="state.showPreview=false; renderStatus()">
            تجاهل وإغلاق
          </button>
          <button type="button" class="btn-primary preview-foot__btn--publish" onclick="publishQuiz()">
            <i data-lucide="rocket" style="width:18px;height:18px"></i>
            اعتماد ونشر الاختبار
          </button>
        </div>
      </div>
    </div>
  `;
}

function regenerateQuestion(idx) {
  showToast("جاري إعادة توليد السؤال... (تجريبي)", "info");
  // Logic for per-question regeneration can be added here
}

function publishQuiz() {
  showToast("تم اعتماد الاختبار ونشره بنجاح!", "success");
  setTimeout(() => {
    window.location.href = "trainer-dashboard.html";
  }, 1500);
}

/* ─── Materials Selector Logic ─────────────────────── */
function updateMaterials(entryId, selectEl) {
  const entry = state.entries.find((e) => e.id === entryId);
  if (!entry) return;
  entry.materials = Array.from(selectEl.selectedOptions).map((o) => o.value);
}

function toggleMaterialsPopover(entryId, event) {
  if (event) event.stopPropagation();
  const popover = document.getElementById(`popover-${entryId}`);
  const isShown = popover.classList.contains("show");

  // Close all other popovers
  document
    .querySelectorAll(".materials-popover")
    .forEach((p) => p.classList.remove("show"));

  if (!isShown) {
    popover.classList.add("show");
  }
}

function renderMaterialsPopoverContent(entry) {
  const session = state.sessions.find((s) => s.id == entry.sourceSessionId);
  if (!entry.sourceSessionId)
    return `<div style="padding:15px; text-align:center; color:var(--text-4); font-size:0.75rem;">يجب اختيار الجلسة أولاً</div>`;
  if (!session || !session.materials || session.materials.length === 0) {
    return `<div style="padding:15px; text-align:center; color:var(--text-4); font-size:0.75rem;">لا توجد مواد متاحة لهذه الجلسة</div>`;
  }

  const allSelected = session.materials.every((m) =>
    entry.materials.includes(m.id),
  );

  return `
    <div class="popover-actions">
      <span style="font-size: 10px; color: var(--text-4); font-weight: 700;">مواد الجلسة (${session.materials.length})</span>
      <button type="button" class="action-link" onclick="toggleAllMaterials(${entry.id}, ${!allSelected}, event)">
        ${allSelected ? "إلغاء تحديد الكل" : "تحديد الكل"}
      </button>
    </div>
    <div class="materials-list">
      ${session.materials
        .map((m) => {
          const isSelected = entry.materials.includes(m.id);
          const iconType =
            m.type === "pdf" ? "file-text" : m.type === "img" ? "image" : "file";
          const iconClass =
            m.type === "pdf" ? "pdf" : m.type === "img" ? "img" : "txt";

          return `
          <div class="material-item ${isSelected ? "selected" : ""}" onclick="toggleMaterial(${entry.id}, '${m.id}', event)">
            <div class="material-checkbox"></div>
            <div class="material-icon ${iconClass}">
              <i data-lucide="${iconType}" style="width:16px;height:16px"></i>
            </div>
            <div class="material-info">
              <div class="material-name" title="${m.name}">${m.name}</div>
              <div class="material-meta">
                <span class="material-type-tag">${m.type.toUpperCase()}</span>
                ${m.size ? `<span style="font-size:8px; color:var(--text-5)">• ${m.size}</span>` : ""}
              </div>
            </div>
          </div>
        `;
        })
        .join("")}
    </div>
  `;
}

function toggleMaterial(entryId, materialId, event) {
  if (event) event.stopPropagation();
  const entry = state.entries.find((e) => e.id === entryId);
  if (!entry) return;

  const idx = entry.materials.indexOf(materialId);
  if (idx > -1) {
    entry.materials.splice(idx, 1);
  } else {
    entry.materials.push(materialId);
  }

  refreshMaterialsUI(entryId, entry);
}

function toggleAllMaterials(entryId, shouldSelectAll, event) {
  if (event) event.stopPropagation();
  const entry = state.entries.find((e) => e.id === entryId);
  const session = state.sessions.find((s) => s.id == entry.sourceSessionId);
  if (!entry || !session) return;

  if (shouldSelectAll) {
    entry.materials = session.materials.map((m) => m.id);
  } else {
    entry.materials = [];
  }

  refreshMaterialsUI(entryId, entry);
}

function refreshMaterialsUI(entryId, entry) {
  const btnSpan = document.querySelector(
    `#entry-materials-wrap-${entryId} .materials-btn span`,
  );
  if (btnSpan) {
    btnSpan.textContent =
      entry.materials.length > 0
        ? `تم اختيار (${entry.materials.length}) مواد`
        : "اختر المواد للأسئلة...";
  }

  const popover = document.getElementById(`popover-${entryId}`);
  if (popover) {
    popover.innerHTML = renderMaterialsPopoverContent(entry);
    if (window.lucide) window.lucide.createIcons();
  }
}

// Close popovers on click outside
document.addEventListener("click", () => {
  document
    .querySelectorAll(".materials-popover")
    .forEach((p) => p.classList.remove("show"));
});

/* ─── Expose globals ─────────────────────────────────── */
Object.assign(window, {
  state,
  runValidation,
  shouldShowError,
  addEntry,
  removeEntry,
  updateEntry,
  updateCount,
  handleGenerate,
  jumpToError,
  publishQuiz,
  render,
  updateMaterials,
  regenerateQuestion
});
