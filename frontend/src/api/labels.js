import http from './index'

export const listGroups = (params) => http.get('/api/labels/groups', { params })
export const createGroup = (data) => http.post('/api/labels/groups', data)
export const deleteGroup = (id) => http.delete(`/api/labels/groups/${id}`)
export const listLabelsByGroup = (groupId, params) => http.get(`/api/labels/groups/${groupId}/labels`, { params })
export const createLabel = (groupId, data) => http.post(`/api/labels/groups/${groupId}/labels`, data)
export const deleteLabel = (groupId, labelId) => http.delete(`/api/labels/groups/${groupId}/labels/${labelId}`)
export const batchAddLabels = (groupId, data) => http.post(`/api/labels/groups/${groupId}/labels/batch`, data)
export const batchRemoveLabels = (groupId, data) => http.post(`/api/labels/groups/${groupId}/labels/batch-remove`, data)