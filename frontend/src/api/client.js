/* ═══════════════════════════════════════════════════════════════════════════
   API Client — Centralized fetch wrapper with RESILIENCE
   
   GUARANTEES:
   • 10-second timeout on ALL requests (never hangs forever)
   • 60-second timeout for LLM-heavy endpoints (report generation, AI eval)
   • Network errors show friendly messages (not raw exceptions)
   • Auto-refresh on 401 (token expiry)
   • Console logging for easy debugging
   ═══════════════════════════════════════════════════════════════════════════ */

export const BASE = '/api/v1';
const REQUEST_TIMEOUT = 10000; // 10 seconds
const LONG_REQUEST_TIMEOUT = 60000; // 60 seconds for LLM-heavy endpoints

function getToken() { return localStorage.getItem('access_token') || ''; }
function getRefresh() { return localStorage.getItem('refresh_token') || ''; }

/* ── Timeout Helper ────────────────────────────────────────────────────── */
function fetchWithTimeout(url, opts = {}, timeout = REQUEST_TIMEOUT) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  return fetch(url, { ...opts, signal: controller.signal })
    .finally(() => clearTimeout(timer));
}

/* ── Auto-refresh on 401 ───────────────────────────────────────────────── */
let _refreshing = false;
let _queue = [];

async function doRefresh() {
  const rt = getRefresh();
  if (!rt) { logout(); return null; }
  try {
    const r = await fetchWithTimeout(`${BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: rt }),
    }, 5000);
    if (!r.ok) { logout(); return null; }
    const data = await r.json();
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data.access_token;
  } catch {
    logout();
    return null;
  }
}

function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  window.location.hash = '#/login';
}

/* ── Core fetch with auth and retry ────────────────────────────────────── */
export async function apiFetch(path, opts = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
    ...(opts.headers || {}),
  };

  let res;
  try {
    res = await fetchWithTimeout(`${BASE}${path}`, { ...opts, headers });
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('Server not responding (timeout). Please check if the backend is running.');
    }
    if (!navigator.onLine) {
      throw new Error('You are offline. Please check your internet connection.');
    }
    throw new Error('Cannot reach server. Please ensure the backend is running on port 8000.');
  }

  // Handle 401 with auto-refresh
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

/* ── JSON response handler ─────────────────────────────────────────────── */
export async function apiJSON(path, opts = {}) {
  const res = await apiFetch(path, opts);
  if (!res.ok) {
    let msg = `Request failed (HTTP ${res.status})`;
    try {
      const d = await res.json();
      if (typeof d.detail === 'string') {
        msg = d.detail;
      } else if (Array.isArray(d.detail)) {
        msg = d.detail.map(e => e.msg || e.message || JSON.stringify(e)).join('; ');
      } else if (d.detail) {
        msg = typeof d.detail === 'object' ? JSON.stringify(d.detail) : String(d.detail);
      } else if (d.message) {
        msg = typeof d.message === 'object' ? JSON.stringify(d.message) : String(d.message);
      }
    } catch { /* ignore parse errors */ }
    console.warn(`[API ERROR] ${opts.method || 'GET'} ${path} → ${res.status}: ${msg}`);
    throw new Error(msg);
  }
  return res.json();
}

/* ── Long-timeout JSON request (for LLM-heavy endpoints like report generation) ── */
export async function apiFetchLong(path, opts = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
    ...(opts.headers || {}),
  };

  let res;
  try {
    res = await fetchWithTimeout(`${BASE}${path}`, { ...opts, headers }, LONG_REQUEST_TIMEOUT);
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('Report generation timed out. Ollama may be slow — try again or check if Ollama is running.');
    }
    throw new Error('Cannot reach server. Please ensure the backend is running on port 8000.');
  }

  // Handle 401 with auto-refresh
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
    return apiFetchLong(path, { ...opts, _retry: true });
  }

  if (!res.ok) {
    let msg = `Request failed (HTTP ${res.status})`;
    try { const d = await res.json(); msg = d.detail || d.message || msg; } catch {}
    throw new Error(msg);
  }
  return res.json();
}

/* ── Multipart upload (file upload) ────────────────────────────────────────────── */
export async function apiUpload(path, formData) {
  const headers = getToken() ? { Authorization: `Bearer ${getToken()}` } : {};

  let res;
  try {
    res = await fetchWithTimeout(`${BASE}${path}`, {
      method: 'POST',
      headers,
      body: formData,
    }, 30000); // 30s timeout for file uploads
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('Upload timed out. The file may be too large.');
    }
    throw new Error('Cannot reach server for upload. Please ensure the backend is running.');
  }

  // Handle 401 with refresh
  if (res.status === 401) {
    const newToken = await doRefresh();
    if (newToken) {
      res = await fetchWithTimeout(`${BASE}${path}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${newToken}` },
        body: formData,
      }, 30000);
    }
  }

  if (!res.ok) {
    let msg = `Upload failed (HTTP ${res.status})`;
    try { 
      const d = await res.json(); 
      if (typeof d.detail === 'string') msg = d.detail;
      else if (Array.isArray(d.detail)) msg = d.detail.map(e => e.msg).join('; ');
      else if (d.detail) msg = JSON.stringify(d.detail);
      else if (d.message) msg = d.message;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}
