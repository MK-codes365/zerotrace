import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('zt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ═══════════════════════════════════════════════════════
// Auth
// ═══════════════════════════════════════════════════════

export const authAPI = {
  register: (data: { username: string; email: string; password: string; full_name: string; role?: string }) =>
    api.post('/auth/register', data),
  login: (data: { username: string; password: string }) =>
    api.post('/auth/login', data),
};

// ═══════════════════════════════════════════════════════
// Cases
// ═══════════════════════════════════════════════════════

export const casesAPI = {
  list: (params?: Record<string, unknown>) => api.get('/cases', { params }),
  get: (id: string) => api.get(`/cases/${id}`),
  create: (data: { title: string; description?: string }) => api.post('/cases', data),
};

// ═══════════════════════════════════════════════════════
// Evidence
// ═══════════════════════════════════════════════════════

export const evidenceAPI = {
  get: (id: string) => api.get(`/evidence/${id}`),
  create: (data: Record<string, unknown>) => api.post('/evidence', data),
  hash: (id: string) => api.post(`/evidence/${id}/hash`),
};

// ═══════════════════════════════════════════════════════
// Jobs
// ═══════════════════════════════════════════════════════

export const jobsAPI = {
  list: (params?: Record<string, unknown>) => api.get('/jobs', { params }),
  get: (id: string) => api.get(`/jobs/${id}`),
};

// ═══════════════════════════════════════════════════════
// Recovery
// ═══════════════════════════════════════════════════════

export const recoveryAPI = {
  start: (data: { evidence_id: string; case_id?: string; file_types?: string[] }) =>
    api.post('/recovery', data),
  getFiles: (jobId: string) => api.get(`/recovery/${jobId}/files`),
};

// ═══════════════════════════════════════════════════════
// Sanitization
// ═══════════════════════════════════════════════════════

export const sanitizationAPI = {
  preview: (data: { target_path: string; target_type?: string }) =>
    api.post('/sanitization/preview', data),
  execute: (data: {
    target_path: string; target_type: string; method: string;
    confirmation_text: string; second_confirmation: boolean; operator: string;
  }) => api.post('/sanitization/execute', data),
  verify: (operationId: string) => api.post(`/sanitization/${operationId}/verify`),
};

// ═══════════════════════════════════════════════════════
// Integrity
// ═══════════════════════════════════════════════════════

export const integrityAPI = {
  verify: (data: { evidence_id: string }) => api.post('/integrity/verify', data),
};

// ═══════════════════════════════════════════════════════
// Audit
// ═══════════════════════════════════════════════════════

export const auditAPI = {
  list: (params?: Record<string, unknown>) => api.get('/audit', { params }),
};

// ═══════════════════════════════════════════════════════
// Reports
// ═══════════════════════════════════════════════════════

export const reportsAPI = {
  generate: (data: { case_id: string; report_type?: string; format?: string; title?: string }) =>
    api.post('/reports', data),
  get: (id: string) => api.get(`/reports/${id}`),
};

// ═══════════════════════════════════════════════════════
// Dashboard
// ═══════════════════════════════════════════════════════

export const dashboardAPI = {
  stats: () => api.get('/dashboard/stats'),
};

// ═══════════════════════════════════════════════════════
// Demo
// ═══════════════════════════════════════════════════════

export const demoAPI = {
  run: (data?: { scenario?: string }) => api.post('/demo/run', data || {}),
};

// ═══════════════════════════════════════════════════════
// Health
// ═══════════════════════════════════════════════════════

export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;
