import { FileSearch, Filter, HardDrive, File, Hash } from 'lucide-react';

export default function EvidencePage() {
  const evidence = [
    { id: 'EV-102', case: 'CS-2026-004', name: 'usb_drive_sandisk_32gb.img', type: 'Physical Image', hash: 'e3b0c44298fc1...', date: '2026-10-04' },
    { id: 'EV-101', case: 'CS-2026-004', name: 'extracted_financials.zip', type: 'Logical Archive', hash: '8d969eef6ecad...', date: '2026-10-04' },
    { id: 'EV-084', case: 'CS-2026-003', name: 'server_raid_0.dd', type: 'Raw Image', hash: '7d865e959b246...', date: '2026-09-28' },
  ];

  return (
    <div className="space-y-6 zt-animate-slide-up">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileSearch className="w-6 h-6 text-zt-emerald" />
            Digital Evidence Tracker
          </h1>
          <p className="text-zt-text-muted text-sm mt-1">Chain of custody and hash verification for seized media</p>
        </div>
        <button className="zt-btn zt-btn-outline">
          <Filter className="w-4 h-4" /> Filter By Case
        </button>
      </div>

      <div className="zt-card bg-zt-surface border-zt-border p-0 overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-zt-surface-hover border-b border-zt-border text-xs text-zt-text-dim uppercase">
            <tr>
              <th className="px-6 py-4">Evidence ID</th>
              <th className="px-6 py-4">Case Ref</th>
              <th className="px-6 py-4">Item Name</th>
              <th className="px-6 py-4">Type</th>
              <th className="px-6 py-4">SHA-256 Hash</th>
              <th className="px-6 py-4">Acquired Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zt-border/50">
            {evidence.map((item, i) => (
              <tr key={i} className="hover:bg-zt-surface-hover transition-colors">
                <td className="px-6 py-4 font-mono font-medium text-zt-emerald">{item.id}</td>
                <td className="px-6 py-4 text-zt-text-muted">{item.case}</td>
                <td className="px-6 py-4 font-medium flex items-center gap-2">
                  <HardDrive className="w-4 h-4 text-zt-cyan" />
                  {item.name}
                </td>
                <td className="px-6 py-4">{item.type}</td>
                <td className="px-6 py-4 font-mono text-xs text-zt-text-dim flex items-center gap-1">
                  <Hash className="w-3 h-3" /> {item.hash}
                </td>
                <td className="px-6 py-4 text-zt-text-muted">{item.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
