/* Top navigation bar */
import { navigate } from '../main.js';

export function renderNavbar(container) {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const initials = (user.name || 'U').split(' ').map(w => w[0]).join('').toUpperCase().slice(0,2);
  const roleLabel = { admin:'Admin', recruiter:'Recruiter', interviewer:'Interviewer', candidate:'Candidate' }[user.role] || '';

  const nav = document.createElement('nav');
  nav.className = 'navbar';
  nav.innerHTML = `
    <a class="navbar-brand" href="#/">
      <span>🤖</span>
      <span>AI Interview</span>
    </a>
    <div class="navbar-spacer"></div>
    <div class="navbar-user">
      <div class="user-avatar">${initials}</div>
      <div>
        <div class="user-name">${user.name || 'User'}</div>
        <div style="font-size:0.72rem;color:var(--text-muted)">${roleLabel}</div>
      </div>
      <button class="logout-btn" id="logout-btn">Sign out</button>
    </div>
  `;

  nav.querySelector('#logout-btn').onclick = () => {
    localStorage.clear();
    navigate('/login');
  };

  container.prepend(nav);
}
