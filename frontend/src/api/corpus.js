import api from './index'

export const listTemplates = () => api.get('/api/corpus/templates')
export const createTemplate = (data) => api.post('/api/corpus/templates', data)
export const updateTemplate = (id, data) => api.put(`/api/corpus/templates/${id}`, data)
export const deleteTemplate = (id) => api.delete(`/api/corpus/templates/${id}`)
export const generateCorpus = (data) => api.post('/api/corpus/generate', data)
export const listRecords = (params) => api.get('/api/corpus/records', { params })
export const updateRecord = (id, data) => api.put(`/api/corpus/records/${id}`, data)
export const confirmRecords = (data) => api.post('/api/corpus/records/confirm', data)
export const exportCorpus = (data) => api.post('/api/corpus/export', data)