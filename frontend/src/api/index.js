import { apiJSON, apiUpload } from './client.js';

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

  generateQuestions: (sessionId) =>
    apiJSON(`/interview/generate-questions/${sessionId}`, { method:'POST' }),

  startInterview: (sessionId) =>
    apiJSON(`/interview/start/${sessionId}`, { method:'POST' }),

  chat: (sessionId, message) =>
    apiJSON('/interview/chat', { method:'POST', body: JSON.stringify({ session_id: sessionId, message }) }),

  getSummary: (sessionId) => apiJSON(`/interview/summary/${sessionId}`),

  saveVoiceSession: (results) =>
    apiJSON('/interview/voice-session', { method:'POST', body: JSON.stringify(results) }),
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
};
