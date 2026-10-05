import { useState } from 'react';
import { Database, FolderOpen, Tag, Calendar, User, Search, Map, Shield } from 'lucide-react';

export default function CasesPage() {
  const [search, setSearch] = useState('');

  const cases = [
    { id: 'CS-2026-004', name: 'Operation DarkNet', investigator: 'Agent Miller', status: 'ACTIVE', date: '2026-10-04', items: 12 },
    { id: 'CS-2026-003', name: 'Corporate Espionage X', investigator: 'Lead forensic', status: 'CLOSED', date: '2026-09-28', items: 45 },
    { id: 'CS-2026-002', name: 'Insider Threat DB', investigator: 'Agent Miller', status: 'ACTIVE', date: '2026-09-15', items: 3 },
    { id: 'CS-2026-001', name: 'Ransomware Triage', investigator: 'Cyber Unit', status: 'CLOSED', date: '2026-08-30', items: 89 },
  ];

  return (
    <div className="space-y-6 zt-animate-slide-up">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Database className="w-6 h-6 text-zt-blue" />
            Forensic Case Management
          </h1>
          <p className="text-zt-text-muted text-sm mt-1">Organize and track digital evidence portfolios</p>
        </div>
        <button className="zt-btn zt-btn-primary">
          <FolderOpen className="w-4 h-4" /> New Case
        </button>
      </div>

      <div className="zt-card bg-zt-surface/50 border-zt-border p-4">
        <div className="relative mb-6 w-full max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zt-text-dim" />
          <input 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="zt-input pl-9 w-full"
            placeholder="Search by Case ID or Name..."
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {cases.filter(c => c.name.toLowerCase().includes(search.toLowerCase()) || c.id.includes(search)).map((c, i) => (
            <div key={i} className="p-4 rounded-xl border border-zt-border bg-zt-surface hover:border-zt-blue/50 transition-colors cursor-pointer group relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1 h-full bg-zt-blue"></div>
              
              <div className="flex justify-between items-start mb-3">
                <span className="text-xs font-mono text-zt-text-muted">{c.id}</span>
                <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${c.status === 'ACTIVE' ? 'bg-zt-emerald/20 text-zt-emerald' : 'bg-zt-text-dim/20 text-zt-text-dim'}`}>
                  {c.status}
                </span>
              </div>
              
              <h3 className="font-semibold text-zt-text mb-4 group-hover:text-zt-blue transition-colors truncate">{c.name}</h3>
              
              <div className="space-y-2 text-xs text-zt-text-dim">
                <div className="flex items-center gap-2"><User className="w-3 h-3" /> {c.investigator}</div>
                <div className="flex items-center gap-2"><Calendar className="w-3 h-3" /> {c.date}</div>
                <div className="flex items-center gap-2"><Tag className="w-3 h-3" /> {c.items} Evidence Items</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
