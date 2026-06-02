import apiClient from './client'

export interface Host {
  id?: number
  hostname?: string
  ip: string
  mac?: string
  vendor?: string
  os_type?: string
  os_version?: string
  distribution?: string
  cpu_info?: string
  cpu_cores?: number
  memory_total?: number
  memory_free?: number
  disk_count?: number
  disk_total_size?: number
  network_count?: number
  device_type?: string
  is_physical?: boolean
  virtualization_platform_id?: number
  collection_status?: string
  source?: string
  error_message?: string
  tags?: Array<{ id: number; name: string; color?: string }>
}

export interface HostCredential {
  username: string
  password?: string
  ssh_port?: number
  key_path?: string
}

export const hostsApi = {
  getHosts: (params?: {
    page?: number
    per_page?: number
    search?: string
    search_field?: string
    os_type?: string
    device_type?: string
    is_physical?: string
    platform_id?: number
    tag_id?: number
    collection_status?: string
    source?: string
  }) => apiClient.get('/hosts', { params }),
  
  getHost: (id: number) => apiClient.get(`/hosts/${id}`),
  
  createHost: (data: Host) => apiClient.post('/hosts', data),
  
  updateHost: (id: number, data: Partial<Host>) => apiClient.put(`/hosts/${id}`, data),
  
  deleteHost: (id: number) => apiClient.delete(`/hosts/${id}`),
  
  batchDeleteHosts: (hostIds: number[]) => apiClient.post('/hosts/batch/delete', { host_ids: hostIds }),
  
  exportHostsExcel: (payload: any) =>
    apiClient.post('/hosts/export/excel', payload, { responseType: 'blob' }),
  
  getExportTemplates: () => apiClient.get('/hosts/export/templates'),

  batchCreateHosts: (hosts: Host[]) => apiClient.post('/hosts/batch', { hosts }),
  
  setCredentials: (id: number, credentials: HostCredential) =>
    apiClient.post(`/hosts/${id}/credentials`, credentials),
  
  getCredentials: (id: number) => apiClient.get(`/hosts/${id}/credentials`),
  
  batchCollect: (host_ids: number[], concurrent_limit?: number) =>
    apiClient.post('/hosts/batch/collect', { host_ids, concurrent_limit }),
  
  getHostDetails: (id: number) => apiClient.get(`/hosts/${id}/details`),
  
  getRelationships: (id: number) => apiClient.get(`/hosts/${id}/relationships`),
  
  batchUpdateHosts: (hosts: Array<Partial<Host> & { id: number }>) =>
    apiClient.post('/hosts/batch/update', { hosts }),
  
  exportHostsCSV: (params?: Record<string, any>) =>
    apiClient.get('/hosts/export/csv', { params, responseType: 'blob' }),
  
  batchUpdateCredentials: (host_ids: number[], credentials: HostCredential) =>
    apiClient.post('/hosts/batch/credentials', { host_ids, credentials }),
  
  getHostsTree: () => apiClient.get('/hosts/tree'),
}

