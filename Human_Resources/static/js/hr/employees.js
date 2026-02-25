/* =========================================================
   EMPLOYEES MODULE
   Renders employee list, handles filters and HR approval
========================================================= */

const CSRF = () => document.cookie.match(/csrftoken=([^;]+)/)?.[1] || "";

let allEmployees = [];
let currentFilter = "all";


/* -----------------------------------------
 * BOOT
 * ----------------------------------------- */
export async function loadEmployees() {
  await fetchAndRender();
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


/* -----------------------------------------
 * FILTER
 * ----------------------------------------- */
function applyFilter(employees) {
  switch (currentFilter) {
    case "active":
      return employees.filter(e => e.is_active && e.approved);
    case "inactive":
      return employees.filter(e => !e.is_active);
    case "pending":
      return employees.filter(e => !e.approved);
    case "unassigned":
      return employees.filter(e => !e.branch);
    default:
      return employees;
  }
}

function updateFilterCounts(employees) {
  const counts = {
    all:        employees.length,
    active:     employees.filter(e => e.is_active && e.approved).length,
    inactive:   employees.filter(e => !e.is_active).length,
    pending:    employees.filter(e => !e.approved).length,
    unassigned: employees.filter(e => !e.branch).length,
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

  employees.forEach(e => {
    const card = buildEmployeeCard(e);
    container.appendChild(card);
  });
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

  const approveBtn = !e.approved
    ? `<button class="btn-approve" data-id="${e.id}">
         <i class="ri-shield-check-line"></i> Approve
       </button>`
    : "";

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
        ${e.employee_email
          ? `<div class="employee-email">${e.employee_email}</div>`
          : ""}
      </div>
    </div>
    <div class="employee-card-right">
      ${statusBadge}
      ${approveBtn}
    </div>
  `;

  // Approve button handler
  const btn = card.querySelector(".btn-approve");
  if (btn) {
    btn.addEventListener("click", () => approveEmployee(e.id, card));
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
      headers: {
        "X-CSRFToken": CSRF(),
        "Content-Type": "application/json",
      },
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