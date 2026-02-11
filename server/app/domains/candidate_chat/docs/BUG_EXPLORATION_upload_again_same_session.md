# Bug exploration: "Upload again" in same session shows questions instead of upload field

## Summary

When the user returns to the **same** chat session (without starting a new one), then tries to **upload a resume again**, the UI does **not** show the upload file field. Instead the bot asks follow-up questions (e.g. DOB, experience) as if still in the previous flow.

---

## Root cause (where the bug lives)

### 1. Routing is **only** by `current_step`

In `send_message()` (chat_service.py ~335–402):

- We load the session and read `current_step` from `session.context_data["step"]`.
- We dispatch to **one** handler based on that step; we do **not** treat "new file upload" as a special case that can override the step.

So:

- If the session is in **MISSING_FIELDS** → we always call `_handle_missing_field_answer`.
- If the session is in **RESUME_PREVIEW** → we always call `_handle_resume_confirmation`.

There is **no** branch that says: “if the user is sending a **new** file (or an explicit ‘upload again’ action), reset to upload flow and show the file field.”

### 2. MISSING_FIELDS: new file is treated as an “answer”

- Handler: `_handle_missing_field_answer` → delegates to `_handle_question_answer`.
- `_handle_question_answer` receives `(session, content, data)`. It does **not** receive `message_type`.
- When the frontend sends a new PDF, it typically sends something like:
  - `content`: e.g. `"Uploaded: filename.pdf"`
  - `message_data`: `{ "file_url": "https://...", "question_key": "resume_pdf" }`
- We have a **special case** only when `question_key == "resume_pdf"` and `pdf_upload_no_role_use_general`: we **re-ask the current question** (“Your resume was already received. Please answer the question below.”) and do **not** treat the payload as a **new** upload.
- So when the user actually uploads a **new** file (new `file_url`) in the same session, we still treat it as “answer to current question” / duplicate and re-ask (e.g. salary or DOB). We **never** call `_handle_resume_upload` with the new `file_url`.

So in **MISSING_FIELDS**, the bug is: **we never check for `data.get("file_url")` and redirect to the upload flow.** We always stay in the question-answer flow.

### 3. RESUME_PREVIEW (pdf_upload): “Upload again” is not handled

In `_handle_resume_confirmation` (chat_service.py ~1364–1603):

- The **only** “switch to upload” branch is:
  - `ctx.get("method") == "aivi_bot"` **and** `_is_choosing_upload(content, data)`.
- So when **method is already "pdf_upload"** (e.g. user came from PDF flow and is at preview), we **never** switch to upload. If the user sends a new file or clicks “upload again”, we fall through to:
  - `is_confirm` / `is_edit` / **“Unrecognized input”** → we return “Please confirm whether you’d like to save this resume” and the same Save/Edit buttons.
- So in **RESUME_PREVIEW** for the PDF flow, **there is no path that shows the upload file field** when the user tries to upload again.

### 4. Session stays ACTIVE with old step/context

- After the user **saves** the resume we set:
  - `context_data["step"] = "completed"`
  - `session_status = COMPLETED`.
- So if they **did** save, the next time they open chat, `create_session(force_new=False)` will **not** return that session (we only return **ACTIVE** sessions in `get_active_resume_session`). So they get a **new** session and see CHOOSE_METHOD / upload as expected.

The bug appears when:

- The user **did not** save (e.g. left at MISSING_FIELDS or RESUME_PREVIEW), **or**
- The frontend **reuses the same session ID** (e.g. “back to chat” without calling create session again).

Then the session is still **ACTIVE** with step **MISSING_FIELDS** or **RESUME_PREVIEW** and **old context** (e.g. `current_question_key`, `collected_data`). Any “upload again” is still handled by the same handler and never resets to the upload flow.

### 5. Exact code locations

| Location | What happens | Missing behavior |
|----------|--------------|------------------|
| `send_message()` ~389–402 | Dispatch by `current_step` only; no “upload again” override. | No branch: “if step in (MISSING_FIELDS, RESUME_PREVIEW) and (file_upload or upload intent) → reset and run upload flow”. |
| `_handle_missing_field_answer` ~721–732 | Always calls `_handle_question_answer(session, content, data)`. | No check: if `data.get("file_url")` → treat as new upload and call `_handle_resume_upload(session, content, data)` instead. |
| `_handle_resume_confirmation` ~1379–1394 | “Switch to upload” only when `method == "aivi_bot"` and `_is_choosing_upload`. | No branch for `method == "pdf_upload"` and (new file in `data` or “upload again” button) → set step to UPLOAD_RESUME and show file field / run extraction with new file. |
| `_handle_question_answer` ~827–852 | When `question_key == "resume_pdf"` and `pdf_upload_no_role_use_general`, we re-ask current question. | We do not distinguish “duplicate upload (same file)” vs “new upload (new file_url)”. So even a **new** file is treated as duplicate and we never call `_handle_resume_upload`. |

---

## Flow that reproduces the bug

1. User uploads PDF → step becomes EXTRACTION_PROCESSING then MISSING_FIELDS.
2. Bot asks e.g. salary, then DOB (`current_question_key` = e.g. `date_of_birth`).
3. User **leaves** without saving (or UI reuses same session).
4. Session remains **ACTIVE**, step = **MISSING_FIELDS**, context has old `collected_data`, `current_question_key`, etc.
5. User comes back and **uploads a new PDF** (or clicks upload again).
6. Frontend sends POST with `message_type: "file_upload"`, `message_data: { file_url: "...", question_key: "resume_pdf" }` to the **same** `session_id`.
7. Backend: `current_step` = MISSING_FIELDS → `_handle_missing_field_answer` → `_handle_question_answer`.
8. We hit the `question_key == "resume_pdf"` branch and **re-ask the current question** (e.g. DOB). We **never** use the new `file_url` or call `_handle_resume_upload`.
9. User sees a question (DOB/experience, etc.) and no upload field.

---

## Intended behavior (for fix)

- **MISSING_FIELDS**: If `data.get("file_url")` is present, treat as **new upload** → reset step/context as needed and call `_handle_resume_upload(session, content, data)` so the new file is extracted and we show either new missing-field questions or preview.
- **RESUME_PREVIEW** (pdf_upload): If user sends a new file (`data.get("file_url")`) or explicit “upload again” (e.g. button), set step to UPLOAD_RESUME and show file field (and optionally run extraction if file_url already present).
- Optionally: after **successful save**, clear or minimalize `context_data` so any future reuse of the session doesn’t carry stale question state (currently we only set step=COMPLETED and session_status=COMPLETED; context is otherwise unchanged).

---

## Files to change (for fix)

1. **chat_service.py**
   - **`_handle_missing_field_answer`**: Before delegating to `_handle_question_answer`, if `data.get("file_url")` is present, call `_handle_resume_upload(session, content, data)` instead (and return its result). Optionally reset context for a clean upload (e.g. clear `current_question_key`, `missing_keys_queue`, or leave as-is and let `_handle_resume_upload` overwrite what it needs).
   - **`_handle_resume_confirmation`**: Add a branch for `method == "pdf_upload"` when `data.get("file_url")` is present or `_is_choosing_upload(content, data)`: set step to UPLOAD_RESUME, update context, and either return INPUT_FILE message or call `_handle_resume_upload` if we already have a file_url.
2. **Optional**: In `_handle_resume_confirmation` after successful save, set `context_data` to a minimal completed state (e.g. only step, resume_id) so no stale question/upload state remains.

No changes to repository or API contract are required for the above; the fix is inside the existing handlers and uses existing `message_data` (e.g. `file_url`, `button_id`).
