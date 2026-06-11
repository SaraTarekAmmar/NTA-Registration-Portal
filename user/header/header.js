; (function () {
    document.addEventListener('DOMContentLoaded', function () {
        var container = document.getElementById('ntaHeader');
        if (!container) return;

        function syncBodyDataPageForCoursesUrl() {
            try {
                var path = window.location.pathname || '';
                var file = path.split('/').pop() || '';
                if (file !== 'courses.html' && !path.endsWith('/courses.html')) return;
                var params = new URLSearchParams(window.location.search || '');
                if (params.get('filter') === 'my') {
                    document.body.setAttribute('data-page', 'enrolled-courses');
                } else {
                    document.body.setAttribute('data-page', 'available-courses');
                }
            } catch (e) { /* ignore */ }
        }

        function renderSharedHeader(skipFetch = false) {
            syncBodyDataPageForCoursesUrl();

            // If nothing loaded (e.g. fetch blocked on file://), inject inline HTML fallback
            if (!container.innerHTML || !container.innerHTML.trim()) {
                container.innerHTML =
                    '<header class="nta-header">' +
                    '  <a href="index.html" class="nta-header__logo">' +
                    '    <img src="images/logo2.png" alt="" class="nta-header__logo-img" ' +
                    '         onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">' +
                    '    <span class="nta-header__logo-fallback">NTA</span>' +
                    '    <div class="nta-header__logo-text">' +
                    '      <span class="nta-header__logo-main">NTA</span>' +
                    '      <span class="nta-header__logo-sub">NATIONAL TRAINING ACADEMY</span>' +
                    '      <span class="nta-header__logo-ar">الأكاديمية الوطنية للتدريب</span>' +
                    '    </div>' +
                    '  </a>' +
                    '  <div class="nta-header__center">' +
                    '    <span class="nta-header__section-label" id="headerSectionLabel">إدارة المهارات</span>' +
                    '    <nav class="nta-header__nav">' +
                    '      <a href="index.html" class="nta-header__btn nta-header__chip" data-page="login" id="headerHomeChip"><span>الرئيسية</span></a>' +
                    '      <a href="courses.html" class="nta-header__btn nta-header__chip" data-page="enrolled-courses" id="headerCoursesChip"><span>دوراتي</span></a>' +
                    '      <a href="admin-users.html" class="nta-header__btn nta-header__chip" data-page="admin-users" id="headerUsersChip" style="display:none"><span>قائمة المرشحين</span></a>' +
                    '      <a href="admissions.html" class="nta-header__btn nta-header__chip" data-page="admissions" id="headerAdmissionsChip" style="display:none"><span>مراحل القبول</span></a>' +
                    '      <a href="profile.html" class="nta-header__btn nta-header__chip" data-page="profile" id="headerProfileChip">' +
                    '        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">' +
                    '          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" ' +
                    '                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>' +
                    '        </svg><span>الملف الشخصي</span></a>' +
                    '    </nav>' +
                    '  </div>' +
                    '  <div class="nta-header__actions">' +
                    '    <button type="button" class="nta-header__btn nta-header__btn--logout" id="logoutBtn">تسجيل الخروج</button>' +
                    '    <button type="button" class="nta-header__theme" id="themeToggle" aria-label="تبديل الوضع">' +
                    '      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">' +
                    '        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" ' +
                    '              d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>' +
                    '      </svg>' +
                    '    </button>' +
                    '  </div>' +
                    '</header>';
            }

            // Auth-related visibility based on trainee session
            var session = {};
            try {
                session = JSON.parse(localStorage.getItem('ntaTrainee') || '{}');
            } catch (e) {
                session = {};
            }

            var loginBtn = container.querySelector('#headerLoginBtn');
            var logoutBtn = container.querySelector('#logoutBtn');
            var coursesChip = container.querySelector('#headerCoursesChip');
            var profileChip = container.querySelector('#headerProfileChip');
            var homeChip = container.querySelector('#headerHomeChip') || container.querySelector('[data-page="login"]');
            var usersChip = container.querySelector('#headerUsersChip');
            var admissionsChip = container.querySelector('#headerAdmissionsChip');
            var adminChip = container.querySelector('#headerAdminChip');
            var sectionLabel = container.querySelector('#headerSectionLabel');

            var isTrainee = session && session.role === 'trainee';
            var isAdmin = session && session.role === 'admin';
            var isEditor = session && session.role === 'editor';
            var isTrainer = session && session.role === 'trainer';

            var curPath = decodeURIComponent(window.location.pathname);
            var prefix = (curPath.includes('/view trainees/') || curPath.includes('/generate quiz/')) ? '../' : '';

            if (loginBtn) loginBtn.style.display = (isTrainee || isAdmin || isEditor || isTrainer) ? 'none' : 'inline-flex';
            if (logoutBtn) logoutBtn.style.display = (isTrainee || isAdmin || isEditor || isTrainer) ? 'inline-flex' : 'none';

            if (isAdmin) {
                if (coursesChip) coursesChip.style.display = 'none';
                if (profileChip) profileChip.style.display = 'none';
                if (adminChip) adminChip.style.display = 'none';
                if (usersChip) {
                    usersChip.style.display = 'inline-flex';
                    usersChip.href = prefix + 'admin-users.html';
                }
                if (homeChip) {
                    homeChip.href = prefix + 'admin.html';
                    homeChip.setAttribute('data-page', 'admin');
                    homeChip.style.display = 'inline-flex';
                    var span = homeChip.querySelector('span');
                    if (span) span.textContent = 'لوحة التحكم';
                }
            } else if (isTrainer) {
                if (coursesChip) coursesChip.style.display = 'none';
                if (profileChip) profileChip.style.display = 'none';
                if (adminChip) adminChip.style.display = 'none';
                if (usersChip) usersChip.style.display = 'none';
                if (homeChip) {
                    homeChip.href = prefix + 'trainer-dashboard.html';
                    homeChip.setAttribute('data-page', 'trainer');
                    homeChip.style.display = 'inline-flex';
                    var spanEl = homeChip.querySelector('span');
                    if (spanEl) spanEl.textContent = 'لوحة المدرب';
                }
            } else {
                if (homeChip) {
                    homeChip.href = isTrainee ? prefix + 'courses.html' : prefix + 'index.html';
                    homeChip.setAttribute('data-page', isTrainee ? 'available-courses' : 'login');
                    homeChip.style.display = 'inline-flex';
                    var spanEl = homeChip.querySelector('span');
                    if (spanEl) spanEl.textContent = isTrainee ? 'الدورات' : 'الرئيسية';
                }
                if (coursesChip) {
                    coursesChip.style.display = isTrainee ? 'inline-flex' : 'none';
                    coursesChip.href = prefix + 'courses.html?filter=my';
                    coursesChip.setAttribute('data-page', 'enrolled-courses');
                }
                if (admissionsChip) {
                    admissionsChip.style.display = isTrainee ? 'inline-flex' : 'none';
                    admissionsChip.href = prefix + 'admissions.html';
                }
                if (profileChip) {
                    profileChip.style.display = isTrainee ? 'inline-flex' : 'none';
                    profileChip.href = prefix + 'profile.html';
                }
                if (usersChip) {
                    usersChip.style.display = isAdmin ? 'inline-flex' : 'none';
                    usersChip.href = prefix + 'admin-users.html';
                }
                if (adminChip) adminChip.style.display = 'none';
            }

            if (sectionLabel) {
                if (isTrainer) {
                    sectionLabel.textContent = 'لوحة المدرب';
                } else if (isAdmin) {
                    sectionLabel.textContent = 'خط التقديم';
                } else {
                    sectionLabel.textContent = 'إدارة المهارات';
                }
            }

            // Highlight active tab after href/data-page mutations (must run last)
            container.querySelectorAll('.nta-header__chip').forEach(function (chip) {
                chip.classList.remove('active');
            });
            var page = document.body.getAttribute('data-page');
            if (page) {
                var activeChip = container.querySelector('.nta-header__chip[data-page="' + page + '"]');
                if (activeChip) {
                    activeChip.classList.add('active');
                }
            }

            if (window.NTATheme && typeof window.NTATheme.bindAllToggles === 'function') {
                window.NTATheme.bindAllToggles();
            }

            // Shared logout button
            if (logoutBtn && !logoutBtn.dataset.ntaLogoutBound) {
                logoutBtn.dataset.ntaLogoutBound = '1';
                logoutBtn.addEventListener('click', function () {
                    try {
                        localStorage.removeItem('ntaTrainee');
                    } catch (e) {
                        console.warn('Unable to clear trainee session', e);
                    }
                    
                    var loginPath = 'index.html';
                    var curPath = decodeURIComponent(window.location.pathname);
                    if (curPath.includes('/view trainees/') || curPath.includes('/generate quiz/')) {
                        loginPath = '../' + loginPath;
                    }
                    window.location.href = loginPath;
                });
            }

            if (skipFetch) return;

            // Smart path detection for subdirectories
            var headerPath = 'header/header.html';
            var logoPath = 'images/logo2.png';
            
            var currentPath = decodeURIComponent(window.location.pathname);
            
            // If we are in a subdirectory like 'view trainees/', we need to go up
            if (currentPath.includes('/view trainees/') || currentPath.includes('/generate quiz/')) {
                headerPath = '../' + headerPath;
                logoPath = '../' + logoPath;
            }

            fetch(headerPath)
                .then(function (res) {
                    if (!res.ok) throw new Error('HTTP ' + res.status);
                    return res.text();
                })
                .then(function (html) {
                    // Adjust internal logo paths in the loaded HTML
                    if (headerPath.startsWith('../')) {
                        html = html.replace(/src="images\//g, 'src="../images/');
                    }
                    container.innerHTML = html;
                    renderSharedHeader(true); // Pass true to skip second fetch
                })
                .catch(function () {
                    renderSharedHeader(true);
                });
        }

        // INITIAL CALL to render the header
        renderSharedHeader();
    });

    // Global helper for authenticated API calls
    window.authenticatedFetch = function (url, options = {}) {
        const session = JSON.parse(localStorage.getItem('ntaTrainee') || '{}');
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
                // Token expired or invalid
                localStorage.removeItem('ntaTrainee');
                window.location.href = 'index.html';
                return Promise.reject('Session expired');
            }
            return res;
        });
    };
})();


