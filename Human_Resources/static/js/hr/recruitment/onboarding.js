/* =========================================================
   ONBOARDING PAGE
   Drives the three-phase onboarding flow.
   All data fetched from onboarding status API.
========================================================= */

const PHASES = [
    { number: 1, label: 'Setup',         owner: 'HR'             },
    { number: 2, label: 'Documentation', owner: 'HR'             },
    { number: 3, label: 'Confirmation',  owner: 'Branch Manager' },
];

let currentRecord = null;
let applicationId  = null;

/* =========================================================
   BOOT
========================================================= */

document.addEventListener('DOMContentLoaded', async () => {
    applicationId = extractApplicationId();
    await initiateOnboarding(applicationId);
    await loadOnboarding(applicationId);
});

function extractApplicationId() {
    const parts = window.location.pathname.split('/').filter(Boolean);
    return parts[parts.length - 1];
}

/* =========================================================
   INITIATE
========================================================= */

async function initiateOnboarding(appId) {
    try {
        await fetch(`/hr/api/onboarding/${appId}/initiate/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            }
        });
    } catch (err) {
        console.error('Initiate error:', err);
    }
}

/* =========================================================
   LOAD STATUS
========================================================= */

async function loadOnboarding(appId) {
    try {
        const response = await fetch(`/hr/api/onboarding/${appId}/status/`);
        if (!response.ok) throw new Error('Failed to load onboarding status');

        const data = await response.json();
        currentRecord = data;

        renderHeader(data);
        renderPhaseRibbon(data);
        renderPhaseContent(data);

    } catch (err) {
        console.error('Load error:', err);
        document.getElementById('phase-content').innerHTML = `
            <div class="text-center text-red-400 py-12">
                Failed to load onboarding record. Please refresh.
            </div>
        `;
    }
}

/* =========================================================
   RENDER HEADER
========================================================= */

function renderHeader(data) {
    document.getElementById('onboarding-name').innerText = data.applicant || '—';
    document.getElementById('onboarding-role').innerText = data.role || '—';

    const badge = document.getElementById('onboarding-status-badge');
    const statusColors = {
        pending:     'bg-gray-100 text-gray-600 border-gray-200',
        in_progress: 'bg-blue-100 text-blue-700 border-blue-200',
        completed:   'bg-green-100 text-green-700 border-green-200',
        stalled:     'bg-red-100 text-red-600 border-red-200',
    };
    badge.className = `inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold uppercase border ${statusColors[data.status] || statusColors.pending}`;
    badge.innerText = (data.status || '—').replace(/_/g, ' ');
}

/* =========================================================
   RENDER PHASE RIBBON
========================================================= */

function renderPhaseRibbon(data) {
    const ribbon = document.getElementById('phase-ribbon');
    if (!ribbon) return;

    ribbon.innerHTML = PHASES.map(phase => {
        const phaseData = data.phases?.find(p => p.phase_number === phase.number);
        const status = phaseData?.status || 'pending';

        let classes = 'flex-1 text-center py-2 text-xs font-semibold uppercase tracking-wide ';

        if (status === 'completed') {
            classes += 'bg-green-500 text-white';
        } else if (phase.number === data.current_phase && data.status !== 'completed') {
            classes += 'bg-blue-600 text-white';
        } else {
            classes += 'bg-gray-100 text-gray-400';
        }

        return `<div class="${classes}">Phase ${phase.number} — ${phase.label}</div>`;
    }).join('');
}

/* =========================================================
   RENDER PHASE CONTENT
========================================================= */

function renderPhaseContent(data) {
    const container = document.getElementById('phase-content');

    if (data.status === 'completed') {
        container.innerHTML = `
            <div class="text-center py-16">
                <div style="font-size:64px; margin-bottom:16px;">🎊</div>
                <h2 class="text-2xl font-bold text-gray-800 mb-3">Onboarding Complete</h2>
                <p class="text-gray-500 text-sm">
                    ${data.applicant} is now fully active in the system.
                </p>
                <p class="text-xs text-gray-400 mt-2">
                    Completed on ${formatDateTime(data.completed_at)}
                </p>
            </div>
        `;
        return;
    }

    const phase = data.current_phase;
    if (phase === 1) renderPhaseOne(data);
    else if (phase === 2) renderPhaseTwo(data);
    else if (phase === 3) renderPhaseThree(data);
}

/* =========================================================
   PHASE 1 — SETUP
========================================================= */

function renderPhaseOne(data) {
    document.getElementById('phase-content').innerHTML = `
        <div class="mb-8">
            <h2 class="text-lg font-semibold text-gray-800">Phase 1 — Setup</h2>
            <p class="text-sm text-gray-500 mt-1">Complete personal information and branch assignment.</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

            <div class="field-group">
                <label class="field-label">House Number</label>
                <input type="text" id="f1-house-number" class="field-input"
                       placeholder="e.g. H/No. 23" />
            </div>

            <div class="field-group">
                <label class="field-label">Nearest Landmark</label>
                <input type="text" id="f1-landmark" class="field-input"
                       placeholder="e.g. Near Madina Market" />
            </div>

            <div class="field-group">
                <label class="field-label">Ghana Card Number</label>
                <input type="text" id="f1-ghana-card" class="field-input"
                       placeholder="GHA-XXXXXXXXX-X" />
            </div>

            <div class="field-group">
                <label class="field-label">Emergency Contact Name</label>
                <input type="text" id="f1-emergency-name" class="field-input"
                       placeholder="Full name" />
            </div>

            <div class="field-group">
                <label class="field-label">Emergency Contact Phone</label>
                <input type="text" id="f1-emergency-phone" class="field-input"
                       placeholder="+233XXXXXXXXX" />
            </div>

            <div class="field-group">
                <label class="field-label">Relationship</label>
                <input type="text" id="f1-emergency-relationship" class="field-input"
                       placeholder="e.g. Brother, Sister, Spouse" />
            </div>

        </div>

        <div class="flex justify-end mt-8">
            <button onclick="submitPhaseOne()"
                    class="onboarding-btn bg-blue-600 text-white hover:bg-blue-700">
                Save & Continue to Documentation →
            </button>
        </div>
    `;
}

/* =========================================================
   PHASE 2 — DOCUMENTATION
========================================================= */

function renderPhaseTwo(data) {
    const role = (data.role || '').toUpperCase();
    const isCashier = role.includes('CASHIER');

    document.getElementById('phase-content').innerHTML = `
        <div class="mb-8">
            <h2 class="text-lg font-semibold text-gray-800">Phase 2 — Documentation</h2>
            <p class="text-sm text-gray-500 mt-1">Complete contract, verification, and banking details.</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

            <!-- Contract Status -->
            <div class="field-group">
                <label class="field-label">Contract Signed</label>
                <select id="f2-contract-signed" class="field-input">
                    <option value="">Select…</option>
                    <option value="true">Yes — Signed</option>
                    <option value="false">No — Pending</option>
                </select>
            </div>

            <!-- Contract Date -->
            <div class="field-group">
                <label class="field-label">Contract Signed Date</label>
                <input type="date" id="f2-contract-date" class="field-input" />
            </div>

            <!-- Contract Upload — full width -->
            <div class="field-group md:col-span-2">
                <label class="field-label">Upload Signed Contract</label>
                <div class="relative">
                    <input type="file" id="f2-contract-upload" class="field-input"
                           accept=".pdf,.doc,.docx,.jpg,.jpeg,.png" />
                </div>
                <p class="text-xs text-gray-400 mt-1">Accepted: PDF, Word, or image. Max 10MB.</p>
            </div>

            <!-- Ghana Card Upload -->
            <div class="field-group">
                <label class="field-label">Ghana Card — Upload Photocopy</label>
                <input type="file" id="f2-ghana-card-upload" class="field-input"
                       accept=".pdf,.jpg,.jpeg,.png" />
            </div>

            <!-- Ghana Card Verification -->
            <div class="field-group">
                <label class="field-label">Ghana Card Verification</label>
                <select id="f2-ghana-card-status" class="field-input">
                    <option value="pending">Pending</option>
                    <option value="verified">Verified</option>
                    <option value="failed">Failed</option>
                </select>
            </div>

            <!-- Bank Name -->
            <div class="field-group">
                <label class="field-label">Bank Name</label>
                <input type="text" id="f2-bank-name" class="field-input"
                       placeholder="e.g. GCB Bank" />
            </div>

            <!-- Bank Account -->
            <div class="field-group">
                <label class="field-label">Bank Account Number</label>
                <input type="text" id="f2-bank-account" class="field-input"
                       placeholder="Account number" />
            </div>

            <!-- SSNIT -->
            <div class="field-group">
                <label class="field-label">SSNIT Number</label>
                <input type="text" id="f2-ssnit" class="field-input"
                       placeholder="SSNIT number" />
            </div>

            <!-- TIN -->
            <div class="field-group">
                <label class="field-label">TIN Number</label>
                <input type="text" id="f2-tin" class="field-input"
                       placeholder="TIN number" />
            </div>

        </div>

        ${isCashier ? guarantorSection() : ''}

        <div class="flex justify-end mt-8">
            <button onclick="submitPhaseTwo(${isCashier})"
                    class="onboarding-btn bg-blue-600 text-white hover:bg-blue-700">
                Save & Continue to Confirmation →
            </button>
        </div>
    `;
}

function guarantorSection() {
    return `
        <div class="mt-8 pt-8 border-t border-gray-200">
            <h3 class="text-sm font-semibold text-gray-800 uppercase tracking-wide mb-1">
                Guarantor Details
            </h3>
            <p class="text-xs text-gray-500 mb-6">
                Required for cashier roles. Guarantor must present Ghana Card and sign guarantee document.
            </p>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

                <div class="field-group">
                    <label class="field-label">Guarantor Full Name</label>
                    <input type="text" id="f2-guarantor-name" class="field-input"
                           placeholder="Full legal name" />
                </div>

                <div class="field-group">
                    <label class="field-label">Guarantor Ghana Card Number</label>
                    <input type="text" id="f2-guarantor-ghana-card" class="field-input"
                           placeholder="GHA-XXXXXXXXX-X" />
                </div>

                <div class="field-group">
                    <label class="field-label">Guarantor Ghana Card — Upload</label>
                    <input type="file" id="f2-guarantor-ghana-card-upload" class="field-input"
                           accept=".pdf,.jpg,.jpeg,.png" />
                </div>

                <div class="field-group">
                    <label class="field-label">Guarantor House Address</label>
                    <input type="text" id="f2-guarantor-address" class="field-input"
                           placeholder="Full house address" />
                </div>

                <div class="field-group">
                    <label class="field-label">Guarantor Nearest Landmark</label>
                    <input type="text" id="f2-guarantor-landmark" class="field-input"
                           placeholder="e.g. Near Tema Station" />
                </div>

                <div class="field-group">
                    <label class="field-label">Guarantee Document — Upload</label>
                    <input type="file" id="f2-guarantor-document" class="field-input"
                           accept=".pdf,.jpg,.jpeg,.png" />
                </div>

            </div>
        </div>
    `;
}

/* =========================================================
   PHASE 3 — REPORTING CONFIRMATION
========================================================= */

function renderPhaseThree(data) {
    document.getElementById('phase-content').innerHTML = `
        <div class="text-center py-12">

            <div style="font-size:56px; margin-bottom:20px;">📋</div>

            <h2 class="text-xl font-semibold text-gray-800 mb-3">Reporting Confirmation</h2>

            <p class="text-sm text-gray-500 max-w-sm mx-auto mb-2">
                Confirm that <strong>${data.applicant}</strong> has physically
                reported to their assigned branch and is ready to begin work.
            </p>

            <p class="text-xs text-gray-400 mb-10">
                This action is performed by the receiving branch manager.
            </p>

            <button onclick="submitPhaseThree()"
                    class="onboarding-btn bg-green-600 text-white hover:bg-green-700 px-8 py-3 text-base">
                ✅ Confirm Employee Has Reported
            </button>

        </div>
    `;
}

/* =========================================================
   SUBMIT PHASE ONE
========================================================= */

async function submitPhaseOne() {
    const payload = {
        house_number:                   getValue('f1-house-number'),
        nearest_landmark:               getValue('f1-landmark'),
        ghana_card_number:              getValue('f1-ghana-card'),
        emergency_contact_name:         getValue('f1-emergency-name'),
        emergency_contact_phone:        getValue('f1-emergency-phone'),
        emergency_contact_relationship: getValue('f1-emergency-relationship'),
    };

    try {
        const response = await fetch(
            `/hr/api/onboarding/${currentRecord.onboarding_id}/phase-one/`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify(payload),
            }
        );

        if (!response.ok) {
            const error = await response.json();
            showToast(error.detail || 'Failed to save Phase 1.', 'error');
            return;
        }

        showToast('Phase 1 complete. Moving to documentation.');
        await loadOnboarding(applicationId);

    } catch (err) {
        showToast('Something went wrong.', 'error');
    }
}

/* =========================================================
   SUBMIT PHASE TWO
========================================================= */

async function submitPhaseTwo(isCashier) {
    const formData = new FormData();

    formData.append('contract_signed',               getValue('f2-contract-signed'));
    formData.append('contract_signed_date',          getValue('f2-contract-date'));
    formData.append('ghana_card_verification_status', getValue('f2-ghana-card-status'));
    formData.append('bank_name',                     getValue('f2-bank-name'));
    formData.append('bank_account_number',           getValue('f2-bank-account'));
    formData.append('ssnit_number',                  getValue('f2-ssnit'));
    formData.append('tin_number',                    getValue('f2-tin'));

    // Contract upload (optional)
    const contractFile = document.getElementById('f2-contract-upload')?.files[0];
    if (contractFile) formData.append('contract_upload', contractFile);

    // Ghana card upload (optional)
    const ghanaCardFile = document.getElementById('f2-ghana-card-upload')?.files[0];
    if (ghanaCardFile) formData.append('ghana_card_upload', ghanaCardFile);

    if (isCashier) {
        formData.append('guarantor_full_name',           getValue('f2-guarantor-name'));
        formData.append('guarantor_ghana_card_number',   getValue('f2-guarantor-ghana-card'));
        formData.append('guarantor_house_address',       getValue('f2-guarantor-address'));
        formData.append('guarantor_nearest_landmark',    getValue('f2-guarantor-landmark'));

        const guarantorCard = document.getElementById('f2-guarantor-ghana-card-upload')?.files[0];
        if (guarantorCard) formData.append('guarantor_ghana_card_upload', guarantorCard);

        const guarantorDoc = document.getElementById('f2-guarantor-document')?.files[0];
        if (guarantorDoc) formData.append('guarantor_guarantee_document', guarantorDoc);
    }

    try {
        const response = await fetch(
            `/hr/api/onboarding/${currentRecord.onboarding_id}/phase-two/`,
            {
                method: 'POST',
                headers: { 'X-CSRFToken': getCSRFToken() },
                body: formData,
            }
        );

        if (!response.ok) {
            const error = await response.json();
            showToast(error.detail || 'Failed to save Phase 2.', 'error');
            return;
        }

        showToast('Phase 2 complete. Awaiting branch confirmation.');
        await loadOnboarding(applicationId);

    } catch (err) {
        showToast('Something went wrong.', 'error');
    }
}

/* =========================================================
   SUBMIT PHASE THREE
========================================================= */

async function submitPhaseThree() {
    try {
        const response = await fetch(
            `/hr/api/onboarding/${currentRecord.onboarding_id}/phase-three/`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
            }
        );

        if (!response.ok) {
            const error = await response.json();
            showToast(error.detail || 'Failed to confirm reporting.', 'error');
            return;
        }

        showToast('Onboarding complete! Employee is now fully active. 🎊');
        await loadOnboarding(applicationId);

    } catch (err) {
        showToast('Something went wrong.', 'error');
    }
}

/* =========================================================
   HELPERS
========================================================= */

function getValue(id) {
    return document.getElementById(id)?.value || '';
}

function formatDateTime(dt) {
    if (!dt) return '—';
    return new Date(dt).toLocaleString();
}

function getCSRFToken() {
    return document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    const bg = type === 'error' ? '#e53935' : '#1a1a1a';
    toast.style.cssText = `
        position: fixed; bottom: 24px; right: 24px;
        background: ${bg}; color: white;
        padding: 12px 20px; border-radius: 8px;
        font-size: 14px; font-weight: 500;
        z-index: 9999; opacity: 0;
        transition: opacity 0.3s ease;
    `;
    toast.innerText = message;
    document.body.appendChild(toast);

    requestAnimationFrame(() => { toast.style.opacity = '1'; });
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}