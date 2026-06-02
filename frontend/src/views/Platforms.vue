<template>
  <div class="px-4 py-6 sm:px-0">
    <div class="mb-4 flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 flex items-center">
          <CloudIcon class="h-7 w-7 mr-2 text-gray-700" />
          {{ $t('platforms.title') }}
        </h1>
        <p class="mt-1 text-sm text-gray-500">{{ $t('platforms.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2">
        <!-- View Toggle -->
        <div class="flex items-center border border-gray-300 rounded-md overflow-hidden">
          <button
            @click="viewMode = 'card'"
            :class="viewMode === 'card' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'"
            class="px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
            :title="$t('platforms.cardView')"
          >
            <Squares2X2Icon class="h-4 w-4" />
          </button>
          <button
            @click="viewMode = 'table'"
            :class="viewMode === 'table' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'"
            class="px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 border-l border-gray-300"
            :title="$t('platforms.tableView')"
          >
            <Bars3Icon class="h-4 w-4" />
          </button>
        </div>

        <!-- Batch Actions Menu (when platforms selected) -->
        <div v-if="selectedPlatforms.length > 0" class="relative">
          <Menu as="div" class="relative inline-block text-left">
            <MenuButton class="inline-flex items-center px-3 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">
              <span class="mr-2">{{ $t('common.batchOperation') }} ({{ selectedPlatforms.length }})</span>
              <ChevronDownIcon class="h-4 w-4" />
            </MenuButton>
            <MenuItems class="absolute right-0 z-10 mt-2 w-56 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
              <div class="py-1">
                <MenuItem v-slot="{ active }">
                  <button
                    @click="openBatchTagManagementModal"
                    :class="[active ? 'bg-gray-100' : '', 'flex items-center w-full px-4 py-2 text-sm text-gray-700']"
                  >
                    <TagIcon class="h-4 w-4 mr-3 text-gray-400" />
                    {{ $t('platforms.batchManageTags') }}
                  </button>
                </MenuItem>
              </div>
            </MenuItems>
          </Menu>
        </div>
        
        <button
          @click="loadPlatforms"
          :disabled="loading"
          class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          <ArrowPathIcon :class="{ 'animate-spin': loading }" class="h-4 w-4 mr-2" />
          {{ $t('common.refresh') }}
        </button>
        <button
          @click="openCreateModal"
          class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <PlusIcon class="h-4 w-4 mr-2" />
          {{ $t('platforms.addPlatform') }}
        </button>
      </div>
    </div>
    
    <!-- Card View -->
    <div v-if="viewMode === 'card'" class="grid grid-cols-1 gap-6 lg:grid-cols-2 relative">
      <LoadingOverlay :loading="loading" :text="$t('common.loading')" />
      <transition-group
        name="fade"
        tag="div"
        class="grid grid-cols-1 gap-6 lg:grid-cols-2 col-span-full"
      >
        <div
          v-for="platform in platforms"
          :key="platform.id"
          class="bg-white shadow rounded-lg overflow-hidden transition-opacity relative"
          :class="{ 'ring-2 ring-blue-500': selectedPlatforms.includes(platform.id!) }"
        >
        <!-- Selection Checkbox -->
        <div class="absolute top-2 right-2 z-10" @click.stop>
          <input
            type="checkbox"
            :value="platform.id"
            v-model="selectedPlatforms"
            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 h-5 w-5"
          />
        </div>
        <!-- Platform Header -->
        <div class="px-6 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <CloudIcon class="h-6 w-6 text-blue-600 mr-2" />
              <h3 class="text-lg font-semibold text-gray-900">{{ platform.name }}</h3>
            </div>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {{ platform.type.toUpperCase() }}
            </span>
          </div>
          <div class="mt-2 flex items-center text-sm text-gray-600">
            <ServerIcon class="h-4 w-4 mr-1" />
            <span>{{ platform.host }}:{{ platform.port || 443 }}</span>
            <span class="mx-2">•</span>
            <UserIcon class="h-4 w-4 mr-1" />
            <span>{{ platform.username }}</span>
            <span v-if="platform.region" class="mx-2">•</span>
            <span v-if="platform.region">{{ platform.region }}</span>
          </div>
          <!-- Tags -->
          <div v-if="platform.tags && platform.tags.length > 0" class="mt-3 flex flex-wrap gap-1">
            <span
              v-for="tag in platform.tags"
              :key="tag.id"
              class="inline-flex items-center px-2 py-1 text-xs font-medium rounded text-white"
              :style="{ backgroundColor: tag.color || '#6B7280' }"
            >
              {{ tag.name }}
            </span>
          </div>
        </div>
        
        <!-- Sync Progress (if syncing) -->
        <div v-if="getPlatformSyncStatus(platform.id)" class="px-6 py-4 bg-blue-50 border-b border-blue-200">
          <h4 class="text-sm font-medium text-blue-900 mb-2 flex items-center">
            <ArrowPathIcon class="h-4 w-4 mr-1 animate-spin" />
            {{ $t('platforms.syncing') }}
          </h4>
          <div class="space-y-2">
            <div class="flex items-center justify-between text-xs text-blue-800">
              <span>{{ $t('scans.progress') }}: {{ getPlatformSyncStatus(platform.id)?.progress || 0 }}%</span>
              <span v-if="getPlatformSyncStatus(platform.id)?.total_count">
                {{ getPlatformSyncStatus(platform.id)?.completed_count || 0 }} / {{ getPlatformSyncStatus(platform.id)?.total_count }} {{ $t('collections.completed') }}
              </span>
              <span v-else>
                {{ getPlatformSyncStatus(platform.id)?.completed_count || 0 }} {{ $t('collections.completed') }}
              </span>
            </div>
            <div class="w-full bg-blue-200 rounded-full h-2">
              <div
                class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                :style="{ width: `${getPlatformSyncStatus(platform.id)?.progress || 0}%` }"
              ></div>
            </div>
            <div class="flex items-center justify-between text-xs text-blue-700">
              <span>
                {{ $t('collections.completed') }}: <span class="font-semibold text-green-700">{{ getPlatformSyncStatus(platform.id)?.completed_count || 0 }}</span>
              </span>
              <span>
                {{ $t('collections.failed') }}: <span class="font-semibold text-red-700">{{ getPlatformSyncStatus(platform.id)?.failed_count || 0 }}</span>
              </span>
              <span v-if="getPlatformSyncStatus(platform.id)?.total_count">
                {{ $t('collections.total') }}: <span class="font-semibold">{{ getPlatformSyncStatus(platform.id)?.total_count }}</span>
              </span>
            </div>
          </div>
        </div>
        
        <!-- Statistics -->
        <div v-if="platform.statistics" class="px-6 py-4">
          <h4 class="text-sm font-medium text-gray-700 mb-3 flex items-center">
            <ChartBarIcon class="h-4 w-4 mr-1" />
            {{ $t('platforms.resourceStats') }}
          </h4>
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-blue-50 p-3 rounded-lg">
              <div class="flex items-center">
                <ServerIcon class="h-6 w-6 text-blue-600" />
                <div class="ml-2">
                  <p class="text-xs text-blue-600 font-medium">{{ $t('platforms.esxiHosts') }}</p>
                  <p class="text-xl font-bold text-blue-900">{{ platform.statistics.esxi_count || 0 }}</p>
                </div>
              </div>
            </div>
            <div class="bg-purple-50 p-3 rounded-lg">
              <div class="flex items-center">
                <CpuChipIcon class="h-6 w-6 text-purple-600" />
                <div class="ml-2">
                  <p class="text-xs text-purple-600 font-medium">{{ $t('platforms.vms') }}</p>
                  <p class="text-xl font-bold text-purple-900">{{ platform.statistics.vm_count || 0 }}</p>
                </div>
              </div>
            </div>
            <div class="bg-green-50 p-3 rounded-lg">
              <div class="flex items-center">
                <CpuChipIcon class="h-6 w-6 text-green-600" />
                <div class="ml-2">
                  <p class="text-xs text-green-600 font-medium">{{ $t('platforms.cpuCores') }}</p>
                  <p class="text-xl font-bold text-green-900">{{ platform.statistics.total_cpu_cores || 0 }}</p>
                </div>
              </div>
            </div>
            <div class="bg-yellow-50 p-3 rounded-lg">
              <div class="flex items-center">
                <Battery100Icon class="h-6 w-6 text-yellow-600" />
                <div class="ml-2">
                  <p class="text-xs text-yellow-600 font-medium">{{ $t('platforms.memoryGB') }}</p>
                  <p class="text-xl font-bold text-yellow-900">{{ platform.statistics.total_memory_gb || 0 }}</p>
                </div>
              </div>
            </div>
          </div>
          <div class="mt-3 bg-gray-50 p-3 rounded-lg">
            <div class="flex items-center">
              <CircleStackIcon class="h-5 w-5 text-gray-600" />
              <div class="ml-2">
                <p class="text-xs text-gray-600 font-medium">{{ $t('platforms.storageGB') }}</p>
                <p class="text-lg font-bold text-gray-900">{{ platform.statistics.total_storage_gb || 0 }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Actions -->
        <div class="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div class="flex flex-wrap gap-2">
            <button
              v-if="platform.id"
              @click="viewPlatform(platform.id)"
              class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <EyeIcon class="h-4 w-4 mr-1" />
              {{ $t('platforms.view') }}
            </button>
            <button
              @click="editPlatform(platform)"
              class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md hover:bg-indigo-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <PencilIcon class="h-4 w-4 mr-1" />
              {{ $t('common.edit') }}
            </button>
            <button
              v-if="platform.id"
              @click="openTagManagementModal(platform)"
              class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-purple-700 bg-purple-50 border border-purple-200 rounded-md hover:bg-purple-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
            >
              <TagIcon class="h-4 w-4 mr-1" />
              {{ $t('platforms.manageTags') }}
            </button>
            <button
              v-if="platform.id"
              @click="testPlatform(platform.id)"
              :disabled="testingPlatformId === platform.id"
              class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              <SignalIcon class="h-4 w-4 mr-1" />
              {{ testingPlatformId === platform.id ? $t('platforms.testing') : $t('platforms.testConnection') }}
            </button>
            <button
              v-if="platform.id"
              @click="syncPlatform(platform.id)"
              :disabled="syncingPlatformId === platform.id || getPlatformSyncStatus(platform.id)"
              class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
            >
              <ArrowPathIcon :class="{ 'animate-spin': syncingPlatformId === platform.id || getPlatformSyncStatus(platform.id)?.status === 'running' }" class="h-4 w-4 mr-1" />
              <span v-if="getPlatformSyncStatus(platform.id)">
                {{ $t('platforms.syncing') }} ({{ getPlatformSyncStatus(platform.id).progress }}%)
              </span>
              <span v-else-if="syncingPlatformId === platform.id">
                {{ $t('platforms.syncing') }}
              </span>
              <span v-else>
                {{ $t('platforms.syncResources') }}
              </span>
            </button>
            <button
              @click="showSyncSettings(platform)"
              class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-purple-700 bg-purple-50 border border-purple-200 rounded-md hover:bg-purple-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
            >
              <Cog6ToothIcon class="h-4 w-4 mr-1" />
              {{ $t('platforms.syncSettings') }}
            </button>
            <button
              v-if="platform.id"
              @click="deletePlatform(platform.id)"
              class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              <TrashIcon class="h-4 w-4 mr-1" />
              {{ $t('common.delete') }}
            </button>
          </div>
        </div>
        </div>
      </transition-group>
      <div v-if="platforms.length === 0 && !loading" class="col-span-full text-center py-12 text-gray-500">
        <CloudIcon class="h-16 w-16 mx-auto text-gray-300 mb-4" />
        <p class="text-lg font-medium">{{ $t('platforms.noPlatforms') }}</p>
        <p class="text-sm mt-1">{{ $t('platforms.addPlatformHint') }}</p>
      </div>
    </div>

    <!-- Table View -->
    <div v-else class="bg-white shadow sm:rounded-md overflow-hidden relative">
      <LoadingOverlay :loading="loading" :text="$t('common.loading')" />
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <input
                  type="checkbox"
                  :checked="allPlatformsSelected"
                  @change="toggleSelectAllPlatforms"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('platforms.platformName') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('platforms.platformType') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('platforms.host') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('platforms.username') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('platforms.esxiHosts') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('platforms.vms') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('platforms.cpuCores') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('platforms.memoryGB') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('platforms.storageGB') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('platforms.tags') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-if="platforms.length === 0 && !loading" class="text-center">
              <td colspan="12" class="px-6 py-12 text-gray-500">
                <CloudIcon class="h-16 w-16 mx-auto text-gray-300 mb-4" />
                <p class="text-lg font-medium">{{ $t('platforms.noPlatforms') }}</p>
                <p class="text-sm mt-1">{{ $t('platforms.addPlatformHint') }}</p>
              </td>
            </tr>
            <tr
              v-for="platform in platforms"
              :key="platform.id"
              class="hover:bg-gray-50 transition-colors"
              :class="{ 'bg-blue-50 hover:bg-blue-100': selectedPlatforms.includes(platform.id!) }"
            >
              <td class="px-6 py-4 whitespace-nowrap" @click.stop>
                <input
                  type="checkbox"
                  :value="platform.id"
                  v-model="selectedPlatforms"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <CloudIcon class="h-5 w-5 text-blue-600 mr-2" />
                  <div>
                    <div class="text-sm font-medium text-gray-900">{{ platform.name }}</div>
                    <div v-if="getPlatformSyncStatus(platform.id)" class="text-xs text-blue-600 mt-1">
                      <ArrowPathIcon class="h-3 w-3 inline animate-spin mr-1" />
                      {{ $t('platforms.syncing') }} ({{ getPlatformSyncStatus(platform.id)?.progress || 0 }}%)
                    </div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {{ platform.type.toUpperCase() }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <div class="flex items-center">
                  <ServerIcon class="h-4 w-4 mr-1" />
                  <span>{{ platform.host }}:{{ platform.port || 443 }}</span>
                </div>
                <div v-if="platform.region" class="text-xs text-gray-400 mt-1">{{ platform.region }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <div class="flex items-center">
                  <UserIcon class="h-4 w-4 mr-1" />
                  <span>{{ platform.username }}</span>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ platform.statistics?.esxi_count || 0 }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ platform.statistics?.vm_count || 0 }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ platform.statistics?.total_cpu_cores || 0 }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ platform.statistics?.total_memory_gb || 0 }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ platform.statistics?.total_storage_gb || 0 }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm" @click.stop>
                <div class="flex flex-wrap gap-1 items-center">
                  <span
                    v-for="tag in platform.tags"
                    :key="tag.id"
                    class="inline-flex items-center px-2 py-1 text-xs font-medium rounded text-white group/tag relative"
                    :style="{ backgroundColor: tag.color || '#6B7280' }"
                  >
                    {{ tag.name }}
                    <button
                      v-if="platform.id"
                      @click.stop="removePlatformTag(platform.id, tag.id!)"
                      class="ml-1 opacity-0 group-hover/tag:opacity-100 hover:bg-black/20 rounded p-0.5 transition-opacity"
                      :title="$t('platforms.removeTag')"
                    >
                      <XMarkIcon class="h-3 w-3" />
                    </button>
                  </span>
                  <button
                    v-if="platform.id"
                    @click.stop="openTagManagementModal(platform)"
                    class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                    :title="$t('platforms.manageTags')"
                  >
                    <TagIcon class="h-3 w-3 mr-1" />
                    {{ $t('platforms.manageTags') }}
                  </button>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <div class="flex items-center space-x-2">
                  <button
                    v-if="platform.id"
                    @click.stop="viewPlatform(platform.id)"
                    class="text-blue-600 hover:text-blue-900 p-1 rounded hover:bg-blue-50"
                    :title="$t('platforms.view')"
                  >
                    <EyeIcon class="h-4 w-4" />
                  </button>
                  <button
                    @click.stop="editPlatform(platform)"
                    class="text-indigo-600 hover:text-indigo-900 p-1 rounded hover:bg-indigo-50"
                    :title="$t('common.edit')"
                  >
                    <PencilIcon class="h-4 w-4" />
                  </button>
                  <button
                    v-if="platform.id"
                    @click.stop="testPlatform(platform.id)"
                    :disabled="testingPlatformId === platform.id"
                    class="text-blue-600 hover:text-blue-900 p-1 rounded hover:bg-blue-50 disabled:opacity-50"
                    :title="$t('platforms.testConnection')"
                  >
                    <SignalIcon class="h-4 w-4" />
                  </button>
                  <button
                    v-if="platform.id"
                    @click.stop="syncPlatform(platform.id)"
                    :disabled="syncingPlatformId === platform.id || getPlatformSyncStatus(platform.id)"
                    class="text-green-600 hover:text-green-900 p-1 rounded hover:bg-green-50 disabled:opacity-50"
                    :title="$t('platforms.syncResources')"
                  >
                    <ArrowPathIcon :class="{ 'animate-spin': syncingPlatformId === platform.id || getPlatformSyncStatus(platform.id)?.status === 'running' }" class="h-4 w-4" />
                  </button>
                  <button
                    @click.stop="showSyncSettings(platform)"
                    class="text-purple-600 hover:text-purple-900 p-1 rounded hover:bg-purple-50"
                    :title="$t('platforms.syncSettings')"
                  >
                    <Cog6ToothIcon class="h-4 w-4" />
                  </button>
                  <button
                    v-if="platform.id"
                    @click.stop="deletePlatform(platform.id)"
                    class="text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50"
                    :title="$t('common.delete')"
                  >
                    <TrashIcon class="h-4 w-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create/Edit Platform Modal -->
    <Modal :open="showCreateModal" @close="closeCreateModal" :title="editingPlatformId ? $t('platforms.editPlatformTitle') : $t('platforms.addPlatformTitle')" max-width="lg">
      <form @submit.prevent="savePlatform" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('platforms.platformName') }} *</label>
          <input
            v-model="platformForm.name"
            type="text"
            required
            placeholder="Enter platform name"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('platforms.platformType') }} *</label>
          <select
            v-model="platformForm.type"
            required
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="vmware">VMware</option>
            <option value="openstack">OpenStack</option>
            <option value="aliyun">{{ $t('platforms.aliyun') }}</option>
            <option value="huaweicloud">{{ $t('platforms.huaweicloud') }}</option>
          </select>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ $t('platforms.host') }} *</label>
            <input
              v-model="platformForm.host"
              type="text"
              required
              placeholder="Enter host address"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ $t('platforms.port') }}</label>
            <input
              v-model.number="platformForm.port"
              type="number"
              placeholder="Enter port number"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ $t('platforms.username') }} *</label>
            <input
              v-model="platformForm.username"
              type="text"
              required
              placeholder="Enter username"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">
              {{ $t('platforms.password') }} {{ editingPlatformId ? `(${$t('platforms.passwordHint')})` : '*' }}
            </label>
            <input
              v-model="platformForm.password"
              type="password"
              :required="!editingPlatformId"
              :placeholder="editingPlatformId ? $t('platforms.passwordHint') : ''"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('platforms.region') }}</label>
          <input
            v-model="platformForm.region"
            type="text"
            placeholder="Enter region"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </form>
      <template #footer>
        <button
          type="button"
          @click="closeCreateModal"
          class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
        >
          {{ $t('common.cancel') }}
        </button>
        <button
          type="button"
          @click="savePlatform"
          :disabled="saving"
          class="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto disabled:opacity-50"
        >
          {{ saving ? $t('settings.saving') : $t('common.save') }}
        </button>
      </template>
    </Modal>

    <!-- Platform Details Modal -->
    <Modal :open="showDetailModal" @close="closeDetailModal" :title="$t('platforms.platformDetails')" max-width="lg">
      <div v-if="platformDetail" class="space-y-6">
        <!-- Basic Info -->
        <div>
          <h3 class="text-sm font-medium text-gray-700 mb-3">{{ $t('platforms.basicInfo') }}</h3>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-sm font-medium text-gray-500">{{ $t('platforms.platformName') }}</label>
              <p class="mt-1 text-sm text-gray-900">{{ platformDetail.name }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-500">{{ $t('platforms.platformType') }}</label>
              <p class="mt-1 text-sm text-gray-900">{{ platformDetail.type.toUpperCase() }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-500">{{ $t('platforms.host') }}</label>
              <p class="mt-1 text-sm text-gray-900">{{ platformDetail.host }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-500">{{ $t('platforms.port') }}</label>
              <p class="mt-1 text-sm text-gray-900">{{ platformDetail.port || 443 }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-500">{{ $t('platforms.username') }}</label>
              <p class="mt-1 text-sm text-gray-900">{{ platformDetail.username }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-500">{{ $t('platforms.region') }}</label>
              <p class="mt-1 text-sm text-gray-900">{{ platformDetail.region || '-' }}</p>
            </div>
          </div>
        </div>
        
        <!-- Sync Result -->
        <div v-if="platformDetail.last_sync_result && platformDetail.last_sync_result.failed_items && platformDetail.last_sync_result.failed_items.length > 0">
          <h3 class="text-sm font-medium text-red-700 mb-3 flex items-center">
            <XCircleIcon class="h-4 w-4 mr-1" />
            {{ $t('platforms.syncFailedItems') }}
          </h3>
          <div class="bg-red-50 border border-red-200 rounded-lg p-4">
            <div class="max-h-48 overflow-y-auto">
              <table class="min-w-full divide-y divide-red-200">
                <thead class="bg-red-100">
                  <tr>
                    <th class="px-3 py-2 text-left text-xs font-medium text-red-800">{{ $t('platforms.type') }}</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-red-800">{{ $t('platforms.name') }}</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-red-800">{{ $t('hosts.ip') }}</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-red-800">{{ $t('platforms.error') }}</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-red-100">
                  <tr v-for="(item, idx) in platformDetail.last_sync_result.failed_items" :key="idx">
                    <td class="px-3 py-2 text-sm text-red-700">{{ item.type === 'esxi' ? $t('platforms.esxiHost') : $t('platforms.vm') }}</td>
                    <td class="px-3 py-2 text-sm text-red-700">{{ item.name }}</td>
                    <td class="px-3 py-2 text-sm text-red-700">{{ item.ip || '-' }}</td>
                    <td class="px-3 py-2 text-sm text-red-600">{{ item.error }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        
        <!-- Statistics -->
        <div v-if="platformDetail.statistics">
          <h3 class="text-sm font-medium text-gray-700 mb-3">{{ $t('platforms.resourceStats') }}</h3>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div class="bg-blue-50 p-4 rounded-lg">
              <div class="flex items-center">
                <ServerIcon class="h-8 w-8 text-blue-600" />
                <div class="ml-3">
                  <p class="text-xs text-blue-600 font-medium">{{ $t('platforms.esxiHosts') }}</p>
                  <p class="text-2xl font-bold text-blue-900">{{ platformDetail.statistics.esxi_count || 0 }}</p>
                </div>
              </div>
            </div>
            <div class="bg-purple-50 p-4 rounded-lg">
              <div class="flex items-center">
                <CpuChipIcon class="h-8 w-8 text-purple-600" />
                <div class="ml-3">
                  <p class="text-xs text-purple-600 font-medium">{{ $t('platforms.vms') }}</p>
                  <p class="text-2xl font-bold text-purple-900">{{ platformDetail.statistics.vm_count || 0 }}</p>
                </div>
              </div>
            </div>
            <div class="bg-green-50 p-4 rounded-lg">
              <div class="flex items-center">
                <CpuChipIcon class="h-8 w-8 text-green-600" />
                <div class="ml-3">
                  <p class="text-xs text-green-600 font-medium">{{ $t('platforms.cpuCores') }}</p>
                  <p class="text-2xl font-bold text-green-900">{{ platformDetail.statistics.total_cpu_cores || 0 }}</p>
                </div>
              </div>
            </div>
            <div class="bg-yellow-50 p-4 rounded-lg">
              <div class="flex items-center">
                <Battery100Icon class="h-8 w-8 text-yellow-600" />
                <div class="ml-3">
                  <p class="text-xs text-yellow-600 font-medium">{{ $t('platforms.memoryGB') }}</p>
                  <p class="text-2xl font-bold text-yellow-900">{{ platformDetail.statistics.total_memory_gb || 0 }}</p>
                </div>
              </div>
            </div>
            <div class="bg-indigo-50 p-4 rounded-lg">
              <div class="flex items-center">
                <CircleStackIcon class="h-8 w-8 text-indigo-600" />
                <div class="ml-3">
                  <p class="text-xs text-indigo-600 font-medium">{{ $t('platforms.storageGB') }}</p>
                  <p class="text-2xl font-bold text-indigo-900">{{ platformDetail.statistics.total_storage_gb || 0 }}</p>
                </div>
              </div>
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

    <!-- Sync Settings Modal -->
    <Modal :open="showSyncSettingsModal" @close="closeSyncSettingsModal" :title="$t('platforms.syncSettings')" max-width="md">
      <div v-if="syncSettingsPlatform" class="space-y-4">
        <div>
          <label class="flex items-center">
            <input
              v-model="syncSettings.auto_sync"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span class="ml-2 text-sm text-gray-700">{{ $t('platforms.autoSync') }}</span>
          </label>
          <p class="mt-1 text-xs text-gray-500">{{ $t('platforms.autoSyncHint') }}</p>
        </div>
        <div v-if="syncSettings.auto_sync">
          <label class="block text-sm font-medium text-gray-700">{{ $t('platforms.syncFrequency') }}</label>
          <select
            v-model="syncSettings.sync_frequency"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="daily">{{ $t('platforms.daily') }}</option>
            <option value="weekly">{{ $t('platforms.weekly') }}</option>
            <option value="monthly">{{ $t('platforms.monthly') }}</option>
          </select>
        </div>
        <div v-if="syncSettings.auto_sync">
          <label class="block text-sm font-medium text-gray-700">{{ $t('platforms.syncTime') }}</label>
          <input
            v-model="syncSettings.sync_time"
            type="time"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>
      <template #footer>
        <button
          type="button"
          @click="closeSyncSettingsModal"
          class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
        >
          {{ $t('common.cancel') }}
        </button>
        <button
          type="button"
          @click="saveSyncSettings"
          class="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto"
        >
          {{ $t('common.save') }}
        </button>
      </template>
    </Modal>

    <!-- Confirm Modal -->
    <ConfirmModal
      :open="showConfirmModal"
      @close="showConfirmModal = false"
      @confirm="handleConfirm"
      :title="$t('platforms.confirmDelete')"
      :message="confirmMessage"
    />

    <!-- Tag Management Modal -->
    <Modal :open="showTagManagementModal" @close="closeTagManagementModal" :title="$t('platforms.manageTags')" max-width="md">
      <div v-if="tagManagementTarget" class="space-y-4">
        <div>
          <p class="text-sm text-gray-600 mb-3">
            {{ $t('platforms.manageTagsFor') }}: <span class="font-semibold">{{ tagManagementTarget.name }}</span>
          </p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('platforms.selectTags') }}</label>
          <div class="max-h-60 overflow-y-auto border border-gray-300 rounded-md p-3 space-y-2">
            <label
              v-for="tag in availableTags"
              :key="tag.id"
              class="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-2 rounded"
            >
              <input
                type="checkbox"
                :value="tag.id"
                v-model="selectedTagIds"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <div class="flex items-center flex-1">
                <div class="w-3 h-3 rounded-full mr-2 flex-shrink-0" :style="{ backgroundColor: tag.color || '#6B7280' }"></div>
                <span class="text-sm text-gray-900">{{ tag.name }}</span>
              </div>
            </label>
          </div>
        </div>
        <div v-if="tagManagementTarget.tags && tagManagementTarget.tags.length > 0">
          <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('platforms.currentTags') }}</label>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="tag in tagManagementTarget.tags"
              :key="tag.id"
              class="inline-flex items-center px-2 py-1 text-xs font-medium rounded text-white"
              :style="{ backgroundColor: tag.color || '#6B7280' }"
            >
              {{ tag.name }}
            </span>
          </div>
        </div>
      </div>
      <template #footer>
        <button
          type="button"
          @click="closeTagManagementModal"
          class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
        >
          {{ $t('common.cancel') }}
        </button>
        <button
          type="button"
          @click="savePlatformTags"
          :disabled="saving"
          class="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto disabled:opacity-50"
        >
          {{ saving ? $t('settings.saving') : $t('common.save') }}
        </button>
      </template>
    </Modal>

    <!-- Batch Tag Management Modal -->
    <Modal :open="showBatchTagManagementModal" @close="closeBatchTagManagementModal" :title="$t('platforms.batchManageTags')" max-width="md">
      <div class="space-y-4">
        <div>
          <p class="text-sm text-gray-600 mb-3">
            {{ $t('platforms.batchManageTagsFor') }}: <span class="font-semibold">{{ selectedPlatforms.length }} {{ $t('platforms.selectedPlatforms') }}</span>
          </p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('platforms.selectTags') }}</label>
          <div class="max-h-60 overflow-y-auto border border-gray-300 rounded-md p-3 space-y-2">
            <label
              v-for="tag in availableTags"
              :key="tag.id"
              class="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-2 rounded"
            >
              <input
                type="checkbox"
                :value="tag.id"
                v-model="batchSelectedTagIds"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <div class="flex items-center flex-1">
                <div class="w-3 h-3 rounded-full mr-2 flex-shrink-0" :style="{ backgroundColor: tag.color || '#6B7280' }"></div>
                <span class="text-sm text-gray-900">{{ tag.name }}</span>
              </div>
            </label>
          </div>
        </div>
        <div class="bg-blue-50 border border-blue-200 rounded-md p-3">
          <p class="text-xs text-blue-800">
            {{ $t('platforms.batchTagHint') }}
          </p>
        </div>
      </div>
      <template #footer>
        <button
          type="button"
          @click="closeBatchTagManagementModal"
          class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
        >
          {{ $t('common.cancel') }}
        </button>
        <button
          type="button"
          @click="saveBatchPlatformTags"
          :disabled="saving || batchSelectedTagIds.length === 0"
          class="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto disabled:opacity-50"
        >
          {{ saving ? $t('settings.saving') : $t('common.save') }}
        </button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { platformsApi, type Platform } from '@/api/platforms'
import { tagsApi } from '@/api/tags'
import Modal from '@/components/Modal.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import LoadingOverlay from '@/components/LoadingOverlay.vue'
import { useToastStore } from '@/stores/toast'
import { useI18n } from 'vue-i18n'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import {
  CloudIcon,
  PlusIcon,
  ServerIcon,
  UserIcon,
  ChartBarIcon,
  CpuChipIcon,
  Battery100Icon,
  CircleStackIcon,
  EyeIcon,
  PencilIcon,
  SignalIcon,
  Cog6ToothIcon,
  TrashIcon,
  ArrowPathIcon,
  XCircleIcon,
  Squares2X2Icon,
  Bars3Icon,
  TagIcon,
  XMarkIcon,
  ChevronDownIcon,
  } from '@heroicons/vue/24/outline'

const { t } = useI18n()
const toastStore = useToastStore()

const platforms = ref<Platform[]>([])
const loading = ref(false)
const viewMode = ref<'card' | 'table'>('card')
const showCreateModal = ref(false)
const showDetailModal = ref(false)
const platformForm = ref<Partial<Platform>>({})
const platformDetail = ref<Platform | null>(null)
const editingPlatformId = ref<number | null>(null)
const saving = ref(false)
const testingPlatformId = ref<number | null>(null)
const syncingPlatformId = ref<number | null>(null)
const showConfirmModal = ref(false)
const confirmAction = ref<(() => void) | null>(null)
const confirmMessage = ref('')
const showSyncSettingsModal = ref(false)
const syncSettingsPlatform = ref<Platform | null>(null)
const syncSettings = ref({
  auto_sync: false,
  sync_frequency: 'daily',
  sync_time: '02:00',
})
const platformSyncTasks = ref<Map<number, any>>(new Map()) // platform_id -> task info
let syncStatusInterval: ReturnType<typeof setInterval> | null = null
const showTagManagementModal = ref(false)
const tagManagementTarget = ref<Platform | null>(null)
const selectedTagIds = ref<number[]>([])
const availableTags = ref<Array<{id: number, name: string, color?: string}>>([])
const selectedPlatforms = ref<number[]>([])
const showBatchTagManagementModal = ref(false)
const batchSelectedTagIds = ref<number[]>([])

interface PlatformSyncTaskInfo {
  task_id: number
  status: string
  progress: number
  completed_count: number
  failed_count: number
  total_count?: number | null
}

const loadPlatforms = async () => {
  loading.value = true
  try {
    const response: any = await platformsApi.getPlatforms()
    // API client interceptor returns response.data, so response is already { code: 200, data: [...] }
    let platformsData: Platform[] = []
    if (response && response.code === 200) {
      platformsData = response.data || []
    } else if (Array.isArray(response)) {
      platformsData = response
    } else if (response && response.data && Array.isArray(response.data)) {
      platformsData = response.data
    }
    
    platforms.value = platformsData
    
    // Load statistics for each platform (optional, can be done lazily)
    if (platforms.value.length > 0) {
      for (const platform of platforms.value) {
        if (platform.id) {
          try {
            const detailRes: any = await platformsApi.getPlatform(platform.id)
            if (detailRes && detailRes.code === 200 && detailRes.data?.statistics) {
              platform.statistics = detailRes.data.statistics
            }
          } catch (e) {
            // Ignore errors loading statistics - not critical
            console.warn(`Failed to load statistics for platform ${platform.id}:`, e)
          }
        }
      }
    }
  } catch (error: any) {
    console.error('Failed to load platforms:', error)
    toastStore.error(error.response?.data?.message || error.message || t('messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  platformForm.value = {
    type: 'vmware',
    port: 443,
  }
  editingPlatformId.value = null
  showCreateModal.value = true
}

const editPlatform = (platform: Platform) => {
  // Copy platform data but don't include password (for security)
  // User needs to re-enter password if they want to change it
  platformForm.value = {
    ...platform,
    password: '', // Clear password field - user must enter new password if changing
  }
  editingPlatformId.value = platform.id!
  showCreateModal.value = true
}

const closeCreateModal = () => {
  showCreateModal.value = false
  platformForm.value = {}
  editingPlatformId.value = null
}

const savePlatform = async () => {
  saving.value = true
  try {
    if (editingPlatformId.value) {
      // For updates, only send password if it's provided (not empty)
      const updateData = { ...platformForm.value }
      if (!updateData.password || updateData.password.trim() === '') {
        // Remove password field if empty - don't update password
        delete updateData.password
      }
      await platformsApi.updatePlatform(editingPlatformId.value, updateData)
      toastStore.success(t('platforms.updateSuccess'))
    } else {
      await platformsApi.createPlatform(platformForm.value as Platform)
      toastStore.success(t('platforms.createSuccess'))
    }
    closeCreateModal()
    loadPlatforms()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.saveFailed'))
  } finally {
    saving.value = false
  }
}

const viewPlatform = async (id: number) => {
  try {
    const response: any = await platformsApi.getPlatform(id)
    if (response && response.code === 200) {
      platformDetail.value = response.data
      showDetailModal.value = true
    }
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.loadFailed'))
  }
}

const showSyncSettings = (platform: Platform) => {
  syncSettingsPlatform.value = platform
  // Load sync settings from platform extra_config
  const extraConfig = platform.extra_config || {}
  syncSettings.value = {
    auto_sync: extraConfig.auto_sync || false,
    sync_frequency: extraConfig.sync_frequency || 'daily',
    sync_time: extraConfig.sync_time || '02:00',
  }
  showSyncSettingsModal.value = true
}

const closeSyncSettingsModal = () => {
  showSyncSettingsModal.value = false
  syncSettingsPlatform.value = null
  syncSettings.value = {
    auto_sync: false,
    sync_frequency: 'daily',
    sync_time: '02:00',
  }
}

const saveSyncSettings = async () => {
  if (!syncSettingsPlatform.value) return
  
  try {
    const extraConfig = {
      ...(syncSettingsPlatform.value.extra_config || {}),
      ...syncSettings.value,
    }
    await platformsApi.updatePlatform(syncSettingsPlatform.value.id!, {
      extra_config: extraConfig,
    })
    toastStore.success(t('platforms.settingsSaved'))
    closeSyncSettingsModal()
    loadPlatforms()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.saveFailed'))
  }
}

const closeDetailModal = () => {
  showDetailModal.value = false
  platformDetail.value = null
}

const testPlatform = async (id: number) => {
  testingPlatformId.value = id
  try {
    await platformsApi.testPlatform(id)
    toastStore.success(t('platforms.testSuccess'))
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('platforms.testFailed'))
  } finally {
    testingPlatformId.value = null
  }
}

const syncPlatform = async (id: number) => {
  syncingPlatformId.value = id
  try {
    const response: any = await platformsApi.syncPlatform(id)
    if (response && response.code === 200 && response.data) {
      const taskData = response.data
      // Store task info for this platform
      if (taskData.task_id) {
        platformSyncTasks.value.set(id, {
          task_id: taskData.task_id,
          status: taskData.status,
          progress: 0,
          completed_count: 0,
          failed_count: 0,
          total_count: null
        })
      }
      toastStore.success(t('platforms.syncTaskCreated'))
      // Start polling for sync status
      startSyncStatusPolling()
    }
    loadPlatforms()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('platforms.syncFailed'))
  } finally {
    syncingPlatformId.value = null
  }
}

const startSyncStatusPolling = () => {
  // Clear existing interval
  if (syncStatusInterval) {
    clearInterval(syncStatusInterval)
  }
  
  // Poll every 2 seconds for sync status
  syncStatusInterval = setInterval(async () => {
    await checkSyncStatus()
  }, 2000)
}

const checkSyncStatus = async () => {
  if (platformSyncTasks.value.size === 0) {
    if (syncStatusInterval) {
      clearInterval(syncStatusInterval)
      syncStatusInterval = null
    }
    return
  }
  
  try {
    const { collectionsApi } = await import('@/api/collections')
    
    for (const [platformId, taskInfo] of platformSyncTasks.value.entries()) {
      try {
        const response: any = await collectionsApi.getCollectionTask(taskInfo.task_id)
        if (response && response.code === 200 && response.data) {
          const task = response.data
          taskInfo.status = task.status
          taskInfo.progress = task.progress || 0
          taskInfo.completed_count = task.completed_count || 0
          taskInfo.failed_count = task.failed_count || 0
          taskInfo.total_count = task.total_count || null
          
          // Refresh platform statistics during sync to show real-time updates
          if (task.status === 'running' || task.status === 'pending') {
            // Update statistics for the platform being synced
            const platform = platforms.value.find(p => p.id === platformId)
            if (platform) {
              try {
                const detailRes: any = await platformsApi.getPlatform(platformId)
                if (detailRes && detailRes.code === 200 && detailRes.data?.statistics) {
                  platform.statistics = detailRes.data.statistics
                }
              } catch (e) {
                // Ignore errors - not critical
                console.warn(`Failed to refresh statistics for platform ${platformId}:`, e)
              }
            }
          }
          
          // If task is completed or failed, stop polling for this task
          if (task.status === 'completed' || task.status === 'failed') {
            if (task.status === 'completed') {
              toastStore.success(t('platforms.syncSuccess'))
            } else {
              toastStore.error(t('platforms.syncFailed') + (task.error_message ? `: ${task.error_message}` : ''))
            }
            platformSyncTasks.value.delete(platformId)
            loadPlatforms() // Refresh platform list with latest statistics
          }
        }
      } catch (error) {
        // Task might not exist anymore, remove it
        platformSyncTasks.value.delete(platformId)
      }
    }
    
    // Stop polling if no active tasks
    if (platformSyncTasks.value.size === 0 && syncStatusInterval) {
      clearInterval(syncStatusInterval)
      syncStatusInterval = null
    }
  } catch (error) {
    console.error('Failed to check sync status:', error)
  }
}

const getPlatformSyncStatus = (platformId: number): PlatformSyncTaskInfo | undefined => {
  return platformSyncTasks.value.get(platformId)
}

const deletePlatform = async (id: number) => {
  confirmMessage.value = t('platforms.confirmDeleteMessage')
  confirmAction.value = async () => {
    try {
      await platformsApi.deletePlatform(id)
      toastStore.success(t('platforms.deleteSuccess'))
      loadPlatforms()
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

const loadTags = async () => {
  try {
    const response: any = await tagsApi.getTags()
    if (response && response.code === 200) {
      availableTags.value = response.data || []
    } else if (Array.isArray(response)) {
      availableTags.value = response
    } else if (response && response.data) {
      availableTags.value = response.data
    }
  } catch (error: any) {
    console.warn('Failed to load tags:', error)
  }
}

const openTagManagementModal = (platform: Platform) => {
  tagManagementTarget.value = platform
  selectedTagIds.value = platform.tags?.map((tag: any) => tag.id!).filter(Boolean) || []
  showTagManagementModal.value = true
}

const closeTagManagementModal = () => {
  showTagManagementModal.value = false
  tagManagementTarget.value = null
  selectedTagIds.value = []
}

const savePlatformTags = async () => {
  if (!tagManagementTarget.value || !tagManagementTarget.value.id) return
  
  saving.value = true
  try {
    const platformId = tagManagementTarget.value.id
    const currentTagIds = tagManagementTarget.value.tags?.map((tag: any) => tag.id!).filter(Boolean) || []
    
    // Remove tags that are not in selectedTagIds
    for (const tagId of currentTagIds) {
      if (!selectedTagIds.value.includes(tagId)) {
        await tagsApi.removePlatformTag(platformId, tagId)
      }
    }
    
    // Add tags that are in selectedTagIds but not in currentTagIds
    const tagsToAdd = selectedTagIds.value.filter(tagId => !currentTagIds.includes(tagId))
    if (tagsToAdd.length > 0) {
      await tagsApi.addPlatformTags(platformId, tagsToAdd)
    }
    
    toastStore.success(t('platforms.tagsUpdated'))
    closeTagManagementModal()
    loadPlatforms()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.saveFailed'))
  } finally {
    saving.value = false
  }
}

const removePlatformTag = async (platformId: number, tagId: number) => {
  try {
    await tagsApi.removePlatformTag(platformId, tagId)
    toastStore.success(t('platforms.tagRemoved'))
    loadPlatforms()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.operationFailed'))
  }
}

const allPlatformsSelected = computed(() => {
  return platforms.value.length > 0 && selectedPlatforms.value.length === platforms.value.length && platforms.value.every(p => p.id && selectedPlatforms.value.includes(p.id))
})

const toggleSelectAllPlatforms = () => {
  if (allPlatformsSelected.value) {
    selectedPlatforms.value = []
  } else {
    selectedPlatforms.value = platforms.value.map(p => p.id!).filter(Boolean)
  }
}

const openBatchTagManagementModal = () => {
  if (selectedPlatforms.value.length === 0) {
    toastStore.warning(t('platforms.noPlatformsSelected'))
    return
  }
  batchSelectedTagIds.value = []
  showBatchTagManagementModal.value = true
}

const closeBatchTagManagementModal = () => {
  showBatchTagManagementModal.value = false
  batchSelectedTagIds.value = []
}

const saveBatchPlatformTags = async () => {
  if (selectedPlatforms.value.length === 0 || batchSelectedTagIds.value.length === 0) {
    return
  }
  
  saving.value = true
  try {
    let successCount = 0
    let failCount = 0
    
    // Add selected tags to all selected platforms
    for (const platformId of selectedPlatforms.value) {
      try {
        await tagsApi.addPlatformTags(platformId, batchSelectedTagIds.value)
        successCount++
      } catch (error: any) {
        console.error(`Failed to add tags to platform ${platformId}:`, error)
        failCount++
      }
    }
    
    if (successCount > 0) {
      toastStore.success(t('platforms.batchTagsAdded', { count: successCount }))
    }
    if (failCount > 0) {
      toastStore.error(t('platforms.batchTagsFailed', { count: failCount }))
    }
    
    closeBatchTagManagementModal()
    selectedPlatforms.value = []
    loadPlatforms()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.operationFailed'))
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadPlatforms()
  loadTags()
  // Load existing sync tasks on mount
  loadSyncTasks()
  // Start polling for sync status
  startSyncStatusPolling()
})

// Cleanup on unmount
onUnmounted(() => {
  if (syncStatusInterval) {
    clearInterval(syncStatusInterval)
    syncStatusInterval = null
  }
})

const loadSyncTasks = async () => {
  try {
    const { collectionsApi } = await import('@/api/collections')
    // Load pending and running tasks separately
    const [pendingRes, runningRes] = await Promise.all([
      collectionsApi.getCollectionTasks({ status: 'pending' }).catch(() => null),
      collectionsApi.getCollectionTasks({ status: 'running' }).catch(() => null)
    ])
    
    const tasks: any[] = []
    const pendingData: any = pendingRes as any
    const runningData: any = runningRes as any
    if (pendingData && pendingData.code === 200 && pendingData.data) {
      tasks.push(...pendingData.data)
    }
    if (runningData && runningData.code === 200 && runningData.data) {
      tasks.push(...runningData.data)
    }
    
    for (const task of tasks) {
      if (task.task_type === 'platform_sync' && task.platform_id) {
        platformSyncTasks.value.set(task.platform_id, {
          task_id: task.id,
          status: task.status,
          progress: task.progress || 0,
          completed_count: task.completed_count || 0,
          failed_count: task.failed_count || 0,
          total_count: task.total_count || null
        })
      }
    }
  } catch (error) {
    console.error('Failed to load sync tasks:', error)
  }
}
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
