/* =========================================================
   NOTIFICATIONS MODULE
   Live bell icon, grouped dropdown (Today / Earlier), caret rotation.
========================================================= */

const API_LIST          = '/notifications/api/';
const API_UNREAD_COUNT  = '/notifications/api/unread-count/';
const API_MARK_READ     = (id) => `/notifications/api/${id}/read/`;
const API_MARK_ALL_READ = '/notifications/api/mark-all-read/';

function getCSRF() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}


/* -----------------------------------------
 * BOOT
 * ----------------------------------------- */
export function initNotifications() {
  refreshUnreadCount();
  bindDropdownOpen();
}


/* -----------------------------------------
 * UNREAD COUNT BADGE
 * ----------------------------------------- */
async function refreshUnreadCount() {
  try {
    const res  = await fetch(API_UNREAD_COUNT);
    const data = await res.json();
    setBadge(data.unread || 0);
  } catch (err) {
    console.error('Notifications: failed to fetch unread count', err);
  }
}

function setBadge(count) {
  const badge = document.querySelector('.notification-count');
  if (!badge) return;
  badge.textContent   = count > 99 ? '99+' : count;
  badge.style.display = count === 0 ? 'none' : 'inline-flex';
}


/* -----------------------------------------
 * DROPDOWN OPEN / CLOSE + CARET
 * ----------------------------------------- */
function bindDropdownOpen() {
  const wrapper  = document.getElementById('notificationWrapper');
  const dropdown = document.getElementById('notificationDropdown');
  const caret    = document.getElementById('notifCaret');
  if (!wrapper || !dropdown) return;

  wrapper.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = dropdown.classList.toggle('open');

    // Rotate caret down when open, reset when closed
    if (caret) caret.classList.toggle('rotated', isOpen);

    if (isOpen) loadNotificationList();
  });

  document.addEventListener('click', () => {
    dropdown?.classList.remove('open');
    if (caret) caret.classList.remove('rotated');
  });
}


/* -----------------------------------------
 * LOAD + RENDER LIST
 * ----------------------------------------- */
async function loadNotificationList() {
  const body = document.getElementById('notificationBody');
  if (!body) return;

  body.innerHTML = `<div class="notification-loading">Loading...</div>`;

  try {
    const res           = await fetch(API_LIST);
    const notifications = await res.json();
    renderList(body, notifications);
  } catch (err) {
    body.innerHTML = `<div class="notification-empty">Failed to load notifications.</div>`;
    console.error('Notifications: fetch failed', err);
  }
}

function renderList(container, notifications) {
  if (!notifications.length) {
    container.innerHTML = `<div class="notification-empty">You're all caught up ✓</div>`;
    return;
  }

  // Split into Today vs Earlier
  const todayStr = new Date().toDateString();
  const today    = notifications.filter(n => new Date(n.created_at).toDateString() === todayStr);
  const earlier  = notifications.filter(n => new Date(n.created_at).toDateString() !== todayStr);

  let html = '';

  if (today.length) {
    html += `<div class="notif-section-label">Today</div>`;
    html += today.map(n => notifItemHTML(n)).join('');
  }

  if (earlier.length) {
    html += `<div class="notif-section-label">Earlier</div>`;
    html += earlier.map(n => notifItemHTML(n)).join('');
  }

  container.innerHTML = html;

  // Mark read on click
  container.querySelectorAll('.notification-item').forEach(item => {
    item.addEventListener('click', (e) => {
      // If they clicked the View link, let it navigate — don't double-fire
      if (e.target.classList.contains('notif-link')) return;
      markRead(item);
    });
  });
}

function notifItemHTML(n) {
  return `
    <div class="notification-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}">
      <div class="notif-content">
        <span class="notif-verb">${verbLabel(n.verb)}</span>
        <p class="notif-message">${n.message}</p>
        <span class="notif-time">${n.created_at}</span>
      </div>
      ${n.link ? `<a class="notif-link" href="${n.link}">View →</a>` : ''}
    </div>
  `;
}

function verbLabel(verb) {
  const labels = {
    recommendation_submitted: '⭐ New Recommendation',
    stage_changed:            '🔄 Stage Updated',
    offer_extended:           '📋 Offer Extended',
    employee_approved:        '✅ Employee Approved',
    onboarding_completed:     '🎉 Onboarding Complete',
  };
  return labels[verb] || verb;
}


/* -----------------------------------------
 * MARK READ
 * ----------------------------------------- */
async function markRead(itemEl) {
  const id = itemEl.dataset.id;
  if (!id || !itemEl.classList.contains('unread')) return;

  try {
    await fetch(API_MARK_READ(id), {
      method:  'POST',
      headers: { 'X-CSRFToken': getCSRF() },
    });
    itemEl.classList.remove('unread');
    refreshUnreadCount();
  } catch (err) {
    console.error('Notifications: mark read failed', err);
  }
}


/* -----------------------------------------
 * MARK ALL READ
 * ----------------------------------------- */
export function bindMarkAllRead() {
  const btn = document.getElementById('markAllReadBtn');
  if (!btn) return;

  btn.addEventListener('click', async (e) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await fetch(API_MARK_ALL_READ, {
        method:  'POST',
        headers: { 'X-CSRFToken': getCSRF() },
      });
      setBadge(0);
      loadNotificationList();
    } catch (err) {
      console.error('Notifications: mark all read failed', err);
    }
  });
}