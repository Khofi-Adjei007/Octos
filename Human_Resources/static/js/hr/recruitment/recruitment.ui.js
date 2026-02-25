import { q } from '../core.js';
import { fetchApplications } from './recruitment.api.js';
import { buildApplicationCard } from './recruitment.cards.js';
import { applyRecruitmentFilter } from './recruitment.filters.js';

const CLOSED_STATUSES = ['hire_approved', 'rejected', 'withdrawn', 'closed', 'onboarding_complete'];

export async function loadRecruitment() {

  const list  = document.querySelector('#recruitment-items');
  const empty = document.querySelector('#recruitment-empty');

  if (!list || !empty) {
    console.log("Missing DOM nodes");
    return;
  }

  list.innerHTML = '';

  try {

    const response = await fetchApplications();

    if (!Array.isArray(response)) {
      throw new Error("Response is not array");
    }

    // Inject counts into filter chips
    updateFilterCounts(response);

    const filtered = applyRecruitmentFilter(response);

    if (filtered.length === 0) {
      empty.classList.remove('hidden');
    } else {
      empty.classList.add('hidden');
      filtered.forEach(app => {
        const card = buildApplicationCard(app);
        list.appendChild(card);
      });
    }

  } catch (error) {
    console.error("Load error:", error);
  }
}


/* -----------------------------------------
 * INJECT COUNTS INTO FILTER CHIPS
 * ----------------------------------------- */
function updateFilterCounts(applications) {

  const counts = {
    all:          applications.length,
    submitted:    applications.filter(a => a.current_stage === 'submitted'    && !CLOSED_STATUSES.includes(a.status)).length,
    screening:    applications.filter(a => a.current_stage === 'screening'    && !CLOSED_STATUSES.includes(a.status)).length,
    interview:    applications.filter(a => a.current_stage === 'interview'    && !CLOSED_STATUSES.includes(a.status)).length,
    final_review: applications.filter(a => a.current_stage === 'final_review' && !CLOSED_STATUSES.includes(a.status)).length,
    decision:     applications.filter(a => a.current_stage === 'decision'     && !CLOSED_STATUSES.includes(a.status)).length,
    onboarding:   applications.filter(a => a.status === 'hire_approved').length,
  };

  document.querySelectorAll('.recruitment-filters .filter-chip').forEach(btn => {
    const filter = btn.dataset.filter;
    const count  = counts[filter] ?? 0;

    // Store original label once, never overwrite it
    if (!btn.dataset.label) {
      btn.dataset.label = btn.textContent.trim();
    }

    btn.innerHTML = `${btn.dataset.label} <span class="chip-count">${count}</span>`;
  });
}