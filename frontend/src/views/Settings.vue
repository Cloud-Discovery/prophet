<template>
  <div class="px-4 py-6 sm:px-0">
    <div class="mb-6 flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 flex items-center">
          <Cog6ToothIcon class="h-7 w-7 mr-2 text-gray-700" />
          {{ $t('settings.title') }}
        </h1>
        <p class="mt-1 text-sm text-gray-500">{{ $t('settings.subtitle') }}</p>
      </div>
      <button
        @click="loadConfig"
        :disabled="loading"
        class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        <ArrowPathIcon :class="{ 'animate-spin': loading }" class="h-4 w-4 mr-2" />
        {{ $t('common.refresh') }}
      </button>
    </div>
    
    <div class="space-y-6">
      <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-lg font-medium text-gray-900 mb-4">{{ $t('settings.concurrentConfig') }}</h2>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ $t('settings.scanConcurrent') }}</label>
            <input
              v-model.number="config.scan_concurrent"
              type="number"
              min="1"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition-colors"
            />
            <p class="mt-1 text-xs text-gray-500">{{ $t('settings.scanConcurrentHint') }}</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ $t('settings.collectConcurrent') }}</label>
            <input
              v-model.number="config.collect_concurrent"
              type="number"
              min="1"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition-colors"
            />
            <p class="mt-1 text-xs text-gray-500">{{ $t('settings.collectConcurrentHint') }}</p>
          </div>
          
          <div>
            <button
              @click="saveConfig"
              :disabled="loading"
              class="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {{ loading ? $t('settings.saving') : $t('settings.saveConfig') }}
            </button>
          </div>
        </div>
      </div>

      <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-lg font-medium text-gray-900 mb-4">{{ $t('settings.tableSettings') }}</h2>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ $t('settings.defaultPageSize') }}</label>
            <select
              v-model.number="pageSize"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition-colors"
            >
              <option :value="10">10 {{ $t('common.itemsPerPage') }}</option>
              <option :value="20">20 {{ $t('common.itemsPerPage') }}</option>
              <option :value="50">50 {{ $t('common.itemsPerPage') }}</option>
              <option :value="100">100 {{ $t('common.itemsPerPage') }}</option>
            </select>
            <p class="mt-1 text-xs text-gray-500">{{ $t('settings.pageSizeHint') }}</p>
          </div>
          
          <div>
            <button
              @click="savePageSize"
              :disabled="savingPageSize"
              class="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {{ savingPageSize ? $t('settings.savingSettings') : $t('settings.saveSettings') }}
            </button>
          </div>
        </div>
      </div>

      <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-lg font-medium text-gray-900 mb-4">{{ $t('settings.languageSettings') }}</h2>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('settings.selectLanguage') }}</label>
            <Menu as="div" class="relative inline-block text-left w-full">
              <MenuButton class="inline-flex w-full items-center justify-between px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors">
                <span class="flex items-center">
                  <GlobeAltIcon class="h-5 w-5 mr-2 text-gray-400" />
                  {{ i18nStore.currentLocale === 'zh-CN' ? $t('settings.chinese') : $t('settings.english') }}
                </span>
                <ChevronDownIcon class="h-4 w-4 text-gray-400" />
              </MenuButton>
              <Transition
                enter-active-class="transition ease-out duration-100"
                enter-from-class="transform opacity-0 scale-95"
                enter-to-class="transform opacity-100 scale-100"
                leave-active-class="transition ease-in duration-75"
                leave-from-class="transform opacity-100 scale-100"
                leave-to-class="transform opacity-0 scale-95"
              >
                <MenuItems class="absolute z-10 mt-2 w-full origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                  <div class="py-1">
                    <MenuItem v-slot="{ active }">
                      <button
                        @click="i18nStore.setLocale('zh-CN')"
                        :class="[active ? 'bg-gray-100' : '', 'flex items-center w-full px-4 py-2 text-sm text-gray-700']"
                      >
                        <CheckIcon v-if="i18nStore.currentLocale === 'zh-CN'" class="h-4 w-4 mr-2 text-blue-600" />
                        <span v-else class="w-6"></span>
                        {{ $t('settings.chinese') }}
                      </button>
                    </MenuItem>
                    <MenuItem v-slot="{ active }">
                      <button
                        @click="i18nStore.setLocale('en-US')"
                        :class="[active ? 'bg-gray-100' : '', 'flex items-center w-full px-4 py-2 text-sm text-gray-700']"
                      >
                        <CheckIcon v-if="i18nStore.currentLocale === 'en-US'" class="h-4 w-4 mr-2 text-blue-600" />
                        <span v-else class="w-6"></span>
                        {{ $t('settings.english') }}
                      </button>
                    </MenuItem>
                  </div>
                </MenuItems>
              </Transition>
            </Menu>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import { Transition } from 'vue'
import { GlobeAltIcon, ChevronDownIcon, CheckIcon, Cog6ToothIcon, ArrowPathIcon } from '@heroicons/vue/24/outline'
import { configApi } from '@/api/config'
import { useToastStore } from '@/stores/toast'
import { useSettingsStore } from '@/stores/settings'
import { useI18nStore } from '@/stores/i18n'

const { t } = useI18n()
const toastStore = useToastStore()
const settingsStore = useSettingsStore()
const i18nStore = useI18nStore()

const config = ref({
  scan_concurrent: 1,
  collect_concurrent: 5,
})

const loading = ref(false)
const pageSize = ref(settingsStore.defaultPageSize)
const savingPageSize = ref(false)

const loadConfig = async () => {
  try {
    const response: any = await configApi.getConcurrentConfig()
    if (response && response.code === 200) {
      config.value = response.data
    } else if (response && response.data) {
      config.value = response.data
    }
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.loadFailed'))
  }
}

const saveConfig = async () => {
  loading.value = true
  try {
    await configApi.updateConcurrentConfig(config.value)
    toastStore.success(t('settings.configSaveSuccess'))
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('settings.configSaveFailed'))
  } finally {
    loading.value = false
  }
}

const savePageSize = () => {
  savingPageSize.value = true
  try {
    settingsStore.setDefaultPageSize(pageSize.value)
    toastStore.success(t('settings.settingsSaveSuccess'))
  } catch (error: any) {
    toastStore.error(t('settings.settingsSaveFailed'))
  } finally {
    savingPageSize.value = false
  }
}

onMounted(() => {
  loadConfig()
  pageSize.value = settingsStore.defaultPageSize
})
</script>
