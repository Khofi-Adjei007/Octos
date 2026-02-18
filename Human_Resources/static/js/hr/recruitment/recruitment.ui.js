import { q } from '../core.js';
import { fetchApplications } from './recruitment.api.js';
import { buildApplicationCard } from './recruitment.cards.js';
import { applyRecruitmentFilter } from './recruitment.filters.js';

export async function loadRecruitment() {

  const list  = document.querySelector('#recruitment-items');
  const empty = document.querySelector('#recruitment-empty');

  if (!list || !empty) {
    console.log("Missing DOM nodes");
    return;
  }

  list.innerHTML = '';

  try {

    console.log("STEP 1: fetching...");
    const response = await fetchApplications();
    console.log("STEP 2: raw response:", response);

    if (!Array.isArray(response)) {
      console.log("NOT ARRAY:", response);
      throw new Error("Response is not array");
    }

    console.log("STEP 3: applying filter...");
    const filtered = applyRecruitmentFilter(response);
    console.log("STEP 4: filtered:", filtered);

    filtered.forEach(app => {
      console.log("STEP 5: building card:", app.id);
      const card = buildApplicationCard(app);
      list.appendChild(card);
    });

    console.log("DONE RENDERING");

  } catch (error) {
    console.error("🔥 REAL ERROR:", error);
  }
}
