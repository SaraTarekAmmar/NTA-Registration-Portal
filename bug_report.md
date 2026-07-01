# Automated Bug Hunt Report

## Admin Portal (Port 8002)
- **Missing Images (404s)**:
  - `http://localhost:8002/data/trainees/Karim_Essam_El-Din_Fahmy_29109141000018/karim_front_photo.png`
  - `http://localhost:8002/data/trainees/Lobna_Hussein_El-Shinawi_29403071000017/lobna_front_photo.png`
  - `http://localhost:8002/data/trainees/Bassem_Mohamed_El-Ghazaly_29008171000016/bassem_front_photo.png`
- **Missing Page (404)**: `admin-reports.html` is linked or expected in navigation but the file does not exist on disk.

## Editor Portal (Port 8004)
- **PASS**: No 404s or console errors detected during deep navigation.

## Coordinator Portal (Port 8005)
- **PASS**: No 404s or console errors detected during deep navigation.

## Admission Center Portal (Port 7776)
- **Missing Page (404)**: `interviews.html` is missing, even though it may be linked in navigation.
- **Null Resource (404)**: A network request is being made to `http://localhost:7776/null`. This implies JavaScript is attempting to fetch a resource with an uninitialized or null variable (e.g., `src="null"` or `fetch(null)`).

## Trainer Portal (Port 8006)
- **Missing Pages (404)**: 
  - `trainer-courses.html` does not exist.
  - `trainer-attendance.html` does not exist.

## Trainee Portal (Port 7771)
- **Missing Pages (404)**: 
  - `dashboard.html` does not exist (the login now redirects correctly to `courses.html`, but if any code or link tries to hit `dashboard.html`, it will fail).

---

### Root Cause Analysis Summary
1. **Missing Views**: `trainer-courses.html`, `trainer-attendance.html`, `interviews.html`, and `admin-reports.html` are simply missing HTML files that have not been created yet but are linked in the headers or navigation flows.
2. **Missing Static Assets**: The admin panel attempts to render front photos for seeded trainee accounts that don't exist on disk (`data/trainees/...`). This was also noted as cosmetic debt in the project's instructions.
3. **Frontend JS Bug**: The Admission Center logic requests a `null` URL, likely an empty `src` or `href` attribute populated dynamically without a fallback.
