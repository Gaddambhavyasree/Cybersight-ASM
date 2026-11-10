import api from './api'
const threatApi={list:(p={})=>{const q=new URLSearchParams();Object.entries(p).forEach(([k,v])=>v!==''&&v!=null&&q.set(k,v));return api.get(`/api/threat-intelligence?${q.toString()}`)},stats:()=>api.get('/api/threat-intelligence/stats'),get:id=>api.get(`/api/threat-intelligence/${id}`)};export default threatApi
