import React, { useState, useEffect, useRef } from 'react';
import {
  MessageSquare,
  Send,
  X,
  Minimize2,
  Maximize2,
  Trash2,
  Shield,
  Zap,
  HelpCircle,
  AlertTriangle,
  RotateCw,
  HardDrive,
  Cpu,
  ChevronDown,
  Sparkles,
  Sliders,
  CheckCircle2,
} from 'lucide-react';
import {
  advisorAPI,
  AdvisorRecommendationRequest,
  AdvisorRecommendationResponse,
  AdvisorChatResponse,
  StorageMedium,
  FileSystemType,
  LossScenario,
} from '../services/api';
import RecommendationCard from './RecommendationCard';

// ── Session Storage Keys ─────────────────────────────────────────────
const STORAGE_KEY_MESSAGES = 'zt_advisor_chat_history';
const STORAGE_KEY_IS_OPEN = 'zt_advisor_chat_is_open';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: number;
  recommendation?: AdvisorRecommendationResponse & {
    target_extension?: string;
    storage_medium?: string;
    file_system?: string;
    loss_scenario?: string;
  };
  isError?: boolean;
  canRetry?: boolean;
  failedPrompt?: string;
  failedType?: 'chat' | 'recommend';
  failedPayload?: any;
}

const INITIAL_WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome-1',
  sender: 'assistant',
  text: 'Hello, Investigator. I am the **ZeroTrace Forensic Recovery Advisor**. I analyze storage conditions, file system structures, and data loss scenarios to recommend mathematically sound, non-destructive forensic recovery pathways.\n\nYou can ask me any question or run a live risk matrix assessment below.',
  timestamp: Date.now(),
};

// Preset quick scenario questions
const QUICK_SCENARIOS = [
  {
    label: 'SSD TRIM Deletion',
    prompt: 'I accidentally deleted important files on an SSD. What is the risk and recommended recovery method?',
    request: {
      storage_medium: 'SSD' as StorageMedium,
      file_system: 'NTFS' as FileSystemType,
      loss_scenario: 'DELETED' as LossScenario,
    },
  },
  {
    label: 'Formatted NTFS Drive',
    prompt: 'My external NTFS hard drive was quick-formatted. Can I recover the data?',
    request: {
      storage_medium: 'HDD' as StorageMedium,
      file_system: 'NTFS' as FileSystemType,
      loss_scenario: 'FORMATTED' as LossScenario,
    },
  },
  {
    label: 'Fragmented MP4 Video',
    prompt: 'How do I carve and reassemble fragmented MP4 videos from an SD card?',
    request: {
      storage_medium: 'SD_CARD' as StorageMedium,
      file_system: 'EXFAT' as FileSystemType,
      loss_scenario: 'DELETED' as LossScenario,
      target_extension: 'mp4',
    },
  },
  {
    label: 'Clicking / Failing HDD',
    prompt: 'My internal mechanical hard drive is making clicking noises and failing. What should I do?',
    request: {
      storage_medium: 'HDD' as StorageMedium,
      file_system: 'NTFS' as FileSystemType,
      loss_scenario: 'HARDWARE_ISSUE' as LossScenario,
    },
  },
];

export const RecoveryAdvisorChat: React.FC = () => {
  // Chat open/minimized state
  const [isOpen, setIsOpen] = useState<boolean>(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY_IS_OPEN);
      return stored ? JSON.parse(stored) : false;
    } catch {
      return false;
    }
  });

  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'matrix'>('chat');

  // Chat message history loaded from sessionStorage
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
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

  const [inputPrompt, setInputPrompt] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Guided Matrix Form State
  const [medium, setMedium] = useState<StorageMedium>('SSD');
  const [fs, setFs] = useState<FileSystemType>('NTFS');
  const [scenario, setScenario] = useState<LossScenario>('DELETED');
  const [extension, setExtension] = useState<string>('');

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  // Sync messages to sessionStorage
  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY_MESSAGES, JSON.stringify(messages));
    } catch (e) {
      console.warn('Failed to save chat to sessionStorage', e);
    }
  }, [messages]);

  // Sync isOpen to sessionStorage
  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY_IS_OPEN, JSON.stringify(isOpen));
    } catch (e) {
      /* ignore */
    }
  }, [isOpen]);

  // Scroll to bottom on new message
  useEffect(() => {
    if (isOpen && !isMinimized) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading, isOpen, isMinimized]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && !isMinimized && activeTab === 'chat') {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen, isMinimized, activeTab]);

  // Listen for global tool triggers to show feedback
  useEffect(() => {
    const handleCarveEvent = (e: any) => {
      const detail = e.detail || {};
      setStatusMessage(`🚀 Scalpel carving dispatched: ${detail.preset || 'Default'}`);
      setTimeout(() => setStatusMessage(null), 3500);
    };

    const handleImageEvent = (e: any) => {
      const detail = e.detail || {};
      setStatusMessage(`🛡️ Bitstream imaging dispatched: format=${detail.format || '.dd'}`);
      setTimeout(() => setStatusMessage(null), 3500);
    };

    const handleOpenAdvisor = () => {
      setIsOpen(true);
      setIsMinimized(false);
    };

    window.addEventListener('zt-launch-carver', handleCarveEvent);
    window.addEventListener('zt-image-disk', handleImageEvent);
    window.addEventListener('zt-open-advisor', handleOpenAdvisor);

    return () => {
      window.removeEventListener('zt-launch-carver', handleCarveEvent);
      window.removeEventListener('zt-image-disk', handleImageEvent);
      window.removeEventListener('zt-open-advisor', handleOpenAdvisor);
    };
  }, []);

  // Send a free-form chat question to /api/v1/advisor/chat
  const handleSendMessage = async (textToSend?: string) => {
    const question = (textToSend || inputPrompt).trim();
    if (!question || isLoading) return;

    setInputPrompt('');

    const userMsgId = `user-${Date.now()}`;
    const userMessage: ChatMessage = {
      id: userMsgId,
      sender: 'user',
      text: question,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await advisorAPI.sendChatMessage(question);
      const data: AdvisorChatResponse = response.data;

      // Check if this response should formulate an actionable recommendation card
      let recommendationObj: AdvisorRecommendationResponse | undefined;

      if (data.suggested_action) {
        // Synthesize an actionable recommendation card based on suggested_action and warnings
        const riskLevel = data.related_warnings.some((w) =>
          w.toLowerCase().includes('trim') || w.toLowerCase().includes('failing') || w.toLowerCase().includes('severe')
        )
          ? 'CRITICAL'
          : data.related_warnings.length > 0
          ? 'MEDIUM'
          : 'LOW';

        recommendationObj = {
          recommended_method: data.answer,
          risk_level: riskLevel,
          safety_warnings: data.related_warnings || [],
          action_type: data.suggested_action,
        };
      }

      const botMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: data.answer,
        timestamp: Date.now(),
        recommendation: recommendationObj,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err: any) {
      const isTimeout = err?.code === 'ECONNABORTED' || err?.message?.includes('timeout');
      const errorMsg = isTimeout
        ? 'Network timeout (10s): The forensic advisor server did not respond in time.'
        : 'Advisor Service Unavailable: Could not communicate with the FastAPI backend engine.';

      const errorMessage: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: `${errorMsg} Please verify that the backend is running at \`http://127.0.0.1:8000\`.`,
        timestamp: Date.now(),
        isError: true,
        canRetry: true,
        failedPrompt: question,
        failedType: 'chat',
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Submit the formal forensic matrix request to /api/v1/advisor/recommend
  const handleMatrixSubmit = async (customPayload?: AdvisorRecommendationRequest) => {
    const payload: AdvisorRecommendationRequest = customPayload || {
      storage_medium: medium,
      file_system: fs,
      loss_scenario: scenario,
      target_extension: extension.trim().replace(/^\./, '') || undefined,
    };

    const userSummary = `Forensic Analysis Request: Storage: ${payload.storage_medium} • FS: ${payload.file_system} • Loss: ${payload.loss_scenario}${
      payload.target_extension ? ` • Target: .${payload.target_extension}` : ''
    }`;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: userSummary,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setActiveTab('chat');
    setIsLoading(true);

    try {
      const response = await advisorAPI.getRecommendation(payload);
      const data: AdvisorRecommendationResponse = response.data;

      const botMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: `Analysis complete for **${payload.storage_medium} (${payload.file_system})** under scenario **${payload.loss_scenario}**. See the actionable recovery card below:`,
        timestamp: Date.now(),
        recommendation: {
          ...data,
          target_extension: payload.target_extension,
          storage_medium: payload.storage_medium,
          file_system: payload.file_system,
          loss_scenario: payload.loss_scenario,
        },
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err: any) {
      const isTimeout = err?.code === 'ECONNABORTED' || err?.message?.includes('timeout');
      const errorMsg = isTimeout
        ? 'Recommendation request timed out (10s).'
        : 'Failed to evaluate forensic rule matrix on backend.';

      const errorMessage: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: `${errorMsg} Please verify FastAPI is running at \`http://127.0.0.1:8000\`.`,
        timestamp: Date.now(),
        isError: true,
        canRetry: true,
        failedType: 'recommend',
        failedPayload: payload,
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Retry a failed message
  const handleRetry = (msg: ChatMessage) => {
    if (msg.failedType === 'recommend' && msg.failedPayload) {
      handleMatrixSubmit(msg.failedPayload);
    } else if (msg.failedPrompt) {
      handleSendMessage(msg.failedPrompt);
    }
  };

  // Clear chat history
  const handleClearHistory = () => {
    if (window.confirm('Clear active forensic consultation history?')) {
      const freshHistory = [INITIAL_WELCOME_MESSAGE];
      setMessages(freshHistory);
      sessionStorage.setItem(STORAGE_KEY_MESSAGES, JSON.stringify(freshHistory));
    }
  };

  return (
    <>
      {/* ── Status Notification Toast ─────────────────────── */}
      {statusMessage && (
        <div className="fixed bottom-20 right-6 z-50 p-3 bg-zinc-900 border border-cyan-500/50 text-cyan-300 text-xs rounded-xl shadow-2xl flex items-center gap-2 zt-animate-fade-in backdrop-blur-md">
          <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* ── Floating Launcher Trigger Button ──────────────── */}
      {!isOpen && (
        <button
          onClick={() => {
            setIsOpen(true);
            setIsMinimized(false);
          }}
          className="fixed bottom-6 right-6 z-40 group flex items-center gap-2.5 px-4 py-3 bg-[#111215] hover:bg-[#181a20] text-zinc-100 rounded-full border border-cyan-500/40 hover:border-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.25)] transition-all duration-300 cursor-pointer"
          title="Open ZeroTrace Forensic Recovery Advisor"
          aria-label="Open ZeroTrace Forensic Recovery Advisor"
        >
          <div className="relative flex items-center justify-center">
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-500 rounded-full animate-ping opacity-75" />
            <span className="relative w-2.5 h-2.5 bg-emerald-500 rounded-full" />
          </div>
          <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center text-white">
            <Shield className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-semibold tracking-wide text-zinc-100 group-hover:text-cyan-300 transition-colors">
            Forensic Advisor
          </span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
            AI MATRIX
          </span>
        </button>
      )}

      {/* ── Chat Modal / Drawer Widget ───────────────────── */}
      {isOpen && (
        <div
          className={`fixed bottom-6 right-6 z-50 w-[95vw] sm:w-[440px] md:w-[480px] bg-[#0c0d0f] border border-zinc-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden transition-all duration-300 font-sans ${
            isMinimized ? 'h-14' : 'h-[620px] max-h-[85vh]'
          }`}
          data-testid="recovery-advisor-widget"
        >
          {/* ── Widget Header ─────────────────────────────── */}
          <div className="h-14 px-4 bg-[#111215] border-b border-zinc-800/80 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-xs">
                <Shield className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <h3 className="text-xs font-bold text-zinc-100 tracking-wide">
                    Recovery Advisor
                  </h3>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                </div>
                <p className="text-[10px] font-mono text-zinc-400">
                  Forensic Rule Matrix & AI Assistant
                </p>
              </div>
            </div>

            {/* Window Controls */}
            <div className="flex items-center gap-1">
              <button
                onClick={handleClearHistory}
                className="p-1.5 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60 rounded-md transition-colors cursor-pointer"
                title="Clear Consultation History"
                aria-label="Clear Consultation History"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="p-1.5 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60 rounded-md transition-colors cursor-pointer"
                title={isMinimized ? 'Expand' : 'Minimize'}
                aria-label={isMinimized ? 'Expand' : 'Minimize'}
              >
                {isMinimized ? <Maximize2 className="w-3.5 h-3.5" /> : <Minimize2 className="w-3.5 h-3.5" />}
              </button>

              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 text-zinc-400 hover:text-rose-400 hover:bg-zinc-800/60 rounded-md transition-colors cursor-pointer"
                title="Close Advisor"
                aria-label="Close Advisor"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {!isMinimized && (
            <>
              {/* ── Sub-Navigation Tabs ─────────────────────── */}
              <div className="px-4 py-2 bg-[#0e1013] border-b border-zinc-800/60 flex items-center justify-between text-xs">
                <div className="flex items-center gap-1 bg-zinc-900/80 p-0.5 rounded-lg border border-zinc-800">
                  <button
                    onClick={() => setActiveTab('chat')}
                    className={`px-3 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer ${
                      activeTab === 'chat'
                        ? 'bg-zinc-800 text-cyan-300 shadow-xs'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    Forensic Chat
                  </button>
                  <button
                    onClick={() => setActiveTab('matrix')}
                    className={`px-3 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer flex items-center gap-1.5 ${
                      activeTab === 'matrix'
                        ? 'bg-zinc-800 text-cyan-300 shadow-xs'
                        : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    <Sliders className="w-3 h-3 text-cyan-400" />
                    <span>Scenario Matrix</span>
                  </button>
                </div>

                <span className="text-[10px] font-mono text-zinc-500">
                  SESSION STORED
                </span>
              </div>

              {/* ── Tab Content ────────────────────────────── */}
              {activeTab === 'matrix' ? (
                /* ── Guided Scenario Matrix Form ──────────── */
                <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-[#090a0c]">
                  <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/80 text-xs">
                    <p className="font-semibold text-zinc-200 mb-1 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                      Deterministic Forensic Matrix Evaluation
                    </p>
                    <p className="text-zinc-400 text-[11px] leading-relaxed">
                      Select your storage medium, file system, and loss condition to compute
                      the safest recovery methodology per NIST SP 800-88 and digital forensics standards.
                    </p>
                  </div>

                  {/* Storage Medium */}
                  <div>
                    <label className="block text-[11px] font-mono uppercase text-zinc-400 mb-1">
                      1. Storage Medium
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {(['SSD', 'HDD', 'USB', 'SD_CARD'] as StorageMedium[]).map((m) => (
                        <button
                          key={m}
                          type="button"
                          onClick={() => setMedium(m)}
                          className={`px-3 py-2 rounded-lg border text-xs font-medium text-left transition-all cursor-pointer ${
                            medium === m
                              ? 'bg-cyan-950/60 border-cyan-500 text-cyan-200 shadow-[0_0_8px_rgba(6,182,212,0.2)]'
                              : 'bg-zinc-900/60 border-zinc-800 text-zinc-300 hover:border-zinc-700'
                          }`}
                        >
                          {m === 'SSD' && '⚡ SSD (Solid State)'}
                          {m === 'HDD' && '💽 HDD (Mechanical)'}
                          {m === 'USB' && '🔌 USB Flash Drive'}
                          {m === 'SD_CARD' && '💳 SD / MicroSD Card'}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* File System */}
                  <div>
                    <label className="block text-[11px] font-mono uppercase text-zinc-400 mb-1">
                      2. File System Structure
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {(['NTFS', 'FAT32', 'EXFAT', 'EXT4', 'UNKNOWN'] as FileSystemType[]).map((f) => (
                        <button
                          key={f}
                          type="button"
                          onClick={() => setFs(f)}
                          className={`px-2.5 py-1.5 rounded-lg border text-xs font-mono transition-all cursor-pointer ${
                            fs === f
                              ? 'bg-cyan-950/60 border-cyan-500 text-cyan-200'
                              : 'bg-zinc-900/60 border-zinc-800 text-zinc-300 hover:border-zinc-700'
                          }`}
                        >
                          {f}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Loss Scenario */}
                  <div>
                    <label className="block text-[11px] font-mono uppercase text-zinc-400 mb-1">
                      3. Data Loss Scenario
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {(
                        [
                          ['DELETED', 'Accidental Deletion'],
                          ['FORMATTED', 'Volume Formatted'],
                          ['CORRUPTED', 'Corrupted / RAW'],
                          ['HARDWARE_ISSUE', 'Hardware / Clicking'],
                        ] as [LossScenario, string][]
                      ).map(([s, label]) => (
                        <button
                          key={s}
                          type="button"
                          onClick={() => setScenario(s)}
                          className={`px-3 py-2 rounded-lg border text-xs font-medium text-left transition-all cursor-pointer ${
                            scenario === s
                              ? 'bg-cyan-950/60 border-cyan-500 text-cyan-200'
                              : 'bg-zinc-900/60 border-zinc-800 text-zinc-300 hover:border-zinc-700'
                          }`}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Target Extension */}
                  <div>
                    <label className="block text-[11px] font-mono uppercase text-zinc-400 mb-1">
                      4. Target Extension (Optional)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. mp4, raw, jpg, docx, sqlite"
                      value={extension}
                      onChange={(e) => setExtension(e.target.value)}
                      className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-xs font-mono text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-cyan-500 transition-colors"
                    />
                  </div>

                  {/* Submit Button */}
                  <button
                    type="button"
                    onClick={() => handleMatrixSubmit()}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white rounded-lg text-xs font-semibold shadow-lg hover:shadow-cyan-500/20 transition-all cursor-pointer disabled:opacity-50"
                  >
                    <Zap className="w-3.5 h-3.5" />
                    <span>Run Forensic Decision Matrix</span>
                  </button>
                </div>
              ) : (
                /* ── Conversational Chat View ─────────────── */
                <div className="flex-1 flex flex-col min-h-0 bg-[#090a0c]">
                  {/* Messages Scroll Area */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-3.5 text-xs">
                    {/* Quick Scenario Pills */}
                    {messages.length <= 2 && (
                      <div className="p-3 bg-zinc-900/50 rounded-xl border border-zinc-800/80 mb-2">
                        <div className="text-[11px] font-mono uppercase text-zinc-400 mb-2 flex items-center gap-1.5">
                          <HelpCircle className="w-3 h-3 text-cyan-400" />
                          <span>Common Forensic Scenarios:</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {QUICK_SCENARIOS.map((sc, idx) => (
                            <button
                              key={idx}
                              onClick={() => {
                                handleMatrixSubmit(sc.request);
                              }}
                              className="px-2.5 py-1.5 rounded-lg bg-zinc-800/80 hover:bg-zinc-700 text-zinc-200 border border-zinc-700/60 text-[11px] transition-colors cursor-pointer hover:border-cyan-500/50"
                            >
                              {sc.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Messages Render */}
                    {messages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex flex-col ${
                          msg.sender === 'user' ? 'items-end' : 'items-start'
                        }`}
                      >
                        <div
                          className={`max-w-[90%] rounded-2xl p-3.5 ${
                            msg.sender === 'user'
                              ? 'bg-gradient-to-r from-cyan-900/50 to-blue-900/50 border border-cyan-500/30 text-zinc-100 rounded-br-xs'
                              : msg.isError
                              ? 'bg-rose-950/40 border border-rose-600/40 text-rose-200 rounded-bl-xs'
                              : 'bg-zinc-900/90 border border-zinc-800/80 text-zinc-200 rounded-bl-xs'
                          }`}
                        >
                          {/* Sender tag */}
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <span className="text-[10px] font-mono text-zinc-500 uppercase">
                              {msg.sender === 'user' ? 'You' : 'ZeroTrace Advisor'}
                            </span>
                            <span className="text-[10px] font-mono text-zinc-500">
                              {new Date(msg.timestamp).toLocaleTimeString([], {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </span>
                          </div>

                          {/* Message Body */}
                          <div className="whitespace-pre-line leading-relaxed text-xs">
                            {msg.text}
                          </div>

                          {/* Actionable Recommendation Card */}
                          {msg.recommendation && (
                            <RecommendationCard
                              recommendation={msg.recommendation}
                              onLaunchCarve={(params) => {
                                setStatusMessage(
                                  `🚀 Launched Scalpel Carving: ${params.preset || 'Default'}`
                                );
                                setTimeout(() => setStatusMessage(null), 3500);
                              }}
                              onImageDisk={() => {
                                setStatusMessage(
                                  '🛡️ Directing to Read-Only Disk Imager (.dd)...'
                                );
                                setTimeout(() => setStatusMessage(null), 3500);
                              }}
                              onRunMftScan={() => {
                                setStatusMessage('⚡ Initiating NTFS MFT Scanner...');
                                setTimeout(() => setStatusMessage(null), 3500);
                              }}
                            />
                          )}

                          {/* Retry Button if Error */}
                          {msg.isError && msg.canRetry && (
                            <div className="mt-2.5 pt-2 border-t border-rose-900/40 flex items-center justify-between">
                              <span className="text-[11px] text-rose-400 font-mono">
                                Request failed
                              </span>
                              <button
                                onClick={() => handleRetry(msg)}
                                className="flex items-center gap-1 px-2.5 py-1 bg-rose-900/60 hover:bg-rose-800 text-rose-200 rounded text-xs font-mono transition-colors cursor-pointer"
                              >
                                <RotateCw className="w-3 h-3" />
                                <span>Retry</span>
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}

                    {/* Loading Typing Indicator */}
                    {isLoading && (
                      <div className="flex items-start">
                        <div className="bg-zinc-900/80 border border-zinc-800 rounded-2xl rounded-bl-xs p-3 text-xs text-zinc-400 flex items-center gap-2">
                          <span className="flex gap-1">
                            <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                            <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                            <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" />
                          </span>
                          <span className="text-[11px] font-mono text-zinc-400">
                            Evaluating forensic matrix & risk vectors...
                          </span>
                        </div>
                      </div>
                    )}

                    <div ref={messagesEndRef} />
                  </div>

                  {/* ── Input Bar ────────────────────────────── */}
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleSendMessage();
                    }}
                    className="p-3 bg-[#111215] border-t border-zinc-800/80 flex items-center gap-2 shrink-0"
                  >
                    <input
                      ref={inputRef}
                      type="text"
                      placeholder="Ask a forensic question or loss scenario..."
                      value={inputPrompt}
                      onChange={(e) => setInputPrompt(e.target.value)}
                      disabled={isLoading}
                      className="flex-1 px-3.5 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-cyan-500 transition-colors disabled:opacity-50"
                    />
                    <button
                      type="submit"
                      disabled={isLoading || !inputPrompt.trim()}
                      className="p-2.5 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white rounded-xl transition-all shadow-md hover:shadow-cyan-500/20 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                      title="Send message"
                      aria-label="Send message"
                    >
                      <Send className="w-3.5 h-3.5" />
                    </button>
                  </form>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </>
  );
};

export default RecoveryAdvisorChat;
