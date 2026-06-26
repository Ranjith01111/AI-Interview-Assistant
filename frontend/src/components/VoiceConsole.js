/* Voice Interview Console — Uses browser-native Web Speech API (fully offline)
 * No external APIs needed. Uses:
 * - SpeechRecognition (STT) — listens to candidate
 * - SpeechSynthesis (TTS) — reads questions aloud
 * - Regular HTTP API for interview logic
 */
import { interview } from '../api/index.js';
import { Toast } from './Toast.js';

export class VoiceConsole {
  constructor(sessionId, onMessage) {
    this.sessionId = sessionId;
    this.onMessage = onMessage;
    this.el = null;
    this.recognition = null;
    this.synth = window.speechSynthesis;
    this.isListening = false;
    this.isSpeaking = false;
    this.transcript = '';
    this.state = 'idle'; // idle | listening | processing | speaking | completed
    this._initSpeechRecognition();
  }

  _initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      Toast.error('Speech Recognition not supported in this browser. Use Chrome.', 'Voice');
      return;
    }
    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';

    this.recognition.onresult = (event) => {
      let interim = '';
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += t + ' ';
        } else {
          interim += t;
        }
      }
      if (final) this.transcript += final;
      this._updateTranscript(this.transcript + interim);
    };

    this.recognition.onerror = (event) => {
      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        Toast.error(`Speech error: ${event.error}`, 'Voice');
      }
    };

    this.recognition.onend = () => {
      if (this.isListening) {
        // Auto-restart if still in listening mode
        try { this.recognition.start(); } catch(e) {}
      }
    };
  }

  render() {
    this.el = document.createElement('div');
    this.el.className = 'voice-console';
    this.el.innerHTML = `
      <div class="voice-orb-wrap">
        <div class="voice-rings"></div>
        <div class="voice-rings"></div>
        <div class="voice-rings"></div>
        <div class="voice-orb" id="voice-orb">🎤</div>
      </div>
      <div class="voice-status" id="voice-status">Click mic to start listening</div>
      <div class="voice-transcript" id="voice-transcript" style="min-height:60px;max-height:120px;overflow-y:auto;padding:8px;background:rgba(0,0,0,0.3);border-radius:8px;font-size:0.85rem;color:var(--text-secondary);margin:8px 0">
        Your spoken answer will appear here...
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn btn-primary btn-sm" id="voice-listen-btn">🎤 Start Listening</button>
        <button class="btn btn-success btn-sm" id="voice-submit-btn" disabled>📤 Submit Answer</button>
        <button class="btn btn-ghost btn-sm" id="voice-clear-btn">🗑️ Clear</button>
      </div>
    `;

    const orb = this.el.querySelector('#voice-orb');
    orb.onclick = () => this._toggleListening();

    this.el.querySelector('#voice-listen-btn').onclick = () => this._toggleListening();
    this.el.querySelector('#voice-submit-btn').onclick = () => this._submitAnswer();
    this.el.querySelector('#voice-clear-btn').onclick = () => this._clearTranscript();

    return this.el;
  }

  _toggleListening() {
    if (this.isSpeaking) return; // Don't listen while AI is speaking
    if (this.isListening) {
      this._stopListening();
    } else {
      this._startListening();
    }
  }

  _startListening() {
    if (!this.recognition) {
      Toast.error('Speech Recognition not available', 'Voice');
      return;
    }
    this.isListening = true;
    this.transcript = '';
    this._updateTranscript('');
    try {
      this.recognition.start();
    } catch(e) {}
    this._setState('listening');
    const btn = this.el.querySelector('#voice-listen-btn');
    btn.textContent = '⏹ Stop Listening';
    btn.classList.replace('btn-primary', 'btn-danger');
  }

  _stopListening() {
    this.isListening = false;
    try { this.recognition?.stop(); } catch(e) {}
    this._setState('idle');
    const btn = this.el.querySelector('#voice-listen-btn');
    btn.textContent = '🎤 Start Listening';
    btn.classList.replace('btn-danger', 'btn-primary');
    // Enable submit if there's text
    if (this.transcript.trim()) {
      this.el.querySelector('#voice-submit-btn').disabled = false;
    }
  }

  async _submitAnswer() {
    const text = this.transcript.trim();
    if (!text) {
      Toast.warning('No answer detected. Speak first, then submit.', 'Voice');
      return;
    }

    this._stopListening();
    this._setState('processing');
    this.el.querySelector('#voice-submit-btn').disabled = true;

    try {
      const resp = await interview.chat(this.sessionId, text);
      
      // Show the response
      this.onMessage?.({
        text: resp.message,
        is_complete: resp.is_interview_complete,
        feedback: resp.feedback,
      });

      // Speak the AI response
      await this._speak(resp.message);

      if (resp.is_interview_complete) {
        this._setState('completed');
      } else {
        // Ready for next answer
        this._clearTranscript();
        this._setState('idle');
      }
    } catch (err) {
      Toast.error(err.message, 'Voice Interview');
      this._setState('idle');
    }
  }

  _speak(text) {
    return new Promise((resolve) => {
      if (!this.synth) { resolve(); return; }
      // Clean markdown for TTS
      const clean = text
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/[❓💡👋🎉🏁✅⚠️👍]/g, '')
        .replace(/---/g, '')
        .replace(/\n/g, '. ')
        .trim();

      if (!clean) { resolve(); return; }

      this.isSpeaking = true;
      this._setState('speaking');

      const utterance = new SpeechSynthesisUtterance(clean);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      
      // Try to pick a good English voice
      const voices = this.synth.getVoices();
      const preferred = voices.find(v => v.name.includes('Google') && v.lang.startsWith('en'))
                     || voices.find(v => v.lang.startsWith('en-'));
      if (preferred) utterance.voice = preferred;

      utterance.onend = () => {
        this.isSpeaking = false;
        this._setState('idle');
        resolve();
      };
      utterance.onerror = () => {
        this.isSpeaking = false;
        this._setState('idle');
        resolve();
      };

      this.synth.speak(utterance);
    });
  }

  _clearTranscript() {
    this.transcript = '';
    this._updateTranscript('');
    this.el.querySelector('#voice-submit-btn').disabled = true;
  }

  _updateTranscript(text) {
    const el = this.el?.querySelector('#voice-transcript');
    if (el) {
      el.textContent = text || 'Your spoken answer will appear here...';
      el.style.color = text ? 'var(--text-primary)' : 'var(--text-secondary)';
    }
  }

  _setState(state) {
    this.state = state;
    const orb = this.el?.querySelector('#voice-orb');
    const status = this.el?.querySelector('#voice-status');
    
    const config = {
      idle:       { icon: '🎤', text: 'Ready — click to listen', cls: '' },
      listening:  { icon: '👂', text: 'Listening... speak your answer', cls: 'listening' },
      processing: { icon: '⏳', text: 'Processing your answer...', cls: 'processing' },
      speaking:   { icon: '🔊', text: 'AI is speaking...', cls: 'speaking' },
      completed:  { icon: '✅', text: 'Interview complete!', cls: 'completed' },
    };
    const c = config[state] || config.idle;
    if (orb) { orb.textContent = c.icon; orb.className = `voice-orb ${c.cls}`; }
    if (status) status.textContent = c.text;
  }

  destroy() {
    this.isListening = false;
    try { this.recognition?.stop(); } catch(e) {}
    this.synth?.cancel();
  }
}
