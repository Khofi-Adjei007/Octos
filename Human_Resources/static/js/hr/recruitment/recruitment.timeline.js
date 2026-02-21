/* =========================================================
   RECRUITMENT TIMELINE ENGINE
   Synced with RecruitmentEngine backend.
   All transitions go through performTransition().
========================================================= */

import { performTransition, finalizeEvaluation } from './recruitment.api.js';

// Must match backend RecruitmentStage exactly
const STAGES = [
  'submitted',
  'screening',
  'interview',
  'final_review',
  'decision',
];

// Maps each stage to the action that moves forward from it
const STAGE_ACTION_MAP = {
  'submitted':    'start_screening',
  'screening':    'schedule_interview',
  'interview':    'complete_interview',
  'final_review': 'submit_final_review',
  'decision':     'approve',
};

// Terminal statuses
const TERMINAL_STATUSES = [
  'hire_approved',
  'rejected',
  'withdrawn',
  'closed',
];

let currentApplication = null;


/* =========================================================
   PUBLIC ENTRY
========================================================= */

export function renderTimeline(app) {
  currentApplication = app;

  const container = document.querySelector('.kanban-placeholder');
  if (!container) return;

  container.innerHTML = `
    <div class="timeline-bar">
      ${STAGES.map(stage => buildStageNode(stage, app.current_stage)).join('')}
    </div>
    <div class="timeline-actions" id="timeline-actions">
      ${buildActionControls(app)}
    </div>
  `;

  bindTimelineEvents();
}


/* =========================================================
   STAGE NODE BUILDER
========================================================= */

function buildStageNode(stage, currentStage) {
  const currentIndex = STAGES.indexOf(currentStage);
  const stageIndex = STAGES.indexOf(stage);

  let statusClass = 'upcoming';
  if (stageIndex < currentIndex) statusClass = 'completed';
  if (stageIndex === currentIndex) statusClass = 'active';

  const label = stage.replace(/_/g, ' ').toUpperCase();

  return `
    <div class="timeline-node ${statusClass}" data-stage="${stage}">
      ${label}
    </div>
  `;
}


/* =========================================================
   ACTION CONTROLS
   Built dynamically based on current stage and status
========================================================= */

function buildActionControls(app) {
  const stage = app.current_stage;
  const status = app.status;

  // Already terminal
  if (TERMINAL_STATUSES.includes(status)) {
    return terminalMessage(status);
  }

  // Decision stage — offer/reject/withdraw options
  if (stage === 'decision') {
    if (status === 'active') {
      return `
        <button class="timeline-action btn-approve" data-action="approve">
          Extend Offer
        </button>
        <button class="timeline-action btn-reject" data-action="reject">
          Reject
        </button>
      `;
    }
    if (status === 'offer_extended') {
      return `
        <button class="timeline-action btn-approve" data-action="accept_offer">
          Accept Offer
        </button>
        <button class="timeline-action btn-reject" data-action="decline_offer">
          Decline Offer
        </button>
        <button class="timeline-action btn-withdraw" data-action="withdraw_offer">
          Withdraw Offer
        </button>
      `;
    }
  }

  // Interview stage needs date payload
  if (stage === 'screening') {
    return `
      <button class="timeline-action btn-primary" data-action="schedule_interview">
        Schedule Interview
      </button>
      <div class="interview-date-picker" id="interview-date-picker" style="display:none;">
        <input type="datetime-local" id="interview-date-input" class="date-input" />
        <button class="timeline-action btn-confirm" id="confirm-interview-date">
          Confirm Date
        </button>
      </div>
      <button class="timeline-action btn-reject" data-action="reject">
        Reject
      </button>
    `;
  }

  // All other forward stages
  const action = STAGE_ACTION_MAP[stage];
  if (!action) return '';

  const label = formatActionLabel(action);

  return `
    <button class="timeline-action btn-primary" data-action="${action}">
      ${label}
    </button>
    <button class="timeline-action btn-reject" data-action="reject">
      Reject
    </button>
  `;
}


/* =========================================================
   EVENT BINDING
========================================================= */

function bindTimelineEvents() {
  const actionsContainer = document.getElementById('timeline-actions');
  if (!actionsContainer) return;

  actionsContainer.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;

    const action = btn.dataset.action;

    // Schedule interview needs date — show picker first
    if (action === 'schedule_interview') {
      const picker = document.getElementById('interview-date-picker');
      if (picker) {
        picker.style.display = picker.style.display === 'none' ? 'flex' : 'none';
      }
      return;
    }

    await handleAction(action);
  });

  // Confirm interview date separately
  const confirmBtn = document.getElementById('confirm-interview-date');
  if (confirmBtn) {
    confirmBtn.addEventListener('click', async () => {
      const dateInput = document.getElementById('interview-date-input');
      const interviewDate = dateInput?.value;

      if (!interviewDate) {
        alert('Please select an interview date.');
        return;
      }

      await handleAction('schedule_interview', {
        interview_date: new Date(interviewDate).toISOString()
      });
    });
  }
}


/* =========================================================
   ACTION HANDLER
========================================================= */

async function handleAction(action, payload = {}) {
  if (!currentApplication) return;

  const actionsContainer = document.getElementById('timeline-actions');
  if (actionsContainer) {
    actionsContainer.innerHTML = `<div class="timeline-loading">Processing...</div>`;
  }

  try {
    const updated = await performTransition(
      currentApplication.id,
      action,
      payload
    );

    currentApplication = updated;

    // Hired — show celebratory modal
    if (updated.status === 'hire_approved') {
      renderTimeline(updated);
      showHireModal(updated);
      return;
    }

    renderTimeline(updated);

  } catch (err) {
    alert(err.message || 'Failed to perform action.');
    // Re-render to restore buttons
    renderTimeline(currentApplication);
  }
}


/* =========================================================
   CELEBRATORY HIRE MODAL
========================================================= */

function showHireModal(app) {
  // Remove existing if any
  const existing = document.getElementById('hire-modal');
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.id = 'hire-modal';
  modal.className = 'hire-modal-overlay';

  modal.innerHTML = `
    <div class="hire-modal-card">
      <div class="hire-modal-emoji">🎉</div>

      <h2 class="hire-modal-title">Congratulations!</h2>

      <p class="hire-modal-message">
        <strong>${app.first_name} ${app.last_name}</strong> has been successfully hired
        as <strong>${app.role_applied_for}</strong>.
        Their onboarding record has been created and is ready to begin.
      </p>

      <div class="hire-modal-actions">
        <button class="btn-start-onboarding" id="btn-start-onboarding">
          🚀 Start Onboarding Now
        </button>
        <button class="btn-later" id="btn-onboard-later">
          Continue Later
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // Animate in
  requestAnimationFrame(() => {
    modal.classList.add('is-open');
  });

  // Start onboarding
  document.getElementById('btn-start-onboarding').addEventListener('click', () => {
    modal.remove();
    window.location.href = `/hr/onboarding/${app.id}/`;
  });

  // Continue later
  document.getElementById('btn-onboard-later').addEventListener('click', () => {
    modal.remove();
  });

  // Close on backdrop click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.remove();
  });
}


/* =========================================================
   TERMINAL MESSAGE
========================================================= */

function terminalMessage(status) {
  const messages = {
    'hire_approved': '✅ Candidate hired. Onboarding in progress.',
    'rejected':      '❌ Application rejected.',
    'withdrawn':     '↩️ Offer withdrawn.',
    'closed':        '🔒 Application closed.',
  };

  return `
    <div class="timeline-terminal">
      ${messages[status] || 'Application closed.'}
    </div>
  `;
}


/* =========================================================
   HELPERS
========================================================= */

function formatActionLabel(action) {
  const labels = {
    'start_screening':     'Start Screening',
    'complete_interview':  'Complete Interview',
    'submit_final_review': 'Submit Final Review',
    'approve':             'Extend Offer',
    'reject':              'Reject',
    'accept_offer':        'Accept Offer',
    'decline_offer':       'Decline Offer',
    'withdraw_offer':      'Withdraw Offer',
  };
  return labels[action] || action;
}