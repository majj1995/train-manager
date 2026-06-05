import api from './index'

export const listTemplates = () => api.get('/corpus/templates')
export const createTemplate = (data) => api.post('/corpus/templates', data)
export const updateTemplate = (id, data) => api.put(`/corpus/templates/${id}`, data)
export const deleteTemplate = (id) => api.delete(`/corpus/templates/${id}`)
export const generateCorpus = (data) => api.post('/corpus/generate', data)
export const listRecords = (params) => api.get('/corpus/records', { params })
export const updateRecord = (id, data) => api.put(`/corpus/records/${id}`, data)
export const confirmRecords = (data) => api.post('/corpus/records/confirm', data)
export const exportCorpus = (data) => api.post('/corpus/export', data)