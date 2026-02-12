/* =========================================================
   RECRUITMENT FILTER MODULE
   v2 Workflow Aware Filtering
========================================================= */

import { qa } from '../core.js';

let currentFilter = 'all';

const TERMINAL_STAGES = ['onboarded', 'rejected'];

const PIPELINE_STAGES = [
  'submitted',
  'screening',
  'interview',
  'final_review',
  'offer'
];


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

  if (currentFilter === 'pipeline') {
    return applications.filter(app =>
      PIPELINE_STAGES.includes(app.current_stage)
    );
  }

  if (currentFilter === 'onboarded') {
    return applications.filter(app =>
      app.current_stage === 'onboarded'
    );
  }

  if (currentFilter === 'rejected') {
    return applications.filter(app =>
      app.current_stage === 'rejected'
    );
  }

  return applications;
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
