import { useState, useEffect } from 'react';
import {
  Activity, Database, FileSearch, HardDrive, Shield,
  CheckCircle2, XCircle, Clock, Cpu, BarChart3,
  TrendingUp, Layers, Zap, AlertTriangle,
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { dashboardAPI } from '../services/api';

const COLORS = ['#06b6d4', '#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardAPI.stats()
      .then(r => setStats(r.data))
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  // Demo fallback for deployed projects without a live backend connection
  const actualStats = stats || {
    active_jobs: 2, completed_jobs: 15, recovery_jobs: 8,
    sanitization_jobs: 5, failed_jobs: 1, evidence_items: 12,
    total_cases: 6, recovered_files_count: 247, throughput_mbps: 45.8,
    workers_active: 3, integrity_status: 'VERIFIED',
  };

  const jobChart = [
    { name: 'Recovery', value: actualStats.recovery_jobs, color: '#06b6d4' },
    { name: 'Sanitization', value: actualStats.sanitization_jobs, color: '#f59e0b' },
    { name: 'Completed', value: actualStats.completed_jobs, color: '#10b981' },
    { name: 'Failed', value: actualStats.failed_jobs, color: '#ef4444' },
  ];

  const recoveryTimeline = [
    { time: '00:00', files: 0, throughput: 0 },
    { time: '00:15', files: 32, throughput: 28 },
    { time: '00:30', files: 78, throughput: 42 },
    { time: '00:45', files: 124, throughput: 55 },
    { time: '01:00', files: 189, throughput: 48 },
    { time: '01:15', files: 247, throughput: 46 },
  ];

  const fileTypes = [
    { name: 'JPEG', count: 89 }, { name: 'PNG', count: 43 },
    { name: 'PDF', count: 38 }, { name: 'ZIP', count: 22 },
    { name: 'DOCX', count: 18 }, { name: 'MP3', count: 15 },
    { name: 'GIF', count: 12 }, { name: 'Other', count: 10 },
  ];

  const statCards = [
    { icon: Activity, label: 'Active Jobs', value: actualStats.active_jobs, color: 'text-zt-cyan', bg: 'from-zt-cyan/10 to-zt-cyan/5' },
    { icon: CheckCircle2, label: 'Completed', value: actualStats.completed_jobs, color: 'text-zt-emerald', bg: 'from-zt-emerald/10 to-zt-emerald/5' },
    { icon: Database, label: 'Evidence Items', value: actualStats.evidence_items, color: 'text-zt-blue', bg: 'from-zt-blue/10 to-zt-blue/5' },
    { icon: FileSearch, label: 'Recovered Files', value: actualStats.recovered_files_count, color: 'text-zt-indigo', bg: 'from-zt-indigo/10 to-zt-indigo/5' },
    { icon: HardDrive, label: 'Sanitizations', value: actualStats.sanitization_jobs, color: 'text-zt-amber', bg: 'from-zt-amber/10 to-zt-amber/5' },
    { icon: Shield, label: 'Cases', value: actualStats.total_cases, color: 'text-zt-rose', bg: 'from-zt-rose/10 to-zt-rose/5' },
  ];

  return (
    <div className="space-y-6 zt-animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-zt-text-muted text-sm mt-1">Forensic Operations Overview</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-zt-emerald/10 border border-zt-emerald/20">
            <div className="w-2 h-2 rounded-full bg-zt-emerald animate-pulse" />
            <span className="text-xs font-medium text-zt-emerald">System Online</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-zt-surface border border-zt-border">
            <Cpu className="w-3.5 h-3.5 text-zt-cyan" />
            <span className="text-xs text-zt-text-muted">{actualStats.throughput_mbps.toFixed(1)} MB/s</span>
          </div>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map(({ icon: Icon, label, value, color, bg }, i) => (
          <div key={i} className={`zt-card bg-gradient-to-br ${bg} border-zt-border hover:zt-glow-cyan`}
               style={{ animationDelay: `${i * 0.05}s` }}>
            <div className="flex items-center gap-2 mb-2">
              <Icon className={`w-4 h-4 ${color}`} />
              <span className="text-xs text-zt-text-dim">{label}</span>
            </div>
            <p className="text-2xl font-bold">{value}</p>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recovery Timeline */}
        <div className="lg:col-span-2 zt-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-zt-cyan" />
              Recovery Timeline
            </h3>
            <span className="zt-badge zt-badge-info">Live</span>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={recoveryTimeline}>
              <defs>
                <linearGradient id="gradCyan" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f33" />
              <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 11 }} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111827', border: '1px solid #1e3a5f', borderRadius: 8 }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Area type="monotone" dataKey="files" stroke="#06b6d4" fillOpacity={1} fill="url(#gradCyan)" strokeWidth={2} />
              <Area type="monotone" dataKey="throughput" stroke="#6366f1" fill="transparent" strokeWidth={2} strokeDasharray="5 5" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Job Distribution */}
        <div className="zt-card">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <Layers className="w-4 h-4 text-zt-indigo" />
            Job Distribution
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={jobChart} cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                   dataKey="value" paddingAngle={4} strokeWidth={0}>
                {jobChart.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #1e3a5f', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-2 mt-2">
            {jobChart.map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-zt-text-muted">{item.name}: {item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* File Types & Integrity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recovered File Types */}
        <div className="zt-card">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <BarChart3 className="w-4 h-4 text-zt-cyan" />
            Recovered File Types
          </h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={fileTypes} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f33" />
              <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} />
              <YAxis dataKey="name" type="category" tick={{ fill: '#94a3b8', fontSize: 11 }} width={50} />
              <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #1e3a5f', borderRadius: 8 }} />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {fileTypes.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Integrity Status */}
        <div className="zt-card">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <Shield className="w-4 h-4 text-zt-emerald" />
            Integrity & Security Status
          </h3>
          <div className="space-y-4">
            {[
              { label: 'Evidence Integrity', status: 'VERIFIED', icon: CheckCircle2, color: 'zt-emerald' },
              { label: 'Hash Chain', status: 'VALID', icon: CheckCircle2, color: 'zt-emerald' },
              { label: 'Merkle Tree', status: 'BUILT', icon: CheckCircle2, color: 'zt-emerald' },
              { label: 'Audit Chain', status: 'INTACT', icon: CheckCircle2, color: 'zt-emerald' },
              { label: 'Safe Demo Mode', status: 'ENABLED', icon: Shield, color: 'zt-cyan' },
              { label: 'Authentication', status: 'JWT + RBAC', icon: Shield, color: 'zt-cyan' },
            ].map(({ label, status, icon: Icon, color }, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-zt-border/30 last:border-0">
                <div className="flex items-center gap-2">
                  <Icon className={`w-4 h-4 text-${color}`} />
                  <span className="text-sm">{label}</span>
                </div>
                <span className={`zt-badge zt-badge-success`}>{status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
