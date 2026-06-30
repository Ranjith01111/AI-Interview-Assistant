/* Step 1 — Resume Upload */
import { interview } from '../../api/index.js';
import { Toast } from '../../components/Toast.js';

export async function renderStep1(container, state, onNext, onSkip = null) {
  container.innerHTML = `
    <div class="step-container slide-up">
      <div class="card">
        <div class="card-header">
          <span>📄</span><h3>Upload Your Resume</h3>
        </div>
        <div class="card-body">
          <div class="upload-zone" id="upload-zone">
            <input type="file" id="file-input" accept=".pdf" />
            <span class="upload-icon">☁️</span>
            <div class="upload-title">Drop your PDF resume here</div>
            <div class="upload-subtitle">or click to browse — max 10 MB</div>
          </div>

          <div id="upload-progress" style="display:none" class="mt-lg">
            <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
              <span style="font-size:0.85rem;color:var(--text-secondary)" id="upload-status-text">Processing…</span>
            </div>
            <div class="progress-bar"><div class="progress-fill" id="upload-progress-fill" style="width:0%"></div></div>
          </div>

          <div id="upload-result" style="display:none" class="mt-lg">
            <div class="alert alert-success" style="margin-bottom:var(--spacing-md)">
              ✅ Resume processed successfully!
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--spacing-md);margin-bottom:var(--spacing-md)">
              <div class="kpi-card">
                <div class="kpi-label">Candidate</div>
                <div class="kpi-value" id="res-name" style="font-size:1.1rem">—</div>
              </div>
              <div class="kpi-card">
                <div class="kpi-label">Experience</div>
                <div class="kpi-value" id="res-exp" style="font-size:1.1rem">—</div>
              </div>
            </div>
            <div class="form-label" style="margin-bottom:8px">Detected Skills</div>
            <div class="skill-tags" id="skill-tags"></div>
          </div>
        </div>
        <div style="padding:var(--spacing-md) var(--spacing-lg);border-top:1px solid var(--border);display:flex;justify-content:${onSkip ? 'space-between' : 'flex-end'}">
          ${onSkip ? '<button class="btn btn-ghost" id="skip-btn" style="color:var(--text-muted)">Skip without Resume →</button>' : ''}
          <button class="btn btn-primary" id="next-btn" disabled>
            Next Step →
          </button>
        </div>
      </div>
    </div>
  `;

  const zone    = container.querySelector('#upload-zone');
  const input   = container.querySelector('#file-input');
  const progDiv = container.querySelector('#upload-progress');
  const progFill= container.querySelector('#upload-progress-fill');
  const statusTxt=container.querySelector('#upload-status-text');
  const result  = container.querySelector('#upload-result');
  const nextBtn = container.querySelector('#next-btn');

  zone.onclick = () => input.click();
  zone.ondragover = (e) => { e.preventDefault(); zone.classList.add('dragover'); };
  zone.ondragleave = () => zone.classList.remove('dragover');
  zone.ondrop = (e) => { e.preventDefault(); zone.classList.remove('dragover'); if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); };
  input.onchange = () => { if (input.files[0]) handleFile(input.files[0]); };

  async function handleFile(file) {
    if (!file.name.endsWith('.pdf')) { Toast.error('Only PDF files supported'); return; }
    if (file.size > 10 * 1024 * 1024) { Toast.error('File too large (max 10 MB)'); return; }

    zone.style.pointerEvents = 'none';
    progDiv.style.display = '';
    result.style.display = 'none';
    nextBtn.disabled = true;

    // Simulate progress
    let p = 0;
    const tick = setInterval(() => {
      p = Math.min(p + 10, 85);
      progFill.style.width = p + '%';
    }, 200);
    statusTxt.textContent = 'Parsing PDF and creating embeddings…';

    try {
      const data = await interview.uploadResume(file);
      clearInterval(tick);
      progFill.style.width = '100%';
      statusTxt.textContent = 'Done!';

      state.sessionId       = data.session_id;
      state.candidateName   = data.candidate_name;
      state.skillsDetected  = data.skills_detected || [];
      state.experienceYears = data.experience_years;

      // Show result
      container.querySelector('#res-name').textContent = data.candidate_name;
      const expYears = data.experience_years;
      container.querySelector('#res-exp').textContent = (!expYears || expYears === 0 || expYears === '0') ? 'Fresher' : `${expYears}+ years`;
      const tagsEl = container.querySelector('#skill-tags');
      tagsEl.innerHTML = (data.skills_detected || []).map(s => `<span class="skill-tag">${s}</span>`).join('');
      result.style.display = '';
      nextBtn.disabled = false;
      Toast.success('Resume uploaded!');
    } catch (err) {
      clearInterval(tick);
      progDiv.style.display = 'none';
      zone.style.pointerEvents = '';
      Toast.error(err.message, 'Upload Failed');
    }
  }

  nextBtn.onclick = () => onNext();
  if (onSkip) {
    const skipBtn = container.querySelector('#skip-btn');
    if (skipBtn) skipBtn.onclick = () => onSkip();
  }
}
