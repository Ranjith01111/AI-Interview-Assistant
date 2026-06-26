import { navigate } from '../main.js';

export function renderSidebar(activeMenu) {
  const sidebar = document.createElement('div');
  sidebar.className = 'app-sidebar';
  sidebar.style.width = '240px';
  sidebar.style.background = 'var(--bg-card)';
  sidebar.style.borderRight = '1px solid var(--border-color)';
  sidebar.style.padding = 'var(--spacing-md) 0';
  sidebar.style.height = 'calc(100vh - 60px)'; // Assuming navbar is 60px
  
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const isCandidate = user.role === 'candidate';
  
  let menuItems = [];
  if (isCandidate) {
    menuItems = [
      { id: 'dashboard', icon: '🏠', label: 'My Dashboard', route: '/dashboard' },
      { id: 'interview', icon: '🎤', label: 'New Interview', route: '/interview' }
    ];
  } else {
    menuItems = [
      { id: 'recruiter', icon: '👥', label: 'Candidates', route: '/recruiter' },
      { id: 'analytics', icon: '📊', label: 'Analytics', route: '/analytics' }
    ];
  }

  const menuHtml = menuItems.map(item => `
    <div class="sidebar-item ${activeMenu === item.id ? 'active' : ''}" 
         data-route="${item.route}"
         style="padding: 12px 20px; cursor: pointer; display: flex; align-items: center; gap: 12px;
                color: ${activeMenu === item.id ? 'white' : 'var(--text-muted)'};
                background: ${activeMenu === item.id ? 'var(--bg-hover)' : 'transparent'};
                border-left: 3px solid ${activeMenu === item.id ? 'var(--accent-gold)' : 'transparent'};
                transition: all 0.2s;">
      <span style="font-size: 1.2rem;">${item.icon}</span> 
      <span style="font-weight: 500;">${item.label}</span>
    </div>
  `).join('');

  sidebar.innerHTML = `
    <div class="sidebar-menu" style="display: flex; flex-direction: column; gap: 4px;">
      ${menuHtml}
    </div>
  `;
  
  // Add hover effects dynamically
  sidebar.querySelectorAll('.sidebar-item').forEach(item => {
    if (!item.classList.contains('active')) {
      item.onmouseenter = () => { item.style.background = 'var(--bg-hover)'; item.style.color = 'white'; };
      item.onmouseleave = () => { item.style.background = 'transparent'; item.style.color = 'var(--text-muted)'; };
    }
    item.onclick = () => navigate(item.dataset.route);
  });
  
  return sidebar;
}
