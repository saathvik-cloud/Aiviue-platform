# Job Recommendations: Category ID & Role ID – Root Cause and Fix

## Why you saw zero recommended jobs after adding the filter

1. **Backend list-jobs now filters by `category_id` (and `role_id`)** when the candidate dashboard sends them (from the candidate’s preferred category/location).
2. **Almost all jobs in your DB have `category_id = NULL` and `role_id = NULL`** because nothing in the employer flow sets them when creating or publishing a job.
3. So when we run `WHERE category_id = '<candidate_preferred_category_id>'`, no rows match → empty list.

So the filter is correct; the missing piece is that **jobs are never being written with category/role**.

---

## Where jobs are created and why category/role are missing

### 1. Employer chat flow (AIVI assistant)

- **Backend (chat)**  
  - `handle_extraction_complete` in `app/domains/chat/services.py` maps extraction result into `collected_data`.  
  - That mapping **does not include `category_id` or `role_id`** (only title, description, location, salary, experience, etc.).
- **Extraction**  
  - JD extraction prompt in `app/shared/llm/prompts.py` does **not** ask the LLM for category or role.  
  - `_clean_extracted_data` in `app/shared/llm/extraction.py` does **not** handle `category_id` or `role_id`.
- **Client**  
  - In `client/src/components/chat/ChatContainer.tsx`, when the employer clicks “Create job”, the `jobRequest` (CreateJobRequest) is built from chat data but **does not include `category_id` or `role_id`**.
- **Result:** Every job created from the chat flow is stored with `category_id = NULL`, `role_id = NULL`.

### 2. Job create API (direct or from extraction worker)

- **Backend**  
  - `JobCreateRequest` in `app/domains/job/schemas.py` **does** have optional `category_id` and `role_id`.  
  - `JobService.create()` and `create_from_extraction()` **do** pass them through to the DB when provided.
- **Client**  
  - `CreateJobRequest` in `client/src/types/job.types.ts` **does not** include `category_id` or `role_id`.  
  - So the employer UI (chat or any form using this type) never sends them.
- **Result:** Even if the backend is ready, the client never sends category/role, so they stay NULL.

### 3. Employer dashboard “Create job” form

- There is no separate dashboard flow that sends `category_id`/`role_id` in the create payload; any job created from the app today ends up with NULL category/role unless something else (e.g. a script or admin) sets them.

### 4. Custom roles

- If the employer selects or creates a “custom” role in the UI but that role is not persisted (e.g. not written to `job_roles` or not sent as `role_id` when creating the job), then `role_id` on the job will remain NULL. The exact behavior depends on your job master/role API and how the create-job payload is built.

---

## What was changed (immediate fix)

**Repository filter behavior** (`app/domains/job/repository.py`):

- When listing jobs with a **category_id** filter (e.g. for candidate recommendations), the query now returns:
  - jobs whose `category_id` equals the requested category, **or**
  - jobs whose `category_id` is NULL (uncategorized).
- Same for **role_id**: match requested role **or** NULL role.

So:

- Candidates still get recommendations: they see all published jobs that either match their preferred category/role **or** are uncategorized (current jobs).
- Once you start setting `category_id` and `role_id` on new (and optionally existing) jobs, the same filter will naturally narrow results to better-matched jobs.

No API or client changes are required for this; the UI stays the same.

---

## What to do so category/role are actually set on jobs

1. **Client**
   - Add `category_id` and `role_id` to `CreateJobRequest` (and any update request if you allow editing category/role).
   - In the employer chat flow, include category/role in the payload when creating the job (e.g. from a chat step or from extraction result if you add it).
   - In any dashboard “Create job” / “Edit job” form, add category and role selectors and send their IDs in the create/update request.

2. **Chat flow**
   - Either:
     - Add a step to collect category (and optionally role) from the employer and store in `collected_data`, then include them in the final job create payload, or
     - Extend JD extraction (prompt + response parsing) to infer category/role (e.g. from job title) and map them to your `job_categories` / `job_roles` IDs and pass through `handle_extraction_complete` and into the job create payload.

3. **Extraction**
   - If you want category/role from the JD text: extend the JD extraction prompt to return something like `category_name` / `role_name` (or IDs if the LLM can use a fixed list), then in the backend resolve names to IDs using `job_categories` / `job_roles` and set `category_id` / `role_id` when creating the job.  
   - Ensure `_clean_extracted_data` and the chat `collected_data` mapping include and pass through these fields.

4. **Custom roles**
   - Ensure that when an employer creates or selects a custom role, you:
     - Persist it (e.g. in `job_roles`) and get back an ID, and
     - Send that `role_id` when creating or updating the job.

After this, new jobs will have `category_id` and `role_id` set, and recommendations will align with the candidate’s preferred category/role without needing to show every uncategorized job. You can then, if you want, tighten the repository filter to **only** match category/role (and no longer include NULL) so that uncategorized jobs no longer appear in “For you”.
