export function buildApplicationCard(app) {

  const stage = String(app?.current_stage || app?.status || 'submitted')
    .toLowerCase();

  const card = document.createElement('div');

  // Stage class drives left accent bar
  card.className = `application-card stage-${stage}`;
  card.dataset.id = app?.id ?? '';
  card.dataset.stage = stage;
  card.dataset.priority = app?.priority || 'normal';
  card.dataset.new = app?.is_new ? 'true' : 'false';

  const firstName = String(app?.first_name || '').toUpperCase();
  const lastName  = String(app?.last_name || '').toUpperCase();
  const role      = app?.role_applied_for || '—';
  const email     = app?.email || '—';

  // SAFE CLASS NORMALIZATION
  const sourceRaw = app?.source ? String(app.source) : null;
  const sourceClass = sourceRaw
    ? `source-${sourceRaw.toLowerCase().replace(/\s+/g, '-')}`
    : null;

  const sourceLabel = sourceRaw ? sourceRaw.toUpperCase() : null;

  const priorityRaw = app?.priority && app.priority !== 'normal'
    ? String(app.priority)
    : null;

  const priorityClass = priorityRaw
    ? `priority-${priorityRaw.toLowerCase().replace(/\s+/g, '-')}`
    : null;

  const priorityLabel = priorityRaw
    ? priorityRaw.toUpperCase()
    : null;

  const appliedText = formatAppliedTime(app?.created_at);

  card.innerHTML = `
    <div class="card-accent"></div>

    <div class="application-card-header">
      <div>
        <div class="application-name">
          ${firstName} ${lastName}
        </div>

        <div class="application-role">
          ${role}
        </div>
      </div>

      <span class="badge status-${stage}">
        ${stage.replace(/_/g, ' ').toUpperCase()}
      </span>
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

      <div style="margin-top:6px; display:flex; gap:6px; flex-wrap:wrap;">
        ${sourceClass ? `
          <span class="badge ${sourceClass}">
            ${sourceLabel}
          </span>
        ` : ''}

        ${app?.resume_url ? `
          <span class="badge">
            📄 RESUME
          </span>
        ` : ''}

        ${priorityClass ? `
          <span class="badge ${priorityClass}">
            ${priorityLabel}
          </span>
        ` : ''}
      </div>

      ${app?.recommender_name ? `
        <div style="margin-top:6px;">
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
