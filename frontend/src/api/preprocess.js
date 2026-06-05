import api from './index'

export const listScripts = () => api.get('/api/preprocess/scripts')
export const createScript = (data) => api.post('/api/preprocess/scripts', data)
export const deleteScript = (id) => api.delete(`/api/preprocess/scripts/${id}`)
export const listTasks = () => api.get('/api/preprocess/tasks')
export const createTask = (data) => api.post('/api/preprocess/tasks', data)
export const getTask = (id) => api.get(`/api/preprocess/tasks/${id}`)
export const getTaskResults = (taskId, params) => api.get(`/api/preprocess/tasks/${taskId}/results`, { params })
export const updateResult = (id, data) => api.put(`/api/preprocess/results/${id}`, data)
export const confirmResults = (data) => api.post('/api/preprocess/results/confirm', data)