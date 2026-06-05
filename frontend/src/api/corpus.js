import http from './index'

export const listTemplates = (params) => http.get('/api/corpus/templates', { params })
export const createTemplate = (data) => http.post('/api/corpus/templates', data)
export const updateTemplate = (id, data) => http.put(`/api/corpus/templates/${id}`, data)
export const deleteTemplate = (id) => http.delete(`/api/corpus/templates/${id}`)
export const generateCorpus = (templateId, data) => http.post(`/api/corpus/templates/${templateId}/generate`, data)
export const listRecords = (templateId, params) => http.get(`/api/corpus/templates/${templateId}/records`, { params })
export const updateRecord = (templateId, recordId, data) => http.put(`/api/corpus/templates/${templateId}/records/${recordId}`, data)
export const confirmRecords = (templateId, data) => http.post(`/api/corpus/templates/${templateId}/records/confirm`, data)
export const exportCorpus = (templateId, params) => http.get(`/api/corpus/templates/${templateId}/export`, { params, responseType: 'blob' })