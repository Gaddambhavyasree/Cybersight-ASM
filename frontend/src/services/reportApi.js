import api from './api'
const reportApi = {
  list: (params = {}) => api.get('/api/reports', { params }),
  generate: (data) => api.post('/api/reports', data),
  get: (id) => api.get(`/api/reports/${id}`),
  remove: (id) => api.delete(`/api/reports/${id}`),
  pdf: (id) => api.get(`/api/reports/${id}/pdf`, { responseType: 'blob' }),
  json: (id) => api.get(`/api/reports/${id}/json`, { responseType: 'blob' }),
  aiSummary: (id) => api.post(`/api/reports/${id}/ai-summary`),
  ask: (id, question) => api.post(`/api/reports/${id}/ask`, { question }),
}
export default reportApi
