(() => {
  const api = '/hr/api';
  const q  = s => document.querySelector(s);
  const qa = s => Array.from(document.querySelectorAll(s));

  let context = 'overview';
  let recruitmentFilter = 'applications';

  /* -----------------------------------------
   * CONTEXT PANEL VISIBILITY
   * ----------------------------------------- */
  function showContext(target) {
    qa('.context-panel').forEach(panel => {
      panel.classList.toggle(
        'hidden',
        panel.dataset.context !== target
      );
    });
  }

  /* -----------------------------------------
   * CONTEXT SWITCHING
   * ----------------------------------------- */
  function bindContextSwitching() {
    qa('.switch-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        context = btn.dataset.context;

        qa('.switch-btn').forEach(b =>
          b.classList.toggle('active', b === btn)
        );

        showContext(context);

        if (context === 'overview') loadOverview();
        if (context === 'recruitment') loadRecruitment();
        if (context === 'employees') loadEmployees?.();
      });
    });
  }

  /* -----------------------------------------
   * OVERVIEW
   * ----------------------------------------- */
  async function loadOverview() {
    let overview;

    try {
      overview = await fetch(api + '/overview/').then(r => r.json());
    } catch {
      overview = {
        region_name: '—',
        branch_count: 0,
        total_employees: 0,
        critical: []
      };
    }

    setText('#region-name', overview.region_name);
    setText('#branch-count', overview.branch_count);
    setText('#region-employees', overview.total_employees);

    const criticalBox = q('#critical-summary');
    if (criticalBox) {
      criticalBox.innerHTML = '';

      if (overview.critical?.length) {
        overview.critical.forEach(item => {
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
  }

  /* -----------------------------------------
   * RECRUITMENT FILTERS
   * ----------------------------------------- */
  function bindRecruitmentFilters() {
    qa('.recruitment-filters .filter-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        recruitmentFilter = btn.dataset.filter;

        qa('.recruitment-filters .filter-chip')
          .forEach(b => b.classList.toggle('active', b === btn));

        loadRecruitment();
      });
    });
  }

  /* -----------------------------------------
   * RECRUITMENT LOAD
   * ----------------------------------------- */
  async function loadRecruitment() {
    const list  = q('#recruitment-items');
    const empty = q('#recruitment-empty');

    if (!list || !empty) return;

    list.innerHTML = '';
    empty.style.display = 'none';

    let applications = [];

    try {
      const res = await fetch(api + '/applications/');
      applications = await res.json();
    } catch (err) {
      empty.style.display = 'block';
      empty.textContent = 'Failed to load applications.';
      return;
    }

    const filtered =
      recruitmentFilter === 'applications'
        ? applications
        : applications.filter(a => a.status === recruitmentFilter);

    if (!filtered.length) {
      empty.style.display = 'block';
      empty.textContent = 'No applications found.';
      return;
    }

    filtered.forEach(app => {

      const appliedDate = new Date(app.created_at);
      const now = new Date();
      const diffHours = Math.floor((now - appliedDate) / (1000 * 60 * 60));
      const diffDays = Math.floor(diffHours / 24);

      let appliedText;
      if (diffHours < 24) {
        appliedText =
          diffHours <= 1
            ? "Applied 1 hour ago"
            : `Applied ${diffHours} hours ago`;
      } else {
        appliedText =
          diffDays === 1
            ? "Applied 1 day ago"
            : `Applied ${diffDays} days ago`;
      }

      const card = document.createElement('div');
      card.className = 'application-card';
      card.dataset.id = app.id;

     card.innerHTML = `
  <div class="application-card-header">
    <div>
      <div class="application-name">
        ${app.first_name.toUpperCase()} ${app.last_name.toUpperCase()}
      </div>
      <div class="application-role">
        ${app.role_applied_for}
      </div>
    </div>

    <div class="status-pill status-${app.status}">
      ${app.status.toUpperCase()}
    </div>
  </div>

  <div class="application-details">
    <div><strong>Email:</strong> ${app.email || '—'}</div>

    ${app.branch_name ? `
      <div><strong>Branch:</strong> ${app.branch_name}</div>
    ` : ''}

    <!-- SOURCE + RESUME SIDE BY SIDE -->
    <div class="card-meta-row">
      <span class="source-badge source-${app.source}">
        ${app.source.toUpperCase()}
      </span>

      ${
        app.resume_url
          ? `
            <span class="resume-badge">
              📄 Resume Attached
            </span>
          `
          : ''
      }
    </div>

    ${app.recommender_name ? `
      <div>
        <strong>Recommended by:</strong>
        ${app.recommender_name}
        ${app.recommender_branch ? ` (${app.recommender_branch})` : ''}
      </div>
    ` : ''}
  </div>

  <div class="application-footer">
    <div class="application-applied">
      ${appliedText}
    </div>

    <button class="btn-review" data-id="${app.id}">
      Review
    </button>
  </div>
`;


      list.appendChild(card);
    });
  }

  /* -----------------------------------------
   * HELPERS
   * ----------------------------------------- */
  function setText(selector, value) {
    const el = q(selector);
    if (el) el.textContent = value;
  }

  function getCSRF() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
  }

  /* -----------------------------------------
   * INIT
   * ----------------------------------------- */
  document.addEventListener('DOMContentLoaded', () => {
    bindContextSwitching();
    bindRecruitmentFilters();
    showContext('overview');
    loadOverview();
  });

})();
