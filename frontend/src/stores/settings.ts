import { defineStore } from 'pinia'

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    defaultPageSize: parseInt(localStorage.getItem('defaultPageSize') || '10', 10),
  }),
  
  getters: {
    getDefaultPageSize: (state) => state.defaultPageSize,
  },
  
  actions: {
    setDefaultPageSize(size: number) {
      this.defaultPageSize = size
      localStorage.setItem('defaultPageSize', size.toString())
    },
  },
})

