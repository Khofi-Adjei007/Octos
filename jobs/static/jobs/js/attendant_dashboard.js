/* ============================================================
 * QUICK RECORD MODAL (OPEN / CLOSE)
 * ============================================================ */
const modal = document.querySelector("#record-job-quick-modal");
const openBtn = document.querySelector("#record-job-btn");
const closeBtn = document.querySelector("#quick-modal-close");
const cancelBtn = document.querySelector("#modal-cancel");

function openModal() {
  if (!modal) return;
  modal.classList.remove("hidden");
  document.body.classList.add("overflow-hidden");
}

function closeModal() {
  if (!modal) return;
  modal.classList.add("hidden");
  document.body.classList.remove("overflow-hidden");
}

openBtn?.addEventListener("click", (e) => {
  e.preventDefault();
  openModal();
});

closeBtn?.addEventListener("click", closeModal);
cancelBtn?.addEventListener("click", closeModal);

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});



(function () {
  /* ============================================================
   * HELPERS
   * ============================================================ */
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  function getCookie(name) {
    const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? m.pop() : "";
  }

  /* ============================================================
   * API ENDPOINTS
   * ============================================================ */
  const API_BASE = "/api/jobs/";
  const SERVICES_ENDPOINT = API_BASE + "services/";
  const JOBS_ENDPOINT = API_BASE + "jobs/";

  /* ============================================================
   * DOM REFERENCES (QUICK RECORD)
   * ============================================================ */
  const serviceLinesBox = $("#service-lines");
  const addLineBtn = $("#add-service-line");
  const summaryBox = $("#summary-lines");
  const summaryTotal = $("#summary-total");
  const form = $("#record-job-form");
  const submitBtn = $("#modal-submit");
  const feedback = $("#quick-feedback");

  const customerName = $("#modal-customer");
  const customerPhone = $("#modal-phone");
  const branchInput = $("#branch-select");

  /* ============================================================
   * STATE
   * ============================================================ */
  let servicesCache = [];

  /* ============================================================
   * DATA LOADING
   * ============================================================ */
  async function loadServicesOnce() {
    if (servicesCache.length) return servicesCache;

    const resp = await fetch(SERVICES_ENDPOINT, { credentials: "same-origin" });
    if (!resp.ok) throw new Error("Failed to load services");

    servicesCache = await resp.json();
    return servicesCache;
  }

  /* ============================================================
   * PRICING HELPERS
   * ============================================================ */
  function serviceHasVariants(service) {
    return Array.isArray(service.pricing_rules) && service.pricing_rules.length > 1;
  }

  function pricingRuleLabel(rule) {
    const parts = [];
    if (rule.paper_size) parts.push(rule.paper_size);
    if (rule.color_mode) parts.push(rule.color_mode);
    if (rule.side_mode) parts.push(rule.side_mode);
    if (rule.print_mode) parts.push(rule.print_mode);
    return parts.length ? parts.join(" • ") : "Standard";
  }

  function getUnitPriceBySelection(serviceId, ruleIndex = 0) {
    const svc = servicesCache.find(s => String(s.id) === String(serviceId));
    if (!svc || !svc.pricing_rules?.length) return 0;

    const rule = svc.pricing_rules[ruleIndex] || svc.pricing_rules[0];
    return parseFloat(rule.unit_price || "0");
  }

  /* ============================================================
   * SERVICE SELECT POPULATION
   * ============================================================ */
  function populateServiceSelect(select) {
    select.innerHTML = `<option value="">Select service</option>`;

    servicesCache.forEach((svc) => {
      if (!svc.is_quick) return;
      const opt = document.createElement("option");
      opt.value = svc.id;
      opt.textContent = svc.name;
      select.appendChild(opt);
    });
  }

  /* ============================================================
   * VARIANT SELECTOR
   * ============================================================ */
  function renderVariantSelect(line, serviceId) {
    const svc = servicesCache.find(s => String(s.id) === String(serviceId));
    if (!svc) return;

    let container = line.querySelector(".variant-container");

    if (!serviceHasVariants(svc)) {
      if (container) container.remove();
      return;
    }

    if (!container) {
      container = document.createElement("div");
      container.className = "variant-container w-full mt-2";
      container.innerHTML = `
        <label class="block text-xs mb-1">Options</label>
        <select class="variant-select w-full border rounded px-2 py-2 text-sm"></select>
      `;
      line.querySelector(".flex-1").appendChild(container);
    }

    const select = container.querySelector(".variant-select");
    select.innerHTML = "";

    svc.pricing_rules.forEach((rule, idx) => {
      const opt = document.createElement("option");
      opt.value = String(idx);
      opt.textContent = pricingRuleLabel(rule);
      select.appendChild(opt);
    });

    select.addEventListener("change", renderSummary);
  }

  /* ============================================================
   * SERVICE LINE CREATION
   * ============================================================ */
  function createServiceLine() {
    const line = document.createElement("div");
    line.className = "service-line flex items-end gap-2";

    line.innerHTML = `
      <div class="flex-1">
        <label class="block text-xs mb-1">Service</label>
        <select class="service-select w-full border rounded px-2 py-2 text-sm"></select>
      </div>
      <div class="w-24">
        <label class="block text-xs mb-1">Qty</label>
        <input type="number" class="service-qty w-full border rounded px-2 py-2 text-sm" min="1" value="1">
      </div>
      <button type="button" class="remove-line text-red-600">✕</button>
    `;

    const serviceSelect = line.querySelector(".service-select");
    populateServiceSelect(serviceSelect);

    line.querySelector(".remove-line").addEventListener("click", () => {
      line.remove();
      renderSummary();
    });

    bindLine(line);
    serviceLinesBox.appendChild(line);
  }

  /* ============================================================
   * SUMMARY CALCULATION
   * ============================================================ */
  function getLineData(line) {
    const svcSelect = line.querySelector(".service-select");
    const qtyInput = line.querySelector(".service-qty");
    const variantSelect = line.querySelector(".variant-select");

    if (!svcSelect || !qtyInput || !svcSelect.value) return null;

    const qty = Math.max(1, parseInt(qtyInput.value || "1", 10));
    const ruleIndex = variantSelect ? parseInt(variantSelect.value || "0", 10) : 0;
    const unitPrice = getUnitPriceBySelection(svcSelect.value, ruleIndex);

    return {
      serviceId: svcSelect.value,
      serviceName: svcSelect.selectedOptions[0].textContent,
      quantity: qty,
      unitPrice,
      lineTotal: unitPrice * qty,
      ruleIndex,
    };
  }

  function renderSummary() {
    summaryBox.innerHTML = "";

    let grandTotal = 0;
    let hasData = false;

    $$(".service-line").forEach((line) => {
      const data = getLineData(line);
      if (!data) return;

      hasData = true;
      grandTotal += data.lineTotal;

      summaryBox.insertAdjacentHTML(
        "beforeend",
        `
        <div class="flex justify-between text-sm border-b pb-1">
          <span>${data.serviceName} × ${data.quantity}</span>
          <span>GHS ${data.lineTotal.toFixed(2)}</span>
        </div>
        `
      );
    });

    summaryTotal.textContent = hasData
      ? `GHS ${grandTotal.toFixed(2)}`
      : "GHS —";
  }

  function bindLine(line) {
    const serviceSelect = line.querySelector(".service-select");
    const qtyInput = line.querySelector(".service-qty");

    serviceSelect?.addEventListener("change", () => {
      renderVariantSelect(line, serviceSelect.value);
      renderSummary();
    });

    qtyInput?.addEventListener("input", renderSummary);
  }

  /* ============================================================
   * INITIALIZATION
   * ============================================================ */
  document.addEventListener("DOMContentLoaded", async () => {
    await loadServicesOnce();

    const existingLines = $$(".service-line");

    if (existingLines.length) {
      existingLines.forEach((line) => {
        const select = line.querySelector(".service-select");
        if (select) populateServiceSelect(select);
        bindLine(line);
      });
    } else {
      createServiceLine();
    }

    renderSummary();
  });

  addLineBtn?.addEventListener("click", createServiceLine);

  /* ============================================================
   * FORM SUBMISSION
   * ============================================================ */
  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    feedback.textContent = "";

    if (!branchInput?.value) {
      feedback.textContent = "No branch assigned.";
      return;
    }

    const lines = $$(".service-line");
    if (!lines.length) {
      feedback.textContent = "Add at least one service.";
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Processing…";

    try {
      let lastJob = null;

      for (const line of lines) {
        const data = getLineData(line);
        if (!data) throw new Error("Select all services.");

        const fd = new FormData();
        fd.append("branch", branchInput.value);
        fd.append("service", data.serviceId);
        fd.append("quantity", data.quantity);
        fd.append("type", "instant");
        fd.append("customer_name", customerName.value || "");
        fd.append("customer_phone", customerPhone.value || "");

        const svc = servicesCache.find(s => String(s.id) === String(data.serviceId));
        if (svc && svc.pricing_rules[data.ruleIndex]) {
          const rule = svc.pricing_rules[data.ruleIndex];
          fd.append("paper_size", rule.paper_size || "");
          fd.append("print_mode", rule.print_mode || "");
          fd.append("color_mode", rule.color_mode || "");
          fd.append("side_mode", rule.side_mode || "");
        }

        const resp = await fetch(JOBS_ENDPOINT, {
          method: "POST",
          headers: { "X-CSRFToken": getCookie("csrftoken") },
          body: fd,
          credentials: "same-origin",
        });

        const resData = await resp.json();
        if (!resp.ok) {
  console.error("JOB CREATE ERROR", resData);
  throw new Error(JSON.stringify(resData));
}

        lastJob = resData;
      }

 if (lastJob?.id) {
  const pdfUrl = `/api/jobs/receipt/${lastJob.id}/pdf/`;
  const win = window.open(pdfUrl, "_blank");
  if (win) {
    win.onload = () => win.print();
  }
}



      serviceLinesBox.innerHTML = "";
      createServiceLine();
      customerName.value = "";
      customerPhone.value = "";
      closeModal();
    } catch (err) {
      feedback.textContent = err.message;
    } finally {
      console.log(
  "Submitting services:",
  servicesCache.map(s => ({ id: s.id, name: s.name }))
);

      submitBtn.disabled = false;
      submitBtn.textContent = "Checkout";
    }
  });

})();

/* ============================================================
 * ATTENDANT TABS + UNDERLINE (DESKTOP & MOBILE)
 * ============================================================ */
(function () {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const panels = document.querySelectorAll(".tab-panel");

  const desktopNav = document.getElementById("attendantDesktopNav");
  const mobileNav = document.getElementById("attendantMobileNav");

  const desktopUnderline = document.getElementById("attTabUnderline");
  const mobileUnderline = document.getElementById("attMobileUnderline");

  if (!tabButtons.length) return;

  function activateTab(tab) {
    const tabName = tab.dataset.tab;
    if (!tabName) return;

    // Panels
    panels.forEach(panel => {
      panel.classList.toggle(
        "hidden",
        panel.id !== `panel-${tabName}`
      );
    });

    // Button styles
    tabButtons.forEach(btn => {
      btn.setAttribute("aria-pressed", "false");
      btn.classList.remove("bg-white", "text-red-700");
      btn.classList.add("bg-transparent", "text-white");
    });

    tab.setAttribute("aria-pressed", "true");
    tab.classList.remove("bg-transparent", "text-white");
    tab.classList.add("bg-white", "text-red-700");

    // Underline movement
    const rect = tab.getBoundingClientRect();

    if (desktopNav && desktopUnderline && desktopNav.contains(tab)) {
      const parentRect = desktopNav.getBoundingClientRect();
      desktopUnderline.style.width = `${rect.width}px`;
      desktopUnderline.style.transform =
        `translateX(${rect.left - parentRect.left}px)`;
    }

    if (mobileNav && mobileUnderline && mobileNav.contains(tab)) {
      const parentRect = mobileNav.getBoundingClientRect();
      mobileUnderline.style.width = `${rect.width}px`;
      mobileUnderline.style.left =
        `${rect.left - parentRect.left}px`;
    }
  }

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => activateTab(btn));
  });

  // Default tab → JOB
  const defaultTab =
    document.querySelector('.tab-btn[data-tab="job"]') || tabButtons[0];

  activateTab(defaultTab);
})();
/* ============================================================
 * USER PROFILE DROPDOWN
 * ============================================================ */
(function () {
  const button = document.getElementById("user-menu-btn");
  const menu = document.getElementById("user-menu");

  if (!button || !menu) return;

  function closeMenu() {
    menu.classList.add("hidden");
    button.setAttribute("aria-expanded", "false");
  }

  function toggleMenu(e) {
    e.stopPropagation();
    const isOpen = !menu.classList.contains("hidden");
    menu.classList.toggle("hidden");
    button.setAttribute("aria-expanded", String(!isOpen));
  }

  button.addEventListener("click", toggleMenu);

  document.addEventListener("click", (e) => {
    if (!menu.contains(e.target) && !button.contains(e.target)) {
      closeMenu();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMenu();
  });
})();
