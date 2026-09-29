const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    let detail = `Request failed: ${res.status}`;
    try { const body = await res.json(); detail = body.detail || detail; } catch { try { detail = await res.text() || detail; } catch {} }
    const err = new Error(detail); err.status = res.status; throw err;
  }
  return res.json();
}

export const api = {
  stats: () => request('/stats'),
  schemes: (params = '') => request(`/schemes${params ? `?${params}` : ''}`),
  scheme: (id) => request(`/schemes/${encodeURIComponent(id)}`),
  match: (profile) => request('/match-schemes', { method: 'POST', body: JSON.stringify({ profile, limit: 15 }) }),
  calculator: (payload) => request('/calculate-loan', { method: 'POST', body: JSON.stringify(payload) }),
  partners: (payload) => request('/nearby-partners', { method: 'POST', body: JSON.stringify(payload) }),
  roadmap: (id) => request(`/roadmap/${encodeURIComponent(id)}`),
  copilot: (payload) => request('/copilot', { method: 'POST', body: JSON.stringify(payload) }),
  eligibilityGap: (payload) => request('/eligibility-gap', { method: 'POST', body: JSON.stringify(payload) }),
  notifications: () => request('/notifications'),
  addReminder: (payload) => request('/notifications/reminders', { method: 'POST', body: JSON.stringify(payload) }),
};
export { API_BASE };
