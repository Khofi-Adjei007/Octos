/* =========================================================
   EMPLOYEES MODULE
   Renders employee list, handles filters, approval, and role assignment
========================================================= */

const CSRF = () => document.cookie.match(/csrftoken=([^;]+)/)?.[1] || "";

let allEmployees = [];
let currentFilter = "all";
let currentBranch = "";
let currentRole   = "";
let currentType   = "";
let roleOptions = { roles: [], branches: [], regions: [] };

/* -----------------------------------------
 * FILTER
 * ----------------------------------------- */
function applyFilter(employees) {
  return employees.filter(e => {
    // Status chip filter
    const statusMatch = (() => {
      switch (currentFilter) {
        case "active":     return e.is_active && e.approved;
        case "inactive":   return !e.is_active;
        case "pending":    return !e.approved;
        case "unassigned": return !e.has_assignment;
        default:           return true;
      }
    })();

    // Dropdown filters
    const branchMatch = !currentBranch || e.branch === currentBranch;
    const roleMatch   = !currentRole   || e.authority_role === currentRole;
    const typeMatch   = !currentType   || e.employee_type === currentType;

    return statusMatch && branchMatch && roleMatch && typeMatch;
  });
}

function updateFilterCounts(employees) {
  const counts = {
    all:        employees.length,
    active:     employees.filter(e => e.is_active && e.approved).length,
    inactive:   employees.filter(e => !e.is_active).length,
    pending:    employees.filter(e => !e.approved).length,
    unassigned: employees.filter(e => !e.has_assignment).length,
  };

  document.querySelectorAll(".employees-filter-chips .filter-chip").forEach(btn => {
    const filter = btn.dataset.filter;
    const count  = counts[filter] ?? 0;
    if (!btn.dataset.label) btn.dataset.label = btn.textContent.trim();
    btn.innerHTML = `${btn.dataset.label} <span class="chip-count">${count}</span>`;
  });
}

function populateDropdowns(employees) {
  // Branches
  const branches = [...new Set(employees.map(e => e.branch).filter(Boolean))].sort();
  const branchSel = document.getElementById("filter-branch");
  if (branchSel) {
    const current = branchSel.value;
    branchSel.innerHTML = `<option value="">All Branches</option>` +
      branches.map(b => `<option value="${b}" ${b === current ? "selected" : ""}>${b}</option>`).join("");
  }

  // Roles
  const roles = [...new Set(employees.map(e => e.authority_role).filter(Boolean))].sort();
  const roleSel = document.getElementById("filter-role");
  if (roleSel) {
    const current = roleSel.value;
    roleSel.innerHTML = `<option value="">All Roles</option>` +
      roles.map(r => `<option value="${r}" ${r === current ? "selected" : ""}>${r}</option>`).join("");
  }
}

function bindFilters() {
  // Status chips
  document.querySelectorAll(".employees-filter-chips .filter-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      currentFilter = btn.dataset.filter;
      document.querySelectorAll(".employees-filter-chips .filter-chip")
        .forEach(b => b.classList.toggle("active", b === btn));
      renderEmployees(applyFilter(allEmployees));
    });
  });

  // Branch dropdown
  document.getElementById("filter-branch")?.addEventListener("change", function () {
    currentBranch = this.value;
    renderEmployees(applyFilter(allEmployees));
  });

  // Role dropdown
  document.getElementById("filter-role")?.addEventListener("change", function () {
    currentRole = this.value;
    renderEmployees(applyFilter(allEmployees));
  });

  // Type dropdown
  document.getElementById("filter-type")?.addEventListener("change", function () {
    currentType = this.value;
    renderEmployees(applyFilter(allEmployees));
  });
}

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
    populateDropdowns(allEmployees);
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

  // Status color must be defined BEFORE using it
  const statusColor = e.approved
    ? e.is_active ? "#27ae60" : "#e74c3c"
    : "#f39c12";

  const statusLabel = e.approved
    ? e.is_active ? "Active" : "Inactive"
    : "Pending";

  card.style.borderLeft = `5px solid ${statusColor}`;

  const roleBadge = e.authority_role
    ? `<span class="badge role-badge">${e.authority_role}</span>`
    : `<span class="badge role-unassigned">No Role</span>`;

  const approveBtn = !e.approved
    ? `<button class="btn-approve" data-id="${e.id}">
         <i class="ri-shield-check-line"></i> Approve
       </button>`
    : "";

  card.innerHTML = `
    <div class="emp-card-avatar">
      <div class="employee-avatar">
        ${e.first_name.charAt(0)}${e.last_name.charAt(0)}
      </div>
    </div>

    <div class="emp-card-body">
      <div class="emp-card-top">
        <span class="emp-name">${e.first_name} ${e.last_name}</span>
        <span class="emp-status-badge" style="background:${statusColor}20; color:${statusColor}; border:1px solid ${statusColor}">
          ${statusLabel}
        </span>
      </div>

      <div class="emp-card-meta">
        <div class="emp-meta-item">
          <i class="ri-id-card-line"></i>
          <span>${e.employee_id || "—"}</span>
        </div>
        <div class="emp-meta-item">
          <i class="ri-map-pin-line"></i>
          <span>${e.branch || "No branch"}</span>
        </div>
        <div class="emp-meta-item">
          <i class="ri-mail-line"></i>
          <span>${e.employee_email || "—"}</span>
        </div>
        <div class="emp-meta-item">
          <i class="ri-briefcase-line"></i>
          <span>${e.position_title || "—"}</span>
        </div>
        <div class="emp-meta-item">
        </div>
        <div class="emp-meta-item">
          <i class="ri-phone-line"></i>
          <span>${e.phone_number || "—"}</span>
        </div>
      </div>

      <div class="emp-card-footer">
        ${roleBadge}
      </div>
    </div>

    <div class="emp-card-actions">
      ${approveBtn}
      <button class="btn-assign-role" data-id="${e.id}">
        <i class="ri-user-settings-line"></i> Assign Role
      </button>
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