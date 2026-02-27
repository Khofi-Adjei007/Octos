/* =========================================================
   RECOMMEND CANDIDATE MODULE
   Handles the recommendation form modal for branch managers
========================================================= */

const CSRF = () => document.cookie.match(/csrftoken=([^;]+)/)?.[1] || "";

let recommendModal = null;


/* -----------------------------------------
 * BOOT — call this from main_branch_file.js
 * ----------------------------------------- */
export function initRecommend() {
  const btn = document.getElementById("btn-recommend-candidate");
  if (btn) {
    btn.addEventListener("click", openRecommendModal);
  }
}


/* -----------------------------------------
 * OPEN MODAL
 * ----------------------------------------- */
function openRecommendModal() {
  document.getElementById("recommend-modal")?.remove();

  const modal = document.createElement("div");
  modal.id = "recommend-modal";
  modal.className = "rec-modal-overlay";

  modal.innerHTML = `
    <div class="rec-modal-box">

      <div class="rec-modal-header">
        <div>
          <h3>Recommend a Candidate</h3>
          <p>This will create a priority application in the HR pipeline.</p>
        </div>
        <button class="rec-modal-close" id="rec-close-btn">✕</button>
      </div>

      <div class="rec-modal-body">

        <div class="rec-form-row">
          <div class="rec-form-group">
            <label>First Name <span class="rec-required">*</span></label>
            <input type="text" id="rec-first-name" placeholder="e.g. Ama" />
          </div>
          <div class="rec-form-group">
            <label>Last Name <span class="rec-required">*</span></label>
            <input type="text" id="rec-last-name" placeholder="e.g. Mensah" />
          </div>
        </div>

        <div class="rec-form-row">
          <div class="rec-form-group">
            <label>Phone <span class="rec-required">*</span></label>
            <input type="tel" id="rec-phone" placeholder="+233XXXXXXXXX" />
          </div>
          <div class="rec-form-group">
            <label>Email</label>
            <input type="email" id="rec-email" placeholder="optional" />
          </div>
        </div>

        <div class="rec-form-row">
          <div class="rec-form-group">
            <label>Position Applied For <span class="rec-required">*</span></label>
            <input type="text" id="rec-role" placeholder="e.g. General Attendant" />
          </div>
          <div class="rec-form-group">
            <label>Gender</label>
            <select id="rec-gender">
              <option value="">— Select —</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>

        <div class="rec-form-group rec-form-full">
          <label>Why are you recommending this candidate?</label>
          <textarea id="rec-notes" rows="3"
            placeholder="Briefly describe why this candidate is a good fit..."></textarea>
        </div>

        <div id="rec-error" class="rec-error hidden"></div>
        <div id="rec-success" class="rec-success hidden"></div>

      </div>

      <div class="rec-modal-footer">
        <button class="rec-btn-cancel" id="rec-cancel-btn">Cancel</button>
        <button class="rec-btn-submit" id="rec-submit-btn">
          <span id="rec-submit-label">Submit Recommendation</span>
        </button>
      </div>

    </div>
  `;

  document.body.appendChild(modal);
  recommendModal = modal;

  // Close handlers
  document.getElementById("rec-close-btn").addEventListener("click", closeRecommendModal);
  document.getElementById("rec-cancel-btn").addEventListener("click", closeRecommendModal);
  modal.addEventListener("click", e => { if (e.target === modal) closeRecommendModal(); });

  // Submit
  document.getElementById("rec-submit-btn").addEventListener("click", submitRecommendation);

  // Focus first field
  setTimeout(() => document.getElementById("rec-first-name")?.focus(), 50);
}


/* -----------------------------------------
 * CLOSE MODAL
 * ----------------------------------------- */
function closeRecommendModal() {
  recommendModal?.remove();
  recommendModal = null;
}


/* -----------------------------------------
 * SUBMIT
 * ----------------------------------------- */
async function submitRecommendation() {
  const firstName = document.getElementById("rec-first-name").value.trim();
  const lastName  = document.getElementById("rec-last-name").value.trim();
  const phone     = document.getElementById("rec-phone").value.trim();
  const email     = document.getElementById("rec-email").value.trim();
  const role      = document.getElementById("rec-role").value.trim();
  const gender    = document.getElementById("rec-gender").value;
  const notes     = document.getElementById("rec-notes").value.trim();

  const errorDiv   = document.getElementById("rec-error");
  const successDiv = document.getElementById("rec-success");
  const submitBtn  = document.getElementById("rec-submit-btn");
  const submitLabel = document.getElementById("rec-submit-label");

  errorDiv.classList.add("hidden");
  successDiv.classList.add("hidden");

  // Validate
  if (!firstName || !lastName || !phone || !role) {
    errorDiv.textContent = "Please fill in all required fields.";
    errorDiv.classList.remove("hidden");
    return;
  }

  submitBtn.disabled = true;
  submitLabel.textContent = "Submitting...";

  try {
    const res = await fetch("/hr/api/recommendations/", {
      method: "POST",
      headers: {
        "X-CSRFToken": CSRF(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        first_name:      firstName,
        last_name:       lastName,
        phone:           phone,
        email:           email,
        role_applied_for: role,
        gender:          gender,
        notes:           notes,
      }),
    });

    const data = await res.json();

    if (data.success) {
      successDiv.innerHTML = `
        <strong>${data.applicant}</strong> has been recommended for
        <strong>${data.role}</strong> and added to the HR pipeline with priority status.
      `;
      successDiv.classList.remove("hidden");

      // Disable form fields
      ["rec-first-name","rec-last-name","rec-phone","rec-email",
       "rec-role","rec-gender","rec-notes"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = true;
      });

      submitBtn.disabled = true;
      submitLabel.textContent = "Submitted ✓";

      // Auto close after 2.5s
      setTimeout(closeRecommendModal, 2500);

    } else {
      errorDiv.textContent = data.error || "Submission failed.";
      errorDiv.classList.remove("hidden");
      submitBtn.disabled = false;
      submitLabel.textContent = "Submit Recommendation";
    }

  } catch (err) {
    console.error("Recommendation error:", err);
    errorDiv.textContent = "Something went wrong. Please try again.";
    errorDiv.classList.remove("hidden");
    submitBtn.disabled = false;
    submitLabel.textContent = "Submit Recommendation";
  }
}