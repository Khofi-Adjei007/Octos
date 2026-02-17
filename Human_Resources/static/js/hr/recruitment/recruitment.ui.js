import { q } from '../core.js';
import { fetchApplications } from './recruitment.api.js';
import { buildApplicationCard } from './recruitment.cards.js';
import { applyRecruitmentFilter } from './recruitment.filters.js';

export async function loadRecruitment() {

  const list  = q('#recruitment-items');
  const empty = q('#recruitment-empty');

  if (!list || !empty) return;

  list.innerHTML = '';
  empty.classList.add('hidden');

  try {
    const response = await fetchApplications();
    const applications = Array.isArray(response)
      ? response
      : response.results || [];

    const filtered = applyRecruitmentFilter(applications);


    if (!filtered.length) {
      empty.classList.remove('hidden');
      return;
    }

    filtered.forEach(app => {
      const card = buildApplicationCard(app);
      list.appendChild(card);
    });

  } catch (err) {
    empty.textContent = 'Failed to load applications.';
    empty.classList.remove('hidden');
  }
}
