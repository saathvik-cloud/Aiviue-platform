'use client';

import { ROUTES } from '@/constants';
import {
    CONVERSATION_STEPS,
    parseExperienceRange,
    parseSalaryRange,
    type ConversationStep
} from '@/lib/chat';
import {
    useChatSession,
    useChatSessions,
    useCreateChatSession,
    useCreateJob,
    useDeleteChatSession,
    useGenerateJobDescription,
    useSendChatMessage,
} from '@/lib/hooks';
import { useAuthStore } from '@/stores';
import type { ChatButton, ChatMessage as ChatMessageType, CreateJobRequest } from '@/types';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { ChatHeader } from './ChatHeader';
import { ChatHistory } from './ChatHistory';
import { ChatInput } from './ChatInput';
import { ChatMessage } from './ChatMessage';

type ViewMode = 'chat' | 'history';

/**
 * ChatContainer - Main chat interface component.
 * Manages conversation state, message display, and user interactions.
 */
export function ChatContainer() {
    const router = useRouter();
    const employer = useAuthStore((state) => state.employer);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // View state
    const [viewMode, setViewMode] = useState<ViewMode>('chat');
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [localMessages, setLocalMessages] = useState<ChatMessageType[]>([]);
    const [historyOffset, setHistoryOffset] = useState(0);

    // API Hooks
    const createSession = useCreateChatSession();
    const sendMessage = useSendChatMessage();
    const deleteSession = useDeleteChatSession();
    const generateDescription = useGenerateJobDescription();
    const createJob = useCreateJob();

    const { data: sessions, isLoading: sessionsLoading, refetch: refetchSessions } = useChatSessions(
        employer?.id,
        20,
        historyOffset
    );

    const { data: sessionData, isLoading: sessionLoading } = useChatSession(
        currentSessionId || undefined,
        employer?.id
    );

    // Scroll to bottom when messages change
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [localMessages, sessionData?.messages]);

    // Sync session messages to local state
    useEffect(() => {
        if (sessionData?.messages) {
            setLocalMessages(sessionData.messages);
        }
    }, [sessionData?.messages]);

    // Get current step from session context
    const currentStep = (sessionData?.context_data?.step || 'welcome') as ConversationStep;
    const collectedData = sessionData?.context_data?.collected_data || {};
    const stepConfig = CONVERSATION_STEPS[currentStep];

    // All messages to display (from API + any local optimistic updates)
    const displayMessages = localMessages;

    // Debug log
    console.log('[ChatContainer] displayMessages:', displayMessages.length, 'sessionLoading:', sessionLoading, 'createSession.isPending:', createSession.isPending);

    // Find the last bot message for button display and input detection
    const lastBotMessage = [...displayMessages].reverse().find(m => m.role === 'bot');

    // Check if we should show input - based on last bot message type from backend
    const showInput = lastBotMessage?.message_type === 'input_text' ||
        lastBotMessage?.message_type === 'input_textarea' ||
        lastBotMessage?.message_type === 'input_number';

    // Get input configuration from last bot message
    const inputPlaceholder = lastBotMessage?.message_data?.placeholder || 'Type your message...';
    const inputType = lastBotMessage?.message_type === 'input_textarea' ? 'textarea' :
        lastBotMessage?.message_type === 'input_number' ? 'number' : 'text';

    // Handle creating a new chat session
    const handleNewChat = useCallback(async () => {
        if (!employer?.id) {
            toast.error('Please login first');
            return;
        }

        console.log('[ChatContainer] Creating new session for employer:', employer.id);

        try {
            const session = await createSession.mutateAsync({
                employer_id: employer.id,
                session_type: 'job_creation',
            });

            console.log('[ChatContainer] Session created:', session);
            console.log('[ChatContainer] Session messages:', session.messages);
            console.log('[ChatContainer] Session messages length:', session.messages?.length);

            setCurrentSessionId(session.id);
            setLocalMessages(session.messages || []);
            setViewMode('chat');
        } catch (error) {
            console.error('[ChatContainer] Failed to create chat session:', error);
            toast.error('Failed to start chat. Please try again.');
        }
    }, [employer?.id, createSession]);

    // Initialize first session on mount
    useEffect(() => {
        if (!currentSessionId && employer?.id && !createSession.isPending) {
            handleNewChat();
        }
    }, [employer?.id]); // eslint-disable-line react-hooks/exhaustive-deps

    // Handle sending a message
    const handleSendMessage = async (content: string, buttonData?: Record<string, any>) => {
        if (!currentSessionId || !employer?.id) return;

        // Add optimistic user message
        const optimisticUserMsg: ChatMessageType = {
            id: `temp-${Date.now()}`,
            session_id: currentSessionId,
            role: 'user',
            content,
            message_type: 'text',
            created_at: new Date().toISOString(),
        };

        const loadingMsg: ChatMessageType = {
            id: `loading-${Date.now()}`,
            session_id: currentSessionId,
            role: 'bot',
            content: 'AIVI is thinking...',
            message_type: 'loading',
            created_at: new Date().toISOString(),
        };

        setLocalMessages(prev => [...prev, optimisticUserMsg, loadingMsg]);

        try {
            const response = await sendMessage.mutateAsync({
                sessionId: currentSessionId,
                employerId: employer.id,
                data: {
                    content,
                    message_data: buttonData,
                },
            });

            // Replace optimistic messages with real ones
            let newMessages = [...response.bot_responses];

            // Check if we need to generate job description (LLM call)
            const generatingResponse = response.bot_responses.find(
                msg => msg.message_type === 'loading' && msg.message_data?.action === 'generate_description'
            );

            if (generatingResponse) {
                // Trigger LLM generation
                await handleGenerateDescription();
                return; // handleGenerateDescription will update messages
            }

            setLocalMessages(prev => {
                const filtered = prev.filter(m => !m.id.startsWith('temp-') && !m.id.startsWith('loading-'));
                return [...filtered, response.user_message, ...newMessages];
            });
        } catch (error) {
            console.error('Failed to send message:', error);
            toast.error('Failed to send message');

            // Remove loading message on error
            setLocalMessages(prev => prev.filter(m => !m.id.startsWith('loading-')));
        }
    };

    // Handle LLM job description generation
    const handleGenerateDescription = async () => {
        if (!sessionData?.context_data?.collected_data || !currentSessionId || !employer?.id) {
            toast.error('No job data available');
            return;
        }

        const data = sessionData.context_data.collected_data;

        // Update loading message
        setLocalMessages(prev => {
            const filtered = prev.filter(m => !m.id.startsWith('loading-'));
            return [...filtered, {
                id: `generating-${Date.now()}`,
                session_id: currentSessionId!,
                role: 'bot' as const,
                content: 'Generating your job description with AI... ✨',
                message_type: 'loading' as const,
                created_at: new Date().toISOString(),
            }];
        });

        try {
            // Parse salary and experience ranges
            const salaryParts = data.salary_range?.split('-').map(Number) || [0, 0];
            const expParts = data.experience_range?.split('-').map(Number) || [0, 0];

            const result = await generateDescription.mutateAsync({
                title: data.title,
                requirements: data.requirements,
                city: data.city,
                state: data.state,
                country: data.country,
                work_type: data.work_type,
                salary_min: salaryParts[0] || undefined,
                salary_max: salaryParts[1] || undefined,
                currency: data.currency || 'INR',
                experience_min: expParts[0] || undefined,
                experience_max: expParts[1] || undefined,
                shift_preference: data.shift_preference,
                openings_count: parseInt(data.openings_count) || 1,
                company_name: employer?.company_name,
            });

            if (!result.success) {
                throw new Error(result.error || 'Failed to generate description');
            }

            // Create the preview message
            const previewMessage: ChatMessageType = {
                id: `preview-${Date.now()}`,
                session_id: currentSessionId!,
                role: 'bot',
                content: "Here's your job posting preview! 🎉",
                message_type: 'job_preview',
                message_data: {
                    job_data: {
                        ...data,
                        description: result.description,
                        requirements: result.requirements,
                        summary: result.summary,
                        generated_description: result.description,
                        generated_requirements: result.requirements,
                        salary_min: salaryParts[0],
                        salary_max: salaryParts[1],
                        experience_min: expParts[0],
                        experience_max: expParts[1],
                    },
                    step: 'preview',
                },
                created_at: new Date().toISOString(),
            };

            // Replace loading with preview
            setLocalMessages(prev => {
                const filtered = prev.filter(m => !m.id.startsWith('generating-') && !m.id.startsWith('loading-'));
                return [...filtered, previewMessage];
            });

            // Update session context with generated data
            // (The backend will handle this in a real scenario, but we're updating locally)

        } catch (error) {
            console.error('Failed to generate job description:', error);
            toast.error('Failed to generate job description. Please try again.');

            // Show error message
            setLocalMessages(prev => {
                const filtered = prev.filter(m => !m.id.startsWith('generating-') && !m.id.startsWith('loading-'));
                return [...filtered, {
                    id: `error-${Date.now()}`,
                    session_id: currentSessionId!,
                    role: 'bot' as const,
                    content: 'Sorry, I had trouble generating the job description. Please try again.',
                    message_type: 'error' as const,
                    created_at: new Date().toISOString(),
                }];
            });
        }
    };

    // Handle button click
    const handleButtonClick = (button: ChatButton) => {
        // Handle special "other" button - switch to text input
        if (button.value === 'other') {
            // The backend will handle this - just send the message
            handleSendMessage('other', { value: 'other', action: 'show_input' });
            return;
        }

        // Handle retry generation
        if (button.value === 'retry_generation') {
            handleGenerateDescription();
            return;
        }

        // Handle edit (going back to input state)
        if (button.value === 'edit_last_step') {
            const lastUserMsg = [...localMessages].reverse().find(m => m.role === 'user');
            if (lastUserMsg) {
                // Just remove the error message and the last loading message to let user type again
                setLocalMessages(prev => prev.filter(m => m.message_type !== 'error' && m.message_type !== 'loading'));
            }
            return;
        }

        handleSendMessage(button.label, { value: button.value });
    };

    // Handle job creation from preview
    const handleCreateJob = async (previewData?: any) => {
        // Use previewData if provided, otherwise fallback to session data
        const data = previewData || sessionData?.context_data?.collected_data;

        if (!data) {
            toast.error('No job data available');
            return;
        }

        // Parse salary and experience ranges
        const salaryRange = data.salary_range ? parseSalaryRange(data.salary_range) : { min: 0, max: 0 };
        const expRange = data.experience_range ? parseExperienceRange(data.experience_range) : { min: 0, max: 0 };

        // Ensure we have a valid description (minimum 10 chars as per backend validation)
        const finalDescription = (data.generated_description || data.description || '').trim();
        const finalRequirements = (data.generated_requirements || data.requirements || '').trim();

        if (finalDescription.length < 10) {
            toast.error('Job description is too short. Please add more details.');
            return;
        }

        const jobRequest: CreateJobRequest = {
            employer_id: employer!.id,
            title: data.title,
            description: finalDescription,
            requirements: finalRequirements,
            city: data.city,
            state: data.state,
            country: data.country,
            location: [data.city, data.state, data.country].filter(Boolean).join(', '),
            work_type: data.work_type as CreateJobRequest['work_type'],
            salary_range_min: data.salary_min || salaryRange.min || undefined,
            salary_range_max: data.salary_max || salaryRange.max || undefined,
            experience_min: data.experience_min || expRange.min || undefined,
            experience_max: data.experience_max || expRange.max || undefined,
            openings_count: parseInt(data.openings_count) || 1,
        };

        try {
            const job = await createJob.mutateAsync(jobRequest);
            toast.success('Job created successfully! 🎉');
            router.push(ROUTES.JOB_DETAILS(job.id));
        } catch (error) {
            console.error('Failed to create job:', error);
            toast.error('Failed to create job. Please check if all fields are valid.');
        }
    };

    // Handle session selection from history
    const handleSelectSession = (sessionId: string) => {
        setCurrentSessionId(sessionId);
        setViewMode('chat');
    };

    // Handle session deletion
    const handleDeleteSession = async (sessionId: string) => {
        if (!employer?.id) return;

        try {
            await deleteSession.mutateAsync({
                sessionId,
                employerId: employer.id,
            });

            // If deleted current session, create new one
            if (sessionId === currentSessionId) {
                handleNewChat();
            }

            refetchSessions();
            toast.success('Chat deleted');
        } catch (error) {
            console.error('Failed to delete session:', error);
            toast.error('Failed to delete chat');
        }
    };

    // Load more history
    const handleLoadMore = () => {
        setHistoryOffset(prev => prev + 20);
    };

    return (
        <div
            className="flex flex-col h-[calc(100vh-120px)] rounded-2xl overflow-hidden"
            style={{
                background: 'rgba(246, 239, 214, 0.97)',
                backdropFilter: 'blur(20px)',
                border: '1px solid var(--neutral-border)',
                boxShadow: '0 8px 32px rgba(124, 58, 237, 0.1)'
            }}
        >
            {/* Header */}
            <ChatHeader
                title="AIVI Assistant"
                onNewChat={handleNewChat}
                onToggleHistory={() => setViewMode(viewMode === 'chat' ? 'history' : 'chat')}
                showHistoryButton={true}
            />

            {/* Main Content */}
            {viewMode === 'history' ? (
                <ChatHistory
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
                        {(sessionLoading || createSession.isPending) ? (
                            <div className="flex items-center justify-center h-full">
                                <div className="text-center">
                                    <div
                                        className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-3 animate-pulse"
                                        style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)' }}
                                    >
                                        <span className="text-2xl">🤖</span>
                                    </div>
                                    <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
                                        {createSession.isPending ? 'Starting conversation...' : 'Loading conversation...'}
                                    </p>
                                </div>
                            </div>
                        ) : displayMessages.length === 0 ? (
                            <div className="flex items-center justify-center h-full">
                                <div className="text-center">
                                    <div
                                        className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
                                        style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)' }}
                                    >
                                        <span className="text-3xl">💬</span>
                                    </div>
                                    <h3 className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                                        Ready to Create a Job?
                                    </h3>
                                    <p className="text-sm mb-4" style={{ color: 'var(--neutral-gray)' }}>
                                        Click the button below to start a conversation with AIVI
                                    </p>
                                    <button
                                        onClick={handleNewChat}
                                        className="px-6 py-2.5 rounded-xl font-medium text-white transition-all hover:scale-105"
                                        style={{ background: 'var(--gradient-primary)' }}
                                    >
                                        🚀 Start Conversation
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <>
                                {displayMessages.map((msg, index) => {
                                    const isFirstInGroup = index === 0 || displayMessages[index - 1].role !== msg.role;
                                    return (
                                        <ChatMessage
                                            key={msg.id}
                                            message={msg}
                                            isLatest={msg.id === lastBotMessage?.id}
                                            onButtonClick={handleButtonClick}
                                            onCreateJob={msg.message_type === 'job_preview' ? handleCreateJob : undefined}
                                            onEditJob={msg.message_type === 'job_preview' ? () => toast.info('Edit feature coming soon!') : undefined}
                                            showAvatar={isFirstInGroup}
                                        />
                                    );
                                })}
                                <div ref={messagesEndRef} />
                            </>
                        )}
                    </div>

                    {/* Input Area */}
                    {showInput && (
                        <ChatInput
                            onSend={handleSendMessage}
                            placeholder={inputPlaceholder}
                            inputType={inputType}
                            disabled={sendMessage.isPending || generateDescription.isPending}
                            isLoading={sendMessage.isPending || generateDescription.isPending}
                            minLength={inputType === 'textarea' ? 10 : 3}
                        />
                    )}
                </>
            )}
        </div>
    );
}
