document.addEventListener("DOMContentLoaded", () => {
    const applicationId = extractApplicationId();
    loadApplication(applicationId);
});


function extractApplicationId() {
    // URL example: /hr/applications/1/
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
            <div class="text-gray-400">
                No resume uploaded.
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <iframe 
            src="${data.resume_url}" 
            class="w-full h-full rounded"
        ></iframe>
    `;
}


function renderStageInfo(data) {
    const container = document.getElementById("stage-content");

    container.innerHTML = `
        <div class="text-sm text-gray-600">
            Current Stage: <strong>${data.current_stage}</strong>
        </div>
        <div class="mt-2 text-sm text-gray-600">
            Evaluation: ${
                data.evaluation
                    ? "Saved"
                    : "Not yet completed"
            }
        </div>
    `;
}


