/**
 * Candidate Chat Types for AIVI Resume Builder Bot.
 *
 * Defines the structure for candidate chat sessions, messages,
 * and WebSocket communication protocol.
 *
 * Mirrors backend Pydantic schemas (candidate_chat domain).
 */

// ==================== MESSAGE CONSTANTS ====================

export type CandidateMessageRole = 'bot' | 'user';

export type CandidateMessageType =
  | 'text'
  | 'buttons'
  | 'resume_preview'
  | 'input_text'
  | 'input_number'
  | 'input_date'
  | 'input_textarea'
  | 'input_file'
  | 'multi_select'
  | 'select'
  | 'boolean'
  | 'loading'
  | 'error'
  | 'progress';

export type CandidateSessionType = 'resume_creation' | 'resume_upload' | 'general';
export type CandidateSessionStatus = 'active' | 'completed' | 'abandoned';

// ==================== CHAT BUTTON ====================

export interface CandidateChatButton {
  id: string;
  label: string;
  description?: string;
  variant?: 'primary' | 'secondary' | 'outline';
}

// ==================== CHAT MESSAGE ====================

export interface CandidateChatMessage {
  id: string;
  session_id: string;
  role: CandidateMessageRole;
  content: string;
  message_type: CandidateMessageType;
  message_data?: {
    buttons?: CandidateChatButton[];
    question_key?: string;
    options?: any[];
    validation?: Record<string, any>;
    is_required?: boolean;
    progress?: {
      current: number;
      total: number;
      percentage: number;
    };
    resume_data?: Record<string, any>;
    summary?: Record<string, any>;
    resume_id?: string;
    version?: number;
    file_url?: string;
    accept?: string;
    max_size_mb?: number;
    error?: string;
    status?: string;
    extracted_count?: number;
    missing_count?: number;
    confidence?: number;
    percentage?: number;
    [key: string]: any;
  };
  created_at: string;
}

// ==================== CHAT SESSION ====================

export interface CandidateChatSession {
  id: string;
  candidate_id: string;
  title?: string;
  session_type: CandidateSessionType;
  session_status: CandidateSessionStatus;
  context_data?: {
    step?: string;
    method?: string;
    role_id?: string;
    role_name?: string;
    job_type?: string;
    collected_data?: Record<string, any>;
    answered_keys?: string[];
    resume_id?: string;
    current_question_key?: string;
    [key: string]: any;
  };
  resume_id?: string;
  is_active: boolean;
  message_count?: number;
  created_at: string;
  updated_at: string;
}

// ==================== API REQUESTS ====================

export interface CreateCandidateChatSessionRequest {
  candidate_id: string;
  session_type?: CandidateSessionType;
}

export interface CandidateSendMessageRequest {
  content: string;
  message_type?: string;
  message_data?: Record<string, any>;
}

// ==================== API RESPONSES ====================

export interface CandidateChatSessionWithMessages extends CandidateChatSession {
  messages: CandidateChatMessage[];
}

export interface CandidateSendMessageResponse {
  user_message: CandidateChatMessage;
  bot_messages: CandidateChatMessage[];
  session: CandidateChatSession;
}

export interface CandidateChatSessionListResponse {
  items: CandidateChatSession[];
  total_count: number;
  has_more: boolean;
}

// ==================== WEBSOCKET PROTOCOL ====================

// Client → Server
export interface WSClientMessage {
  type: 'message' | 'ping';
  content?: string;
  message_type?: string;
  message_data?: Record<string, any>;
}

// Server → Client
export type WSServerMessage =
  | WSConnectedMessage
  | WSPongMessage
  | WSTypingMessage
  | WSUserMessageAckMessage
  | WSBotMessage
  | WSSessionUpdateMessage
  | WSErrorMessage;

export interface WSConnectedMessage {
  type: 'connected';
  session_id: string;
  candidate_id: string;
  timestamp: string;
}

export interface WSPongMessage {
  type: 'pong';
  timestamp: string;
}

export interface WSTypingMessage {
  type: 'typing';
  is_typing: boolean;
}

export interface WSUserMessageAckMessage {
  type: 'user_message_ack';
  message: CandidateChatMessage;
}

export interface WSBotMessage {
  type: 'bot_message';
  message: CandidateChatMessage;
}

export interface WSSessionUpdateMessage {
  type: 'session_update';
  session: CandidateChatSession;
}

export interface WSErrorMessage {
  type: 'error';
  error: string;
  code: string;
}
