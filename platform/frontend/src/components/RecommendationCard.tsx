import React, { useState } from 'react';
import {
  AlertTriangle,
  Shield,
  Zap,
  HardDrive,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  ChevronRight,
  Info,
  Clock,
} from 'lucide-react';
import { AdvisorRecommendationResponse, RiskLevel, ActionType } from '../services/api';

export interface RecommendationCardProps {
  recommendation: AdvisorRecommendationResponse & {
    target_extension?: string;
    storage_medium?: string;
    file_system?: string;
    loss_scenario?: string;
  };
  onLaunchCarve?: (params: { target_extension?: string; preset?: string }) => void;
  onImageDisk?: (params: { format: string; readOnly: boolean }) => void;
  onRunMftScan?: (params: { file_system?: string }) => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  onLaunchCarve,
  onImageDisk,
  onRunMftScan,
}) => {
  const [actionTriggered, setActionTriggered] = useState<string | null>(null);

  const {
    recommended_method,
    risk_level,
    safety_warnings = [],
    action_type,
    target_extension,
    storage_medium,
  } = recommendation;

  // Determine Warning Badge styling & text
  const getBadgeDetails = (level: RiskLevel) => {
    switch (level) {
      case 'CRITICAL':
        return {
          bg: 'bg-rose-950/60 border-rose-500/50 text-rose-300 shadow-[0_0_12px_rgba(244,63,94,0.25)]',
          badgeText:
            storage_medium === 'SSD'
              ? 'CRITICAL: TRIM Risk Detected'
              : 'CRITICAL: Severe Data Risk / Hardware Alert',
          icon: AlertTriangle,
          accentBorder: 'border-rose-800/60',
          pillBg: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
        };
      case 'MEDIUM':
        return {
          bg: 'bg-amber-950/50 border-amber-500/40 text-amber-300 shadow-[0_0_10px_rgba(245,158,11,0.2)]',
          badgeText:
            storage_medium === 'SSD'
              ? 'MEDIUM: TRIM Risk Detected'
              : 'MEDIUM RISK: Procedural Caution Advised',
          icon: AlertCircle,
          accentBorder: 'border-amber-800/60',
          pillBg: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
        };
      case 'LOW':
      default:
        return {
          bg: 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300',
          badgeText: 'LOW RISK: Standard Non-Destructive Carving',
          icon: CheckCircle2,
          accentBorder: 'border-emerald-800/60',
          pillBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
        };
    }
  };

  const badge = getBadgeDetails(risk_level);
  const BadgeIcon = badge.icon;

  const handleLaunchCarve = () => {
    const preset = target_extension
      ? `Scalpel Deep Carve (Target: .${target_extension})`
      : 'Scalpel Deep Signature Carving';
    
    setActionTriggered('carve');
    if (onLaunchCarve) {
      onLaunchCarve({ target_extension, preset });
    } else {
      window.dispatchEvent(
        new CustomEvent('zt-launch-carver', {
          detail: {
            target_extension,
            preset,
            action: 'LAUNCH_CARVE',
            timestamp: Date.now(),
          },
        })
      );
    }
    setTimeout(() => setActionTriggered(null), 4000);
  };

  const handleImageDisk = () => {
    setActionTriggered('image');
    if (onImageDisk) {
      onImageDisk({ format: 'raw_dd', readOnly: true });
    } else {
      window.dispatchEvent(
        new CustomEvent('zt-image-disk', {
          detail: {
            format: 'raw_dd',
            readOnly: true,
            action: 'IMAGE_DISK',
            timestamp: Date.now(),
          },
        })
      );
    }
    setTimeout(() => setActionTriggered(null), 4000);
  };

  const handleRunMftScan = () => {
    setActionTriggered('mft');
    if (onRunMftScan) {
      onRunMftScan({ file_system: recommendation.file_system || 'NTFS' });
    } else {
      window.dispatchEvent(
        new CustomEvent('zt-mft-scan', {
          detail: {
            file_system: recommendation.file_system || 'NTFS',
            action: 'RUN_MFT_SCAN',
            timestamp: Date.now(),
          },
        })
      );
    }
    setTimeout(() => setActionTriggered(null), 4000);
  };

  return (
    <div
      className={`my-3 p-4 rounded-xl border bg-[#0e1013] ${badge.accentBorder} shadow-lg transition-all duration-200 text-left font-sans`}
      data-testid="recommendation-card"
    >
      {/* ── Warning Badge ────────────────────────────── */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <div
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold tracking-wide ${badge.bg}`}
        >
          <BadgeIcon className="w-3.5 h-3.5 shrink-0" />
          <span>{badge.badgeText}</span>
        </div>

        <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded border ${badge.pillBg}`}>
          {action_type}
        </span>
      </div>

      {/* ── Recommended Method ───────────────────────── */}
      <div className="mb-3">
        <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider mb-1 flex items-center gap-1">
          <Info className="w-3 h-3 text-cyan-400" />
          <span>Recommended Forensic Strategy</span>
        </div>
        <p className="text-sm font-medium text-zinc-100 leading-snug">
          {recommended_method}
        </p>
      </div>

      {/* ── Safety Warnings ──────────────────────────── */}
      {safety_warnings.length > 0 && (
        <div className="mb-3.5 p-3 rounded-lg bg-zinc-950/70 border border-zinc-800/80">
          <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            <span>Safety Warnings & Protocols</span>
          </div>
          <ul className="space-y-1.5">
            {safety_warnings.map((warn, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-zinc-300">
                <span className="text-amber-400 font-mono text-[11px] shrink-0 mt-0.5">⚠️</span>
                <span>{warn}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Action Trigger Feedback Banner ──────────── */}
      {actionTriggered && (
        <div className="mb-3 p-2.5 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-xs text-emerald-300 flex items-center justify-between zt-animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              {actionTriggered === 'carve' && '🚀 Scalpel Carving preset sent to recovery console!'}
              {actionTriggered === 'image' && '🛡️ Read-only bitstream disk imager engaged (.dd)!'}
              {actionTriggered === 'mft' && '⚡ NTFS MFT rapid metadata scanner initialized!'}
            </span>
          </div>
          <span className="text-[10px] font-mono text-emerald-400">ACTIVE</span>
        </div>
      )}

      {/* ── Action Buttons ───────────────────────────── */}
      <div className="pt-2 border-t border-zinc-800/80 flex flex-col sm:flex-row gap-2">
        {/* Primary Action Button */}
        {action_type === 'RUN_MFT_SCAN' ? (
          <>
            <button
              onClick={handleRunMftScan}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg text-xs font-semibold shadow-md hover:shadow-cyan-500/20 transition-all cursor-pointer"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>[ ⚡ Run MFT Fast Scan ]</span>
            </button>
            <button
              onClick={handleLaunchCarve}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 rounded-lg text-xs font-medium transition-colors cursor-pointer"
            >
              <span>[ 🚀 Launch Scalpel Carving ]</span>
            </button>
          </>
        ) : (
          <button
            onClick={handleLaunchCarve}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white rounded-lg text-xs font-semibold shadow-md hover:shadow-cyan-500/25 transition-all cursor-pointer"
          >
            <span>[ 🚀 Launch Scalpel Carving ]</span>
            {target_extension && (
              <span className="font-mono text-[10px] bg-black/30 px-1.5 py-0.5 rounded text-cyan-200">
                .{target_extension}
              </span>
            )}
          </button>
        )}

        {/* Safety Action Button */}
        <button
          onClick={handleImageDisk}
          className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
            risk_level === 'CRITICAL'
              ? 'bg-rose-950/60 hover:bg-rose-900/60 text-rose-200 border-rose-600/60 shadow-xs'
              : 'bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border-zinc-700 hover:text-white'
          }`}
        >
          <Shield className="w-3.5 h-3.5 text-cyan-400" />
          <span>[ 🛡️ Create Read-Only Image (.dd) ]</span>
        </button>
      </div>
    </div>
  );
};

export default RecommendationCard;
