"""
Pure message builders for candidate chat.

Build bot message dicts from context (no DB). Used by CandidateChatService.
"""

from typing import Any, Dict, List

from app.domains.candidate_chat.models.db_models import (
    CandidateMessageRole,
    CandidateMessageType,
)


def build_preview_messages(ctx: Dict[str, Any]) -> List[dict]:
    """Build resume preview messages (reusable across flows)."""
    collected_data = ctx.get("collected_data", {})
    return [
        {
            "role": CandidateMessageRole.BOT,
            "content": "Here's a preview of your resume. Would you like to confirm and save it?",
            "message_type": CandidateMessageType.RESUME_PREVIEW,
            "message_data": {
                "resume_data": collected_data,
                "role_name": ctx.get("role_name", ""),
                "job_type": ctx.get("job_type", ""),
            },
        },
        {
            "role": CandidateMessageRole.BOT,
            "content": "Would you like to save this resume?",
            "message_type": CandidateMessageType.BUTTONS,
            "message_data": {
                "buttons": [
                    {"id": "confirm_resume", "label": "✅ Yes, save my resume"},
                    {"id": "edit_resume", "label": "✏️ No, let me make changes"},
                ],
            },
        },
    ]
