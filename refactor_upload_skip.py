import re

def patch_step1():
    path = r"frontend\src\pages\steps\Step1Upload.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Change signature
    content = content.replace(
        "export async function renderStep1(container, state, onNext) {",
        "export async function renderStep1(container, state, onNext, onSkip = null) {"
    )

    # Change UI bottom bar
    old_bar = """        <div style="padding:var(--spacing-md) var(--spacing-lg);border-top:1px solid var(--border);display:flex;justify-content:flex-end">
          <button class="btn btn-primary" id="next-btn" disabled>
            Generate Questions →
          </button>
        </div>"""
    new_bar = """        <div style="padding:var(--spacing-md) var(--spacing-lg);border-top:1px solid var(--border);display:flex;justify-content:${onSkip ? 'space-between' : 'flex-end'}">
          ${onSkip ? '<button class="btn btn-ghost" id="skip-btn" style="color:var(--text-muted)">Skip without Resume →</button>' : ''}
          <button class="btn btn-primary" id="next-btn" disabled>
            Next Step →
          </button>
        </div>"""
    content = content.replace(old_bar, new_bar)

    # Add skip handler
    old_next = "nextBtn.onclick = () => onNext();"
    new_next = """nextBtn.onclick = () => onNext();
  if (onSkip) {
    const skipBtn = container.querySelector('#skip-btn');
    if (skipBtn) skipBtn.onclick = () => onSkip();
  }"""
    content = content.replace(old_next, new_next)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def patch_flow():
    path = r"frontend\src\pages\InterviewFlow.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove the custom bypass block at the bottom
    bypass_block = """  // If starting fresh in custom mode, provision a session and skip Step 0
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
  } else {
    goToStep(currentStep);
  }"""
    content = content.replace(bypass_block, "  goToStep(currentStep);")

    # Update case 0
    case_0_old = """      case 0: await renderStep1(host, state, () => {
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
      
    case_0_new = """      case 0: 
        const onSkip = interviewMode === 'custom' ? () => {
          host.innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-muted)">Initializing custom session...</div>';
          interview.createCustomSession().then(res => {
            state.sessionId = res.session_id;
            state.candidateName = 'Custom Setup';
            goToStep(1);
          }).catch(err => {
            Toast.error('Failed to create session');
            console.error(err);
          });
        } : null;

        await renderStep1(host, state, () => {
          if (interviewMode === 'resume') {
            state.interviewConfig = {
              preset_id: 'resume_based',
              focus_categories: [], 
              timer_seconds: 0,
              session_time_minutes: 25,
              num_questions: 10,
              difficulty: 'medium'
            };
            goToStep(2); // Jump to questions
          } else {
            goToStep(1); // Go to manual setup
          }
        }, onSkip); 
        break;"""
        
    content = content.replace(case_0_old, case_0_new)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    patch_step1()
    patch_flow()
