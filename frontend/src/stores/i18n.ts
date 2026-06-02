import { defineStore } from 'pinia'
import { ref } from 'vue'
import i18n from '@/i18n'

export type Locale = 'zh-CN' | 'en-US'

export const useI18nStore = defineStore('i18n', () => {
  const savedLocale = (localStorage.getItem('locale') as Locale) || 'zh-CN'
  const currentLocale = ref<Locale>(savedLocale)

  // Initialize locale
  i18n.global.locale.value = currentLocale.value

  const setLocale = (newLocale: Locale) => {
    currentLocale.value = newLocale
    i18n.global.locale.value = newLocale
    localStorage.setItem('locale', newLocale)
  }

  const toggleLocale = () => {
    const newLocale = currentLocale.value === 'zh-CN' ? 'en-US' : 'zh-CN'
    setLocale(newLocale)
  }

  return {
    currentLocale,
    setLocale,
    toggleLocale,
  }
})

