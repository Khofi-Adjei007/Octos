const GRADIENTS = [
  'gradient-green',
  'gradient-blue',
  'gradient-purple',
  'gradient-orange',
  'gradient-red',
  'gradient-teal'
];

function getGradientFromId(branchId) {
  return GRADIENTS[branchId % GRADIENTS.length];
}

export function applyBranchGradients() {
  const cards = document.querySelectorAll('.branch-card');
  if (!cards.length) return;

  cards.forEach((card) => {
    const branchId = parseInt(card.dataset.branchId, 10);
    if (isNaN(branchId)) return;

    const gradientClass = getGradientFromId(branchId);
    card.classList.remove(...GRADIENTS);
    card.classList.add(gradientClass);
  });
}


document.addEventListener("DOMContentLoaded", () => {
  loadBranches();
});


async function loadBranches() {
  const grid = document.getElementById("branchesGrid");
  if (!grid) return;

  grid.innerHTML = `<div class="text-gray-400">Loading branches...</div>`;

  try {
    const response = await fetch("/hr/api/branches/");
    const data = await response.json();

    grid.innerHTML = "";

    if (!data.branches || data.branches.length === 0) {
      grid.innerHTML = `<div>No branches found for this region.</div>`;
      return;
    }

    data.branches.forEach(branch => {
      grid.insertAdjacentHTML("beforeend", buildBranchCard(branch));
    });

    applyBranchGradients();

  } catch (error) {
    console.error("Branch load error:", error);
    grid.innerHTML = `<div>Failed to load branches.</div>`;
  }
}


function buildBranchCard(branch) {

  // You can later compute health dynamically
  const healthLabel = "Stable";

  return `
    <div class="branch-card"
         data-branch-id="${branch.id}">

      <!-- Header -->
<div class="branch-header">
  <div class="branch-title-group">
    <h3>${branch.name}</h3>

    <div class="branch-sub-row">
      <span class="branch-code">${branch.code}</span>
      <span class="health-badge stable">
        Stable
      </span>
    </div>
  </div>
</div>


      <!-- Meta Grid -->
      <div class="branch-meta-grid">

        <div class="meta-item">
          <span class="meta-label">Manager</span>
          <strong>${branch.manager}</strong>
        </div>

        <div class="meta-item">
          <span class="meta-label">Active Since</span>
          <strong>${branch.active_since ?? "-"}</strong>
        </div>

        <div class="meta-item">
          <span class="meta-label">Distance</span>
          <strong>${branch.distance_from_hq ?? "-"} km</strong>
        </div>

      </div>

      <!-- Metrics -->
      <div class="branch-metrics">
        <div class="metric-box">
          <span>Total</span>
          <strong>${branch.total_employees}</strong>
        </div>

        <div class="metric-box">
          <span>Active</span>
          <strong>${branch.active_employees}</strong>
        </div>

        <div class="metric-box">
          <span>Open Roles</span>
          <strong>${branch.open_roles}</strong>
        </div>
      </div>

      <!-- Trend -->
      <div class="branch-trend">
        ${branch.trend ?? ""}
      </div>

      <!-- Actions -->
      <div class="branch-actions">
        <button class="branch-btn">
          <i class="ri-bar-chart-line"></i>
          Analytics
        </button>

        <button class="branch-btn secondary">
          <i class="ri-group-line"></i>
          Employees
        </button>
      </div>

    </div>
  `;
}
