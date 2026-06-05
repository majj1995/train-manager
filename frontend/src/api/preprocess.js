import http from './index'

export const listScripts = (params) => http.get('/api/preprocess/scripts', { params })
export const createScript = (data) => http.post('/api/preprocess/scripts', data)
export const deleteScript = (id) => http.delete(`/api/preprocess/scripts/${id}`)
export const listTasks = (params) => http.get('/api/preprocess/tasks', { params })
export const createTask = (data) => http.post('/api/preprocess/tasks', data)
export const getTask = (id) => http.get(`/api/preprocess/tasks/${id}`)
export const getTaskResults = (taskId, params) => http.get(`/api/preprocess/tasks/${taskId}/results`, { params })
export const updateResult = (taskId, resultId, data) => http.put(`/api/preprocess/tasks/${taskId}/results/${resultId}`, data)
export const confirmResults = (taskId, data) => http.post(`/api/preprocess/tasks/${taskId}/results/confirm`, data)