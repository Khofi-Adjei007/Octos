/* =========================================================
   RECRUITMENT DETAIL PAGE
   Wired to RecruitmentEngine via transition API.
   All mutations go through performTransition().
========================================================= */

const STAGES = ['submitted', 'screening', 'interview', 'final_review', 'decision'];

const STAGE_COLORS = {
  submitted:    { bg: 'bg-gray-200',   text: 'text-gray-700'   },
  screening:    { bg: 'bg-blue-600',   text: 'text-white'      },
  interview:    { bg: 'bg-amber-400',  text: 'text-white'      },
  final_review: { bg: 'bg-purple-500', text: 'text-white'      },
  decision:     { bg: 'bg-red-500',    text: 'text-white'      },
};

const TERMINAL_STATUSES = ['hire_approved', 'rejected', 'withdrawn', 'closed'];

let currentApp = null;

/* =========================================================
   BOOT
========================================================= */

document.addEventListener("DOMContentLoaded", () => {
  const applicationId = extractApplicationId();
  loadApplication(applicationId);
  activateRatingSystem();
});


function extractApplicationId() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  return parts[parts.length - 1];
}


/* =========================================================
   LOAD APPLICATION
========================================================= */
async function loadApplication(applicationId) {
  try {
    const response = await fetch(`/hr/api/applications/${applicationId}/`);
    if (!response.ok) throw new Error("Failed to fetch application");

    const data = await response.json();
    currentApp = data;

    renderHeader(data);
    renderResume(data);
    renderProgressRibbon(data);
    renderActionPanel(data);
    renderEvaluationPanel(data);

    if (data.evaluation && data.evaluation.stage === data.current_stage) {
      hydrateEvaluation(data.evaluation);
      if (data.evaluation.is_finalized) {
        lockEvaluationUI();
      }
    } else {
      resetEvaluationUI();
    }

  } catch (error) {
    console.error("Error loading application:", error);
  }
}
/* =========================================================
   RENDER HEADER
========================================================= */

function renderHeader(data) {
  const fullName = `${data.first_name} ${data.last_name}`;

  document.getElementById("applicant-fullname").innerText = fullName;
  document.getElementById("applicant-role").innerText = data.role_applied_for || "";
  document.getElementById("applicant-email").innerText = data.email || "";

  const badge = document.getElementById("current-stage-badge");
  if (badge) {
    badge.innerText = (data.current_stage || "").replace(/_/g, " ").toUpperCase();
  }

  // Update CV stage label dynamically
  const stageLabel = document.getElementById("cv-stage-label");
  if (stageLabel) {
    stageLabel.innerText = (data.current_stage || "").replace(/_/g, " ").toUpperCase() + " STAGE";
  }
}


/* =========================================================
   RENDER RESUME
========================================================= */
function renderResume(data) {
  const container = document.getElementById("cv-viewer");
  const panelTitle = document.getElementById("left-panel-title");
  if (!container) return;

  if (data.current_stage === 'interview') {
    if (panelTitle) panelTitle.innerText = "Interview";

    container.innerHTML = `
      <div style="
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        height: 100%; padding: 40px; text-align: center;
        background: linear-gradient(135deg, #eff6ff, #ffffff);
      ">
        <div style="font-size: 80px; margin-bottom: 16px; line-height:1;">
          🧑‍💼🤝👩‍💼
        </div>
        <h3 style="font-size: 18px; font-weight: 700; color: #1e40af; margin-bottom: 8px;">
          Interview In Progress
        </h3>
        <p style="font-size: 13px; color: #6b7280; max-width: 260px; line-height: 1.6;">
          Score the candidate using the evaluation panel. Finalize when the interview is complete.
        </p>

        ${data.interview_date ? `
        <div style="
          margin-top: 24px; background: white; border: 1px solid #e5e7eb;
          border-radius: 12px; padding: 16px 24px; font-size: 13px; color: #374151;
        ">
          <div style="font-weight: 600; color: #1e40af; margin-bottom: 4px;">
            📅 Scheduled
          </div>
          <div>${new Date(data.interview_date).toLocaleString()}</div>
        </div>
        ` : ''}
      </div>
    `;
    return;
  }

  if (data.current_stage === 'final_review') {
    if (panelTitle) panelTitle.innerText = "Final Review";
  } else if (data.current_stage === 'decision') {
    if (panelTitle) panelTitle.innerText = "Decision";
  } else {
    if (panelTitle) panelTitle.innerText = "Curriculum Vitae";
  }

  if (!data.resume_url) {
    container.innerHTML = `
      <div class="text-gray-400 flex items-center justify-center h-full text-sm">
        No resume uploaded.
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <iframe
      src="${data.resume_url}"
      class="w-full h-full"
      style="border:none;"
      loading="lazy">
    </iframe>
  `;
}


/* =========================================================
   RENDER PROGRESS RIBBON (DYNAMIC)
========================================================= */
function renderProgressRibbon(data) {
  const ribbon = document.getElementById("stage-ribbon");
  if (!ribbon) return;

  const currentIndex = STAGES.indexOf(data.current_stage);

  const STAGE_STYLES = {
    submitted:    'background:#6b7280; color:white;',
    screening:    'background:#2563eb; color:white;',
    interview:    'background:#f59e0b; color:white;',
    final_review: 'background:#8b5cf6; color:white;',
    decision:     'background:#ef4444; color:white;',
  };

  ribbon.innerHTML = STAGES.map((stage, index) => {
    let style;
    if (index < currentIndex) {
      style = 'background:#22c55e; color:white;';
    } else if (index === currentIndex) {
      style = STAGE_STYLES[stage] || 'background:#2563eb; color:white;';
    } else {
      style = 'background:#f3f4f6; color:#9ca3af;';
    }

    const label = stage.replace(/_/g, " ");
    return `<div class="flex-1 text-center py-2 text-xs font-semibold uppercase tracking-wide" style="${style}">${label}</div>`;
  }).join('');
}


/* =========================================================
   RENDER EVALUATION PANEL
   Updates title based on current stage
========================================================= */

function renderEvaluationPanel(data) {
  const title = document.getElementById("evaluation-panel-title");
  if (title) {
    const stageLabel = (data.current_stage || "screening").replace(/_/g, " ");
    title.innerText = stageLabel.toUpperCase() + " EVALUATION";
  }
}


/* =========================================================
   RENDER ACTION PANEL
   Shows contextual actions based on current stage/status
========================================================= */

function renderActionPanel(data) {
  const panel = document.getElementById("action-panel");
  if (!panel) return;

  const stage = data.current_stage;
  const status = data.status;

  if (TERMINAL_STATUSES.includes(status)) {
    const messages = {
      hire_approved: "✅ Candidate hired. Onboarding initiated.",
      rejected:      "❌ Application rejected.",
      withdrawn:     "↩️ Offer withdrawn.",
      closed:        "🔒 Application closed.",
    };
    panel.innerHTML = `
      <div class="text-sm font-medium text-gray-500 py-2">
        ${messages[status] || "Application closed."}
      </div>
    `;
    return;
  }

  if (stage === 'submitted') {
    panel.innerHTML = `
      <button onclick="handleTransition('start_screening')"
        class="action-btn bg-blue-600 text-white hover:bg-blue-700">
        Start Screening
      </button>
    `;
  }

  else if (stage === 'screening') {
    // Controlled from evaluation panel after finalization
    panel.innerHTML = '';
  }

  else if (stage === 'interview') {
    // Controlled from evaluation panel after finalization
    panel.innerHTML = '';
  }

  else if (stage === 'final_review') {
    panel.innerHTML = `
      <button onclick="handleTransition('submit_final_review')"
        class="action-btn bg-purple-600 text-white hover:bg-purple-700">
        Submit Final Review
      </button>
    `;
  }

  else if (stage === 'decision') {
    if (status === 'active') {
      panel.innerHTML = `
        <button onclick="handleTransition('approve')"
          class="action-btn bg-green-600 text-white hover:bg-green-700">
          Extend Offer
        </button>
        <button onclick="handleTransition('reject')"
          class="action-btn bg-red-100 text-red-600 hover:bg-red-200">
          Reject
        </button>
      `;
    } else if (status === 'offer_extended') {
      panel.innerHTML = `
        <button onclick="handleTransition('accept_offer')"
          class="action-btn bg-green-600 text-white hover:bg-green-700">
          Accept Offer
        </button>
        <button onclick="handleTransition('decline_offer')"
          class="action-btn bg-red-100 text-red-600 hover:bg-red-200">
          Decline Offer
        </button>
        <button onclick="handleTransition('withdraw_offer')"
          class="action-btn bg-orange-100 text-orange-600 hover:bg-orange-200">
          Withdraw Offer
        </button>
      `;
    }
  }
}

/* =========================================================
   HANDLE TRANSITION
========================================================= */

async function handleTransition(action, payload = {}) {
  if (!currentApp) return;

  try {
    const response = await fetch(
      `/hr/api/recruitment/${currentApp.id}/transition/`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ action, ...payload })
      }
    );

    if (!response.ok) {
    const error = await response.json();
    console.error("Transition error:", JSON.stringify(error));
    alert(error.detail || "Action failed.");
    return;
  }

    const updated = await response.json();
    currentApp = updated;

    renderHeader(updated);
    renderProgressRibbon(updated);
    renderActionPanel(updated);
    renderEvaluationPanel(updated);

    if (updated.status === "hire_approved") {
      showHireModal(updated);
    }

  } catch (err) {
    console.error(err);
    alert("Something went wrong. Please try again.");
  }
}


/* =========================================================
   INTERVIEW MODAL
========================================================= */

let selectedInterviewMode = 'in_person';

function setInterviewMode(mode) {
  selectedInterviewMode = mode;
  const inPerson = document.getElementById('mode-inperson');
  const virtual  = document.getElementById('mode-virtual');

  if (mode === 'in_person') {
    inPerson.className = 'flex-1 py-2 text-sm font-semibold rounded-lg border-2 border-blue-600 bg-blue-600 text-white';
    virtual.className  = 'flex-1 py-2 text-sm font-semibold rounded-lg border-2 border-gray-200 text-gray-500';
  } else {
    virtual.className  = 'flex-1 py-2 text-sm font-semibold rounded-lg border-2 border-blue-600 bg-blue-600 text-white';
    inPerson.className = 'flex-1 py-2 text-sm font-semibold rounded-lg border-2 border-gray-200 text-gray-500';
  }
}

async function loadInterviewers() {
  try {
    const response = await fetch('/hr/api/interviewers/');
    if (!response.ok) return;

    const data = await response.json();
    const select = document.getElementById('interviewer-select');
    if (!select) return;

    select.innerHTML = `<option value="">Select interviewer...</option>` +
      data.map(i => `<option value="${i.id}" data-name="${i.name}">${i.name}</option>`).join('');

  } catch (err) {
    console.error('Failed to load interviewers:', err);
  }
}

function openInterviewModal() {
  const modal = document.getElementById("interview-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.classList.add("flex");
  selectedInterviewMode = 'in_person';
  loadInterviewers();
}

function closeInterviewModal() {
  const modal = document.getElementById("interview-modal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("close-interview-modal")
    ?.addEventListener("click", closeInterviewModal);

  document.getElementById("cancel-interview")
    ?.addEventListener("click", closeInterviewModal);

  document.getElementById("confirm-interview")
    ?.addEventListener("click", async () => {
      const dateInput         = document.getElementById("interview-date");
      const interviewerSelect = document.getElementById("interviewer-select");
      const interviewDate     = dateInput?.value;

      if (!interviewDate) {
        alert("Please select an interview date.");
        return;
      }

      if (!interviewerSelect?.value) {
        alert("Please select an interviewer.");
        return;
      }

      closeInterviewModal();

      await handleTransition("schedule_interview", {
        interview_date:   new Date(interviewDate).toISOString(),
        interviewer_id:   interviewerSelect.value,
        interviewer_name: interviewerSelect.selectedOptions[0]?.dataset.name || "",
        interview_mode:   selectedInterviewMode,
      });
    });

  document.getElementById("save-screening")
    ?.addEventListener("click", () => {
      saveEvaluation();
    });

  document.getElementById("finalize-screening")
    ?.addEventListener("click", () => {
      finalizeEvaluation();
    });
});


/* =========================================================
   SAVE EVALUATION
========================================================= */

async function saveEvaluation() {
  if (!currentApp) return;

  const ratingGroups = document.querySelectorAll(".rating-group");
  const textareas = document.querySelectorAll("textarea");

  const getScore = (index) => {
    const group = ratingGroups[index];
    return group?.dataset.score ? parseFloat(group.dataset.score) : null;
  };

  const payload = {
    stage: currentApp.current_stage,
    career_score:       getScore(0),
    career_notes:       textareas[0]?.value || "",
    experience_score:   getScore(1),
    experience_notes:   textareas[1]?.value || "",
    stability_score:    getScore(2),
    stability_notes:    textareas[2]?.value || "",
    education_score:    getScore(3),
    education_notes:    textareas[3]?.value || "",
    skills_score:       getScore(4),
    skills_notes:       textareas[4]?.value || "",
  };

  try {
    const response = await fetch(
      `/hr/api/applications/${currentApp.id}/evaluate/`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify(payload)
      }
    );

    if (!response.ok) {
      const error = await response.json();
      alert(error.detail || "Failed to save evaluation.");
      return;
    }

    showToast("Evaluation saved successfully.");

  } catch {
    alert("Error saving evaluation.");
  }
}


/* =========================================================
   FINALIZE EVALUATION
========================================================= */
async function finalizeEvaluation() {
  if (!currentApp) return;

  try {
    const response = await fetch(
      `/hr/api/applications/${currentApp.id}/evaluate/`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken()
        }
      }
    );

    if (!response.ok) {
      const error = await response.json();
      alert(error.detail || "Failed to finalize evaluation.");
      return;
    }

    const stage = currentApp.current_stage;
    const toastMessages = {
      screening:    "✅ Evaluation finalized. Schedule the interview to proceed.",
      interview:    "✅ Interview scored. Click Complete Interview to advance.",
      final_review: "✅ Review finalized. Submit to proceed to decision.",
    };

    showToast(toastMessages[stage] || "✅ Evaluation finalized.");
    lockEvaluationUI();

    // DO NOT reload application here — it would overwrite lockEvaluationUI()

  } catch {
    alert("Error finalizing evaluation.");
  }
}

/* =========================================================
   CELEBRATORY HIRE MODAL
========================================================= */

function showHireModal(app) {
  const existing = document.getElementById("hire-modal");
  if (existing) existing.remove();

  const modal = document.createElement("div");
  modal.id = "hire-modal";
  modal.style.cssText = `
    position: fixed; inset: 0; background: rgba(0,0,0,0.5);
    display: flex; align-items: center; justify-content: center;
    z-index: 1000; opacity: 0; transition: opacity 0.3s ease;
  `;

  modal.innerHTML = `
    <div style="
      background: white; border-radius: 16px; padding: 48px 40px;
      max-width: 480px; width: 90%; text-align: center;
      box-shadow: 0 20px 60px rgba(0,0,0,0.2);
      transform: translateY(20px); transition: transform 0.3s ease;
    " id="hire-modal-card">

      <div style="font-size: 64px; margin-bottom: 16px;">🎉</div>

      <h2 style="font-size: 28px; font-weight: 700; color: #111; margin-bottom: 12px;">
        Congratulations!
      </h2>

      <p style="font-size: 15px; color: #555; line-height: 1.6; margin-bottom: 32px;">
        <strong>${app.first_name} ${app.last_name}</strong> has been successfully hired
        as <strong>${app.role_applied_for}</strong>.
        Their onboarding record has been created and is ready to begin.
      </p>

      <div style="display: flex; flex-direction: column; gap: 12px;">
        <button id="btn-start-onboarding" style="
          background: #e53935; color: white; border: none;
          padding: 14px 24px; border-radius: 8px;
          font-size: 15px; font-weight: 600; cursor: pointer;
        ">
          🚀 Start Onboarding Now
        </button>

        <button id="btn-onboard-later" style="
          background: transparent; color: #888;
          border: 1px solid #ddd; padding: 12px 24px;
          border-radius: 8px; font-size: 14px; cursor: pointer;
        ">
          Continue Later
        </button>
      </div>

    </div>
  `;

  document.body.appendChild(modal);

  requestAnimationFrame(() => {
    modal.style.opacity = "1";
    document.getElementById("hire-modal-card").style.transform = "translateY(0)";
  });

  document.getElementById("btn-start-onboarding").addEventListener("click", () => {
    modal.remove();
    window.location.href = `/hr/onboarding/${app.id}/`;
  });

  document.getElementById("btn-onboard-later").addEventListener("click", () => {
    modal.remove();
  });

  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.remove();
  });
}


/* =========================================================
   RATING SYSTEM
========================================================= */

function activateRatingSystem() {
  const ratingGroups = document.querySelectorAll(".rating-group");
  const scoreDisplay = document.getElementById("overall-score");
  const scoreBar = document.getElementById("score-bar");

  ratingGroups.forEach(group => {
    const buttons = group.querySelectorAll(".rating-btn");

    buttons.forEach((button, index) => {
      button.addEventListener("click", () => {
        if (button.disabled) return;

        buttons.forEach(btn => {
          btn.classList.remove("ring-2", "ring-offset-1", "ring-black", "scale-105");
        });

        button.classList.add("ring-2", "ring-offset-1", "ring-black", "scale-105");
        group.dataset.score = 5 - index;
        updateOverallScore();
      });
    });
  });

  function updateOverallScore() {
    let total = 0;
    let count = 0;

    ratingGroups.forEach(group => {
      if (group.dataset.score) {
        total += parseInt(group.dataset.score);
        count++;
      }
    });

    if (!scoreDisplay || !scoreBar) return;

    if (count === 0) {
      scoreDisplay.innerText = "0.00 / 10";
      scoreBar.style.width = "0%";
      return;
    }

    const average = total / count;
    const finalScore = (average / 5) * 10;
    scoreDisplay.innerText = finalScore.toFixed(2) + " / 10";
    scoreBar.style.width = ((finalScore / 10) * 100) + "%";
  }
}


/* =========================================================
   HYDRATE EVALUATION
========================================================= */

function hydrateEvaluation(evaluation) {
  const ratingGroups = document.querySelectorAll(".rating-group");
  const scoreDisplay = document.getElementById("overall-score");
  const scoreBar = document.getElementById("score-bar");

  const scores = [
    evaluation.career_score,
    evaluation.experience_score,
    evaluation.stability_score,
    evaluation.education_score,
    evaluation.skills_score,
  ];

  ratingGroups.forEach((group, index) => {
    const score = scores[index];
    if (!score) return;

    const buttons = group.querySelectorAll(".rating-btn");
    const buttonIndex = 5 - score;

    if (buttons[buttonIndex]) {
      buttons[buttonIndex].classList.add("ring-2", "ring-offset-1", "ring-black", "scale-105");
      group.dataset.score = score;
    }
  });

  if (evaluation.weighted_score && scoreDisplay && scoreBar) {
    const finalScore = (evaluation.weighted_score / 5) * 10;
    scoreDisplay.innerText = finalScore.toFixed(2) + " / 10";
    scoreBar.style.width = ((finalScore / 10) * 100) + "%";
  }

  const textareas = document.querySelectorAll("textarea");
  if (textareas.length >= 5) {
    textareas[0].value = evaluation.career_notes || "";
    textareas[1].value = evaluation.experience_notes || "";
    textareas[2].value = evaluation.stability_notes || "";
    textareas[3].value = evaluation.education_notes || "";
    textareas[4].value = evaluation.skills_notes || "";
  }
}


/* =========================================================
   LOCK EVALUATION UI
========================================================= */
function lockEvaluationUI() {
  // Lock the entire evaluation panel — nothing clickable
  const panel = document.getElementById("evaluation-panel");
  if (panel) {
    panel.style.pointerEvents = "none";
    panel.style.opacity = "0.85";
  }

  // Replace actions div with stage-appropriate forward button
  // Must temporarily re-enable pointer events on actions div only
  const actionsDiv = document.getElementById("screening-actions");
  if (!actionsDiv || !currentApp) return;

  const stage = currentApp.current_stage;

  if (stage === 'screening') {
    actionsDiv.innerHTML = `
      <button type="button"
              onclick="openInterviewModal()"
              style="pointer-events: auto;"
              class="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
        Schedule Interview
      </button>
    `;
  } else if (stage === 'interview') {
    actionsDiv.innerHTML = `
      <button type="button"
              onclick="handleTransition('complete_interview')"
              style="pointer-events: auto;"
              class="px-4 py-2 text-sm font-semibold text-white bg-amber-500 rounded-lg hover:bg-amber-600">
        ✅ Complete Interview
      </button>
    `;
  } else if (stage === 'final_review') {
    actionsDiv.innerHTML = `
      <button type="button"
              onclick="handleTransition('submit_final_review')"
              style="pointer-events: auto;"
              class="px-4 py-2 text-sm font-semibold text-white bg-purple-600 rounded-lg hover:bg-purple-700">
        Submit Final Review
      </button>
    `;
  }

  // Re-enable pointer events on the actions div itself
  actionsDiv.style.pointerEvents = "auto";
}
/* =========================================================
   RESET EVALUATION UI
   Clears form for fresh stage evaluation
========================================================= */
function resetEvaluationUI() {
  // Re-enable the panel
  const panel = document.getElementById("evaluation-panel");
  if (panel) {
    panel.style.pointerEvents = "auto";
    panel.style.opacity = "1";
  }

  document.querySelectorAll(".rating-btn").forEach(btn => {
    btn.disabled = false;
    btn.classList.remove("opacity-60", "cursor-not-allowed", "ring-2", "ring-offset-1", "ring-black", "scale-105");
  });

  document.querySelectorAll("textarea").forEach(area => {
    area.value = "";
    area.disabled = false;
    area.classList.remove("bg-gray-100");
  });

  document.querySelectorAll(".rating-group").forEach(group => {
    delete group.dataset.score;
  });

  const scoreDisplay = document.getElementById("overall-score");
  const scoreBar = document.getElementById("score-bar");
  if (scoreDisplay) scoreDisplay.innerText = "0.00 / 10";
  if (scoreBar) scoreBar.style.width = "0%";

  const actionsDiv = document.getElementById("screening-actions");
  if (actionsDiv) {
    actionsDiv.innerHTML = `
      <button type="button" id="save-screening"
              class="px-4 py-2 text-sm font-medium border border-gray-300 rounded-lg hover:bg-gray-50">
          Save Evaluation
      </button>
      <button type="button" id="finalize-screening"
              class="px-4 py-2 text-sm font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700">
          Finalize Evaluation
      </button>
    `;
    document.getElementById("save-screening")?.addEventListener("click", () => saveEvaluation());
    document.getElementById("finalize-screening")?.addEventListener("click", () => finalizeEvaluation());
  }
}

/* =========================================================
   TOAST NOTIFICATION
========================================================= */

function showToast(message) {
  const toast = document.createElement("div");
  toast.style.cssText = `
    position: fixed; bottom: 24px; right: 24px;
    background: #1a1a1a; color: white;
    padding: 12px 20px; border-radius: 8px;
    font-size: 14px; font-weight: 500;
    z-index: 9999; opacity: 0;
    transition: opacity 0.3s ease;
  `;
  toast.innerText = message;
  document.body.appendChild(toast);

  requestAnimationFrame(() => { toast.style.opacity = "1"; });
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}


/* =========================================================
   CSRF
========================================================= */

function getCSRFToken() {
  return document.cookie
    .split("; ")
    .find(row => row.startsWith("csrftoken="))
    ?.split("=")[1];
}