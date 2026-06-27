/* Candidate Dashboard — Clean Home with 3-dot Recent Sessions */
import { renderNavbar } from '../components/Navbar.js';
import { analytics } from '../api/index.js';
import { navigate } from '../main.js';
import { Toast } from '../components/Toast.js';

export async function renderCandidateDashboard(container) {
  container.innerHTML = '';
  renderNavbar(container);

  const main = document.createElement('div');
  main.className = 'app-main';
  main.innerHTML = `
    <div class="page-content candidate-dashboard">
      <!-- Top-right 3-dot menu -->
      <div class="three-dot-menu" id="three-dot-menu">
        <button class="three-dot-btn" id="three-dot-btn" title="Recent Sessions">⋮</button>
        <div class="three-dot-popup" id="three-dot-popup" style="display:none">
          <div class="popup-header">
            <span>📋 Recent Sessions</span>
            <button class="popup-close" id="popup-close">✕</button>
          </div>
          <div class="popup-body" id="recent-sessions-list">
            <div class="skeleton" style="height:40px;border-radius:8px;margin-bottom:6px"></div>
            <div class="skeleton" style="height:40px;border-radius:8px;margin-bottom:6px"></div>
            <div class="skeleton" style="height:40px;border-radius:8px"></div>
          </div>
        </div>
      </div>

      <!-- Main content — clean & centered -->
      <div class="home-hero">
        <div class="hero-icon">🤖</div>
        <h1 class="hero-title">AI Interview Assistant</h1>
        <p class="hero-subtitle">Choose your interview mode to get started</p>

        <div class="interview-mode-cards">
          <div class="mode-card" id="new-interview-btn">
            <div class="mode-icon">💬</div>
            <h3>Text Interview</h3>
            <p>Resume-based interview with AI-generated questions, coding challenges, and detailed feedback</p>
            <span class="mode-tag">Interview + Coding</span>
          </div>
          <div class="mode-card voice-mode" id="voice-interview-btn">
            <div class="mode-icon">🎤</div>
            <h3>Voice Interview</h3>
            <p>HR-style phone call simulation to evaluate communication skills and fluency</p>
            <span class="mode-tag">Communication</span>
          </div>
        </div>

        <!-- Resume active session banner -->
        <div id="resume-banner" style="display:none" class="resume-banner">
          <span>⏸️ You have an active session in progress</span>
          <button class="btn btn-primary btn-sm" id="resume-session-btn">Resume →</button>
          <button class="btn btn-ghost btn-sm" id="discard-session-btn" style="color:var(--accent-red)">Discard</button>
        </div>
      </div>
    </div>
  `;
  container.appendChild(main);

  /* Event handlers */
  main.querySelector('#new-interview-btn').onclick = () => navigate('/interview');
  main.querySelector('#voice-interview-btn').onclick = () => navigate('/voice-interview');

  /* Check for active session to resume */
  const savedSession = localStorage.getItem('interview_session_state');
  if (savedSession) {
    try {
      const sess = JSON.parse(savedSession);
      if (sess.sessionId && sess.currentStep !== undefined) {
        const banner = main.querySelector('#resume-banner');
        banner.style.display = 'flex';
        main.querySelector('#resume-session-btn').onclick = () => navigate('/interview?resume=true');
        main.querySelector('#discard-session-btn').onclick = () => {
          localStorage.removeItem('interview_session_state');
          banner.style.display = 'none';
          Toast.success('Previous session discarded', 'Cleared');
        };
      }
    } catch(e) {}
  }

  /* Three-dot menu toggle */
  const threeBtn = main.querySelector('#three-dot-btn');
  const popup = main.querySelector('#three-dot-popup');
  const _closePopupHandler = (e) => {
    if (!popup.contains(e.target) && e.target !== threeBtn) popup.style.display = 'none';
  };
  threeBtn.onclick = (e) => {
    e.stopPropagation();
    popup.style.display = popup.style.display === 'none' ? 'block' : 'none';
    if (popup.style.display === 'block') loadRecentSessions();
  };
  main.querySelector('#popup-close').onclick = () => { popup.style.display = 'none'; };
  document.addEventListener('click', _closePopupHandler);

  /* Cleanup listener on navigation (called by hash change) */
  container._cleanup = () => {
    document.removeEventListener('click', _closePopupHandler);
  };

  /* Load recent sessions into popup */
  async function loadRecentSessions() {
    const listEl = main.querySelector('#recent-sessions-list');
    try {
      const history = await analytics.history();
      const sessions = history?.sessions || history || [];
      const completedSessions = sessions.filter(s => s.status === 'completed');
      if (!completedSessions.length) {
        listEl.innerHTML = `<div style="text-align:center;padding:16px;color:var(--text-muted);font-size:0.85rem">No completed sessions yet</div>`;
        return;
      }
      listEl.innerHTML = '';
      completedSessions.slice(0, 10).forEach(s => {
        const score = s.average_score;
        const hasScore = score !== null && score !== undefined;
        const scoreVal = hasScore ? Number(score) : 0;
        const date = s.created_at ? new Date(s.created_at).toLocaleDateString('en-GB', { day:'numeric', month:'short' }) : '—';
        const recommendation = s.recommendation || 'Completed';
        const recColor = recommendation.toLowerCase().includes('strong') ? 'badge-emerald' :
                          recommendation.toLowerCase().includes('no') ? 'badge-red' :
                          recommendation.toLowerCase().includes('hire') ? 'badge-amber' : 'badge-emerald';
        const item = document.createElement('div');
        item.className = 'recent-session-item';
        item.innerHTML = `
          <div class="rs-info">
            <span class="rs-date">${date}</span>
            <span class="rs-status badge ${recColor}">${recommendation}</span>
          </div>
          <span class="rs-score" style="color:${scoreVal >= 7 ? 'var(--accent-emerald)' : scoreVal >= 5 ? 'var(--accent-amber)' : 'var(--text-muted)'}">${hasScore ? scoreVal.toFixed(1) + '/10' : 'View →'}</span>
        `;
        item.onclick = () => navigate(`/interview/summary/${s.session_id}`);
        listEl.appendChild(item);
      });
    } catch (err) {
      listEl.innerHTML = `<div style="padding:12px;color:var(--accent-red);font-size:0.8rem">${err.message}</div>`;
    }
  }
}
