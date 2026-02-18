/* =========================================================
   HR ENTRY FILE
   Wires all modules together
========================================================= */

import { initApp } from './core.js';

import { loadOverview } from './overview.js';

import { loadRecruitment } from './recruitment/recruitment.ui.js';
import { bindRecruitmentFilters } from './recruitment/recruitment.filters.js';

import {
  initRecruitmentModal,
  openRecruitmentModal
} from './recruitment/recruitment.modal.js';

import { applyBranchGradients } from './branches.js';

document.addEventListener('DOMContentLoaded', () => {
  applyBranchGradients();
});


/* -----------------------------------------
 * BOOTSTRAP APPLICATION
 * ----------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {

  /* -----------------------------
     INIT MODAL SYSTEM
  ------------------------------ */
  initRecruitmentModal();

  /* -----------------------------
     REVIEW BUTTON (Event Delegation)
  ------------------------------ */
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-review');
    if (!btn) return;

    const id = btn.dataset.id;
    if (!id) return;

    openRecruitmentModal(id);
  });


  /* -----------------------------
     RECRUITMENT FILTERS
  ------------------------------ */
  bindRecruitmentFilters(() => {
    loadRecruitment();
  });


  /* -----------------------------
     CORE CONTEXT ROUTING
  ------------------------------ */
  initApp({
    onOverview: loadOverview,
    onRecruitment: loadRecruitment,
  });

});


  const profile = document.getElementById('userProfile');
  const dropdown = document.getElementById('profileDropdown');

  profile.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.toggle('open');
  });

  document.addEventListener('click', () => {
    dropdown.classList.remove('open');
  });



  const notificationWrapper = document.getElementById('notificationWrapper');
  const notificationDropdown = document.getElementById('notificationDropdown');

  notificationWrapper.addEventListener('click', (e) => {
    e.stopPropagation();
    notificationDropdown.classList.toggle('open');
  });

  document.addEventListener('click', () => {
    notificationDropdown.classList.remove('open');
  });


