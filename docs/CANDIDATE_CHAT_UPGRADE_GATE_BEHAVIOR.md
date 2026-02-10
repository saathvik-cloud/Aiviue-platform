# Candidate Chat: One-Time Free & Upgrade Gate Behavior

## Session types

- **resume_creation**: Build resume by chatting with AIVI bot (questions, then preview, then save).
- **resume_upload**: User uploads a PDF; we extract and optionally ask missing fields. No limit.

## When creating a session (POST /api/v1/candidate-chat/sessions)

1. **Idempotency (both types)**  
   If there is already an **active** session of the same type and `force_new=False`, the API **returns that existing session** (no new one created). No upgrade gate is applied.

2. **resume_upload**  
   **Always allowed** for any user (free or pro). The user is providing their own resume; we do not limit this.

3. **resume_creation** (new session, no existing active session or `force_new=True`):
   - **Pro user (`candidate.is_pro = true`)**: **Unlimited** resume_creation sessions. Always allowed.
   - **Free user (`candidate.is_pro = false`)**:
     - If they have **zero** completed resumes with `source = aivi_bot`: **Allowed** (first time / one chance).
     - If they already have **one or more** completed resumes with `source = aivi_bot`: **403 Forbidden** with `error.code = "UPGRADE_REQUIRED"` and message like "Upgrade to premium to create multiple resumes with AIVI bot."

## Summary table

| User   | Session type      | Already has completed AIVI bot resume? | Result        |
|--------|-------------------|----------------------------------------|---------------|
| Free   | resume_creation   | No                                     | 201 Created   |
| Free   | resume_creation   | Yes                                    | 403 UPGRADE_REQUIRED |
| Pro    | resume_creation   | Any                                    | 201 Created   |
| Any    | resume_upload     | Any                                    | 201 Created   |
| Any    | (existing active session returned) | N/A                    | 201 (same session) |

## Flow summary

- **New user (free)**: First resume_creation → allowed. After they complete one resume via the bot, the next attempt to create a **new** resume_creation session → 403 UPGRADE_REQUIRED. Upload (resume_upload) remains always available.
- **Pro user**: Can create as many resume_creation sessions as they want.
- **Upload PDF**: Always available for everyone; no gate.
