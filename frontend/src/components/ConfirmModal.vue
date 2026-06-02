<template>
  <Modal :open="open" @close="handleClose" :title="displayTitle" max-width="sm">
    <div class="space-y-4">
      <p class="text-sm text-gray-600">{{ message }}</p>
    </div>
    <template #footer>
      <button
        type="button"
        @click="handleClose"
        class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto transition-colors"
      >
        {{ $t('common.cancel') }}
      </button>
      <button
        type="button"
        @click="handleConfirm"
        :class="[
          'inline-flex w-full justify-center rounded-md px-3 py-2 text-sm font-semibold text-white shadow-sm sm:ml-3 sm:w-auto transition-colors',
          confirmButtonClass
        ]"
      >
        {{ displayConfirmText }}
      </button>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Modal from './Modal.vue'

interface Props {
  open: boolean
  title?: string
  message: string
  confirmText?: string
  confirmButtonClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  confirmText: '',
  confirmButtonClass: 'bg-red-600 hover:bg-red-500',
})

const { t } = useI18n()

const displayTitle = computed(() => props.title || t('common.confirm'))
const displayConfirmText = computed(() => props.confirmText || t('common.confirm'))

const emit = defineEmits<{
  close: []
  confirm: []
}>()

const handleClose = () => {
  emit('close')
}

const handleConfirm = () => {
  emit('confirm')
}
</script>

