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
export async function saveEvaluation(id, payload) {
  const response = await fetch(`${API_BASE}/applications/${id}/evaluate/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRF()
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to save evaluation.');
  }

  return response.json();
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