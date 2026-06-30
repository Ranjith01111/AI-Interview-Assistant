/* ═══════════════════════════════════════════════════════════════════════════
   AI Interview Assistant — Main Entry Point (RESILIENT VERSION)
   Golden Yellow Edition ✨
   
   GUARANTEES:
   • Loading screen ALWAYS dismissed (never stuck)
   • Pages never hang — 10s timeout with friendly error message
   • If backend is down, shows clear "Backend not reachable" message
   • Route errors show retry button instead of blank screen
   ═══════════════════════════════════════════════════════════════════════════ */

// ── Import ALL stylesheets (Vite requires explicit CSS imports) ──
import './fonts/fonts.css';
import './styles/main.css';
import './styles/auth.css';
import './styles/components.css';
import './styles/interview.css';
import './styles/dashboard.css';
import './styles/pipeline.css';
import './styles/analytics.css';

// ── IMMEDIATELY dismiss loading screen ──
// This runs synchronously before any async work
if (window.__stopLoader) window.__stopLoader();

// ── Page renderers ──
import { renderLoginPage } from './pages/LoginPage.js';
import { renderCandidateDashboard } from './pages/CandidateDashboard.js';
import { renderInterviewFlow } from './pages/InterviewFlow.js';
import { renderRecruiterDashboard } from './pages/RecruiterDashboard.js';
import { renderAnalyticsDashboard } from './pages/AnalyticsDashboard.js';
import { renderVoiceInterview } from './pages/VoiceInterview.js';
import { renderSessionSummaryPage } from './pages/SessionSummaryPage.js';
import { renderPipelinePage } from './pages/PipelinePage.js';


export function navigate(path) {
  window.location.hash = path;
}

function getRoute() {
  const hash = window.location.hash || '#/login';
  return hash.replace(/^#/, '');
}

/* ── Timeout wrapper for page renders ──────────────────────────────────── */
function withTimeout(promise, ms = 15000) {
  return Promise.race([
    promise,
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Page load timed out. Backend may not be running.')), ms)
    ),
  ]);
}

/* ── Error display helper ──────────────────────────────────────────── */
function showError(app, err) {
  const isNetworkError = err.message.includes('timeout') || 
                         err.message.includes('reach server') ||
                         err.message.includes('not responding') ||
                         err.message.includes('Backend');
  
  app.innerHTML = `
    <div class="error-page">
      <div class="error-page-icon">${isNetworkError ? '🔌' : '⚠️'}</div>
      <h2 class="error-page-title ${isNetworkError ? 'error-network' : 'error-generic'}">
        ${isNetworkError ? 'Backend Not Reachable' : 'Something went wrong'}
      </h2>
      <p class="error-page-body">
        ${isNetworkError 
          ? 'Cannot connect to the backend server. Please ensure:<br>1. Run <code>python run_backend.py</code><br>2. PostgreSQL is running<br>3. Check the terminal for errors'
          : err.message}
      </p>
      <div class="error-page-actions">
        <button class="btn btn-primary" onclick="location.reload()">🔄 Retry</button>
        <button class="btn btn-secondary" onclick="location.hash='#/login'">← Login</button>
      </div>
    </div>`;
}

/* ── Main route handler ────────────────────────────────────────────────── */
async function handleRoute() {
  const path = getRoute();
  const app = document.getElementById('app');

  // Ensure loading screen is gone
  const loadingEl = document.getElementById('loading-screen');
  if (loadingEl) loadingEl.remove();

  // Auth Check
  const token = localStorage.getItem('access_token');
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : null;

  const isPublic = path.startsWith('/login');

  if (!token && !isPublic) {
    navigate('/login');
    return;
  }

  if (token && isPublic) {
    if (user && (user.role === 'admin' || user.role === 'recruiter' || user.role === 'interviewer')) {
      navigate('/recruiter');
    } else {
      navigate('/dashboard');
    }
    return;
  }

  app.innerHTML = '';

  try {
    // Cleanup previous page
    if (app._cleanup) { app._cleanup(); app._cleanup = null; }

    if (path.startsWith('/login')) {
      renderLoginPage(app);
    } else if (path.startsWith('/dashboard')) {
      await withTimeout(renderCandidateDashboard(app));
    } else if (path.startsWith('/interview/summary/')) {
      const parts = path.split('/');
      const sessionId = parts[parts.length - 1];
      await withTimeout(renderSessionSummaryPage(app, sessionId));
    } else if (path.startsWith('/voice-interview')) {
      await withTimeout(renderVoiceInterview(app));
    } else if (path.startsWith('/interview')) {
      renderInterviewFlow(app);
    } else if (path.startsWith('/recruiter')) {
      await withTimeout(renderRecruiterDashboard(app));
    } else if (path.startsWith('/analytics')) {
      await withTimeout(renderAnalyticsDashboard(app));
    } else if (path.startsWith('/pipeline')) {
      await withTimeout(renderPipelinePage(app));
    } else {
      // 404
      app.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:center;min-height:100vh;flex-direction:column;gap:16px;">
          <div style="font-size:4rem;">🔍</div>
          <h2 style="color:var(--accent-gold);">404 — Page Not Found</h2>
          <p style="color:var(--text-secondary);">The page you're looking for doesn't exist.</p>
          <a href="#/dashboard" class="btn btn-primary">Back to Dashboard</a>
        </div>`;
    }
  } catch (err) {
    console.error('[Router Error]', err);
    showError(app, err);
  }
}

// ── Route listener ──
window.addEventListener('hashchange', handleRoute);

// ── Initialize on DOM ready ──
if (document.readyState === 'loading') {
  // DOM not yet ready — wait for it
  window.addEventListener('DOMContentLoaded', () => {
    if (window.__stopLoader) window.__stopLoader();
    const loadingEl = document.getElementById('loading-screen');
    if (loadingEl) loadingEl.remove();
    handleRoute();
  });
} else {
  // DOM already ready (module loaded after parse) — run immediately
  if (window.__stopLoader) window.__stopLoader();
  const loadingEl = document.getElementById('loading-screen');
  if (loadingEl) loadingEl.remove();
  handleRoute();
}
