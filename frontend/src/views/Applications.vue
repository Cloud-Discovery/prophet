<template>
  <div class="px-4 py-6 sm:px-0">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 flex items-center">
          <CubeIcon class="h-7 w-7 mr-2 text-gray-700" />
          {{ $t('applications.title') }}
        </h1>
        <p class="mt-1 text-sm text-gray-500">{{ $t('applications.subtitle') }}</p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <div class="relative">
          <span class="absolute inset-y-0 left-3 flex items-center text-gray-400">
            <MagnifyingGlassIcon class="h-4 w-4" />
          </span>
          <input
            v-model="searchTerm"
            type="text"
            :placeholder="$t('applications.searchPlaceholder')"
            class="pl-9 pr-3 py-2 rounded-md border border-gray-300 shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          />
        </div>
        <button
          @click="loadApplications"
          :disabled="loading"
          class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          <ArrowPathIcon :class="{ 'animate-spin': loading }" class="h-4 w-4 mr-2" />
          {{ $t('common.refresh') }}
        </button>
        <button
          @click="openCreateModal"
          class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
        >
          <PlusIcon class="h-4 w-4 mr-2" />
          {{ $t('applications.createApp') }}
        </button>
      </div>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
      <div class="rounded-lg border border-blue-100 bg-blue-50 p-4">
        <p class="text-xs uppercase tracking-wide text-blue-600 font-semibold">{{ $t('applications.totalApplications') }}</p>
        <p class="mt-2 text-2xl font-bold text-blue-900">{{ summary.totalApplications }}</p>
      </div>
      <div class="rounded-lg border border-emerald-100 bg-emerald-50 p-4">
        <p class="text-xs uppercase tracking-wide text-emerald-600 font-semibold">{{ $t('applications.totalHosts') }}</p>
        <p class="mt-2 text-2xl font-bold text-emerald-900">{{ summary.totalHosts }}</p>
      </div>
      <div class="rounded-lg border border-purple-100 bg-purple-50 p-4">
        <p class="text-xs uppercase tracking-wide text-purple-600 font-semibold">{{ $t('applications.lastUpdated') }}</p>
        <p class="mt-2 text-sm font-medium text-purple-900">{{ summary.lastUpdated }}</p>
      </div>
    </div>
    
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 relative">
      <LoadingOverlay :loading="loading" :text="$t('common.loading')" />
      <transition-group
        name="fade"
        tag="div"
        class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 col-span-full"
      >
        <div
          v-for="app in filteredApplications"
          :key="app.id"
          class="bg-white shadow rounded-lg p-6 transition-opacity space-y-4"
        >
          <div>
            <h3 class="text-lg font-semibold text-gray-900 truncate">{{ app.name }}</h3>
            <p class="text-sm text-gray-500 mt-1 line-clamp-2">{{ app.description || $t('applications.noDescription') }}</p>
          </div>
          <div class="grid grid-cols-2 gap-3 text-sm text-gray-600">
            <div>
              <p class="font-medium text-gray-500 uppercase tracking-wide text-xs">{{ $t('applications.hostCount') }}</p>
              <p class="mt-1 text-gray-800 font-semibold">{{ getHostCount(app) }}</p>
            </div>
            <div>
              <p class="font-medium text-gray-500 uppercase tracking-wide text-xs">{{ $t('applications.createdAt') }}</p>
              <p class="mt-1 text-gray-800">{{ formatDate(app.created_at) }}</p>
            </div>
            <div>
              <p class="font-medium text-gray-500 uppercase tracking-wide text-xs">{{ $t('applications.updatedAt') }}</p>
              <p class="mt-1 text-gray-800">{{ formatDate(app.updated_at) }}</p>
            </div>
            <div>
              <p class="font-medium text-gray-500 uppercase tracking-wide text-xs">{{ $t('applications.membership') }}</p>
              <p class="mt-1 text-gray-800">{{ app.hosts?.slice(0, 2).map(h => h.hostname || h.ip).join(', ') || $t('applications.unknown') }}</p>
            </div>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              @click="viewApplication(app.id!)"
              class="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
            >
              {{ $t('applications.viewDetails') }}
            </button>
            <button
              @click="editApplication(app)"
              class="px-3 py-1 text-sm bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200 transition-colors"
            >
              {{ $t('common.edit') }}
            </button>
            <button
              @click="deleteApplication(app.id!)"
              class="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
            >
              {{ $t('common.delete') }}
            </button>
          </div>
        </div>
      </transition-group>
      <div v-if="filteredApplications.length === 0 && !loading" class="col-span-full text-center py-8 text-gray-500">
        <CubeIcon class="h-12 w-12 mx-auto text-gray-300 mb-2" />
        <p>{{ searchTerm ? $t('applications.noSearchResults') : $t('applications.noApps') }}</p>
      </div>
    </div>

    <!-- Create/Edit Application Modal -->
    <Modal :open="showCreateModal" @close="closeCreateModal" :title="editingAppId ? $t('applications.editAppTitle') : $t('applications.createAppTitle')" max-width="md">
      <form @submit.prevent="saveApplication" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('applications.appName') }} *</label>
          <input
            v-model="appForm.name"
            type="text"
            required
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition-colors"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('applications.description') }}</label>
          <textarea
            v-model="appForm.description"
            rows="3"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition-colors"
          />
        </div>
      </form>
      <template #footer>
        <button
          type="button"
          @click="closeCreateModal"
          class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto transition-colors"
        >
          {{ $t('common.cancel') }}
        </button>
        <button
          type="button"
          @click="saveApplication"
          :disabled="saving"
          class="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto disabled:opacity-50 transition-colors"
        >
          {{ saving ? $t('common.loading') : $t('common.save') }}
        </button>
      </template>
    </Modal>

    <!-- Confirm Modal -->
    <ConfirmModal
      :open="showConfirmModal"
      @close="showConfirmModal = false"
      @confirm="handleConfirm"
      :title="$t('applications.confirmDelete')"
      :message="confirmMessage"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { applicationsApi, type Application } from '@/api/applications'
import Modal from '@/components/Modal.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import LoadingOverlay from '@/components/LoadingOverlay.vue'
import { useToastStore } from '@/stores/toast'
import { CubeIcon, PlusIcon, ArrowPathIcon, MagnifyingGlassIcon } from '@heroicons/vue/24/outline'

const { t } = useI18n()
const router = useRouter()
const toastStore = useToastStore()

const applications = ref<any[]>([])
const loading = ref(false)
const showCreateModal = ref(false)
const appForm = ref<Partial<Application>>({})
const editingAppId = ref<number | null>(null)
const saving = ref(false)
const showConfirmModal = ref(false)
const confirmAction = ref<(() => void) | null>(null)
const confirmMessage = ref('')
const searchTerm = ref('')

const filteredApplications = computed(() => {
  if (!searchTerm.value.trim()) {
    return applications.value
  }
  const keyword = searchTerm.value.trim().toLowerCase()
  return applications.value.filter((app) => {
    const nameMatch = app.name?.toLowerCase().includes(keyword)
    const descriptionMatch = app.description?.toLowerCase().includes(keyword)
    return nameMatch || descriptionMatch
  })
})

const summary = computed(() => {
  const totalApps = filteredApplications.value.length
  const totalHosts = filteredApplications.value.reduce(
    (acc, app) => acc + getHostCount(app),
    0
  )
  const latestDate = filteredApplications.value.reduce<string | null>((acc, app) => {
    const updatedAt = app.updated_at || app.created_at
    if (!updatedAt) return acc
    if (!acc) return updatedAt
    return new Date(updatedAt) > new Date(acc) ? updatedAt : acc
  }, null)
  return {
    totalApplications: totalApps,
    totalHosts,
    lastUpdated: latestDate ? formatDate(latestDate, true) : '-'
  }
})

const formatDate = (value?: string, includeTime = false) => {
  if (!value) return '-'
  const date = new Date(value)
  const options: Intl.DateTimeFormatOptions = includeTime
    ? { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }
    : { year: 'numeric', month: 'short', day: 'numeric' }
  return new Intl.DateTimeFormat(undefined, options).format(date)
}

const getHostCount = (app: any) => {
  if (typeof app.host_count === 'number') return app.host_count
  if (Array.isArray(app.hosts)) return app.hosts.length
  return 0
}

const loadApplications = async () => {
  loading.value = true
  try {
    const response = await applicationsApi.getApplications()
    applications.value = response.data || []
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  appForm.value = {}
  editingAppId.value = null
  showCreateModal.value = true
}

const editApplication = (app: Application) => {
  appForm.value = { ...app }
  editingAppId.value = app.id!
  showCreateModal.value = true
}

const closeCreateModal = () => {
  showCreateModal.value = false
  appForm.value = {}
  editingAppId.value = null
}

const saveApplication = async () => {
  saving.value = true
  try {
    if (editingAppId.value) {
      await applicationsApi.updateApplication(editingAppId.value, appForm.value)
      toastStore.success(t('applications.updateSuccess'))
    } else {
      await applicationsApi.createApplication(appForm.value as Application)
      toastStore.success(t('applications.createSuccess'))
    }
    closeCreateModal()
    loadApplications()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.saveFailed'))
  } finally {
    saving.value = false
  }
}

const viewApplication = (id: number) => {
  router.push(`/applications/${id}`)
}

const deleteApplication = async (id: number) => {
  confirmMessage.value = t('applications.confirmDeleteMessage')
  confirmAction.value = async () => {
    try {
      await applicationsApi.deleteApplication(id)
      toastStore.success(t('applications.deleteSuccess'))
      loadApplications()
    } catch (error: any) {
      toastStore.error(error.response?.data?.message || t('messages.deleteFailed'))
    }
  }
  showConfirmModal.value = true
}

const handleConfirm = () => {
  if (confirmAction.value) {
    confirmAction.value()
  }
  showConfirmModal.value = false
  confirmAction.value = null
}

onMounted(() => {
  loadApplications()
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
