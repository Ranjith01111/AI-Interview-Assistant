/* Step 2 — Generate Questions */
import { interview } from '../../api/index.js';
import { Toast } from '../../components/Toast.js';

export async function renderStep2(container, state, onNext) {
  container.innerHTML = `
    <div class="step-container slide-up">
      <div class="card">
        <div class="card-header"><span>🧠</span><h3>Generating Your Interview Questions</h3></div>
        <div class="card-body questions-ready" id="q-body">
          <div id="q-loading" style="text-align:center;padding:var(--spacing-2xl)">
            <div style="font-size:3rem;animation:spin 1.5s linear infinite;display:inline-block">⚙️</div>
            <p style="margin-top:var(--spacing-md);color:var(--text-secondary)">Analysing your resume and generating personalised questions…</p>
          </div>
          <div id="q-ready" style="display:none">
            <div class="check-icon">✅</div>
            <h2>Questions Ready!</h2>
            <p style="margin-top:8px;color:var(--text-muted)">
              Your personalised interview questions have been generated based on your resume.
            </p>
            <div class="question-count-grid" id="q-count-grid"></div>
            <div class="alert alert-info" style="margin-top:var(--spacing-md);text-align:left">
              💡 Questions are tailored to your projects, tech stack, and experience level.
              The AI will ask follow-up questions if your answers need more depth.
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
    const data = await interview.generateQuestions(state.sessionId);
    state.questions = data.questions || [];
    state.totalQuestions = data.total_questions || state.questions.length;

    // Count by category
    const cats = {};
    state.questions.forEach(q => { cats[q.category || q.type || 'technical'] = (cats[q.category || q.type || 'technical'] || 0) + 1; });

    const grid = container.querySelector('#q-count-grid');
    const catLabels = { project_based:'Project Based', challenge:'Challenge', architecture:'Architecture', debugging:'Debugging', technical:'Technical', hr:'HR' };
    Object.entries(cats).forEach(([cat, cnt]) => {
      const div = document.createElement('div');
      div.className = 'q-count-item';
      div.innerHTML = `<div class="q-count-num">${cnt}</div><div class="q-count-label">${catLabels[cat] || cat}</div>`;
      grid.appendChild(div);
    });
    const totalDiv = document.createElement('div');
    totalDiv.className = 'q-count-item';
    totalDiv.innerHTML = `<div class="q-count-num" style="color:var(--accent-emerald)">${state.totalQuestions}</div><div class="q-count-label">Total</div>`;
    grid.appendChild(totalDiv);

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
