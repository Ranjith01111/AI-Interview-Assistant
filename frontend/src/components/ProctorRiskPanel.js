/**
 * ProctorRiskPanel Component
 *
 * Collapsible risk dashboard for a session's proctoring data.
 * Features:
 *   - SVG donut gauge showing 0–100 risk score (green/amber/red)
 *   - Violation count badges grouped by type
 *   - Scrollable chronological event timeline
 *   - Auto-terminated session warning
 *   - Dark + Gold (#f5b800) theme
 *
 * Usage:
 *   import { ProctorRiskPanel } from './components/ProctorRiskPanel.js';
 *   const panel = new ProctorRiskPanel(sessionId);
 *   panel.mount(document.getElementById('proctoring-container'));
 */

import { apiJSON } from '../api/client.js';

export class ProctorRiskPanel {
  constructor(sessionId) {
    this.sessionId = sessionId;
    this.el = null;
    this.data = null;
    this.collapsed = false;
  }

  async mount(parentEl) {
    this.el = document.createElement('div');
    this.el.className = 'proctor-risk-panel';
    this.el.innerHTML = this._loadingTemplate();
    parentEl.appendChild(this.el);

    this._injectStyles();
    await this._loadData();
  }

  // —— Templates ——————————————————————————————————————————————————

  _loadingTemplate() {
    return `
      <div class="prp-header" id="prp-header">
        <div class="prp-header-left">
          <svg class="prp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <h3 class="prp-title">Proctoring Risk</h3>
        </div>
        <button class="prp-collapse-btn" id="prp-collapse-btn" title="Toggle panel">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <polyline points="6,9 12,15 18,9"/>
          </svg>
        </button>
      </div>
      <div class="prp-body" id="prp-body">
        <div class="prp-loading">
          <div class="prp-spinner"></div>
          <span>Analyzing proctoring data...</span>
        </div>
      </div>
    `;
  }

  _mainTemplate() {
    const { risk_score, risk_level, total_violations, violations_by_type, timeline, auto_terminated } = this.data;
    const color = this._riskColor(risk_level);
    const circumference = 2 * Math.PI * 54; // radius = 54
    const offset = circumference - (risk_score / 100) * circumference;

    return `
      <div class="prp-header" id="prp-header">
        <div class="prp-header-left">
          <svg class="prp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <h3 class="prp-title">Proctoring Risk</h3>
          <span class="prp-level-badge ${risk_level}">${risk_level.toUpperCase()}</span>
        </div>
        <button class="prp-collapse-btn" id="prp-collapse-btn" title="Toggle panel">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <polyline points="6,9 12,15 18,9"/>
          </svg>
        </button>
      </div>

      <div class="prp-body" id="prp-body">
        ${auto_terminated ? `
          <div class="prp-terminated-warning">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            Session was auto-terminated due to excessive violations
          </div>
        ` : ''}

        <!-- Score Gauge + Summary -->
        <div class="prp-score-section">
          <div class="prp-gauge-wrap">
            <svg class="prp-gauge" viewBox="0 0 120 120">
              <!-- Background ring -->
              <circle cx="60" cy="60" r="54" fill="none" stroke="#2a2a4a" stroke-width="8"/>
              <!-- Score arc -->
              <circle 
                cx="60" cy="60" r="54" 
                fill="none" 
                stroke="${color}" 
                stroke-width="8"
                stroke-linecap="round"
                stroke-dasharray="${circumference}"
                stroke-dashoffset="${offset}"
                transform="rotate(-90 60 60)"
                class="prp-gauge-arc"
              />
              <!-- Center text -->
              <text x="60" y="55" text-anchor="middle" class="prp-gauge-score" fill="${color}">${risk_score}</text>
              <text x="60" y="72" text-anchor="middle" class="prp-gauge-label" fill="#888">/ 100</text>
            </svg>
          </div>

          <div class="prp-stats">
            <div class="prp-stat-item">
              <span class="prp-stat-value">${total_violations}</span>
              <span class="prp-stat-label">Total Violations</span>
            </div>
            <div class="prp-stat-item">
              <span class="prp-stat-value">${violations_by_type.length}</span>
              <span class="prp-stat-label">Violation Types</span>
            </div>
            <div class="prp-stat-item">
              <span class="prp-stat-value prp-risk-${risk_level}">${risk_level}</span>
              <span class="prp-stat-label">Risk Level</span>
            </div>
          </div>
        </div>

        <!-- Violation Badges -->
        ${violations_by_type.length > 0 ? `
          <div class="prp-violations-section">
            <h4 class="prp-section-title">Violations by Type</h4>
            <div class="prp-violation-badges">
              ${violations_by_type.map(v => `
                <div class="prp-violation-badge" title="Risk weight: ${v.risk_weight}">
                  <span class="prp-vb-icon">${this._violationIcon(v.type)}</span>
                  <span class="prp-vb-label">${this._formatEventType(v.type)}</span>
                  <span class="prp-vb-count">${v.count}</span>
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}

        <!-- Timeline -->
        ${timeline.length > 0 ? `
          <div class="prp-timeline-section">
            <h4 class="prp-section-title">Event Timeline</h4>
            <div class="prp-timeline" id="prp-timeline">
              ${timeline.map((evt, i) => `
                <div class="prp-timeline-item ${i === 0 ? 'first' : ''}">
                  <div class="prp-tl-dot"></div>
                  <div class="prp-tl-content">
                    <div class="prp-tl-header">
                      <span class="prp-tl-type">${this._formatEventType(evt.event_type)}</span>
                      <span class="prp-tl-time">${this._formatTimestamp(evt.timestamp)}</span>
                    </div>
                    ${evt.details && evt.details.violation ? `
                      <div class="prp-tl-detail">${this._escapeHtml(evt.details.violation)}</div>
                    ` : ''}
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        ` : `
          <div class="prp-no-events">
            <span>✓ No proctoring violations recorded</span>
          </div>
        `}
      </div>
    `;
  }

  // —— Data Loading ———————————————————————————————————————————————

  async _loadData() {
    try {
      this.data = await apiJSON(`/recruiter/sessions/${this.sessionId}/proctoring`);
      this.el.innerHTML = this._mainTemplate();
      this._bindEvents();
    } catch (err) {
      console.error('[ProctorRiskPanel] Failed to load proctoring data:', err);
      this.el.querySelector('#prp-body').innerHTML = `
        <div class="prp-error">
          <span>⚠ Failed to load proctoring data: ${this._escapeHtml(err.message)}</span>
        </div>
      `;
      this._bindEvents();
    }
  }

  // —— Events ————————————————————————————————————————————————————

  _bindEvents() {
    const header = this.el.querySelector('#prp-header');
    if (header) {
      header.addEventListener('click', () => this._toggleCollapse());
    }
  }

  _toggleCollapse() {
    this.collapsed = !this.collapsed;
    const body = this.el.querySelector('#prp-body');
    const btn = this.el.querySelector('#prp-collapse-btn');
    if (body) body.classList.toggle('collapsed', this.collapsed);
    if (btn) btn.classList.toggle('rotated', this.collapsed);
  }

  // —— Utilities ——————————————————————————————————————————————————

  _riskColor(level) {
    switch (level) {
      case 'low': return '#4caf50';
      case 'medium': return '#f5b800';
      case 'high': return '#ef5350';
      default: return '#888';
    }
  }

  _violationIcon(type) {
    const icons = {
      'FACE_NOT_DETECTED': '👤',
      'MULTIPLE_FACES_DETECTED': '👥',
      'OBJECT_DETECTED': '📱',
      'GAZE_TRACKING_VIOLATION': '👁',
      'HEAD_POSE_VIOLATION': '🔄',
      'FACE_MISMATCH': '⚠️',
      'TAB_SWITCH': '🔀',
      'WINDOW_BLUR': '🪟',
      'WINDOW_RESIZE': '↔️',
      'FULLSCREEN_EXIT': '⛶',
      'COPY_PASTE': '📋',
      'VOICE_DETECTED': '🎤',
      'MULTIPLE_VOICES_DETECTED': '🗣️',
    };
    return icons[type] || '⚡';
  }

  _formatEventType(type) {
    return type
      .replace(/_/g, ' ')
      .toLowerCase()
      .replace(/\b\w/g, c => c.toUpperCase());
  }

  _formatTimestamp(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    });
  }

  _escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
  }

  // —— Styles ————————————————————————————————————————————————————

  _injectStyles() {
    if (document.getElementById('proctor-risk-panel-styles')) return;

    const style = document.createElement('style');
    style.id = 'proctor-risk-panel-styles';
    style.textContent = `
      .proctor-risk-panel {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 12px;
        overflow: hidden;
        margin: 16px 0;
        font-family: 'Inter', -apple-system, sans-serif;
      }

      .prp-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 18px;
        cursor: pointer;
        background: #16162a;
        border-bottom: 1px solid #2a2a4a;
        transition: background 0.2s;
      }
      .prp-header:hover { background: #1e1e3a; }

      .prp-header-left {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .prp-icon {
        width: 20px;
        height: 20px;
        color: #f5b800;
      }

      .prp-title {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
        color: #e0e0e0;
      }

      .prp-level-badge {
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .prp-level-badge.low { background: rgba(76,175,80,0.15); color: #4caf50; }
      .prp-level-badge.medium { background: rgba(245,184,0,0.15); color: #f5b800; }
      .prp-level-badge.high { background: rgba(239,83,80,0.15); color: #ef5350; }

      .prp-collapse-btn {
        background: none;
        border: none;
        color: #888;
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        transition: transform 0.3s, color 0.2s;
      }
      .prp-collapse-btn:hover { color: #f5b800; }
      .prp-collapse-btn.rotated { transform: rotate(-90deg); }

      .prp-body {
        max-height: 800px;
        overflow: hidden;
        transition: max-height 0.3s ease, opacity 0.3s;
        opacity: 1;
        padding: 18px;
      }
      .prp-body.collapsed {
        max-height: 0;
        opacity: 0;
        padding: 0 18px;
      }

      /* Terminated Warning */
      .prp-terminated-warning {
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(239, 83, 80, 0.1);
        border: 1px solid rgba(239, 83, 80, 0.3);
        color: #ef5350;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 500;
        margin-bottom: 18px;
      }

      /* Score Section */
      .prp-score-section {
        display: flex;
        align-items: center;
        gap: 30px;
        margin-bottom: 20px;
      }

      .prp-gauge-wrap {
        flex-shrink: 0;
      }
      .prp-gauge {
        width: 120px;
        height: 120px;
      }
      .prp-gauge-arc {
        transition: stroke-dashoffset 1s ease;
      }
      .prp-gauge-score {
        font-size: 26px;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
      }
      .prp-gauge-label {
        font-size: 11px;
      }

      .prp-stats {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .prp-stat-item {
        display: flex;
        flex-direction: column;
      }
      .prp-stat-value {
        font-size: 18px;
        font-weight: 700;
        color: #e0e0e0;
      }
      .prp-stat-label {
        font-size: 11px;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .prp-risk-low { color: #4caf50 !important; }
      .prp-risk-medium { color: #f5b800 !important; }
      .prp-risk-high { color: #ef5350 !important; }

      /* Violation Badges */
      .prp-violations-section {
        margin-bottom: 20px;
      }
      .prp-section-title {
        font-size: 12px;
        font-weight: 600;
        color: #999;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0 0 10px 0;
      }
      .prp-violation-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .prp-violation-badge {
        display: flex;
        align-items: center;
        gap: 6px;
        background: #12122a;
        border: 1px solid #2a2a4a;
        border-radius: 6px;
        padding: 6px 10px;
        transition: border-color 0.2s;
      }
      .prp-violation-badge:hover { border-color: #3a3a5a; }
      .prp-vb-icon { font-size: 14px; }
      .prp-vb-label {
        font-size: 11px;
        color: #ccc;
        font-weight: 500;
      }
      .prp-vb-count {
        background: #f5b800;
        color: #1a1a2e;
        font-size: 10px;
        font-weight: 700;
        padding: 1px 6px;
        border-radius: 8px;
        min-width: 16px;
        text-align: center;
      }

      /* Timeline */
      .prp-timeline-section {
        margin-top: 4px;
      }
      .prp-timeline {
        max-height: 280px;
        overflow-y: auto;
        padding-left: 16px;
        border-left: 2px solid #2a2a4a;
      }
      .prp-timeline::-webkit-scrollbar { width: 5px; }
      .prp-timeline::-webkit-scrollbar-track { background: transparent; }
      .prp-timeline::-webkit-scrollbar-thumb { background: #3a3a5a; border-radius: 3px; }

      .prp-timeline-item {
        position: relative;
        padding: 8px 0 8px 18px;
        border-bottom: 1px solid #1e1e38;
      }
      .prp-timeline-item:last-child { border-bottom: none; }

      .prp-tl-dot {
        position: absolute;
        left: -7px;
        top: 14px;
        width: 10px;
        height: 10px;
        background: #f5b800;
        border-radius: 50%;
        border: 2px solid #1a1a2e;
      }

      .prp-tl-content { }
      .prp-tl-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
      }
      .prp-tl-type {
        font-size: 12px;
        font-weight: 600;
        color: #e0e0e0;
      }
      .prp-tl-time {
        font-size: 11px;
        color: #666;
        font-family: 'JetBrains Mono', monospace;
      }
      .prp-tl-detail {
        font-size: 11px;
        color: #999;
        line-height: 1.4;
      }

      /* No Events */
      .prp-no-events {
        text-align: center;
        padding: 30px;
        color: #4caf50;
        font-size: 14px;
        font-weight: 500;
      }

      /* Loading */
      .prp-loading {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        padding: 40px;
        color: #888;
        font-size: 13px;
      }
      .prp-spinner {
        width: 20px;
        height: 20px;
        border: 2px solid #2a2a4a;
        border-top: 2px solid #f5b800;
        border-radius: 50%;
        animation: prp-spin 0.8s linear infinite;
      }
      @keyframes prp-spin {
        to { transform: rotate(360deg); }
      }

      /* Error */
      .prp-error {
        background: rgba(239, 83, 80, 0.1);
        border: 1px solid rgba(239, 83, 80, 0.3);
        color: #ef5350;
        padding: 12px 16px;
        border-radius: 8px;
        font-size: 12px;
        text-align: center;
      }
    `;
    document.head.appendChild(style);
  }

  // —— Cleanup ———————————————————————————————————————————————————

  destroy() {
    if (this.el && this.el.parentNode) {
      this.el.parentNode.removeChild(this.el);
    }
    this.el = null;
  }
}
