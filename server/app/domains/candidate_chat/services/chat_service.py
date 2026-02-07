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
from app.domains.job_master.repository import JobMasterRepository
from app.shared.exceptions import NotFoundError, ValidationError
from app.shared.logging import get_logger


logger = get_logger(__name__)


# ==================== STATIC WELCOME MESSAGES ====================

WELCOME_MESSAGES = [
    {
        "role": CandidateMessageRole.BOT,
        "content": "👋 Hello! I'm AIVI, your personal resume assistant.",
        "message_type": CandidateMessageType.TEXT,
        "message_data": {},
    },
    {
        "role": CandidateMessageRole.BOT,
        "content": "I'll help you create a professional resume that gets you noticed by employers. How would you like to proceed?",
        "message_type": CandidateMessageType.BUTTONS,
        "message_data": {
            "buttons": [
                {
                    "id": "upload_pdf",
                    "label": "📄 Upload Resume PDF",
                    "description": "I already have a resume PDF",
                },
                {
                    "id": "create_with_bot",
                    "label": "🤖 Create with AIVI Bot",
                    "description": "Help me build my resume step by step",
                },
            ],
        },
    },
]


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
    ) -> Tuple[CandidateChatSession, List[dict]]:
        """
        Create a new chat session with idempotency.

        If an active resume session already exists, returns it instead of
        creating a duplicate (resume-from-where-left-off).

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
        # If there's an active resume session, return it instead of creating new
        existing_session = await self._chat_repo.get_active_resume_session(candidate_id)
        if existing_session:
            logger.info(
                f"Returning existing active session: {existing_session.id}",
                extra={"session_id": str(existing_session.id), "candidate_id": str(candidate_id)},
            )
            # Return existing session with a "welcome back" message
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
        # Fetch session
        session = await self._chat_repo.get_session_by_id(session_id)
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

        # Re-fetch session to get updated context_data
        updated_session = await self._chat_repo.get_session_by_id(session_id)

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

        else:  # aivi_bot
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
                processing_msgs.extend(self._build_preview_messages(ctx))
        else:
            # All fields extracted — go to preview
            ctx["step"] = ChatStep.RESUME_PREVIEW
            await self._chat_repo.update_session(session.id, context_data=ctx)
            processing_msgs.extend(self._build_preview_messages(ctx))

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
        1. Determine which question is being answered (from context or data)
        2. Validate the answer via QuestionEngine
        3. If invalid → re-ask with error message
        4. If valid → save to collected_data, ask next question
        5. If all questions done → move to RESUME_PREVIEW
        """
        ctx = self._copy_context(session)
        collected_data = ctx.get("collected_data", {})

        # Get the question_key being answered
        question_key = data.get("question_key")

        if not question_key:
            # Determine from context: which question was the bot last asking?
            question_key = ctx.get("current_question_key")

        if not question_key:
            # Shouldn't happen, but recover gracefully
            logger.warning(f"No question_key found for session {session.id}")
            return await self._build_next_question_messages(session)

        # Get role's question templates
        role_id = ctx.get("role_id")
        if not role_id:
            return [{
                "role": CandidateMessageRole.BOT,
                "content": "Something went wrong — your role preference is missing. Please update your profile and try again.",
                "message_type": CandidateMessageType.ERROR,
                "message_data": {},
            }]

        templates = await self._job_master_repo.get_templates_by_role(UUID(role_id))
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
            # ==================== ALL QUESTIONS ANSWERED ====================
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
            # Go back to asking questions
            ctx = self._copy_context(session)
            ctx["step"] = ChatStep.ASKING_QUESTIONS
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
            role_name = ctx.get("role_name", "Unknown")
            job_type = ctx.get("job_type", "")
            method = ctx.get("method", "aivi_bot")

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

        Loads the candidate's preferred role, fetches question templates,
        and sends the first question.
        """
        role_id = ctx.get("role_id")

        if not role_id:
            return [{
                "role": CandidateMessageRole.BOT,
                "content": "It looks like you haven't set your preferred job role yet. Please update your profile with a preferred job role, then come back to build your resume.",
                "message_type": CandidateMessageType.ERROR,
                "message_data": {},
            }]

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
            # No templates for this role — use a generic fallback
            return [{
                "role": CandidateMessageRole.BOT,
                "content": f"I see you're interested in the **{role.name}** role. Unfortunately, I don't have specific questions for this role yet. Please check back later or upload your resume PDF instead.",
                "message_type": CandidateMessageType.TEXT,
                "message_data": {},
            }]

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
            "content": f"Let's build your resume for the **{role.name}** role! I'll ask you a few questions. Let's start:",
            "message_type": CandidateMessageType.TEXT,
            "message_data": {},
        }

        question_msg = engine.build_question_message(first_question)

        return [intro_msg, question_msg]

    async def _build_next_question_messages(
        self,
        session: CandidateChatSession,
    ) -> List[dict]:
        """Build message for the next unanswered question (used for resume-from-left-off)."""
        ctx = session.context_data or {}
        role_id = ctx.get("role_id")
        collected_data = ctx.get("collected_data", {})

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

        return [engine.build_question_message(next_q)]

    def _build_preview_messages(self, ctx: dict) -> List[dict]:
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
