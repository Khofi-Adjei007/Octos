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

  const userMenuBtn = $('user-menu-btn') || $('profileBtn') || null;
  const userMenu = $('user-menu') || $('profilePopup') || null;

  const quickModal = $('record-job-quick-modal') || null;
  const quickBackdrop = $('quick-modal-backdrop') || null;
  const openQuickBtn = $('record-job-btn') || $('openQuickJobBtn') || $('openQuickJobBtnInner') || null;
  const quickClose = $('quick-modal-close') || null;
  const modalCancel = $('modal-cancel') || null;
  const quickForm = $('record-job-form') || null;

  const walkinModal = $('walkin-modal') || null;
  const walkinClose = $('walkin-close') || null;

  const btnRefresh = $('btn-refresh-queue') || null;
  const btnPoll = $('btn-poll-toggle') || null;
  let polling = false, pollTimer = null;

  const modalService = $('modal-service') || null;
  const modalQty = $('modal-quantity') || null;
  const modalTotalLabel = $('modal-total-amount') || null;

  // API endpoints (update if your router uses different base)
  const API_BASE = '/api/jobs/';           // router base for jobs app
  const JOBS_ENDPOINT = API_BASE + 'jobs/';          // POST here to create job
  const RECEIPT_BASE = API_BASE + 'receipt/';       // open RECEIPT_BASE + id + '/'

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

  // ---------- tabs ----------
  function showPanel(name){
    panels.forEach(p=>p.classList.add('hidden'));
    const p = $('panel-' + name) || $('tab-' + name) || document.querySelector('#tab-' + name);
    if(p) p.classList.remove('hidden');

    tabBtns.forEach(b=>{
      const isActive = b.dataset.tab === name;
      attr(b, 'aria-pressed', isActive ? 'true' : 'false');
      if(isActive){
        b.classList.add('bg-red-600','text-white'); b.classList.remove('text-gray-600','bg-transparent');
      } else {
        b.classList.remove('bg-red-600','text-white'); b.classList.add('text-gray-600','bg-transparent');
      }
    });

    // move underline if present
    const nav = $('managerTabNav') || $('attendantDesktopNav') || null;
    const underline = $('tabUnderline') || $('attTabUnderline') || null;
    if(underline && nav){
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

  (function initDefaultTab(){
    const prefer = ['job','overview','overview','job'];
    let found = null;
    for(const p of prefer){
      found = tabBtns.find(t => t.dataset.tab === p);
      if(found) break;
    }
    if(!found) found = tabBtns[0];
    if(found) found.click();
  })();

  document.addEventListener('keydown', function(e){
    if (e.key === 'Escape') {
      closeUserMenu();
      closeQuickModal();
      closeWalkinModal();
    }
  });

  // ---------- quick modal open/close ----------
  function openQuickModal(){
    if(!quickModal) return;
    quickModal.classList.remove('hidden');
    if(quickBackdrop) { quickBackdrop.classList.remove('hidden'); quickBackdrop.classList.add('backdrop-blur-sm','bg-black/40'); }
    body.classList.add('overflow-hidden');
    // try to set focus
    const sel = quickModal.querySelector('#modal-service') || quickModal.querySelector('select');
    if(sel) sel.focus();
    // recompute total
    updateQuickTotal();
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

  // ---------- walkin ----------
  function openWalkinModal(){ if(!walkinModal) return; walkinModal.classList.remove('hidden'); body.classList.add('overflow-hidden'); }
  function closeWalkinModal(){ if(!walkinModal) return; walkinModal.classList.add('hidden'); body.classList.remove('overflow-hidden'); }
  on(walkinClose, 'click', function(e){ e && e.preventDefault && e.preventDefault(); closeWalkinModal(); });

  // ---------- pricing helpers ----------
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

  // ---------- quick form submission (AJAX) ----------
  if(quickForm){
    quickForm.addEventListener('submit', async function(e){
      e && e.preventDefault && e.preventDefault();

      // UI elements
      const feedbackText = (function(){
        let el = document.getElementById('create-feedback');
        if(!el){
          el = document.createElement('div');
          el.id = 'create-feedback';
          el.className = 'mt-2 text-sm';
          quickForm.appendChild(el);
        }
        return el;
      })();

      // gather required values
      const branchEl = document.getElementById('branch-select');
      const branchId = branchEl ? (branchEl.value || '').trim() : '';
      const svcEl = modalService;
      const svcId = svcEl ? svcEl.value : '';
      const qty = modalQty ? Number(modalQty.value || 1) : 1;
      const payment = document.getElementById('modal-payment') ? document.getElementById('modal-payment').value : 'cash';
      const name = document.getElementById('modal-customer') ? document.getElementById('modal-customer').value : '';
      const phone = document.getElementById('modal-phone') ? document.getElementById('modal-phone').value : '';
      const notes = document.getElementById('modal-notes') ? document.getElementById('modal-notes').value : '';

      // validate
      if(!branchId){
        feedbackText.textContent = 'Select a branch';
        if(branchEl){
          branchEl.classList.add('ring-2','ring-red-300');
          branchEl.focus();
          setTimeout(()=> branchEl.classList.remove('ring-2','ring-red-300'), 2000);
        }
        return;
      }
      if(!svcId){
        feedbackText.textContent = 'Select a service';
        if(svcEl){
          svcEl.classList.add('ring-2','ring-red-300');
          svcEl.focus();
          setTimeout(()=> svcEl.classList.remove('ring-2','ring-red-300'), 2000);
        }
        return;
      }

      // disable submit
      const submitBtn = $('modal-submit');
      if(submitBtn){ submitBtn.disabled = true; submitBtn.textContent = 'Processing…'; }

      feedbackText.textContent = 'Creating job...';

      try {
        const fd = new FormData();
        fd.append('branch', branchId);
        fd.append('service', svcId);
        fd.append('quantity', qty);
        // quick record should be instant (completed) — we rely on serializer/service to handle 'instant'
        fd.append('type', 'instant');
        fd.append('customer_name', name);
        fd.append('customer_phone', phone);
        fd.append('description', notes);
        fd.append('payment_type', payment);

        const resp = await fetch(JOBS_ENDPOINT, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCookie('csrftoken')
            // don't set Content-Type: browser will set multipart/form-data boundary automatically for FormData
          },
          body: fd,
          credentials: 'same-origin'
        });

        if(!resp.ok){
          let errText = `Create failed (${resp.status})`;
          try{
            const errJson = await resp.json().catch(()=>null);
            if(errJson && errJson.detail) errText = errJson.detail;
            else if(errJson) errText = JSON.stringify(errJson);
          }catch(e){}
          feedbackText.textContent = errText;
          console.warn('Job create failed', resp.status);
          return;
        }

        const data = await resp.json().catch(()=>null);
        feedbackText.textContent = 'Created';

        // open receipt if possible (API may or may not return a receipt_url)
        if(data && data.id){
          const url = (data.receipt_url) ? data.receipt_url : (RECEIPT_BASE + data.id + '/');
          try { window.open(url, '_blank'); } catch(e){ console.warn('Failed to open receipt', e); }
        }

        // refresh queue and UI (if you have a function to fetch queue, call it)
        if(typeof refreshQueue === 'function') try{ refreshQueue(); }catch(e){/*ignore*/}

        // reset modal inputs
        if(modalQty) modalQty.value = '1';
        if(modalService) modalService.selectedIndex = 0;
        if(document.getElementById('modal-customer')) document.getElementById('modal-customer').value = '';
        if(document.getElementById('modal-phone')) document.getElementById('modal-phone').value = '';
        if(document.getElementById('modal-notes')) document.getElementById('modal-notes').value = '';

        // close modal after a short delay
        setTimeout(()=>{ closeQuickModal(); feedbackText.textContent = ''; }, 700);

      } catch(err) {
        console.error('create error', err);
        feedbackText.textContent = 'Network error';
      } finally {
        if(submitBtn){ submitBtn.disabled = false; submitBtn.textContent = 'Checkout'; }
      }
    });
  }

  // ---------- queue controls ----------
  async function refreshQueue(){
    // Best-effort placeholder: you should implement actual fetch to queue endpoint and patch DOM
    console.log('Refresh queue placeholder — implement API fetch here to update queue DOM.');
  }
  on(btnRefresh, 'click', function(){ refreshQueue(); });
  on(btnPoll, 'click', function(){
    polling = !polling;
    if(btnPoll) btnPoll.textContent = polling ? 'Auto ✓' : 'Auto';
    if(polling) pollTimer = setInterval(refreshQueue, 5000);
    else { clearInterval(pollTimer); pollTimer = null; }
  });

  // ---------- keyboard nav ----------
  tabBtns.forEach(t=>{
    on(t, 'keydown', function(ev){
      if(ev.key === 'Enter' || ev.key === ' '){
        ev.preventDefault();
        t.click();
      }
    });
  });

  // ---------- underline reposition on resize ----------
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

  console.debug('Merged attendant dashboard JS initialized');
})();
