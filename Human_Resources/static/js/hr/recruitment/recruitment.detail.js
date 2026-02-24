/* =========================================================
   RECRUITMENT DETAIL PAGE
   Wired to RecruitmentEngine via transition API.
========================================================= */

const STAGES = ['submitted', 'screening', 'interview', 'final_review', 'decision'];

const STAGE_STYLES = {
  submitted:    'background:#6b7280; color:white;',
  screening:    'background:#2563eb; color:white;',
  interview:    'background:#f59e0b; color:white;',
  final_review: 'background:#8b5cf6; color:white;',
  decision:     'background:#ef4444; color:white;',
};

const TERMINAL_STATUSES = ['hire_approved', 'rejected', 'withdrawn', 'closed'];

let currentApp = null;

/* =========================================================
   BOOT
========================================================= */

document.addEventListener("DOMContentLoaded", () => {
  const applicationId = extractApplicationId();
  loadApplication(applicationId);
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
    renderProgressRibbon(data);
    renderActionPanel(data);
    renderEvaluationPanel(data);
    renderFinalReview(data);
    renderDecisionPanel(data);
    switchEvaluationPanel(data.current_stage);
    switchLayout(data.current_stage);
    renderResume(data);
    activateRatingSystem(data.current_stage);

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
   SWITCH EVALUATION PANEL
========================================================= */

function switchEvaluationPanel(stage) {
  const screeningPanel   = document.getElementById('screening-panel');
  const interviewPanel   = document.getElementById('interview-panel');
  const finalReviewPanel = document.getElementById('final-review-panel-wrapper');

  if (screeningPanel)   screeningPanel.style.display   = 'none';
  if (interviewPanel)   interviewPanel.style.display   = 'none';
  if (finalReviewPanel) finalReviewPanel.style.display = 'none';

  if (stage === 'interview') {
    if (interviewPanel) interviewPanel.style.display = 'block';
    document.getElementById('save-interview')
      ?.addEventListener('click', () => saveEvaluation());
    document.getElementById('finalize-interview')
      ?.addEventListener('click', () => finalizeEvaluation());

  } else if (stage === 'final_review') {
    if (finalReviewPanel) finalReviewPanel.style.display = 'block';

  } else if (stage === 'decision') {
    if (finalReviewPanel) finalReviewPanel.style.display = 'block';

  } else {
    if (screeningPanel) screeningPanel.style.display = 'block';
    document.getElementById('save-screening')
      ?.addEventListener('click', () => saveEvaluation());
    document.getElementById('finalize-screening')
      ?.addEventListener('click', () => finalizeEvaluation());
  }
}


/* =========================================================
   SWITCH LAYOUT
========================================================= */

function switchLayout(stage) {
  const leftPanel  = document.getElementById('left-panel');
  const rightPanel = document.getElementById('right-panel');

  if (!leftPanel || !rightPanel) return;

  if (stage === 'final_review' || stage === 'decision') {
    leftPanel.style.display = 'none';
    rightPanel.className    = 'col-span-12 flex flex-col overflow-hidden';
  } else {
    leftPanel.style.display = '';
    rightPanel.className    = 'col-span-12 lg:col-span-5 flex flex-col overflow-hidden';
  }
}


/* =========================================================
   RENDER HEADER
========================================================= */

function renderHeader(data) {
  const fullName = `${data.first_name} ${data.last_name}`;

  document.getElementById("applicant-fullname").innerText = fullName;
  document.getElementById("applicant-role").innerText     = data.role_applied_for || "";
  document.getElementById("applicant-email").innerText    = data.email || "";

  const badge = document.getElementById("current-stage-badge");
  if (badge) {
    badge.innerText = (data.current_stage || "").replace(/_/g, " ").toUpperCase();
  }

  const stageLabel = document.getElementById("cv-stage-label");
  if (stageLabel) {
    stageLabel.innerText = (data.current_stage || "").replace(/_/g, " ").toUpperCase() + " STAGE";
  }
}


/* =========================================================
   RENDER RESUME
========================================================= */

function renderResume(data) {
  const container  = document.getElementById("cv-viewer");
  const panelTitle = document.getElementById("left-panel-title");

  if (!container) return;

  // Final Review / Decision — show candidate profile instead of CV
  if (data.current_stage === 'final_review' || data.current_stage === 'decision') {
    if (panelTitle) panelTitle.innerText = "Candidate Profile";

    const se = data.screening_evaluation;
    const ie = data.interview_evaluation;
    const overallNum = se && ie
      ? (se.weighted_score + ie.weighted_score) / 2
      : (se ? se.weighted_score : ie ? ie.weighted_score : 0);
    const overall        = overallNum.toFixed(2);
    const scoreBarColor  = overallNum >= 7 ? '#22c55e' : overallNum >= 4 ? '#f59e0b' : '#ef4444';
    const scoreTextColor = overallNum >= 7 ? '#15803d' : overallNum >= 4 ? '#b45309' : '#dc2626';

    container.innerHTML = `
      <div style="
        display:flex; flex-direction:column;
        height:100%; padding:32px; gap:24px;
        background:linear-gradient(135deg,#faf5ff,#ffffff);
        overflow-y:auto;
      ">
        <div style="text-align:center; padding-bottom:20px; border-bottom:1px solid #f3f4f6;">
          <div style="
            width:56px; height:56px; border-radius:50%;
            background:linear-gradient(135deg,#e53935,#ef5350);
            color:white; font-size:20px; font-weight:700;
            display:flex; align-items:center; justify-content:center;
            margin:0 auto 12px auto;
          ">${data.first_name.charAt(0)}${data.last_name.charAt(0)}</div>
          <div style="font-size:20px; font-weight:800; color:#0f172a; margin-bottom:4px;">
            ${data.first_name} ${data.last_name}
          </div>
          <div style="font-size:13px; color:#6b7280; margin-bottom:12px;">
            ${data.role_applied_for}
          </div>
          <div style="
            display:inline-block; background:#f3e8ff; color:#7c3aed;
            font-size:11px; font-weight:700; padding:4px 12px;
            border-radius:20px; letter-spacing:0.06em; text-transform:uppercase;
          ">Final Review</div>
        </div>

        <div style="
          background:white; border:1px solid #e5e7eb;
          border-radius:14px; padding:20px; text-align:center;
        ">
          <div style="font-size:11px; font-weight:700; color:#9ca3af;
                      text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px;">
            Composite Score
          </div>
          <div style="font-size:40px; font-weight:800; color:${scoreTextColor};">
            ${overall}
          </div>
          <div style="font-size:12px; color:#9ca3af;">out of 10</div>
          <div style="margin-top:12px; height:6px; background:#f3f4f6; border-radius:99px; overflow:hidden;">
            <div style="
              height:100%; border-radius:99px;
              width:${overallNum / 10 * 100}%;
              background:${scoreBarColor};
              transition:width 0.6s ease;
            "></div>
          </div>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
          <div style="
            background:#eff6ff; border:1px solid #bfdbfe;
            border-radius:12px; padding:16px; text-align:center;
          ">
            <div style="font-size:10px; font-weight:700; color:#3b82f6;
                        text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px;">
              Screening
            </div>
            <div style="font-size:28px; font-weight:800; color:#1d4ed8;">
              ${se ? se.weighted_score.toFixed(1) : '—'}
            </div>
            <div style="font-size:11px; color:#93c5fd;">out of 10</div>
          </div>
          <div style="
            background:#fffbeb; border:1px solid #fde68a;
            border-radius:12px; padding:16px; text-align:center;
          ">
            <div style="font-size:10px; font-weight:700; color:#f59e0b;
                        text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px;">
              Interview
            </div>
            <div style="font-size:28px; font-weight:800; color:#b45309;">
              ${ie ? ie.weighted_score.toFixed(1) : '—'}
            </div>
            <div style="font-size:11px; color:#fcd34d;">out of 10</div>
          </div>
        </div>

        <div style="
          background:white; border:1px solid #e5e7eb;
          border-radius:12px; padding:16px;
          display:flex; flex-direction:column; gap:8px;
        ">
          <div style="display:flex; align-items:center; gap:10px; font-size:12px; color:#4b5563;">
            <span>&#x2709;&#xFE0F;</span> ${data.email}
          </div>
          <div style="display:flex; align-items:center; gap:10px; font-size:12px; color:#4b5563;">
            <span>&#x1F464;</span> Reviewed by ${data.assigned_reviewer || '—'}
          </div>
          <div style="display:flex; align-items:center; gap:10px; font-size:12px; color:#4b5563;">
            <span>&#x1F4C5;</span> Interview: ${data.interview_date ? new Date(data.interview_date).toLocaleString() : '—'}
          </div>
        </div>
      </div>
    `;
    return;
  }

  // Interview — show in-progress placeholder
  if (data.current_stage === 'interview') {
    if (panelTitle) panelTitle.innerText = "Interview";

    container.innerHTML = `
      <div style="
        display:flex; flex-direction:column;
        align-items:center; justify-content:center;
        height:100%; padding:40px; text-align:center;
        background:linear-gradient(135deg,#fffbeb,#ffffff);
      ">
        <div style="font-size:80px; margin-bottom:16px; line-height:1;">&#x1F9D1;&#x200D;&#x1F4BC;&#x1F91D;&#x1F469;&#x200D;&#x1F4BC;</div>
        <h3 style="font-size:18px; font-weight:700; color:#b45309; margin-bottom:8px;">
          Interview In Progress
        </h3>
        <p style="font-size:13px; color:#6b7280; max-width:260px; line-height:1.6;">
          Score the candidate via the evaluation panel.
          Finalize when the interview is complete.
        </p>
        ${data.interview_date ? `
        <div style="
          margin-top:24px; background:white; border:1px solid #e5e7eb;
          border-radius:12px; padding:16px 24px; font-size:13px; color:#374151;
        ">
          <div style="font-weight:600; color:#b45309; margin-bottom:4px;">Scheduled</div>
          <div>${new Date(data.interview_date).toLocaleString()}</div>
        </div>
        ` : ''}
      </div>
    `;
    return;
  }

  // Default — show CV
  if (panelTitle) {
    if (data.current_stage === 'final_review') panelTitle.innerText = "Final Review";
    else if (data.current_stage === 'decision') panelTitle.innerText = "Decision";
    else panelTitle.innerText = "Curriculum Vitae";
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
   RENDER PROGRESS RIBBON
========================================================= */

function renderProgressRibbon(data) {
  const ribbon = document.getElementById("stage-ribbon");
  if (!ribbon) return;

  const currentIndex = STAGES.indexOf(data.current_stage);

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
    return `<div class="flex-1 text-center py-2 text-xs font-semibold uppercase tracking-wide"
                 style="${style}">${label}</div>`;
  }).join('');
}


/* =========================================================
   RENDER EVALUATION PANEL TITLE
========================================================= */

function renderEvaluationPanel(data) {
  const title = document.getElementById("evaluation-panel-title");
  if (title) {
    const stageLabel = (data.current_stage || "screening").replace(/_/g, " ");
    title.innerText = stageLabel.toUpperCase() + " EVALUATION";
  }
}


/* =========================================================
   RENDER FINAL REVIEW PANEL
========================================================= */

function renderFinalReview(data) {
  if (data.current_stage !== 'final_review') return;

  const se = data.screening_evaluation;
  const ie = data.interview_evaluation;

  if (!se && !ie) return;

  const overallNum  = se && ie
    ? (se.weighted_score + ie.weighted_score) / 2
    : (se ? se.weighted_score : ie ? ie.weighted_score : 0);
  const overall     = overallNum.toFixed(2);
  const scoreColor  = overallNum >= 7 ? '#15803d' : overallNum >= 4 ? '#b45309' : '#dc2626';
  const scoreBg     = overallNum >= 7 ? '#dcfce7' : overallNum >= 4 ? '#fef3c7' : '#fee2e2';

  // --- Identity bar ---
  const identityBar = document.getElementById('fr-identity-bar');
  if (identityBar && data.first_name) {
    const initials = data.first_name.charAt(0) + data.last_name.charAt(0);
    identityBar.innerHTML = `
      <div class="flex items-center gap-3">
        <div style="
          width:40px; height:40px; border-radius:50%;
          background:linear-gradient(135deg,#e53935,#ef5350);
          color:white; font-size:14px; font-weight:700;
          display:flex; align-items:center; justify-content:center;
          flex-shrink:0;
        ">${initials}</div>
        <div>
          <div class="text-sm font-bold text-gray-900">${data.first_name} ${data.last_name}</div>
          <div class="text-xs text-gray-500">${data.role_applied_for}</div>
        </div>
      </div>
      <div class="flex items-center gap-3 text-xs text-gray-500">
        <span>${data.email}</span>
        <span class="opacity-30">·</span>
        <span>Reviewed by ${data.assigned_reviewer || '—'}</span>
        <span class="opacity-30">·</span>
        <span>${data.interview_date ? new Date(data.interview_date).toLocaleDateString() : '—'}</span>
      </div>
    `;
  }

  // --- Score pills ---
  const scorePills = document.getElementById('fr-score-pills');
  if (scorePills) {
    scorePills.innerHTML = `
      <div class="flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-100 rounded-xl">
        <span class="text-xs font-semibold text-blue-500 uppercase tracking-wide">Screening</span>
        <span class="text-lg font-bold text-blue-600">${se ? se.weighted_score.toFixed(1) : '—'}</span>
        <span class="text-xs text-blue-400">/ 10</span>
      </div>
      <div class="flex items-center gap-2 px-4 py-2 bg-amber-50 border border-amber-100 rounded-xl">
        <span class="text-xs font-semibold text-amber-500 uppercase tracking-wide">Interview</span>
        <span class="text-lg font-bold text-amber-500">${ie ? ie.weighted_score.toFixed(1) : '—'}</span>
        <span class="text-xs text-amber-400">/ 10</span>
      </div>
      <div class="flex items-center gap-2 px-4 py-2 rounded-xl border"
           style="background:${scoreBg}; border-color:${scoreColor}33;">
        <span class="text-xs font-semibold uppercase tracking-wide" style="color:${scoreColor}">Overall</span>
        <span class="text-lg font-bold" style="color:${scoreColor}">${overall}</span>
        <span class="text-xs" style="color:${scoreColor}88">/ 10</span>
      </div>
      <div class="ml-auto">
        <div class="w-32 bg-gray-100 rounded-full h-2">
          <div style="
            height:100%; border-radius:99px;
            width:${overallNum / 10 * 100}%;
            background:${overallNum >= 7 ? '#22c55e' : overallNum >= 4 ? '#f59e0b' : '#ef4444'};
          "></div>
        </div>
      </div>
    `;
  }

  // --- Screening criteria ---
  const screeningScore = document.getElementById('fr-screening-score');
  if (screeningScore && se) screeningScore.innerText = se.weighted_score.toFixed(1) + ' / 10';

  const screeningCriteria = document.getElementById('fr-screening-criteria');
  if (screeningCriteria && se) {
    screeningCriteria.innerHTML = [
      { label: 'Career Path',       score: se.career_score,     notes: se.career_notes     },
      { label: 'Experience Depth',  score: se.experience_score, notes: se.experience_notes },
      { label: 'Job Stability',     score: se.stability_score,  notes: se.stability_notes  },
      { label: 'Education',         score: se.education_score,  notes: se.education_notes  },
      { label: 'Skills Competency', score: se.skills_score,     notes: se.skills_notes     },
    ].map(c => buildCriterionRow(c)).join('');
  }

  // --- Interview criteria ---
  const interviewScore = document.getElementById('fr-interview-score');
  if (interviewScore && ie) interviewScore.innerText = ie.weighted_score.toFixed(1) + ' / 10';

  const interviewCriteria = document.getElementById('fr-interview-criteria');
  if (interviewCriteria && ie) {
    interviewCriteria.innerHTML = [
      { label: 'Communication',   score: ie.communication_score,   notes: ie.communication_notes   },
      { label: 'Attitude',        score: ie.attitude_score,        notes: ie.attitude_notes        },
      { label: 'Role Knowledge',  score: ie.role_knowledge_score,  notes: ie.role_knowledge_notes  },
      { label: 'Problem Solving', score: ie.problem_solving_score, notes: ie.problem_solving_notes },
      { label: 'Cultural Fit',    score: ie.cultural_fit_score,    notes: ie.cultural_fit_notes    },
    ].map(c => buildCriterionRow(c)).join('');
  }

  // --- Actions ---
  const actions = document.getElementById('final-review-actions');
  if (actions) {
    actions.innerHTML = `
      <div class="flex items-center justify-between w-full">

        <div class="flex items-center gap-3 cursor-pointer" onclick="toggleFRConfirm()">
          <div id="fr-toggle-track" style="
            width:44px; height:24px; border-radius:99px;
            background:#e5e7eb; position:relative;
            transition:background 0.2s ease; cursor:pointer; flex-shrink:0;
          ">
            <div id="fr-toggle-thumb" style="
              width:20px; height:20px; border-radius:50%;
              background:white; box-shadow:0 1px 3px rgba(0,0,0,0.2);
              position:absolute; top:2px; left:2px;
              transition:transform 0.2s ease;
            "></div>
          </div>
          <span id="fr-toggle-label" style="font-size:12px; color:#9ca3af; font-weight:500; cursor:pointer;">
            I confirm this review is complete and accurate
          </span>
        </div>

        <button type="button"
                id="fr-submit-btn"
                disabled
                class="px-5 py-2 text-sm font-semibold text-white rounded-lg
                       bg-gray-300 cursor-not-allowed transition-all duration-200">
          Submit Final Review →
        </button>

      </div>
    `;
  }
}


/* =========================================================
   RENDER DECISION PANEL
========================================================= */

function renderDecisionPanel(data) {
  if (data.current_stage !== 'decision') return;

  const wrapper = document.getElementById('final-review-panel-wrapper');
  if (!wrapper) return;

  const se = data.screening_evaluation;
  const ie = data.interview_evaluation;

  const overallNum     = se && ie
    ? (se.weighted_score + ie.weighted_score) / 2
    : (se ? se.weighted_score : ie ? ie.weighted_score : 0);
  const overall        = overallNum.toFixed(2);
  const scoreTextColor = overallNum >= 7 ? '#15803d' : overallNum >= 4 ? '#b45309' : '#dc2626';
  const scoreBg        = overallNum >= 7 ? '#dcfce7' : overallNum >= 4 ? '#fef3c7' : '#fee2e2';
  const scoreBarColor  = overallNum >= 7 ? '#22c55e' : overallNum >= 4 ? '#f59e0b' : '#ef4444';

  const message     = buildRecommendationMessage(data, overallNum, ie);
  const topCriteria = getTopCriteria(ie);
  const initials    = data.first_name.charAt(0) + data.last_name.charAt(0);

  // Verdict left border color
  const verdictBorder = overallNum >= 8 ? '#16a34a'
    : overallNum >= 6 ? '#9333ea'
    : overallNum >= 4 ? '#f59e0b'
    : '#dc2626';

  // Timeline
  const logs     = data.transition_logs || [];
  const timeline = buildTimeline(logs, data);

  wrapper.innerHTML = `
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">

      <!-- AVATAR + IDENTITY -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50">
        <div class="flex items-center gap-3">
          <div style="
            width:44px; height:44px; border-radius:50%;
            background:linear-gradient(135deg,#e53935,#ef5350);
            color:white; font-size:15px; font-weight:700;
            display:flex; align-items:center; justify-content:center; flex-shrink:0;
          ">${initials}</div>
          <div>
            <div class="text-sm font-bold text-gray-900">${data.first_name} ${data.last_name}</div>
            <div class="text-xs text-gray-500">${data.role_applied_for}</div>
          </div>
        </div>
        <div class="flex items-center gap-3 text-xs text-gray-400">
          <span>${data.email || '—'}</span>
          <span>·</span>
          <span>Reviewed by ${data.assigned_reviewer || '—'}</span>
        </div>
      </div>

      <!-- SCORE PILLS -->
      <div class="flex items-center gap-4 px-6 py-3 border-b border-gray-100">
        <div class="flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-100 rounded-xl">
          <span class="text-xs font-semibold text-blue-500 uppercase tracking-wide">Screening</span>
          <span class="text-lg font-bold text-blue-600">${se ? se.weighted_score.toFixed(1) : '—'}</span>
          <span class="text-xs text-blue-400">/ 10</span>
        </div>
        <div class="flex items-center gap-2 px-4 py-2 bg-amber-50 border border-amber-100 rounded-xl">
          <span class="text-xs font-semibold text-amber-500 uppercase tracking-wide">Interview</span>
          <span class="text-lg font-bold text-amber-500">${ie ? ie.weighted_score.toFixed(1) : '—'}</span>
          <span class="text-xs text-amber-400">/ 10</span>
        </div>
        <div class="flex items-center gap-2 px-4 py-2 rounded-xl border"
             style="background:${scoreBg}; border-color:${scoreTextColor}33;">
          <span class="text-xs font-semibold uppercase tracking-wide" style="color:${scoreTextColor}">Overall</span>
          <span class="text-lg font-bold" style="color:${scoreTextColor}">${overall}</span>
          <span class="text-xs" style="color:${scoreTextColor}88">/ 10</span>
        </div>
        <div class="ml-auto flex items-center gap-2">
          <div class="w-28 bg-gray-100 rounded-full h-2">
            <div style="
              height:100%; border-radius:99px;
              width:${overallNum / 10 * 100}%;
              background:${scoreBarColor};
              transition:width 0.6s ease;
            "></div>
          </div>
        </div>
      </div>

      <!-- MAIN BODY: recommendation + timeline side by side -->
      <div class="grid grid-cols-5 divide-x divide-gray-100">

        <!-- LEFT: Octos Recommendation (3 cols) -->
        <div class="col-span-3 p-6">
          <div class="rounded-xl overflow-hidden border"
               style="border-left: 4px solid ${verdictBorder}; border-color:${verdictBorder}33; border-left-color:${verdictBorder}; background:linear-gradient(135deg,#faf5ff,#f3e8ff);">

            <!-- Card header -->
            <div class="flex items-center gap-3 px-5 py-3 border-b border-purple-100"
                 style="background:rgba(139,92,246,0.08);">
              <div style="
                width:26px; height:26px; border-radius:50%;
                background:linear-gradient(135deg,#7c3aed,#9333ea);
                display:flex; align-items:center; justify-content:center;
                font-size:13px; flex-shrink:0;
              ">⚡</div>
              <span class="text-xs font-bold text-purple-700 uppercase tracking-widest">
                Octos Recommendation
              </span>
              <span class="ml-auto text-xs font-semibold px-2 py-0.5 rounded-full"
                    style="background:${scoreBg}; color:${scoreTextColor};">
                ${message.verdict}
              </span>
            </div>

            <!-- Message -->
            <div class="px-5 py-4">
              <p class="text-sm text-gray-700 leading-relaxed" style="font-style:italic;">
                "${message.text}"
              </p>
              ${topCriteria.length > 0 ? `
              <div class="flex flex-wrap gap-2 mt-4">
                ${topCriteria.map(c => `
                  <div class="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold"
                       style="background:#ede9fe; color:#6d28d9;">
                    <span>★</span><span>${c.label}</span>
                    <span class="opacity-60">${c.score}/5</span>
                  </div>
                `).join('')}
              </div>
              ` : ''}
            </div>
          </div>
        </div>

        <!-- RIGHT: Stage Timeline (2 cols) -->
        <div class="col-span-2 p-6">
          <div class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">
            Pipeline Journey
          </div>
          <div class="relative">
            <!-- Vertical line -->
            <div class="absolute left-3 top-0 bottom-0 w-px bg-gray-200"></div>
            <div class="space-y-5">
              ${timeline}
            </div>
          </div>
        </div>

      </div>

      <!-- DECISION ACTIONS -->
      <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100 bg-gray-50">
        ${data.status === 'active' ? `
          <button type="button"
                  onclick="handleTransition('reject')"
                  class="px-5 py-2 text-sm font-semibold rounded-lg border border-red-200
                         text-red-600 bg-white hover:bg-red-50 transition-all duration-200">
            Reject
          </button>
          <button type="button"
                  onclick="handleTransition('approve')"
                  class="px-5 py-2 text-sm font-semibold text-white rounded-lg
                         bg-green-600 hover:bg-green-700 transition-all duration-200">
            Extend Offer →
          </button>
        ` : data.status === 'offer_extended' ? `
          <button type="button"
                  onclick="handleTransition('withdraw_offer')"
                  class="px-5 py-2 text-sm font-semibold rounded-lg border border-orange-200
                         text-orange-600 bg-white hover:bg-orange-50 transition-all duration-200">
            Withdraw Offer
          </button>
          <button type="button"
                  onclick="handleTransition('decline_offer')"
                  class="px-5 py-2 text-sm font-semibold rounded-lg border border-red-200
                         text-red-600 bg-white hover:bg-red-50 transition-all duration-200">
            Declined by Candidate
          </button>
          <button type="button"
                  onclick="handleTransition('accept_offer')"
                  class="px-5 py-2 text-sm font-semibold text-white rounded-lg
                         bg-green-600 hover:bg-green-700 transition-all duration-200">
            Accepted by Candidate ✓
          </button>
        ` : `
          <div class="text-sm font-medium text-gray-400 py-2">
            This application has been closed.
          </div>
        `}
      </div>

    </div>
  `;
}


/* =========================================================
   STAGE TIMELINE BUILDER
========================================================= */

function buildTimeline(logs, data) {
  if (!logs || logs.length === 0) {
    return `<p class="text-xs text-gray-400 pl-8">No transition history yet.</p>`;
  }

  const stageColors = {
    submitted:    { dot: '#6b7280', bg: '#f3f4f6', text: '#374151' },
    screening:    { dot: '#2563eb', bg: '#eff6ff', text: '#1d4ed8' },
    interview:    { dot: '#f59e0b', bg: '#fffbeb', text: '#b45309' },
    final_review: { dot: '#8b5cf6', bg: '#f5f3ff', text: '#6d28d9' },
    decision:     { dot: '#ef4444', bg: '#fef2f2', text: '#dc2626' },
  };

  // Get score for each stage from evaluations
  const stageScores = {
    screening:    data.screening_evaluation?.weighted_score,
    interview:    data.interview_evaluation?.weighted_score,
    final_review: null,
  };

  return logs.map((log, index) => {
    const colors   = stageColors[log.new_stage] || stageColors.submitted;
    const label    = log.new_stage.replace(/_/g, ' ');
    const date     = new Date(log.created_at).toLocaleDateString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric'
    });
    const score    = stageScores[log.new_stage];
    const duration = formatDuration(log.duration_seconds);
    const isLast   = index === logs.length - 1;

    return `
      <div class="relative pl-8">
        <!-- Dot -->
        <div style="
          position:absolute; left:0; top:3px;
          width:14px; height:14px; border-radius:50%;
          background:${colors.dot}; border:2px solid white;
          box-shadow:0 0 0 2px ${colors.dot}33;
          z-index:1;
        "></div>

        <!-- Content -->
        <div class="mb-1 flex items-center gap-2 flex-wrap">
          <span class="text-xs font-bold uppercase tracking-wide"
                style="color:${colors.text};">${label}</span>
          ${score != null ? `
            <span class="text-xs font-semibold px-1.5 py-0.5 rounded-full"
                  style="background:${colors.bg}; color:${colors.text};">
              ${score.toFixed(1)} / 10
            </span>
          ` : ''}
        </div>
        <div class="text-xs text-gray-500">${date}</div>
        <div class="text-xs text-gray-400">by ${log.performed_by}</div>
        <div class="text-xs text-gray-400 mt-0.5">
          ⏱ ${duration} in previous stage
        </div>
      </div>
    `;
  }).join('');
}


/* =========================================================
   DURATION FORMATTER
========================================================= */

function formatDuration(seconds) {
  if (seconds < 60)   return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  const days  = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  return hours > 0 ? `${days}d ${hours}h` : `${days}d`;
}


/* =========================================================
   RECOMMENDATION MESSAGE BUILDER
========================================================= */

function buildRecommendationMessage(data, overallNum, ie) {
  const firstName      = data.first_name;
  const fullName       = `${data.first_name} ${data.last_name}`;
  const role           = data.role_applied_for || 'the role';
  const branch         = data.branch_name || 'your branch';
  const reviewer       = data.assigned_reviewer || 'the reviewer';
  const reviewerFirst  = reviewer.split(' ')[0];

  // Gender pronoun
  const gender  = (data.gender || '').toLowerCase();
  const pronoun = gender === 'female' ? 'She' : gender === 'male' ? 'He' : 'They';

  // Verdict based on overall score
  let verdict, opening;
  if (overallNum >= 8) {
    verdict = 'Strongly Recommended';
    opening = `Octos strongly recommends ${fullName}.`;
  } else if (overallNum >= 6) {
    verdict = 'Recommended';
    opening = `Octos recommends ${fullName} for consideration.`;
  } else if (overallNum >= 4) {
    verdict = 'Borderline';
    opening = `Octos notes that ${fullName} presents a borderline profile.`;
  } else {
    verdict = 'Not Recommended';
    opening = `Octos does not recommend advancing ${fullName} at this time.`;
  }

  // Best interview criterion
  let strengthStatement = '';
  if (ie) {
    const interviewCriteria = [
      { label: 'communication',   score: ie.communication_score   },
      { label: 'attitude',        score: ie.attitude_score        },
      { label: 'role knowledge',  score: ie.role_knowledge_score  },
      { label: 'problem solving', score: ie.problem_solving_score },
      { label: 'cultural fit',    score: ie.cultural_fit_score    },
    ].filter(c => c.score != null);

    if (interviewCriteria.length > 0) {
      const best = interviewCriteria.reduce((a, b) => a.score >= b.score ? a : b);
      strengthStatement = ` ${pronoun} demonstrated a strong sense of ${best.label} during the interview process.`;
    }
  }

  const branchStatement  = ` ${firstName} could be a strong addition to ${branch} as ${role}.`;
  const closingStatement = ` But the ball is in your court, ${reviewerFirst}.`;

  return {
    verdict,
    text: opening + strengthStatement + branchStatement + closingStatement,
  };
}


/* =========================================================
   TOP CRITERIA EXTRACTOR
   Returns top 3 interview criteria by score
========================================================= */

function getTopCriteria(ie) {
  if (!ie) return [];

  return [
    { label: 'Communication',   score: ie.communication_score   },
    { label: 'Attitude',        score: ie.attitude_score        },
    { label: 'Role Knowledge',  score: ie.role_knowledge_score  },
    { label: 'Problem Solving', score: ie.problem_solving_score },
    { label: 'Cultural Fit',    score: ie.cultural_fit_score    },
  ]
  .filter(c => c.score != null && c.score >= 4)
  .sort((a, b) => b.score - a.score)
  .slice(0, 3);
}


/* =========================================================
   CRITERION ROW BUILDER
========================================================= */

function buildCriterionRow(criterion) {
  const score = criterion.score || 0;
  const label = scoreLabel(score);
  const color = scoreColor(score);

  return `
    <div style="border-left: 4px solid ${color.border};"
         class="bg-gray-50 rounded-lg p-3 border border-gray-100 rounded-l-none">
      <div class="flex justify-between items-center mb-1">
        <span class="text-xs font-semibold text-gray-700">${criterion.label}</span>
        <span class="text-xs font-bold px-2 py-0.5 rounded-full"
              style="background:${color.bg}; color:${color.text}">
          ${label} &middot; ${score}/5
        </span>
      </div>
      ${criterion.notes ? `<p class="text-xs text-gray-500 leading-relaxed mt-1">${criterion.notes}</p>` : ''}
    </div>
  `;
}

function scoreLabel(score) {
  if (score >= 5) return 'Excellent';
  if (score >= 4) return 'Strong';
  if (score >= 3) return 'Acceptable';
  if (score >= 2) return 'Weak';
  return 'Poor';
}

function scoreColor(score) {
  if (score >= 5) return { bg: '#d1fae5', text: '#065f46', border: '#22c55e' };
  if (score >= 4) return { bg: '#dcfce7', text: '#15803d', border: '#86efac' };
  if (score >= 3) return { bg: '#dbeafe', text: '#1d4ed8', border: '#60a5fa' };
  if (score >= 2) return { bg: '#fef3c7', text: '#b45309', border: '#fbbf24' };
  return { bg: '#fee2e2', text: '#dc2626', border: '#f87171' };
}


/* =========================================================
   RENDER ACTION PANEL
========================================================= */

function renderActionPanel(data) {
  const panel = document.getElementById("action-panel");
  if (!panel) return;

  const stage  = data.current_stage;
  const status = data.status;

  // Decision stage actions are now inside the decision panel itself
  if (stage === 'decision') {
    panel.innerHTML = '';
    return;
  }

  if (TERMINAL_STATUSES.includes(status)) {
    const messages = {
      hire_approved: "Candidate hired. Onboarding initiated.",
      rejected:      "Application rejected.",
      withdrawn:     "Offer withdrawn.",
      closed:        "Application closed.",
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
  } else if (stage === 'screening' || stage === 'interview' || stage === 'final_review') {
    panel.innerHTML = '';
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
    renderFinalReview(updated);
    renderDecisionPanel(updated);
    switchEvaluationPanel(updated.current_stage);
    switchLayout(updated.current_stage);
    renderResume(updated);
    activateRatingSystem(updated.current_stage);
    resetEvaluationUI();

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

    const data   = await response.json();
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
    ?.addEventListener("click", () => saveEvaluation());

  document.getElementById("finalize-screening")
    ?.addEventListener("click", () => finalizeEvaluation());

});


/* =========================================================
   SAVE EVALUATION
========================================================= */

async function saveEvaluation() {
  if (!currentApp) return;

  const stage   = currentApp.current_stage;
  const panelId = stage === 'interview' ? 'interview-panel' : 'screening-panel';
  const panel   = document.getElementById(panelId);
  if (!panel) return;

  const ratingGroups = panel.querySelectorAll(".rating-group");
  const textareas    = panel.querySelectorAll("textarea");

  const getScore = (index) => {
    const group = ratingGroups[index];
    return group?.dataset.score ? parseFloat(group.dataset.score) : null;
  };

  let payload = { stage };

  if (stage === 'interview') {
    payload = {
      ...payload,
      communication_score:   getScore(0),
      communication_notes:   textareas[0]?.value || "",
      attitude_score:        getScore(1),
      attitude_notes:        textareas[1]?.value || "",
      role_knowledge_score:  getScore(2),
      role_knowledge_notes:  textareas[2]?.value || "",
      problem_solving_score: getScore(3),
      problem_solving_notes: textareas[3]?.value || "",
      cultural_fit_score:    getScore(4),
      cultural_fit_notes:    textareas[4]?.value || "",
    };
  } else {
    payload = {
      ...payload,
      career_score:     getScore(0),
      career_notes:     textareas[0]?.value || "",
      experience_score: getScore(1),
      experience_notes: textareas[1]?.value || "",
      stability_score:  getScore(2),
      stability_notes:  textareas[2]?.value || "",
      education_score:  getScore(3),
      education_notes:  textareas[3]?.value || "",
      skills_score:     getScore(4),
      skills_notes:     textareas[4]?.value || "",
    };
  }

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
      screening:    "Evaluation finalized. Schedule the interview to proceed.",
      interview:    "Interview scored. Click Complete Interview to advance.",
      final_review: "Review finalized. Submit to proceed to decision.",
    };

    showToast(toastMessages[stage] || "Evaluation finalized.");
    lockEvaluationUI();

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
    position:fixed; inset:0; background:rgba(0,0,0,0.5);
    display:flex; align-items:center; justify-content:center;
    z-index:1000; opacity:0; transition:opacity 0.3s ease;
  `;

  modal.innerHTML = `
    <div style="
      background:white; border-radius:16px; padding:48px 40px;
      max-width:480px; width:90%; text-align:center;
      box-shadow:0 20px 60px rgba(0,0,0,0.2);
      transform:translateY(20px); transition:transform 0.3s ease;
    " id="hire-modal-card">
      <div style="font-size:64px; margin-bottom:16px;">&#x1F389;</div>
      <h2 style="font-size:28px; font-weight:700; color:#111; margin-bottom:12px;">Congratulations!</h2>
      <p style="font-size:15px; color:#555; line-height:1.6; margin-bottom:32px;">
        <strong>${app.first_name} ${app.last_name}</strong> has been successfully hired
        as <strong>${app.role_applied_for}</strong>.
        Their onboarding record has been created and is ready to begin.
      </p>
      <div style="display:flex; flex-direction:column; gap:12px;">
        <button id="btn-start-onboarding" style="
          background:#e53935; color:white; border:none;
          padding:14px 24px; border-radius:8px;
          font-size:15px; font-weight:600; cursor:pointer;">
          Start Onboarding Now
        </button>
        <button id="btn-onboard-later" style="
          background:transparent; color:#888;
          border:1px solid #ddd; padding:12px 24px;
          border-radius:8px; font-size:14px; cursor:pointer;">
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

  document.getElementById("btn-onboard-later").addEventListener("click", () => modal.remove());
  modal.addEventListener("click", (e) => { if (e.target === modal) modal.remove(); });
}


/* =========================================================
   ACTIVATE RATING SYSTEM
========================================================= */

function activateRatingSystem(stage) {
  const panelId = stage === 'interview' ? 'interview-panel' : 'screening-panel';
  const panel   = document.getElementById(panelId);
  if (!panel) return;

  const scoreDisplay = document.getElementById(
    stage === 'interview' ? 'interview-overall-score' : 'overall-score'
  );
  const scoreBar = document.getElementById(
    stage === 'interview' ? 'interview-score-bar' : 'score-bar'
  );

  panel.removeEventListener('click', panel._ratingHandler);

  panel._ratingHandler = function(e) {
    const btn = e.target.closest('.rating-btn');
    if (!btn || btn.disabled) return;

    const group = btn.closest('.rating-group');
    if (!group) return;

    const buttons = group.querySelectorAll('.rating-btn');
    buttons.forEach(b => b.classList.remove('ring-2', 'ring-offset-1', 'ring-black', 'scale-105'));
    btn.classList.add('ring-2', 'ring-offset-1', 'ring-black', 'scale-105');

    const index = Array.from(buttons).indexOf(btn);
    group.dataset.score = 5 - index;

    updateOverallScore();
  };

  panel.addEventListener('click', panel._ratingHandler);

  function updateOverallScore() {
    const ratingGroups = panel.querySelectorAll('.rating-group');
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
      scoreBar.style.width   = "0%";
      return;
    }

    const finalScore = (total / count / 5) * 10;
    scoreDisplay.innerText = finalScore.toFixed(2) + " / 10";
    scoreBar.style.width   = ((finalScore / 10) * 100) + "%";
  }
}


/* =========================================================
   HYDRATE EVALUATION
========================================================= */

function hydrateEvaluation(evaluation) {
  const stage   = evaluation.stage;
  const panelId = stage === 'interview' ? 'interview-panel' : 'screening-panel';
  const panel   = document.getElementById(panelId);
  if (!panel) return;

  const ratingGroups = panel.querySelectorAll('.rating-group');
  const textareas    = panel.querySelectorAll('textarea');

  const scoreDisplay = document.getElementById(
    stage === 'interview' ? 'interview-overall-score' : 'overall-score'
  );
  const scoreBar = document.getElementById(
    stage === 'interview' ? 'interview-score-bar' : 'score-bar'
  );

  const scores = stage === 'interview' ? [
    evaluation.communication_score,
    evaluation.attitude_score,
    evaluation.role_knowledge_score,
    evaluation.problem_solving_score,
    evaluation.cultural_fit_score,
  ] : [
    evaluation.career_score,
    evaluation.experience_score,
    evaluation.stability_score,
    evaluation.education_score,
    evaluation.skills_score,
  ];

  const notes = stage === 'interview' ? [
    evaluation.communication_notes,
    evaluation.attitude_notes,
    evaluation.role_knowledge_notes,
    evaluation.problem_solving_notes,
    evaluation.cultural_fit_notes,
  ] : [
    evaluation.career_notes,
    evaluation.experience_notes,
    evaluation.stability_notes,
    evaluation.education_notes,
    evaluation.skills_notes,
  ];

  ratingGroups.forEach((group, index) => {
    const score = scores[index];
    if (!score) return;
    const buttons     = group.querySelectorAll('.rating-btn');
    const buttonIndex = 5 - score;
    if (buttons[buttonIndex]) {
      buttons[buttonIndex].classList.add('ring-2', 'ring-offset-1', 'ring-black', 'scale-105');
      group.dataset.score = score;
    }
  });

  textareas.forEach((area, index) => { area.value = notes[index] || ''; });

  if (evaluation.weighted_score && scoreDisplay && scoreBar) {
    scoreDisplay.innerText = evaluation.weighted_score.toFixed(2) + ' / 10';
    scoreBar.style.width   = ((evaluation.weighted_score / 10) * 100) + '%';
  }
}


/* =========================================================
   LOCK EVALUATION UI
========================================================= */

function lockEvaluationUI() {
  const stage = currentApp?.current_stage;

  const panelId   = stage === 'interview' ? 'interview-evaluation-panel' : 'evaluation-panel';
  const actionsId = stage === 'interview' ? 'interview-actions' : 'screening-actions';

  const panel = document.getElementById(panelId);
  if (panel) {
    panel.style.pointerEvents = "none";
    panel.style.opacity       = "0.85";
  }

  const actionsDiv = document.getElementById(actionsId);
  if (!actionsDiv) return;

  if (stage === 'screening') {
    actionsDiv.innerHTML = `
      <button type="button"
              onclick="openInterviewModal()"
              style="pointer-events:auto;"
              class="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700">
        Schedule Interview
      </button>
    `;
  } else if (stage === 'interview') {
    actionsDiv.innerHTML = `
      <button type="button"
              onclick="handleTransition('complete_interview')"
              style="pointer-events:auto;"
              class="px-4 py-2 text-sm font-semibold text-white bg-amber-500 rounded-lg hover:bg-amber-600">
        Complete Interview
      </button>
    `;
  } else if (stage === 'final_review') {
    actionsDiv.innerHTML = `
      <button type="button"
              onclick="handleTransition('submit_final_review')"
              style="pointer-events:auto;"
              class="px-4 py-2 text-sm font-semibold text-white bg-purple-600 rounded-lg hover:bg-purple-700">
        Submit Final Review
      </button>
    `;
  }

  actionsDiv.style.pointerEvents = "auto";
}


/* =========================================================
   RESET EVALUATION UI
========================================================= */

function resetEvaluationUI() {
  const panel = document.getElementById("evaluation-panel");
  if (panel) {
    panel.style.pointerEvents = "auto";
    panel.style.opacity       = "1";
  }

  document.querySelectorAll(".rating-btn").forEach(btn => {
    btn.disabled = false;
    btn.classList.remove("opacity-60", "cursor-not-allowed", "ring-2", "ring-offset-1", "ring-black", "scale-105");
  });

  document.querySelectorAll("textarea").forEach(area => {
    area.value    = "";
    area.disabled = false;
    area.classList.remove("bg-gray-100");
  });

  document.querySelectorAll(".rating-group").forEach(group => {
    delete group.dataset.score;
  });

  const scoreDisplay = document.getElementById("overall-score");
  const scoreBar     = document.getElementById("score-bar");
  if (scoreDisplay) scoreDisplay.innerText = "0.00 / 10";
  if (scoreBar)     scoreBar.style.width   = "0%";

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
   TOAST
========================================================= */

function showToast(message) {
  const toast = document.createElement("div");
  toast.style.cssText = `
    position:fixed; bottom:24px; right:24px;
    background:#1a1a1a; color:white;
    padding:12px 20px; border-radius:8px;
    font-size:14px; font-weight:500;
    z-index:9999; opacity:0;
    transition:opacity 0.3s ease;
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
   FINAL REVIEW CONFIRM TOGGLE
========================================================= */

let frToggleState = false;

function toggleFRConfirm() {
  frToggleState = !frToggleState;

  const track = document.getElementById('fr-toggle-track');
  const thumb = document.getElementById('fr-toggle-thumb');
  const label = document.getElementById('fr-toggle-label');
  const btn   = document.getElementById('fr-submit-btn');

  if (!track || !thumb || !btn) return;

  if (frToggleState) {
    track.style.background = '#9333ea';
    thumb.style.transform  = 'translateX(20px)';
    label.style.color      = '#7c3aed';
    btn.disabled           = false;
    btn.onclick            = () => handleTransition('submit_final_review');
    btn.className = 'px-5 py-2 text-sm font-semibold text-white rounded-lg bg-purple-600 hover:bg-purple-700 cursor-pointer transition-all duration-200';
  } else {
    track.style.background = '#e5e7eb';
    thumb.style.transform  = 'translateX(0)';
    label.style.color      = '#9ca3af';
    btn.disabled           = true;
    btn.onclick            = null;
    btn.className = 'px-5 py-2 text-sm font-semibold text-white rounded-lg bg-gray-300 cursor-not-allowed transition-all duration-200';
  }
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