/* =========================================================
   EMPLOYEES MODULE
   Renders employee list, handles filters, approval, and role assignment
========================================================= */

const CSRF = () => document.cookie.match(/csrftoken=([^;]+)/)?.[1] || "";

let allEmployees = [];
let currentFilter = "all";
let roleOptions = { roles: [], branches: [], regions: [] };


/* -----------------------------------------
 * BOOT
 * ----------------------------------------- */
export async function loadEmployees() {
  await Promise.all([fetchRoleOptions(), fetchAndRender()]);
  bindFilters();
}


/* -----------------------------------------
 * FETCH
 * ----------------------------------------- */
async function fetchAndRender() {
  try {
    const res = await fetch("/hr/api/employees/");
    allEmployees = await res.json();
    updateFilterCounts(allEmployees);
    renderEmployees(applyFilter(allEmployees));
  } catch (e) {
    console.error("Failed to load employees:", e);
  }
}

async function fetchRoleOptions() {
  try {
    const res = await fetch("/hr/api/employees/role-options/");
    roleOptions = await res.json();
  } catch (e) {
    console.error("Failed to load role options:", e);
  }
}


/* -----------------------------------------
 * FILTER
 * ----------------------------------------- */
function applyFilter(employees) {
  switch (currentFilter) {
    case "active":     return employees.filter(e => e.is_active && e.approved);
    case "inactive":   return employees.filter(e => !e.is_active);
    case "pending":    return employees.filter(e => !e.approved);
    case "unassigned": return employees.filter(e => !e.has_assignment);
    default:           return employees;
  }
}

function updateFilterCounts(employees) {
  const counts = {
    all:        employees.length,
    active:     employees.filter(e => e.is_active && e.approved).length,
    inactive:   employees.filter(e => !e.is_active).length,
    pending:    employees.filter(e => !e.approved).length,
    unassigned: employees.filter(e => !e.has_assignment).length,
  };

  document.querySelectorAll(".employees-filters .filter-chip").forEach(btn => {
    const filter = btn.dataset.filter;
    const count  = counts[filter] ?? 0;
    if (!btn.dataset.label) btn.dataset.label = btn.textContent.trim();
    btn.innerHTML = `${btn.dataset.label} <span class="chip-count">${count}</span>`;
  });
}

function bindFilters() {
  document.querySelectorAll(".employees-filters .filter-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      currentFilter = btn.dataset.filter;
      document.querySelectorAll(".employees-filters .filter-chip")
        .forEach(b => b.classList.toggle("active", b === btn));
      renderEmployees(applyFilter(allEmployees));
    });
  });
}


/* -----------------------------------------
 * RENDER
 * ----------------------------------------- */
function renderEmployees(employees) {
  const container = document.getElementById("employees-list-items");
  const empty     = document.getElementById("employees-empty");
  if (!container) return;
  container.innerHTML = "";
  if (employees.length === 0) {
    empty.classList.remove("hidden");
    return;
  }
  empty.classList.add("hidden");
  employees.forEach(e => container.appendChild(buildEmployeeCard(e)));
}

function buildEmployeeCard(e) {
  const card = document.createElement("div");
  card.className = "employee-card";
  card.dataset.id = e.id;

  const statusBadge = e.approved
    ? e.is_active
      ? `<span class="badge status-active">Active</span>`
      : `<span class="badge status-inactive">Inactive</span>`
    : `<span class="badge status-pending">Pending Approval</span>`;

  const roleBadge = e.authority_role
    ? `<span class="badge role-badge">${e.authority_role}</span>`
    : `<span class="badge role-unassigned">No Role</span>`;

  const approveBtn = !e.approved
    ? `<button class="btn-approve" data-id="${e.id}">
         <i class="ri-shield-check-line"></i> Approve
       </button>`
    : "";

  const assignRoleBtn = `
    <button class="btn-assign-role" data-id="${e.id}">
      <i class="ri-user-settings-line"></i> Assign Role
    </button>`;

  card.innerHTML = `
    <div class="employee-card-left">
      <div class="employee-avatar">
        ${e.first_name.charAt(0)}${e.last_name.charAt(0)}
      </div>
      <div class="employee-info">
        <div class="employee-name">${e.first_name} ${e.last_name}</div>
        <div class="employee-meta">
          ${e.position_title || "—"}
          ${e.branch ? ` · <span class="employee-branch">${e.branch}</span>` : ""}
        </div>
        ${e.employee_email ? `<div class="employee-email">${e.employee_email}</div>` : ""}
        <div class="employee-role-row">${roleBadge}</div>
      </div>
    </div>
    <div class="employee-card-right">
      ${statusBadge}
      <div class="employee-actions">
        ${approveBtn}
        ${assignRoleBtn}
      </div>
    </div>
  `;

  const approveButton = card.querySelector(".btn-approve");
  if (approveButton) {
    approveButton.addEventListener("click", () => approveEmployee(e.id, card));
  }

  const assignButton = card.querySelector(".btn-assign-role");
  if (assignButton) {
    assignButton.addEventListener("click", () => openAssignRoleModal(e));
  }

  return card;
}


/* -----------------------------------------
 * APPROVE
 * ----------------------------------------- */
async function approveEmployee(id, card) {
  const btn = card.querySelector(".btn-approve");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<i class="ri-loader-4-line"></i> Approving...`;
  }

  try {
    const res = await fetch(`/hr/api/employees/${id}/approve/`, {
      method: "POST",
      headers: { "X-CSRFToken": CSRF(), "Content-Type": "application/json" },
    });
    const data = await res.json();
    if (data.success) {
      showToast("Employee approved successfully.", "success");
      await fetchAndRender();
    } else {
      showToast(data.error || "Approval failed.", "error");
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<i class="ri-shield-check-line"></i> Approve`;
      }
    }
  } catch (e) {
    console.error("Approve error:", e);
    showToast("Something went wrong.", "error");
  }
}


/* -----------------------------------------
 * ASSIGN ROLE MODAL
 * ----------------------------------------- */
function openAssignRoleModal(employee) {
  // Remove existing modal if any
  document.getElementById("assign-role-modal")?.remove();

  const modal = document.createElement("div");
  modal.id = "assign-role-modal";
  modal.className = "modal-overlay";

  const roleOptions_html = roleOptions.roles.map(r =>
    `<option value="${r.id}" data-scopes='${JSON.stringify(r.allowed_scopes)}'>${r.name}</option>`
  ).join("");

  const branchOptions_html = roleOptions.branches.map(b =>
    `<option value="${b.id}">${b.name}</option>`
  ).join("");

  const regionOptions_html = roleOptions.regions.map(r =>
    `<option value="${r.id}">${r.name}</option>`
  ).join("");

  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3>Assign Role</h3>
        <button class="modal-close" id="close-assign-modal">✕</button>
      </div>
      <div class="modal-body">
        <p class="modal-employee-name">${employee.first_name} ${employee.last_name}</p>
        ${employee.authority_role
          ? `<p class="modal-current-role">Current role: <strong>${employee.authority_role}</strong></p>`
          : `<p class="modal-current-role no-role">No role assigned yet</p>`}

        <div class="form-group">
          <label>Authority Role</label>
          <select id="modal-role-select">
            <option value="">— Select role —</option>
            ${roleOptions_html}
          </select>
        </div>

        <div class="form-group" id="scope-type-group" style="display:none">
          <label>Scope Type</label>
          <select id="modal-scope-select">
            <option value="">— Select scope —</option>
          </select>
        </div>

        <div class="form-group" id="branch-group" style="display:none">
          <label>Branch</label>
          <select id="modal-branch-select">
            <option value="">— Select branch —</option>
            ${branchOptions_html}
          </select>
        </div>

        <div class="form-group" id="region-group" style="display:none">
          <label>Region</label>
          <select id="modal-region-select">
            <option value="">— Select region —</option>
            ${regionOptions_html}
          </select>
        </div>

        <div id="modal-error" class="modal-error hidden"></div>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" id="cancel-assign-modal">Cancel</button>
        <button class="btn-primary" id="confirm-assign-role" data-id="${employee.id}">
          Assign Role
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // Close handlers
  document.getElementById("close-assign-modal").addEventListener("click", () => modal.remove());
  document.getElementById("cancel-assign-modal").addEventListener("click", () => modal.remove());
  modal.addEventListener("click", (e) => { if (e.target === modal) modal.remove(); });

  // Role select → show scope options
  document.getElementById("modal-role-select").addEventListener("change", function () {
    const selected = this.options[this.selectedIndex];
    const scopes = JSON.parse(selected.dataset.scopes || "[]");

    const scopeSelect = document.getElementById("modal-scope-select");
    scopeSelect.innerHTML = `<option value="">— Select scope —</option>` +
      scopes.map(s => `<option value="${s}">${s}</option>`).join("");

    document.getElementById("scope-type-group").style.display = scopes.length ? "block" : "none";
    document.getElementById("branch-group").style.display = "none";
    document.getElementById("region-group").style.display = "none";
  });

  // Scope select → show branch or region
  document.getElementById("modal-scope-select").addEventListener("change", function () {
    const scope = this.value;
    document.getElementById("branch-group").style.display = scope === "BRANCH" ? "block" : "none";
    document.getElementById("region-group").style.display = scope === "REGION" ? "block" : "none";
  });

  // Confirm
  document.getElementById("confirm-assign-role").addEventListener("click", () => {
    submitAssignRole(employee.id);
  });
}

async function submitAssignRole(employeeId) {
  const roleId    = document.getElementById("modal-role-select").value;
  const scopeType = document.getElementById("modal-scope-select").value;
  const branchId  = document.getElementById("modal-branch-select").value;
  const regionId  = document.getElementById("modal-region-select").value;
  const errorDiv  = document.getElementById("modal-error");
  const confirmBtn = document.getElementById("confirm-assign-role");

  errorDiv.classList.add("hidden");

  if (!roleId || !scopeType) {
    errorDiv.textContent = "Please select a role and scope type.";
    errorDiv.classList.remove("hidden");
    return;
  }

  confirmBtn.disabled = true;
  confirmBtn.textContent = "Assigning...";

  try {
    const res = await fetch(`/hr/api/employees/${employeeId}/assign-role/`, {
      method: "POST",
      headers: { "X-CSRFToken": CSRF(), "Content-Type": "application/json" },
      body: JSON.stringify({ role_id: roleId, scope_type: scopeType, branch_id: branchId, region_id: regionId }),
    });

    const data = await res.json();

    if (data.success) {
      document.getElementById("assign-role-modal")?.remove();
      showToast(`Role '${data.role}' assigned successfully.`, "success");
      await fetchAndRender();
    } else {
      errorDiv.textContent = data.error || "Assignment failed.";
      errorDiv.classList.remove("hidden");
      confirmBtn.disabled = false;
      confirmBtn.textContent = "Assign Role";
    }
  } catch (e) {
    console.error("Assign role error:", e);
    errorDiv.textContent = "Something went wrong.";
    errorDiv.classList.remove("hidden");
    confirmBtn.disabled = false;
    confirmBtn.textContent = "Assign Role";
  }
}


/* -----------------------------------------
 * TOAST
 * ----------------------------------------- */
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.classList.add("toast-visible"), 10);
  setTimeout(() => {
    toast.classList.remove("toast-visible");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}