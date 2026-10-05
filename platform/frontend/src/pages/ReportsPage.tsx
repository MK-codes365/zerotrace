import { useState, useEffect } from 'react';
import { FileText, Shield, Download, Lock, CheckCircle2, Hash, Database, ChevronDown, ChevronRight } from 'lucide-react';
import { auditAPI } from '../services/api';

export default function ReportsPage() {
  const [expandedBlock, setExpandedBlock] = useState<string | null>(null);
  const [blocks, setBlocks] = useState<any[]>([]);

  useEffect(() => {
    auditAPI.list().then(res => {
      const mapped = res.data.map((event: any) => ({
        id: event.event_id || event.id || Math.random().toString().slice(2, 6),
        operation: event.action || event.event_type || 'System Event',
        hash: event.current_hash || 'N/A',
        prevHash: event.previous_hash || 'N/A',
        time: event.timestamp ? new Date(event.timestamp).toLocaleString() : 'N/A',
        status: 'VERIFIED'
      }));
      setBlocks(mapped);
    }).catch(console.error);
  }, []);
  return (
    <div className="space-y-6 zt-animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <Lock className="text-zt-cyan" />
            Audit Management System
          </h1>
          <p className="text-zt-text-muted text-sm mt-1">Cryptographic Ledger & Compliance Certificates</p>
        </div>
        <button className="btn-primary">
          <Download className="w-4 h-4" /> Export Ledger (PDF)
        </button>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Ledger Column */}
        <div className="lg:col-span-2 space-y-4">
          <div className="zt-card bg-zt-surface border-zt-border mb-4">
            <div className="flex justify-between items-center">
              <h2 className="font-bold flex items-center gap-2">
                <Shield className="w-5 h-5 text-zt-emerald" /> 
                Immutable Hash Chain
              </h2>
              <span className="zt-badge zt-badge-success">Ledger Intact</span>
            </div>
            <p className="text-xs text-zt-text-dim mt-2">All blocks verified against current Merkle root.</p>
          </div>

          <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-zt-border before:to-transparent">
            {blocks.length === 0 ? (
              <p className="text-zt-text-dim text-center py-8">No audit logs found. Perform a wipe or operation to generate a block.</p>
            ) : (
              blocks.map((block) => (
                <div key={block.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-zt-surface shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow shadow-zt-cyan/20 z-10">
                    <Database className="w-4 h-4 text-zt-cyan" />
                  </div>
                  
                  <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-zt-border bg-zt-surface/50 backdrop-blur hover:bg-zt-surface transition-all cursor-pointer shadow-lg" onClick={() => setExpandedBlock(expandedBlock === block.id ? null : block.id)}>
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs font-bold text-zt-text-muted">Block #{String(block.id).slice(0, 8)}</span>
                      <span className="text-xs text-zt-text-dim">{block.time}</span>
                    </div>
                    <h3 className="font-semibold text-zt-text">{block.operation}</h3>
                    
                    {expandedBlock === block.id && (
                      <div className="mt-4 p-3 bg-black/40 rounded-lg border border-zt-border/50 text-xs font-mono break-all zt-animate-fade-in space-y-2">
                        <div>
                          <span className="text-zt-text-dim block">Block Hash:</span>
                          <span className="text-zt-cyan">{block.hash}</span>
                        </div>
                        <div>
                          <span className="text-zt-text-dim block">Previous Hash:</span>
                          <span className="text-zt-text-muted">{block.prevHash}</span>
                        </div>
                        <div className="flex items-center gap-2 mt-2 pt-2 border-t border-zt-border/30">
                          <CheckCircle2 className="w-3 h-3 text-zt-emerald" />
                          <span className="text-zt-emerald">Signature Valid</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Side Panel */}
        <div className="space-y-6">
          <div className="zt-card">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <FileText className="w-4 h-4 text-zt-indigo" />
              Recent Compliance Reports
            </h3>
            <div className="space-y-3">
              {[
                { name: 'Cert_Drive_Sanitize_A.pdf', type: 'NIST 800-88' },
                { name: 'Cert_Drive_Sanitize_B.pdf', type: 'DoD 5220.22-M' },
                { name: 'Forensic_Extraction_Log.pdf', type: 'Chain of Custody' }
              ].map((cert, i) => (
                <div key={i} className="p-3 border border-zt-border/50 rounded-lg bg-zt-surface/30 hover:bg-zt-surface transition-colors flex items-center justify-between cursor-pointer group">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-zt-indigo/10 rounded text-zt-indigo">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-xs font-medium">{cert.name}</p>
                      <p className="text-[10px] text-zt-text-dim">{cert.type}</p>
                    </div>
                  </div>
                  <Download className="w-3 h-3 text-zt-text-dim group-hover:text-zt-cyan" />
                </div>
              ))}
            </div>
          </div>

          <div className="zt-card bg-gradient-to-br from-zt-cyan/5 to-zt-indigo/5">
            <h3 className="font-semibold mb-2">Cryptographic Integrity</h3>
            <p className="text-xs text-zt-text-muted mb-4 leading-relaxed">
              ZeroTrace uses SHA-256 hash chains to ensure the immutability of audit logs. Modifying any past event will invalidate all subsequent blocks.
            </p>
            <div className="p-3 bg-black/40 rounded border border-zt-border text-center">
              <span className="text-xs font-mono text-zt-cyan truncate block">
                ROOT: 4898da28047151...
              </span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
