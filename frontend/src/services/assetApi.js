import api from './api'

const assetApi = {
  list: (params = {}) => {
    const query = new URLSearchParams()
    if (params.page) query.set('page', params.page)
    if (params.per_page) query.set('per_page', params.per_page)
    if (params.search) query.set('search', params.search)
    if (params.source) query.set('source', params.source)
    if (params.status) query.set('status', params.status)
    if (params.project_id) query.set('project_id', params.project_id)
    return api.get(`/api/assets?${query.toString()}`)
  },

  stats: () => api.get('/api/assets/stats'),

  byProject: (projectId, params = {}) => {
    const query = new URLSearchParams()
    if (params.page) query.set('page', params.page)
    if (params.per_page) query.set('per_page', params.per_page)
    if (params.search) query.set('search', params.search)
    if (params.source) query.set('source', params.source)
    return api.get(`/api/assets/project/${projectId}?${query.toString()}`)
  },
}

export default assetApi
