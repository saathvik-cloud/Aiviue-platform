# Candidate Module – Verification & Testing

## File upload flow (verified)

1. **Resume PDF**: Frontend uploads the file to **Supabase Storage** (`resumes` bucket) via `uploadResume()` in `client/src/lib/supabase.ts`. The frontend gets a **public URL** and sends it to the backend in the chat message (`file_url`). The backend fetches the PDF from that URL (e.g. in `resume_extraction_service.py` via `extract_from_url_async`) and runs extraction. No backend file upload endpoint is used for resumes.

2. **Profile photo**: Frontend uploads to Supabase Storage (`profile-photos` bucket) via `uploadProfilePhoto()`, then updates the candidate profile with the returned URL. Ensure the `profile-photos` bucket exists in your Supabase project (create it if missing).

## WebSocket (frontend ↔ backend)

- **Backend**: `GET /api/v1/candidate-chat/ws/{session_id}?candidate_id={uuid}` (FastAPI WebSocket).
- **Frontend**: `CandidateChatSocketManager` in `client/src/lib/websocket/candidate-chat-socket.ts` builds the URL from `NEXT_PUBLIC_API_URL` (e.g. `ws://localhost:8000/...` in dev), so the client connects to the same host as the REST API.
- **How to verify**: Log in as a candidate, open “Build Resume”, create a session and send a message. In the browser Network tab, filter by “WS”; you should see a connection to `/api/v1/candidate-chat/ws/...` with status 101. Backend logs should show the WebSocket connection and message handling.

## Quick test checklist

1. **Profile photo**: Candidate Dashboard → Profile → “Upload Photo” or camera icon → choose image &lt; 2MB → photo appears and persists after refresh.
2. **Resume history**: After creating a resume (AIVI or PDF upload), Candidate Dashboard → Resume → “Resume History” shows the latest resume with version and “Download PDF” if available.
3. **Flow = upload**: Open “Upload PDF” from the resume page (or `/candidate/dashboard/resume/new?flow=upload`) → bot should immediately ask for PDF upload.
4. **Job recommendations**: Candidate Dashboard → Jobs → see “For You” / “Explore All Jobs”. With profile category/location set, “For You” filters; “View details” opens the job detail page.
