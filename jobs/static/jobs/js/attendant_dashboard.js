 // ---------- tabs ----------
 (function(){
  function init(){
    // all your existing init code here (tab switching, event bindings)
    console.log('attendant_dashboard.js loaded');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

    document.querySelectorAll('.tab-btn').forEach(btn=>{
      btn.addEventListener('click', (e)=>{
        document.querySelectorAll('.tab-btn').forEach(b=>{
          b.classList.remove('bg-white','text-red-700');
          b.classList.add('text-gray-600');
        });
        btn.classList.add('bg-white','text-red-700');
        btn.classList.remove('text-gray-600');

        const tab = btn.dataset.tab;
        document.querySelectorAll('.tab-panel').forEach(p=>p.classList.add('hidden'));
        const panel = document.getElementById('panel-' + tab);
        if(panel) panel.classList.remove('hidden');
      });
    });
    const initial = document.querySelector('.tab-btn[data-tab="job"]');
    if(initial) initial.click();

    // ---------- user menu ----------
    const userBtn = document.getElementById('user-menu-btn');
    const userMenu = document.getElementById('user-menu');

    function isDescendant(parent, child) {
      if (!parent || !child) return false;
      let node = child;
      while (node) {
        if (node === parent) return true;
        node = node.parentNode;
      }
      return false;
    }

    userBtn?.addEventListener('click', (e)=>{
      e.stopPropagation();
      userMenu.classList.toggle('hidden');
    });

    document.addEventListener('click', (e)=>{
      const tgt = e.target;
      if (isDescendant(userMenu, tgt) || isDescendant(userBtn, tgt)) return;
      if (!userMenu.classList.contains('hidden')) userMenu.classList.add('hidden');
    });

    // ---------- helpers ----------
    function getCookie(name) {
      const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
      return v ? v.pop() : '';
    }

    // ---------- price calc ----------
    const serviceSel = document.getElementById('service');
    const qtyEl = document.getElementById('quantity');
    const depositEl = document.getElementById('deposit_amount');
    const unitEl = document.getElementById('unit-price');
    const totalEl = document.getElementById('line-total');
    const attachmentEl = document.getElementById('attachment');
    const feedback = document.getElementById('create-feedback');

    function parsePrice(v){ return Number(v||0); }

    function calcTotal(){
      const opt = serviceSel?.selectedOptions?.[0];
      const price = opt ? parsePrice(opt.dataset.price) : 0;
      const qty = Number(qtyEl.value || 1);
      const deposit = Number(depositEl.value || 0);
      const total = Math.max(0, (price * Math.max(1, qty)) - deposit);
      unitEl.textContent = price.toFixed(2);
      totalEl.textContent = total.toFixed(2);
      return {price, qty, deposit, total};
    }

    serviceSel?.addEventListener('change', calcTotal);
    qtyEl?.addEventListener('input', calcTotal);
    depositEl?.addEventListener('input', calcTotal);
    calcTotal();

    // ---------- create & print (instant) ----------
    document.getElementById('btn-create-print')?.addEventListener('click', async ()=>{
      feedback.textContent = 'Creating job...';
      const {price, qty, deposit} = calcTotal();
      const branchId = document.getElementById('branch-select')?.value;
      if(!branchId){ feedback.textContent = 'Select branch'; return; }
      if(!serviceSel.value){ feedback.textContent = 'Select service'; return; }

      try{
        const fd = new FormData();
        fd.append('branch', branchId);
        fd.append('service', serviceSel.value);
        fd.append('quantity', qty);
        fd.append('type', 'instant');
        fd.append('deposit_amount', deposit);
        fd.append('description', document.getElementById('notes').value || '');
        fd.append('customer_name', document.getElementById('customer_name').value || '');
        fd.append('customer_phone', document.getElementById('customer_phone').value || '');
        // attach file if any
        if(attachmentEl.files && attachmentEl.files.length) fd.append('attachment', attachmentEl.files[0]);

        const resp = await fetch('/api/jobs/jobs/', {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
          },
          body: fd
        });

        if(!resp.ok){
          const txt = await resp.text();
          feedback.textContent = 'Create failed: ' + resp.status;
          console.error('create error', resp.status, txt);
          return;
        }

        const data = await resp.json();
        feedback.textContent = 'Created. Opening receipt...';
        // open receipt (server should return receipt_url)
        if(data.receipt_url){
          window.open(data.receipt_url, '_blank');
        } else if(data.id){
          window.open(`/api/jobs/receipt/${data.id}/`, '_blank');
        }
        // clear form lightly
        document.getElementById('create-job-form').reset();
        calcTotal();
        setTimeout(()=> feedback.textContent = '', 2000);
      } catch(err){
        console.error(err);
        feedback.textContent = 'Network error';
      }
    });

    // placeholders
    document.getElementById('btn-refresh-queue')?.addEventListener('click', ()=>{
      alert('Refresh queue (API not wired yet)');
    });
    document.getElementById('btn-create-pay')?.addEventListener('click', ()=>{
      alert('Create & Pay (API not wired yet)');
    });

    // branch change (reload queue if needed)
    document.getElementById('branch-select')?.addEventListener('change', ()=>{
      // basic behaviour: reload page with ?branch=ID so server picks it up
      const id = document.getElementById('branch-select').value;
      const url = new URL(window.location.href);
      url.searchParams.set('branch', id);
      window.location.href = url.toString();
    });

// modal helper (put inside the IIFE/bootstrap you already added)
function toggleModal(show){
  const modal = document.getElementById('record-job-modal');
  if(!modal) return;
  modal.classList.toggle('hidden', !show);
  if(show) {
    modal.querySelector('[autofocus]')?.focus();
  }
}

// open modal from quickinfo button
document.getElementById('open-walkin-btn')?.addEventListener('click', ()=> toggleModal(true));

// Record Job button could open a tiny quick-entry modal (reuse same modal include)
document.getElementById('record-job-btn')?.addEventListener('click', ()=> toggleModal(true));

// close on outside click or ESC
document.addEventListener('click', (e)=>{
  const modal = document.getElementById('record-job-modal');
  if(modal && !modal.classList.contains('hidden')){
    if(!modal.querySelector('.modal-content').contains(e.target)) toggleModal(false);
  }
});
document.addEventListener('keydown', (e)=> { if(e.key === 'Escape') toggleModal(false); });

// attendant_dashboard.js — modal behaviour: close via buttons/Esc only; blur background when open
(function(){
  // element getter with debug
  const get = id => {
    const e = document.getElementById(id);
    if(!e) console.debug(`[modal] missing #${id}`);
    return e;
  };

  const openBtn = get('record-job-btn');
  const modal = get('record-job-modal');           // wrapper (fixed inset-0, flex items-start pt-20)
  const backdrop = get('record-job-backdrop');     // full-screen backdrop element
  const closeBtn = get('record-job-close');        // top-right ✕
  const cancelBtn = get('modal-cancel');          // bottom cancel button
  const form = get('record-job-form');
  const serviceSel = get('modal-service');
  const qty = get('modal-quantity');
  const totalAmountEl = get('modal-total-amount');
  const submitBtn = get('modal-submit');

  if(!modal){
    console.warn('[modal] modal wrapper not found — aborting modal script.');
    return;
  }

  // show/hide helpers
  function showModal(){
    // reveal modal wrapper (was hidden)
    modal.classList.remove('hidden');
    modal.classList.add('flex'); // wrapper uses flex to center horizontally and items-start for vertical
    // add backdrop blur + ensure backdrop visible
    if(backdrop){
      backdrop.classList.remove('hidden');
      // visual blur + slightly darker black
      backdrop.classList.add('backdrop-blur-sm', 'bg-black/40');
    }
    // prevent body scroll while modal open
    document.documentElement.classList.add('overflow-hidden');
    // focus
    setTimeout(()=> { if(serviceSel) serviceSel.focus(); }, 60);
    computeTotal();
    console.debug('[modal] opened');
  }

  function hideModal(){
    // hide wrapper
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    // remove backdrop visual classes but keep it hidden
    if(backdrop){
      backdrop.classList.add('hidden');
      backdrop.classList.remove('backdrop-blur-sm','bg-black/40');
    }
    document.documentElement.classList.remove('overflow-hidden');
    console.debug('[modal] closed');
  }

  // events to open/close
  if(openBtn) openBtn.addEventListener('click', (e)=> { e.preventDefault(); showModal(); });

  // close via explicit buttons only
  if(closeBtn) closeBtn.addEventListener('click', (e)=> { e.preventDefault(); hideModal(); });
  if(cancelBtn) cancelBtn.addEventListener('click', (e)=> { e.preventDefault(); hideModal(); });

  // IMPORTANT: DO NOT close on backdrop click - ensure no listener attached
  // If you previously added backdrop click handler, remove it or ensure nothing runs on backdrop clicks.

  // close on Esc
  document.addEventListener('keydown', (e)=>{
    if(e.key === 'Escape'){
      // only close if visible
      if(!modal.classList.contains('hidden')) hideModal();
    }
  });

  // keep clicks inside modal panel from doing anything weird (stop propagation)
  const panel = modal.querySelector('.relative') || modal.querySelector('.modal-panel');
  if(panel){
    panel.addEventListener('click', (ev)=> ev.stopPropagation());
  }

  // pricing helpers
  function getSelectedPrice(){
    if(!serviceSel) return 0;
    const opt = serviceSel.selectedOptions && serviceSel.selectedOptions[0];
    const p = opt ? (opt.dataset.price || opt.getAttribute('data-price') || 0) : 0;
    return parseFloat(p) || 0;
  }

  function computeTotal(){
    if(!totalAmountEl) return;
    const price = getSelectedPrice();
    const q = qty ? Math.max(1, parseInt(qty.value || '1', 10)) : 1;
    const total = price * q;
    totalAmountEl.textContent = total ? `GHS ${total.toFixed(2)}` : '—';
  }

  if(serviceSel) serviceSel.addEventListener('change', computeTotal);
  if(qty) qty.addEventListener('input', computeTotal);

  // form submit logic left intact (you had it before) — defensive wrapper
  if(form){
    form.addEventListener('submit', async (ev)=>{
      ev.preventDefault();
      if(submitBtn){ submitBtn.disabled = true; submitBtn.dataset.prev = submitBtn.textContent; submitBtn.textContent = 'Processing...'; }

      const payload = {
        service: serviceSel ? serviceSel.value : '',
        quantity: qty ? qty.value : 1,
        payment_type: (document.getElementById('modal-payment') || {}).value || 'cash',
        customer_name: (document.getElementById('modal-customer') || {}).value || '',
        customer_phone: (document.getElementById('modal-phone') || {}).value || '',
        notes: (document.getElementById('modal-notes') || {}).value || ''
      };

      // csrf helper
      const getCookie = name => {
        const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return m ? m.pop() : '';
      };
      const csrftoken = getCookie('csrftoken');

      try{
        const res = await fetch('/api/jobs/quick_create/', {
          method: 'POST',
          headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrftoken},
          body: JSON.stringify(payload)
        });

        if(res.ok){
          const data = await res.json().catch(()=>null);
          alert('Job recorded' + (data && data.id ? ` — #${data.id}` : ''));
          hideModal();
          if(typeof window.refreshQueue === 'function') window.refreshQueue();
        } else {
          const text = await res.text().catch(()=>res.status);
          alert('Failed to record job: ' + text);
        }
      } catch(err){
        console.error('[modal] network error', err);
        alert('Network error while recording job');
      } finally {
        if(submitBtn){ submitBtn.disabled = false; submitBtn.textContent = submitBtn.dataset.prev || 'Checkout'; }
      }
    });
  }

  console.debug('[modal] script initialized');
})();
