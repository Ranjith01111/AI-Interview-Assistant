/* Step 5 — Final Cumulative Summary (Interview + Coding) */
import { interview } from '../../api/index.js';
import { Toast } from '../../components/Toast.js';
import { navigate } from '../../main.js';

export async function renderStep5(container, state) {
  // Explicitly ensure fullscreen is exited when arriving at the summary
  if (document.fullscreenElement || document.webkitFullscreenElement) {
    try {
      if (document.exitFullscreen) await document.exitFullscreen();
      else if (document.webkitExitFullscreen) await document.webkitExitFullscreen();
    } catch (e) {}
  }

  container.innerHTML = `
    <div class="step-container slide-up">
      <div id="summary-loading" style="text-align:center;padding:var(--spacing-2xl)">
        <div style="font-size:3rem;animation:spin 1.5s linear infinite;display:inline-block">📊</div>
        <p style="margin-top:var(--spacing-md)">Generating your comprehensive report…</p>
      </div>
      <div id="summary-content" style="display:none"></div>
    </div>
  `;

  try {
    const data = await interview.getSummary(state.sessionId);
    // Merge client-side coding score
    data._clientCodingScore = state.codingScore ?? null;
    data._interviewScore = state.interviewScore ?? data.average_score ?? 0;
    container.querySelector('#summary-loading').style.display = 'none';
    renderSummary(container.querySelector('#summary-content'), data, state);
  } catch (err) {
    container.querySelector('#summary-loading').innerHTML = `<div class="alert alert-error">${err.message}</div>`;
    Toast.error(err.message, 'Summary Error');
  }
}

function renderSummary(el, data, state) {
  const interviewScore = state.interviewScore ?? data.average_score ?? 0;
  
  const codingEntries = data.coding_submissions || [];
  let codingScoreRaw = state.codingScore;
  if (codingScoreRaw === undefined || codingScoreRaw === null) {
    codingScoreRaw = codingEntries.length 
      ? Math.round(codingEntries.reduce((acc, curr) => acc + curr.score, 0) / codingEntries.length)
      : 0;
  }
  
  const codingScore10 = codingScoreRaw / 10; // convert to /10 scale
  const hasCoding = true; // Coding is now always part of the mandatory flow

  // Weights
  const iWeight = hasCoding ? 60 : 100;
  const cWeight = hasCoding ? 40 : 0;
  const finalScore = hasCoding
    ? (interviewScore * 0.6) + (codingScore10 * 0.4)
    : interviewScore;

  const isPass = finalScore >= 7.0;
  const ringColor = isPass ? '#10b981' : finalScore >= 5 ? '#f59e0b' : '#ef4444';
  const circum = 2 * Math.PI * 54;


  el.style.display = '';
  el.innerHTML = `
    <div class="card mb-lg">
      <div class="card-body summary-header">
        <h2 style="margin-bottom:var(--spacing-xl)">🎉 Final Report — ${data.candidate_name || 'Candidate'}</h2>

        <!-- Score ring -->
        <div class="score-ring-wrap">
          <svg viewBox="0 0 120 120" width="160" height="160">
            <circle class="score-ring-bg" cx="60" cy="60" r="54"/>
            <circle class="score-ring-fill" cx="60" cy="60" r="54"
              stroke="${ringColor}"
              stroke-dasharray="${circum}"
              stroke-dashoffset="${circum}"
              id="ring-fill"/>
          </svg>
          <div class="score-ring-text">
            <div class="score-ring-num" style="color:${ringColor}">${finalScore.toFixed(1)}</div>
            <div class="score-ring-label">Final Score</div>
          </div>
        </div>

        <!-- Recommendation -->
        <div class="recommendation-badge ${isPass ? 'pass' : 'fail'}">
          ${isPass ? '✅ PASS — HR will contact you soon 👍' : '❌ FAIL — Keep practising!'}
        </div>

        <!-- Panel Scores Breakdown -->
        <div class="panel-scores-grid">
          <div class="panel-score-card interview-panel-card">
            <div class="panel-score-icon">💬</div>
            <div class="panel-score-val" style="color:var(--accent-gold)">${interviewScore.toFixed(1)}<small>/10</small></div>
            <div class="panel-score-label">Interview Panel</div>
            <div class="panel-score-weight">${iWeight}% weight</div>
          </div>
          ${hasCoding ? `
          <div class="panel-score-card coding-panel-card">
            <div class="panel-score-icon">💻</div>
            <div class="panel-score-val" style="color:var(--accent-emerald)">${codingScore10.toFixed(1)}<small>/10</small></div>
            <div class="panel-score-label">Coding Panel</div>
            <div class="panel-score-weight">${cWeight}% weight</div>
          </div>
          ` : ''}
          <div class="panel-score-card final-panel-card">
            <div class="panel-score-icon">📊</div>
            <div class="panel-score-val" style="color:${ringColor}">${finalScore.toFixed(1)}<small>/10</small></div>
            <div class="panel-score-label">Cumulative</div>
            <div class="panel-score-weight">Weighted Final</div>
          </div>
        </div>

        <!-- Overall feedback -->
        <div class="card" style="text-align:left;margin-bottom:var(--spacing-lg)">
          <div class="card-header"><span>💬</span><h3>Overall Feedback</h3></div>
          <div class="card-body">
            <p style="white-space:pre-line;font-size:0.9rem">${data.overall_feedback || 'No feedback available.'}</p>
          </div>
        </div>

        <!-- Interview Q&A breakdown -->
        <div style="text-align:left;margin-bottom:var(--spacing-lg)">
          <h3 style="margin-bottom:var(--spacing-md)">💬 Interview Panel — Question Breakdown</h3>
          <div id="accordion-list">
            ${(data.score_breakdown || []).map((q, i) => `
              <div class="accordion-item">
                <div class="accordion-header" onclick="this.nextElementSibling.classList.toggle('open');this.querySelector('.acc-arrow').textContent = this.nextElementSibling.classList.contains('open') ? '▲' : '▼'">
                  <div style="flex:1">
                    <span style="font-weight:600;font-size:0.9rem">Q${q.question_number}${q.is_follow_up ? ' <span class="badge badge-cyan" style="font-size:0.65rem">Follow-up</span>' : ''}: ${(q.question||'').substring(0,80)}${q.question?.length > 80 ? '…' : ''}</span>
                  </div>
                  <div style="display:flex;align-items:center;gap:8px">
                    <span style="font-weight:700;color:${q.score>=7?'var(--accent-emerald)':q.score>=5?'var(--accent-amber)':'var(--accent-red)'}">${q.score}/10</span>
                    <span class="acc-arrow" style="color:var(--text-muted);font-size:0.8rem">▼</span>
                  </div>
                </div>
                <div class="accordion-body">
                  <div style="margin-bottom:8px"><strong>Strengths:</strong> ${(q.strengths||[]).join(', ') || 'None noted'}</div>
                  <div><strong>Improvements:</strong> ${(q.improvements||[]).join(', ') || 'None noted'}</div>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Coding Panel breakdown -->
        ${hasCoding ? `
          <div style="text-align:left;margin-bottom:var(--spacing-lg)">
            <h3 style="margin-bottom:var(--spacing-md)">💻 Coding Panel — Challenge Results</h3>
            <div class="coding-results-grid">
              ${codingEntries.length ? codingEntries.map(s => `
                <div class="card mb-md">
                  <div class="card-body">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                      <div><strong>${s.challenge_title || 'Challenge'}</strong> <span class="badge badge-cyan" style="font-size:0.7rem">${s.language}</span></div>
                      <div style="font-weight:700;color:${s.score >= 70?'var(--accent-emerald)':s.score >= 40?'var(--accent-amber)':'var(--accent-red)'}">${s.score}/100</div>
                    </div>
                    <div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px">Status: ${s.status}</div>
                  </div>
                </div>
              `).join('') : `
                <div class="card mb-md">
                  <div class="card-body" style="text-align:center;color:var(--text-muted)">
                    <p>Coding score: <strong>${state.codingScore}/100</strong> (${codingScore10.toFixed(1)}/10)</p>
                  </div>
                </div>
              `}
            </div>
          </div>
        ` : ''}

        <div style="display:flex;gap:var(--spacing-md);justify-content:center;flex-wrap:wrap">
          <button class="btn btn-primary" onclick="window.location.hash='#/dashboard'">← Back to Dashboard</button>
          <button class="btn btn-secondary" onclick="window.print()">🖨 Print Report</button>
        </div>
      </div>
    </div>
  `;

  // Animate ring
  requestAnimationFrame(() => {
    setTimeout(() => {
      const ring = el.querySelector('#ring-fill');
      if (ring) ring.style.strokeDashoffset = String(circum - (finalScore / 10) * circum);
    }, 100);
  });
}
