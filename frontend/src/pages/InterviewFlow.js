/* Interview Flow Controller — Separated Interview + Coding Panels with Session Resume */
import { renderNavbar } from '../components/Navbar.js';
import { renderStep1 } from './steps/Step1Upload.js';
import { renderStep2 } from './steps/Step2Questions.js';
import { renderStep3 } from './steps/Step3Interview.js';
import { renderStep4 } from './steps/Step4Coding.js';
import { renderStep5 } from './steps/Step5Summary.js';
import { renderInterviewSummary } from './steps/InterviewSummaryPanel.js';
import { renderCodingTransition } from './steps/CodingTransitionPanel.js';

/*
  NEW FLOW:
  Step 0: Upload Resume
  Step 1: Generate Questions
  Step 2: Interview Panel (Text chat) — proctored
  Step 3: Interview Score Summary
  Step 4: Transition — "Continue to Coding?" or "End"
  Step 5: Coding Panel — proctored
  Step 6: Final Cumulative Summary (Interview + Coding)
*/

const STEPS = [
  { label: 'Upload',    icon: '📄' },
  { label: 'Questions', icon: '🧠' },
  { label: 'Interview', icon: '💬' },
  { label: 'Coding',    icon: '💻' },
  { label: 'Summary',   icon: '📊' },
];

export function renderInterviewFlow(container) {
  container.innerHTML = '';
  renderNavbar(container);

  const shell = document.createElement('div');
  shell.className = 'app-main';
  container.appendChild(shell);

  /* Stepper */
  const stepperEl = document.createElement('div');
  stepperEl.className = 'stepper';
  stepperEl.id = 'stepper';
  shell.appendChild(stepperEl);

  /* Step content host */
  const host = document.createElement('div');
  host.id = 'step-host';
  shell.appendChild(host);

  const state = {};
  let currentStep = 0;

  /* Check if resuming */
  const isResume = window.location.hash.includes('resume=true');
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

  function renderStepper(active) {
    /* Map internal steps to visual stepper */
    let visualStep = 0;
    if (active <= 1) visualStep = active;
    else if (active === 2 || active === 3) visualStep = 2; // Interview
    else if (active === 4 || active === 5) visualStep = 3; // Coding
    else visualStep = 4; // Summary

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

  async function goToStep(step) {
    // Clean up proctoring from previous steps
    host._destroyProctor?.();
    currentStep = step;
    saveSessionState(step);
    renderStepper(step);
    host.innerHTML = '';

    switch (step) {
      case 0: // Upload
        await renderStep1(host, state, () => goToStep(1));
        break;
      case 1: // Generate Questions
        await renderStep2(host, state, () => goToStep(2));
        break;
      case 2: // Interview Panel (proctored)
        await renderStep3(host, state, () => goToStep(3), () => goToStep(6));
        break;
      case 3: // Interview Score Summary + Transition
        await renderInterviewSummary(host, state, {
          onContinue: () => goToStep(4), // Go to coding
          onEnd: () => goToStep(6),       // Skip to final summary
        });
        break;
      case 4: // Coding Transition (brief ready screen)
        await renderCodingTransition(host, state, () => goToStep(5));
        break;
      case 5: // Coding Panel (proctored)
        await renderStep4(host, state, () => goToStep(6), () => goToStep(6));
        break;
      case 6: // Final Cumulative Summary
        clearSessionState(); // Session complete
        await renderStep5(host, state);
        break;
    }
  }

  goToStep(currentStep);
}
