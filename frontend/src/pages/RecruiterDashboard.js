import { renderNavbar } from '../components/Navbar.js';
import { renderSidebar } from '../components/Sidebar.js';
import { auth, analytics, proctor } from '../api/index.js';
import { apiJSON } from '../api/client.js';
import { navigate } from '../main.js';
import { Toast } from '../components/Toast.js';

/**
 * Recruiter Dashboard — Candidate Ranking Table
 * Features: Search, Sort, Filter, Pagination, Color-coded scores
 */

// ── State ──────────────────────────────────────────────────────────────────────
let state = {
  candidates: [],
  totalCount: 0,
  page: 1,
  pageSize: 20,
  totalPages: 1,
  search: '',
  sortBy: 'date',
  sortOrder: 'desc',
  status: '',
  dateRange: 'all',
  minScore: null,
  maxScore: null,
  skills: [],
  availableSkills: [],
  loading: false,
};

let debounceTimer = null;

// ── Main Render ────────────────────────────────────────────────────────────────
export async function renderRecruiterDashboard(container) {
  container.innerHTML = '';
  renderNavbar(container);

  const layout = document.createElement('div');
  layout.className = 'dashboard-shell';

  layout.appendChild(renderSidebar('recruiter'));

  const main = document.createElement('div');
  main.className = 'dashboard-main';

  main.innerHTML = `
    <div class="page-content recruiter-dashboard">
      <div class="page-header">
        <h1>Candidate Management</h1>
        <p>Search, filter, and rank interview candidates</p>
      </div>

      <!-- ═══ Filters Bar ═══ -->
      <div class="recruiter-filters" style="
        display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
        margin-top: 20px; padding: 16px; background: var(--bg-card);
        border: 1px solid var(--border-color); border-radius: 12px;
      ">
        <!-- Search -->
        <div style="flex: 1; min-width: 220px;">
          <input type="text" id="rc-search" placeholder="🔍 Search name or email..."
            style="
              width: 100%; padding: 10px 14px; border-radius: 8px;
              border: 1px solid var(--border-color); background: var(--bg-main);
              color: var(--text-primary); font-size: 0.9rem;
            " />
        </div>

        <!-- Status Filter -->
        <select id="rc-status" style="
          padding: 10px 14px; border-radius: 8px;
          border: 1px solid var(--border-color); background: var(--bg-main);
          color: var(--text-primary); font-size: 0.85rem; min-width: 140px;
        ">
          <option value="">All Statuses</option>
          <option value="completed">Completed</option>
          <option value="in_progress">In Progress</option>
          <option value="pending">Pending</option>
          <option value="questions_generated">Questions Ready</option>
          <option value="decision">All Decisions</option>
          <option value="strong_hire">↳ Strong Hire</option>
          <option value="hire">↳ Hire</option>
          <option value="maybe">↳ Maybe</option>
          <option value="no_hire">↳ No Hire</option>
        </select>

        <!-- Date Range Filter -->
        <select id="rc-date-range" style="
          padding: 10px 14px; border-radius: 8px;
          border: 1px solid var(--border-color); background: var(--bg-main);
          color: var(--text-primary); font-size: 0.85rem; min-width: 140px;
        ">
          <option value="all">All Time</option>
          <option value="today">Today</option>
          <option value="week">Last 7 Days</option>
          <option value="month">Last 30 Days</option>
        </select>

        <!-- Score Range -->
        <select id="rc-score-range" style="
          padding: 10px 14px; border-radius: 8px;
          border: 1px solid var(--border-color); background: var(--bg-main);
          color: var(--text-primary); font-size: 0.85rem; min-width: 140px;
        ">
          <option value="">All Scores</option>
          <option value="0-4">0 – 4 (Low)</option>
          <option value="4-6">4 – 6 (Below Avg)</option>
          <option value="6-8">6 – 8 (Good)</option>
          <option value="8-10">8 – 10 (Excellent)</option>
        </select>

        <!-- Skills Multi-Select -->
        <div class="rc-skills-wrapper" style="position: relative; min-width: 180px;">
          <button id="rc-skills-btn" style="
            padding: 10px 14px; border-radius: 8px;
            border: 1px solid var(--border-color); background: var(--bg-main);
            color: var(--text-primary); font-size: 0.85rem; cursor: pointer;
            width: 100%; text-align: left;
          ">🏷️ Skills <span id="rc-skills-count"></span></button>
          <div id="rc-skills-dropdown" style="
            display: none; position: absolute; top: 100%; left: 0; z-index: 100;
            margin-top: 4px; background: var(--bg-card); border: 1px solid var(--border-color);
            border-radius: 8px; max-height: 240px; overflow-y: auto; min-width: 220px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.4); padding: 8px;
          "></div>
        </div>

        <!-- Reset -->
        <button id="rc-reset-btn" style="
          padding: 10px 14px; border-radius: 8px; border: 1px solid var(--accent-gold);
          background: transparent; color: var(--accent-gold); font-size: 0.85rem;
          cursor: pointer; font-weight: 500;
        ">↻ Reset</button>
      </div>

      <!-- ═══ Candidate Table ═══ -->
      <div class="rc-table-wrapper" style="
        margin-top: 20px; background: var(--bg-card);
        border: 1px solid var(--border-color); border-radius: 12px;
        overflow: hidden;
      ">
        <div style="overflow-x: auto;">
          <table id="rc-table" style="width: 100%; border-collapse: collapse; text-align: left; min-width: 760px; table-layout: fixed;">
            <thead style="background: var(--bg-hover); border-bottom: 1px solid var(--border-color);">
              <tr>
                <th class="rc-th rc-sortable" data-sort="name" style="padding: 12px 14px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; cursor: pointer; user-select: none; width: 25%;">
                  Candidate <span class="sort-icon"></span>
                </th>
                <th class="rc-th rc-sortable" data-sort="score" style="padding: 12px 10px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; cursor: pointer; user-select: none; width: 15%; text-align: center;">
                  Top Score <span class="sort-icon"></span>
                </th>
                <th class="rc-th" style="padding: 12px 10px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; width: 15%; text-align: center;">
                  Total Interviews
                </th>
                <th class="rc-th" style="padding: 12px 10px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; width: 15%; text-align: center;">
                  Total Violations
                </th>
                <th class="rc-th rc-sortable" data-sort="date" style="padding: 12px 10px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; cursor: pointer; user-select: none; width: 20%; text-align: right;">
                  Latest Date <span class="sort-icon"></span>
                </th>
                <th class="rc-th" style="padding: 12px 14px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; width: 10%; text-align: right;">
                  Expand
                </th>
              </tr>
            </thead>
            <tbody id="rc-table-body" style="position:relative">
              <tr><td colspan="8" style="padding: 40px; text-align: center; color: var(--text-muted);">Loading candidates...</td></tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div id="rc-pagination" style="
          display: flex; align-items: center; justify-content: space-between;
          padding: 14px 16px; border-top: 1px solid var(--border-color);
        ">
          <span id="rc-page-info" style="color: var(--text-muted); font-size: 0.85rem;"></span>
          <div style="display: flex; gap: 8px; align-items: center;">
            <button id="rc-prev-btn" class="btn btn-sm btn-outline" style="
              padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border-color);
              background: transparent; color: var(--text-primary); cursor: pointer; font-size: 0.85rem;
            ">← Previous</button>
            <span id="rc-page-num" style="color: var(--accent-gold); font-weight: 600; font-size: 0.9rem;"></span>
            <button id="rc-next-btn" class="btn btn-sm btn-outline" style="
              padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border-color);
              background: transparent; color: var(--text-primary); cursor: pointer; font-size: 0.85rem;
            ">Next →</button>
          </div>
        </div>
      </div>

      <!-- ═══ User Management Section ═══ -->
      <h2 style="margin-top: 40px; margin-bottom: 16px; font-size: 1.2rem;">User Management</h2>
      <div class="table-container" style="background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border-color); overflow: hidden;">
        <table style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead style="background: var(--bg-hover); border-bottom: 1px solid var(--border-color);">
            <tr>
              <th style="padding: 14px 16px; color: var(--text-muted); font-weight: 500; font-size: 0.85rem;">Name</th>
              <th style="padding: 14px 16px; color: var(--text-muted); font-weight: 500; font-size: 0.85rem;">Email</th>
              <th style="padding: 14px 16px; color: var(--text-muted); font-weight: 500; font-size: 0.85rem;">Role</th>
              <th style="padding: 14px 16px; color: var(--text-muted); font-weight: 500; font-size: 0.85rem;">Status</th>
              <th style="padding: 14px 16px; color: var(--text-muted); font-weight: 500; font-size: 0.85rem;">Actions</th>
            </tr>
          </thead>
          <tbody id="user-table-body">
            <tr><td colspan="5" style="padding: 20px; text-align: center; color: var(--text-muted);">Loading users...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `;

  layout.appendChild(main);
  container.appendChild(layout);

  // ── Initialize ──
  _bindEvents(main);
  await _loadAvailableSkills();
  await _fetchCandidates(main);
  await _loadUsers(main);
}


// ── Event Bindings ─────────────────────────────────────────────────────────────
function _bindEvents(main) {
  // Search (debounced)
  const searchInput = main.querySelector('#rc-search');
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      state.search = searchInput.value.trim();
      state.page = 1;
      _fetchCandidates(main);
    }, 350);
  });

  // Status filter
  main.querySelector('#rc-status').addEventListener('change', (e) => {
    state.status = e.target.value;
    state.page = 1;
    _fetchCandidates(main);
  });

  // Date Range filter
  main.querySelector('#rc-date-range').addEventListener('change', (e) => {
    state.dateRange = e.target.value;
    state.page = 1;
    _fetchCandidates(main);
  });

  // Score range filter
  main.querySelector('#rc-score-range').addEventListener('change', (e) => {
    const val = e.target.value;
    if (val) {
      const [min, max] = val.split('-').map(Number);
      state.minScore = min;
      state.maxScore = max;
    } else {
      state.minScore = null;
      state.maxScore = null;
    }
    state.page = 1;
    _fetchCandidates(main);
  });

  // Skills dropdown toggle
  const skillsBtn = main.querySelector('#rc-skills-btn');
  const skillsDropdown = main.querySelector('#rc-skills-dropdown');
  skillsBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    skillsDropdown.style.display = skillsDropdown.style.display === 'none' ? 'block' : 'none';
  });
  document.addEventListener('click', () => {
    skillsDropdown.style.display = 'none';
  });
  skillsDropdown.addEventListener('click', (e) => e.stopPropagation());

  // Sort columns
  main.querySelectorAll('.rc-sortable').forEach(th => {
    th.addEventListener('click', () => {
      const field = th.dataset.sort;
      if (state.sortBy === field) {
        state.sortOrder = state.sortOrder === 'asc' ? 'desc' : 'asc';
      } else {
        state.sortBy = field;
        state.sortOrder = field === 'name' ? 'asc' : 'desc';
      }
      state.page = 1;
      _fetchCandidates(main);
    });
  });

  // Pagination
  main.querySelector('#rc-prev-btn').addEventListener('click', () => {
    if (state.page > 1) {
      state.page--;
      _fetchCandidates(main);
    }
  });
  main.querySelector('#rc-next-btn').addEventListener('click', () => {
    if (state.page < state.totalPages) {
      state.page++;
      _fetchCandidates(main);
    }
  });

  // Reset filters
  main.querySelector('#rc-reset-btn').addEventListener('click', () => {
    state.search = '';
    state.status = '';
    state.dateRange = 'all';
    state.minScore = null;
    state.maxScore = null;
    state.skills = [];
    state.sortBy = 'date';
    state.sortOrder = 'desc';
    state.page = 1;

    main.querySelector('#rc-search').value = '';
    main.querySelector('#rc-status').value = '';
    main.querySelector('#rc-date-range').value = 'all';
    main.querySelector('#rc-score-range').value = '';
    _renderSkillsDropdown(main);
    _fetchCandidates(main);
  });
}


// ── Fetch Candidates ───────────────────────────────────────────────────────────
async function _fetchCandidates(main) {
  state.loading = true;
  _renderLoading(main);

  try {
    const params = new URLSearchParams();
    params.set('page', state.page);
    params.set('page_size', state.pageSize);
    params.set('sort_by', state.sortBy);
    params.set('sort_order', state.sortOrder);

    if (state.search) params.set('search', state.search);
    if (state.status) params.set('status', state.status);
    if (state.dateRange && state.dateRange !== 'all') params.set('date_range', state.dateRange);
    if (state.minScore !== null) params.set('min_score', state.minScore);
    if (state.maxScore !== null) params.set('max_score', state.maxScore);
    if (state.skills.length > 0) params.set('skills', state.skills.join(','));

    const data = await apiJSON(`/recruiter/candidates?${params.toString()}`);

    state.candidates = data.candidates || [];
    state.totalCount = data.total_count || 0;
    state.page = data.page || 1;
    state.totalPages = data.total_pages || 1;

    _renderTable(main);
    _renderPagination(main);
    _updateSortIcons(main);
  } catch (err) {
    Toast.error(err.message, 'Load Candidates');
    _renderEmpty(main, 'Failed to load candidates');
  } finally {
    state.loading = false;
  }
}


// ── Load Available Skills ──────────────────────────────────────────────────────
async function _loadAvailableSkills() {
  try {
    const data = await apiJSON('/recruiter/candidates/skills');
    state.availableSkills = data.skills || [];
  } catch {
    state.availableSkills = [];
  }
}


// ── Render Table ───────────────────────────────────────────────────────────────
function _renderTable(main) {
  const tbody = main.querySelector('#rc-table-body');

  if (!state.candidates.length) {
    _renderEmpty(main, 'No candidates match your filters');
    return;
  }

  tbody.innerHTML = '';
  state.candidates.forEach((c, idx) => {
    // 1. Parent Row
    const tr = document.createElement('tr');
    tr.style.borderBottom = '1px solid var(--border-color)';
    tr.style.transition = 'background 0.15s';
    tr.style.cursor = 'pointer';
    tr.addEventListener('mouseenter', () => tr.style.background = 'var(--bg-hover)');
    tr.addEventListener('mouseleave', () => tr.style.background = 'transparent');

    const score = c.highest_score;
    const scoreColor = _getScoreColor(score);
    const scoreDisplay = score ? score.toFixed(1) : '—';

    const dateStr = c.latest_date
      ? new Date(c.latest_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
      : '—';
      
    tr.innerHTML = `
      <td style="padding: 12px 14px;">
        <div style="font-weight: 600; color: var(--text-primary); font-size: 0.9rem;">${_escapeHtml(c.candidate_name)}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 2px;">${c.email ? _escapeHtml(c.email) : '—'}</div>
      </td>
      <td style="padding: 12px 10px; text-align: center;">
        <span style="
          display: inline-block; padding: 4px 10px; border-radius: 6px;
          font-weight: 700; font-size: 0.85rem; color: ${scoreColor};
          background: ${scoreColor}15; border: 1px solid ${scoreColor}40;
        ">${scoreDisplay}</span>
      </td>
      <td style="padding: 12px 10px; text-align: center; color: var(--text-secondary); font-weight: 500;">
        ${c.total_sessions}
      </td>
      <td style="padding: 12px 10px; text-align: center;">
        <span style="
          display: inline-block; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.78rem;
          color: ${c.total_violations > 5 ? 'var(--accent-red)' : c.total_violations > 0 ? 'var(--accent-amber)' : 'var(--accent-emerald)'};
          background: ${c.total_violations > 5 ? 'rgba(239,68,68,0.1)' : c.total_violations > 0 ? 'rgba(245,184,0,0.1)' : 'rgba(16,185,129,0.1)'};
          border: 1px solid ${c.total_violations > 5 ? 'rgba(239,68,68,0.3)' : c.total_violations > 0 ? 'rgba(245,184,0,0.3)' : 'rgba(16,185,129,0.3)'};
        ">${c.total_violations}</span>
      </td>
      <td style="padding: 12px 10px; text-align: right; color: var(--text-muted); font-size: 0.8rem;">
        ${dateStr}
      </td>
      <td style="padding: 12px 14px; text-align: right;">
        <button class="btn btn-sm btn-outline" style="border: none; background: transparent; color: var(--text-muted); font-size: 1.2rem; cursor: pointer;">
          <span class="expand-icon">▼</span>
        </button>
      </td>
    `;

    // 2. Child Row (Accordion Content)
    const childTr = document.createElement('tr');
    childTr.style.display = 'none';
    childTr.style.background = 'var(--bg-main)';
    childTr.style.borderBottom = '1px solid var(--border-color)';
    
    let sessionsHtml = c.sessions.map(s => {
      const sScore = s.average_score;
      const sScoreColor = _getScoreColor(sScore);
      const sScoreDisplay = sScore !== null ? sScore.toFixed(1) : '—';
      const sDateStr = s.created_at ? new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—';
      const statusBadge = _getStatusBadge(s.status);
      const pipelineBadge = _getDecisionBadge(s.recommendation, s.pipeline_stage);
      
      const skillsBadges = (s.skills_detected || []).slice(0, 3).map(sk =>
        `<span style="display: inline-block; padding: 2px 6px; border-radius: 4px; background: rgba(245, 184, 0, 0.1); border: 1px solid rgba(245, 184, 0, 0.3); color: var(--accent-gold); font-size: 0.7rem; margin: 2px 3px 2px 0;">${_escapeHtml(sk)}</span>`
      ).join('');

      return `
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
          <td style="padding: 8px 10px; font-size: 0.8rem; color: var(--text-secondary);">${sDateStr}</td>
          <td style="padding: 8px 10px;">${statusBadge}</td>
          <td style="padding: 8px 10px;">
            <span style="font-weight: 700; color: ${sScoreColor};">${sScoreDisplay}</span>
          </td>
          <td style="padding: 8px 10px; max-width: 150px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">${skillsBadges}</td>
          <td style="padding: 8px 10px; text-align: center;">
            <span style="color: ${s.violations_count > 0 ? 'var(--accent-red)' : 'var(--text-muted)'}; font-size: 0.75rem;">${s.violations_count || 0}</span>
          </td>
          <td style="padding: 8px 10px;">
            <div style="display: flex; align-items: center; gap: 6px;">
              ${pipelineBadge}
              <select class="rc-decision-select" data-sid="${s.session_id}" style="
                padding:2px 4px; border-radius:4px;
                border:1px solid var(--border-color); background:var(--bg-card);
                color:var(--text-primary); font-size:0.7rem; cursor:pointer; max-width: 90px;
              ">
                <option value="" ${!s.recommendation ? 'selected' : ''}>Change</option>
                <option value="Strong Hire" ${s.recommendation === 'Strong Hire' ? 'selected' : ''}>Strong Hire</option>
                <option value="Hire" ${s.recommendation === 'Hire' ? 'selected' : ''}>Hire</option>
                <option value="Maybe" ${(s.recommendation === 'Maybe' || s.recommendation === 'Maybe — needs improvement') ? 'selected' : ''}>Maybe</option>
                <option value="No Hire" ${s.recommendation === 'No Hire' ? 'selected' : ''}>No Hire</option>
              </select>
            </div>
          </td>
          <td style="padding: 8px 10px; text-align: right;">
            <button class="rc-view-btn" data-sid="${s.session_id}" style="
              padding: 4px 8px; border-radius: 4px; border: 1px solid var(--accent-gold);
              background: transparent; color: var(--accent-gold); font-size: 0.7rem;
              cursor: pointer; font-weight: 500;
            ">View Report</button>
          </td>
        </tr>
      `;
    }).join('');

    childTr.innerHTML = `
      <td colspan="6" style="padding: 0;">
        <div style="padding: 12px 14px 12px 30px; border-left: 2px solid var(--accent-gold);">
          <h4 style="margin-bottom: 8px; font-size: 0.85rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px;">Interview Sessions (${c.total_sessions})</h4>
          <table style="width: 100%; border-collapse: collapse; text-align: left;">
            <thead>
              <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;">
                <th style="padding: 6px 10px; font-weight: 600;">Date</th>
                <th style="padding: 6px 10px; font-weight: 600;">Status</th>
                <th style="padding: 6px 10px; font-weight: 600;">Score</th>
                <th style="padding: 6px 10px; font-weight: 600;">Skills</th>
                <th style="padding: 6px 10px; font-weight: 600; text-align: center;">Violations</th>
                <th style="padding: 6px 10px; font-weight: 600;">Decision</th>
                <th style="padding: 6px 10px; font-weight: 600; text-align: right;">Action</th>
              </tr>
            </thead>
            <tbody>
              ${sessionsHtml}
            </tbody>
          </table>
        </div>
      </td>
    `;

    // Toggle logic
    tr.addEventListener('click', () => {
      const isExpanded = childTr.style.display !== 'none';
      childTr.style.display = isExpanded ? 'none' : 'table-row';
      tr.querySelector('.expand-icon').textContent = isExpanded ? '▼' : '▲';
      tr.style.background = isExpanded ? 'transparent' : 'var(--bg-hover)';
    });

    tbody.appendChild(tr);
    tbody.appendChild(childTr);
  });

  // Bind view buttons
  tbody.querySelectorAll('.rc-view-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      navigate(`/interview/summary/${btn.dataset.sid}`);
    });
  });

  // Bind decision change dropdowns
  tbody.querySelectorAll('.rc-decision-select').forEach(sel => {
    sel.addEventListener('click', (e) => e.stopPropagation());
    sel.addEventListener('change', async (e) => {
      e.stopPropagation();
      const sid = sel.dataset.sid;
      const newDecision = sel.value;
      if (!newDecision) return;

      try {
        await apiJSON(`/recruiter/candidates/${sid}/decision`, {
          method: 'PUT',
          body: JSON.stringify({ recommendation: newDecision }),
        });

        Toast.success(`Updated to "${newDecision}"`, '✓');
        
        // Refresh to get updated pipeline badges
        _fetchCandidates(main);
        
      } catch (err) {
        Toast.error(err.message || 'Failed to update decision', 'Error');
        sel.value = '';
      }
    });
  });
}

// ── Render Helpers ─────────────────────────────────────────────────────────────

function _renderLoading(main) {
  const tbody = main.querySelector('#rc-table-body');
  tbody.innerHTML = `
    <tr><td colspan="8" style="padding: 40px; text-align: center; color: var(--text-muted);">
      <div style="display: inline-block; width: 20px; height: 20px; border: 2px solid var(--accent-gold); border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
      <div style="margin-top: 8px;">Loading candidates...</div>
    </td></tr>
  `;
}

function _renderEmpty(main, message) {
  const tbody = main.querySelector('#rc-table-body');
  tbody.innerHTML = `
    <tr><td colspan="8" style="padding: 50px; text-align: center; color: var(--text-muted);">
      <div style="font-size: 2rem; margin-bottom: 8px;">📋</div>
      <div>${message}</div>
    </td></tr>
  `;
}

function _renderPagination(main) {
  const info = main.querySelector('#rc-page-info');
  const pageNum = main.querySelector('#rc-page-num');
  const prevBtn = main.querySelector('#rc-prev-btn');
  const nextBtn = main.querySelector('#rc-next-btn');

  const start = ((state.page - 1) * state.pageSize) + 1;
  const end = Math.min(state.page * state.pageSize, state.totalCount);

  info.textContent = state.totalCount > 0
    ? `Showing ${start}–${end} of ${state.totalCount} candidates`
    : 'No results';

  pageNum.textContent = `Page ${state.page} / ${state.totalPages}`;

  prevBtn.disabled = state.page <= 1;
  nextBtn.disabled = state.page >= state.totalPages;

  prevBtn.style.opacity = state.page <= 1 ? '0.4' : '1';
  nextBtn.style.opacity = state.page >= state.totalPages ? '0.4' : '1';
}

function _updateSortIcons(main) {
  main.querySelectorAll('.rc-sortable .sort-icon').forEach(icon => {
    icon.textContent = '';
  });

  const activeTh = main.querySelector(`.rc-sortable[data-sort="${state.sortBy}"]`);
  if (activeTh) {
    const icon = activeTh.querySelector('.sort-icon');
    icon.textContent = state.sortOrder === 'asc' ? ' ↑' : ' ↓';
    icon.style.color = 'var(--accent-gold)';
  }
}

function _renderSkillsDropdown(main) {
  const dropdown = main.querySelector('#rc-skills-dropdown');
  const countSpan = main.querySelector('#rc-skills-count');

  if (!state.availableSkills.length) {
    dropdown.innerHTML = '<div style="padding: 12px; color: var(--text-muted); font-size: 0.85rem;">No skills found</div>';
    countSpan.textContent = '';
    return;
  }

  dropdown.innerHTML = state.availableSkills.map(skill => {
    const checked = state.skills.includes(skill) ? 'checked' : '';
    return `
      <label style="
        display: flex; align-items: center; gap: 8px; padding: 6px 8px;
        border-radius: 4px; cursor: pointer; font-size: 0.85rem; color: var(--text-primary);
      " class="rc-skill-option">
        <input type="checkbox" value="${_escapeHtml(skill)}" ${checked}
          style="accent-color: var(--accent-gold);" />
        ${_escapeHtml(skill)}
      </label>
    `;
  }).join('');

  // Bind checkboxes
  dropdown.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', () => {
      if (cb.checked) {
        if (!state.skills.includes(cb.value)) state.skills.push(cb.value);
      } else {
        state.skills = state.skills.filter(s => s !== cb.value);
      }
      countSpan.textContent = state.skills.length > 0 ? `(${state.skills.length})` : '';
      state.page = 1;
      _fetchCandidates(main);
    });
  });

  countSpan.textContent = state.skills.length > 0 ? `(${state.skills.length})` : '';
}


// ── Score Color Logic ──────────────────────────────────────────────────────────
function _getScoreColor(score) {
  if (score === null || score === undefined) return 'var(--text-muted)';
  if (score < 5) return '#ef4444';        // Red
  if (score < 6.5) return '#f59e0b';      // Amber
  if (score < 8) return '#f5b800';        // Gold (accent)
  return '#10b981';                        // Green
}


// ── Status Badge ───────────────────────────────────────────────────────────────
function _getStatusBadge(status) {
  const config = {
    completed: { label: 'Completed', bg: 'rgba(16, 185, 129, 0.1)', color: '#10b981', border: 'rgba(16, 185, 129, 0.3)' },
    in_progress: { label: 'In Progress', bg: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', border: 'rgba(59, 130, 246, 0.3)' },
    created: { label: 'Pending', bg: 'rgba(107, 114, 128, 0.1)', color: '#6b7280', border: 'rgba(107, 114, 128, 0.3)' },
    questions_generated: { label: 'Ready', bg: 'rgba(245, 184, 0, 0.1)', color: '#f5b800', border: 'rgba(245, 184, 0, 0.3)' },
  };
  const c = config[status] || config.created;
  return `<span style="
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 500;
    background: ${c.bg}; color: ${c.color}; border: 1px solid ${c.border};
  ">${c.label}</span>`;
}


// ── Pipeline Stage Badge ───────────────────────────────────────────────────────
function _getDecisionBadge(recommendation, pipelineStage) {
  // Show actual recommendation with distinct color per decision type
  if (recommendation) {
    const decisionConfig = {
      'Strong Hire': { icon: '🌟', color: '#10b981', bg: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.4)' },
      'Hire':        { icon: '✅', color: '#34d399', bg: 'rgba(52,211,153,0.10)', border: 'rgba(52,211,153,0.35)' },
      'Maybe':       { icon: '🤔', color: '#f59e0b', bg: 'rgba(245,158,11,0.10)', border: 'rgba(245,158,11,0.35)' },
      'Maybe — needs improvement': { icon: '🤔', color: '#f59e0b', bg: 'rgba(245,158,11,0.10)', border: 'rgba(245,158,11,0.35)' },
      'No Hire':     { icon: '❌', color: '#ef4444', bg: 'rgba(239,68,68,0.10)', border: 'rgba(239,68,68,0.35)' },
    };
    const d = decisionConfig[recommendation] || { icon: '⚖️', color: '#8b5cf6', bg: 'rgba(139,92,246,0.10)', border: 'rgba(139,92,246,0.35)' };
    return `<span style="display:inline-block;padding:3px 8px;border-radius:6px;font-size:0.75rem;font-weight:600;color:${d.color};background:${d.bg};border:1px solid ${d.border};white-space:nowrap;">${d.icon} ${recommendation}</span>`;
  }

  // Fallback to pipeline stage if no decision yet
  const stageConfig = {
    screening:  { label: '📋 Screening', color: '#6b7280' },
    interview:  { label: '🎤 Interview', color: '#3b82f6' },
    evaluation: { label: '📊 Evaluation', color: '#f59e0b' },
    decision:   { label: '⚖️ Pending', color: '#8b5cf6' },
    hired:      { label: '✅ Hired', color: '#10b981' },
    rejected:   { label: '❌ Rejected', color: '#ef4444' },
  };
  const c = stageConfig[pipelineStage] || stageConfig.screening;
  return `<span style="font-size:0.78rem;color:${c.color};font-weight:500;white-space:nowrap;">${c.label}</span>`;
}


// ── Load Users (existing functionality preserved) ──────────────────────────────
async function _loadUsers(main) {
  try {
    const usersRes = await auth.listUsers();
    const tbody = main.querySelector('#user-table-body');
    const users = usersRes.users || [];

    if (users.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="padding: 20px; text-align: center; color: var(--text-muted);">No users found</td></tr>';
    } else {
      tbody.innerHTML = '';
      users.forEach(u => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid var(--border-color)';
        const isActive = u.is_active;
        tr.innerHTML = `
          <td style="padding: 14px 16px; font-weight: 500;">${_escapeHtml(u.name)}</td>
          <td style="padding: 14px 16px; color: var(--text-muted);">${_escapeHtml(u.email)}</td>
          <td style="padding: 14px 16px;"><span class="badge badge-gray" style="
            padding: 3px 10px; border-radius: 20px; font-size: 0.75rem;
            background: rgba(107, 114, 128, 0.1); color: #9ca3af; border: 1px solid rgba(107, 114, 128, 0.3);
          ">${u.role}</span></td>
          <td style="padding: 14px 16px;">
            <span style="
              display: inline-block; padding: 3px 10px; border-radius: 20px;
              font-size: 0.75rem; font-weight: 500;
              background: ${isActive ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)'};
              color: ${isActive ? '#10b981' : '#ef4444'};
              border: 1px solid ${isActive ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'};
            ">${isActive ? 'Active' : 'Inactive'}</span>
          </td>
          <td style="padding: 14px 16px;">
            ${isActive && u.role === 'candidate' ? `<button class="deactivate-btn" data-id="${u.id}" style="
              padding: 5px 10px; border-radius: 6px; border: 1px solid #ef4444;
              background: transparent; color: #ef4444; font-size: 0.78rem;
              cursor: pointer;
            ">Deactivate</button>` : ''}
          </td>
        `;
        tbody.appendChild(tr);
      });

      // Deactivate logic
      tbody.querySelectorAll('.deactivate-btn').forEach(btn => {
        btn.onclick = async () => {
          if (!confirm('Are you sure you want to deactivate this user?')) return;
          try {
            await auth.deactivateUser(btn.dataset.id);
            Toast.success('User deactivated successfully');
            btn.parentElement.previousElementSibling.querySelector('span').style.background = 'rgba(239, 68, 68, 0.1)';
            btn.parentElement.previousElementSibling.querySelector('span').style.color = '#ef4444';
            btn.parentElement.previousElementSibling.querySelector('span').textContent = 'Inactive';
            btn.remove();
          } catch (err) {
            Toast.error(err.message, 'Deactivate');
          }
        };
      });
    }
  } catch (err) {
    Toast.error(err.message, 'Load Users');
  }

  // After loading skills, render skills dropdown
  const main2 = main; // closure
  _renderSkillsDropdown(main2);
}


// ── Utilities ──────────────────────────────────────────────────────────────────
function _escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
