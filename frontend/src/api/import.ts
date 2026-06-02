import apiClient from './client'

export const importApi = {
  importHostsFromCSV: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/import/csv/hosts', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
  getHostImportMetadata: () => apiClient.get('/import/csv/hosts/metadata'),
}

