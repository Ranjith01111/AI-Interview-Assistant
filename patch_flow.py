import re

def main():
    path = r"frontend\src\pages\InterviewFlow.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Add api import
    if "import { interview } from '../api/index.js';" not in content:
        content = content.replace(
            "import { renderCodingTransition } from './steps/CodingTransitionPanel.js';",
            "import { renderCodingTransition } from './steps/CodingTransitionPanel.js';\nimport { interview } from '../api/index.js';\nimport { Toast } from '../components/Toast.js';"
        )

    # Parse mode
    mode_parsing = """  const isResume = window.location.hash.includes('resume=true');
  const searchParams = new URLSearchParams(window.location.hash.split('?')[1] || '');
  const interviewMode = searchParams.get('mode') || 'resume'; // 'resume' or 'custom'
"""
    content = content.replace("  const isResume = window.location.hash.includes('resume=true');", mode_parsing)

    # Init custom session if needed
    init_logic = """  goToStep(currentStep);

  // If starting fresh in custom mode, provision a session and skip Step 0
  if (!isResume && currentStep === 0 && interviewMode === 'custom') {
    host.innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-muted)">Initializing custom session...</div>';
    interview.createCustomSession().then(res => {
      state.sessionId = res.session_id;
      state.candidateName = 'Custom Setup';
      goToStep(1); // Jump to Setup
    }).catch(err => {
      Toast.error('Failed to create session');
      console.error(err);
    });
  }"""
    content = content.replace("  goToStep(currentStep);", init_logic)

    # Change case 0
    case_0_old = "case 0: await renderStep1(host, state, () => goToStep(1)); break;"
    case_0_new = """case 0: await renderStep1(host, state, () => {
        if (interviewMode === 'resume') {
          // Skip setup, auto-configure 25 min default
          state.interviewConfig = {
            preset_id: 'resume_based',
            focus_categories: [], // backend will use detected skills
            timer_seconds: 0,
            session_time_minutes: 25,
            num_questions: 10,
            difficulty: 'medium'
          };
          goToStep(2);
        } else {
          goToStep(1);
        }
      }); break;"""
    content = content.replace(case_0_old, case_0_new)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
