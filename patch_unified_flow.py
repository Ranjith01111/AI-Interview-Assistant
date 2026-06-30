import re

def main():
    path = r"frontend\src\pages\InterviewFlow.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find case 0 block
    start_idx = content.find("      case 0: \n        const onSkip")
    if start_idx == -1:
        # Try to find just case 0:
        start_idx = content.find("      case 0:")

    end_idx = content.find("      case 1:", start_idx)

    new_case_0 = """      case 0: 
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
          goToStep(1); // Always go to setup after upload
        }, onSkip); 
        break;
"""

    content = content[:start_idx] + new_case_0 + content[end_idx:]

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
