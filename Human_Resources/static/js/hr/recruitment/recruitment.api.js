/* =========================================================
   RECRUITMENT API MODULE
   Handles all Recruitment-related HTTP calls.
   All stage mutations go through the transition endpoint.
========================================================= */

import { API_BASE, getCSRF } from '../core.js';


/* -----------------------------------------
 * FETCH ALL APPLICATIONS
 * ----------------------------------------- */
export async function fetchApplications() {
  const response = await fetch(`${API_BASE}/applications/`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' }
  });

  if (!response.ok) throw new Error('Failed to fetch recruitment applications.');
  return response.json();
}


/* -----------------------------------------
 * FETCH SINGLE APPLICATION
 * ----------------------------------------- */
export async function fetchApplicationById(id) {
  const response = await fetch(`${API_BASE}/applications/${id}/`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' }
  });

  if (!response.ok) throw new Error('Failed to fetch application detail.');
  return response.json();
}


/* -----------------------------------------
 * PERFORM TRANSITION ACTION
 * Replaces updateApplicationStage, scheduleInterview.
 * All stage mutations go through here.
 * ----------------------------------------- */
export async function performTransition(id, action, payload = {}) {
  const response = await fetch(`${API_BASE}/recruitment/${id}/transition/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRF()
    },
    body: JSON.stringify({ action, ...payload })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Transition failed.');
  }

  return response.json();
}


/* -----------------------------------------
 * SAVE EVALUATION (create or update)
 * ----------------------------------------- */
async function saveEvaluation() {
  if (!currentApp) return;

  const stage = currentApp.current_stage;
  const ratingGroups = document.querySelectorAll(
    `#${stage === 'interview' ? 'interview' : 'screening'}-panel .rating-group`
  );
  const textareas = document.querySelectorAll(
    `#${stage === 'interview' ? 'interview' : 'screening'}-panel textarea`
  );

  const getScore = (index) => {
    const group = ratingGroups[index];
    return group?.dataset.score ? parseFloat(group.dataset.score) : null;
  };

  let payload = { stage };

  if (stage === 'interview') {
    payload = {
      ...payload,
      communication_score:    getScore(0),
      communication_notes:    textareas[0]?.value || '',
      attitude_score:         getScore(1),
      attitude_notes:         textareas[1]?.value || '',
      role_knowledge_score:   getScore(2),
      role_knowledge_notes:   textareas[2]?.value || '',
      problem_solving_score:  getScore(3),
      problem_solving_notes:  textareas[3]?.value || '',
      cultural_fit_score:     getScore(4),
      cultural_fit_notes:     textareas[4]?.value || '',
    };
  } else {
    payload = {
      ...payload,
      career_score:       getScore(0),
      career_notes:       textareas[0]?.value || '',
      experience_score:   getScore(1),
      experience_notes:   textareas[1]?.value || '',
      stability_score:    getScore(2),
      stability_notes:    textareas[2]?.value || '',
      education_score:    getScore(3),
      education_notes:    textareas[3]?.value || '',
      skills_score:       getScore(4),
      skills_notes:       textareas[4]?.value || '',
    };
  }

  try {
    const response = await fetch(
      `/hr/api/applications/${currentApp.id}/evaluate/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(payload)
      }
    );

    if (!response.ok) {
      const error = await response.json();
      alert(error.detail || 'Failed to save evaluation.');
      return;
    }

    showToast('Evaluation saved successfully.');

  } catch {
    alert('Error saving evaluation.');
  }
}


/* -----------------------------------------
 * FINALIZE EVALUATION
 * ----------------------------------------- */
export async function finalizeEvaluation(id) {
  const response = await fetch(`${API_BASE}/applications/${id}/evaluate/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRF()
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to finalize evaluation.');
  }

  return response.json();
}


/* -----------------------------------------
 * INITIATE ONBOARDING
 * Called when HR clicks "Start Onboarding"
 * ----------------------------------------- */
export async function initiateOnboarding(applicationId) {
  const response = await fetch(`${API_BASE}/onboarding/${applicationId}/initiate/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRF()
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to initiate onboarding.');
  }

  return response.json();
}