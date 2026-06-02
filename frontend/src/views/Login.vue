<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <Transition
      appear
      enter-active-class="transition ease-out duration-300"
      enter-from-class="opacity-0 translate-y-4"
      enter-to-class="opacity-100 translate-y-0"
    >
      <div class="max-w-md w-full space-y-8">
        <div class="text-center">
          <div class="flex justify-center mb-4">
            <img src="/prophet-logo.png" alt="Prophet" class="h-16 w-auto" />
          </div>
          <p class="mt-2 text-sm text-gray-600">{{ $t('auth.platformName') }}</p>
        </div>
        
        <div class="bg-white py-8 px-6 shadow rounded-lg sm:px-10 relative">
          <!-- Language Switcher -->
          <div class="absolute top-4 right-4">
            <div class="flex items-center gap-1 bg-gray-50 rounded-full p-1 border border-gray-200">
              <button
                @click="i18nStore.setLocale('zh-CN')"
                :class="[
                  'px-3 py-1 text-xs font-medium rounded-full transition-all duration-200 min-w-[2.5rem]',
                  i18nStore.currentLocale === 'zh-CN'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                ]"
              >
                中文
              </button>
              <button
                @click="i18nStore.setLocale('en-US')"
                :class="[
                  'px-3 py-1 text-xs font-medium rounded-full transition-all duration-200 min-w-[2.5rem]',
                  i18nStore.currentLocale === 'en-US'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                ]"
              >
                EN
              </button>
            </div>
          </div>
          
          <div class="mb-6">
            <h2 class="text-2xl font-semibold text-gray-900 text-center">{{ $t('auth.loginTitle') }}</h2>
            <p class="mt-2 text-sm text-gray-600 text-center">{{ $t('auth.loginSubtitle') }}</p>
          </div>
          
          <form class="space-y-6" @submit.prevent="handleLogin">
            <div class="space-y-4">
              <div>
                <label for="username" class="block text-sm font-medium text-gray-700 mb-1">
                  {{ $t('auth.username') }}
                </label>
                <div class="relative">
                  <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <UserIcon class="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="username"
                    v-model="form.username"
                    type="text"
                    required
                    autocomplete="username"
                    class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition-colors"
                    :placeholder="$t('auth.username')"
                  />
                </div>
              </div>
              
              <div>
                <label for="password" class="block text-sm font-medium text-gray-700 mb-1">
                  {{ $t('auth.password') }}
                </label>
                <div class="relative">
                  <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <LockClosedIcon class="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="password"
                    v-model="form.password"
                    :type="showPassword ? 'text' : 'password'"
                    required
                    autocomplete="current-password"
                    class="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition-colors"
                    :placeholder="$t('auth.password')"
                  />
                  <button
                    type="button"
                    @click="showPassword = !showPassword"
                    class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 focus:outline-none transition-colors"
                  >
                    <EyeIcon v-if="!showPassword" class="h-5 w-5" />
                    <EyeSlashIcon v-else class="h-5 w-5" />
                  </button>
                </div>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  {{ $t('auth.captcha') }}
                </label>
                <div class="flex items-center space-x-3">
                  <div class="flex-1 relative">
                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <ShieldCheckIcon class="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      v-model="form.captcha_code"
                      type="text"
                      required
                      maxlength="4"
                      class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm uppercase transition-colors"
                      :placeholder="$t('auth.captchaPlaceholder')"
                    />
                  </div>
                  <div class="relative">
                    <div class="border border-gray-300 rounded-md overflow-hidden bg-gray-50 hover:bg-gray-100 transition-colors relative group">
                      <img
                        v-if="captcha.image"
                        :src="captcha.image"
                        :alt="$t('auth.captcha')"
                        class="h-10 w-24 object-contain cursor-pointer"
                        @click="loadCaptcha"
                        :title="$t('auth.captchaClickRefresh')"
                      />
                      <div v-else class="h-10 w-24 flex items-center justify-center text-gray-400 text-xs">
                        {{ $t('common.loading') }}
                      </div>
                      <button
                        type="button"
                        @click.stop="loadCaptcha"
                        class="absolute top-0.5 right-0.5 p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-gray-400 transition-colors opacity-0 group-hover:opacity-100"
                        :title="$t('auth.captchaRefresh')"
                      >
                        <ArrowPathIcon class="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <Transition
              enter-active-class="transition ease-out duration-200"
              enter-from-class="opacity-0 transform scale-95"
              enter-to-class="opacity-100 transform scale-100"
              leave-active-class="transition ease-in duration-150"
              leave-from-class="opacity-100 transform scale-100"
              leave-to-class="opacity-0 transform scale-95"
            >
              <div v-if="error" class="rounded-md bg-red-50 p-4 border border-red-200">
                <div class="flex">
                  <div class="flex-shrink-0">
                    <ExclamationCircleIcon class="h-5 w-5 text-red-400" />
                  </div>
                  <div class="ml-3">
                    <p class="text-sm text-red-800">{{ error }}</p>
                  </div>
                </div>
              </div>
            </Transition>
            
            <div>
              <button
                type="submit"
                :disabled="loading"
                class="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <span v-if="loading" class="flex items-center">
                  <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {{ $t('auth.loggingIn') }}
                </span>
                <span v-else>{{ $t('auth.loginButton') }}</span>
              </button>
            </div>
            
            <div class="text-center">
              <p class="text-sm text-gray-600">
                {{ $t('auth.noAccount') }}
                <router-link to="/register" class="font-medium text-blue-600 hover:text-blue-500 transition-colors">
                  {{ $t('auth.registerNow') }}
                </router-link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ExclamationCircleIcon, EyeIcon, EyeSlashIcon, UserIcon, LockClosedIcon, ShieldCheckIcon, ArrowPathIcon } from '@heroicons/vue/24/outline'
import { Transition } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18nStore } from '@/stores/i18n'
import { authApi } from '@/api/auth'
import { useToastStore } from '@/stores/toast'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const authStore = useAuthStore()
const i18nStore = useI18nStore()
const toastStore = useToastStore()

const form = ref({
  username: '',
  password: '',
  captcha_id: '',
  captcha_code: '',
})

const captcha = ref({
  captcha_id: '',
  image: '',
})

const error = ref('')
const loading = ref(false)
const showPassword = ref(false)

const loadCaptcha = async () => {
  try {
    const response = await authApi.getCaptcha() as any
    captcha.value = response.data
    form.value.captcha_id = response.data.captcha_id
    form.value.captcha_code = ''
  } catch (err) {
    toastStore.error(t('auth.captchaLoadFailed'))
  }
}

const handleLogin = async () => {
  // Prevent multiple submissions
  if (loading.value) {
    return
  }
  
  error.value = ''
  loading.value = true
  
  try {
    // Ensure we use the correct captcha_id
    const loginData = {
      username: form.value.username,
      password: form.value.password,
      captcha_id: captcha.value.captcha_id || form.value.captcha_id,
      captcha_code: form.value.captcha_code.trim().toUpperCase(),
    }
    
    await authStore.login(loginData)
    toastStore.success(t('auth.loginSuccess'))
  } catch (err: any) {
    const errorMessage = typeof err === 'string' ? err : 
                        err?.message || 
                        err?.response?.data?.message || 
                        t('auth.loginFailed')
    error.value = errorMessage
    toastStore.error(errorMessage)
    // Reload captcha on error
    loadCaptcha()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCaptcha()
})
</script>
