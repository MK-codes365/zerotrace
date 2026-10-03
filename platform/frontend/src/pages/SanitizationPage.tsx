import { useState } from 'react';
import { HardDrive, AlertTriangle, ShieldAlert, CheckCircle2, XCircle, Trash2 } from 'lucide-react';
import { sanitizationAPI } from '../services/api';

export default function SanitizationPage() {
  const [target, setTarget] = useState('/dev/sdb');
  const [targetType, setTargetType] = useState('drive');
  const [preview, setPreview] = useState<any>(null);
  const [confirmText, setConfirmText] = useState('');
  const [secondConfirm, setSecondConfirm] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'preview' | 'confirm' | 'result'>('preview');

  const loadPreview = async () => {
    setLoading(true);
    try {
      const { data } = await sanitizationAPI.preview({ target_path: target, target_type: targetType });
      setPreview(data);
      setStep('confirm');
    } catch (err: any) {
      setPreview({ error: err.response?.data?.detail || 'Failed to preview' });
    }
    setLoading(false);
  };

  const executeSanitization = async () => {
    if (confirmText !== 'CONFIRM SANITIZATION') return;
    setLoading(true);
    try {
      const { data } = await sanitizationAPI.execute({
        target_path: target,
        target_type: targetType,
        method: preview?.recommended_method || 'DOD_522220M',
        confirmation_text: confirmText,
        second_confirmation: secondConfirm,
        operator: 'current_user',
      });
      setResult(data);
      setStep('result');
    } catch (err: any) {
      setResult({ error: err.response?.data?.detail || 'Failed' });
      setStep('result');
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6 zt-animate-slide-up">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <HardDrive className="w-6 h-6 text-zt-amber" />
          Secure Sanitization
        </h1>
        <p className="text-zt-text-muted text-sm mt-1">Drive and file erasure with verification</p>
      </div>

      {/* Safety Warning */}
      <div className="p-4 rounded-lg bg-zt-amber/10 border border-zt-amber/20 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-zt-amber flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-zt-amber">SAFE DEMO MODE ACTIVE</p>
          <p className="text-sm text-zt-text-muted mt-1">
            No actual destructive operations will occur. All sanitization is simulated.
            Real erasure requires SAFE_DEMO_MODE=false and explicit confirmation.
          </p>
        </div>
      </div>

      {/* Step 1: Target Selection */}
      <div className="zt-card space-y-4">
        <h3 className="font-semibold">Step 1: Select Target</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="sanitization-target-path" className="text-xs text-zt-text-dim mb-1 block">Target Path</label>
            <input
              id="sanitization-target-path"
              name="targetPath"
              className="zt-input"
              value={target}
              onChange={e => setTarget(e.target.value)}
              placeholder="/dev/sdb or C:\path\to\file"
              autoComplete="off"
            />
          </div>
          <div>
            <label htmlFor="sanitization-target-type" className="text-xs text-zt-text-dim mb-1 block">Target Type</label>
            <select
              id="sanitization-target-type"
              name="targetType"
              className="zt-input"
              value={targetType}
              onChange={e => setTargetType(e.target.value)}
            >
              <option value="drive">Drive</option>
              <option value="file">File</option>
              <option value="folder">Folder</option>
            </select>
          </div>
        </div>
        <button onClick={loadPreview} disabled={loading} className="zt-btn zt-btn-outline">
          {loading ? 'Loading...' : 'Preview Sanitization'}
        </button>
      </div>

      {/* Step 2: Confirmation */}
      {step === 'confirm' && preview && !preview.error && (
        <div className="zt-card space-y-4 border-zt-red/30">
          <h3 className="font-semibold flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-zt-red" />
            Step 2: Review & Confirm
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Target', value: preview.target_path },
              { label: 'Type', value: preview.target_type },
              { label: 'Device Type', value: preview.device_type },
              { label: 'Capacity', value: `${((preview.capacity_bytes || 0) / 1e9).toFixed(1)} GB` },
              { label: 'Filesystem', value: preview.filesystem },
              { label: 'Method', value: preview.recommended_method },
              { label: 'System Drive', value: preview.is_system_drive ? '⚠️ YES' : 'No' },
              { label: 'Est. Duration', value: `${Math.round((preview.estimated_duration_seconds || 0) / 60)} min` },
            ].map(({ label, value }, i) => (
              <div key={i}>
                <p className="text-xs text-zt-text-dim">{label}</p>
                <p className="text-sm font-medium">{value}</p>
              </div>
            ))}
          </div>

          {preview.warnings?.length > 0 && (
            <div className="p-3 rounded-lg bg-zt-amber/10 border border-zt-amber/20">
              {preview.warnings.map((w: string, i: number) => (
                <p key={i} className="text-sm text-zt-amber">{w}</p>
              ))}
            </div>
          )}

          <div className="border-t border-zt-border pt-4 space-y-3">
            <div>
              <label htmlFor="sanitization-confirm-text" className="text-sm font-medium text-zt-red block mb-1">
                Type "CONFIRM SANITIZATION" to proceed:
              </label>
              <input
                id="sanitization-confirm-text"
                name="confirmText"
                className="zt-input border-zt-red/30 focus:border-zt-red"
                value={confirmText}
                onChange={e => setConfirmText(e.target.value)}
                placeholder="CONFIRM SANITIZATION"
                autoComplete="off"
              />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                id="sanitization-second-confirm"
                name="secondConfirm"
                type="checkbox"
                checked={secondConfirm}
                onChange={e => setSecondConfirm(e.target.checked)}
                className="rounded border-zt-border"
              />
              I understand this is a destructive operation (second confirmation)
            </label>
            <button onClick={executeSanitization}
              disabled={confirmText !== 'CONFIRM SANITIZATION' || !secondConfirm || loading}
              className="zt-btn zt-btn-danger">
              <Trash2 className="w-4 h-4" />
              {loading ? 'Executing...' : 'Execute Sanitization'}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Result */}
      {step === 'result' && result && (
        <div className={`zt-card space-y-4 ${result.success ? 'border-zt-emerald/30 zt-glow-emerald' : 'border-zt-red/30 zt-glow-red'}`}>
          <div className="flex items-center gap-2">
            {result.success ? (
              <CheckCircle2 className="w-5 h-5 text-zt-emerald" />
            ) : (
              <XCircle className="w-5 h-5 text-zt-red" />
            )}
            <h3 className="font-semibold">
              {result.success ? 'Sanitization Complete' : 'Sanitization Failed'}
            </h3>
            {result.is_simulated && <span className="zt-badge zt-badge-warning">SIMULATED</span>}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Method', value: result.method },
              { label: 'Passes', value: result.passes_completed },
              { label: 'Bytes Processed', value: `${((result.bytes_processed || 0) / 1e9).toFixed(1)} GB` },
              { label: 'Duration', value: `${(result.duration_seconds || 0).toFixed(2)}s` },
            ].map(({ label, value }, i) => (
              <div key={i}>
                <p className="text-xs text-zt-text-dim">{label}</p>
                <p className="text-sm font-medium">{String(value)}</p>
              </div>
            ))}
          </div>
          {result.warnings?.map((w: string, i: number) => (
            <p key={i} className="text-sm text-zt-amber bg-zt-amber/10 p-2 rounded">{w}</p>
          ))}
          {result.error && <p className="text-sm text-zt-red">{result.error}</p>}
          <button onClick={() => { setStep('preview'); setResult(null); setConfirmText(''); setSecondConfirm(false); }}
            className="zt-btn zt-btn-outline">
            New Sanitization
          </button>
        </div>
      )}

      {/* Method Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[
          { method: 'ZERO_FILL', passes: 1, desc: 'Single pass zero fill', best: 'HDD, USB', color: 'zt-cyan' },
          { method: 'RANDOM_DATA', passes: 1, desc: 'Single pass random data', best: 'HDD, USB', color: 'zt-blue' },
          { method: 'DOD_522220M', passes: 3, desc: 'DoD 5220.22-M standard', best: 'HDD', color: 'zt-indigo' },
          { method: 'GUTMANN', passes: 35, desc: 'Gutmann 35-pass method', best: 'HDD only', color: 'zt-amber' },
          { method: 'SECURE_ERASE_ATA', passes: 1, desc: 'ATA Secure Erase command', best: 'SSD', color: 'zt-emerald' },
          { method: 'CRYPTO_ERASE', passes: 1, desc: 'Cryptographic key erasure', best: 'SED drives', color: 'zt-rose' },
        ].map(({ method, passes, desc, best, color }, i) => (
          <div key={i} className="zt-card">
            <h4 className={`font-semibold text-${color} mb-1`}>{method}</h4>
            <p className="text-sm text-zt-text-muted">{desc}</p>
            <div className="flex justify-between mt-3 text-xs text-zt-text-dim">
              <span>Passes: {passes}</span>
              <span>Best for: {best}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
