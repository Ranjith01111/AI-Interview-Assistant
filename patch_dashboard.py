import re

def main():
    path = r"frontend\src\pages\RecruiterDashboard.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. State
    content = content.replace("status: '',\n  minScore: null,", "status: '',\n  dateRange: 'all',\n  minScore: null,")

    # 2. Filter HTML
    filter_html = """          <option value="maybe">↳ Maybe</option>
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
        </select>"""
    content = content.replace("""          <option value="maybe">↳ Maybe</option>
          <option value="no_hire">↳ No Hire</option>
        </select>""", filter_html)

    # 3. Filter bind
    bind_js = """  // Status filter
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
  });"""
    content = content.replace("""  // Status filter
  main.querySelector('#rc-status').addEventListener('change', (e) => {
    state.status = e.target.value;
    state.page = 1;
    _fetchCandidates(main);
  });""", bind_js)

    # 4. Reset bind
    content = content.replace("state.status = '';\n    state.minScore = null;", "state.status = '';\n    state.dateRange = 'all';\n    state.minScore = null;")
    content = content.replace("main.querySelector('#rc-status').value = '';\n    main.querySelector('#rc-score-range').value = '';", "main.querySelector('#rc-status').value = '';\n    main.querySelector('#rc-date-range').value = 'all';\n    main.querySelector('#rc-score-range').value = '';")

    # 5. Fetch params
    content = content.replace("if (state.status) params.set('status', state.status);", "if (state.status) params.set('status', state.status);\n    if (state.dateRange && state.dateRange !== 'all') params.set('date_range', state.dateRange);")

    # 6. Table Headers
    old_headers = """                <th class="rc-th rc-sortable" data-sort="name" style="padding: 12px 14px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; cursor: pointer; user-select: none; width: 22%;">
                  Name <span class="sort-icon"></span>
                </th>
                <th class="rc-th rc-sortable" data-sort="score" style="padding: 12px 10px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; cursor: pointer; user-select: none; width: 8%; text-align: center;">
                  Score <span class="sort-icon"></span>
                </th>
                <th class="rc-th" style="padding: 12px 10px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; width: 20%;">
                  Skills
                </th>
                <th class="rc-th" style="padding: 12px 10px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; width: 10%; text-align: center;">
                  Status
                </th>
                <th class="rc-th" style="padding: 12px 10px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; width: 20%;">
                  Decision
                </th>
                <th class="rc-th" style="padding: 12px 10px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; width: 8%; text-align: center;">
                  Violations
                </th>
                <th class="rc-th rc-sortable" data-sort="date" style="padding: 12px 10px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; cursor: pointer; user-select: none; width: 10%;">
                  Date <span class="sort-icon"></span>
                </th>
                <th class="rc-th" style="padding: 12px 10px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; width: 6%; text-align: center;">
                  Actions
                </th>"""
                
    new_headers = """                <th class="rc-th rc-sortable" data-sort="name" style="padding: 12px 14px; color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; cursor: pointer; user-select: none; width: 25%;">
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
                </th>"""
    
    content = content.replace(old_headers, new_headers)

    # 7. Render Table
    old_render_table = content[content.find("function _renderTable(main) {"):content.find("// ── Render Helpers")]
    
    new_render_table = """function _renderTable(main) {
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

"""
    content = content.replace(old_render_table, new_render_table)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
