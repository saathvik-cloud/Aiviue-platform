# WhatsApp Outreach & WATI Integration Documentation

This document details the integration between our backend and the WATI Business API. It specifically outlines the **WATI API endpoints** consumed by our system, the **Internal API endpoints** exposed to our frontend, and how they map to each other.

## 1. WATI API Endpoints (External)

These are the endpoints our backend calls on the WATI servers. These calls happen inside `app/modules/whatsapp_outreach/services/wati_client.py`.

### 1.1 Send Template Message
**Used to send a WhatsApp message to a lead.**

- **WATI Endpoint**: `POST /api/v1/sendTemplateMessage`
- **Full URL**: `{{WATI_API_ENDPOINT}}/api/v1/sendTemplateMessage`
- **Query Parameters**:
  - `whatsappNumber`: The lead's phone number (E.164 format, e.g., `919876543210`)
- **Request Body (JSON)**:
  ```json
  {
    "template_name": "welcome_message_v1",  // Must match an approved template name in WATI
    "parameters": [                         // List of variables for the template
      {
        "name": "name",
        "value": "John Doe"
      },
      {
        "name": "company",
        "value": "Acme Corp"
      }
    ],
    "broadcast_name": "january_outreach"    // Optional: for WATI analytics
  }
  ```
- **Response**: Returns message IDs and status.

### 1.2 Get Message Templates
**Used to fetch the list of approved templates for the UI dropdown.**

- **WATI Endpoint**: `GET /api/v1/getMessageTemplates`
- **Full URL**: `{{WATI_API_ENDPOINT}}/api/v1/getMessageTemplates`
- **Query Parameters**:
  - `pageSize`: `100` (default)
  - `pageNumber`: `1` (default)
- **Response**: List of template objects containing `elementName` (template_name), body text, and parameters.

### 1.3 Get Messages (History)
**Used to show the chat history with a lead in the backend UI.**

- **WATI Endpoint**: `GET /api/v1/getMessages/{phone_number}`
- **Full URL**: `{{WATI_API_ENDPOINT}}/api/v1/getMessages/919876543210`
- **Query Parameters**:
  - `pageSize`: `100`
  - `pageNumber`: `1`
- **Response**: List of messages (both sent and received).

### 1.4 Add Contact
**Used to add or update a lead in WATI's system.** (Often called implicitly or during sync).

- **WATI Endpoint**: `POST /api/v1/addContact/{phone_number}`
- **Full URL**: `{{WATI_API_ENDPOINT}}/api/v1/addContact/919876543210`
- **Request Body (JSON)**:
  ```json
  {
    "name": "John Doe",
    "customParams": [
      {
        "name": "email",
        "value": "john@example.com"
      }
    ]
  }
  ```

### 1.5 Get Contacts
**Used to sync contact lists from WATI.**

- **WATI Endpoint**: `GET /api/v1/getContacts`
- **Full URL**: `{{WATI_API_ENDPOINT}}/api/v1/getContacts`

### 1.6 Webhook Registration (Programmatic)
*(Currently managed manually in dashboard, but code exists)*
- **WATI Endpoint**: `POST /api/v2/webhookEndpoints`

---

## 2. Internal API <-> External WATI API Mapping

This table shows which of **our** backend endpoints trigger which **WATI** API endpoints.

| Feature | Our Internal Endpoint (Frontend calls this) | Consumed WATI Endpoint (Backend calls this) | Description |
| :--- | :--- | :--- | :--- |
| **Send Message** | `POST /api/v1/whatsapp/leads/{id}/send` | `POST /api/v1/sendTemplateMessage` | Sends the message via WATI. |
| **List Templates** | `GET /api/v1/whatsapp/templates` | `GET /api/v1/getMessageTemplates` | Fetches templates (cached for 5m). |
| **Chat History** | `GET /api/v1/whatsapp/leads/{id}/messages` | `GET /api/v1/getMessages/{phone}` | Fetches real-time chat history. |
| **Sync Status** | `POST /api/v1/whatsapp/leads/{id}/sync-status` | `GET /api/v1/getMessages/{phone}` | Checks latest message status. |
| **Bulk Check** | `POST /api/v1/whatsapp/bulk/check` | *(Database only)* | Checks local DB for eligibility. |
| **Bulk Send** | `POST /api/v1/whatsapp/bulk/jobs` | `POST /api/v1/sendTemplateMessage` | Calls send endpoint multiple times. |

---

## 3. Configuration & Credentials
The following credentials are currently configured in your `.env` file for the WATI integration:

| Key | Value | Description |
|-----|-------|-------------|
| **WATI_API_ENDPOINT** | `https://live-mt-server.wati.io/105961` | The base URL for WATI API calls. |
| **WATI_CHANNEL_NUMBER** | `919981859930` | The sender phone number associated with your WATI account. |
| **WATI_WEBHOOK_SECRET** | `KqUQL3ZWLNW1ZWoPOTIP24qPzMvG5Z9RIUSz3cdHdAY` | Secret used to verify the authenticity of incoming webhooks. |
| **WATI_API_TOKEN** | `Bearer eyJhbGciOiJIUzI1NiIsInR5...` | The Bearer token used for authentication (truncated for security). |

## 4. Webhook Handling
The system exposes an endpoint at `/api/v1/whatsapp/webhook` to handle incoming events from WATI.

- **Security**:
  - Validates the `X-Webhook-Secret` header against your `WATI_WEBHOOK_SECRET`.
  - Optionally checks against `WATI_WEBHOOK_ALLOWED_IPS` (currently empty/disabled).
- **Processed Events**:
  - `templateMessageSent`: Marks message as sent in local DB.
  - `messageDelivered`: Updates status to 'delivered'.
  - `messageRead`: Updates status to 'read'.
  - `templateMessageFailed`: Logs failure reason.
  - `message`: Captures incoming replies from leads.

## 5. Directory Structure
- **Client Service**: `app/modules/whatsapp_outreach/services/wati_client.py`
- **API Endpoints**: `app/modules/whatsapp_outreach/api/whatsapp_endpoints.py`
- **Schemas**: `app/modules/whatsapp_outreach/schemas/whatsapp_schemas.py`
- **Cache Logic**: `app/modules/whatsapp_outreach/services/wati_cache.py`
