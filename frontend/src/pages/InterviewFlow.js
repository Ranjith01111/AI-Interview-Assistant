/* Interview Flow Controller — Fixed-height shell with stable stepper */
import { renderNavbar } from '../components/Navbar.js';
import { renderStep1 } from './steps/Step1Upload.js';
import { renderSessionSetup } from './steps/SessionSetup.js';
import { renderStep2 } from './steps/Step2Questions.js';
import { renderStep3 } from './steps/Step3Interview.js';
import { renderStep4 } from './steps/Step4Coding.js';
import { renderStep5 } from './steps/Step5Summary.js';
import { renderInterviewSummary } from './steps/InterviewSummaryPanel.js';
import { renderCodingTransition } from './steps/CodingTransitionPanel.js';
import { interview } from '../api/index.js';
import { Toast } from '../components/Toast.js';

/*
  FLOW:
  Step 0: Upload Resume
  Step 1: Session Setup (Presets + Topic Focus + Timer Config)
  Step 2: Generate Questions
  Step 3: Interview Panel (Text chat) — proctored
  Step 4: Interview Score Summary
  Step 5: Transition — "Continue to Coding?" or "End"
  Step 6: Coding Panel — proctored
  Step 7: Final Cumulative Summary (Interview + Coding)
*/

const STEPS = [
  { label: 'Upload',    icon: '📄' },
  { label: 'Setup',     icon: '🎯' },
  { label: 'Questions', icon: '🧠' },
  { label: 'Interview', icon: '💬' },
  { label: 'Coding',    icon: '💻' },
  { label: 'Summary',   icon: '📊' },
];

export function renderInterviewFlow(container) {
  container.innerHTML = '';
  renderNavbar(container);

  // ── Stable shell — full viewport height, no reflow ──────────────
  const shell = document.createElement('div');
  shell.className = 'interview-flow-shell';
  container.appendChild(shell);

  // ── Fixed stepper ───────────────────────────────────────────────
  const stepperEl = document.createElement('div');
  stepperEl.className = 'stepper interview-stepper';
  stepperEl.id = 'stepper';
  shell.appendChild(stepperEl);

  // ── Scrollable content host ─────────────────────────────────────
  const host = document.createElement('div');
  host.id = 'step-host';
  host.className = 'interview-step-host';
  shell.appendChild(host);

  const state = {};
  let currentStep = 0;

  // ── Resume saved session ────────────────────────────────────────
  const isResume = window.location.hash.includes('resume=true');
  const searchParams = new URLSearchParams(window.location.hash.split('?')[1] || '');
  const interviewMode = searchParams.get('mode') || 'resume'; // 'resume' or 'custom'

  if (isResume) {
    const saved = localStorage.getItem('interview_session_state');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        Object.assign(state, parsed);
        currentStep = parsed.currentStep || 0;
      } catch(e) { currentStep = 0; }
    }
  }

  function saveSessionState(step) {
    state.currentStep = step;
    localStorage.setItem('interview_session_state', JSON.stringify(state));
  }

  function clearSessionState() {
    localStorage.removeItem('interview_session_state');
  }

  // ── Render stepper ──────────────────────────────────────────────
  function renderStepper(active) {
    let visualStep = 0;
    if      (active === 0)              visualStep = 0; // Upload
    else if (active === 1)              visualStep = 1; // Setup
    else if (active === 2)              visualStep = 2; // Questions
    else if (active === 3 || active === 4) visualStep = 3; // Interview
    else if (active === 5 || active === 6) visualStep = 4; // Coding
    else                                visualStep = 5; // Summary

    stepperEl.innerHTML = '';
    STEPS.forEach((s, i) => {
      const wrapper = document.createElement('div');
      wrapper.className = 'step-wrapper';

      const circle = document.createElement('div');
      circle.className = `step-circle ${i < visualStep ? 'done' : i === visualStep ? 'active' : ''}`;
      circle.textContent = i < visualStep ? '✓' : i + 1;

      const label = document.createElement('div');
      label.className = `step-label ${i < visualStep ? 'done' : i === visualStep ? 'active' : ''}`;
      label.textContent = s.label;

      wrapper.appendChild(circle);
      wrapper.appendChild(label);
      stepperEl.appendChild(wrapper);

      if (i < STEPS.length - 1) {
        const connector = document.createElement('div');
        connector.className = `step-connector ${i < visualStep ? 'done' : ''}`;
        stepperEl.appendChild(connector);
      }
    });
  }

  // ── Navigate to step ────────────────────────────────────────────
  async function goToStep(step) {
    host._destroyProctor?.();
    currentStep = step;
    saveSessionState(step);
    renderStepper(step);
    host.innerHTML = '';
    // Scroll host back to top on every step change
    host.scrollTop = 0;

    switch (step) {
      case 0: 
        const onSkip = () => {
          host.innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-muted)">Initializing session...</div>';
          interview.createCustomSession().then(res => {
            state.sessionId = res.session_id;
            state.candidateName = 'Custom Setup';
            goToStep(1);
          }).catch(err => {
            Toast.error('Failed to create session');
            console.error(err);
            goToStep(0); // reset if fail
          });
        };

        await renderStep1(host, state, () => {
          // Resume uploaded -> Auto-configure 25 min default & skip Setup
          state.interviewConfig = {
            preset_id: 'resume_based',
            focus_categories: [], // Backend will use detected skills
            timer_seconds: 0,
            session_time_minutes: 25,
            num_questions: 10,
            difficulty: 'medium'
          };
          goToStep(2); // Jump straight to Questions
        }, onSkip); 
        break;
      case 1: await renderSessionSetup(host, state, () => goToStep(2)); break;
      case 2: await renderStep2(host, state, () => goToStep(3)); break;
      case 3: await renderStep3(host, state, () => goToStep(5), () => goToStep(7)); break;
      case 4:
        // Skipped per user request: text interview summary is merged into the final summary
        goToStep(5);
        break;
      case 5: await renderCodingTransition(host, state, () => goToStep(6)); break;
      case 6: await renderStep4(host, state, () => goToStep(7), () => goToStep(7)); break;
      case 7:
        clearSessionState();
        await renderStep5(host, state);
        break;
    }
  }

  goToStep(currentStep);
}
