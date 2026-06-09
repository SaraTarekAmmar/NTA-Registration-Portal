# NTA Admin UI — Full Audit Report
**Date:** 2026-06-08 | **Scope:** `admin/` directory (all HTML, JS, CSS)

---

## Executive Summary

A comprehensive code-level review of all admin-facing pages was conducted. **20 distinct bugs and issues** were identified across 6 pages. Issues are rated by severity:

| Severity | Count |
|---|---|
| 🔴 Critical (breaks core functionality) | 5 |
| 🟠 High (significant UX regression) | 7 |
| 🟡 Medium (noticeable but non-blocking) | 5 |
| 🔵 Low (polish / cosmetic) | 3 |

---

## Page-by-Page Findings

---

### 1. `index.html` — Login Page

#### 🟠 BUG-01: Arrow icon moves in the wrong direction on hover
**File:** `index.html` L152 & `styles.css` L413-415

The submit button shows a left-pointing arrow `←`. On hover, the animation translates it `translateX(4px)` (to the right). In an RTL (`dir="rtl"`) context, **right-pointing motion on the ← arrow is visually wrong** — the arrow should move left to indicate progression.

```diff
- transform: translateX(4px);   /* moves → which is backwards in RTL */
+ transform: translateX(-4px);  /* moves ← which matches the arrow direction */
```

#### 🟠 BUG-02: Login error shown via `alert()` — breaks UI
**File:** `index.html` L211

Login failures call `alert("خطأ في تسجيل الدخول: " + err.message)`. The `alert()` dialog is a blocking browser modal. All other pages use the toast/dropdown notification system. The login page should be consistent.

**Fix:** Replace `alert()` with an inline error element inside the card.

#### 🟡 BUG-03: `theme.css` version cache-busted inconsistently
**File:** `index.html` L5 vs `admin-users.html` L5, `admin-trainees.html` L5

`index.html` loads `theme.css?v=3` but `admin-users.html` and `admin-trainees.html` load `/common/css/theme.css` **without a version query**. Browsers may serve a stale cached copy on those two pages.

```diff
- <link rel="stylesheet" href="/common/css/theme.css" />
+ <link rel="stylesheet" href="/common/css/theme.css?v=3" />
```
**Affected files:** `admin-users.html` L5, `admin-trainees.html` L5

---

### 2. `admin.html` — Main Dashboard

#### 🔴 BUG-04: ECharts tooltip uses CSS variable string, not resolved color
**File:** `admin.html` L1123-1126

The `sharedTooltip()` function sets `textStyle.color` to the literal string `"var(--text-main)"`. ECharts does **not** evaluate CSS custom properties — tooltip text becomes invisible.

```diff
- color: "var(--text-main)",
+ color: getThemeColor("--text-main", "#e2e8f0"),
```

#### 🟡 BUG-05: Stage 2 and Stage 3 share the same color variable
**File:** `admin.html` L1048-1049

```js
{ id: 2, label: "الاستعلام الأمني", colorVar: "--color-info-soft", fallback: "#60a5fa" },
{ id: 3, label: "الاختبار النفسي",  colorVar: "--color-info-soft", fallback: "#60a5fa" },
```
Stages 2 and 3 are assigned **identical colors** — indistinguishable in the donut chart and legend.

```diff
- { id: 3, label: "الاختبار النفسي", colorVar: "--color-info-soft", fallback: "#60a5fa" },
+ { id: 3, label: "الاختبار النفسي", colorVar: "--color-info",      fallback: "#3b82f6" },
```

#### 🟠 BUG-06: `initCharts()` bound as `nta-theme-changed` listener accumulates on every call
**File:** `admin.html` L1472-1473

```js
window.removeEventListener("nta-theme-changed", initCharts);
window.addEventListener("nta-theme-changed", initCharts);
```

`initCharts` is an **inner function** — a new reference on each call. `removeEventListener` never removes the old one. Each theme change stacks another listener and calls `initCharts` multiple times, causing multiple chart re-initializations (memory leak).

**Fix:** Hoist `initCharts` to a stable outer-scope reference.

#### 🔵 BUG-07: `kpiDropped` KPI label says "المنسحبون" but counts `status === 'rejected'`
**File:** `admin.html` L1084-1086, L782

The KPI card label ("المنسحبون" = withdrawals) doesn't match its filter (`status === 'rejected'`). The label should be "المرفوضون" to match the data.

---

### 3. `admin-users.html` — Candidates List

#### 🔴 BUG-08: URL param `?status=rejected` never shows rejected users
**File:** `admin-users.html` L998-1002

The "المنسحبون" KPI card links to `admin-users.html?status=rejected`. The handler only catches:
```js
if (urlStatus === "accepted") activeStage = 7;
```
The case `urlStatus === "rejected"` is **never handled**. Clicking the red KPI card shows the full unfiltered candidate list — rejected users are never visible.

#### 🟠 BUG-09: Stage pill counts only count `status === 'active'` — pending candidates invisible
**File:** `admin-users.html` L760-762, L790-792

Both the pill counter and `applyFilters()` filter to `t.status === 'active'` only. Candidates in `pending` state are completely invisible — **they won't appear in any stage pill or card grid**. This silently drops candidates from the admin view.

#### 🟡 BUG-10: Search placeholder mentions email but email search can silently fail
**File:** `admin-users.html` L609-610

The search placeholder says "بحث بالاسم أو البريد..." but if `t.email` is `null`/`undefined`, the email OR branch is simply skipped with no indication to the admin that email search isn't working.

#### 🔵 BUG-11: Header version inconsistency — `header.js?v=2` vs `?v=3`
**File:** `admin-stage-review.html` L472

`admin-stage-review.html` still loads `header.js?v=2` while all other pages use `?v=3`. If `header.js` was updated, stage review is running a **stale header version**.

```diff
- <script src="header/header.js?v=2"></script>
+ <script src="header/header.js?v=3"></script>
```

---

### 4. `admin-trainees.html` — Enrolled Trainees

#### 🔴 BUG-12: Course ID type mismatch (number vs string) — entire trainee view broken
**File:** `admin-trainees.html` L1297, L1510, L1334, L1371

`activeCourse` defaults to string `"0"`. After first data load:
```js
activeCourse = COURSES[0].id;  // number: 1
```
But each student's courseId is stringified: `t.course_id.toString()` → `"1"`.

The strict equality check `s.courseId === activeCourse` compares `"1" === 1` → **always false**. KPI row shows `0` and grid shows "لا يوجد متدربون" even with real data.

```diff
- activeCourse = COURSES[0].id;
+ activeCourse = COURSES[0].id.toString();
```

#### 🟠 BUG-13: No loading state on course strip — blank bar on initial render
**File:** `admin-trainees.html` L1561

`renderCourseStrip()` is called before `fetchData()` resolves. The course strip shows only the label "الدورة:" with no pills and no loading indicator. Users see a blank strip with no feedback.

#### 🟠 BUG-14: Dead modal CSS with unscoped class may accidentally activate
**File:** `admin-trainees.html` L666-717

A large block of removed-modal CSS remains. The class `.at-modal-backdrop.is-open` (L679, without the `-unused` suffix) could accidentally match any future element with class `at-modal-backdrop`, causing an invisible ghost modal to display.

**Fix:** Delete the entire unused modal CSS block (lines 666–717).

---

### 5. `admin-stage-review.html` — Stage Review

#### 🔴 BUG-15: Two orphaned closing tags break DOM structure after stage panels
**File:** `admin-stage-review.html` L464-467

```html
        </section>  ← closes .admin-stage-panels (correct)
      </div>        ← ORPHAN — no matching open tag
      </section>    ← ORPHAN — no matching open tag
  </main>
```
These extra closing tags break the HTML parser, causing chat widget and scripts to land in incorrectly-parsed DOM nodes, creating **layout breaks below the stage panels**.

**Fix:** Remove lines 466 and 467.

#### 🔴 BUG-16: `triggerStage1AI` reads `window.traineeId` which is never set
**File:** `admin-stage-review.html` L1074

```js
let traineeId = window.traineeId;  // always undefined
```
The local `traineeId` (parsed from URL params at L482) is never assigned to `window.traineeId`. The AI full-check API fires with `trainee_id=undefined`, causing a 400/422 error. **Stage 1 AI verification button is non-functional.**

**Fix:** After line 482, add:
```js
window.traineeId = traineeId;
```
Or simply remove the re-declaration and use the outer-scope `traineeId` directly inside `triggerStage1AI`.

#### 🟠 BUG-17: Stage 7 "القبول النهائي" shows no confirmation of actual enrollment
**File:** `admin-stage-review.html` L796-806

When Stage 7 is accepted, only a stage review record is saved via POST `/api/admin/stage-review`. Whether the backend also updates `current_stage_id` to 7 and enrolls the trainee in the selected course is unclear from the UI. If enrollment fails silently, the admin sees a success toast but the trainee is not actually enrolled.

**Fix:** The success handler should display enrollment-specific confirmation (e.g., "تم قبول المتدرب وإلحاقه بالدورة") and navigate to the profile page.

#### 🟠 BUG-18: Stage 7 course dropdown not validated — can submit with no course selected
**File:** `admin-stage-review.html` L750-767

The mandatory field validator checks `[data-field]` elements but `<select>` with an empty default (`value=""`) passes the `!input.value` check. A reviewer can click "قبول واعتماد" **without selecting a course**, submitting `assigned_course_id: ""`.

**Fix:** Add explicit validation for Stage 7 before submit:
```js
if (stageId === 7) {
    const courseSelect = document.getElementById('assignedCourse');
    if (!courseSelect || !courseSelect.value) {
        window.showDropdownMessage('يرجى اختيار الدورة التدريبية قبل القبول', true);
        return;
    }
}
```

---

### 6. `admin-profile.html` — Trainee Profile

#### 🟡 BUG-19: No guard against `authenticatedFetch` being unavailable
**File:** `admin-profile.html` — general JS pattern

The profile page relies on `window.authenticatedFetch` being defined by `header.js`. If for any reason `header.js` fails to load (network error, CDN issue), all API calls on the page throw `TypeError: window.authenticatedFetch is not a function` with no user-facing error.

**Fix:** Add a guard at the start of the inline script:
```js
if (typeof window.authenticatedFetch !== 'function') {
    window.location.href = 'index.html';
    return;
}
```

#### 🔵 BUG-20: `chat.js` missing from `admin-users.html` and `admin-trainees.html`
**File:** `admin-users.html`, `admin-trainees.html`

`admin.html` and `admin-stage-review.html` load `chat.js` with a `#chatWidget` container. `admin-users.html` and `admin-trainees.html` have **no `chat.js` and no `#chatWidget`**. If the chat widget is a required global admin tool, it should be included on all admin pages.

---

## Summary Table

| # | Severity | Page | Category | Issue |
|---|---|---|---|---|
| BUG-01 | 🟠 High | index.html | UI/CSS | RTL arrow hover animation moves wrong direction |
| BUG-02 | 🟠 High | index.html | UX | Login errors use blocking `alert()` instead of toast |
| BUG-03 | 🟡 Medium | admin-users, admin-trainees | CSS | `theme.css` missing `?v=3` cache-buster |
| BUG-04 | 🔴 Critical | admin.html | JS/ECharts | CSS variables passed as strings to ECharts — invisible tooltip text |
| BUG-05 | 🟡 Medium | admin.html | UI/Charts | Stage 2 and 3 have identical colors in all charts |
| BUG-06 | 🟠 High | admin.html | JS | Theme-change listener accumulates — multiple chart re-renders on each change |
| BUG-07 | 🔵 Low | admin.html | UX/Copy | "المنسحبون" KPI label doesn't match its "rejected" filter |
| BUG-08 | 🔴 Critical | admin-users.html | JS | `?status=rejected` URL param never handled — rejected user view broken |
| BUG-09 | 🟠 High | admin-users.html | JS | Pending-status candidates are silently invisible in all views |
| BUG-10 | 🟡 Medium | admin-users.html | JS | Email search can silently fail for null email values |
| BUG-11 | 🔵 Low | admin-stage-review.html | HTML | `header.js?v=2` instead of `?v=3` — stale header |
| BUG-12 | 🔴 Critical | admin-trainees.html | JS | Course ID type mismatch (number vs string) breaks entire trainee view |
| BUG-13 | 🟠 High | admin-trainees.html | UX | No loading state on course strip — blank on initial render |
| BUG-14 | 🟠 High | admin-trainees.html | CSS | Dead modal CSS with unscoped class may accidentally activate |
| BUG-15 | 🔴 Critical | admin-stage-review.html | HTML | Two orphaned `</div></section>` break DOM structure after stage panels |
| BUG-16 | 🔴 Critical | admin-stage-review.html | JS | `window.traineeId` never set — Stage 1 AI check fires with `undefined` ID |
| BUG-17 | 🟠 High | admin-stage-review.html | UX/Logic | Stage 7 accept shows no enrollment confirmation |
| BUG-18 | 🟠 High | admin-stage-review.html | JS/Validation | Stage 7 course dropdown not validated — can enroll with no course |
| BUG-19 | 🟡 Medium | admin-profile.html | JS | No guard against `authenticatedFetch` being unavailable |
| BUG-20 | 🔵 Low | Multiple | HTML | `chat.js` missing from admin-users and admin-trainees pages |

---

## Priority Fix Order

**Fix immediately (blocks core workflows):**
1. BUG-15 — Remove orphaned tags in `admin-stage-review.html`
2. BUG-16 — Set `window.traineeId` so Stage 1 AI check works
3. BUG-12 — Fix course ID type mismatch in `admin-trainees.html`
4. BUG-08 — Handle `?status=rejected` URL param in `admin-users.html`
5. BUG-04 — Resolve CSS variables before passing to ECharts

**Fix soon (significant UX regressions):**
6. BUG-18 — Validate course selection on Stage 7 submit
7. BUG-09 — Show pending-status candidates in admin-users
8. BUG-06 — Fix accumulating theme-change listener
9. BUG-02 — Replace `alert()` with inline error in login

**Polish (fix when time allows):**
10. BUG-01, BUG-03, BUG-05, BUG-07, BUG-11, BUG-13, BUG-14, BUG-17, BUG-19, BUG-20
