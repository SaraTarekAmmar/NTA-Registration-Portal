(function () {
    const TOTAL_STEPS = 10;
    const API_PREFIX = (window.location.protocol.startsWith('http'))
        ? ''
        : 'http://127.0.0.1:8000';

    // Dynamic flow: keyed by step_key ("step_1" … "step_10")
    // Each entry: { is_visible, is_locked, locked_reason, status, id }
    const dynamicFlow = {};
    const urlParams0 = new URLSearchParams(window.location.search);
    const flowCourseType = urlParams0.get('course_type') || 'default';

    function _loadDynamicFlow() {
        var session = {};
        try { session = JSON.parse(localStorage.getItem('ntaTrainee') || '{}'); } catch(e) {}
        var token = session.token;
        var headers = token ? { 'Authorization': 'Bearer ' + token } : {};
        fetch(API_PREFIX + '/api/registration-flow?course_type=' + encodeURIComponent(flowCourseType), { headers: headers })
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
                if (!data || !data.steps) return;
                // Mark every step_1..step_10 hidden by default, then overlay resolved flow
                for (var i = 1; i <= TOTAL_STEPS; i++) {
                    dynamicFlow['step_' + i] = { is_visible: false, is_locked: false, locked_reason: null };
                }
                data.steps.forEach(function(s) {
                    dynamicFlow[s.step_key] = {
                        is_visible:    true,
                        is_locked:     s.is_locked,
                        locked_reason: s.locked_reason,
                        status:        s.status,
                        id:            s.id,
                        config:        s.config
                    };
                });
                _applyDynamicFlow();
            })
            .catch(function() {
                // Fallback: all steps visible, none locked
                for (var i = 1; i <= TOTAL_STEPS; i++) {
                    dynamicFlow['step_' + i] = { is_visible: true, is_locked: false, locked_reason: null };
                }
            });
    }

    function _applyDynamicFlow() {
        var stepperItems = document.querySelectorAll('.reg-stepper__item');
        stepperItems.forEach(function(item, idx) {
            var key = 'step_' + (idx + 1);
            var fd = dynamicFlow[key];
            if (fd && !fd.is_visible) {
                item.style.display = 'none';
                item.setAttribute('aria-hidden', 'true');
            }
        });
        // Hide form step panels that are not in flow
        document.querySelectorAll('.reg-step').forEach(function(panel) {
            var num = parseInt(panel.getAttribute('data-step'), 10);
            if (!num) return;
            var key = 'step_' + num;
            var fd = dynamicFlow[key];
                    if (fd && !fd.is_visible) {
                panel.setAttribute('data-flow-hidden', 'true');
            } else if (fd && fd.config && fd.config.fields) {
                // Hide specific fields if is_active is false
                fd.config.fields.forEach(function(f) {
                    if (f.is_active === false) {
                        var fieldId = f.field_id;
                        var els = panel.querySelectorAll('[name="' + fieldId + '"], [name="' + fieldId + '[]"], #' + fieldId);
                        els.forEach(function(el) {
                            var wrapper = el.closest('.editor-form-group') || el.closest('.form-group') || el.closest('div[style*="display: flex"]') || el.parentElement;
                            if (wrapper) {
                                wrapper.style.display = 'none';
                                wrapper.setAttribute('data-flow-hidden', 'true');
                            }
                            // Also disable so it skips validation
                            el.disabled = true;
                        });
                    }
                });
            }
        });
        updateUI();
    }

    function _getVisibleStepCount() {
        var count = 0;
        for (var i = 1; i <= TOTAL_STEPS; i++) {
            var fd = dynamicFlow['step_' + i];
            if (!fd || fd.is_visible !== false) count++;
        }
        return count;
    }

    function _nextVisibleStep(from) {
        for (var i = from + 1; i <= TOTAL_STEPS; i++) {
            var fd = dynamicFlow['step_' + i];
            if (!fd || fd.is_visible !== false) return i;
        }
        return null;
    }

    function _prevVisibleStep(from) {
        for (var i = from - 1; i >= 1; i--) {
            var fd = dynamicFlow['step_' + i];
            if (!fd || fd.is_visible !== false) return i;
        }
        return null;
    }

    _loadDynamicFlow();

    // Legacy locked-step set (kept for backward compat, superseded by dynamicFlow)
    const lockedStepOrders = new Set();
    const MAX_IDENTITY_DOCUMENT_FILES = 3;

    // Parse role from URL query parameters (default to 'trainee')
    const urlParams = new URLSearchParams(window.location.search);
    const registrationRole = urlParams.get('role') === 'trainer' ? 'trainer' : 'trainee';
    window.registrationRole = registrationRole;

    // Initialize Alert Banner
    document.addEventListener("DOMContentLoaded", function () {
        const banner = document.getElementById("roleAlertBanner");
        const label = document.getElementById("roleAlertLabel");
        const icon = document.getElementById("roleAlertIcon");
        if (banner && label) {
            banner.style.display = "flex";
            if (registrationRole === "trainer") {
                banner.classList.add("trainer");
                label.innerText = "مدرب معتمد (Trainer)";
                if (icon) icon.innerHTML = NTAIcons('teacher', 20);
            } else {
                banner.classList.add("trainee");
                label.innerText = "متدرب جديد (Trainee)";
                if (icon) icon.innerText = "🎓";
            }
        }
    });

    /** Per-step checks: visible fields must be filled; patterns and custom rules apply. Always enabled in production. */
    const STEP_VALIDATION_ENABLED = true;
    let currentStep = 1;
    /** True after leaving step 5 forward; shows read-only overlay on step 5 until cleared via Prev / stepper back to 5. */
    let skillsStep5Locked = false;

    const form = document.getElementById('regForm');
    if (form) form.setAttribute('novalidate', 'novalidate');

    const steps = document.querySelectorAll('.reg-step');
    const stepperItems = document.querySelectorAll('.reg-stepper__item');
    const progressBar = document.querySelector('.reg-stepper__bar');
    const btnPrev = document.getElementById('btnPrev');
    const btnNext = document.getElementById('btnNext');
    const btnSubmit = document.getElementById('btnSubmit');

    // -- Unified Dropdown Notification System (Toast) --
    window.showDropdownMessage = function (msg, isError = true) {
        let toastContainer = document.getElementById('globalToastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'globalToastContainer';
            toastContainer.className = 'global-toast-container';
            document.body.appendChild(toastContainer);
        }
        const toast = document.createElement('div');
        toast.className = 'reg-toast ' + (isError ? 'reg-toast--error' : 'reg-toast--success');
        toast.innerHTML = `<span style="font-size:1.25rem;">${isError ? '⚠️' : '✅'}</span><div style="flex:1;line-height:1.5;">${msg}</div><button type="button" class="reg-toast__close">&times;</button>`;
        toast.querySelector('button').onclick = () => { toast.style.opacity = '0'; toast.style.transform = 'translateY(-20px)'; setTimeout(() => toast.remove(), 300); };
        toastContainer.appendChild(toast);
        requestAnimationFrame(() => { toast.style.transform = 'translateY(0)'; toast.style.opacity = '1'; });
        setTimeout(() => { if (toast.parentElement) toast.querySelector('button').click(); }, 6000);
    };

    function isElementVisiblyHidden(el, stopAt) {
        let n = el;
        while (n && n !== stopAt) {
            if (!(n instanceof Element)) break;
            const st = window.getComputedStyle(n);
            if (st.display === 'none' || st.visibility === 'hidden') return true;
            n = n.parentElement;
        }
        return false;
    }

    /**
     * Require every visible control in the step: selects, text fields, files, radios (one per group),
     * and checkboxes (with special rules for interests, identity docs, social platforms).
     */
    function validateUniversalVisibleFields(stepEl) {
        let ok = true;
        const skipInputTypes = new Set(['hidden', 'button', 'submit', 'reset', 'image']);
        const hidden = (el) => isElementVisiblyHidden(el, stepEl);
        
        const stepNum = parseInt(stepEl.getAttribute('data-step'), 10);
        const fd = dynamicFlow['step_' + stepNum];
        const dynamicRequiredFields = new Set();
        if (fd && fd.config && fd.config.fields) {
            fd.config.fields.forEach(f => {
                if (f.is_required) dynamicRequiredFields.add(f.field_id);
            });
        }

        stepEl.querySelectorAll('select').forEach((sel) => {
            if (sel.disabled || hidden(sel)) return;
            if (sel.classList.contains('optional-select')) { sel.classList.remove('error'); return; }
            if (!String(sel.value || '').trim()) {
                sel.classList.add('error');
                sel.setAttribute('aria-invalid', 'true');
                ok = false;
            } else {
                sel.classList.remove('error');
                sel.removeAttribute('aria-invalid');
            }
        });

        stepEl.querySelectorAll('textarea').forEach((ta) => {
            if (ta.disabled || hidden(ta)) return;
            const optionalTextareas = ['scholarshipEssay', 'dietaryRestrictions', 'accessibilityRequirements'];
            const isDynamicReq = dynamicRequiredFields.has(ta.id) || dynamicRequiredFields.has(ta.name);
            if (!String(ta.value || '').trim()) {
                if (!isDynamicReq && (optionalTextareas.includes(ta.name) || ta.classList.contains('optional-input') || (ta.placeholder && ta.placeholder.includes('اختياري')))) {
                    ta.classList.remove('error');
                    ta.removeAttribute('aria-invalid');
                } else {
                    ta.classList.add('error');
                    ta.setAttribute('aria-invalid', 'true');
                    ok = false;
                }
            } else {
                ta.classList.remove('error');
                ta.removeAttribute('aria-invalid');
            }
        });

        stepEl.querySelectorAll('input').forEach((inp) => {
            if (inp.disabled || hidden(inp)) return;
            if (skipInputTypes.has(inp.type)) return;
            if (inp.type === 'radio' || inp.type === 'checkbox') return;
            if (inp.placeholder && inp.placeholder.includes('اختياري')) return;
            if (
                ['standardizedTestName[]', 'standardizedTestScore[]', 'standardizedTestAuthority[]', 'standardizedTestDate[]'].includes(inp.name)
                && !inp.value.trim()
            ) {
                const card = inp.closest('.test-score-card');
                if (card) {
                    const cardInputs = [...card.querySelectorAll('input[name="standardizedTestName[]"], input[name="standardizedTestScore[]"], input[name="standardizedTestAuthority[]"], input[name="standardizedTestDate[]"]')];
                    const hasAnyValue = cardInputs.some((el) => String(el.value || '').trim());
                    if (!hasAnyValue) return;
                }
            }

            if (inp.type === 'file') {
                const hasFile = inp.files && inp.files.length > 0;
                
                const optionalFiles = [
                    'lettersOfRecommendation',
                    'employerNoc',
                    'scholarshipEssayFile',
                    'portfolioFile',
                    'graduationCertificateScan[]'
                ];
                const isDynamicReq = dynamicRequiredFields.has(inp.id) || dynamicRequiredFields.has(inp.name);
                if (!isDynamicReq && (optionalFiles.includes(inp.name) || inp.classList.contains('optional-input')) && !hasFile) {
                    inp.classList.remove('error');
                    if (inp.parentElement) inp.parentElement.classList.remove('error');
                    return;
                }

                // Special case for standardized tests: if the entire card is empty, don't require the file
                if (inp.name === 'standardizedTestDocument[]') {
                    const card = inp.closest('.test-score-card');
                    if (card) {
                        const cardInputs = [...card.querySelectorAll('input[type="text"], input[type="date"]')];
                        const hasAnyTextValue = cardInputs.some((el) => String(el.value || '').trim());
                        if (!hasAnyTextValue && !hasFile) return; // Entire entry is empty, skip
                    }
                }

                inp.classList.toggle('error', !hasFile);
                const card = inp.closest('.photo-upload-card');
                if (card) {
                    card.classList.toggle('error', !hasFile);
                } else if (inp.parentElement) {
                    inp.parentElement.classList.toggle('error', !hasFile);
                }
                if (!hasFile) ok = false;
                return;
            }

            const optionalInputNames = [
                'mobileNumber2',
                'secondaryEmail',
                'emergencyId1',
                'emergencyId2',
                'scheduleAcknowledgment'  // informational confirmation checkbox — not a hard blocker
            ];
            const isDynamicReq = dynamicRequiredFields.has(inp.id) || dynamicRequiredFields.has(inp.name);

            if (!String(inp.value || '').trim()) {
                if (!isDynamicReq && (optionalInputNames.includes(inp.name) || inp.classList.contains('optional-input'))) {
                    inp.classList.remove('error');
                    inp.removeAttribute('aria-invalid');
                } else {
                    inp.classList.add('error');
                    inp.setAttribute('aria-invalid', 'true');
                    ok = false;
                }
            } else {
                inp.classList.remove('error');
                inp.removeAttribute('aria-invalid');
            }
        });

        const radioNames = new Set();
        stepEl.querySelectorAll('input[type="radio"]').forEach((r) => {
            if (!r.disabled && !hidden(r)) radioNames.add(r.name);
        });
        radioNames.forEach((name) => {
            const radios = [...stepEl.querySelectorAll(`input[type="radio"][name="${CSS.escape(name)}"]`)].filter(
                (r) => !r.disabled && !hidden(r)
            );
            if (radios.length === 0) return;
            const groupOk = radios.some((r) => r.checked);
            radios.forEach((r) => {
                const wrap = r.closest('.cognition-option') || r.closest('.reg-radio') || r.closest('label');
                if (wrap) wrap.classList.toggle('error', !groupOk);
            });
            if (!groupOk) ok = false;
        });

        const socialBlock = stepEl.querySelector('#socialMediaPlatformsBlock');
        if (socialBlock && !hidden(socialBlock)) {
            const uses = document.getElementById('usesSocialMedia');
            if (uses && uses.value === 'yes') {
                const vis = [...stepEl.querySelectorAll('input[type="checkbox"][name^="socialPlatform"]')].filter(
                    (b) => !hidden(b)
                );
                if (vis.length > 0) {
                    const anyPlat = vis.some((b) => b.checked);
                    vis.forEach((b) => b.closest('.social-toggle')?.classList.toggle('error', !anyPlat));
                    if (!anyPlat) ok = false;
                }
            }
        }

        const cbByName = new Map();
        stepEl.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
            if (cb.disabled || hidden(cb)) return;
            const n = cb.name;
            if (!n) return; // skip nameless checkboxes (e.g. whatsappSameAsMobile helper)
            if (n.startsWith('socialPlatform')) return;
            if (!cbByName.has(n)) cbByName.set(n, []);
            cbByName.get(n).push(cb);
        });

        cbByName.forEach((boxes, name) => {
            if (name === 'interestCode[]') {
                const n = boxes.filter((b) => b.checked).length;
                const interestOk = n >= 1 && n <= 5;
                boxes.forEach((b) => b.closest('.interest-item')?.classList.toggle('error', !interestOk));
                if (!interestOk) ok = false;
                return;
            }
            if (name === 'identityDocType') {
                const any = boxes.some((b) => b.checked);
                boxes.forEach((b) => b.closest('.identity-doc-option')?.classList.toggle('error', !any));
                if (!any) ok = false;
                return;
            }
            if (name === 'deansListHonors[]' || name === 'pvStillMember[]' || name === 'scheduleAcknowledgment') {
                return;
            }
            if (boxes.length === 1) {
                const b = boxes[0];
                const wrap = b.closest('label') || b.closest('.reg-checkbox');
                if (!b.checked) {
                    b.classList.add('error');
                    if (wrap) wrap.classList.add('error');
                    ok = false;
                } else {
                    b.classList.remove('error');
                    if (wrap) wrap.classList.remove('error');
                }
                return;
            }
            const any = boxes.some((b) => b.checked);
            boxes.forEach((b) => b.classList.toggle('error', !any));
            if (!any) ok = false;
        });

        return ok;
    }

    /**
     * @param {{ silent?: boolean }} [options] — if silent, no summary toast/scroll (used when checking multiple steps)
     */
    function validateCurrentStep(options = {}) {
        const silent = options.silent === true;
        const stepEl = document.querySelector(`.reg-step[data-step="${currentStep}"]`);
        if (!stepEl) return true;
        if (!STEP_VALIDATION_ENABLED) return true;

        let isValid = validateUniversalVisibleFields(stepEl);

        // Pattern validation (when field has a value)
        stepEl.querySelectorAll('input[pattern], textarea[pattern]').forEach((input) => {
            if (input.disabled || isElementVisiblyHidden(input, stepEl)) return;
            const v = String(input.value || '').trim();
            if (!v) return;
            if (input.pattern && !new RegExp(input.pattern).test(v)) {
                input.classList.add('error');
                isValid = false;
            }
        });

        // 1. Strict international phone (also emergency phones marked as type="text")
        const phoneInputs = stepEl.querySelectorAll(
            'input[type="tel"], input[name="emergencyPhone1"], input[name="emergencyPhone2"]'
        );
        const phonePattern = /^(\+|00)[1-9]\d{6,13}$/;
        phoneInputs.forEach((input) => {
            const prevPhoneErr = input.parentElement ? input.parentElement.querySelector('.phone-format-error') : null;
            if (prevPhoneErr) prevPhoneErr.remove();
            if (input.disabled || isElementVisiblyHidden(input, stepEl)) return;
            const v = input.value.trim();
            if (!v) return;
            if (!phonePattern.test(v)) {
                input.classList.add('error');
                isValid = false;
                window.showDropdownMessage('صيغة الهاتف غير صحيحة. يُرجى استخدام الصيغة الدولية، مثلاً: +201156806495 أو 00201156806495', true);
            }
        });

        // 2. Dates/Age Check (DOB between 16 and 60) - legacy field if present
        const dobInput = document.querySelector('input[name="dob"]');
        if (currentStep === 1 && dobInput && dobInput.value) {
            const birth = new Date(dobInput.value);
            const today = new Date();
            let age = today.getFullYear() - birth.getFullYear();
            const m = today.getMonth() - birth.getMonth();
            if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
            if (age < 16 || age > 60) {
                dobInput.classList.add('error');
                isValid = false;
                window.showDropdownMessage("يجب أن يكون العمر بين 16 و 60 عاماً.", true);
            }

            const maritalSelect = stepEl.querySelector('select[name="maritalStatus"]');
            if (maritalSelect && maritalSelect.value === 'married' && age < 18) {
                maritalSelect.classList.add('error');
                isValid = false;
                if (!silent) window.showDropdownMessage("لا يمكن اختيار حالة متزوج لسن أقل من 18 عاماً.", true);
            }
        }

        // 3. National ID match check (legacy flow: requires DOB + National ID)
        const nidInput = document.querySelector('input[name="nationalId"]');
        if (currentStep === 1 && nidInput && nidInput.value.trim().length === 14 && dobInput && dobInput.value && isValid) {
            const birth = new Date(dobInput.value);
            const yearStr = birth.getFullYear().toString();
            // Egyptian national ID logic: Century code (2 for 19xx, 3 for 20xx) + YYMMDD
            const centuryPattern = yearStr.startsWith('19') ? '2' : '3';
            const yy = yearStr.slice(-2);
            const mm = (birth.getMonth() + 1).toString().padStart(2, '0');
            const dd = birth.getDate().toString().padStart(2, '0');
            const expectedPrefix = centuryPattern + yy + mm + dd;
            if (!nidInput.value.startsWith(expectedPrefix)) {
                nidInput.classList.add('error');
                isValid = false;
                window.showDropdownMessage("الرقم القومي المدخل لا يتطابق مع تاريخ الميلاد.", true);
            }
        }

        // 4. Professional History Timeline (End > Start) — legacy summary section fields
        if (currentStep === 4) {
            const starts = stepEl.querySelectorAll('input[name="startDate[]"]');
            const ends = stepEl.querySelectorAll('input[name="endDate[]"]');
            for (let i = 0; i < starts.length; i++) {
                if (starts[i].value && ends[i].value) {
                    if (new Date(ends[i].value) <= new Date(starts[i].value)) {
                        ends[i].classList.add('error');
                        isValid = false;
                        window.showDropdownMessage("تاريخ الانتهاء في التاريخ المهني يجب أن يكون بعد تاريخ البدء.", true);
                    } else {
                        ends[i].classList.remove('error');
                    }
                }
            }

            // BUG-12 fix: Also validate the primary employment history cards
            // (.emp-history-card) which use .emp-joining-date / .emp-end-date,
            // NOT the legacy startDate[]/endDate[] fields validated above.
            stepEl.querySelectorAll('.emp-history-card').forEach((card) => {
                if (isElementVisiblyHidden(card, stepEl)) return;
                const joiningInput = card.querySelector('.emp-joining-date');
                const endInput = card.querySelector('.emp-end-date');
                // Skip if currently working (end-date wrap is hidden → no end date expected)
                const endDateWrap = card.querySelector('.emp-end-date-wrap');
                const currentlyWorking = endDateWrap && endDateWrap.style.display === 'none';
                if (!joiningInput || !endInput || currentlyWorking) return;
                if (joiningInput.value && endInput.value) {
                    if (new Date(endInput.value) <= new Date(joiningInput.value)) {
                        endInput.classList.add('error');
                        isValid = false;
                        if (!silent) window.showDropdownMessage("تاريخ انتهاء الخبرة المهنية يجب أن يكون بعد تاريخ الالتحاق.", true);
                    } else {
                        endInput.classList.remove('error');
                    }
                }
            });
        }

        // 5. Academic Grad Year Check (between DOB+16 and current year) — section 3
        if (currentStep === 3 && dobInput && dobInput.value) {
            const birthYear = new Date(dobInput.value).getFullYear();
            const gradYears = stepEl.querySelectorAll('input[name="graduationYear[]"]');
            const currYear = new Date().getFullYear();
            gradYears.forEach(gy => {
                if (gy.value) {
                    const yr = parseInt(gy.value);
                    if (yr < birthYear + 16 || yr > currYear) {
                        gy.classList.add('error');
                        isValid = false;
                        window.showDropdownMessage("سنة التخرج المدخلة غير منطقية مقارنة بتاريخ الميلاد.", true);
                    } else {
                        gy.classList.remove('error');
                    }
                }
            });
        }

        // 6. Step 10 — URL format for visible social-verify rows (files & attestation covered by universal pass)
        if (currentStep === 10) {
            stepEl.querySelectorAll('.social-verify-row').forEach((row) => {
                if (isElementVisiblyHidden(row, stepEl)) return;
                const u = row.querySelector('input[type="url"]');
                if (!u) return;
                const v = u.value.trim();
                if (!v) {
                    u.classList.add('error');
                    isValid = false;
                } else if (!/^https?:\/\/.+\..+/.test(v)) {
                    u.classList.add('error');
                    isValid = false;
                } else {
                    u.classList.remove('error');
                }
            });
        }

        // 6b. URL Verification Check (portfolio URL — merged into section 6)
        if (currentStep === 6) {
            const urlInputs = stepEl.querySelectorAll('input[type="url"]');
            urlInputs.forEach(u => {
                if (u.value.trim() && !/^https?:\/\/.+\..+/.test(u.value.trim())) {
                    u.classList.add('error');
                    isValid = false;
                } else if (u.value.trim()) {
                    u.classList.remove('error');
                }
            });
        }

        // 6b. Step 2 – Emergency contact count logic validation
        if (currentStep === 2) {
            const contactCount = stepEl.querySelector('select[name="emergencyContactsCount"]');
            const name2 = stepEl.querySelector('input[name="emergencyName2"]');
            const phone2 = stepEl.querySelector('input[name="emergencyPhone2"]');
            const address2 = stepEl.querySelector('input[name="emergencyAddress2"]');
            if (contactCount && contactCount.value === '2') {
                [name2, phone2, address2].forEach((el) => {
                    if (el && !el.value.trim()) {
                        el.classList.add('error');
                        isValid = false;
                    }
                });
            }

            // Both primaryEmail and secondaryEmail live in Step 2 — scope query to stepEl.
            const primaryEmail = stepEl.querySelector('input[name="primaryEmail"]');
            const secondaryEmail = stepEl.querySelector('input[name="secondaryEmail"]');
            if (primaryEmail && secondaryEmail && primaryEmail.value.trim() && secondaryEmail.value.trim()) {
                if (primaryEmail.value.trim().toLowerCase() === secondaryEmail.value.trim().toLowerCase()) {
                    primaryEmail.classList.add('error');
                    secondaryEmail.classList.add('error');
                    isValid = false;
                    if (!silent) window.showDropdownMessage("لا يمكن استخدام نفس البريد الإلكتروني كبريد أساسي وثانوي.", true);
                }
            }
        }

        // 7. References Check — section 8
        if (currentStep === 8) {
            const contacts = stepEl.querySelectorAll('input[name="referenceContact[]"]');
            contacts.forEach(c => {
                // Remove any previous reference contact error
                const prevRefErr = c.parentElement ? c.parentElement.querySelector('.ref-contact-error') : null;
                if (prevRefErr) prevRefErr.remove();

                if (c.value.trim()) {
                    const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(c.value.trim());
                    const phonePattern = /^(\+|00)[1-9]\d{6,13}$/;
                    const isPhone = phonePattern.test(c.value.trim());
                    if (!isEmail && !isPhone) {
                        c.classList.add('error');
                        isValid = false;
                        window.showDropdownMessage('يجب أن تكون معلومات جهات الاتصال بريدًا إلكترونيًا صحيحًا أو رقمًا دوليًا مثل +201156806495.', true);
                    } else {
                        c.classList.remove('error');
                    }
                }
            });
        }

        // 8. Mandatory document uploads — section 8
        if (currentStep === 8) {
            const hasPriorConvictions = (document.getElementById('hasPriorCriminalConvictions')?.value || '').trim();
            const step8CriminalGroup = document.getElementById('step8CriminalRecordGroup');
            const step8CriminalInput = document.getElementById('criminalRecord');
            const mandatoryDocs = ['cvResume'];
            if (step8CriminalInput && step8CriminalGroup && !isElementVisiblyHidden(step8CriminalGroup, stepEl)) {
                if (hasPriorConvictions !== 'yes') mandatoryDocs.push('criminalRecord');
            }
            mandatoryDocs.forEach(name => {
                const input = stepEl.querySelector(`input[name="${name}"]`);
                if (input && (!input.files || input.files.length === 0)) {
                    if (input.parentElement) input.parentElement.classList.add('error');
                    isValid = false;
                } else if (input && input.parentElement) {
                    input.parentElement.classList.remove('error');
                }
            });
        }

        // 9. Step 3 — Education conditional mandatory fields
        if (currentStep === 3) {
            const degreeSel = document.getElementById('eduHighestDegree');
            const mainBlock = document.getElementById('eduMainFieldsBlock');
            if (degreeSel && degreeSel.value && mainBlock && mainBlock.style.display !== 'none') {
                mainBlock.querySelectorAll('.main-education-card').forEach(card => {
                    const inst = card.querySelector('.edu-institution');
                    const gpaGroup = card.querySelector('.edu-gpa-group');
                    const totalScoreGroup = card.querySelector('.edu-total-score-group');
                    const pctGroup = card.querySelector('.edu-percentage-group');
                    const gradDate = card.querySelector('.edu-graduation-date');
                    if (inst && !inst.value) { inst.classList.add('error'); isValid = false; }
                    if (gpaGroup && gpaGroup.style.display !== 'none') {
                        const gpa = gpaGroup.querySelector('.edu-gpa');
                        if (gpa && !gpa.value.trim()) { gpa.classList.add('error'); isValid = false; }
                    }
                    if (totalScoreGroup && totalScoreGroup.style.display !== 'none') {
                        const ts = totalScoreGroup.querySelector('.edu-total-score');
                        if (ts && !ts.value.trim()) { ts.classList.add('error'); isValid = false; }
                    }
                    if (pctGroup && pctGroup.style.display !== 'none') {
                        const pct = pctGroup.querySelector('.edu-percentage');
                        if (pct && !pct.value.trim()) { pct.classList.add('error'); isValid = false; }
                    }
                    if (gradDate && !gradDate.value) { gradDate.classList.add('error'); isValid = false; }
                });
            }
            const pgHas = document.getElementById('eduHasPostgraduate');
            const pgDetails = document.getElementById('eduPostgraduateDetails');
            if (pgHas && pgHas.value === 'yes' && pgDetails && pgDetails.style.display !== 'none') {
                pgDetails.querySelectorAll('.higher-education-card').forEach(card => {
                    const degType = card.querySelector('.edu-pg-degree-type');
                    const issuer = card.querySelector('.edu-degree-issuer-entity');
                    const mainSpec = card.querySelector('.edu-main-speciality-pg');
                    const startDate = card.querySelector('.edu-pg-start-date');
                    const endDate = card.querySelector('.edu-pg-end-date');
                    if (degType && !degType.value) { degType.classList.add('error'); isValid = false; }
                    if (issuer && !issuer.value.trim()) { issuer.classList.add('error'); isValid = false; }
                    if (mainSpec && !mainSpec.value.trim()) { mainSpec.classList.add('error'); isValid = false; }
                    if (startDate && !startDate.value) { startDate.classList.add('error'); isValid = false; }
                    if (endDate && !endDate.value) { endDate.classList.add('error'); isValid = false; }
                });
            }

            // Standardized tests conditional validation
            const testCards = stepEl.querySelectorAll('.test-score-card');
            testCards.forEach(card => {
                const nameInp = card.querySelector('.test-name');
                const scoreInp = card.querySelector('.test-score');
                const authInp = card.querySelector('.test-authority');
                const dateInp = card.querySelector('.standardized-test-date');
                const docInp = card.querySelector('.test-document');
                const urlInp = card.querySelector('.test-url');
                
                const hasValue = (nameInp && nameInp.value.trim()) ||
                                  (scoreInp && scoreInp.value.trim()) ||
                                  (authInp && authInp.value.trim()) ||
                                  (dateInp && dateInp.value.trim()) ||
                                  (docInp && docInp.files && docInp.files.length > 0);
                                  
                if (hasValue) {
                    if (urlInp && !urlInp.value.trim()) {
                        urlInp.classList.add('error');
                        isValid = false;
                        if (!silent) window.showDropdownMessage('يرجى إدخال رابط التحقق لكل اختبار معياري قمت بملئه.', true);
                    } else if (urlInp) {
                        urlInp.classList.remove('error');
                    }
                } else if (urlInp) {
                    urlInp.classList.remove('error');
                }
            });
        }

        // 10. Step 4 — Employment conditional mandatory fields
        if (currentStep === 4) {
            const empStatus = document.querySelector('select[name="empExperienceStatus"]');
            if (empStatus && empStatus.value === 'have_experience') {
                const empBlock = document.getElementById('employmentDetailsBlock') || document.getElementById('empHaveExperienceBlock');
                if (empBlock && empBlock.style.display !== 'none') {
                    const empCvInput = empBlock.querySelector('input[name="employmentSectionCv"]');
                    if (empCvInput && (!empCvInput.files || empCvInput.files.length === 0)) {
                        if (empCvInput.parentElement) empCvInput.parentElement.classList.add('error');
                        isValid = false;
                        window.showDropdownMessage('يرجى رفع السيرة الذاتية في قسم الخبرة المهنية.', true);
                    }
                }
            }
        }

        // 11. Step 5 — Skills mandatory: at least 1 entry each + interestsDescription
        if (currentStep === 5) {
            const stepEl5 = document.querySelector('.reg-step[data-step="5"]');
            if (stepEl5) {
                const checkSkillSection = (containerSelector, labelText) => {
                    const container = stepEl5.querySelector(containerSelector);
                    if (!container || isElementVisiblyHidden(container, stepEl5)) return;
                    // Skill rows use <select class="skill-name">, not input[type="text"].
                    // Validation passes if at least one skill-name select has a non-empty value.
                    const skillSelects = container.querySelectorAll('select.skill-name');
                    const hasEntry = Array.from(skillSelects).some(sel => sel.value && sel.value.trim());
                    if (!hasEntry) {
                        skillSelects.forEach(sel => sel.classList.add('error'));
                        isValid = false;
                        if (!silent) window.showDropdownMessage(`يرجى إضافة ${labelText} واحدة على الأقل.`, true);
                    }
                };
                checkSkillSection('#technicalSkillsContainer', 'مهارة تقنية');
                checkSkillSection('#softSkillsContainer', 'مهارة شخصية');
                checkSkillSection('#computerSkillsContainer', 'مهارة حاسوبية');
                // BUG 18 fix: interestsDescription is <input type="text">, not <textarea>.
                const intDesc = stepEl5.querySelector('input[name="interestsDescription"]');
                if (intDesc && !isElementVisiblyHidden(intDesc, stepEl5) && !intDesc.value.trim()) {
                    intDesc.classList.add('error');
                    isValid = false;
                }
            }
        }

        // 12. Step 7 — Conditional mandatory sub-fields for yes/no sections
        if (currentStep === 7) {
            const stepEl7 = document.querySelector('.reg-step[data-step="7"]');
            if (stepEl7) {
                const requireFields = (blockId, fieldSelectors) => {
                    const block = document.getElementById(blockId);
                    if (!block || block.style.display === 'none') return;
                    fieldSelectors.forEach(sel => {
                        const el = block.querySelector(sel);
                        if (!el || isElementVisiblyHidden(el, stepEl7)) return;
                        const isEmpty = (el.tagName === 'SELECT') ? !el.value : !el.value.trim();
                        if (isEmpty) { el.classList.add('error'); isValid = false; }
                    });
                };
                const hasPvWork = document.getElementById('hasPublicVoluntaryWork');
                if (hasPvWork && hasPvWork.value === 'yes') {
                    const pvCards = document.querySelectorAll('#publicVoluntaryWorkBlock .pv-card, #publicVoluntaryWorkContainer .pv-entry');
                    if (pvCards.length > 0) {
                        pvCards.forEach(card => {
                            ['input[name="pvFoundationName[]"]','input[name="pvPosition[]"]','input[name="pvJoinDate[]"]'].forEach(sel => {
                                const el = card.querySelector(sel);
                                if (el && !el.value.trim()) { el.classList.add('error'); isValid = false; }
                            });
                        });
                    } else {
                        requireFields('publicVoluntaryWorkBlock', [
                            'input[name="pvFoundationName[]"]','input[name="pvPosition[]"]','input[name="pvJoinDate[]"]'
                        ]);
                    }
                }
                const hasPolitical = document.getElementById('hasPoliticalParticipation');
                if (hasPolitical && hasPolitical.value === 'yes') {
                    requireFields('politicalWorkBlock', [
                        'input[name="politicalPartyName"]',
                        'input[name="politicalRole"]',
                        'input[name="politicalWorkDetails"]'
                    ]);
                }
                const hasCandidacy = document.getElementById('hasPoliticalCandidacy');
                if (hasCandidacy && hasCandidacy.value === 'yes') {
                    requireFields('politicalCandidacyBlock', [
                        'input[name="candidacyPositionName"]',
                        'select[name="candidacyResult"]',
                        'input[name="candidacyExperienceDescription"]'
                    ]);
                }
                const hasPriorConv = document.getElementById('hasPriorCriminalConvictions');
                if (hasPriorConv && hasPriorConv.value === 'yes') {
                    requireFields('legalStatusBlock', ['input[name="priorConvictionDescription"]']);
                    const legalBlock = document.getElementById('legalStatusBlock');
                    if (legalBlock && legalBlock.style.display !== 'none') {
                        const certInput = legalBlock.querySelector('input[name="sectionSevenCriminalRecordCertificate"]');
                        if (certInput && (!certInput.files || certInput.files.length === 0)) {
                            if (certInput.parentElement) certInput.parentElement.classList.add('error');
                            isValid = false;
                        }
                    }
                }
            }
        }

        // 13. Section 1 conditional checks
        if (currentStep === 1) {
            const identityDocCheckboxes = stepEl.querySelectorAll('input[name="identityDocType"]');
            const nationalIdInput = stepEl.querySelector('input[name="nationalId"]');
            const passportInput = stepEl.querySelector('input[name="passportNumber"]');
            const idScanInput = stepEl.querySelector('input[name="identityDocumentScan"]');
            const militaryStatus = stepEl.querySelector('select[name="militaryStatus"]');
            const militaryReason = stepEl.querySelector('input[name="militaryReason"]');
            const nationalityCount = stepEl.querySelector('select[name="numberOfNationalities"]');
            const secondNationality = stepEl.querySelector('select[name="secondNationality"]');
            const thirdNationality = stepEl.querySelector('select[name="thirdNationality"]');
            const selectedDocTypes = Array.from(identityDocCheckboxes).filter(c => c.checked).map(c => c.value);

            if (identityDocCheckboxes.length > 0 && selectedDocTypes.length === 0) {
                isValid = false;
            }

            if (selectedDocTypes.includes('national_id')) {
                const val = (nationalIdInput.value || '').trim();
                if (!nationalIdInput || !/^\d{14}$/.test(val)) {
                    if (nationalIdInput) nationalIdInput.classList.add('error');
                    isValid = false;
                } else if (nationalIdInput) {
                    const genderDigit = parseInt(val.charAt(12), 10);
                    const expectedGender = (genderDigit % 2 === 0) ? 'female' : 'male';
                    const selectedGenderRadio = stepEl.querySelector('input[name="gender"]:checked');
                    if (selectedGenderRadio && selectedGenderRadio.value !== expectedGender) {
                        nationalIdInput.classList.add('error');
                        isValid = false;
                        if (!silent) window.showDropdownMessage("النوع المدخل لا يتطابق مع الرقم القومي.", true);
                    } else {
                        nationalIdInput.classList.remove('error');
                    }
                }
            }

            if (selectedDocTypes.includes('passport')) {
                if (!passportInput || !/^[a-zA-Z0-9]+$/.test((passportInput.value || '').trim())) {
                    if (passportInput) passportInput.classList.add('error');
                    isValid = false;
                }
            }

            if (selectedDocTypes.length > 0) {
                if (!idScanInput || !idScanInput.files || idScanInput.files.length === 0) {
                    if (idScanInput && idScanInput.parentElement) idScanInput.parentElement.classList.add('error');
                    isValid = false;
                } else if (idScanInput.files.length > MAX_IDENTITY_DOCUMENT_FILES) {
                    if (idScanInput.parentElement) idScanInput.parentElement.classList.add('error');
                    isValid = false;
                    if (!silent) window.showDropdownMessage(`يمكنك رفع ${MAX_IDENTITY_DOCUMENT_FILES} ملفات كحد أقصى لوثيقة الهوية.`, true);
                }
            }

            if (militaryStatus && militaryReason) {
                const needsReason = ['exempted', 'postponed', 'currently_serving'].includes(militaryStatus.value);
                if (needsReason && !militaryReason.value.trim()) {
                    militaryReason.classList.add('error');
                    isValid = false;
                }
            }

            if (nationalityCount) {
                if (['2', '3'].includes(nationalityCount.value) && (!secondNationality || !secondNationality.value)) {
                    if (secondNationality) secondNationality.classList.add('error');
                    isValid = false;
                }
                if (nationalityCount.value === '3' && (!thirdNationality || !thirdNationality.value)) {
                    if (thirdNationality) thirdNationality.classList.add('error');
                    isValid = false;
                }
            }
        }

        if (!isValid && !silent) {
            const errorFields = [];
            stepEl.querySelectorAll('.error, .reg-radio.error, .reg-checkbox.error, .accordion-header.error, .photo-upload-card.error, .social-toggle.error').forEach(el => {
                let labelText = '';
                const formGroup = el.closest('.form-group') || el.closest('.form-group-inline') || el.closest('.skill-row-inline') || el.closest('.additional-lang-row');
                if (formGroup) {
                    const label = formGroup.querySelector('label');
                    if (label) {
                        labelText = label.textContent.replace(/\(.*?\)/g, '').replace(/[\*:]/g, '').trim();
                    }
                }
                if (!labelText && el.placeholder) {
                    labelText = el.placeholder.trim();
                }
                if (!labelText && el.getAttribute('aria-label')) {
                    labelText = el.getAttribute('aria-label').trim();
                }
                if (!labelText && el.name) {
                    labelText = el.name;
                }
                if (labelText && !errorFields.includes(labelText)) {
                    errorFields.push(labelText);
                }
            });

            let errMsg = "يوجد أخطاء في الحقول التالية:<br>";
            if (errorFields.length > 0) {
                errMsg += "• " + errorFields.join("<br>• ");
            } else {
                errMsg += "يرجى مراجعة الحقول المحددة باللون الأحمر وتصحيحها.";
            }

            window.showDropdownMessage(errMsg, true);

            stepEl.querySelectorAll('.acc-item:not(.open)').forEach(acc => {
                if (acc.querySelector('.error')) {
                    acc.classList.add('open');
                }
            });
            stepEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        return isValid;
    }

    function setupStepTenPhotoFilenameHints() {
        document.querySelectorAll('.reg-step[data-step="10"] .photo-upload-card').forEach((card) => {
            const input = card.querySelector('.photo-input');
            const nameEl = card.querySelector('.photo-upload-filename');
            const previewEl = card.querySelector('.photo-upload-preview');
            const iconEl = card.querySelector('.photo-upload-icon');
            if (!input || !nameEl) return;

            const clearPreview = () => {
                const oldUrl = input.dataset.previewUrl;
                if (oldUrl) {
                    URL.revokeObjectURL(oldUrl);
                    delete input.dataset.previewUrl;
                }
                if (previewEl) {
                    previewEl.removeAttribute('src');
                    previewEl.hidden = true;
                }
                if (iconEl) iconEl.hidden = false;
            };

            input.addEventListener('change', () => {
                const file = input.files && input.files[0];
                if (file && file.name) {
                    nameEl.textContent = file.name;
                    nameEl.hidden = false;
                    clearPreview();
                    if (previewEl && file.type && file.type.startsWith('image/')) {
                        const previewUrl = URL.createObjectURL(file);
                        input.dataset.previewUrl = previewUrl;
                        previewEl.src = previewUrl;
                        previewEl.hidden = false;
                        if (iconEl) iconEl.hidden = true;
                    }
                } else {
                    nameEl.textContent = '';
                    nameEl.hidden = true;
                    clearPreview();
                }
            });
        });
    }

    function setupStepEightMultiFileNames() {
        const stepEightEl = document.querySelector('.reg-step[data-step="8"]');
        if (!stepEightEl) return;

        stepEightEl.querySelectorAll('input[type="file"][multiple]').forEach((input) => {
            const render = () => {
                const files = Array.from(input.files || []);
                if (files.length === 0) {
                    input.removeAttribute('title');
                    return;
                }

                const names = files.map((f) => f.name);
                input.title = names.join('، ');
            };

            input.addEventListener('change', render);
        });
    }

    function setupStepEightScholarshipEssayCount() {
        const essayTextarea = document.getElementById('scholarshipEssay');
        const counterEl = document.getElementById('essayWordCount');
        if (essayTextarea && counterEl) {
            const updateCount = () => {
                const len = essayTextarea.value.length;
                counterEl.textContent = `الحروف: ${len} / 5000`;
            };
            essayTextarea.addEventListener('input', updateCount);
            essayTextarea.addEventListener('change', updateCount);
            updateCount();
        }
    }

    function syncStepTenSocialRows() {
        const usesEl = document.getElementById('usesSocialMedia');
        const yes = usesEl && usesEl.value === 'yes';
        document.querySelectorAll('.social-verify-row').forEach((row) => {
            const plat = row.getAttribute('data-requires-platform');
            const cb = plat ? document.querySelector(`input[name="${plat}"]`) : null;
            const input = row.querySelector('input[type="url"]');
            const show = Boolean(yes && cb && cb.checked);
            row.style.display = show ? '' : 'none';
            if (input) {
                input.required = show;
                if (!show) input.classList.remove('error');
            }
        });
    }

    function disableNativeValidationAttributes() {
        // Redundant since novalidate is set on the form.
    }

    // ── URL step routing ──────────────────────────────────────────────────────
    function syncUrlToStep(step, replace = false) {
        const url = new URL(window.location.href);
        url.searchParams.set('step', step);
        if (replace) {
            history.replaceState({ step }, '', url.toString());
        } else {
            history.pushState({ step }, '', url.toString());
        }
    }

    // ── Form state persistence (sessionStorage) ───────────────────────────────
    const STATE_KEY = 'nta_reg_form_state';

    function saveFormState() {
        if (!form) return;
        const state = { _step: currentStep };
        const nameCounts = {};

        form.querySelectorAll('input, select, textarea').forEach(el => {
            if (!el.name || el.type === 'file' || el.type === 'submit' || el.type === 'button' || el.type === 'image' || el.type === 'reset') return;
            const name = el.name;
            if (nameCounts[name] === undefined) {
                nameCounts[name] = 0;
            } else {
                nameCounts[name]++;
            }
            const key = name + '@@idx_' + nameCounts[name];

            if (el.type === 'checkbox' || el.type === 'radio') {
                if (!state[key]) state[key] = [];
                if (el.checked) state[key].push(el.value);
            } else {
                state[key] = el.value;
            }
        });

        // Save dynamically cloned card counts
        const cardCounts = {};
        [
            ['#mainEducationContainer', '.main-education-card'],
            ['#higherEducationContainer', '.higher-education-card'],
            ['#employmentHistoryContainer', '.emp-history-card'],
            ['#empReferencesContainer', '.employment-ref-card'],
            ['#technicalSkillsContainer', '.skill-row-inline'],
            ['#softSkillsContainer', '.skill-row-inline'],
            ['#computerSkillsContainer', '.skill-row-inline'],
            ['#prizesAwardsContainer', '.prize-entry-card'],
            ['#conferencesWorkshopsContainer', '.cw-entry-card'],
            ['#publicVoluntaryContainer', '.pv-work-card'],
            ['#phoneNumbersContainer', '.phone-row'],
            ['#additionalLanguagesContainer', '.additional-lang-row'],
            ['#referencesContainer', '.reference-row'],
        ].forEach(([container, card]) => {
            const el = document.querySelector(container);
            if (el) cardCounts[container] = el.querySelectorAll(card).length;
        });
        state.__cardCounts = cardCounts;

        try { sessionStorage.setItem(STATE_KEY, JSON.stringify(state)); } catch (_) {}
    }

    function restoreFormState() {
        let raw;
        try { raw = sessionStorage.getItem(STATE_KEY); } catch (_) { return; }
        if (!raw) return;
        let state;
        try { state = JSON.parse(raw); } catch (_) { return; }
        if (!form) return;
        // Restore step from URL param first, then state
        const urlStep = parseInt(new URLSearchParams(window.location.search).get('step') || '0', 10);
        if (urlStep >= 1 && urlStep <= TOTAL_STEPS) currentStep = urlStep;
        else if (state._step >= 1 && state._step <= TOTAL_STEPS) currentStep = state._step;

        // Restore field values after a small delay to let lookups populate
        setTimeout(() => {
            // Restore card counts by programmatically clicking "Add" buttons
            const counts = state.__cardCounts || {};
            const addBtnMap = {
                '#mainEducationContainer': '#addMainEduBtn',
                '#higherEducationContainer': '#addHigherEduBtn',
                '#employmentHistoryContainer': '#addEmploymentCardBtn',
                '#empReferencesContainer': '#addEmpReferenceBtn',
                '#technicalSkillsContainer': '#addTechnicalSkillBtn',
                '#computerSkillsContainer': '#addComputerSkillBtn',
                '#softSkillsContainer': '#addSoftSkillBtn',
                '#prizesAwardsContainer': '#addPrizeEntryBtn',
                '#conferencesWorkshopsContainer': '#addConferenceWorkshopBtn',
                '#publicVoluntaryContainer': '#addPublicVoluntaryBtn',
                '#phoneNumbersContainer': '#addPhoneBtn',
                '#additionalLanguagesContainer': '#addAdditionalLanguageBtn',
                '#referencesContainer': '#addReferenceBtn',
            };

            Object.entries(addBtnMap).forEach(([containerSelector, btnSelector]) => {
                const container = document.querySelector(containerSelector);
                const btn = document.querySelector(btnSelector);
                if (!container || !btn) return;
                
                const cardClass = containerSelector === '#mainEducationContainer' ? '.main-education-card' :
                                  containerSelector === '#higherEducationContainer' ? '.higher-education-card' :
                                  containerSelector === '#employmentHistoryContainer' ? '.emp-history-card' :
                                  containerSelector === '#empReferencesContainer' ? '.employment-ref-card' :
                                  containerSelector === '#technicalSkillsContainer' ? '.skill-row-inline' :
                                  containerSelector === '#computerSkillsContainer' ? '.skill-row-inline' :
                                  containerSelector === '#softSkillsContainer' ? '.skill-row-inline' :
                                  containerSelector === '#prizesAwardsContainer' ? '.prize-entry-card' :
                                  containerSelector === '#conferencesWorkshopsContainer' ? '.cw-entry-card' :
                                  containerSelector === '#publicVoluntaryContainer' ? '.pv-work-card' :
                                  containerSelector === '#phoneNumbersContainer' ? '.phone-row' :
                                  containerSelector === '#additionalLanguagesContainer' ? '.additional-lang-row' :
                                  containerSelector === '#referencesContainer' ? '.reference-row' : null;
                
                if (!cardClass) return;
                
                const targetCount = counts[containerSelector] || 1;
                const currentCount = container.querySelectorAll(cardClass).length;
                for (let i = currentCount; i < targetCount; i++) {
                    btn.click();
                }
            });

            const nameCounts = {};
            form.querySelectorAll('input, select, textarea').forEach(el => {
                if (!el.name || el.type === 'file' || el.type === 'submit' || el.type === 'button' || el.type === 'image' || el.type === 'reset') return;
                const name = el.name;
                if (nameCounts[name] === undefined) {
                    nameCounts[name] = 0;
                } else {
                    nameCounts[name]++;
                }
                const key = name + '@@idx_' + nameCounts[name];

                if (!(key in state)) return;
                if (el.type === 'checkbox' || el.type === 'radio') {
                    el.checked = Array.isArray(state[key]) && state[key].includes(el.value);
                } else {
                    el.value = state[key];
                }
                // Fire change so dependent show/hide logic runs
                el.dispatchEvent(new Event('change', { bubbles: true }));
            });

            // BUG-08 fix: Explicitly re-sync empHaveExperienceBlock visibility after
            // state restoration. The change event fired above may arrive after the
            // initial sync inside setupStepFourEmploymentLogic() already ran with an
            // empty value, leaving the block hidden when status === 'have_experience'.
            const empStatusSel = document.getElementById('empExperienceStatus');
            const empBlock = document.getElementById('empHaveExperienceBlock') || document.getElementById('employmentDetailsBlock');
            const empProfSection = document.getElementById('professionalHistorySummarySection');
            if (empStatusSel && empBlock) {
                const showEmp = empStatusSel.value === 'have_experience';
                empBlock.style.display = showEmp ? '' : 'none';
                if (empProfSection) empProfSection.style.display = showEmp ? '' : 'none';
            }

            updateUI();
        }, 900);
    }

    function clearFormState() {
        try { sessionStorage.removeItem(STATE_KEY); } catch (_) {}
    }

    function updateUI() {
        steps.forEach((step) => {
            const stepNum = parseInt(step.getAttribute('data-step'), 10);
            step.classList.toggle('active', stepNum === currentStep);
        });

        stepperItems.forEach((item, i) => {
            const stepNum = i + 1;
            const fd = dynamicFlow['step_' + stepNum];
            if (fd && !fd.is_visible) return; // already hidden
            item.classList.toggle('active', stepNum === currentStep);
            item.classList.toggle('completed', stepNum < currentStep);
        });

        const visibleCount = _getVisibleStepCount();
        const visibleSteps = [];
        for (let i = 1; i <= TOTAL_STEPS; i++) {
            const fd = dynamicFlow['step_' + i];
            if (!fd || fd.is_visible !== false) visibleSteps.push(i);
        }
        const posInVisible = visibleSteps.indexOf(currentStep);
        const progress = visibleSteps.length > 1 ? (posInVisible / (visibleSteps.length - 1)) * 100 : 100;
        progressBar.style.setProperty('--progress', progress + '%');
        const stepperSteps = document.querySelector('.reg-stepper__steps');
        if (stepperSteps) stepperSteps.style.setProperty('--progress', progress + '%');

        btnPrev.disabled = _prevVisibleStep(currentStep) === null;

        const lastVisible = visibleSteps[visibleSteps.length - 1];
        if (currentStep === lastVisible) {
            btnNext.style.display = 'none';
            btnSubmit.style.display = '';
        } else {
            btnNext.style.display = '';
            btnSubmit.style.display = 'none';
        }

        const lockOverlay = document.getElementById('skillsStep5LockOverlay');
        if (lockOverlay) {
            const onStep5 = currentStep === 5;
            lockOverlay.style.display = skillsStep5Locked && onStep5 ? 'block' : 'none';
        }

        if (currentStep === 10) syncStepTenSocialRows();
        disableNativeValidationAttributes();

        // Update progressbar ARIA attributes
        const bar = document.querySelector('.reg-stepper__bar');
        if (bar) {
            bar.setAttribute('aria-valuenow', posInVisible + 1);
            bar.setAttribute('aria-label', 'تقدم التسجيل: الخطوة ' + (posInVisible + 1) + ' من ' + visibleSteps.length);
        }

        // Announce step change to screen readers and move focus
        const announcer = document.getElementById('a11yAnnouncer');
        const activeStep = document.querySelector('.reg-step.active');
        if (activeStep) {
            const heading = activeStep.querySelector('h2');
            if (heading) {
                if (announcer) {
                    const stepLabel = document.querySelector('.reg-stepper__item.active .reg-stepper__label');
                    announcer.textContent = '';
                    setTimeout(() => {
                        announcer.textContent = 'الخطوة ' + currentStep + ' من ' + TOTAL_STEPS + ': ' + (heading.textContent || '');
                    }, 50);
                }
                heading.setAttribute('tabindex', '-1');
                setTimeout(() => heading.focus(), 100);
            }
        }
    }

    function goNext() {
        if (validateCurrentStep()) {
            const nextStep = _nextVisibleStep(currentStep);
            if (nextStep === null) return;
            const fd = dynamicFlow['step_' + nextStep];
            if (fd && fd.is_locked) {
                showDropdownMessage(fd.locked_reason || 'هذه الخطوة مغلقة مؤقتاً من قِبَل الإدارة. يرجى المحاولة لاحقاً.', true);
                return;
            }
            const leaving = currentStep;
            saveFormState();
            currentStep = nextStep;
            if (leaving === 5) skillsStep5Locked = true;
            syncUrlToStep(currentStep);
            updateUI();
        } else {
            // Focus first invalid field for screen reader users
            const stepEl = document.querySelector('.reg-step.active');
            if (stepEl) {
                const firstErr = stepEl.querySelector('[aria-invalid="true"], .error input, .error select, .error textarea, input.error, select.error, textarea.error');
                if (firstErr) {
                    firstErr.setAttribute('tabindex', firstErr.tabIndex < 0 ? '0' : firstErr.tabIndex);
                    firstErr.focus();
                }
            }
        }
    }

    function goPrev() {
        const prevStep = _prevVisibleStep(currentStep);
        if (prevStep !== null) {
            saveFormState();
            currentStep = prevStep;
            if (currentStep === 5) skillsStep5Locked = false;
            syncUrlToStep(currentStep);
            updateUI();
        }
    }

    // Handle browser back/forward
    window.addEventListener('popstate', (e) => {
        const step = e.state && e.state.step ? e.state.step : 1;
        if (step >= 1 && step <= TOTAL_STEPS) {
            currentStep = step;
            if (currentStep < 5) skillsStep5Locked = false;
            updateUI();
        }
    });

    btnPrev.addEventListener('click', goPrev);
    btnNext.addEventListener('click', goNext);

    let globalCountries = []; // Store for dynamic cards

    const populateSelect = (selectEl, data, defaultText, valueKey = 'id', textKeyAr = 'name_ar', textKeyEn = 'name_en') => {
        if (!selectEl) return;
        const prevValue = selectEl.value;
        selectEl.innerHTML = `<option value="">${defaultText}</option>`;
        data.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item[valueKey];
            opt.textContent = item[textKeyAr] || item[textKeyEn];
            selectEl.appendChild(opt);
        });
        if (prevValue) selectEl.value = prevValue;
    };

    function buildEduCountryOptions(selectEl) {
        if (!selectEl) return;
        const previous = selectEl.value;
        selectEl.innerHTML = '<option value="">اختر الدولة</option>';
        if (globalCountries && globalCountries.length > 0) {
            globalCountries.forEach((c) => {
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = c.name_ar || c.name_en;
                selectEl.appendChild(opt);
            });
        } else {
            const sourceCountrySelect = document.getElementById('countryOfStay');
            const sourceOptions = sourceCountrySelect ? Array.from(sourceCountrySelect.options) : [];
            sourceOptions.forEach((opt) => {
                if (!opt.value) return;
                const nextOpt = document.createElement('option');
                nextOpt.value = opt.value;
                nextOpt.textContent = opt.textContent;
                selectEl.appendChild(nextOpt);
            });
        }
        if (previous) selectEl.value = previous;
    }

    async function loadLookups() {
        try {
            const [
                countries, 
                interests, 
                languages, 
                militaryStatus, 
                identityDocTypes, 
                degreeLevels, 
                grades, 
                ministries, 
                jobTitles, 
                maritalStatus, 
                monthlyIncome
            ] = await Promise.all([
                fetch(API_PREFIX + '/api/lookups/countries').then(res => res.json()),
                fetch(API_PREFIX + '/api/lookups/interests').then(res => res.json()),
                fetch(API_PREFIX + '/api/lookups/languages').then(res => res.json()),
                fetch(API_PREFIX + '/api/lookups/military-status').then(res => res.json()),
                fetch(API_PREFIX + '/api/lookups/identity-doc-types').then(res => res.json()),
                fetch(API_PREFIX + '/api/lookups/degree-levels').then(res => res.json()),
                fetch(API_PREFIX + '/api/lookups/grades').then(res => res.json()),
                fetch(API_PREFIX + '/api/lookups/ministries').then(res => res.json()),
                fetch(API_PREFIX + '/api/lookups/job-titles').then(res => res.json()),
                fetch(API_PREFIX + '/api/lookups/marital-status').then(res => res.json()),
                fetch(API_PREFIX + '/api/lookups/monthly-income').then(res => res.json())
            ]);

            globalCountries = countries;

            populateSelect(document.getElementById('countryOfStay'), countries, 'اختر الدولة');
            document.querySelectorAll('select[name="nationality"], select[name="secondNationality"], select[name="thirdNationality"]').forEach(sel => 
                populateSelect(sel, countries, 'اختر الجنسية')
            );
            document.querySelectorAll('.pv-country').forEach(sel => populateSelect(sel, countries, 'اختر الدولة'));
            document.querySelectorAll('.edu-degree-country').forEach(buildEduCountryOptions);

            const interestsGrid = document.getElementById('interestsGrid');
            if (interestsGrid) {
                interestsGrid.innerHTML = '';
                interests.forEach(interest => {
                    const label = document.createElement('label');
                    label.className = 'interest-item';
                    label.innerHTML = `
                        <input type="checkbox" name="interestCode[]" value="${interest.id}">
                        <span class="interest-item__text">${interest.name_ar || interest.name_en}</span>
                    `;
                    interestsGrid.appendChild(label);
                });
            }

            populateSelect(document.getElementById('nativeLanguage'), languages, 'اختر اللغة');
            // BUG 16 fix: englishProficiency was never populated — use the same languages list
            // since the select expects language-proficiency levels. If a dedicated endpoint
            // exists in the future, swap languages here for that response.
            const engProfSelect = document.getElementById('englishProficiency');
            if (engProfSelect) {
                const proficiencyLevels = [
                    { id: 'beginner',     name_ar: 'مبتدئ (Beginner)' },
                    { id: 'elementary',   name_ar: 'أساسي (Elementary / A2)' },
                    { id: 'intermediate', name_ar: 'متوسط (Intermediate / B1)' },
                    { id: 'upper_int',    name_ar: 'فوق المتوسط (Upper-Intermediate / B2)' },
                    { id: 'advanced',     name_ar: 'متقدم (Advanced / C1)' },
                    { id: 'proficient',   name_ar: 'محترف (Proficient / C2)' },
                    { id: 'native',       name_ar: 'لغة أم (Native)' }
                ];
                populateSelect(engProfSelect, proficiencyLevels, 'اختر المستوى');
            }
            populateSelect(document.getElementById('militaryStatus'), militaryStatus, 'اختر الحالة العسكرية', 'code');

            const idDocGrid = document.querySelector('.identity-doc-grid');
            if (idDocGrid) {
                idDocGrid.innerHTML = '';
                identityDocTypes.forEach(type => {
                    const label = document.createElement('label');
                    label.className = 'identity-doc-option';
                    label.setAttribute('for', `idDocType_${type.id}`);
                    label.innerHTML = `
                        <input id="idDocType_${type.id}" type="checkbox" name="identityDocType" value="${type.code}">
                        <span class="identity-doc-option__content">
                            <span class="identity-doc-option__text">
                                <span class="identity-doc-option__title">${type.name_ar}</span>
                                <span class="identity-doc-option__hint">${type.name_en}</span>
                            </span>
                        </span>
                    `;
                    idDocGrid.appendChild(label);
                });
                const newCheckboxes = idDocGrid.querySelectorAll('input[name="identityDocType"]');
                newCheckboxes.forEach(cb => {
                    cb.addEventListener('change', () => {
                        const selected = Array.from(newCheckboxes).filter(c => c.checked).map(c => c.value);
                        const showNationalId = selected.includes('national_id');
                        const showPassport = selected.includes('passport');
                        const nationalIdGroup = document.getElementById('nationalIdGroup');
                        const passportGroup = document.getElementById('passportNumberGroup');
                        const idScanGroup = document.getElementById('identityDocScanGroup');
                        if (nationalIdGroup) nationalIdGroup.style.display = showNationalId ? '' : 'none';
                        if (passportGroup) passportGroup.style.display = showPassport ? '' : 'none';
                        if (idScanGroup) idScanGroup.style.display = selected.length > 0 ? '' : 'none';
                        newCheckboxes.forEach(c => c.closest('.identity-doc-option')?.classList.toggle('is-selected', c.checked));
                    });
                });
            }

            populateSelect(document.getElementById('eduHighestDegree'), degreeLevels.filter(d => d.type === 'undergraduate'), 'اختر المؤهل', 'code');
            document.querySelectorAll('.edu-pg-degree-type').forEach(sel => 
                populateSelect(sel, degreeLevels.filter(d => d.type === 'postgraduate'), 'اختر', 'code')
            );
            document.querySelectorAll('.edu-grade').forEach(sel => populateSelect(sel, grades, 'اختر التقدير', 'code'));
            document.querySelectorAll('.emp-ministry').forEach(sel => populateSelect(sel, ministries, 'اختر الوزارة'));
            document.querySelectorAll('.emp-job-title').forEach(sel => populateSelect(sel, jobTitles, 'اختر المسمى الوظيفي'));
            populateSelect(document.querySelector('select[name="maritalStatus"]'), maritalStatus, 'اختر الحالة الاجتماعية', 'code');
            populateSelect(document.querySelector('select[name="monthlyAverageIncome"]'), monthlyIncome, 'اختر متوسط الدخل', 'code');

        } catch (err) {
            console.error('Error loading lookups:', err);
            let errMsg = 'خطأ أثناء تحميل البيانات:\n' + err.message;
            if (err.message.includes('fetch') || err.message.includes('NetworkError') || err.message.includes('Failed to fetch')) {
                errMsg += '\n\nملاحظة: يرجى التأكد من تشغيل الخادم الخلفي (Backend Server) وفتح الصفحة عبر الرابط:\nhttp://localhost:8001/registration.html\nوليس كملف محلي (file://) أو منفذ آخر.';
            }
            window.showDropdownMessage(errMsg, true);
            fetch(API_PREFIX + '/api/debug/log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ error: err.message, stack: err.stack })
            }).catch(() => {});
            window.showDropdownMessage('فشل في تحميل بعض قوائم البيانات. يرجى المحاولة لاحقاً.', true);
        }
    }

    async function updateStates() {
        const countrySelect = document.getElementById('countryOfStay');
        const stateSelect = document.getElementById('governmentOrState');
        if (!countrySelect || !stateSelect) return;
        const countryId = countrySelect.value;
        if (!countryId) {
            stateSelect.innerHTML = '<option value="">اختر المحافظة / الولاية</option>';
            return;
        }
        try {
            const states = await fetch(API_PREFIX + `/api/lookups/states/${countryId}`).then(res => res.json());
            stateSelect.innerHTML = '<option value="">اختر المحافظة / الولاية</option>';
            states.forEach((state) => {
                const opt = document.createElement('option');
                opt.value = state.id;
                opt.textContent = state.name_ar || state.name_en; 
                stateSelect.appendChild(opt);
            });
        } catch (err) {
            console.error('Error loading states:', err);
        }
    }

    async function updateUniversitiesForCountry(countryId, targetSelects) {
        if (!countryId) return;
        try {
            const univs = await fetch(API_PREFIX + `/api/lookups/universities/${countryId}`).then(res => res.json());
            const selects = targetSelects || document.querySelectorAll('.edu-institution');
            selects.forEach((eduInst) => {
                const prev = eduInst.value;
                eduInst.innerHTML = '<option value="">اختر من القائمة</option>';
                univs.forEach((u) => {
                    const opt = document.createElement('option');
                    opt.value = u.id;
                    opt.textContent = u.name_ar || u.name_en;
                    opt.setAttribute('data-faculty', '1');
                    eduInst.appendChild(opt);
                });
                const others = [
                    { v: 'institute', t: 'معهد تعليمي' },
                    { v: 'other', t: 'أخرى' }
                ];
                others.forEach((o) => {
                    const opt = document.createElement('option');
                    opt.value = o.v;
                    opt.textContent = o.t;
                    eduInst.appendChild(opt);
                });
                if (prev) eduInst.value = prev;
            });
        } catch (err) {
            console.error('Error loading universities:', err);
        }
    }

    async function updateUniversities() {
        const countrySelect = document.getElementById('countryOfStay');
        const countryId = countrySelect?.value;
        if (!countryId) return;
        await updateUniversitiesForCountry(countryId);
    }

    function setupStepOneDynamicLogic() {
        const countrySelect = document.getElementById('countryOfStay');
        const militaryStatusSelect = document.getElementById('militaryStatus');
        const militaryReasonGroup = document.getElementById('militaryReasonGroup');
        const militaryReasonInput = document.getElementById('militaryReason');
        const nationalityCountSelect = document.getElementById('numberOfNationalities');
        const secondNationalityGroup = document.getElementById('secondNationalityGroup');
        const thirdNationalityGroup = document.getElementById('thirdNationalityGroup');
        const secondNationalitySelect = document.getElementById('secondNationality');
        const thirdNationalitySelect = document.getElementById('thirdNationality');
        const nationalIdGroup = document.getElementById('nationalIdGroup');
        const passportGroup = document.getElementById('passportNumberGroup');
        const idScanGroup = document.getElementById('identityDocScanGroup');
        const identityDocScanInput = document.getElementById('identityDocumentScan');
        const nationalIdInput = document.getElementById('nationalId');
        const passportInput = document.getElementById('passportNumber');
        const identityDocCheckboxes = document.querySelectorAll('input[name="identityDocType"]');

        if (countrySelect) {
            countrySelect.addEventListener('change', () => {
                updateStates();
                updateUniversities();
            });
        }

        if (militaryStatusSelect && militaryReasonGroup && militaryReasonInput) {
            const updateMilitaryReason = () => {
                const showReason = ['exempted', 'postponed', 'currently_serving'].includes(militaryStatusSelect.value);
                militaryReasonGroup.style.display = showReason ? '' : 'none';
                militaryReasonInput.required = showReason;
                if (!showReason) militaryReasonInput.value = '';
            };
            militaryStatusSelect.addEventListener('change', updateMilitaryReason);
            updateMilitaryReason();

            // Gender-based visibility for Military Service
            const genderRadios = document.querySelectorAll('input[name="gender"]');
            const militaryStatusGroup = militaryStatusSelect.closest('.form-group');
            
            const updateMilitaryVisibility = () => {
                const selectedGender = Array.from(genderRadios).find(r => r.checked)?.value;
                const isFemale = selectedGender === 'female';
                
                if (militaryStatusGroup) {
                    militaryStatusGroup.style.display = isFemale ? 'none' : '';
                }
                
                if (isFemale) {
                    militaryStatusSelect.required = false;
                    militaryStatusSelect.value = '';
                    militaryReasonGroup.style.display = 'none';
                    militaryReasonInput.required = false;
                    militaryReasonInput.value = '';
                } else {
                    militaryStatusSelect.required = true;
                }
            };

            genderRadios.forEach(radio => radio.addEventListener('change', updateMilitaryVisibility));
            updateMilitaryVisibility(); // Initial check
        }

        if (nationalityCountSelect && secondNationalityGroup && thirdNationalityGroup) {
            const updateNationalities = () => {
                const count = nationalityCountSelect.value;
                secondNationalityGroup.style.display = ['2', '3'].includes(count) ? '' : 'none';
                thirdNationalityGroup.style.display = count === '3' ? '' : 'none';
                if (secondNationalitySelect) secondNationalitySelect.required = ['2', '3'].includes(count);
                if (thirdNationalitySelect) thirdNationalitySelect.required = count === '3';
                if (count === '1' && secondNationalitySelect) secondNationalitySelect.value = '';
                if (count !== '3' && thirdNationalitySelect) thirdNationalitySelect.value = '';
            };
            nationalityCountSelect.addEventListener('change', updateNationalities);
            updateNationalities();
        }

        if (identityDocCheckboxes.length > 0) {
            const updateIdentityFields = () => {
                const selected = Array.from(identityDocCheckboxes).filter(c => c.checked).map(c => c.value);
                const showNationalId = selected.includes('national_id');
                const showPassport = selected.includes('passport');
                if (nationalIdGroup) nationalIdGroup.style.display = showNationalId ? '' : 'none';
                if (passportGroup) passportGroup.style.display = showPassport ? '' : 'none';
                if (idScanGroup) idScanGroup.style.display = selected.length > 0 ? '' : 'none';
                if (nationalIdInput) nationalIdInput.required = showNationalId;
                if (passportInput) passportInput.required = showPassport;
                identityDocCheckboxes.forEach((cb) => {
                    const option = cb.closest('.identity-doc-option');
                    if (option) option.classList.toggle('is-selected', cb.checked);
                });
            };
            identityDocCheckboxes.forEach(cb => cb.addEventListener('change', updateIdentityFields));
            updateIdentityFields();
        }

        const primaryNationalitySelect = document.querySelector('select[name="nationality"]');
        if (primaryNationalitySelect && secondNationalitySelect && thirdNationalitySelect) {
            const checkDuplicateNationalities = () => {
                const pVal = primaryNationalitySelect.value;
                const sVal = secondNationalitySelect.value;
                const tVal = thirdNationalitySelect.value;
                
                if (sVal && sVal === pVal) {
                    secondNationalitySelect.value = '';
                    window.showDropdownMessage("لا يمكن اختيار نفس الجنسية مرتين.", true);
                }
                if (tVal && (tVal === pVal || tVal === sVal)) {
                    thirdNationalitySelect.value = '';
                    window.showDropdownMessage("لا يمكن اختيار نفس الجنسية مرتين.", true);
                }
            };
            primaryNationalitySelect.addEventListener('change', checkDuplicateNationalities);
            secondNationalitySelect.addEventListener('change', checkDuplicateNationalities);
            thirdNationalitySelect.addEventListener('change', checkDuplicateNationalities);
        }

        const dobInput = document.querySelector('input[name="dob"]');
        const maritalSelect = document.querySelector('select[name="maritalStatus"]');
        if (dobInput && maritalSelect) {
            const checkMaritalStatusAndAge = () => {
                if (!dobInput.value) return;
                const birth = new Date(dobInput.value);
                const today = new Date();
                let age = today.getFullYear() - birth.getFullYear();
                const m = today.getMonth() - birth.getMonth();
                if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
                if (age < 18) {
                    const marriedOption = maritalSelect.querySelector('option[value="married"]');
                    if (marriedOption) {
                        marriedOption.disabled = true;
                        if (maritalSelect.value === 'married') {
                            maritalSelect.value = '';
                            window.showDropdownMessage("تم إلغاء تحديد الحالة الاجتماعية 'متزوج' لأن العمر أقل من 18 عاماً.", true);
                        }
                    }
                } else {
                    const marriedOption = maritalSelect.querySelector('option[value="married"]');
                    if (marriedOption) marriedOption.disabled = false;
                }
            };
            dobInput.addEventListener('change', checkMaritalStatusAndAge);
            dobInput.addEventListener('input', checkMaritalStatusAndAge);
            maritalSelect.addEventListener('change', checkMaritalStatusAndAge);
            // Run initially
            checkMaritalStatusAndAge();
        }

        const whatsappNumber = document.getElementById('whatsappNumber');
        const whatsappSameAsMobile = document.getElementById('whatsappSameAsMobile');
        const mobileNumber1 = document.querySelector('input[name="mobileNumber1"]');
        if (whatsappNumber && whatsappSameAsMobile && mobileNumber1) {
            whatsappSameAsMobile.addEventListener('change', function() {
                if (this.checked) {
                    whatsappNumber.value = mobileNumber1.value;
                    whatsappNumber.dispatchEvent(new Event('input'));
                } else {
                    whatsappNumber.value = '';
                }
            });
            mobileNumber1.addEventListener('input', function() {
                if (whatsappSameAsMobile.checked) {
                    whatsappNumber.value = this.value;
                }
            });
        }

        if (nationalIdInput) {
            nationalIdInput.addEventListener('input', function() {
                const val = this.value.trim();
                if (val.length === 14 && /^\d{14}$/.test(val)) {
                    const genderDigit = parseInt(val.charAt(12), 10);
                    const genderValue = (genderDigit % 2 === 0) ? 'female' : 'male';
                    const genderRadio = document.querySelector(`input[name="gender"][value="${genderValue}"]`);
                    if (genderRadio && !genderRadio.checked) {
                        genderRadio.checked = true;
                        genderRadio.dispatchEvent(new Event('change'));
                        window.showDropdownMessage('تم تحديد النوع تلقائياً بناءً على الرقم القومي.', false);
                    }
                }
            });
        }

        if (identityDocScanInput) {
            identityDocScanInput.addEventListener('change', () => {
                if (identityDocScanInput.files && identityDocScanInput.files.length > MAX_IDENTITY_DOCUMENT_FILES) {
                    identityDocScanInput.value = '';
                    window.showDropdownMessage(`يمكنك رفع ${MAX_IDENTITY_DOCUMENT_FILES} ملفات كحد أقصى لوثيقة الهوية.`, true);
                }
            });
        }

        // AI Extract Button Dummy Handler
        const aiBtn = document.getElementById('aiExtractBtn');
        if (aiBtn) {
            aiBtn.addEventListener('click', () => {
                const status = document.getElementById('aiExtractStatus');
                const fileInput = document.getElementById('identityDocumentScan');
                if (fileInput && fileInput.files.length > 0) {
                    if (status) status.textContent = 'جاري استخراج البيانات بالذكاء الاصطناعي... (قيد التطوير)';
                    setTimeout(() => {
                        if (status) status.textContent = 'تم إتمام المسح بنجاح! سيتم ربط ميزة الاستخراج الآلي قريباً.';
                    }, 2000);
                } else {
                    window.showDropdownMessage('يرجى اختيار ملف الهوية لبدء عملية المسح والتحقق.', true);
                }
            });
        }

        // Load initial lookups
        loadLookups();
    }

    function setupStepTwoDynamicLogic() {
        const countSelect = document.getElementById('emergencyContactsCount');
        const contact2Block = document.getElementById('emergencyContact2Block');
        const name2 = document.getElementById('emergencyName2');
        const phone2 = document.getElementById('emergencyPhone2');
        const address2 = document.getElementById('emergencyAddress2');
        if (!countSelect || !contact2Block) return;

        const updateEmergencyContactVisibility = () => {
            const showContact2 = countSelect.value === '2';
            contact2Block.style.display = showContact2 ? '' : 'none';
            if (name2) {
                name2.required = showContact2;
                if (!showContact2) name2.value = '';
            }
            if (phone2) {
                phone2.required = showContact2;
                if (!showContact2) phone2.value = '';
            }
            if (address2) {
                address2.required = showContact2;
                if (!showContact2) address2.value = '';
            }
        };

        countSelect.addEventListener('change', updateEmergencyContactVisibility);
        updateEmergencyContactVisibility();
    }

    function setupStepThreeEducationalLogic() {
        const degreeSel = document.getElementById('eduHighestDegree');
        const mainBlock = document.getElementById('eduMainFieldsBlock');
        const pgSection = document.getElementById('eduPostgraduateSection');
        const pgHas = document.getElementById('eduHasPostgraduate');
        const pgDetails = document.getElementById('eduPostgraduateDetails');

        const mainEduContainer = document.getElementById('mainEducationContainer');
        const addMainEduBtn = document.getElementById('addMainEduBtn');

        const higherEduContainer = document.getElementById('higherEducationContainer');
        const addHigherEduBtn = document.getElementById('addHigherEduBtn');

        if (!degreeSel || !mainBlock) return;

        const genericFaculties = [
            { v: 'engineering', t: 'كلية الهندسة' },
            { v: 'commerce', t: 'كلية التجارة' },
            { v: 'science', t: 'كلية العلوم' },
            { v: 'medicine', t: 'كلية الطب' },
            { v: 'law', t: 'كلية الحقوق' },
            { v: 'arts', t: 'كلية الآداب' },
            { v: 'education', t: 'كلية التربية' },
            { v: 'computers_it', t: 'كلية الحاسبات والمعلومات' }
        ];

        function fillFacultySelect(selectEl) {
            if (!selectEl) return;
            selectEl.innerHTML = '<option value="">اختر الكلية</option>';
            genericFaculties.forEach((f) => {
                const opt = document.createElement('option');
                opt.value = f.v;
                opt.textContent = f.t;
                selectEl.appendChild(opt);
            });
        }

        function setAnimatedFieldVisibility(groupEl, show) {
            if (!groupEl) return;
            if (show) {
                groupEl.style.display = '';
                requestAnimationFrame(() => {
                    groupEl.classList.add('edu-field-visible', 'edu-active-field');
                });
            } else {
                groupEl.classList.remove('edu-field-visible', 'edu-active-field');
                setTimeout(() => {
                    if (!groupEl.classList.contains('edu-field-visible')) {
                        groupEl.style.display = 'none';
                    }
                }, 180);
            }
        }


        function setSectionDisabled(container, disabled) {
            if (!container) return;
            container.querySelectorAll('input, select, textarea, button').forEach((el) => {
                if (el.id === 'eduHighestDegree') return;
                if (el.classList.contains('remove-main-edu-btn')) return;
                if (el.classList.contains('remove-higher-edu-btn')) return;
                if (el.classList.contains('accordion-header')) return;
                el.disabled = disabled;
            });
        }

        function updateDegreeDependent() {
            const v = degreeSel.value;
            mainBlock.style.display = v ? '' : 'none';
            setSectionDisabled(mainBlock, !v);
            if (!v) return;

            if (mainEduContainer) {
                const mainCards = mainEduContainer.querySelectorAll('.main-education-card');
                mainCards.forEach(card => {
                    const gpaGroup = card.querySelector('.edu-gpa-group');
                    const totalScoreGroup = card.querySelector('.edu-total-score-group');
                    const pctGroup = card.querySelector('.edu-percentage-group');
                    const degreeCountryGroup = card.querySelector('.edu-degree-country-group');
                    const institutionGroup = card.querySelector('.edu-institution-group');
                    const instituteNameGroup = card.querySelector('.edu-institute-name-group');
                    const schoolNameGroup = card.querySelector('.edu-school-name-group');
                    const degreeCountryInput = card.querySelector('.edu-degree-country');
                    const instSel = card.querySelector('.edu-institution');
                    const instituteNameInput = card.querySelector('.edu-institute-name');
                    const schoolNameInput = card.querySelector('.edu-school-name');

                    if (gpaGroup) gpaGroup.style.display = v === 'higher_degree' ? '' : 'none';
                    if (totalScoreGroup) totalScoreGroup.style.display = v === 'intermediate' ? '' : 'none';
                    if (pctGroup) pctGroup.style.display = v === 'above_intermediate' ? '' : 'none';

                    setAnimatedFieldVisibility(degreeCountryGroup, v === 'higher_degree');
                    setAnimatedFieldVisibility(institutionGroup, v === 'higher_degree');
                    setAnimatedFieldVisibility(instituteNameGroup, v === 'above_intermediate');
                    setAnimatedFieldVisibility(schoolNameGroup, v === 'intermediate');

                    if (degreeCountryInput) degreeCountryInput.required = v === 'higher_degree';
                    if (instSel) instSel.required = v === 'higher_degree';
                    if (instituteNameInput) instituteNameInput.required = v === 'above_intermediate';
                    if (schoolNameInput) schoolNameInput.required = v === 'intermediate';

                    if (v !== 'higher_degree') {
                        if (degreeCountryInput) degreeCountryInput.value = '';
                        if (instSel) instSel.selectedIndex = 0;
                    }
                    if (v !== 'above_intermediate' && instituteNameInput) {
                        instituteNameInput.value = '';
                    }
                    if (v !== 'intermediate' && schoolNameInput) {
                        schoolNameInput.value = '';
                    }
                });
            }

            if (pgSection) pgSection.style.display = v === 'higher_degree' ? '' : 'none';
            if (v !== 'higher_degree' && pgHas) {
                pgHas.value = '';
                if (pgDetails) pgDetails.style.display = 'none';
            }
        }

        function refreshMainEduTitles() {
            if (!mainEduContainer) return;
            const degreeOption = degreeSel && degreeSel.selectedOptions ? degreeSel.selectedOptions[0] : null;
            const degreeLabel = degreeOption && degreeOption.value
                ? degreeOption.textContent.split('/')[0].trim()
                : 'مؤهل';
            mainEduContainer.querySelectorAll('.main-education-card').forEach((card, idx) => {
                const titleEl = card.querySelector('.accordion-title');
                const instSel = card.querySelector('.edu-institution');
                const instituteNameInput = card.querySelector('.edu-institute-name');
                const schoolNameInput = card.querySelector('.edu-school-name');
                const collegeSel = card.querySelector('.edu-college-faculty-select');
                const collegeText = card.querySelector('.edu-college-faculty-text');
                if (titleEl) {
                    let title = `${degreeLabel} (Degree #${idx + 1})`;
                    if (instSel && instSel.value) {
                        const opt = instSel.selectedOptions[0];
                        if (opt && opt.value) {
                            title += ` - ${opt.textContent.trim()}`;
                        }
                    }
                    if (collegeSel && collegeSel.value) {
                        const cOpt = collegeSel.selectedOptions[0];
                        if (cOpt && cOpt.value) title += ` - ${cOpt.textContent.trim()}`;
                    } else if (collegeText && collegeText.value.trim()) {
                        title += ` - ${collegeText.value.trim()}`;
                    } else if (instituteNameInput && instituteNameInput.value.trim()) {
                        title += ` - ${instituteNameInput.value.trim()}`;
                    } else if (schoolNameInput && schoolNameInput.value.trim()) {
                        title += ` - ${schoolNameInput.value.trim()}`;
                    }
                    titleEl.textContent = title;
                }
            });
        }

        function bindMainEducationCard(card) {
            updateUniversities(); // default preload for legacy flow
            const instSel = card.querySelector('.edu-institution');
            const degreeCountrySel = card.querySelector('.edu-degree-country');
            const instituteNameInput = card.querySelector('.edu-institute-name');
            const schoolNameInput = card.querySelector('.edu-school-name');
            const collegeSelectWrap = card.querySelector('.edu-college-select-wrap');
            const collegeTextWrap = card.querySelector('.edu-college-text-wrap');
            const collegeSelect = card.querySelector('.edu-college-faculty-select');
            const collegeText = card.querySelector('.edu-college-faculty-text');

            const header = card.querySelector('.accordion-header');

            if (header) {
                // Remove existing listener if any by cloning
                const newHeader = header.cloneNode(true);
                header.replaceWith(newHeader);
                newHeader.addEventListener('click', (e) => {
                    if (e.target.closest('.remove-main-edu-btn')) return;
                    card.classList.toggle('open');
                });
            }

            async function updateInstitutionCollegeMode() {
                if (!instSel) return;
                const val = instSel.value;
                if (!val) {
                    if (collegeSelectWrap) collegeSelectWrap.style.display = 'none';
                    if (collegeTextWrap) collegeTextWrap.style.display = 'none';
                    return;
                }
                
                if (/^\d+$/.test(val)) {
                    try {
                        const colleges = await fetch(API_PREFIX + `/api/lookups/universities/${val}/colleges`).then(res => res.json());
                        if (colleges && colleges.length > 0) {
                            if (collegeSelectWrap) collegeSelectWrap.style.display = '';
                            if (collegeTextWrap) collegeTextWrap.style.display = 'none';
                            if (collegeSelect) {
                                collegeSelect.innerHTML = '<option value="">اختر الكلية</option>';
                                colleges.forEach((c) => {
                                    const opt = document.createElement('option');
                                    opt.value = c.name_en;
                                    opt.textContent = c.name_ar || c.name_en;
                                    collegeSelect.appendChild(opt);
                                });
                            }
                            if (collegeText) collegeText.value = '';
                            refreshMainEduTitles();
                            return;
                        }
                    } catch (err) {
                        console.error('Error fetching colleges:', err);
                    }
                }
                
                if (collegeSelectWrap) collegeSelectWrap.style.display = 'none';
                if (collegeTextWrap) collegeTextWrap.style.display = '';
                if (collegeSelect) collegeSelect.selectedIndex = 0;
                refreshMainEduTitles();
            }

            async function updateUniversitiesByCardCountry() {
                if (!degreeCountrySel || !instSel) return;
                if (!degreeCountrySel.value) {
                    instSel.innerHTML = '<option value="">اختر من القائمة</option>';
                    return;
                }
                await updateUniversitiesForCountry(degreeCountrySel.value, [instSel]);
                updateInstitutionCollegeMode();
            }

            if (instSel) {
                instSel.removeEventListener('change', updateInstitutionCollegeMode);
                instSel.addEventListener('change', updateInstitutionCollegeMode);
            }
            if (degreeCountrySel) {
                buildEduCountryOptions(degreeCountrySel);
                const fallbackCountry = document.getElementById('countryOfStay')?.value;
                if (!degreeCountrySel.value && fallbackCountry) degreeCountrySel.value = fallbackCountry;
                degreeCountrySel.addEventListener('change', updateUniversitiesByCardCountry);
            }
            if (collegeSelect) collegeSelect.addEventListener('change', refreshMainEduTitles);
            if (collegeText) collegeText.addEventListener('input', refreshMainEduTitles);
            if (instituteNameInput) instituteNameInput.addEventListener('input', refreshMainEduTitles);
            if (schoolNameInput) schoolNameInput.addEventListener('input', refreshMainEduTitles);
            updateInstitutionCollegeMode();
            updateUniversitiesByCardCountry();
            updateDegreeDependent();
        }

        function updateRemoveMainEduVisibility() {
            if (!mainEduContainer) return;
            const n = mainEduContainer.querySelectorAll('.main-education-card').length;
            mainEduContainer.querySelectorAll('.remove-main-edu-btn').forEach((b) => {
                b.style.display = n > 1 ? '' : 'none';
            });
        }

        if (mainEduContainer) {
            mainEduContainer.querySelectorAll('.main-education-card').forEach(bindMainEducationCard);

            mainEduContainer.addEventListener('click', (e) => {
                const t = e.target.closest('.remove-main-edu-btn');
                if (!t) return;
                const card = t.closest('.main-education-card');
                if (!card || mainEduContainer.querySelectorAll('.main-education-card').length <= 1) return;
                card.remove();
                updateRemoveMainEduVisibility();
                refreshMainEduTitles();

                // Auto-open last item if nothing is open
                const remaining = mainEduContainer.querySelectorAll('.main-education-card');
                if (remaining.length > 0 && !mainEduContainer.querySelector('.main-education-card.open')) {
                    remaining[remaining.length - 1].classList.add('open');
                }
            });

            addMainEduBtn?.addEventListener('click', () => {
                const first = mainEduContainer.querySelector('.main-education-card');
                if (!first) return;

                // Collapse all existing
                mainEduContainer.querySelectorAll('.main-education-card').forEach(c => {
                    c.classList.remove('open');
                });

                const clone = first.cloneNode(true);
                clone.querySelectorAll('input,select').forEach((el) => {
                    if (el.type === 'checkbox' || el.type === 'radio') el.checked = false;
                    else el.value = '';
                });

                // Expand new
                clone.classList.add('open');

                mainEduContainer.appendChild(clone);
                bindMainEducationCard(clone);
                updateRemoveMainEduVisibility();
                refreshMainEduTitles();

                clone.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
            updateRemoveMainEduVisibility();
            refreshMainEduTitles();
        }

        function updatePostgraduateDetails() {
            if (!pgDetails || !pgHas) return;
            pgDetails.style.display = pgHas.value === 'yes' ? '' : 'none';
        }

        function refreshHigherEduTitles() {
            if (!higherEduContainer) return;
            higherEduContainer.querySelectorAll('.higher-education-card').forEach((card, idx) => {
                const titleEl = card.querySelector('.accordion-title');
                const degreeSel = card.querySelector('.edu-pg-degree-type');
                const issuerInput = card.querySelector('.edu-degree-issuer-entity');
                if (titleEl) {
                    let title = `دراسات عليا #${idx + 1} (Postgraduate #${idx + 1})`;
                    if (degreeSel && degreeSel.value) {
                        const opt = degreeSel.selectedOptions[0];
                        if (opt && opt.value) {
                            title += ` - ${opt.textContent.split('/')[0].trim()}`;
                        }
                    }
                    if (issuerInput && issuerInput.value.trim()) title += ` - ${issuerInput.value.trim()}`;
                    titleEl.textContent = title;
                }
            });
        }

        function bindHigherEducationCard(card) {
            const fundingSel = card.querySelector('.edu-funding');
            const scholarshipGroup = card.querySelector('.edu-scholarship-group');
            const degreeSel = card.querySelector('.edu-pg-degree-type');

            const header = card.querySelector('.accordion-header');

            if (header) {
                const newHeader = header.cloneNode(true);
                header.replaceWith(newHeader);
                newHeader.addEventListener('click', (e) => {
                    if (e.target.closest('.remove-higher-edu-btn')) return;
                    card.classList.toggle('open');
                });
            }

            function updateScholarship() {
                if (!scholarshipGroup || !fundingSel) return;
                scholarshipGroup.style.display = fundingSel.value === 'third_party' ? '' : 'none';
                if (fundingSel.value !== 'third_party') {
                    const inp = card.querySelector('.edu-scholarship-entity');
                    if (inp) inp.value = '';
                }
            }

            if (fundingSel) {
                fundingSel.removeEventListener('change', updateScholarship);
                fundingSel.addEventListener('change', updateScholarship);
            }

            if (degreeSel) {
                degreeSel.removeEventListener('change', refreshHigherEduTitles);
                degreeSel.addEventListener('change', refreshHigherEduTitles);
            }
            const issuerInput = card.querySelector('.edu-degree-issuer-entity');
            if (issuerInput) issuerInput.addEventListener('input', refreshHigherEduTitles);

            updateScholarship();
        }

        function updateRemoveHigherEduVisibility() {
            if (!higherEduContainer) return;
            const n = higherEduContainer.querySelectorAll('.higher-education-card').length;
            higherEduContainer.querySelectorAll('.remove-higher-edu-btn').forEach((b) => {
                b.style.display = n > 1 ? '' : 'none';
            });
        }

        if (higherEduContainer) {
            higherEduContainer.querySelectorAll('.higher-education-card').forEach(bindHigherEducationCard);

            higherEduContainer.addEventListener('click', (e) => {
                const t = e.target.closest('.remove-higher-edu-btn');
                if (!t) return;
                const card = t.closest('.higher-education-card');
                if (!card || higherEduContainer.querySelectorAll('.higher-education-card').length <= 1) return;
                if (!window.confirm('هل تريد حذف هذا الإدخال من الدراسات العليا؟')) return;
                card.remove();
                updateRemoveHigherEduVisibility();
                refreshHigherEduTitles();

                // Auto-open last item if nothing is open
                const remaining = higherEduContainer.querySelectorAll('.higher-education-card');
                if (remaining.length > 0 && !higherEduContainer.querySelector('.higher-education-card.open')) {
                    remaining[remaining.length - 1].classList.add('open');
                }
            });

            addHigherEduBtn?.addEventListener('click', () => {
                const first = higherEduContainer.querySelector('.higher-education-card');
                if (!first) return;

                // Collapse all existing
                higherEduContainer.querySelectorAll('.higher-education-card').forEach(c => {
                    c.classList.remove('open');
                });

                const clone = first.cloneNode(true);
                clone.querySelectorAll('input,select').forEach((el) => {
                    if (el.type === 'checkbox' || el.type === 'radio') el.checked = false;
                    else el.value = '';
                });

                // Expand new
                clone.classList.add('open');

                higherEduContainer.appendChild(clone);
                bindHigherEducationCard(clone);
                updateRemoveHigherEduVisibility();
                refreshHigherEduTitles();

                clone.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
            updateRemoveHigherEduVisibility();
            refreshHigherEduTitles();
        }

        degreeSel.addEventListener('change', updateDegreeDependent);
        degreeSel.addEventListener('change', refreshMainEduTitles);
        if (pgHas) pgHas.addEventListener('change', updatePostgraduateDetails);

        updateDegreeDependent();
        updatePostgraduateDetails();
    }

    function setupStepFourEmploymentLogic() {
        const statusSel = document.getElementById('empExperienceStatus');
        const block = document.getElementById('empHaveExperienceBlock') || document.getElementById('employmentDetailsBlock');
        const professionalSection = document.getElementById('professionalHistorySummarySection');
        const container = document.getElementById('employmentHistoryContainer');
        const addCardBtn = document.getElementById('addEmploymentCardBtn');
        const refContainer = document.getElementById('empReferencesContainer');
        const addRefBtn = document.getElementById('addEmpReferenceBtn');

        if (!statusSel || !block || !container || !refContainer) return;

        const EMP_MINISTRY_SUB = {
            education: [
                { v: 'central', t: 'الإدارة المركزية للوزارة' },
                { v: 'governance', t: 'إدارات المحافظات' },
                { v: 'institutes', t: 'المعاهد التابعة' }
            ],
            health: [
                { v: 'hospitals', t: 'المستشفيات الحكومية' },
                { v: 'primary', t: 'الرعاية الصحية الأولية' }
            ],
            finance: [
                { v: 'tax', t: 'مصلحة الضرائب' },
                { v: 'treasury', t: 'خزانة الدولة' }
            ],
            communications: [
                { v: 'ntra', t: 'الجهات التنظيمية' },
                { v: 'infra', t: 'البنية التحتية' }
            ],
            solidarity: [
                { v: 'social', t: 'تأمينات اجتماعية' },
                { v: 'pension', t: 'معاشات' }
            ],
            other: [{ v: 'other_sub', t: 'جهة أخرى' }]
        };

        const TITLE_SPECIALITY_HINT = {
            admin: 'إدارة عامة',
            engineer: 'هندسة',
            specialist: 'تخصص دقيق حسب المجال',
            manager: 'إدارة',
            consultant: 'استشارات',
            other: ''
        };

        const EMP_WORK_NATURE_BY_TYPE = {
            governmental: [
                { v: 'full_time', t: 'دوام كامل' },
                { v: 'consultant', t: 'استشاري' },
                { v: 'contractual', t: 'تعاقدي' }
            ],
            private: [
                { v: 'contract', t: 'عقد' },
                { v: 'consultant', t: 'استشاري' },
                { v: 'full_time', t: 'دوام كامل' },
                { v: 'part_time', t: 'دوام جزئي' }
            ],
            entrepreneur: [
                { v: 'full_time', t: 'دوام كامل' },
                { v: 'part_time', t: 'دوام جزئي' }
            ],
            freelance: [
                { v: 'full_time', t: 'دوام كامل' },
                { v: 'part_time', t: 'دوام جزئي' },
                { v: 'contract', t: 'عقد' }
            ]
        };

        async function fillMinistrySub(ministrySel, subSel) {
            if (!subSel || !ministrySel) return;
            const m = ministrySel.value;
            subSel.innerHTML = '<option value="">اختر الجهة</option>';
            if (!m) return;
            
            if (/^\d+$/.test(m)) {
                try {
                    const authorities = await fetch(API_PREFIX + `/api/lookups/ministries/${m}/authorities`).then(res => res.json());
                    if (authorities && authorities.length > 0) {
                        authorities.forEach((item) => {
                            const opt = document.createElement('option');
                            opt.value = item.name;
                            opt.textContent = item.name;
                            subSel.appendChild(opt);
                        });
                        return;
                    }
                } catch (err) {
                    console.error('Error fetching ministry authorities:', err);
                }
            }
            
            (EMP_MINISTRY_SUB[m] || []).forEach((item) => {
                const opt = document.createElement('option');
                opt.value = item.v;
                opt.textContent = item.t;
                subSel.appendChild(opt);
            });
        }

        function populateWorkNatureOptions(card) {
            if (!card) return;
            const typeSel = card.querySelector('.emp-job-type');
            const natureSel = card.querySelector('.emp-work-nature');
            const natureWrap = card.querySelector('.emp-work-nature-wrap');
            if (!typeSel || !natureSel) return;

            const prev = natureSel.value;
            const options = EMP_WORK_NATURE_BY_TYPE[typeSel.value] || [];
            natureSel.innerHTML = '<option value="">اختر طبيعة الوظيفة</option>';
            options.forEach((item) => {
                const opt = document.createElement('option');
                opt.value = item.v;
                opt.textContent = item.t;
                natureSel.appendChild(opt);
            });

            const stillValid = prev && options.some((item) => item.v === prev);
            if (stillValid) {
                natureSel.value = prev;
            } else {
                natureSel.value = '';
            }

            if (natureWrap) {
                natureWrap.classList.add('is-updating');
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => natureWrap.classList.remove('is-updating'));
                });
            }
        }

        function updateCardFieldVisibility(card) {
            if (!card) return;
            const jt = card.querySelector('.emp-job-type')?.value || '';
            const gov = card.querySelector('.emp-block-gov');
            const org = card.querySelector('.emp-block-org');
            const free = card.querySelector('.emp-block-free');
            const cur = card.querySelector('.emp-currently-working')?.value || '';
            const endWrap = card.querySelector('.emp-end-date-wrap');

            if (gov) gov.style.display = jt === 'governmental' ? '' : 'none';
            if (org) org.style.display = (jt === 'governmental' || jt === 'private') ? '' : 'none';
            if (free) free.style.display = (jt === 'entrepreneur' || jt === 'freelance') ? '' : 'none';
            if (endWrap) endWrap.style.display = cur === 'no' ? '' : 'none';
        }

        function suggestSpeciality(card) {
            const titleSel = card.querySelector('.emp-job-title');
            const specInp = card.querySelector('.emp-speciality');
            if (!titleSel || !specInp) return;
            const hint = TITLE_SPECIALITY_HINT[titleSel.value];
            if (hint !== undefined && hint) {
                specInp.placeholder = `مقترح: ${hint}`;
                if (!specInp.dataset.touched && !specInp.value.trim()) specInp.value = hint;
            }
        }

        function employmentRowLabel(card, index) {
            const jt = card.querySelector('.emp-job-type')?.value || '';
            const title = card.querySelector('.emp-job-title');
            const seniority = card.querySelector('.emp-seniority');
            const dept = card.querySelector('.emp-department');
            const spec = card.querySelector('.emp-speciality');
            const ministry = card.querySelector('.emp-ministry');

            const parts = [];
            if (jt === 'governmental' && ministry?.selectedOptions[0] && ministry.value) {
                parts.push(ministry.selectedOptions[0].text);
            }
            if (title?.selectedOptions[0] && title.value) parts.push(title.selectedOptions[0].text);
            if (seniority?.selectedOptions[0] && seniority.value) parts.push(seniority.selectedOptions[0].text);
            if (dept?.selectedOptions[0] && dept.value) parts.push(dept.selectedOptions[0].text);
            if (spec && spec.value.trim()) parts.push(spec.value.trim());
            if (jt === 'entrepreneur') parts.push('رائد أعمال');
            if (jt === 'freelance') parts.push('عمل حر');
            if (jt === 'private' && (!title || !title.value)) parts.push('قطاع خاص');
            return parts.filter(Boolean).join(' — ') || `خبرة #${index + 1}`;
        }

        function refreshRefPlaceOptions() {
            const cards = container.querySelectorAll('.emp-history-card');
            const labels = [];
            cards.forEach((card, i) => {
                labels.push({ value: String(i), label: employmentRowLabel(card, i) });
            });
            refContainer.querySelectorAll('.emp-ref-place-select').forEach((sel) => {
                const prev = sel.value;
                sel.innerHTML = '<option value="">اختر من الخبرات المدخلة</option>';
                labels.forEach((L) => {
                    const o = document.createElement('option');
                    o.value = L.value;
                    o.textContent = L.label;
                    sel.appendChild(o);
                });
                if (prev && [...sel.options].some((o) => o.value === prev)) sel.value = prev;
            });
        }

        function updateRemoveCardVisibility() {
            const n = container.querySelectorAll('.emp-history-card').length;
            container.querySelectorAll('.emp-remove-card').forEach((b) => {
                b.style.display = n > 1 ? '' : 'none';
            });
        }

        function updateRemoveRefVisibility() {
            const n = refContainer.querySelectorAll('.employment-ref-card').length;
            refContainer.querySelectorAll('.emp-remove-ref').forEach((b) => {
                b.style.display = n > 1 ? '' : 'none';
            });
        }

        function bindCard(card) {
            const jobType = card.querySelector('.emp-job-type');
            const ministry = card.querySelector('.emp-ministry');
            const cur = card.querySelector('.emp-currently-working');
            const title = card.querySelector('.emp-job-title');
            const spec = card.querySelector('.emp-speciality');

            const onJobOrCur = () => {
                updateCardFieldVisibility(card);
                refreshRefPlaceOptions();
            };

            jobType?.addEventListener('change', () => {
                onJobOrCur();
                populateWorkNatureOptions(card);
                if (ministry) fillMinistrySub(ministry, card.querySelector('.emp-ministry-sub'));
                suggestSpeciality(card);
            });
            ministry?.addEventListener('change', () => {
                fillMinistrySub(ministry, card.querySelector('.emp-ministry-sub'));
                refreshRefPlaceOptions();
            });
            cur?.addEventListener('change', onJobOrCur);
            title?.addEventListener('change', () => {
                suggestSpeciality(card);
                refreshRefPlaceOptions();
            });
            card.querySelector('.emp-seniority')?.addEventListener('change', refreshRefPlaceOptions);
            card.querySelector('.emp-department')?.addEventListener('change', refreshRefPlaceOptions);
            spec?.addEventListener('input', () => {
                spec.dataset.touched = '1';
                refreshRefPlaceOptions();
            });
            spec?.addEventListener('change', refreshRefPlaceOptions);

            const prim = card.querySelector('.emp-industry-primary');
            const sec = card.querySelector('.emp-industry-secondary');
            function dedupeIndustry() {
                if (prim && sec && sec.value && sec.value === prim.value) sec.selectedIndex = 0;
            }
            prim?.addEventListener('change', dedupeIndustry);
            sec?.addEventListener('change', dedupeIndustry);

            updateCardFieldVisibility(card);
            populateWorkNatureOptions(card);
            if (ministry) fillMinistrySub(ministry, card.querySelector('.emp-ministry-sub'));
        }

        container.querySelectorAll('.emp-history-card').forEach(bindCard);

        container.addEventListener('click', (e) => {
            const t = e.target.closest('.emp-remove-card');
            if (!t) return;
            const card = t.closest('.emp-history-card');
            if (!card || container.querySelectorAll('.emp-history-card').length <= 1) return;
            card.remove();
            refreshRefPlaceOptions();
            updateRemoveCardVisibility();
        });

        addCardBtn?.addEventListener('click', () => {
            const first = container.querySelector('.emp-history-card');
            if (!first) return;
            const clone = first.cloneNode(true);
            clone.querySelectorAll('input,select').forEach((el) => {
                if (el.type === 'checkbox' || el.type === 'radio') el.checked = false;
                else el.value = '';
                if (el.classList.contains('emp-speciality')) el.dataset.touched = '';
            });
            const sub = clone.querySelector('.emp-ministry-sub');
            if (sub) sub.innerHTML = '<option value="">اختر الجهة</option>';
            container.appendChild(clone);
            bindCard(clone);
            updateRemoveCardVisibility();
            refreshRefPlaceOptions();
        });

        refContainer.addEventListener('click', (e) => {
            const t = e.target.closest('.emp-remove-ref');
            if (!t) return;
            const row = t.closest('.employment-ref-card');
            if (!row || refContainer.querySelectorAll('.employment-ref-card').length <= 1) return;
            row.remove();
            updateRemoveRefVisibility();
        });

        addRefBtn?.addEventListener('click', () => {
            const firstRow = refContainer.querySelector('.employment-ref-card');
            if (!firstRow) return;
            const clone = firstRow.cloneNode(true);
            clone.querySelectorAll('input,select').forEach((el) => {
                el.value = '';
            });
            refContainer.appendChild(clone);
            updateRemoveRefVisibility();
            refreshRefPlaceOptions();
        });

        statusSel.addEventListener('change', () => {
            const show = statusSel.value === 'have_experience';
            block.style.display = show ? '' : 'none';
            if (professionalSection) professionalSection.style.display = show ? '' : 'none';
            if (show) refreshRefPlaceOptions();
        });

        updateRemoveCardVisibility();
        updateRemoveRefVisibility();
        refreshRefPlaceOptions();
        const showExperience = statusSel.value === 'have_experience';
        block.style.display = showExperience ? '' : 'none';
        if (professionalSection) professionalSection.style.display = showExperience ? '' : 'none';
    }

    // Ensure date picker opens when clicking the wrapper or icon (also for dynamically added rows)
    function openDatePickerFromWrapper(wrap) {
        const input = wrap?.querySelector('input[type="date"]');
        if (!input) return;
        try {
            if (typeof input.showPicker === 'function') {
                input.showPicker();
            } else {
                input.focus();
                input.click();
            }
        } catch (e) {
            console.error("Picker failed", e);
        }
    }
    document.addEventListener('click', (e) => {
        const wrap = e.target.closest('.reg-input-wrap--date');
        if (!wrap) return;
        openDatePickerFromWrapper(wrap);
    });

    // Dynamic phone numbers in contact step
    const phoneContainer = document.getElementById('phoneNumbersContainer');
    const addPhoneBtn = document.getElementById('addPhoneBtn');

    if (phoneContainer && addPhoneBtn) {
        addPhoneBtn.addEventListener('click', function () {
            if (phoneContainer.querySelectorAll('.phone-row').length >= 3) {
                window.showDropdownMessage("تم الوصول للحد الأقصى لأرقام الهواتف (3).", true);
                return;
            }
            const row = document.createElement('div');
            row.className = 'reg-form__row phone-row';
            row.innerHTML = `
                <div class="form-group">
                    <input type="tel" name="phoneNumbers[]" placeholder="أدخل رقم هاتف آخر">
                </div>
            `;
            phoneContainer.appendChild(row);
        });
    }

    // ===== Skills, Languages & Interests (Step 5) - Dynamic Load =====
    let skillsTree = [];
    let languagesList = [];
    let proficiencyMasterList = [];

    function initSkillProficiencyNumericSelects() {
        document.querySelectorAll('.reg-step[data-step="5"] .skill-proficiency').forEach((sel) => {
            if (sel.options.length <= 1) {
                sel.innerHTML = '<option value="">١–١٠</option>';
                for (let i = 1; i <= 10; i++) {
                    const o = document.createElement('option');
                    o.value = String(i);
                    o.textContent = String(i);
                    sel.appendChild(o);
                }
            }
        });
    }

    function populateAdditionalLangSelect(sel) {
        if (!(sel instanceof HTMLSelectElement)) return;
        const nativeVal = document.getElementById('nativeLanguage')?.value || '';
        const prev = sel.value;
        sel.innerHTML = '<option value="">اختر اللغة</option>';
        languagesList.forEach((l) => {
            if (nativeVal && String(l.id) === String(nativeVal)) return;
            const o = document.createElement('option');
            o.value = l.id;
            o.textContent = l.name_ar;
            sel.appendChild(o);
        });
        if (prev && [...sel.options].some((o) => o.value === prev)) sel.value = prev;
    }

    function fillLanguageProficiencySelect(sel) {
        if (!(sel instanceof HTMLSelectElement)) return;
        sel.innerHTML = '<option value="">اختر المستوى</option>';
        proficiencyMasterList.forEach((p) => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.level_ar;
            sel.appendChild(opt);
        });
    }

    function createAdditionalLanguageRow() {
        const wrap = document.createElement('div');
        wrap.className = 'additional-lang-row reg-form__row';
        wrap.innerHTML = `
            <div class="form-group">
                <label>اللغة</label>
                <div class="reg-input-wrap reg-input-wrap--select">
                    <span class="reg-input-icon reg-input-icon--chevron" aria-hidden="true"></span>
                    <select name="additionalLanguageId[]" class="additional-lang-id"></select>
                </div>
            </div>
            <div class="form-group">
                <label>مستوى الإجادة</label>
                <div class="reg-input-wrap reg-input-wrap--select">
                    <span class="reg-input-icon reg-input-icon--chevron" aria-hidden="true"></span>
                    <select name="additionalLanguageProficiency[]" class="additional-lang-prof"></select>
                </div>
            </div>
            <div class="form-group" style="display: flex; align-items: flex-end; max-width: 50px;">
                <button type="button" class="reg-btn reg-btn--danger lang-delete-btn" style="padding: 2px 8px; height: 38px; min-width: 32px; margin-bottom: 2px;" title="حذف">✕</button>
            </div>
        `;
        const langSel = wrap.querySelector('.additional-lang-id');
        const profSel = wrap.querySelector('.additional-lang-prof');
        populateAdditionalLangSelect(langSel);
        fillLanguageProficiencySelect(profSel);

        const delBtn = wrap.querySelector('.lang-delete-btn');
        if (delBtn) {
            delBtn.addEventListener('click', () => wrap.remove());
        }

        return wrap;
    }

    function setupStepFiveLanguagesInterests() {
        initSkillProficiencyNumericSelects();

        const addLangBtn = document.getElementById('addAdditionalLanguageBtn');
        const addLangContainer = document.getElementById('additionalLanguagesContainer');
        addLangBtn?.addEventListener('click', () => {
            if (!addLangContainer) return;
            if (addLangContainer.querySelectorAll('.additional-lang-row').length >= 2) {
                window.showDropdownMessage('يمكن إضافة لغتين إضافيتين كحد أقصى.', true);
                return;
            }
            addLangContainer.appendChild(createAdditionalLanguageRow());
        });

        document.getElementById('nativeLanguage')?.addEventListener('change', () => {
            addLangContainer?.querySelectorAll('.additional-lang-id').forEach((el) => populateAdditionalLangSelect(el));
        });

        const interestsGrid = document.getElementById('interestsGrid');
        interestsGrid?.addEventListener('change', (e) => {
            const t = e.target;
            if (!(t instanceof HTMLInputElement) || t.name !== 'interestCode[]') return;
            const checked = interestsGrid.querySelectorAll('input[name="interestCode[]"]:checked');
            if (checked.length > 5) {
                t.checked = false;
                window.showDropdownMessage('يمكن اختيار 5 اهتمامات كحد أقصى.', true);
            }
        });

        const usesSocial = document.getElementById('usesSocialMedia');
        const socialBlock = document.getElementById('socialMediaPlatformsBlock');
        usesSocial?.addEventListener('change', function () {
            if (!socialBlock) return;
            socialBlock.style.display = this.value === 'yes' ? '' : 'none';
            if (this.value !== 'yes') {
                socialBlock.querySelectorAll('input[type="checkbox"]').forEach((c) => { c.checked = false; });
            }
            syncStepTenSocialRows();
        });
        socialBlock?.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
            cb.addEventListener('change', syncStepTenSocialRows);
        });
    }

    // Fetch skills from DB on load
    async function initSkills() {
        console.log("Initializing skills from API...");
        try {
            const response = await fetch(API_PREFIX + '/api/skills/tree');
            if (response.ok) {
                skillsTree = await response.json();
                console.log("Skills tree loaded:", skillsTree);
                populateSectionSubcategories('technicalSkill', 1);
                populateSectionSubcategories('computerSkill', 2);
                populateSectionSubcategories('softSkill', 3);
            } else {
                console.error('Backend Error:', response.status);
                showSkillsError();
            }

            const langRes = await fetch(API_PREFIX + '/api/skills/languages');
            if (langRes.ok) {
                languagesList = await langRes.json();
            }

            const profRes = await fetch(API_PREFIX + '/api/skills/proficiencies');
            if (profRes.ok) {
                proficiencyMasterList = await profRes.json();
                const englishProfSelect = document.getElementById('englishProficiency');
                if (englishProfSelect) {
                    englishProfSelect.innerHTML = '<option value="">اختر المستوى</option>';
                    proficiencyMasterList.forEach((p) => {
                        const opt = document.createElement('option');
                        opt.value = p.id;
                        opt.textContent = p.level_ar;
                        englishProfSelect.appendChild(opt);
                    });
                }
            }

            initSkillProficiencyNumericSelects();
        } catch (err) {
            console.error('Network Error - Is the backend running at localhost:8001?', err);
            showSkillsError();
        }
    }

    function showSkillsError() {
        // Optional: show a small warning in UI
        const warning = document.createElement('div');
        warning.className = 'reg-skills-warning';
        warning.innerHTML = `<strong>تنبيه (Warning):</strong> تعذر الاتصال بخادم المهارات. يرجى التأكد من تشغيل <code>RUN_USER.bat</code> وفتح الرابط <a href="/registration.html">/registration.html</a>.`;

        const skillsStep = document.querySelector('.reg-step[data-step="5"]');
        if (skillsStep) {
            skillsStep.prepend(warning);
        }
    }

    function populateSectionSubcategories(namePrefix, categoryId) {
        const categoryData = skillsTree.find(c => c.id === categoryId);
        if (!categoryData) return;

        const selects = document.querySelectorAll(`select[name="${namePrefix}Category[]"]`);
        selects.forEach(sel => {
            // Backup current value
            const currentVal = sel.value;
            sel.innerHTML = `<option value="">${sel.options[0].text}</option>`;
            categoryData.subcategories.forEach(sub => {
                const opt = document.createElement('option');
                opt.value = sub.id;
                opt.textContent = sub.name_ar; // Bilingual: name_ar
                sel.appendChild(opt);
            });
            sel.value = currentVal;
        });
    }

    function createSkillRow(namePrefix, categoryPlaceholder, skillPlaceholder, categoryId) {
        let profOpts = '<option value="">١–١٠</option>';
        for (let i = 1; i <= 10; i++) profOpts += `<option value="${i}">${i}</option>`;

        const row = document.createElement('div');
        row.className = 'skill-row-inline';
        row.innerHTML = `
            <select class="skill-category" name="${namePrefix}Category[]">
                <option value="">${categoryPlaceholder}</option>
            </select>
            <select class="skill-name" name="${namePrefix}Name[]">
                <option value="">${skillPlaceholder}</option>
            </select>
            <select class="skill-proficiency" name="${namePrefix}Proficiency[]" aria-label="الإتقان 1-10">${profOpts}</select>
            <button type="button" class="reg-btn reg-btn--danger skill-delete-btn" style="padding: 2px 8px; margin-right: 5px; height: 38px; min-width: 32px;" title="حذف">✕</button>
        `;

        const delBtn = row.querySelector('.skill-delete-btn');
        if (delBtn) {
            delBtn.addEventListener('click', () => row.remove());
        }

        if (skillsTree.length > 0) {
            const sel = row.querySelector('.skill-category');
            const categoryData = skillsTree.find(c => c.id === categoryId);
            if (categoryData) {
                categoryData.subcategories.forEach(sub => {
                    const opt = document.createElement('option');
                    opt.value = sub.id;
                    opt.textContent = sub.name_ar;
                    sel.appendChild(opt);
                });
            }
        }
        return row;
    }

    function bindSkillsContainer(container, sectionCategoryId) {
        if (!container) return;

        container.addEventListener('change', function (event) {
            const target = event.target;
            if (target instanceof HTMLSelectElement && target.classList.contains('skill-category')) {
                const subcategoryId = parseInt(target.value);
                const row = target.closest('.skill-row-inline');
                if (!row) return;
                const skillSelect = row.querySelector('.skill-name');
                if (!(skillSelect instanceof HTMLSelectElement)) return;

                // Clear current options
                skillSelect.innerHTML = '<option value="">اختر المهارة</option>';

                // Find skills in tree
                const categoryData = skillsTree.find(c => c.id === sectionCategoryId);
                if (categoryData) {
                    const subcatData = categoryData.subcategories.find(s => s.id === subcategoryId);
                    if (subcatData) {
                        subcatData.skills.forEach(skill => {
                            const opt = document.createElement('option');
                            opt.value = skill.id;
                            opt.textContent = skill.name_ar;
                            skillSelect.appendChild(opt);
                        });
                    }
                }
            }
        });
    }

    // Call init
    initSkills();

    bindSkillsContainer(document.getElementById('technicalSkillsContainer'), 1);
    bindSkillsContainer(document.getElementById('computerSkillsContainer'), 2);
    bindSkillsContainer(document.getElementById('softSkillsContainer'), 3);

    const technicalSkillsContainer = document.getElementById('technicalSkillsContainer');
    const addTechnicalSkillBtn = document.getElementById('addTechnicalSkillBtn');
    const computerSkillsContainer = document.getElementById('computerSkillsContainer');
    const addComputerSkillBtn = document.getElementById('addComputerSkillBtn');
    const softSkillsContainer = document.getElementById('softSkillsContainer');
    const addSoftSkillBtn = document.getElementById('addSoftSkillBtn');

    if (addTechnicalSkillBtn && technicalSkillsContainer) {
        addTechnicalSkillBtn.addEventListener('click', function () {
            if (technicalSkillsContainer.querySelectorAll('.skill-row-inline').length >= 20) { window.showDropdownMessage("الحد الأقصى 20 مهارة تقنية.", true); return; }
            technicalSkillsContainer.appendChild(createSkillRow('technicalSkill', 'اختر الفئة', 'اختر المهارة', 1));
        });
    }

    if (addComputerSkillBtn && computerSkillsContainer) {
        addComputerSkillBtn.addEventListener('click', function () {
            if (computerSkillsContainer.querySelectorAll('.skill-row-inline').length >= 20) { window.showDropdownMessage("الحد الأقصى 20 مهارة حاسوبية.", true); return; }
            computerSkillsContainer.appendChild(createSkillRow('computerSkill', 'اختر الفئة', 'اختر المهارة', 2));
        });
    }

    if (addSoftSkillBtn && softSkillsContainer) {
        addSoftSkillBtn.addEventListener('click', function () {
            if (softSkillsContainer.querySelectorAll('.skill-row-inline').length >= 20) { window.showDropdownMessage("الحد الأقصى 20 مهارة شخصية.", true); return; }
            softSkillsContainer.appendChild(createSkillRow('softSkill', 'Skill Domain / فئة المهارة', 'Specific Competency / المهارة', 3));
        });
    }

    setupStepFiveLanguagesInterests();

    function setupStepSixPrizesConferencesLogic() {
        const hasPrizes = document.getElementById('hasPrizesAwards');
        const prizesBlock = document.getElementById('prizesAwardsBlock');
        const prizesContainer = document.getElementById('prizesAwardsContainer');
        const addPrizeBtn = document.getElementById('addPrizeEntryBtn');

        const hasCw = document.getElementById('hasConferencesWorkshops');
        const cwBlock = document.getElementById('conferencesWorkshopsBlock');
        const cwContainer = document.getElementById('conferencesWorkshopsContainer');
        const addCwBtn = document.getElementById('addConferenceWorkshopBtn');

        function updatePrizesVisibility() {
            if (!prizesBlock) return;
            prizesBlock.style.display = hasPrizes && hasPrizes.value === 'yes' ? '' : 'none';
        }

        function updateCwVisibility() {
            if (!cwBlock) return;
            cwBlock.style.display = hasCw && hasCw.value === 'yes' ? '' : 'none';
        }

        function updatePrizeRemoveButtons() {
            if (!prizesContainer) return;
            const n = prizesContainer.querySelectorAll('.prize-entry-card').length;
            prizesContainer.querySelectorAll('.prize-remove-btn').forEach((b) => {
                b.style.display = n > 1 ? '' : 'none';
            });
        }

        function updateCwRemoveButtons() {
            if (!cwContainer) return;
            const n = cwContainer.querySelectorAll('.cw-entry-card').length;
            cwContainer.querySelectorAll('.cw-remove-btn').forEach((b) => {
                b.style.display = n > 1 ? '' : 'none';
            });
        }

        hasPrizes?.addEventListener('change', updatePrizesVisibility);
        hasCw?.addEventListener('change', updateCwVisibility);

        prizesContainer?.addEventListener('click', (e) => {
            const t = e.target.closest('.prize-remove-btn');
            if (!t || !prizesContainer) return;
            const card = t.closest('.prize-entry-card');
            if (!card || prizesContainer.querySelectorAll('.prize-entry-card').length <= 1) return;
            card.remove();
            updatePrizeRemoveButtons();
        });

        addPrizeBtn?.addEventListener('click', () => {
            const first = prizesContainer?.querySelector('.prize-entry-card');
            if (!first || !prizesContainer) return;
            const clone = first.cloneNode(true);
            clone.querySelectorAll('input,select').forEach((el) => {
                if (el.type === 'file') el.value = '';
                else el.value = '';
            });
            prizesContainer.appendChild(clone);
            updatePrizeRemoveButtons();
        });

        cwContainer?.addEventListener('click', (e) => {
            const t = e.target.closest('.cw-remove-btn');
            if (!t || !cwContainer) return;
            const card = t.closest('.cw-entry-card');
            if (!card || cwContainer.querySelectorAll('.cw-entry-card').length <= 1) return;
            card.remove();
            updateCwRemoveButtons();
        });

        addCwBtn?.addEventListener('click', () => {
            const first = cwContainer?.querySelector('.cw-entry-card');
            if (!first || !cwContainer) return;
            const clone = first.cloneNode(true);
            clone.querySelectorAll('input,select').forEach((el) => {
                el.value = '';
            });
            cwContainer.appendChild(clone);
            updateCwRemoveButtons();
        });

        updatePrizesVisibility();
        updateCwVisibility();
        updatePrizeRemoveButtons();
        updateCwRemoveButtons();
    }

    function setupStepSevenPublicPoliticalLegalLogic() {
        async function fillPvStateSelect(countrySel, stateSel) {
            if (!stateSel) return;
            const countryId = countrySel && countrySel.value;
            const prev = stateSel.value;
            stateSel.innerHTML = '<option value="">اختر المحافظة / الولاية</option>';
            
            if (!countryId) return;

            try {
                const states = await fetch(API_PREFIX + `/api/lookups/states/${countryId}`).then(res => res.json());
                states.forEach((state) => {
                    const opt = document.createElement('option');
                    opt.value = state.id;
                    opt.textContent = state.name_ar || state.name_en;
                    stateSel.appendChild(opt);
                });
                if (prev) stateSel.value = prev;
            } catch (err) {
                console.error('Error fetching PV states:', err);
            }
        }

        function bindPvCard(card) {
            const country = card.querySelector('.pv-country');
            const state = card.querySelector('.pv-state');
            const still = card.querySelector('.pv-still-member');
            const leaveWrap = card.querySelector('.pv-leave-wrap');
            const leaveDate = card.querySelector('.pv-leave-date');

            const onStill = () => {
                const hide = still && still.checked;
                if (leaveWrap) leaveWrap.style.display = hide ? 'none' : '';
                if (hide && leaveDate) leaveDate.value = '';
            };

            still?.addEventListener('change', onStill);
            
            // Listen for country change on this specific card
            country?.addEventListener('change', () => fillPvStateSelect(country, state));
            
            fillPvStateSelect(country, state);
            onStill();
        }

        const hasPv = document.getElementById('hasPublicVoluntaryWork');
        const pvBlock = document.getElementById('publicVoluntaryBlock');
        const pvContainer = document.getElementById('publicVoluntaryContainer');
        const addPvBtn = document.getElementById('addPublicVoluntaryBtn');

        hasPv?.addEventListener('change', () => {
            if (pvBlock) pvBlock.style.display = hasPv.value === 'yes' ? '' : 'none';
        });
        if (pvBlock) pvBlock.style.display = hasPv && hasPv.value === 'yes' ? '' : 'none';

        pvContainer?.querySelectorAll('.pv-work-card').forEach(bindPvCard);

        pvContainer?.addEventListener('click', (e) => {
            const t = e.target.closest('.pv-remove-btn');
            if (!t || !pvContainer) return;
            const card = t.closest('.pv-work-card');
            if (!card || pvContainer.querySelectorAll('.pv-work-card').length <= 1) return;
            card.remove();
            updatePvRemoveButtons();
        });

        function updatePvRemoveButtons() {
            if (!pvContainer) return;
            const n = pvContainer.querySelectorAll('.pv-work-card').length;
            pvContainer.querySelectorAll('.pv-remove-btn').forEach((b) => {
                b.style.display = n > 1 ? '' : 'none';
            });
        }

        addPvBtn?.addEventListener('click', () => {
            const first = pvContainer?.querySelector('.pv-work-card');
            if (!first || !pvContainer) return;
            const clone = first.cloneNode(true);
            clone.querySelectorAll('input,select').forEach((el) => {
                if (el.type === 'checkbox') el.checked = false;
                else el.value = '';
            });

            // Ensure country list is there
            const country = clone.querySelector('.pv-country');
            if (country) {
                country.innerHTML = '<option value="">اختر الدولة</option>';
                globalCountries.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.id;
                    opt.textContent = c.name_ar || c.name_en;
                    country.appendChild(opt);
                });
            }

            const st = clone.querySelector('.pv-state');
            if (st) st.innerHTML = '<option value="">اختر المحافظة / الولاية</option>';
            pvContainer.appendChild(clone);
            bindPvCard(clone);
            updatePvRemoveButtons();
        });

        updatePvRemoveButtons();

        const hasPol = document.getElementById('hasPoliticalParticipation');
        const polBlock = document.getElementById('politicalWorkBlock');
        hasPol?.addEventListener('change', () => {
            if (polBlock) polBlock.style.display = hasPol.value === 'yes' ? '' : 'none';
        });
        if (polBlock) polBlock.style.display = hasPol && hasPol.value === 'yes' ? '' : 'none';

        const hasCand = document.getElementById('hasPoliticalCandidacy');
        const candBlock = document.getElementById('politicalCandidacyBlock');
        hasCand?.addEventListener('change', () => {
            if (candBlock) candBlock.style.display = hasCand.value === 'yes' ? '' : 'none';
        });
        if (candBlock) candBlock.style.display = hasCand && hasCand.value === 'yes' ? '' : 'none';

        const hasLeg = document.getElementById('hasPriorCriminalConvictions');
        const legBlock = document.getElementById('legalStatusBlock');
        const section7CriminalInput = document.getElementById('sectionSevenCriminalRecordCertificate');
        
        function syncSectionEightCriminalRecord() {
            const step8CriminalGroup = document.getElementById('step8CriminalRecordGroup');
            const step8CriminalInput = document.getElementById('criminalRecord');
            const step8PrefillHint = document.getElementById('step8CriminalRecordPrefillHint');
            if (!step8CriminalGroup || !step8CriminalInput) return;

            const hasPriorConv = (hasLeg?.value || '').trim();
            const hasSection7Certificate = !!(section7CriminalInput?.files && section7CriminalInput.files.length > 0);

            // User answered "no": always show Step 8 criminal record field.
            if (hasPriorConv === 'no') {
                step8CriminalGroup.style.display = '';
                step8CriminalInput.required = true;
                if (step8PrefillHint) step8PrefillHint.style.display = 'none';
                return;
            }

            // User answered "yes" and already uploaded in Step 7: hide duplicate Step 8 field.
            if (hasPriorConv === 'yes' && hasSection7Certificate) {
                step8CriminalGroup.style.display = 'none';
                step8CriminalInput.required = false;
                step8CriminalInput.value = '';
                if (step8PrefillHint) step8PrefillHint.style.display = 'none';
                if (step8CriminalInput.parentElement) step8CriminalInput.parentElement.classList.remove('error');
                return;
            }

            // Fallback states: keep Step 8 field visible unless Step 7 file exists.
            step8CriminalGroup.style.display = '';
            step8CriminalInput.required = true;
            if (step8PrefillHint) step8PrefillHint.style.display = 'none';
        }

        hasLeg?.addEventListener('change', () => {
            if (legBlock) legBlock.style.display = hasLeg.value === 'yes' ? '' : 'none';
            syncSectionEightCriminalRecord();
        });
        section7CriminalInput?.addEventListener('change', syncSectionEightCriminalRecord);
        if (legBlock) legBlock.style.display = hasLeg && hasLeg.value === 'yes' ? '' : 'none';
        syncSectionEightCriminalRecord();
    }

    function collectPublicVoluntaryWorkFromDom() {
        const cards = document.querySelectorAll('#publicVoluntaryContainer .pv-work-card');
        const arr = [];
        cards.forEach((card) => {
            const foundation = (card.querySelector('input[name="pvFoundationName[]"]')?.value || '').trim();
            const country = card.querySelector('.pv-country')?.value || '';
            if (!foundation && !country) return;
            const still = !!card.querySelector('.pv-still-member')?.checked;
            arr.push({
                foundationOrCharityName: foundation || null,
                position: card.querySelector('.pv-position')?.value || null,
                joinDate: card.querySelector('.pv-join-date')?.value || null,
                stillMember: still,
                leaveDate: still ? null : (card.querySelector('.pv-leave-date')?.value || null),
                scopeOfWork: (card.querySelector('input[name="pvScope[]"]')?.value || '').trim() || null,
                workField: card.querySelector('select[name="pvWorkField[]"]')?.value || null,
                country: country || null,
                stateOrGovernorate: card.querySelector('.pv-state')?.value || null
            });
        });
        return arr;
    }

    // ===== Academic Data (Step 8) =====
    const testScoresContainer = document.getElementById('testScoresContainer');
    const addTestScoreBtn = document.getElementById('addTestScoreBtn');
    const academicHistoryContainer = document.getElementById('academicHistoryContainer');
    const addAcademicHistoryBtn = document.getElementById('addAcademicHistoryBtn');

    if (addTestScoreBtn && testScoresContainer) {
        testScoresContainer.addEventListener('click', (e) => {
            const removeBtn = e.target.closest('.remove-test-row-btn');
            if (!removeBtn) return;
            const card = removeBtn.closest('.test-score-card');
            if (!card) return;
            card.remove();
            updateTestScoreTitles();
        });

        function updateTestScoreTitles() {
            const cards = testScoresContainer.querySelectorAll('.test-score-card');
            cards.forEach((card, idx) => {
                const titleEl = card.querySelector('.acc-title');
                if (titleEl) {
                    titleEl.textContent = `اختبار #${idx + 1} (Test #${idx + 1})`;
                }
            });
        }

        addTestScoreBtn.addEventListener('click', function () {
            const count = testScoresContainer.querySelectorAll('.test-score-card').length;
            if (count >= 5) { window.showDropdownMessage("الحد الأقصى 5 اختبارات معيارية.", true); return; }

            const card = document.createElement('div');
            card.className = 'test-score-card acc-item open mb-3';
            card.innerHTML = `
                <div class="acc-header accordion-header">
                    <span class="acc-title accordion-title">اختبار #${count + 1} (Test #${count + 1})</span>
                    <button type="button" class="acc-delete-btn remove-test-row-btn" aria-label="حذف الاختبار" title="حذف الاختبار">
                        <span class="acc-delete-btn__icon">&#10005;</span>
                    </button>
                    <svg class="acc-chevron accordion-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M6 9l6 6 6-6"/>
                    </svg>
                </div>
                <div class="acc-body accordion-body">
                    <div class="reg-form__row">
                        <div class="form-group">
                            <label>اسم الاختبار (Test Name)</label>
                            <input type="text" name="standardizedTestName[]" placeholder="مثال: GMAT / GRE / CFA / IELTS" class="test-name">
                        </div>
                        <div class="form-group">
                            <label>درجة الاختبار (Test Score)</label>
                            <input type="text" name="standardizedTestScore[]" placeholder="مثال: 700" class="test-score">
                        </div>
                    </div>
                    <div class="reg-form__row">
                        <div class="form-group">
                            <label>جهة الإصدار (Issuing Authority)</label>
                            <input type="text" name="standardizedTestAuthority[]" placeholder="اسم الجهة المانحة" class="test-authority">
                        </div>
                        <div class="form-group">
                            <label>تاريخ الحصول (Date Obtained)</label>
                            <div class="reg-input-wrap reg-input-wrap--date">
                                <span class="reg-input-icon reg-input-icon--calendar" aria-hidden="true"></span>
                                <input type="date" name="standardizedTestDate[]" class="standardized-test-date">
                            </div>
                        </div>
                    </div>
                    <div class="reg-form__row">
                        <div class="form-group">
                            <label>Attach Document (اختياري)</label>
                            <input type="file" name="standardizedTestDocument[]" accept=".pdf,.jpg,.jpeg,.png" class="test-document">
                        </div>
                        <div class="form-group">
                            <label>رابط التحقق من الشهادة (اجباري عند ملء هذا القسم)</label>
                            <input type="url" name="standardizedTestUrl[]" placeholder="https://..." class="test-url">
                        </div>
                    </div>
                    <div class="acc-actions">
                        <button type="button" class="reg-btn reg-btn--danger remove-test-row-btn">
                            <span class="reg-btn__icon">&#10005;</span> حذف (Remove)
                        </button>
                    </div>
                </div>
            `;

            testScoresContainer.appendChild(card);

            // Add accordion header click handler
            const header = card.querySelector('.accordion-header');
            if (header) {
                header.addEventListener('click', (e) => {
                    if (e.target.closest('.remove-test-row-btn')) return;
                    card.classList.toggle('open');
                });
            }
        });

        // Initialize accordion headers for existing test score cards
        testScoresContainer.querySelectorAll('.test-score-card .accordion-header').forEach((header) => {
            header.addEventListener('click', (e) => {
                if (e.target.closest('.remove-test-row-btn')) return;
                const card = header.closest('.test-score-card');
                if (card) card.classList.toggle('open');
            });
        });
    }

    if (addAcademicHistoryBtn && academicHistoryContainer) {
        addAcademicHistoryBtn.addEventListener('click', function () {
            if (academicHistoryContainer.querySelectorAll('.academic-history-card').length >= 5) { window.showDropdownMessage("تم الوصول للحد الأقصى (5) سجلات أكاديمية.", true); return; }
            const card = document.createElement('div');
            card.className = 'academic-history-card';
            card.innerHTML = `
                <div class="reg-form__row">
                    <div class="form-group">
                        <label>اسم المؤسسة التعليمية (Institution Name)</label>
                        <input type="text" name="institutionName[]" placeholder="أدخل اسم الجامعة أو المؤسسة">
                    </div>
                </div>
                <div class="reg-form__row">
                    <div class="form-group">
                        <label>المعدل / مقياس الدرجات (GPA / Grade Scale)</label>
                        <input type="text" name="gpaGradeScale[]" placeholder="مثال: 3.8 / 4.0 أو تقدير عام">
                    </div>
                    <div class="form-group">
                        <label>التخصص / المجال (Major / Specialization)</label>
                        <input type="text" name="majorSpecialization[]" placeholder="أدخل التخصص">
                    </div>
                </div>
                <div class="reg-form__row">
                    <div class="form-group">
                        <label class="reg-checkbox">
                            <input type="checkbox" name="deansListHonors[]">
                            <span>قائمة الشرف / مرتبة الشرف (Dean's List / Honors)</span>
                        </label>
                    </div>
                    <div class="form-group">
                        <label>أعلى درجة علمية تم الحصول عليها (Highest Degree Attained)</label>
                        <select name="highestDegreeAttained[]">
                            <option value="">اختر الدرجة</option>
                            <option value="diploma">دبلوم</option>
                            <option value="bachelor">بكالوريوس</option>
                            <option value="master">ماجستير</option>
                            <option value="phd">دكتوراه</option>
                            <option value="other">أخرى</option>
                        </select>
                    </div>
                </div>
                <div class="reg-form__row">
                    <div class="form-group">
                        <label>سنة التخرج (Graduation Year)</label>
                        <input type="text" name="graduationYear[]" placeholder="YYYY">
                    </div>
                    <div class="form-group">
                        <label>رتبة / تصنيف الجامعة (University Prestige / Ranking)</label>
                        <input type="text" name="universityRanking[]" placeholder="أدخل التصنيف أو السمعة الأكاديمية">
                    </div>
                </div>
            `;
            academicHistoryContainer.appendChild(card);
        });
    }

    // ===== Professional Data (Step 9) =====
    const professionalHistoryContainer = document.getElementById('professionalHistoryContainer');
    const addProfessionalHistoryBtn = document.getElementById('addProfessionalHistoryBtn');

    if (addProfessionalHistoryBtn && professionalHistoryContainer) {
        addProfessionalHistoryBtn.addEventListener('click', function () {
            if (professionalHistoryContainer.querySelectorAll('.professional-history-card').length >= 10) { window.showDropdownMessage("تم الوصول للحد الأقصى (10) سجلات مهنية.", true); return; }
            const card = document.createElement('div');
            card.className = 'professional-history-card';
            card.innerHTML = `
                <div class="reg-form__row">
                    <div class="form-group">
                        <label>المنظمة / جهة العمل والقطاع (Organization &amp; Industry)</label>
                        <input type="text" name="organizationIndustry[]" placeholder="اسم الجهة والقطاع">
                    </div>
                </div>
                <div class="reg-form__row">
                    <div class="form-group">
                        <label>تاريخ البدء (Start Date)</label>
                        <input type="date" name="startDate[]">
                    </div>
                    <div class="form-group">
                        <label>تاريخ الانتهاء (End Date)</label>
                        <input type="date" name="endDate[]">
                    </div>
                </div>
                <div class="form-group">
                    <label>المسؤوليات الرئيسية (Key Responsibilities)</label>
                    <textarea name="keyResponsibilities[]" rows="3" placeholder="أبرز المسؤوليات والمهام في هذه الوظيفة"></textarea>
                </div>
                <div class="form-group">
                    <label>سبب ترك العمل (Reason for Leaving)</label>
                    <select name="reasonForLeaving[]">
                        <option value="">اختر السبب</option>
                        <option value="career_growth">نمو مهني / فرصة أفضل</option>
                        <option value="relocation">انتقال / تغيير مكان الإقامة</option>
                        <option value="contract_end">انتهاء التعاقد</option>
                        <option value="personal_reasons">أسباب شخصية</option>
                        <option value="organizational_changes">تغييرات تنظيمية</option>
                        <option value="other">أخرى</option>
                    </select>
                </div>
            `;
            professionalHistoryContainer.appendChild(card);
        });
    }

    // ===== Impact & Awards (Step 7) =====
    const awardsContainer = document.getElementById('awardsContainer');
    const addAwardBtn = document.getElementById('addAwardBtn');
    const extracurricularContainer = document.getElementById('extracurricularContainer');
    const addExtracurricularBtn = document.getElementById('addExtracurricularBtn');

    if (addAwardBtn && awardsContainer) {
        addAwardBtn.addEventListener('click', function () {
            if (awardsContainer.querySelectorAll('.academic-history-card').length >= 10) { window.showDropdownMessage("تم الوصول للحد الأقصى (10) جوائز.", true); return; }
            const card = document.createElement('div');
            card.className = 'academic-history-card';
            card.innerHTML = `
                <div class="reg-form__row">
                    <div class="form-group">
                        <label>عنوان الجائزة / التكريم (Award / Recognition Title)</label>
                        <input type="text" name="awardTitle[]" placeholder="مثال: جائزة الموظف المتميز على مستوى الشركة" class="optional-input">
                    </div>
                </div>
                <div class="reg-form__row">
                    <div class="form-group">
                        <label>الجهة المانحة (Issuing Body)</label>
                        <input type="text" name="issuingBody[]" placeholder="اسم الجهة أو المؤسسة المانحة" class="optional-input">
                    </div>
                </div>
                <div class="form-group">
                    <label>الإنجاز الرئيسي (حتى 100 كلمة) (Key Achievement)</label>
                    <textarea name="keyAchievement[]" rows="3" placeholder="وصف مختصر للإنجاز الذي تم تكريمه من أجله" class="optional-input"></textarea>
                </div>
            `;
            awardsContainer.appendChild(card);
        });
    }

    if (addExtracurricularBtn && extracurricularContainer) {
        addExtracurricularBtn.addEventListener('click', function () {
            if (extracurricularContainer.querySelectorAll('.extracurricular-row').length >= 10) { window.showDropdownMessage("الحد الأقصى 10 أنشطة إضافية.", true); return; }
            const row = document.createElement('div');
            row.className = 'reg-form__row extracurricular-row';
            row.innerHTML = `
                <div class="form-group">
                    <label>الدور (Role)</label>
                    <input type="text" name="extracurricularRole[]" placeholder="مثال: عضو مجلس إدارة، قائد فريق، ..." class="optional-input">
                </div>
                <div class="form-group">
                    <label>مدة المشروع (Project Duration)</label>
                    <input type="text" name="extracurricularDuration[]" placeholder="مثال: من 2022 إلى 2023" class="optional-input">
                </div>
            `;
            extracurricularContainer.appendChild(row);
        });
    }

    // ===== Documents & References (Section 8 wizard step) =====
    const referencesContainer = document.getElementById('referencesContainer');
    const addReferenceBtn = document.getElementById('addReferenceBtn');

    if (addReferenceBtn && referencesContainer) {
        addReferenceBtn.addEventListener('click', function () {
            if (referencesContainer.querySelectorAll('.reference-row').length >= 5) { window.showDropdownMessage("تم الوصول للحد الأقصى (5) مراجع.", true); return; }
            const row = document.createElement('div');
            row.className = 'reg-form__row reference-row';
            row.innerHTML = `
                <div class="form-group">
                    <label>الاسم (Name)</label>
                    <input type="text" name="referenceName[]" placeholder="اسم المرجع">
                </div>
                <div class="form-group">
                    <label>العلاقة / المسمى الوظيفي (Relationship / Title)</label>
                    <input type="text" name="referenceRelationship[]" placeholder="مثال: مدير مباشر، أستاذ جامعي">
                </div>
                <div class="form-group">
                    <label>معلومات الاتصال (Contact Information)</label>
                    <input type="text" name="referenceContact[]" placeholder="بريد إلكتروني أو رقم هاتف">
                </div>
            `;
            referencesContainer.appendChild(row);
        });
    }

    function collectEmploymentHistoryFromDom() {
        const cards = document.querySelectorAll('#employmentHistoryContainer .emp-history-card');
        const arr = [];
        cards.forEach((card) => {
            const jobType = card.querySelector('.emp-job-type')?.value;
            if (!jobType) return;
            const p = card.querySelector('.emp-industry-primary')?.value;
            const s = card.querySelector('.emp-industry-secondary')?.value;
            const industries = [];
            if (p) industries.push(p);
            if (s && s !== p) industries.push(s);
            arr.push({
                jobType,
                ministry: card.querySelector('.emp-ministry')?.value || null,
                ministrySub: card.querySelector('.emp-ministry-sub')?.value || null,
                joiningDate: card.querySelector('.emp-joining-date')?.value || null,
                currentlyWorking: card.querySelector('.emp-currently-working')?.value || null,
                endDate: card.querySelector('.emp-end-date')?.value || null,
                workNature: card.querySelector('.emp-work-nature')?.value || null,
                jobTitle: card.querySelector('.emp-job-title')?.value || null,
                seniority: card.querySelector('.emp-seniority')?.value || null,
                department: card.querySelector('.emp-department')?.value || null,
                speciality: (card.querySelector('.emp-speciality')?.value || '').trim() || null,
                jobDescription: (card.querySelector('[name="empJobDescription"]')?.value || '').trim() || null,
                companyAddress: (card.querySelector('[name="empCompanyAddress"]')?.value || '').trim() || null,
                industries: industries.length ? industries : null
            });
        });
        return arr;
    }

    // Helper to upload a file and return its path
    async function uploadFile(file, folder = 'general', inputElement = null, allowedMimeTypes = null) {
        if (!file) return null;

        const defaultTypes = ['image/jpeg', 'image/png', 'application/pdf'];
        const allowedTypes = Array.isArray(allowedMimeTypes) && allowedMimeTypes.length
            ? allowedMimeTypes
            : defaultTypes;
        if (!allowedTypes.includes(file.type)) {
            window.showDropdownMessage(
                allowedTypes.some((t) => t === 'application/pdf' || t.includes('msword') || t.includes('wordprocessingml'))
                    ? 'صيغة الملف غير مدعومة. يُسمح بـ PDF أو DOC أو DOCX لهذا المرفق.'
                    : 'الفورمات غير مدعوم. يرجى التأكد من رفع ملفات بصيغة PDF, JPG, أو PNG فقط.',
                true
            );
            if (inputElement && inputElement.parentElement) inputElement.parentElement.classList.add('error');
            return null;
        }

        if (file.size > 10 * 1024 * 1024) { // 10MB Limit
            window.showDropdownMessage('حجم الملف كبير جداً. الحد الأقصى لحجم الملف هو 10 ميجابايت لجميع المرفقات.', true);
            if (inputElement && inputElement.parentElement) inputElement.parentElement.classList.add('error');
            return null;
        }

        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await fetch(API_PREFIX + `/api/trainee/upload?folder=${folder}`, {
                method: 'POST',
                body: formData
            });
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                const reason = errData.detail || `خطأ ${response.status}`;
                window.showDropdownMessage(`فشل رفع الملف: ${reason}. يرجى المحاولة مرة أخرى.`, true);
                if (inputElement && inputElement.parentElement) inputElement.parentElement.classList.add('error');
                return null;
            }
            // Clear any previous error if upload succeeds
            if (inputElement && inputElement.parentElement) {
                const prevErr = inputElement.parentElement.querySelector('.upload-error-msg');
                if (prevErr) prevErr.remove();
            }
            const data = await response.json();
            return data.file_path;
        } catch (err) {
            console.error('Upload error:', err);
            window.showDropdownMessage('تعذر رفع الملف بسبب مشكلة في الاتصال بالخادم. تأكد من اتصالك للمحاولة مجدداً.', true);
            if (inputElement && inputElement.parentElement) inputElement.parentElement.classList.add('error');
            return null;
        }
    }

    function collectCognitionResultsFromDom(fd) {
        const answers = {};
        for (let i = 1; i <= 9; i++) {
            const qName = `cog${i}`;
            const selectedVal = fd.get(qName); // 'a', 'b', 'c', or 'd'
            if (!selectedVal) { answers[qName] = null; continue; }
            // Read the full answer text from the matching radio label's <span>
            const radio = document.querySelector(`input[name="${qName}"][value="${selectedVal}"]`);
            const labelSpan = radio ? radio.parentElement.querySelector('span') : null;
            const answerText = labelSpan ? labelSpan.textContent.trim() : selectedVal;
            // Format: { a: "Full answer text" } — key validated by backend
            answers[qName] = { [selectedVal]: answerText };
        }
        return { score: 0, answers };
    }

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        // Disable submit button during fetch
        if (btnSubmit) {
            btnSubmit.disabled = true;
            btnSubmit.innerHTML = '<span class="reg-btn__icon reg-btn__icon--check">⏳</span><span>جاري الإرسال...</span>';
        }
        // Persist form state so data survives any page reload
        saveFormState();

        const fd = new FormData(form);

        // --- 1. Handle File Uploads first ---
        const pickFileList = (name) =>
            fd.getAll(name).filter((file) => file && typeof file.size === 'number' && file.size > 0);
        const pickFirstFile = (name) => pickFileList(name)[0] || null;

        const docFiles = {
            cvResume: pickFirstFile('cvResume'),
            orgChartFiles: pickFileList('organizationalChart'),
            idScanFiles: pickFileList('idScan'),
            criminalRecord: pickFirstFile('criminalRecord'),
            employerNocFiles: pickFileList('employerNoc'),
            essay: pickFirstFile('scholarshipEssayFile')
        };

        // Upload documents and get paths
        const cvPath = await uploadFile(docFiles.cvResume, 'cvs');
        const orgPaths = [];
        for (const file of docFiles.orgChartFiles) {
            const path = await uploadFile(file, 'org_charts');
            if (path) orgPaths.push(path);
        }
        const orgPath = orgPaths[0] || null;

        const idPaths = [];
        for (const file of docFiles.idScanFiles) {
            const path = await uploadFile(file, 'ids');
            if (path) idPaths.push(path);
        }
        const idPath = idPaths[0] || null;

        const crimPath = await uploadFile(docFiles.criminalRecord, 'certificates');
        const nocPaths = [];
        for (const file of docFiles.employerNocFiles) {
            const path = await uploadFile(file, 'nocs');
            if (path) nocPaths.push(path);
        }
        const nocPath = nocPaths[0] || null;
        const essayPath = await uploadFile(docFiles.essay, 'essays');

        const gradCertEl = document.getElementById('graduationCertificateScan');
        const gradCertFile = fd.get('graduationCertificateScan');
        const gradCertPath = gradCertFile && gradCertFile.size > 0
            ? await uploadFile(gradCertFile, 'graduation_certs', gradCertEl)
            : null;

        const step1IdScanEl = document.getElementById('identityDocumentScan');
        const step1IdScanFiles = pickFileList('identityDocumentScan').slice(0, MAX_IDENTITY_DOCUMENT_FILES);
        const identityDocumentScanPaths = [];
        for (const file of step1IdScanFiles) {
            const path = await uploadFile(file, 'ids', step1IdScanEl);
            if (path) identityDocumentScanPaths.push(path);
        }
        const identityDocumentScanPath = identityDocumentScanPaths[0] || null;

        const empStatus = (fd.get('empExperienceStatus') || '').trim();
        const empCvEl = document.getElementById('employmentSectionCv');
        const empCvFile = fd.get('employmentSectionCv');
        let employmentSectionCvPath = null;
        if (empStatus === 'have_experience' && empCvFile && empCvFile.size > 0) {
            employmentSectionCvPath = await uploadFile(empCvFile, 'cvs', empCvEl, [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]);
        }

        const employmentHistory = empStatus === 'have_experience' ? collectEmploymentHistoryFromDom() : [];
        const employmentReferences = [];
        if (empStatus === 'have_experience') {
            const refNames = fd.getAll('empRefName[]');
            const refPhones = fd.getAll('empRefPhone[]');
            const refEmails = fd.getAll('empRefEmail[]');
            const refPlaces = fd.getAll('empRefPlaceIndex[]');
            for (let i = 0; i < refNames.length; i++) {
                if ((refNames[i] || '').trim()) {
                    const pi = refPlaces[i];
                    employmentReferences.push({
                        name: (refNames[i] || '').trim(),
                        phone: (refPhones[i] || '').trim(),
                        email: (refEmails[i] || '').trim(),
                        employmentHistoryIndex: pi !== undefined && pi !== null && String(pi).trim() !== ''
                            ? parseInt(String(pi), 10)
                            : null
                    });
                }
            }
        }

        const hasPrizesAwards = (fd.get('hasPrizesAwards') || '').trim();
        const prizeNames = fd.getAll('prizeName[]');
        const prizeDates = fd.getAll('prizeDateAchieved[]');
        const prizeCats = fd.getAll('prizeCategory[]');
        const prizeBodies = fd.getAll('prizeIssuingBody[]');
        const prizeCertFiles = fd.getAll('prizeCertificate[]');

        const prizesAwardsEntries = [];
        if (hasPrizesAwards === 'yes') {
            const rowCount = Math.max(
                prizeNames.length,
                prizeDates.length,
                prizeCats.length,
                prizeBodies.length,
                prizeCertFiles.length
            );
            for (let i = 0; i < rowCount; i++) {
                const file = prizeCertFiles[i];
                let certPath = null;
                if (file && file.size > 0) {
                    certPath = await uploadFile(file, 'prize_certificates');
                }
                const nm = (prizeNames[i] || '').trim();
                const bd = (prizeBodies[i] || '').trim();
                if (!nm && !prizeDates[i] && !prizeCats[i] && !bd && !certPath) continue;
                prizesAwardsEntries.push({
                    prizeName: nm || null,
                    dateAchieved: prizeDates[i] || null,
                    category: prizeCats[i] || null,
                    issuingBody: bd || null,
                    certificateScan: certPath
                });
            }
        }

        const hasConferencesWorkshops = (fd.get('hasConferencesWorkshops') || '').trim();
        const cwTypes = fd.getAll('cwActivityType[]');
        const cwEvents = fd.getAll('cwEventName[]');
        const cwOrgs = fd.getAll('cwOrganizingEntity[]');
        const cwStarts = fd.getAll('cwStartDate[]');
        const cwEnds = fd.getAll('cwEndDate[]');
        const cwParts = fd.getAll('cwParticipationLevel[]');
        const conferencesWorkshopsEntries = [];
        if (hasConferencesWorkshops === 'yes') {
            const rowCount = Math.max(
                cwTypes.length,
                cwEvents.length,
                cwOrgs.length,
                cwStarts.length,
                cwEnds.length,
                cwParts.length
            );
            for (let i = 0; i < rowCount; i++) {
                const en = (cwEvents[i] || '').trim();
                const org = (cwOrgs[i] || '').trim();
                if (!en && !cwTypes[i] && !org && !cwStarts[i] && !cwEnds[i] && !cwParts[i]) continue;
                conferencesWorkshopsEntries.push({
                    activityType: cwTypes[i] || null,
                    eventName: en || null,
                    organizingEntity: org || null,
                    startDate: cwStarts[i] || null,
                    endDate: cwEnds[i] || null,
                    participationLevel: cwParts[i] || null
                });
            }
        }

        const hasPvWork = (fd.get('hasPublicVoluntaryWork') || '').trim();
        const publicVoluntaryWorkEntries = hasPvWork === 'yes' ? collectPublicVoluntaryWorkFromDom() : [];

        const standardizedTestNames = fd.getAll('standardizedTestName[]');
        const standardizedTestScores = fd.getAll('standardizedTestScore[]');
        const standardizedTestAuthorities = fd.getAll('standardizedTestAuthority[]');
        const standardizedTestDates = fd.getAll('standardizedTestDate[]');
        const standardizedTestDocs = fd.getAll('standardizedTestDocument[]');
        const standardizedTestUrls = fd.getAll('standardizedTestUrl[]');
        const standardizedTestsEntries = [];
        const standardizedRows = Math.max(
            standardizedTestNames.length,
            standardizedTestScores.length,
            standardizedTestAuthorities.length,
            standardizedTestDates.length,
            standardizedTestDocs.length,
            standardizedTestUrls.length
        );
        for (let i = 0; i < standardizedRows; i++) {
            const name = (standardizedTestNames[i] || '').trim();
            const score = (standardizedTestScores[i] || '').trim();
            const authority = (standardizedTestAuthorities[i] || '').trim();
            const obtainedDate = standardizedTestDates[i] || null;
            const docFile = standardizedTestDocs[i];
            const verificationUrl = (standardizedTestUrls[i] || '').trim();
            let documentPath = null;
            if (docFile && docFile.size > 0) {
                documentPath = await uploadFile(docFile, 'standardized_tests');
            }
            if (!name && !score && !authority && !obtainedDate && !documentPath && !verificationUrl) continue;
            standardizedTestsEntries.push({
                testName: name || null,
                testScore: score || null,
                issuingAuthority: authority || null,
                dateObtained: obtainedDate,
                document: documentPath,
                verificationUrl: verificationUrl || null
            });
        }

        const hasPolPart = (fd.get('hasPoliticalParticipation') || '').trim();
        const hasPolCand = (fd.get('hasPoliticalCandidacy') || '').trim();
        const hasPriorConv = (fd.get('hasPriorCriminalConvictions') || '').trim();

        let sectionSevenCriminalRecordCertificate = null;
        if (hasPriorConv === 'yes') {
            const certEl = document.getElementById('sectionSevenCriminalRecordCertificate');
            const certFile = fd.get('sectionSevenCriminalRecordCertificate');
            if (certFile && certFile.size > 0) {
                sectionSevenCriminalRecordCertificate = await uploadFile(certFile, 'legal_certificates', certEl);
            }
        }

        // Handle multiple letters of recommendation
        const lorFiles = fd.getAll('lettersOfRecommendation');
        const lorPaths = [];
        for (const file of lorFiles) {
            if (file && file.size > 0) {
                const path = await uploadFile(file, 'recommendations');
                if (path) lorPaths.push(path);
            }
        }

        // BUG-04 fix: when the user has prior convictions the authoritative criminal
        // record document is the one uploaded in Step 7 (sectionSevenCriminalRecordCertificate).
        // Step 8's `criminalRecord` input is hidden+cleared by syncSectionEightCriminalRecord(),
        // but input.value = '' has no effect on <input type="file"> so it may still carry a
        // stale selection.  Prefer the Step 7 cert for the 'yes' path; fall back to Step 8
        // only when Step 7 cert is absent.  For the 'no' path, Step 8 is the primary source.
        const finalCriminalRecordPath = hasPriorConv === 'yes'
            ? (sectionSevenCriminalRecordCertificate || crimPath || null)
            : (crimPath || sectionSevenCriminalRecordCertificate || null);

        const identityPhotosPaths = {};
        const pFront = fd.get('photoFront');
        if (pFront && pFront.size > 0) identityPhotosPaths.front = await uploadFile(pFront, 'photos', document.getElementById('photoFront'));

        // --- 2. Construct Payload ---

        const getSkillArray = (prefix) => {
            const values = [];
            const names = fd.getAll(prefix + 'Name[]');
            const cats = fd.getAll(prefix + 'Category[]');
            const profs = fd.getAll(prefix + 'Proficiency[]');
            for (let i = 0; i < names.length; i++) {
                if (names[i]) values.push({ category: cats[i], name: names[i], proficiency: profs[i] || null });
            }
            return values;
        };

        const additionalLangIds = fd.getAll('additionalLanguageId[]');
        const additionalLangProfs = fd.getAll('additionalLanguageProficiency[]');
        const additionalLanguages = [];
        for (let i = 0; i < additionalLangIds.length; i++) {
            if (additionalLangIds[i]) {
                additionalLanguages.push({
                    languageId: additionalLangIds[i],
                    proficiencyId: additionalLangProfs[i] || null
                });
            }
        }

        const usesSm = (fd.get('usesSocialMedia') || '').trim();
        let socialMediaPlatforms = null;
        if (usesSm === 'yes') {
            socialMediaPlatforms = {
                facebook: fd.get('socialPlatformFacebook') === '1',
                instagram: fd.get('socialPlatformInstagram') === '1',
                x: fd.get('socialPlatformX') === '1',
                linkedin: fd.get('socialPlatformLinkedIn') === '1',
                tiktok: fd.get('socialPlatformTikTok') === '1'
            };
        }

        const buildSocialProfileUrlsPayload = () => {
            const yes = usesSm === 'yes';
            const pick = (inputName, platformName) => {
                if (!yes) return null;
                const cb = document.querySelector(`input[name="${platformName}"]`);
                if (!cb || !cb.checked) return null;
                const v = (fd.get(inputName) || '').trim();
                return v || null;
            };
            return {
                facebook: pick('socialProfileFacebookUrl', 'socialPlatformFacebook'),
                instagram: pick('socialProfileInstagramUrl', 'socialPlatformInstagram'),
                x: pick('socialProfileXUrl', 'socialPlatformX'),
                linkedin: pick('socialProfileLinkedInUrl', 'socialPlatformLinkedIn'),
                tiktok: pick('socialProfileTikTokUrl', 'socialPlatformTikTok')
            };
        };

        // Construct the full registration payload
        const collegeFacultyVal = fd.get('eduCollegeFacultySelect') || fd.get('eduCollegeFacultyText') || '';

        const phoneFromMobile = [];
        const m1 = (fd.get('mobileNumber1') || '').trim();
        const m2 = (fd.get('mobileNumber2') || '').trim();
        const wa = (fd.get('whatsappNumber') || '').trim();
        if (m1) phoneFromMobile.push(m1);
        // Include whatsapp as a required secondary phone if different from mobileNumber1
        if (wa && wa !== m1) phoneFromMobile.push(wa);
        if (m2 && m2 !== m1 && m2 !== wa) phoneFromMobile.push(m2);
        const legacyPhones = fd.getAll('phoneNumbers[]').map((p) => (p || '').trim()).filter(Boolean);
        const phoneNumbers = phoneFromMobile.length ? phoneFromMobile : legacyPhones;

        const addrLine = (fd.get('address') || fd.get('currentAddress') || '').trim();
        const cityLine = (fd.get('city') || '').trim();
        const govLine = (fd.get('governmentOrState') || '').trim();
        const countryLine = (fd.get('countryOfStay') || '').trim();
        const composedAddress = [addrLine, cityLine, govLine, countryLine].filter(Boolean).join(' — ');

        const payload = {
            fullName: fd.get('fullName'),
            fullNameEn: (fd.get('fullNameEn') || '').trim() || (fd.get('fullName') || '').trim(),
            dob: fd.get('dob'),
            nationalId: (fd.get('nationalId') || '').trim(),
            gender: fd.get('gender'),
            militaryStatus: fd.get('militaryStatus'),
            militaryReason: fd.get('militaryReason'),
            maritalStatus: fd.get('maritalStatus'),
            email: fd.get('primaryEmail'),
            secondaryEmail: fd.get('secondaryEmail') || null,
            phoneNumbers,
            emergencyName: (fd.get('emergencyName1') || fd.get('emergencyName') || '').trim(),
            emergencyPhone: (fd.get('emergencyPhone1') || fd.get('emergencyPhone') || '').trim(),
            currentAddress: composedAddress || addrLine,
            permanentAddress: (fd.get('permanentAddress') || '').trim() || composedAddress || addrLine,
            educationalBackground: {
                highestDegree: fd.get('eduHighestDegree') || null,
                institution: fd.get('eduInstitution') || null,
                collegeFaculty: collegeFacultyVal || null,
                speciality: fd.get('eduSpeciality') || null,
                gpa: fd.get('eduGpa') || null,
                totalScore: fd.get('eduTotalScore') || null,
                percentage: fd.get('eduPercentage') || null,
                graduationDate: fd.get('eduGraduationDate') || null,
                graduationCertificateScan: gradCertPath,
                hasPostgraduate: fd.get('eduHasPostgraduate') || null,
                postgraduateDegreeType: fd.get('eduPostgraduateDegreeType') || null,
                degreeIssuerEntity: fd.get('eduDegreeIssuerEntity') || null,
                mainSpecialityPostgraduate: fd.get('eduMainSpecialityPg') || null,
                secondarySpecialityPostgraduate: fd.get('eduSecondarySpecialityPg') || null,
                pgStartDate: fd.get('eduPgStartDate') || null,
                pgEndDate: fd.get('eduPgEndDate') || null,
                funding: fd.get('eduFunding') || null,
                recommendingEntity: fd.get('eduRecommendingEntity') || null,
                scholarshipEntity: fd.get('eduScholarshipEntity') || null
            },
            standardizedTestsEntries,
            technicalSkills: getSkillArray('technicalSkill'),
            softSkills: getSkillArray('softSkill'),
            computerSkills: getSkillArray('computerSkill'),
            nativeLanguage: fd.get('nativeLanguage') || null,
            englishProficiency: fd.get('englishProficiency') || null,
            additionalLanguages,
            nationality: fd.get('nationality') || '',
            countryOfStay: fd.get('countryOfStay') || '',
            governmentOrState: fd.get('governmentOrState') || '',
            city: fd.get('city') || '',
            monthlyAverageIncome: fd.get('monthlyAverageIncome') || '',
            numberOfNationalities: parseInt(fd.get('numberOfNationalities') || '1', 10),
            identityDocType: fd.getAll('identityDocType').join(',') || null,
            otherSkillsFreeText: (fd.get('otherSkillsFreeText') || '').trim() || null,
            interests: fd.getAll('interestCode[]'),
            interestsDescription: (fd.get('interestsDescription') || '').trim() || null,
            usesSocialMedia: usesSm || null,
            socialMediaPlatforms,
            socialMediaProfileUrls: buildSocialProfileUrlsPayload(),
            dataAccuracyTermsConfirmed: fd.get('dataAccuracyTermsConfirmed') === '1',
            academicHistory: [],
            professionalHistory: [],
            portfolioUrl: fd.get('portfolioUrl') || '',
            learningObjectives: fd.get('primaryLearningObjective') || '',
            references: [],
            dietaryRestrictions: fd.get('dietaryRestrictions') || 'None',
            accessibilityRequirements: fd.get('accessibilityRequirements') || 'None',
            photoFront: identityPhotosPaths.front || null,
            quizResults: collectCognitionResultsFromDom(fd),
            role: window.registrationRole || "trainee",


            // Document Paths
            cvResume: cvPath,
            organizationalChart: orgPath,
            organizationalChartFiles: orgPaths,
            lettersOfRecommendation: lorPaths,
            idScan: idPath,
            idScanFiles: idPaths,
            identityDocumentScan: identityDocumentScanPath,
            identityDocumentScanFiles: identityDocumentScanPaths,
            employmentSectionCv: employmentSectionCvPath,
            employmentHistory,
            employmentReferences,
            hasPrizesAwards: hasPrizesAwards || null,
            prizesAwardsEntries,
            hasConferencesWorkshops: hasConferencesWorkshops || null,
            conferencesWorkshopsEntries,
            hasPublicVoluntaryWork: hasPvWork || null,
            publicVoluntaryWorkEntries,
            hasPoliticalParticipation: hasPolPart || null,
            politicalPartyName: (fd.get('politicalPartyName') || '').trim() || null,
            politicalRole: (fd.get('politicalRole') || '').trim() || null,
            politicalWorkDetails: (fd.get('politicalWorkDetails') || '').trim() || null,
            hasPoliticalCandidacy: hasPolCand || null,
            candidacyPositionName: (fd.get('candidacyPositionName') || '').trim() || null,
            candidacyResult: fd.get('candidacyResult') || null,
            candidacyExperienceDescription: (fd.get('candidacyExperienceDescription') || '').trim() || null,
            hasPriorCriminalConvictions: hasPriorConv || null,
            priorConvictionDescription: (fd.get('priorConvictionDescription') || '').trim() || null,
            sectionSevenCriminalRecordCertificate,
            criminalRecord: finalCriminalRecordPath,
            employerNoc: nocPath,
            employerNocFiles: nocPaths,
            scholarshipEssayFile: essayPath,
            identityPhotos: identityPhotosPaths
        };

        // Map Academic History
        // 1. Collect Main Qualifications from DOM
        const mainEduCards = document.querySelectorAll('#mainEducationContainer .main-education-card');
        mainEduCards.forEach(card => {
            const instSel = card.querySelector('.edu-institution');
            if (!instSel) return;
            
            let institution = '';
            const instVal = instSel.value;
            if (instVal === 'institute') {
                institution = card.querySelector('.edu-institute-name')?.value || 'معهد تعليمي';
            } else if (instVal === 'other') {
                institution = card.querySelector('.edu-school-name')?.value || 'أخرى';
            } else {
                const opt = instSel.selectedOptions[0];
                institution = opt ? opt.textContent.trim() : '';
            }
            
            const collegeSel = card.querySelector('.edu-college-faculty-select');
            const collegeText = card.querySelector('.edu-college-faculty-text');
            let college = '';
            if (collegeSel && collegeSel.style.display !== 'none' && collegeSel.value) {
                const opt = collegeSel.selectedOptions[0];
                college = opt ? opt.textContent.trim() : '';
            } else if (collegeText && collegeText.value) {
                college = collegeText.value.trim();
            }
            
            if (college) {
                institution = `${institution} - ${college}`;
            }
            
            const speciality = card.querySelector('.edu-speciality')?.value || '';
            const degreeLevelSel = document.getElementById('eduHighestDegree');
            const degreeLevelText = degreeLevelSel && degreeLevelSel.selectedOptions[0] ? degreeLevelSel.selectedOptions[0].textContent.trim() : '';
            const gpa = card.querySelector('.edu-gpa')?.value || card.querySelector('.edu-percentage')?.value || card.querySelector('.edu-total-score')?.value || '';
            const gradDate = card.querySelector('.edu-graduation-date')?.value || '';
            const gradYear = gradDate ? gradDate.split('-')[0] : '';
            
            if (institution) {
                payload.academicHistory.push({
                    institution: institution,
                    major: speciality || null,
                    degree: degreeLevelText || null,
                    gpa: gpa || null,
                    gradYear: gradYear || null,
                    ranking: null
                });
            }
        });

        // 2. Collect Postgraduate Qualifications from DOM
        const hasPgSel = document.getElementById('eduHasPostgraduate');
        if (hasPgSel && hasPgSel.value === 'yes') {
            const pgCards = document.querySelectorAll('#higherEducationContainer .higher-education-card');
            pgCards.forEach(card => {
                const issuer = card.querySelector('.edu-degree-issuer-entity')?.value || '';
                const degreeTypeSel = card.querySelector('.edu-pg-degree-type');
                const degreeText = degreeTypeSel && degreeTypeSel.selectedOptions[0] ? degreeTypeSel.selectedOptions[0].textContent.trim() : '';
                const major = card.querySelector('.edu-main-speciality-pg')?.value || '';
                const endDate = card.querySelector('.edu-pg-end-date')?.value || '';
                const gradYear = endDate ? endDate.split('-')[0] : '';
                
                if (issuer) {
                    payload.academicHistory.push({
                        institution: issuer,
                        major: major || null,
                        degree: degreeText || null,
                        gpa: null,
                        gradYear: gradYear || null,
                        ranking: null
                    });
                }
            });
        }

        // 3. Collect Additional Academic History
        const instNames = fd.getAll('institutionName[]');
        const gpas = fd.getAll('gpaGradeScale[]');
        const majors = fd.getAll('majorSpecialization[]');
        const degrees = fd.getAll('highestDegreeAttained[]');
        const gradYears = fd.getAll('graduationYear[]');
        const rankings = fd.getAll('universityRanking[]');

        for (let i = 0; i < instNames.length; i++) {
            if (instNames[i]) {
                payload.academicHistory.push({
                    institution: instNames[i],
                    gpa: gpas[i] || null,
                    major: majors[i] || null,
                    degree: degrees[i] || null,
                    gradYear: gradYears[i] || null,
                    ranking: rankings[i] || null
                });
            }
        }

        // Map Professional History
        // 1. Collect Step 4 Employment Details from DOM
        if (empStatus === 'have_experience') {
            const empCards = document.querySelectorAll('#employmentHistoryContainer .emp-history-card');
            empCards.forEach(card => {
                const jobType = card.querySelector('.emp-job-type')?.value;
                if (!jobType) return;
                
                let org = '';
                if (jobType === 'governmental') {
                    const minSel = card.querySelector('.emp-ministry');
                    const minOpt = minSel ? minSel.selectedOptions[0] : null;
                    const minText = minOpt && minOpt.value ? minOpt.textContent.trim() : '';
                    const subSel = card.querySelector('.emp-ministry-sub');
                    const subOpt = subSel ? subSel.selectedOptions[0] : null;
                    const subText = subOpt && subOpt.value ? subOpt.textContent.trim() : '';
                    org = minText;
                    if (org && subText) org += ` - ${subText}`;
                    if (!org) org = 'وزارة / جهة حكومية';
                } else if (jobType === 'private') {
                    org = 'القطاع الخاص';
                } else if (jobType === 'freelance' || jobType === 'entrepreneur') {
                    org = 'عمل حر';
                } else {
                    org = jobType;
                }
                
                const titleSel = card.querySelector('.emp-job-title');
                const titleOpt = titleSel ? titleSel.selectedOptions[0] : null;
                let titleText = titleOpt && titleOpt.value ? titleOpt.textContent.trim() : '';
                const specVal = (card.querySelector('.emp-speciality')?.value || '').trim();
                if (specVal) {
                    titleText = titleText ? `${titleText} (${specVal})` : specVal;
                }
                if (!titleText) titleText = 'موظف';
                
                const joiningDate = card.querySelector('.emp-joining-date')?.value || null;
                const currentlyWorking = card.querySelector('.emp-currently-working')?.value || null;
                const endDate = currentlyWorking === 'yes' ? null : (card.querySelector('.emp-end-date')?.value || null);
                const jobDescription = (card.querySelector('[name="empJobDescription"]')?.value || '').trim() || null;
                
                payload.professionalHistory.push({
                    organization: org,
                    title: titleText,
                    startDate: joiningDate,
                    endDate: endDate,
                    responsibilities: jobDescription,
                    reasonForLeaving: null
                });
            });
        }

        // 2. Collect Additional Professional History from form fields (guard against duplicates
        //    in case these fields overlap with the DOM cards collected above).
        const orgs = fd.getAll('organizationIndustry[]');
        const starts = fd.getAll('startDate[]');
        const ends = fd.getAll('endDate[]');
        const responsibilities = fd.getAll('keyResponsibilities[]');
        const reasons = fd.getAll('reasonForLeaving[]');

        // Build a Set of organisation names already captured from the DOM cards
        const existingOrgs = new Set(
            payload.professionalHistory.map((e) => (e.organization || '').trim().toLowerCase())
        );

        for (let i = 0; i < orgs.length; i++) {
            const orgName = (orgs[i] || '').trim();
            if (!orgName) continue;
            // Skip if this organisation was already added by the DOM-card loop above
            if (existingOrgs.has(orgName.toLowerCase())) continue;
            payload.professionalHistory.push({
                organization: orgName,
                startDate: starts[i] || null,
                endDate: ends[i] || null,
                responsibilities: responsibilities[i] || null,
                reasonForLeaving: reasons[i] || null,
                title: 'موظف'
            });
        }

        // Map References
        const refNames = fd.getAll('referenceName[]');
        const refRels = fd.getAll('referenceRelationship[]');
        const refContacts = fd.getAll('referenceContact[]');

        for (let i = 0; i < refNames.length; i++) {
            if (refNames[i]) {
                payload.references.push({
                    name: refNames[i],
                    relationship: refRels[i],
                    contact: refContacts[i]
                });
            }
        }

        // Helper to read cookie
        const getCookie = (name) => {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        };
        const csrfToken = getCookie('csrf_token');

        // Actual API Call
        fetch(API_PREFIX + '/api/trainee/register', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken || ''
            },
            body: JSON.stringify(payload)
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.detail || 'Registration failed'); });
                }
                return response.json();
            })
            .then(data => {
                clearFormState();
                window.location.href = 'index.html?registered=1';
            })
            .catch(err => {
                // Restore submit button — keep the form on step 10 with all data intact
                if (btnSubmit) {
                    btnSubmit.disabled = false;
                    btnSubmit.innerHTML = '<span class="reg-btn__icon reg-btn__icon--check">✓</span><span>إرسال التسجيل</span>';
                }
                // Show a detailed, persistent error banner
                const errDetail = err.message || 'خطأ غير معروف';
                window.showDropdownMessage(
                    '❌ فشل إرسال التسجيل: ' + errDetail +
                    ' — يرجى مراجعة الحقول وإعادة المحاولة. بياناتك محفوظة ولم تُحذف.',
                    true
                );
                // Make sure we stay on step 10
                currentStep = TOTAL_STEPS;
                updateUI();
                // Scroll to top of final step so user sees the error toast
                const finalStep = document.querySelector('.reg-step[data-step="10"]');
                if (finalStep) finalStep.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
    });

    stepperItems.forEach((item) => {
        item.addEventListener('click', function () {
            const step = parseInt(this.dataset.step, 10);
            if (step < currentStep) {
                saveFormState();
                currentStep = step;
                if (step === 5) skillsStep5Locked = false;
                syncUrlToStep(currentStep);
                updateUI();
            } else if (step > currentStep) {
                const startStep = currentStep;
                let failedAt = 0;
                for (let s = startStep; s < step; s++) {
                    currentStep = s;
                    if (!validateCurrentStep({ silent: true })) {
                        failedAt = s;
                        break;
                    }
                }
                if (failedAt) {
                    currentStep = failedAt;
                    updateUI();
                    const failEl = document.querySelector(`.reg-step[data-step="${failedAt}"]`);
                    failEl?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    window.showDropdownMessage('أكمل جميع الحقول المطلوبة في هذه الخطوة قبل الانتقال إلى خطوة أخرى.', true);
                    return;
                }
                saveFormState();
                currentStep = step;
                if (step > 5 && startStep <= 5) skillsStep5Locked = true;
                syncUrlToStep(currentStep);
                updateUI();
            }
        });
    });

    setupStepOneDynamicLogic();
    setupStepTwoDynamicLogic();
    setupStepThreeEducationalLogic();
    setupStepFourEmploymentLogic();
    setupStepSixPrizesConferencesLogic();
    setupStepSevenPublicPoliticalLegalLogic();
    setupStepEightMultiFileNames();
    setupStepEightScholarshipEssayCount();
    setupStepTenPhotoFilenameHints();

    // Restore persisted form data and step, then set initial URL state
    restoreFormState();
    syncUrlToStep(currentStep, true);  // replace (not push) so back-button history starts clean
    updateUI();
})();

