/**
 * ntaConfirm — Accessible styled confirmation dialog replacing native confirm().
 * 
 * Usage:
 *   const ok = await ntaConfirm('هل أنت متأكد من حذف هذه الخطوة؟');
 *   if (ok) { ... }
 * 
 * Features:
 * - Fully keyboard navigable (Tab cycles between buttons; Enter/Escape work)
 * - Focus trapped inside dialog while open
 * - Focus returns to the triggering element on close
 * - Respects prefers-reduced-motion
 * - RTL-aware layout
 */
(function () {
  'use strict';

  let _overlay = null;

  function _ensureStyles() {
    if (document.getElementById('nta-confirm-styles')) return;
    const style = document.createElement('style');
    style.id = 'nta-confirm-styles';
    style.textContent = `
      .nta-confirm-overlay {
        position: fixed; inset: 0; z-index: 99999;
        display: flex; align-items: center; justify-content: center;
        background: rgba(3, 7, 18, 0.75);
        backdrop-filter: blur(6px);
        animation: nta-confirm-fade-in 0.18s ease forwards;
      }
      @media (prefers-reduced-motion: reduce) {
        .nta-confirm-overlay { animation: none; }
        .nta-confirm-dialog { animation: none; }
      }
      @keyframes nta-confirm-fade-in {
        from { opacity: 0; }
        to   { opacity: 1; }
      }
      @keyframes nta-confirm-slide-in {
        from { opacity: 0; transform: translateY(-12px) scale(0.97); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
      }
      .nta-confirm-dialog {
        background: var(--bg-card-solid, #0f172a);
        border: 1px solid var(--border-color, rgba(51,65,85,0.9));
        border-radius: 16px;
        box-shadow: 0 24px 80px rgba(0,0,0,0.6);
        padding: 28px 32px;
        max-width: 420px; width: calc(100% - 40px);
        direction: rtl; text-align: right;
        animation: nta-confirm-slide-in 0.22s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        outline: none;
      }
      .nta-confirm-icon {
        width: 48px; height: 48px; border-radius: 50%;
        background: rgba(239,68,68,0.12);
        border: 1px solid rgba(239,68,68,0.3);
        display: flex; align-items: center; justify-content: center;
        margin: 0 0 16px auto;
        font-size: 22px;
      }
      .nta-confirm-title {
        font-size: 1.05rem; font-weight: 700;
        color: var(--text-main, #f8fafc);
        margin: 0 0 10px; line-height: 1.5;
      }
      .nta-confirm-message {
        font-size: 0.88rem;
        color: var(--text-muted, #cbd5e1);
        margin: 0 0 24px; line-height: 1.6;
      }
      .nta-confirm-actions {
        display: flex; gap: 10px; justify-content: flex-end;
      }
      .nta-confirm-btn {
        padding: 9px 22px; border-radius: 8px; border: none;
        font-family: inherit; font-size: 0.9rem; font-weight: 600;
        cursor: pointer; transition: opacity 0.15s ease;
      }
      .nta-confirm-btn:focus-visible {
        outline: 2px solid var(--accent, #6366f1);
        outline-offset: 2px;
      }
      .nta-confirm-btn:hover { opacity: 0.88; }
      .nta-confirm-btn--danger {
        background: var(--color-error, #ef4444);
        color: #fff;
      }
      .nta-confirm-btn--cancel {
        background: var(--surface-glass-strong, rgba(255,255,255,0.08));
        color: var(--text-muted, #cbd5e1);
        border: 1px solid var(--border-color, rgba(51,65,85,0.9));
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * ntaConfirm(message, options?) → Promise<boolean>
   * @param {string} message   Main message text (Arabic supported)
   * @param {object} [opts]
   *   @param {string} [opts.title='تأكيد العملية']   Dialog title
   *   @param {string} [opts.confirmText='حذف']       Confirm button label
   *   @param {string} [opts.cancelText='إلغاء']      Cancel button label
   *   @param {string} [opts.icon='⚠️']               Icon inside the circle
   */
  window.ntaConfirm = function (message, opts = {}) {
    _ensureStyles();
    const {
      title = 'تأكيد العملية',
      confirmText = 'تأكيد',
      cancelText = 'إلغاء',
      icon = '⚠️',
    } = opts;

    // Close any existing dialog
    if (_overlay) _overlay.remove();

    return new Promise((resolve) => {
      const trigger = document.activeElement;

      _overlay = document.createElement('div');
      _overlay.className = 'nta-confirm-overlay';
      _overlay.setAttribute('role', 'dialog');
      _overlay.setAttribute('aria-modal', 'true');
      _overlay.setAttribute('aria-labelledby', 'nta-confirm-title');
      _overlay.setAttribute('aria-describedby', 'nta-confirm-message');

      _overlay.innerHTML = `
        <div class="nta-confirm-dialog" tabindex="-1">
          <div class="nta-confirm-icon" aria-hidden="true">${icon}</div>
          <h2 id="nta-confirm-title" class="nta-confirm-title">${title}</h2>
          <p id="nta-confirm-message" class="nta-confirm-message">${message}</p>
          <div class="nta-confirm-actions">
            <button class="nta-confirm-btn nta-confirm-btn--cancel" id="nta-btn-cancel">${cancelText}</button>
            <button class="nta-confirm-btn nta-confirm-btn--danger" id="nta-btn-confirm">${confirmText}</button>
          </div>
        </div>
      `;

      function close(result) {
        _overlay.remove();
        _overlay = null;
        if (trigger && typeof trigger.focus === 'function') trigger.focus();
        resolve(result);
      }

      // Button handlers
      _overlay.querySelector('#nta-btn-confirm').addEventListener('click', () => close(true));
      _overlay.querySelector('#nta-btn-cancel').addEventListener('click', () => close(false));

      // Keyboard: Escape = cancel, Tab = cycle focus
      _overlay.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') { e.preventDefault(); close(false); return; }
        if (e.key === 'Tab') {
          const focusable = _overlay.querySelectorAll('button');
          const first = focusable[0], last = focusable[focusable.length - 1];
          if (e.shiftKey && document.activeElement === first) {
            e.preventDefault(); last.focus();
          } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault(); first.focus();
          }
        }
      });

      // Click outside = cancel
      _overlay.addEventListener('click', (e) => {
        if (e.target === _overlay) close(false);
      });

      document.body.appendChild(_overlay);
      // Focus the dialog container so keyboard events fire
      _overlay.querySelector('.nta-confirm-dialog').focus();
    });
  };
})();
