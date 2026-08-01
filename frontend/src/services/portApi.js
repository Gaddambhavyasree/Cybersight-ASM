import api from './api'

const portApi = {
  list: (params = {}) => {
    const query = new URLSearchParams()
    if (params.page) query.set('page', params.page)
    if (params.per_page) query.set('per_page', params.per_page)
    if (params.asset_id) query.set('asset_id', params.asset_id)
    if (params.project_id) query.set('project_id', params.project_id)
    if (params.scan_id) query.set('scan_id', params.scan_id)
    if (params.hostname) query.set('hostname', params.hostname)
    if (params.ip) query.set('ip', params.ip)
    if (params.port) query.set('port', params.port)
    if (params.protocol) query.set('protocol', params.protocol)
    if (params.state) query.set('state', params.state)
    if (params.service) query.set('service', params.service)
    if (params.date_from) query.set('date_from', params.date_from)
    if (params.date_to) query.set('date_to', params.date_to)
    return api.get(`/api/ports?${query.toString()}`)
  },

  stats: (params = {}) => {
    const query = new URLSearchParams()
    if (params.project_id) query.set('project_id', params.project_id)
    return api.get(`/api/ports/stats?${query.toString()}`)
  },
}

export default portApi
