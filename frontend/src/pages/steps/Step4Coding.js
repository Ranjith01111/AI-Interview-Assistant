/* Step 4 — Coding Assessment (Monaco IDE + Proctored) */
import { coding, leetcode } from '../../api/index.js';
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
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--spacing-lg);padding:8px 0;">
        <h2 style="margin:0;font-size:1.4rem">💻 Coding Panel</h2>
        <div style="display:flex;align-items:center;gap:24px">
          <div class="panel-timer" id="panel-timer" style="display:flex;align-items:center;gap:6px;background:rgba(255,255,255,0.05);padding:6px 14px;border-radius:20px;">
            <span class="timer-icon" style="font-size:1.2rem">⏱</span>
            <span class="timer-display" id="timer-display" style="font-weight:700;font-size:1.1rem;color:var(--accent-gold)">30:00</span>
          </div>
          <span style="font-size:0.9rem;font-weight:600;color:var(--text-primary);background:rgba(16,185,129,0.1);padding:6px 14px;border-radius:20px;border:1px solid rgba(16,185,129,0.2)" id="coding-score-display">Score: —</span>
          <button class="btn btn-primary" id="finish-coding-btn" style="padding:8px 20px;border-radius:24px;font-weight:700;box-shadow:0 4px 12px rgba(99,102,241,0.3)">End Session →</button>
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
            <button class="btn btn-secondary btn-sm" id="leetcode-search-btn" style="white-space:nowrap;font-size:0.75rem;padding:6px 10px;border-radius:6px;background:linear-gradient(135deg,#ffa116,#f5b800);color:#1a1a2e;font-weight:700;border:none;cursor:pointer" title="Search LeetCode Problems">🔍 LeetCode</button>
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

  async function finishCoding() {
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
    const scores = Object.values(codingScores);
    state.codingScore = scores.length ? Math.round(scores.reduce((a,b) => a+b, 0) / scores.length) : 0;
    state.codingScores = codingScores;
    proctor?.destroy();

    // Explicitly ensure fullscreen is exited before moving to summary
    if (document.fullscreenElement || document.webkitFullscreenElement) {
      try {
        if (document.exitFullscreen) await document.exitFullscreen();
        else if (document.webkitExitFullscreen) await document.webkitExitFullscreen();
      } catch (e) {}
    }

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
          html += `<div style="font-size:0.75rem;margin-top:6px;display:flex;flex-direction:column;gap:6px">`;
          html += `<div style="padding:6px;background:rgba(255,255,255,0.05);border-radius:4px;border-left:2px solid var(--accent-emerald)"><span style="color:var(--text-muted);margin-right:8px">Expected:</span> <code style="color:var(--accent-emerald)">${escapeHtml(t.expected || '')}</code></div>`;
          html += `<div style="padding:6px;background:rgba(255,255,255,0.05);border-radius:4px;border-left:2px solid var(--accent-red)"><span style="color:var(--text-muted);margin-right:8px">Output:</span> <code style="color:var(--accent-red)">${escapeHtml(t.actual || '')}</code></div>`;
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
    onSessionEnd: () => { if (onForceEnd) onForceEnd(); }
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

  /* ══════════════════════════════════════════════════════════════════
     LEETCODE SEARCH MODAL
     ══════════════════════════════════════════════════════════════════ */
  const lcBtn = container.querySelector('#leetcode-search-btn');
  if (lcBtn) {
    lcBtn.addEventListener('click', () => showLeetCodeModal());
  }

  function showLeetCodeModal() {
    // Remove existing modal if any
    const existing = document.getElementById('lc-modal-overlay');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.id = 'lc-modal-overlay';
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:9999;display:flex;align-items:center;justify-content:center;animation:fadeIn 0.2s ease';
    overlay.innerHTML = `
      <div style="background:var(--bg-surface,#1e1e2e);border:1px solid var(--border,#333);border-radius:16px;width:90%;max-width:700px;max-height:80vh;display:flex;flex-direction:column;box-shadow:0 20px 60px rgba(0,0,0,0.5)">
        <div style="padding:16px 20px;border-bottom:1px solid var(--border,#333);display:flex;align-items:center;gap:12px">
          <span style="font-size:1.2rem">🔍</span>
          <h3 style="margin:0;flex:1;font-size:1rem;color:var(--text-primary,#fff)">Search LeetCode Problems</h3>
          <button id="lc-daily-btn" style="font-size:0.7rem;padding:4px 10px;border-radius:6px;background:#ffa116;color:#1a1a2e;font-weight:700;border:none;cursor:pointer">⭐ Daily</button>
          <button id="lc-close-btn" style="background:none;border:none;color:var(--text-muted,#888);font-size:1.2rem;cursor:pointer">✕</button>
        </div>
        <div style="padding:12px 20px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <input id="lc-search-input" type="text" placeholder="Search by name (e.g. two-sum, binary-tree)..." style="flex:1;min-width:200px;padding:8px 12px;border:1px solid var(--border,#333);border-radius:8px;background:var(--bg-elevated,#252535);color:var(--text-primary,#fff);font-size:0.85rem" />
          <select id="lc-difficulty-filter" style="padding:8px;border:1px solid var(--border,#333);border-radius:8px;background:var(--bg-elevated,#252535);color:var(--text-primary,#fff);font-size:0.8rem">
            <option value="">All Difficulties</option>
            <option value="EASY">Easy</option>
            <option value="MEDIUM">Medium</option>
            <option value="HARD">Hard</option>
          </select>
          <button id="lc-search-go" style="padding:8px 16px;border-radius:8px;background:var(--accent-gold,#f5b800);color:#1a1a2e;font-weight:700;border:none;cursor:pointer;font-size:0.85rem">Search</button>
        </div>
        <div id="lc-results" style="flex:1;overflow-y:auto;padding:0 20px 16px;min-height:200px">
          <p style="color:var(--text-muted,#888);text-align:center;padding:40px 0;font-size:0.85rem">Search for LeetCode problems or click ⭐ Daily for today's challenge</p>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    // Close modal
    overlay.querySelector('#lc-close-btn').onclick = () => overlay.remove();
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });

    // Search handler
    const doSearch = async () => {
      const query = overlay.querySelector('#lc-search-input').value.trim();
      const diff = overlay.querySelector('#lc-difficulty-filter').value;
      const resultsDiv = overlay.querySelector('#lc-results');
      resultsDiv.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:20px">🔄 Searching...</p>';

      try {
        const res = await leetcode.search(query, diff || null, [], 1000);
        if (!res.success || !res.problems?.length) {
          resultsDiv.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:30px">No problems found. Try a different search term.</p>';
          return;
        }
        renderLCResults(resultsDiv, res.problems);
      } catch (err) {
        resultsDiv.innerHTML = `<p style="text-align:center;color:#f44;padding:20px">Error: ${err.message || 'Search failed'}</p>`;
      }
    };

    overlay.querySelector('#lc-search-go').onclick = doSearch;
    overlay.querySelector('#lc-search-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') doSearch();
    });

    // Daily button
    overlay.querySelector('#lc-daily-btn').onclick = async () => {
      const resultsDiv = overlay.querySelector('#lc-results');
      resultsDiv.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:20px">🔄 Fetching daily challenge...</p>';
      try {
        const res = await leetcode.getDaily();
        if (res.success && res.problem) {
          renderLCProblemPreview(resultsDiv, res.problem, overlay);
        } else {
          resultsDiv.innerHTML = `<p style="text-align:center;color:#f44;padding:20px">${res.error || 'Could not fetch daily problem'}</p>`;
        }
      } catch (err) {
        resultsDiv.innerHTML = `<p style="text-align:center;color:#f44;padding:20px">Error: ${err.message}</p>`;
      }
    };
  }

  function renderLCResults(container, problems) {
    container.innerHTML = problems.map(p => `
      <div class="lc-problem-row" data-slug="${p.titleSlug}" style="display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:8px;cursor:pointer;transition:background 0.15s;border-bottom:1px solid rgba(255,255,255,0.05)">
        <span style="font-size:0.75rem;color:var(--text-muted);min-width:32px">#${p.questionId || ''}</span>
        <span style="flex:1;font-size:0.85rem;color:var(--text-primary,#fff)">${p.title}</span>
        <span style="font-size:0.7rem;padding:2px 8px;border-radius:4px;font-weight:600;${
          p.difficulty === 'Easy' ? 'background:rgba(0,175,155,0.15);color:#00af9b' :
          p.difficulty === 'Hard' ? 'background:rgba(255,55,95,0.15);color:#ff375f' :
          'background:rgba(255,161,22,0.15);color:#ffa116'
        }">${p.difficulty}</span>
        <span style="font-size:0.7rem;color:var(--text-muted)">${(p.topicTags || []).slice(0,2).join(', ')}</span>
        <button class="lc-import-btn" data-slug="${p.titleSlug}" style="font-size:0.7rem;padding:4px 10px;border-radius:6px;background:var(--accent-gold,#f5b800);color:#1a1a2e;font-weight:700;border:none;cursor:pointer">+ Import</button>
      </div>
    `).join('');

    // Hover effect
    container.querySelectorAll('.lc-problem-row').forEach(row => {
      row.addEventListener('mouseenter', () => row.style.background = 'rgba(245,184,0,0.05)');
      row.addEventListener('mouseleave', () => row.style.background = 'transparent');
    });

    // Import buttons
    container.querySelectorAll('.lc-import-btn').forEach(btn => {
      btn.onclick = async (e) => {
        e.stopPropagation();
        const slug = btn.dataset.slug;
        btn.textContent = '⏳...';
        btn.disabled = true;
        try {
          const res = await leetcode.importProblem(slug);
          if (res.success) {
            btn.textContent = '✅ Added';
            btn.style.background = '#00af9b';
            btn.style.color = '#fff';
            Toast.success(`Imported: ${res.title}`);
            // Reload challenges dropdown
            await reloadChallenges();
          } else {
            btn.textContent = '❌ Failed';
            Toast.error(res.error || 'Import failed');
          }
        } catch (err) {
          btn.textContent = '❌ Error';
          Toast.error(err.message || 'Import failed');
        }
      };
    });
  }

  function renderLCProblemPreview(container, problem, overlay) {
    container.innerHTML = `
      <div style="padding:8px 0">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
          <h4 style="margin:0;flex:1;color:var(--text-primary,#fff)">${problem.title}</h4>
          <span style="font-size:0.75rem;padding:3px 10px;border-radius:4px;font-weight:600;${
            problem.difficulty === 'Easy' ? 'background:rgba(0,175,155,0.15);color:#00af9b' :
            problem.difficulty === 'Hard' ? 'background:rgba(255,55,95,0.15);color:#ff375f' :
            'background:rgba(255,161,22,0.15);color:#ffa116'
          }">${problem.difficulty}</span>
        </div>
        <div style="font-size:0.8rem;line-height:1.6;color:var(--text-secondary,#ccc);max-height:250px;overflow-y:auto;padding:12px;background:var(--bg-elevated,#252535);border-radius:8px;margin-bottom:12px">${problem.description?.substring(0, 800) || 'No description'}...</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px">
          ${(problem.topicTags || []).map(t => `<span style="font-size:0.65rem;padding:2px 6px;border-radius:4px;background:rgba(100,150,255,0.1);color:#6496ff">${t}</span>`).join('')}
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end">
          <button id="lc-preview-import" style="padding:8px 20px;border-radius:8px;background:var(--accent-gold,#f5b800);color:#1a1a2e;font-weight:700;border:none;cursor:pointer;font-size:0.85rem">⬇️ Import This Problem</button>
        </div>
      </div>
    `;

    container.querySelector('#lc-preview-import').onclick = async () => {
      const btn = container.querySelector('#lc-preview-import');
      btn.textContent = '⏳ Importing...';
      btn.disabled = true;
      try {
        const res = await leetcode.importProblem(problem.titleSlug);
        if (res.success) {
          Toast.success(`Imported: ${res.title}`);
          await reloadChallenges();
          overlay.remove();
        } else {
          btn.textContent = '❌ Failed';
          Toast.error(res.error || 'Import failed');
        }
      } catch (err) {
        btn.textContent = '❌ Error';
        Toast.error(err.message || 'Import failed');
      }
    };
  }

  async function reloadChallenges() {
    try {
      const challenges = await coding.getChallenges();
      const sel = container.querySelector('#challenge-select');
      sel.innerHTML = '<option value="">Select a challenge…</option>';
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
    } catch (err) { console.error('Reload challenges failed:', err); }
  }

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
