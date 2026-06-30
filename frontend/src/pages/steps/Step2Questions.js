/* Step 2 — Generate Questions (reads interviewConfig from Session Setup) */
import { interview } from '../../api/index.js';
import { Toast } from '../../components/Toast.js';

export async function renderStep2(container, state, onNext) {
  const config = state.interviewConfig || {};
  const presetName = config.preset_id ? _getPresetLabel(config.preset_id) : 'Custom';
  const numQ = config.num_questions || 10;

  container.innerHTML = `
    <div class="step-container slide-up">
      <div class="card">
        <div class="card-header"><span>🧠</span><h3>Generating Your Interview Questions</h3></div>
        <div class="card-body questions-ready" id="q-body">
          <div id="q-loading" style="text-align:center;padding:var(--spacing-2xl)">
            <div style="font-size:3rem;animation:spin 1.5s linear infinite;display:inline-block">⚙️</div>
            <p style="margin-top:var(--spacing-md);color:var(--text-secondary)">
              Generating ${numQ} personalised questions (${presetName} mode)…
            </p>
            ${config.focus_categories?.length ? `<p style="font-size:0.8rem;color:var(--text-muted)">Focus: ${config.focus_categories.join(', ')}</p>` : ''}
          </div>
          <div id="q-ready" style="display:none">
            <div class="check-icon">✅</div>
            <h2>Questions Ready!</h2>
            <p style="margin-top:8px;color:var(--text-muted)">
              Your personalised interview questions have been generated based on your resume and settings.
            </p>

            <!-- Removed total count badge per user request -->

            <div class="setup-summary" style="margin-top:var(--spacing-md)">
              <div class="summary-item">
                <span class="summary-label">Mode</span>
                <span class="summary-value">${presetName}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Difficulty</span>
                <span class="summary-value">${(config.difficulty || 'medium').charAt(0).toUpperCase() + (config.difficulty || 'medium').slice(1)}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Timer</span>
                <span class="summary-value">${config.timer_seconds ? config.timer_seconds + 's/Q' : 'Off'}</span>
              </div>
            </div>
            <div class="alert alert-info" style="margin-top:var(--spacing-md);text-align:left">
              💡 Questions are tailored to your projects, tech stack, and selected focus areas.
              ${config.timer_seconds ? `⏱️ You'll have <strong>${config.timer_seconds} seconds</strong> per question.` : ''}
            </div>
          </div>
        </div>
        <div style="padding:var(--spacing-md) var(--spacing-lg);border-top:1px solid var(--border);display:flex;justify-content:flex-end">
          <button class="btn btn-primary" id="start-btn" disabled>Start Interview →</button>
        </div>
      </div>
    </div>
  `;

  const startBtn = container.querySelector('#start-btn');

  try {
    const data = await interview.generateQuestions(state.sessionId, config);
    state.questions = data.questions || [];
    state.totalQuestions = data.total_questions || state.questions.length;

    // Badge has been removed from UI per user request

    container.querySelector('#q-loading').style.display = 'none';
    container.querySelector('#q-ready').style.display   = '';
    startBtn.disabled = false;
    Toast.success(`${state.totalQuestions} questions generated!`);
  } catch (err) {
    container.querySelector('#q-loading').innerHTML = `
      <div class="alert alert-error">${err.message}</div>
      <button class="btn btn-secondary mt-md" id="retry-btn">Retry</button>
    `;
    container.querySelector('#retry-btn')?.addEventListener('click', () => renderStep2(container, state, onNext));
    Toast.error(err.message, 'Generation Failed');
  }

  startBtn.onclick = onNext;
}

function _getPresetLabel(presetId) {
  const labels = {
    faang_hard: 'FAANG Style',
    startup_practical: 'Startup Style',
    fresher_friendly: 'Fresher Friendly',
    amazon_lp: 'Amazon LP',
    frontend_specialist: 'Frontend Expert',
    backend_engineer: 'Backend Engineer',
    quick_practice: 'Quick Practice',
  };
  return labels[presetId] || 'Custom';
}
