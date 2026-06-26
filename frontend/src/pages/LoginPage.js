/* Login / Register Page */
import { auth } from '../api/index.js';
import { navigate } from '../main.js';
import { Toast } from '../components/Toast.js';

export function renderLoginPage(container) {
  container.innerHTML = `
    <div class="auth-page">
      <div class="auth-card">
        <div class="auth-header">
          <span class="auth-logo">🤖</span>
          <h1>AI Interview Assistant</h1>
          <p>Your intelligent mock interview platform</p>
        </div>
        <div class="auth-tabs">
          <button class="auth-tab active" id="tab-login">Sign In</button>
          <button class="auth-tab" id="tab-register">Create Account</button>
        </div>

        <!-- LOGIN FORM -->
        <form class="auth-form" id="login-form">
          <div id="login-error" style="display:none" class="auth-error"></div>
          <div class="form-group">
            <label class="form-label">Email address</label>
            <input class="form-input" id="login-email" type="email" placeholder="you@example.com" autocomplete="email" required />
          </div>
          <div class="form-group">
            <label class="form-label">Password</label>
            <input class="form-input" id="login-password" type="password" placeholder="••••••••" autocomplete="current-password" required />
          </div>
          <button class="btn btn-primary auth-submit" type="submit" id="login-btn">
            Sign In
          </button>
        </form>

        <!-- REGISTER FORM -->
        <form class="auth-form" id="register-form" style="display:none">
          <div id="reg-error" style="display:none" class="auth-error"></div>
          <div class="form-group">
            <label class="form-label">Full name</label>
            <input class="form-input" id="reg-name" type="text" placeholder="Jane Doe" autocomplete="name" required />
          </div>
          <div class="form-group">
            <label class="form-label">Email address</label>
            <input class="form-input" id="reg-email" type="email" placeholder="you@example.com" autocomplete="email" required />
          </div>
          <div class="form-group">
            <label class="form-label">Password</label>
            <input class="form-input" id="reg-password" type="password" placeholder="Min. 8 characters" autocomplete="new-password" required />
          </div>
          <div class="form-group">
            <label class="form-label">I am a…</label>
            <div class="role-grid">
              <div class="role-option selected" data-role="candidate">
                <span class="role-icon">🎓</span>
                <div class="role-name">Candidate</div>
              </div>
              <div class="role-option" data-role="recruiter">
                <span class="role-icon">👔</span>
                <div class="role-name">Recruiter</div>
              </div>
            </div>
          </div>
          <input type="hidden" id="reg-role" value="candidate" />
          <button class="btn btn-primary auth-submit" type="submit" id="reg-btn">
            Create Account
          </button>
        </form>

        <div class="auth-footer">
          Secured by JWT · AI-powered interviews
        </div>
      </div>
    </div>
  `;

  /* Tab switching */
  const tabLogin    = container.querySelector('#tab-login');
  const tabRegister = container.querySelector('#tab-register');
  const loginForm   = container.querySelector('#login-form');
  const regForm     = container.querySelector('#register-form');

  tabLogin.onclick = () => {
    tabLogin.classList.add('active');    tabRegister.classList.remove('active');
    loginForm.style.display = '';        regForm.style.display = 'none';
  };
  tabRegister.onclick = () => {
    tabRegister.classList.add('active'); tabLogin.classList.remove('active');
    regForm.style.display = '';          loginForm.style.display = 'none';
  };

  /* Role selector */
  container.querySelectorAll('.role-option').forEach(opt => {
    opt.onclick = () => {
      container.querySelectorAll('.role-option').forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
      container.querySelector('#reg-role').value = opt.dataset.role;
    };
  });

  /* Login submit */
  loginForm.onsubmit = async (e) => {
    e.preventDefault();
    const btn = container.querySelector('#login-btn');
    const errEl = container.querySelector('#login-error');
    const email = container.querySelector('#login-email').value.trim();
    const password = container.querySelector('#login-password').value;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Signing in…`;
    errEl.style.display = 'none';
    try {
      const data = await auth.login(email, password);
      localStorage.setItem('access_token',  data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      Toast.success(`Welcome back, ${data.user.name}!`);
      _redirectByRole(data.user.role);
    } catch (err) {
      errEl.textContent = err.message;
      errEl.style.display = 'block';
      btn.disabled = false;
      btn.textContent = 'Sign In';
    }
  };

  /* Register submit */
  regForm.onsubmit = async (e) => {
    e.preventDefault();
    const btn = container.querySelector('#reg-btn');
    const errEl = container.querySelector('#reg-error');
    const name  = container.querySelector('#reg-name').value.trim();
    const email = container.querySelector('#reg-email').value.trim();
    const password = container.querySelector('#reg-password').value;
    const role  = container.querySelector('#reg-role').value;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Creating…`;
    errEl.style.display = 'none';
    try {
      await auth.register(name, email, password, role);
      Toast.success('Account created! Please sign in.');
      tabLogin.click();
      container.querySelector('#login-email').value = email;
      btn.disabled = false;
      btn.textContent = 'Create Account';
    } catch (err) {
      errEl.textContent = err.message;
      errEl.style.display = 'block';
      btn.disabled = false;
      btn.textContent = 'Create Account';
    }
  };
}

function _redirectByRole(role) {
  if (role === 'admin' || role === 'recruiter' || role === 'interviewer') {
    navigate('/recruiter');
  } else {
    navigate('/dashboard');
  }
}
