(function(){
  const quickRecordUrl = "{{ quick_record_url|default:''|escapejs }}";
  const managerDashboardUrl = "{{ manager_dashboard_url|default:''|escapejs }}";
  const logoutUrl = "{{ logout_url|default:'#'|escapejs }}";

  // PROFILE POPUP
  const profileBtn = document.getElementById('profileBtn');
  const profilePopup = document.getElementById('profilePopup');
  const profileRoot = document.getElementById('profileRoot');

  function closeProfile() {
    if (!profilePopup || !profileBtn) return;
    profilePopup.classList.add('hidden');
    profileBtn.setAttribute('aria-expanded', 'false');
  }
  function openProfile() {
    if (!profilePopup || !profileBtn) return;
    profilePopup.classList.remove('hidden');
    profileBtn.setAttribute('aria-expanded', 'true');
  }

  document.addEventListener('click', function(e){
    if (!profileRoot) return;
    if (profileRoot.contains(e.target)) {
      if (!profilePopup) return;
      if (profilePopup.classList.contains('hidden')) openProfile(); else closeProfile();
    } else {
      closeProfile();
    }
  });

  document.addEventListener('keydown', function(e){
    if (e.key === 'Escape') closeProfile();
  });

  // DOM ready
  document.addEventListener('DOMContentLoaded', function() {
    // Outsource / Record buttons (top & inner)
    const btnTop = document.getElementById('openQuickJobBtn');
    const btnInner = document.getElementById('openQuickJobBtnInner');
    [btnTop, btnInner].forEach(btn=>{
      if (!btn) return;
      btn.addEventListener('click', function(evt) {
        if (quickRecordUrl) { window.location.href = quickRecordUrl; return; }
        if (managerDashboardUrl) { window.location.href = managerDashboardUrl; return; }
        window.location.href = '/';
      });
    });

    // overview quick new sheet (mirrors sheets tab button)
    const overviewNewSheetBtn = document.getElementById('overviewNewSheetBtn');
    if (overviewNewSheetBtn) {
      overviewNewSheetBtn.addEventListener('click', function(){ const el = document.getElementById('btnNewSheet'); el && el.click(); });
    }

    // Tab elements and underlines
    const desktopNav = document.getElementById('managerTabNav');
    const desktopUnderline = document.getElementById('tabUnderline');

    const mobileNav = document.getElementById('mobileTabNav');
    const mobileUnderline = document.getElementById('mobileTabUnderline');

    // All tab buttons (desktop + mobile + inline)
    const tabs = Array.from(document.querySelectorAll('.tab-btn'));
    const panels = Array.from(document.querySelectorAll('.tab-panel'));

    function showPanel(name) {
      const target = document.getElementById('tab-' + name);
      panels.forEach(p => p.classList.remove('active'));
      if (target) {
        requestAnimationFrame(() => target.classList.add('active'));
      }
    }

    function updateGenericTabs(name) {
      tabs.forEach(t => {
        const isActive = t.dataset.tab === name;
        if (isActive) {
          t.classList.add('bg-red-600','text-white');
          t.classList.remove('bg-transparent','text-slate-700');
          t.setAttribute('aria-pressed','true');
        } else {
          t.classList.remove('bg-red-600','text-white');
          t.classList.add('bg-transparent','text-slate-700');
          t.setAttribute('aria-pressed','false');
        }
      });
    }

    // compute left offset (relative to given nav)
    function computeNavOffset(navEl, btnEl) {
      const navRect = navEl.getBoundingClientRect();
      const btnRect = btnEl.getBoundingClientRect();
      return { left: btnRect.left - navRect.left, width: btnRect.width };
    }

    function moveUnderline(underlineEl, navEl, btnEl) {
      if (!underlineEl || !navEl || !btnEl) return;
      const { left, width } = computeNavOffset(navEl, btnEl);
      underlineEl.style.width = width + 'px';
      underlineEl.style.transform = 'translateX(' + left + 'px)';
    }

    // on tab click
    function onTabClick(e) {
      const btn = e.currentTarget;
      const name = btn.dataset.tab;
      if (!name) return;
      // show panel
      showPanel(name);
      // update generic visuals
      updateGenericTabs(name);

      // move desktop underline if applicable
      if (desktopNav) {
        const desktopBtn = desktopNav.querySelector('.tab-btn[data-tab="' + name + '"]');
        if (desktopBtn) moveUnderline(desktopUnderline, desktopNav, desktopBtn);
      }
      // move mobile underline if applicable
      if (mobileNav) {
        const mobileBtn = mobileNav.querySelector('.tab-btn[data-tab="' + name + '"]');
        if (mobileBtn) moveUnderline(mobileUnderline, mobileNav, mobileBtn);
        // also ensure mobile scroll keeps the active tab visible
        try { mobileBtn && mobileBtn.scrollIntoView({ inline: 'center', behavior: 'smooth' }); } catch(e){/*ignore*/ }
      }
    }

    // attach to all tab buttons
    tabs.forEach(t => {
      t.addEventListener('click', onTabClick);
      t.addEventListener('keydown', function(ev){
        if (ev.key === 'Enter' || ev.key === ' ') {
          ev.preventDefault();
          t.click();
        }
      });
    });

    // initialize defaults (overview)
    function init() {
      const defaultTab = 'overview';
      showPanel(defaultTab);
      updateGenericTabs(defaultTab);

      // position desktop underline
      if (desktopNav && desktopUnderline) {
        const db = desktopNav.querySelector('.tab-btn[data-tab="' + defaultTab + '"]');
        if (db) setTimeout(()=> moveUnderline(desktopUnderline, desktopNav, db), 10);
      }
      // position mobile underline
      if (mobileNav && mobileUnderline) {
        const mb = mobileNav.querySelector('.tab-btn[data-tab="' + defaultTab + '"]');
        if (mb) setTimeout(()=> moveUnderline(mobileUnderline, mobileNav, mb), 10);
      }
    }

    // recompute on resize (throttle)
    let rt = null;
    window.addEventListener('resize', function(){
      if (rt) clearTimeout(rt);
      rt = setTimeout(function(){
        // find active tab
        const active = tabs.find(t => t.getAttribute('aria-pressed') === 'true') || tabs.find(t => t.dataset.tab === 'overview') || tabs[0];
        if (!active) return;
        const nm = active.dataset.tab;
        if (desktopNav && desktopUnderline) {
          const db = desktopNav.querySelector('.tab-btn[data-tab="' + nm + '"]');
          if (db) moveUnderline(desktopUnderline, desktopNav, db);
        }
        if (mobileNav && mobileUnderline) {
          const mb = mobileNav.querySelector('.tab-btn[data-tab="' + nm + '"]');
          if (mb) moveUnderline(mobileUnderline, mobileNav, mb);
        }
      }, 120);
    });

    // initial setup
    init();


    /* =========================
       Daily Sheet / Shift actions
       ========================= */

    // helper to read CSRF cookie
    function getCookie(name) {
      const v = document.cookie.split('; ').find(row => row.startsWith(name + '='));
      return v ? decodeURIComponent(v.split('=')[1]) : null;
    }
    const csrftoken = getCookie('csrftoken');

    // Branch id — prefer branch.pk then branch.id then from context variable branch_id if provided
    const BRANCH_ID = "{{ branch.pk|default:branch.id|default:'' }}";

    function showToast(msg) { /* tiny placeholder; replace with nicer UI if you like */ alert(msg); }

    async function postJson(url, data) {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken || ''
        },
        body: JSON.stringify(data || {})
      });
      const txt = await res.text();
      try { return JSON.parse(txt); } catch(e) { return { ok: res.ok, status: res.status, text: txt }; }
    }

    // btn handlers
    const btnNew = document.getElementById('btnNewSheet');
    const btnLock = document.getElementById('btnLockSheet');
    const btnClose = document.getElementById('btnCloseDay');

    if (btnNew) {
      btnNew.addEventListener('click', async function(){
        if (!BRANCH_ID) { showToast('Branch not available'); return; }
        btnNew.disabled = true;
        const resp = await postJson(`/branches/${BRANCH_ID}/daysheet/new/`, {});
        btnNew.disabled = false;
        if (resp && resp.ok) { showToast('DaySheet created'); window.location.reload(); }
        else { showToast(resp.detail || 'Failed to create daysheet'); }
      });
    }

    if (btnLock) {
      btnLock.addEventListener('click', async function(){
        if (!BRANCH_ID) { showToast('Branch not available'); return; }
        const action = prompt("Type 'lock' to lock or 'unlock' to unlock", "lock");
        if (!action) return;
        const resp = await postJson(`/branches/${BRANCH_ID}/daysheet/lock/`, { action: action });
        if (resp && resp.ok) { showToast('Lock updated'); window.location.reload(); }
        else { showToast(resp.detail || 'Failed to update lock'); }
      });
    }

    // PIN modal wiring for close day
    const pinModal = document.getElementById('pinModal');
    const pinInput = document.getElementById('pinInput');
    const pinConfirm = document.getElementById('pinConfirm');
    const pinCancel = document.getElementById('pinCancel');

    function openPin() { pinInput.value = ''; pinModal.classList.remove('hidden'); pinInput.focus(); }
    function closePin() { pinModal.classList.add('hidden'); pinInput.value = ''; }

    if (btnClose) btnClose.addEventListener('click', function(){ openPin(); });
    if (pinCancel) pinCancel.addEventListener('click', closePin);
    if (pinConfirm) {
      pinConfirm.addEventListener('click', async function(){
        const pin = pinInput.value.trim();
        if (!pin) { alert('PIN required'); return; }
        pinConfirm.disabled = true;
        const resp = await postJson(`/branches/${BRANCH_ID}/daysheet/close/`, { pin: pin });
        pinConfirm.disabled = false;
        closePin();
        if (resp && resp.ok) { showToast('Day closed'); window.location.reload(); }
        else { showToast(resp.detail || 'Failed to close day'); }
      });
    }

    // close-shift buttons inside table (delegated)
    document.addEventListener('click', async function(e){
      const btn = e.target.closest('.btn-close-shift');
      if (!btn) return;
      const shiftId = btn.dataset.shift;
      if (!shiftId) return;
      const cash = prompt('Enter closing cash amount (GHS)', '0.00');
      if (cash === null) return;
      const pin = prompt('Enter PIN to confirm', '');
      if (!pin) { alert('PIN required'); return; }
      const resp = await postJson(`/branches/${BRANCH_ID}/shifts/${shiftId}/close/`, { closing_cash: cash, pin: pin });
      if (resp && resp.ok) { showToast('Shift closed'); window.location.reload(); }
      else { showToast(resp.detail || 'Failed to close shift'); }
    });

  }); // end DOMContentLoaded


  // =====================================================
  // RECOMMEND CANDIDATE
  // =====================================================

  const CSRF_TOKEN = () => document.cookie.match(/csrftoken=([^;]+)/)?.[1] || "";

  function initRecommend() {
    const btn = document.getElementById("btn-recommend-candidate");
    if (btn) btn.addEventListener("click", openRecommendModal);
  }

  async function openRecommendModal() {
    document.getElementById("recommend-modal")?.remove();

    // Fetch positions first
    let positions = [];
    try {
      const res = await fetch("/hr/api/positions/");
      const data = await res.json();
      positions = data;
    } catch(err) {
      console.error("Failed to load positions:", err);
    }

    const positionOptions = positions.map(p =>
      `<option value="${p.id}">${p.title}</option>`
    ).join("");

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
              <select id="rec-position">
                <option value="">— Select position —</option>
                ${positionOptions}
              </select>
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
            <label>Upload CV / Resume</label>
            <input type="file" id="rec-cv" accept=".pdf,.doc,.docx" />
            <span style="font-size:11px;color:#aaa;margin-top:3px">PDF, DOC or DOCX — max 5MB</span>
          </div>
          <div class="rec-form-group rec-form-full">
            <label>Why are you recommending this candidate?</label>
            <textarea id="rec-notes" rows="3"
              placeholder="Briefly describe why this candidate is a good fit..."></textarea>
          </div>
          <div id="rec-error" class="rec-error" style="display:none"></div>
          <div id="rec-success" class="rec-success" style="display:none"></div>
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

    document.getElementById("rec-close-btn").addEventListener("click", closeRecommendModal);
    document.getElementById("rec-cancel-btn").addEventListener("click", closeRecommendModal);
    modal.addEventListener("click", e => { if (e.target === modal) closeRecommendModal(); });
    document.getElementById("rec-submit-btn").addEventListener("click", submitRecommendation);

    setTimeout(() => document.getElementById("rec-first-name")?.focus(), 50);
  }

  async function submitRecommendation() {
    const firstName   = document.getElementById("rec-first-name").value.trim();
    const lastName    = document.getElementById("rec-last-name").value.trim();
    const phone       = document.getElementById("rec-phone").value.trim();
    const email       = document.getElementById("rec-email").value.trim();
    const positionId  = document.getElementById("rec-position").value;
    const gender      = document.getElementById("rec-gender").value;
    const cvFile      = document.getElementById("rec-cv").files[0];

    const errorDiv    = document.getElementById("rec-error");
    const successDiv  = document.getElementById("rec-success");
    const submitBtn   = document.getElementById("rec-submit-btn");
    const submitLabel = document.getElementById("rec-submit-label");

    errorDiv.style.display   = "none";
    successDiv.style.display = "none";

    if (!firstName || !lastName || !phone || !positionId) {
      errorDiv.textContent   = "Please fill in all required fields and select a position.";
      errorDiv.style.display = "block";
      return;
    }

    if (cvFile && cvFile.size > 5 * 1024 * 1024) {
      errorDiv.textContent   = "CV file must be under 5MB.";
      errorDiv.style.display = "block";
      return;
    }

    submitBtn.disabled      = true;
    submitLabel.textContent = "Submitting...";

    try {
      const formData = new FormData();
      formData.append("first_name",  firstName);
      formData.append("last_name",   lastName);
      formData.append("phone",       phone);
      formData.append("email",       email);
      formData.append("position_id", positionId);
      formData.append("gender",      gender);
      if (cvFile) formData.append("resume", cvFile);

      const res = await fetch("/hr/api/recommendations/", {
        method: "POST",
        headers: { "X-CSRFToken": CSRF_TOKEN() },
        body: formData,
      });

      const data = await res.json();

      if (data.success) {
        successDiv.innerHTML     = `<strong>${data.applicant}</strong> has been recommended for <strong>${data.role}</strong> and added to the HR pipeline with priority status.`;
        successDiv.style.display = "block";

        ["rec-first-name","rec-last-name","rec-phone","rec-email",
         "rec-position","rec-gender","rec-cv","rec-notes"].forEach(id => {
          const el = document.getElementById(id);
          if (el) el.disabled = true;
        });

        submitBtn.disabled      = true;
        submitLabel.textContent = "Submitted ✓";
        setTimeout(closeRecommendModal, 2500);

      } else {
        errorDiv.textContent    = data.error || "Submission failed.";
        errorDiv.style.display  = "block";
        submitBtn.disabled      = false;
        submitLabel.textContent = "Submit Recommendation";
      }

    } catch (err) {
      console.error("Recommendation error:", err);
      errorDiv.textContent    = "Something went wrong. Please try again.";
      errorDiv.style.display  = "block";
      submitBtn.disabled      = false;
      submitLabel.textContent = "Submit Recommendation";
    }
  }

  function closeRecommendModal() {
    document.getElementById("recommend-modal")?.remove();
  }

  document.addEventListener("DOMContentLoaded", initRecommend);

})();