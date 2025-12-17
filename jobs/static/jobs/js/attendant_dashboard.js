(function () {
  // ---------------- helpers ----------------
  const $ = (id) => document.getElementById(id);
  const qsAll = (sel) => Array.from(document.querySelectorAll(sel));
  const on = (el, ev, fn) => el && el.addEventListener(ev, fn);

  function getCookie(name) {
    const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? m.pop() : "";
  }

  // ---------------- constants ----------------
  const API_BASE = "/api/jobs/";
  const SERVICES_ENDPOINT = API_BASE + "services/";
  const JOBS_ENDPOINT = API_BASE + "jobs/";
  const RECEIPT_BASE = API_BASE + "receipt/";

  // ---------------- elements ----------------
  const quickModal = $("record-job-quick-modal");
  const openQuickBtn = $("record-job-btn");
  const closeQuickBtn = $("quick-modal-close");
  const cancelQuickBtn = $("modal-cancel");
  const quickForm = $("record-job-form");

  const serviceSelect = $("modal-service");
  const qtyInput = $("modal-quantity");
  const totalLabel = $("modal-total-amount");

  // ---------------- modal helpers ----------------
  function openQuickModal() {
    if (!quickModal) return;
    quickModal.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
  }

  function closeQuickModal() {
    if (!quickModal) return;
    quickModal.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
  }

  on(openQuickBtn, "click", (e) => {
    if (e) e.preventDefault();
    openQuickModal();
  });
  on(closeQuickBtn, "click", closeQuickModal);
  on(cancelQuickBtn, "click", closeQuickModal);

  // ---------------- services loading ----------------
  async function loadServices() {
    if (!serviceSelect) return;

    serviceSelect.innerHTML =
      '<option value="">Loading services…</option>';

    try {
      const resp = await fetch(SERVICES_ENDPOINT, {
        credentials: "same-origin",
      });

      if (!resp.ok) {
        throw new Error("Failed to load services");
      }

      const services = await resp.json();

      serviceSelect.innerHTML =
        '<option value="">Select service</option>';

      services.forEach((svc) => {
        // ✅ Quick Record only supports non-print quick services
        if (!svc.is_quick || svc.is_print_service) return;

        const opt = document.createElement("option");
        opt.value = svc.id;
        opt.textContent = svc.name;
        serviceSelect.appendChild(opt);
      });

      // If nothing valid remains
      if (serviceSelect.options.length === 1) {
        serviceSelect.innerHTML =
          '<option value="">No quick services available</option>';
      }
    } catch (err) {
      console.error("Service load failed", err);
      serviceSelect.innerHTML =
        '<option value="">Unable to load services</option>';
    }
  }

  // Load services once when page is ready
  document.addEventListener("DOMContentLoaded", function () {
    loadServices();
  });

  // ---------------- total label ----------------
  function updateTotalPlaceholder() {
    if (totalLabel) {
      totalLabel.textContent = "Calculated at checkout";
    }
  }

  on(serviceSelect, "change", updateTotalPlaceholder);
  on(qtyInput, "input", updateTotalPlaceholder);

  // ---------------- submit quick job ----------------
  if (quickForm) {
    quickForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      const serviceId = serviceSelect.value;
      const qty = Math.max(1, parseInt(qtyInput.value || "1", 10));

      if (!serviceId) {
        alert("Please select a service");
        serviceSelect.focus();
        return;
      }

      const submitBtn = $("modal-submit");
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Processing…";
      }

      try {
        const fd = new FormData();
        fd.append("service", serviceId);
        fd.append("quantity", qty);
        fd.append("type", "instant");
        fd.append("customer_name", $("modal-customer")?.value || "");
        fd.append("customer_phone", $("modal-phone")?.value || "");
        fd.append("description", $("modal-notes")?.value || "");

        const resp = await fetch(JOBS_ENDPOINT, {
          method: "POST",
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: fd,
          credentials: "same-origin",
        });

        if (!resp.ok) {
          let err = "Job creation failed";
          try {
            const j = await resp.json();
            err = JSON.stringify(j);
          } catch {}
          throw new Error(err);
        }

        const data = await resp.json();

        // Open receipt
        if (data && data.id) {
          const urls = [
            data.receipt_url,
            "/jobs/receipt/" + data.id + "/",
            RECEIPT_BASE + data.id + "/",
          ];
          for (const u of urls) {
            if (!u) continue;
            try {
              window.open(u, "_blank");
              break;
            } catch {}
          }
        }

        // reset
        serviceSelect.selectedIndex = 0;
        qtyInput.value = "1";
        $("modal-customer").value = "";
        $("modal-phone").value = "";
        $("modal-notes").value = "";
        updateTotalPlaceholder();

        closeQuickModal();
      } catch (err) {
        console.error(err);
        alert("Could not create job");
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Checkout";
        }
      }
    });
  }

  console.debug("Attendant dashboard JS (API-driven services, filtered) loaded");
})();
