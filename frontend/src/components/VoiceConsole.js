/* Voice Interview Console — Uses browser-native Web Speech API for STT
 * and Backend edge-tts (neural voices) for TTS.
 *
 * FIXED ISSUES (2026-06-29):
 * 1. TTS now uses backend /api/v1/tts/speak (neural voice) instead of browser SpeechSynthesis
 * 2. Auto-submit after 3.5 seconds of silence (like Verbal Interview page)
 * 3. Properly passes answered/total count to parent callback for progress tracking
 * 4. Handles recognition restart gracefully without crash loops
 */
import { interview } from '../api/index.js';
import { Toast } from './Toast.js';

const SILENCE_TIMEOUT = 3500; // ms before auto-submit after last speech
const NO_SPEECH_TIMEOUT = 15000; // ms before warning user no speech detected

export class VoiceConsole {
  constructor(sessionId, onMessage) {
    this.sessionId = sessionId;
    this.onMessage = onMessage;
    this.el = null;
    this.recognition = null;
    this.isListening = false;
    this.isSpeaking = false;
    this.transcript = '';
    this.state = 'idle'; // idle | listening | processing | speaking | completed
    this.silenceTimer = null;
    this.noSpeechTimer = null;
    this.currentAudio = null;
    this._restartAttempts = 0;
    this._initSpeechRecognition();
  }

  _initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      Toast.error('Speech Recognition not supported in this browser. Use Chrome or Edge.', 'Voice');
      return;
    }
    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';

    this.recognition.onresult = (event) => {
      if (!this.isListening) return;

      // Clear no-speech timer since we got results
      if (this.noSpeechTimer) {
        clearTimeout(this.noSpeechTimer);
        this.noSpeechTimer = null;
      }

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

      // Reset silence timer — auto-submit after silence
      if (this.silenceTimer) clearTimeout(this.silenceTimer);
      this.silenceTimer = setTimeout(() => this._onSilenceDetected(), SILENCE_TIMEOUT);
    };

    this.recognition.onerror = (event) => {
      if (event.error === 'no-speech') {
        // Ignore — just means silence, recognition will restart
        return;
      }
      if (event.error === 'aborted') return;
      if (event.error === 'not-allowed') {
        Toast.error('Microphone access denied. Please allow microphone in browser settings.', 'Voice');
        this._stopListening();
        return;
      }
      console.warn('[VoiceConsole] Speech error:', event.error);
    };

    this.recognition.onend = () => {
      if (this.isListening && this._restartAttempts < 5) {
        // Auto-restart to keep listening
        this._restartAttempts++;
        setTimeout(() => {
          if (this.isListening) {
            try { this.recognition.start(); } catch(e) {}
          }
        }, 100);
      }
    };
  }

  render() {
    this.el = document.createElement('div');
    this.el.className = 'voice-console-compact';
    this.el.innerHTML = `
      <div style="display:flex; align-items:center; gap:var(--spacing-md); background:var(--bg-elevated); padding:12px; border-radius:12px; border:1px solid var(--border); box-shadow:0 4px 12px rgba(0,0,0,0.1)">
        
        <div style="position:relative; width:60px; height:60px; flex-shrink:0" class="compact-orb-wrap">
          <div class="voice-orb" id="voice-orb" style="width:100%; height:100%; font-size:1.5rem; border-radius:50%; background:var(--grad-primary); display:flex; align-items:center; justify-content:center; cursor:pointer; box-shadow:0 0 15px rgba(245,184,0,0.3); transition:all 0.3s ease;">🎤</div>
        </div>
        
        <div style="flex:1; display:flex; flex-direction:column; gap:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center">
            <span class="voice-status" id="voice-status" style="font-weight:600; color:var(--text-primary); font-size:0.9rem">Click mic to start listening</span>
            <div style="display:flex; gap:8px">
               <button class="btn btn-success btn-sm" id="voice-submit-btn" disabled style="padding:4px 12px">📤 Submit</button>
               <button class="btn btn-ghost btn-sm" id="voice-clear-btn" style="padding:4px 8px" title="Clear transcript">🗑️</button>
               <button id="voice-listen-btn" style="display:none"></button>
            </div>
          </div>
          <div class="voice-transcript" id="voice-transcript" style="font-size:0.85rem; color:var(--text-secondary); max-height:50px; overflow-y:auto; background:rgba(0,0,0,0.2); padding:6px 10px; border-radius:6px; min-height:30px">
            Your spoken answer will appear here...
          </div>
        </div>

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
    this._restartAttempts = 0;
    this._updateTranscript('');
    try {
      this.recognition.start();
    } catch(e) {}
    this._setState('listening');
    const btn = this.el.querySelector('#voice-listen-btn');
    btn.textContent = '⏹ Stop Listening';
    btn.classList.replace('btn-primary', 'btn-danger');

    // Set no-speech timeout — warn user if no speech detected for 15s
    this.noSpeechTimer = setTimeout(() => {
      if (this.isListening && !this.transcript.trim()) {
        Toast.info('No speech detected. Make sure your microphone is working.', 'Voice');
      }
    }, NO_SPEECH_TIMEOUT);
  }

  _stopListening() {
    this.isListening = false;
    if (this.silenceTimer) { clearTimeout(this.silenceTimer); this.silenceTimer = null; }
    if (this.noSpeechTimer) { clearTimeout(this.noSpeechTimer); this.noSpeechTimer = null; }
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

  _onSilenceDetected() {
    // Auto-submit after silence if we have a meaningful transcript
    const text = this.transcript.trim();
    if (text && text.split(/\s+/).length >= 3) {
      // At least 3 words — auto-submit
      this._submitAnswer();
    } else if (text) {
      // Very short — give user a nudge but don't auto-submit
      Toast.info('Speak more or click Submit when ready.', 'Voice');
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

      // Pass proper data to parent including answered count for progress tracking
      this.onMessage?.({
        text: resp.message,
        is_complete: resp.is_interview_complete,
        feedback: resp.feedback,
        answered: resp.current_question_number || 0,
        total: resp.total_questions || 0,
      });

      // Speak the AI response using backend TTS (neural voice)
      await this._speak(resp.message);

      if (resp.is_interview_complete) {
        this._setState('completed');
      } else {
        // Ready for next answer
        this._clearTranscript();
        this._setState('idle');
        // Auto-start listening for next answer after AI finishes speaking
        setTimeout(() => {
          if (this.state !== 'completed') {
            this._startListening();
          }
        }, 500);
      }
    } catch (err) {
      Toast.error(err.message, 'Voice Interview');
      this._setState('idle');
    }
  }

  _speak(text) {
    return new Promise((resolve) => {
      // Clean markdown for TTS
      const clean = text
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/[❓💡👋🎉🏁✅⚠️👍🤖]/g, '')
        .replace(/---/g, '')
        .replace(/\n/g, '. ')
        .trim();

      if (!clean) { resolve(); return; }

      this.isSpeaking = true;
      this._setState('speaking');

      // Use backend edge-tts neural voice (much better quality than browser SpeechSynthesis)
      const ttsUrl = '/api/v1/tts/speak?text=' + encodeURIComponent(clean.slice(0, 490));
      const audio = new Audio(ttsUrl);
      audio.volume = 1.0;
      this.currentAudio = audio;

      // Minimum speaking time based on text length (prevents cutting short)
      const minMs = Math.max(clean.length * 55, 3000);
      let audioDone = false, timerDone = false;

      const check = () => {
        if (audioDone && timerDone) {
          this.isSpeaking = false;
          this.currentAudio = null;
          resolve();
        }
      };

      setTimeout(() => { timerDone = true; check(); }, minMs);

      audio.onended = () => { audioDone = true; check(); };
      audio.onerror = (e) => {
        console.warn('[VoiceConsole] TTS audio error, falling back to browser TTS:', e);
        audioDone = true;
        // Fallback to browser SpeechSynthesis if backend TTS fails
        this._browserSpeak(clean).then(() => { check(); });
      };
      audio.play().catch(() => {
        // Audio play blocked (no user interaction) — fallback
        audioDone = true;
        this._browserSpeak(clean).then(() => { check(); });
      });
    });
  }

  _browserSpeak(text) {
    // Fallback: use browser SpeechSynthesis if backend TTS fails
    return new Promise((resolve) => {
      const synth = window.speechSynthesis;
      if (!synth) { resolve(); return; }

      const utterance = new SpeechSynthesisUtterance(text.slice(0, 300));
      utterance.rate = 1.0;
      utterance.pitch = 1.0;

      // Pick a good English voice
      const voices = synth.getVoices();
      const preferred = voices.find(v => v.name.includes('Google') && v.lang.startsWith('en'))
                     || voices.find(v => v.lang.startsWith('en-'));
      if (preferred) utterance.voice = preferred;

      utterance.onend = resolve;
      utterance.onerror = resolve;
      synth.speak(utterance);

      // Safety timeout — don't hang forever
      setTimeout(resolve, 20000);
    });
  }

  _clearTranscript() {
    this.transcript = '';
    this._updateTranscript('');
    this.el.querySelector('#voice-submit-btn').disabled = true;
    if (this.silenceTimer) { clearTimeout(this.silenceTimer); this.silenceTimer = null; }
  }

  _updateTranscript(text) {
    const el = this.el?.querySelector('#voice-transcript');
    if (el) {
      el.textContent = text || 'Your spoken answer will appear here...';
      el.style.color = text ? 'var(--text-primary)' : 'var(--text-secondary)';
      // Auto-scroll to bottom
      el.scrollTop = el.scrollHeight;
    }
    // Enable/disable submit button
    const submitBtn = this.el?.querySelector('#voice-submit-btn');
    if (submitBtn) {
      submitBtn.disabled = !text?.trim();
    }
  }

  _setState(state) {
    this.state = state;
    const orb = this.el?.querySelector('#voice-orb');
    const status = this.el?.querySelector('#voice-status');

    const config = {
      idle:       { icon: '🎤', text: 'Ready — click to listen', cls: '' },
      listening:  { icon: '👂', text: 'Listening... speak your answer (auto-submits on silence)', cls: 'listening' },
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
    if (this.silenceTimer) { clearTimeout(this.silenceTimer); this.silenceTimer = null; }
    if (this.noSpeechTimer) { clearTimeout(this.noSpeechTimer); this.noSpeechTimer = null; }
    try { this.recognition?.stop(); } catch(e) {}
    if (this.currentAudio) {
      try { this.currentAudio.pause(); this.currentAudio.src = ''; } catch(e) {}
      this.currentAudio = null;
    }
    window.speechSynthesis?.cancel();
  }
}
