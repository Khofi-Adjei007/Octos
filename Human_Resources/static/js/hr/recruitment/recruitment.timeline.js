/* =========================================================
   RECRUITMENT TIMELINE ENGINE
   Forward-only progression
   Rejected always accessible
   Onboarded + Rejected are terminal
========================================================= */

import { updateApplicationStage } from './recruitment.api.js';

const STAGES = [
  'submitted',
  'screening',
  'interview',
  'final_review',
  'offer',
  'onboarded'
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
      ${buildRejectNode(app.current_stage)}
    </div>

    <div class="timeline-actions">
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

  let statusClass = '';

  if (stageIndex < currentIndex) statusClass = 'completed';
  if (stageIndex === currentIndex) statusClass = 'active';
  if (stageIndex > currentIndex) statusClass = 'upcoming';

  return `
    <div class="timeline-node ${statusClass}" data-stage="${stage}">
      ${stage.replace('_', ' ')}
    </div>
  `;
}


/* =========================================================
   REJECT NODE
========================================================= */

function buildRejectNode(currentStage) {

  if (currentStage === 'rejected') {
    return `
      <div class="timeline-node rejected active">
        Rejected
      </div>
    `;
  }

  return `
    <div class="timeline-node reject-node" data-stage="rejected">
      Reject
    </div>
  `;
}


/* =========================================================
   ACTION CONTROLS
========================================================= */

function buildActionControls(app) {

  if (isTerminal(app.current_stage)) {
    return `
      <div class="timeline-locked">
        This application is closed.
      </div>
    `;
  }

  const currentIndex = STAGES.indexOf(app.current_stage);
  const nextStage = STAGES[currentIndex + 1];

  return `
    <button class="timeline-next" data-stage="${nextStage}">
      Move to ${formatStage(nextStage)}
    </button>

    <button class="timeline-reject" data-stage="rejected">
      Reject Application
    </button>
  `;
}


/* =========================================================
   EVENT BINDING
========================================================= */

function bindTimelineEvents() {

  const nextBtn = document.querySelector('.timeline-next');
  const rejectBtn = document.querySelector('.timeline-reject');

  if (nextBtn) {
    nextBtn.addEventListener('click', async () => {
      await transitionStage(nextBtn.dataset.stage);
    });
  }

  if (rejectBtn) {
    rejectBtn.addEventListener('click', async () => {
      await transitionStage('rejected');
    });
  }
}


/* =========================================================
   TRANSITION LOGIC
========================================================= */

async function transitionStage(newStage) {

  if (!currentApplication) return;

  try {

    const updated = await updateApplicationStage(
      currentApplication.id,
      newStage
    );

    currentApplication = updated;

    renderTimeline(updated);

  } catch (err) {
    alert('Failed to update stage.');
  }
}


/* =========================================================
   HELPERS
========================================================= */

function isTerminal(stage) {
  return stage === 'onboarded' || stage === 'rejected';
}

function formatStage(stage) {
  if (!stage) return '';
  return stage.replace('_', ' ');
}
