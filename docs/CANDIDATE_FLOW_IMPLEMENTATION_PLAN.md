# Candidate Flow Implementation Plan

## Overview
Change candidate signup and post-signup flow: simpler signup (mobile, name, current location, preferred location only), land on chatbot first, one-time free AIVI bot resume, then upgrade for more.

---

## Step 1: Backend – Signup accepts location fields; basic profile category/role optional
**What:** Add `current_location` and `preferred_location` (or `preferred_job_location`) to signup request and service. Make `preferred_job_category_id` and `preferred_job_role_id` optional in basic profile schema and service.
**Files:** `candidate/schemas.py`, `candidate/services.py`, `candidate/repository.py` (if needed), `candidate/api/routes.py` (if needed).
**Test:** Signup with 4 fields via API; basic profile with only location (no category/role) via API.

---

## Step 2: Backend – Add `is_pro` column to candidates
**What:** Alembic migration + add `is_pro` (Boolean, default False) to Candidate model.
**Files:** New migration, `candidate/models.py`, `candidate/schemas.py` (response if needed).
**Test:** Migration runs; GET candidate returns `is_pro`.

---

## Step 3: Backend – Gate one-time bot resume (create session) ✅
**What:** When creating a candidate-chat session of type `resume_creation`, if candidate is not `is_pro` and already has one completed resume with `source=aivi_bot`, return 403 with error code `UPGRADE_REQUIRED`.
**Files:** `shared/exceptions/base.py` (ForbiddenError), `candidate/repository.py` (count_completed_aivi_bot_resumes), `candidate_chat/services/chat_service.py` (gate before creating new session).
**Test:** Create session once (succeeds); with one completed aivi_bot resume and not is_pro, create again (403 UPGRADE_REQUIRED).

---

## Step 4: Frontend – Signup form (4 fields only) ✅
**What:** Candidate register/signup form: mobile, full name, current location, preferred location. Remove job category and job role fields.
**Files:** `types/candidate.types.ts` (CandidateSignupRequest), `app/candidate/register/page.tsx`, `services/candidate.service.ts` (comment).
**Test:** UI shows only 4 fields; submit calls signup API with mobile, name, current_location, preferred_location.

---

## Step 5: Frontend – Redirect after signup to chatbot page ✅
**What:** After successful signup (and login), redirect to `/candidate/dashboard/resume` instead of dashboard home or complete-profile.
**Files:** `app/candidate/register/page.tsx`.
**Test:** Signup → lands on resume/chat page.

---

## Step 6: Frontend – Allow basic users on chatbot (no forced complete-profile) ✅
**What:** In candidate dashboard layout, remove redirect that sends `profile_status === 'basic'` to complete-profile.
**Files:** `app/candidate/dashboard/layout.tsx`.
**Test:** Signup (basic profile) → lands on /candidate/dashboard/resume and stays there.

---

## Step 7: Frontend – Chatbot page UI (banner, taglines, one-time CTA) ✅
**Done:** Resume page banner has icon taglines; chat welcome has "Build with AIVI (one-time free)" and copy explaining Upload free / Build one-time free / Pro unlimited. Upgrade banner when one-time used is Step 8.
**What:** Improve resume/chat page: better banner, taglines, icons; prominent “Make resume with AIVI bot (one-time)” and “Upload resume”; show upgrade banner when one-time is already used.
**Files:** Resume page and/or `CandidateChatContainer` (or resume landing component).
**Test:** Visual check; one-time button and upgrade message visibility based on state.

---

## Step 8: Frontend – Gate "Build with AIVI" and show upgrade on API response ✅ “Build with AIVI” and show upgrade on API response
**What:** When user clicks “Build with AIVI”, call create session; if backend returns upgrade_required (403 or custom code), show “Upgrade to premium” and do not start chat. Use `is_pro` and resume count on frontend if needed for UX.
**Files:** Resume page, candidate-chat service/hook, error handling.
**Test:** Free user: first session succeeds; second attempt shows upgrade. Pro user: multiple sessions succeed.

---

## Order of execution
1. Step 1 (Backend signup + basic profile)
2. Step 2 (Backend is_pro)
3. Step 3 (Backend gate)
4. Step 4 (Frontend signup form)
5. Step 5 (Frontend redirect)
6. Step 6 (Frontend no forced complete-profile)
7. Step 7 (Frontend chatbot UI)
8. Step 8 (Frontend gate + upgrade message)

After each step: explain what was done, how to test, then ask permission before proceeding.
