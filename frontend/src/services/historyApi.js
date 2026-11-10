import api from './api'
const historyApi = {
  list: (params = {}) => api.get('/api/history', { params }),
  get: (id) => api.get(`/api/history/${id}`),
  compare: (previous_id, current_id) => api.get('/api/history/compare', { params: { previous_id, current_id } }),
  remove: (id) => api.delete(`/api/history/${id}`),
}
export default historyApi
