# Octos — Claude Context File
> Drop this file into any new Claude chat to instantly restore full project context.
> **Keep this file updated after every session.**

---

## Project Overview
**Octos** is a branch communication and HR management system for a multi-branch printing press company.
- **Repo:** https://github.com/Khofi-Adjei007/Octos
- **Stack:** Django · PostgreSQL · Tailwind CSS · Vanilla JS · Docker · Redis

---

## App Structure
| App | Role |
|-----|------|
| `hr_workflows` | All HR logic — models, views, URLs, transitions |
| `Human_Resources` | HTML templates for HR UI |
| `employees` | Employee records |
| `jobs` | Job postings |
| `notifications` | In-app notifications |
| `branches` | Branch management |

---

## Recruitment Pipeline (COMPLETE ✅)
Stages in order:
`Application → Screening → Interview → Interview Scores → Final Review → Decision`

- All stages are fully wired end-to-end
- `Recruitment.stage` field tracks current stage
- `transitions.py` handles all stage progressions
- `RecruitmentTransitionLog` records every transition
- Decision panel: score pills, Octos Recommendation card, Pipeline Journey timeline
- Extend Offer → opens modal → saves `JobOffer` → triggers `approve` transition
- `hire_approved` status shows "Open Onboarding →" button → `/hr/onboarding/{id}/`

---

## Current Sprint: Onboarding Module (IN PROGRESS 🔧)
**Goal:** Build the onboarding page at `/hr/onboarding/{id}/` that a hiring manager lands on after approving a candidate.

### Onboarding sections to build:
- [ ] Documents checklist (ID, contract, tax forms, etc.)
- [ ] Equipment assignment (laptop, access card, tools)
- [ ] First-day schedule / task list
- [ ] Contract generation

### Files to create/modify:
- `hr_workflows/models.py` — add `OnboardingChecklist`, `EquipmentAssignment` models
- `hr_workflows/views.py` — add `onboarding_detail` view
- `hr_workflows/urls.py` — register `/hr/onboarding/<int:pk>/`
- `Human_Resources/templates/hr/onboarding.html` — new template

---

## Key File Contents
> Paste the ACTUAL current code for each file below. Update after every session.

### `hr_workflows/models.py`
```python
# PASTE FULL FILE CONTENTS HERE
```

### `hr_workflows/urls.py`
```python
# PASTE FULL FILE CONTENTS HERE
```

### `hr_workflows/transitions.py`
```python
# PASTE FULL FILE CONTENTS HERE
```

### `hr_workflows/views/` (or views.py)
```python
# PASTE FULL FILE CONTENTS HERE
```

### `Human_Resources/templates/hr/decision.html`
```html
<!-- PASTE FULL FILE CONTENTS HERE -->
```

### `Human_Resources/templates/hr/onboarding.html`
```html
<!-- PASTE FULL FILE CONTENTS HERE ONCE CREATED -->
```

---

## Architectural Decisions (Do Not Contradict These)
- No React — server-side rendered Django templates only
- Tailwind CSS for all styling (purple-themed UI)
- API layer lives in `Human_Resources/api/views/`
- Serializers used for JS-rendered detail panels
- `transitions.py` is the single source of truth for stage changes — never update `stage` directly in views
- Always write a `RecruitmentTransitionLog` entry on every transition

---

## UI / Style Conventions
- Primary color: purple (`purple-600`, `purple-700`)
- Cards use `rounded-2xl shadow-sm border border-gray-100`
- Buttons: `bg-purple-600 hover:bg-purple-700 text-white rounded-xl px-4 py-2`
- Page layout: sidebar + main content area
- Status pills: colored dot + label (e.g. green for approved, red for rejected)

---

## What's Done (Running Log)
| Date | What was built |
|------|---------------|
| — | Application → Screening → Interview → Final Review pipeline |
| — | Decision panel with score pills and recommendation card |
| — | Extend Offer modal → JobOffer model → approve transition |
| — | RecruitmentTransitionLog on every transition |
| — | hire_approved → "Open Onboarding" button wired to /hr/onboarding/{id}/ |

---

## How to Resume Any Session
1. Open new Claude chat
2. Paste this entire file
3. Say: *"Continuing Octos development. Here's the context file."*
4. Claude will have full context — then paste any specific files needed for the task

---
*Last updated: [DATE] after [WHAT YOU BUILT]*