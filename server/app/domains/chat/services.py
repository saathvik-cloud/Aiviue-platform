"""
Chat Domain Services for AIVI Conversational Bot.

Business logic for chat sessions and the conversational job creation flow.
"""

from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.chat.models import ChatSession, ChatMessage, MessageRole, MessageType, SessionType
from app.domains.chat.repository import ChatRepository
from app.domains.chat.schemas import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionWithMessagesResponse,
    ChatSessionListResponse,
    ChatMessageResponse,
    SendMessageResponse,
)
from app.shared.logging import get_logger
from app.shared.exceptions.base import NotFoundError, ValidationError


logger = get_logger(__name__)


class ChatService:
    """
    Service for chat operations.
    
    Handles business logic for chat sessions and messages.
    """
    
    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session."""
        self.db = db
        self.repo = ChatRepository(db)
    
    # ==================== SESSION MANAGEMENT ====================
    
    async def create_session(
        self,
        employer_id: UUID,
        session_type: str = SessionType.JOB_CREATION,
        title: Optional[str] = None,
    ) -> ChatSessionWithMessagesResponse:
        """
        Create a new chat session and add welcome message.
        
        Args:
            employer_id: Employer UUID
            session_type: Type of session
            title: Optional session title
            
        Returns:
            Created session with welcome messages
        """
        # Create session with step set to choose_method (welcome buttons ask this question)
        session = await self.repo.create_session(
            employer_id=employer_id,
            session_type=session_type,
            title=title or "New Conversation",
            context_data={"step": "choose_method", "collected_data": {}},
        )
        
        # Add welcome messages
        welcome_messages = self._get_welcome_messages()
        logger.info(f"Adding {len(welcome_messages)} welcome messages to session {session.id}")
        await self.repo.add_messages_batch(session.id, welcome_messages)
        
        # Refresh to get messages - force a clean query
        session = await self.repo.get_session_by_id(session.id, include_messages=True)
        logger.info(f"After refresh - session has {len(session.messages) if session.messages else 0} messages")
        
        logger.info(f"Created new chat session: {session.id}")
        response = self._to_session_with_messages_response(session)
        logger.info(f"Response has {len(response.messages) if response.messages else 0} messages")
        return response
    
    async def get_session(
        self,
        session_id: UUID,
        employer_id: UUID,
    ) -> ChatSessionWithMessagesResponse:
        """
        Get a chat session with all messages.
        
        Args:
            session_id: Session UUID
            employer_id: Employer UUID (for authorization)
            
        Returns:
            Session with messages
            
        Raises:
            NotFoundError: If session not found or unauthorized
        """
        session = await self.repo.get_session_by_id(session_id, include_messages=True)
        
        if session is None:
            raise NotFoundError(f"Chat session not found: {session_id}")
        
        if session.employer_id != employer_id:
            raise NotFoundError(f"Chat session not found: {session_id}")
        
        return self._to_session_with_messages_response(session)
    
    async def get_session_history(
        self,
        employer_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> ChatSessionListResponse:
        """
        Get chat session history for an employer.
        
        Args:
            employer_id: Employer UUID
            limit: Max sessions
            offset: Pagination offset
            
        Returns:
            List of sessions
        """
        sessions, total_count = await self.repo.get_sessions_by_employer(
            employer_id=employer_id,
            limit=limit,
            offset=offset,
        )
        
        return ChatSessionListResponse(
            items=[self._to_session_response(s) for s in sessions],
            total_count=total_count,
            has_more=(offset + len(sessions)) < total_count,
        )
    
    async def delete_session(
        self,
        session_id: UUID,
        employer_id: UUID,
    ) -> bool:
        """
        Delete (deactivate) a chat session.
        
        Args:
            session_id: Session UUID
            employer_id: Employer UUID (for authorization)
            
        Returns:
            True if deleted
            
        Raises:
            NotFoundError: If session not found
        """
        session = await self.repo.get_session_by_id(session_id, include_messages=False)
        
        if session is None or session.employer_id != employer_id:
            raise NotFoundError(f"Chat session not found: {session_id}")
        
        return await self.repo.delete_session(session_id)
    
    # ==================== MESSAGE HANDLING ====================
    
    async def send_message(
        self,
        session_id: UUID,
        employer_id: UUID,
        content: str,
        message_data: Optional[dict] = None,
    ) -> SendMessageResponse:
        """
        Send a user message and get bot response.
        
        Args:
            session_id: Session UUID
            employer_id: Employer UUID
            content: User message content
            message_data: Additional data (selected button value, etc.)
            
        Returns:
            User message and bot responses
        """
        # Get session
        session = await self.repo.get_session_by_id(session_id, include_messages=False)
        
        if session is None or session.employer_id != employer_id:
            raise NotFoundError(f"Chat session not found: {session_id}")
        
        # Add user message
        user_message = await self.repo.add_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=content,
            message_type=MessageType.TEXT,
            message_data=message_data,
        )
        
        # Process user input and get bot responses
        bot_responses = await self._process_user_input(session, content, message_data)
        
        # Add bot responses
        created_bot_messages = []
        for bot_msg in bot_responses:
            msg = await self.repo.add_message(
                session_id=session_id,
                role=MessageRole.BOT,
                content=bot_msg["content"],
                message_type=bot_msg.get("message_type", MessageType.TEXT),
                message_data=bot_msg.get("message_data"),
            )
            created_bot_messages.append(msg)
        
        return SendMessageResponse(
            user_message=self._to_message_response(user_message),
            bot_responses=[self._to_message_response(m) for m in created_bot_messages],
        )
    
    async def update_session_context(
        self,
        session_id: UUID,
        employer_id: UUID,
        context_data: dict,
        title: Optional[str] = None,
    ) -> ChatSessionResponse:
        """
        Update session context data.
        
        Args:
            session_id: Session UUID
            employer_id: Employer UUID
            context_data: New context data
            title: Optional new title
            
        Returns:
            Updated session
        """
        session = await self.repo.get_session_by_id(session_id, include_messages=False)
        
        if session is None or session.employer_id != employer_id:
            raise NotFoundError(f"Chat session not found: {session_id}")
        
        # Merge context data
        current_context = session.context_data or {}
        merged_context = {**current_context, **context_data}
        
        updated = await self.repo.update_session(
            session_id=session_id,
            context_data=merged_context,
            title=title,
        )
        
        return self._to_session_response(updated)
    
    # ==================== CONVERSATION LOGIC ====================
    
    def _get_welcome_messages(self) -> List[dict]:
        """Get welcome messages for a new session."""
        return [
            {
                "role": MessageRole.BOT,
                "content": "Hi! I'm AIVI, your AI recruiting expert!...",
                "message_type": MessageType.TEXT,
            },
            {
                "role": MessageRole.BOT,
                "content": "I'm here to help you create a job posting.\n\nHow would you like to proceed?",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": [
                        {"id": "paste_jd", "label": "📋 Paste JD", "value": "paste_jd"},
                        {"id": "use_aivi", "label": "💬 Use AIVI Bot", "value": "use_aivi"},
                    ],
                    "step": "choose_method",
                },
            },
        ]
    
    async def _process_user_input(
        self,
        session: ChatSession,
        content: str,
        message_data: Optional[dict],
    ) -> List[dict]:
        """
        Process user input and generate bot responses.
        
        This is the core conversation logic.
        
        Args:
            session: Current chat session
            content: User message content
            message_data: Additional data (selected button value)
            
        Returns:
            List of bot response messages
        """
        context = session.context_data or {}
        current_step = context.get("step", "welcome")
        collected_data = context.get("collected_data", {})
        
        # Get the selected value (from button click or text input)
        selected_value = message_data.get("value") if message_data else content
        
        # Route based on current step
        if current_step in ("choose_method", "welcome"):
            return await self._handle_method_selection(session, selected_value)
        
        elif current_step == "paste_jd":
            return await self._handle_paste_jd(session, content)
        
        elif current_step.startswith("job_"):
            return await self._handle_job_creation_step(session, selected_value, message_data)
        
        else:
            # Default response
            return [{
                "content": "I'm not sure how to help with that. Would you like to create a job posting?",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": [
                        {"id": "paste_jd", "label": "📋 Paste JD", "value": "paste_jd"},
                        {"id": "use_aivi", "label": "💬 Use AIVI Bot", "value": "use_aivi"},
                    ],
                    "step": "choose_method",
                },
            }]
    
    async def _handle_method_selection(
        self,
        session: ChatSession,
        selected_value: str,
    ) -> List[dict]:
        """Handle job creation method selection."""
        
        if selected_value == "paste_jd":
            # Update session context
            await self.repo.update_session(
                session_id=session.id,
                context_data={"step": "paste_jd", "collected_data": {}},
                title="Job Creation - Paste JD",
            )
            
            return [{
                "content": "Great! Please paste your job description below, and I'll extract all the details for you.",
                "message_type": MessageType.INPUT_TEXTAREA,
                "message_data": {
                    "placeholder": "Paste your job description here...",
                    "step": "paste_jd",
                },
            }]
        
        elif selected_value == "use_aivi":
            # Update session context
            await self.repo.update_session(
                session_id=session.id,
                context_data={"step": "job_title", "collected_data": {}},
                title="Job Creation - AIVI Bot",
            )
            
            return [
                {
                    "content": "Great choice! Let's create your job posting together. 🎯",
                    "message_type": MessageType.TEXT,
                },
                {
                    "content": "What's the job title you're hiring for?",
                    "message_type": MessageType.INPUT_TEXT,
                    "message_data": {
                        "placeholder": "e.g., Senior Software Engineer",
                        "field": "title",
                        "step": "job_title",
                    },
                },
            ]
        
        else:
            return [{
                "content": "Please select one of the options above.",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": [
                        {"id": "paste_jd", "label": "📋 Paste JD", "value": "paste_jd"},
                        {"id": "use_aivi", "label": "💬 Use AIVI Bot", "value": "use_aivi"},
                    ],
                    "step": "choose_method",
                },
            }]
    
    async def _handle_paste_jd(
        self,
        session: ChatSession,
        content: str,
    ) -> List[dict]:
        """Handle pasted JD - trigger extraction."""
        
        if len(content) < 50:
            return [{
                "content": "That seems too short for a job description. Please paste a complete JD (at least 50 characters).",
                "message_type": MessageType.INPUT_TEXTAREA,
                "message_data": {
                    "placeholder": "Paste your job description here...",
                    "step": "paste_jd",
                },
            }]
        
        # Store the raw JD and update step
        await self.repo.update_session(
            session_id=session.id,
            context_data={
                "step": "extracting",
                "collected_data": {"raw_jd": content},
            },
        )
        
        return [
            {
                "content": "Got it! Let me analyze your job description... 🔍",
                "message_type": MessageType.LOADING,
                "message_data": {
                    "action": "extract_jd",
                    "raw_jd": content,
                    "step": "extracting",
                },
            },
        ]
    
    async def handle_extraction_complete(
        self,
        session_id: UUID,
        employer_id: UUID,
        extracted_data: dict,
    ) -> SendMessageResponse:
        """
        Handle completion of JD extraction.
        
        Takes extracted data, determines which fields are missing,
        and returns the next question or preview.
        
        Args:
            session_id: Session UUID
            employer_id: Employer UUID
            extracted_data: Data extracted from JD by LLM
            
        Returns:
            SendMessageResponse with next question(s)
        """
        session = await self.repo.get_session_by_id(session_id, include_messages=True)
        
        if session is None or session.employer_id != employer_id:
            raise NotFoundError(f"Chat session not found: {session_id}")
        
        # Map extracted fields to our internal field names
        collected_data = {
            "title": extracted_data.get("title"),
            "requirements": extracted_data.get("requirements"),
            "description": extracted_data.get("description"),
            "country": extracted_data.get("country"),
            "state": extracted_data.get("state"),
            "city": extracted_data.get("city"),
            "work_type": extracted_data.get("work_type"),
            "currency": extracted_data.get("currency", "INR"),  # Default currency
            "salary_range": self._format_salary_range(
                extracted_data.get("salary_range_min"),
                extracted_data.get("salary_range_max")
            ),
            "experience_range": self._format_experience_range(
                extracted_data.get("experience_min"),
                extracted_data.get("experience_max")
            ),
            "shift_preference": self._format_shift_preference(
                extracted_data.get("shift_preferences")
            ),
            "openings_count": str(extracted_data.get("openings_count", "1")),
        }
        
        # Remove None values
        collected_data = {k: v for k, v in collected_data.items() if v is not None and v != ""}
        
        # Find the first missing required field
        first_missing_step = self._get_first_missing_step(collected_data)
        
        logger.info(
            f"Extraction complete for session {session_id}. "
            f"Collected: {list(collected_data.keys())}, First missing: {first_missing_step}"
        )
        
        # Add a confirmation message about extracted fields
        extracted_summary = self._get_extraction_summary(collected_data)
        
        # Create user message (representation of extraction result - hidden from UI)
        user_message = await self.repo.add_message(
            session_id=session_id,
            role=MessageRole.USER,
            content="",  # Empty content so it won't show in UI
            message_type=MessageType.TEXT,
            message_data={"extracted": True, "hidden": True, "fields": list(collected_data.keys())},
        )
        
        # Update session with collected data and next step
        await self.repo.update_session(
            session_id=session_id,
            context_data={
                "step": first_missing_step,
                "collected_data": collected_data,
            },
            title=f"Job Creation - {collected_data.get('title', 'Untitled')}",
        )
        
        # Build bot responses
        bot_responses = []
        
        # Add summary message
        bot_responses.append({
            "content": extracted_summary,
            "message_type": MessageType.TEXT,
        })
        
        # Add next step question or generate description
        next_question = self._get_step_question(first_missing_step, collected_data)
        bot_responses.extend(next_question)
        
        # Save bot messages
        created_bot_messages = []
        for bot_msg in bot_responses:
            msg = await self.repo.add_message(
                session_id=session_id,
                role=MessageRole.BOT,
                content=bot_msg["content"],
                message_type=bot_msg.get("message_type", MessageType.TEXT),
                message_data=bot_msg.get("message_data"),
            )
            created_bot_messages.append(msg)
        
        return SendMessageResponse(
            user_message=self._to_message_response(user_message),
            bot_responses=[self._to_message_response(m) for m in created_bot_messages],
        )
    
    def _format_salary_range(self, min_val: any, max_val: any) -> Optional[str]:
        """Format salary range as 'min-max' string."""
        if min_val is not None and max_val is not None:
            return f"{min_val}-{max_val}"
        elif min_val is not None:
            return f"{min_val}-0"
        return None
    
    def _format_experience_range(self, min_val: any, max_val: any) -> Optional[str]:
        """Format experience range as 'min-max' string."""
        if min_val is not None and max_val is not None:
            return f"{min_val}-{max_val}"
        elif min_val is not None:
            return f"{min_val}-0"
        return None
    
    def _format_shift_preference(self, shift_data: any) -> Optional[str]:
        """
        Convert shift_preferences (object or string) to a simple string.
        
        LLM may return:
        - {'shifts': ['day', 'night'], 'hours': '9-5'}
        - {'hours': '8-10 hours per day'}
        - 'day shift'
        - None
        
        We need to convert to a simple string like 'day', 'night', 'flexible', etc.
        """
        if shift_data is None:
            return None
        
        # Already a string - return as is
        if isinstance(shift_data, str):
            return shift_data
        
        # It's a dict - extract meaningful info
        if isinstance(shift_data, dict):
            parts = []
            
            # Check for 'shifts' array
            shifts = shift_data.get("shifts")
            if shifts and isinstance(shifts, list):
                parts.extend(shifts)
            
            # Check for 'hours'
            hours = shift_data.get("hours")
            if hours:
                parts.append(str(hours))
            
            # Check for 'shift' (singular)
            shift = shift_data.get("shift")
            if shift:
                parts.append(str(shift))
            
            # If we got something, join it
            if parts:
                return ", ".join(parts)
            
            # Fallback: convert entire dict to string
            return str(shift_data)
        
        # Fallback for any other type
        return str(shift_data) if shift_data else None
    
    def _get_first_missing_step(self, collected_data: dict) -> str:
        """
        Determine the first step with missing required data.
        
        Required fields order:
        1. title (always required)
        2. requirements (always required)
        3. country -> state -> city (location)
        4. work_type
        5. currency -> salary_range
        6. experience_range
        7. shift_preference
        8. openings_count
        
        Returns:
            Step name for the first missing field, or 'generating' if all complete.
        """
        # Define required fields and their corresponding steps
        field_to_step = [
            ("title", "job_title"),
            ("requirements", "job_requirements"),
            ("country", "job_country"),
            ("state", "job_state"),
            ("city", "job_city"),
            ("work_type", "job_work_type"),
            ("currency", "job_currency"),
            ("salary_range", "job_salary"),
            ("experience_range", "job_experience"),
            ("shift_preference", "job_shift"),
            ("openings_count", "job_openings"),
        ]
        
        for field, step in field_to_step:
            value = collected_data.get(field)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return step
        
        # All fields present - go to generating
        return "generating"
    
    def _get_extraction_summary(self, collected_data: dict) -> str:
        """Generate a summary message of what was extracted."""
        extracted_items = []
        
        if collected_data.get("title"):
            extracted_items.append(f"📋 Title: {collected_data['title']}")
        if collected_data.get("country"):
            location_parts = [
                collected_data.get("city"),
                collected_data.get("state"),
                collected_data.get("country"),
            ]
            location = ", ".join(filter(None, location_parts))
            if location:
                extracted_items.append(f"📍 Location: {location}")
        if collected_data.get("work_type"):
            extracted_items.append(f"🏢 Work Type: {collected_data['work_type']}")
        if collected_data.get("experience_range"):
            extracted_items.append(f"⏱️ Experience: {collected_data['experience_range']} years")
        if collected_data.get("salary_range"):
            extracted_items.append(f"💰 Salary: {collected_data['salary_range']}")        
        if extracted_items:
            summary = "I found the following details from your JD:\n\n" + "\n".join(extracted_items)
            
            # Check what's missing
            missing_fields = []
            if not collected_data.get("country"):
                missing_fields.append("location")
            if not collected_data.get("work_type"):
                missing_fields.append("work type")
            if not collected_data.get("salary_range"):
                missing_fields.append("salary range")
            if not collected_data.get("shift_preference"):
                missing_fields.append("shift preference")
            if not collected_data.get("openings_count") or collected_data.get("openings_count") == "1":
                missing_fields.append("number of openings")
            
            if missing_fields:
                summary += f"\n\n🔎 I just need a few more details: {', '.join(missing_fields[:3])}..."
            else:
                summary += "\n\n✅ All details found! Let me generate your job description."
            
            return summary
        else:
            return "I couldn't extract many details from the JD. Let me ask you a few questions."
    
    async def _handle_job_creation_step(
        self,
        session: ChatSession,
        value: str,
        message_data: Optional[dict],
    ) -> List[dict]:
        """
        Handle a step in the conversational job creation flow.
        
        This is the main state machine for collecting job details.
        Each step stores data, then returns the next question.
        """
        context = session.context_data or {}
        current_step = context.get("step", "job_title")
        collected_data = context.get("collected_data", {})
        
        # Handle "other" selection - prompt for text input
        if value == "other" or (message_data and message_data.get("action") == "show_input"):
            return self._get_other_input_prompt(current_step)
        
        # Map current step to field name (no hardcoded next_step!)
        step_to_field = {
            "job_title": "title",
            "job_requirements": "requirements",
            "job_country": "country",
            "job_state": "state",
            "job_city": "city",
            "job_work_type": "work_type",
            "job_currency": "currency",
            "job_salary": "salary_range",
            "job_experience": "experience_range",
            "job_shift": "shift_preference",
            "job_openings": "openings_count",
        }
        
        if current_step in step_to_field:
            # Store the user's answer
            field_name = step_to_field[current_step]
            collected_data[field_name] = value
            
            # DYNAMICALLY find the next missing step (skips already-extracted fields!)
            next_step = self._get_first_missing_step(collected_data)
            
            # Update session with new data and next step
            await self.repo.update_session(
                session_id=session.id,
                context_data={
                    "step": next_step,
                    "collected_data": collected_data,
                },
            )
            
            # Return the next question (or generate if all complete)
            return self._get_step_question(next_step, collected_data)
        
        # Fallback
        return [{
            "content": "Something went wrong. Let's start over.",
            "message_type": MessageType.BUTTONS,
            "message_data": {
                "buttons": [
                    {"id": "paste_jd", "label": "📋 Paste JD", "value": "paste_jd"},
                    {"id": "use_aivi", "label": "💬 Use AIVI Bot", "value": "use_aivi"},
                ],
                "step": "choose_method",
            },
        }]
    
    def _get_other_input_prompt(self, step: str) -> List[dict]:
        """Get text input prompt for 'Other' selections."""
        prompts = {
            "job_country": ("Enter the country name:", "e.g., Singapore"),
            "job_state": ("Enter the state/region name:", "e.g., Central Region"),
            "job_city": ("Enter the city name:", "e.g., Singapore City"),
            "job_salary": ("Enter salary range (min-max):", "e.g., 500000-1000000"),
            "job_experience": ("Enter experience range in years (min-max):", "e.g., 3-5"),
            "job_openings": ("How many positions?", "e.g., 2"),
        }
        
        content, placeholder = prompts.get(step, ("Please enter your value:", "Type here..."))
        
        return [{
            "content": content,
            "message_type": MessageType.INPUT_TEXT,
            "message_data": {
                "placeholder": placeholder,
                "step": step,
            },
        }]
    
    def _get_step_question(self, step: str, collected_data: dict) -> List[dict]:
        """Get the question and buttons for a specific step."""
        
        # ==================== JOB TITLE ====================
        if step == "job_title":
            return [{
                "content": "I couldn't find the job title in your JD. What position are you hiring for?",
                "message_type": MessageType.INPUT_TEXT,
                "message_data": {
                    "placeholder": "e.g., Plumber, Software Engineer, Data Analyst",
                    "field": "title",
                    "step": "job_title",
                },
            }]
        
        # ==================== REQUIREMENTS ====================
        if step == "job_requirements":
            return [{
                "content": f"Nice! '{collected_data.get('title')}' - that's a great role! 💼\n\nWhat skills and qualifications are you looking for?",
                "message_type": MessageType.INPUT_TEXTAREA,
                "message_data": {
                    "placeholder": "e.g., 5+ years in React, Node.js, PostgreSQL...",
                    "field": "requirements",
                    "step": "job_requirements",
                },
            }]
        
        # ==================== COUNTRY ====================
        if step == "job_country":
            return [{
                "content": "Got it! Now, which country is this job located in?",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": [
                        {"id": "india", "label": "🇮🇳 India", "value": "India"},
                        {"id": "usa", "label": "🇺🇸 USA", "value": "USA"},
                        {"id": "uk", "label": "🇬🇧 UK", "value": "UK"},
                        {"id": "other", "label": "✏️ Other", "value": "other"},
                    ],
                    "step": "job_country",
                },
            }]
        
        # ==================== STATE ====================
        if step == "job_state":
            country = collected_data.get("country", "")
            states_map = {
                "India": [
                    {"id": "mh", "label": "Maharashtra", "value": "Maharashtra"},
                    {"id": "ka", "label": "Karnataka", "value": "Karnataka"},
                    {"id": "dl", "label": "Delhi NCR", "value": "Delhi NCR"},
                    {"id": "tn", "label": "Tamil Nadu", "value": "Tamil Nadu"},
                    {"id": "tg", "label": "Telangana", "value": "Telangana"},
                    {"id": "gj", "label": "Gujarat", "value": "Gujarat"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
                "USA": [
                    {"id": "ca", "label": "California", "value": "California"},
                    {"id": "ny", "label": "New York", "value": "New York"},
                    {"id": "tx", "label": "Texas", "value": "Texas"},
                    {"id": "wa", "label": "Washington", "value": "Washington"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
                "UK": [
                    {"id": "england", "label": "England", "value": "England"},
                    {"id": "scotland", "label": "Scotland", "value": "Scotland"},
                    {"id": "wales", "label": "Wales", "value": "Wales"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
            }
            buttons = states_map.get(country, [{"id": "other", "label": "✏️ Enter manually", "value": "other"}])
            
            return [{
                "content": f"Which state/region in {country}?",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": buttons,
                    "step": "job_state",
                },
            }]
        
        # ==================== CITY ====================
        if step == "job_city":
            state = collected_data.get("state", "")
            cities_map = {
                "Maharashtra": [
                    {"id": "mumbai", "label": "Mumbai", "value": "Mumbai"},
                    {"id": "pune", "label": "Pune", "value": "Pune"},
                    {"id": "nagpur", "label": "Nagpur", "value": "Nagpur"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
                "Karnataka": [
                    {"id": "bangalore", "label": "Bangalore", "value": "Bangalore"},
                    {"id": "mysore", "label": "Mysore", "value": "Mysore"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
                "Delhi NCR": [
                    {"id": "delhi", "label": "New Delhi", "value": "New Delhi"},
                    {"id": "gurgaon", "label": "Gurgaon", "value": "Gurgaon"},
                    {"id": "noida", "label": "Noida", "value": "Noida"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
                "Tamil Nadu": [
                    {"id": "chennai", "label": "Chennai", "value": "Chennai"},
                    {"id": "coimbatore", "label": "Coimbatore", "value": "Coimbatore"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
                "Telangana": [
                    {"id": "hyderabad", "label": "Hyderabad", "value": "Hyderabad"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
                "Gujarat": [
                    {"id": "ahmedabad", "label": "Ahmedabad", "value": "Ahmedabad"},
                    {"id": "surat", "label": "Surat", "value": "Surat"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
                "California": [
                    {"id": "sf", "label": "San Francisco", "value": "San Francisco"},
                    {"id": "la", "label": "Los Angeles", "value": "Los Angeles"},
                    {"id": "sj", "label": "San Jose", "value": "San Jose"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
                "New York": [
                    {"id": "nyc", "label": "New York City", "value": "New York City"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
                "Texas": [
                    {"id": "austin", "label": "Austin", "value": "Austin"},
                    {"id": "dallas", "label": "Dallas", "value": "Dallas"},
                    {"id": "houston", "label": "Houston", "value": "Houston"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
                "Washington": [
                    {"id": "seattle", "label": "Seattle", "value": "Seattle"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
                "England": [
                    {"id": "london", "label": "London", "value": "London"},
                    {"id": "manchester", "label": "Manchester", "value": "Manchester"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
                "Scotland": [
                    {"id": "edinburgh", "label": "Edinburgh", "value": "Edinburgh"},
                    {"id": "glasgow", "label": "Glasgow", "value": "Glasgow"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
                "Wales": [
                    {"id": "cardiff", "label": "Cardiff", "value": "Cardiff"},
                    {"id": "other", "label": "✏️ Other", "value": "other"},
                ],
            }
            buttons = cities_map.get(state, [{"id": "other", "label": "✏️ Enter manually", "value": "other"}])
            
            return [{
                "content": f"Which city in {state}?",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": buttons,
                    "step": "job_city",
                },
            }]
        
        # ==================== WORK TYPE ====================
        if step == "job_work_type":
            return [{
                "content": "Perfect! 📍 What's the work arrangement?",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": [
                        {"id": "onsite", "label": "🏢 On-site", "value": "onsite"},
                        {"id": "remote", "label": "🏠 Remote", "value": "remote"},
                        {"id": "hybrid", "label": "🔄 Hybrid", "value": "hybrid"},
                    ],
                    "step": "job_work_type",
                },
            }]
        
        # ==================== CURRENCY ====================
        if step == "job_currency":
            return [{
                "content": "Now let's talk compensation! 💰\n\nSelect the salary currency:",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": [
                        {"id": "inr", "label": "₹ INR", "value": "INR"},
                        {"id": "usd", "label": "$ USD", "value": "USD"},
                        {"id": "gbp", "label": "£ GBP", "value": "GBP"},
                        {"id": "eur", "label": "€ EUR", "value": "EUR"},
                    ],
                    "step": "job_currency",
                },
            }]
        
        # ==================== SALARY ====================
        if step == "job_salary":
            currency = collected_data.get("currency", "INR")
            salary_options = {
                "INR": [
                    {"id": "inr_5_10", "label": "₹5L - 10L", "value": "500000-1000000"},
                    {"id": "inr_10_25", "label": "₹10L - 25L", "value": "1000000-2500000"},
                    {"id": "inr_25_50", "label": "₹25L - 50L", "value": "2500000-5000000"},
                    {"id": "inr_50_plus", "label": "₹50L+", "value": "5000000-0"},
                    {"id": "custom", "label": "✏️ Custom", "value": "other"},
                ],
                "USD": [
                    {"id": "usd_50_100", "label": "$50K - 100K", "value": "50000-100000"},
                    {"id": "usd_100_150", "label": "$100K - 150K", "value": "100000-150000"},
                    {"id": "usd_150_200", "label": "$150K - 200K", "value": "150000-200000"},
                    {"id": "usd_200_plus", "label": "$200K+", "value": "200000-0"},
                    {"id": "custom", "label": "✏️ Custom", "value": "other"},
                ],
                "GBP": [
                    {"id": "gbp_40_80", "label": "£40K - 80K", "value": "40000-80000"},
                    {"id": "gbp_80_120", "label": "£80K - 120K", "value": "80000-120000"},
                    {"id": "gbp_120_plus", "label": "£120K+", "value": "120000-0"},
                    {"id": "custom", "label": "✏️ Custom", "value": "other"},
                ],
                "EUR": [
                    {"id": "eur_40_80", "label": "€40K - 80K", "value": "40000-80000"},
                    {"id": "eur_80_120", "label": "€80K - 120K", "value": "80000-120000"},
                    {"id": "eur_120_plus", "label": "€120K+", "value": "120000-0"},
                    {"id": "custom", "label": "✏️ Custom", "value": "other"},
                ],
            }
            buttons = salary_options.get(currency, salary_options["INR"])
            
            return [{
                "content": "What's the annual salary range?",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": buttons,
                    "step": "job_salary",
                },
            }]
        
        # ==================== EXPERIENCE ====================
        if step == "job_experience":
            return [{
                "content": "What experience level are you looking for?",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": [
                        {"id": "fresher", "label": "Fresher (0-1 yr)", "value": "0-1"},
                        {"id": "junior", "label": "1-3 years", "value": "1-3"},
                        {"id": "mid", "label": "3-5 years", "value": "3-5"},
                        {"id": "senior", "label": "5-10 years", "value": "5-10"},
                        {"id": "expert", "label": "10+ years", "value": "10-99"},
                        {"id": "custom", "label": "✏️ Custom", "value": "other"},
                    ],
                    "step": "job_experience",
                },
            }]
        
        # ==================== SHIFT ====================
        if step == "job_shift":
            return [{
                "content": "Preferred shift timing?",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": [
                        {"id": "day", "label": "☀️ Day Shift", "value": "day"},
                        {"id": "night", "label": "🌙 Night Shift", "value": "night"},
                        {"id": "flexible", "label": "🌤️ Flexible", "value": "flexible"},
                    ],
                    "step": "job_shift",
                },
            }]
        
        # ==================== OPENINGS ====================
        if step == "job_openings":
            return [{
                "content": "Almost done! 🎉\n\nHow many positions are you hiring for?",
                "message_type": MessageType.BUTTONS,
                "message_data": {
                    "buttons": [
                        {"id": "1", "label": "1", "value": "1"},
                        {"id": "2", "label": "2", "value": "2"},
                        {"id": "3", "label": "3", "value": "3"},
                        {"id": "5", "label": "5", "value": "5"},
                        {"id": "custom", "label": "✏️ Custom", "value": "other"},
                    ],
                    "step": "job_openings",
                },
            }]
        
        # ==================== GENERATING ====================
        if step == "generating":
            # Build a summary of collected data
            location_parts = [
                collected_data.get("city", ""),
                collected_data.get("state", ""),
                collected_data.get("country", ""),
            ]
            location = ", ".join(filter(None, location_parts))
            
            return [
                {
                    "content": "Perfect! I have all the details. Let me generate your job description... 🔮",
                    "message_type": MessageType.LOADING,
                    "message_data": {
                        "action": "generate_description",
                        "step": "generating",
                    },
                },
            ]
        
        # ==================== PREVIEW ====================
        if step == "preview":
            return [{
                "content": "Here's your job posting preview! 🎉",
                "message_type": MessageType.JOB_PREVIEW,
                "message_data": {
                    "job_data": collected_data,
                    "step": "preview",
                },
            }]
        
        # Default fallback
        return [{
            "content": "Let's continue with the job creation.",
            "message_type": MessageType.TEXT,
        }]
    
    # ==================== RESPONSE MAPPERS ====================
    
    def _to_session_response(self, session: ChatSession) -> ChatSessionResponse:
        """Convert ChatSession to response schema."""
        return ChatSessionResponse(
            id=session.id,
            employer_id=session.employer_id,
            title=session.title,
            session_type=session.session_type,
            context_data=session.context_data,
            is_active=session.is_active,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=session.message_count,
            last_message_at=session.last_message_at,
        )
    
    def _to_session_with_messages_response(
        self,
        session: ChatSession,
    ) -> ChatSessionWithMessagesResponse:
        """Convert ChatSession to response with messages."""
        return ChatSessionWithMessagesResponse(
            id=session.id,
            employer_id=session.employer_id,
            title=session.title,
            session_type=session.session_type,
            context_data=session.context_data,
            is_active=session.is_active,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=[self._to_message_response(m) for m in session.messages],
        )
    
    def _to_message_response(self, message: ChatMessage) -> ChatMessageResponse:
        """Convert ChatMessage to response schema."""
        return ChatMessageResponse(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            message_type=message.message_type,
            message_data=message.message_data,
            created_at=message.created_at,
        )


# ==================== DEPENDENCY INJECTION ====================

def get_chat_service(db: AsyncSession) -> ChatService:
    """Get ChatService instance with database session."""
    return ChatService(db)
