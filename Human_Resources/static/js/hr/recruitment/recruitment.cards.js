/* =========================================================
   RECRUITMENT CARD RENDERER
   Transforms application data → DOM element
   (Defensive / Safe Version)
========================================================= */

export function buildApplicationCard(app) {

  const card = document.createElement('div');
  card.className = 'application-card';
  card.dataset.id = app?.id ?? '';
  card.dataset.stage = app?.current_stage || app?.status || 'submitted';
  card.dataset.priority = app?.priority || 'normal';
  card.dataset.new = app?.is_new ? 'true' : 'false';

  /* -----------------------------------------
   * SAFE NORMALIZATION
   * ----------------------------------------- */
  const stage = String(app?.current_stage || app?.status || 'submitted')
    .toLowerCase();

  const firstName = String(app?.first_name || '').toUpperCase();
  const lastName  = String(app?.last_name || '').toUpperCase();
  const role      = app?.role_applied_for || '—';
  const email     = app?.email || '—';
  const source    = app?.source ? String(app.source).toUpperCase() : null;
  const priority  = app?.priority && app.priority !== 'normal'
    ? String(app.priority).toUpperCase()
    : null;

  const appliedText = formatAppliedTime(app?.created_at);

  /* -----------------------------------------
   * BUILD CARD
   * ----------------------------------------- */
  card.innerHTML = `
    <div class="application-card-header">

      <div>
        <div class="application-name">
          ${firstName} ${lastName}
          ${app?.is_new ? `<span class="badge-new">NEW</span>` : ``}
        </div>

        <div class="application-role">
          ${role}
        </div>
      </div>

      <div class="status-pill stage-${stage}">
        ${stage.replace('_', ' ').toUpperCase()}
      </div>
    </div>

    <div class="application-details">
      <div><strong>Email:</strong> ${email}</div>

      ${app?.branch_name ? `
        <div><strong>Branch:</strong> ${app.branch_name}</div>
      ` : ''}

      ${app?.assigned_reviewer ? `
        <div><strong>Reviewer:</strong> ${app.assigned_reviewer}</div>
      ` : ''}

      ${app?.interview_date ? `
        <div><strong>Interview:</strong> ${formatDateTime(app.interview_date)}</div>
      ` : ''}

      <div class="card-meta-row">
        ${source ? `
          <span class="source-badge source-${app.source}">
            ${source}
          </span>
        ` : ''}

        ${
          app?.resume_url
            ? `<span class="resume-badge">📄 Resume</span>`
            : ''
        }

        ${priority ? `
          <span class="priority-badge priority-${app.priority}">
            ${priority}
          </span>
        ` : ''}
      </div>

      ${app?.recommender_name ? `
        <div>
          <strong>Recommended by:</strong>
          ${app.recommender_name}
          ${app?.recommender_branch ? ` (${app.recommender_branch})` : ''}
        </div>
      ` : ''}
    </div>

    <div class="application-footer">
      <div class="application-applied">
        ${appliedText}
      </div>

      <button class="btn-review" data-id="${app?.id}">
        Review
      </button>
    </div>
  `;

  return card;
}


/* =========================================================
   INTERNAL HELPERS
========================================================= */

function formatAppliedTime(createdAt) {

  if (!createdAt) return '—';

  const appliedDate = new Date(createdAt);
  const now = new Date();

  const diffHours = Math.floor((now - appliedDate) / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);

  if (diffHours < 24) {
    return diffHours <= 1
      ? 'Applied 1 hour ago'
      : `Applied ${diffHours} hours ago`;
  }

  return diffDays === 1
    ? 'Applied 1 day ago'
    : `Applied ${diffDays} days ago`;
}


function formatDateTime(datetime) {
  if (!datetime) return '—';
  return new Date(datetime).toLocaleString();
}
