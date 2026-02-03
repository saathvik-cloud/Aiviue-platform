"""
Chat Domain Schemas for AIVI Conversational Bot.

Pydantic schemas (DTOs) for chat sessions and messages.
"""

from datetime import datetime
from typing import Any, Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ==================== MESSAGE SCHEMAS ====================

class ChatMessageCreate(BaseModel):
    """Schema for creating a new chat message."""
    
    role: str = Field(
        ...,
        pattern="^(bot|user)$",
        description="Message role: bot or user",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Message text content",
    )
    message_type: str = Field(
        default="text",
        description="Type: text, buttons, job_preview, etc.",
    )
    message_data: Optional[dict[str, Any]] = Field(
        None,
        description="Additional data (button options, job data, etc.)",
    )


class ChatMessageResponse(BaseModel):
    """Schema for chat message response."""
    
    id: UUID
    session_id: UUID
    role: str
    content: str
    message_type: str
    message_data: Optional[dict[str, Any]]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== SESSION SCHEMAS ====================

class ChatSessionCreate(BaseModel):
    """Schema for creating a new chat session."""
    
    employer_id: UUID = Field(
        ...,
        description="Employer UUID",
    )
    title: Optional[str] = Field(
        None,
        max_length=255,
        description="Session title (auto-generated if not provided)",
    )
    session_type: str = Field(
        default="job_creation",
        description="Type: job_creation, general",
    )
    context_data: Optional[dict[str, Any]] = Field(
        None,
        description="Session context data",
    )


class ChatSessionResponse(BaseModel):
    """Schema for chat session response."""
    
    id: UUID
    employer_id: UUID
    title: Optional[str]
    session_type: str
    context_data: Optional[dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    message_count: int = Field(default=0, description="Number of messages")
    last_message_at: Optional[datetime] = Field(None, description="Last message timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class ChatSessionWithMessagesResponse(BaseModel):
    """Schema for chat session with all messages."""
    
    id: UUID
    employer_id: UUID
    title: Optional[str]
    session_type: str
    context_data: Optional[dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class ChatSessionListResponse(BaseModel):
    """Schema for listing chat sessions."""
    
    items: List[ChatSessionResponse]
    total_count: int
    has_more: bool


# ==================== ACTION SCHEMAS ====================

class SendMessageRequest(BaseModel):
    """Schema for sending a message to a session."""
    
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User message content",
    )
    message_data: Optional[dict[str, Any]] = Field(
        None,
        description="Additional data (e.g., selected button value)",
    )


class SendMessageResponse(BaseModel):
    """Schema for send message response."""
    
    user_message: ChatMessageResponse
    bot_responses: List[ChatMessageResponse] = Field(
        default_factory=list,
        description="Bot responses (can be multiple messages)",
    )


class UpdateSessionContextRequest(BaseModel):
    """Schema for updating session context."""
    
    context_data: dict[str, Any] = Field(
        ...,
        description="Updated context data",
    )
    title: Optional[str] = Field(
        None,
        max_length=255,
        description="Updated title",
    )


class ExtractionCompleteRequest(BaseModel):
    """Schema for notifying that JD extraction is complete."""
    
    extracted_data: dict[str, Any] = Field(
        ...,
        description="Data extracted from job description",
        examples=[{
            "title": "Software Engineer",
            "description": "We are looking for...",
            "requirements": "5+ years experience...",
            "experience_min": 3,
            "experience_max": 5,
            "city": "Mumbai",
            "state": "Maharashtra",
            "country": "India",
        }],
    )


# ==================== GENERATION SCHEMAS ====================

class GenerateDescriptionRequest(BaseModel):
    """Schema for generating a job description from structured data."""
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Job title (required)",
    )
    requirements: Optional[str] = Field(
        None,
        max_length=5000,
        description="Skills/qualifications mentioned by user",
    )
    city: Optional[str] = Field(
        None,
        max_length=100,
        description="City name",
    )
    state: Optional[str] = Field(
        None,
        max_length=100,
        description="State/province",
    )
    country: Optional[str] = Field(
        None,
        max_length=100,
        description="Country",
    )
    work_type: Optional[str] = Field(
        None,
        pattern="^(remote|hybrid|onsite)$",
        description="Work type: remote, hybrid, or onsite",
    )
    salary_min: Optional[float] = Field(
        None,
        ge=0,
        description="Minimum salary",
    )
    salary_max: Optional[float] = Field(
        None,
        ge=0,
        description="Maximum salary",
    )
    currency: str = Field(
        default="INR",
        max_length=10,
        description="Salary currency: INR, USD, etc.",
    )
    experience_min: Optional[float] = Field(
        None,
        ge=0,
        le=99,
        description="Minimum years of experience",
    )
    experience_max: Optional[float] = Field(
        None,
        ge=0,
        le=99,
        description="Maximum years of experience",
    )
    shift_preference: Optional[str] = Field(
        None,
        description="Shift preference: day, night, flexible",
    )
    openings_count: int = Field(
        default=1,
        ge=1,
        description="Number of positions",
    )
    company_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Company name for personalization",
    )


class GenerateDescriptionResponse(BaseModel):
    """Schema for generated job description response."""
    
    description: str = Field(
        ...,
        description="Generated job description",
    )
    requirements: str = Field(
        ...,
        description="Generated requirements list",
    )
    summary: str = Field(
        ...,
        description="Short summary for listings",
    )
    success: bool = Field(
        ...,
        description="Whether LLM generation succeeded (false = fallback used)",
    )
    error: Optional[str] = Field(
        None,
        description="Error message if generation failed",
    )
