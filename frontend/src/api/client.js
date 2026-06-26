/* ─────────────────────────────────────────────────
   API client — centralised fetch wrapper
   All requests go to /api/v1/* (proxied by Vite → localhost:8000)
───────────────────────────────────────────────── */

export const BASE = '/api/v1';

function getToken() { return localStorage.getItem('access_token') || ''; }
function getRefresh(){ return localStorage.getItem('refresh_token') || ''; }

/* Interceptor: auto-refresh on 401 */
let _refreshing = false;
let _queue = [];

async function doRefresh() {
  const rt = getRefresh();
  if (!rt) { logout(); return null; }
  const r = await fetch(`${BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: rt }),
  });
  if (!r.ok) { logout(); return null; }
  const data = await r.json();
  localStorage.setItem('access_token',  data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  return data.access_token;
}

function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  window.location.hash = '#/login';
}

export async function apiFetch(path, opts = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
    ...(opts.headers || {}),
  };

  let res = await fetch(`${BASE}${path}`, { ...opts, headers });

  if (res.status === 401 && !opts._retry) {
    if (_refreshing) {
      await new Promise(r => _queue.push(r));
    } else {
      _refreshing = true;
      await doRefresh();
      _refreshing = false;
      _queue.forEach(r => r());
      _queue = [];
    }
    return apiFetch(path, { ...opts, _retry: true });
  }

  return res;
}

export async function apiJSON(path, opts = {}) {
  const res = await apiFetch(path, opts);
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const d = await res.json(); msg = d.detail || d.message || msg; } catch {}
    throw new Error(msg);
  }
  return res.json();
}

/* ── Multipart (file upload) ── */
export async function apiUpload(path, formData) {
  const headers = getToken() ? { Authorization: `Bearer ${getToken()}` } : {};

  let res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers,
    body: formData,
  });

  // If 401, try refreshing token and retry
  if (res.status === 401) {
    const newToken = await doRefresh();
    if (newToken) {
      res = await fetch(`${BASE}${path}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${newToken}` },
        body: formData,
      });
    }
  }

  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const d = await res.json(); msg = d.detail || msg; } catch {}
    throw new Error(msg);
  }
  return res.json();
}
