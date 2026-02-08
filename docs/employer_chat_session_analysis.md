# Employer Chat – Session Behavior Analysis

## What Was Implemented (Code)

- **Employer chat header UI:** Same behavior as candidate module.
  - **Connecting…** (amber/orange, pulsing Wifi icon + status dot) when session is not ready (`!currentSessionId` or `isInitializing` or `createSession.isPending`).
  - **Connected** (green CheckCircle + “Connected” + green status dot) when session is ready.
- **Where:** `ChatHeader` now accepts `sessionReady`; `ChatContainer` passes `sessionReady={Boolean(currentSessionId) && !isInitializing && !createSession.isPending}`.

---

## Employer vs Candidate – Session Behavior (Analysis Only)

### Candidate module (current behavior)

- **Backend:** Session create is **idempotent**.
  - If an **active** resume session already exists and `force_new` is false → backend **returns that session** (“resume where you left off”).
  - If `force_new` is true (e.g. “+ New Resume”) → always creates a **new** session.
- **UI:**
  - **New Resume** → new session.
  - **Reopen chat / same session** → continues in the same session (backend returns existing active session).

### Employer module (current behavior)

- **Backend:** Session create is **not idempotent**.
  - Every `POST /api/v1/chat/sessions` call **creates a new session**. There is no “return existing active session” or `force_new`; the employer chat repo/service do not check for an existing active session.
- **UI:**
  - **“New” button** → calls `handleNewChat()` → creates a **new** session and shows welcome messages. ✅ “New chat = new session.”
  - **History → select a session** → `handleSelectSession(sessionId)` sets `currentSessionId` and refetches that session’s messages. ✅ “Resume where you left off” **when you explicitly choose a session from history.**
  - **Reopen chat page (e.g. navigate away and back, or refresh)** → On mount, if there is no `currentSessionId`, the effect runs and calls `handleNewChat()` once → **creates a new session every time**. So you do **not** automatically resume the last session; you get a new one.

### Summary

| Behavior | Candidate | Employer |
|----------|-----------|----------|
| New chat button → new session | ✅ (force_new) | ✅ |
| Select session from history → resume that session | ✅ | ✅ |
| Reopen / return to chat without clicking New → resume same session | ✅ (backend returns active session) | ❌ (new session created on mount) |

So: employer chat **does** support “new chat = new session” and “resume when I pick a session from history,” but **does not** support “resume the same session when I come back to the chat later” unless that session is explicitly selected from history. Adding that would require backend support (e.g. “get or create” active session, or storing “last session” and restoring it on mount).
