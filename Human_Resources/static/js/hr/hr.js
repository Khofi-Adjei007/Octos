/* =========================================================
   HR ENTRY FILE
   Wires all modules together
========================================================= */

import { initApp } from './core.js';

import { loadOverview } from './overview.js';

import { loadRecruitment } from './recruitment/recruitment.ui.js';
import { bindRecruitmentFilters } from './recruitment/recruitment.filters.js';

import { applyBranchGradients } from './branches.js';


/* -----------------------------------------
 * TEMP: PAYROLL LOADER
 * ----------------------------------------- */
function loadPayroll() {
  console.log('Payroll context loaded');
}


/* -----------------------------------------
 * INITIAL GRADIENT SETUP
 * ----------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {
  applyBranchGradients();
});


/* -----------------------------------------
 * BOOTSTRAP APPLICATION
 * ----------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {

  /* -----------------------------
     REVIEW BUTTON (Event Delegation)
     Navigates directly to detail page.
  ------------------------------ */
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-review');
    if (!btn) return;

    const id = btn.dataset.id;
    if (!id) return;

    window.location.href = `/hr/applications/${id}/`;
  });


  /* -----------------------------
     CORE CONTEXT ROUTING
  ------------------------------ */
  initApp({
    onOverview: loadOverview,
    onRecruitment: () => {
      loadRecruitment();
      bindRecruitmentFilters(() => {
        loadRecruitment();
      });
    },
    onPayroll: loadPayroll,
  });

});


/* -----------------------------------------
   PROFILE DROPDOWN
----------------------------------------- */
const profile = document.getElementById('userProfile');
const dropdown = document.getElementById('profileDropdown');

if (profile && dropdown) {
  profile.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.toggle('open');
  });

  document.addEventListener('click', () => {
    dropdown.classList.remove('open');
  });
}


/* -----------------------------------------
   NOTIFICATION DROPDOWN
----------------------------------------- */
const notificationWrapper = document.getElementById('notificationWrapper');
const notificationDropdown = document.getElementById('notificationDropdown');

if (notificationWrapper && notificationDropdown) {
  notificationWrapper.addEventListener('click', (e) => {
    e.stopPropagation();
    notificationDropdown.classList.toggle('open');
  });

  document.addEventListener('click', () => {
    notificationDropdown.classList.remove('open');
  });
}