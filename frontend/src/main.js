/* ═══════════════════════════════════════════════════════════
   AI Interview Assistant — Main Entry Point
   Golden Yellow Edition ✨
   ═══════════════════════════════════════════════════════════ */

// ── Import ALL stylesheets (Vite requires explicit CSS imports) ──
import './styles/main.css';
import './styles/auth.css';
import './styles/components.css';
import './styles/interview.css';
import './styles/dashboard.css';

// ── Page renderers ──
import { renderLoginPage } from './pages/LoginPage.js';
import { renderCandidateDashboard } from './pages/CandidateDashboard.js';
import { renderInterviewFlow } from './pages/InterviewFlow.js';
import { renderRecruiterDashboard } from './pages/RecruiterDashboard.js';
import { renderAnalyticsDashboard } from './pages/AnalyticsDashboard.js';
import { renderVoiceInterview } from './pages/VoiceInterview.js';

export function navigate(path) {
  window.location.hash = path;
}

function getRoute() {
  const hash = window.location.hash || '#/login';
  return hash.replace(/^#/, '');
}

async function handleRoute() {
  const path = getRoute();
  const app = document.getElementById('app');
  
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
    if (path.startsWith('/login')) {
      renderLoginPage(app);
    } else if (path.startsWith('/dashboard')) {
      await renderCandidateDashboard(app);
    } else if (path.startsWith('/voice-interview')) {
      await renderVoiceInterview(app);
    } else if (path.startsWith('/interview')) {
      renderInterviewFlow(app);
    } else if (path.startsWith('/recruiter')) {
      await renderRecruiterDashboard(app);
    } else if (path.startsWith('/analytics')) {
      await renderAnalyticsDashboard(app);
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
    console.error('Route error:', err);
    app.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:center;min-height:100vh;flex-direction:column;gap:16px;">
        <div style="font-size:4rem;">⚠️</div>
        <h2 style="color:var(--accent-red);">Something went wrong</h2>
        <p style="color:var(--text-secondary);">${err.message}</p>
        <button class="btn btn-secondary" onclick="location.reload()">Reload Page</button>
      </div>`;
  }
}

window.addEventListener('hashchange', handleRoute);

// Initialize app
window.addEventListener('DOMContentLoaded', () => {
  if (window.__stopLoader) window.__stopLoader();
  handleRoute();
});
