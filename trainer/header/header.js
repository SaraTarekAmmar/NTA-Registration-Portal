; (function () {
    document.addEventListener('DOMContentLoaded', function () {
        var container = document.getElementById('ntaHeader');
        if (!container) return;

        function renderSharedHeader() {
            var currentPath = window.location.pathname || '';
            var headerPath = 'header/header.html';

            // If we are in a subdirectory like 'view trainees/' or 'generate quiz/'
            if (currentPath.includes('/view trainees/') || currentPath.includes('/generate quiz/')) {
                headerPath = '../' + headerPath;
            }

            fetch(headerPath)
                .then(function (res) {
                    if (!res.ok) throw new Error('HTTP ' + res.status);
                    return res.text();
                })
                .then(function (html) {
                    if (headerPath.startsWith('../')) {
                        html = html.replace(/src="images\//g, 'src="../images/');
                        html = html.replace(/href="trainer-dashboard\.html/g, 'href="../trainer-dashboard.html');
                    }
                    container.innerHTML = html;
                    initHeaderBehavior();
                })
                .catch(function (err) {
                    console.error('Error rendering header:', err);
                });
        }

        function initHeaderBehavior() {
            var logoutBtn = container.querySelector('#logoutBtn');
            var themeToggle = container.querySelector('#themeToggle');

            if (logoutBtn) {
                logoutBtn.addEventListener('click', function () {
                    localStorage.removeItem('ntaTrainer');
                    window.location.replace('/index.html');
                });
            }

            if (themeToggle) {
                themeToggle.addEventListener('click', function () {
                    var html = document.documentElement;
                    if (html.classList.contains('light-mode')) {
                        html.classList.remove('light-mode');
                        localStorage.setItem('nta-theme', 'dark');
                    } else {
                        html.classList.add('light-mode');
                        localStorage.setItem('nta-theme', 'light');
                    }
                });
            }
        }

        renderSharedHeader();
    });

    // Global helper for authenticated API calls for Trainer
    window.authenticatedFetch = function (url, options = {}) {
        const session = JSON.parse(localStorage.getItem('ntaTrainer') || '{}');
        const token = session.token;

        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return fetch(url, {
            ...options,
            headers: headers
        }).then(res => {
            if (res.status === 401) {
                localStorage.removeItem('ntaTrainer');
                window.location.replace('/index.html');
                return Promise.reject('Session expired');
            }
            return res;
        });
    };
})();
