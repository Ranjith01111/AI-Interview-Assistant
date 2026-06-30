/* Session Setup — Interview Mode Selection + Topic Focus + Timer Config */
import { Toast } from '../../components/Toast.js';

// ── Interview Presets (mirrors backend/nlp_engine/interview_presets.py) ──
const PRESETS = [
  {
    id: 'faang_hard',
    name: 'FAANG Style',
    icon: '🏢',
    description: 'Heavy DSA + System Design. Google/Meta level.',
    difficulty: 'hard',
    num_questions: 8,
    timer_seconds: 90,
    session_time_minutes: 20,
    tags: ['Google', 'Meta', 'Amazon'],
    distribution: { data_structures: 0.35, system_design: 0.30, behavioral: 0.15, python: 0.10, api_design: 0.10 },
  },
  {
    id: 'startup_practical',
    name: 'Startup Style',
    icon: '🚀',
    description: 'Practical full-stack. Fast-paced, real-world.',
    difficulty: 'medium',
    num_questions: 7,
    timer_seconds: 120,
    session_time_minutes: 20,
    tags: ['Startup', 'Full-Stack'],
    distribution: { system_design: 0.30, python: 0.20, javascript: 0.15, behavioral: 0.20, api_design: 0.15 },
  },
  {
    id: 'fresher_friendly',
    name: 'Fresher Friendly',
    icon: '🎓',
    description: 'Easy + behavioral. No timer pressure.',
    difficulty: 'easy',
    num_questions: 6,
    timer_seconds: null,
    session_time_minutes: 30,
    tags: ['Entry-Level', 'Campus'],
    distribution: { behavioral: 0.40, python: 0.20, data_structures: 0.20, sql: 0.10, git: 0.10 },
  },
  {
    id: 'amazon_lp',
    name: 'Amazon LP',
    icon: '📦',
    description: 'Leadership Principles + STAR method.',
    difficulty: 'medium',
    num_questions: 8,
    timer_seconds: 120,
    session_time_minutes: 25,
    tags: ['Amazon', 'Leadership'],
    distribution: { behavioral: 0.50, system_design: 0.25, data_structures: 0.15, api_design: 0.10 },
  },
  {
    id: 'frontend_specialist',
    name: 'Frontend Expert',
    icon: '🎨',
    description: 'React + JS deep-dive with UI design.',
    difficulty: 'medium',
    num_questions: 8,
    timer_seconds: 90,
    session_time_minutes: 20,
    tags: ['Frontend', 'React'],
    distribution: { react: 0.35, javascript: 0.30, system_design: 0.15, behavioral: 0.10, testing: 0.10 },
  },
  {
    id: 'backend_engineer',
    name: 'Backend Engineer',
    icon: '⚙️',
    description: 'APIs, databases, system design, DevOps.',
    difficulty: 'medium',
    num_questions: 8,
    timer_seconds: 90,
    session_time_minutes: 20,
    tags: ['Backend', 'APIs'],
    distribution: { python: 0.20, sql: 0.20, system_design: 0.25, docker: 0.15, api_design: 0.10, security: 0.10 },
  },
  {
    id: 'quick_practice',
    name: 'Quick Practice',
    icon: '⚡',
    description: '5 questions, 60s each. Daily warmup.',
    difficulty: 'medium',
    num_questions: 5,
    timer_seconds: 60,
    session_time_minutes: 10,
    tags: ['Quick', 'Daily'],
    distribution: { python: 0.20, data_structures: 0.20, system_design: 0.20, behavioral: 0.20, javascript: 0.20 },
  },
];

// All available categories for topic focus
const ALL_CATEGORIES = [
  { id: 'python', label: 'Python', icon: '🐍' },
  { id: 'javascript', label: 'JavaScript', icon: '🟨' },
  { id: 'react', label: 'React', icon: '⚛️' },
  { id: 'sql', label: 'SQL', icon: '🗄️' },
  { id: 'system_design', label: 'System Design', icon: '🏗️' },
  { id: 'data_structures', label: 'DSA', icon: '🌳' },
  { id: 'aws', label: 'AWS/Cloud', icon: '☁️' },
  { id: 'docker', label: 'Docker/DevOps', icon: '🐳' },
  { id: 'machine_learning', label: 'ML/AI', icon: '🤖' },
  { id: 'api_design', label: 'API Design', icon: '🔗' },
  { id: 'git', label: 'Git', icon: '📂' },
  { id: 'testing', label: 'Testing', icon: '🧪' },
  { id: 'security', label: 'Security', icon: '🔒' },
  { id: 'behavioral', label: 'Behavioral/HR', icon: '💬' },
];

const TIMER_OPTIONS = [
  { value: 0, label: 'No Timer', icon: '♾️' },
  { value: 30, label: '30 sec', icon: '⚡' },
  { value: 60, label: '60 sec', icon: '⏱️' },
  { value: 90, label: '90 sec', icon: '⏳' },
  { value: 120, label: '2 min', icon: '🕐' },
];

const SESSION_TIME_OPTIONS = [
  { value: 10, label: '10 min', icon: '⚡' },
  { value: 15, label: '15 min', icon: '⏱️' },
  { value: 20, label: '20 min', icon: '⏳' },
  { value: 25, label: '25 min', icon: '🕐' },
  { value: 30, label: '30 min', icon: '🕑' },
  { value: 45, label: '45 min', icon: '🕒' },
];


export async function renderSessionSetup(container, state, onNext) {
  // Detect skills from resume for highlighting relevant categories
  const detectedSkills = (state.skillsDetected || []).map(s => s.toLowerCase());
  const detectedCategories = _mapSkillsToCategories(detectedSkills);

  container.innerHTML = `
    <div class="step-container slide-up" style="max-width:950px">
      <div class="card">
        <div class="card-header">
          <span>🎯</span><h3>Configure Your Interview</h3>
        </div>
        <div class="card-body" style="padding:var(--spacing-lg)">

          <!-- Section 1: Interview Mode Presets -->
          <div class="setup-section">
            <div class="setup-section-header">
              <h4>📋 Choose Interview Mode</h4>
              <span class="setup-hint">Select a preset or customize below</span>
            </div>
            <div class="preset-grid" id="preset-grid"></div>
          </div>

          <!-- Section 2: Topic Focus (Category Picker) -->
          <div class="setup-section" style="margin-top:var(--spacing-xl)">
            <div class="setup-section-header">
              <h4>🎯 Focus Topics</h4>
              <span class="setup-hint">Pick categories to focus on (or use preset defaults)</span>
            </div>
            <div class="category-chips" id="category-chips"></div>
            <div class="detected-hint" id="detected-hint" style="display:none">
              <span>✨ Highlighted categories match your resume skills</span>
            </div>
          </div>

          <!-- Section 3: Timer Configuration -->
          <div class="setup-section" style="margin-top:var(--spacing-xl)">
            <div class="setup-section-header">
              <h4>⏱️ Per-Question Timer</h4>
              <span class="setup-hint">Add time pressure for realistic practice</span>
            </div>
            <div class="timer-options" id="timer-options"></div>
          </div>

          <!-- Section 4: Session Duration -->
          <div class="setup-section" style="margin-top:var(--spacing-xl)">
            <div class="setup-section-header">
              <h4>⏰ Session Duration</h4>
              <span class="setup-hint">Total interview time limit — questions keep coming until timer ends</span>
            </div>
            <div class="timer-options" id="session-time-options"></div>
          </div>

          <!-- Summary Bar -->
          <div class="setup-summary" id="setup-summary" style="margin-top:var(--spacing-xl)">
            <div class="summary-item">
              <span class="summary-label">Mode</span>
              <span class="summary-value" id="sum-mode">Custom</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">Difficulty</span>
              <span class="summary-value" id="sum-difficulty">Medium</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">Timer</span>
              <span class="summary-value" id="sum-timer">Off</span>
            </div>
          </div>

        </div>
        <div style="padding:var(--spacing-md) var(--spacing-lg);border-top:1px solid var(--border);display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:0.8rem;color:var(--text-muted)">💡 Settings affect question generation</span>
          <button class="btn btn-primary" id="start-btn">
            Generate Questions →
          </button>
        </div>
      </div>
    </div>
  `;

  // ── State ──
  let selectedPreset = null;
  let selectedCategories = new Set(detectedCategories);
  let selectedTimer = 0; // 0 = no timer
  let numQuestions = 10;
  let selectedSessionTime = 20; // default 20 minutes
  let difficulty = 'medium';

  // ── Render Preset Cards ──
  const presetGrid = container.querySelector('#preset-grid');
  PRESETS.forEach(preset => {
    const card = document.createElement('div');
    card.className = 'preset-card';
    card.dataset.presetId = preset.id;
    card.innerHTML = `
      <div class="preset-icon">${preset.icon}</div>
      <div class="preset-info">
        <div class="preset-name">${preset.name}</div>
        <div class="preset-desc">${preset.description}</div>
        <div class="preset-tags">${preset.tags.map(t => `<span class="preset-tag">${t}</span>`).join('')}</div>
      </div>
      <div class="preset-meta">
        <span class="preset-meta-item">${preset.session_time_minutes}min</span>
        ${preset.timer_seconds ? `<span class="preset-meta-item">${preset.timer_seconds}s</span>` : '<span class="preset-meta-item">No timer</span>'}
      </div>
    `;
    card.onclick = () => selectPreset(preset);
    presetGrid.appendChild(card);
  });

  // ── Render Category Chips ──
  const chipsEl = container.querySelector('#category-chips');
  ALL_CATEGORIES.forEach(cat => {
    const chip = document.createElement('button');
    chip.className = `category-chip ${selectedCategories.has(cat.id) ? 'active' : ''} ${detectedCategories.includes(cat.id) ? 'detected' : ''}`;
    chip.dataset.catId = cat.id;
    chip.innerHTML = `<span class="chip-icon">${cat.icon}</span><span>${cat.label}</span>`;
    chip.onclick = () => toggleCategory(cat.id, chip);
    chipsEl.appendChild(chip);
  });

  if (detectedCategories.length > 0) {
    container.querySelector('#detected-hint').style.display = '';
  }

  // ── Render Timer Options ──
  const timerEl = container.querySelector('#timer-options');
  TIMER_OPTIONS.forEach(opt => {
    const btn = document.createElement('button');
    btn.className = `timer-option-btn ${opt.value === selectedTimer ? 'active' : ''}`;
    btn.dataset.value = opt.value;
    btn.innerHTML = `<span class="timer-opt-icon">${opt.icon}</span><span>${opt.label}</span>`;
    btn.onclick = () => selectTimer(opt.value);
    timerEl.appendChild(btn);
  });

  // ── Render Session Time Options ──
  const sessionTimeEl = container.querySelector('#session-time-options');
  SESSION_TIME_OPTIONS.forEach(opt => {
    const btn = document.createElement('button');
    btn.className = `timer-option-btn ${opt.value === selectedSessionTime ? 'active' : ''}`;
    btn.dataset.value = opt.value;
    btn.innerHTML = `<span class="timer-opt-icon">${opt.icon}</span><span>${opt.label}</span>`;
    btn.onclick = () => selectSessionTime(opt.value);
    sessionTimeEl.appendChild(btn);
  });

  // ── Interactions ──
  function selectPreset(preset) {
    selectedPreset = preset;
    numQuestions = preset.num_questions;
    difficulty = preset.difficulty;
    selectedTimer = preset.timer_seconds || 0;
    selectedSessionTime = preset.session_time_minutes || 20;
    selectedCategories = new Set(Object.keys(preset.distribution));

    // Update UI
    presetGrid.querySelectorAll('.preset-card').forEach(c => c.classList.remove('selected'));
    presetGrid.querySelector(`[data-preset-id="${preset.id}"]`).classList.add('selected');

    // Update chips
    chipsEl.querySelectorAll('.category-chip').forEach(chip => {
      chip.classList.toggle('active', selectedCategories.has(chip.dataset.catId));
    });

    // Update timer
    timerEl.querySelectorAll('.timer-option-btn').forEach(btn => {
      btn.classList.toggle('active', parseInt(btn.dataset.value) === selectedTimer);
    });

    // Update session time
    sessionTimeEl.querySelectorAll('.timer-option-btn').forEach(btn => {
      btn.classList.toggle('active', parseInt(btn.dataset.value) === selectedSessionTime);
    });

    updateSummary();
    Toast.success(`${preset.name} selected!`);
  }

  function toggleCategory(catId, chipEl) {
    if (selectedCategories.has(catId)) {
      selectedCategories.delete(catId);
      chipEl.classList.remove('active');
    } else {
      selectedCategories.add(catId);
      chipEl.classList.add('active');
    }
    // If user customizes categories, clear preset selection
    selectedPreset = null;
    presetGrid.querySelectorAll('.preset-card').forEach(c => c.classList.remove('selected'));
    updateSummary();
  }

  function selectTimer(value) {
    selectedTimer = value;
    timerEl.querySelectorAll('.timer-option-btn').forEach(btn => {
      btn.classList.toggle('active', parseInt(btn.dataset.value) === value);
    });
    updateSummary();
  }

  function selectSessionTime(value) {
    selectedSessionTime = value;
    sessionTimeEl.querySelectorAll('.timer-option-btn').forEach(btn => {
      btn.classList.toggle('active', parseInt(btn.dataset.value) === value);
    });
    updateSummary();
  }

  function updateSummary() {
    container.querySelector('#sum-mode').textContent = selectedPreset ? selectedPreset.name : 'Custom';
    container.querySelector('#sum-difficulty').textContent = difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
    const timerLabel = selectedTimer ? `${selectedTimer}s/Q` : 'Off';
    container.querySelector('#sum-timer').textContent = `${selectedSessionTime}min | ${timerLabel}`;
  }

  updateSummary();

  // ── Start Button ──
  container.querySelector('#start-btn').onclick = () => {
    // Save settings to state
    state.interviewConfig = {
      preset_id: selectedPreset?.id || null,
      focus_categories: Array.from(selectedCategories),
      timer_seconds: selectedTimer,
      session_time_minutes: selectedSessionTime,
      num_questions: numQuestions,
      difficulty: difficulty,
    };
    onNext();
  };
}


// ── Helper: Map skill strings to category IDs ──
function _mapSkillsToCategories(skills) {
  const map = {
    python: 'python', django: 'python', flask: 'python', fastapi: 'python',
    javascript: 'javascript', typescript: 'javascript', nodejs: 'javascript', 'node.js': 'javascript',
    react: 'react', 'react.js': 'react', nextjs: 'react', redux: 'react',
    sql: 'sql', postgresql: 'sql', mysql: 'sql', mongodb: 'sql',
    aws: 'aws', azure: 'aws', gcp: 'aws', lambda: 'aws', s3: 'aws', ec2: 'aws',
    docker: 'docker', kubernetes: 'docker', 'ci/cd': 'docker', jenkins: 'docker',
    'machine learning': 'machine_learning', tensorflow: 'machine_learning', pytorch: 'machine_learning',
    'system design': 'system_design', microservices: 'system_design', architecture: 'system_design',
    git: 'git', github: 'git',
    testing: 'testing', jest: 'testing', pytest: 'testing',
    security: 'security', oauth: 'security', jwt: 'security',
    rest: 'api_design', graphql: 'api_design', api: 'api_design',
    'data structures': 'data_structures', algorithms: 'data_structures', dsa: 'data_structures',
  };

  const result = new Set();
  skills.forEach(skill => {
    const lower = skill.toLowerCase().trim();
    if (map[lower]) result.add(map[lower]);
    // Partial match
    Object.entries(map).forEach(([key, cat]) => {
      if (lower.includes(key) || key.includes(lower)) result.add(cat);
    });
  });
  return Array.from(result);
}
