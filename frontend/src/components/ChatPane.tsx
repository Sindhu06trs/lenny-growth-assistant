import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  PlusCircle,
  AlertCircle,
  Compass,
  History,
  Trash2,
  ChevronDown,
  X,
  MessageSquare,
  Loader2,
} from 'lucide-react';
import { ChatMessage, Session } from '../types/chat';
import { MessageBubble } from './MessageBubble';

interface ChatPaneProps {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  onNewChat: () => void;
  onOpenArtifact?: (artifactId: string) => void;
  isLoading?: boolean;
  sessions?: Session[];
  currentSessionId?: string | null;
  onSelectSession?: (sessionId: string) => void;
  onDeleteSession?: (sessionId: string) => void;
  errorMessage?: string | null;
  onDismissError?: () => void;
}

const SUGGESTED_PROMPTS = [
  {
    title: 'Customer Retention',
    prompt: 'How can an early-stage startup improve user retention?',
    category: 'Growth Strategy',
  },
  {
    title: 'Product Launch',
    prompt: 'What frameworks help orchestrate a successful self-serve product launch?',
    category: 'Product Management',
  },
  {
    title: 'Product-Market Fit',
    prompt: 'Summarize the core signals and metrics that indicate Product-Market Fit.',
    category: 'Foundations',
  },
  {
    title: 'Interactive Dashboard',
    prompt: 'Create an HTML dashboard showing customer retention strategies.',
    category: 'Artifact Demonstration',
  },
];

export const ChatPane: React.FC<ChatPaneProps> = ({
  messages,
  onSendMessage,
  onNewChat,
  onOpenArtifact,
  isLoading = false,
  sessions = [],
  currentSessionId,
  onSelectSession,
  onDeleteSession,
  errorMessage,
  onDismissError,
}) => {
  const [input, setInput] = useState('');
  const [inputError, setInputError] = useState<string | null>(null);
  const [isSessionMenuOpen, setIsSessionMenuOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Adjust textarea height dynamically
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (inputError) setInputError(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  };

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed) {
      setInputError('Please enter a message before sending.');
      return;
    }
    onSendMessage(trimmed);
    setInput('');
    setInputError(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const activeSession = sessions.find((s) => s.id === currentSessionId);

  return (
    <div className="flex flex-col h-full bg-dark-bg border-r border-dark-border relative">
      {/* Chat Pane Header Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-dark-border bg-dark-surface/80 backdrop-blur-md z-10 gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-2.5 h-2.5 rounded-full bg-brand-500 shrink-0" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300 shrink-0 hidden sm:block">
            Growth Chat
          </h2>

          {/* Session Switcher Popover */}
          <div className="relative">
            <button
              onClick={() => setIsSessionMenuOpen(!isSessionMenuOpen)}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-dark-card hover:bg-dark-hover border border-dark-border text-xs text-slate-300 hover:text-white transition-colors max-w-[180px] sm:max-w-[220px]"
              aria-label="Toggle sessions history"
              title="Switch or manage conversation sessions"
            >
              <History className="w-3.5 h-3.5 text-brand-400 shrink-0" />
              <span className="truncate text-xs font-medium">
                {activeSession ? activeSession.title : 'Active Session'}
              </span>
              <ChevronDown className="w-3 h-3 text-slate-400 shrink-0 ml-0.5" />
            </button>

            {isSessionMenuOpen && (
              <>
                <div
                  className="fixed inset-0 z-30"
                  onClick={() => setIsSessionMenuOpen(false)}
                />
                <div className="absolute left-0 mt-1.5 w-72 rounded-xl bg-dark-surface border border-dark-border shadow-2xl p-2 z-40 animate-in fade-in zoom-in-95 duration-100 max-h-80 overflow-y-auto">
                  <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-dark-border px-1">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      Saved Sessions ({sessions.length})
                    </span>
                    <button
                      onClick={() => {
                        setIsSessionMenuOpen(false);
                        onNewChat();
                      }}
                      className="text-[11px] text-brand-400 hover:text-brand-300 font-medium flex items-center gap-1"
                    >
                      <PlusCircle className="w-3 h-3" />
                      <span>New</span>
                    </button>
                  </div>

                  {sessions.length === 0 ? (
                    <div className="py-4 text-center text-xs text-slate-400">
                      No saved sessions found.
                    </div>
                  ) : (
                    <div className="space-y-1">
                      {sessions.map((s) => {
                        const isCurrent = s.id === currentSessionId;
                        return (
                          <div
                            key={s.id}
                            className={`group flex items-center justify-between px-2 py-1.5 rounded-lg text-xs transition-colors ${
                              isCurrent
                                ? 'bg-brand-500/15 border border-brand-500/30 text-white'
                                : 'hover:bg-dark-card border border-transparent text-slate-300'
                            }`}
                          >
                            <button
                              onClick={() => {
                                onSelectSession && onSelectSession(s.id);
                                setIsSessionMenuOpen(false);
                              }}
                              className="flex items-center gap-2 min-w-0 text-left flex-1"
                            >
                              <MessageSquare className="w-3.5 h-3.5 text-slate-400 group-hover:text-brand-400 shrink-0" />
                              <div className="truncate">
                                <div className="font-medium truncate">{s.title || 'Untitled Chat'}</div>
                                <div className="text-[10px] text-slate-400 font-mono">
                                  {s.message_count || 0} messages
                                </div>
                              </div>
                            </button>

                            {onDeleteSession && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onDeleteSession(s.id);
                                }}
                                className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 transition-all shrink-0 ml-1"
                                title="Delete session"
                                aria-label="Delete session"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        <button
          onClick={onNewChat}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-dark-card hover:bg-dark-hover border border-dark-border text-xs text-slate-300 hover:text-white transition-colors shrink-0"
          aria-label="Start a new chat session"
          title="Start a fresh conversation thread"
        >
          <PlusCircle className="w-3.5 h-3.5 text-brand-400" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="px-4 py-2 bg-rose-500/10 border-b border-rose-500/20 text-rose-300 text-xs flex items-center justify-between gap-2 z-10 animate-in fade-in duration-150">
          <div className="flex items-center gap-2 min-w-0">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span className="truncate">{errorMessage}</span>
          </div>
          {onDismissError && (
            <button
              onClick={onDismissError}
              className="p-1 rounded hover:bg-rose-500/20 text-rose-300"
              aria-label="Dismiss error"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}

      {/* Message Feed Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-2">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto py-12 px-4 animate-in fade-in duration-300">
            <div className="w-12 h-12 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 mb-4 shadow-lg shadow-brand-500/5">
              <Compass className="w-6 h-6" />
            </div>

            <h3 className="text-base font-semibold text-slate-100 mb-1">
              The Lenny Growth Assistant
            </h3>
            <p className="text-xs text-slate-400 mb-6 leading-relaxed">
              Ask strategic questions regarding product management, cohort retention, and growth loops.
              Connected directly to your configured AI model provider.
            </p>

            <div className="w-full space-y-2">
              <span className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase block mb-1">
                Suggested Prompts
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
                {SUGGESTED_PROMPTS.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => onSendMessage(item.prompt)}
                    className="p-2.5 rounded-xl bg-dark-surface hover:bg-dark-hover border border-dark-border hover:border-brand-500/40 transition-all group flex flex-col justify-between"
                  >
                    <span className="text-xs font-medium text-slate-200 group-hover:text-brand-300 transition-colors">
                      {item.title}
                    </span>
                    <span className="text-[11px] text-slate-400 line-clamp-2 mt-1">
                      {item.prompt}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                onOpenArtifact={onOpenArtifact}
              />
            ))}

            {/* Live Typing / Thinking Indicator */}
            {isLoading && (
              <div className="flex items-start gap-3 my-4">
                <div className="w-8 h-8 rounded-full bg-dark-card border border-dark-border flex items-center justify-center text-brand-400 shrink-0">
                  <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
                </div>
                <div className="rounded-2xl p-4 bg-dark-surface border border-dark-border rounded-tl-sm flex items-center gap-2">
                  <span className="text-xs text-slate-400">Assistant is thinking</span>
                  <span className="flex gap-1 items-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-dark-border bg-dark-surface/50 backdrop-blur-md">
        {inputError && (
          <div className="text-[11px] text-rose-400 mb-1.5 flex items-center gap-1">
            <AlertCircle className="w-3 h-3 shrink-0" />
            <span>{inputError}</span>
          </div>
        )}
        <div className="relative flex items-end rounded-xl bg-dark-card border border-dark-border focus-within:border-brand-500 focus-within:ring-1 focus-within:ring-brand-500 transition-all">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask about retention loops, product frameworks, or request an artifact..."
            rows={1}
            disabled={isLoading}
            className="w-full resize-none bg-transparent py-3 pl-3.5 pr-12 text-sm text-slate-100 placeholder-slate-500 focus:outline-none max-h-44 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="absolute right-2 bottom-2 p-2 rounded-lg bg-brand-600 text-white hover:bg-brand-500 disabled:opacity-40 disabled:hover:bg-brand-600 transition-colors shadow-sm"
            aria-label="Send message"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
        <div className="flex justify-between items-center mt-1.5 px-1 text-[10px] text-slate-400">
          <span>Press Enter to send, Shift+Enter for new line</span>
          <span>FastAPI + PostgreSQL Active</span>
        </div>
      </div>
    </div>
  );
};
