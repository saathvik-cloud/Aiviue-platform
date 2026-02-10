"""
Candidate Chat Service - Core Orchestrator.

Manages the full conversation flow for candidate resume building.

Production patterns used:
- Dictionary dispatch for step routing (no if/elif chains)
- Idempotent session creation (returns existing active session if found)
- Context-based auto-save (every answer persisted immediately)
- Stateless service (all state in session.context_data)

Conversation Flow:
    WELCOME → CHOOSE_METHOD →
        → (aivi_bot)     → ASKING_QUESTIONS → RESUME_PREVIEW → COMPLETED
        → (pdf_upload)   → UPLOAD_RESUME → EXTRACTION_PROCESSING → MISSING_FIELDS → RESUME_PREVIEW → COMPLETED
"""

import copy
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.candidate.repository import CandidateRepository
from app.domains.candidate_chat.services.chat_constants import (
    EDIT_FIELD_ALIASES,
    WELCOME_MESSAGES,
    normalize_for_match,
)
from app.domains.candidate_chat.services.chat_message_builders import build_preview_messages
from app.domains.candidate_chat.models.db_models import (
    CandidateChatSession,
    CandidateMessageRole,
    CandidateMessageType,
    CandidateSessionStatus,
    ChatStep,
)
from app.domains.candidate_chat.models.schemas import (
    CandidateChatMessageResponse,
    CandidateChatSessionResponse,
    CandidateSendMessageResponse,
)
from app.domains.candidate_chat.repository.chat_repository import CandidateChatRepository
from app.domains.candidate_chat.services.question_engine import QuestionEngine
from app.domains.candidate_chat.services.resume_builder_service import ResumeBuilderService
from app.domains.candidate_chat.services.resume_extraction_service import (
    ResumeExtractionService,
    get_resume_extractor,
)
from app.domains.candidate_chat.services.resume_from_chat_llm_service import (
    build_resume_from_chat_llm,
)
from app.domains.job_master.repository import JobMasterRepository
from app.shared.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.shared.logging import get_logger


logger = get_logger(__name__)

# Education values that imply white vs blue collar (from fallback options)
EDUCATION_WHITE_COLLAR = {"undergraduate", "postgraduate"}
EDUCATION_BLUE_COLLAR = {"primary", "10th", "12th"}
# Experience option ids that imply experienced (≥2 years) for blue collar
EXPERIENCE_EXPERIENCED_IDS = {"2_years", "3_years", "4_years", "5_plus_years"}


def _has_known_fallback_role(collected_data: dict) -> bool:
    """True if user picked a known role from DB (job_role_id is a UUID, not 'custom')."""
    rid = collected_data.get("job_role_id")
    if not rid or str(rid).strip().lower() == "custom":
        return False
    try:
        UUID(str(rid))
        return True
    except (ValueError, TypeError):
        return False


# ==================== CHAT SERVICE ====================

class CandidateChatService:
    """
    Core orchestrator for candidate chat conversations.

    Uses dictionary dispatch to route messages to the correct handler
    based on the current conversation step.

    All state is stored in session.context_data:
    {
        "step": "asking_questions",
        "method": "aivi_bot" | "pdf_upload",
        "role_id": "uuid",
        "role_slug": "delivery-boy",
        "role_name": "Delivery Boy",
        "job_type": "blue_collar",
        "collected_data": { "full_name": "Rahul", ... },
        "answered_keys": ["full_name", "date_of_birth", ...],
        "resume_id": null
    }
    """

    def __init__(
        self,
        chat_repo: CandidateChatRepository,
        candidate_repo: CandidateRepository,
        job_master_repo: JobMasterRepository,
        resume_builder: ResumeBuilderService,
        resume_extractor: ResumeExtractionService,
        session: AsyncSession,
    ) -> None:
        self._chat_repo = chat_repo
        self._candidate_repo = candidate_repo
        self._job_master_repo = job_master_repo
        self._resume_builder = resume_builder
        self._resume_extractor = resume_extractor
        self._db_session = session

        # ==================== DICTIONARY DISPATCH ====================
        # Maps step → handler method. Each handler receives (session, user_content, user_data)
        # and returns a list of bot message dicts.
        self._step_handlers: Dict[str, Callable] = {
            ChatStep.WELCOME: self._handle_welcome_response,
            ChatStep.CHOOSE_METHOD: self._handle_method_selection,
            ChatStep.UPLOAD_RESUME: self._handle_resume_upload,
            ChatStep.EXTRACTION_PROCESSING: self._handle_extraction_result,
            ChatStep.MISSING_FIELDS: self._handle_missing_field_answer,
            ChatStep.ASKING_QUESTIONS: self._handle_question_answer,
            ChatStep.RESUME_PREVIEW: self._handle_resume_confirmation,
            ChatStep.COMPLETED: self._handle_completed_session,
        }

    # ==================== PUBLIC API ====================

    async def create_session(
        self,
        candidate_id: UUID,
        session_type: str = "resume_creation",
        force_new: bool = False,
    ) -> Tuple[CandidateChatSession, List[dict]]:
        """
        Create a new chat session with idempotency.

        If force_new is False and an active resume session already exists,
        returns it (resume-from-where-left-off). If force_new is True (e.g. "+ New Resume"),
        always creates a new session.

        Returns:
            Tuple of (session, welcome_messages)
        """
        # Verify candidate exists
        candidate = await self._candidate_repo.get_by_id(candidate_id)
        if not candidate:
            raise NotFoundError(
                message="Candidate not found",
                error_code="CANDIDATE_NOT_FOUND",
            )

        # ==================== IDEMPOTENCY CHECK ====================
        # If there's an active resume session and not force_new, return it (no message load)
        existing_session = None if force_new else await self._chat_repo.get_active_resume_session(
            candidate_id, include_messages=False
        )
        if existing_session:
            logger.info(
                f"Returning existing active session: {existing_session.id}",
                extra={"session_id": str(existing_session.id), "candidate_id": str(candidate_id)},
            )
            # Return existing session with a "welcome back" message (no upgrade gate for existing session)
            welcome_back = [{
                "role": CandidateMessageRole.BOT,
                "content": "Welcome back! Let's continue building your resume from where you left off.",
                "message_type": CandidateMessageType.TEXT,
                "message_data": {},
            }]

            # If we're in the middle of asking questions, send the next question
            if existing_session.current_step == ChatStep.ASKING_QUESTIONS:
                next_q_msgs = await self._build_next_question_messages(existing_session)
                welcome_back.extend(next_q_msgs)

            # Store welcome back messages
            await self._chat_repo.add_messages_batch(existing_session.id, welcome_back)

            # Re-fetch to get updated messages
            updated = await self._chat_repo.get_session_by_id(existing_session.id)
            return updated, welcome_back

        # ==================== ONE-TIME FREE GATE (resume_creation only) ====================
        # Non-pro candidates get one free AIVI bot resume; after that they must upgrade.
        if session_type == "resume_creation":
            is_pro = getattr(candidate, "is_pro", False)
            if not is_pro:
                aivi_bot_count = await self._candidate_repo.count_completed_aivi_bot_resumes(
                    candidate_id
                )
                if aivi_bot_count >= 1:
                    raise ForbiddenError(
                        message="Upgrade to premium to create multiple resumes with AIVI bot.",
                        error_code="UPGRADE_REQUIRED",
                        context={"candidate_id": str(candidate_id)},
                    )

        # ==================== CREATE NEW SESSION ====================
        # Build initial context
        initial_context = {
            "step": ChatStep.CHOOSE_METHOD,
            "method": None,
            "role_id": str(candidate.preferred_job_role_id) if candidate.preferred_job_role_id else None,
            "collected_data": {},
            "answered_keys": [],
            "resume_id": None,
        }

        # Auto-generate title
        title = f"Resume Builder - {candidate.name}"

        session = await self._chat_repo.create_session(
            candidate_id=candidate_id,
            session_type=session_type,
            title=title,
            context_data=initial_context,
        )

        # Store welcome messages
        stored_msgs = await self._chat_repo.add_messages_batch(
            session.id, WELCOME_MESSAGES
        )

        # Re-fetch session with messages
        session = await self._chat_repo.get_session_by_id(session.id)

        logger.info(
            f"Created new chat session: {session.id}",
            extra={"session_id": str(session.id), "candidate_id": str(candidate_id)},
        )

        return session, WELCOME_MESSAGES

    async def send_message(
        self,
        session_id: UUID,
        content: str,
        message_type: str = "text",
        message_data: Optional[dict] = None,
    ) -> CandidateSendMessageResponse:
        """
        Process a user message and generate bot response(s).

        Uses dictionary dispatch to route to the correct step handler.

        Args:
            session_id: Chat session UUID
            content: User message content
            message_type: Type of message (text, button_click, file_upload)
            message_data: Additional data (selected option, file URL, etc.)

        Returns:
            CandidateSendMessageResponse with user message, bot messages, and session
        """
        # Fetch session (no messages – we only need context_data/current_step for processing)
        session = await self._chat_repo.get_session_by_id(session_id, include_messages=False)
        if not session:
            raise NotFoundError(
                message="Chat session not found",
                error_code="SESSION_NOT_FOUND",
            )

        if session.session_status != CandidateSessionStatus.ACTIVE:
            raise ValidationError(
                message="This chat session is no longer active.",
                error_code="SESSION_NOT_ACTIVE",
            )

        # Store user message
        user_msg = await self._chat_repo.add_message(
            session_id=session_id,
            role=CandidateMessageRole.USER,
            content=content,
            message_type=message_type,
            message_data=message_data or {},
        )

        # ==================== DICTIONARY DISPATCH ====================
        current_step = session.current_step
        handler = self._step_handlers.get(current_step)

        if not handler:
            logger.error(f"Unknown step: {current_step}", extra={"session_id": str(session_id)})
            bot_messages = [{
                "role": CandidateMessageRole.BOT,
                "content": "I'm sorry, something went wrong. Let me start over.",
                "message_type": CandidateMessageType.ERROR,
                "message_data": {"error": f"Unknown step: {current_step}"},
            }]
        else:
            bot_messages = await handler(session, content, message_data or {})

        # Store bot messages
        stored_bot_msgs = []
        if bot_messages:
            stored_bot_msgs = await self._chat_repo.add_messages_batch(
                session_id, bot_messages
            )

        # Re-fetch session for response (no messages – response schema does not include message list)
        updated_session = await self._chat_repo.get_session_by_id(session_id, include_messages=False)

        return CandidateSendMessageResponse(
            user_message=CandidateChatMessageResponse.model_validate(user_msg),
            bot_messages=[
                CandidateChatMessageResponse.model_validate(m) for m in stored_bot_msgs
            ],
            session=CandidateChatSessionResponse.model_validate(updated_session),
        )

    # ==================== STEP HANDLERS (Dictionary Dispatch Targets) ====================

    async def _handle_welcome_response(
        self,
        session: CandidateChatSession,
        content: str,
        data: dict,
    ) -> List[dict]:
        """Handle any message when in welcome state - redirect to choose_method."""
        # Update step
        ctx = self._copy_context(session)
        ctx["step"] = ChatStep.CHOOSE_METHOD
        await self._chat_repo.update_session(session.id, context_data=ctx)

        return WELCOME_MESSAGES[1:]  # Re-send the method selection buttons

    async def _handle_method_selection(
        self,
        session: CandidateChatSession,
        content: str,
        data: dict,
    ) -> List[dict]:
        """
        Handle method selection: "Upload PDF" or "Create with Bot".

        Uses button_id from message_data for reliable routing,
        falls back to content text matching.
        """
        # Determine selection via button_id (reliable) or content (fallback)
        button_id = data.get("button_id", "").lower()
        content_lower = content.strip().lower()

        # ==================== METHOD DISPATCH ====================
        method_dispatch = {
            "upload_pdf": "pdf_upload",
            "upload": "pdf_upload",
            "pdf": "pdf_upload",
            "create_with_bot": "aivi_bot",
            "create": "aivi_bot",
            "bot": "aivi_bot",
            "aivi": "aivi_bot",
        }

        method = method_dispatch.get(button_id)
        if not method:
            # Fallback: match against content text
            for key, val in method_dispatch.items():
                if key in content_lower:
                    method = val
                    break

        if not method:
            # User typed something unrecognized - ask again
            return [{
                "role": CandidateMessageRole.BOT,
                "content": "I didn't quite catch that. Please select one of the options below:",
                "message_type": CandidateMessageType.BUTTONS,
                "message_data": {
                    "buttons": [
                        {"id": "upload_pdf", "label": "📄 Upload Resume PDF"},
                        {"id": "create_with_bot", "label": "🤖 Create with AIVI Bot"},
                    ],
                },
            }]

        # ==================== ROUTE TO SELECTED METHOD ====================
        ctx = self._copy_context(session)
        ctx["method"] = method

        if method == "pdf_upload":
            ctx["step"] = ChatStep.UPLOAD_RESUME
            await self._chat_repo.update_session(session.id, context_data=ctx)

            return [{
                "role": CandidateMessageRole.BOT,
                "content": "Great! Please upload your resume PDF (max 2MB). I'll extract the information and ask for any missing details.",
                "message_type": CandidateMessageType.INPUT_FILE,
                "message_data": {
                    "question_key": "resume_pdf",
                    "accept": ".pdf",
                    "max_size_mb": 2,
                },
            }]

        else:  # aivi_bot — enforce one-time-free gate (same as create_session)
            candidate = await self._candidate_repo.get_by_id(session.candidate_id)
            if candidate:
                is_pro = getattr(candidate, "is_pro", False)
                if not is_pro:
                    aivi_bot_count = await self._candidate_repo.count_completed_aivi_bot_resumes(
                        session.candidate_id
                    )
                    if aivi_bot_count >= 1:
                        raise ForbiddenError(
                            message="To create another resume with AIVI bot, upgrade to Pro.",
                            error_code="UPGRADE_REQUIRED",
                            context={"candidate_id": str(session.candidate_id)},
                        )

            ctx["step"] = ChatStep.ASKING_QUESTIONS
            await self._chat_repo.update_session(session.id, context_data=ctx)

            # Load role info and start asking questions
            return await self._start_question_flow(session, ctx)

    async def _handle_resume_upload(
        self,
        session: CandidateChatSession,
        content: str,
        data: dict,
    ) -> List[dict]:
        """
        Handle resume PDF upload.

        Expects file_url in message_data. Triggers the full extraction pipeline:
        PDF → Text → LLM → Normalize → Detect Missing → Ask or Preview.
        """
        file_url = data.get("file_url", "").strip()

        if not file_url:
            return [{
                "role": CandidateMessageRole.BOT,
                "content": "I didn't receive a file. Please upload your resume PDF.",
                "message_type": CandidateMessageType.INPUT_FILE,
                "message_data": {
                    "question_key": "resume_pdf",
                    "accept": ".pdf",
                    "max_size_mb": 2,
                },
            }]

        # Store file URL in context
        ctx = self._copy_context(session)
        ctx["uploaded_pdf_url"] = file_url
        ctx["step"] = ChatStep.EXTRACTION_PROCESSING
        await self._chat_repo.update_session(session.id, context_data=ctx)

        # Show processing message first
        processing_msgs = [{
            "role": CandidateMessageRole.BOT,
            "content": "📄 Resume received! I'm analyzing it now...",
            "message_type": CandidateMessageType.LOADING,
            "message_data": {"status": "extracting"},
        }]

        # ==================== RUN EXTRACTION PIPELINE ====================
        # Get role info for context-aware extraction
        role_id = ctx.get("role_id")
        role_name = ctx.get("role_name")
        job_type = ctx.get("job_type")

        # Fetch question templates for missing field detection
        templates = []
        if role_id:
            templates = await self._job_master_repo.get_templates_by_role(UUID(role_id))

        # Run extraction
        extraction_result = await self._resume_extractor.extract_from_pdf_url(
            pdf_url=file_url,
            role_name=role_name,
            job_type=job_type,
            question_templates=templates,
        )

        if not extraction_result.success:
            # Extraction failed — offer retry or manual creation
            ctx["step"] = ChatStep.CHOOSE_METHOD
            await self._chat_repo.update_session(session.id, context_data=ctx)

            processing_msgs.append({
                "role": CandidateMessageRole.BOT,
                "content": f"⚠️ I couldn't extract information from your resume: {extraction_result.error_message}",
                "message_type": CandidateMessageType.TEXT,
                "message_data": {},
            })
            processing_msgs.append({
                "role": CandidateMessageRole.BOT,
                "content": "Would you like to try again or create your resume manually with me?",
                "message_type": CandidateMessageType.BUTTONS,
                "message_data": {
                    "buttons": [
                        {"id": "upload_pdf", "label": "📄 Upload Again"},
                        {"id": "create_with_bot", "label": "🤖 Create with AIVI Bot"},
                    ],
                },
            })
            return processing_msgs

        # ==================== EXTRACTION SUCCEEDED ====================
        extracted_data = extraction_result.extracted_data or {}
        missing_keys = extraction_result.missing_keys
        confidence = extraction_result.extraction_confidence

        # Store extracted data in context
        ctx["collected_data"] = extracted_data
        ctx["answered_keys"] = extraction_result.extracted_keys
        ctx["extraction_confidence"] = confidence
        ctx["method"] = "pdf_upload"

        # Load role info if not already set
        if not role_name and role_id:
            role = await self._job_master_repo.get_role_by_id(UUID(role_id))
            if role:
                ctx["role_name"] = role.name
                ctx["role_slug"] = role.slug
                ctx["job_type"] = role.job_type

        processing_msgs.append({
            "role": CandidateMessageRole.BOT,
            "content": f"✅ I've extracted {len(extraction_result.extracted_keys)} fields from your resume (confidence: {confidence:.0%}).",
            "message_type": CandidateMessageType.PROGRESS,
            "message_data": {
                "extracted_count": len(extraction_result.extracted_keys),
                "missing_count": len(missing_keys),
                "confidence": confidence,
            },
        })

        if missing_keys:
            # There are missing required fields — ask for them
            ctx["step"] = ChatStep.MISSING_FIELDS
            ctx["missing_keys_queue"] = missing_keys

            # Get the first missing question
            engine = QuestionEngine(templates, extracted_data)
            next_template = engine.get_next_question()

            if next_template:
                ctx["current_question_key"] = next_template.question_key
                await self._chat_repo.update_session(session.id, context_data=ctx)

                processing_msgs.append({
                    "role": CandidateMessageRole.BOT,
                    "content": f"I still need {len(missing_keys)} more detail(s). Let me ask you:",
                    "message_type": CandidateMessageType.TEXT,
                    "message_data": {},
                })

                question_msg = engine.build_question_message(next_template)
                processing_msgs.append(question_msg)
            else:
                # Engine says nothing to ask — go to preview
                ctx["step"] = ChatStep.RESUME_PREVIEW
                await self._chat_repo.update_session(session.id, context_data=ctx)
                processing_msgs.extend(build_preview_messages(ctx))
        else:
            # All fields extracted — go to preview
            ctx["step"] = ChatStep.RESUME_PREVIEW
            await self._chat_repo.update_session(session.id, context_data=ctx)
            processing_msgs.extend(build_preview_messages(ctx))

        return processing_msgs

    async def _handle_extraction_result(
        self,
        session: CandidateChatSession,
        content: str,
        data: dict,
    ) -> List[dict]:
        """
        Handle messages during extraction processing step.

        This step is transitional — normally extraction completes within
        the _handle_resume_upload call. But if the user sends a message
        while still in this state, we re-trigger extraction or inform.
        """
        ctx = self._copy_context(session)
        pdf_url = ctx.get("uploaded_pdf_url")

        if not pdf_url:
            ctx["step"] = ChatStep.UPLOAD_RESUME
            await self._chat_repo.update_session(session.id, context_data=ctx)
            return [{
                "role": CandidateMessageRole.BOT,
                "content": "It seems the upload didn't complete. Please upload your resume PDF again.",
                "message_type": CandidateMessageType.INPUT_FILE,
                "message_data": {
                    "question_key": "resume_pdf",
                    "accept": ".pdf",
                    "max_size_mb": 2,
                },
            }]

        # Re-trigger extraction (idempotent — will re-extract)
        return await self._handle_resume_upload(session, content, {"file_url": pdf_url})

    async def _handle_missing_field_answer(
        self,
        session: CandidateChatSession,
        content: str,
        data: dict,
    ) -> List[dict]:
        """
        Handle answers for missing fields after PDF extraction.

        Same logic as asking_questions but for fields not found in the PDF.
        """
        return await self._handle_question_answer(session, content, data)

    async def _handle_question_answer(
        self,
        session: CandidateChatSession,
        content: str,
        data: dict,
    ) -> List[dict]:
        """
        Handle a user's answer to a question during the AIVI bot flow.

        Flow:
        0. If awaiting_edit_field_name: treat content as field name → ask that question.
        1. Determine which question is being answered (from context or data)
        2. Validate the answer via QuestionEngine
        3. If invalid → re-ask with error message
        4. If valid → save to collected_data, ask next question
        5. If all questions done → move to RESUME_PREVIEW
        """
        ctx = self._copy_context(session)
        collected_data = ctx.get("collected_data", {})

        # ==================== EDIT RESUME: user just typed which field to change ====================
        if ctx.get("awaiting_edit_field_name") and not data.get("question_key"):
            field_name_raw = (content or "").strip()
            if not field_name_raw:
                return [{
                    "role": CandidateMessageRole.BOT,
                    "content": "Please type the field you want to change (e.g. name, skills, salary).",
                    "message_type": CandidateMessageType.TEXT,
                    "message_data": {},
                }]
            field_name = normalize_for_match(field_name_raw)
            field_name_underscore = field_name.replace(" ", "_")
            question_key = (
                EDIT_FIELD_ALIASES.get(field_name)
                or EDIT_FIELD_ALIASES.get(field_name_underscore)
                or (field_name_underscore if field_name else None)
            )
            role_id = ctx.get("role_id")
            if not role_id:
                ctx["awaiting_edit_field_name"] = False
                await self._chat_repo.update_session(session.id, context_data=ctx)
                return [{
                    "role": CandidateMessageRole.BOT,
                    "content": "Something went wrong — your role preference is missing. Please update your profile and try again.",
                    "message_type": CandidateMessageType.ERROR,
                    "message_data": {},
                }]
            templates = await self._job_master_repo.get_templates_by_role(UUID(role_id))
            template_by_key = {t.question_key: t for t in templates}
            if question_key and question_key in template_by_key:
                ctx["awaiting_edit_field_name"] = False
                ctx["current_question_key"] = question_key
                await self._chat_repo.update_session(session.id, context_data=ctx)
                engine = QuestionEngine(templates, collected_data)
                template = template_by_key[question_key]
                return [engine.build_question_message(template)]
            # Not found: suggest some keys from this role
            suggested = ", ".join(sorted(template_by_key.keys())[:10])
            return [{
                "role": CandidateMessageRole.BOT,
                "content": f"I didn't recognize that field. Try one of: {suggested}",
                "message_type": CandidateMessageType.TEXT,
                "message_data": {},
            }]

        # Get the question_key being answered
        question_key = data.get("question_key")

        if not question_key:
            # Determine from context: which question was the bot last asking?
            question_key = ctx.get("current_question_key")

        if not question_key:
            # Shouldn't happen, but recover gracefully
            logger.warning(f"No question_key found for session {session.id}")
            return await self._build_next_question_messages(session)

        # Handle "custom salary" text when user clicked Custom for salary_expectation and we asked for input
        if ctx.get("awaiting_custom_salary_text") and question_key == "salary_expectation":
            custom_salary = (content or "").strip()
            if not custom_salary:
                return [{
                    "role": CandidateMessageRole.BOT,
                    "content": "Please enter your expected salary (e.g. 50000 or 50k-60k per month).",
                    "message_type": CandidateMessageType.TEXT,
                    "message_data": {},
                }, {
                    "role": CandidateMessageRole.BOT,
                    "content": "Type your expected salary below:",
                    "message_type": CandidateMessageType.INPUT_TEXT,
                    "message_data": {"question_key": "salary_expectation"},
                }]
            collected_data["salary_expectation"] = custom_salary
            ctx["awaiting_custom_salary_text"] = False
            ctx["collected_data"] = collected_data
            answered_keys = ctx.get("answered_keys", [])
            if "salary_expectation" not in answered_keys:
                answered_keys = list(answered_keys) + ["salary_expectation"]
            ctx["answered_keys"] = answered_keys
            await self._chat_repo.update_session(session.id, context_data=ctx)
            engine = QuestionEngine(templates, collected_data)
            next_template = engine.get_next_question()
            if next_template is None:
                if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "general":
                    return await self._transition_fallback_after_general(session, ctx)
                # role_based / type_specific same as below
                if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "role_based":
                    return await self._transition_fallback_after_general(session, ctx)
                if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "type_specific":
                    polished = await build_resume_from_chat_llm(
                        collected_data,
                        job_type=ctx.get("fallback_job_type", "blue_collar"),
                        role_name=ctx.get("role_name", "General"),
                    )
                    ctx["collected_data"] = polished
                    await self._chat_repo.update_session(session.id, context_data=ctx)
                ctx["step"] = ChatStep.RESUME_PREVIEW
                ctx["current_question_key"] = None
                await self._chat_repo.update_session(session.id, context_data=ctx)
                return [
                    {"role": CandidateMessageRole.BOT, "content": "✅ Great! I've collected all the information.", "message_type": CandidateMessageType.TEXT, "message_data": {}},
                    {"role": CandidateMessageRole.BOT, "content": "Here's a preview of your resume. Would you like to confirm and save it?", "message_type": CandidateMessageType.RESUME_PREVIEW, "message_data": {"resume_data": collected_data, "role_name": ctx.get("role_name", ""), "job_type": ctx.get("job_type", "")}},
                    {"role": CandidateMessageRole.BOT, "content": "Would you like to save this resume?", "message_type": CandidateMessageType.BUTTONS, "message_data": {"buttons": [{"id": "confirm_resume", "label": "✅ Yes, save my resume"}, {"id": "edit_resume", "label": "✏️ No, let me make changes"}]}},
                ]
            ctx["current_question_key"] = next_template.question_key
            await self._chat_repo.update_session(session.id, context_data=ctx)
            if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "general" and next_template.question_key in ("job_category_id", "job_role_id"):
                question_msg = self._build_fallback_category_role_question_message(next_template, ctx, engine)
            else:
                question_msg = engine.build_question_message(next_template)
            return [{"role": CandidateMessageRole.BOT, "content": "Got it! ✓", "message_type": CandidateMessageType.TEXT, "message_data": {}}, question_msg]

        # Handle "custom role" text when user clicked Custom for job_role_id and we asked for input
        if ctx.get("awaiting_custom_role_text") and question_key == "job_role_id":
            custom_text = (content or "").strip()
            if not custom_text:
                return [{
                    "role": CandidateMessageRole.BOT,
                    "content": "Please enter your custom role (e.g. Data Scientist, Product Manager).",
                    "message_type": CandidateMessageType.TEXT,
                    "message_data": {},
                }, {
                    "role": CandidateMessageRole.BOT,
                    "content": "Type your custom role below:",
                    "message_type": CandidateMessageType.INPUT_TEXT,
                    "message_data": {"question_key": "job_role_id"},
                }]
            collected_data["job_role_id"] = "custom"
            collected_data["job_role_custom_text"] = custom_text
            collected_data["job_role_name"] = custom_text
            ctx["awaiting_custom_role_text"] = False
            ctx["collected_data"] = collected_data
            answered_keys = ctx.get("answered_keys", [])
            if "job_role_id" not in answered_keys:
                answered_keys = list(answered_keys) + ["job_role_id"]
            ctx["answered_keys"] = answered_keys
            await self._chat_repo.update_session(session.id, context_data=ctx)
            engine = QuestionEngine(templates, collected_data)
            next_template = engine.get_next_question()
            if next_template is None:
                # We're in general phase; custom role means no role_based phase, go straight to type/preview.
                return await self._transition_fallback_after_general(session, ctx)
            ctx["current_question_key"] = next_template.question_key
            await self._chat_repo.update_session(session.id, context_data=ctx)
            if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "general" and next_template.question_key in ("job_category_id", "job_role_id"):
                question_msg = self._build_fallback_category_role_question_message(next_template, ctx, engine)
            else:
                question_msg = engine.build_question_message(next_template)
            return [question_msg]

        # Handle "custom education" text when user clicked Custom for education
        if ctx.get("awaiting_custom_education_text") and question_key == "education":
            custom_text = (content or "").strip()
            if not custom_text:
                return [{
                    "role": CandidateMessageRole.BOT,
                    "content": "Please enter your highest education (e.g. B.Tech, Diploma, MBA).",
                    "message_type": CandidateMessageType.TEXT,
                    "message_data": {},
                }, {
                    "role": CandidateMessageRole.BOT,
                    "content": "Type your education below:",
                    "message_type": CandidateMessageType.INPUT_TEXT,
                    "message_data": {"question_key": "education"},
                }]
            collected_data["education"] = custom_text
            ctx["awaiting_custom_education_text"] = False
            ctx["collected_data"] = collected_data
            answered_keys = ctx.get("answered_keys", [])
            if "education" not in answered_keys:
                answered_keys = list(answered_keys) + ["education"]
            ctx["answered_keys"] = answered_keys
            await self._chat_repo.update_session(session.id, context_data=ctx)
            engine = QuestionEngine(templates, collected_data)
            next_template = engine.get_next_question()
            if next_template is None:
                if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "general":
                    return await self._transition_fallback_after_general(session, ctx)
                if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "role_based":
                    return await self._transition_fallback_after_general(session, ctx)
                if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "type_specific":
                    polished = await build_resume_from_chat_llm(
                        collected_data,
                        job_type=ctx.get("fallback_job_type", "blue_collar"),
                        role_name=ctx.get("role_name", "General"),
                    )
                    ctx["collected_data"] = polished
                    await self._chat_repo.update_session(session.id, context_data=ctx)
                ctx["step"] = ChatStep.RESUME_PREVIEW
                ctx["current_question_key"] = None
                await self._chat_repo.update_session(session.id, context_data=ctx)
                return [
                    {"role": CandidateMessageRole.BOT, "content": "✅ Great! I've collected all the information.", "message_type": CandidateMessageType.TEXT, "message_data": {}},
                    {"role": CandidateMessageRole.BOT, "content": "Here's a preview of your resume. Would you like to confirm and save it?", "message_type": CandidateMessageType.RESUME_PREVIEW, "message_data": {"resume_data": collected_data, "role_name": ctx.get("role_name", ""), "job_type": ctx.get("job_type", "")}},
                    {"role": CandidateMessageRole.BOT, "content": "Would you like to save this resume?", "message_type": CandidateMessageType.BUTTONS, "message_data": {"buttons": [{"id": "confirm_resume", "label": "✅ Yes, save my resume"}, {"id": "edit_resume", "label": "✏️ No, let me make changes"}]}},
                ]
            ctx["current_question_key"] = next_template.question_key
            await self._chat_repo.update_session(session.id, context_data=ctx)
            if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "general" and next_template.question_key in ("job_category_id", "job_role_id"):
                question_msg = self._build_fallback_category_role_question_message(next_template, ctx, engine)
            else:
                question_msg = engine.build_question_message(next_template)
            return [{"role": CandidateMessageRole.BOT, "content": "Got it! ✓", "message_type": CandidateMessageType.TEXT, "message_data": {}}, question_msg]

        # Handle "custom experience" text when user clicked Custom for experience_years
        if ctx.get("awaiting_custom_experience_text") and question_key == "experience_years":
            custom_text = (content or "").strip()
            if not custom_text:
                return [{
                    "role": CandidateMessageRole.BOT,
                    "content": "Please enter your work experience (e.g. 6 years, 10+ years).",
                    "message_type": CandidateMessageType.TEXT,
                    "message_data": {},
                }, {
                    "role": CandidateMessageRole.BOT,
                    "content": "Type your experience below:",
                    "message_type": CandidateMessageType.INPUT_TEXT,
                    "message_data": {"question_key": "experience_years"},
                }]
            collected_data["experience_years"] = custom_text
            ctx["awaiting_custom_experience_text"] = False
            ctx["collected_data"] = collected_data
            answered_keys = ctx.get("answered_keys", [])
            if "experience_years" not in answered_keys:
                answered_keys = list(answered_keys) + ["experience_years"]
            ctx["answered_keys"] = answered_keys
            await self._chat_repo.update_session(session.id, context_data=ctx)
            engine = QuestionEngine(templates, collected_data)
            next_template = engine.get_next_question()
            if next_template is None:
                if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "general":
                    return await self._transition_fallback_after_general(session, ctx)
                if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "role_based":
                    return await self._transition_fallback_after_general(session, ctx)
                if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "type_specific":
                    polished = await build_resume_from_chat_llm(
                        collected_data,
                        job_type=ctx.get("fallback_job_type", "blue_collar"),
                        role_name=ctx.get("role_name", "General"),
                    )
                    ctx["collected_data"] = polished
                    await self._chat_repo.update_session(session.id, context_data=ctx)
                ctx["step"] = ChatStep.RESUME_PREVIEW
                ctx["current_question_key"] = None
                await self._chat_repo.update_session(session.id, context_data=ctx)
                return [
                    {"role": CandidateMessageRole.BOT, "content": "✅ Great! I've collected all the information.", "message_type": CandidateMessageType.TEXT, "message_data": {}},
                    {"role": CandidateMessageRole.BOT, "content": "Here's a preview of your resume. Would you like to confirm and save it?", "message_type": CandidateMessageType.RESUME_PREVIEW, "message_data": {"resume_data": collected_data, "role_name": ctx.get("role_name", ""), "job_type": ctx.get("job_type", "")}},
                    {"role": CandidateMessageRole.BOT, "content": "Would you like to save this resume?", "message_type": CandidateMessageType.BUTTONS, "message_data": {"buttons": [{"id": "confirm_resume", "label": "✅ Yes, save my resume"}, {"id": "edit_resume", "label": "✏️ No, let me make changes"}]}},
                ]
            ctx["current_question_key"] = next_template.question_key
            await self._chat_repo.update_session(session.id, context_data=ctx)
            if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "general" and next_template.question_key in ("job_category_id", "job_role_id"):
                question_msg = self._build_fallback_category_role_question_message(next_template, ctx, engine)
            else:
                question_msg = engine.build_question_message(next_template)
            return [{"role": CandidateMessageRole.BOT, "content": "Got it! ✓", "message_type": CandidateMessageType.TEXT, "message_data": {}}, question_msg]

        # Get question templates (role-based or fallback)
        role_id = ctx.get("role_id")
        if ctx.get("fallback_mode"):
            phase = ctx.get("fallback_phase", "general")
            if phase == "general":
                # Ensure categories/roles loaded once (e.g. resumed session from before this feature)
                if not ctx.get("_job_categories"):
                    categories = await self._job_master_repo.get_all_categories(
                        active_only=True, include_roles=True
                    )
                    ctx["_job_categories"] = self._serialize_categories_for_context(categories)
                templates = await self._job_master_repo.get_fallback_questions(
                    job_type=None,
                    experience_level=None,
                )
            elif phase == "role_based":
                rid = ctx.get("role_id") or collected_data.get("job_role_id")
                if not rid:
                    return await self._transition_fallback_after_general(session, ctx)
                templates = await self._job_master_repo.get_templates_by_role(UUID(str(rid)))
            else:
                templates = await self._job_master_repo.get_fallback_questions(
                    job_type=ctx.get("fallback_job_type"),
                    experience_level=ctx.get("fallback_experience_level") or "experienced",
                )
        elif role_id:
            templates = await self._job_master_repo.get_templates_by_role(UUID(role_id))
        else:
            return [{
                "role": CandidateMessageRole.BOT,
                "content": "Something went wrong — your role preference is missing. Please update your profile and try again.",
                "message_type": CandidateMessageType.ERROR,
                "message_data": {},
            }]

        engine = QuestionEngine(templates, collected_data)

        # Parse the user's answer value
        answer_value = data.get("value", content)

        # Validate answer
        is_valid, parsed_value, error_msg = engine.process_answer(question_key, answer_value)

        if not is_valid:
            # Re-ask the same question with error
            template = engine.get_template_by_key(question_key)
            if template:
                msg = engine.build_question_message(template)
                error_prefix = {
                    "role": CandidateMessageRole.BOT,
                    "content": f"⚠️ {error_msg}",
                    "message_type": CandidateMessageType.TEXT,
                    "message_data": {},
                }
                return [error_prefix, msg]
            return [{
                "role": CandidateMessageRole.BOT,
                "content": f"⚠️ {error_msg} Please try again.",
                "message_type": CandidateMessageType.TEXT,
                "message_data": {},
            }]

        # ==================== SAVE ANSWER (Auto-save) ====================
        if parsed_value is not None:
            collected_data[question_key] = parsed_value
            # Enrich with names for category/role (for resume display and profile update)
            if question_key == "job_category_id" and parsed_value:
                for c in ctx.get("_job_categories") or []:
                    if str(c.get("id")) == str(parsed_value):
                        collected_data["job_category_name"] = c.get("name", "")
                        break
            if question_key == "job_role_id" and parsed_value:
                if parsed_value == "custom":
                    # Don't mark as answered yet; ask for custom role text in next message.
                    collected_data["job_role_id"] = "custom"
                    ctx["collected_data"] = collected_data
                    ctx["awaiting_custom_role_text"] = True
                    await self._chat_repo.update_session(session.id, context_data=ctx)
                    return [{
                        "role": CandidateMessageRole.BOT,
                        "content": "Type your custom role below (e.g. Data Scientist, Product Manager):",
                        "message_type": CandidateMessageType.INPUT_TEXT,
                        "message_data": {"question_key": "job_role_id"},
                    }]
                else:
                    cat_id = collected_data.get("job_category_id")
                    for c in ctx.get("_job_categories") or []:
                        if str(c.get("id")) == str(cat_id):
                            for r in c.get("roles", []):
                                if str(r.get("id")) == str(parsed_value):
                                    collected_data["job_role_name"] = r.get("name", "")
                                    break
                            break
            if question_key == "salary_expectation" and parsed_value == "custom":
                # Don't mark as answered yet; ask for custom salary in next message.
                collected_data["salary_expectation"] = "custom"
                ctx["collected_data"] = collected_data
                ctx["awaiting_custom_salary_text"] = True
                await self._chat_repo.update_session(session.id, context_data=ctx)
                return [{
                    "role": CandidateMessageRole.BOT,
                    "content": "Type your expected salary below (e.g. 50000 or 50k-60k per month):",
                    "message_type": CandidateMessageType.INPUT_TEXT,
                    "message_data": {"question_key": "salary_expectation"},
                }]
            if question_key == "education" and parsed_value == "custom":
                collected_data["education"] = "custom"
                ctx["collected_data"] = collected_data
                ctx["awaiting_custom_education_text"] = True
                await self._chat_repo.update_session(session.id, context_data=ctx)
                return [{
                    "role": CandidateMessageRole.BOT,
                    "content": "Type your highest education below (e.g. B.Tech, Diploma, MBA):",
                    "message_type": CandidateMessageType.INPUT_TEXT,
                    "message_data": {"question_key": "education"},
                }]
            if question_key == "experience_years" and parsed_value == "custom":
                collected_data["experience_years"] = "custom"
                ctx["collected_data"] = collected_data
                ctx["awaiting_custom_experience_text"] = True
                await self._chat_repo.update_session(session.id, context_data=ctx)
                return [{
                    "role": CandidateMessageRole.BOT,
                    "content": "Type your work experience below (e.g. 6 years, 10+ years):",
                    "message_type": CandidateMessageType.INPUT_TEXT,
                    "message_data": {"question_key": "experience_years"},
                }]

        answered_keys = ctx.get("answered_keys", [])
        if question_key not in answered_keys:
            answered_keys.append(question_key)

        ctx["collected_data"] = collected_data
        ctx["answered_keys"] = answered_keys

        # Rebuild engine with updated data to get next question
        engine = QuestionEngine(templates, collected_data)

        # Get next question
        next_template = engine.get_next_question()

        if next_template is None:
            # ==================== ALL QUESTIONS ANSWERED (or phase done) ====================
            if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "general":
                if _has_known_fallback_role(collected_data):
                    ctx["role_id"] = str(collected_data["job_role_id"])
                    ctx["fallback_phase"] = "role_based"
                    ctx["current_question_key"] = None
                    await self._chat_repo.update_session(session.id, context_data=ctx)
                    role_templates = await self._job_master_repo.get_templates_by_role(UUID(ctx["role_id"]))
                    if not role_templates:
                        return await self._transition_fallback_after_general(session, ctx)
                    role_engine = QuestionEngine(role_templates, collected_data)
                    first_role_q = role_engine.get_next_question()
                    if not first_role_q:
                        return await self._transition_fallback_after_general(session, ctx)
                    ctx["current_question_key"] = first_role_q.question_key
                    await self._chat_repo.update_session(session.id, context_data=ctx)
                    intro = {
                        "role": CandidateMessageRole.BOT,
                        "content": f"A few role-specific questions for {collected_data.get('job_role_name', 'your role')}:",
                        "message_type": CandidateMessageType.TEXT,
                        "message_data": {},
                    }
                    return [intro, role_engine.build_question_message(first_role_q)]
                return await self._transition_fallback_after_general(session, ctx)
            if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "role_based":
                return await self._transition_fallback_after_general(session, ctx)
            if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "type_specific":
                polished = await build_resume_from_chat_llm(
                    collected_data,
                    job_type=ctx.get("fallback_job_type", "blue_collar"),
                    role_name=ctx.get("role_name", "General"),
                )
                ctx["collected_data"] = polished
                await self._chat_repo.update_session(session.id, context_data=ctx)

            ctx["step"] = ChatStep.RESUME_PREVIEW
            ctx["current_question_key"] = None
            await self._chat_repo.update_session(session.id, context_data=ctx)

            return [
                {
                    "role": CandidateMessageRole.BOT,
                    "content": f"✅ Great! I've collected all the information ({engine.progress_percentage}% complete).",
                    "message_type": CandidateMessageType.PROGRESS,
                    "message_data": {"percentage": 100},
                },
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

        # ==================== ASK NEXT QUESTION ====================
        ctx["current_question_key"] = next_template.question_key
        await self._chat_repo.update_session(session.id, context_data=ctx)

        if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "general" and next_template.question_key in ("job_category_id", "job_role_id"):
            question_msg = self._build_fallback_category_role_question_message(next_template, ctx, engine)
        else:
            question_msg = engine.build_question_message(next_template)

        # Add an acknowledgment for the previous answer
        ack_messages = []
        if parsed_value is not None:
            ack_messages.append({
                "role": CandidateMessageRole.BOT,
                "content": f"Got it! ✓",
                "message_type": CandidateMessageType.TEXT,
                "message_data": {},
            })

        ack_messages.append(question_msg)
        return ack_messages

    async def _handle_resume_confirmation(
        self,
        session: CandidateChatSession,
        content: str,
        data: dict,
    ) -> List[dict]:
        """
        Handle resume confirmation or edit request.

        Confirmation triggers resume compilation (Step 2.2).
        Edit request goes back to asking questions.
        """
        button_id = data.get("button_id", "").lower()
        content_lower = content.strip().lower()

        # Determine user choice
        confirm_keywords = {"confirm_resume", "yes", "save", "confirm", "ok", "done"}
        edit_keywords = {"edit_resume", "no", "edit", "change", "modify"}

        is_confirm = button_id in confirm_keywords or any(k in content_lower for k in confirm_keywords)
        is_edit = button_id in edit_keywords or any(k in content_lower for k in edit_keywords)

        if is_edit:
            # Go back to asking questions; next user message is the field name they want to edit
            ctx = self._copy_context(session)
            ctx["step"] = ChatStep.ASKING_QUESTIONS
            ctx["awaiting_edit_field_name"] = True
            ctx["current_question_key"] = None
            await self._chat_repo.update_session(session.id, context_data=ctx)

            return [{
                "role": CandidateMessageRole.BOT,
                "content": "No problem! Which field would you like to change? You can type the field name (e.g., 'name', 'skills', 'salary').",
                "message_type": CandidateMessageType.TEXT,
                "message_data": {},
            }]

        if is_confirm:
            ctx = self._copy_context(session)
            collected_data = ctx.get("collected_data", {})
            role_name = (ctx.get("role_name") or "").strip()  # Avoid "Unknown" in PDF title when role not set
            job_type = ctx.get("job_type", "")
            method = ctx.get("method", "aivi_bot")

            # ==================== IDEMPOTENCY: session already has a resume ====================
            if session.resume_id:
                existing_resume = await self._candidate_repo.get_resume_by_id(session.resume_id)
                if existing_resume and existing_resume.resume_data:
                    summary = self._resume_builder.get_resume_summary(existing_resume.resume_data)
                    return [
                        {
                            "role": CandidateMessageRole.BOT,
                            "content": f"🎉 Your resume (v{existing_resume.version_number}) has already been saved.",
                            "message_type": CandidateMessageType.TEXT,
                            "message_data": {
                                "resume_id": str(existing_resume.id),
                                "version": existing_resume.version_number,
                            },
                        },
                        {
                            "role": CandidateMessageRole.BOT,
                            "content": "Here's a quick summary of your resume:",
                            "message_type": CandidateMessageType.RESUME_PREVIEW,
                            "message_data": {
                                "summary": summary,
                                "resume_id": str(existing_resume.id),
                            },
                        },
                        {
                            "role": CandidateMessageRole.BOT,
                            "content": "You can now view job recommendations on your dashboard. You can also update your resume anytime by starting a new chat.",
                            "message_type": CandidateMessageType.TEXT,
                            "message_data": {},
                        },
                    ]

            # Determine resume source and uploaded PDF URL (for download link)
            source = "pdf_upload" if method == "pdf_upload" else "aivi_bot"
            uploaded_pdf_url = ctx.get("uploaded_pdf_url") if source == "pdf_upload" else None

            try:
                # ==================== COMPILE & PERSIST RESUME ====================
                result = await self._resume_builder.compile_resume(
                    candidate_id=session.candidate_id,
                    collected_data=collected_data,
                    role_name=role_name,
                    job_type=job_type,
                    source=source,
                    chat_session_id=session.id,
                    pdf_url=uploaded_pdf_url,
                )

                resume_id = result["resume_id"]
                version = result["version"]

                # ==================== UPDATE CANDIDATE PROFILE (category/role from chat) ====================
                cat_id = collected_data.get("job_category_id")
                role_id_val = collected_data.get("job_role_id")
                update_data = {}
                if cat_id and str(cat_id).strip().lower() != "custom":
                    try:
                        update_data["preferred_job_category_id"] = UUID(str(cat_id))
                    except (ValueError, TypeError):
                        pass
                if role_id_val and str(role_id_val).strip().lower() != "custom":
                    try:
                        update_data["preferred_job_role_id"] = UUID(str(role_id_val))
                    except (ValueError, TypeError):
                        pass
                if update_data:
                    try:
                        candidate = await self._candidate_repo.get_by_id(session.candidate_id)
                        if candidate:
                            await self._candidate_repo.update(
                                session.candidate_id,
                                update_data,
                                candidate.version,
                            )
                    except Exception as profile_err:
                        logger.warning(
                            "Failed to update candidate profile from chat choices: %s",
                            profile_err,
                            extra={"candidate_id": str(session.candidate_id)},
                        )

                # Update session context with resume info
                ctx["step"] = ChatStep.COMPLETED
                ctx["resume_id"] = resume_id

                await self._chat_repo.update_session(
                    session.id,
                    context_data=ctx,
                    session_status=CandidateSessionStatus.COMPLETED,
                    resume_id=UUID(resume_id),
                )

                # Get summary for display
                summary = self._resume_builder.get_resume_summary(result["resume_data"])

                return [
                    {
                        "role": CandidateMessageRole.BOT,
                        "content": f"🎉 Your resume (v{version}) has been saved successfully!",
                        "message_type": CandidateMessageType.TEXT,
                        "message_data": {
                            "resume_id": resume_id,
                            "version": version,
                        },
                    },
                    {
                        "role": CandidateMessageRole.BOT,
                        "content": "Here's a quick summary of your resume:",
                        "message_type": CandidateMessageType.RESUME_PREVIEW,
                        "message_data": {
                            "summary": summary,
                            "resume_id": resume_id,
                        },
                    },
                    {
                        "role": CandidateMessageRole.BOT,
                        "content": "You can now view job recommendations on your dashboard. You can also update your resume anytime by starting a new chat.",
                        "message_type": CandidateMessageType.TEXT,
                        "message_data": {},
                    },
                ]

            except Exception as e:
                logger.error(
                    f"Resume compilation failed: {e}",
                    extra={"session_id": str(session.id), "error": str(e)},
                )
                return [
                    {
                        "role": CandidateMessageRole.BOT,
                        "content": "⚠️ Something went wrong while saving your resume. Please try again.",
                        "message_type": CandidateMessageType.ERROR,
                        "message_data": {"error": str(e)},
                    },
                    {
                        "role": CandidateMessageRole.BOT,
                        "content": "Would you like to try saving again?",
                        "message_type": CandidateMessageType.BUTTONS,
                        "message_data": {
                            "buttons": [
                                {"id": "confirm_resume", "label": "✅ Yes, try again"},
                                {"id": "edit_resume", "label": "✏️ Go back and edit"},
                            ],
                        },
                    },
                ]

        # Unrecognized input
        return [{
            "role": CandidateMessageRole.BOT,
            "content": "Please confirm whether you'd like to save this resume:",
            "message_type": CandidateMessageType.BUTTONS,
            "message_data": {
                "buttons": [
                    {"id": "confirm_resume", "label": "✅ Yes, save my resume"},
                    {"id": "edit_resume", "label": "✏️ No, let me make changes"},
                ],
            },
        }]

    async def _handle_completed_session(
        self,
        session: CandidateChatSession,
        content: str,
        data: dict,
    ) -> List[dict]:
        """Handle messages in a completed session — suggest starting new."""
        return [{
            "role": CandidateMessageRole.BOT,
            "content": "This resume session is complete! To create a new resume or make updates, please start a new chat session.",
            "message_type": CandidateMessageType.TEXT,
            "message_data": {},
        }]

    # ==================== INTERNAL HELPERS ====================

    async def _start_question_flow(
        self,
        session: CandidateChatSession,
        ctx: dict,
    ) -> List[dict]:
        """
        Initialize the question-asking flow.

        If role_id is set: load role templates and first question.
        If no role_id: start fallback flow (general questions → job type → type-specific).
        """
        role_id = ctx.get("role_id")

        if not role_id:
            return await self._start_fallback_question_flow(session, ctx)

        # Fetch role details
        role = await self._job_master_repo.get_role_by_id(UUID(role_id))
        if not role:
            return [{
                "role": CandidateMessageRole.BOT,
                "content": "The selected job role could not be found. Please update your profile and try again.",
                "message_type": CandidateMessageType.ERROR,
                "message_data": {},
            }]

        # Store role info in context
        ctx["role_slug"] = role.slug
        ctx["role_name"] = role.name
        ctx["job_type"] = role.job_type

        # Get question templates
        templates = await self._job_master_repo.get_templates_by_role(UUID(role_id))

        if not templates:
            # Role exists but has no question templates — fall back to universal questions
            return await self._start_fallback_question_flow(session, ctx)

        # Initialize question engine
        engine = QuestionEngine(templates, ctx.get("collected_data", {}))
        first_question = engine.get_next_question()

        if not first_question:
            ctx["step"] = ChatStep.RESUME_PREVIEW
            await self._chat_repo.update_session(session.id, context_data=ctx)
            return [{
                "role": CandidateMessageRole.BOT,
                "content": "All information is already available! Let me generate your resume.",
                "message_type": CandidateMessageType.TEXT,
                "message_data": {},
            }]

        # Store current question in context
        ctx["current_question_key"] = first_question.question_key
        await self._chat_repo.update_session(session.id, context_data=ctx)

        # Build intro + first question
        intro_msg = {
            "role": CandidateMessageRole.BOT,
            "content": f"Let's build your resume for the {role.name} role! I'll ask you a few questions. Let's start:",
            "message_type": CandidateMessageType.TEXT,
            "message_data": {},
        }

        question_msg = engine.build_question_message(first_question)

        return [intro_msg, question_msg]

    def _build_fallback_category_role_question_message(
        self,
        template: Any,
        ctx: dict,
        engine: QuestionEngine,
    ) -> dict:
        """
        Build bot message for job_category_id or job_role_id with buttons from context.
        Used only in fallback general phase; options come from ctx["_job_categories"] (no DB).
        """
        question_key = template.question_key
        collected = ctx.get("collected_data", {})
        categories = ctx.get("_job_categories") or []

        if question_key == "job_category_id":
            # No Custom: user must pick a category from DB (sufficient options available).
            buttons = [{"id": c["id"], "label": c["name"]} for c in categories]
        elif question_key == "job_role_id":
            cat_id = collected.get("job_category_id")
            if not cat_id or cat_id == "custom":
                buttons = [{"id": "custom", "label": "Custom"}]
            else:
                roles = []
                for c in categories:
                    if c.get("id") == cat_id:
                        roles = [{"id": r["id"], "label": r["name"]} for r in c.get("roles", [])]
                        break
                buttons = roles + [{"id": "custom", "label": "Custom"}]
        else:
            return engine.build_question_message(template)

        progress = {
            "current": engine.answered_count + 1,
            "total": engine.total_applicable_questions,
            "percentage": engine.progress_percentage,
        }
        return {
            "role": CandidateMessageRole.BOT,
            "content": template.question_text,
            "message_type": CandidateMessageType.BUTTONS,
            "message_data": {
                "question_key": question_key,
                "buttons": buttons,
                "progress": progress,
                "is_required": getattr(template, "is_required", True),
            },
        }

    def _infer_fallback_job_type_and_level(
        self, collected_data: dict, ctx: dict
    ) -> Tuple[str, Optional[str]]:
        """
        Infer fallback_job_type (white_collar, blue_collar, grey_collar) and
        experience_level (fresher, experienced) from education and experience_years.
        experience_level is only relevant for blue_collar; None for white/grey.
        """
        education = collected_data.get("education")
        if isinstance(education, str):
            education = education.strip().lower().replace(" ", "_")
        exp_raw = collected_data.get("experience_years")

        if education in EDUCATION_WHITE_COLLAR:
            return "white_collar", None
        if education in EDUCATION_BLUE_COLLAR:
            level = "fresher"
            if isinstance(exp_raw, str) and exp_raw.strip().lower() in EXPERIENCE_EXPERIENCED_IDS:
                level = "experienced"
            elif isinstance(exp_raw, (int, float)):
                level = "experienced" if exp_raw >= 2 else "fresher"
            return "blue_collar", level

        # custom or unknown: use role's job_type if they picked a known role
        role_id = collected_data.get("job_role_id")
        if role_id and role_id != "custom" and ctx.get("_job_categories"):
            for c in ctx["_job_categories"]:
                for r in c.get("roles", []):
                    if str(r.get("id")) == str(role_id):
                        role_job_type = (r.get("job_type") or "white_collar").lower()
                        if role_job_type == "white_collar":
                            return "white_collar", None
                        if role_job_type == "blue_collar":
                            level = "fresher"
                            if isinstance(exp_raw, str) and exp_raw.strip().lower() in EXPERIENCE_EXPERIENCED_IDS:
                                level = "experienced"
                            elif isinstance(exp_raw, (int, float)):
                                level = "experienced" if exp_raw >= 2 else "fresher"
                            return "blue_collar", level
                        return "grey_collar", None
        # default: grey_collar (vocational / other)
        return "grey_collar", None

    async def _transition_fallback_after_general(
        self, session: CandidateChatSession, ctx: dict
    ) -> List[dict]:
        """
        After all general questions: infer job type and experience level,
        then go to resume preview (white_collar) or ask type_specific questions (blue/grey).
        No choose_job_type step.
        """
        collected_data = ctx.get("collected_data", {})
        job_type, experience_level = self._infer_fallback_job_type_and_level(collected_data, ctx)
        # IMPORTANT: Apply the same "experienced" fallback used in the DB query (line 1549)
        # so that the answer handler loads the same template set.
        resolved_experience_level = experience_level or "experienced"
        ctx["fallback_job_type"] = job_type
        ctx["fallback_experience_level"] = resolved_experience_level
        ctx["job_type"] = job_type
        ctx["role_name"] = (
            collected_data.get("job_role_name")
            or collected_data.get("job_role_custom_text")
            or collected_data.get("job_category_name")
            or ctx.get("role_name")
            or job_type.replace("_", " ").title()
        )
        ctx["fallback_phase"] = "type_specific"

        if job_type == "white_collar":
            ctx["step"] = ChatStep.RESUME_PREVIEW
            ctx["current_question_key"] = None
            polished = await build_resume_from_chat_llm(
                collected_data,
                job_type=job_type,
                role_name=ctx["role_name"],
            )
            ctx["collected_data"] = polished
            await self._chat_repo.update_session(session.id, context_data=ctx)
            return [
                {
                    "role": CandidateMessageRole.BOT,
                    "content": "✅ I've got everything I need. Here's your resume preview.",
                    "message_type": CandidateMessageType.TEXT,
                    "message_data": {},
                },
                *build_preview_messages(ctx),
            ]

        type_templates = await self._job_master_repo.get_fallback_questions(
            job_type=job_type,
            experience_level=resolved_experience_level,
        )
        if not type_templates:
            ctx["step"] = ChatStep.RESUME_PREVIEW
            ctx["current_question_key"] = None
            polished = await build_resume_from_chat_llm(
                collected_data,
                job_type=job_type,
                role_name=ctx["role_name"],
            )
            ctx["collected_data"] = polished
            await self._chat_repo.update_session(session.id, context_data=ctx)
            return [
                {
                    "role": CandidateMessageRole.BOT,
                    "content": "✅ I've got everything I need. Here's your resume preview.",
                    "message_type": CandidateMessageType.TEXT,
                    "message_data": {},
                },
                *build_preview_messages(ctx),
            ]

        engine = QuestionEngine(type_templates, collected_data)
        next_template = engine.get_next_question()
        if not next_template:
            ctx["step"] = ChatStep.RESUME_PREVIEW
            ctx["current_question_key"] = None
            polished = await build_resume_from_chat_llm(
                collected_data,
                job_type=job_type,
                role_name=ctx["role_name"],
            )
            ctx["collected_data"] = polished
            await self._chat_repo.update_session(session.id, context_data=ctx)
            return [
                {"role": CandidateMessageRole.BOT, "content": "✅ All set! Here's your resume.", "message_type": CandidateMessageType.TEXT, "message_data": {}},
                *build_preview_messages(ctx),
            ]

        ctx["current_question_key"] = next_template.question_key
        await self._chat_repo.update_session(session.id, context_data=ctx)
        intro = {
            "role": CandidateMessageRole.BOT,
            "content": f"A few more questions for your profile ({job_type.replace('_', ' ')}):",
            "message_type": CandidateMessageType.TEXT,
            "message_data": {},
        }
        msg = engine.build_question_message(next_template)
        return [intro, msg]

    def _serialize_categories_for_context(
        self, categories: List[Any],
    ) -> List[dict]:
        """
        Build JSON-serializable list of categories with roles for session context.
        Called once at fallback start so we never hit DB for category/role options again.
        """
        out = []
        for c in categories:
            roles = []
            for r in getattr(c, "roles", []) or []:
                if getattr(r, "is_active", True):
                    roles.append({
                        "id": str(r.id),
                        "name": r.name,
                        "slug": getattr(r, "slug", ""),
                        "job_type": getattr(r, "job_type", "white_collar"),
                    })
            out.append({
                "id": str(c.id),
                "name": c.name,
                "slug": getattr(c, "slug", ""),
                "roles": roles,
            })
        return out

    async def _start_fallback_question_flow(
        self,
        session: CandidateChatSession,
        ctx: dict,
    ) -> List[dict]:
        """Start fallback flow: general questions first (no role in DB)."""
        ctx["fallback_mode"] = True
        ctx["fallback_phase"] = "general"
        ctx["role_name"] = ctx.get("role_name") or "General"
        ctx["job_type"] = ctx.get("job_type") or "blue_collar"

        # Load job categories + roles once and store in context (no DB calls during general phase)
        if not ctx.get("_job_categories"):
            categories = await self._job_master_repo.get_all_categories(
                active_only=True, include_roles=True
            )
            ctx["_job_categories"] = self._serialize_categories_for_context(categories)

        general_templates = await self._job_master_repo.get_fallback_questions(
            job_type=None,
            experience_level=None,
        )
        if not general_templates:
            return [{
                "role": CandidateMessageRole.BOT,
                "content": "Resume builder is not configured for general flow yet. Please set a job role in your profile and try again.",
                "message_type": CandidateMessageType.ERROR,
                "message_data": {},
            }]

        collected = ctx.get("collected_data", {})
        engine = QuestionEngine(general_templates, collected)
        first_question = engine.get_next_question()
        if not first_question:
            if _has_known_fallback_role(collected):
                ctx["role_id"] = str(collected["job_role_id"])
                ctx["fallback_phase"] = "role_based"
                ctx["current_question_key"] = None
                await self._chat_repo.update_session(session.id, context_data=ctx)
                role_templates = await self._job_master_repo.get_templates_by_role(UUID(ctx["role_id"]))
                if role_templates:
                    role_engine = QuestionEngine(role_templates, collected)
                    first_role_q = role_engine.get_next_question()
                    if first_role_q:
                        ctx["current_question_key"] = first_role_q.question_key
                        await self._chat_repo.update_session(session.id, context_data=ctx)
                        intro = {
                            "role": CandidateMessageRole.BOT,
                            "content": f"A few role-specific questions for {collected.get('job_role_name', 'your role')}:",
                            "message_type": CandidateMessageType.TEXT,
                            "message_data": {},
                        }
                        return [intro, role_engine.build_question_message(first_role_q)]
            return await self._transition_fallback_after_general(session, ctx)

        ctx["current_question_key"] = first_question.question_key
        await self._chat_repo.update_session(session.id, context_data=ctx)

        intro_msg = {
            "role": CandidateMessageRole.BOT,
            "content": "Let's build your resume! I'll ask a few general questions first, then we'll narrow down by job type.",
            "message_type": CandidateMessageType.TEXT,
            "message_data": {},
        }
        if first_question.question_key in ("job_category_id", "job_role_id"):
            question_msg = self._build_fallback_category_role_question_message(first_question, ctx, engine)
        else:
            question_msg = engine.build_question_message(first_question)
        return [intro_msg, question_msg]

    async def _build_next_question_messages(
        self,
        session: CandidateChatSession,
    ) -> List[dict]:
        """Build message for the next unanswered question (used for resume-from-left-off)."""
        ctx = session.context_data or {}
        collected_data = ctx.get("collected_data", {})

        if ctx.get("fallback_mode"):
            phase = ctx.get("fallback_phase", "general")
            if phase == "choose_job_type":
                return []
            if phase == "general":
                if not ctx.get("_job_categories"):
                    categories = await self._job_master_repo.get_all_categories(
                        active_only=True, include_roles=True
                    )
                    ctx["_job_categories"] = self._serialize_categories_for_context(categories)
                    await self._chat_repo.update_session(session.id, context_data=ctx)
                templates = await self._job_master_repo.get_fallback_questions(
                    job_type=None,
                    experience_level=None,
                )
            elif phase == "role_based":
                rid = ctx.get("role_id") or collected_data.get("job_role_id")
                if not rid:
                    return []
                templates = await self._job_master_repo.get_templates_by_role(UUID(str(rid)))
            else:
                templates = await self._job_master_repo.get_fallback_questions(
                    job_type=ctx.get("fallback_job_type"),
                    experience_level=ctx.get("fallback_experience_level") or "experienced",
                )
        else:
            role_id = ctx.get("role_id")
            if not role_id:
                return []
            templates = await self._job_master_repo.get_templates_by_role(UUID(role_id))

        engine = QuestionEngine(templates, collected_data)
        next_q = engine.get_next_question()

        if not next_q:
            return []

        # Update current question key
        ctx["current_question_key"] = next_q.question_key
        await self._chat_repo.update_session(session.id, context_data=ctx)

        if ctx.get("fallback_mode") and ctx.get("fallback_phase") == "general" and next_q.question_key in ("job_category_id", "job_role_id"):
            return [self._build_fallback_category_role_question_message(next_q, ctx, engine)]
        return [engine.build_question_message(next_q)]

    def _copy_context(self, session: CandidateChatSession) -> dict:
        """Deep copy context_data to avoid mutation issues."""
        return copy.deepcopy(session.context_data or {})


# ==================== FACTORY ====================

def get_candidate_chat_service(session: AsyncSession) -> CandidateChatService:
    """Factory function to create CandidateChatService with all dependencies."""
    chat_repo = CandidateChatRepository(session)
    candidate_repo = CandidateRepository(session)
    job_master_repo = JobMasterRepository(session)
    resume_builder = ResumeBuilderService(candidate_repo, session)
    resume_extractor = get_resume_extractor()
    return CandidateChatService(
        chat_repo=chat_repo,
        candidate_repo=candidate_repo,
        job_master_repo=job_master_repo,
        resume_builder=resume_builder,
        resume_extractor=resume_extractor,
        session=session,
    )
