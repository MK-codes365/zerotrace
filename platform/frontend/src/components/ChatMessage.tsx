import React from 'react';
import { Shield, User, AlertTriangle, AlertCircle, CheckCircle2, Terminal } from 'lucide-react';

export type ChatMessageType = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date | number;
  warnings?: string[];
  riskLevel?: 'LOW' | 'MEDIUM' | 'CRITICAL';
  actionType?: string;
  isError?: boolean;
};

interface ChatMessageProps {
  message: ChatMessageType;
  onActionClick?: (actionType: string) => void;
}

const formatTimestamp = (timestamp?: Date | number): string => {
  if (!timestamp) return '';
  const date = typeof timestamp === 'number' ? new Date(timestamp) : timestamp;
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onActionClick }) => {
  const isUser = message.role === 'user';
  const timeStr = formatTimestamp(message.timestamp);

  // Parse markdown-style bold (**text**) and bullet lists for clean rendering
  const renderFormattedContent = (text: string) => {
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      // Check if line is a bullet item
      const isBullet = line.trim().startsWith('- ') || line.trim().startsWith('• ');
      const content = isBullet ? line.trim().substring(2) : line;

      // Simple parser for **bold** text
      const parts = content.split(/(\*\*[^*]+\*\*)/g);
      const formattedParts = parts.map((part, pIdx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={pIdx} className="font-semibold text-cyan-300">
              {part.slice(2, -2)}
            </strong>
          );
        }
        return part;
      });

      if (isBullet) {
        return (
          <li key={idx} className="ml-4 list-disc text-sm text-stone-300 my-1 leading-relaxed">
            {formattedParts}
          </li>
        );
      }

      if (!line.trim()) {
        return <div key={idx} className="h-2" />;
      }

      return (
        <p key={idx} className="text-sm leading-relaxed mb-1.5 last:mb-0">
          {formattedParts}
        </p>
      );
    });
  };

  const getRiskBadge = (level?: 'LOW' | 'MEDIUM' | 'CRITICAL') => {
    switch (level) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold tracking-wide uppercase bg-rose-500/20 text-rose-300 border border-rose-500/40 shadow-[0_0_8px_rgba(244,63,94,0.2)]">
            <AlertTriangle className="w-3 h-3" /> Critical Risk
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold tracking-wide uppercase bg-amber-500/20 text-amber-300 border border-amber-500/40">
            <AlertCircle className="w-3 h-3" /> Medium Risk
          </span>
        );
      case 'LOW':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold tracking-wide uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
            <CheckCircle2 className="w-3 h-3" /> Safe Procedure
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div
      className={`flex w-full mb-3.5 transition-opacity duration-200 ${
        isUser ? 'justify-end' : 'justify-start'
      }`}
    >
      <div
        className={`flex items-start gap-2.5 max-w-[88%] sm:max-w-[82%] ${
          isUser ? 'flex-row-reverse' : 'flex-row'
        }`}
      >
        {/* Avatar */}
        <div
          className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-semibold shadow-md ${
            isUser
              ? 'bg-gradient-to-br from-cyan-600 to-blue-700 text-white'
              : 'bg-gradient-to-br from-cyan-500 via-emerald-600 to-teal-700 text-white ring-1 ring-cyan-400/40'
          }`}
          aria-hidden="true"
        >
          {isUser ? <User className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
        </div>

        {/* Message Bubble */}
        <div
          className={`flex flex-col rounded-2xl px-4 py-3 shadow-lg ${
            isUser
              ? 'bg-[#252220] border border-cyan-500/30 text-[#f4efe7] rounded-tr-none'
              : message.isError
              ? 'bg-rose-950/40 border border-rose-500/40 text-rose-200 rounded-tl-none'
              : 'bg-[#1e1c1b] border border-cyan-500/20 text-[#f4efe7] rounded-tl-none shadow-[0_4px_16px_rgba(0,0,0,0.3)]'
          }`}
        >
          {/* Header metadata for AI message */}
          {!isUser && (
            <div className="flex items-center justify-between gap-2 mb-1.5 pb-1 border-b border-white/5">
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] font-semibold tracking-wider text-cyan-400 uppercase">
                  ZeroTrace Advisor
                </span>
                {getRiskBadge(message.riskLevel)}
              </div>
              {timeStr && (
                <span className="text-[10px] text-stone-500 tracking-tight">{timeStr}</span>
              )}
            </div>
          )}

          {/* Message Content */}
          <div className="text-sm select-text break-words">
            {renderFormattedContent(message.content)}
          </div>

          {/* Safety Warnings box if present */}
          {message.warnings && message.warnings.length > 0 && (
            <div className="mt-2.5 pt-2 border-t border-amber-500/20 bg-amber-950/20 rounded-lg p-2.5 border border-amber-500/30">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-300 mb-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                <span>Forensic Safety Warnings</span>
              </div>
              <ul className="space-y-1 pl-1">
                {message.warnings.map((w, wIdx) => (
                  <li
                    key={wIdx}
                    className="text-xs text-amber-200/90 leading-snug flex items-start gap-1.5"
                  >
                    <span className="text-amber-400 font-bold">•</span>
                    <span>{w}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Trigger Button if present */}
          {message.actionType && onActionClick && (
            <div className="mt-2.5 pt-2 border-t border-cyan-500/20 flex items-center justify-between">
              <button
                type="button"
                onClick={() => onActionClick(message.actionType!)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gradient-to-r from-cyan-600/30 to-emerald-600/30 hover:from-cyan-600/50 hover:to-emerald-600/50 border border-cyan-400/40 text-cyan-200 transition-all cursor-pointer shadow-sm hover:shadow-[0_0_12px_rgba(6,182,212,0.3)]"
              >
                <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                <span>Execute {message.actionType} in Station</span>
              </button>
            </div>
          )}

          {/* User message timestamp footer */}
          {isUser && timeStr && (
            <span className="text-[10px] text-stone-500 tracking-tight self-end mt-1">
              {timeStr}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
