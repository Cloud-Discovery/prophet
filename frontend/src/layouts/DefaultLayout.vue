<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-18 min-h-[72px]">
          <div class="flex items-center flex-1 min-w-0">
            <div class="flex-shrink-0 flex items-center">
              <router-link to="/" class="flex items-center">
                <img src="/prophet-logo.png" alt="Prophet" class="h-10 w-auto" />
              </router-link>
            </div>
            <!-- Desktop Navigation - Show main items + More menu on all desktop screens -->
            <div class="hidden lg:ml-8 lg:flex lg:space-x-2">
              <router-link
                v-for="item in mainNavigation"
                :key="item.key"
                :to="item.to"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium transition-colors whitespace-nowrap"
                active-class="border-blue-500 text-gray-900"
              >
                <component :is="item.icon" class="h-5 w-5 mr-2 flex-shrink-0" />
                <span>{{ $t(item.key) }}</span>
              </router-link>
              <Menu as="div" class="relative inline-block text-left">
                <MenuButton class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium transition-colors">
                  <Squares2X2Icon class="h-5 w-5 mr-2 flex-shrink-0" />
                  <span>{{ $t('navigation.more') }}</span>
                  <ChevronDownIcon class="h-4 w-4 ml-1 flex-shrink-0" />
                </MenuButton>
                <Transition
                  enter-active-class="transition ease-out duration-100"
                  enter-from-class="transform opacity-0 scale-95"
                  enter-to-class="transform opacity-100 scale-100"
                  leave-active-class="transition ease-in duration-75"
                  leave-from-class="transform opacity-100 scale-100"
                  leave-to-class="transform opacity-0 scale-95"
                >
                  <MenuItems class="absolute left-0 z-50 mt-2 w-56 origin-top-left rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                    <div class="py-1">
                      <MenuItem v-for="item in moreNavigation" :key="item.key" v-slot="{ active }">
                        <router-link
                          :to="item.to"
                          :class="[active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', 'flex items-center px-4 py-2 text-sm']"
                        >
                          <component :is="item.icon" class="h-5 w-5 mr-3 text-gray-400" />
                          {{ $t(item.key) }}
                        </router-link>
                      </MenuItem>
                    </div>
                  </MenuItems>
                </Transition>
              </Menu>
            </div>
            <!-- Mobile Menu Button -->
            <div class="lg:hidden ml-4">
              <Menu as="div" class="relative inline-block text-left">
                <MenuButton class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500">
                  <Bars3Icon class="h-6 w-6" />
                </MenuButton>
                <Transition
                  enter-active-class="transition ease-out duration-100"
                  enter-from-class="transform opacity-0 scale-95"
                  enter-to-class="transform opacity-100 scale-100"
                  leave-active-class="transition ease-in duration-75"
                  leave-from-class="transform opacity-100 scale-100"
                  leave-to-class="transform opacity-0 scale-95"
                >
                  <MenuItems class="absolute left-0 z-50 mt-2 w-56 origin-top-left rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                    <div class="py-1">
                      <MenuItem v-for="item in navigation" :key="item.key" v-slot="{ active }">
                        <router-link
                          :to="item.to"
                          :class="[active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', 'flex items-center px-4 py-2 text-sm']"
                        >
                          <component :is="item.icon" class="h-5 w-5 mr-3 text-gray-400" />
                          {{ $t(item.key) }}
                        </router-link>
                      </MenuItem>
                    </div>
                  </MenuItems>
                </Transition>
              </Menu>
            </div>
          </div>
          <div class="flex items-center space-x-3 ml-4 flex-shrink-0">
            <!-- Language Switcher -->
            <button
              @click="i18nStore.toggleLocale()"
              class="inline-flex items-center justify-center w-8 h-8 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors focus:outline-none"
              :title="i18nStore.currentLocale === 'zh-CN' ? $t('settings.english') : $t('settings.chinese')"
            >
              <span class="text-base">{{ i18nStore.currentLocale === 'zh-CN' ? '🇨🇳' : '🇺🇸' }}</span>
            </button>
            
            <div class="hidden sm:flex items-center space-x-3 border-l border-gray-200 pl-3">
              <span class="text-sm font-medium text-gray-700 truncate max-w-[120px]">{{ authStore.user?.username }}</span>
              <button
                @click="handleLogout"
                class="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-md transition-colors"
              >
                <ArrowRightOnRectangleIcon class="h-4 w-4 mr-1.5" />
                <span class="hidden md:inline">{{ $t('auth.logout') }}</span>
              </button>
            </div>
            <!-- Mobile Logout Button -->
            <div class="sm:hidden">
              <button
                @click="handleLogout"
                class="inline-flex items-center justify-center p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                :title="$t('auth.logout')"
              >
                <ArrowRightOnRectangleIcon class="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
    
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import { computed, Transition } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18nStore } from '@/stores/i18n'
import {
  HomeIcon,
  ServerIcon,
  MagnifyingGlassIcon,
  CloudIcon,
  CubeIcon,
  TagIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  CpuChipIcon,
  ChevronDownIcon,
  Bars3Icon,
  Squares2X2Icon,
} from '@heroicons/vue/24/outline'

const authStore = useAuthStore()
const i18nStore = useI18nStore()

const navigation = [
  { key: 'navigation.overview', to: '/', icon: HomeIcon },
  { key: 'navigation.hosts', to: '/hosts', icon: ServerIcon },
  { key: 'navigation.scans', to: '/scans', icon: MagnifyingGlassIcon },
  { key: 'navigation.collections', to: '/collections', icon: CpuChipIcon },
  { key: 'navigation.platforms', to: '/platforms', icon: CloudIcon },
  { key: 'navigation.applications', to: '/applications', icon: CubeIcon },
  { key: 'navigation.tags', to: '/tags', icon: TagIcon },
  { key: 'navigation.settings', to: '/settings', icon: Cog6ToothIcon },
]

// Main navigation items - show first 4 items, rest in "More" menu
const mainNavigation = computed(() => navigation.slice(0, 5))

// More navigation items for "More" menu
const moreNavigation = computed(() => navigation.slice(5))

const handleLogout = () => {
  authStore.logout()
}
</script>
