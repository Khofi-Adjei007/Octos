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
      panels.forEach(p => p.classList.add('hidden'));
      const target = document.getElementById('tab-' + name);
      if (target) target.classList.remove('hidden');
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

  });
})();