import { useState } from 'react';
import { Search, ShieldAlert, CheckCircle2, PlayCircle, Loader2, Upload, Activity, FileSearch, Database } from 'lucide-react';

export default function RecoveryPage() {
  const [target, setTarget] = useState('E01_Image_001.dd');
  const [status, setStatus] = useState<'idle' | 'scanning' | 'completed'>('idle');
  const [progress, setProgress] = useState(0);

  const startCarving = () => {
    setStatus('scanning');
    setProgress(0);
    const interval = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          clearInterval(interval);
          setStatus('completed');
          return 100;
        }
        return p + 5;
      });
    }, 300);
  };

  const recoveredFiles = [
    { name: 'evidence_photo_01.jpg', type: 'JPEG', score: '98%', fragment: 'Contiguous', size: '2.4 MB' },
    { name: 'financial_ledger.xlsx', type: 'XLSX', score: '85%', fragment: 'Fragmented (2 chunks)', size: '1.1 MB' },
    { name: 'deleted_chat_log.db', type: 'SQLite', score: '92%', fragment: 'Contiguous', size: '450 KB' },
    { name: 'hidden_video.mp4', type: 'MP4', score: '64%', fragment: 'Highly Fragmented', size: '15.6 MB' },
  ];

  return (
    <div className="space-y-6 zt-animate-slide-up">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <FileSearch className="w-6 h-6 text-zt-cyan" />
          Advanced File Carving & Recovery
        </h1>
        <p className="text-zt-text-muted text-sm mt-1">
          Recover deleted files from damaged media using signature, structure, and intelligent carving.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Carving Configuration */}
        <div className="lg:col-span-1 space-y-4">
          <div className="zt-card bg-zt-surface border-zt-border">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <Database className="w-5 h-5 text-zt-indigo" />
              Target Selection
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-xs text-zt-text-dim block mb-1">Image/Drive Path</label>
                <div className="flex gap-2">
                  <input
                    value={target}
                    onChange={e => setTarget(e.target.value)}
                    className="zt-input flex-1"
                    placeholder="Enter physical drive or image path"
                  />
                  <button className="zt-btn zt-btn-outline px-3"><Upload className="w-4 h-4" /></button>
                </div>
              </div>

              <div>
                <label className="text-xs text-zt-text-dim block mb-2">Carving Algorithms</label>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" defaultChecked className="rounded border-zt-border" />
                    Signature-based Carving (Headers/Footers)
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" defaultChecked className="rounded border-zt-border" />
                    Structure-based Consensus Validation
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" defaultChecked className="rounded border-zt-border" />
                    Bi-Directional Fragment Reconstruction
                  </label>
                </div>
              </div>

              <button 
                onClick={startCarving}
                disabled={status === 'scanning'}
                className="zt-btn zt-btn-primary w-full justify-center"
              >
                {status === 'scanning' ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing Sectors...</>
                ) : (
                  <><PlayCircle className="w-4 h-4" /> Start Deep Recovery</>
                )}
              </button>
            </div>
          </div>

          <div className="zt-card bg-zt-surface/30">
             <h3 className="text-sm font-semibold mb-2">Compliance Note</h3>
             <p className="text-xs text-zt-text-muted">
               ZeroTrace preserves evidential integrity by ensuring all carving operations are strictly read-only against the target media.
             </p>
          </div>
        </div>

        {/* Live Recovery Console */}
        <div className="lg:col-span-2 space-y-4">
          <div className="zt-card bg-black/40 border-zt-border h-[200px] flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold flex items-center gap-2 text-zt-cyan">
                <Activity className="w-4 h-4" />
                Live Sector Analysis
              </h3>
              <span className="text-xs font-mono text-zt-text-muted">{progress}% Complete</span>
            </div>
            
            <div className="flex-1 bg-black/60 rounded border border-zt-border/50 p-3 font-mono text-xs overflow-hidden relative">
              {status === 'idle' && <span className="text-zt-text-dim">Waiting for input...</span>}
              {status === 'scanning' && (
                <div className="text-zt-emerald flex flex-col gap-1 zt-animate-slide-up">
                  <span>[+] Mapping cluster bitmaps... OK</span>
                  <span>[+] Generating entropy maps... OK</span>
                  <span>[*] Scanning Sector {145392 + (progress * 500)} for Hex signatures...</span>
                  {progress > 30 && <span>[!] JPEG Header Found @ Offset 0x4B3A</span>}
                  {progress > 60 && <span>[!] Fragment gap detected, initiating graph reconstruction...</span>}
                </div>
              )}
              {status === 'completed' && <span className="text-zt-cyan">[+] Deep carve complete. Analyzed 1.5 TB volume.</span>}
              
              {/* Progress Bar */}
              <div className="absolute bottom-0 left-0 h-1 bg-zt-border w-full">
                <div className="h-full bg-zt-cyan transition-all duration-300" style={{ width: `${progress}%` }} />
              </div>
            </div>
          </div>

          {/* Results Table */}
          {status === 'completed' && (
            <div className="zt-card border-zt-emerald/30 zt-animate-fade-in">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-zt-emerald" />
                  Classified Extracted Artifacts
                </h3>
                <span className="zt-badge zt-badge-success">{recoveredFiles.length} Found</span>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-zt-text-dim uppercase border-b border-zt-border/50">
                    <tr>
                      <th className="px-4 py-2">Filename</th>
                      <th className="px-4 py-2">Type</th>
                      <th className="px-4 py-2">Structure</th>
                      <th className="px-4 py-2">Confidence</th>
                      <th className="px-4 py-2">Size</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recoveredFiles.map((file, i) => (
                      <tr key={i} className="border-b border-zt-border/30 hover:bg-zt-surface-hover transition-colors">
                        <td className="px-4 py-3 font-medium text-zt-text">{file.name}</td>
                        <td className="px-4 py-3 text-zt-cyan">{file.type}</td>
                        <td className="px-4 py-3 text-zt-text-muted">{file.fragment}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-xs ${parseInt(file.score) > 90 ? 'bg-zt-emerald/20 text-zt-emerald' : 'bg-zt-amber/20 text-zt-amber'}`}>
                            {file.score}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-zt-text-dim">{file.size}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
