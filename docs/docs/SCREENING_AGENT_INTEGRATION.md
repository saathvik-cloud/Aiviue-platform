# Screening Agent API Integration Guide

**A beginner-friendly guide for developers:** How to send candidate data from your Screening Agent to the Aiviue (iView) platform.

---

## Table of Contents

1. [What This Guide Is For](#what-this-guide-is-for)
2. [The Big Picture](#the-big-picture)
3. [Before You Start – What You Need](#before-you-start--what-you-need)
4. [Step-by-Step: How to Implement](#step-by-step-how-to-implement)
5. [The Two APIs You Will Use](#the-two-apis-you-will-use)
6. [API 1: Submit a Screened Candidate](#api-1-submit-a-screened-candidate)
7. [API 2: List Failed Requests (for Debugging)](#api-2-list-failed-requests-for-debugging)
8. [Field Reference (Quick Lookup)](#field-reference-quick-lookup)
9. [Examples You Can Copy](#examples-you-can-copy)
10. [When Something Goes Wrong](#when-something-goes-wrong)
11. [Important Notes](#important-notes)

---

## What This Guide Is For

- **You:** A developer building or maintaining the **Screening Agent** (the system that screens candidates, e.g. from Meta leads).
- **Goal:** After your Screening Agent screens a candidate, you need to **send that candidate’s data to the Aiviue platform** (the iView side) so the candidate appears as an application on the right job.
- **This document:** Tells you exactly which URLs to call, what JSON to send, and how to handle errors—in a simple, step-by-step way.

---

## The Big Picture

```
┌─────────────────────┐         ┌─────────────────────────────────────┐
│  Your Screening     │   API   │  Aiviue (iView) Platform             │
│  Agent (your code)  │ ──────► │  - Creates/updates candidate         │
│                     │  POST   │  - Saves resume (if you send it)     │
│  - Gets lead data   │         │  - Creates job application            │
│  - Screens candidate│         │  - Shows up in iView for recruiters   │
└─────────────────────┘         └─────────────────────────────────────┘
```

**In short:** Your backend receives screened candidate data → your backend calls the Aiviue API once per screened application → Aiviue stores the candidate and links them to the job. Recruiters then see the application in the iView platform.

**Where to call from:** Call the Aiviue API from **your backend** (Node.js, Python, etc.), not from the browser. Meta sends leads to your backend; your backend then calls Aiviue. This keeps future API keys secure.

---

## Before You Start – What You Need

- [ ] **A valid `job_id`**  
  The job must already exist in the Aiviue database and be **published**. For testing, the Aiviue team will give you one or more job UUIDs. Use exactly those in your requests.

- [ ] **Candidate data from your Screening Agent**  
  At minimum: **phone** (10-digit) and **name**. Everything else (email, skills, resume URL, etc.) is optional but recommended.

- [ ] **Base URL**  
  Live API base URL:
  ```text
  https://aiviue-mvp-server-production-3788.up.railway.app
  ```

- [ ] **No API key for now**  
  For testing, do **not** send any `X-Api-Key` header. When the platform enables API keys later, you will add: `X-Api-Key: <your-api-key>`.

---

## Step-by-Step: How to Implement

1. **Get a test `job_id`**  
   Ask the Aiviue team for at least one UUID of a **published** job. You will send this in every “submit application” request.

2. **When a candidate is screened in your system**  
   Build a JSON body that includes:
   - `job_id` (the one you received)
   - `candidate` with at least `phone` and `name`
   - Optionally `resume` (e.g. `file_url`, `file_name`) and any extra candidate fields

3. **Send a POST request**  
   - **URL:** `https://aiviue-mvp-server-production-3788.up.railway.app/api/v1/screening/applications`  
   - **Method:** `POST`  
   - **Header:** `Content-Type: application/json`  
   - **Body:** the JSON from step 2

4. **Handle the response**  
   - **201:** Success. You get `application_id`, `candidate_id`, and a success message.  
   - **4xx:** See [When Something Goes Wrong](#when-something-goes-wrong) and optionally use the “list failed requests” API to inspect stored failures.

5. **(Optional) Check failed requests**  
   If something failed, you can call **GET** `.../api/v1/screening/failed-requests` to see stored failed payloads and error messages for debugging and retry.

---

## The Two APIs You Will Use

| What you want to do              | Method | Full URL |
|----------------------------------|--------|----------|
| Submit a screened application    | **POST** | `https://aiviue-mvp-server-production-3788.up.railway.app/api/v1/screening/applications` |
| List failed requests (debugging) | **GET**  | `https://aiviue-mvp-server-production-3788.up.railway.app/api/v1/screening/failed-requests` |

---

## API 1: Submit a Screened Candidate

**Purpose:** Send one screened candidate + optional resume to Aiviue. The platform will create or update the candidate and create a job application.

### Request

- **Method:** `POST`
- **URL:** `https://aiviue-mvp-server-production-3788.up.railway.app/api/v1/screening/applications`
- **Headers:**  
  - `Content-Type: application/json` (required)  
  - `X-Api-Key`: omit for testing; add when the platform enables it

### Minimum body (only required fields)

You can start with this and add more fields later:

```json
{
  "job_id": "8fadd86b-0cdf-4e95-bdc0-81c8db73e923",
  "candidate": {
    "phone": "9876543210",
    "name": "Full Name"
  }
}
```

- `job_id`: Must be a UUID of a **published** job in Aiviue (get from Aiviue team for testing).
- `candidate.phone`: 10-digit Indian mobile (required).
- `candidate.name`: Full name (required).

### Full body (all optional fields included)

Use this when you have more data from your Screening Agent:

```json
{
  "job_id": "8fadd86b-0cdf-4e95-bdc0-81c8db73e923",
  "correlation_id": "your-internal-id-123",
  "candidate": {
    "phone": "9876543210",
    "name": "Full Name",
    "email": "email@example.com",
    "current_location": "Mumbai, Maharashtra",
    "years_experience": 3,
    "relevant_skills": "Python, SQL, ETL",
    "job_title": "Data Engineer",
    "work_preference": "remote",
    "is_fresher": false,
    "resume_summary": "LLM-generated summary...",
    "fit_score_details": {
      "overall": 78,
      "skill_match": { "python": 0.9, "sql": 0.7 },
      "notes": "Relevant exp in ETL"
    }
  },
  "resume": {
    "file_url": "https://storage.example.com/resume.pdf",
    "file_type": "pdf",
    "file_name": "resume.pdf",
    "file_size": 102400,
    "mime_type": "application/pdf",
    "resume_data": {}
  }
}
```

- **`correlation_id`:** Optional. Your own ID for tracking this submission (e.g. for debugging).
- **`resume`:** Optional. If the candidate has no resume, omit the whole `resume` object.

### Success response (201 Created)

```json
{
  "application_id": "uuid",
  "candidate_id": "uuid",
  "resume_id": "uuid-or-null",
  "message": "Application submitted successfully.",
  "already_applied": false
}
```

- If the same candidate (same phone) already applied to the same job, you still get 201 but with `already_applied: true`. Safe to retry.

### Error responses (what to show your developer)

| HTTP Status | Error code (in body) | Meaning |
|-------------|----------------------|---------|
| 400 | REQUEST_VALIDATION_FAILED | Invalid JSON or missing/invalid fields (e.g. phone too short, invalid email). Check the response body for details. |
| 404 | JOB_NOT_FOUND | The `job_id` does not exist in Aiviue. Use a job_id provided by the Aiviue team or seed the job first. |
| 422 | JOB_NOT_PUBLISHED | The job exists but is not published. Only published jobs accept applications. |
| 401 | - | Invalid or missing API key (when API key is enabled). |

Failed requests are stored in a “dead letter” table. Your developer can list them with the second API (see below).

---

## API 2: List Failed Requests (for Debugging)

**Purpose:** See payloads that failed to be processed (e.g. wrong job_id, validation errors). Use this to fix data and retry.

- **Method:** `GET`
- **URL:** `https://aiviue-mvp-server-production-3788.up.railway.app/api/v1/screening/failed-requests`

### Optional query parameters

| Param   | Type   | Default | Description |
|---------|--------|---------|-------------|
| status  | string | (all)   | Filter: `failed`, `pending_retry`, `resolved` |
| limit   | int    | 50      | Max items (1–100) |
| offset  | int    | 0       | Pagination offset |

### Example response (200 OK)

```json
{
  "items": [
    {
      "id": "uuid",
      "raw_payload": { ... },
      "error_message": "Job not found",
      "error_code": "JOB_NOT_FOUND",
      "status": "failed",
      "correlation_id": null,
      "created_at": "2026-02-15T14:25:40.362467Z"
    }
  ],
  "total": 1
}
```

Your developer can use `raw_payload` and `error_message` / `error_code` to fix the request and resubmit.

---

## Field Reference (Quick Lookup)

### Top-level

| Field            | Type   | Required | Notes |
|------------------|--------|----------|--------|
| job_id           | UUID   | Yes      | Must exist in Aiviue and be **published**. |
| correlation_id   | string | No       | Your tracking/debug ID. |
| candidate        | object | Yes      | See below. |
| resume           | object | No       | Omit if no resume. |

### Candidate object

| Field               | Type   | Required | Notes |
|---------------------|--------|----------|--------|
| phone               | string | Yes      | 10-digit Indian mobile; stored as `mobile` in platform. |
| name                | string | Yes      | |
| email               | string | No       | |
| current_location    | string | No       | |
| years_experience    | int    | No       | 0–70 |
| relevant_skills     | string | No       | |
| job_title           | string | No       | |
| work_preference     | string | No       | e.g. `remote`, `onsite`, `hybrid` |
| is_fresher          | bool   | No       | |
| resume_summary      | string | No       | |
| fit_score_details   | object | No       | Any structure (e.g. overall score, skill match). |

### Resume object

| Field       | Type   | Required | Notes |
|------------|--------|----------|--------|
| file_url   | string | No       | Stored as `pdf_url` in platform. |
| file_type  | string | No       | e.g. `pdf`, `docx`, `parsed-json` |
| file_name  | string | No       | |
| file_size  | int    | No       | Size in bytes |
| mime_type  | string | No       | e.g. `application/pdf` |
| resume_data| object | No       | Optional structured JSON for display |

---

## Examples You Can Copy

### cURL (command line)

```bash
# Submit application (no API key for testing)
curl -X POST "https://aiviue-mvp-server-production-3788.up.railway.app/api/v1/screening/applications" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "8fadd86b-0cdf-4e95-bdc0-81c8db73e923",
    "candidate": {
      "phone": "9876543210",
      "name": "Test Candidate",
      "email": "test@example.com"
    },
    "resume": {
      "file_url": "https://storage.example.com/resume.pdf",
      "file_name": "resume.pdf"
    }
  }'

# List failed requests
curl "https://aiviue-mvp-server-production-3788.up.railway.app/api/v1/screening/failed-requests"
```

### Node.js (fetch)

```javascript
const BASE_URL = "https://aiviue-mvp-server-production-3788.up.railway.app/api/v1";

async function submitApplication(payload) {
  const res = await fetch(`${BASE_URL}/screening/applications`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

// Example: minimal payload
const payload = {
  job_id: "8fadd86b-0cdf-4e95-bdc0-81c8db73e923",  // Use job_id from Aiviue team
  candidate: { phone: "9876543210", name: "Test Candidate" },
  resume: { file_url: "https://...", file_name: "resume.pdf" },
};

submitApplication(payload).then(console.log).catch(console.error);
```

### Python (requests)

```python
import requests

BASE_URL = "https://aiviue-mvp-server-production-3788.up.railway.app/api/v1"

def submit_application(payload):
    r = requests.post(
        f"{BASE_URL}/screening/applications",
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    return r.json()

# Example: minimal payload
payload = {
    "job_id": "8fadd86b-0cdf-4e95-bdc0-81c8db73e923",
    "candidate": {"phone": "9876543210", "name": "Test Candidate"},
    "resume": {"file_url": "https://...", "file_name": "resume.pdf"},
}
print(submit_application(payload))
```

---

## When Something Goes Wrong

1. **404 JOB_NOT_FOUND**  
   The `job_id` is not in Aiviue’s database. For testing, use a job_id given by the Aiviue team. For your own jobs, the Aiviue team can seed them (e.g. via `scripts/seed_screening_job.py`); then use `--verify` to confirm the job exists and is published.

2. **422 JOB_NOT_PUBLISHED**  
   The job exists but is not published. Only published jobs accept applications. Publish the job in Aiviue or use another job_id.

3. **400 REQUEST_VALIDATION_FAILED**  
   Check the response body for which field failed (e.g. phone length, email format). Fix the payload and retry. Failed payloads are stored; use GET `/screening/failed-requests` to inspect them.

4. **401 (when API key is enabled)**  
   Add the correct `X-Api-Key` header. You will receive the key when the platform enables it.

5. **Duplicate submission**  
   If the same candidate (same phone) already applied to the same job, the API still returns 201 and `already_applied: true`. No duplicate application is created; safe to retry.

---

## Important Notes

- **Job ID:** Always use a `job_id` that exists in Aiviue and is **published**. For testing, get one from the Aiviue team.
- **Call from backend:** Call these APIs from your backend (Node/Python/etc.), not from the browser, so API keys stay secure when they are enabled.
- **Idempotency:** Sending the same candidate (same phone) for the same job again returns the existing application with `already_applied: true`; safe to retry.
- **Failed payloads:** Failed requests are stored. Use GET `/screening/failed-requests` to list them, fix issues (e.g. job_id, validation), and retry.
- **Field mapping:** `phone` → `mobile`, `file_url` → `pdf_url` in the platform.

---

## JSON Schema (POST body)

For validation or code generation, you can use this schema for the POST body:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["job_id", "candidate"],
  "additionalProperties": false,
  "properties": {
    "job_id": {
      "type": "string",
      "format": "uuid",
      "description": "Job this application is for (must exist in Aiviue DB)"
    },
    "correlation_id": {
      "type": ["string", "null"],
      "maxLength": 255,
      "description": "Optional ID for correlation"
    },
    "candidate": {
      "type": "object",
      "required": ["phone", "name"],
      "properties": {
        "phone": { "type": "string", "minLength": 10, "maxLength": 20 },
        "name": { "type": "string", "minLength": 1, "maxLength": 255 },
        "email": { "type": ["string", "null"], "format": "email" },
        "current_location": { "type": ["string", "null"], "maxLength": 255 },
        "years_experience": { "type": ["integer", "null"], "minimum": 0, "maximum": 70 },
        "relevant_skills": { "type": ["string", "null"] },
        "job_title": { "type": ["string", "null"] },
        "work_preference": { "type": ["string", "null"], "maxLength": 50 },
        "is_fresher": { "type": ["boolean", "null"] },
        "resume_summary": { "type": ["string", "null"] },
        "fit_score_details": { "type": ["object", "null"] }
      }
    },
    "resume": {
      "type": ["object", "null"],
      "properties": {
        "file_url": { "type": ["string", "null"], "maxLength": 500 },
        "file_type": { "type": ["string", "null"], "maxLength": 50 },
        "file_name": { "type": ["string", "null"], "maxLength": 500 },
        "file_size": { "type": ["integer", "null"], "minimum": 0 },
        "mime_type": { "type": ["string", "null"], "maxLength": 100 },
        "resume_data": { "type": ["object", "null"] }
      }
    }
  }
}
```

---

*End of Screening Agent API Integration Guide. For a valid test `job_id`, contact the Aiviue team or run `python scripts/seed_screening_job.py` and use `--verify` to confirm.*
