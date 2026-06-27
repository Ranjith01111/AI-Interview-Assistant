/**
 * RecruiterNotes Component
 * 
 * Collapsible panel for recruiter notes on a session summary page.
 * Features:
 *   - View existing notes with author name + timestamp
 *   - Add new note with private/shared toggle
 *   - Delete own notes (X button)
 *   - Dark + Gold (#f5b800) theme
 * 
 * Usage:
 *   import { RecruiterNotes } from './components/RecruiterNotes.js';
 *   const notesPanel = new RecruiterNotes(sessionId);
 *   notesPanel.mount(document.getElementById('notes-container'));
 */

import { apiJSON } from '../api/client.js';

export class RecruiterNotes {
  constructor(sessionId) {
    this.sessionId = sessionId;
    this.el = null;
    this.notes = [];
    this.collapsed = false;
    this.currentUserId = null;

    // Get current user from localStorage
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      this.currentUserId = user.id || null;
    } catch { /* ignore */ }
  }

  async mount(parentEl) {
    this.el = document.createElement('div');
    this.el.className = 'recruiter-notes-panel';
    this.el.innerHTML = this._template();
    parentEl.appendChild(this.el);

    this._injectStyles();
    this._bindEvents();
    await this._loadNotes();
  }

  // —— Template ————————————————————————————————————————————————

  _template() {
    return `
      <div class="rn-header" id="rn-header">
        <div class="rn-header-left">
          <svg class="rn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14,2 14,8 20,8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10,9 9,9 8,9"/>
          </svg>
          <h3 class="rn-title">Recruiter Notes</h3>
          <span class="rn-badge" id="rn-count">0</span>
        </div>
        <button class="rn-collapse-btn" id="rn-collapse-btn" title="Toggle panel">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <polyline points="6,9 12,15 18,9"/>
          </svg>
        </button>
      </div>

      <div class="rn-body" id="rn-body">
        <!-- Notes List -->
        <div class="rn-notes-list" id="rn-notes-list">
          <div class="rn-empty" id="rn-empty">No notes yet. Add the first one below.</div>
        </div>

        <!-- Add Note Form -->
        <div class="rn-form">
          <textarea 
            class="rn-textarea" 
            id="rn-textarea" 
            placeholder="Add a note about this candidate..."
            rows="3"
            maxlength="5000"
          ></textarea>
          <div class="rn-form-actions">
            <label class="rn-private-toggle">
              <input type="checkbox" id="rn-private-check" checked />
              <span class="rn-toggle-label">Private</span>
              <span class="rn-toggle-hint" id="rn-toggle-hint">Only you can see this</span>
            </label>
            <button class="rn-add-btn" id="rn-add-btn" disabled>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Add Note
            </button>
          </div>
        </div>
      </div>
    `;
  }

  // —— Events ————————————————————————————————————————————————————

  _bindEvents() {
    // Collapse toggle
    const header = this.el.querySelector('#rn-header');
    header.addEventListener('click', () => this._toggleCollapse());

    // Textarea input → enable/disable button
    const textarea = this.el.querySelector('#rn-textarea');
    const addBtn = this.el.querySelector('#rn-add-btn');
    textarea.addEventListener('input', () => {
      addBtn.disabled = !textarea.value.trim();
    });

    // Prevent collapse when clicking inside textarea
    textarea.addEventListener('click', (e) => e.stopPropagation());

    // Add note button
    addBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      this._addNote();
    });

    // Private toggle hint update
    const privateCheck = this.el.querySelector('#rn-private-check');
    const hint = this.el.querySelector('#rn-toggle-hint');
    privateCheck.addEventListener('change', (e) => {
      e.stopPropagation();
      hint.textContent = privateCheck.checked ? 'Only you can see this' : 'Visible to all recruiters';
    });

    // Stop propagation on form area
    const form = this.el.querySelector('.rn-form');
    form.addEventListener('click', (e) => e.stopPropagation());
  }

  _toggleCollapse() {
    this.collapsed = !this.collapsed;
    const body = this.el.querySelector('#rn-body');
    const btn = this.el.querySelector('#rn-collapse-btn');
    body.classList.toggle('collapsed', this.collapsed);
    btn.classList.toggle('rotated', this.collapsed);
  }

  // —— API Calls ——————————————————————————————————————————————————

  async _loadNotes() {
    try {
      const data = await apiJSON(`/recruiter/sessions/${this.sessionId}/notes`);
      this.notes = data.notes || [];
      this._renderNotes();
    } catch (err) {
      console.error('[RecruiterNotes] Failed to load notes:', err);
      this._showError('Failed to load notes');
    }
  }

  async _addNote() {
    const textarea = this.el.querySelector('#rn-textarea');
    const privateCheck = this.el.querySelector('#rn-private-check');
    const addBtn = this.el.querySelector('#rn-add-btn');
    const content = textarea.value.trim();

    if (!content) return;

    addBtn.disabled = true;
    addBtn.textContent = 'Saving...';

    try {
      const note = await apiJSON(`/recruiter/sessions/${this.sessionId}/notes`, {
        method: 'POST',
        body: JSON.stringify({
          content,
          is_private: privateCheck.checked,
        }),
      });

      // Prepend to local list (newest first)
      this.notes.unshift(note);
      this._renderNotes();

      // Clear form
      textarea.value = '';
      addBtn.disabled = true;
    } catch (err) {
      console.error('[RecruiterNotes] Failed to add note:', err);
      this._showError('Failed to save note');
    } finally {
      addBtn.disabled = false;
      addBtn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Add Note
      `;
    }
  }

  async _deleteNote(noteId) {
    if (!confirm('Delete this note?')) return;

    try {
      await apiJSON(`/recruiter/notes/${noteId}`, { method: 'DELETE' });
      this.notes = this.notes.filter(n => n.id !== noteId);
      this._renderNotes();
    } catch (err) {
      console.error('[RecruiterNotes] Failed to delete note:', err);
      this._showError('Failed to delete note');
    }
  }

  // —— Rendering ——————————————————————————————————————————————————

  _renderNotes() {
    const list = this.el.querySelector('#rn-notes-list');
    const empty = this.el.querySelector('#rn-empty');
    const badge = this.el.querySelector('#rn-count');

    badge.textContent = this.notes.length;

    if (this.notes.length === 0) {
      empty.style.display = 'block';
      // Remove any existing note cards
      list.querySelectorAll('.rn-note-card').forEach(el => el.remove());
      return;
    }

    empty.style.display = 'none';

    // Clear existing cards
    list.querySelectorAll('.rn-note-card').forEach(el => el.remove());

    for (const note of this.notes) {
      const card = document.createElement('div');
      card.className = 'rn-note-card';
      card.dataset.noteId = note.id;

      const isOwn = note.recruiter_id === this.currentUserId;
      const timeAgo = this._formatTime(note.created_at);
      const visibility = note.is_private
        ? '<span class="rn-vis-badge private">Private</span>'
        : '<span class="rn-vis-badge shared">Shared</span>';

      card.innerHTML = `
        <div class="rn-note-header">
          <div class="rn-note-meta">
            <span class="rn-author">${this._escapeHtml(note.recruiter_name)}</span>
            ${visibility}
            <span class="rn-time">${timeAgo}</span>
          </div>
          ${isOwn ? `<button class="rn-delete-btn" data-id="${note.id}" title="Delete note">✕</button>` : ''}
        </div>
        <div class="rn-note-content">${this._escapeHtml(note.content)}</div>
      `;

      // Bind delete button
      const delBtn = card.querySelector('.rn-delete-btn');
      if (delBtn) {
        delBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          this._deleteNote(note.id);
        });
      }

      list.appendChild(card);
    }
  }

  _showError(message) {
    // Simple inline error display
    const list = this.el.querySelector('#rn-notes-list');
    const errorEl = document.createElement('div');
    errorEl.className = 'rn-error';
    errorEl.textContent = `⚠ ${message}`;
    list.prepend(errorEl);
    setTimeout(() => errorEl.remove(), 4000);
  }

  // —— Utilities ——————————————————————————————————————————————————

  _formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMin = Math.floor(diffMs / 60000);

    if (diffMin < 1) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDays = Math.floor(diffHr / 24);
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  _escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // —— Styles ————————————————————————————————————————————————————

  _injectStyles() {
    if (document.getElementById('recruiter-notes-styles')) return;

    const style = document.createElement('style');
    style.id = 'recruiter-notes-styles';
    style.textContent = `
      .recruiter-notes-panel {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 12px;
        overflow: hidden;
        margin: 16px 0;
        font-family: 'Inter', -apple-system, sans-serif;
      }

      .rn-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 18px;
        cursor: pointer;
        background: #16162a;
        border-bottom: 1px solid #2a2a4a;
        transition: background 0.2s;
      }
      .rn-header:hover {
        background: #1e1e3a;
      }

      .rn-header-left {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .rn-icon {
        width: 20px;
        height: 20px;
        color: #f5b800;
      }

      .rn-title {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
        color: #e0e0e0;
      }

      .rn-badge {
        background: #f5b800;
        color: #1a1a2e;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 10px;
        min-width: 18px;
        text-align: center;
      }

      .rn-collapse-btn {
        background: none;
        border: none;
        color: #888;
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        transition: transform 0.3s, color 0.2s;
      }
      .rn-collapse-btn:hover { color: #f5b800; }
      .rn-collapse-btn.rotated { transform: rotate(-90deg); }

      .rn-body {
        max-height: 600px;
        overflow: hidden;
        transition: max-height 0.3s ease, opacity 0.3s;
        opacity: 1;
      }
      .rn-body.collapsed {
        max-height: 0;
        opacity: 0;
      }

      .rn-notes-list {
        max-height: 350px;
        overflow-y: auto;
        padding: 12px 18px;
      }
      .rn-notes-list::-webkit-scrollbar { width: 6px; }
      .rn-notes-list::-webkit-scrollbar-track { background: transparent; }
      .rn-notes-list::-webkit-scrollbar-thumb { background: #3a3a5a; border-radius: 3px; }

      .rn-empty {
        color: #666;
        font-size: 13px;
        text-align: center;
        padding: 20px 0;
      }

      .rn-note-card {
        background: #12122a;
        border: 1px solid #2a2a4a;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
        transition: border-color 0.2s;
      }
      .rn-note-card:hover {
        border-color: #3a3a5a;
      }

      .rn-note-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }

      .rn-note-meta {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
      }

      .rn-author {
        font-size: 12px;
        font-weight: 600;
        color: #f5b800;
      }

      .rn-vis-badge {
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .rn-vis-badge.private {
        background: rgba(245, 184, 0, 0.15);
        color: #f5b800;
      }
      .rn-vis-badge.shared {
        background: rgba(76, 175, 80, 0.15);
        color: #66bb6a;
      }

      .rn-time {
        font-size: 11px;
        color: #666;
      }

      .rn-delete-btn {
        background: none;
        border: none;
        color: #666;
        font-size: 14px;
        cursor: pointer;
        padding: 2px 6px;
        border-radius: 4px;
        transition: color 0.2s, background 0.2s;
      }
      .rn-delete-btn:hover {
        color: #ef5350;
        background: rgba(239, 83, 80, 0.1);
      }

      .rn-note-content {
        font-size: 13px;
        color: #ccc;
        line-height: 1.5;
        white-space: pre-wrap;
        word-break: break-word;
      }

      .rn-form {
        padding: 14px 18px;
        border-top: 1px solid #2a2a4a;
        background: #14142a;
      }

      .rn-textarea {
        width: 100%;
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 8px;
        padding: 10px 12px;
        color: #e0e0e0;
        font-size: 13px;
        font-family: inherit;
        resize: vertical;
        min-height: 60px;
        max-height: 150px;
        transition: border-color 0.2s;
        box-sizing: border-box;
      }
      .rn-textarea:focus {
        outline: none;
        border-color: #f5b800;
      }
      .rn-textarea::placeholder {
        color: #555;
      }

      .rn-form-actions {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 10px;
      }

      .rn-private-toggle {
        display: flex;
        align-items: center;
        gap: 6px;
        cursor: pointer;
        font-size: 12px;
        color: #999;
      }
      .rn-private-toggle input[type="checkbox"] {
        accent-color: #f5b800;
        width: 14px;
        height: 14px;
      }
      .rn-toggle-label {
        font-weight: 500;
        color: #ccc;
      }
      .rn-toggle-hint {
        font-size: 11px;
        color: #666;
      }

      .rn-add-btn {
        display: flex;
        align-items: center;
        gap: 6px;
        background: #f5b800;
        color: #1a1a2e;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        transition: opacity 0.2s, transform 0.1s;
      }
      .rn-add-btn:hover:not(:disabled) {
        opacity: 0.9;
        transform: translateY(-1px);
      }
      .rn-add-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }

      .rn-error {
        background: rgba(239, 83, 80, 0.1);
        border: 1px solid rgba(239, 83, 80, 0.3);
        color: #ef5350;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        margin-bottom: 8px;
        animation: rn-fade-in 0.3s;
      }

      @keyframes rn-fade-in {
        from { opacity: 0; transform: translateY(-4px); }
        to { opacity: 1; transform: translateY(0); }
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
