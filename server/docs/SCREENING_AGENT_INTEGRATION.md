# Screening Agent API Integration Guide

This document describes how to integrate the Screening Agent with the Aiviue Platform backend.

---

## Base URL

```
https://<your-platform-host>/api/v1
```

Example (local): `http://localhost:8000/api/v1`

---

## Authentication

When `SCREENING_API_KEY` is configured on the platform, include the API key in the request header:

```
X-Api-Key: <your-api-key>
```

If not configured, no auth is required (development mode only).

---

## Endpoints

### 1. Submit Screened Application

**POST** `/screening/applications`

Submits a screened candidate + application. Platform creates/updates candidate, optional resume, and job application.

#### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| Content-Type | Yes | application/json |
| X-Api-Key | If configured | Your API key |

#### Request Body (JSON)

```json
{
  "job_id": "uuid",
  "correlation_id": "optional-string-for-your-tracking",
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
      "skill_match": {"python": 0.9, "sql": 0.7},
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

#### Field Reference

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| job_id | UUID | Yes | Must be a published job |
| correlation_id | string | No | Your ID for debugging/correlation |
| candidate | object | Yes | See candidate fields below |
| resume | object | No | Omit if no resume |

**Candidate fields:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| phone | string | Yes | 10-digit Indian mobile; maps to `mobile` in platform |
| name | string | Yes | |
| email | string | No | |
| current_location | string | No | |
| years_experience | int | No | 0-70 |
| relevant_skills | string | No | |
| job_title | string | No | |
| work_preference | string | No | remote, onsite, hybrid |
| is_fresher | bool | No | |
| resume_summary | string | No | |
| fit_score_details | object | No | Structured scoring output |

**Resume fields:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| file_url | string | No | Maps to `pdf_url` in platform |
| file_type | string | No | pdf, docx, parsed-json |
| file_name | string | No | |
| file_size | int | No | bytes |
| mime_type | string | No | |
| resume_data | object | No | Structured JSON for card display |

#### Response (201 Created)

```json
{
  "application_id": "uuid",
  "candidate_id": "uuid",
  "resume_id": "uuid-or-null",
  "message": "Application submitted successfully.",
  "already_applied": false
}
```

#### Error Responses

| Status | Code | Meaning |
|--------|------|---------|
| 400 | REQUEST_VALIDATION_FAILED | Invalid payload (check error details) |
| 404 | JOB_NOT_FOUND | Job does not exist |
| 422 | JOB_NOT_PUBLISHED | Job exists but is not published |
| 401 | - | Invalid/missing API key |

---

### 2. List Failed Requests

**GET** `/screening/failed-requests`

Returns payloads that failed to insert (dead letter table). Use for debugging and visibility.

#### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| X-Api-Key | If configured | Your API key |

#### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| status | string | (all) | Filter: failed, pending_retry, resolved |
| limit | int | 50 | Max items (1-100) |
| offset | int | 0 | Pagination offset |

#### Response (200 OK)

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

---

## JSON Schema (POST body)

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
      "description": "Job this application is for"
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
        "phone": {
          "type": "string",
          "minLength": 10,
          "maxLength": 20,
          "description": "10-digit Indian mobile"
        },
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

## Field Mapping (API → Platform DB)

| Your Field | Platform Field |
|------------|----------------|
| phone | mobile |
| file_url | pdf_url |

---

## Example cURL

```bash
# Submit application
curl -X POST "https://your-platform.com/api/v1/screening/applications" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your-api-key" \
  -d '{
    "job_id": "8fadd86b-0cdf-4e95-bdc0-81c8db73e923",
    "candidate": {
      "phone": "9876543210",
      "name": "Test Candidate"
    }
  }'

# List failed requests
curl "https://your-platform.com/api/v1/screening/failed-requests" \
  -H "X-Api-Key: your-api-key"
```

---

## Idempotency

POST is idempotent: if the same candidate (by phone) has already applied to the same job, the API returns the existing application with `already_applied: true`.

---

## Failed Payloads

When a request fails (validation, job not found, DB error), the payload is stored in a dead letter table. Use GET `/screening/failed-requests` to inspect and retry after fixing issues.
