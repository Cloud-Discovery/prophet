<template>
  <div class="px-4 py-6 sm:px-0 relative">
    <div class="mb-6 flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 flex items-center">
          <HomeIcon class="h-7 w-7 mr-2 text-gray-700" />
          {{ $t('dashboard.title') }}
        </h1>
        <p class="mt-1 text-sm text-gray-500">{{ $t('dashboard.subtitle') }}</p>
      </div>
      <button
        @click="loadStats"
        :disabled="loading"
        class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        <ArrowPathIcon :class="{ 'animate-spin': loading }" class="h-4 w-4 mr-2" />
        {{ $t('common.refresh') }}
      </button>
    </div>
    
    <LoadingOverlay :loading="loading" :text="$t('common.loading')" />
    
    <transition
      enter-active-class="transition-opacity duration-300 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-show="!loading" class="space-y-6">
      <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <!-- 总设备数 -->
        <div class="bg-gradient-to-br from-blue-50 to-blue-100 overflow-hidden shadow rounded-lg border border-blue-200">
          <div class="p-5">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <p class="text-sm font-medium text-blue-600 mb-1">{{ $t('dashboard.totalHosts') }}</p>
                <p class="text-3xl font-bold text-blue-900">{{ stats.totalHosts }}</p>
                <p class="text-xs text-blue-600 mt-2">
                  <span v-if="stats.totalHosts > 0">
                    {{ $t('dashboard.physicalHosts') }}: {{ stats.physicalHosts || 0 }} | {{ $t('dashboard.virtualHosts') }}: {{ stats.virtualHosts || 0 }}
                  </span>
                  <span v-else>{{ $t('dashboard.noDevices') }}</span>
                </p>
              </div>
              <div class="flex-shrink-0">
                <ServerIcon class="h-12 w-12 text-blue-500 opacity-80" />
              </div>
            </div>
          </div>
        </div>
        
        <!-- 已采集设备 -->
        <div class="bg-gradient-to-br from-green-50 to-green-100 overflow-hidden shadow rounded-lg border border-green-200">
          <div class="p-5">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <p class="text-sm font-medium text-green-600 mb-1">{{ $t('dashboard.collectedHosts') }}</p>
                <p class="text-3xl font-bold text-green-900">{{ stats.collectedHosts }}</p>
                <p class="text-xs text-green-600 mt-2">
                  <span v-if="stats.totalHosts > 0">
                    {{ $t('dashboard.collectionRate') }}: {{ Math.round((stats.collectedHosts / stats.totalHosts) * 100) }}%
                  </span>
                  <span v-else>{{ $t('dashboard.noData') }}</span>
                </p>
              </div>
              <div class="flex-shrink-0">
                <CheckCircleIcon class="h-12 w-12 text-green-500 opacity-80" />
              </div>
            </div>
          </div>
        </div>
        
        <!-- 虚拟化平台 -->
        <div class="bg-gradient-to-br from-purple-50 to-purple-100 overflow-hidden shadow rounded-lg border border-purple-200">
          <div class="p-5">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <p class="text-sm font-medium text-purple-600 mb-1">{{ $t('dashboard.platforms') }}</p>
                <p class="text-3xl font-bold text-purple-900">{{ stats.platforms }}</p>
                <p class="text-xs text-purple-600 mt-2">
                  <span v-if="stats.platforms > 0">
                    {{ $t('dashboard.vmTotal') }}: {{ stats.totalVMs || 0 }}
                  </span>
                  <span v-else>{{ $t('dashboard.noPlatform') }}</span>
                </p>
              </div>
              <div class="flex-shrink-0">
                <CloudIcon class="h-12 w-12 text-purple-500 opacity-80" />
              </div>
            </div>
          </div>
        </div>
        
        <!-- 应用数量 -->
        <div class="bg-gradient-to-br from-orange-50 to-orange-100 overflow-hidden shadow rounded-lg border border-orange-200">
          <div class="p-5">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <p class="text-sm font-medium text-orange-600 mb-1">{{ $t('dashboard.applications') }}</p>
                <p class="text-3xl font-bold text-orange-900">{{ stats.applications }}</p>
                <p class="text-xs text-orange-600 mt-2">
                  <span v-if="stats.applications > 0">
                    {{ $t('dashboard.relatedHosts') }}: {{ stats.appHosts || 0 }}
                  </span>
                  <span v-else>{{ $t('dashboard.noApplications') }}</span>
                </p>
              </div>
              <div class="flex-shrink-0">
                <CubeIcon class="h-12 w-12 text-orange-500 opacity-80" />
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="mt-8">
        <h3 class="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <ClockIcon class="h-5 w-5 mr-2 text-gray-500" />
          {{ $t('dashboard.recentTasks') }}
        </h3>
        <div class="bg-white shadow overflow-hidden sm:rounded-md">
          <div v-if="recentTasks.length === 0" class="text-center py-8 text-gray-500">
            <ClockIcon class="h-12 w-12 mx-auto text-gray-300 mb-2" />
            <p>{{ $t('dashboard.noScanTasks') }}</p>
          </div>
          <ul v-else class="divide-y divide-gray-200">
            <li v-for="task in recentTasks" :key="task.id" class="px-4 py-4 sm:px-6 hover:bg-gray-50">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-medium text-gray-900">{{ task.name }}</p>
                  <p class="text-sm text-gray-500">{{ task.target }}</p>
                </div>
                <div class="flex items-center space-x-4">
                  <span class="px-2 py-1 text-xs font-medium rounded-full" :class="getStatusClass(task.status)">
                    {{ getStatusText(task.status) }}
                  </span>
                  <span class="text-sm text-gray-500">{{ task.progress || 0 }}%</span>
                </div>
              </div>
            </li>
          </ul>
        </div>
      </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { hostsApi } from '@/api/hosts'
import { scansApi } from '@/api/scans'
import { platformsApi } from '@/api/platforms'
import { applicationsApi } from '@/api/applications'
import { useToastStore } from '@/stores/toast'
import LoadingOverlay from '@/components/LoadingOverlay.vue'
import {
  HomeIcon,
  ServerIcon,
  CheckCircleIcon,
  CloudIcon,
  CubeIcon,
  ClockIcon,
  ArrowPathIcon,
} from '@heroicons/vue/24/outline'

const { t } = useI18n()
const toastStore = useToastStore()

const stats = ref({
  totalHosts: 0,
  collectedHosts: 0,
  platforms: 0,
  applications: 0,
  physicalHosts: 0,
  virtualHosts: 0,
  totalVMs: 0,
  appHosts: 0,
})

const recentTasks = ref<any[]>([])
const loading = ref(false)

const getStatusClass = (status: string) => {
  const classes: Record<string, string> = {
    completed: 'bg-green-100 text-green-800',
    running: 'bg-blue-100 text-blue-800',
    pending: 'bg-yellow-100 text-yellow-800',
    failed: 'bg-red-100 text-red-800',
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    completed: t('common.completed'),
    running: t('common.running'),
    pending: t('common.pending'),
    failed: t('common.failed'),
  }
  return texts[status] || status
}

const loadStats = async () => {
  loading.value = true
  try {
    // Optimize: Get hosts with pagination info only, don't fetch all hosts for count
    const [hostsRes, platformsRes, applicationsRes, scansRes] = await Promise.all([
      hostsApi.getHosts({ per_page: 1 }),
      platformsApi.getPlatforms(),
      applicationsApi.getApplications(),
      scansApi.getScanTasks({ per_page: 5 }),
    ])
    
    const hostsResponse: any = hostsRes
    stats.value.totalHosts = hostsResponse.pagination?.total || 0
    stats.value.platforms = platformsRes.data?.length || 0
    stats.value.applications = applicationsRes.data?.length || 0
    recentTasks.value = scansRes.data || []
    
    // Count collected hosts and other stats
    try {
      if (stats.value.totalHosts > 0 && stats.value.totalHosts <= 500) {
        const allHostsRes: any = await hostsApi.getHosts({ per_page: Math.min(stats.value.totalHosts, 500) })
        const allHosts = allHostsRes.data || []
        stats.value.collectedHosts = allHosts.filter((h: any) => h.cpu_cores || h.memory_total).length
        stats.value.physicalHosts = allHosts.filter((h: any) => h.is_physical).length
        stats.value.virtualHosts = allHosts.filter((h: any) => !h.is_physical).length
      } else {
        stats.value.collectedHosts = stats.value.totalHosts
      }
      
      // Get platform statistics
      if (stats.value.platforms > 0) {
        const platformsData = platformsRes.data || []
        let totalVMs = 0
        for (const platform of platformsData) {
          if (platform.id) {
            try {
              const detailRes: any = await platformsApi.getPlatform(platform.id)
              if (detailRes && detailRes.code === 200 && detailRes.data?.statistics) {
                totalVMs += detailRes.data.statistics.vm_count || 0
              }
            } catch (e) {
              // Ignore errors
            }
          }
        }
        stats.value.totalVMs = totalVMs
      }
      
      // Get application statistics
      if (stats.value.applications > 0) {
        const appsData = applicationsRes.data || []
        let appHosts = 0
        for (const app of appsData) {
          appHosts += app.host_count || 0
        }
        stats.value.appHosts = appHosts
      }
    } catch (error) {
      // Ignore errors for additional stats
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.message || error.message || t('messages.loadFailed')
    // Handle 429 specifically
    if (error.response?.status === 429) {
      toastStore.error(t('messages.requestTooFrequent'))
    } else {
      toastStore.error(errorMsg)
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>
