import { renderNavbar } from '../components/Navbar.js';
import { renderSidebar } from '../components/Sidebar.js';
import { analytics } from '../api/index.js';
import { Toast } from '../components/Toast.js';

/**
 * Analytics Dashboard — Full SVG charting suite
 * Charts: Performance Trend (line), Skills (h-bar), Strengths/Weaknesses,
 *         Proctor Violations (donut), Score Distribution (histogram)
 */

// ─── SVG Chart Generators ───────────────────────────────────────────

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
  const width = 560;
  const totalH = items.length * itemH + 10;

  const bars = items.map((d, i) => {
    const barW = max > 0 ? (d.value / max) * 340 : 0;
    const y = i * itemH + 6;
    return `
      <text x="0" y="${y + 18}" class="ana-svg-label" fill="var(--text-secondary)" font-size="12">${d.label}</text>
      <rect x="160" y="${y + 4}" width="${barW.toFixed(1)}" height="20" rx="4" fill="${barColor}" opacity="0.85" class="ana-bar-rect">
        <animate attributeName="width" from="0" to="${barW.toFixed(1)}" dur="0.6s" fill="freeze"/>
      </rect>
      <text x="${160 + barW + 8}" y="${y + 18}" class="ana-svg-label" fill="var(--text-muted)" font-size="11">${d.value}</text>
    `;
  }).join('');

  return `
    <svg viewBox="0 0 ${width} ${totalH}" class="ana-chart-svg" preserveAspectRatio="xMidYMid meet" style="max-height:${totalH}px;">
      ${bars}
    </svg>
  `;
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

// ─── Skeleton Loaders ───────────────────────────────────────────────

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

// ─── Main Render ────────────────────────────────────────────────────

export async function renderAnalyticsDashboard(container) {
  container.innerHTML = '';
  renderNavbar(container);

  const layout = document.createElement('div');
  layout.className = 'ana-layout';

  layout.appendChild(renderSidebar('analytics'));

  const main = document.createElement('div');
  main.className = 'app-main ana-main';

  main.innerHTML = `
    <div class="page-content ana-page">
      <div class="ana-header">
        <h1 class="ana-title">Platform Analytics</h1>
        <p class="ana-subtitle">Insights into interview performance and proctoring integrity</p>
      </div>
      <div id="ana-content">${renderSkeletons()}</div>
    </div>
  `;

  layout.appendChild(main);
  container.appendChild(layout);

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

    const content = main.querySelector('#ana-content');
    content.innerHTML = '';

    // ── 1. KPI Cards ────────────────────────────────────
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

    // ── 2. Performance Trend ────────────────────────────
    const trendData = trend?.scores || trend?.data || trend || [];
    const trendHTML = `
      <div class="ana-card ana-card--wide ana-fade-in" style="animation-delay:0.1s">
        <h3 class="ana-card-title">📈 Performance Trend</h3>
        <div class="ana-chart-container">${svgLineTrend(Array.isArray(trendData) ? trendData : [])}</div>
      </div>
    `;

    // ── 3. Skills Distribution ──────────────────────────
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

    // ── 4. Strengths & Weaknesses ───────────────────────
    const strengthsList = sw?.strengths || [];
    const weaknessesList = sw?.weaknesses || [];

    const swStrengthItems = strengthsList.slice(0, 6).map(s => ({
      label: s.topic || s.skill || s,
      value: s.count ?? s.score ?? 1
    }));
    const swWeaknessItems = weaknessesList.slice(0, 6).map(w => ({
      label: w.topic || w.skill || w,
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

    // ── 5. Proctor Violations Donut ─────────────────────
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

    // ── 6. Score Distribution Histogram ─────────────────
    const historyScores = (history?.sessions || []).map(s => s.score ?? s.final_score ?? s.average_score ?? 0);
    const histogramHTML = `
      <div class="ana-card ana-fade-in" style="animation-delay:0.5s">
        <h3 class="ana-card-title">📊 Score Distribution</h3>
        <div class="ana-chart-container">${svgHistogram(historyScores)}</div>
      </div>
    `;

    // ── Assemble ────────────────────────────────────────
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
}
