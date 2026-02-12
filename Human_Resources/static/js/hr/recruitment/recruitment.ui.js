import { q } from '../core.js';
import { fetchApplications } from './recruitment.api.js';
import { buildApplicationCard } from './recruitment.cards.js';
import { applyRecruitmentFilter } from './recruitment.filters.js';

export async function loadRecruitment() {

  const list  = q('#recruitment-items');
  const empty = q('#recruitment-empty');

  if (!list || !empty) return;

  list.innerHTML = '';
  empty.style.display = 'none';

  try {
    const applications = await fetchApplications();
    const filtered = applyRecruitmentFilter(applications);

    if (!filtered.length) {
      empty.style.display = 'block';
      empty.textContent = 'No applications found.';
      return;
    }

    filtered.forEach(app => {
      const card = buildApplicationCard(app);
      list.appendChild(card);
    });

  } catch {
    empty.style.display = 'block';
    empty.textContent = 'Failed to load applications.';
  }
}
