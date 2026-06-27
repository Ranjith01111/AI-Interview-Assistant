import { renderNavbar } from '../components/Navbar.js';
import { renderSidebar } from '../components/Sidebar.js';

/**
 * PipelinePage.js — Candidate Pipeline Kanban Board
 *
 * Vanilla JS implementation of a recruiter pipeline workflow.
 * Displays candidates in 5 columns: Screening → Shortlisted → Selected → Rejected → On Hold
 *
 * Features:
 * - Fetches pipeline data from /api/v1/recruiter/pipeline
 * - Kanban board with color-coded columns
 * - Move candidates between stages via dropdown
 * - Quick-notes modal on stage transitions
 * - Toast notifications for feedback
 * - Real-time count updates
 */

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Configuration
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const API_BASE = '/api/v1/recruiter';

const STAGES = [
    { key: 'screening', label: 'Screening', color: '#6b7280', icon: '🔍' },
    { key: 'shortlisted', label: 'Shortlisted', color: '#d97706', icon: '⭐' },
    { key: 'selected', label: 'Selected', color: '#059669', icon: '✅' },
    { key: 'rejected', label: 'Rejected', color: '#dc2626', icon: '❌' },
    { key: 'on_hold', label: 'On Hold', color: '#d97706', icon: '⏸️' },
];

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// State
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

let pipelineData = { stages: {}, counts: {}, total: 0 };
let activeDropdown = null;
let pendingMove = null; // { sessionId, candidateName, fromStage, toStage }

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// API Helpers
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function apiFetch(endpoint, options = {}) {
    const token = localStorage.getItem('access_token') || '';
    const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers,
        },
        ...options,
    });

    if (!response.ok) {
        const errBody = await response.json().catch(() => ({}));
        throw new Error(errBody.detail || `API error ${response.status}`);
    }

    return response.json();
}

async function fetchPipelineBoard() {
    return apiFetch('/pipeline');
}

async function updateCandidateStage(sessionId, stage, notes = '') {
    return apiFetch(`/candidates/${sessionId}/pipeline`, {
        method: 'PATCH',
        body: JSON.stringify({ stage, notes }),
    });
}

async function fetchCandidateNotes(sessionId) {
    return apiFetch(`/candidates/${sessionId}/notes`);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Rendering
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function getScoreClass(score) {
    if (score === null || score === undefined) return 'score-none';
    if (score >= 7.5) return 'score-high';
    if (score >= 5.0) return 'score-medium';
    return 'score-low';
}

function formatScore(score) {
    if (score === null || score === undefined) return '—';
    return score.toFixed(1);
}

function formatDate(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function renderSkillTags(skills) {
    if (!skills || skills.length === 0) return '';
    const displayed = skills.slice(0, 3);
    const remaining = skills.length - 3;

    let html = displayed.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('');
    if (remaining > 0) {
        html += `<span class="skill-tag">+${remaining}</span>`;
    }
    return html;
}

function renderCandidateCard(candidate) {
    const scoreClass = getScoreClass(candidate.average_score);
    const dateStr = formatDate(candidate.stage_updated_at || candidate.created_at);

    return `
        <div class="candidate-card" data-session-id="${candidate.session_id}" data-stage="${candidate.stage}">
            <div class="card-header">
                <span class="candidate-name">${escapeHtml(candidate.candidate_name)}</span>
                <span class="score-badge ${scoreClass}">${formatScore(candidate.average_score)}</span>
            </div>
            <div class="skills-list">
                ${renderSkillTags(candidate.skills)}
            </div>
            <div class="card-footer">
                <span class="card-date">${dateStr}</span>
                <div class="card-actions">
                    <button class="stage-move-btn" onclick="toggleDropdown(event, '${candidate.session_id}')">
                        Move ▾
                    </button>
                </div>
            </div>
            <div class="stage-dropdown" id="dropdown-${candidate.session_id}">
                ${renderDropdownItems(candidate.session_id, candidate.stage, candidate.candidate_name)}
            </div>
        </div>
    `;
}

function renderDropdownItems(sessionId, currentStage, candidateName) {
    return STAGES
        .filter(s => s.key !== currentStage)
        .map(s => `
            <div class="dropdown-item" onclick="initiateMove('${sessionId}', '${candidateName}', '${currentStage}', '${s.key}')">
                <span class="dot" style="background: ${s.color}"></span>
                ${s.icon} ${s.label}
            </div>
        `)
        .join('');
}

function renderColumn(stageConfig, candidates) {
    const count = candidates ? candidates.length : 0;

    return `
        <div class="pipeline-column stage-${stageConfig.key}">
            <div class="column-header">
                <div class="stage-label">
                    <span class="stage-dot"></span>
                    ${stageConfig.icon} ${stageConfig.label}
                </div>
                <span class="stage-count">${count}</span>
            </div>
            <div class="column-cards">
                ${candidates && candidates.length > 0
                    ? candidates.map(c => renderCandidateCard(c)).join('')
                    : ''
                }
            </div>
        </div>
    `;
}

function renderBoard() {
    const boardEl = document.getElementById('pipeline-board');
    if (!boardEl) return;

    boardEl.innerHTML = STAGES.map(stage => {
        const candidates = pipelineData.stages[stage.key] || [];
        return renderColumn(stage, candidates);
    }).join('');

    // Update total count
    const totalBadge = document.getElementById('total-badge');
    if (totalBadge) {
        totalBadge.textContent = `${pipelineData.total} candidates`;
    }
}

function renderPage() {
    const container = document.getElementById('pipeline-container');
    if (!container) return;

    container.innerHTML = `
        <div class="pipeline-page">
            <div class="pipeline-header">
                <div style="display:flex; align-items:center; gap:12px;">
                    <h1>📋 Candidate Pipeline</h1>
                    <span class="total-badge" id="total-badge">${pipelineData.total} candidates</span>
                </div>
                <div class="pipeline-filters">
                    <select id="filter-status" onchange="handleFilterChange()">
                        <option value="">All Sessions</option>
                        <option value="completed" selected>Completed Only</option>
                        <option value="in_progress">In Progress</option>
                    </select>
                    <button class="stage-move-btn" onclick="refreshBoard()" style="padding:8px 14px;">
                        🔄 Refresh
                    </button>
                </div>
            </div>
            <div class="pipeline-board" id="pipeline-board">
                <div class="pipeline-loading">
                    <div class="spinner"></div>
                    Loading pipeline...
                </div>
            </div>
        </div>

        <!-- Notes Modal -->
        <div class="modal-overlay" id="notes-modal">
            <div class="modal-content">
                <h3 id="modal-title">Move Candidate</h3>
                <p class="modal-subtitle" id="modal-subtitle"></p>
                <textarea
                    id="modal-notes"
                    placeholder="Add a note about this stage change (optional)..."
                ></textarea>
                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                    <button class="btn btn-primary" onclick="confirmMove()">Confirm Move</button>
                </div>
            </div>
        </div>

        <!-- Toast -->
        <div class="pipeline-toast" id="pipeline-toast"></div>
    `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Interactions
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function toggleDropdown(event, sessionId) {
    event.stopPropagation();

    // Close any open dropdown
    if (activeDropdown && activeDropdown !== sessionId) {
        const prevEl = document.getElementById(`dropdown-${activeDropdown}`);
        if (prevEl) prevEl.classList.remove('active');
    }

    const dropdown = document.getElementById(`dropdown-${sessionId}`);
    if (dropdown) {
        const isActive = dropdown.classList.contains('active');
        dropdown.classList.toggle('active');
        activeDropdown = isActive ? null : sessionId;
    }
}

function initiateMove(sessionId, candidateName, fromStage, toStage) {
    // Close dropdown
    closeAllDropdowns();

    // Store pending move
    pendingMove = { sessionId, candidateName, fromStage, toStage };

    // Get stage labels
    const fromLabel = STAGES.find(s => s.key === fromStage)?.label || fromStage;
    const toLabel = STAGES.find(s => s.key === toStage)?.label || toStage;

    // Show modal
    const modal = document.getElementById('notes-modal');
    const title = document.getElementById('modal-title');
    const subtitle = document.getElementById('modal-subtitle');
    const notesInput = document.getElementById('modal-notes');

    title.textContent = `Move ${candidateName}`;
    subtitle.textContent = `${fromLabel} → ${toLabel}`;
    notesInput.value = '';

    modal.classList.add('active');
    notesInput.focus();
}

async function confirmMove() {
    if (!pendingMove) return;

    const { sessionId, candidateName, fromStage, toStage } = pendingMove;
    const notes = document.getElementById('modal-notes')?.value || '';

    // Close modal immediately
    closeModal();

    try {
        await updateCandidateStage(sessionId, toStage, notes);

        // Optimistic UI update: move the card locally
        moveCardLocally(sessionId, fromStage, toStage);

        // Re-render board
        renderBoard();

        // Show success toast
        const toLabel = STAGES.find(s => s.key === toStage)?.label || toStage;
        showToast(`✓ ${candidateName} moved to ${toLabel}`, 'success');

    } catch (err) {
        showToast(`✗ Failed: ${err.message}`, 'error');
        // Refresh from server to reset state
        await refreshBoard();
    }

    pendingMove = null;
}

function moveCardLocally(sessionId, fromStage, toStage) {
    // Find and remove from source stage
    const fromList = pipelineData.stages[fromStage] || [];
    const cardIndex = fromList.findIndex(c => c.session_id === sessionId);

    if (cardIndex === -1) return;

    const [card] = fromList.splice(cardIndex, 1);
    card.stage = toStage;
    card.stage_updated_at = new Date().toISOString();

    // Add to target stage (at top)
    if (!pipelineData.stages[toStage]) {
        pipelineData.stages[toStage] = [];
    }
    pipelineData.stages[toStage].unshift(card);

    // Update counts
    pipelineData.counts[fromStage] = (pipelineData.counts[fromStage] || 1) - 1;
    pipelineData.counts[toStage] = (pipelineData.counts[toStage] || 0) + 1;
}

function closeModal() {
    const modal = document.getElementById('notes-modal');
    if (modal) modal.classList.remove('active');
    pendingMove = null;
}

function closeAllDropdowns() {
    document.querySelectorAll('.stage-dropdown.active').forEach(el => {
        el.classList.remove('active');
    });
    activeDropdown = null;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Toast Notifications
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function showToast(message, type = 'success') {
    const toast = document.getElementById('pipeline-toast');
    if (!toast) return;

    toast.textContent = message;
    toast.className = `pipeline-toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Data Loading
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function refreshBoard() {
    try {
        pipelineData = await fetchPipelineBoard();
        renderBoard();
    } catch (err) {
        console.error('Failed to load pipeline:', err);
        showToast(`Failed to load pipeline: ${err.message}`, 'error');
    }
}

function handleFilterChange() {
    // Re-fetch with filter (would need to adjust API call)
    refreshBoard();
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Utilities
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

// Close dropdowns when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.stage-dropdown') && !e.target.closest('.stage-move-btn')) {
        closeAllDropdowns();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
        closeAllDropdowns();
    }
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Initialization
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Initialize the Pipeline Page.
 * Call this from your app's router or page loader:
 *   initPipelinePage('pipeline-container')
 */
function initPipelinePage(containerId = 'pipeline-container') {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Pipeline: container #${containerId} not found`);
        return;
    }

    // Render initial structure
    renderPage();

    // Load data
    refreshBoard();

    // Auto-refresh every 30 seconds
    setInterval(refreshBoard, 30000);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ES Module Export — Compatible with main.js SPA router
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export async function renderPipelinePage(container) {
    container.innerHTML = '';
    renderNavbar(container);

    const layout = document.createElement('div');
    layout.style.display = 'flex';
    layout.style.height = 'calc(100vh - 60px)';

    layout.appendChild(renderSidebar('pipeline'));

    const main = document.createElement('div');
    main.className = 'app-main';
    main.id = 'pipeline-container';
    main.style.flex = '1';
    main.style.overflowY = 'auto';

    layout.appendChild(main);
    container.appendChild(layout);

    // Now init the pipeline inside the container
    renderPage();
    refreshBoard();
}
