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
   * CONTEXT SWITCHING (TABS)
   * ----------------------------------------- */
  function bindContextSwitching() {
    qa('.switch-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        context = btn.dataset.context;

        // Toggle active tab
        qa('.switch-btn').forEach(b =>
          b.classList.toggle('active', b === btn)
        );

        // Show correct panel
        showContext(context);

        // Load context data
        if (context === 'overview') {
          loadOverview();
        }

        if (context === 'recruitment') {
          loadRecruitment();
        }

        if (context === 'employees') {
          loadEmployees?.(); // safe call (future)
        }
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
   * RECRUITMENT
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

  async function loadRecruitment() {
  const list  = q('.recruitment-items');
  const empty = q('#recruitment-empty');

  if (!list || !empty) return;

  // Reset UI
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

  // Filter logic
  const filtered =
    recruitmentFilter === 'applications'
      ? applications
      : applications.filter(a => a.status === recruitmentFilter);

  // Empty state
  if (!filtered.length) {
    empty.style.display = 'block';
    empty.textContent = 'No applications found.';
    return;
  }

  // Render rows
  filtered.forEach(app => {
    const row = document.createElement('div');
    row.className = 'application-row';

    row.innerHTML = `
      <div class="application-main">
        <strong class="application-name">
          ${app.first_name} ${app.last_name}
        </strong>
        <span class="application-meta">
          ${app.recommended_role || '—'} • ${app.email || '—'}
        </span>
      </div>

      <div class="application-actions">
        ${
          app.status === 'pending'
            ? `
              <button class="btn-approve">Approve</button>
              <button class="btn-reject">Reject</button>
            `
            : `<span class="status-pill status-${app.status}">
                 ${app.status}
               </span>`
        }
      </div>
    `;

    list.appendChild(row);
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
