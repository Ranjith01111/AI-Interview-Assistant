/* Verbal Interview — Real-time Conversational AI Interview
   Natural speaking flow with per-answer feedback + detailed final review.
   
   Uses:
   - Ollama LLM for natural conversational questions (resume-based)
   - Browser Web Speech API (speech-to-text)
   - Backend edge-tts (text-to-speech for interviewer voice)
   - Real-time scoring + suggestions after each answer
*/
import { renderNavbar } from '../components/Navbar.js';
import { Toast } from '../components/Toast.js';
import { navigate } from '../main.js';
import { verbal } from '../api/index.js';

export async function renderVoiceInterview(container) {
  container.innerHTML = '';
  renderNavbar(container);

  const main = document.createElement('div');
  main.className = 'app-main';
  main.innerHTML = `
    <div class="page-content" style="max-width:650px;margin:0 auto;padding-top:var(--spacing-md)">
      <!-- Interview Card -->
      <div class="card" style="padding:28px;text-align:center" id="interview-card">
        <div id="orb" style="margin:0 auto 14px;width:100px;height:100px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:2.4rem;cursor:pointer;background:linear-gradient(135deg,var(--accent-gold),#ff8c00);box-shadow:0 4px 24px rgba(245,184,0,0.3);transition:all 0.4s ease">📞</div>
        <div id="status-text" style="font-size:1rem;font-weight:600;margin-bottom:4px">Tap to Start Interview</div>
        <div id="sub-text" style="font-size:0.78rem;color:var(--text-muted);margin-bottom:16px">Real-time AI conversation with feedback after each answer</div>

        <!-- Interviewer speaking -->
        <div id="interviewer-box" style="display:none;background:rgba(99,102,241,0.08);border-left:3px solid #6366f1;border-radius:0 8px 8px 0;padding:14px 16px;text-align:left;margin-bottom:12px">
          <div style="font-size:0.65rem;color:#8b5cf6;font-weight:700;margin-bottom:5px">🗣️ INTERVIEWER</div>
          <div id="interviewer-text" style="font-size:0.88rem;line-height:1.6"></div>
        </div>

        <!-- Candidate speaking -->
        <div id="candidate-box" style="display:none;background:rgba(16,185,129,0.06);border-left:3px solid #10b981;border-radius:0 8px 8px 0;padding:14px 16px;text-align:left;margin-bottom:12px">
          <div style="font-size:0.65rem;color:#10b981;font-weight:700;margin-bottom:5px">🎤 YOU (speaking...)</div>
          <div id="candidate-text" style="font-size:0.85rem;color:var(--text-muted);min-height:20px">Listening...</div>
        </div>

        <!-- Real-time feedback (shown briefly after each answer) -->
        <div id="feedback-box" style="display:none;background:rgba(245,184,0,0.05);border:1px solid rgba(245,184,0,0.2);border-radius:10px;padding:12px 16px;text-align:left;margin-bottom:12px;animation:fadeIn 0.3s ease">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <span style="font-size:0.68rem;color:var(--accent-gold);font-weight:700">💡 QUICK FEEDBACK</span>
            <span id="fb-score" style="font-size:0.8rem;font-weight:700"></span>
          </div>
          <div id="fb-strength" style="font-size:0.78rem;color:var(--accent-emerald);margin-bottom:4px"></div>
          <div id="fb-suggestion" style="font-size:0.78rem;color:var(--text-secondary)"></div>
        </div>

        <!-- Progress -->
        <div id="progress-section" style="display:none;margin-top:12px">
          <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:var(--text-muted);margin-bottom:3px">
            <span id="progress-label">Question</span>
            <span id="progress-count"></span>
          </div>
          <div class="progress-bar"><div class="progress-fill" id="progress-bar" style="width:0%;transition:width 0.5s ease"></div></div>
        </div>

        <!-- Controls -->
        <div style="margin-top:12px;display:flex;gap:10px;justify-content:center">
          <button id="skip-btn" style="display:none;background:none;border:1px solid var(--text-muted);color:var(--text-muted);padding:5px 14px;border-radius:20px;cursor:pointer;font-size:0.72rem">Skip →</button>
          <button id="end-btn" style="display:none;background:none;border:1px solid var(--accent-red);color:var(--accent-red);padding:5px 14px;border-radius:20px;cursor:pointer;font-size:0.72rem">End Interview</button>
        </div>
      </div>

      <!-- Final Report -->
      <div id="report-section" style="display:none;margin-top:20px"></div>
    </div>
  `;
  container.appendChild(main);

  // ═══════════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════════
  let verbalSessionId = null;
  let active = false;
  let recog = null;
  let transcript = '';
  let listening = false;
  let silenceTimer = null;
  let noSpeechTimer = null;
  let questionCount = 0;
  let currentAudio = null; // Track active TTS audio

  const $ = (sel) => main.querySelector(sel);
  const orb = $('#orb'), statusText = $('#status-text'), subText = $('#sub-text');
  const interviewerBox = $('#interviewer-box'), interviewerText = $('#interviewer-text');
  const candidateBox = $('#candidate-box'), candidateText = $('#candidate-text');
  const feedbackBox = $('#feedback-box');
  const progressBar = $('#progress-bar'), progressCount = $('#progress-count');
  const progressSection = $('#progress-section');
  const skipBtn = $('#skip-btn'), endBtn = $('#end-btn');

  // ═══════════════════════════════════════════════════════════════
  // TTS
  // ═══════════════════════════════════════════════════════════════
  function speak(text, onDone) {
    const url = '/api/v1/tts/speak?text=' + encodeURIComponent(text.slice(0, 490));
    const audio = new Audio(url);
    audio.volume = 1.0;
    currentAudio = audio; // Track so we can stop it
    const minMs = Math.max(text.length * 55, 3500);
    let audioDone = false, timerDone = false;
    const check = () => { if (audioDone && timerDone && active) setTimeout(onDone, 800); };
    setTimeout(() => { timerDone = true; check(); }, minMs);
    audio.onended = () => { audioDone = true; check(); };
    audio.onerror = () => { audioDone = true; check(); };
    audio.play().catch(() => { audioDone = true; check(); });
  }

  function stopAudio() {
    if (currentAudio) { try { currentAudio.pause(); currentAudio.src = ''; } catch(e) {} currentAudio = null; }
  }

  // ═══════════════════════════════════════════════════════════════
  // SPEECH RECOGNITION
  // ═══════════════════════════════════════════════════════════════
  function initRecognition() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { Toast.error('Requires Chrome or Edge.'); return false; }
    recog = new SR();
    recog.continuous = true;
    recog.interimResults = true;
    recog.lang = 'en-US';
    recog.onresult = (e) => {
      if (!listening) return;
      let t = '';
      for (let i = 0; i < e.results.length; i++) t += e.results[i][0].transcript;
      if (noSpeechTimer) { clearTimeout(noSpeechTimer); noSpeechTimer = null; }
      transcript = t;
      candidateText.textContent = t;
      candidateText.style.color = 'var(--text-primary)';
      if (silenceTimer) clearTimeout(silenceTimer);
      silenceTimer = setTimeout(finishAnswer, 3500);
    };
    recog.onerror = (e) => { if (e.error === 'not-allowed') Toast.error('Allow microphone access.'); };
    recog.onend = () => { if (active && listening && !silenceTimer) try { recog.start(); } catch(e) {} };
    return true;
  }

  function stopRecognition() {
    listening = false;
    if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null; }
    if (noSpeechTimer) { clearTimeout(noSpeechTimer); noSpeechTimer = null; }
    try { recog?.stop(); } catch(e) {}
  }

  // ═══════════════════════════════════════════════════════════════
  // FLOW
  // ═══════════════════════════════════════════════════════════════
  orb.onclick = async () => {
    if (active) return;
    if (!initRecognition()) return;
    active = true;
    endBtn.style.display = ''; skipBtn.style.display = ''; progressSection.style.display = '';
    orb.style.background = 'linear-gradient(135deg,#6366f1,#8b5cf6)';
    orb.textContent = '🗣️';
    statusText.textContent = 'Connecting...';
    subText.textContent = 'Starting AI interviewer...';

    try {
      const sessionId = localStorage.getItem('active_session_id') || null;
      const res = await verbal.start(sessionId);
      if (res.success) {
        verbalSessionId = res.verbal_session_id;
        questionCount = res.question_number;
        showInterviewer(res.message);
      } else { Toast.error('Failed to start'); resetUI(); }
    } catch (err) { Toast.error(err.message || 'Connection failed'); resetUI(); }
  };

  endBtn.onclick = () => endInterview();
  skipBtn.onclick = () => { stopRecognition(); sendResponse('[skipped]'); };

  function showInterviewer(msg) {
    feedbackBox.style.display = 'none';
    interviewerBox.style.display = ''; candidateBox.style.display = 'none';
    interviewerText.textContent = msg;
    orb.style.background = 'linear-gradient(135deg,#6366f1,#8b5cf6)';
    orb.textContent = '🗣️';
    statusText.textContent = '🗣️ Interviewer speaking...';
    subText.textContent = `Question ${questionCount} of ~8`;
    progressCount.textContent = `${questionCount}/8`;
    progressBar.style.width = `${Math.min(100, (questionCount / 8) * 100)}%`;
    speak(msg, () => { if (active) setTimeout(startListening, 600); });
  }

  function startListening() {
    if (!active) return;
    feedbackBox.style.display = 'none';
    interviewerBox.style.display = 'none'; candidateBox.style.display = '';
    orb.style.background = 'linear-gradient(135deg,#10b981,#059669)';
    orb.textContent = '🎤';
    statusText.textContent = '🎤 Your turn — speak naturally';
    subText.textContent = 'I\'m listening... (silence for 3s = done)';
    candidateText.textContent = 'Listening...'; candidateText.style.color = 'var(--text-muted)';
    transcript = ''; listening = true;
    try { recog.start(); } catch(e) {}
    noSpeechTimer = setTimeout(() => {
      if (!transcript.trim()) candidateText.textContent = 'No speech detected — try again or tap Skip.';
    }, 12000);
  }

  async function finishAnswer() {
    stopRecognition();
    if (!transcript.trim()) { startListening(); return; }
    await sendResponse(transcript.trim());
  }

  async function sendResponse(answer) {
    if (!verbalSessionId) return;
    candidateBox.style.display = 'none';
    orb.style.background = 'linear-gradient(135deg,var(--accent-gold),#ff8c00)';
    orb.textContent = '💭'; statusText.textContent = '💭 Processing...'; subText.textContent = '';

    try {
      const res = await verbal.respond(verbalSessionId, answer);
      if (!res.success) { Toast.error('Error'); startListening(); return; }

      questionCount = res.question_number;

      // Show quick feedback if available
      if (res.feedback && answer !== '[skipped]') {
        showQuickFeedback(res.feedback);
        // Wait 3s to let user read, then continue
        await new Promise(r => setTimeout(r, 3000));
      }

      if (res.is_complete) { await endInterview(); }
      else { showInterviewer(res.message); }
    } catch (err) { Toast.error(err.message || 'Error'); startListening(); }
  }

  function showQuickFeedback(fb) {
    feedbackBox.style.display = '';
    const avg = ((fb.relevance + fb.clarity + fb.depth + fb.communication) / 4).toFixed(1);
    const color = avg >= 7 ? 'var(--accent-emerald)' : avg >= 5 ? 'var(--accent-gold)' : 'var(--accent-red)';
    $('#fb-score').textContent = `${avg}/10`;
    $('#fb-score').style.color = color;
    $('#fb-strength').textContent = `✓ ${fb.strength}`;
    $('#fb-suggestion').textContent = `→ ${fb.suggestion}`;
  }

  async function endInterview() {
    active = false; stopRecognition(); stopAudio();
    orb.textContent = '✅'; orb.style.background = '#1a1a2e'; orb.style.cursor = 'default'; orb.style.boxShadow = 'none';
    statusText.textContent = 'Interview Complete';
    subText.textContent = 'Generating detailed review...';
    endBtn.style.display = 'none'; skipBtn.style.display = 'none';
    interviewerBox.style.display = 'none'; candidateBox.style.display = 'none'; feedbackBox.style.display = 'none';

    if (verbalSessionId) {
      try {
        const res = await verbal.end(verbalSessionId);
        if (res && res.evaluation) {
          subText.textContent = '';
          buildReport(res.evaluation);
        } else {
          subText.textContent = '';
          // Build a minimal report even with partial data
          const fallback = res?.evaluation || { overall_score: 0, rating: 'Session ended', scores: {}, stats: {}, question_reviews: [], overall_suggestion: 'Start a new interview for full evaluation.', top_strengths: [], areas_to_improve: [] };
          buildReport(fallback);
        }
      } catch (err) {
        console.error('End interview error:', err);
        subText.textContent = '';
        // Show report with whatever we have
        buildReport({ overall_score: 0, rating: 'Error generating review', scores: {}, stats: {}, question_reviews: [], overall_suggestion: err.message || 'Server connection failed. Make sure backend is running.', top_strengths: [], areas_to_improve: ['Ensure Ollama is running (ollama serve)'] });
      }
    }
  }

  function resetUI() {
    active = false;
    orb.style.background = 'linear-gradient(135deg,var(--accent-gold),#ff8c00)';
    orb.textContent = '📞'; orb.style.cursor = 'pointer'; orb.style.boxShadow = '0 4px 24px rgba(245,184,0,0.3)';
    statusText.textContent = 'Tap to Start Interview';
    subText.textContent = 'Real-time AI conversation with feedback after each answer';
  }

  // ═══════════════════════════════════════════════════════════════
  // DETAILED REPORT
  // ═══════════════════════════════════════════════════════════════
  function buildReport(ev) {
    const rpt = $('#report-section');
    rpt.style.display = '';
    const sc = ev.scores || { relevance: 0, clarity: 0, depth: 0, communication: 0, fluency: 0 };
    const stats = ev.stats || { total_questions: 0, total_answers: 0, total_words: 0, avg_words_per_answer: 0, filler_words_count: 0 };
    const overallScore = ev.overall_score || 0;
    const rating = ev.rating || 'No rating';
    const mainColor = overallScore >= 7 ? 'var(--accent-emerald)' : overallScore >= 5 ? 'var(--accent-gold)' : 'var(--accent-red)';

    rpt.innerHTML = `
      <div class="card" style="padding:24px">
        <h3 style="text-align:center;margin-bottom:20px">📊 Detailed Interview Review</h3>

        <!-- Overall Score -->
        <div style="text-align:center;margin-bottom:24px;padding:20px;background:var(--bg-elevated);border-radius:12px">
          <div style="font-size:2.8rem;font-weight:800;color:${mainColor}">${overallScore}/10</div>
          <div style="font-size:0.9rem;color:${mainColor};font-weight:600;margin-top:4px">${rating}</div>
        </div>

        <!-- Score Breakdown -->
        <h4 style="font-size:0.85rem;color:var(--text-muted);margin-bottom:12px;text-transform:uppercase;letter-spacing:0.5px">Score Breakdown</h4>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:24px">
          ${scoreBar('Relevance', sc.relevance)}
          ${scoreBar('Clarity', sc.clarity)}
          ${scoreBar('Depth', sc.depth)}
          ${scoreBar('Communication', sc.communication)}
          ${scoreBar('Fluency', sc.fluency)}
          ${scoreBar('Avg Words', ev.stats.avg_words_per_answer, true)}
        </div>

        <!-- Stats Row -->
        <div style="display:flex;justify-content:space-around;padding:12px;background:var(--bg-elevated);border-radius:8px;margin-bottom:24px;text-align:center">
          <div><div style="font-size:1.1rem;font-weight:700;color:var(--accent-gold)">${stats.total_questions}</div><div style="font-size:0.65rem;color:var(--text-muted)">Questions</div></div>
          <div><div style="font-size:1.1rem;font-weight:700;color:var(--accent-emerald)">${stats.total_words}</div><div style="font-size:0.65rem;color:var(--text-muted)">Words</div></div>
          <div><div style="font-size:1.1rem;font-weight:700;color:${stats.filler_words_count > 5 ? 'var(--accent-red)' : 'var(--text-primary)'}">${stats.filler_words_count}</div><div style="font-size:0.65rem;color:var(--text-muted)">Fillers</div></div>
        </div>

        <!-- Per-Question Review -->
        <h4 style="font-size:0.85rem;color:var(--text-muted);margin-bottom:12px;text-transform:uppercase;letter-spacing:0.5px">Per-Question Feedback</h4>
        <div style="margin-bottom:24px">
          ${(ev.question_reviews || []).map(q => questionCard(q)).join('') || '<p style="color:var(--text-muted);font-size:0.82rem">No per-question data available.</p>'}
        </div>

        <!-- Strengths & Improvements -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px">
          <div style="background:rgba(16,185,129,0.05);border:1px solid rgba(16,185,129,0.2);border-radius:10px;padding:14px">
            <div style="font-size:0.72rem;color:var(--accent-emerald);font-weight:700;margin-bottom:8px">✓ STRENGTHS</div>
            ${(ev.top_strengths || ['Completed the interview']).map(s => `<div style="font-size:0.78rem;color:var(--text-secondary);margin-bottom:4px">• ${esc(s)}</div>`).join('')}
          </div>
          <div style="background:rgba(245,184,0,0.05);border:1px solid rgba(245,184,0,0.2);border-radius:10px;padding:14px">
            <div style="font-size:0.72rem;color:var(--accent-gold);font-weight:700;margin-bottom:8px">→ IMPROVE</div>
            ${(ev.areas_to_improve || ['Practice with more mock interviews']).map(s => `<div style="font-size:0.78rem;color:var(--text-secondary);margin-bottom:4px">• ${esc(s)}</div>`).join('')}
          </div>
        </div>

        <!-- Overall AI Suggestion -->
        <div style="background:rgba(99,102,241,0.05);border-left:3px solid #6366f1;border-radius:0 8px 8px 0;padding:14px;margin-bottom:20px">
          <div style="font-size:0.7rem;color:#8b5cf6;font-weight:700;margin-bottom:6px">🤖 AI COACHING TIPS</div>
          <div style="font-size:0.82rem;line-height:1.7;color:var(--text-secondary);white-space:pre-line">${esc(ev.overall_suggestion || 'Complete a full interview session for personalized coaching tips.')}</div>
        </div>

        <!-- Actions -->
        <div style="display:flex;gap:10px;justify-content:center">
          <button class="btn btn-primary" id="home-btn" style="padding:10px 24px;border-radius:8px">← Dashboard</button>
          <button class="btn btn-secondary" id="retry-btn" style="padding:10px 24px;border-radius:8px">🔄 Practice Again</button>
        </div>
      </div>
    `;

    rpt.querySelector('#home-btn').onclick = () => navigate('/dashboard');
    rpt.querySelector('#retry-btn').onclick = () => { rpt.style.display = 'none'; resetUI(); };
  }

  function scoreBar(label, value, isCount = false) {
    const v = isCount ? value : value;
    const pct = isCount ? Math.min(100, (value / 60) * 100) : (value / 10) * 100;
    const color = isCount ? 'var(--accent-gold)' : value >= 7 ? 'var(--accent-emerald)' : value >= 5 ? 'var(--accent-gold)' : 'var(--accent-red)';
    return `<div style="text-align:center">
      <div style="font-size:1rem;font-weight:700;color:${color}">${isCount ? value : value + '/10'}</div>
      <div style="font-size:0.65rem;color:var(--text-muted);margin-top:2px">${label}</div>
      <div style="height:3px;background:var(--bg-elevated);border-radius:2px;margin-top:4px"><div style="height:100%;width:${pct}%;background:${color};border-radius:2px"></div></div>
    </div>`;
  }

  function questionCard(q) {
    const avg = q.scores.average;
    const color = avg >= 7 ? 'var(--accent-emerald)' : avg >= 5 ? 'var(--accent-gold)' : 'var(--accent-red)';
    return `<div style="border:1px solid var(--border);border-radius:10px;padding:12px;margin-bottom:10px;border-left:3px solid ${color}">
      <div style="display:flex;justify-content:space-between;margin-bottom:6px">
        <span style="font-size:0.72rem;font-weight:600;color:var(--text-muted)">Q${q.question_number}</span>
        <span style="font-size:0.78rem;font-weight:700;color:${color}">${avg}/10</span>
      </div>
      <div style="font-size:0.78rem;color:var(--text-primary);margin-bottom:6px;font-style:italic">"${esc(q.question.slice(0, 120))}"</div>
      <div style="font-size:0.72rem;color:var(--text-muted);margin-bottom:8px">Your answer: "${esc(q.answer_preview.slice(0, 100))}${q.answer_preview.length > 100 ? '...' : ''}" (${q.word_count} words)</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px">
        ${miniScore('REL', q.scores.relevance)}${miniScore('CLR', q.scores.clarity)}${miniScore('DPT', q.scores.depth)}${miniScore('COM', q.scores.communication)}
      </div>
      <div style="font-size:0.72rem;color:var(--accent-emerald)">✓ ${esc(q.strength)}</div>
      <div style="font-size:0.72rem;color:var(--accent-amber);margin-top:2px">→ ${esc(q.suggestion)}</div>
    </div>`;
  }

  function miniScore(label, val) {
    const c = val >= 7 ? '#10b981' : val >= 5 ? '#f5b800' : '#ef4444';
    return `<span style="font-size:0.6rem;padding:2px 5px;border-radius:4px;background:${c}20;color:${c};font-weight:600">${label}:${val}</span>`;
  }

  function esc(s) { if (!s) return ''; const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
}
