import { renderNavbar } from '../components/Navbar.js';
import { renderSidebar } from '../components/Sidebar.js';
import { auth, analytics } from '../api/index.js';
import { navigate } from '../main.js';
import { Toast } from '../components/Toast.js';

export async function renderRecruiterDashboard(container) {
  container.innerHTML = '';
  renderNavbar(container);
  
  const layout = document.createElement('div');
  layout.style.display = 'flex';
  layout.style.height = 'calc(100vh - 60px)';
  
  layout.appendChild(renderSidebar('recruiter'));
  
  const main = document.createElement('div');
  main.className = 'app-main';
  main.style.flex = '1';
  main.style.overflowY = 'auto';
  
  main.innerHTML = `
    <div class="page-content recruiter-dashboard">
      <div class="page-header">
        <h1>Candidate Management</h1>
        <p>Review candidate interviews and manage users</p>
      </div>

      <div class="table-container" style="background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border-color); overflow: hidden; margin-top: 24px;">
        <table style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead style="background: var(--bg-hover); border-bottom: 1px solid var(--border-color);">
            <tr>
              <th style="padding: 16px; color: var(--text-muted); font-weight: 500;">Name</th>
              <th style="padding: 16px; color: var(--text-muted); font-weight: 500;">Email</th>
              <th style="padding: 16px; color: var(--text-muted); font-weight: 500;">Role</th>
              <th style="padding: 16px; color: var(--text-muted); font-weight: 500;">Status</th>
              <th style="padding: 16px; color: var(--text-muted); font-weight: 500;">Actions</th>
            </tr>
          </thead>
          <tbody id="user-table-body">
            <tr><td colspan="5" style="padding: 20px; text-align: center;">Loading users...</td></tr>
          </tbody>
        </table>
      </div>
      
      <h2 style="margin-top: 32px; margin-bottom: 16px;">Recent Sessions</h2>
      <div id="session-list"></div>
    </div>
  `;
  
  layout.appendChild(main);
  container.appendChild(layout);

  try {
    const [usersRes, history] = await Promise.all([
      auth.listUsers(),
      analytics.history()
    ]);
    
    // Render Users
    const tbody = main.querySelector('#user-table-body');
    const users = usersRes.users || [];
    if (users.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="padding: 20px; text-align: center;">No users found</td></tr>';
    } else {
      tbody.innerHTML = '';
      users.forEach(u => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid var(--border-color)';
        const isActive = u.is_active;
        tr.innerHTML = `
          <td style="padding: 16px;">${u.name}</td>
          <td style="padding: 16px; color: var(--text-muted);">${u.email}</td>
          <td style="padding: 16px;"><span class="badge badge-gray">${u.role}</span></td>
          <td style="padding: 16px;">
             <span class="badge ${isActive ? 'badge-emerald' : 'badge-red'}">${isActive ? 'Active' : 'Inactive'}</span>
          </td>
          <td style="padding: 16px;">
              ${isActive && u.role === 'candidate' ? `<button class="btn btn-sm btn-outline deactivate-btn" data-id="${u.id}" style="color: var(--accent-red); border-color: var(--accent-red); padding: 4px 8px; font-size: 0.8rem;">Deactivate</button>` : ''}
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
            btn.parentElement.previousElementSibling.innerHTML = '<span class="badge badge-red">Inactive</span>';
            btn.remove();
          } catch (err) {
            Toast.error(err.message, 'Deactivate');
          }
        };
      });
    }

    // Render Sessions
    const listEl = main.querySelector('#session-list');
    const sessions = history?.sessions || history || [];
    if (!sessions.length) {
      listEl.innerHTML = `<div class="empty-state">No interview sessions found</div>`;
      return;
    }

    listEl.innerHTML = '';
    sessions.slice(0, 10).forEach(s => {
      const score     = s.average_score ?? 0;
      const status    = s.status || 'pending';
      const date      = s.created_at ? new Date(s.created_at).toLocaleDateString() : '—';
      const isPass    = score >= 7;

      const card = document.createElement('div');
      card.className = 'session-card';
      card.style.cursor = 'pointer';
      card.innerHTML = `
        <div class="session-card-info">
          <div class="session-card-name">${s.candidate_name || 'Candidate'} — Session</div>
          <div class="session-card-meta">
            <span>🗓 ${date}</span>
            <span class="badge ${status === 'completed' ? 'badge-emerald' : 'badge-gray'}">${status}</span>
          </div>
        </div>
        <div class="session-card-score ${status !== 'completed' ? 'pending' : isPass ? 'pass' : 'fail'}">
          ${status !== 'completed' ? '—' : score.toFixed(1)}
        </div>
      `;
      card.onclick = () => navigate(`/interview/summary/${s.session_id}`);
      listEl.appendChild(card);
    });
    
  } catch (err) {
    Toast.error(err.message, 'Recruiter Dashboard');
  }
}
