document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const courseId = urlParams.get('course_id');
    const token = urlParams.get('token');
    
    // Attempt to persist token in sessionStorage if it was passed in URL
    if (token) {
        let session = {};
        try {
            session = JSON.parse(sessionStorage.getItem('ntaTrainee') || '{}');
        } catch(e) {}
        session.token = token;
        sessionStorage.setItem('ntaTrainee', JSON.stringify(session));
    }
    
    // Retrieve token (either from URL or storage)
    const activeToken = token || (JSON.parse(sessionStorage.getItem('ntaTrainee') || '{}').token);

    if (!courseId) {
        alert("Course ID is missing. Cannot load workflow.");
        return;
    }
    
    if (!activeToken) {
        alert("You are not authenticated. Please log in.");
        window.location.href = "/";
        return;
    }

    const container = document.getElementById('wizard-container');
    const loader = document.getElementById('globalLoader');

    let currentStepId = null;

    function showLoader() {
        if (loader) loader.classList.remove('hidden');
    }

    function hideLoader() {
        if (loader) setTimeout(() => loader.classList.add('hidden'), 300);
    }

    function authHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${activeToken}`
        };
    }

    async function loadWorkflowStep() {
        showLoader();
        try {
            const res = await fetch(`/api/progress/status?course_id=${courseId}`, {
                headers: authHeaders()
            });
            if (!res.ok) {
                if (res.status === 401) {
                    alert('Session expired. Please log in again.');
                    window.location.href = "/";
                    return;
                }
                throw new Error('Failed to fetch status');
            }
            const data = await res.json();
            
            if (data.status === 'not_started') {
                container.innerHTML = '<div class="step-card" style="text-align: center;"><h2>Course not started</h2><p>Please initiate registration.</p></div>';
                hideLoader();
                return;
            }

            currentStepId = data.current_step_id;

            // Wait Gate UI Routing
            if (data.status === 'waiting_for_event') {
                const htmlRes = await fetch('components/wait_gate.html');
                const html = await htmlRes.text();
                container.innerHTML = html;
                
                // Inject metadata if present
                if (data.meta_data && data.meta_data.exam_date) {
                    const d = new Date(data.meta_data.exam_date);
                    const el = document.getElementById('waitGateDate');
                    if (el) el.innerText = d.toLocaleString('ar-EG');
                }
                hideLoader();
                return;
            }

            // RBAC Lockout UI Routing
            if (data.status === 'admission_phase') {
                const htmlRes = await fetch('components/admission_review.html');
                const html = await htmlRes.text();
                container.innerHTML = html;
                hideLoader();
                return;
            }

            // Normal Component Routing
            if (data.frontend_component_route) {
                const htmlRes = await fetch(data.frontend_component_route);
                const html = await htmlRes.text();
                container.innerHTML = html;
                attachFormListener();
            } else {
                container.innerHTML = '<div class="step-card"><h2>Error</h2><p>No component route defined for this step.</p></div>';
            }
        } catch (err) {
            console.error(err);
            container.innerHTML = `<div class="step-card"><h2>Error</h2><p>${err.message}</p></div>`;
        } finally {
            hideLoader();
        }
    }

    function attachFormListener() {
        const form = document.getElementById('stepForm');
        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }

            const formData = new FormData(form);
            const payload = {};
            formData.forEach((value, key) => {
                payload[key] = value;
            });

            // Special logic for boolean select
            if (payload.has_toefl === "true") payload.has_toefl = true;
            if (payload.has_toefl === "false") payload.has_toefl = false;

            showLoader();
            try {
                const res = await fetch('/api/progress/advance', {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify({
                        course_id: parseInt(courseId),
                        current_step_id: currentStepId,
                        payload: payload
                    })
                });

                if (!res.ok) {
                    const errData = await res.json();
                    alert('Submission Error: ' + (errData.detail || 'Unknown Error'));
                    hideLoader();
                    return;
                }

                // Move to next step
                loadWorkflowStep();
            } catch (err) {
                console.error(err);
                alert('An error occurred while submitting.');
                hideLoader();
            }
        });
    }

    // Initialize
    loadWorkflowStep();
});

