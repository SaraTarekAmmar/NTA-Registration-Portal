
document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('superadmin_token');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    try {
        const res = await fetch('/api/stats/overview', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.status === 401) {
            localStorage.removeItem('superadmin_token');
            window.location.href = 'index.html';
            return;
        }

        if (res.ok) {
            const data = await res.json();
            // Assuming we have these elements in the HTML from admin dashboard
            const kpiValues = document.querySelectorAll('.kpi-value');
            if (kpiValues.length >= 4) {
                kpiValues[0].textContent = data.total_trainees || '0';
                kpiValues[1].textContent = data.pending_ocr || '0';
                kpiValues[2].textContent = data.ocr_commits || '0';
                kpiValues[3].textContent = data.pending_enrollment || '0';
            }
        }
    } catch (error) {
        console.error('Error fetching superadmin stats:', error);
    }
});
