import React, { useState, useEffect, useRef } from 'react';
import {
  Shield,
  Send,
  X,
  Trash2,
  Sparkles,
  RefreshCw,
  HardDrive,
  FileWarning,
  Flame,
  CornerDownLeft,
} from 'lucide-react';
import ChatMessage, { ChatMessageType } from './ChatMessage';
import { advisorAPI } from '../services/api';
import { getLocalAdvisorAdvice } from '../services/advisorFallback';

const STORAGE_KEY_MESSAGES = 'zt_advisor_chat_history';
const STORAGE_KEY_IS_OPEN = 'zt_advisor_chat_is_open';

const INITIAL_MESSAGE_CONTENT =
  "Hi! I'm the ZeroTrace AI Recovery Advisor. Tell me what happened to your storage device and I'll suggest the safest recovery approach.";

const INITIAL_WELCOME_MESSAGE: ChatMessageType = {
  id: 'welcome-initial',
  role: 'assistant',
  content: INITIAL_MESSAGE_CONTENT,
  timestamp: Date.now(),
};

const QUICK_PROMPTS = [
  {
    id: 'ssd',
    label: 'Accidental SSD Deletion',
    query: 'Accidental SSD Deletion: I accidentally deleted files on an SSD. What is the safest recovery procedure and risk level?',
    icon: HardDrive,
  },
  {
    id: 'usb',
    label: 'Formatted USB (FAT32)',
    query: 'Formatted USB (FAT32): My USB flash drive was formatted with FAT32. How can I recover the lost data safely?',
    icon: RefreshCw,
  },
  {
    id: 'raw',
    label: 'Corrupted RAW Partition',
    query: 'Corrupted RAW Partition: The partition table is corrupted and showing as RAW. What should I do to prevent data loss?',
    icon: FileWarning,
  },
  {
    id: 'clicking',
    label: 'Clicking Hard Drive',
    query: 'Clicking Hard Drive: My mechanical hard drive is clicking and making unusual noises. What is the forensic protocol?',
    icon: Flame,
  },
];

export const RecoveryAdvisorChat: React.FC = () => {
  const [isOpen, setIsOpen] = useState<boolean>(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY_IS_OPEN);
      return stored ? JSON.parse(stored) : false;
    } catch {
      return false;
    }
  });

  const [messages, setMessages] = useState<ChatMessageType[]>(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY_MESSAGES);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (e) {
      console.warn('Failed to parse chat messages from sessionStorage', e);
    }
    return [INITIAL_WELCOME_MESSAGE];
  });

  const [inputVal, setInputVal] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showQuickPrompts, setShowQuickPrompts] = useState<boolean>(() => {
    return messages.length <= 1;
  });

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  // Sync open state to sessionStorage
  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY_IS_OPEN, JSON.stringify(isOpen));
    } catch (e) {
      console.warn('Failed to save open state to sessionStorage', e);
    }
  }, [isOpen]);

  // Sync messages to sessionStorage
  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY_MESSAGES, JSON.stringify(messages));
    } catch (e) {
      console.warn('Failed to save messages to sessionStorage', e);
    }
  }, [messages]);

  // Listen for custom open event dispatched from anywhere in the application
  useEffect(() => {
    const handleOpenAdvisor = () => {
      setIsOpen(true);
    };

    window.addEventListener('zt-open-advisor', handleOpenAdvisor);
    return () => {
      window.removeEventListener('zt-open-advisor', handleOpenAdvisor);
    };
  }, []);

  // Auto-scroll to bottom when messages or loading state change
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading, isOpen]);

  // Auto-focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 150);
    }
  }, [isOpen]);

  const toggleChat = () => {
    setIsOpen((prev) => !prev);
  };

  const handleClearChat = () => {
    const resetMessages: ChatMessageType[] = [
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: INITIAL_MESSAGE_CONTENT,
        timestamp: Date.now(),
      },
    ];
    setMessages(resetMessages);
    setShowQuickPrompts(true);
    setInputVal('');
    try {
      sessionStorage.setItem(STORAGE_KEY_MESSAGES, JSON.stringify(resetMessages));
    } catch (e) {
      console.warn('Failed to clear sessionStorage', e);
    }
  };

  const sendMessage = async (text: string, customDisplayPrompt?: string) => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    const userMessage: ChatMessageType = {
      id: `user-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      role: 'user',
      content: customDisplayPrompt || trimmed,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputVal('');
    setIsLoading(true);

    try {
      // 1. Attempt to query backend API first
      let aiContent = '';
      let aiWarnings: string[] = [];
      let aiRiskLevel: 'LOW' | 'MEDIUM' | 'CRITICAL' | undefined = undefined;
      let aiActionType: string | undefined = undefined;

      try {
        const response = await advisorAPI.sendChatMessage(trimmed);
        if (response && response.data) {
          aiContent = response.data.answer;
          aiWarnings = response.data.related_warnings || [];
          aiActionType = response.data.suggested_action || undefined;
          
          if (aiContent.toLowerCase().includes('critical') || aiContent.toLowerCase().includes('clicking')) {
            aiRiskLevel = 'CRITICAL';
          } else if (aiContent.toLowerCase().includes('medium') || aiContent.toLowerCase().includes('trim')) {
            aiRiskLevel = 'MEDIUM';
          } else {
            aiRiskLevel = 'LOW';
          }
        }
      } catch (apiError) {
        // Backend unavailable or network error: cleanly use local fallback advisor
        console.info('Backend advisor API unreachable, utilizing built-in ZeroTrace fallback engine.');
        const fallback = getLocalAdvisorAdvice(trimmed);
        aiContent = fallback.answer;
        aiWarnings = fallback.warnings;
        aiRiskLevel = fallback.riskLevel;
        aiActionType = fallback.actionType;
      }

      if (!aiContent) {
        const fallback = getLocalAdvisorAdvice(trimmed);
        aiContent = fallback.answer;
        aiWarnings = fallback.warnings;
        aiRiskLevel = fallback.riskLevel;
        aiActionType = fallback.actionType;
      }

      // Small natural processing pause for smooth UI feel
      await new Promise((res) => setTimeout(res, 400));

      const assistantMessage: ChatMessageType = {
        id: `ai-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
        role: 'assistant',
        content: aiContent,
        timestamp: Date.now(),
        warnings: aiWarnings,
        riskLevel: aiRiskLevel,
        actionType: aiActionType,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: unknown) {
      console.error('Advisor processing error:', err);
      const errorMessage: ChatMessageType = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content:
          'A system error occurred while generating recommendations. As a safe standard procedure: power off the device, create a forensic image using a hardware write-blocker, and never write back onto the original drive.',
        timestamp: Date.now(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePromptClick = (prompt: (typeof QUICK_PROMPTS)[0]) => {
    // Automatically adds as user message and triggers advice flow immediately
    sendMessage(prompt.query, prompt.label);
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputVal);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputVal);
    }
  };

  const handleActionClick = (actionType: string) => {
    window.dispatchEvent(
      new CustomEvent('zt-station-action', {
        detail: {
          action: actionType,
          timestamp: Date.now(),
        },
      })
    );
  };

  return (
    <>
      {/* ── Fixed Floating Trigger Button ──────────────────────────────────── */}
      <button
        type="button"
        onClick={toggleChat}
        aria-label="Toggle AI Recovery Advisor chat"
        className="fixed bottom-5 right-5 z-50 flex items-center gap-2.5 px-4 py-3 rounded-full bg-gradient-to-r from-[#181717] via-[#201e1d] to-[#181717] text-[#f4efe7] border border-cyan-500/50 shadow-[0_0_20px_rgba(6,182,212,0.25)] hover:shadow-[0_0_30px_rgba(6,182,212,0.45)] hover:border-cyan-400 active:scale-95 transition-all duration-300 group cursor-pointer focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-[#181717]"
      >
        <div className="relative flex items-center justify-center">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 via-teal-500 to-emerald-600 flex items-center justify-center shadow-inner group-hover:scale-110 transition-transform duration-300">
            <Shield className="w-4 h-4 text-white animate-pulse" />
          </div>
          <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full ring-2 ring-[#181717] animate-ping" />
          <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full ring-2 ring-[#181717]" />
        </div>
        <span className="text-sm font-semibold tracking-wide bg-gradient-to-r from-cyan-300 via-emerald-200 to-white bg-clip-text text-transparent group-hover:brightness-110">
          AI Recovery Advisor
        </span>
      </button>

      {/* ── Floating Chat Window Panel ────────────────────────────────────── */}
      {isOpen && (
        <div
          role="dialog"
          aria-label="AI Recovery Advisor Chat Window"
          className="fixed bottom-20 right-3 sm:right-6 z-50 w-[calc(100vw-24px)] sm:w-[410px] max-w-[430px] h-[580px] max-h-[calc(100vh-100px)] flex flex-col rounded-2xl bg-[#181717]/95 backdrop-blur-xl border border-cyan-500/30 shadow-[0_10px_40px_rgba(0,0,0,0.7),0_0_25px_rgba(6,182,212,0.18)] overflow-hidden transition-all duration-300 animate-in fade-in slide-in-from-bottom-5"
        >
          {/* ── Chat Header ─────────────────────────────────────────────── */}
          <div className="flex items-center justify-between px-4 py-3.5 bg-gradient-to-r from-[#201e1d] to-[#1a1818] border-b border-cyan-500/20 flex-shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-emerald-600 flex items-center justify-center shadow-md ring-1 ring-cyan-400/40">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <div>
                <h2 className="text-sm font-bold tracking-wide text-[#f4efe7] flex items-center gap-1.5 leading-none">
                  AI Recovery Advisor
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                </h2>
                <div className="flex items-center gap-1.5 mt-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_6px_#34d399]" />
                  <span className="text-[11px] text-emerald-300 font-medium">Online</span>
                  <span className="text-[10px] text-stone-500">• Forensic Mode</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={handleClearChat}
                title="Clear chat history"
                aria-label="Clear chat history"
                className="p-1.5 rounded-lg text-stone-400 hover:text-stone-200 hover:bg-white/5 transition-colors cursor-pointer focus:outline-none focus:ring-1 focus:ring-cyan-500"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={toggleChat}
                title="Close Advisor"
                aria-label="Close Advisor"
                className="p-1.5 rounded-lg text-stone-400 hover:text-stone-200 hover:bg-white/5 transition-colors cursor-pointer focus:outline-none focus:ring-1 focus:ring-cyan-500"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* ── Scrollable Message History Area ─────────────────────────── */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-2 scroll-smooth">
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                onActionClick={handleActionClick}
              />
            ))}

            {/* Quick Prompt Suggestion Chips */}
            {showQuickPrompts && (
              <div className="pt-2 pb-1">
                <p className="text-[11px] font-semibold text-stone-400 uppercase tracking-wider mb-2 px-0.5">
                  Common Recovery Scenarios:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {QUICK_PROMPTS.map((item) => {
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => handlePromptClick(item)}
                        disabled={isLoading}
                        className="flex items-center gap-2 p-2.5 rounded-xl bg-[#232120]/80 hover:bg-cyan-950/40 border border-cyan-500/20 hover:border-cyan-400/60 text-left transition-all group cursor-pointer shadow-sm hover:shadow-[0_0_12px_rgba(6,182,212,0.2)] disabled:opacity-50 disabled:pointer-events-none"
                      >
                        <div className="w-6 h-6 rounded-md bg-cyan-500/10 group-hover:bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center flex-shrink-0 text-cyan-400 transition-colors">
                          <Icon className="w-3.5 h-3.5" />
                        </div>
                        <span className="text-xs font-medium text-stone-200 group-hover:text-cyan-200 leading-tight">
                          {item.label}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Loading / Typing Indicator */}
            {isLoading && (
              <div className="flex items-center gap-2 text-xs text-cyan-300/90 py-2 px-1 animate-pulse">
                <div className="w-6 h-6 rounded-lg bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center">
                  <Shield className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                </div>
                <span>AI Recovery Advisor is analyzing...</span>
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* ── Input Bar ───────────────────────────────────────────────── */}
          <form
            onSubmit={handleFormSubmit}
            className="p-3 bg-[#1d1b1a] border-t border-cyan-500/20 flex items-center gap-2 flex-shrink-0"
          >
            <div className="relative flex-1">
              <input
                ref={inputRef}
                type="text"
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Describe your data loss scenario..."
                disabled={isLoading}
                aria-label="Data loss scenario message"
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#282524] text-[#f4efe7] placeholder:text-stone-500 text-sm border border-stone-700/80 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none transition-all disabled:opacity-50"
              />
            </div>
            <button
              type="submit"
              disabled={!inputVal.trim() || isLoading}
              aria-label="Send Message"
              className="p-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white shadow-md hover:shadow-[0_0_15px_rgba(6,182,212,0.4)] transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-cyan-400"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}
    </>
  );
};

export default RecoveryAdvisorChat;
