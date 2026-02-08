/**
 * Candidate Chat WebSocket Manager.
 *
 * NOT USED IN CURRENT FLOW. Chat uses HTTP request–response (POST /sessions/:id/messages).
 * This module is kept for future use, e.g.:
 * - Streaming bot reply token-by-token (ChatGPT-style)
 * - Server-initiated push (e.g. "Resume ready" notification)
 *
 * When re-enabled: CandidateChatContainer will call setupWebSocket() after session create
 * and use sendMessage() when the socket is connected.
 *
 * Features (for when re-enabled):
 * - Auto-reconnection with exponential backoff
 * - Heartbeat (ping/pong) for connection health
 * - Message queue for offline resilience
 *
 * Pattern: Singleton per session (one connection per chat session).
 */

import type {
    CandidateChatMessage,
    CandidateChatSession,
    WSClientMessage,
    WSServerMessage,
} from '@/types';

// ==================== TYPES ====================

export type ConnectionStatus =
    | 'connecting'
    | 'connected'
    | 'reconnecting'
    | 'disconnected'
    | 'error';

export interface WSEventHandlers {
    onConnected?: (sessionId: string, candidateId: string) => void;
    onDisconnected?: (reason: string) => void;
    onReconnecting?: (attempt: number, maxAttempts: number) => void;
    onTyping?: (isTyping: boolean) => void;
    onUserMessageAck?: (message: CandidateChatMessage) => void;
    onBotMessage?: (message: CandidateChatMessage) => void;
    onSessionUpdate?: (session: CandidateChatSession) => void;
    onError?: (error: string, code: string) => void;
    onStatusChange?: (status: ConnectionStatus) => void;
}

export interface WSConnectionOptions {
    maxReconnectAttempts?: number;
    reconnectBaseDelay?: number; // ms
    reconnectMaxDelay?: number; // ms
    heartbeatInterval?: number; // ms
    heartbeatTimeout?: number; // ms
}

const DEFAULT_OPTIONS: Required<WSConnectionOptions> = {
    maxReconnectAttempts: 5,
    reconnectBaseDelay: 1000,
    reconnectMaxDelay: 16000,
    heartbeatInterval: 30000, // 30s
    heartbeatTimeout: 10000, // 10s
};

// ==================== WEBSOCKET MANAGER CLASS ====================

export class CandidateChatSocketManager {
    private ws: WebSocket | null = null;
    private url: string;
    private sessionId: string;
    private candidateId: string;
    private handlers: WSEventHandlers;
    private options: Required<WSConnectionOptions>;

    private status: ConnectionStatus = 'disconnected';
    private reconnectAttempts = 0;
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
    private heartbeatTimeoutTimer: ReturnType<typeof setTimeout> | null = null;
    private messageQueue: WSClientMessage[] = [];
    private isIntentionalClose = false;

    constructor(
        sessionId: string,
        candidateId: string,
        handlers: WSEventHandlers = {},
        options: WSConnectionOptions = {}
    ) {
        this.sessionId = sessionId;
        this.candidateId = candidateId;
        this.handlers = handlers;
        this.options = { ...DEFAULT_OPTIONS, ...options };

        // Build WebSocket URL
        // Build WebSocket URL from environment variable
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const wsProtocol = apiUrl.startsWith('https') ? 'wss:' : 'ws:';
        const wsHost = apiUrl.replace(/^https?:\/\//, '');
        const apiVersion = process.env.NEXT_PUBLIC_API_VERSION || 'v1';

        this.url = `${wsProtocol}//${wsHost}/api/${apiVersion}/candidate-chat/ws/${sessionId}?candidate_id=${candidateId}`;
    }

    // ==================== PUBLIC METHODS ====================

    /**
     * Connect to WebSocket server.
     */
    connect(): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            console.log('[WS] Already connected');
            return;
        }

        if (this.ws?.readyState === WebSocket.CONNECTING) {
            console.log('[WS] Connection in progress');
            return;
        }

        this.isIntentionalClose = false;
        this.setStatus('connecting');

        try {
            console.log('[WS] Connecting to:', this.url);
            this.ws = new WebSocket(this.url);
            this.setupEventListeners();
        } catch (error) {
            console.error('[WS] Failed to create WebSocket:', error);
            this.setStatus('error');
            this.scheduleReconnect();
        }
    }

    /**
     * Disconnect from WebSocket server.
     */
    disconnect(): void {
        this.isIntentionalClose = true;
        this.cleanup();
        this.setStatus('disconnected');
        this.handlers.onDisconnected?.('User disconnected');
    }

    /**
     * Send a chat message to the server.
     */
    sendMessage(
        content: string,
        messageType: string = 'text',
        messageData?: Record<string, any>
    ): void {
        const msg: WSClientMessage = {
            type: 'message',
            content,
            message_type: messageType,
            message_data: messageData,
        };

        if (this.status === 'connected' && this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(msg));
        } else {
            // Queue for later when reconnected
            console.log('[WS] Queueing message (not connected):', msg);
            this.messageQueue.push(msg);
        }
    }

    /**
     * Send a ping to keep connection alive.
     */
    sendPing(): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'ping' }));
        }
    }

    /**
     * Get current connection status.
     */
    getStatus(): ConnectionStatus {
        return this.status;
    }

    /**
     * Check if connected.
     */
    isConnected(): boolean {
        return this.status === 'connected' && this.ws?.readyState === WebSocket.OPEN;
    }

    // ==================== PRIVATE METHODS ====================

    private setupEventListeners(): void {
        if (!this.ws) return;

        this.ws.onopen = () => {
            console.log('[WS] Connected');
            this.reconnectAttempts = 0;
            this.startHeartbeat();
            // Don't set status to 'connected' yet - wait for server 'connected' message
        };

        this.ws.onmessage = (event) => {
            try {
                const data: WSServerMessage = JSON.parse(event.data);
                this.handleServerMessage(data);
            } catch (error) {
                console.error('[WS] Failed to parse message:', error);
            }
        };

        this.ws.onerror = (event) => {
            console.error('[WS] Error:', event);
            this.handlers.onError?.('WebSocket error', 'CONNECTION_ERROR');
        };

        this.ws.onclose = (event) => {
            console.log('[WS] Closed:', event.code, event.reason);
            this.stopHeartbeat();

            if (!this.isIntentionalClose) {
                this.setStatus('disconnected');
                this.handlers.onDisconnected?.(event.reason || 'Connection closed');
                this.scheduleReconnect();
            }
        };
    }

    private handleServerMessage(data: WSServerMessage): void {
        // Reset heartbeat timeout on any message
        this.resetHeartbeatTimeout();

        switch (data.type) {
            case 'connected':
                console.log('[WS] Server confirmed connection:', data.session_id);
                this.setStatus('connected');
                this.handlers.onConnected?.(data.session_id, data.candidate_id);
                this.flushMessageQueue();
                break;

            case 'pong':
                // Heartbeat response received
                console.log('[WS] Pong received');
                break;

            case 'typing':
                this.handlers.onTyping?.(data.is_typing);
                break;

            case 'user_message_ack':
                this.handlers.onUserMessageAck?.(data.message);
                break;

            case 'bot_message':
                this.handlers.onBotMessage?.(data.message);
                break;

            case 'session_update':
                this.handlers.onSessionUpdate?.(data.session);
                break;

            case 'error':
                console.error('[WS] Server error:', data.error, data.code);
                this.handlers.onError?.(data.error, data.code);
                break;

            default:
                console.warn('[WS] Unknown message type:', data);
        }
    }

    private setStatus(status: ConnectionStatus): void {
        if (this.status !== status) {
            this.status = status;
            this.handlers.onStatusChange?.(status);
        }
    }

    private scheduleReconnect(): void {
        if (this.isIntentionalClose) return;
        if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
            console.log('[WS] Max reconnect attempts reached');
            this.setStatus('error');
            this.handlers.onError?.(
                'Failed to reconnect after multiple attempts',
                'MAX_RECONNECT_REACHED'
            );
            return;
        }

        // Exponential backoff with jitter
        const delay = Math.min(
            this.options.reconnectBaseDelay * Math.pow(2, this.reconnectAttempts) +
            Math.random() * 1000,
            this.options.reconnectMaxDelay
        );

        this.reconnectAttempts++;
        console.log(
            `[WS] Scheduling reconnect attempt ${this.reconnectAttempts}/${this.options.maxReconnectAttempts} in ${delay}ms`
        );

        this.setStatus('reconnecting');
        this.handlers.onReconnecting?.(
            this.reconnectAttempts,
            this.options.maxReconnectAttempts
        );

        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, delay);
    }

    private startHeartbeat(): void {
        this.stopHeartbeat();
        this.heartbeatTimer = setInterval(() => {
            this.sendPing();
            this.setHeartbeatTimeout();
        }, this.options.heartbeatInterval);
    }

    private stopHeartbeat(): void {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
        this.resetHeartbeatTimeout();
    }

    private setHeartbeatTimeout(): void {
        this.resetHeartbeatTimeout();
        this.heartbeatTimeoutTimer = setTimeout(() => {
            console.warn('[WS] Heartbeat timeout - server not responding');
            this.ws?.close(4000, 'Heartbeat timeout');
        }, this.options.heartbeatTimeout);
    }

    private resetHeartbeatTimeout(): void {
        if (this.heartbeatTimeoutTimer) {
            clearTimeout(this.heartbeatTimeoutTimer);
            this.heartbeatTimeoutTimer = null;
        }
    }

    private flushMessageQueue(): void {
        if (this.messageQueue.length === 0) return;

        console.log(`[WS] Flushing ${this.messageQueue.length} queued messages`);
        while (this.messageQueue.length > 0) {
            const msg = this.messageQueue.shift();
            if (msg && this.ws?.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify(msg));
            }
        }
    }

    private cleanup(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        this.stopHeartbeat();

        if (this.ws) {
            this.ws.onopen = null;
            this.ws.onmessage = null;
            this.ws.onerror = null;
            this.ws.onclose = null;

            if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
                this.ws.close(1000, 'Client disconnecting');
            }
            this.ws = null;
        }
    }
}

// ==================== HOOK FOR REACT ====================

/**
 * Create a WebSocket manager instance.
 * Use this in useEffect for proper lifecycle management.
 *
 * Example:
 * ```tsx
 * useEffect(() => {
 *   const manager = createCandidateChatSocket(sessionId, candidateId, handlers);
 *   manager.connect();
 *   return () => manager.disconnect();
 * }, [sessionId, candidateId]);
 * ```
 */
export function createCandidateChatSocket(
    sessionId: string,
    candidateId: string,
    handlers: WSEventHandlers = {},
    options: WSConnectionOptions = {}
): CandidateChatSocketManager {
    return new CandidateChatSocketManager(sessionId, candidateId, handlers, options);
}
