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
