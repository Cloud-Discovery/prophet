import apiClient from './client'

export interface ScanTask {
  id?: number
  name: string
  target: string
  nmap_args?: string
  status?: string
  progress?: number
  result_count?: number
}

export const scansApi = {
  createScanTask: (data: ScanTask) => apiClient.post('/scans', data),
  
  getScanTasks: (params?: { page?: number; per_page?: number; status?: string }) =>
    apiClient.get('/scans', { params }),
  
  getScanTask: (id: number) => apiClient.get(`/scans/${id}`),
  
  getScanResults: (id: number) => apiClient.get(`/scans/${id}/results`),
}

