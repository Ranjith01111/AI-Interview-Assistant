import { renderNavbar } from '../components/Navbar.js';
import { renderSidebar } from '../components/Sidebar.js';
import { analytics } from '../api/index.js';
import { Toast } from '../components/Toast.js';

export async function renderAnalyticsDashboard(container) {
  container.innerHTML = '';
  renderNavbar(container);
  
  const layout = document.createElement('div');
  layout.style.display = 'flex';
  layout.style.height = 'calc(100vh - 60px)';
  
  layout.appendChild(renderSidebar('analytics'));
  
  const main = document.createElement('div');
  main.className = 'app-main';
  main.style.flex = '1';
  main.style.overflowY = 'auto';
  
  main.innerHTML = `
    <div class="page-content">
      <div class="page-header">
        <h1>Platform Analytics</h1>
        <p>Insights into interview performance and proctoring integrity</p>
      </div>

      <div class="kpi-grid mb-lg" id="analytics-kpi">
        <div class="kpi-card skeleton" style="height:100px"></div>
        <div class="kpi-card skeleton" style="height:100px"></div>
        <div class="kpi-card skeleton" style="height:100px"></div>
      </div>
      
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px;">
        <div class="panel" style="background: var(--bg-card); padding: 24px; border-radius: 12px; border: 1px solid var(--border-color);">
           <h3 style="margin-bottom: 16px;">Top Strengths</h3>
           <div id="strengths-list">Loading...</div>
        </div>
        <div class="panel" style="background: var(--bg-card); padding: 24px; border-radius: 12px; border: 1px solid var(--border-color);">
           <h3 style="margin-bottom: 16px;">Proctoring Violations</h3>
           <div id="violations-list">Loading...</div>
        </div>
      </div>
    </div>
  `;
  
  layout.appendChild(main);
  container.appendChild(layout);

  try {
    const [overview, strengths, violations] = await Promise.all([
      analytics.overview(),
      analytics.strengths(),
      analytics.violations()
    ]);

    // Render KPIs
    const kpiEl = main.querySelector('#analytics-kpi');
    kpiEl.innerHTML = `
      <div class="kpi-card">
        <div class="kpi-icon">📋</div>
        <div class="kpi-label">Total Interviews</div>
        <div class="kpi-value">${overview.total_interviews ?? 0}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon">⭐</div>
        <div class="kpi-label">Average Score</div>
        <div class="kpi-value" style="color:var(--accent-gold)">${(overview.average_score ?? 0).toFixed(1)}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon">🏆</div>
        <div class="kpi-label">Overall Pass Rate</div>
        <div class="kpi-value" style="color:var(--accent-emerald)">${Math.round(overview.pass_rate ?? 0)}%</div>
      </div>
    `;

    // Render Strengths
    const strengthsEl = main.querySelector('#strengths-list');
    const sList = strengths?.top_strengths || [];
    if (!sList.length) {
      strengthsEl.innerHTML = '<p style="color:var(--text-muted)">Not enough data</p>';
    } else {
      strengthsEl.innerHTML = '<ul style="padding-left: 20px; color: var(--text-body); line-height: 1.6;">' + 
        sList.slice(0, 5).map(s => `<li>${s.topic || s} (${s.count || 1} mentions)</li>`).join('') + 
        '</ul>';
    }

    // Render Violations
    const violEl = main.querySelector('#violations-list');
    const vList = violations?.violations || violations || [];
    if (!vList.length) {
      violEl.innerHTML = '<p style="color:var(--text-muted)">No violations recorded</p>';
    } else {
      violEl.innerHTML = '<ul style="padding-left: 20px; color: var(--accent-red); line-height: 1.6;">' + 
        vList.slice(0, 5).map(v => `<li>${v.event_type}: ${v.count} occurrences</li>`).join('') + 
        '</ul>';
    }

  } catch (err) {
    Toast.error(err.message, 'Analytics');
    main.querySelector('#analytics-kpi').innerHTML = `<div class="alert alert-error" style="grid-column:1/-1">${err.message}</div>`;
  }
}
