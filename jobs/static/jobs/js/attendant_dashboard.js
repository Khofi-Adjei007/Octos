(function(){
  // ---------- small helpers ----------
  const $ = id => document.getElementById(id);
  const on = (el, ev, fn) => el && el.addEventListener(ev, fn);
  const qsAll = sel => Array.from(document.querySelectorAll(sel || ''));
  const attr = (el, name, val) => { if(!el) return; if(val===undefined) return el.getAttribute(name); el.setAttribute(name, val); };

  // ---------- config / cached nodes ----------
  const body = document.documentElement || document.body;
  const tabBtns = qsAll('.tab-btn');
  const panels = qsAll('.tab-panel');

  // user menu elements (multiple templates used different ids)
  const userMenuBtn = $('user-menu-btn') || $('profileBtn') || null;
  const userMenu = $('user-menu') || $('user-menu') || $('profilePopup') || null;

  // Modals (support both quick modal naming conventions from template versions)
  const quickModal = $('record-job-quick-modal') || $('record-job-modal') || $('record-job-quick') || null;
  const quickBackdrop = $('quick-modal-backdrop') || $('record-job-backdrop') || $('record-job-backdrop') || null;
  const openQuickBtn = $('record-job-btn') || $('openQuickJobBtn') || $('openQuickJobBtnInner') || null;
  const quickClose = $('quick-modal-close') || $('record-job-close') || $('modal-close') || null;
  const modalCancel = $('modal-cancel') || null;
  const quickForm = $('record-job-form') || null;

  // walk-in / larger modal
  const walkinModal = $('walkin-modal') || $('walkinModal') || $('walkin_modal') || null;
  const walkinClose = $('walkin-close') || null;

  // queue controls
  const btnRefresh = $('btn-refresh-queue') || null;
  const btnPoll = $('btn-poll-toggle') || null;
  let polling = false, pollTimer = null;

  // pricing elements (multiple possible ids)
  const modalService = $('modal-service') || $('service') || null;
  const modalQty = $('modal-quantity') || $('quantity') || null;
  const modalTotalLabel = $('modal-total-amount') || $('modal-total-amount') || $('line-total') || null;

  // CSRF helper
  function getCookie(name){
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }

  // ---------- user menu (toggle) ----------
  function closeUserMenu(){
    if(!userMenu) return;
    userMenu.classList.add('hidden');
    if(userMenuBtn) attr(userMenuBtn, 'aria-expanded', 'false');
  }
  function openUserMenu(){
    if(!userMenu) return;
    userMenu.classList.remove('hidden');
    if(userMenuBtn) attr(userMenuBtn, 'aria-expanded', 'true');
  }

  document.addEventListener('click', function(e){
    if (!userMenuBtn) return;
    if (userMenuBtn.contains(e.target)) {
      if (userMenu && userMenu.classList.contains('hidden')) openUserMenu(); else closeUserMenu();
    } else {
      closeUserMenu();
    }
  });

  // ---------- tabs (generic showPanel) ----------
  function showPanel(name){
    panels.forEach(p=>p.classList.add('hidden'));
    // try panel id patterns: panel-{name} or tab-{name}
    const p = $('panel-' + name) || $('tab-' + name) || document.querySelector('#tab-' + name) || $('panel-' + name);
    if(p) p.classList.remove('hidden');

    // update pressed state & classes
    tabBtns.forEach(b=>{
      const isActive = b.dataset.tab === name;
      attr(b, 'aria-pressed', isActive ? 'true' : 'false');
      if(isActive){
        b.classList.add('bg-red-600','text-white');
        b.classList.remove('text-gray-600','bg-transparent');
      } else {
        b.classList.remove('bg-red-600','text-white');
        b.classList.add('text-gray-600','bg-transparent');
      }
    });

    // Also try to move underline if desktop underline exists (support both IDs)
    const nav = $('managerTabNav') || $('attendantDesktopNav') || null;
    const underline = $('tabUnderline') || $('attTabUnderline') || $('attTabUnderline') || null;
    if(underline && nav){
      // find desktop button for the name
      const deskBtn = nav.querySelector('.tab-btn[data-tab="'+name+'"]');
      if(deskBtn){
        const navRect = nav.getBoundingClientRect();
        const btnRect = deskBtn.getBoundingClientRect();
        const left = btnRect.left - navRect.left;
        underline.style.width = btnRect.width + 'px';
        underline.style.transform = 'translateX(' + left + 'px)';
      }
    }
  }

  tabBtns.forEach(b => b.addEventListener('click', function(e){
    const name = this.dataset.tab;
    if(!name) return;
    showPanel(name);
  }));

  // default tab
  (function initDefaultTab(){
    // prefer job -> overview -> first
    const prefer = ['job','overview','overview','overview','job'];
    let found = null;
    for(const p of prefer){
      found = tabBtns.find(t => t.dataset.tab === p);
      if(found) break;
    }
    if(!found) found = tabBtns[0];
    if(found) found.click();
  })();

  // keyboard: close modals / user menu on Esc
  document.addEventListener('keydown', function(e){
    if (e.key === 'Escape') {
      closeUserMenu();
      closeQuickModal();
      closeWalkinModal();
    }
  });

  // ---------- quick modal open/close logic ----------
  function openQuickModal(){
    if(!quickModal) return;
    quickModal.classList.remove('hidden');
    // focus first control if present
    const sel = quickModal.querySelector('#modal-service') || quickModal.querySelector('select');
    if(sel) sel.focus();
    // add backdrop blur if a backdrop is present
    if(quickBackdrop) { quickBackdrop.classList.remove('hidden'); quickBackdrop.classList.add('backdrop-blur-sm','bg-black/40'); }
    body.classList.add('overflow-hidden');
  }

  function closeQuickModal(){
    if(!quickModal) return;
    quickModal.classList.add('hidden');
    if(quickBackdrop) { quickBackdrop.classList.add('hidden'); quickBackdrop.classList.remove('backdrop-blur-sm','bg-black/40'); }
    body.classList.remove('overflow-hidden');
  }

  on(openQuickBtn, 'click', function(e){ e && e.preventDefault && e.preventDefault(); openQuickModal(); });
  on(quickClose, 'click', function(e){ e && e.preventDefault && e.preventDefault(); closeQuickModal(); });
  on(modalCancel, 'click', function(e){ e && e.preventDefault && e.preventDefault(); closeQuickModal(); });

  // do not close modal on backdrop click per requirement (no listener)

  // ---------- walkin modal ----------
  function openWalkinModal(){ if(!walkinModal) return; walkinModal.classList.remove('hidden'); body.classList.add('overflow-hidden'); }
  function closeWalkinModal(){ if(!walkinModal) return; walkinModal.classList.add('hidden'); body.classList.remove('overflow-hidden'); }
  on(walkinClose, 'click', function(e){ e && e.preventDefault && e.preventDefault(); closeWalkinModal(); });

  // ---------- quick modal pricing helpers ----------
  function parsePrice(v){ const n = parseFloat(v); return isNaN(n) ? 0 : n; }
  function updateQuickTotal(){
    if(!modalService || !modalQty || !modalTotalLabel) return;
    const opt = modalService.selectedOptions && modalService.selectedOptions[0];
    const price = opt ? parsePrice(opt.dataset.price || opt.getAttribute('data-price')) : 0;
    const qty = Math.max(1, parseInt(modalQty.value || '1', 10) || 1);
    const total = price * qty;
    modalTotalLabel.textContent = total ? ('GHS ' + total.toFixed(2)) : 'GHS 0.00';
  }
  if(modalService) on(modalService, 'change', updateQuickTotal);
  if(modalQty) on(modalQty, 'input', updateQuickTotal);
  updateQuickTotal();

  // disable submit double-click for quickForm
  if(quickForm){
    quickForm.addEventListener('submit', function(e){
      const btn = $('modal-submit');
      if(btn){ btn.disabled = true; btn.textContent = 'Processing…'; }
      // allow form to submit normally; if you want AJAX, hook here
    });
  }

  // ---------- queue controls (refresh / poll) ----------
  async function refreshQueue(){
    console.log('Refresh queue (placeholder) — implement your API call here');
    // optionally: fetch data and update DOM
  }
  on(btnRefresh, 'click', function(){ refreshQueue(); });
  on(btnPoll, 'click', function(){
    polling = !polling;
    if(btnPoll) btnPoll.textContent = polling ? 'Auto ✓' : 'Auto';
    if(polling) pollTimer = setInterval(refreshQueue, 5000);
    else { clearInterval(pollTimer); pollTimer = null; }
  });

  // ---------- advanced: create/print / quick create via fetch (if you used earlier code) ----------
  // Keep this optional: if elements exist, wire the quick-create AJAX path
  (function wireCreateIfPresent(){
    const createBtn = $('btn-create-print');
    const feedback = $('create-feedback');
    const serviceEl = $('service') || modalService;
    const qtyEl = $('quantity') || modalQty;
    if(!createBtn) return;

    createBtn.addEventListener('click', async function(){
      if(feedback) feedback.textContent = 'Creating job...';
      const price = (serviceEl && serviceEl.selectedOptions && serviceEl.selectedOptions[0] && parsePrice(serviceEl.selectedOptions[0].dataset.price)) || 0;
      const qty = Number(qtyEl?.value || 1);
      const branchId = $('branch-select')?.value;
      if(!branchId){ if(feedback) feedback.textContent = 'Select branch'; return; }
      if(!serviceEl || !serviceEl.value){ if(feedback) feedback.textContent = 'Select service'; return; }

      try{
        const fd = new FormData();
        fd.append('branch', branchId);
        fd.append('service', serviceEl.value);
        fd.append('quantity', qty);
        fd.append('type', 'instant');
        // append other fields as needed...
        const resp = await fetch('/api/jobs/jobs/', {
          method: 'POST',
          headers: { 'X-CSRFToken': getCookie('csrftoken') },
          body: fd
        });
        if(!resp.ok){
          if(feedback) feedback.textContent = 'Create failed: ' + resp.status;
          return;
        }
        const data = await resp.json().catch(()=>null);
        if(feedback) feedback.textContent = 'Created';
        if(data && (data.receipt_url || data.id)) {
          const url = data.receipt_url || `/api/jobs/receipt/${data.id}/`;
          window.open(url, '_blank');
        }
      } catch(err){
        console.error('create error', err);
        if(feedback) feedback.textContent = 'Network error';
      }
    });
  })();

  // ---------- accessibility helpers: keyboard navigation for tab buttons ----------
  tabBtns.forEach(t=>{
    on(t, 'keydown', function(ev){
      if(ev.key === 'Enter' || ev.key === ' '){
        ev.preventDefault();
        t.click();
      }
    });
  });

  // ---------- underline reposition on resize (if underline exists) ----------
  const nav = $('managerTabNav') || $('attendantDesktopNav') || null;
  const underline = $('tabUnderline') || $('attTabUnderline') || null;
  if(underline && nav){
    let rt = null;
    window.addEventListener('resize', function(){
      if(rt) clearTimeout(rt);
      rt = setTimeout(function(){
        const active = tabBtns.find(t => t.getAttribute('aria-pressed') === 'true') || tabBtns[0];
        if(!active) return;
        const btn = nav.querySelector('.tab-btn[data-tab="'+ active.dataset.tab +'"]') || active;
        const navRect = nav.getBoundingClientRect();
        const btnRect = btn.getBoundingClientRect();
        underline.style.width = btnRect.width + 'px';
        underline.style.transform = 'translateX(' + (btnRect.left - navRect.left) + 'px)';
      }, 100);
    });
  }

  // final debug log
  console.debug('Merged attendant dashboard JS initialized');
})();

