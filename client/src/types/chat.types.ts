/**
 * Chat Types for AIVI Conversational Bot.
 * 
 * Defines the structure for chat sessions, messages, and API communication.
 */

import type { BaseEntity } from './api.types';
import type { Currency, WorkType } from './job.types';

// Message Roles
export type MessageRole = 'bot' | 'user';

// Message Types for UI Rendering
export type MessageType =
    | 'text'
    | 'buttons'
    | 'job_preview'
    | 'input_text'
    | 'input_number'
    | 'input_textarea'
    | 'loading'
    | 'error';

// Session Types
export type SessionType = 'job_creation' | 'general';

// Button Option Structure
export interface ChatButton {
    id: string;
    label: string;
    value: string;
    variant?: 'primary' | 'secondary' | 'outline';
    icon?: string;
}

// Chat Message Entity
export interface ChatMessage {
    id: string;
    session_id: string;
    role: MessageRole;
    content: string;
    message_type: MessageType;
    message_data?: {
        buttons?: ChatButton[];
        step?: string;
        field?: string;
        placeholder?: string;
        action?: string;
        job_data?: Record<string, unknown>; // Used for job_preview
        [key: string]: unknown;
    };
    created_at: string;
}

// Chat Session Entity
export interface ChatSession extends BaseEntity {
    employer_id: string;
    title?: string;
    session_type: SessionType;
    context_data?: {
        step?: string;
        collected_data?: Record<string, unknown>;
        [key: string]: unknown;
    };
    is_active: boolean;
    message_count: number;
    last_message_at?: string;
}

// API REQUESTS
export interface CreateChatSessionRequest {
    employer_id: string;
    session_type?: SessionType;
    title?: string;
    /** When true, always create a new session (e.g. "New chat"). When false, return existing active session if any. */
    force_new?: boolean;
}

export interface SendMessageRequest {
    content: string;
    message_data?: Record<string, unknown>;
}

export interface GenerateDescriptionRequest {
    title: string;
    requirements?: string;
    city?: string;
    state?: string;
    country?: string;
    work_type?: WorkType;
    salary_min?: number;
    salary_max?: number;
    currency?: Currency;
    experience_min?: number;
    experience_max?: number;
    shift_preference?: string;
    openings_count?: number;
    company_name?: string;
}

// API RESPONSES
export interface ChatSessionWithMessages extends ChatSession {
    messages: ChatMessage[];
}

export interface SendMessageResponse {
    user_message: ChatMessage;
    bot_responses: ChatMessage[];
}

export interface ChatSessionListResponse {
    items: ChatSession[];
    total_count: number;
    has_more: boolean;
}

export interface GenerateDescriptionResponse {
    description: string;
    requirements: string;
    summary: string;
    success: boolean;
    error?: string;
}
