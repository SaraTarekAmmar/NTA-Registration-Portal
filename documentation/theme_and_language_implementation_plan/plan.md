# Implementation Plan: Universal Dark/Light Mode & I18n Support

This document outlines the comprehensive strategy for implementing a system-wide Theme Toggle (Dark/Light) and Language Switcher (Arabic/English) across the NTA Registration Portal ecosystem.

## 1. Core Architecture

To ensure consistency across the **Super Admin (React)**, **Admin (Vanilla)**, and **User (Vanilla)** portals, we will utilize a shared persistence and styling strategy.

### 1.1 State Persistence
*   **Storage**: `localStorage` will be used to store preferences:
    *   `nta-theme`: `'dark'` (default) or `'light'`
    *   `nta-lang`: `'ar'` (default) or `'en'`
*   **Initialization**: A small, blocking script will be placed in the `<head>` of every HTML file to apply the correct classes and `dir` attribute before the page renders, preventing "theme flashing."

### 1.2 Styling Strategy
*   **CSS Variables**: All hardcoded colors will be replaced with CSS variables.
*   **Tailwind Integration**: For the Super Admin portal, we will enable the `class` strategy for dark mode.

---

## 2. Theme Toggle Implementation

### 2.1 CSS Variable Refactor
A global CSS file (or shared variables) will define the theme tokens:

```css
:root {
    /* Dark Theme (Default) */
    --bg-main: #0a0c10;
    --bg-card: rgba(255, 255, 255, 0.03);
    --border-main: rgba(255, 255, 255, 0.08);
    --text-main: #f1f5f9;
    --text-muted: #94a3b8;
    --accent: #6366f1;
}

body.light-mode {
    /* Light Theme Overrides */
    --bg-main: #f8fafc;
    --bg-card: #ffffff;
    --border-main: #e2e8f0;
    --text-main: #1e293b;
    --text-muted: #64748b;
    --accent: #4f46e5;
}
```

### 2.2 Functional Toggle Logic
The existing `themeToggle` button in the headers will be activated:

```javascript
const toggleTheme = () => {
    const isDark = document.body.classList.toggle('light-mode');
    localStorage.setItem('nta-theme', isDark ? 'light' : 'dark');
    updateThemeIcon(); // Switch between sun/moon icons
};
```

---

## 3. Language Switcher Implementation (Arabic/English)

### 3.1 Localization Strategy (i18n)
*   **Admin & User Portals**: Since these are vanilla HTML, we will implement a `data-i18n` attribute system.
    *   Example: `<span data-i18n="nav_home">الرئيسية</span>`
*   **Super Admin Portal**: Integrated into React state.
    *   Example: `{t('nav_home')}`

### 3.2 Direction and Typography
When switching to English:
1.  Set `document.documentElement.dir = 'ltr'`.
2.  Set `document.documentElement.lang = 'en'`.
3.  Switch font-family to `Inter` (English) from `Tajawal` (Arabic).

### 3.3 Translations Dictionary (`translations.js`)
A centralized JSON object will hold all mappings:
```javascript
const translations = {
    ar: {
        nav_home: "الرئيسية",
        nav_courses: "دوراتي",
        logout: "تسجيل الخروج",
        // ...
    },
    en: {
        nav_home: "Home",
        nav_courses: "My Courses",
        logout: "Logout",
        // ...
    }
};
```

---

## 4. Required File Changes

### 4.1 Global/Common Changes
- **New File**: `common/js/i18n.js` — Shared translation logic.
- **New File**: `common/css/theme.css` — Shared CSS variables.

### 4.2 Super Admin Portal (`superadmin/frontend/`)
- **`index.html`**:
    - Update Tailwind config to `{ darkMode: 'class' }`.
    - Wrap UI strings in a `t()` translation function.
    - Add a Language Toggle button in the `aside` or `header`.
- **`js/superadmin.js`**:
    - Add `language` and `theme` states to the `App` component.

### 4.3 Admin Portal (`admin/`)
- **`header/header.js`**:
    - Add click listeners to `themeToggle`.
    - Add the new `langToggle` button and its listener.
- **`styles.css` / `admin.css`**:
    - Replace HEX/RGBA values with `var(--variable-name)`.
- **All individual HTML files**:
    - Add `data-i18n` attributes to all static text.

### 4.4 User Portal (`user/`)
- **`header/header.js`**: (Same as Admin Portal).
- **`styles.css` / `trainee.css`**: (Same as Admin Portal).
- **All individual HTML files**: (Same as Admin Portal).

---

## 5. Next Steps
1.  **Variable Audit**: Scan all CSS files to extract unique colors.
2.  **String Extraction**: Compile a list of all Arabic strings for translation.
3.  **Variable Injection**: Replace hardcoded values with variables.
4.  **Header Activation**: Update the shared header files to include functional buttons.
