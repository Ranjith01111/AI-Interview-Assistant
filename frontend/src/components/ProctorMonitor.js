/* AI Proctoring Monitor — webcam + fullscreen enforcement + frame analysis */
import { proctor } from '../api/index.js';
import { Toast } from './Toast.js';

export class ProctorMonitor {
  constructor(sessionId, options = {}) {
    this.sessionId = sessionId;
    this._skipFullscreen = options.skipFullscreen || false;
    this._skipExitFullscreen = options.skipExitFullscreen || false;
    this.el = null;
    this.video = null;
    this.canvas = document.createElement('canvas');
    this.stream = null;
    this.interval = null;
    this.minimized = false;
    this.violationCount = 0;
    this.onSessionEnd = options.onSessionEnd || null; // callback when session must end
    this._boundVis = this._onVisChange.bind(this);
    this._boundCopy = this._onCopy.bind(this);
    this._boundFullscreenChange = this._onFullscreenChange.bind(this);
    this._isFullscreen = false;
    this._sessionEnded = false;
    this._tabSwitchCount = 0;
    this._voiceViolationCount = 0;
    this._audioContext = null;
    this._audioAnalyser = null;
    this._audioInterval = null;
    this._audioStream = null;
    this._lastSoundAlert = 0; // cooldown timestamp
    this._voiceDetectionPaused = false; // pause during voice input mode
  }

  async mount(parentEl) {
    if (!this._skipFullscreen) {
      // Show fullscreen prompt first
      const accepted = await this._showFullscreenPrompt(parentEl);
      if (!accepted) {
        Toast.error('Fullscreen is required for proctoring. Session cannot start.', 'Proctor');
        return false;
      }

      // Enter fullscreen
      await this._enterFullscreen();
    }

    // Create proctor widget
    this.el = document.createElement('div');
    this.el.className = 'proctor-monitor';
    this.el.innerHTML = `
      <div class="proctor-header">
        <div class="proctor-status">
          <div class="proctor-dot" id="proctor-dot"></div>
          <span id="proctor-status-text">Proctoring</span>
        </div>
        <button class="proctor-toggle-btn" id="proctor-min-btn" title="Minimize">⬇</button>
      </div>
      <div class="proctor-video-wrap" id="proctor-vid-wrap">
        <video class="proctor-video" id="proctor-video" autoplay muted playsinline></video>
        <div class="proctor-overlay" id="proctor-overlay">
          <div class="proctor-alert-text" id="proctor-alert-text">⚠️ Violation</div>
        </div>
      </div>
      <div class="proctor-violations" id="proctor-viol-list"></div>
    `;
    parentEl.appendChild(this.el);

    this.el.querySelector('#proctor-min-btn').onclick = () => this._toggleMinimize();
    this.el.onclick = () => { if (this.minimized) this._toggleMinimize(); };
    this._makeDraggable();

    await this._startCamera();
    await this._startAudioDetection();
    this._startAnalysis();
    this._attachBrowserEvents();

    return true;
  }

  /* Fullscreen prompt popup */
  _showFullscreenPrompt(parentEl) {
    return new Promise((resolve) => {
      const overlay = document.createElement('div');
      overlay.className = 'proctor-fullscreen-prompt';
      overlay.innerHTML = `
        <div class="proctor-prompt-card">
          <div class="proctor-prompt-icon">🖥️</div>
          <h2>Fullscreen Required</h2>
          <p>This session requires fullscreen mode for proctoring.<br>
          Your screen, camera, and activity will be monitored.</p>
          <div class="proctor-prompt-rules">
            <div class="rule-item">📷 Camera will be active</div>
            <div class="rule-item">🖥️ Fullscreen must remain active</div>
            <div class="rule-item">🚫 Tab switching is not allowed</div>
            <div class="rule-item">🔇 No talking / external sound</div>
            <div class="rule-item">⚠️ Pressing Esc will end the session</div>
          </div>
          <div style="display:flex;gap:12px;margin-top:20px">
            <button class="btn btn-primary btn-lg" id="proctor-accept-btn">✓ Enter Fullscreen & Start</button>
            <button class="btn btn-ghost" id="proctor-decline-btn">Cancel</button>
          </div>
        </div>
      `;
      parentEl.appendChild(overlay);

      overlay.querySelector('#proctor-accept-btn').onclick = () => {
        overlay.remove();
        resolve(true);
      };
      overlay.querySelector('#proctor-decline-btn').onclick = () => {
        overlay.remove();
        resolve(false);
      };
    });
  }

  async _enterFullscreen() {
    try {
      const docEl = document.documentElement;
      if (docEl.requestFullscreen) {
        await docEl.requestFullscreen();
      } else if (docEl.webkitRequestFullscreen) {
        await docEl.webkitRequestFullscreen();
      } else if (docEl.msRequestFullscreen) {
        await docEl.msRequestFullscreen();
      }
      this._isFullscreen = true;
    } catch (e) {
      Toast.warning('Could not enter fullscreen. Proctoring continues.', 'Proctor');
    }
  }

  _onFullscreenChange() {
    const isNowFullscreen = !!(document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement);

    if (this._isFullscreen && !isNowFullscreen && !this._sessionEnded) {
      // User pressed Esc or exited fullscreen — end session
      this._sessionEnded = true;
      Toast.error('Fullscreen exited! Session ending automatically.', 'Proctoring');
      proctor.logEvent(this.sessionId, 'FULLSCREEN_EXIT', { detail: 'Candidate exited fullscreen — session terminated' });

      // Trigger session end callback
      if (this.onSessionEnd) {
        setTimeout(() => this.onSessionEnd(), 1000);
      }
    }
    this._isFullscreen = isNowFullscreen;
  }

  async _startCamera() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ video: { width:320, height:240 }, audio: true });
      this.video = this.el.querySelector('#proctor-video');
      this.video.srcObject = this.stream;
    } catch (e) {
      Toast.warning('Camera not available — proctoring limited.', 'Proctor');
    }
  }

  async _startAudioDetection() {
    try {
      // Use audio track from existing stream, or get a separate one
      let audioStream = this.stream;
      if (!audioStream || audioStream.getAudioTracks().length === 0) {
        audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      }
      this._audioStream = audioStream;

      this._audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = this._audioContext.createMediaStreamSource(audioStream);
      this._audioAnalyser = this._audioContext.createAnalyser();
      this._audioAnalyser.fftSize = 512;
      this._audioAnalyser.smoothingTimeConstant = 0.3;
      source.connect(this._audioAnalyser);

      // Check audio levels every 2 seconds
      this._audioInterval = setInterval(() => this._checkAudioLevel(), 2000);
    } catch (e) {
      // Audio detection not available — continue without it
      console.warn('Audio detection not available:', e.message);
    }
  }

  _checkAudioLevel() {
    if (!this._audioAnalyser || this._sessionEnded || this._voiceDetectionPaused) return;

    const dataArray = new Uint8Array(this._audioAnalyser.frequencyBinCount);
    this._audioAnalyser.getByteFrequencyData(dataArray);

    // Calculate average volume
    const avg = dataArray.reduce((sum, val) => sum + val, 0) / dataArray.length;

    // Threshold: avg > 45 means someone is speaking (adjust if needed)
    const VOICE_THRESHOLD = 45;
    const now = Date.now();

    if (avg > VOICE_THRESHOLD && (now - this._lastSoundAlert > 10000)) {
      // Cooldown: at least 10 seconds between alerts
      this._lastSoundAlert = now;
      this._voiceViolationCount++;
      proctor.logEvent(this.sessionId, 'VOICE_DETECTED', { detail: `Voice/sound detected (level: ${Math.round(avg)})`, count: this._voiceViolationCount });

      if (this._voiceViolationCount >= 3) {
        Toast.error('❌ Voice detected 3 times! Session ending.', 'Proctoring');
        this._addViolationEntry('3rd voice detection — session terminated');
        this._sessionEnded = true;
        if (this.onSessionEnd) {
          setTimeout(() => this.onSessionEnd(), 1000);
        }
      } else {
        const remaining = 3 - this._voiceViolationCount;
        Toast.error(`🔊 Voice/sound detected! ${remaining} warning${remaining > 1 ? 's' : ''} left.`, 'Proctoring');
        this._addViolationEntry(`Voice detected (${this._voiceViolationCount}/3)`);
      }
    }
  }

  /**
   * Pause voice/sound detection — call when candidate is using voice input mode.
   * This prevents false violations while the candidate is speaking into the mic.
   */
  pauseVoiceDetection() {
    this._voiceDetectionPaused = true;
    const statusText = this.el?.querySelector('#proctor-status-text');
    if (statusText) statusText.textContent = 'Monitoring (voice mode)';
  }

  /**
   * Resume voice/sound detection — call when candidate switches back to text mode.
   */
  resumeVoiceDetection() {
    this._voiceDetectionPaused = false;
    const statusText = this.el?.querySelector('#proctor-status-text');
    if (statusText) statusText.textContent = 'Monitoring';
  }

  _startAnalysis() {
    this.interval = setInterval(() => this._analyzeFrame(), 15000);
  }

  async _analyzeFrame() {
    if (!this.video || !this.stream) return;
    try {
      this.canvas.width  = 320;
      this.canvas.height = 240;
      const ctx = this.canvas.getContext('2d');
      ctx.drawImage(this.video, 0, 0, 320, 240);
      const imageData = this.canvas.toDataURL('image/jpeg', 0.6);
      const result = await proctor.analyzeFrame(this.sessionId, imageData);
      this._handleResult(result);
    } catch (_) {}
  }

  _handleResult(result) {
    if (!result.violations?.length) {
      this._setStatus('Monitoring', false);
      return;
    }
    this.violationCount += result.violations.length;
    const firstMsg = result.violations[0]?.details?.violation || result.violations[0]?.event_type;
    this._setStatus('⚠ Violation', true);
    this._showAlert(firstMsg);
    this._addViolationEntry(firstMsg);
    Toast.error(firstMsg, 'Proctoring Alert');
    setTimeout(() => this._clearAlert(), 4000);
  }

  _setStatus(text, isAlert) {
    const dot = this.el?.querySelector('#proctor-dot');
    const txt = this.el?.querySelector('#proctor-status-text');
    if (dot) { dot.classList.toggle('alert', isAlert); }
    if (txt)  txt.textContent = text;
  }

  _showAlert(msg) {
    const overlay = this.el?.querySelector('#proctor-overlay');
    const alertTxt = this.el?.querySelector('#proctor-alert-text');
    if (overlay) overlay.classList.add('alert');
    if (alertTxt) alertTxt.textContent = `⚠️ ${msg}`;
  }

  _clearAlert() {
    this.el?.querySelector('#proctor-overlay')?.classList.remove('alert');
    this._setStatus('Monitoring', false);
  }

  _addViolationEntry(msg) {
    const list = this.el?.querySelector('#proctor-viol-list');
    if (!list) return;
    const item = document.createElement('div');
    item.className = 'proctor-viol-item';
    item.textContent = `${new Date().toLocaleTimeString()}: ${msg}`;
    list.prepend(item);
    if (list.children.length > 6) list.lastChild?.remove();
  }

  _toggleMinimize() {
    this.minimized = !this.minimized;
    this.el.classList.toggle('minimized', this.minimized);
    const minBtn = this.el.querySelector('#proctor-min-btn');
    if (minBtn) minBtn.textContent = this.minimized ? '⬆' : '⬇';
  }

  _onVisChange() {
    if (document.hidden) {
      this._tabSwitchCount++;
      proctor.logEvent(this.sessionId, 'TAB_SWITCH', { detail: 'Candidate switched tabs' });

      if (this._tabSwitchCount >= 3) {
        Toast.error('❌ 3 tab switches detected! Session ending.', 'Proctoring');
        this._addViolationEntry('3rd tab switch — session terminated');
        this._sessionEnded = true;
        if (this.onSessionEnd) {
          setTimeout(() => this.onSessionEnd(), 1000);
        }
      } else {
        const remaining = 3 - this._tabSwitchCount;
        Toast.error(`⚠️ Tab switch detected! ${remaining} warning${remaining > 1 ? 's' : ''} left before session ends.`, 'Proctoring Alert');
        this._addViolationEntry(`Tab switch (${this._tabSwitchCount}/3)`);
      }
    }
  }

  _onCopy(e) {
    proctor.logEvent(this.sessionId, 'COPY_PASTE', { detail: 'Copy/paste detected during interview' });
    Toast.warning('Copy/paste detected.', 'Proctoring');
  }

  _attachBrowserEvents() {
    document.addEventListener('visibilitychange', this._boundVis);
    document.addEventListener('copy', this._boundCopy);
    document.addEventListener('paste', this._boundCopy);
    document.addEventListener('fullscreenchange', this._boundFullscreenChange);
    document.addEventListener('webkitfullscreenchange', this._boundFullscreenChange);
    window.addEventListener('blur', () => {
      proctor.logEvent(this.sessionId, 'WINDOW_BLUR', { detail: 'Window lost focus' });
    });
  }

  _makeDraggable() {
    let isDragging = false;
    let startX, startY, startLeft, startTop;

    const header = this.el.querySelector('.proctor-header');
    const target = this.el;

    const onMouseDown = (e) => {
      if (this.minimized) return;
      isDragging = true;
      target.classList.add('dragging');
      const rect = target.getBoundingClientRect();
      startX = e.clientX || e.touches?.[0]?.clientX;
      startY = e.clientY || e.touches?.[0]?.clientY;
      startLeft = rect.left;
      startTop = rect.top;
      e.preventDefault();
    };

    const onMouseMove = (e) => {
      if (!isDragging) return;
      const cx = e.clientX || e.touches?.[0]?.clientX;
      const cy = e.clientY || e.touches?.[0]?.clientY;
      const dx = cx - startX;
      const dy = cy - startY;
      target.style.left = (startLeft + dx) + 'px';
      target.style.top = (startTop + dy) + 'px';
      target.style.right = 'auto';
      target.style.bottom = 'auto';
    };

    const onMouseUp = () => {
      isDragging = false;
      target.classList.remove('dragging');
    };

    header.addEventListener('mousedown', onMouseDown);
    header.addEventListener('touchstart', onMouseDown, { passive: false });
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('touchmove', onMouseMove, { passive: false });
    document.addEventListener('mouseup', onMouseUp);
    document.addEventListener('touchend', onMouseUp);
  }

  destroy() {
    this._sessionEnded = true;
    clearInterval(this.interval);
    if (this._audioInterval) { clearInterval(this._audioInterval); this._audioInterval = null; }
    if (this._audioContext) {
      try { this._audioContext.close(); } catch(_) {}
    }
    this.stream?.getTracks().forEach(t => t.stop());
    document.removeEventListener('visibilitychange', this._boundVis);
    document.removeEventListener('copy', this._boundCopy);
    document.removeEventListener('paste', this._boundCopy);
    document.removeEventListener('fullscreenchange', this._boundFullscreenChange);
    document.removeEventListener('webkitfullscreenchange', this._boundFullscreenChange);
    this.el?.remove();

    // Exit fullscreen if still in it (unless told to keep it)
    if (!this._skipExitFullscreen && (document.fullscreenElement || document.webkitFullscreenElement)) {
      try {
        if (document.exitFullscreen) document.exitFullscreen();
        else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
      } catch(_) {}
    }
  }
}
