"""
Resume From Chat LLM Service.

One Gemini call to convert raw Q&A (from fallback or chat) into the exact flat
schema expected by ResumeBuilderService (QUESTION_KEY_TO_SECTION keys).
Used when candidate has no role or we want an intelligent polish pass.
"""

import json
from typing import Any, Dict, Optional

from app.domains.candidate_chat.services.resume_builder_service import (
    QUESTION_KEY_TO_SECTION,
)
from app.shared.llm.client import GeminiClient, LLMError, get_gemini_client
from app.shared.logging import get_logger


logger = get_logger(__name__)

# All known keys the resume builder expects (so LLM knows what to output)
RESUME_SCHEMA_KEYS = list(QUESTION_KEY_TO_SECTION.keys())

# Add common fallback keys that map to sections or additional_info
EXTRA_KEYS = [
    "reason_for_change",
    "training_certificates",
    "when_can_start",
    "current_work",
    "tools_machines",
    "experience_years_blue",
    "languages_blue",
    "night_shift_ok",
    "why_this_work",
    "iti_training",
    "worked_before",
    "learn_on_job",
    "current_job_daily",
    "equipment_systems",
    "certificates_licenses",
    "difficult_problem",
    "work_alone",
    "on_call_ok",
    "customer_facing",
    "desired_role_title",
]
ALL_KEYS = list(dict.fromkeys(RESUME_SCHEMA_KEYS + EXTRA_KEYS))


SYSTEM_INSTRUCTION = """You are a resume builder. You receive a list of question-answer pairs from a conversation.
Your task is to output a single JSON object where:
1. Keys are exactly the field names from the allowed list (use snake_case).
2. Values are the extracted or inferred values from the answers. Use the right type: string, number, boolean, or list of strings.
3. Map conversational answers to the correct field. Examples:
   - "What role are you looking for?" -> desired_role_title or full_name if it's their name
   - "Why changing job?" -> reason_for_change (string) or about
   - "Do you have driving license?" -> has_driving_license (boolean)
   - "Salary?" -> salary_expectation (number)
   - "Languages?" -> languages_known (list or comma-separated string)
   - "Experience years?" -> experience_years (number)
   - "About me" -> about (string)
4. Only include keys that you have data for. Omit keys with no answer.
5. Normalize: dates as YYYY-MM-DD, booleans as true/false, numbers as numbers not strings.
6. If a question does not map to a known key, put it in a key that fits (e.g. reason_for_change, or use "additional_info" as a JSON object with sub-keys - but prefer flat keys from the list).
Output ONLY valid JSON, no markdown or explanation."""

PROMPT_TEMPLATE = """Below are the question-answer pairs from the conversation. Produce a flat JSON object with keys from the allowed list and values from the answers.

Allowed keys (use only these, snake_case): {allowed_keys}

Job type for context: {job_type}

Question-Answer pairs:
{qa_list}

Output a single JSON object:"""


async def build_resume_from_chat_llm(
    collected_data: Dict[str, Any],
    job_type: str = "blue_collar",
    role_name: str = "General",
    llm_client: Optional[GeminiClient] = None,
) -> Dict[str, Any]:
    """
    Call Gemini once to convert raw collected_data (Q&A) into flat schema expected by resume builder.

    Args:
        collected_data: Raw answers from chat (question_key -> value).
        job_type: blue_collar, white_collar, or grey_collar for context.
        role_name: Role name for context.
        llm_client: Optional Gemini client (uses get_gemini_client() if not provided).

    Returns:
        Flat dict with keys from RESUME_SCHEMA / QUESTION_KEY_TO_SECTION. Ready for compile_resume().
    """
    client = llm_client or get_gemini_client()
    qa_list = "\n".join(
        f"- {k}: {v!r}" for k, v in sorted(collected_data.items()) if v is not None and str(v).strip()
    )
    if not qa_list.strip():
        return collected_data  # Nothing to do

    allowed_keys_str = ", ".join(ALL_KEYS)
    prompt = PROMPT_TEMPLATE.format(
        allowed_keys=allowed_keys_str,
        job_type=job_type,
        qa_list=qa_list or "(none)",
    )

    try:
        response = await client.generate_json(
            prompt=prompt,
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.1,
            max_tokens=4096,
        )
    except LLMError as e:
        logger.warning("Resume-from-chat LLM call failed: %s; using raw collected_data", e)
        return collected_data

    if not isinstance(response, dict):
        logger.warning("Resume-from-chat LLM returned non-dict; using raw collected_data")
        return collected_data

    # Pass through keys that match our schema or extra list; others go to additional_info
    out = {}
    for k, v in response.items():
        if k in QUESTION_KEY_TO_SECTION or k in EXTRA_KEYS:
            out[k] = v
        elif k != "additional_info":
            out[k] = v  # LLM may emit other keys; resume builder puts unknown in additional_info
    return out if out else collected_data
