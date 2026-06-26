/* Coding Transition Panel — Brief ready screen before coding */
export async function renderCodingTransition(container, state, onStart) {
  container.innerHTML = `
    <div class="step-container slide-up">
      <div class="card" style="text-align:center">
        <div class="card-body" style="padding:var(--spacing-2xl)">
          <div style="font-size:4rem;margin-bottom:var(--spacing-md)">💻</div>
          <h2 style="margin-bottom:var(--spacing-sm)">Coding Challenge Panel</h2>
          <p style="color:var(--text-secondary);margin-bottom:var(--spacing-lg)">
            Solve coding challenges to demonstrate your problem-solving skills.<br>
            Your code will be run against visible and hidden test cases.
          </p>

          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:var(--spacing-md);max-width:400px;margin:0 auto var(--spacing-xl)">
            <div style="text-align:center">
              <div style="font-size:1.5rem">🖥️</div>
              <div style="font-size:0.75rem;color:var(--text-muted)">Code Editor</div>
            </div>
            <div style="text-align:center">
              <div style="font-size:1.5rem">🧪</div>
              <div style="font-size:0.75rem;color:var(--text-muted)">Test Cases</div>
            </div>
            <div style="text-align:center">
              <div style="font-size:1.5rem">👁️</div>
              <div style="font-size:0.75rem;color:var(--text-muted)">Proctored</div>
            </div>
          </div>

          <div class="alert alert-info" style="text-align:left;margin-bottom:var(--spacing-lg)">
            <strong>📋 Instructions:</strong>
            <ul style="margin:8px 0 0;padding-left:20px;font-size:0.85rem">
              <li>Select a challenge from the dropdown</li>
              <li>Write your solution in the editor</li>
              <li>Use "Run" to test against visible cases</li>
              <li>Use "Submit" to evaluate against all cases (including hidden)</li>
            </ul>
          </div>

          <button class="btn btn-primary btn-lg" id="start-coding-btn">
            ▶ Start Coding →
          </button>
        </div>
      </div>
    </div>
  `;

  container.querySelector('#start-coding-btn').onclick = onStart;
}
