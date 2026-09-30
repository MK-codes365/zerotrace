import React, { useState } from 'react';
import { Shield, User, Lock, Mail, ArrowRight } from 'lucide-react';
import { authAPI } from '../services/api';

interface LoginPageProps {
  onLogin: (data: { access_token: string; username: string; role: string }) => void;
}

export default function LoginPage({ onLogin }: LoginPageProps) {
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ username: '', password: '', email: '', full_name: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isRegister) {
        await authAPI.register({ ...form, role: 'INVESTIGATOR' });
      }
      const { data } = await authAPI.login({ username: form.username, password: form.password });
      onLogin(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Ensure the backend is running.');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Background grid effect */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(6,182,212,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(6,182,212,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-zt-cyan/5 rounded-full blur-[120px]" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-zt-indigo/5 rounded-full blur-[120px]" />

      <div className="relative z-10 w-full max-w-md px-4">
        {/* Logo */}
        <div className="text-center mb-8 zt-animate-slide-up">
          <img
            src="/logo.png"
            alt="ZeroTrace Logo"
            className="w-16 h-16 object-contain mx-auto mb-4 drop-shadow-[0_0_15px_rgba(0,255,157,0.4)]"
          />
          <h1 className="text-3xl font-bold tracking-tight">
            <span className="bg-gradient-to-r from-zt-cyan to-zt-indigo bg-clip-text text-transparent">ZERO</span>
            <span className="text-white">Trace</span>
          </h1>
          <p className="text-zt-text-muted text-sm mt-1">
            Integrated Secure Data Erasure &<br />Advanced File Recovery Platform
          </p>
          <p className="text-zt-text-dim text-xs mt-2">Enterprise Forensic Edition</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="zt-glass p-6 space-y-4 zt-animate-slide-up" style={{ animationDelay: '0.1s' }}>
          <h2 className="text-lg font-semibold text-center mb-2">
            {isRegister ? 'Create Account' : 'Sign In'}
          </h2>

          {error && (
            <div className="p-3 rounded-lg bg-zt-red/10 border border-zt-red/20 text-zt-red text-sm">
              {error}
            </div>
          )}

          {isRegister && (
            <>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zt-text-dim" />
                <input className="zt-input pl-10" placeholder="Full Name" value={form.full_name}
                  onChange={e => setForm({ ...form, full_name: e.target.value })} required />
              </div>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zt-text-dim" />
                <input className="zt-input pl-10" type="email" placeholder="Email" value={form.email}
                  onChange={e => setForm({ ...form, email: e.target.value })} required />
              </div>
            </>
          )}

          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zt-text-dim" />
            <input className="zt-input pl-10" placeholder="Username" value={form.username}
              onChange={e => setForm({ ...form, username: e.target.value })} required />
          </div>

          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zt-text-dim" />
            <input className="zt-input pl-10" type="password" placeholder="Password" value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })} required minLength={8} />
          </div>

          <button type="submit" disabled={loading}
            className="zt-btn zt-btn-primary w-full justify-center py-3">
            {loading ? 'Processing...' : isRegister ? 'Create Account' : 'Sign In'}
            <ArrowRight className="w-4 h-4" />
          </button>

          <p className="text-center text-sm text-zt-text-dim">
            {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button type="button" onClick={() => { setIsRegister(!isRegister); setError(''); }}
              className="text-zt-cyan hover:underline">
              {isRegister ? 'Sign In' : 'Register'}
            </button>
          </p>
        </form>
      </div>
    </div>
  );
}
