/* Step 4 — Coding Assessment (Monaco IDE + Proctored) */
import { coding } from '../../api/index.js';
import { Toast } from '../../components/Toast.js';
import { ProctorMonitor } from '../../components/ProctorMonitor.js';

const LANG_MAP = { python:'python', javascript:'javascript', java:'java', c:'c', cpp:'cpp', sql:'sql' };
const CODING_TIME_LIMIT = 30 * 60; // 30 minutes in seconds

import * as monaco from 'monaco-editor';
import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker';
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker';
import cssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker';
import htmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker';
import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker';

self.MonacoEnvironment = {
  getWorker(_, label) {
    if (label === 'json') return new jsonWorker();
    if (label === 'css' || label === 'scss' || label === 'less') return new cssWorker();
    if (label === 'html' || label === 'handlebars' || label === 'razor') return new htmlWorker();
    if (label === 'typescript' || label === 'javascript') return new tsWorker();
    return new editorWorker();
  }
};

export async function renderStep4(container, state, onNext, onForceEnd) {
  container.innerHTML = `
    <div style="padding:0 var(--spacing-md);animation:slideUp 0.4s ease;height:calc(100vh - 160px);display:flex;flex-direction:column;overflow:hidden">
      <!-- Coding header with score tracker -->
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--spacing-md)">
        <h2 style="margin:0;font-size:1.1rem">💻 Coding Panel</h2>
        <div style="display:flex;align-items:center;gap:12px">
          <div class="panel-timer" id="panel-timer">
            <span class="timer-icon">⏱</span>
            <span class="timer-display" id="timer-display">30:00</span>
          </div>
          <span style="font-size:0.8rem;color:var(--text-muted)" id="coding-score-display">Score: —</span>
          <button class="btn btn-primary btn-sm" id="finish-coding-btn">Finish Coding →</button>
        </div>
      </div>

      <div class="coding-layout" id="coding-layout">
        <!-- Challenge Panel -->
        <div class="challenge-panel">
          <div class="card-header">
            <span>💻</span>
            <select class="form-select" id="challenge-select" style="flex:1;padding:8px 12px;border:1px solid var(--border);border-radius:8px;background:var(--bg-elevated);color:var(--text-primary);font-weight:600;font-size:0.85rem;cursor:pointer;appearance:auto">
              <option value="">Select a challenge…</option>
            </select>
          </div>
          <div class="challenge-body" id="challenge-body">
            <div class="empty-state"><div class="icon">💡</div><h3>Choose a challenge</h3><p>Select a problem from the dropdown</p></div>
          </div>
        </div>

        <!-- Editor Panel -->
        <div class="editor-panel">
          <div class="editor-toolbar">
            <select class="lang-selector" id="lang-selector">
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="java">Java</option>
              <option value="c">C</option>
              <option value="cpp">C++</option>
              <option value="sql">SQL</option>
            </select>
            <div style="flex:1"></div>
            <button class="btn btn-secondary btn-sm" id="run-btn" disabled>▶ Run</button>
            <button class="btn btn-success btn-sm" id="submit-btn" disabled>✔ Submit</button>
          </div>
          <div id="monaco-container" style="flex:1;min-height:200px"></div>
          <div class="terminal-panel" id="terminal">
            <div class="terminal-line info">// Run your code to see results</div>
          </div>
        </div>
      </div>
    </div>
  `;

  let editor = null;
  let selectedChallenge = null;
  let proctor = null;
  let challengesMap = {};
  const codingScores = {};
  let timerInterval = null;
  let timeRemaining = CODING_TIME_LIMIT;

  /* ══════════════════════════════════════════════════════════════════
     HELPER FUNCTIONS
     ══════════════════════════════════════════════════════════════════ */

  function startTimer() {
    updateTimerDisplay();
    timerInterval = setInterval(() => {
      timeRemaining--;
      updateTimerDisplay();
      if (timeRemaining <= 0) {
        clearInterval(timerInterval);
        timerInterval = null;
        Toast.warning('⏰ Time is up! Coding panel ending automatically.', 'Time Over');
        finishCoding();
      }
    }, 1000);
  }

  function updateTimerDisplay() {
    const mins = Math.floor(timeRemaining / 60);
    const secs = timeRemaining % 60;
    const display = container.querySelector('#timer-display');
    if (display) {
      display.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
      const timerEl = container.querySelector('#panel-timer');
      if (timeRemaining <= 300) timerEl.classList.add('timer-warning');
      if (timeRemaining <= 60) timerEl.classList.add('timer-critical');
    }
  }

  function finishCoding() {
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
    const scores = Object.values(codingScores);
    state.codingScore = scores.length ? Math.round(scores.reduce((a,b) => a+b, 0) / scores.length) : 0;
    state.codingScores = codingScores;
    proctor?.destroy();
    if (onNext) onNext();
  }

  function renderChallengeDetails(c) {
    const body = container.querySelector('#challenge-body');
    body.innerHTML = `
      <div style="margin-bottom:var(--spacing-md)">
        <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
          <h3 style="margin:0">${c.title}</h3>
          <span class="badge ${c.difficulty === 'Easy' ? 'badge-emerald' : c.difficulty === 'Hard' ? 'badge-red' : 'badge-amber'}">${c.difficulty}</span>
        </div>
        <p style="font-size:0.75rem;color:var(--text-muted)">⏱ ${c.time_limit}s • 💾 ${c.memory_limit}MB</p>
      </div>
      <div class="challenge-desc" style="font-size:0.82rem;line-height:1.6;overflow-y:auto">${markdownToHtml(c.description)}</div>
    `;
  }

  function markdownToHtml(md) {
    return md
      .replace(/^## (.*$)/gm, '<h3 style="color:var(--accent-gold);margin:12px 0 6px">$1</h3>')
      .replace(/^### (.*$)/gm, '<h4 style="margin:10px 0 4px;font-size:0.85rem">$1</h4>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code style="background:rgba(245,184,0,0.1);padding:1px 4px;border-radius:3px;font-size:0.8rem">$1</code>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
  }

  function escapeHtml(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function updateCodingScoreDisplay() {
    const scores = Object.values(codingScores);
    const avg = scores.length ? Math.round(scores.reduce((a,b) => a+b, 0) / scores.length) : 0;
    container.querySelector('#coding-score-display').textContent = `Score: ${avg}/100`;
  }

  function renderResults(termEl, result, mode) {
    const tests = result?.results || [];
    const score = result?.score;
    const status = result?.status;

    if (!tests.length) {
      if (status === 'System Error') {
        termEl.innerHTML = `<div class="terminal-line fail">❌ System Error: ${result?.compile_error || result?.error || 'Could not execute code'}</div>`;
      } else {
        termEl.innerHTML = `<div class="terminal-line info">${status || 'No results'}</div>`;
      }
      return;
    }

    let html = `<div style="font-size:0.75rem;font-weight:600;color:var(--accent-gold);margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid var(--border)">${mode} Results</div>`;

    tests.forEach((t, i) => {
      const icon = t.passed ? '✅' : '❌';
      const label = t.is_hidden ? `Test ${i+1} (Hidden)` : `Test ${i+1}`;
      const statusColor = t.passed ? 'var(--accent-emerald)' : 'var(--accent-red)';

      html += `<div style="padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.03)">`;
      html += `<div style="display:flex;justify-content:space-between;align-items:center">`;
      html += `<span style="font-size:0.8rem">${icon} ${label}</span>`;
      html += `<span style="font-size:0.7rem;color:${statusColor};font-weight:600">${t.status || (t.passed ? 'PASS' : 'FAIL')}</span>`;
      html += `</div>`;

      if (!t.is_hidden && !t.passed) {
        if (t.error) {
          html += `<div style="font-size:0.72rem;color:var(--accent-red);margin-top:3px;padding:4px 8px;background:rgba(239,68,68,0.08);border-radius:4px">${t.error}</div>`;
        } else {
          html += `<div style="font-size:0.72rem;margin-top:4px;display:grid;grid-template-columns:1fr 1fr;gap:6px">`;
          html += `<div style="padding:4px 8px;background:rgba(16,185,129,0.06);border-radius:4px"><span style="color:var(--text-muted)">Expected:</span><br><code style="color:var(--accent-emerald)">${escapeHtml(t.expected || '')}</code></div>`;
          html += `<div style="padding:4px 8px;background:rgba(239,68,68,0.06);border-radius:4px"><span style="color:var(--text-muted)">Got:</span><br><code style="color:var(--accent-red)">${escapeHtml(t.actual || '')}</code></div>`;
          html += `</div>`;
        }
      }
      if (!t.is_hidden && t.passed && t.run_time_ms) {
        html += `<div style="font-size:0.65rem;color:var(--text-muted);margin-top:2px">⏱ ${t.run_time_ms}ms</div>`;
      }
      html += `</div>`;
    });

    const passed = tests.filter(t => t.passed).length;
    const total = tests.length;
    const pct = Math.round((passed / total) * 100);
    const barColor = pct === 100 ? 'var(--accent-emerald)' : pct > 0 ? 'var(--accent-amber)' : 'var(--accent-red)';

    html += `<div style="margin-top:10px;padding-top:10px;border-top:1px solid var(--border)">`;
    html += `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">`;
    html += `<span style="font-size:0.8rem;font-weight:600">Score: ${score ?? pct}/100</span>`;
    html += `<span style="font-size:0.75rem;color:var(--text-muted)">${passed}/${total} passed</span>`;
    html += `</div>`;
    html += `<div class="progress-bar" style="height:6px"><div class="progress-fill" style="width:${pct}%;background:${barColor}"></div></div>`;
    html += `</div>`;

    termEl.innerHTML = html;
  }

  /* Start Proctoring */
  proctor = new ProctorMonitor(state.sessionId, {
    onSessionEnd: () => { if (onForceEnd) onForceEnd(); },
    skipFullscreen: true
  });
  await proctor.mount(document.body);
  startTimer();

  /* Load Challenges */
  try {
    const challenges = await coding.getChallenges();
    const sel = container.querySelector('#challenge-select');
    if (challenges.length === 0) sel.innerHTML = '<option value="">No challenges available</option>';
    else {
      const seen = new Set();
      challenges.forEach(c => {
        if (!seen.has(c.title)) {
          seen.add(c.title);
          const opt = document.createElement('option');
          opt.value = c.id;
          opt.textContent = `${c.title} [${c.difficulty.toUpperCase()}]`;
          sel.appendChild(opt);
          challengesMap[c.id] = c;
        }
      });
    }
  } catch (err) { console.error(err); Toast.error('Failed to load challenges'); }

  /* Challenge select handler */
  const challengeSelectHandler = async (e) => {
    const id = e.target ? e.target.value : e;
    if (!id) return;
    try {
      selectedChallenge = challengesMap[id] || await coding.getChallenge(id);
      renderChallengeDetails(selectedChallenge);
      const lang = container.querySelector('#lang-selector').value;
      const tmpl = selectedChallenge.template_code?.[lang] || `# Write your ${lang} solution here\n`;
      if (editor) {
        editor.setValue(tmpl);
        monaco.editor.setModelLanguage(editor.getModel(), LANG_MAP[lang] || 'python');
      }
      container.querySelector('#run-btn').disabled = false;
      container.querySelector('#submit-btn').disabled = false;
    } catch (err) { Toast.error('Failed to load challenge'); }
  };

  const selectEl = container.querySelector('#challenge-select');
  selectEl.onchange = challengeSelectHandler;

  /* Load Monaco IDE locally */
  const monacoEl = container.querySelector('#monaco-container');
  monacoEl.style.flex = '1';
  editor = monaco.editor.create(monacoEl, {
    value: '# Select a challenge to begin\n',
    language: 'python',
    theme: 'vs-dark',
    fontSize: 14,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    automaticLayout: true,
    fontFamily: "'JetBrains Mono', monospace",
  });

  /* Language change */
  container.querySelector('#lang-selector').onchange = (e) => {
    const lang = e.target.value;
    if (editor) monaco.editor.setModelLanguage(editor.getModel(), LANG_MAP[lang] || 'python');
    if (selectedChallenge) {
      const tmpl = selectedChallenge.template_code?.[lang] || `# Write your ${lang} solution here\n`;
      if (editor) editor.setValue(tmpl);
    }
  };

  /* Run */
  container.querySelector('#run-btn').onclick = async () => {
    if (!selectedChallenge) return;
    const code = editor ? editor.getValue() : '';
    const lang = container.querySelector('#lang-selector').value;
    const term = container.querySelector('#terminal');
    const btn = container.querySelector('#run-btn');
    btn.disabled = true; btn.textContent = '⏳ Running...';
    term.innerHTML = '<div class="terminal-line info">⏳ Executing code against test cases...</div>';
    try {
      const result = await coding.runCode(selectedChallenge.id, lang, code);
      renderResults(term, result, 'Run');
    } catch (err) { term.innerHTML = `<div class="terminal-line fail">❌ Error: ${err.message}</div>`; }
    btn.disabled = false; btn.textContent = '▶ Run';
  };

  /* Submit */
  container.querySelector('#submit-btn').onclick = async () => {
    if (!selectedChallenge || !state.sessionId) return;
    const code = editor ? editor.getValue() : '';
    const lang = container.querySelector('#lang-selector').value;
    const btn = container.querySelector('#submit-btn');
    const term = container.querySelector('#terminal');
    btn.disabled = true; btn.textContent = '⏳ Evaluating...';
    term.innerHTML = '<div class="terminal-line info">⏳ Running against all test cases (including hidden)...</div>';
    try {
      const result = await coding.submitCode(state.sessionId, selectedChallenge.id, lang, code);
      const data = result.results || result;
      renderResults(term, data, 'Submit');
      const score = data.score ?? result.score ?? 0;
      codingScores[selectedChallenge.id] = score;
      updateCodingScoreDisplay();
      if (score === 100) Toast.success('🎉 All test cases passed! Perfect score.', 'Accepted');
      else if (score > 0) Toast.warning(`Score: ${score}/100 — Some test cases failed.`, 'Partial');
      else Toast.error(`Score: 0/100 — No test cases passed.`, 'Failed');
    } catch (err) {
      term.innerHTML = `<div class="terminal-line fail">❌ ${err.message}</div>`;
    }
    btn.disabled = false; btn.textContent = '✔ Submit';
  };

  /* Finish coding */
  container.querySelector('#finish-coding-btn').addEventListener('click', () => finishCoding());

  /* Clean up proctor on navigate away */
  container._destroyProctor = () => {
    proctor?.destroy();
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
  };
}
