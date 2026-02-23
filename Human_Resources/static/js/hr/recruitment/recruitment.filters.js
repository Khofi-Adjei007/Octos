/* =========================================================
   RECRUITMENT FILTER MODULE
   Stage-based filtering aligned with RecruitmentEngine
========================================================= */

import { qa } from '../core.js';

let currentFilter = 'all';

const CLOSED_STATUSES = ['hire_approved', 'rejected', 'withdrawn', 'closed'];


/* -----------------------------------------
 * GET CURRENT FILTER
 * ----------------------------------------- */
export function getRecruitmentFilter() {
  return currentFilter;
}


/* -----------------------------------------
 * APPLY FILTER TO DATASET
 * ----------------------------------------- */
export function applyRecruitmentFilter(applications) {

  if (currentFilter === 'all') {
    return applications;
  }

  if (currentFilter === 'closed') {
    return applications.filter(app =>
      CLOSED_STATUSES.includes(app.status)
    );
  }

  // Stage-based filters: submitted, screening, interview, final_review, decision
  return applications.filter(app =>
    app.current_stage === currentFilter &&
    !CLOSED_STATUSES.includes(app.status)
  );
}


/* -----------------------------------------
 * BIND FILTER BUTTONS
 * ----------------------------------------- */
export function bindRecruitmentFilters(onChange) {

  qa('.recruitment-filters .filter-chip')
    .forEach(btn => {

      btn.addEventListener('click', () => {

        currentFilter = btn.dataset.filter;

        qa('.recruitment-filters .filter-chip')
          .forEach(b => b.classList.toggle('active', b === btn));

        if (typeof onChange === 'function') {
          onChange(currentFilter);
        }

      });

    });
}