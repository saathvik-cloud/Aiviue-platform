"""
Question Engine for Candidate Resume Builder.

Drives the dynamic questioning flow based on role-specific templates.
Handles:
- Template-based question ordering
- Conditional question evaluation (depends_on logic)
- Answer validation against template rules
- Progress tracking
- Question-type to message-type mapping

Production patterns:
- Dictionary dispatch for question type → message type mapping
- Pure functions for condition evaluation (no side effects)
- Immutable template data (templates are read-only)
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from app.domains.job_master.models import RoleQuestionTemplate
from app.shared.logging import get_logger


logger = get_logger(__name__)


# ==================== QUESTION TYPE → MESSAGE TYPE MAPPING ====================

QUESTION_TYPE_TO_MESSAGE_TYPE: Dict[str, str] = {
    "text": "input_text",
    "number": "input_number",
    "date": "input_date",
    "boolean": "boolean",
    "select": "select",
    "multi_select": "multi_select",
    "file": "input_file",
}


# ==================== ANSWER PARSERS (Dictionary Dispatch) ====================

def _parse_text(value: Any, rules: Optional[dict]) -> Tuple[Any, Optional[str]]:
    """Parse and validate text answer."""
    val = str(value).strip()
    if not val:
        return None, "This field cannot be empty."
    if rules:
        min_len = rules.get("min_length", 0)
        max_len = rules.get("max_length", 5000)
        if len(val) < min_len:
            return None, f"Must be at least {min_len} characters."
        if len(val) > max_len:
            return None, f"Must be at most {max_len} characters."
    return val, None


def _parse_number(value: Any, rules: Optional[dict]) -> Tuple[Any, Optional[str]]:
    """Parse and validate number answer."""
    try:
        num = float(value)
    except (ValueError, TypeError):
        return None, "Please enter a valid number."
    if rules:
        min_val = rules.get("min")
        max_val = rules.get("max")
        if min_val is not None and num < min_val:
            return None, f"Value must be at least {min_val}."
        if max_val is not None and num > max_val:
            return None, f"Value must be at most {max_val}."
    # Return int if whole number, float otherwise
    return int(num) if num == int(num) else num, None


def _parse_date(value: Any, rules: Optional[dict]) -> Tuple[Any, Optional[str]]:
    """Parse and validate date answer (DOB validation)."""
    try:
        if isinstance(value, str):
            # Support multiple formats
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    parsed = datetime.strptime(value, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                return None, "Invalid date format. Use YYYY-MM-DD."
        elif isinstance(value, date):
            parsed = value
        else:
            return None, "Invalid date format."
    except Exception:
        return None, "Invalid date format. Use YYYY-MM-DD."

    # Age validation
    if rules:
        today = date.today()
        age = today.year - parsed.year - ((today.month, today.day) < (parsed.month, parsed.day))
        min_age = rules.get("min_age")
        max_age = rules.get("max_age")
        if min_age is not None and age < min_age:
            return None, f"You must be at least {min_age} years old."
        if max_age is not None and age > max_age:
            return None, f"Age must be at most {max_age} years."

    return parsed.isoformat(), None


def _parse_boolean(value: Any, rules: Optional[dict]) -> Tuple[Any, Optional[str]]:
    """Parse boolean answer."""
    if isinstance(value, bool):
        return value, None
    if isinstance(value, str):
        lower = value.strip().lower()
        truthy = {"yes", "true", "1", "y"}
        falsy = {"no", "false", "0", "n"}
        if lower in truthy:
            return True, None
        if lower in falsy:
            return False, None
    return None, "Please answer Yes or No."


def _parse_select(value: Any, rules: Optional[dict]) -> Tuple[Any, Optional[str]]:
    """Parse single-select answer."""
    val = str(value).strip()
    if not val:
        return None, "Please select an option."
    return val, None


def _parse_multi_select(value: Any, rules: Optional[dict]) -> Tuple[Any, Optional[str]]:
    """Parse multi-select answer."""
    if isinstance(value, list):
        cleaned = [str(v).strip() for v in value if str(v).strip()]
        if not cleaned:
            return None, "Please select at least one option."
        return cleaned, None
    if isinstance(value, str):
        # Handle comma-separated string
        items = [v.strip() for v in value.split(",") if v.strip()]
        if not items:
            return None, "Please select at least one option."
        return items, None
    return None, "Invalid selection format."


def _parse_file(value: Any, rules: Optional[dict]) -> Tuple[Any, Optional[str]]:
    """Parse file upload answer (URL string)."""
    val = str(value).strip()
    if not val:
        return None, "Please upload a file."
    return val, None


# Dictionary dispatch for answer parsing
ANSWER_PARSERS: Dict[str, callable] = {
    "text": _parse_text,
    "number": _parse_number,
    "date": _parse_date,
    "boolean": _parse_boolean,
    "select": _parse_select,
    "multi_select": _parse_multi_select,
    "file": _parse_file,
}


# ==================== QUESTION ENGINE ====================

class QuestionEngine:
    """
    Drives the dynamic questioning flow for resume building.

    Uses role-specific question templates to determine:
    1. Which question to ask next
    2. Whether a conditional question should be shown
    3. How to validate answers
    4. Current progress percentage

    This class is stateless — all state lives in the session's context_data.
    Templates are immutable input.
    """

    def __init__(
        self,
        templates: List[RoleQuestionTemplate],
        collected_data: Dict[str, Any],
    ) -> None:
        """
        Initialize QuestionEngine.

        Args:
            templates: Role-specific question templates, sorted by display_order
            collected_data: Already collected answers from session context
        """
        self._templates = sorted(
            [t for t in templates if t.is_active],
            key=lambda t: t.display_order,
        )
        self._collected_data = collected_data or {}

    # ==================== CORE METHODS ====================

    def get_next_question(self) -> Optional[RoleQuestionTemplate]:
        """
        Find the next unanswered, applicable question.

        Logic:
        1. Iterate templates in display_order
        2. Skip already-answered questions
        3. Skip conditional questions whose condition is not met
        4. Return the first applicable question, or None if all done

        Returns:
            Next question template, or None if all questions answered
        """
        for template in self._templates:
            # Already answered → skip
            if template.question_key in self._collected_data:
                continue

            # Check conditional display
            if not self._evaluate_condition(template):
                continue

            return template

        return None  # All applicable questions answered

    def process_answer(
        self,
        question_key: str,
        raw_value: Any,
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Validate and parse an answer for a question.

        Args:
            question_key: The question being answered
            raw_value: The raw answer from the user

        Returns:
            Tuple of (is_valid, parsed_value, error_message)
        """
        template = self._get_template_by_key(question_key)
        if not template:
            logger.warning(f"Question key not found: {question_key}")
            return False, None, "Unknown question."

        # Get the appropriate parser via dictionary dispatch
        parser = ANSWER_PARSERS.get(template.question_type, _parse_text)
        parsed_value, error = parser(raw_value, template.validation_rules)

        if error:
            # For required fields, return error
            if template.is_required:
                return False, None, error
            # For optional fields, allow empty/invalid (skip)
            return True, None, None

        return True, parsed_value, None

    # ==================== PROGRESS TRACKING ====================

    @property
    def total_applicable_questions(self) -> int:
        """Count of applicable questions (excluding skipped conditionals)."""
        count = 0
        for template in self._templates:
            if self._evaluate_condition(template):
                count += 1
        return count

    @property
    def answered_count(self) -> int:
        """Count of answered questions."""
        count = 0
        for template in self._templates:
            if template.question_key in self._collected_data:
                count += 1
            elif not self._evaluate_condition(template):
                # Conditional question that was correctly skipped counts as handled
                count += 1
        return count

    @property
    def progress_percentage(self) -> float:
        """Calculate completion percentage (0.0 to 100.0)."""
        total = self.total_applicable_questions
        if total == 0:
            return 100.0
        return round((self.answered_count / total) * 100, 1)

    @property
    def is_complete(self) -> bool:
        """Check if all applicable questions have been answered."""
        return self.get_next_question() is None

    @property
    def remaining_required_count(self) -> int:
        """Count of remaining required questions."""
        count = 0
        for template in self._templates:
            if template.question_key in self._collected_data:
                continue
            if not self._evaluate_condition(template):
                continue
            if template.is_required:
                count += 1
        return count

    # ==================== MESSAGE BUILDERS ====================

    def build_question_message(self, template: RoleQuestionTemplate) -> dict:
        """
        Build a bot message dict for a question template.

        Maps question_type to the appropriate message_type for frontend rendering.

        Returns:
            dict with keys: role, content, message_type, message_data
        """
        message_type = QUESTION_TYPE_TO_MESSAGE_TYPE.get(
            template.question_type, "input_text"
        )

        message_data = {
            "question_key": template.question_key,
        }

        # Add options for select/multi_select/boolean types
        if template.options:
            if isinstance(template.options, list):
                message_data["options"] = template.options
            elif isinstance(template.options, dict):
                message_data["options"] = template.options
        elif template.question_type == "boolean":
            message_data["options"] = [
                {"label": "Yes", "value": True},
                {"label": "No", "value": False},
            ]

        # Add validation rules for frontend validation
        if template.validation_rules:
            message_data["validation"] = template.validation_rules

        # Add required flag
        message_data["is_required"] = template.is_required

        # Add progress info
        message_data["progress"] = {
            "current": self.answered_count + 1,
            "total": self.total_applicable_questions,
            "percentage": self.progress_percentage,
        }

        return {
            "role": "bot",
            "content": template.question_text,
            "message_type": message_type,
            "message_data": message_data,
        }

    # ==================== INTERNAL HELPERS ====================

    def _evaluate_condition(self, template: RoleQuestionTemplate) -> bool:
        """
        Evaluate whether a conditional question should be shown.

        Condition format: {"depends_on": "question_key", "value": expected_value}

        Returns:
            True if question should be shown, False if skipped
        """
        if not template.condition:
            return True  # No condition → always show

        depends_on = template.condition.get("depends_on")
        expected_value = template.condition.get("value")

        if depends_on is None:
            return True  # Malformed condition → show by default

        # If the dependency hasn't been answered yet, don't show this question
        if depends_on not in self._collected_data:
            return False

        actual_value = self._collected_data[depends_on]
        return actual_value == expected_value

    def _get_template_by_key(self, question_key: str) -> Optional[RoleQuestionTemplate]:
        """Find a template by its question_key."""
        for template in self._templates:
            if template.question_key == question_key:
                return template
        return None
