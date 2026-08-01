import api from './api'

const scanApi = {
  start: (data) => api.post('/api/scans/start', data),

  list: (params = {}) => {
    const query = new URLSearchParams()
    if (params.page) query.set('page', params.page)
    if (params.per_page) query.set('per_page', params.per_page)
    if (params.search) query.set('search', params.search)
    if (params.status) query.set('status', params.status)
    if (params.project_id) query.set('project_id', params.project_id)
    return api.get(`/api/scans?${query.toString()}`)
  },

  get: (id) => api.get(`/api/scans/${id}`),

  cancel: (id) => api.patch(`/api/scans/${id}/cancel`),

  delete: (id) => api.delete(`/api/scans/${id}`),
}

export default scanApi
