/* QuestionTimer — Per-question countdown timer with circular SVG arc */

export class QuestionTimer {
  /**
   * @param {Object} options
   * @param {number} options.seconds - Timer duration per question (0 = disabled)
   * @param {Function} options.onTimeout - Called when time runs out
   * @param {Function} [options.onWarning] - Called when warning threshold reached
   * @param {Function} [options.onTick] - Called every second with remaining time
   */
  constructor({ seconds = 0, onTimeout, onWarning, onTick }) {
    this.totalSeconds = seconds;
    this.remaining = seconds;
    this.onTimeout = onTimeout;
    this.onWarning = onWarning || (() => {});
    this.onTick = onTick || (() => {});
    this.interval = null;
    this.el = null;
    this.isRunning = false;
    this.hasWarned = false;
  }

  /**
   * Render the timer element. Returns a DOM node.
   */
  render() {
    if (this.totalSeconds <= 0) return null;

    this.el = document.createElement('div');
    this.el.className = 'question-timer';
    this.el.innerHTML = this._getHTML();
    return this.el;
  }

  /**
   * Start or restart the timer for a new question.
   */
  start() {
    if (this.totalSeconds <= 0) return;
    this.stop();
    this.remaining = this.totalSeconds;
    this.hasWarned = false;
    this.isRunning = true;
    this._updateDisplay();
    this._removeStates();

    this.interval = setInterval(() => {
      this.remaining--;
      this._updateDisplay();
      this.onTick(this.remaining);

      // Warning at 25% time remaining
      if (!this.hasWarned && this.remaining <= Math.ceil(this.totalSeconds * 0.25)) {
        this.hasWarned = true;
        this.el?.classList.add('timer-warning');
        this.onWarning(this.remaining);
      }

      // Critical at 10 seconds
      if (this.remaining <= 10 && this.remaining > 0) {
        this.el?.classList.remove('timer-warning');
        this.el?.classList.add('timer-critical');
      }

      // Timeout
      if (this.remaining <= 0) {
        this.stop();
        this.el?.classList.add('timer-expired');
        this.onTimeout();
      }
    }, 1000);
  }

  /**
   * Stop the timer.
   */
  stop() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
    this.isRunning = false;
  }

  /**
   * Pause the timer (e.g., while AI is responding).
   */
  pause() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
  }

  /**
   * Resume after pause.
   */
  resume() {
    if (this.remaining > 0 && this.isRunning && !this.interval) {
      this.interval = setInterval(() => {
        this.remaining--;
        this._updateDisplay();
        this.onTick(this.remaining);

        if (!this.hasWarned && this.remaining <= Math.ceil(this.totalSeconds * 0.25)) {
          this.hasWarned = true;
          this.el?.classList.add('timer-warning');
          this.onWarning(this.remaining);
        }
        if (this.remaining <= 10 && this.remaining > 0) {
          this.el?.classList.remove('timer-warning');
          this.el?.classList.add('timer-critical');
        }
        if (this.remaining <= 0) {
          this.stop();
          this.el?.classList.add('timer-expired');
          this.onTimeout();
        }
      }, 1000);
    }
  }

  /**
   * Reset timer for next question.
   */
  reset() {
    this.stop();
    this.remaining = this.totalSeconds;
    this.hasWarned = false;
    this.isRunning = false;
    this._removeStates();
    this._updateDisplay();
  }

  /**
   * Destroy and cleanup.
   */
  destroy() {
    this.stop();
    this.el?.remove();
    this.el = null;
  }

  // ── Private ──

  _getHTML() {
    const r = 20; // radius
    const circumference = 2 * Math.PI * r;
    return `
      <div class="qt-circle-wrap">
        <svg class="qt-svg" width="52" height="52" viewBox="0 0 52 52">
          <circle class="qt-track" cx="26" cy="26" r="${r}" />
          <circle class="qt-progress" cx="26" cy="26" r="${r}"
            stroke-dasharray="${circumference}"
            stroke-dashoffset="0"
            id="qt-arc" />
        </svg>
        <div class="qt-time" id="qt-time">${this._formatTime(this.totalSeconds)}</div>
      </div>
      <div class="qt-label">per question</div>
    `;
  }

  _updateDisplay() {
    if (!this.el) return;
    const timeEl = this.el.querySelector('#qt-time');
    const arcEl = this.el.querySelector('#qt-arc');

    if (timeEl) timeEl.textContent = this._formatTime(this.remaining);

    if (arcEl) {
      const r = 20;
      const circumference = 2 * Math.PI * r;
      const progress = 1 - (this.remaining / this.totalSeconds);
      arcEl.setAttribute('stroke-dashoffset', circumference * progress);
    }
  }

  _formatTime(secs) {
    if (secs <= 0) return '0s';
    if (secs < 60) return `${secs}s`;
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${String(s).padStart(2, '0')}`;
  }

  _removeStates() {
    this.el?.classList.remove('timer-warning', 'timer-critical', 'timer-expired');
  }
}
