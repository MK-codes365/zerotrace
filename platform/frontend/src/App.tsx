import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import {
  Shield, Database, HardDrive, FileSearch, BarChart3,
  FileText, PlayCircle, Settings, LogOut, Menu, X,
  AlertTriangle, CheckCircle2, Clock, Cpu,
} from 'lucide-react';
import Dashboard from './pages/Dashboard';
import CasesPage from './pages/CasesPage';
import EvidencePage from './pages/EvidencePage';
import SanitizationPage from './pages/SanitizationPage';
import RecoveryPage from './pages/RecoveryPage';
import ReportsPage from './pages/ReportsPage';
import DemoPage from './pages/DemoPage';
import LoginPage from './pages/LoginPage';

function App() {
  const [token, setToken] = useState(localStorage.getItem('zt_token'));
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [user, setUser] = useState<{ username: string; role: string } | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem('zt_user');
    if (stored) {
      try { setUser(JSON.parse(stored)); } catch { /* ignore */ }
    }
  }, [token]);

  const handleLogin = (tokenData: { access_token: string; username: string; role: string }) => {
    localStorage.setItem('zt_token', tokenData.access_token);
    localStorage.setItem('zt_user', JSON.stringify({ username: tokenData.username, role: tokenData.role }));
    setToken(tokenData.access_token);
    setUser({ username: tokenData.username, role: tokenData.role });
  };

  const handleLogout = () => {
    localStorage.removeItem('zt_token');
    localStorage.removeItem('zt_user');
    setToken(null);
    setUser(null);
  };

  if (!token) {
    return <LoginPage onLogin={handleLogin} />;
  }

  const navItems = [
    { to: '/', icon: BarChart3, label: 'Dashboard' },
    { to: '/cases', icon: Database, label: 'Cases' },
    { to: '/evidence', icon: FileSearch, label: 'Evidence' },
    { to: '/sanitization', icon: HardDrive, label: 'Sanitization' },
    { to: '/recovery', icon: Shield, label: 'Recovery' },
    { to: '/reports', icon: FileText, label: 'Reports' },
    { to: '/demo', icon: PlayCircle, label: 'Run Demo' },
  ];

  return (
    <BrowserRouter>
      <div className="flex min-h-screen zt-scan-overlay">
        {/* ── Sidebar ──────────────────────────────── */}
        <aside className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-zt-surface border-r border-zt-border transition-all duration-300 flex flex-col fixed h-full z-40`}>
          {/* Logo */}
          <div className="flex items-center gap-3 px-4 py-5 border-b border-zt-border">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-zt-cyan to-zt-indigo flex items-center justify-center flex-shrink-0">
              <Shield className="w-5 h-5 text-white" />
            </div>
            {sidebarOpen && (
              <div className="zt-animate-fade-in">
                <h1 className="text-sm font-bold tracking-wider bg-gradient-to-r from-zt-cyan to-zt-indigo bg-clip-text text-transparent">
                  ZEROTrace
                </h1>
                <p className="text-[10px] text-zt-text-dim leading-tight">Forensic Platform</p>
              </div>
            )}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="ml-auto text-zt-text-dim hover:text-zt-cyan transition-colors"
            >
              {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>

          {/* Nav */}
          <nav className="flex-1 py-4 space-y-1 px-2">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-zt-cyan/10 to-zt-indigo/10 text-zt-cyan border border-zt-cyan/20'
                      : 'text-zt-text-muted hover:text-zt-text hover:bg-zt-surface-hover'
                  }`
                }
              >
                <Icon className="w-4.5 h-4.5 flex-shrink-0" />
                {sidebarOpen && <span className="zt-animate-fade-in">{label}</span>}
              </NavLink>
            ))}
          </nav>

          {/* User */}
          <div className="border-t border-zt-border p-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-zt-cyan to-zt-blue flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                {user?.username?.[0]?.toUpperCase() || 'U'}
              </div>
              {sidebarOpen && (
                <div className="flex-1 min-w-0 zt-animate-fade-in">
                  <p className="text-sm font-medium truncate">{user?.username}</p>
                  <p className="text-xs text-zt-text-dim">{user?.role}</p>
                </div>
              )}
              {sidebarOpen && (
                <button onClick={handleLogout} className="text-zt-text-dim hover:text-zt-red transition-colors">
                  <LogOut className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </aside>

        {/* ── Main Content ─────────────────────────── */}
        <main className={`flex-1 ${sidebarOpen ? 'ml-64' : 'ml-16'} transition-all duration-300`}>
          {/* Top bar */}
          <header className="sticky top-0 z-30 bg-zt-bg/80 backdrop-blur-md border-b border-zt-border px-6 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="zt-badge zt-badge-success">
                <CheckCircle2 className="w-3 h-3" />
                SAFE DEMO MODE
              </span>
              <span className="zt-badge zt-badge-info">
                <Cpu className="w-3 h-3" />
                v1.0.0
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-zt-text-dim">
              <Clock className="w-3.5 h-3.5" />
              {new Date().toLocaleString()}
            </div>
          </header>

          {/* Routes */}
          <div className="p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/cases" element={<CasesPage />} />
              <Route path="/evidence" element={<EvidencePage />} />
              <Route path="/sanitization" element={<SanitizationPage />} />
              <Route path="/recovery" element={<RecoveryPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/demo" element={<DemoPage />} />
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
