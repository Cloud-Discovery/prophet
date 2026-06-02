<template>
  <div class="px-4 py-6 sm:px-0">
    <div class="mb-4 flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 flex items-center">
          <CpuChipIcon class="h-7 w-7 mr-2 text-gray-700" />
          {{ $t('collections.title') }}
        </h1>
        <p class="mt-1 text-sm text-gray-500">{{ $t('collections.subtitle') }}</p>
      </div>
      <button
        @click="loadTasks(1)"
        :disabled="loading"
        class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        <ArrowPathIcon :class="{ 'animate-spin': loading }" class="h-4 w-4 mr-2" />
        {{ $t('common.refresh') }}
      </button>
    </div>
    
    <!-- Task List -->
    <div class="bg-white shadow overflow-hidden sm:rounded-md mb-6 relative">
      <LoadingOverlay :loading="loading" :text="$t('common.loading')" />
      <div class="overflow-x-auto max-h-[calc(100vh-300px)] overflow-y-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50 sticky top-0 z-20">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('collections.taskId') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('collections.taskType') }}</th>
              <th class="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap w-28">{{ $t('common.status') }}</th>
              <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap w-40">{{ $t('scans.progress') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('collections.completed') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('collections.failed') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('collections.concurrent') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('scans.createdAt') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap sticky right-0 bg-gray-50 z-10">{{ $t('common.operation') }}</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-if="!loading && tasks.length === 0" class="text-center py-8">
              <td colspan="9" class="px-4 py-4 text-gray-500">
                <CpuChipIcon class="h-12 w-12 mx-auto text-gray-300 mb-2" />
                <p>{{ $t('collections.noTasks') }}</p>
              </td>
            </tr>
            <tr 
              v-else 
              v-for="task in tasks" 
              :key="task.id"
              class="hover:bg-gray-50 cursor-pointer transition-colors"
              :class="{ 'bg-blue-50 hover:bg-blue-100': selectedTaskId === task.id }"
              @click="selectedTaskId = task.id"
            >
                  <td class="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900">#{{ task.id }}</td>
                  <td class="px-4 py-4 whitespace-nowrap text-sm">
                    <span v-if="task.task_type === 'platform_sync'" class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-purple-100 text-purple-800">
                      <CloudIcon class="h-3 w-3 mr-1" />
                      {{ $t('collections.platformSync') }}
                      <span v-if="task.platform_name" class="ml-1">({{ task.platform_name }})</span>
                    </span>
                    <span v-else class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
                      <CpuChipIcon class="h-3 w-3 mr-1" />
                      {{ $t('collections.collection') }}
                    </span>
                  </td>
                  <td class="px-2 py-4 text-sm w-28">
                    <div class="flex flex-col">
                      <span
                        :class="getStatusClass(task.status)"
                        class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                      >
                        <component
                          :is="getStatusIcon(task.status)"
                          class="h-3.5 w-3.5 mr-1 flex-shrink-0"
                        />
                        <span class="truncate">{{ getStatusText(task.status) }}</span>
                      </span>
                      <span v-if="task.status === 'failed' && task.error_message" class="mt-1 text-xs text-red-600 truncate" :title="task.error_message">
                        {{ task.error_message.split('\n')[0].substring(0, 30) }}{{ task.error_message.split('\n')[0].length > 30 ? '...' : '' }}
                      </span>
                    </div>
                  </td>
              <td class="px-3 py-4 text-sm w-40">
                <div class="flex items-center gap-2">
                  <div class="flex-1 bg-gray-200 rounded-full h-2.5 min-w-20">
                    <div
                      class="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                      :style="{ width: `${task.progress || 0}%` }"
                    ></div>
                  </div>
                  <span class="text-xs font-medium text-gray-900 whitespace-nowrap">{{ task.progress || 0 }}%</span>
                </div>
              </td>
              <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-500">{{ task.completed_count || 0 }}</td>
              <td class="px-4 py-4 whitespace-nowrap text-sm text-red-600">{{ task.failed_count || 0 }}</td>
              <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-500">{{ task.concurrent_limit || 5 }}</td>
              <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatDate(task.created_at) }}</td>
              <td class="px-4 py-4 whitespace-nowrap text-sm font-medium sticky right-0 bg-white z-10 transition-colors"
                  :class="{ 'bg-blue-50 hover:bg-blue-100': selectedTaskId === task.id }"
                  @click.stop
              >
                <div class="flex items-center space-x-1">
                  <button
                    @click="viewTaskDetails(task.id)"
                    class="text-blue-600 hover:text-blue-900 p-1 rounded hover:bg-blue-50"
                    :title="$t('collections.viewDetails')"
                  >
                    <EyeIcon class="h-5 w-5" />
                  </button>
                  <button
                    v-if="task.status === 'pending' || task.status === 'running'"
                    @click.stop="cancelTask(task.id)"
                    class="text-orange-600 hover:text-orange-900 p-1 rounded hover:bg-orange-50"
                    :title="$t('collections.cancel')"
                  >
                    <XCircleIcon class="h-5 w-5" />
                  </button>
                  <button
                    v-if="task.status === 'failed'"
                    @click.stop="retryTask(task.id)"
                    class="text-green-600 hover:text-green-900 p-1 rounded hover:bg-green-50"
                    :title="$t('collections.retry')"
                  >
                    <ArrowPathIcon class="h-5 w-5" />
                  </button>
                  <button
                    v-if="task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled'"
                    @click.stop="exportTaskResults(task.id)"
                    class="text-gray-600 hover:text-gray-900 p-1 rounded hover:bg-gray-50"
                    :title="$t('collections.export')"
                  >
                    <ArrowDownTrayIcon class="h-5 w-5" />
                  </button>
                  <button
                    v-if="task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled'"
                    @click.stop="deleteTask(task.id)"
                    class="text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50"
                    :title="$t('common.delete')"
                  >
                    <TrashIcon class="h-5 w-5" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div v-if="pagination && pagination.total > 0" class="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
        <div class="flex items-center space-x-4">
          <div class="flex items-center space-x-2">
            <label class="text-sm text-gray-700">{{ $t('common.perPage') }}:</label>
            <select
              v-model.number="perPage"
              @change="loadTasks(1)"
              class="px-2 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
          <p class="text-sm text-gray-700">
            {{ $t('common.page') }} <span class="font-medium">{{ (pagination.page - 1) * pagination.per_page + 1 }}</span>
            {{ $t('common.of') }} <span class="font-medium">{{ Math.min(pagination.page * pagination.per_page, pagination.total) }}</span>
            {{ $t('common.total') }} <span class="font-medium">{{ pagination.total }}</span> {{ $t('common.items') }}
          </p>
        </div>
        <div class="flex items-center space-x-2">
          <button
            @click="loadTasks(pagination.page - 1)"
            :disabled="pagination.page <= 1"
            class="relative inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ $t('common.previous') }}
          </button>
          <span class="text-sm text-gray-700">
            {{ $t('common.page') }} {{ pagination.page }} {{ $t('common.of') }} {{ pagination.pages }}
          </span>
          <button
            @click="loadTasks(pagination.page + 1)"
            :disabled="pagination.page >= pagination.pages"
            class="relative inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ $t('common.next') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Task Details Modal -->
    <Modal :open="showDetailModal" @close="closeDetailModal" :title="$t('collections.taskDetails')" max-width="6xl">
      <div v-if="taskDetail" class="space-y-6">
        <!-- Task Info -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm font-medium text-gray-500">{{ $t('collections.taskId') }}</label>
            <p class="mt-1 text-sm text-gray-900">#{{ taskDetail.id }}</p>
          </div>
          <div>
            <label class="text-sm font-medium text-gray-500">{{ $t('common.status') }}</label>
            <p class="mt-1">
              <span
                :class="getStatusClass(taskDetail.status)"
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
              >
                <component
                  :is="getStatusIcon(taskDetail.status)"
                  class="h-3.5 w-3.5 mr-1"
                />
                {{ getStatusText(taskDetail.status) }}
              </span>
            </p>
          </div>
          <div>
            <label class="text-sm font-medium text-gray-500">{{ $t('scans.progress') }}</label>
            <div class="mt-1 flex items-center">
              <div class="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                <div
                  class="bg-blue-600 h-2 rounded-full transition-all"
                  :style="{ width: `${taskDetail.progress || 0}%` }"
                ></div>
              </div>
              <span class="text-sm font-medium text-gray-900">{{ taskDetail.progress || 0 }}%</span>
            </div>
            <p class="mt-1 text-xs text-gray-500">
              {{ (taskDetail.completed_count || 0) + (taskDetail.failed_count || 0) }} / {{ taskDetail.total_count || 0 }} {{ $t('collections.completed') }}
            </p>
          </div>
          <div>
            <label class="text-sm font-medium text-gray-500">{{ $t('collections.concurrent') }}</label>
            <p class="mt-1 text-sm text-gray-900">{{ taskDetail.concurrent_limit || 5 }}</p>
          </div>
        </div>
        
        <!-- Error Message (if failed) -->
        <div v-if="taskDetail.status === 'failed' && taskDetail.error_message" class="bg-red-50 border border-red-200 rounded-lg p-4">
          <div class="flex items-start">
            <XCircleIcon class="h-5 w-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-medium text-red-800 mb-2">{{ $t('collections.errorMessage') }}</h4>
              <pre class="text-xs text-red-700 whitespace-pre-wrap break-words overflow-x-auto">{{ taskDetail.error_message }}</pre>
            </div>
          </div>
        </div>
        
        <!-- Statistics -->
        <div class="grid grid-cols-4 gap-4">
          <div class="bg-gray-50 p-4 rounded-lg">
            <div class="flex items-center">
              <CpuChipIcon class="h-8 w-8 text-gray-600" />
              <div class="ml-3">
                <p class="text-sm font-medium text-gray-600">{{ $t('collections.total') }}</p>
                <p class="text-2xl font-bold text-gray-900">{{ taskDetail.total_count || 0 }}</p>
              </div>
            </div>
          </div>
          <div class="bg-blue-50 p-4 rounded-lg">
            <div class="flex items-center">
              <CheckCircleIcon class="h-8 w-8 text-blue-600" />
              <div class="ml-3">
                <p class="text-sm font-medium text-blue-600">{{ $t('collections.completed') }}</p>
                <p class="text-2xl font-bold text-blue-900">{{ taskDetail.completed_count || 0 }}</p>
              </div>
            </div>
          </div>
          <div class="bg-red-50 p-4 rounded-lg">
            <div class="flex items-center">
              <XCircleIcon class="h-8 w-8 text-red-600" />
              <div class="ml-3">
                <p class="text-sm font-medium text-red-600">{{ $t('collections.failed') }}</p>
                <p class="text-2xl font-bold text-red-900">{{ taskDetail.failed_count || 0 }}</p>
              </div>
            </div>
          </div>
          <div class="bg-yellow-50 p-4 rounded-lg">
            <div class="flex items-center">
              <CpuChipIcon class="h-8 w-8 text-yellow-600" />
              <div class="ml-3">
                <p class="text-sm font-medium text-yellow-600">{{ $t('collections.running') }}</p>
                <p class="text-2xl font-bold text-yellow-900">{{ taskDetail.current_running || 0 }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Results Table -->
        <div>
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-medium text-gray-900">
              {{ $t('collections.collectionResults') }}
              <span class="text-sm font-normal text-gray-500 ml-2">
                ({{ $t('collections.totalHosts', { count: filteredResults.length }) }})
              </span>
            </h3>
          </div>
          
          <!-- Filter Input -->
          <div class="relative mb-4">
            <input
              v-model="filterText"
              type="text"
              :placeholder="$t('collections.filterPlaceholder')"
              class="w-full px-3 py-2 pl-10 border border-gray-300 rounded-md shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <MagnifyingGlassIcon class="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          </div>

          <!-- Table Container with Fixed Header -->
          <div class="border border-gray-200 rounded-lg overflow-hidden">
            <div v-if="filteredResults.length === 0" class="text-center py-8 text-gray-500">
              <DocumentTextIcon class="h-12 w-12 mx-auto text-gray-300 mb-2" />
              <p>{{ filterText ? $t('collections.noFilteredResults') : $t('collections.noResults') }}</p>
            </div>
            <div v-else class="max-h-[50vh] overflow-y-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50 sticky top-0 z-10">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('collections.hostIP') }}</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('collections.hostname') }}</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('common.status') }}</th>
                       <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap" style="min-width: 250px; max-width: 400px;">{{ $t('collections.errorMessage') }}</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('common.operation') }}</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="result in filteredResults" :key="result.id" class="hover:bg-gray-50 transition-colors">
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900 font-medium">{{ result.ip }}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{{ result.hostname || '-' }}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm">
                      <span
                        v-if="result.collection_status === 'completed' || result.collection_success === true"
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                      >
                        <CheckCircleIcon class="h-3.5 w-3.5 mr-1" />
                        {{ $t('common.completed') }}
                      </span>
                      <span
                        v-else-if="result.collection_status === 'failed' || result.collection_success === false"
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
                      >
                        <XCircleIcon class="h-3.5 w-3.5 mr-1" />
                        {{ $t('common.failed') }}
                      </span>
                      <span
                        v-else-if="result.collection_status === 'collecting'"
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800"
                      >
                        <ArrowPathIcon class="h-3.5 w-3.5 mr-1 animate-spin" />
                        {{ $t('hosts.collecting') }}
                      </span>
                      <span
                        v-else
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                      >
                        <ClockIcon class="h-3.5 w-3.5 mr-1" />
                        {{ $t('common.pending') }}
                      </span>
                    </td>
                    <td class="px-4 py-3 text-sm relative">
                      <div v-if="(result.collection_status === 'failed' || result.collection_success === false) && result.error_message" class="relative">
                        <button
                          @click.stop="toggleResultError(result.id)"
                          class="flex items-center text-left text-red-600 hover:text-red-800 transition-colors group w-full"
                        >
                          <ExclamationTriangleIcon class="h-4 w-4 mr-1.5 flex-shrink-0" />
                          <span class="text-xs font-medium truncate flex-1">{{ $t('collections.viewError') }}</span>
                          <ChevronDownIcon 
                            class="h-3 w-3 ml-1 flex-shrink-0 transition-transform"
                            :class="{ 'rotate-180': expandedResultErrors.has(result.id) }"
                          />
                        </button>
                        <Transition
                          enter-active-class="transition ease-out duration-200"
                          enter-from-class="opacity-0 transform scale-95"
                          enter-to-class="opacity-100 transform scale-100"
                          leave-active-class="transition ease-in duration-150"
                          leave-from-class="opacity-100 transform scale-100"
                          leave-to-class="opacity-0 transform scale-95"
                        >
                          <div v-if="expandedResultErrors.has(result.id)" class="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800 break-words whitespace-pre-wrap max-w-full max-h-[200px] overflow-y-auto z-10 relative">
                            {{ result.error_message }}
                          </div>
                        </Transition>
                      </div>
                      <span v-else class="text-gray-400">-</span>
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm font-medium">
                      <button
                        v-if="result"
                        @click="viewHostDetails(result)"
                        class="text-blue-600 hover:text-blue-900"
                      >
                        {{ $t('collections.viewHostDetails') }}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <button
          type="button"
          @click="closeDetailModal"
          class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
        >
          {{ $t('common.close') }}
        </button>
      </template>
    </Modal>

    <!-- Confirm Modal -->
    <ConfirmModal
      :open="showConfirmModal"
      @close="showConfirmModal = false"
      @confirm="handleConfirm"
      :title="confirmTitle"
      :message="confirmMessage"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Transition } from 'vue'
import { useI18n } from 'vue-i18n'
import { collectionsApi, type CollectionTask } from '@/api/collections'
import Modal from '@/components/Modal.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import LoadingOverlay from '@/components/LoadingOverlay.vue'
import { useToastStore } from '@/stores/toast'
import { useSettingsStore } from '@/stores/settings'

const { t } = useI18n()
import {
  CpuChipIcon,
  CloudIcon,
  EyeIcon,
  XCircleIcon,
  ArrowPathIcon,
  ArrowDownTrayIcon,
  TrashIcon,
  CheckCircleIcon,
  ClockIcon,
  PlayIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  ChevronDownIcon,
} from '@heroicons/vue/24/outline'

const toastStore = useToastStore()
const settingsStore = useSettingsStore()

const tasks = ref<CollectionTask[]>([])
const loading = ref(false)
const pagination = ref<any>(null)
const showDetailModal = ref(false)
const taskDetail = ref<CollectionTask | null>(null)
const taskResults = ref<any[]>([])
const showConfirmModal = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
const confirmAction = ref<(() => void) | null>(null)
const selectedTaskId = ref<number | null>(null)
const perPage = ref(10)
const filterText = ref('')
const expandedResultErrors = ref<Set<number>>(new Set())

let pollInterval: ReturnType<typeof setInterval> | null = null

const loadTasks = async (page = 1) => {
  loading.value = true
  try {
    const response: any = await collectionsApi.getCollectionTasks({ page, per_page: perPage.value })
    // API client interceptor returns response.data, so response is already { code: 200, data: [...] }
    if (response && response.code === 200) {
      tasks.value = response.data || []
      pagination.value = response.pagination
    } else if (Array.isArray(response)) {
      tasks.value = response
    } else if (response && response.data && Array.isArray(response.data)) {
      tasks.value = response.data
      pagination.value = response.pagination
    }
  } catch (error: any) {
    console.error('Failed to load collection tasks:', error)
    toastStore.error(error.response?.data?.message || error.message || t('messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const startPolling = () => {
  if (pollInterval) clearInterval(pollInterval)
  pollInterval = setInterval(() => {
    // Only poll if there are running tasks
    const hasRunningTasks = tasks.value.some(t => t.status === 'running' || t.status === 'pending')
    if (hasRunningTasks) {
      loadTasks(pagination.value?.page || 1)
    }
  }, 3000) // Poll every 3 seconds
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

const getStatusClass = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': 'bg-yellow-100 text-yellow-800',
    'running': 'bg-blue-100 text-blue-800',
    'completed': 'bg-green-100 text-green-800',
    'failed': 'bg-red-100 text-red-800',
    'cancelled': 'bg-gray-100 text-gray-800',
  }
  return statusMap[status] || 'bg-gray-100 text-gray-800'
}

const getStatusIcon = (status: string) => {
  const iconMap: Record<string, any> = {
    'pending': ClockIcon,
    'running': PlayIcon,
    'completed': CheckCircleIcon,
    'failed': XCircleIcon,
    'cancelled': XCircleIcon,
  }
  return iconMap[status] || ClockIcon
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    'pending': t('common.pending'),
    'running': t('collections.running'),
    'completed': t('common.completed'),
    'failed': t('common.failed'),
    'cancelled': t('collections.cancel'),
  }
  return textMap[status] || status
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const viewTaskDetails = async (id: number) => {
  try {
    const [taskRes, resultsRes] = await Promise.all([
      collectionsApi.getCollectionTask(id),
      collectionsApi.getCollectionResults(id).catch(() => ({ code: 200, data: [] })),
    ])
    
    // API client interceptor returns response.data
    const taskResponse: any = taskRes
    const resultsResponse: any = resultsRes
    
    if (taskResponse && taskResponse.code === 200) {
      taskDetail.value = taskResponse.data
    }
    
    if (resultsResponse && resultsResponse.code === 200) {
      taskResults.value = resultsResponse.data || []
    } else if (Array.isArray(resultsResponse)) {
      taskResults.value = resultsResponse
    } else if (resultsResponse && resultsResponse.data && Array.isArray(resultsResponse.data)) {
      taskResults.value = resultsResponse.data
    }
    
    showDetailModal.value = true
    
    // Start polling for this task if it's running
    if (taskDetail.value?.status === 'running' || taskDetail.value?.status === 'pending') {
      startPollingForTask(id)
    }
  } catch (error: any) {
    console.error('Failed to load task details:', error)
    toastStore.error(error.response?.data?.message || error.message || t('messages.loadFailed'))
  }
}

// Polling for task details when modal is open
let taskDetailPollInterval: ReturnType<typeof setInterval> | null = null

const startPollingForTask = (taskId: number) => {
  if (taskDetailPollInterval) clearInterval(taskDetailPollInterval)
  taskDetailPollInterval = setInterval(async () => {
    if (!showDetailModal.value || !taskDetail.value) {
      stopPollingForTask()
      return
    }
    
    try {
      const [taskRes, resultsRes] = await Promise.all([
        collectionsApi.getCollectionTask(taskId),
        collectionsApi.getCollectionResults(taskId).catch(() => ({ code: 200, data: [] })),
      ])
      
      const taskResponse: any = taskRes
      const resultsResponse: any = resultsRes
      
      if (taskResponse && taskResponse.code === 200) {
        taskDetail.value = taskResponse.data
      }
      
      if (resultsResponse && resultsResponse.code === 200) {
        taskResults.value = resultsResponse.data || []
      }
      
      // Stop polling if task is completed or failed
      if (taskDetail.value?.status === 'completed' || taskDetail.value?.status === 'failed' || taskDetail.value?.status === 'cancelled') {
        stopPollingForTask()
      }
    } catch (error) {
      console.error('Failed to poll task details:', error)
    }
  }, 2000) // Poll every 2 seconds for real-time updates
}

const stopPollingForTask = () => {
  if (taskDetailPollInterval) {
    clearInterval(taskDetailPollInterval)
    taskDetailPollInterval = null
  }
}

// Computed property for filtered results
const filteredResults = computed(() => {
  if (!filterText.value.trim()) {
    return taskResults.value
  }
  const searchTerm = filterText.value.toLowerCase()
  return taskResults.value.filter((result: any) => {
    return (
      result.ip?.toLowerCase().includes(searchTerm) ||
      result.hostname?.toLowerCase().includes(searchTerm) ||
      result.collection_status?.toLowerCase().includes(searchTerm) ||
      result.error_message?.toLowerCase().includes(searchTerm) ||
      (result.collection_status === 'completed' && t('common.completed').toLowerCase().includes(searchTerm)) ||
      (result.collection_status === 'failed' && t('common.failed').toLowerCase().includes(searchTerm)) ||
      (result.collection_status === 'collecting' && t('hosts.collecting').toLowerCase().includes(searchTerm)) ||
      (result.collection_status === 'pending' && t('common.pending').toLowerCase().includes(searchTerm))
    )
  })
})

const toggleResultError = (resultId: number) => {
  if (expandedResultErrors.value.has(resultId)) {
    expandedResultErrors.value.delete(resultId)
  } else {
    expandedResultErrors.value.add(resultId)
  }
}

const closeDetailModal = () => {
  showDetailModal.value = false
  stopPollingForTask()
  taskDetail.value = null
  taskResults.value = []
  filterText.value = ''
  expandedResultErrors.value.clear()
}

const cancelTask = (id: number) => {
  confirmTitle.value = t('collections.confirmCancel')
  confirmMessage.value = t('collections.confirmCancelMessage')
  confirmAction.value = async () => {
    try {
      await collectionsApi.cancelCollectionTask(id)
      toastStore.success(t('collections.cancelSuccess'))
      loadTasks(pagination.value?.page || 1)
    } catch (error: any) {
      toastStore.error(error.response?.data?.message || t('messages.operationFailed'))
    }
  }
  showConfirmModal.value = true
}

const retryTask = (id: number) => {
  confirmTitle.value = t('collections.confirmRetry')
  confirmMessage.value = t('collections.confirmRetryMessage')
  confirmAction.value = async () => {
    try {
      await collectionsApi.retryCollectionTask(id)
      toastStore.success(t('collections.retrySuccess'))
      loadTasks(pagination.value?.page || 1)
    } catch (error: any) {
      toastStore.error(error.response?.data?.message || t('messages.operationFailed'))
    }
  }
  showConfirmModal.value = true
}

const deleteTask = (id: number) => {
  confirmTitle.value = t('collections.confirmDelete')
  confirmMessage.value = t('collections.confirmDeleteMessage')
  confirmAction.value = async () => {
    try {
      await collectionsApi.deleteCollectionTask(id)
      toastStore.success(t('collections.deleteSuccess'))
      loadTasks(pagination.value?.page || 1)
    } catch (error: any) {
      toastStore.error(error.response?.data?.message || t('messages.deleteFailed'))
    }
  }
  showConfirmModal.value = true
}

const exportTaskResults = async (id: number) => {
  try {
    const response: any = await collectionsApi.exportCollectionResultsCSV(id)
    
    // Response interceptor already returns response.data, so response is already a Blob
    const blob = response instanceof Blob
      ? response
      : new Blob([response], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `collection_task_${id}_results_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    toastStore.success(t('collections.exportSuccess'))
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.operationFailed'))
  }
}

const viewHostDetails = (host: any) => {
  if (!host) return
  const params = new URLSearchParams()
  if (host.ip) {
    params.set('search_field', 'ip')
    params.set('search', host.ip)
  }
  if (host.id) {
    params.set('highlightHostId', String(host.id))
  }
  const url = `/hosts${params.toString() ? `?${params.toString()}` : ''}`
  window.open(url, '_blank')
  closeDetailModal()
}

const handleConfirm = () => {
  if (confirmAction.value) {
    confirmAction.value()
  }
  showConfirmModal.value = false
  confirmAction.value = null
}

onMounted(() => {
  perPage.value = settingsStore.defaultPageSize
  loadTasks()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
  stopPollingForTask()
})
</script>
