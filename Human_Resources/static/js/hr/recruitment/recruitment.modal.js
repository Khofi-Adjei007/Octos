/* =========================================================
   RECRUITMENT MODAL MODULE
   Animated Version + Timeline Integrated
========================================================= */

import { q } from '../core.js';
import { fetchApplicationById } from './recruitment.api.js';
import { renderTimeline } from './recruitment.timeline.js';

let modalEl = null;


/* =========================================================
   INIT MODAL
========================================================= */

export function initRecruitmentModal() {

  if (modalEl) return; // Prevent double initialization

  modalEl = document.createElement('div');
  modalEl.className = 'recruitment-modal';

  modalEl.innerHTML = `
    <div class="modal-backdrop"></div>

    <div class="modal-container">
      <div class="modal-header">
        <div>
          <h3 class="modal-title">Application Review</h3>
          <div class="modal-subtitle" id="modal-role"></div>
        </div>

        <button class="modal-close">&times;</button>
      </div>

      <div class="modal-body" id="modal-content">
        <div class="modal-loading">
          Loading application...
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modalEl);

  bindModalEvents();
}


/* =========================================================
   OPEN MODAL
========================================================= */

export async function openRecruitmentModal(id) {

  if (!modalEl) return;

  const content = q('#modal-content');
  content.innerHTML = `<div class="modal-loading">Loading application...</div>`;

  // Trigger animation smoothly
  requestAnimationFrame(() => {
    modalEl.classList.add('is-open');
  });

  document.body.classList.add('modal-open');

  try {
    const app = await fetchApplicationById(id);
    renderModalContent(app);
  } catch {
    content.innerHTML = `
      <div class="modal-error">
        Failed to load application.
      </div>
    `;
  }
}


/* =========================================================
   CLOSE MODAL
========================================================= */

export function closeRecruitmentModal() {

  if (!modalEl) return;

  modalEl.classList.remove('is-open');
  document.body.classList.remove('modal-open');
}


/* =========================================================
   RENDER CONTENT
========================================================= */

function renderModalContent(app) {

  const content = q('#modal-content');
  const roleEl = q('#modal-role');

  roleEl.textContent = app?.role_applied_for || '';

  content.innerHTML = `
    <div class="modal-grid">

      <div>
        <strong>Name:</strong>
        ${app?.first_name || ''} ${app?.last_name || ''}
      </div>

      <div>
        <strong>Email:</strong>
        ${app?.email || '—'}
      </div>

      <div>
        <strong>Current Stage:</strong>
        ${formatStage(app?.current_stage || app?.status || 'submitted')}
      </div>

      ${app?.resume_url ? `
        <div>
          <strong>Resume:</strong>
          <a href="${app.resume_url}" target="_blank">View Resume</a>
        </div>
      ` : ''}

    </div>

    <div class="modal-section">
      <h4>Workflow Progression</h4>
      <div class="kanban-placeholder"></div>
    </div>
  `;

  // Render the stage timeline engine
  renderTimeline(app);
}


/* =========================================================
   EVENTS
========================================================= */

function bindModalEvents() {

  modalEl.addEventListener('click', (e) => {

    if (e.target.classList.contains('modal-backdrop')) {
      closeRecruitmentModal();
    }

    if (e.target.classList.contains('modal-close')) {
      closeRecruitmentModal();
    }

  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalEl.classList.contains('is-open')) {
      closeRecruitmentModal();
    }
  });
}


/* =========================================================
   HELPERS
========================================================= */

function formatStage(stage) {
  if (!stage) return '';
  return stage.replace('_', ' ');
}
