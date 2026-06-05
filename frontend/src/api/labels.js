import api from './index'

export const listGroups = () => api.get('/labels/groups')
export const createGroup = (data) => api.post('/labels/groups', data)
export const deleteGroup = (id) => api.delete(`/labels/groups/${id}`)
export const listLabelsByGroup = (groupId) => api.get(`/labels/groups/${groupId}/labels`)
export const createLabel = (groupId, data) => api.post(`/labels/groups/${groupId}/labels`, data)
export const deleteLabel = (id) => api.delete(`/labels/${id}`)
export const batchAddLabels = (data) => api.post('/labels/batch-add', data)
export const batchRemoveLabels = (data) => api.post('/labels/batch-remove', data)