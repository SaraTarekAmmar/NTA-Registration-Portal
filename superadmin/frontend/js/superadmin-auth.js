
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            const errorMsg = document.getElementById('loginError');

            try {
                submitBtn.disabled = true;
                submitBtn.innerHTML = 'جاري التحقق...';
                if(errorMsg) errorMsg.style.display = 'none';

                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('superadmin_token', data.access_token);
                    window.location.href = 'superadmin-dashboard.html';
                } else {
                    const data = await response.json();
                    throw new Error(data.detail || 'خطأ في تسجيل الدخول');
                }
            } catch (error) {
                if(errorMsg) {
                    errorMsg.textContent = error.message;
                    errorMsg.style.display = 'block';
                } else {
                    alert(error.message);
                }
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'تسجيل الدخول';
            }
        });
    }
});
