<template>
  <transition
    enter-active-class="transition-opacity duration-200 ease-out"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition-opacity duration-200 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="loading"
      class="absolute inset-0 bg-white bg-opacity-75 backdrop-blur-sm z-50 flex items-center justify-center"
      :class="overlayClass"
    >
      <div class="flex flex-col items-center space-y-3">
        <div class="relative">
          <div class="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        </div>
        <p v-if="text" class="text-sm font-medium text-gray-600">{{ text }}</p>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
defineProps<{
  loading: boolean
  text?: string
  overlayClass?: string
}>()
</script>

