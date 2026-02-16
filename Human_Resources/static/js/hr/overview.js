/* =========================================================
   HR OVERVIEW MODULE
   Handles Overview API + Rendering
========================================================= */

import { API_BASE, q } from '../../js/hr/core.js';


/* -----------------------------------------
 * LOAD OVERVIEW DATA
 * ----------------------------------------- */
export async function loadOverview() {

  let overview;

  try {
    const response = await fetch(`${API_BASE}/overview/`);
    overview = await response.json();
  } catch (err) {
    overview = {
      region_name: null,
      branch_count: 0,
      total_employees: 0,
      critical: []
    };
  }

  renderOverview(overview);
}


/* -----------------------------------------
 * RENDER OVERVIEW UI
 * ----------------------------------------- */
function renderOverview(data) {

  // =========================
  // REGION HEADER
  // =========================
  setText('#region-name', data.region_name);
  setText('#branch-count', data.branch_count);
  setText('#region-employees', data.total_employees);

  const branchLabel = q('#branch-label');
  if (branchLabel) {
    branchLabel.textContent =
      data.branch_count === 1 ? 'branch' : 'branches';
  }

  // =========================
  // METRIC CARDS
  // =========================
  setText('#metric-1', data.total_employees);
  setText('#metric-2', data.active_employees);
  setText('#metric-3', data.pending);
  setText('#metric-4', data.branch_count);

  // =========================
  // CRITICAL SIGNALS
  // =========================
  const criticalBox = q('#critical-summary');
  if (!criticalBox) return;

  criticalBox.innerHTML = '';

  if (data.critical?.length) {

    data.critical.forEach(item => {
      const pill = document.createElement('div');
      pill.className = 'critical-pill';
      pill.textContent = item;
      criticalBox.appendChild(pill);
    });

  } else {

    criticalBox.innerHTML =
      '<div class="critical-pill">No critical issues</div>';
  }
}


/* -----------------------------------------
 * SMALL INTERNAL HELPER
 * ----------------------------------------- */
function setText(selector, value) {
  const el = q(selector);
  if (!el) return;

  if (value !== null && value !== undefined) {
    el.textContent = value;
  }
}
