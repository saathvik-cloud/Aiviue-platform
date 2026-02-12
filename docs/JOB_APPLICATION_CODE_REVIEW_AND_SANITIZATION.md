# Job Application Module – Code Review & Input Sanitization

## 1. Code Review Summary

### Bugs Fixed
- **Race condition in apply:** Concurrent apply requests could both pass the "existing" check and attempt insert. The second would fail with `IntegrityError`. **Fix:** Catch `IntegrityError` on commit, rollback, re-fetch existing application, and return idempotent response (`already_applied=True`).

### Potential Issues Checked (None Found)
- **job.role access:** Uses `job.role.name if job.role else None` – safe when role is null.
- **application.candidate access:** Uses `app.candidate.name if app.candidate else ""` – safe.
- **resume ownership:** Validates `resume.candidate_id == candidate_id` before using resume.
- **Unique constraint:** `(job_id, candidate_id)` enforced at DB level; service respects it.
- **N+1 queries:** Uses `selectinload` for candidate and resume; job loaded once with role.

---

## 2. Input Sanitization Assessment

### Job Application Endpoints – Sanitization Status

| Endpoint | Input | Sanitization | Notes |
|----------|-------|--------------|-------|
| **POST /jobs/{job_id}/apply** | `job_id` (path) | ✅ UUID validated by FastAPI | No free text |
| | `candidate_id` (from JWT) | ✅ From verified token | Not user-supplied |
| | `resume_id` (body, optional) | ✅ UUID validated by Pydantic | No free text |
| **GET /jobs/{job_id}/applications** | `job_id` (path) | ✅ UUID validated | No free text |
| **GET /jobs/{job_id}/applications/{application_id}** | `job_id`, `application_id` (path) | ✅ UUID validated | No free text |

### Conclusion: **No String Sanitization Needed (Current MVP)**

- **Apply request:** Only `resume_id` (optional UUID). Pydantic validates UUID format; no HTML/script risk.
- **List/Detail:** Path params are UUIDs. No free-text input.
- **Future (screening agent):** When we add ingestion of screening payloads (e.g. `resume_snapshot` JSON, candidate name, etc.), we **must** sanitize:
  - `sanitize_text()` for name, location, and other string fields.
  - `sanitize_dict()` for nested JSON (e.g. resume_snapshot) before storage.
  - Use shared sanitization from `app.shared.utils.sanitize`.

### Comparison with Other Domains

| Domain | String Input | Sanitization |
|--------|--------------|--------------|
| Employer | name, company_name, description, etc. | ✅ `sanitize_text()` in service |
| Job | title, description, raw_jd, etc. | ✅ `sanitize_text()` in service |
| Candidate | name, locations, about, etc. | ⚠️ Via `normalize_location`; full sanitization in update/create recommended |
| **Job Application (MVP)** | **None** | **N/A – UUIDs only** |

---

## 3. Recommendations

1. **Current MVP:** No changes needed for job_application input sanitization.
2. **Screening agent ingestion:** Implement sanitization for all string fields and nested JSON when that flow is added.
3. **Consistency:** When adding new endpoints that accept free-text (e.g. notes, comments), use `sanitize_text()` before storage.

---

## 4. Test Coverage

See `tests/test_job_application.py` for:
- Apply success, idempotency, error cases (404, 422, 400, 401)
- List applications success, empty, 403, 422, 401
- Get application detail success, 404, 403, 401
- Verification that `source_application` is not in employer-facing responses

**Run:** `pytest tests/test_job_application.py -v` (with venv activated)
