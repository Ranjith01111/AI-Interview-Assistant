/* Session Summary Page — View a completed interview session's results */
import { renderNavbar } from '../components/Navbar.js';
import { interview } from '../api/index.js';
import { navigate } from '../main.js';
import { Toast } from '../components/Toast.js';

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export async function renderSessionSummaryPage(container, sessionId) {
  container.innerHTML = '';
  renderNavbar(container);

  const main = document.createElement('div');
  main.className = 'app-main';
  main.innerHTML = `
    <div class="page-content" style="max-width:800px;margin:0 auto;padding:var(--spacing-lg)">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:var(--spacing-lg)">
        <button class="btn btn-ghost" id="back-btn" style="padding:6px 12px">← Back</button>
        <h1 style="font-size:1.5rem;margin:0">Interview Summary</h1>
      </div>
      <div id="summary-content">
        <div style="text-align:center;padding:40px">
          <div class="spinner"></div>
          <p style="color:var(--text-muted);margin-top:12px">Loading session summary…</p>
        </div>
      </div>
    </div>
  `;
  container.appendChild(main);

  main.querySelector('#back-btn').onclick = () => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.role === 'recruiter' || user.role === 'admin') {
      navigate('/recruiter');
    } else {
      navigate('/dashboard');
    }
  };

  const content = main.querySelector('#summary-content');

  try {
    const data = await interview.getSummary(sessionId);

    if (!data || (!data.score_breakdown && !data.questions && !data.average_score && !data.summary)) {
      content.innerHTML = `
        <div class="card" style="padding:24px;text-align:center">
          <div style="font-size:2rem;margin-bottom:12px">📋</div>
          <h3>No Summary Available</h3>
          <p style="color:var(--text-muted)">This session hasn't been completed yet or no data is available.</p>
        </div>
      `;
      return;
    }

    const score = data.average_score ?? data.summary?.average_score ?? 0;
    const status = data.status || 'completed';
    const recommendation = data.recommendation || data.summary?.recommendation || '—';
    const questions = data.score_breakdown || data.questions || data.summary?.questions || [];
    const scoreColor = score >= 8 ? 'var(--accent-emerald)' : score >= 6.5 ? 'var(--accent-gold)' : score >= 5 ? 'var(--accent-amber)' : 'var(--accent-red)';

    let questionsHtml = '';
    if (questions.length > 0) {
      questionsHtml = questions.map((q, i) => {
        const qScore = q.score ?? 0;
        const qColor = qScore >= 8 ? 'var(--accent-emerald)' : qScore >= 6 ? 'var(--accent-gold)' : qScore >= 4 ? 'var(--accent-amber)' : 'var(--accent-red)';
        const qTitle = q.category || q.question_text || q.question || 'Question';
        const qText = q.question || q.question_text || '';
        return `
          <div class="card" style="padding:14px;margin-bottom:8px;border-left:3px solid ${qColor}">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <span style="font-weight:600;font-size:0.85rem">Q${i + 1}: ${escapeHtml(qTitle.slice(0, 60))}</span>
              <span style="font-weight:700;color:${qColor}">${qScore.toFixed(1)}/10</span>
            </div>
            <div style="font-size:0.82rem;color:var(--text-secondary);margin-bottom:6px"><strong>Q:</strong> ${escapeHtml(qText.slice(0, 200))}</div>
            ${q.answer ? `<div style="font-size:0.8rem;color:var(--text-muted);background:var(--bg-tertiary);padding:8px;border-radius:6px;margin-bottom:6px"><strong>A:</strong> ${escapeHtml(q.answer.slice(0, 300))}${q.answer.length > 300 ? '…' : ''}</div>` : ''}
            ${q.feedback ? `<div style="font-size:0.78rem;color:var(--accent-amber)">💡 ${escapeHtml(q.feedback)}</div>` : ''}
            ${q.strengths ? `<div style="font-size:0.78rem;color:var(--accent-emerald);margin-top:4px">✅ ${escapeHtml(Array.isArray(q.strengths) ? q.strengths.join(', ') : q.strengths)}</div>` : ''}
            ${q.improvements ? `<div style="font-size:0.78rem;color:var(--accent-amber);margin-top:2px">📈 ${escapeHtml(Array.isArray(q.improvements) ? q.improvements.join(', ') : q.improvements)}</div>` : ''}
          </div>
        `;
      }).join('');
    }

    content.innerHTML = `
      <!-- Score Card -->
      <div class="card" style="padding:24px;text-align:center;margin-bottom:16px">
        <div style="font-size:3rem;font-weight:800;color:${scoreColor}">${score.toFixed(1)}/10</div>
        <div style="font-size:1.1rem;font-weight:600;color:${scoreColor};margin-top:4px">${recommendation}</div>
        ${data.overall_feedback ? `<p style="color:var(--text-secondary);margin-top:12px;font-size:0.9rem;max-width:500px;margin-left:auto;margin-right:auto">${escapeHtml(data.overall_feedback)}</p>` : ''}
        <div style="font-size:0.8rem;color:var(--text-muted);margin-top:8px">
          Session: ${sessionId.slice(0, 8)}… • Status: <span class="badge ${status === 'completed' ? 'badge-emerald' : 'badge-gray'}">${status}</span>
        </div>
      </div>

      <!-- Questions Breakdown -->
      ${questions.length > 0 ? `
        <h3 style="margin-bottom:12px;font-size:1rem">📝 Question Breakdown (${questions.length})</h3>
        ${questionsHtml}
      ` : ''}
    `;
  } catch (err) {
    content.innerHTML = `
      <div class="card" style="padding:24px;text-align:center">
        <div style="font-size:2rem;margin-bottom:12px">⚠️</div>
        <h3>Failed to Load Summary</h3>
        <p style="color:var(--text-muted)">${escapeHtml(err.message)}</p>
        <button class="btn btn-secondary" style="margin-top:12px" id="retry-btn">Retry</button>
      </div>
    `;
    content.querySelector('#retry-btn').onclick = () => renderSessionSummaryPage(container, sessionId);
  }
}
