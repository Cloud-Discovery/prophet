import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // 将 LogicFlow 相关库单独打包
          'logicflow': ['@logicflow/core', '@logicflow/extension'],
          // 将 Vue 核心库单独打包
          'vue-vendor': ['vue', 'vue-router', 'vue-i18n', 'pinia'],
          // 将 UI 组件库单独打包
          'ui-vendor': ['@headlessui/vue', '@heroicons/vue'],
          // 将工具库单独打包
          'utils': ['axios'],
        },
      },
    },
    // 提高 chunk 大小警告阈值到 1000KB（因为 LogicFlow 库本身就比较大）
    chunkSizeWarningLimit: 1000,
  },
})

