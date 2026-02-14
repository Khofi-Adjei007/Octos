document.addEventListener("DOMContentLoaded", () => {
    const applicationId = extractApplicationId();
    loadApplication(applicationId);

    activateRatingSystem();
    setupInterviewModal(applicationId); // ✅ FIXED

    const saveBtn = document.getElementById("save-screening");
    if (saveBtn) {
        saveBtn.addEventListener("click", () => {
            saveScreeningEvaluation(applicationId);
        });
    }
});


function extractApplicationId() {
    const parts = window.location.pathname.split("/").filter(Boolean);
    return parts[parts.length - 1];
}


async function loadApplication(applicationId) {
    try {
        const response = await fetch(`/hr/api/applications/${applicationId}/`);

        if (!response.ok) {
            throw new Error("Failed to fetch application");
        }

        const data = await response.json();

        renderHeader(data);
        renderResume(data);
        renderStageInfo(data);

        if (data.evaluation) {
            hydrateEvaluation(data.evaluation);

            if (data.evaluation.is_finalized) {
                lockScreeningUI();
            }
        }

    } catch (error) {
        console.error("Error loading application:", error);
    }
}


function renderHeader(data) {
    const fullName = `${data.first_name} ${data.last_name}`;

    document.getElementById("applicant-fullname").innerText = fullName;
    document.getElementById("applicant-role").innerText = data.role_applied_for;
    document.getElementById("applicant-email").innerText = data.email || "";

    const badge = document.getElementById("current-stage-badge");
    badge.innerText = data.current_stage.toUpperCase();
}


function renderResume(data) {
    const container = document.getElementById("cv-viewer");

    if (!data.resume_url) {
        container.innerHTML = `
            <div class="text-gray-400 flex items-center justify-center h-full">
                No resume uploaded.
            </div>
        `;
        return;
    }

    container.className =
        "flex-1 w-full border border-gray-200 rounded-md bg-white overflow-hidden";

    container.innerHTML = `
        <iframe
            src="${data.resume_url}"
            class="w-full h-full"
            style="border:none;"
            loading="lazy">
        </iframe>
    `;
}


function renderStageInfo(data) {
    const container = document.getElementById("stage-content");
    if (!container) return;

    container.innerHTML = `
        <div class="text-sm text-gray-600">
            Current Stage: <strong>${data.current_stage}</strong>
        </div>
    `;
}


/* ======================================
   RATING SYSTEM ACTIVATION
====================================== */

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
                count += 1;
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

        const percent = (finalScore / 10) * 100;
        scoreBar.style.width = percent + "%";
    }
}


/* ======================================
   HYDRATE SAVED EVALUATION
====================================== */

function hydrateEvaluation(evaluation) {

    const ratingGroups = document.querySelectorAll(".rating-group");
    const scoreDisplay = document.getElementById("overall-score");
    const scoreBar = document.getElementById("score-bar");

    const scores = [
        evaluation.career_score,
        evaluation.experience_score,
        evaluation.stability_score,
        evaluation.education_score,
        evaluation.skills_score
    ];

    ratingGroups.forEach((group, index) => {

        const score = scores[index];
        if (!score) return;

        const buttons = group.querySelectorAll(".rating-btn");
        const buttonIndex = 5 - score;

        if (buttons[buttonIndex]) {
            buttons[buttonIndex].classList.add(
                "ring-2",
                "ring-offset-1",
                "ring-black",
                "scale-105"
            );
            group.dataset.score = score;
        }
    });

    if (evaluation.weighted_score && scoreDisplay && scoreBar) {

        const finalScore = (evaluation.weighted_score / 5) * 10;

        scoreDisplay.innerText = finalScore.toFixed(2) + " / 10";

        const percent = (finalScore / 10) * 100;
        scoreBar.style.width = percent + "%";
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


/* ======================================
   LOCK SCREENING UI (FINALIZED)
====================================== */

function lockScreeningUI() {

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

    const proceedBtn = document.getElementById("proceed-interview");
    if (proceedBtn) {
        proceedBtn.disabled = false;
        proceedBtn.classList.remove("opacity-50", "cursor-not-allowed");
    }
}


/* ======================================
   INTERVIEW MODAL LOGIC
====================================== */

function setupInterviewModal(applicationId) {

    const openBtn = document.getElementById("proceed-interview");
    const modal = document.getElementById("interview-modal");
    const closeBtn = document.getElementById("close-interview-modal");
    const cancelBtn = document.getElementById("cancel-interview");

    if (!openBtn || !modal) return;

    openBtn.addEventListener("click", () => {
        modal.classList.remove("hidden");
        modal.classList.add("flex");
    });

    const closeModal = () => {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
    };

    closeBtn?.addEventListener("click", closeModal);
    cancelBtn?.addEventListener("click", closeModal);
}


/* ===========================
   SCREENING SAVE LOGIC
=========================== */

async function saveScreeningEvaluation(applicationId) {

    const ratingGroups = document.querySelectorAll(".rating-group");
    const textareas = document.querySelectorAll("textarea");

    const getScore = (index) => {
        const group = ratingGroups[index];
        return group && group.dataset.score
            ? parseFloat(group.dataset.score)
            : null;
    };

    const payload = {
        stage: "screening",
        career_score: getScore(0),
        career_notes: textareas[0]?.value || "",
        experience_score: getScore(1),
        experience_notes: textareas[1]?.value || "",
        stability_score: getScore(2),
        stability_notes: textareas[2]?.value || "",
        education_score: getScore(3),
        education_notes: textareas[3]?.value || "",
        skills_score: getScore(4),
        skills_notes: textareas[4]?.value || ""
    };

    try {
        const response = await fetch(
            `/hr/api/applications/${applicationId}/evaluate/`,
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
            const errorData = await response.json();
            alert(errorData.detail || "Failed to save evaluation.");
            return;
        }

        alert("Screening evaluation saved successfully.");

    } catch (error) {
        alert("Error saving evaluation.");
    }
}


function getCSRFToken() {
    return document.cookie
        .split("; ")
        .find(row => row.startsWith("csrftoken="))
        ?.split("=")[1];
}
