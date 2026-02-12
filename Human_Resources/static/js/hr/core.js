/* =========================================================
   HR CORE
   Global infrastructure + context orchestration
========================================================= */

/* -----------------------------------------
 * CONFIG
 * ----------------------------------------- */
export const API_BASE = '/hr/api';


/* -----------------------------------------
 * DOM HELPERS
 * ----------------------------------------- */
export const q = (selector, scope = document) =>
  scope.querySelector(selector);

export const qa = (selector, scope = document) =>
  Array.from(scope.querySelectorAll(selector));


/* -----------------------------------------
 * CSRF HELPER
 * ----------------------------------------- */
export function getCSRF() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}


/* -----------------------------------------
 * CONTEXT STATE
 * ----------------------------------------- */
let currentContext = 'overview';

export function getContext() {
  return currentContext;
}

export function setContext(value) {
  currentContext = value;
}


/* -----------------------------------------
 * CONTEXT PANEL VISIBILITY
 * ----------------------------------------- */
export function showContext(target) {
  qa('.context-panel').forEach(panel => {
    panel.classList.toggle(
      'hidden',
      panel.dataset.context !== target
    );
  });
}


/* -----------------------------------------
 * CONTEXT SWITCHING
 * ----------------------------------------- */
function bindContextSwitching(onChange) {
  qa('.switch-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const newContext = btn.dataset.context;

      setContext(newContext);

      qa('.switch-btn').forEach(b =>
        b.classList.toggle('active', b === btn)
      );

      showContext(newContext);

      if (typeof onChange === 'function') {
        onChange(newContext);
      }
    });
  });
}


/* -----------------------------------------
 * APP INITIALIZER
 * ----------------------------------------- */
export function initApp({
  onOverview,
  onRecruitment,
  onEmployees
} = {}) {

  bindContextSwitching((ctx) => {

    if (ctx === 'overview') {
      onOverview?.();
    }

    if (ctx === 'recruitment') {
      onRecruitment?.();
    }

    if (ctx === 'employees') {
      onEmployees?.();
    }

  });

  // Default boot state
  showContext(currentContext);

  if (currentContext === 'overview') {
    onOverview?.();
  }
}
