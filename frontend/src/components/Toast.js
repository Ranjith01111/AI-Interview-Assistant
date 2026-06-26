/* Toast notification system */

let _container = null;

function getContainer() {
  if (!_container) {
    _container = document.createElement('div');
    _container.className = 'toast-container';
    document.body.appendChild(_container);
  }
  return _container;
}

const ICONS = { success:'✅', error:'❌', warning:'⚠️', info:'ℹ️' };

export function toast(message, type = 'info', title = '', duration = 4000) {
  const c = getContainer();
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `
    <span class="toast-icon">${ICONS[type] || '💬'}</span>
    <div class="toast-body">
      ${title ? `<div class="toast-title">${title}</div>` : ''}
      <div class="toast-msg">${message}</div>
    </div>
    <button class="toast-close" onclick="this.closest('.toast').remove()">✕</button>
  `;
  c.appendChild(t);
  setTimeout(() => {
    t.classList.add('removing');
    setTimeout(() => t.remove(), 300);
  }, duration);
}

export const Toast = {
  success: (msg, title='')  => toast(msg, 'success', title),
  error:   (msg, title='')  => toast(msg, 'error',   title),
  warning: (msg, title='')  => toast(msg, 'warning',  title),
  info:    (msg, title='')  => toast(msg, 'info',     title),
};
