# Application Management – Implementation Plan

## 1. Feature Summary

- **Application Management** in employer sidebar: one entry that opens the flow.
- **Page 1 – Jobs list:** “Candidates for the following jobs” → list of **published** jobs (employer’s only). Glassmorphic job tiles with preview (title, role, maybe application count).
- **Page 2 – Candidates for a job:** Click a job → list of candidates who **applied** to that job. Tiles: name, role applied for, short preview.
- **Page 3 – Candidate detail:** Click a candidate → **full profile** (same as candidate module) + **resume card** (same as candidate resume history view) + **Download resume** button (same as candidate module). Reuse existing components; no re-implementation.

**Candidate sources (for later):**

- **Platform:** Candidate signs up, builds/uploads resume, applies to a job → we have `candidate_id` + resume (latest or chosen).
- **Screening agent:** Sends lead data (e.g. Redis event) → we create/merge candidate (dedup by mobile), create application for a job. Resume: PDF URL or JSON (we render same card). `source` stored in DB for admin only; employer does not see it.

**Scope for MVP:**

- Only **published** jobs in Application Management. Design so “draft” can be added later (e.g. filter by status).
- **Apply flow:** Candidate applies for a job → creates one row in `job_applications`. Idempotent per (job, candidate).
- **Deduplication:** Same person (e.g. by mobile) = one candidate. `source_application` (or similar) stored in DB, not shown to employer.
- **Resume:** Platform = use latest completed resume (or snapshot at apply time). Screening = PDF URL or JSON; we build the same card. Download = same as candidate module (reuse).

---

## 2. Design Decisions (Confirmed)

| Topic | Decision |
|-------|----------|
| Application Management | Only **published** jobs; extendable to draft later. |
| Applications per job | Employer sees applications **per job**. One candidate can apply to many jobs (same/different employers); employer only sees “applications for my jobs”. |
| Resume per application | Platform: use **latest** resume (or let candidate choose later). Screening: PDF URL or JSON; same card. |
| Duplicate candidate | One candidate record; dedup by **mobile**. Same person from platform + screening = one `candidate_id`. |
| Source (platform vs screening) | Stored in DB as `source_application` (e.g. `platform` / `screening_agent`). **Admin only**; not in employer-facing API. |
| UI | Full profile on click; resume card and download = **reuse** candidate module (same card + same download button). |
| Style | Glassmorphism, gradients, sticky navbar/sidebar, scrollable content; employer tiles with glass effect, name, role, preview. |

---

## 3. Data Model (Backend)

### 3.1 New table: `job_applications`

- **id** (UUID, PK)
- **job_id** (UUID, FK → jobs, NOT NULL)
- **candidate_id** (UUID, FK → candidates, NOT NULL)
- **applied_at** (timestamp, NOT NULL)
- **source_application** (`platform` | `screening_agent`) – for admin; not returned to employer.
- **resume_id** (UUID, FK → candidate_resumes, nullable) – for platform: which resume they applied with; for screening can be null if we store PDF/JSON on application.
- Optional: **resume_snapshot** (JSONB) and **resume_pdf_url** (string) for screening-sourced applications when we don’t create a full `candidate_resumes` row (or we do create one and link here; TBD in implementation).
- **created_at**, **updated_at**
- **Unique constraint** on `(job_id, candidate_id)` → idempotent apply; no duplicate application for same job by same candidate.

Indexes:

- `(job_id)` – list applications by job.
- `(candidate_id)` – list applications by candidate (e.g. “applications I applied to”).
- Unique on `(job_id, candidate_id)`.

### 3.2 Existing tables (no schema change for MVP)

- **jobs** – already has `status`, `published_at`; filter `status = published` for Application Management.
- **candidates** – already has profile, mobile (for dedup).
- **candidate_resumes** – already has `resume_data`, `pdf_url`; employer view reuses same structure.

### 3.3 Constants

- `ApplicationSource.PLATFORM`, `ApplicationSource.SCREENING_AGENT` (or equivalent in config/constants).

---

## 4. API Design (Backend)

- **GET** `/api/v1/employers/me/jobs/published` (or `/api/v1/jobs?employer_id=current&status=published`)  
  → List published jobs for current employer. (If job list already exists, reuse and filter by status.)

- **GET** `/api/v1/jobs/{job_id}/applications`  
  → List applications for `job_id`. Only if job belongs to current employer and job is published.  
  Response: list of application summaries (candidate_id, candidate name, role applied for, applied_at, maybe resume_id). **Do not** expose `source_application` to employer.

- **GET** `/api/v1/jobs/{job_id}/applications/{application_id}` (or by candidate_id)  
  → Single application detail: candidate **full profile** + resume (resume_data + pdf_url) for display/download.  
  Again: only for employer’s job; no `source_application` in response.

- **POST** `/api/v1/jobs/{job_id}/apply` (candidate-facing)  
  → Candidate applies to job. Body: optional `resume_id` (default: latest). Idempotent: if (job_id, candidate_id) exists, return 200 + existing application.  
  Auth: candidate JWT. Validations: job is published; candidate exists; resume exists if provided.

- **Future (screening agent):**  
  Internal or authenticated endpoint to create candidate (if new) + job_application with `source_application = screening_agent` and optional PDF/JSON. Not in MVP scope; design so this is easy to add.

---

## 5. UI Flow (Frontend)

1. **Employer dashboard**
   - Sidebar: new item **“Application Management”** (e.g. icon: ClipboardList or Users).
   - Click → navigate to `/dashboard/applications` (or similar).

2. **Page 1 – Applications home**
   - Route: e.g. `/dashboard/applications`
   - Heading: “Candidates for the following jobs”
   - Content: List of **published** jobs (employer’s). Each tile: glassmorphic card, job title, role/category, optional application count, clickable → Page 2.

3. **Page 2 – Candidates for one job**
   - Route: e.g. `/dashboard/applications/jobs/[jobId]`
   - Heading: Job title + “Applications”
   - Content: List of candidates who applied to this job. Each tile: name, role applied for, short preview; clickable → Page 3.

4. **Page 3 – Candidate detail**
   - Route: e.g. `/dashboard/applications/jobs/[jobId]/candidates/[candidateId]` (or by application_id if preferred).
   - Content:
     - **Full profile** (same structure as candidate profile in candidate module).
     - **Resume card** (same as candidate resume history detail – reuse component or page structure).
     - **Download resume** button (same as candidate module – reuse; uses `pdf_url` from resume or application).

5. **Candidate side (apply)**
   - From job listing (e.g. candidate dashboard jobs), “Apply” on a job → calls `POST /api/v1/jobs/{job_id}/apply`. Idempotent; show success or “Already applied”.

---

## 6. Implementation Steps (Order)

| Step | What | Deliverable |
|------|------|-------------|
| **1** | Backend: Data model + migration | `job_applications` table; Alembic migration; constants for source. |
| **2** | Backend: Application domain | Repository, service, routes (list published jobs, list applications, get application detail, apply). Idempotency, dedup, no N+1, sanitization, validation. |
| **3** | Frontend: Routes + nav + list jobs | Application Management in sidebar; route `/dashboard/applications`; page “Candidates for the following jobs” with published job tiles (glassmorphic). |
| **4** | Frontend: List candidates + candidate detail | Page per job with candidate tiles; candidate detail page reusing profile + resume card + download. |
| **5** | Candidate apply (optional in same batch) | Apply button on candidate job view; call apply API; idempotent handling. |

---

## 7. Coding Standards (Recap)

- **Backend:** Idempotency where applicable; dedup by (job_id, candidate_id); avoid race conditions and N+1; input sanitization and validation; production-style (e.g. dictionary dispatch for multiple if/else).
- **Frontend:** Match employer/candidate module: glassmorphism, gradients, sticky nav/sidebar, scrollable main content; reuse candidate resume card and download button; DRY.

---

## 8. How to Test (Per Step)

- **Step 1:** Run migration; verify table and indexes; optional: create one row via SQL and query.
- **Step 2:** Call APIs with employer JWT (list jobs, list applications, get detail) and candidate JWT (apply); verify idempotent apply and 403 for wrong employer.
- **Step 3:** Click Application Management → see published jobs; style matches dashboard.
- **Step 4:** Click job → see candidates; click candidate → see profile + resume card + download.
- **Step 5:** As candidate, apply to job; as employer, see that application in list.

---

*Document version: 1.0. Next: Step 1 – Data model + migration.*
