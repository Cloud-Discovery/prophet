<template>
  <div class="px-4 py-6 sm:px-0">
    <div class="mb-4 flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 flex items-center">
          <TagIcon class="h-7 w-7 mr-2 text-gray-700" />
          {{ $t('tags.title') }}
        </h1>
        <p class="mt-1 text-sm text-gray-500">{{ $t('tags.subtitle') }}</p>
      </div>
      <div class="flex items-center space-x-2">
        <button
          @click="loadTags"
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
          {{ $t('tags.createTag') }}
        </button>
      </div>
    </div>
    
    <div class="bg-white shadow overflow-hidden sm:rounded-md relative">
      <LoadingOverlay :loading="loading" :text="$t('common.loading')" />
      <div class="grid grid-cols-1 gap-4 p-4 sm:grid-cols-2 lg:grid-cols-3">
        <transition-group
          name="fade"
          tag="div"
          class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 col-span-full"
        >
          <div
            v-for="tag in tags"
            :key="tag.id"
            class="border border-gray-200 rounded-lg p-4 transition-opacity"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-2">
                  <span
                    class="inline-block px-2 py-1 text-xs font-medium rounded text-white"
                    :style="{ backgroundColor: tag.color || '#6B7280' }"
                  >
                    {{ tag.name }}
                  </span>
                  <span class="text-xs text-gray-500">
                    {{ $t('tags.hostCount', { count: tag.host_count || 0 }) }}
                  </span>
                </div>
                <p class="text-sm text-gray-500 mb-2">{{ tag.description || $t('tags.noDescription') }}</p>
                <button
                  v-if="(tag.host_count || 0) > 0"
                  @click="viewTagHosts(tag)"
                  class="text-xs text-blue-600 hover:text-blue-800 transition-colors flex items-center"
                >
                  <EyeIcon class="h-3.5 w-3.5 mr-1" />
                  {{ $t('tags.viewHosts') }}
                </button>
              </div>
              <div class="flex flex-col space-y-1 ml-2">
                <button
                  @click="editTag(tag)"
                  class="text-indigo-600 hover:text-indigo-900 transition-colors text-sm"
                >
                  {{ $t('common.edit') }}
                </button>
                <button
                  @click="deleteTag(tag.id!)"
                  class="text-red-600 hover:text-red-900 transition-colors text-sm"
                >
                  {{ $t('common.delete') }}
                </button>
              </div>
            </div>
          </div>
        </transition-group>
        <div v-if="tags.length === 0 && !loading" class="col-span-full text-center py-8 text-gray-500">
          <TagIcon class="h-12 w-12 mx-auto text-gray-300 mb-2" />
          <p>{{ $t('tags.noTags') }}</p>
        </div>
      </div>
    </div>

    <!-- Create/Edit Tag Modal -->
    <Modal :open="showCreateModal" @close="closeCreateModal" :title="editingTagId ? $t('tags.editTagTitle') : $t('tags.createTagTitle')" max-width="md">
      <form @submit.prevent="saveTag" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('tags.tagName') }} *</label>
          <input
            v-model="tagForm.name"
            type="text"
            required
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition-colors"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('tags.description') }}</label>
          <textarea
            v-model="tagForm.description"
            rows="3"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition-colors"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('tags.color') }}</label>
          <div class="mt-2 flex space-x-2">
            <input
              v-model="tagForm.color"
              type="color"
              class="h-10 w-20 border border-gray-300 rounded cursor-pointer transition-colors"
            />
            <input
              v-model="tagForm.color"
              type="text"
              placeholder="#6B7280"
              pattern="^#[0-9A-Fa-f]{6}$"
              class="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition-colors"
            />
          </div>
          <p class="mt-1 text-xs text-gray-500">{{ $t('tags.colorHint') }}</p>
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
          @click="saveTag"
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
      :title="$t('tags.confirmDelete')"
      :message="confirmMessage"
    />

    <!-- Tag Hosts Modal -->
    <Modal 
      :open="showHostsModal" 
      @close="closeHostsModal" 
      :title="$t('tags.tagHostsTitle', { tagName: selectedTag?.name || '' })" 
      max-width="6xl"
    >
      <div v-if="selectedTag" class="space-y-4">
        <!-- Search and Actions -->
        <div class="flex items-center justify-between">
          <div class="flex-1 max-w-md">
            <div class="relative">
              <input
                v-model="hostSearchQuery"
                type="text"
                :placeholder="$t('tags.searchHosts')"
                class="w-full px-3 py-2 pl-10 border border-gray-300 rounded-md shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                @input="debouncedLoadTagHosts"
              />
              <MagnifyingGlassIcon class="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
            </div>
          </div>
          <div class="flex items-center space-x-2">
            <span class="text-sm text-gray-600">
              {{ $t('tags.totalHosts', { count: tagHostsPagination?.total || 0 }) }}
              <span v-if="selectedHostIds.length > 0" class="ml-2 text-blue-600 font-medium">
                ({{ $t('tags.selectedCount', { count: selectedHostIds.length }) }})
              </span>
            </span>
            <button
              v-if="selectedHostIds.length > 0"
              @click="batchRemoveTagHosts"
              :disabled="removing"
              class="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {{ removing ? $t('common.removing') : $t('tags.batchRemove') }}
            </button>
          </div>
        </div>

        <!-- Hosts Table -->
        <div class="border border-gray-200 rounded-lg overflow-hidden">
          <div class="max-h-[50vh] overflow-y-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                    <input
                      type="checkbox"
                      :checked="isAllHostsSelected"
                      @change="toggleSelectAllHosts"
                      class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('hosts.ip') }}</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('hosts.hostname') }}</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('hosts.osType') }}</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('common.status') }}</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{{ $t('common.operation') }}</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-if="tagHosts.length === 0 && !loadingHosts" class="text-center">
                  <td colspan="6" class="px-4 py-8 text-gray-500">
                    {{ hostSearchQuery ? $t('tags.noHostsFound') : $t('tags.noHosts') }}
                  </td>
                </tr>
                <tr 
                  v-for="host in tagHosts" 
                  :key="host.id" 
                  class="hover:bg-gray-50 transition-colors"
                  :class="{ 'bg-blue-50': selectedHostIds.includes(host.id!) }"
                >
                  <td class="px-4 py-3 whitespace-nowrap">
                    <input
                      type="checkbox"
                      :checked="selectedHostIds.includes(host.id!)"
                      @change="toggleSelectHost(host.id!)"
                      class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900 font-medium">{{ host.ip }}</td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{{ host.hostname || '-' }}</td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{{ host.os_type || '-' }}</td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm">
                    <span
                      :class="getCollectionStatusClass(host.collection_status)"
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                    >
                      {{ getCollectionStatusText(host.collection_status) }}
                    </span>
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm font-medium">
                    <button
                      @click="viewHostDetails(host.id!, host.ip!)"
                      class="text-blue-600 hover:text-blue-900 mr-3"
                    >
                      {{ $t('common.viewDetails') }}
                    </button>
                    <button
                      @click="removeTagHost(host.id!)"
                      class="text-red-600 hover:text-red-900"
                    >
                      {{ $t('tags.removeTag') }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="tagHostsPagination && tagHostsPagination.pages > 1" class="flex items-center justify-between">
          <div class="text-sm text-gray-700">
            {{ $t('common.showingResults', { 
              from: (tagHostsPagination.page - 1) * tagHostsPagination.per_page + 1,
              to: Math.min(tagHostsPagination.page * tagHostsPagination.per_page, tagHostsPagination.total),
              total: tagHostsPagination.total
            }) }}
          </div>
          <div class="flex space-x-2">
            <button
              @click="loadTagHosts(tagHostsPagination.page - 1)"
              :disabled="tagHostsPagination.page <= 1"
              class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ $t('common.previous') }}
            </button>
            <button
              @click="loadTagHosts(tagHostsPagination.page + 1)"
              :disabled="tagHostsPagination.page >= tagHostsPagination.pages"
              class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ $t('common.next') }}
            </button>
          </div>
        </div>
      </div>
      <template #footer>
        <button
          type="button"
          @click="closeHostsModal"
          class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
        >
          {{ $t('common.close') }}
        </button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { tagsApi, type Tag } from '@/api/tags'
import Modal from '@/components/Modal.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import LoadingOverlay from '@/components/LoadingOverlay.vue'
import { useToastStore } from '@/stores/toast'
import { TagIcon, PlusIcon, ArrowPathIcon, EyeIcon, MagnifyingGlassIcon } from '@heroicons/vue/24/outline'

// Simple debounce function
const debounce = (func: Function, wait: number) => {
  let timeout: ReturnType<typeof setTimeout> | null = null
  return function executedFunction(...args: any[]) {
    const later = () => {
      timeout = null
      func(...args)
    }
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

const { t } = useI18n()
const router = useRouter()
const toastStore = useToastStore()

const tags = ref<Tag[]>([])
const loading = ref(false)
const showCreateModal = ref(false)
const tagForm = ref<Partial<Tag>>({})
const editingTagId = ref<number | null>(null)
const saving = ref(false)
const deletingTagId = ref<number | null>(null)
const showConfirmModal = ref(false)
const confirmAction = ref<(() => void) | null>(null)
const confirmMessage = ref('')

// Tag hosts modal
const showHostsModal = ref(false)
const selectedTag = ref<Tag | null>(null)
const tagHosts = ref<any[]>([])
const loadingHosts = ref(false)
const tagHostsPagination = ref<any>(null)
const hostSearchQuery = ref('')
const selectedHostIds = ref<number[]>([])
const removing = ref(false)
const currentHostPage = ref(1)
const hostsPerPage = ref(20)

const loadTags = async () => {
  loading.value = true
  try {
    const response = await tagsApi.getTags()
    tags.value = response.data || []
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  tagForm.value = {
    color: '#6B7280',
  }
  editingTagId.value = null
  showCreateModal.value = true
}

const editTag = (tag: Tag) => {
  tagForm.value = { ...tag }
  editingTagId.value = tag.id!
  showCreateModal.value = true
}

const closeCreateModal = () => {
  showCreateModal.value = false
  tagForm.value = {}
  editingTagId.value = null
}

const saveTag = async () => {
  saving.value = true
  try {
    if (editingTagId.value) {
      await tagsApi.updateTag(editingTagId.value, tagForm.value)
      toastStore.success(t('tags.updateSuccess'))
    } else {
      await tagsApi.createTag(tagForm.value as Tag)
      toastStore.success(t('tags.createSuccess'))
    }
    closeCreateModal()
    loadTags()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.saveFailed'))
  } finally {
    saving.value = false
  }
}

const deleteTag = async (id: number) => {
  confirmMessage.value = t('tags.confirmDeleteMessage')
  confirmAction.value = async () => {
    deletingTagId.value = id
    try {
      await tagsApi.deleteTag(id)
      toastStore.success(t('tags.deleteSuccess'))
      loadTags()
    } catch (error: any) {
      toastStore.error(error.response?.data?.message || t('messages.deleteFailed'))
    } finally {
      deletingTagId.value = null
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

// Tag hosts management
const viewTagHosts = (tag: Tag) => {
  selectedTag.value = tag
  selectedHostIds.value = []
  hostSearchQuery.value = ''
  currentHostPage.value = 1
  showHostsModal.value = true
  loadTagHosts(1)
}

const closeHostsModal = () => {
  showHostsModal.value = false
  selectedTag.value = null
  tagHosts.value = []
  selectedHostIds.value = []
  hostSearchQuery.value = ''
  tagHostsPagination.value = null
}

const loadTagHosts = async (page: number = 1) => {
  if (!selectedTag.value) return
  
  loadingHosts.value = true
  currentHostPage.value = page
  try {
    const response = await tagsApi.getTagHosts(
      selectedTag.value.id!,
      page,
      hostsPerPage.value,
      hostSearchQuery.value
    )
    tagHosts.value = response.data || []
    tagHostsPagination.value = response.pagination || null
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.loadFailed'))
  } finally {
    loadingHosts.value = false
  }
}

const debouncedLoadTagHosts = debounce(() => {
  loadTagHosts(1)
}, 300)

const toggleSelectHost = (hostId: number) => {
  const index = selectedHostIds.value.indexOf(hostId)
  if (index > -1) {
    selectedHostIds.value.splice(index, 1)
  } else {
    selectedHostIds.value.push(hostId)
  }
}

const isAllHostsSelected = computed(() => {
  return tagHosts.value.length > 0 && 
         tagHosts.value.every(host => selectedHostIds.value.includes(host.id!))
})

const toggleSelectAllHosts = () => {
  if (isAllHostsSelected.value) {
    // Deselect all visible hosts
    tagHosts.value.forEach(host => {
      const index = selectedHostIds.value.indexOf(host.id!)
      if (index > -1) {
        selectedHostIds.value.splice(index, 1)
      }
    })
  } else {
    // Select all visible hosts
    tagHosts.value.forEach(host => {
      if (!selectedHostIds.value.includes(host.id!)) {
        selectedHostIds.value.push(host.id!)
      }
    })
  }
}

const removeTagHost = async (hostId: number) => {
  if (!selectedTag.value) return
  
  try {
    await tagsApi.removeHostTag(hostId, selectedTag.value.id!)
    toastStore.success(t('tags.removeTagSuccess'))
    loadTagHosts(currentHostPage.value)
    loadTags() // Refresh tag list to update host count
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.operationFailed'))
  }
}

const batchRemoveTagHosts = async () => {
  if (!selectedTag.value || selectedHostIds.value.length === 0) return
  
  removing.value = true
  try {
    await tagsApi.batchRemoveTagHosts(selectedTag.value.id!, selectedHostIds.value)
    toastStore.success(t('tags.batchRemoveSuccess', { count: selectedHostIds.value.length }))
    selectedHostIds.value = []
    loadTagHosts(currentHostPage.value)
    loadTags() // Refresh tag list to update host count
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.operationFailed'))
  } finally {
    removing.value = false
  }
}

const viewHostDetails = (hostId: number, hostIp: string) => {
  const url = `/hosts?search_field=ip&search=${hostIp}&highlightHostId=${hostId}`
  window.open(url, '_blank')
  closeHostsModal()
}

const getCollectionStatusClass = (status?: string) => {
  const statusMap: Record<string, string> = {
    'not_collected': 'bg-gray-100 text-gray-800',
    'collecting': 'bg-blue-100 text-blue-800',
    'completed': 'bg-green-100 text-green-800',
    'failed': 'bg-red-100 text-red-800',
  }
  return statusMap[status || 'not_collected'] || 'bg-gray-100 text-gray-800'
}

const getCollectionStatusText = (status?: string) => {
  const textMap: Record<string, string> = {
    'not_collected': t('hosts.notCollected'),
    'collecting': t('hosts.collecting'),
    'completed': t('common.completed'),
    'failed': t('common.failed'),
  }
  return textMap[status || 'not_collected'] || t('hosts.notCollected')
}

onMounted(() => {
  loadTags()
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
