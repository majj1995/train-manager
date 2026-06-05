import api from './index'

export const listGroups = () => api.get('/api/labels/groups')
export const createGroup = (data) => api.post('/api/labels/groups', data)
export const deleteGroup = (id) => api.delete(`/api/labels/groups/${id}`)
export const listLabelsByGroup = (groupId) => api.get(`/api/labels/groups/${groupId}/labels`)
export const createLabel = (groupId, data) => api.post(`/api/labels/groups/${groupId}/labels`, data)
export const deleteLabel = (id) => api.delete(`/api/labels/${id}`)
export const batchAddLabels = (data) => api.post('/api/labels/batch-add', data)
export const batchRemoveLabels = (data) => api.post('/api/labels/batch-remove', data)