import { apiJSON, apiUpload, apiFetchLong } from './client.js';

export const auth = {
  login:  (email, password) =>
    apiJSON('/auth/login', { method:'POST', body: JSON.stringify({ email, password }) }),

  register: (name, email, password, role='candidate') =>
    apiJSON('/auth/register', { method:'POST', body: JSON.stringify({ name, email, password, role }) }),

  refresh: (refresh_token) =>
    apiJSON('/auth/refresh', { method:'POST', body: JSON.stringify({ refresh_token }) }),

  getMe: () => apiJSON('/auth/me'),

  listUsers: () => apiJSON('/auth/users'),

  deactivateUser: (userId) =>
    apiJSON(`/auth/users/${userId}/deactivate`, { method:'POST' }),
};

export const interview = {
  uploadResume: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return apiUpload('/resume/upload', fd);
  },

  generateQuestions: (sessionId, config = {}) =>
    apiJSON(`/interview/generate-questions/${sessionId}`, {
      method: 'POST',
      body: JSON.stringify({
        preset_id: config.preset_id || null,
        focus_categories: config.focus_categories || [],
        num_questions: config.num_questions || 10,
        difficulty: config.difficulty || null,
      }),
    }),

  createCustomSession: () =>
    apiJSON('/interview/setup-custom', { method: 'POST' }),

  startInterview: (sessionId) =>
    apiJSON(`/interview/start/${sessionId}`, { method:'POST' }),

  chat: (sessionId, message) =>
    apiFetchLong('/interview/chat', { method:'POST', body: JSON.stringify({ session_id: sessionId, message }) }),

  getSummary: (sessionId) => apiJSON(`/interview/summary/${sessionId}`),

  saveVoiceSession: (results) =>
    apiJSON('/interview/voice-session', { method:'POST', body: JSON.stringify(results) }),

  getPresets: () => apiJSON('/interview/presets'),
};

export const coding = {
  getChallenges: () => apiJSON('/coding/challenges'),

  getChallenge: (id) => apiJSON(`/coding/challenges/${id}`),

  runCode: (challengeId, language, code) =>
    apiJSON('/coding/run', { method:'POST', body: JSON.stringify({ challenge_id: challengeId, language, code }) }),

  submitCode: (sessionId, challengeId, language, code) =>
    apiJSON('/coding/submit', { method:'POST', body: JSON.stringify({ session_id: sessionId, challenge_id: challengeId, language, code }) }),

  getSubmissions: (sessionId) => apiJSON(`/coding/submissions/${sessionId}`),
};

export const leetcode = {
  search: (query = '', difficulty = null, tags = [], limit = 50) =>
    apiJSON('/leetcode/search', { method:'POST', body: JSON.stringify({ query, difficulty, tags, limit }) }),

  searchByNumber: (number) =>
    apiJSON('/leetcode/search', { method:'POST', body: JSON.stringify({ number, limit: 1 }) }),

  getProblem: (titleSlug) => apiJSON(`/leetcode/problem/${titleSlug}`),

  getDaily: () => apiJSON('/leetcode/daily'),

  importProblem: (titleSlug, customTestCases = null) =>
    apiJSON('/leetcode/import', { method:'POST', body: JSON.stringify({
      title_slug: titleSlug,
      custom_test_cases: customTestCases
    })}),

  getTags: () => apiJSON('/leetcode/tags'),
};

export const verbal = {
  start: (sessionId = null, resumeText = null) =>
    apiJSON('/verbal/start', { method:'POST', body: JSON.stringify({ session_id: sessionId, resume_text: resumeText }) }),

  respond: (verbalSessionId, candidateMessage) =>
    apiFetchLong('/verbal/respond', { method:'POST', body: JSON.stringify({ verbal_session_id: verbalSessionId, candidate_message: candidateMessage }) }),

  end: (verbalSessionId) =>
    apiFetchLong('/verbal/end', { method:'POST', body: JSON.stringify({ verbal_session_id: verbalSessionId }) }),
};

export const proctor = {
  analyzeFrame: (sessionId, imageData) =>
    apiJSON('/proctor/analyze-frame', { method:'POST', body: JSON.stringify({ session_id: sessionId, image_data: imageData }) }),

  logEvent: (sessionId, event_type, details = {}) =>
    apiJSON('/proctor/log-event', { method:'POST', body: JSON.stringify({ session_id: sessionId, event_type, details }) }),

  getSessionReport: (sessionId) => apiJSON(`/proctor/session-report/${sessionId}`),
};

export const analytics = {
  overview:   () => apiJSON('/analytics/overview'),
  history:    () => apiJSON('/analytics/history'),
  skills:     () => apiJSON('/analytics/skills'),
  strengths:  () => apiJSON('/analytics/strengths-weaknesses'),
  violations: () => apiJSON('/analytics/proctor-violations'),
  trend:      () => apiJSON('/analytics/performance-trend'),
  candidateDetail: (sessionId) => apiJSON(`/analytics/candidate/${sessionId}`),
};
