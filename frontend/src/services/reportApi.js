import api from './api'
const reportApi = {
  list: (params = {}) => api.get('/api/reports', { params }),
  generate: (data) => api.post('/api/reports', data),
  get: (id) => api.get(`/api/reports/${id}`),
  remove: (id) => api.delete(`/api/reports/${id}`),
  pdf: (id) => api.get(`/api/reports/${id}/pdf`, { responseType: 'blob' }),
  json: (id) => api.get(`/api/reports/${id}/json`, { responseType: 'blob' }),
}
export default reportApi
