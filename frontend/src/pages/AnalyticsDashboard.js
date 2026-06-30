import { renderNavbar } from '../components/Navbar.js';
import { renderSidebar } from '../components/Sidebar.js';
import { analytics } from '../api/index.js';
import { Toast } from '../components/Toast.js';

/**
 * Analytics Dashboard — Full SVG charting suite
 * Charts: Performance Trend (line), Skills (h-bar), Strengths/Weaknesses,
 *         Proctor Violations (donut), Score Distribution (histogram)
 * 
 * CANDIDATE SELECTOR: Switch between "All Candidates" (overall) and
 * individual candidate analytics view.
 */

// ——— SVG Chart Generators ———————————————————————————————————

function svgLineTrend(data, width = 560, height = 220) {
  if (!data || !data.length) return '<p class="ana-empty">No trend data available</p>';

  const pad = { top: 20, right: 20, bottom: 40, left: 45 };
  const w = width - pad.left - pad.right;
  const h = height - pad.top - pad.bottom;

  const scores = data.map(d => d.score ?? d.average_score ?? 0);
  const maxY = Math.max(10, ...scores);
  const minY = 0;

  const points = scores.map((s, i) => ({
    x: pad.left + (i / Math.max(1, scores.length - 1)) * w,
    y: pad.top + h - ((s - minY) / (maxY - minY)) * h
  }));

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
  const areaD = pathD + ` L${points[points.length - 1].x.toFixed(1)},${pad.top + h} L${points[0].x.toFixed(1)},${pad.top + h} Z`;

  // Y-axis labels
  const yTicks = 5;
  let yLabels = '';
  for (let i = 0; i <= yTicks; i++) {
    const val = minY + ((maxY - minY) * i) / yTicks;
    const y = pad.top + h - (i / yTicks) * h;
    yLabels += `<text x="${pad.left - 10}" y="${y + 4}" class="ana-svg-label" text-anchor="end">${val.toFixed(0)}</text>`;
    yLabels += `<line x1="${pad.left}" y1="${y}" x2="${pad.left + w}" y2="${y}" stroke="var(--border)" stroke-dasharray="3,3" />`;
  }

  // X-axis labels (show max 8)
  let xLabels = '';
  const step = Math.max(1, Math.floor(data.length / 8));
  data.forEach((d, i) => {
    if (i % step === 0 || i === data.length - 1) {
      const label = d.date ? d.date.slice(5) : `#${i + 1}`;
      xLabels += `<text x="${points[i].x}" y="${pad.top + h + 24}" class="ana-svg-label" text-anchor="middle">${label}</text>`;
    }
  });

  return `
    <svg viewBox="0 0 ${width} ${height}" class="ana-chart-svg" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="var(--accent-gold)" stop-opacity="0.35"/>
          <stop offset="100%" stop-color="var(--accent-gold)" stop-opacity="0.02"/>
        </linearGradient>
      </defs>
      ${yLabels}
      ${xLabels}
      <path d="${areaD}" fill="url(#trendGrad)" class="ana-area-path"/>
      <path d="${pathD}" fill="none" stroke="var(--accent-gold)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="ana-line-path"/>
      ${points.map((p, i) => `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="var(--bg-card)" stroke="var(--accent-gold)" stroke-width="2" class="ana-dot"><title>${scores[i].toFixed(1)}</title></circle>`).join('')}
    </svg>
  `;
}

function svgHorizontalBars(items, { maxVal = null, barColor = 'var(--accent-gold)', height: itemH = 36 } = {}) {
  if (!items || !items.length) return '<p class="ana-empty">No data available</p>';

  const max = maxVal || Math.max(...items.map(d => d.value));

  const rows = items.map((d, i) => {
    const pct = max > 0 ? Math.round((d.value / max) * 100) : 0;
    return `
      <div style="margin-bottom:10px;">
        <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:3px;">
          <span style="font-size:0.8rem;color:var(--text-secondary);line-height:1.3;">${d.label}</span>
          <span style="font-size:0.75rem;font-weight:700;color:var(--text-primary);margin-left:8px;white-space:nowrap;">${d.value}</span>
        </div>
        <div style="width:100%;height:10px;background:rgba(255,255,255,0.06);border-radius:5px;overflow:hidden;">
          <div style="width:${pct}%;height:100%;background:${barColor};border-radius:5px;transition:width 0.6s ease;"></div>
        </div>
      </div>
    `;
  }).join('');

  return `<div class="ana-bars-container">${rows}</div>`;
}

function svgDonutChart(segments, size = 200) {
  if (!segments || !segments.length) return '<p class="ana-empty">No violation data</p>';

  const total = segments.reduce((s, d) => s + d.value, 0);
  if (total === 0) return '<p class="ana-empty">No violations recorded 🎉</p>';

  const cx = size / 2, cy = size / 2, r = 70, strokeW = 24;
  const colors = ['#ef4444', '#f59e0b', '#06b6d4', '#8b5cf6', '#10b981', '#ec4899'];
  const circumference = 2 * Math.PI * r;

  let offset = 0;
  const arcs = segments.map((d, i) => {
    const pct = d.value / total;
    const dash = pct * circumference;
    const gap = circumference - dash;
    const arc = `
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none"
        stroke="${colors[i % colors.length]}" stroke-width="${strokeW}"
        stroke-dasharray="${dash.toFixed(2)} ${gap.toFixed(2)}"
        stroke-dashoffset="${(-offset).toFixed(2)}"
        stroke-linecap="round"
        class="ana-donut-arc" style="animation-delay:${i * 0.1}s"/>
    `;
    offset += dash;
    return arc;
  }).join('');

  const legend = segments.map((d, i) => `
    <div class="ana-legend-item">
      <span class="ana-legend-dot" style="background:${colors[i % colors.length]}"></span>
      <span class="ana-legend-label">${d.label}</span>
      <span class="ana-legend-val">${d.value}</span>
    </div>
  `).join('');

  return `
    <div class="ana-donut-wrap">
      <svg viewBox="0 0 ${size} ${size}" class="ana-donut-svg">
        ${arcs}
        <text x="${cx}" y="${cy - 6}" text-anchor="middle" fill="var(--text-primary)" font-size="22" font-weight="700">${total}</text>
        <text x="${cx}" y="${cy + 14}" text-anchor="middle" fill="var(--text-muted)" font-size="11">total</text>
      </svg>
      <div class="ana-legend">${legend}</div>
    </div>
  `;
}

function svgHistogram(scores, width = 560, height = 200) {
  const buckets = [
    { label: '0–2', min: 0, max: 2, count: 0 },
    { label: '2–4', min: 2, max: 4, count: 0 },
    { label: '4–6', min: 4, max: 6, count: 0 },
    { label: '6–8', min: 6, max: 8, count: 0 },
    { label: '8–10', min: 8, max: 10, count: 0 },
  ];

  (scores || []).forEach(s => {
    const val = typeof s === 'number' ? s : (s.score ?? s.average_score ?? 0);
    for (const b of buckets) {
      if (val >= b.min && (val < b.max || (b.max === 10 && val <= 10))) { b.count++; break; }
    }
  });

  const maxCount = Math.max(1, ...buckets.map(b => b.count));
  const pad = { top: 15, right: 20, bottom: 35, left: 40 };
  const chartW = width - pad.left - pad.right;
  const chartH = height - pad.top - pad.bottom;
  const barGap = 12;
  const barW = (chartW - barGap * (buckets.length - 1)) / buckets.length;

  const bars = buckets.map((b, i) => {
    const barH = (b.count / maxCount) * chartH;
    const x = pad.left + i * (barW + barGap);
    const y = pad.top + chartH - barH;
    const color = b.min >= 6 ? 'var(--accent-emerald)' : b.min >= 4 ? 'var(--accent-gold)' : 'var(--accent-red)';
    return `
      <rect x="${x}" y="${y}" width="${barW}" height="${barH}" rx="4" fill="${color}" opacity="0.85" class="ana-hist-bar">
        <animate attributeName="height" from="0" to="${barH}" dur="0.5s" fill="freeze"/>
        <animate attributeName="y" from="${pad.top + chartH}" to="${y}" dur="0.5s" fill="freeze"/>
      </rect>
      <text x="${x + barW / 2}" y="${pad.top + chartH + 20}" text-anchor="middle" class="ana-svg-label">${b.label}</text>
      <text x="${x + barW / 2}" y="${y - 6}" text-anchor="middle" class="ana-svg-label" fill="var(--text-secondary)" font-size="11">${b.count}</text>
    `;
  }).join('');

  // Y-axis
  let yAxis = '';
  for (let i = 0; i <= 4; i++) {
    const val = Math.round((maxCount * i) / 4);
    const y = pad.top + chartH - (i / 4) * chartH;
    yAxis += `<text x="${pad.left - 8}" y="${y + 4}" text-anchor="end" class="ana-svg-label">${val}</text>`;
    yAxis += `<line x1="${pad.left}" y1="${y}" x2="${pad.left + chartW}" y2="${y}" stroke="var(--border)" stroke-dasharray="3,3"/>`;
  }

  return `
    <svg viewBox="0 0 ${width} ${height}" class="ana-chart-svg" preserveAspectRatio="xMidYMid meet">
      ${yAxis}
      ${bars}
    </svg>
  `;
}

// ——— Vertical Bar Chart (for per-question scores) ———————————————
function svgVerticalBars(items, width = 560, height = 240) {
  if (!items || !items.length) return '<p class="ana-empty">No score data available</p>';

  const pad = { top: 20, right: 20, bottom: 50, left: 45 };
  const chartW = width - pad.left - pad.right;
  const chartH = height - pad.top - pad.bottom;
  const maxVal = 10; // scores are out of 10
  const barGap = 6;
  const barW = Math.min(40, (chartW - barGap * (items.length - 1)) / items.length);

  const bars = items.map((d, i) => {
    const barH = (d.value / maxVal) * chartH;
    const x = pad.left + i * (barW + barGap);
    const y = pad.top + chartH - barH;
    const color = d.value >= 7 ? 'var(--accent-emerald)' : d.value >= 5 ? 'var(--accent-gold)' : 'var(--accent-red)';
    return `
      <rect x="${x}" y="${y}" width="${barW}" height="${barH}" rx="3" fill="${color}" opacity="0.85">
        <animate attributeName="height" from="0" to="${barH}" dur="0.5s" fill="freeze"/>
        <animate attributeName="y" from="${pad.top + chartH}" to="${y}" dur="0.5s" fill="freeze"/>
        <title>Q${d.label}: ${d.value}/10</title>
      </rect>
      <text x="${x + barW / 2}" y="${pad.top + chartH + 18}" text-anchor="middle" class="ana-svg-label" font-size="10">Q${d.label}</text>
      <text x="${x + barW / 2}" y="${y - 5}" text-anchor="middle" class="ana-svg-label" fill="var(--text-secondary)" font-size="10">${d.value}</text>
    `;
  }).join('');

  // Y-axis
  let yAxis = '';
  for (let i = 0; i <= 5; i++) {
    const val = (maxVal * i) / 5;
    const y = pad.top + chartH - (i / 5) * chartH;
    yAxis += `<text x="${pad.left - 8}" y="${y + 4}" text-anchor="end" class="ana-svg-label">${val.toFixed(0)}</text>`;
    yAxis += `<line x1="${pad.left}" y1="${y}" x2="${pad.left + chartW}" y2="${y}" stroke="var(--border)" stroke-dasharray="3,3"/>`;
  }

  return `
    <svg viewBox="0 0 ${width} ${height}" class="ana-chart-svg" preserveAspectRatio="xMidYMid meet">
      ${yAxis}
      ${bars}
    </svg>
  `;
}

// ——— Skeleton Loaders ———————————————————————————————————————

function renderSkeletons() {
  return `
    <div class="ana-section">
      <div class="ana-kpi-row">
        ${Array(5).fill('<div class="ana-kpi skeleton"></div>').join('')}
      </div>
    </div>
    <div class="ana-grid">
      <div class="ana-card ana-card--wide skeleton" style="height:280px"></div>
      <div class="ana-card skeleton" style="height:280px"></div>
      <div class="ana-card skeleton" style="height:320px"></div>
      <div class="ana-card skeleton" style="height:260px"></div>
      <div class="ana-card skeleton" style="height:260px"></div>
    </div>
  `;
}

// ——— Main Render ————————————————————————————————————————————

export async function renderAnalyticsDashboard(container) {
  container.innerHTML = '';
  renderNavbar(container);

  const layout = document.createElement('div');
  layout.className = 'dashboard-shell';

  layout.appendChild(renderSidebar('analytics'));

  const main = document.createElement('div');
  main.className = 'dashboard-main';

  main.innerHTML = `
    <div class="page-content ana-page">
      <div class="ana-header">
        <h1 class="ana-title">Platform Analytics</h1>
        <p class="ana-subtitle">Insights into interview performance and proctoring integrity</p>
      </div>

      <!-- ══ Candidate Selector ══ -->
      <div id="ana-candidate-selector" style="
        margin-top: 16px; margin-bottom: 8px; padding: 14px 18px;
        background: var(--bg-card); border: 1px solid var(--border-color);
        border-radius: 12px; display: flex; align-items: center; gap: 14px;
      ">
        <label for="ana-candidate-select" style="
          font-size: 0.9rem; font-weight: 600; color: var(--text-primary); white-space: nowrap;
        ">📊 View Analytics For:</label>
        <select id="ana-candidate-select" style="
          flex: 1; max-width: 400px; padding: 10px 14px; border-radius: 8px;
          border: 1px solid var(--border-color); background: var(--bg-main);
          color: var(--text-primary); font-size: 0.9rem; cursor: pointer;
        ">
          <option value="">All Candidates (Overall)</option>
        </select>
        <span id="ana-candidate-status" style="font-size: 0.8rem; color: var(--text-muted);"></span>
      </div>

      <div id="ana-content">${renderSkeletons()}</div>
    </div>
  `;

  layout.appendChild(main);
  container.appendChild(layout);

  // Store fetched data for re-use
  let cachedOverallData = null;
  let cachedHistory = null;

  // Fetch all data in parallel
  try {
    const [overview, trend, skills, sw, violations, history] = await Promise.all([
      analytics.overview(),
      analytics.trend(),
      analytics.skills(),
      analytics.strengths(),
      analytics.violations(),
      analytics.history(),
    ]);

    cachedOverallData = { overview, trend, skills, sw, violations, history };
    cachedHistory = history;

    // Populate candidate selector from history
    _populateCandidateSelector(main, history);

    // Render overall dashboard
    _renderOverallDashboard(main, cachedOverallData);

  } catch (err) {
    console.error('[Analytics]', err);
    Toast.error(err.message || 'Failed to load analytics', 'Analytics');
    const content = main.querySelector('#ana-content');
    content.innerHTML = `
      <div class="ana-error">
        <span class="ana-error-icon">⚠️</span>
        <p>Unable to load analytics data</p>
        <small>${err.message || 'Unknown error'}</small>
      </div>
    `;
  }

  // Bind candidate selector change event
  const selector = main.querySelector('#ana-candidate-select');
  selector.addEventListener('change', async () => {
    const sessionId = selector.value;
    const statusEl = main.querySelector('#ana-candidate-status');

    if (!sessionId) {
      // Show overall dashboard
      statusEl.textContent = '';
      if (cachedOverallData) {
        _renderOverallDashboard(main, cachedOverallData);
      }
    } else {
      // Show individual candidate analytics
      statusEl.textContent = 'Loading...';
      const content = main.querySelector('#ana-content');
      content.innerHTML = renderSkeletons();

      try {
        const detail = await analytics.candidateDetail(sessionId);
        statusEl.textContent = '';
        _renderCandidateDashboard(main, detail);
      } catch (err) {
        statusEl.textContent = '';
        Toast.error(err.message || 'Failed to load candidate data', 'Analytics');
        content.innerHTML = `
          <div class="ana-error">
            <span class="ana-error-icon">⚠️</span>
            <p>Unable to load candidate analytics</p>
            <small>${err.message || 'Unknown error'}</small>
          </div>
        `;
      }
    }
  });
}


// ——— Populate Candidate Selector ————————————————————————————————
function _populateCandidateSelector(main, history) {
  const selector = main.querySelector('#ana-candidate-select');
  const sessions = history?.sessions || [];

  sessions.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s.session_id;
    const score = s.average_score !== null && s.average_score !== undefined
      ? ` (Score: ${s.average_score.toFixed(1)})`
      : '';
    const date = s.created_at
      ? ` — ${new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`
      : '';
    opt.textContent = `${s.candidate_name || 'Unknown'}${score}${date}`;
    selector.appendChild(opt);
  });
}


// ——— Render Overall Dashboard (unchanged behavior) ——————————————
function _renderOverallDashboard(main, data) {
  const { overview, trend, skills, sw, violations, history } = data;
  const content = main.querySelector('#ana-content');
  content.innerHTML = '';

  // —— 1. KPI Cards ————————————————————————————————
  const totalInterviews = overview.total_interviews ?? 0;
  const completed = overview.completed_interviews ?? 0;
  const completionRate = totalInterviews > 0 ? Math.round((completed / totalInterviews) * 100) : 0;
  const avgScore = (overview.average_score ?? 0).toFixed(1);
  const passRate = Math.round(overview.pass_rate ?? 0);
  const totalViolations = overview.total_violations ?? 0;

  const kpiHTML = `
    <div class="ana-section ana-fade-in">
      <div class="ana-kpi-row">
        <div class="ana-kpi">
          <div class="ana-kpi-icon">📋</div>
          <div class="ana-kpi-body">
            <span class="ana-kpi-value">${totalInterviews}</span>
            <span class="ana-kpi-label">Total Interviews</span>
          </div>
        </div>
        <div class="ana-kpi">
          <div class="ana-kpi-icon">✅</div>
          <div class="ana-kpi-body">
            <span class="ana-kpi-value">${completionRate}%</span>
            <span class="ana-kpi-label">Completion Rate</span>
          </div>
        </div>
        <div class="ana-kpi">
          <div class="ana-kpi-icon">⭐</div>
          <div class="ana-kpi-body">
            <span class="ana-kpi-value ana-kpi-value--gold">${avgScore}</span>
            <span class="ana-kpi-label">Avg Score</span>
          </div>
        </div>
        <div class="ana-kpi">
          <div class="ana-kpi-icon">🏆</div>
          <div class="ana-kpi-body">
            <span class="ana-kpi-value ana-kpi-value--green">${passRate}%</span>
            <span class="ana-kpi-label">Pass Rate</span>
          </div>
        </div>
        <div class="ana-kpi">
          <div class="ana-kpi-icon">🚨</div>
          <div class="ana-kpi-body">
            <span class="ana-kpi-value ana-kpi-value--red">${totalViolations}</span>
            <span class="ana-kpi-label">Violations</span>
          </div>
        </div>
      </div>
    </div>
  `;

  // —— 2. Performance Trend ————————————————————————
  const trendData = trend?.scores || trend?.data || trend?.trend || trend || [];
  const trendHTML = `
    <div class="ana-card ana-card--wide ana-fade-in" style="animation-delay:0.1s">
      <h3 class="ana-card-title">📈 Performance Trend</h3>
      <div class="ana-chart-container">${svgLineTrend(Array.isArray(trendData) ? trendData : [])}</div>
    </div>
  `;

  // —— 3. Skills Distribution ——————————————————————
  const skillItems = (skills?.skills || []).map(s => ({
    label: s.skill || s.name || 'Unknown',
    value: s.candidate_count ?? s.average_score ?? 0
  }));
  const skillsHTML = `
    <div class="ana-card ana-fade-in" style="animation-delay:0.2s">
      <h3 class="ana-card-title">🎯 Skills Distribution</h3>
      <div class="ana-chart-container">${svgHorizontalBars(skillItems.slice(0, 8))}</div>
    </div>
  `;

  // —— 4. Strengths & Weaknesses —————————————————
  const strengthsList = sw?.strengths || [];
  const weaknessesList = sw?.weaknesses || [];

  const swStrengthItems = strengthsList.slice(0, 6).map(s => ({
    label: s.topic || s.skill || s.text || s,
    value: s.count ?? s.score ?? 1
  }));
  const swWeaknessItems = weaknessesList.slice(0, 6).map(w => ({
    label: w.topic || w.skill || w.text || w,
    value: w.count ?? w.score ?? 1
  }));

  const swHTML = `
    <div class="ana-card ana-fade-in" style="animation-delay:0.3s">
      <h3 class="ana-card-title">💪 Strengths & Weaknesses</h3>
      <div class="ana-sw-columns">
        <div class="ana-sw-col">
          <h4 class="ana-sw-heading ana-sw-heading--green">Strengths</h4>
          ${svgHorizontalBars(swStrengthItems, { barColor: 'var(--accent-emerald)' })}
        </div>
        <div class="ana-sw-col">
          <h4 class="ana-sw-heading ana-sw-heading--amber">Weaknesses</h4>
          ${svgHorizontalBars(swWeaknessItems, { barColor: 'var(--accent-amber)' })}
        </div>
      </div>
    </div>
  `;

  // —— 5. Proctor Violations Donut ———————————————
  const violationSegments = (violations?.by_type || violations?.violations || []).map(v => ({
    label: v.event_type || v.type || 'Unknown',
    value: v.count ?? 0
  }));
  const violationsHTML = `
    <div class="ana-card ana-fade-in" style="animation-delay:0.4s">
      <h3 class="ana-card-title">🛡️ Proctor Violations</h3>
      <div class="ana-chart-container ana-chart-container--center">${svgDonutChart(violationSegments)}</div>
    </div>
  `;

  // —— 6. Score Distribution Histogram ———————————
  const historyScores = (history?.sessions || []).map(s => s.score ?? s.final_score ?? s.average_score ?? 0);
  const histogramHTML = `
    <div class="ana-card ana-fade-in" style="animation-delay:0.5s">
      <h3 class="ana-card-title">📊 Score Distribution</h3>
      <div class="ana-chart-container">${svgHistogram(historyScores)}</div>
    </div>
  `;

  // —— Assemble ————————————————————————————————————
  content.innerHTML = `
    ${kpiHTML}
    <div class="ana-grid">
      ${trendHTML}
      ${skillsHTML}
      ${swHTML}
      ${violationsHTML}
      ${histogramHTML}
    </div>
  `;
}


// ——— Render Individual Candidate Dashboard ——————————————————————
function _renderCandidateDashboard(main, detail) {
  const content = main.querySelector('#ana-content');
  content.innerHTML = '';

  const name = detail.candidate_name || 'Unknown';
  const avgScore = detail.average_score ?? 0;
  const totalQuestions = detail.question_count ?? 0;
  const violationsCount = detail.violations_count ?? 0;
  const recommendation = detail.recommendation || '—';
  const scoreColor = avgScore >= 7 ? '#10b981' : avgScore >= 5 ? '#f5b800' : '#ef4444';

  // —— 1. Candidate KPI Row ———————————————————————
  const kpiHTML = `
    <div class="ana-section ana-fade-in">
      <div class="ana-kpi-row">
        <div class="ana-kpi">
          <div class="ana-kpi-icon">👤</div>
          <div class="ana-kpi-body">
            <span class="ana-kpi-value" style="font-size: 1.1rem;">${_escapeHtml(name)}</span>
            <span class="ana-kpi-label">Candidate</span>
          </div>
        </div>
        <div class="ana-kpi">
          <div class="ana-kpi-icon">⭐</div>
          <div class="ana-kpi-body">
            <span class="ana-kpi-value" style="color: ${scoreColor};">${avgScore.toFixed(1)}</span>
            <span class="ana-kpi-label">Avg Score</span>
          </div>
        </div>
        <div class="ana-kpi">
          <div class="ana-kpi-icon">📝</div>
          <div class="ana-kpi-body">
            <span class="ana-kpi-value">${totalQuestions}</span>
            <span class="ana-kpi-label">Questions</span>
          </div>
        </div>
        <div class="ana-kpi">
          <div class="ana-kpi-icon">🚨</div>
          <div class="ana-kpi-body">
            <span class="ana-kpi-value ${violationsCount > 5 ? 'ana-kpi-value--red' : violationsCount > 0 ? 'ana-kpi-value--gold' : 'ana-kpi-value--green'}">${violationsCount}</span>
            <span class="ana-kpi-label">Violations</span>
          </div>
        </div>
        <div class="ana-kpi">
          <div class="ana-kpi-icon">📋</div>
          <div class="ana-kpi-body">
            <span class="ana-kpi-value" style="font-size: 0.95rem; color: ${
              recommendation.toLowerCase().includes('strong') ? '#10b981' :
              recommendation.toLowerCase().includes('no') ? '#ef4444' :
              recommendation.toLowerCase().includes('hire') ? '#f5b800' : 'var(--text-primary)'
            };">${_escapeHtml(recommendation)}</span>
            <span class="ana-kpi-label">Recommendation</span>
          </div>
        </div>
      </div>
    </div>
  `;

  // —— 2. Per-Question Scores (Bar Chart) ————————
  const perQ = detail.per_question_scores || [];
  const questionBarItems = perQ.map(q => ({
    label: `${q.question_number}`,
    value: q.score
  }));

  const questionScoresHTML = `
    <div class="ana-card ana-card--wide ana-fade-in" style="animation-delay:0.1s">
      <h3 class="ana-card-title">📊 Score Per Question</h3>
      <div class="ana-chart-container">${svgVerticalBars(questionBarItems)}</div>
      ${perQ.length > 0 ? `
        <div style="margin-top: 12px; padding: 10px; background: var(--bg-hover); border-radius: 8px; max-height: 180px; overflow-y: auto;">
          <table style="width: 100%; border-collapse: collapse; font-size: 0.8rem;">
            <thead>
              <tr style="border-bottom: 1px solid var(--border-color);">
                <th style="text-align: left; padding: 4px 8px; color: var(--text-muted);">#</th>
                <th style="text-align: left; padding: 4px 8px; color: var(--text-muted);">Topic</th>
                <th style="text-align: left; padding: 4px 8px; color: var(--text-muted);">Difficulty</th>
                <th style="text-align: center; padding: 4px 8px; color: var(--text-muted);">Score</th>
              </tr>
            </thead>
            <tbody>
              ${perQ.map(q => {
                const qColor = q.score >= 7 ? '#10b981' : q.score >= 5 ? '#f5b800' : '#ef4444';
                return `<tr style="border-bottom: 1px solid var(--border-color);">
                  <td style="padding: 4px 8px; color: var(--text-muted);">${q.question_number}</td>
                  <td style="padding: 4px 8px; color: var(--text-primary);">${_escapeHtml(q.topic || q.category)}</td>
                  <td style="padding: 4px 8px; color: var(--text-muted); text-transform: capitalize;">${q.difficulty}</td>
                  <td style="padding: 4px 8px; text-align: center; font-weight: 700; color: ${qColor};">${q.score}/10</td>
                </tr>`;
              }).join('')}
            </tbody>
          </table>
        </div>
      ` : ''}
    </div>
  `;

  // —— 3. Strengths vs Weaknesses ————————————————
  const strengthItems = (detail.strengths || []).map(s => ({
    label: typeof s === 'string' ? s : (s.text || 'Unknown'),
    value: typeof s === 'string' ? 1 : (s.count ?? 1)
  }));

  // Fallback: if no strengths recorded, derive from high-scoring questions
  if (strengthItems.length === 0 && detail.per_question_scores) {
    const goodQs = detail.per_question_scores.filter(q => q.score >= 6);
    const topicCounts = {};
    goodQs.forEach(q => { const t = q.topic || q.category; topicCounts[t] = (topicCounts[t] || 0) + 1; });
    Object.entries(topicCounts).sort((a,b) => b[1]-a[1]).slice(0, 5).forEach(([topic, count]) => {
      strengthItems.push({ label: topic.replace(/_/g, ' '), value: count });
    });
  }

  const weaknessItems = (detail.weaknesses || []).map(w => ({
    label: typeof w === 'string' ? w : (w.text || 'Unknown'),
    value: typeof w === 'string' ? 1 : (w.count ?? 1)
  }));

  const swHTML = `
    <div class="ana-card ana-fade-in" style="animation-delay:0.2s">
      <h3 class="ana-card-title">💪 Strengths vs Weaknesses</h3>
      <div class="ana-sw-columns">
        <div class="ana-sw-col">
          <h4 class="ana-sw-heading ana-sw-heading--green">Strengths</h4>
          ${strengthItems.length > 0
            ? svgHorizontalBars(strengthItems.slice(0, 6), { barColor: 'var(--accent-emerald)' })
            : '<p class="ana-empty">No strengths recorded</p>'}
        </div>
        <div class="ana-sw-col">
          <h4 class="ana-sw-heading ana-sw-heading--amber">Areas for Improvement</h4>
          ${weaknessItems.length > 0
            ? svgHorizontalBars(weaknessItems.slice(0, 6), { barColor: 'var(--accent-amber)' })
            : '<p class="ana-empty">No weaknesses recorded</p>'}
        </div>
      </div>
    </div>
  `;

  // —— 4. Violations Breakdown (Donut) ———————————
  const violationSegments = (detail.violations_by_type || []).map(v => ({
    label: (v.event_type || 'Unknown').replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase()),
    value: v.count ?? 0
  }));

  const violationsHTML = `
    <div class="ana-card ana-fade-in" style="animation-delay:0.3s">
      <h3 class="ana-card-title">🛡️ Violation Breakdown</h3>
      <div class="ana-chart-container ana-chart-container--center">${svgDonutChart(violationSegments)}</div>
    </div>
  `;

  // —— 5. Skills Detected ————————————————————————
  const skillsDetected = detail.skills_detected || [];
  const skillsHTML = skillsDetected.length > 0 ? `
    <div class="ana-card ana-fade-in" style="animation-delay:0.4s">
      <h3 class="ana-card-title">🏷️ Skills Detected</h3>
      <div style="display: flex; flex-wrap: wrap; gap: 8px; padding: 12px 0;">
        ${skillsDetected.map(s => `
          <span style="
            display: inline-block; padding: 6px 14px; border-radius: 20px;
            background: rgba(245, 184, 0, 0.1); border: 1px solid rgba(245, 184, 0, 0.3);
            color: var(--accent-gold); font-size: 0.82rem; font-weight: 500;
          ">${_escapeHtml(s)}</span>
        `).join('')}
      </div>
    </div>
  ` : '';

  // —— Assemble ————————————————————————————————————
  content.innerHTML = `
    ${kpiHTML}
    <div class="ana-grid">
      ${questionScoresHTML}
      ${swHTML}
      ${violationsHTML}
      ${skillsHTML}
    </div>
  `;
}


// ——— Utilities ——————————————————————————————————————————————————
function _escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
