import apiClient from './client'

export interface CollectionTask {
  id: number
  scan_task_id?: number
  host_ids: number[]
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  concurrent_limit: number
  current_running: number
  completed_count: number
  failed_count: number
  total_count?: number
  error_message?: string
  created_by?: number
  created_at: string
  started_at?: string
  completed_at?: string
  task_type?: 'collection' | 'platform_sync'
  platform_id?: number
  platform_name?: string
}

export const collectionsApi = {
  getCollectionTasks: (params?: {
    page?: number
    per_page?: number
    status?: string
  }) => apiClient.get('/collections', { params }),
  
  getCollectionTask: (taskId: number) => apiClient.get(`/collections/${taskId}`),
  
  cancelCollectionTask: (id: number) => apiClient.post(`/collections/${id}/cancel`),
  
  retryCollectionTask: (id: number) => apiClient.post(`/collections/${id}/retry`),
  
  deleteCollectionTask: (id: number) => apiClient.delete(`/collections/${id}`),
  
  getCollectionResults: (id: number) => apiClient.get(`/collections/${id}/results`),
  
  exportCollectionResultsCSV: (id: number) =>
    apiClient.get(`/collections/${id}/export/csv`, { responseType: 'blob' }),
}

