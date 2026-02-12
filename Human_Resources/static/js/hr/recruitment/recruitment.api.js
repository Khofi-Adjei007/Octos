/* =========================================================
   RECRUITMENT API MODULE
   Handles all Recruitment-related HTTP calls
========================================================= */

import { API_BASE, getCSRF } from '../core.js';


/* -----------------------------------------
 * FETCH ALL APPLICATIONS
 * ----------------------------------------- */
export async function fetchApplications() {

  const response = await fetch(`${API_BASE}/applications/`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error('Failed to fetch recruitment applications.');
  }

  return response.json();
}


/* -----------------------------------------
 * FETCH SINGLE APPLICATION (for modal)
 * ----------------------------------------- */
export async function fetchApplicationById(id) {

  const response = await fetch(`${API_BASE}/applications/${id}/`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error('Failed to fetch application detail.');
  }

  return response.json();
}


/* -----------------------------------------
 * UPDATE APPLICATION STAGE
 * ----------------------------------------- */
export async function updateApplicationStage(id, stage) {

  const response = await fetch(`${API_BASE}/applications/${id}/stage/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRF()
    },
    body: JSON.stringify({ stage })
  });

  if (!response.ok) {
    throw new Error('Failed to update application stage.');
  }

  return response.json();
}


/* -----------------------------------------
 * ASSIGN REVIEWER
 * ----------------------------------------- */
export async function assignReviewer(id, reviewerId) {

  const response = await fetch(`${API_BASE}/applications/${id}/assign/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRF()
    },
    body: JSON.stringify({ reviewer_id: reviewerId })
  });

  if (!response.ok) {
    throw new Error('Failed to assign reviewer.');
  }

  return response.json();
}


/* -----------------------------------------
 * SCHEDULE INTERVIEW
 * ----------------------------------------- */
export async function scheduleInterview(id, datetime) {

  const response = await fetch(`${API_BASE}/applications/${id}/schedule/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRF()
    },
    body: JSON.stringify({ interview_date: datetime })
  });

  if (!response.ok) {
    throw new Error('Failed to schedule interview.');
  }

  return response.json();
}
