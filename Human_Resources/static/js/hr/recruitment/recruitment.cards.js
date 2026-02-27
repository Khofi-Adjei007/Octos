/* =========================================================
   RECRUITMENT CARDS
   Clean card style — reference design mapped precisely
========================================================= */

export function buildApplicationCard(app) {

  const stage = String(app?.current_stage || app?.status || 'submitted').toLowerCase();

  const card = document.createElement('div');
  card.className = `application-card stage-${stage}`;
  card.dataset.id = app?.id ?? '';
  card.dataset.stage = stage;

  const firstName   = app?.first_name || '';
  const lastName    = app?.last_name  || '';
  const role        = app?.role_applied_for || '—';
  const email       = app?.email || '—';
  const phone       = app?.phone || '—';
  const source      = app?.source ? app.source.toUpperCase() : '—';
  const appliedText = formatAppliedTime(app?.created_at);
  const stageLabel  = stage.replace(/_/g, ' ').toUpperCase();

  const isHighPriority   = app?.priority === 'high';
  const isRecommendation = app?.source === 'recommendation';

  // Recommended-by strip — only shown for recommendations with recommender data
  const recommendedBy     = app?.recommender_name || null;
  const recommendedBranch = app?.recommender_branch || null;
  const recommendedByLine = (isRecommendation && recommendedBy) ? `
    <div class="card-recommended-by">
      <span class="card-rec-icon">👤</span>
      <span class="card-rec-text">
        Recommended by <strong>${recommendedBy}</strong>${recommendedBranch ? ` · ${recommendedBranch}` : ''}
      </span>
    </div>
  ` : '';

  const showInterviewer = ['interview', 'final_review', 'decision'].includes(stage);
  const showInterview   = app?.interview_date && showInterviewer;

  card.innerHTML = `

    <!-- Line 1: Stage pill · time ago · priority badge -->
    <div class="card-line1">
      <span class="card-stage-pill stage-pill-${stage}">${stageLabel}</span>
      <span class="card-dot">·</span>
      <span class="card-time">${appliedText}</span>
      ${isHighPriority ? `<span class="card-priority-badge">⭐ Priority</span>` : ''}
    </div>

    <!-- Applicant name -->
    <div class="card-name">${firstName} ${lastName}</div>

    <!-- Role -->
    <div class="card-role-label">
      Role Applied
      <span class="card-role-link">· ${role}</span>
    </div>

    <!-- Recommended-by strip (recommendations only) -->
    ${recommendedByLine}

    <!-- Separator -->
    <div class="card-sep"></div>

    <!-- Info grid — 2 columns, logically paired -->
    <div class="card-info-grid">

      <div class="card-info-cell">
        <span class="card-info-icon">✉️</span>
        <span class="card-info-text">${email}</span>
      </div>

      <div class="card-info-cell">
        <span class="card-info-icon">📞</span>
        <span class="card-info-text">${phone}</span>
      </div>

      <div class="card-info-cell">
        <span class="card-info-icon">🌐</span>
        <span class="card-info-text">${source}</span>
      </div>

      ${showInterviewer && app?.assigned_reviewer ? `
      <div class="card-info-cell">
        <span class="card-info-icon">👤</span>
        <span class="card-info-text">${app.assigned_reviewer}</span>
      </div>
      ` : `<div class="card-info-cell"></div>`}

      ${showInterview ? `
      <div class="card-info-cell">
        <span class="card-info-icon">🗓️</span>
        <span class="card-info-text">${formatDateTime(app.interview_date)}</span>
      </div>
      ` : ''}

    </div>

    <!-- Separator -->
    <div class="card-sep"></div>

    <!-- Action block: resume + review -->
    <div class="card-action-block">
      <div class="card-resume-indicator ${app?.resume_url ? 'has-resume' : 'no-resume'}">
        <span class="card-resume-icon">${app?.resume_url ? '🔗' : '⚠️'}</span>
        <div class="card-resume-text">
          <span class="card-resume-title">${app?.resume_url ? 'Resume' : 'No Resume'}</span>
          <span class="card-resume-sub">${app?.resume_url ? 'Attached' : 'Not uploaded'}</span>
        </div>
      </div>
      <button class="btn-review" data-id="${app?.id}">Review →</button>
    </div>

  `;

  return card;
}

/* =========================================================
   HELPERS
========================================================= */

function formatAppliedTime(createdAt) {
  if (!createdAt) return '—';
  const diff = Math.floor((Date.now() - new Date(createdAt)) / 3600000);
  const days = Math.floor(diff / 24);
  if (diff < 1)   return 'Just now';
  if (diff < 24)  return `${diff}h ago`;
  if (days === 1) return '1 day ago';
  return `${days} days ago`;
}

function formatDateTime(datetime) {
  if (!datetime) return '—';
  return new Date(datetime).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}