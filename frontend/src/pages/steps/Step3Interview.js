/* Step 3 — Mock Interview (Text Chat) — with Session Timer + Per-Question Timer */
import { interview } from '../../api/index.js';
import { Toast } from '../../components/Toast.js';
import { ProctorMonitor } from '../../components/ProctorMonitor.js';
import { VoiceConsole } from '../../components/VoiceConsole.js';
import { QuestionTimer } from '../../components/QuestionTimer.js';

export async function renderStep3(container, state, onNext, onForceEnd) {
  const timerPerQuestion = state.interviewConfig?.timer_seconds || 0;
  // Use EXACTLY the session time the user configured — no default fallback
  const sessionMinutes   = state.interviewConfig?.session_time_minutes ?? 0;
  const hasSessionTimer  = sessionMinutes > 0;
  const INTERVIEW_TIME_LIMIT = sessionMinutes * 60;

  container.innerHTML = `
    <div class="interview-step-wrap">

      <!-- Top control bar -->
      <div class="interview-control-bar">
        <div class="icb-left">
          <span class="icb-answered" id="q-fraction">0 answered</span>
          <div class="progress-bar icb-progress">
            <div class="progress-fill" id="q-progress" style="width:0%"></div>
          </div>
        </div>
        <div class="icb-right">
          ${hasSessionTimer ? `
          <div class="panel-timer" id="panel-timer">
            <span class="timer-icon">⏱</span>
            <span class="timer-display" id="timer-display">${String(sessionMinutes).padStart(2,'0')}:00</span>
          </div>` : ''}
          <button class="btn btn-primary btn-sm" id="submit-interview-btn" style="display:none">✓ Submit</button>
          <button class="btn btn-sm interview-end-btn" id="end-interview-btn">⏹ End</button>
        </div>
      </div>

      <!-- Chat panel — fixed height, no layout jump -->
      <div class="chat-panel interview-chat-panel">
        <div class="chat-header">
          <div class="chat-header-left">
            <div class="live-dot"></div>
            <span class="chat-header-title">Live Interview</span>
            ${timerPerQuestion > 0
              ? `<span class="timer-badge">⏱️ ${timerPerQuestion}s/question</span>`
              : ''}
          </div>
          <div class="chat-mode-toggle">
            <button class="mode-btn active" id="mode-text">💬 Text</button>
            <button class="mode-btn" id="mode-voice">🎤 Voice</button>
          </div>
        </div>

        <!-- Per-question timer strip (only shown when timer > 0) -->
        <div id="question-timer-area" class="question-timer-strip" style="display:${timerPerQuestion > 0 ? 'flex' : 'none'}"></div>

        <div class="chat-messages" id="chat-messages"></div>

        <!-- Text input -->
        <div class="chat-input-area" id="text-input-area">
          <textarea class="chat-textarea" id="chat-input"
            placeholder="Type your answer here… (Shift+Enter for new line)" rows="1"></textarea>
          <button class="btn btn-primary chat-send-btn" id="send-btn">Send</button>
        </div>

        <!-- Voice panel (hidden by default) -->
        <div id="voice-input-area" style="display:none"></div>
      </div>

    </div>
  `;

  let proctor  = null;
  let voice    = null;
  let answered = 0;
  let isComplete         = false;
  let allQuestionsAnswered = false;
  let timerInterval      = null;
  let timeRemaining      = INTERVIEW_TIME_LIMIT;

  // ── Per-Question Timer ──────────────────────────────────────────
  let questionTimer = null;
  if (timerPerQuestion > 0) {
    questionTimer = new QuestionTimer({
      seconds: timerPerQuestion,
      onTimeout: () => {
        Toast.warning("⏰ Time's up for this question!", 'Auto-submitting');
        autoSubmitOnTimeout();
      },
      onWarning: (remaining) => {
        Toast.info(`⚠️ ${remaining}s remaining for this question`);
      },
      onTick: () => {},
    });
    const timerArea = container.querySelector('#question-timer-area');
    const timerEl   = questionTimer.render();
    if (timerEl) timerArea.appendChild(timerEl);
  }

  // ── Session Timer (only if user configured a duration) ─────────
  function startSessionTimer() {
    if (!hasSessionTimer) return;
    updateTimerDisplay();
    timerInterval = setInterval(() => {
      timeRemaining--;
      updateTimerDisplay();
      if (timeRemaining <= 0) {
        clearInterval(timerInterval);
        timerInterval = null;
        Toast.warning('⏰ Time is up! Interview ending automatically.', 'Time Over');
        finishInterview();
      }
    }, 1000);
  }

  function updateTimerDisplay() {
    const mins    = Math.floor(timeRemaining / 60);
    const secs    = timeRemaining % 60;
    const display = container.querySelector('#timer-display');
    if (!display) return;
    display.textContent = `${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}`;
    const timerEl = container.querySelector('#panel-timer');
    if (timerEl) {
      if (timeRemaining <= 300) timerEl.classList.add('timer-warning');
      if (timeRemaining <= 60)  timerEl.classList.add('timer-critical');
    }
  }

  // ── Start Interview ─────────────────────────────────────────────
  try {
    const startData = await interview.startInterview(state.sessionId);
    addMessage('ai', startData.message);
    // Only start session timer if user explicitly set a duration
    if (hasSessionTimer) startSessionTimer();
    questionTimer?.start();
  } catch (err) {
    Toast.error(err.message, 'Start Failed');
    return;
  }

  // ── Proctoring ──────────────────────────────────────────────────
  proctor = new ProctorMonitor(state.sessionId, {
    onSessionEnd: () => { if (onForceEnd) onForceEnd(); },
    skipExitFullscreen: true,
  });
  await proctor.mount(document.body);

  // ── Mode Toggle ─────────────────────────────────────────────────
  const modeText  = container.querySelector('#mode-text');
  const modeVoice = container.querySelector('#mode-voice');
  const textArea  = container.querySelector('#text-input-area');
  const voiceArea = container.querySelector('#voice-input-area');

  modeText.onclick = () => {
    modeText.classList.add('active'); modeVoice.classList.remove('active');
    textArea.style.display = '';      voiceArea.style.display = 'none';
    voice?.destroy(); voice = null;
    proctor?.resumeVoiceDetection();
  };
  modeVoice.onclick = () => {
    modeVoice.classList.add('active'); modeText.classList.remove('active');
    voiceArea.style.display = '';      textArea.style.display = 'none';
    voice = new VoiceConsole(state.sessionId, handleVoiceMessage);
    voiceArea.appendChild(voice.render());
    proctor?.pauseVoiceDetection();
  };

  // ── Submit / End buttons ────────────────────────────────────────
  container.querySelector('#submit-interview-btn').onclick = () => finishInterview();
  container.querySelector('#end-interview-btn').onclick = () => {
    if (confirm('End the interview now? Your progress will be saved.')) finishInterview();
  };

  // ── Textarea auto-resize ────────────────────────────────────────
  const chatInput = container.querySelector('#chat-input');
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
  });
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
  container.querySelector('#send-btn').onclick = sendMessage;

  // ── Auto-submit on question timeout ────────────────────────────
  function autoSubmitOnTimeout() {
    if (!chatInput.value.trim()) chatInput.value = '[Time expired — no answer provided]';
    sendMessage();
  }

  // ── Send Message ────────────────────────────────────────────────
  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || isComplete) return;
    chatInput.value = '';
    chatInput.style.height = 'auto';
    addMessage('user', text);
    showTyping();
    container.querySelector('#send-btn').disabled = true;
    questionTimer?.pause();

    try {
      const resp = await interview.chat(state.sessionId, text);
      removeTyping();
      addMessage('ai', resp.message);

      if (!resp.is_follow_up) {
        answered = resp.current_question_number || (answered + 1);
        updateProgress(answered, resp.total_questions || state.totalQuestions);
      }

      if (resp.is_interview_complete) {
        allQuestionsAnswered = true;
        questionTimer?.stop();
        container.querySelector('#submit-interview-btn').style.display = '';
        Toast.success('All questions answered! Click Submit to proceed.', 'Ready');
      } else {
        questionTimer?.start();
      }
    } catch (err) {
      removeTyping();
      Toast.error(err.message, 'Error');
      questionTimer?.resume();
    }
    container.querySelector('#send-btn').disabled = false;
  }

  function handleVoiceMessage(msg) {
    if (msg.text) addMessage('ai', msg.text);
    if (msg.answered) {
      answered = msg.answered;
      updateProgress(answered, msg.total || state.totalQuestions);
    }
    if (msg.is_complete) {
      allQuestionsAnswered = true;
      questionTimer?.stop();
      container.querySelector('#submit-interview-btn').style.display = '';
      Toast.success('All questions answered! Click Submit to proceed.', 'Ready');
    } else {
      questionTimer?.start();
    }
  }

  function finishInterview() {
    if (isComplete) return;
    isComplete = true;
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
    questionTimer?.destroy();
    state.interviewPanel   = 'completed';
    state.interviewComplete = true;
    proctor?.destroy();
    voice?.destroy();
    container.querySelector('#text-input-area').style.display = 'none';
    Toast.success('Interview complete! Moving to next step...', 'Done');
    setTimeout(() => { if (onNext) onNext(); }, 1500);
  }

  // ── Message helpers ─────────────────────────────────────────────
  function addMessage(role, text) {
    const msgs = container.querySelector('#chat-messages');
    const div  = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `
      <div class="message-avatar">${role === 'ai' ? '🤖' : '👤'}</div>
      <div class="message-bubble">${formatText(text)}</div>
    `;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function showTyping() {
    const msgs = container.querySelector('#chat-messages');
    const div  = document.createElement('div');
    div.id = 'typing-indicator';
    div.className = 'message ai';
    div.innerHTML = `<div class="message-avatar">🤖</div><div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>`;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function removeTyping() { container.querySelector('#typing-indicator')?.remove(); }

  function updateProgress(qNum, total) {
    const t   = total || state.totalQuestions;
    const pct = Math.min((qNum / t) * 100, 100);
    container.querySelector('#q-progress').style.width = pct + '%';
    container.querySelector('#q-fraction').textContent = `${qNum} of ${t} answered`;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g,  '&amp;')
      .replace(/</g,  '&lt;')
      .replace(/>/g,  '&gt;')
      .replace(/"/g,  '&quot;');
  }

  function formatText(text) {
    return escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
  }

  // ── Cleanup on navigate away ────────────────────────────────────
  container._destroyProctor = () => {
    proctor?.destroy();
    voice?.destroy();
    questionTimer?.destroy();
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
  };
}
