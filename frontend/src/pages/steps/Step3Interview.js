/* Step 3 — Mock Interview (Text Chat) — with 25-minute timer */
import { interview } from '../../api/index.js';
import { Toast } from '../../components/Toast.js';
import { ProctorMonitor } from '../../components/ProctorMonitor.js';
import { VoiceConsole } from '../../components/VoiceConsole.js';

const INTERVIEW_TIME_LIMIT = 25 * 60; // 25 minutes in seconds

export async function renderStep3(container, state, onNext, onForceEnd) {
  container.innerHTML = `
    <div style="padding:var(--spacing-md) var(--spacing-lg) 0;animation:slideUp 0.4s ease">
      <!-- Progress bar + Timer + Submit -->
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:var(--spacing-md)">
        <span style="font-size:0.8rem;color:var(--text-muted)" id="q-fraction">0 / ${state.totalQuestions || '?'} answered</span>
        <div class="progress-bar" style="flex:1"><div class="progress-fill" id="q-progress" style="width:0%"></div></div>
        <div class="panel-timer" id="panel-timer">
          <span class="timer-icon">⏱</span>
          <span class="timer-display" id="timer-display">25:00</span>
        </div>
        <button class="btn btn-primary btn-sm" id="submit-interview-btn" style="display:none">✓ Submit</button>
        <button class="btn btn-ghost" id="end-interview-btn" style="color:var(--accent-red);font-size:0.8rem;padding:4px 10px;border:1px solid var(--accent-red);border-radius:6px">⏹ End</button>
      </div>

      <!-- Chat Panel (full width, no sidebar) -->
      <div class="chat-panel" style="max-width:100%">
        <div class="chat-header">
          <div style="display:flex;align-items:center;gap:8px">
            <div style="width:8px;height:8px;border-radius:50%;background:var(--accent-emerald);animation:ping 1.5s infinite"></div>
            <span style="font-weight:600;font-size:0.9rem">Live Interview</span>
          </div>
          <div class="chat-mode-toggle">
            <button class="mode-btn active" id="mode-text">💬 Text</button>
            <button class="mode-btn" id="mode-voice">🎤 Voice</button>
          </div>
        </div>
        <div class="chat-messages" id="chat-messages"></div>
        <!-- Text input -->
        <div class="chat-input-area" id="text-input-area">
          <textarea class="chat-textarea" id="chat-input" placeholder="Type your answer here… (Shift+Enter for new line)" rows="1"></textarea>
          <button class="btn btn-primary chat-send-btn" id="send-btn">Send</button>
        </div>
        <!-- Voice panel (hidden by default) -->
        <div id="voice-input-area" style="display:none"></div>
      </div>
    </div>
  `;

  let proctor = null;
  let voice = null;
  let answered = 0;
  let isComplete = false;
  let allQuestionsAnswered = false;
  let timerInterval = null;
  let timeRemaining = INTERVIEW_TIME_LIMIT;

  /* Start Timer */
  function startTimer() {
    updateTimerDisplay();
    timerInterval = setInterval(() => {
      timeRemaining--;
      updateTimerDisplay();
      if (timeRemaining <= 0) {
        clearInterval(timerInterval);
        timerInterval = null;
        Toast.warning('⏰ Time is up! Interview panel ending automatically.', 'Time Over');
        finishInterview();
      }
    }, 1000);
  }

  function updateTimerDisplay() {
    const mins = Math.floor(timeRemaining / 60);
    const secs = timeRemaining % 60;
    const display = container.querySelector('#timer-display');
    if (display) {
      display.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
      // Change color when less than 5 minutes
      const timerEl = container.querySelector('#panel-timer');
      if (timeRemaining <= 300) {
        timerEl.classList.add('timer-warning');
      }
      if (timeRemaining <= 60) {
        timerEl.classList.add('timer-critical');
      }
    }
  }

  /* Start interview */
  try {
    const startData = await interview.startInterview(state.sessionId);
    addMessage('ai', startData.message);
    startTimer(); // Start countdown
  } catch (err) {
    Toast.error(err.message, 'Start Failed');
    return;
  }

  /* Proctoring — with fullscreen enforcement */
  proctor = new ProctorMonitor(state.sessionId, {
    onSessionEnd: () => {
      // Esc pressed / fullscreen exited → go directly to final summary
      if (onForceEnd) onForceEnd();
    },
    skipExitFullscreen: true
  });
  await proctor.mount(document.body);

  /* Mode toggle */
  const modeText = container.querySelector('#mode-text');
  const modeVoice = container.querySelector('#mode-voice');
  const textArea = container.querySelector('#text-input-area');
  const voiceArea = container.querySelector('#voice-input-area');

  modeText.onclick = () => {
    modeText.classList.add('active'); modeVoice.classList.remove('active');
    textArea.style.display = ''; voiceArea.style.display = 'none';
    voice?.destroy(); voice = null;
    proctor?.resumeVoiceDetection();
  };
  modeVoice.onclick = () => {
    modeVoice.classList.add('active'); modeText.classList.remove('active');
    voiceArea.style.display = ''; textArea.style.display = 'none';
    voice = new VoiceConsole(state.sessionId, handleVoiceMessage);
    voiceArea.appendChild(voice.render());
    proctor?.pauseVoiceDetection();
  };

  /* Submit button — only shows after all questions answered */
  container.querySelector('#submit-interview-btn').onclick = () => {
    finishInterview();
  };

  /* End interview early */
  container.querySelector('#end-interview-btn').onclick = () => {
    if (confirm('End the interview now? Your progress will be saved.')) {
      finishInterview();
    }
  };

  /* Auto-resize textarea */
  const chatInput = container.querySelector('#chat-input');
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
  });
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
  container.querySelector('#send-btn').onclick = sendMessage;

  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || isComplete) return;
    chatInput.value = '';
    chatInput.style.height = 'auto';
    addMessage('user', text);
    showTyping();
    container.querySelector('#send-btn').disabled = true;

    try {
      const resp = await interview.chat(state.sessionId, text);
      removeTyping();
      addMessage('ai', resp.message);
      answered = resp.current_question_number || (answered + 1);
      updateProgress(answered, resp.total_questions || state.totalQuestions);

      if (resp.is_interview_complete || answered >= (resp.total_questions || state.totalQuestions || 10)) {
        // Don't auto-finish — show Submit button
        allQuestionsAnswered = true;
        container.querySelector('#submit-interview-btn').style.display = '';
        Toast.success('All questions answered! Click Submit to proceed.', 'Ready');
      }
    } catch (err) {
      removeTyping();
      Toast.error(err.message, 'Error');
    }
    container.querySelector('#send-btn').disabled = false;
  }

  function handleVoiceMessage(msg) {
    addMessage('ai', msg.text);
    if (msg.is_complete || msg.answered >= (state.totalQuestions || 10)) {
      allQuestionsAnswered = true;
      container.querySelector('#submit-interview-btn').style.display = '';
      Toast.success('All questions answered! Click Submit to proceed.', 'Ready');
    }
  }

  function finishInterview() {
    if (isComplete) return;
    isComplete = true;
    // Stop timer
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
    state.interviewPanel = 'completed';
    state.interviewComplete = true;
    proctor?.destroy();
    voice?.destroy();
    container.querySelector('#text-input-area').style.display = 'none';
    Toast.success('Interview complete! Moving to next step...', 'Done');
    // Auto-advance to next step after brief delay
    setTimeout(() => { if (onNext) onNext(); }, 1500);
  }

  function addMessage(role, text) {
    const msgs = container.querySelector('#chat-messages');
    const div = document.createElement('div');
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
    const div = document.createElement('div');
    div.id = 'typing-indicator';
    div.className = 'message ai';
    div.innerHTML = `<div class="message-avatar">🤖</div><div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>`;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function removeTyping() {
    container.querySelector('#typing-indicator')?.remove();
  }

  function updateProgress(qNum, total) {
    const t = total || state.totalQuestions;
    const pct = Math.min((qNum / t) * 100, 100);
    container.querySelector('#q-progress').style.width = pct + '%';
    container.querySelector('#q-fraction').textContent = `${qNum} / ${t} answered`;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatText(text) {
    return escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
  }

  /* Clean up proctor + timer on navigate away */
  container._destroyProctor = () => {
    proctor?.destroy();
    voice?.destroy();
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
  };
}
