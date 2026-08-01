import api from './api'

const riskApi = {
  list: (params = {}) => api.get('/api/risk-assessment', { params }),
  stats: (project_id) => api.get('/api/risk-assessment/stats', { params: project_id ? { project_id } : {} }),
  get: (id) => api.get(`/api/risk-assessment/${id}`),
}

export default riskApi
