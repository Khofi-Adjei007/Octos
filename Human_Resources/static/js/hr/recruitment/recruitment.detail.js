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

    if (data.evaluation) {
      hydrateEvaluation(data.evaluation);
      if (data.evaluation.is_finalized) {
        lockEvaluationUI();
      }
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
  if (!container) return;

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

  ribbon.innerHTML = STAGES.map((stage, index) => {
    let classes = "flex-1 text-center py-2 text-xs font-semibold uppercase tracking-wide ";

    if (index < currentIndex) {
      classes += "bg-green-500 text-white";
    } else if (index === currentIndex) {
      const color = STAGE_COLORS[stage] || { bg: 'bg-blue-600', text: 'text-white' };
      classes += `${color.bg} ${color.text}`;
    } else {
      classes += "bg-gray-100 text-gray-400";
    }

    const label = stage.replace(/_/g, " ");
    return `<div class="${classes}">${label}</div>`;
  }).join('');
}


/* =========================================================
   RENDER EVALUATION PANEL
   Updates title and labels based on current stage
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

  // Terminal state
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
    panel.innerHTML = `
      <button onclick="openInterviewModal()"
        class="action-btn bg-blue-600 text-white hover:bg-blue-700"
        id="proceed-interview">
        Schedule Interview
      </button>
      <button onclick="handleTransition('reject')"
        class="action-btn bg-red-100 text-red-600 hover:bg-red-200">
        Reject
      </button>
    `;
  }

  else if (stage === 'interview') {
    panel.innerHTML = `
      <button onclick="handleTransition('complete_interview')"
        class="action-btn bg-blue-600 text-white hover:bg-blue-700">
        Complete Interview
      </button>
      <button onclick="handleTransition('reject')"
        class="action-btn bg-red-100 text-red-600 hover:bg-red-200">
        Reject
      </button>
    `;
  }

  else if (stage === 'final_review') {
    panel.innerHTML = `
      <button onclick="handleTransition('submit_final_review')"
        class="action-btn bg-purple-600 text-white hover:bg-purple-700">
        Submit Final Review
      </button>
      <button onclick="handleTransition('reject')"
        class="action-btn bg-red-100 text-red-600 hover:bg-red-200">
        Reject
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

function openInterviewModal() {
  const modal = document.getElementById("interview-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.classList.add("flex");
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
      const dateInput = document.getElementById("interview-date");
      const interviewDate = dateInput?.value;

      if (!interviewDate) {
        alert("Please select an interview date.");
        return;
      }

      closeInterviewModal();

      await handleTransition("schedule_interview", {
        interview_date: new Date(interviewDate).toISOString()
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

    showToast("Evaluation finalized.");
    lockEvaluationUI();
    await loadApplication(currentApp.id);

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
  document.querySelectorAll(".rating-btn").forEach(btn => {
    btn.disabled = true;
    btn.classList.add("opacity-60", "cursor-not-allowed");
  });

  document.querySelectorAll("textarea").forEach(area => {
    area.disabled = true;
    area.classList.add("bg-gray-100");
  });

  const saveBtn = document.getElementById("save-screening");
  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.classList.add("opacity-50", "cursor-not-allowed");
  }

  const finalizeBtn = document.getElementById("finalize-screening");
  if (finalizeBtn) {
    finalizeBtn.disabled = true;
    finalizeBtn.classList.add("opacity-50", "cursor-not-allowed");
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