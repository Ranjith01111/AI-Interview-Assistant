/* Interview Summary Panel — Shown after interview, asks Continue to Coding or End */
import { interview } from '../../api/index.js';
import { Toast } from '../../components/Toast.js';

export async function renderInterviewSummary(container, state, { onContinue, onEnd }) {
  container.innerHTML = `
    <div class="step-container slide-up">
      <div id="isummary-loading" style="text-align:center;padding:var(--spacing-2xl)">
        <div style="font-size:3rem;animation:spin 1.5s linear infinite;display:inline-block">📊</div>
        <p style="margin-top:var(--spacing-md);color:var(--text-secondary)">Calculating your interview score…</p>
      </div>
      <div id="isummary-content" style="display:none"></div>
    </div>
  `;

  try {
    const data = await interview.getSummary(state.sessionId);
    state.interviewScore = data.average_score ?? 0;
    state.interviewData = data;
    container.querySelector('#isummary-loading').style.display = 'none';
    renderPanel(container.querySelector('#isummary-content'), data, { onContinue, onEnd });
  } catch (err) {
    // Fallback: show basic score
    state.interviewScore = state.interviewScore || 0;
    container.querySelector('#isummary-loading').style.display = 'none';
    renderPanel(container.querySelector('#isummary-content'), {
      average_score: state.interviewScore,
      score_breakdown: [],
      overall_feedback: 'Interview completed.'
    }, { onContinue, onEnd });
    Toast.warning('Could not load full summary, showing partial results.', 'Note');
  }
}

function renderPanel(el, data, { onContinue, onEnd }) {
  const score = data.average_score ?? 0;
  const isPass = score >= 7.0;
  const ringColor = isPass ? '#10b981' : score >= 5 ? '#f59e0b' : '#ef4444';
  const circum = 2 * Math.PI * 54;

  el.style.display = '';
  el.innerHTML = `
    <div class="card mb-lg">
      <div class="card-body" style="text-align:center">
        <h2 style="margin-bottom:var(--spacing-lg)">💬 Interview Panel — Complete</h2>

        <!-- Score ring -->
        <div class="score-ring-wrap">
          <svg viewBox="0 0 120 120" width="140" height="140">
            <circle class="score-ring-bg" cx="60" cy="60" r="54"/>
            <circle class="score-ring-fill" cx="60" cy="60" r="54"
              stroke="${ringColor}"
              stroke-dasharray="${circum}"
              stroke-dashoffset="${circum}"
              id="interview-ring-fill"/>
          </svg>
          <div class="score-ring-text">
            <div class="score-ring-num" style="color:${ringColor}">${score.toFixed(1)}</div>
            <div class="score-ring-label">Interview Score</div>
          </div>
        </div>

        <!-- Quick stats -->
        <div style="display:flex;gap:var(--spacing-lg);justify-content:center;margin:var(--spacing-lg) 0;flex-wrap:wrap">
          <div style="text-align:center">
            <div style="font-size:1.5rem;font-weight:700;color:var(--accent-gold)">${(data.score_breakdown || []).length}</div>
            <div style="font-size:0.75rem;color:var(--text-muted)">Questions</div>
          </div>
          <div style="text-align:center">
            <div style="font-size:1.5rem;font-weight:700;color:var(--accent-emerald)">${(data.score_breakdown || []).filter(q => (q.score || 0) >= 7).length}</div>
            <div style="font-size:0.75rem;color:var(--text-muted)">Strong Answers</div>
          </div>
          <div style="text-align:center">
            <div style="font-size:1.5rem;font-weight:700;color:var(--accent-red)">${(data.score_breakdown || []).filter(q => (q.score || 0) < 5).length}</div>
            <div style="font-size:0.75rem;color:var(--text-muted)">Needs Work</div>
          </div>
        </div>

        <!-- Brief feedback -->
        <div class="card" style="text-align:left;margin-bottom:var(--spacing-xl)">
          <div class="card-body" style="padding:var(--spacing-md)">
            <p style="font-size:0.85rem;color:var(--text-secondary);margin:0;white-space:pre-line">${(data.overall_feedback || 'Good effort! Review the detailed summary at the end.').substring(0, 300)}</p>
          </div>
        </div>

        <!-- Decision buttons -->
        <div class="transition-decision">
          <h3 style="margin-bottom:var(--spacing-md);color:var(--text-primary)">What would you like to do next?</h3>
          <div style="display:flex;gap:var(--spacing-md);justify-content:center;flex-wrap:wrap">
            <button class="btn btn-primary btn-lg" id="continue-coding-btn">
              💻 Continue to Coding Panel →
            </button>
            <button class="btn btn-secondary btn-lg" id="end-session-btn">
              📊 End & View Final Summary
            </button>
          </div>
          <p style="font-size:0.75rem;color:var(--text-muted);margin-top:var(--spacing-md)">
            Coding panel adds to your final cumulative score
          </p>
        </div>
      </div>
    </div>
  `;

  // Animate ring
  requestAnimationFrame(() => {
    setTimeout(() => {
      const ring = el.querySelector('#interview-ring-fill');
      if (ring) ring.style.strokeDashoffset = String(circum - (score / 10) * circum);
    }, 100);
  });

  el.querySelector('#continue-coding-btn').onclick = onContinue;
  el.querySelector('#end-session-btn').onclick = onEnd;
}
