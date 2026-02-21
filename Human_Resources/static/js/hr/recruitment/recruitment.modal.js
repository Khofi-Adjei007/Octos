/* =========================================================
   RECRUITMENT MODAL MODULE
   Opens application detail in a modal.
   Timeline and actions rendered inside.
========================================================= */

import { q } from '../core.js';
import { fetchApplicationById } from './recruitment.api.js';
import { renderTimeline } from './recruitment.timeline.js';

let modalEl = null;


/* =========================================================
   INIT MODAL
========================================================= */

export function initRecruitmentModal() {
  if (modalEl) return;

  modalEl = document.createElement('div');
  modalEl.className = 'recruitment-modal';

  modalEl.innerHTML = `
    <div class="modal-backdrop"></div>

    <div class="modal-container">

      <div class="modal-header">
        <div>
          <h3 class="modal-title" id="modal-applicant-name">Loading...</h3>
          <div class="modal-subtitle" id="modal-role"></div>
        </div>
        <button class="modal-close" id="modal-close-btn">&times;</button>
      </div>

      <div class="modal-body" id="modal-content">
        <div class="modal-loading">Loading application...</div>
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
  if (!modalEl) initRecruitmentModal();

  const content = q('#modal-content');
  content.innerHTML = `<div class="modal-loading">Loading application...</div>`;

  // Animate in
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
        Failed to load application. Please try again.
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
  const nameEl = q('#modal-applicant-name');
  const roleEl = q('#modal-role');

  nameEl.textContent = `${app?.first_name || ''} ${app?.last_name || ''}`;
  roleEl.textContent = app?.role_applied_for || '';

  content.innerHTML = `

    <div class="modal-meta-grid">
      <div class="modal-meta-item">
        <span class="meta-label">Email</span>
        <span class="meta-value">${app?.email || '—'}</span>
      </div>

      <div class="modal-meta-item">
        <span class="meta-label">Source</span>
        <span class="meta-value">${app?.source?.toUpperCase() || '—'}</span>
      </div>

      ${app?.branch_name ? `
        <div class="modal-meta-item">
          <span class="meta-label">Branch</span>
          <span class="meta-value">${app.branch_name}</span>
        </div>
      ` : ''}

      ${app?.assigned_reviewer ? `
        <div class="modal-meta-item">
          <span class="meta-label">Reviewer</span>
          <span class="meta-value">${app.assigned_reviewer}</span>
        </div>
      ` : ''}

      ${app?.interview_date ? `
        <div class="modal-meta-item">
          <span class="meta-label">Interview</span>
          <span class="meta-value">${formatDateTime(app.interview_date)}</span>
        </div>
      ` : ''}

      ${app?.resume_url ? `
        <div class="modal-meta-item">
          <span class="meta-label">Resume</span>
          <span class="meta-value">
            <a href="${app.resume_url}" target="_blank" class="resume-link">
              📄 View Resume
            </a>
          </span>
        </div>
      ` : ''}
    </div>

    <div class="modal-section">
      <h4 class="modal-section-title">Pipeline</h4>
      <div class="kanban-placeholder"></div>
    </div>

  `;

  // Wire up the timeline engine
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

    if (e.target.id === 'modal-close-btn') {
      closeRecruitmentModal();
    }

  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalEl?.classList.contains('is-open')) {
      closeRecruitmentModal();
    }
  });
}


/* =========================================================
   HELPERS
========================================================= */

function formatDateTime(datetime) {
  if (!datetime) return '—';
  return new Date(datetime).toLocaleString();
}