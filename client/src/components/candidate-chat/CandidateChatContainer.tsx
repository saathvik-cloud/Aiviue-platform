'use client';

/**
 * CandidateChatContainer - Main chat interface for the AIVI Resume Builder Bot.
 *
 * This is the primary component for the candidate chat experience.
 * Features:
 * - WebSocket-based real-time communication with REST fallback
 * - Optimistic UI updates for instant feedback
 * - Auto-reconnection with exponential backoff
 * - Session persistence (resume from where you left off)
 * - PDF upload with drag-and-drop
 * - Responsive design
 *
 * Pattern: Mirrors employer ChatContainer for consistency.
 */

import {
    useCandidateChatSession,
    useCandidateChatSessions,
    useCreateCandidateChatSession,
    useDeleteCandidateChatSession,
    useSendCandidateChatMessage,
} from '@/lib/hooks';
import { uploadResume } from '@/lib/supabase';
import {
    CandidateChatSocketManager,
    ConnectionStatus,
    createCandidateChatSocket,
} from '@/lib/websocket/candidate-chat-socket';
import { useCandidateAuthStore } from '@/stores';
import type { CandidateChatButton, CandidateChatMessage as CandidateChatMessageType } from '@/types';
import { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { CandidateChatHeader } from './CandidateChatHeader';
import { CandidateChatHistory } from './CandidateChatHistory';
import { CandidateChatInput } from './CandidateChatInput';
import { CandidateChatMessage } from './CandidateChatMessage';

type ViewMode = 'chat' | 'history';

/**
 * Static welcome messages shown immediately for better UX.
 * These match the backend welcome messages.
 */
const STATIC_WELCOME_MESSAGES: CandidateChatMessageType[] = [
    {
        id: 'welcome-1',
        session_id: '',
        role: 'bot',
        content: "Hi! I'm AIVI, your AI career assistant! 🎯",
        message_type: 'text',
        created_at: new Date().toISOString(),
    },
    {
        id: 'welcome-2',
        session_id: '',
        role: 'bot',
        content: "I'm here to help you build a professional resume.\n\nHow would you like to proceed?",
        message_type: 'buttons',
        message_data: {
            buttons: [
                { id: 'upload_resume', label: '📄 Upload My Resume', variant: 'primary' },
                { id: 'build_new', label: '✨ Build with AIVI', variant: 'secondary' },
            ],
        },
        created_at: new Date().toISOString(),
    },
];

/**
 * Progress messages shown during resume extraction.
 */
const EXTRACTION_PROGRESS_MESSAGES = [
    'Reading your resume... 📖',
    'Extracting your experience... 💼',
    'Parsing skills and education... 🎓',
    'Organizing the data... 📊',
    'Almost there... ✨',
];

export interface CandidateChatContainerProps {
    /** When 'upload', auto-selects "Upload PDF" so user goes straight to upload step */
    initialFlow?: 'upload';
}

/**
 * CandidateChatContainer
 */
export function CandidateChatContainer({ initialFlow }: CandidateChatContainerProps = {}) {
    const candidate = useCandidateAuthStore((state) => state.candidate);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const wsManagerRef = useRef<CandidateChatSocketManager | null>(null);
    const initialFlowSentRef = useRef(false);

    // View state
    const [viewMode, setViewMode] = useState<ViewMode>('chat');
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [localMessages, setLocalMessages] = useState<CandidateChatMessageType[]>(STATIC_WELCOME_MESSAGES);
    const [historyOffset, setHistoryOffset] = useState(0);
    const [isInitializing, setIsInitializing] = useState(true);
    const [isProcessing, setIsProcessing] = useState(false);
    const [progressMsgIndex, setProgressMsgIndex] = useState(0);
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
    const [isTyping, setIsTyping] = useState(false);

    // Ref to track session ID for async operations
    const sessionIdRef = useRef<string | null>(null);

    // API Hooks
    const createSession = useCreateCandidateChatSession();
    const sendMessageRest = useSendCandidateChatMessage();
    const deleteSession = useDeleteCandidateChatSession();

    const { data: sessions, isLoading: sessionsLoading, refetch: refetchSessions } = useCandidateChatSessions(
        candidate?.id,
        20,
        historyOffset
    );

    const { data: sessionData, isLoading: sessionLoading } = useCandidateChatSession(
        currentSessionId || undefined
    );

    // ==================== EFFECTS ====================

    // Scroll to bottom when messages change
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [localMessages, isTyping]);

    // Sync session messages to local state (only for the current session so "+ New Resume" isn't overwritten by stale data)
    useEffect(() => {
        if (
            !sessionData?.messages?.length ||
            !sessionData?.id ||
            sessionData.id !== currentSessionId
        ) {
            return;
        }
        setLocalMessages((prev) => {
            const hasStaticWelcome = prev.some((m) => m.id.startsWith('welcome-'));
            const backendHasOnlyWelcome =
                sessionData.messages.length <= 2 &&
                sessionData.messages.every(
                    (m) => m.message_type === 'text' || m.message_type === 'buttons'
                );

            if (hasStaticWelcome && backendHasOnlyWelcome) {
                return prev.map((m) => ({ ...m, session_id: sessionData.id }));
            }

            return sessionData.messages;
        });
    }, [sessionData?.messages, sessionData?.id, currentSessionId]);

    // Cycle through progress messages
    useEffect(() => {
        if (!isProcessing) {
            setProgressMsgIndex(0);
            return;
        }

        const interval = setInterval(() => {
            setProgressMsgIndex((prev) => (prev + 1) % EXTRACTION_PROGRESS_MESSAGES.length);
        }, 800);

        return () => clearInterval(interval);
    }, [isProcessing]);

    // Update loading message content when progress index changes
    useEffect(() => {
        if (!isProcessing) return;

        setLocalMessages((prev) => {
            const hasLoadingMessage = prev.some((msg) => msg.id.startsWith('processing-'));
            if (!hasLoadingMessage) return prev;

            return prev.map((msg) =>
                msg.id.startsWith('processing-')
                    ? { ...msg, content: EXTRACTION_PROGRESS_MESSAGES[progressMsgIndex] }
                    : msg
            );
        });
    }, [progressMsgIndex, isProcessing]);

    // ==================== WEBSOCKET SETUP ====================

    const setupWebSocket = useCallback((sessionId: string, candidateId: string) => {
        // Cleanup existing connection
        if (wsManagerRef.current) {
            wsManagerRef.current.disconnect();
        }

        const manager = createCandidateChatSocket(sessionId, candidateId, {
            onConnected: (sid, cid) => {
                console.log('[CandidateChat] WebSocket connected:', sid, cid);
                setConnectionStatus('connected');
            },
            onDisconnected: (reason) => {
                console.log('[CandidateChat] WebSocket disconnected:', reason);
                setConnectionStatus('disconnected');
            },
            onReconnecting: (attempt, max) => {
                console.log(`[CandidateChat] Reconnecting ${attempt}/${max}`);
                setConnectionStatus('reconnecting');
                // Reconnecting state shown in chat header only; no global toast so it doesn't appear on other pages.
            },
            onTyping: (typing) => {
                setIsTyping(typing);
            },
            onUserMessageAck: (message) => {
                // Replace optimistic message with server-confirmed message
                setLocalMessages((prev) => {
                    const filtered = prev.filter((m) => !m.id.startsWith('temp-'));
                    return [...filtered, message];
                });
            },
            onBotMessage: (message) => {
                // Remove loading message and add bot message
                setLocalMessages((prev) => {
                    const filtered = prev.filter((m) => !m.id.startsWith('loading-'));
                    return [...filtered, message];
                });
                setIsTyping(false);
            },
            onSessionUpdate: (session) => {
                console.log('[CandidateChat] Session updated:', session);
            },
            onError: (error, code) => {
                console.error('[CandidateChat] WebSocket error:', error, code);
                setConnectionStatus('error');
                if (code === 'MAX_RECONNECT_REACHED') {
                    toast.error('Connection lost. Please refresh the page.');
                }
            },
            onStatusChange: (status) => {
                setConnectionStatus(status);
            },
        });

        wsManagerRef.current = manager;
        manager.connect();
    }, []);

    // Cleanup WebSocket on unmount
    useEffect(() => {
        return () => {
            if (wsManagerRef.current) {
                wsManagerRef.current.disconnect();
            }
        };
    }, []);

    // ==================== HANDLERS ====================

    // Create a new chat session (on mount for first session, or when user clicks "+ New Resume" with force_new)
    const handleNewChat = useCallback(async (forceNew: boolean = false) => {
        if (!candidate?.id) {
            toast.error('Please login first');
            return;
        }

        console.log('[CandidateChat] Creating session for candidate:', candidate.id, 'force_new:', forceNew);

        // Reset so a new session truly starts from welcome (e.g. after "+ New Resume")
        initialFlowSentRef.current = false;

        // Show welcome messages immediately (optimistic UI)
        setLocalMessages(STATIC_WELCOME_MESSAGES);
        setViewMode('chat');
        setIsInitializing(true);

        // Disconnect existing WebSocket
        if (wsManagerRef.current) {
            wsManagerRef.current.disconnect();
        }

        try {
            const session = await createSession.mutateAsync({
                candidate_id: candidate.id,
                session_type: 'resume_creation',
                force_new: forceNew,
            });

            console.log('[CandidateChat] Session created:', session.id);

            setCurrentSessionId(session.id);
            sessionIdRef.current = session.id;

            // Update session_id on static messages
            setLocalMessages((prev) =>
                prev.map((m) => ({ ...m, session_id: session.id }))
            );

            // Setup WebSocket
            setupWebSocket(session.id, candidate.id);

            setIsInitializing(false);
        } catch (error) {
            console.error('[CandidateChat] Failed to create session:', error);
            toast.error('Failed to start chat. Please try again.');
            setIsInitializing(false);
        }
    }, [candidate?.id, createSession, setupWebSocket]);

    // Initialize first session on mount
    useEffect(() => {
        if (!currentSessionId && candidate?.id && !createSession.isPending) {
            handleNewChat();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [candidate?.id]);

    // When initialFlow=upload, auto-send "Upload PDF" choice once session is ready
    useEffect(() => {
        if (
            initialFlow !== 'upload' ||
            initialFlowSentRef.current ||
            !currentSessionId ||
            isInitializing
        ) {
            return;
        }
        initialFlowSentRef.current = true;
        handleSendMessage('📄 Upload My Resume', {
            value: 'upload_pdf',
            button_id: 'upload_pdf',
            message_type: 'button_click',
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [initialFlow, currentSessionId, isInitializing]);

    // Send a message (via WebSocket, with REST fallback)
    const handleSendMessage = async (content: string, messageData?: Record<string, any>) => {
        if (!currentSessionId || !candidate?.id) return;

        // Add optimistic user message
        const optimisticUserMsg: CandidateChatMessageType = {
            id: `temp-${Date.now()}`,
            session_id: currentSessionId,
            role: 'user',
            content,
            message_type: 'text',
            created_at: new Date().toISOString(),
        };

        const loadingMsg: CandidateChatMessageType = {
            id: `loading-${Date.now()}`,
            session_id: currentSessionId,
            role: 'bot',
            content: 'AIVI is thinking...',
            message_type: 'loading',
            created_at: new Date().toISOString(),
        };

        setLocalMessages((prev) => [...prev, optimisticUserMsg, loadingMsg]);
        setIsTyping(true);

        const messageType = messageData?.message_type || 'text';

        // Try WebSocket first
        if (wsManagerRef.current?.isConnected()) {
            wsManagerRef.current.sendMessage(content, messageType, messageData);
        } else {
            // REST fallback
            try {
                const response = await sendMessageRest.mutateAsync({
                    sessionId: currentSessionId,
                    data: {
                        content,
                        message_type: messageType,
                        message_data: messageData,
                    },
                });

                setLocalMessages((prev) => {
                    const filtered = prev.filter(
                        (m) => !m.id.startsWith('temp-') && !m.id.startsWith('loading-')
                    );
                    return [...filtered, response.user_message, ...response.bot_messages];
                });
            } catch (error) {
                console.error('[CandidateChat] Failed to send message:', error);
                toast.error('Failed to send message');
                setLocalMessages((prev) => prev.filter((m) => !m.id.startsWith('loading-')));
            } finally {
                setIsTyping(false);
            }
        }
    };

    // Handle button click
    const handleButtonClick = async (button: CandidateChatButton) => {
        // Wait for session if not ready
        if (!sessionIdRef.current && (createSession.isPending || isInitializing)) {
            let waitTime = 0;
            const checkInterval = 100;
            const maxWait = 5000;

            while (!sessionIdRef.current && waitTime < maxWait) {
                await new Promise((resolve) => setTimeout(resolve, checkInterval));
                waitTime += checkInterval;
            }

            if (!sessionIdRef.current) {
                toast.error('Session not ready. Please try again.');
                return;
            }
        }

        handleSendMessage(button.label, { value: button.id, button_id: button.id });
    };

    // Handle file upload
    const handleFileUpload = async (file: File) => {
        if (!currentSessionId || !candidate?.id) {
            toast.error('Session not ready');
            return;
        }

        // Show processing state
        setIsProcessing(true);
        setLocalMessages((prev) => [
            ...prev,
            {
                id: `temp-file-${Date.now()}`,
                session_id: currentSessionId,
                role: 'user',
                content: `Uploaded: ${file.name}`,
                message_type: 'text',
                created_at: new Date().toISOString(),
            },
            {
                id: `processing-${Date.now()}`,
                session_id: currentSessionId,
                role: 'bot',
                content: EXTRACTION_PROGRESS_MESSAGES[0],
                message_type: 'loading',
                created_at: new Date().toISOString(),
            },
        ]);

        try {
            // 1. Upload file to Supabase Storage
            const publicUrl = await uploadResume(file, currentSessionId);

            // 2. Send message to backend with the file URL
            // This will trigger the backend extraction pipeline
            handleSendMessage(`Uploaded: ${file.name}`, {
                file_url: publicUrl,
                question_key: 'resume_pdf',
                message_type: 'file_upload'
            });

            // Cleanup processing messages as handleSendMessage will add its own bot responses
            setLocalMessages((prev) => prev.filter((m) => !m.id.startsWith('processing-')));
        } catch (error) {
            console.error('[CandidateChat] File upload failed:', error);
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            toast.error(`Failed to upload file: ${errorMessage}`);
            setLocalMessages((prev) => prev.filter((m) => !m.id.startsWith('processing-')));
        } finally {
            setIsProcessing(false);
        }
    };

    // Handle retry
    const handleRetry = () => {
        // Remove error message and try again
        setLocalMessages((prev) => prev.filter((m) => m.message_type !== 'error'));
    };

    // Handle session selection from history
    const handleSelectSession = (sessionId: string) => {
        setCurrentSessionId(sessionId);
        sessionIdRef.current = sessionId;
        setViewMode('chat');

        // Setup WebSocket for this session
        if (candidate?.id) {
            setupWebSocket(sessionId, candidate.id);
        }
    };

    // Handle session deletion
    const handleDeleteSession = async (sessionId: string) => {
        if (!candidate?.id) return;

        try {
            await deleteSession.mutateAsync({
                sessionId,
                candidateId: candidate.id,
            });

            if (sessionId === currentSessionId) {
                handleNewChat();
            }

            refetchSessions();
            toast.success('Chat deleted');
        } catch (error) {
            console.error('[CandidateChat] Failed to delete session:', error);
            toast.error('Failed to delete chat');
        }
    };

    // Load more history
    const handleLoadMore = () => {
        setHistoryOffset((prev) => prev + 20);
    };

    // ==================== COMPUTED VALUES ====================

    // Filter out hidden messages
    const displayMessages = localMessages.filter(
        (msg) => msg.content && msg.content.trim() !== '' && !msg.message_data?.hidden
    );

    // Find last bot message for button display
    const lastBotMessage = [...displayMessages].reverse().find((m) => m.role === 'bot');

    // Determine input mode based on last bot message
    const getInputMode = (): 'text' | 'textarea' | 'number' | 'date' | 'file' | 'disabled' => {
        if (!lastBotMessage) return 'disabled';
        if (lastBotMessage.message_type === 'loading' || isProcessing) return 'disabled';
        if (lastBotMessage.message_type === 'buttons') return 'disabled';
        if (lastBotMessage.message_type === 'boolean') return 'disabled';
        if (lastBotMessage.message_type === 'resume_preview') return 'disabled';
        if (lastBotMessage.message_type === 'input_file') return 'file';
        if (lastBotMessage.message_type === 'input_textarea') return 'textarea';
        if (lastBotMessage.message_type === 'input_number') return 'number';
        if (lastBotMessage.message_type === 'input_date') return 'date';
        return 'text';
    };

    const inputMode = getInputMode();
    const inputPlaceholder = lastBotMessage?.message_data?.placeholder || 'Type your answer...';

    // ==================== RENDER ====================

    return (
        <div
            className="flex flex-col h-[calc(100vh-120px)] rounded-2xl overflow-hidden"
            style={{
                background: 'rgba(246, 239, 214, 0.97)',
                backdropFilter: 'blur(20px)',
                border: '1px solid var(--neutral-border)',
                boxShadow: '0 8px 32px rgba(13, 148, 136, 0.1)',
            }}
        >
            {/* Header */}
            <CandidateChatHeader
                title="AIVI Resume Builder"
                connectionStatus={connectionStatus}
                onNewChat={() => handleNewChat(true)}
                onToggleHistory={() => setViewMode(viewMode === 'chat' ? 'history' : 'chat')}
                showHistoryButton={true}
            />

            {/* Main Content */}
            {viewMode === 'history' ? (
                <CandidateChatHistory
                    sessions={sessions?.items || []}
                    isLoading={sessionsLoading}
                    hasMore={sessions?.has_more || false}
                    onSelectSession={handleSelectSession}
                    onDeleteSession={handleDeleteSession}
                    onLoadMore={handleLoadMore}
                    onBack={() => setViewMode('chat')}
                />
            ) : (
                <>
                    {/* Messages Area */}
                    <div className="flex-1 overflow-y-auto p-5 scrollbar-thin">
                        {sessionLoading && currentSessionId && !isInitializing ? (
                            <div className="flex items-center justify-center h-full">
                                <div className="text-center">
                                    <div
                                        className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-3 animate-pulse"
                                        style={{
                                            background:
                                                'linear-gradient(135deg, rgba(13, 148, 136, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%)',
                                        }}
                                    >
                                        <span className="text-2xl">🤖</span>
                                    </div>
                                    <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
                                        Loading conversation...
                                    </p>
                                </div>
                            </div>
                        ) : displayMessages.length === 0 ? (
                            <div className="flex items-center justify-center h-full">
                                <div className="text-center">
                                    <div
                                        className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
                                        style={{
                                            background:
                                                'linear-gradient(135deg, rgba(13, 148, 136, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%)',
                                        }}
                                    >
                                        <span className="text-3xl">📄</span>
                                    </div>
                                    <h3 className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                                        Ready to Build Your Resume?
                                    </h3>
                                    <p className="text-sm mb-4" style={{ color: 'var(--neutral-gray)' }}>
                                        Click below to start a conversation with AIVI
                                    </p>
                                    <button
                                        onClick={handleNewChat}
                                        className="px-6 py-2.5 rounded-xl font-medium text-white transition-all hover:scale-105"
                                        style={{ background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)' }}
                                    >
                                        🚀 Start Building
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <>
                                {displayMessages.map((msg, index) => {
                                    const isFirstInGroup =
                                        index === 0 || displayMessages[index - 1].role !== msg.role;
                                    return (
                                        <CandidateChatMessage
                                            key={msg.id}
                                            message={msg}
                                            isLatest={msg.id === lastBotMessage?.id}
                                            onButtonClick={handleButtonClick}
                                            onRetry={handleRetry}
                                            showAvatar={isFirstInGroup}
                                        />
                                    );
                                })}

                                {/* Typing indicator */}
                                {isTyping && (
                                    <div className="flex items-center gap-3 mb-4 animate-fade-in">
                                        <div
                                            className="w-9 h-9 rounded-xl flex items-center justify-center"
                                            style={{
                                                background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)',
                                            }}
                                        >
                                            <span className="text-base">🤖</span>
                                        </div>
                                        <div
                                            className="flex items-center gap-1 px-4 py-3 rounded-2xl rounded-tl-md"
                                            style={{
                                                background:
                                                    'linear-gradient(135deg, rgba(13, 148, 136, 0.05) 0%, rgba(124, 58, 237, 0.05) 100%)',
                                                border: '1px solid rgba(13, 148, 136, 0.1)',
                                            }}
                                        >
                                            <div
                                                className="w-1.5 h-1.5 rounded-full bg-teal-500 typing-dot"
                                                style={{ animationDelay: '0s' }}
                                            />
                                            <div
                                                className="w-1.5 h-1.5 rounded-full bg-teal-500 typing-dot"
                                                style={{ animationDelay: '0.2s' }}
                                            />
                                            <div
                                                className="w-1.5 h-1.5 rounded-full bg-teal-500 typing-dot"
                                                style={{ animationDelay: '0.4s' }}
                                            />
                                        </div>
                                    </div>
                                )}

                                <div ref={messagesEndRef} />
                            </>
                        )}
                    </div>

                    {/* Input */}
                    <CandidateChatInput
                        mode={inputMode}
                        placeholder={inputPlaceholder}
                        onSend={handleSendMessage}
                        onFileUpload={handleFileUpload}
                        disabled={createSession.isPending || isProcessing}
                        isLoading={sendMessageRest.isPending || isProcessing}
                    />
                </>
            )}
        </div>
    );
}
