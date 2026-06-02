<template>
  <div :class="['sm:px-0', isCanvasFullscreen ? 'p-0 fixed inset-0 z-[9998] bg-white' : 'px-4 py-6']">
    <div v-if="!isCanvasFullscreen" class="mb-4 flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <button
          @click="$router.push('/applications')"
          class="text-gray-600 hover:text-gray-900 transition-colors"
        >
          ← {{ $t('common.back') }}
        </button>
        <h1 class="text-2xl font-bold text-gray-900">{{ application?.name || $t('applications.appDetail') }}</h1>
      </div>
      <div class="flex space-x-2">
        <button
          @click="showAddHostModal = true"
          class="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 transition-colors"
        >
          {{ $t('applications.addHost') }}
        </button>
        <button
          @click="openAddRelationshipModal"
          class="px-4 py-2 bg-purple-600 text-white rounded-md text-sm hover:bg-purple-700 transition-colors"
        >
          {{ $t('applications.addRelationship') }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-500">{{ $t('common.loading') }}</div>
    
    <div v-else-if="application" class="space-y-6">
      <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-lg font-medium text-gray-900 mb-4">{{ $t('applications.basicInfo') }}</h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm font-medium text-gray-500">{{ $t('applications.appName') }}</label>
            <p class="mt-1 text-sm text-gray-900">{{ application.name }}</p>
          </div>
          <div>
            <label class="text-sm font-medium text-gray-500">{{ $t('applications.description') }}</label>
            <p class="mt-1 text-sm text-gray-900">{{ application.description || '-' }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white shadow rounded-lg p-6 space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-medium text-gray-900">{{ $t('applications.hostList') }}</h2>
            <p class="text-sm text-gray-500">{{ $t('applications.hostListSubtitle') }}</p>
          </div>
          <div class="relative">
            <span class="absolute inset-y-0 left-3 flex items-center text-gray-400">
              <MagnifyingGlassIcon class="h-4 w-4" />
            </span>
            <input
              v-model="hostSearchTerm"
              type="text"
              :placeholder="$t('applications.hostSearchPlaceholder')"
              class="pl-9 pr-3 py-2 rounded-md border border-gray-300 shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            />
          </div>
        </div>

        <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div class="rounded-md border border-blue-100 bg-blue-50 p-3">
            <p class="text-xs font-semibold uppercase tracking-wide text-blue-600">{{ $t('applications.totalHosts') }}</p>
            <p class="mt-2 text-xl font-bold text-blue-900">{{ summaryStats.totalHosts }}</p>
          </div>
          <div class="rounded-md border border-emerald-100 bg-emerald-50 p-3">
            <p class="text-xs font-semibold uppercase tracking-wide text-emerald-600">{{ $t('applications.physicalHosts') }}</p>
            <p class="mt-2 text-xl font-bold text-emerald-900">{{ summaryStats.physicalHosts }}</p>
          </div>
          <div class="rounded-md border border-purple-100 bg-purple-50 p-3">
            <p class="text-xs font-semibold uppercase tracking-wide text-purple-600">{{ $t('applications.virtualHosts') }}</p>
            <p class="mt-2 text-xl font-bold text-purple-900">{{ summaryStats.virtualHosts }}</p>
          </div>
        </div>

        <div v-if="filteredHosts.length === 0" class="text-center py-8 text-gray-500">
          <ServerIcon class="h-12 w-12 mx-auto text-gray-300 mb-2" />
          <p>{{ hostSearchTerm ? $t('applications.noHostSearchResults') : $t('applications.noHosts') }}</p>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
                <th @click="setSortKey('ip')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer">
                  {{ $t('hosts.ip') }}
                </th>
                <th @click="setSortKey('hostname')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer">
                  {{ $t('hosts.hostname') }}
                </th>
                <th @click="setSortKey('os_type')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer">
                  {{ $t('hosts.osType') }}
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.cpuInfo') }}</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.memory') }}</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.disk') }}</th>
                <th @click="setSortKey('device_type')" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer">
                  {{ $t('hosts.deviceType') }}
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.tags') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('common.operation') }}</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="host in filteredHosts" :key="host.id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ host.ip }}</td>
                <td class="px-6 py-4 text-sm text-gray-500 max-w-[200px] truncate">{{ host.hostname || '-' }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ host.os_type || '-' }}</td>
                <td class="px-6 py-4 text-sm text-gray-500">
                  <div class="flex flex-col">
                    <span class="truncate max-w-[220px]">{{ host.cpu_info || '-' }}</span>
                    <span v-if="host.cpu_cores" class="text-xs text-gray-400">{{ $t('hosts.cpuCores') }}: {{ host.cpu_cores }}</span>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatMetric(host.memory_total) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatMetric(host.disk_total_size) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">{{ host.device_type || '-' }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <div class="flex flex-wrap gap-1">
                    <span
                      v-for="tag in getHostTags(host)"
                      :key="tag.id"
                      class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
                      :style="tag.color ? { backgroundColor: tag.color + '20', color: tag.color } : {}"
                    >
                      {{ tag.name }}
                    </span>
                    <span v-if="getHostTags(host).length === 0" class="text-gray-400">{{ $t('applications.noTags') }}</span>
                  </div>
                </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button
                  @click="removeHost(host.id!)"
                  class="text-red-600 hover:text-red-900 transition-colors"
                >
                  {{ $t('common.delete') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        </div>
      </div>

      <div class="bg-white shadow rounded-lg p-6 space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-medium text-gray-900">{{ $t('applications.relationshipList') }}</h2>
            <p class="text-sm text-gray-500">{{ $t('applications.relationshipListSubtitle') }}</p>
        </div>
          <div class="relative">
            <span class="absolute inset-y-0 left-3 flex items-center text-gray-400">
              <MagnifyingGlassIcon class="h-4 w-4" />
            </span>
            <input
              v-model="relationshipSearchTerm"
              type="text"
              :placeholder="$t('applications.relationshipSearchPlaceholder')"
              class="pl-9 pr-3 py-2 rounded-md border border-gray-300 shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors"
            />
          </div>
        </div>
        <div v-if="filteredRelationships.length === 0" class="text-center py-6 text-gray-500">
          <ShareIcon class="h-12 w-12 mx-auto text-gray-300 mb-2" />
          <p>{{ relationshipSearchTerm ? $t('applications.noRelationshipSearchResults') : $t('applications.noRelationships') }}</p>
        </div>
        <table v-else class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('applications.sourceHost') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('applications.targetHost') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('applications.relationshipType') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('applications.description') }}</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('common.operation') }}</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="relation in filteredRelationships" :key="relation.id" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{{ getHostLabel(relation.from_host_id) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{{ getHostLabel(relation.to_host_id) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">{{ relation.relationship_type }}</td>
              <td class="px-6 py-4 text-sm text-gray-500">
                {{ relation.description || '-' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-3">
                <button
                  @click="editRelationship(relation)"
                  class="text-indigo-600 hover:text-indigo-900 transition-colors"
                >
                  {{ $t('common.edit') }}
                </button>
                <button
                  @click="deleteRelationship(relation)"
                  class="text-red-600 hover:text-red-900 transition-colors"
                >
                  {{ $t('common.delete') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div
        :class="[
          'bg-white shadow rounded-lg transition-all duration-200 ease-in-out',
          isCanvasFullscreen ? 'fixed inset-0 z-[9999] rounded-none shadow-xl flex flex-col bg-white' : ''
        ]"
      >
        <div class="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <div>
            <h2 class="text-lg font-medium text-gray-900">{{ $t('applications.relationshipCanvas') }}</h2>
            <p class="text-sm text-gray-500">{{ $t('applications.relationshipCanvasSubtitle') }}</p>
          </div>
        </div>
        <div :class="[
            'flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 px-6 py-3 text-xs text-gray-500',
            isCanvasFullscreen ? 'bg-white' : ''
          ]">
          <div class="flex items-center gap-2">
            <button
              @click="applyLayout('grid')"
              :class="[
                'rounded-md border px-3 py-1 font-medium transition',
                selectedLayout === 'grid'
                  ? 'border-blue-500 bg-blue-50 text-blue-600'
                  : 'border-gray-300 bg-white text-gray-600 hover:bg-gray-50'
              ]"
            >
              {{ $t('applications.canvasLayoutGrid') }}
            </button>
            <button
              @click="applyLayout('horizontal')"
              :class="[
                'rounded-md border px-3 py-1 font-medium transition',
                selectedLayout === 'horizontal'
                  ? 'border-blue-500 bg-blue-50 text-blue-600'
                  : 'border-gray-300 bg-white text-gray-600 hover:bg-gray-50'
              ]"
            >
              {{ $t('applications.canvasLayoutHorizontal') }}
            </button>
            <button
              @click="applyLayout('vertical')"
              :class="[
                'rounded-md border px-3 py-1 font-medium transition',
                selectedLayout === 'vertical'
                  ? 'border-blue-500 bg-blue-50 text-blue-600'
                  : 'border-gray-300 bg-white text-gray-600 hover:bg-gray-50'
              ]"
            >
              {{ $t('applications.canvasLayoutVertical') }}
            </button>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="zoomOut"
              class="rounded-md border border-gray-300 bg-white px-2 py-1 font-semibold text-gray-600 transition hover:bg-gray-50"
            >
              −
            </button>
            <button
              @click="zoomIn"
              class="rounded-md border border-gray-300 bg-white px-2 py-1 font-semibold text-gray-600 transition hover:bg-gray-50"
            >
              +
            </button>
            <button
              @click="fitView"
              class="rounded-md border border-gray-300 bg-white px-3 py-1 font-medium text-gray-600 transition hover:bg-gray-50"
            >
              {{ $t('applications.canvasFitView') }}
            </button>
            <button
              @click="resetZoom"
              class="rounded-md border border-gray-300 bg-white px-3 py-1 font-medium text-gray-600 transition hover:bg-gray-50"
            >
              {{ $t('applications.canvasResetZoom') }}
            </button>
            <button
              @click="saveCanvasLayout"
              :disabled="isSavingGraph"
              class="inline-flex items-center gap-1 rounded-md border border-blue-500 bg-blue-50 px-3 py-1 font-medium text-blue-600 transition hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <ArrowDownOnSquareIcon class="h-4 w-4" />
              <span>{{ isSavingGraph ? $t('common.saving') : $t('applications.canvasSave') }}</span>
            </button>
            <button
              @click="exportCanvasLayout"
              :disabled="isExportingGraph"
              class="inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1 font-medium text-gray-600 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <ArrowDownTrayIcon class="h-4 w-4" />
              <span>{{ isExportingGraph ? $t('applications.canvasExporting') : $t('applications.canvasExport') }}</span>
            </button>
            <button
              @click="exportCanvasAsImage"
              class="inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1 font-medium text-gray-600 transition hover:bg-gray-50"
            >
              <PhotoIcon class="h-4 w-4" />
              <span>{{ $t('applications.canvasExportImage') }}</span>
            </button>
            <!-- Edge Style Editor -->
            <div class="relative edge-style-menu-container" v-if="selectedCanvasEdge">
              <button
                @click.stop="showEdgeStyleMenu = !showEdgeStyleMenu"
                class="inline-flex items-center gap-1 rounded-md border border-purple-300 bg-purple-50 px-3 py-1 font-medium text-purple-700 transition hover:bg-purple-100"
              >
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                </svg>
                <span>{{ $t('applications.edgeStyle') }}</span>
              </button>
              <Transition
                enter-active-class="transition ease-out duration-100"
                enter-from-class="transform opacity-0 scale-95"
                enter-to-class="transform opacity-100 scale-100"
                leave-active-class="transition ease-in duration-75"
                leave-from-class="transform opacity-100 scale-100"
                leave-to-class="transform opacity-0 scale-95"
              >
                <div
                  v-if="showEdgeStyleMenu"
                  @click.stop
                  class="absolute right-0 mt-2 w-80 rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5 z-[10000] edge-style-menu-container divide-y divide-gray-100"
                >
                  <div class="p-4 space-y-4">
                    <!-- Edge Type -->
                    <div>
                      <label class="block text-xs font-semibold text-gray-900 mb-2 uppercase tracking-wide">{{ $t('applications.edgeType') }}</label>
                      <div class="grid grid-cols-3 gap-2">
                        <button
                          @click="applyEdgeStyle({ edgeType: 'polyline' })"
                          :class="edgeForm.edgeType === 'polyline' ? 'bg-purple-600 text-white border-purple-600 shadow-sm' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'"
                          class="px-3 py-2 text-sm font-medium rounded-md border transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                        >
                          {{ $t('applications.edgeTypePolyline') }}
                        </button>
                        <button
                          @click="applyEdgeStyle({ edgeType: 'line' })"
                          :class="edgeForm.edgeType === 'line' ? 'bg-purple-600 text-white border-purple-600 shadow-sm' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'"
                          class="px-3 py-2 text-sm font-medium rounded-md border transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                        >
                          {{ $t('applications.edgeTypeLine') }}
                        </button>
                        <button
                          @click="applyEdgeStyle({ edgeType: 'bezier' })"
                          :class="edgeForm.edgeType === 'bezier' ? 'bg-purple-600 text-white border-purple-600 shadow-sm' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'"
                          class="px-3 py-2 text-sm font-medium rounded-md border transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                        >
                          {{ $t('applications.edgeTypeBezier') }}
                        </button>
                      </div>
                    </div>
                    <!-- Edge Style -->
                    <div>
                      <label class="block text-xs font-semibold text-gray-900 mb-2 uppercase tracking-wide">{{ $t('applications.edgeStyle') }}</label>
                      <div class="grid grid-cols-4 gap-2">
                        <button
                          @click="applyEdgeStyle({ strokeDasharray: '' })"
                          :class="edgeForm.strokeDasharray === '' ? 'bg-purple-600 text-white border-purple-600 shadow-sm' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'"
                          class="px-3 py-2 text-sm font-medium rounded-md border transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                        >
                          {{ $t('applications.edgeStyleSolid') }}
                        </button>
                        <button
                          @click="applyEdgeStyle({ strokeDasharray: '5 5' })"
                          :class="edgeForm.strokeDasharray === '5 5' ? 'bg-purple-600 text-white border-purple-600 shadow-sm' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'"
                          class="px-3 py-2 text-sm font-medium rounded-md border transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                        >
                          {{ $t('applications.edgeStyleDashed') }}
                        </button>
                        <button
                          @click="applyEdgeStyle({ strokeDasharray: '10 5' })"
                          :class="edgeForm.strokeDasharray === '10 5' ? 'bg-purple-600 text-white border-purple-600 shadow-sm' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'"
                          class="px-3 py-2 text-sm font-medium rounded-md border transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                        >
                          {{ $t('applications.edgeStyleLongDashed') }}
                        </button>
                        <button
                          @click="applyEdgeStyle({ strokeDasharray: '3 3' })"
                          :class="edgeForm.strokeDasharray === '3 3' ? 'bg-purple-600 text-white border-purple-600 shadow-sm' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'"
                          class="px-3 py-2 text-sm font-medium rounded-md border transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                        >
                          {{ $t('applications.edgeStyleDotted') }}
                        </button>
                      </div>
                    </div>
                    <!-- Edge Width -->
                    <div>
                      <label class="block text-xs font-semibold text-gray-900 mb-2 uppercase tracking-wide">{{ $t('applications.edgeWidth') }}</label>
                      <div class="grid grid-cols-3 gap-2">
                        <button
                          @click="applyEdgeStyle({ strokeWidth: 1 })"
                          :class="edgeForm.strokeWidth === 1 ? 'bg-purple-600 text-white border-purple-600 shadow-sm' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'"
                          class="px-4 py-2 text-sm font-medium rounded-md border transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                        >
                          {{ $t('applications.edgeWidthThin') }}
                        </button>
                        <button
                          @click="applyEdgeStyle({ strokeWidth: 2 })"
                          :class="edgeForm.strokeWidth === 2 ? 'bg-purple-600 text-white border-purple-600 shadow-sm' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'"
                          class="px-4 py-2 text-sm font-medium rounded-md border transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                        >
                          {{ $t('applications.edgeWidthMedium') }}
                        </button>
                        <button
                          @click="applyEdgeStyle({ strokeWidth: 3 })"
                          :class="edgeForm.strokeWidth === 3 ? 'bg-purple-600 text-white border-purple-600 shadow-sm' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'"
                          class="px-4 py-2 text-sm font-medium rounded-md border transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                        >
                          {{ $t('applications.edgeWidthThick') }}
                        </button>
                      </div>
                    </div>
                    <!-- Edge Color -->
                    <div>
                      <label class="block text-xs font-semibold text-gray-900 mb-2 uppercase tracking-wide">{{ $t('applications.edgeColor') }}</label>
                      <!-- 预设颜色（圆形展示） -->
                      <div class="mb-3 flex items-center gap-2 flex-wrap">
                        <button
                          v-for="color in presetColors"
                          :key="color"
                          @click="applyEdgeStyle({ stroke: color })"
                          :class="[
                            'h-8 w-8 rounded-full border-2 transition-all hover:scale-110 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-1',
                            edgeForm.stroke === color 
                              ? 'border-purple-600 ring-2 ring-purple-500 ring-offset-1 shadow-md' 
                              : 'border-gray-300 hover:border-gray-400'
                          ]"
                          :style="{ backgroundColor: color }"
                          :title="color"
                        />
                      </div>
                      <!-- 自定义颜色选择器 -->
                      <div class="flex items-center gap-3">
                        <input
                          type="color"
                          :value="edgeForm.stroke"
                          @input="applyEdgeStyle({ stroke: ($event.target as HTMLInputElement).value })"
                          class="h-10 w-16 rounded-md border border-gray-300 cursor-pointer focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-all"
                        />
                        <input
                          type="text"
                          :value="edgeForm.stroke"
                          @input="applyEdgeStyle({ stroke: ($event.target as HTMLInputElement).value })"
                          class="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-all"
                          placeholder="#000000"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </Transition>
            </div>
            <button
              @click="toggleCanvasFullscreen"
              class="rounded-md border border-gray-300 bg-white px-3 py-1 font-medium text-gray-600 transition hover:bg-gray-50"
            >
              {{ isCanvasFullscreen ? $t('applications.canvasExitFullscreen') : $t('applications.canvasFullscreen') }}
            </button>
          </div>
        </div>
        <div :class="['flex', isCanvasFullscreen ? 'flex-1 min-h-0 h-full' : 'h-[560px]']">
          <aside 
            :style="{ width: isCanvasFullscreen ? `${leftSidebarWidth}px` : '288px' }"
            class="border-r border-gray-200 bg-gray-50 flex flex-col transition-all duration-200 flex-shrink-0"
          >
            <div class="flex-1 overflow-y-auto p-4 space-y-6">
              <div>
                <h4 class="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  {{ $t('applications.resourcePaletteTitle') }}
                </h4>
                <p class="mt-1 text-xs text-gray-500">{{ $t('applications.resourcePaletteHint') }}</p>
                <div :class="['mt-3 grid gap-2', (isCanvasFullscreen ? leftSidebarWidth : 288) < 300 ? 'grid-cols-1' : 'grid-cols-2']">
                  <button
                    v-for="item in resourceLibrary"
                    :key="item.key"
                    class="flex items-center gap-2 rounded-md border border-dashed border-gray-300 bg-white px-3 py-2 text-xs text-left transition hover:border-blue-400 hover:bg-blue-50"
                    draggable="true"
                    @dragstart="onResourceDragStart(item, $event)"
                    @dragend="onResourceDragEnd"
                    @click="createResourceNode(item)"
                  >
                    <span
                      class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white"
                      :style="{ backgroundColor: item.color }"
                    >
                      <component :is="RESOURCE_ICON_COMPONENTS[item.key]" class="h-4 w-4" />
                    </span>
                    <span class="flex-1 min-w-0">
                      <p class="font-semibold text-gray-700 truncate">{{ item.label }}</p>
                      <p class="text-[11px] text-gray-500 truncate">{{ item.description }}</p>
                    </span>
                  </button>
                </div>
              </div>

              <div>
                <h4 class="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  {{ $t('applications.currentHosts') }}
                </h4>
                <ul class="mt-2 space-y-1 text-xs text-gray-600">
                  <li
                    v-for="host in hosts"
                    :key="host.id"
                    class="flex items-center justify-between rounded-md border border-gray-200 bg-white px-3 py-2"
                  >
                    <span class="truncate">{{ host.hostname || host.ip || (`#${host.id}`) }}</span>
                    <span class="ml-2 text-[10px] uppercase text-gray-400">{{ host.device_type || 'host' }}</span>
                  </li>
                  <li v-if="hosts.length === 0" class="rounded-md border border-dashed border-gray-200 bg-white px-3 py-2 text-gray-400">
                    {{ $t('applications.noHosts') }}
                  </li>
                </ul>
              </div>
            </div>
            <div class="border-t border-gray-200 bg-white p-4">
              <div>
                <label class="text-xs font-medium text-gray-600">{{ $t('applications.searchHosts') }}</label>
                <div class="relative mt-2">
                  <MagnifyingGlassIcon class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                  <input
                    v-model="hostLibraryKeyword"
                    type="text"
                    :placeholder="$t('applications.hostSearchPlaceholder')"
                    class="w-full rounded-md border border-gray-300 bg-white py-2 pl-9 pr-3 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div class="mt-3 max-h-52 overflow-y-auto space-y-2 pr-1">
                <div
                  v-for="host in filteredAvailableHostsForCanvas"
                  :key="host.id"
                  class="flex items-start justify-between rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-xs"
                >
                  <div class="flex-1">
                    <p class="font-semibold text-gray-700 truncate">{{ host.ip }}</p>
                    <p class="text-gray-500 truncate">{{ host.hostname || $t('applications.unknown') }}</p>
                    <p v-if="host.vendor" class="text-[10px] uppercase text-gray-400 mt-1 truncate">{{ host.vendor }}</p>
                  </div>
                  <button
                    @click="addHostFromLibrary(host.id)"
                    :disabled="hostLibraryAddingId === host.id"
                    class="ml-3 inline-flex items-center rounded-md bg-blue-600 px-2 py-1 text-[11px] font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {{ hostLibraryAddingId === host.id ? $t('applications.adding') : $t('applications.add') }}
                  </button>
                </div>
                <p v-if="filteredAvailableHostsForCanvas.length === 0" class="rounded-md border border-dashed border-gray-300 bg-white px-3 py-2 text-xs text-gray-400">
                  {{ $t('applications.noAvailableHosts') }}
                </p>
              </div>
            </div>
          </aside>
          <!-- 左侧拖动条 -->
          <div
            v-if="isCanvasFullscreen"
            @mousedown="startResizeLeft"
            :class="[
              'group relative flex items-center justify-center cursor-col-resize flex-shrink-0 transition-all duration-200',
              'w-1 hover:w-2',
              isResizingLeft ? 'w-2' : ''
            ]"
            title="拖动调整左侧边栏宽度"
          >
            <!-- 拖动区域背景 -->
            <div
              :class="[
                'absolute inset-0 transition-all duration-200',
                'bg-gray-100/50 hover:bg-blue-50/80',
                isResizingLeft ? 'bg-blue-100/90' : ''
              ]"
            />
            <!-- 拖动指示器（三个点） -->
            <div
              :class="[
                'relative z-10 flex flex-col gap-1.5 items-center justify-center transition-all duration-200',
                'opacity-40 group-hover:opacity-100',
                isResizingLeft ? 'opacity-100' : ''
              ]"
            >
              <div
                :class="[
                  'w-1 h-1 rounded-full transition-all duration-200',
                  isResizingLeft 
                    ? 'bg-blue-600 shadow-sm' 
                    : 'bg-gray-500 group-hover:bg-blue-500 group-hover:shadow-sm'
                ]"
              />
              <div
                :class="[
                  'w-1 h-1 rounded-full transition-all duration-200',
                  isResizingLeft 
                    ? 'bg-blue-600 shadow-sm' 
                    : 'bg-gray-500 group-hover:bg-blue-500 group-hover:shadow-sm'
                ]"
              />
              <div
                :class="[
                  'w-1 h-1 rounded-full transition-all duration-200',
                  isResizingLeft 
                    ? 'bg-blue-600 shadow-sm' 
                    : 'bg-gray-500 group-hover:bg-blue-500 group-hover:shadow-sm'
                ]"
              />
            </div>
            <!-- 拖动区域边框线 -->
            <div
              :class="[
                'absolute inset-y-0 left-0 w-px transition-all duration-200',
                isResizingLeft 
                  ? 'bg-blue-500 shadow-sm' 
                  : 'bg-gray-300 group-hover:bg-blue-400'
              ]"
            />
          </div>
          <div
            :class="['flex-1 relative', isCanvasFullscreen ? 'min-h-0' : '']"
            ref="canvasContainerRef"
            @dragover="handleCanvasDragOver"
            @drop="handleCanvasDrop"
          >
            <ApplicationCanvas
              ref="canvasRef"
              :nodes="canvasNodes"
              :edges="canvasEdges"
              @canvas:ready="handleCanvasReady"
              @node:click="handleCanvasNodeClick"
              @edge:click="handleCanvasEdgeClick"
              @node:moved="handleCanvasNodeMoved"
              @node:removed="handleCanvasNodeRemoved"
              @edge:added="handleCanvasEdgeAdded"
              @edge:removed="handleCanvasEdgeRemoved"
              @blank:click="handleCanvasBlankClick"
            />
            <div v-if="canvasNodes.length === 0" class="pointer-events-none absolute inset-0 flex items-center justify-center bg-white/70">
              <div class="text-center text-sm text-gray-500">
                <ShareIcon class="mx-auto mb-3 h-12 w-12 text-gray-300" />
                <p>{{ $t('applications.noRelationshipData') }}</p>
              </div>
            </div>
          </div>
          <!-- 右侧拖动条 -->
          <div
            v-if="isCanvasFullscreen"
            @mousedown="startResizeRight"
            :class="[
              'group relative flex items-center justify-center cursor-col-resize flex-shrink-0 transition-all duration-200',
              'w-1 hover:w-2',
              isResizingRight ? 'w-2' : ''
            ]"
            title="拖动调整右侧边栏宽度"
          >
            <!-- 拖动区域背景 -->
            <div
              :class="[
                'absolute inset-0 transition-all duration-200',
                'bg-gray-100/50 hover:bg-blue-50/80',
                isResizingRight ? 'bg-blue-100/90' : ''
              ]"
            />
            <!-- 拖动指示器（三个点） -->
            <div
              :class="[
                'relative z-10 flex flex-col gap-1.5 items-center justify-center transition-all duration-200',
                'opacity-40 group-hover:opacity-100',
                isResizingRight ? 'opacity-100' : ''
              ]"
            >
              <div
                :class="[
                  'w-1 h-1 rounded-full transition-all duration-200',
                  isResizingRight 
                    ? 'bg-blue-600 shadow-sm' 
                    : 'bg-gray-500 group-hover:bg-blue-500 group-hover:shadow-sm'
                ]"
              />
              <div
                :class="[
                  'w-1 h-1 rounded-full transition-all duration-200',
                  isResizingRight 
                    ? 'bg-blue-600 shadow-sm' 
                    : 'bg-gray-500 group-hover:bg-blue-500 group-hover:shadow-sm'
                ]"
              />
              <div
                :class="[
                  'w-1 h-1 rounded-full transition-all duration-200',
                  isResizingRight 
                    ? 'bg-blue-600 shadow-sm' 
                    : 'bg-gray-500 group-hover:bg-blue-500 group-hover:shadow-sm'
                ]"
              />
            </div>
            <!-- 拖动区域边框线 -->
            <div
              :class="[
                'absolute inset-y-0 right-0 w-px transition-all duration-200',
                isResizingRight 
                  ? 'bg-blue-500 shadow-sm' 
                  : 'bg-gray-300 group-hover:bg-blue-400'
              ]"
            />
          </div>
          <aside 
            :style="{ width: isCanvasFullscreen ? `${rightSidebarWidth}px` : '288px' }"
            class="border-l border-gray-200 bg-white flex-shrink-0 transition-all duration-200"
          >
            <div class="h-full overflow-y-auto p-4 space-y-4">
              <div>
                <h3 class="text-sm font-semibold text-gray-700">{{ $t('applications.canvasInspector') }}</h3>
                <p class="mt-1 text-xs text-gray-500">{{ $t('applications.canvasInspectorHint') }}</p>
              </div>
              <div v-if="selectedCanvasNode" class="space-y-4">
                <div class="rounded-md border border-blue-100 bg-blue-50 p-3">
                  <p class="text-xs font-semibold uppercase tracking-wide text-blue-600">
                    {{ $t('applications.selectedNode') }}
                  </p>
                  <p class="mt-1 text-sm font-medium text-blue-900 truncate">{{ selectedCanvasNode.label }}</p>
                  <p class="text-xs text-blue-500">
                    {{ selectedCanvasNode.data?.displayStatus || selectedCanvasNode.status || selectedCanvasNode.type }}
                  </p>
                </div>
                <div
                  v-if="selectedHostDetails.length > 0"
                  class="rounded-md border border-gray-200 bg-gray-50 p-3"
                >
                  <dl class="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                    <div
                      v-for="detail in selectedHostDetails"
                      :key="`${detail.label}-${detail.value}`"
                      class="min-w-0"
                    >
                      <dt class="text-gray-500 font-medium truncate">{{ detail.label }}</dt>
                      <dd class="text-gray-900 truncate" :title="detail.value">
                        {{ detail.value || '-' }}
                      </dd>
                    </div>
                  </dl>
                </div>
                <div v-if="selectedCanvasNode.bindingHostId" class="space-y-2">
                  <div>
                    <label class="block text-xs font-medium text-gray-600">
                      {{ $t('applications.bindHost') }}
                    </label>
                    <select
                      v-model="nodeBindingHostId"
                      class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="">
                        {{ $t('applications.selectHostPlaceholder') }}
                      </option>
                      <option
                        v-for="host in selectableHosts"
                        :key="host.id"
                        :value="host.id"
                      >
                        {{ host.ip }} · {{ host.hostname || $t('applications.unknown') }}
                      </option>
                    </select>
                  </div>
                  <div class="flex flex-col gap-2">
                    <button
                      @click="updateNodeBinding"
                      :disabled="updatingNodeBinding || !canUpdateBinding"
                      class="inline-flex items-center justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {{ updatingNodeBinding ? $t('common.saving') : $t('applications.updateBinding') }}
                    </button>
                    <button
                      @click="deleteSelectedNode"
                      class="inline-flex items-center justify-center rounded-md border border-red-200 px-3 py-2 text-sm font-semibold text-red-600 transition-colors hover:bg-red-50"
                    >
                      {{ $t('applications.removeHostFromCanvas') }}
                    </button>
                  </div>
                </div>
                <div class="space-y-3">
                  <div>
                    <label class="block text-xs font-medium text-gray-600">{{ $t('applications.resourceName') }}</label>
                    <input
                      v-model="resourceLabel"
                      type="text"
                      class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                    />
                  </div>
                  <button
                    @click="updateResourceNodeLabel"
                    :disabled="!resourceLabel || resourceLabel.trim() === selectedCanvasNode.label"
                    class="inline-flex items-center justify-center rounded-md bg-purple-600 px-3 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-purple-500 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {{ $t('applications.updateResource') }}
                  </button>
                  <div>
                    <label class="block text-xs font-medium text-gray-600">
                      {{ $t('applications.resourceColor') }}
                    </label>
                    <div class="mt-2 flex flex-wrap gap-2">
                      <button
                        v-for="color in COLOR_PRESETS"
                        :key="color"
                        type="button"
                        @click="updateSelectedNodeColor(color)"
                        :class="[
                          'h-7 w-7 rounded-full border transition',
                          selectedCanvasNode.color === color ? 'ring-2 ring-offset-1 ring-blue-500 border-blue-500' : 'border-gray-200'
                        ]"
                        :style="{ backgroundColor: color }"
                        :title="color"
                      />
                    </div>
                  </div>
                  <button
                    @click="duplicateSelectedResource"
                    class="inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-semibold text-gray-700 transition hover:bg-gray-50"
                  >
                    {{ $t('applications.duplicateResource') }}
                  </button>
                  <p class="text-[11px] text-gray-500">
                    {{ $t('applications.resourceHint') }}
                  </p>
                </div>
              </div>
              <div v-else-if="selectedCanvasEdge" class="space-y-4">
                <div class="rounded-md border border-purple-100 bg-purple-50 p-3">
                  <p class="text-xs font-semibold uppercase tracking-wide text-purple-600">
                    {{ $t('applications.selectedEdge') }}
                  </p>
                  <p class="mt-1 text-sm font-medium text-purple-900 truncate">
                    {{ getHostLabel(Number(selectedCanvasEdge.source)) }} → {{ getHostLabel(Number(selectedCanvasEdge.target)) }}
                  </p>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600">{{ $t('applications.relationshipType') }}</label>
                  <select
                    v-model="edgeForm.relationship_type"
                    class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                  >
                    <option
                      v-for="option in relationshipTypeOptions"
                      :key="option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600">{{ $t('applications.description') }}</label>
                  <textarea
                    v-model="edgeForm.description"
                    rows="3"
                    class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                  />
                </div>
                <div class="rounded-md border border-blue-100 bg-blue-50 p-3">
                  <p class="text-xs text-blue-700">
                    {{ $t('applications.edgeStyleHint') }}
                  </p>
                </div>
                <div class="flex flex-col gap-2">
                  <button
                    @click="updateEdgeProperties"
                    :disabled="updatingEdge"
                    class="inline-flex items-center justify-center rounded-md bg-purple-600 px-3 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-purple-500 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {{ updatingEdge ? $t('common.saving') : $t('applications.updateRelationship') }}
                  </button>
                  <button
                    @click="deleteSelectedEdge"
                    class="inline-flex items-center justify-center rounded-md border border-red-200 px-3 py-2 text-sm font-semibold text-red-600 transition-colors hover:bg-red-50"
                  >
                    {{ $t('applications.deleteRelationship') }}
                  </button>
                </div>
              </div>
              <div v-else class="rounded-md border border-dashed border-gray-200 bg-gray-50 p-4 text-xs text-gray-500">
                <p>{{ $t('applications.canvasInspectorEmpty') }}</p>
                <p class="mt-2">
                  {{ $t('applications.canvasInspectorTip') }}
                </p>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>

    <!-- Add Host Modal -->
    <Modal :open="showAddHostModal" @close="closeAddHostModal" :title="$t('applications.addHost')" max-width="lg">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('applications.selectHost') }}</label>
          <div class="mt-2 max-h-60 overflow-y-auto border border-gray-300 rounded-md">
            <div
              v-for="host in availableHosts"
              :key="host.id"
              class="p-2 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 transition-colors"
            >
              <label class="flex items-center">
                <input
                  type="checkbox"
                  :value="host.id"
                  v-model="selectedHostIds"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span class="ml-2 text-sm text-gray-900">{{ host.ip }} - {{ host.hostname || $t('applications.unknown') }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <button
          type="button"
          @click="closeAddHostModal"
          class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto transition-colors"
        >
          {{ $t('common.cancel') }}
        </button>
        <button
          type="button"
          @click="addHosts"
          :disabled="selectedHostIds.length === 0 || adding"
          class="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto disabled:opacity-50 transition-colors"
        >
          {{ adding ? $t('applications.adding') : $t('applications.add') }}
        </button>
      </template>
    </Modal>

    <!-- Resource Binding Modal -->
    <Modal
      :open="showResourceBindingModal"
      @close="handleResourceBindingCancel"
      :title="selectedResourceHostId && !pendingResourceDefinition ? $t('applications.selectResourceType') : $t('applications.resourceBindingTitle')"
      max-width="lg"
    >
      <div class="space-y-5">
        <div
          v-if="pendingResourceDefinition"
          class="rounded-md border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700"
        >
          <strong class="font-semibold">{{ pendingResourceDefinition.label }}</strong>
          <span class="ml-1 text-blue-600">
            {{ pendingResourceDefinition.description }}
          </span>
          <p class="mt-2 text-xs text-blue-600">
            {{ $t('applications.resourceBindingDescription') }}
          </p>
        </div>

        <!-- 添加主机后选择资源类型 -->
        <div v-if="selectedResourceHostId && !pendingResourceDefinition">
          <div class="mb-4 rounded-md border border-blue-100 bg-blue-50 px-4 py-3">
            <p class="text-sm font-medium text-blue-900">
              {{ $t('applications.selectResourceTypeForHost') }}
            </p>
            <p class="mt-1 text-xs text-blue-700" v-if="currentSelectedHost">
              {{ currentSelectedHost.ip }}
              <span v-if="currentSelectedHost.hostname" class="ml-1">
                • {{ currentSelectedHost.hostname }}
              </span>
            </p>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div
              v-for="resource in resourceLibrary"
              :key="resource.key"
              @click="handleResourceSelected(resource)"
              class="cursor-pointer rounded-lg border-2 p-4 transition-all hover:border-purple-500 hover:bg-purple-50"
              :class="selectedResourceType === resource.key ? 'border-purple-500 bg-purple-50' : 'border-gray-200'"
            >
              <div class="flex items-center gap-3">
                <div
                  class="flex h-12 w-12 items-center justify-center rounded-full"
                  :style="{ backgroundColor: resource.color + '20' }"
                >
                  <component
                    :is="RESOURCE_ICON_COMPONENTS[resource.key]"
                    class="h-6 w-6"
                    :style="{ color: resource.color }"
                  />
                </div>
                <div class="flex-1">
                  <p class="text-sm font-medium text-gray-900">{{ resource.label }}</p>
                  <p class="text-xs text-gray-500">{{ resource.description }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 原有：从资源库拖拽后选择主机 -->
        <div v-else>
          <label class="block text-sm font-medium text-gray-700">
            {{ $t('applications.resourceBindingSelectHost') }}
          </label>
          <div class="mt-2 flex flex-col gap-3 sm:flex-row sm:items-center">
            <div class="relative flex-1">
              <MagnifyingGlassIcon class="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
              <input
                v-model="resourceBindingSearch"
                type="text"
                :placeholder="$t('applications.resourceBindingSearchPlaceholder')"
                class="w-full rounded-md border border-gray-300 py-2 pl-9 pr-3 text-sm shadow-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
              />
            </div>
          </div>
          <div class="mt-3 max-h-72 overflow-y-auto rounded-md border border-gray-200">
            <div
              v-if="filteredBindableHosts.length === 0"
              class="px-6 py-10 text-center text-sm text-gray-500"
            >
              {{ $t('applications.resourceBindingNoHosts') }}
            </div>
            <div
              v-else
              v-for="item in filteredBindableHosts"
              :key="item.host.id"
              class="border-b border-gray-100 last:border-b-0"
            >
              <label class="flex cursor-pointer items-center justify-between gap-4 px-4 py-3 transition hover:bg-gray-50">
                <div class="flex items-center gap-3">
                  <input
                    type="radio"
                    name="resource-binding-host"
                    :value="item.host.id"
                    v-model="selectedResourceHostId"
                    class="h-4 w-4 border-gray-300 text-purple-600 focus:ring-purple-500"
                  />
                  <div>
                    <p class="text-sm font-medium text-gray-900">
                      {{ item.host.ip }}
                      <span v-if="item.host.hostname" class="ml-1 text-gray-500">• {{ item.host.hostname }}</span>
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ item.host.device_type || '-' }} • {{ item.host.vendor || '-' }}
                    </p>
                  </div>
                </div>
                <span
                  class="rounded-full px-2.5 py-1 text-xs font-semibold"
                  :class="item.inApplication ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'"
                >
                  {{ item.inApplication ? $t('applications.resourceBindingAlreadyInApp') : $t('applications.resourceBindingNotInApp') }}
                </span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <button
          type="button"
          @click="handleResourceBindingCancel"
          class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto transition-colors"
        >
          {{ $t('common.cancel') }}
        </button>
        <button
          v-if="pendingResourceDefinition"
          type="button"
          @click="confirmResourceBinding"
          :disabled="!selectedResourceHostId || bindingResource"
          class="inline-flex w-full justify-center rounded-md bg-purple-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 sm:ml-3 sm:w-auto disabled:cursor-not-allowed disabled:opacity-60 transition-colors"
        >
          {{ bindingResource ? $t('common.saving') : $t('applications.resourceBindingConfirm') }}
        </button>
        <button
          v-if="selectedResourceHostId && !pendingResourceDefinition"
          type="button"
          @click="confirmResourceTypeSelection"
          :disabled="!selectedResourceType || bindingResource"
          class="inline-flex w-full justify-center rounded-md bg-purple-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 sm:ml-3 sm:w-auto disabled:cursor-not-allowed disabled:opacity-60 transition-colors"
        >
          {{ bindingResource ? $t('common.saving') : $t('common.confirm') }}
        </button>
      </template>
    </Modal>

    <!-- Add Relationship Modal -->
    <Modal
      :open="showAddRelationshipModal"
      @close="closeAddRelationshipModal"
      :title="editingRelationshipId ? $t('applications.editRelationshipTitle') : $t('applications.addRelationshipTitle')"
      max-width="md"
    >
      <form @submit.prevent="addRelationship" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('applications.sourceHost') }} *</label>
          <select
            v-model="relationshipForm.from_host_id"
            required
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition-colors"
          >
            <option value="">{{ $t('hosts.pleaseSelect') }}</option>
            <option v-for="host in hosts" :key="host.id" :value="host.id">
              {{ host.ip }} - {{ host.hostname || $t('applications.unknown') }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('applications.targetHost') }} *</label>
          <select
            v-model="relationshipForm.to_host_id"
            required
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition-colors"
          >
            <option value="">{{ $t('hosts.pleaseSelect') }}</option>
            <option v-for="host in hosts" :key="host.id" :value="host.id">
              {{ host.ip }} - {{ host.hostname || $t('applications.unknown') }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('applications.relationshipType') }} *</label>
          <select
            v-model="relationshipForm.relationship_type"
            required
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition-colors"
          >
            <option value="">{{ $t('hosts.pleaseSelect') }}</option>
            <option value="depends_on">{{ $t('applications.dependsOn') }}</option>
            <option value="connects_to">{{ $t('applications.connectsTo') }}</option>
            <option value="runs_on">{{ $t('applications.runsOn') }}</option>
            <option value="member">{{ $t('applications.member') }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('applications.description') }}</label>
          <textarea
            v-model="relationshipForm.description"
            rows="2"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition-colors"
          />
        </div>
      </form>
      <template #footer>
        <button
          type="button"
          @click="closeAddRelationshipModal"
          class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto transition-colors"
        >
          {{ $t('common.cancel') }}
        </button>
        <button
          type="button"
          @click="addRelationship"
          :disabled="adding"
          class="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto disabled:opacity-50 transition-colors"
        >
          {{ adding ? $t('applications.adding') : (editingRelationshipId ? $t('applications.update') : $t('applications.add')) }}
        </button>
      </template>
    </Modal>

    <!-- Confirm Modal -->
    <ConfirmModal
      :open="showConfirmModal"
      @close="showConfirmModal = false"
      @confirm="handleConfirm"
      :title="$t('applications.confirmRemove')"
      :message="confirmMessage"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, reactive, nextTick, onBeforeUnmount, Transition } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { applicationsApi, type HostRelationship } from '@/api/applications'
import { hostsApi } from '@/api/hosts'
import Modal from '@/components/Modal.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import { useToastStore } from '@/stores/toast'
import {
  ServerIcon,
  ShareIcon,
  MagnifyingGlassIcon,
  ComputerDesktopIcon,
  GlobeAltIcon,
  ServerStackIcon,
  CloudIcon,
  Cog6ToothIcon,
  CircleStackIcon,
  ArrowDownOnSquareIcon,
  ArrowDownTrayIcon,
  PhotoIcon
} from '@heroicons/vue/24/outline'
import ApplicationCanvas from '@/components/ApplicationCanvas.vue'
import { CanvasNodeType } from '@/components/ApplicationCanvas/types'
import type { CanvasEdgeData, CanvasNodeData } from '@/components/ApplicationCanvas/types'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const toastStore = useToastStore()

const application = ref<any>(null)
const hosts = ref<any[]>([])
const availableHosts = ref<any[]>([])
const canvasNodes = ref<CanvasNodeData[]>([])
const canvasEdges = ref<CanvasEdgeData[]>([])
const resourceNodes = ref<CanvasNodeData[]>([])
const loading = ref(false)
const showAddHostModal = ref(false)
const showAddRelationshipModal = ref(false)
const selectedHostIds = ref<number[]>([])
const adding = ref(false)
const relationshipForm = ref<Partial<HostRelationship>>({})
const showConfirmModal = ref(false)
const confirmAction = ref<(() => void) | null>(null)
const confirmMessage = ref('')
const hostSearchTerm = ref('')
const sortKey = ref<'ip' | 'hostname' | 'os_type' | 'device_type'>('ip')
const sortOrder = ref<'asc' | 'desc'>('asc')
const relationships = ref<any[]>([])
const relationshipSearchTerm = ref('')
const editingRelationshipId = ref<number | null>(null)
const canvasRef = ref<InstanceType<typeof ApplicationCanvas> | null>(null)
const canvasContainerRef = ref<HTMLElement | null>(null)
const logicFlowInstance = ref<any>(null)
const selectedCanvasNode = ref<CanvasNodeData | null>(null)
const selectedCanvasEdge = ref<CanvasEdgeData | null>(null)
const nodeBindingHostId = ref<string>('')
const updatingNodeBinding = ref(false)
const edgeForm = reactive({
  relationship_type: 'member',
  description: '',
  edgeType: 'polyline',
  strokeDasharray: '',
  strokeWidth: 2,
  stroke: '#94a3b8'
})
// 预设的常用颜色（黑色作为默认开头）
const presetColors = [
  '#000000', // 黑色（默认）
  '#3b82f6', // 蓝色
  '#10b981', // 绿色
  '#ef4444', // 红色
  '#f59e0b', // 橙色
  '#8b5cf6', // 紫色
  '#94a3b8', // 灰色
  '#06b6d4', // 青色
]
const updatingEdge = ref(false)
const suppressedEdgeRemovals = new Set<string>()
const hostLibraryKeyword = ref('')
const hostLibraryAddingId = ref<number | null>(null)
const selectedLayout = ref<'grid' | 'horizontal' | 'vertical'>('grid')
const showEdgeStyleMenu = ref(false)
const resourceLabel = ref('')
const isCanvasFullscreen = ref(false)
const draggingResourceKey = ref<string | null>(null)
const isSavingGraph = ref(false)
const isExportingGraph = ref(false)
// 侧边栏宽度控制（仅在全屏模式下可调整）
const leftSidebarWidth = ref(288) // 默认 w-72 = 288px
const rightSidebarWidth = ref(288) // 默认 w-72 = 288px
const minSidebarWidth = 200
const maxSidebarWidth = 600
const isResizingLeft = ref(false)
const isResizingRight = ref(false)

type HostTag = {
  id?: number
  name?: string
  color?: string
}

const idsEqual = (a: string | number | undefined, b: string | number | undefined) =>
  a !== undefined && b !== undefined && String(a) === String(b)

const filteredHosts = computed(() => {
  const keyword = hostSearchTerm.value.trim().toLowerCase()
  let result = hosts.value.slice()
  if (keyword) {
    result = result.filter((host) => {
      const ip = host.ip?.toLowerCase() || ''
      const hostname = host.hostname?.toLowerCase() || ''
      const osType = host.os_type?.toLowerCase() || ''
      const tags: string[] = Array.isArray(host.tags)
        ? host.tags.map((t: HostTag) => t.name?.toLowerCase() || '')
        : []
      return (
        ip.includes(keyword) ||
        hostname.includes(keyword) ||
        osType.includes(keyword) ||
        tags.some((tag: string) => tag.includes(keyword))
      )
    })
  }
  result.sort((a, b) => {
    const aValue = (a[sortKey.value] ?? '').toString().toLowerCase()
    const bValue = (b[sortKey.value] ?? '').toString().toLowerCase()
    if (aValue < bValue) return sortOrder.value === 'asc' ? -1 : 1
    if (aValue > bValue) return sortOrder.value === 'asc' ? 1 : -1
    return 0
  })
  return result
})

const summaryStats = computed(() => ({
  totalHosts: hosts.value.length,
  physicalHosts: hosts.value.filter((host) => host.is_physical).length,
  virtualHosts: hosts.value.filter((host) => host.is_physical === false).length
}))

const selectableHosts = computed(() => {
  const hostMap = new Map<number, any>()
  hosts.value.forEach((host) => {
    if (host?.id) {
      hostMap.set(host.id, host)
    }
  })
  availableHosts.value.forEach((host) => {
    if (host?.id && !hostMap.has(host.id)) {
      hostMap.set(host.id, host)
    }
  })
  return Array.from(hostMap.values())
})

const canUpdateBinding = computed(() => {
  if (!selectedCanvasNode.value) return false
  const target =
    nodeBindingHostId.value === '' || nodeBindingHostId.value === null
      ? null
      : Number(nodeBindingHostId.value)
  if (!target) return false
  return target !== selectedCanvasNode.value.bindingHostId
})

const relationshipTypeOptions = computed(() => [
  { value: 'member', label: t('applications.member') },
  { value: 'depends_on', label: t('applications.dependsOn') },
  { value: 'connects_to', label: t('applications.connectsTo') },
  { value: 'runs_on', label: t('applications.runsOn') }
])

const filteredAvailableHostsForCanvas = computed(() => {
  const keyword = hostLibraryKeyword.value.trim().toLowerCase()
  if (!keyword) return availableHosts.value
  return availableHosts.value.filter((host) => {
    const ip = host.ip?.toLowerCase() || ''
    const hostname = host.hostname?.toLowerCase() || ''
    const vendor = host.vendor?.toLowerCase() || ''
    return ip.includes(keyword) || hostname.includes(keyword) || vendor.includes(keyword)
  })
})

const DEFAULT_TYPE_COLORS: Record<CanvasNodeType, string> = {
  [CanvasNodeType.HOST]: '#2563eb',
  [CanvasNodeType.NETWORK]: '#0ea5e9',
  [CanvasNodeType.STORAGE]: '#a855f7',
  [CanvasNodeType.OBJECT_STORAGE]: '#f97316',
  [CanvasNodeType.DATABASE]: '#ef4444',
  [CanvasNodeType.SERVICE]: '#6366f1',
  [CanvasNodeType.CUSTOM]: '#0f172a',
}

const COLOR_PRESETS = [
  '#2563eb',
  '#0ea5e9',
  '#22c55e',
  '#a855f7',
  '#f97316',
  '#ef4444',
  '#6366f1',
  '#14b8a6',
  '#0f172a'
]

const generateNodeId = (prefix = 'resource') =>
  `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`

interface ResourceDefinition {
  key: 'host' | 'network' | 'storage' | 'objectStorage' | 'service' | 'database'
  type: CanvasNodeType
  icon: CanvasNodeType
  color: string
  label: string
  description: string
}

const RESOURCE_ICON_COMPONENTS = {
  host: ComputerDesktopIcon,
  network: GlobeAltIcon,
  storage: ServerStackIcon,
  objectStorage: CloudIcon,
  service: Cog6ToothIcon,
  database: CircleStackIcon,
}

const resourceLibrary = computed<ResourceDefinition[]>(() => [
  {
    key: 'host',
    type: CanvasNodeType.HOST,
    icon: CanvasNodeType.HOST,
    color: DEFAULT_TYPE_COLORS[CanvasNodeType.HOST],
    label: t('applications.resourcePalette.host'),
    description: t('applications.resourcePalette.hostDesc'),
  },
  {
    key: 'network',
    type: CanvasNodeType.NETWORK,
    icon: CanvasNodeType.NETWORK,
    color: DEFAULT_TYPE_COLORS[CanvasNodeType.NETWORK],
    label: t('applications.resourcePalette.network'),
    description: t('applications.resourcePalette.networkDesc'),
  },
  {
    key: 'storage',
    type: CanvasNodeType.STORAGE,
    icon: CanvasNodeType.STORAGE,
    color: DEFAULT_TYPE_COLORS[CanvasNodeType.STORAGE],
    label: t('applications.resourcePalette.storage'),
    description: t('applications.resourcePalette.storageDesc'),
  },
  {
    key: 'objectStorage',
    type: CanvasNodeType.OBJECT_STORAGE,
    icon: CanvasNodeType.OBJECT_STORAGE,
    color: DEFAULT_TYPE_COLORS[CanvasNodeType.OBJECT_STORAGE],
    label: t('applications.resourcePalette.objectStorage'),
    description: t('applications.resourcePalette.objectStorageDesc'),
  },
  {
    key: 'service',
    type: CanvasNodeType.SERVICE,
    icon: CanvasNodeType.SERVICE,
    color: DEFAULT_TYPE_COLORS[CanvasNodeType.SERVICE],
    label: t('applications.resourcePalette.service'),
    description: t('applications.resourcePalette.serviceDesc'),
  },
  {
    key: 'database',
    type: CanvasNodeType.DATABASE,
    icon: CanvasNodeType.DATABASE,
    color: DEFAULT_TYPE_COLORS[CanvasNodeType.DATABASE],
    label: t('applications.resourcePalette.database'),
    description: t('applications.resourcePalette.databaseDesc'),
  },
])

const resourceLibraryMap = computed<Map<string, ResourceDefinition>>(() => {
  const map = new Map<string, ResourceDefinition>()
  resourceLibrary.value.forEach((item) => {
    map.set(item.key, item)
  })
  return map
})

const getTypeColor = (type: CanvasNodeType): string => {
  return DEFAULT_TYPE_COLORS[type] || DEFAULT_TYPE_COLORS[CanvasNodeType.HOST]
}

const showResourceBindingModal = ref(false)
const pendingResourceDefinition = ref<ResourceDefinition | null>(null)
const pendingResourcePosition = ref<{ x: number; y: number } | null>(null)
const selectedResourceHostId = ref<number | null>(null)
const resourceBindingSearch = ref('')
const bindingResource = ref(false)
const pendingResourceSelectionHosts = ref<number[]>([])
const selectedResourceType = ref<string | null>(null)
// 存储待添加的主机信息（用于在资源选择弹窗中显示，但还未真正添加到应用）
const pendingHostsInfo = ref<Map<number, any>>(new Map())

const currentSelectedHost = computed(() => {
  if (!selectedResourceHostId.value) return null
  // 优先从待添加的主机信息中查找，如果找不到再从已添加的主机中查找
  const pendingHost = pendingHostsInfo.value.get(selectedResourceHostId.value)
  if (pendingHost) return pendingHost
  return hosts.value.find((h: any) => h.id === selectedResourceHostId.value) || null
})

const filteredBindableHosts = computed(() => {
  const map = new Map<number, { host: any; inApplication: boolean }>()

  hosts.value.forEach((host) => {
    if (host?.id) {
      map.set(host.id, { host, inApplication: true })
    }
  })

  availableHosts.value.forEach((host) => {
    if (host?.id && !map.has(host.id)) {
      map.set(host.id, { host, inApplication: false })
    }
  })

  let list = Array.from(map.values())
  const keyword = resourceBindingSearch.value.trim().toLowerCase()
  if (keyword) {
    list = list.filter(({ host }) => {
      const ip = host.ip?.toLowerCase() || ''
      const hostname = host.hostname?.toLowerCase() || ''
      const vendor = host.vendor?.toLowerCase() || ''
      const tags = Array.isArray(host.tags) ? host.tags.map((tag: any) => tag.name?.toLowerCase?.()).join(' ') : ''
      return ip.includes(keyword) || hostname.includes(keyword) || vendor.includes(keyword) || tags.includes(keyword)
    })
  }

  return list.sort((a, b) => {
    if (a.inApplication === b.inApplication) {
      return (a.host.ip || '').localeCompare(b.host.ip || '')
    }
    return a.inApplication ? -1 : 1
  })
})

const selectedHostDetails = computed(() => {
  const data: any = selectedCanvasNode.value?.data || {}
  const details: Array<{ label: string; value: string }> = []

  if (data.hostname || data.ip) {
    details.push({
      label: t('hosts.hostname'),
      value: data.hostname || data.ip || '-'
    })
  }

  if (data.ip) {
    details.push({
      label: t('hosts.ip'),
      value: data.ip
    })
  }

  if (data.os_type || data.os_version) {
    details.push({
      label: t('hosts.osType'),
      value: [data.os_type, data.os_version].filter(Boolean).join(' ') || '-'
    })
  }

  if (data.device_type) {
    details.push({
      label: t('hosts.deviceType'),
      value: data.device_type
    })
  }

  if (data.platform_name) {
    details.push({
      label: t('hosts.platform'),
      value: data.platform_name
    })
  }

  if (data.cpu_info || data.cpu_cores) {
    details.push({
      label: t('hosts.cpuInfo'),
      value: [data.cpu_info, data.cpu_cores ? `${t('hosts.cpuCores')}: ${data.cpu_cores}` : ''].filter(Boolean).join(' · ') || '-'
    })
  }

  if (data.memory_total) {
    details.push({
      label: t('hosts.memory'),
      value: formatMetric(data.memory_total)
    })
  }

  if (data.disk_total_size) {
    details.push({
      label: t('hosts.disk'),
      value: formatMetric(data.disk_total_size)
    })
  }

  if (Array.isArray(data.tags) && data.tags.length > 0) {
    details.push({
      label: t('hosts.tags'),
      value: data.tags.map((tag: any) => tag.name).join(', ')
    })
  }

  return details
})

const filteredRelationships = computed(() => {
  const keyword = relationshipSearchTerm.value.trim().toLowerCase()
  if (!keyword) return relationships.value
  return relationships.value.filter((relation) => {
    const fromHost = getHostLabel(relation.from_host_id).toLowerCase()
    const toHost = getHostLabel(relation.to_host_id).toLowerCase()
    const type = relation.relationship_type?.toLowerCase() || ''
    const description = relation.description?.toLowerCase() || ''
    return (
      fromHost.includes(keyword) ||
      toHost.includes(keyword) ||
      type.includes(keyword) ||
      description.includes(keyword)
    )
  })
})

const setSortKey = (key: 'ip' | 'hostname' | 'os_type' | 'device_type') => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

const formatMetric = (value?: number, suffix = 'GB') => {
  if (value === null || value === undefined) return '-'
  const numericValue = Number(value)
  if (Number.isNaN(numericValue)) return '-'
  const rounded = Math.round((numericValue + Number.EPSILON) * 100) / 100
  return `${rounded} ${suffix}`
}

const getHostTags = (host: any): HostTag[] => {
  if (!Array.isArray(host.tags) || host.tags.length === 0) return []
  return host.tags
}

const getHostLabel = (hostId: number) => {
  const host = hosts.value.find((item) => item.id === hostId)
  if (!host) return `#${hostId}`
  return host.hostname || host.ip || `#${hostId}`
}


const getStatusLabel = (node: any) => {
  if (typeof node?.is_physical === 'boolean') {
    return node.is_physical ? t('applications.physicalHost') : t('applications.virtualHost')
  }
  if (node?.group) {
    const key = `applications.nodeGroup.${node.group}`
    const translated = t(key)
    return translated === key ? node.group : translated
  }
  return ''
}

const getRelationshipLabel = (type?: string) => {
  switch (type) {
    case 'depends_on':
      return t('applications.dependsOn')
    case 'connects_to':
      return t('applications.connectsTo')
    case 'runs_on':
      return t('applications.runsOn')
    case 'member':
      return t('applications.member')
    default:
      return type || ''
  }
}

const computeInitialPosition = (index: number) => {
  const column = index % 4
  const row = Math.floor(index / 4)
  const paddingX = 180
  const paddingY = 150
  const gapX = 220
  const gapY = 160
  return {
    x: paddingX + column * gapX,
    y: paddingY + row * gapY
  }
}

const refreshSelections = () => {
  if (selectedCanvasNode.value) {
    const updatedNode = canvasNodes.value.find((node) => node.id === selectedCanvasNode.value?.id)
    selectedCanvasNode.value = updatedNode || null
    nodeBindingHostId.value = updatedNode?.bindingHostId ? String(updatedNode.bindingHostId) : ''
    resourceLabel.value =
      updatedNode && !updatedNode.bindingHostId ? updatedNode.label : ''
  }
  if (selectedCanvasEdge.value) {
    // 从 canvasEdges 中获取最新的边数据，确保使用保存的样式
    const updatedEdge = canvasEdges.value.find((edge) => {
      if (selectedCanvasEdge.value?.id && edge.id) {
        return String(edge.id) === String(selectedCanvasEdge.value.id)
      }
      return edge.source === selectedCanvasEdge.value?.source && edge.target === selectedCanvasEdge.value?.target
    })
    selectedCanvasEdge.value = updatedEdge || selectedCanvasEdge.value
    if (updatedEdge) {
      // 从最新的边数据中加载样式，确保每条边独立
      edgeForm.relationship_type = updatedEdge.relationshipType || 'member'
      edgeForm.description = updatedEdge.description || ''
      edgeForm.edgeType = updatedEdge.edgeType || 'polyline'
      edgeForm.strokeDasharray = updatedEdge.strokeDasharray || ''
      edgeForm.strokeWidth = typeof updatedEdge.strokeWidth === 'number' 
        ? updatedEdge.strokeWidth 
        : (updatedEdge.strokeWidth === 'thin' ? 1 : updatedEdge.strokeWidth === 'thick' ? 3 : 2)
      edgeForm.stroke = updatedEdge.stroke || '#94a3b8'
    }
  }
}

const syncCanvasEdgesFromRelationships = () => {
  if (!relationships.value.length) {
    // 如果没有关系，清空所有边
    canvasEdges.value = []
    return
  }
  
  // 创建关系ID到关系的映射
  const relationMap = new Map<number, any>()
  relationships.value.forEach((relation) => {
    if (relation?.id) {
      relationMap.set(relation.id, relation)
    }
  })
  
  // 创建已存在的边的映射（通过 source-target 或 id）
  const existingEdgesMap = new Map<string, CanvasEdgeData>()
  canvasEdges.value.forEach((edge) => {
    const key = edge.id ? String(edge.id) : `${edge.source}-${edge.target}`
    existingEdgesMap.set(key, edge)
  })
  
  // 从关系数据创建或更新边
  const newEdges: CanvasEdgeData[] = []
  relationships.value.forEach((relation) => {
    if (!relation?.id || !relation.from_host_id || !relation.to_host_id) return
    
    const sourceId = String(relation.from_host_id)
    const targetId = String(relation.to_host_id)
    const edgeKey = String(relation.id)
    
    // 查找已存在的边
    const existingEdge = existingEdgesMap.get(edgeKey) || existingEdgesMap.get(`${sourceId}-${targetId}`)
    
    if (existingEdge) {
      // 更新已存在的边，保留所有样式属性
      newEdges.push({
        ...existingEdge,
        id: String(relation.id),
        source: sourceId,
        target: targetId,
        relationshipType: relation.relationship_type || existingEdge.relationshipType || 'member',
        label: getRelationshipLabel(relation.relationship_type || existingEdge.relationshipType || 'member'),
        description: relation.description || existingEdge.description || '',
        // 保留样式属性
        edgeType: existingEdge.edgeType || 'polyline',
        strokeDasharray: existingEdge.strokeDasharray || '',
        strokeWidth: existingEdge.strokeWidth || 2,
        stroke: existingEdge.stroke || '#94a3b8',
      data: {
          ...(existingEdge.data || {}),
        relationship: relation
      }
      })
    } else {
      // 创建新边，设置默认样式属性
      newEdges.push({
        id: String(relation.id),
        source: sourceId,
        target: targetId,
        relationshipType: relation.relationship_type || 'member',
        label: getRelationshipLabel(relation.relationship_type || 'member'),
        description: relation.description || '',
        // 设置默认样式属性
        edgeType: 'polyline',
        strokeDasharray: '',
        strokeWidth: 2,
        stroke: '#94a3b8',
        data: { relationship: relation }
      })
    }
  })
  
  canvasEdges.value = newEdges
  refreshSelections()
}

const normalizeResourceNode = (raw: any, index = 0): CanvasNodeData => {
  const position = computeInitialPosition(index)
  const bindingHostId =
    raw?.bindingHostId !== undefined && raw?.bindingHostId !== null
      ? Number(raw.bindingHostId)
      : undefined
  const resourceKey = raw?.data?.resourceKey || raw?.resourceKey || raw?.key
  const libraryInfo = resourceKey ? resourceLibraryMap.value.get(resourceKey) : undefined
  // 优先使用保存的图标类型，如果没有则使用资源库的类型，最后默认 CUSTOM
  const savedIconType = raw?.icon || raw?.data?.iconType
  const icon = savedIconType || libraryInfo?.type || CanvasNodeType.CUSTOM
  const nodeType = (raw?.type || icon) as CanvasNodeType
  const color = raw?.color || raw?.data?.customColor || raw?.data?.color || getTypeColor(nodeType)
  const label =
    raw?.label ||
    libraryInfo?.label ||
    raw?.data?.label ||
    (bindingHostId ? `#${bindingHostId}` : t('applications.genericResource'))
  const status =
    raw?.status || raw?.data?.displayStatus || libraryInfo?.description || ''

  return {
    id: raw?.id ?? generateNodeId('resource'),
    type: nodeType,
    x: typeof raw?.x === 'number' ? raw.x : position.x,
    y: typeof raw?.y === 'number' ? raw.y : position.y,
    label,
    color,
    icon,
    bindingHostId,
    status,
    data: {
      ...(raw?.data || {}),
      resource: true,
      resourceKey: resourceKey || libraryInfo?.key || nodeType,
      displayStatus: status,
      color,
      label,
      iconType: icon,
      customColor: color
    }
  }
}

const syncCanvasData = (graph: { nodes?: any[]; edges?: any[]; resourceNodes?: any[]; metadata?: Record<string, any> }) => {
  const nodes = Array.isArray(graph?.nodes) ? graph.nodes ?? [] : []
  const edges = Array.isArray(graph?.edges) ? graph.edges ?? [] : []
  const resourcePayload = Array.isArray(graph?.resourceNodes) ? graph.resourceNodes ?? [] : []

  if (graph?.metadata?.layout && ['grid', 'horizontal', 'vertical'].includes(graph.metadata.layout)) {
    selectedLayout.value = graph.metadata.layout
  }

  const hostIndex = new Map<number, any>()
  hosts.value.forEach((host) => {
    if (host?.id) {
      hostIndex.set(host.id, host)
    }
  })

  const normalizedResourceNodes: CanvasNodeData[] = resourcePayload.map((raw, idx) =>
    normalizeResourceNode(raw, idx)
  )
  const overlayByHostId = new Map<number, CanvasNodeData>()
  const resourceIdSet = new Set<string | number>()
  normalizedResourceNodes.forEach((node) => {
    resourceIdSet.add(node.id)
    if (node.bindingHostId) {
      overlayByHostId.set(node.bindingHostId, node)
    }
  })

  const hostNodes: CanvasNodeData[] = []
  const seenHostIds = new Set<number>()

  nodes.forEach((rawNode: any, index: number) => {
    const hostId =
      rawNode?.bindingHostId !== undefined && rawNode?.bindingHostId !== null
        ? Number(rawNode.bindingHostId)
        : typeof rawNode?.id === 'number'
          ? rawNode.id
          : undefined

    if (hostId && hostIndex.has(hostId)) {
      const hostRecord = hostIndex.get(hostId)
      const overlay = overlayByHostId.get(hostId)
      const basePosition = computeInitialPosition(index)
      const x = typeof rawNode?.x === 'number' ? rawNode.x : overlay?.x ?? basePosition.x
      const y = typeof rawNode?.y === 'number' ? rawNode.y : overlay?.y ?? basePosition.y
      // 优先使用保存的图标类型，如果没有则默认使用 HOST 类型，不再使用设备类型映射
      const savedIconType = overlay?.icon || rawNode?.icon || rawNode?.data?.iconType
      const icon = savedIconType || CanvasNodeType.HOST
      const nodeType = (overlay?.type || rawNode?.type || icon) as CanvasNodeType
      const color = overlay?.color || rawNode?.color || rawNode?.data?.customColor || rawNode?.data?.color || getTypeColor(nodeType)
      // label 优先使用主机名，而不是资源类型的名称
      const label =
        rawNode?.label ||
        hostRecord.hostname ||
        hostRecord.ip ||
        overlay?.label ||
        `#${hostId}`
      const status = overlay?.status || getStatusLabel(hostRecord)

      hostNodes.push({
        id: hostId,
        type: nodeType,
        x,
        y,
        label,
        bindingHostId: hostId,
        status,
        icon,
        color,
        data: {
          ...hostRecord,
          ...(rawNode?.data || {}),
          ...(overlay?.data || {}),
          resource: !!overlay,
          color,
          iconType: icon,
          customColor: color
        }
      })
      seenHostIds.add(hostId)
    } else if (!resourceIdSet.has(rawNode?.id)) {
      const normalized = normalizeResourceNode(rawNode, normalizedResourceNodes.length + index)
      resourceIdSet.add(normalized.id)
      if (normalized.bindingHostId) {
        overlayByHostId.set(normalized.bindingHostId, normalized)
        seenHostIds.add(normalized.bindingHostId)
      }
      normalizedResourceNodes.push(normalized)
    }
  })

  hosts.value.forEach((host, hostIndexPosition) => {
    if (!seenHostIds.has(host.id)) {
      const position = computeInitialPosition(hostNodes.length + hostIndexPosition)
      // 旧数据默认使用 HOST 类型
      const nodeType = CanvasNodeType.HOST
      const color = getTypeColor(nodeType)
      hostNodes.push({
        id: host.id,
        type: nodeType,
        x: position.x,
        y: position.y,
        label: host.hostname || host.ip || `#${host.id}`,
        bindingHostId: host.id,
        status: getStatusLabel(host),
        icon: nodeType,
        color,
        data: {
          ...host,
          resource: false,
          color,
          iconType: nodeType
        }
      })
    }
  })

  resourceNodes.value = normalizedResourceNodes.map((node) => {
    if (!node.bindingHostId) {
      return node
    }
    const hostRecord = hostIndex.get(node.bindingHostId)
    if (!hostRecord) {
      return {
        ...node,
        bindingHostId: undefined,
        data: { resource: true, label: node.label },
        status: ''
      }
    }
    // 优先使用保存的图标类型，如果没有则默认使用 HOST 类型，不再使用设备类型映射
    const savedIconType = node.icon || node.data?.iconType
    const icon = savedIconType || CanvasNodeType.HOST
    const nodeType = node.type || icon
    const color = node.color || node.data?.customColor || node.data?.color || getTypeColor(nodeType)
    // label 优先使用主机名，而不是资源类型的名称
    const label = hostRecord.hostname || hostRecord.ip || node.label || `#${node.bindingHostId}`
    return {
      ...node,
      type: nodeType,
      icon,
      color,
      label,
      status: getStatusLabel(hostRecord),
      data: { ...hostRecord, resource: true, color, iconType: icon, customColor: color, label }
    }
  })

  const unboundResources = resourceNodes.value.filter((node) => !node.bindingHostId)
  canvasNodes.value = [...hostNodes, ...unboundResources]

  // 先处理从 graph 数据中来的边
  const relationMap = new Map<number, any>()
  relationships.value.forEach((relation) => {
    if (relation?.id) {
      relationMap.set(relation.id, relation)
    }
  })

      const edgesFromGraph = edges.map((edge: any) => {
    const relation = edge?.id ? relationMap.get(Number(edge.id)) : null
    const relationshipType = edge?.relationshipType || relation?.relationship_type || edge?.label
    return {
          id: edge?.id ? String(edge.id) : undefined,
          source: String(edge?.source ?? edge?.from ?? ''),
          target: String(edge?.target ?? edge?.to ?? ''),
      relationshipType,
      label: relationshipType ? getRelationshipLabel(relationshipType) : edge?.label,
      description: edge?.description !== undefined ? edge.description : (relation?.description || ''),
      // 直接使用 graph 中的样式属性（从服务器保存的），保留所有值包括空字符串
      edgeType: edge?.edgeType !== undefined ? edge.edgeType : 'polyline',
      strokeDasharray: edge?.strokeDasharray !== undefined ? edge.strokeDasharray : '',
      strokeWidth: edge?.strokeWidth !== undefined ? edge.strokeWidth : 2,
      stroke: edge?.stroke !== undefined ? edge.stroke : '#94a3b8',
      data: {
        ...(edge?.data || {}),
        relationship: relation
      }
    }
  })

  // 从关系数据同步边（确保所有关系都有对应的边）
  syncCanvasEdgesFromRelationships()
  
  // 合并从 graph 来的边和从关系同步来的边
  // 优先使用从 graph 加载的边（包含样式信息），然后补充关系同步来的边
  const edgesMap = new Map<string, CanvasEdgeData>()
  // 先添加从关系同步来的边（作为基础）
  canvasEdges.value.forEach(edge => {
    if (edge.id) {
      edgesMap.set(String(edge.id), edge)
    } else {
      edgesMap.set(`${edge.source}-${edge.target}`, edge)
    }
  })
  // 再添加从 graph 来的边（优先保留样式信息，覆盖关系同步的边）
  edgesFromGraph.forEach(edge => {
    if (edge.id) {
      const existingEdge = edgesMap.get(String(edge.id))
      if (existingEdge) {
        // 合并：优先使用 graph 中的样式（从服务器保存的），但保留关系数据
        edgesMap.set(String(edge.id), {
          ...existingEdge,
          // 优先使用 graph 中的样式属性（从服务器加载的），使用 !== undefined 检查保留空字符串
          edgeType: edge.edgeType !== undefined ? edge.edgeType : (existingEdge.edgeType !== undefined ? existingEdge.edgeType : 'polyline'),
          strokeDasharray: edge.strokeDasharray !== undefined ? edge.strokeDasharray : (existingEdge.strokeDasharray !== undefined ? existingEdge.strokeDasharray : ''),
          strokeWidth: edge.strokeWidth !== undefined ? edge.strokeWidth : (existingEdge.strokeWidth !== undefined ? existingEdge.strokeWidth : 2),
          stroke: edge.stroke !== undefined ? edge.stroke : (existingEdge.stroke !== undefined ? existingEdge.stroke : '#94a3b8'),
          // 保留其他属性
          id: edge.id || existingEdge.id,
          source: edge.source || existingEdge.source,
          target: edge.target || existingEdge.target,
          relationshipType: edge.relationshipType || existingEdge.relationshipType,
          label: edge.label || existingEdge.label,
          description: edge.description !== undefined ? edge.description : (existingEdge.description || ''),
          // 确保关系数据不丢失
          data: {
            ...(existingEdge.data || {}),
            ...(edge.data || {})
          }
        })
      } else {
        edgesMap.set(String(edge.id), edge)
      }
    } else if (edge.source && edge.target) {
      const key = `${edge.source}-${edge.target}`
      const existingEdge = edgesMap.get(key)
      if (existingEdge) {
        // 合并：优先使用 graph 中的样式（从服务器保存的），但保留关系数据
        edgesMap.set(key, {
          ...existingEdge,
          // 优先使用 graph 中的样式属性（从服务器加载的），使用 !== undefined 检查保留空字符串
          edgeType: edge.edgeType !== undefined ? edge.edgeType : (existingEdge.edgeType !== undefined ? existingEdge.edgeType : 'polyline'),
          strokeDasharray: edge.strokeDasharray !== undefined ? edge.strokeDasharray : (existingEdge.strokeDasharray !== undefined ? existingEdge.strokeDasharray : ''),
          strokeWidth: edge.strokeWidth !== undefined ? edge.strokeWidth : (existingEdge.strokeWidth !== undefined ? existingEdge.strokeWidth : 2),
          stroke: edge.stroke !== undefined ? edge.stroke : (existingEdge.stroke !== undefined ? existingEdge.stroke : '#94a3b8'),
          // 保留其他属性
          id: edge.id || existingEdge.id,
          source: edge.source || existingEdge.source,
          target: edge.target || existingEdge.target,
          relationshipType: edge.relationshipType || existingEdge.relationshipType,
          label: edge.label || existingEdge.label,
          description: edge.description !== undefined ? edge.description : (existingEdge.description || ''),
          // 确保关系数据不丢失
          data: {
            ...(existingEdge.data || {}),
            ...(edge.data || {})
          }
        })
      } else {
        edgesMap.set(key, edge)
      }
    }
  })
  
  canvasEdges.value = Array.from(edgesMap.values())

  refreshSelections()
}

const clearCanvasSelection = () => {
  selectedCanvasNode.value = null
  selectedCanvasEdge.value = null
  showEdgeStyleMenu.value = false // 关闭样式菜单
  nodeBindingHostId.value = ''
  edgeForm.relationship_type = 'member'
  edgeForm.description = ''
  edgeForm.edgeType = 'polyline'
  edgeForm.strokeDasharray = ''
  edgeForm.strokeWidth = 2
  edgeForm.stroke = '#94a3b8'
  resourceLabel.value = ''
}

const handleCanvasReady = (lf: any) => {
  logicFlowInstance.value = lf
}

const handleCanvasNodeClick = (node: CanvasNodeData) => {
  // 确保节点数据是最新的
  const latestNode = canvasNodes.value.find(n => idsEqual(n.id, node.id) || idsEqual(n.bindingHostId, node.bindingHostId)) || node
  selectedCanvasNode.value = {
    ...latestNode,
    // 确保数据包含完整的主机信息
    data: latestNode.data || node.data || {}
  }
  selectedCanvasEdge.value = null
  nodeBindingHostId.value = latestNode.bindingHostId ? String(latestNode.bindingHostId) : ''
  if (latestNode.bindingHostId) {
    const overlay = resourceNodes.value.find((overlayNode) => overlayNode.bindingHostId === latestNode.bindingHostId)
    resourceLabel.value = overlay?.label || latestNode.label
  } else {
    resourceLabel.value = latestNode.label
  }
}

const handleCanvasEdgeClick = (edge: CanvasEdgeData) => {
  // 从 canvasEdges 中获取最新的边数据，确保使用保存的样式
  const latestEdge = canvasEdges.value.find(e => 
    (e.id && edge.id && String(e.id) === String(edge.id)) ||
    (e.source === edge.source && e.target === edge.target)
  ) || edge
  
  selectedCanvasEdge.value = latestEdge
  selectedCanvasNode.value = null
  showEdgeStyleMenu.value = false // 关闭样式菜单
  
  // 从最新的边数据中加载样式，确保每条边独立
  edgeForm.relationship_type = latestEdge.relationshipType || 'member'
  edgeForm.description = latestEdge.description || ''
  // 使用 !== undefined 检查保留空字符串和 falsy 值
  edgeForm.edgeType = latestEdge.edgeType !== undefined ? latestEdge.edgeType : 'polyline'
  edgeForm.strokeDasharray = latestEdge.strokeDasharray !== undefined ? latestEdge.strokeDasharray : ''
  edgeForm.strokeWidth = typeof latestEdge.strokeWidth === 'number' 
    ? latestEdge.strokeWidth 
    : (latestEdge.strokeWidth === 'thin' ? 1 : latestEdge.strokeWidth === 'thick' ? 3 : 2)
  edgeForm.stroke = latestEdge.stroke !== undefined ? latestEdge.stroke : '#94a3b8'
}

const handleCanvasBlankClick = () => {
  clearCanvasSelection()
}

const handleCanvasNodeMoved = (node: CanvasNodeData) => {
  const index = canvasNodes.value.findIndex((item) => idsEqual(item.id, node.id))
  if (index >= 0) {
    canvasNodes.value[index] = {
      ...canvasNodes.value[index],
      x: node.x,
      y: node.y
    }
  }
  canvasNodes.value = [...canvasNodes.value]
  if (node.bindingHostId) {
    const overlayIndex = resourceNodes.value.findIndex((item) => idsEqual(item.bindingHostId, node.bindingHostId))
    if (overlayIndex >= 0) {
      resourceNodes.value[overlayIndex] = {
        ...resourceNodes.value[overlayIndex],
        x: node.x,
        y: node.y
      }
      resourceNodes.value = [...resourceNodes.value]
    }
  } else {
    const resourceIndex = resourceNodes.value.findIndex((item) => idsEqual(item.id, node.id))
    if (resourceIndex >= 0) {
      resourceNodes.value[resourceIndex] = {
        ...resourceNodes.value[resourceIndex],
        x: node.x,
        y: node.y
      }
      resourceNodes.value = [...resourceNodes.value]
    }
  }
}

const updateNodeBinding = async () => {
  if (!selectedCanvasNode.value) return
  const currentBinding = selectedCanvasNode.value.bindingHostId
  const targetHostId =
    nodeBindingHostId.value === '' || nodeBindingHostId.value === null
      ? null
      : Number(nodeBindingHostId.value)

  if (!targetHostId || targetHostId === currentBinding) {
    return
  }

  updatingNodeBinding.value = true
  // 保存当前节点的原始 icon 和资源信息，以便在重新加载后恢复
  // 优先从 icon 字段获取，其次从 data.iconType，最后从 type 字段
  const originalIcon = selectedCanvasNode.value.icon || 
                       selectedCanvasNode.value.data?.iconType || 
                       selectedCanvasNode.value.type ||
                       CanvasNodeType.HOST
  const originalResourceKey = selectedCanvasNode.value.data?.resourceKey
  const originalColor = selectedCanvasNode.value.color || 
                        selectedCanvasNode.value.data?.customColor || 
                        selectedCanvasNode.value.data?.color
  
  try {
    const appId = parseInt(route.params.id as string)
    if (currentBinding) {
      await applicationsApi.removeHost(appId, currentBinding)
      // 更新本地状态：从 hosts 中移除旧绑定
      hosts.value = hosts.value.filter(h => h.id !== currentBinding)
    }
    await applicationsApi.addHosts(appId, [targetHostId])
    
    // 重新加载应用数据以确保与服务端同步（包括 hosts 和 graph）
    try {
      const [appRes, graphRes, relationshipRes] = await Promise.all([
        applicationsApi.getApplication(appId),
        applicationsApi.getGraph(appId).catch(() => ({ data: { nodes: [], edges: [] } })),
        applicationsApi.getRelationships(appId).catch(() => ({ data: [] }))
      ])
      
      // 更新应用和关系数据
      application.value = appRes.data
      relationships.value = relationshipRes.data || []
      
      // 更新 hosts（从应用数据中获取最新的 hosts）
      if (application.value.hosts) {
        hosts.value = application.value.hosts
      }
      
      // 在重新同步画布数据之前，确保 graph 数据中包含原始 icon 信息
      const graphData = graphRes.data || { nodes: [], edges: [] }
      
      // 删除所有指向旧 bindingHostId 的节点和资源节点
      if (graphData.nodes && Array.isArray(graphData.nodes)) {
        graphData.nodes = graphData.nodes.filter((node: any) => {
          const nodeHostId = node?.bindingHostId !== undefined && node?.bindingHostId !== null
            ? Number(node.bindingHostId)
            : typeof node?.id === 'number' ? node.id : undefined
          // 保留不是旧绑定主机的节点，或者是要更新为新绑定主机的节点
          return !nodeHostId || nodeHostId !== currentBinding || nodeHostId === targetHostId
        })
        
        // 获取新主机信息用于设置 label
        const newHostRecord = hosts.value.find(h => h.id === targetHostId)
        
        // 更新节点：将旧 bindingHostId 的节点更新为新 bindingHostId，并保持原始 icon
        graphData.nodes = graphData.nodes.map((node: any) => {
          const nodeHostId = node?.bindingHostId !== undefined && node?.bindingHostId !== null
            ? Number(node.bindingHostId)
            : typeof node?.id === 'number' ? node.id : undefined
          
          if (nodeHostId === currentBinding || (nodeHostId === targetHostId && originalIcon)) {
            // label 优先使用主机名
            const nodeLabel = newHostRecord?.hostname || newHostRecord?.ip || node.label || `#${targetHostId}`
            return {
              ...node,
              id: targetHostId,
            bindingHostId: targetHostId,
              icon: originalIcon || node.icon,
              label: nodeLabel,
              data: {
                ...(node.data || {}),
                iconType: originalIcon || node.data?.iconType || node.icon,
                resourceKey: originalResourceKey || node.data?.resourceKey,
                label: nodeLabel
              }
            }
          }
          return node
        })
      }
      
      if (graphData.resourceNodes && Array.isArray(graphData.resourceNodes)) {
        // 删除所有指向旧 bindingHostId 的资源节点
        graphData.resourceNodes = graphData.resourceNodes.filter((node: any) => {
          const nodeHostId = node?.bindingHostId !== undefined && node?.bindingHostId !== null
            ? Number(node.bindingHostId)
            : undefined
          return !nodeHostId || nodeHostId !== currentBinding
        })
        
        // 获取新主机信息用于设置 label
        const newHostRecord = hosts.value.find(h => h.id === targetHostId)
        
        // 更新资源节点：将指向新 bindingHostId 的资源节点保持原始 icon
        graphData.resourceNodes = graphData.resourceNodes.map((node: any) => {
          const nodeHostId = node?.bindingHostId !== undefined && node?.bindingHostId !== null
            ? Number(node.bindingHostId)
            : undefined
          
          if (nodeHostId === targetHostId) {
            // label 优先使用主机名
            const nodeLabel = newHostRecord?.hostname || newHostRecord?.ip || node.label || `#${targetHostId}`
            return {
              ...node,
              id: targetHostId,
              bindingHostId: targetHostId,
              icon: originalIcon || node.icon,
              label: nodeLabel,
              data: {
                ...(node.data || {}),
                iconType: originalIcon || node.data?.iconType || node.icon,
                resourceKey: originalResourceKey || node.data?.resourceKey,
                label: nodeLabel
              }
            }
          }
          return node
        })
      }
      
      // 重新同步画布数据（这会基于服务端数据重新构建所有节点，避免重复）
      syncCanvasData(graphData)
    } catch (error: any) {
      console.error('Failed to reload application data:', error)
    }
    
    // 等待画布更新
    await nextTick()
    
    // 手动更新新节点的 icon 和资源信息，确保保留原始 icon
    // 更新 canvasNodes 中对应节点的 icon
    canvasNodes.value = canvasNodes.value.map((node) => {
      if (idsEqual(node.bindingHostId, targetHostId)) {
        return {
          ...node,
          icon: originalIcon,
          type: originalIcon as CanvasNodeType,
          color: originalColor || node.color,
          data: {
            ...(node.data || {}),
            iconType: originalIcon,
            customColor: originalColor || node.data?.customColor || node.data?.color,
            color: originalColor || node.data?.customColor || node.data?.color,
            resourceKey: originalResourceKey || node.data?.resourceKey,
            resource: !!originalResourceKey || node.data?.resource || false
          }
        }
      }
      return node
    })
      
    // 更新 resourceNodes 中对应节点的 icon
    const existingResourceNode = resourceNodes.value.find(n => idsEqual(n.bindingHostId, targetHostId))
    if (existingResourceNode) {
      resourceNodes.value = resourceNodes.value.map((node) => {
        if (idsEqual(node.bindingHostId, targetHostId)) {
          return {
            ...node,
            icon: originalIcon,
            type: originalIcon as CanvasNodeType,
            color: originalColor || node.color,
            data: {
              ...(node.data || {}),
              iconType: originalIcon,
              customColor: originalColor || node.data?.customColor || node.data?.color,
              color: originalColor || node.data?.customColor || node.data?.color,
              resourceKey: originalResourceKey || node.data?.resourceKey,
              resource: true
            }
          }
        }
        return node
      })
      } else {
      // 如果 resourceNodes 中没有对应节点，创建一个新的资源节点
      const hostNode = canvasNodes.value.find(n => idsEqual(n.bindingHostId, targetHostId))
      if (hostNode) {
        resourceNodes.value = [
          ...resourceNodes.value,
          {
            ...hostNode,
            icon: originalIcon,
            type: originalIcon as CanvasNodeType,
            color: originalColor || hostNode.color,
            data: {
              ...(hostNode.data || {}),
              iconType: originalIcon,
              customColor: originalColor || hostNode.data?.customColor || hostNode.data?.color,
              color: originalColor || hostNode.data?.customColor || hostNode.data?.color,
              resourceKey: originalResourceKey || hostNode.data?.resourceKey || originalIcon,
              resource: true
            }
          }
        ]
      }
    }
        resourceNodes.value = [...resourceNodes.value]
    canvasNodes.value = [...canvasNodes.value]
    
    // 保存更新后的布局
    await saveCanvasLayout()
    
    // 更新选中节点，确保属性面板显示最新信息
    const updatedNode = canvasNodes.value.find(n => idsEqual(n.bindingHostId, targetHostId))
    if (updatedNode) {
      selectedCanvasNode.value = updatedNode
      nodeBindingHostId.value = String(targetHostId)
      if (updatedNode.bindingHostId) {
        const overlay = resourceNodes.value.find((overlayNode) => overlayNode.bindingHostId === updatedNode.bindingHostId)
        resourceLabel.value = overlay?.label || updatedNode.label
      } else {
        resourceLabel.value = updatedNode.label
      }
    }
    
    toastStore.success(t('applications.updateBindingSuccess'))
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('applications.updateBindingFailed'))
  } finally {
    updatingNodeBinding.value = false
  }
}

const deleteSelectedNode = () => {
  if (!selectedCanvasNode.value?.bindingHostId) return
  removeHost(selectedCanvasNode.value.bindingHostId)
}

// 实时应用边的样式（无需保存按钮）
const applyEdgeStyle = async (styleUpdate: Partial<typeof edgeForm>) => {
  if (!selectedCanvasEdge.value?.id) return
  
  // 更新edgeForm（用于UI显示）
  Object.assign(edgeForm, styleUpdate)
  
  const relationshipId = Number(selectedCanvasEdge.value.id)
  if (!relationshipId) return
  
  // 更新本地边的样式属性 - 确保每条边独立保存样式
  const edgeIndex = canvasEdges.value.findIndex(e => Number(e.id) === relationshipId)
  if (edgeIndex >= 0) {
    // 获取当前边的完整数据，只更新样式相关字段
    const currentEdge = canvasEdges.value[edgeIndex]
    const updatedEdge = {
      ...currentEdge,
      // 只更新样式相关的字段，保持其他字段不变
      edgeType: styleUpdate.edgeType !== undefined ? styleUpdate.edgeType : currentEdge.edgeType,
      strokeDasharray: styleUpdate.strokeDasharray !== undefined ? styleUpdate.strokeDasharray : currentEdge.strokeDasharray,
      strokeWidth: styleUpdate.strokeWidth !== undefined ? styleUpdate.strokeWidth : currentEdge.strokeWidth,
      stroke: styleUpdate.stroke !== undefined ? styleUpdate.stroke : currentEdge.stroke,
    }
    // 直接更新数组中的元素
    canvasEdges.value[edgeIndex] = updatedEdge
    // 同时更新 selectedCanvasEdge，确保选中状态同步
    selectedCanvasEdge.value = {
      ...selectedCanvasEdge.value,
      ...updatedEdge
    }
    // 注意：不在这里创建新数组，避免触发 renderGraph 重新渲染所有边
    // 我们直接更新 LogicFlow 中的边样式，而不是通过重新渲染整个图
    
    // 立即更新 LogicFlow 中的边样式 - 使用更新后的边数据，而不是 edgeForm
    if (logicFlowInstance.value && selectedCanvasEdge.value.id) {
      await nextTick()
      try {
        const lfEdge = logicFlowInstance.value.getEdgeModelById(String(selectedCanvasEdge.value.id))
        if (lfEdge) {
          // 如果边的类型改变了，需要重新创建边
          if (styleUpdate.edgeType && lfEdge.type !== styleUpdate.edgeType) {
            const sourceNode = lfEdge.sourceNodeId
            const targetNode = lfEdge.targetNodeId
            const text = lfEdge.text?.value || ''
            const properties = lfEdge.properties || {}
            logicFlowInstance.value.deleteEdge(String(selectedCanvasEdge.value.id))
            await nextTick()
            logicFlowInstance.value.addEdge({
              id: String(selectedCanvasEdge.value.id),
              type: updatedEdge.edgeType,
              sourceNodeId: sourceNode,
              targetNodeId: targetNode,
              text,
              properties: {
                ...properties,
                edgeType: updatedEdge.edgeType,
                strokeDasharray: updatedEdge.strokeDasharray,
                strokeWidth: updatedEdge.strokeWidth,
                stroke: updatedEdge.stroke,
              },
              style: {
                strokeDasharray: updatedEdge.strokeDasharray,
                strokeWidth: updatedEdge.strokeWidth,
                stroke: updatedEdge.stroke,
              },
            })
            await nextTick()
            // 确保新创建的边的样式正确应用
            const newEdge = logicFlowInstance.value.getEdgeModelById(String(selectedCanvasEdge.value.id))
            if (newEdge) {
              newEdge.updateStyle({
                strokeDasharray: updatedEdge.strokeDasharray,
                strokeWidth: updatedEdge.strokeWidth,
                stroke: updatedEdge.stroke,
              })
            }
          } else {
            // 只更新样式，不改变类型
            // 构建新的样式对象 - 使用更新后的边数据
            const newStyle: any = {}
            if (updatedEdge.strokeDasharray) {
              newStyle.strokeDasharray = updatedEdge.strokeDasharray
            } else {
              newStyle.strokeDasharray = ''
            }
            newStyle.strokeWidth = updatedEdge.strokeWidth
            newStyle.stroke = updatedEdge.stroke
            
            // 更新 properties - 使用更新后的边数据
            const newProperties = {
              ...(lfEdge.properties || {}),
              edgeType: updatedEdge.edgeType,
              strokeDasharray: updatedEdge.strokeDasharray,
              strokeWidth: updatedEdge.strokeWidth,
              stroke: updatedEdge.stroke,
            }
            
            // 使用 setProperties 而不是 updateProperties
            if (typeof (lfEdge as any).setProperties === 'function') {
              (lfEdge as any).setProperties(newProperties)
            } else if (typeof (lfEdge as any).updateProperties === 'function') {
              (lfEdge as any).updateProperties(newProperties)
            } else {
              // 直接设置 properties
              (lfEdge as any).properties = newProperties
            }
            
            // 更新 style - 使用 updateStyle 方法
            if (typeof (lfEdge as any).updateStyle === 'function') {
              (lfEdge as any).updateStyle(newStyle)
            } else {
              // 如果没有 updateStyle，直接设置 style
              (lfEdge as any).style = { ...((lfEdge as any).style || {}), ...newStyle }
            }
            
            // 直接操作 DOM 元素来确保样式立即生效（可选，因为 LogicFlow API 可能已经生效）
            await nextTick()
            // 等待更长时间确保 DOM 已更新
            await new Promise(resolve => setTimeout(resolve, 50))
            try {
              // LogicFlow 使用 data-model-id 属性存储边的ID
              const edgeId = String(selectedCanvasEdge.value.id)
              // 尝试多种选择器
              let edgeElement: Element | null = null
              
              // 方法1: 通过 data-model-id
              edgeElement = document.querySelector(`[data-model-id="${edgeId}"]`)
              
              // 方法2: 通过 data-id
              if (!edgeElement) {
                edgeElement = document.querySelector(`[data-id="${edgeId}"]`)
              }
              
              // 方法3: 通过 class 和 ID 组合查找（避免使用 # 选择器，因为 ID 可能以数字开头）
              if (!edgeElement) {
                const allEdges = document.querySelectorAll('.lf-edge')
                allEdges.forEach((el) => {
                  const modelId = el.getAttribute('data-model-id')
                  if (modelId === edgeId) {
                    edgeElement = el
                  }
                })
              }
              
              // 方法4: 尝试查找所有可能的边元素
              if (!edgeElement) {
                // 查找所有包含该 ID 的元素
                const allElements = document.querySelectorAll('[data-model-id], [data-id], [id]')
                allElements.forEach((el) => {
                  const modelId = el.getAttribute('data-model-id') || el.getAttribute('data-id') || el.getAttribute('id')
                  if (modelId === edgeId) {
                    edgeElement = el
                  }
                })
              }
              
              // 方法5: 尝试通过 getElementById（如果 ID 是有效的）
              if (!edgeElement && /^[a-zA-Z]/.test(edgeId)) {
                edgeElement = document.getElementById(edgeId)
              }
              
              if (edgeElement) {
                // 查找所有 path 元素（边可能由多个path组成）
                const pathElements = edgeElement.querySelectorAll('path')
                pathElements.forEach((pathElement) => {
                  if (newStyle.strokeDasharray) {
                    pathElement.setAttribute('stroke-dasharray', newStyle.strokeDasharray)
                  } else {
                    pathElement.removeAttribute('stroke-dasharray')
                  }
                  pathElement.setAttribute('stroke-width', String(newStyle.strokeWidth))
                  pathElement.setAttribute('stroke', newStyle.stroke)
                })
                
                // 也尝试直接更新 edgeElement 的样式（如果是 polyline 或其他类型）
                if (edgeElement instanceof SVGElement) {
                  if (newStyle.strokeDasharray) {
                    edgeElement.setAttribute('stroke-dasharray', newStyle.strokeDasharray)
                  } else {
                    edgeElement.removeAttribute('stroke-dasharray')
                  }
                  edgeElement.setAttribute('stroke-width', String(newStyle.strokeWidth))
                  edgeElement.setAttribute('stroke', newStyle.stroke)
                }
                
                // 查找 g 元素（LogicFlow 可能使用 g 包裹）
                const gElements = edgeElement.querySelectorAll('g')
                gElements.forEach((gElement) => {
                  const paths = gElement.querySelectorAll('path')
                  paths.forEach((pathElement) => {
                    if (newStyle.strokeDasharray) {
                      pathElement.setAttribute('stroke-dasharray', newStyle.strokeDasharray)
                    } else {
                      pathElement.removeAttribute('stroke-dasharray')
                    }
                    pathElement.setAttribute('stroke-width', String(newStyle.strokeWidth))
                    pathElement.setAttribute('stroke', newStyle.stroke)
                  })
                })
              }
              // 移除警告，因为 LogicFlow API 可能已经生效，DOM 操作只是额外的保障
            } catch (error) {
              // 静默处理错误，不影响功能
              // console.debug('Failed to update edge DOM (non-critical):', error)
            }
          }
        }
      } catch (error) {
        console.warn('Failed to apply edge style in LogicFlow:', error)
      }
    }
  }
  
  // 防抖保存到服务端
  debouncedSaveEdgeStyle()
}

// 防抖保存边的样式
let saveEdgeStyleTimeout: ReturnType<typeof setTimeout> | null = null
const debouncedSaveEdgeStyle = () => {
  if (saveEdgeStyleTimeout) {
    clearTimeout(saveEdgeStyleTimeout)
  }
  saveEdgeStyleTimeout = setTimeout(() => {
    saveEdgeStyleToServer()
  }, 500) // 500ms 防抖
}

// 保存边的样式到服务端
const saveEdgeStyleToServer = async () => {
  if (!selectedCanvasEdge.value?.id) return
  const relationshipId = Number(selectedCanvasEdge.value.id)
  if (!relationshipId) return
  
  try {
    await saveCanvasLayout()
  } catch (error) {
    console.warn('Failed to save edge style:', error)
  }
}

const updateEdgeProperties = async () => {
  if (!selectedCanvasEdge.value?.id) return
  const relationshipId = Number(selectedCanvasEdge.value.id)
  if (!relationshipId) return
  updatingEdge.value = true
  try {
    const appId = parseInt(route.params.id as string)
    await applicationsApi.updateRelationship(appId, relationshipId, {
      relationship_type: edgeForm.relationship_type,
      description: edgeForm.description
    })
    
    // 更新本地边的样式属性 - 使用 edgeForm 中的值（因为这是用户当前编辑的值）
    const edgeIndex = canvasEdges.value.findIndex(e => Number(e.id) === relationshipId)
    if (edgeIndex >= 0) {
      // 获取当前边的完整数据，只更新关系类型、描述和样式
      const currentEdge = canvasEdges.value[edgeIndex]
      const updatedEdge = {
        ...currentEdge,
        relationshipType: edgeForm.relationship_type,
        description: edgeForm.description,
        // 保留样式属性（从 edgeForm 中获取，因为这是用户当前编辑的值）
        edgeType: edgeForm.edgeType,
        strokeDasharray: edgeForm.strokeDasharray,
        strokeWidth: edgeForm.strokeWidth,
        stroke: edgeForm.stroke,
      }
      canvasEdges.value[edgeIndex] = updatedEdge
      // 同时更新 selectedCanvasEdge，确保选中状态同步
      selectedCanvasEdge.value = {
        ...selectedCanvasEdge.value,
        ...updatedEdge
      }
      // 注意：不在这里创建新数组，避免触发 renderGraph 重新渲染所有边
      // 我们直接更新 LogicFlow 中的边样式，而不是通过重新渲染整个图
    }
    
    // 更新 LogicFlow 中的边样式 - 使用更新后的边数据
    if (logicFlowInstance.value && selectedCanvasEdge.value.id) {
      await nextTick()
      try {
        const lfEdge = logicFlowInstance.value.getEdgeModelById(String(selectedCanvasEdge.value.id))
        if (lfEdge) {
          // 获取更新后的边数据
          const updatedEdge = canvasEdges.value.find(e => Number(e.id) === relationshipId)
          if (!updatedEdge) return
          
          // 如果边的类型改变了，需要重新创建边
          if (lfEdge.type !== updatedEdge.edgeType) {
            const sourceNode = lfEdge.sourceNodeId
            const targetNode = lfEdge.targetNodeId
            const text = lfEdge.text?.value || ''
            const properties = lfEdge.properties || {}
            logicFlowInstance.value.deleteEdge(String(selectedCanvasEdge.value.id))
            await nextTick()
            logicFlowInstance.value.addEdge({
              id: String(selectedCanvasEdge.value.id),
              type: updatedEdge.edgeType,
              sourceNodeId: sourceNode,
              targetNodeId: targetNode,
              text,
              properties: {
                ...properties,
                edgeType: updatedEdge.edgeType,
                strokeDasharray: updatedEdge.strokeDasharray,
                strokeWidth: updatedEdge.strokeWidth,
                stroke: updatedEdge.stroke,
              },
              style: {
                strokeDasharray: updatedEdge.strokeDasharray,
                strokeWidth: updatedEdge.strokeWidth,
                stroke: updatedEdge.stroke,
              },
            })
            await nextTick()
            // 确保新创建的边的样式正确应用
            const newEdge = logicFlowInstance.value.getEdgeModelById(String(selectedCanvasEdge.value.id))
            if (newEdge) {
              newEdge.updateStyle({
                strokeDasharray: updatedEdge.strokeDasharray,
                strokeWidth: updatedEdge.strokeWidth,
                stroke: updatedEdge.stroke,
              })
            }
          } else {
            // 只更新样式，不改变类型
            // 使用更新后的边数据
            const newProperties = {
              ...(lfEdge.properties || {}),
              edgeType: updatedEdge.edgeType,
              strokeDasharray: updatedEdge.strokeDasharray,
              strokeWidth: updatedEdge.strokeWidth,
              stroke: updatedEdge.stroke,
            }
            const newStyle = {
              strokeDasharray: updatedEdge.strokeDasharray || '',
              strokeWidth: updatedEdge.strokeWidth,
              stroke: updatedEdge.stroke,
            }
            
            if (typeof (lfEdge as any).setProperties === 'function') {
              (lfEdge as any).setProperties(newProperties)
            } else {
              (lfEdge as any).properties = newProperties
            }
            
            if (typeof (lfEdge as any).updateStyle === 'function') {
              (lfEdge as any).updateStyle(newStyle)
            } else {
              (lfEdge as any).style = { ...((lfEdge as any).style || {}), ...newStyle }
            }
            
            // 直接操作 DOM 确保样式生效（可选，因为 LogicFlow API 可能已经生效）
            await nextTick()
            // 等待更长时间确保 DOM 已更新
            await new Promise(resolve => setTimeout(resolve, 50))
            try {
              const edgeId = String(selectedCanvasEdge.value.id)
              let edgeElement: Element | null = null
              
              // 方法1: 通过 data-model-id
              edgeElement = document.querySelector(`[data-model-id="${edgeId}"]`)
              
              // 方法2: 通过 data-id
              if (!edgeElement) {
                edgeElement = document.querySelector(`[data-id="${edgeId}"]`)
              }
              
              // 方法3: 通过 class 和 ID 组合查找（避免使用 # 选择器，因为 ID 可能以数字开头）
              if (!edgeElement) {
                const allEdges = document.querySelectorAll('.lf-edge')
                allEdges.forEach((el) => {
                  if (el.getAttribute('data-model-id') === edgeId) {
                    edgeElement = el
                  }
                })
              }
              
              // 方法4: 尝试查找所有可能的边元素
              if (!edgeElement) {
                const allElements = document.querySelectorAll('[data-model-id], [data-id], [id]')
                allElements.forEach((el) => {
                  const modelId = el.getAttribute('data-model-id') || el.getAttribute('data-id') || el.getAttribute('id')
                  if (modelId === edgeId) {
                    edgeElement = el
                  }
                })
              }
              
              // 方法5: 尝试通过 getElementById（如果 ID 是有效的）
              if (!edgeElement && /^[a-zA-Z]/.test(edgeId)) {
                edgeElement = document.getElementById(edgeId)
              }
              
              if (edgeElement) {
                const pathElements = edgeElement.querySelectorAll('path')
                pathElements.forEach((pathElement) => {
                  if (newStyle.strokeDasharray) {
                    pathElement.setAttribute('stroke-dasharray', newStyle.strokeDasharray)
                  } else {
                    pathElement.removeAttribute('stroke-dasharray')
                  }
                  pathElement.setAttribute('stroke-width', String(newStyle.strokeWidth || 2))
                  pathElement.setAttribute('stroke', newStyle.stroke || '#94a3b8')
                })
                
                if (edgeElement instanceof SVGElement) {
                  if (newStyle.strokeDasharray) {
                    edgeElement.setAttribute('stroke-dasharray', newStyle.strokeDasharray)
                  } else {
                    edgeElement.removeAttribute('stroke-dasharray')
                  }
                  edgeElement.setAttribute('stroke-width', String(newStyle.strokeWidth || 2))
                  edgeElement.setAttribute('stroke', newStyle.stroke || '#94a3b8')
                }
              }
              // 移除警告，因为 LogicFlow API 可能已经生效，DOM 操作只是额外的保障
            } catch (error) {
              // 静默处理错误，不影响功能
              // console.debug('Failed to update edge DOM in updateEdgeProperties (non-critical):', error)
            }
          }
        }
      } catch (error) {
        console.warn('Failed to update edge style in LogicFlow:', error)
      }
    }
    
    // 保存画布布局
    await saveCanvasLayout()
    
    toastStore.success(t('applications.updateRelationshipSuccess'))
    await loadRelationships()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('applications.updateRelationshipFailed'))
  } finally {
    updatingEdge.value = false
  }
}

const deleteSelectedEdge = () => {
  if (!selectedCanvasEdge.value?.id) return
  const relationshipId = Number(selectedCanvasEdge.value.id)
  if (!relationshipId) return

  confirmMessage.value = t('applications.confirmRelationshipDelete')
  confirmAction.value = async () => {
    try {
      const appId = parseInt(route.params.id as string)
      await applicationsApi.deleteRelationship(appId, relationshipId)
      toastStore.success(t('applications.deleteRelationshipSuccess'))
      await loadRelationships()
      suppressedEdgeRemovals.add(String(relationshipId))
      canvasEdges.value = canvasEdges.value.filter((edge) => Number(edge.id) !== relationshipId)
      clearCanvasSelection()
    } catch (error: any) {
      toastStore.error(error.response?.data?.message || t('applications.deleteRelationshipFailed'))
    }
  }
  showConfirmModal.value = true
}

const handleCanvasEdgeAdded = async (edge: CanvasEdgeData & { _isAdjusting?: boolean }) => {
  // 如果是锚点调整，只更新边的source/target，不创建新关系
  if (edge._isAdjusting && edge.id) {
    const edgeIndex = canvasEdges.value.findIndex(e => e.id === edge.id)
    if (edgeIndex >= 0) {
      // 保留所有样式属性
      canvasEdges.value[edgeIndex] = {
        ...canvasEdges.value[edgeIndex],
        source: edge.source,
        target: edge.target,
        // 保留样式属性
        edgeType: canvasEdges.value[edgeIndex].edgeType || 'polyline',
        strokeDasharray: canvasEdges.value[edgeIndex].strokeDasharray || '',
        strokeWidth: canvasEdges.value[edgeIndex].strokeWidth || 2,
        stroke: canvasEdges.value[edgeIndex].stroke || '#94a3b8',
      }
      canvasEdges.value = [...canvasEdges.value]
      // 自动保存布局
      await saveCanvasLayout()
    }
    return
  }

  const appId = parseInt(route.params.id as string)
  const sourceId = Number(edge.source)
  const targetId = Number(edge.target)

  if (!sourceId || !targetId) {
    toastStore.error(t('applications.canvasEdgeMissingHost'))
    if (edge.id && canvasRef.value) {
      suppressedEdgeRemovals.add(String(edge.id))
      canvasRef.value.removeEdge(edge.id)
    }
    return
  }

  if (sourceId === targetId) {
    toastStore.error(t('applications.canvasSelfLoopNotAllowed'))
    if (edge.id && canvasRef.value) {
      suppressedEdgeRemovals.add(String(edge.id))
      canvasRef.value.removeEdge(edge.id)
    }
    return
  }

  const exists = relationships.value.some(
    (relation) => relation.from_host_id === sourceId && relation.to_host_id === targetId
  )
  if (exists) {
    toastStore.error(t('applications.addRelationshipFailed'))
    if (edge.id && canvasRef.value) {
      suppressedEdgeRemovals.add(String(edge.id))
      canvasRef.value.removeEdge(edge.id)
    }
    return
  }

  try {
    const response = await applicationsApi.createRelationship(appId, {
      from_host_id: sourceId,
      to_host_id: targetId,
      relationship_type: 'member'
    })
    toastStore.success(t('applications.addRelationshipSuccess'))
    
    // 更新本地状态：添加关系
    const newRelationship = response.data || { id: edge.id, from_host_id: sourceId, to_host_id: targetId, relationship_type: 'member' }
    relationships.value.push(newRelationship)
    
    // 更新画布边：如果边已存在则更新，否则添加
    const existingEdgeIndex = canvasEdges.value.findIndex(e => e.id === edge.id || (e.source === edge.source && e.target === edge.target))
    if (existingEdgeIndex >= 0) {
      // 更新已存在的边，保留所有样式属性
      canvasEdges.value[existingEdgeIndex] = {
        ...canvasEdges.value[existingEdgeIndex],
        id: String(newRelationship.id),
        relationshipType: newRelationship.relationship_type,
        label: getRelationshipLabel(newRelationship.relationship_type),
        description: newRelationship.description || '',
        // 保留样式属性
        edgeType: canvasEdges.value[existingEdgeIndex].edgeType || 'polyline',
        strokeDasharray: canvasEdges.value[existingEdgeIndex].strokeDasharray || '',
        strokeWidth: canvasEdges.value[existingEdgeIndex].strokeWidth || 2,
        stroke: canvasEdges.value[existingEdgeIndex].stroke || '#94a3b8',
        data: { ...(canvasEdges.value[existingEdgeIndex].data || {}), relationship: newRelationship }
      }
      canvasEdges.value = [...canvasEdges.value]
    } else {
      // 添加新边，设置默认样式属性
      const newEdge: CanvasEdgeData = {
        id: String(newRelationship.id),
        source: String(sourceId),
        target: String(targetId),
        relationshipType: newRelationship.relationship_type || 'member',
        label: getRelationshipLabel(newRelationship.relationship_type || 'member'),
        description: newRelationship.description || '',
        // 设置默认样式属性
        edgeType: edge.edgeType || 'polyline',
        strokeDasharray: edge.strokeDasharray || '',
        strokeWidth: edge.strokeWidth || 2,
        stroke: edge.stroke || '#94a3b8',
        data: { relationship: newRelationship }
      }
      canvasEdges.value = [...canvasEdges.value, newEdge]
    }
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('applications.addRelationshipFailed'))
    if (edge.id && canvasRef.value) {
      suppressedEdgeRemovals.add(String(edge.id))
      canvasRef.value.removeEdge(edge.id)
    }
  }
}

const handleCanvasEdgeRemoved = async (edge: CanvasEdgeData) => {
  const relationshipId = edge.id ? Number(edge.id) : NaN
  const idKey = edge.id ? String(edge.id) : ''
  if (idKey && suppressedEdgeRemovals.has(idKey)) {
    suppressedEdgeRemovals.delete(idKey)
    return
  }

  if (!relationshipId || Number.isNaN(relationshipId)) {
    return
  }

  const exists = relationships.value.some((relation) => relation.id === relationshipId)
  if (!exists) {
    return
  }

  try {
    const appId = parseInt(route.params.id as string)
    await applicationsApi.deleteRelationship(appId, relationshipId)
    toastStore.success(t('applications.deleteRelationshipSuccess'))
    
    // 更新本地状态：移除关系
    relationships.value = relationships.value.filter(r => r.id !== relationshipId)
    canvasEdges.value = canvasEdges.value.filter((item) => Number(item.id) !== relationshipId)
    clearCanvasSelection()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('applications.deleteRelationshipFailed'))
  }
}

const handleCanvasNodeRemoved = async (node: CanvasNodeData) => {
  if (!node.bindingHostId) {
    // 删除未绑定的资源节点
    resourceNodes.value = resourceNodes.value.filter((item) => !idsEqual(item.id, node.id))
    canvasNodes.value = canvasNodes.value.filter((item) => !idsEqual(item.id, node.id))
    clearCanvasSelection()
    // 自动保存布局
    await saveCanvasLayout()
    return
  }

  const hostId = Number(node.bindingHostId)
  if (!hostId) {
    return
  }

  const exists = hosts.value.some((host) => host.id === hostId)
  if (!exists) {
    return
  }

  try {
    const appId = parseInt(route.params.id as string)
    await applicationsApi.removeHost(appId, hostId)
    
    // 更新本地状态
    hosts.value = hosts.value.filter(h => h.id !== hostId)
    resourceNodes.value = resourceNodes.value.filter((item) => !idsEqual(item.bindingHostId, hostId))
    canvasNodes.value = canvasNodes.value.filter(n => !idsEqual(n.bindingHostId, hostId))
    relationships.value = relationships.value.filter(r => r.from_host_id !== hostId && r.to_host_id !== hostId)
    canvasEdges.value = canvasEdges.value.filter(e => {
      const sourceId = Number(e.source)
      const targetId = Number(e.target)
      return sourceId !== hostId && targetId !== hostId
    })
    await loadAvailableHosts()
    
    // 自动保存布局到服务端
    await saveCanvasLayout()
    
    toastStore.success(t('applications.removeHostSuccess'))
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('applications.removeHostFailed'))
  }
}

const addHostFromLibrary = async (hostId: number) => {
  if (!hostId) return
  hostLibraryAddingId.value = hostId
  
  // 从 availableHosts 中获取主机信息
  const host = availableHosts.value.find((h: any) => h.id === hostId)
  if (!host) {
    toastStore.error(t('applications.hostNotFound'))
    hostLibraryAddingId.value = null
    return
  }
  
  // 将主机信息存储到 pendingHostsInfo 中，用于在资源选择弹窗中显示
  // 但不真正添加到 hosts.value，只有确认资源类型后才添加
  pendingHostsInfo.value.set(hostId, host)
  
  // 显示资源选择弹窗
  await nextTick()
  pendingResourceSelectionHosts.value = [hostId]
  await nextTick()
  processNextResourceSelection()
  
  hostLibraryAddingId.value = null
}

const startResourceBinding = (resource: ResourceDefinition, position: { x: number; y: number } | null = null) => {
  pendingResourceDefinition.value = resource
  pendingResourcePosition.value = position
  selectedResourceHostId.value = null
  resourceBindingSearch.value = ''
  showResourceBindingModal.value = true
}

const createResourceNode = (resource: ResourceDefinition) => {
  const position = computeInitialPosition(canvasNodes.value.length)
  startResourceBinding(resource, position)
}

const updateResourceNodeLabel = () => {
  if (!selectedCanvasNode.value) return
  const trimmed = resourceLabel.value.trim()
  if (!trimmed) return

  if (selectedCanvasNode.value.bindingHostId) {
    const hostId = selectedCanvasNode.value.bindingHostId
    const index = resourceNodes.value.findIndex((node) => idsEqual(node.bindingHostId, hostId))
    if (index >= 0) {
      resourceNodes.value[index] = {
        ...resourceNodes.value[index],
        label: trimmed,
        data: { ...(resourceNodes.value[index].data || {}), label: trimmed }
      }
      resourceNodes.value = [...resourceNodes.value]
    } else {
      const resourceKey = (selectedCanvasNode.value.data?.resourceKey as string) || selectedCanvasNode.value.type
      resourceNodes.value = [
        ...resourceNodes.value,
        {
          id: `overlay-${hostId}-${Date.now().toString(36)}`,
          type: selectedCanvasNode.value.type,
          x: selectedCanvasNode.value.x,
          y: selectedCanvasNode.value.y,
          label: trimmed,
          color: selectedCanvasNode.value.color || getTypeColor(selectedCanvasNode.value.type as CanvasNodeType),
          icon: selectedCanvasNode.value.type,
          bindingHostId: hostId,
          status: selectedCanvasNode.value.status,
          data: {
            ...(selectedCanvasNode.value.data || {}),
            label: trimmed,
            resource: true,
            resourceKey,
            iconType: selectedCanvasNode.value.type,
          }
        }
      ]
    }
    canvasNodes.value = canvasNodes.value.map((node) =>
      idsEqual(node.bindingHostId, hostId) ? { ...node, label: trimmed, x: node.x, y: node.y } : node
    )
  } else {
    resourceNodes.value = resourceNodes.value.map((node) =>
      idsEqual(node.id, selectedCanvasNode.value?.id)
        ? { ...node, label: trimmed, data: { ...(node.data || {}), label: trimmed } }
        : node
    )
    resourceNodes.value = [...resourceNodes.value]
    canvasNodes.value = canvasNodes.value.map((node) =>
      idsEqual(node.id, selectedCanvasNode.value?.id)
        ? { ...node, label: trimmed, x: node.x, y: node.y, data: { ...(node.data || {}), label: trimmed } }
        : node
    )
  }

  selectedCanvasNode.value = {
    ...selectedCanvasNode.value,
    label: trimmed
  }
  resourceLabel.value = trimmed
  saveCanvasLayout()
}

// 防抖保存函数
let saveColorTimeout: ReturnType<typeof setTimeout> | null = null
const debouncedSaveCanvasLayout = () => {
  if (saveColorTimeout) {
    clearTimeout(saveColorTimeout)
  }
  saveColorTimeout = setTimeout(() => {
    saveCanvasLayout()
  }, 500) // 500ms 防抖
}

const updateSelectedNodeColor = (color: string) => {
  if (!selectedCanvasNode.value) return
  const node = selectedCanvasNode.value

  if (node.bindingHostId) {
    const hostId = node.bindingHostId
    const index = resourceNodes.value.findIndex((overlay) => overlay.bindingHostId === hostId)
    if (index >= 0) {
      const existingIconType = resourceNodes.value[index].icon || resourceNodes.value[index].data?.iconType || node.icon || node.data?.iconType
      resourceNodes.value[index] = {
        ...resourceNodes.value[index],
        color,
        data: { 
          ...(resourceNodes.value[index].data || {}), 
          color,
          customColor: color,
          iconType: existingIconType
        }
      }
      resourceNodes.value = [...resourceNodes.value]
    } else {
      const resourceKey = (node.data?.resourceKey as string) || node.type
      const existingIconType = node.icon || node.data?.iconType || node.type
      resourceNodes.value = [
        ...resourceNodes.value,
        {
          id: `overlay-${hostId}-${Date.now().toString(36)}`,
          type: node.type,
          x: node.x,
          y: node.y,
          label: node.label,
          color,
          icon: existingIconType,
          bindingHostId: hostId,
          status: node.status,
          data: { ...(node.data || {}), color, customColor: color, resource: true, resourceKey, iconType: existingIconType }
        }
      ]
      resourceNodes.value = [...resourceNodes.value]
    }
    canvasNodes.value = canvasNodes.value.map((existing) => {
      if (idsEqual(existing.bindingHostId, hostId)) {
        const existingIconType = existing.icon || existing.data?.iconType
        return { 
          ...existing, 
          color,
          x: existing.x,
          y: existing.y,
          data: {
            ...(existing.data || {}),
            color,
            customColor: color,
            iconType: existingIconType
          }
        }
      }
      return existing
    })
  } else {
    const nodeId = node.id
    const existingIconType = node.icon || node.data?.iconType
    canvasNodes.value = canvasNodes.value.map((existing) => {
      if (idsEqual(existing.id, nodeId)) {
        return {
          ...existing,
          color,
          x: existing.x,
          y: existing.y,
          data: {
            ...(existing.data || {}),
            color,
            customColor: color,
            iconType: existingIconType
          }
        }
      }
      return existing
    })
    resourceNodes.value = resourceNodes.value.map((existing) => {
      if (idsEqual(existing.id, nodeId)) {
        return {
          ...existing,
          color,
          data: { 
            ...(existing.data || {}), 
            color,
            customColor: color,
            iconType: existingIconType
          }
        }
      }
      return existing
    })
    resourceNodes.value = [...resourceNodes.value]
  }

  selectedCanvasNode.value = {
    ...selectedCanvasNode.value,
    color
  }

  // 自动保存到服务端
  debouncedSaveCanvasLayout()
}

const duplicateSelectedResource = () => {
  if (!selectedCanvasNode.value) return
  const node = selectedCanvasNode.value
  const source =
    node.bindingHostId
      ? resourceNodes.value.find((overlay) => overlay.bindingHostId === node.bindingHostId) || node
      : node

  const id = generateNodeId()
  const clone: CanvasNodeData = {
    ...source,
    id,
    bindingHostId: undefined,
    x: (source.x ?? node.x) + 48,
    y: (source.y ?? node.y) + 48,
    icon: source.icon || source.type,
    data: { ...(source.data || {}), resource: true, iconType: source.icon || source.type }
  }

  resourceNodes.value = [...resourceNodes.value, clone]
  canvasNodes.value = [...canvasNodes.value, clone]
  selectedCanvasNode.value = clone
  selectedCanvasEdge.value = null
  nodeBindingHostId.value = ''
  resourceLabel.value = clone.label
}

const exportCanvasAsImage = async () => {
  if (!logicFlowInstance.value || !canvasRef.value) {
    toastStore.error(t('applications.canvasExportImageFailed'))
    return
  }

  const appId = parseInt(route.params.id as string)

  try {
    // 方法1: 尝试使用 LogicFlow 的 snapshot 方法
    let snapshot: any
    if (typeof logicFlowInstance.value.getSnapshot === 'function') {
      snapshot = logicFlowInstance.value.getSnapshot()
      if (snapshot instanceof Promise) {
        snapshot = await snapshot
      }
    } else if (typeof logicFlowInstance.value.getGraphSnapshot === 'function') {
      snapshot = logicFlowInstance.value.getGraphSnapshot()
      if (snapshot instanceof Promise) {
        snapshot = await snapshot
      }
    }

    let dataUrl: string | null = null

    // 如果 snapshot 方法可用，使用它
    if (snapshot) {
    if (snapshot instanceof Blob) {
      dataUrl = URL.createObjectURL(snapshot)
    } else if (typeof snapshot === 'string' && snapshot.startsWith('data:')) {
      dataUrl = snapshot
    } else if (typeof snapshot === 'string') {
      dataUrl = `data:image/png;base64,${snapshot}`
      }
    }

    // 方法2: 如果 snapshot 不可用，使用 SVG 转 PNG
    if (!dataUrl) {
      // 查找 canvas 容器
      const canvasContainer = document.querySelector('.application-canvas__wrapper') || 
                              canvasRef.value?.$el?.querySelector('.application-canvas__wrapper')
      if (!canvasContainer) {
        throw new Error('Canvas wrapper not found')
      }

      // 查找 SVG 元素
      const svgElement = canvasContainer.querySelector('svg')
      if (!svgElement) {
        throw new Error('SVG element not found')
      }

      // 获取 SVG 的尺寸
      const bbox = svgElement.getBBox()
      const width = bbox.width || svgElement.clientWidth || 800
      const height = bbox.height || svgElement.clientHeight || 600

      // 克隆 SVG 元素以避免修改原始元素
      const clonedSvg = svgElement.cloneNode(true) as SVGElement
      
      // 设置 SVG 的 viewBox 和尺寸
      if (!clonedSvg.getAttribute('viewBox')) {
        clonedSvg.setAttribute('viewBox', `${bbox.x} ${bbox.y} ${width} ${height}`)
      }
      clonedSvg.setAttribute('width', String(width))
      clonedSvg.setAttribute('height', String(height))
      clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg')

      // 获取 SVG 的字符串表示
      const svgData = new XMLSerializer().serializeToString(clonedSvg)
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })
      const svgUrl = URL.createObjectURL(svgBlob)

      // 创建 Image 对象加载 SVG
      const img = new Image()
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')

      if (!ctx) {
        URL.revokeObjectURL(svgUrl)
        throw new Error('Canvas context not available')
      }

      // 等待图片加载
      await new Promise<void>((resolve, reject) => {
        img.onload = () => {
          try {
            // 设置 canvas 尺寸（添加一些边距）
            const padding = 20
            canvas.width = width + padding * 2
            canvas.height = height + padding * 2

            // 填充白色背景
            ctx.fillStyle = 'white'
            ctx.fillRect(0, 0, canvas.width, canvas.height)

            // 绘制 SVG 图片
            ctx.drawImage(img, padding, padding, width, height)

            URL.revokeObjectURL(svgUrl)
            resolve()
          } catch (error) {
            URL.revokeObjectURL(svgUrl)
            reject(error)
          }
        }
        img.onerror = () => {
          URL.revokeObjectURL(svgUrl)
          reject(new Error('Failed to load SVG image'))
        }
        img.src = svgUrl
      })

      // 转换为 PNG data URL
      dataUrl = canvas.toDataURL('image/png')
    }

    if (!dataUrl) {
      throw new Error('Failed to generate image')
    }

    // 下载图片
    const link = document.createElement('a')
    link.href = dataUrl
    link.download = appId ? `application-${appId}-graph.png` : 'application-graph.png'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    // 清理
    if (snapshot instanceof Blob && dataUrl.startsWith('blob:')) {
      URL.revokeObjectURL(dataUrl)
    }

    toastStore.success(t('applications.canvasExportImageSuccess'))
  } catch (error) {
    console.error('Failed to export PNG', error)
    toastStore.error(t('applications.canvasExportImageFailed'))
  }
}

const applyResourceOverlay = (
  hostId: number,
  resource: ResourceDefinition,
  position: { x: number; y: number } | null,
  overridePosition = false
) => {
  // 获取主机信息
  const hostRecord = hosts.value.find(h => h.id === hostId)
  if (!hostRecord) {
    console.warn(`Host ${hostId} not found`)
    return
  }

  const defaultPosition = position || computeInitialPosition(canvasNodes.value.length)
  // label 使用主机名，而不是资源类型的名称
  const nodeLabel = hostRecord.hostname || hostRecord.ip || resource.label || `#${hostId}`
  let overlayNode: CanvasNodeData = {
    id: generateNodeId(resource.key),
    type: resource.type,
    x: defaultPosition.x,
    y: defaultPosition.y,
    label: nodeLabel,
    color: resource.color,
    icon: resource.type,
    bindingHostId: hostId,
    status: getStatusLabel(hostRecord),
    data: {
      ...hostRecord,
      resource: true,
      resourceKey: resource.key,
      displayStatus: resource.description,
      label: nodeLabel,
      color: resource.color,
      customColor: resource.color,
      iconType: resource.type
    }
  }

  let hostFound = false
  canvasNodes.value = canvasNodes.value.map((node) => {
    if (idsEqual(node.bindingHostId, hostId)) {
      hostFound = true
      const targetX = overridePosition ? defaultPosition.x : node.x ?? defaultPosition.x
      const targetY = overridePosition ? defaultPosition.y : node.y ?? defaultPosition.y
      overlayNode = {
        ...overlayNode,
        x: targetX,
        y: targetY,
        status: getStatusLabel(hostRecord)
      }
      // 保持原始 icon，但更新资源类型信息
      const originalIcon = node.icon || node.data?.iconType || resource.type
      // label 使用主机名，而不是资源类型的名称
      const nodeLabel = hostRecord.hostname || hostRecord.ip || node.label || resource.label || `#${hostId}`
      return {
        ...node,
        type: resource.type,
        label: nodeLabel,
        icon: originalIcon, // 保持原始 icon
        color: resource.color,
        x: targetX,
        y: targetY,
        data: {
          ...hostRecord,
          ...(node.data || {}),
          resource: true,
          resourceKey: resource.key,
          displayStatus: resource.description,
          label: nodeLabel,
          color: resource.color,
          customColor: resource.color,
          iconType: originalIcon // 保持原始 icon
        }
      }
    }
    return node
  })

  // 如果主机节点不存在，需要先创建主机节点
  if (!hostFound) {
    // label 使用主机名，而不是资源类型的名称
    const nodeLabel = hostRecord.hostname || hostRecord.ip || resource.label || `#${hostId}`
    const hostNode: CanvasNodeData = {
      id: hostId,
      type: resource.type,
      x: defaultPosition.x,
      y: defaultPosition.y,
      label: nodeLabel,
      icon: resource.type,
      color: resource.color,
      bindingHostId: hostId,
      status: getStatusLabel(hostRecord),
      data: {
        ...hostRecord,
        resource: true,
        resourceKey: resource.key,
        displayStatus: resource.description,
        label: nodeLabel,
        color: resource.color,
        customColor: resource.color,
        iconType: resource.type
      }
    }
    canvasNodes.value = [
      ...canvasNodes.value,
      hostNode
    ]
    overlayNode = hostNode
  } else {
    canvasNodes.value = [...canvasNodes.value]
  }

  resourceNodes.value = [
    ...resourceNodes.value.filter((node) => !idsEqual(node.bindingHostId, hostId)),
    overlayNode
  ]
  resourceNodes.value = [...resourceNodes.value]

  // 确保选中节点包含完整信息
  const selected = canvasNodes.value.find((node) => idsEqual(node.bindingHostId, hostId)) || overlayNode
  selectedCanvasNode.value = {
    ...selected,
    data: {
      ...hostRecord,
      ...(selected.data || {}),
      resource: true,
      resourceKey: resource.key,
      displayStatus: resource.description,
      label: resource.label,
      color: resource.color,
      customColor: resource.color,
      iconType: resource.type
    }
  }
  
  // 更新属性面板的绑定主机ID和资源标签
  nodeBindingHostId.value = String(hostId)
  resourceLabel.value = overlayNode.label
  selectedCanvasEdge.value = null
  refreshSelections()
}

const handleCanvasDragOver = (event: DragEvent) => {
  if (!draggingResourceKey.value) return
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'copy'
  }
}

const handleCanvasDrop = (event: DragEvent) => {
  event.preventDefault()
  const resourceKey =
    event.dataTransfer?.getData('application/resource') || draggingResourceKey.value
  draggingResourceKey.value = null
  if (!resourceKey) return

  const resource = resourceLibraryMap.value.get(resourceKey)
  if (!resource) return

  let dropPosition: { x: number; y: number } | null = null
  if (logicFlowInstance.value?.getPointByClient) {
    const point = logicFlowInstance.value.getPointByClient(event.clientX, event.clientY)
    if (point?.canvasOverlayPosition) {
      dropPosition = {
        x: point.canvasOverlayPosition.x,
        y: point.canvasOverlayPosition.y
      }
    }
  }

  startResourceBinding(resource, dropPosition)
}

const onResourceDragStart = (resource: ResourceDefinition, event: DragEvent) => {
  draggingResourceKey.value = resource.key
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/resource', resource.key)
    event.dataTransfer.effectAllowed = 'copy'
  }
}

const onResourceDragEnd = () => {
  draggingResourceKey.value = null
}

const sanitizeNodeForPersist = (node: CanvasNodeData) => ({
  id: node.id,
  type: node.type,
  x: node.x,
  y: node.y,
  label: node.label,
  color: node.color,
  icon: node.icon,
  status: node.status,
  bindingHostId:
    node.bindingHostId !== undefined && node.bindingHostId !== null
      ? Number(node.bindingHostId)
      : undefined,
  data: {
    ...(node.data || {}),
    // 确保保存图标类型和颜色
    iconType: node.icon || node.data?.iconType,
    customColor: node.color || node.data?.customColor || node.data?.color,
    color: node.color || node.data?.customColor || node.data?.color
  }
})

const sanitizeEdgeForPersist = (edge: CanvasEdgeData) => ({
  id: edge.id,
  source: edge.source,
  target: edge.target,
  relationshipType: edge.relationshipType,
  label: edge.label,
  description: edge.description,
  edgeType: edge.edgeType,
  strokeDasharray: edge.strokeDasharray,
  strokeWidth: edge.strokeWidth,
  stroke: edge.stroke,
  data: edge.data || {}
})

const serializeGraph = () => {
  // 在保存之前，从 LogicFlow 同步所有节点的最新位置
  if (logicFlowInstance.value) {
    canvasNodes.value.forEach((node) => {
      try {
        const lfNode = logicFlowInstance.value.getNodeModelById(String(node.id))
        if (lfNode) {
          node.x = lfNode.x
          node.y = lfNode.y
        }
      } catch (error) {
        // 如果节点不存在或获取失败，使用原有位置
        console.warn(`Failed to sync position for node ${node.id}:`, error)
      }
    })
    
    // 同步 resourceNodes 的位置
    resourceNodes.value.forEach((node) => {
      try {
        const lfNode = logicFlowInstance.value.getNodeModelById(String(node.id))
        if (lfNode) {
          node.x = lfNode.x
          node.y = lfNode.y
        }
      } catch (error) {
        // 如果节点不存在或获取失败，使用原有位置
        console.warn(`Failed to sync position for resource node ${node.id}:`, error)
      }
    })
    
    // 同步所有边的样式（从 LogicFlow 获取最新的样式）
    canvasEdges.value.forEach((edge) => {
      if (edge.id) {
        try {
          const lfEdge = logicFlowInstance.value.getEdgeModelById(String(edge.id))
          if (lfEdge) {
            const properties = lfEdge.properties || {}
            const style = lfEdge.style || {}
            // 从 LogicFlow 同步样式到 canvasEdges，使用 !== undefined 检查保留空字符串
            edge.edgeType = properties.edgeType !== undefined ? properties.edgeType : (lfEdge.type !== undefined ? lfEdge.type : (edge.edgeType !== undefined ? edge.edgeType : 'polyline'))
            edge.strokeDasharray = style.strokeDasharray !== undefined ? style.strokeDasharray : (properties.strokeDasharray !== undefined ? properties.strokeDasharray : (edge.strokeDasharray !== undefined ? edge.strokeDasharray : ''))
            edge.strokeWidth = style.strokeWidth !== undefined ? style.strokeWidth : (properties.strokeWidth !== undefined ? properties.strokeWidth : (edge.strokeWidth !== undefined ? edge.strokeWidth : 2))
            edge.stroke = style.stroke !== undefined ? style.stroke : (properties.stroke !== undefined ? properties.stroke : (edge.stroke !== undefined ? edge.stroke : '#94a3b8'))
          }
        } catch (error) {
          // 如果边不存在或获取失败，使用原有样式
          console.warn(`Failed to sync style for edge ${edge.id}:`, error)
        }
      }
    })
  }
  
  return {
  nodes: canvasNodes.value.map(sanitizeNodeForPersist),
  edges: canvasEdges.value.map(sanitizeEdgeForPersist),
  resourceNodes: resourceNodes.value.map(sanitizeNodeForPersist),
  metadata: {
    layout: selectedLayout.value
  }
  }
}

const saveCanvasLayout = async () => {
  const appId = parseInt(route.params.id as string)
  if (!appId || isSavingGraph.value) return

  isSavingGraph.value = true
  try {
    await applicationsApi.saveGraph(appId, serializeGraph())
    toastStore.success(t('applications.canvasSaveSuccess'))
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('applications.canvasSaveFailed'))
  } finally {
    isSavingGraph.value = false
  }
}

const exportCanvasLayout = async () => {
  const appId = parseInt(route.params.id as string)
  if (!appId || isExportingGraph.value) return

  isExportingGraph.value = true
  try {
    const blob = await applicationsApi.exportGraph(appId)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `application-${appId}-graph.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    toastStore.success(t('applications.canvasExportSuccess'))
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('applications.canvasExportFailed'))
  } finally {
    isExportingGraph.value = false
  }
}

const resetPendingResource = () => {
  pendingResourceDefinition.value = null
  pendingResourcePosition.value = null
  selectedResourceHostId.value = null
  resourceBindingSearch.value = ''
}

const handleResourceBindingCancel = async () => {
  showResourceBindingModal.value = false
  
  // 如果取消时还有待处理的主机，清理所有待添加的主机信息
  if (pendingResourceSelectionHosts.value.length > 0 || selectedResourceHostId.value) {
    // 如果当前选中的主机还未添加到应用，从待添加列表中移除
    if (selectedResourceHostId.value && pendingHostsInfo.value.has(selectedResourceHostId.value)) {
      pendingHostsInfo.value.delete(selectedResourceHostId.value)
    }
    
    // 如果还有待处理的主机，继续处理下一个
    if (pendingResourceSelectionHosts.value.length > 0) {
      await processNextResourceSelection()
    } else {
      // 如果没有待处理的主机了，清理所有状态
  resetPendingResource()
      pendingResourceSelectionHosts.value = []
      selectedResourceType.value = null
      pendingHostsInfo.value.clear()
    }
  } else {
    resetPendingResource()
    pendingResourceSelectionHosts.value = []
    selectedResourceType.value = null
    pendingHostsInfo.value.clear()
  }
}

const confirmResourceBinding = async () => {
  if (!pendingResourceDefinition.value || !selectedResourceHostId.value) {
    toastStore.error(t('applications.resourceBindingSelectNotice'))
    return
  }

  const resourceDef = pendingResourceDefinition.value
  const hostId = selectedResourceHostId.value
  const alreadyInApplication = hosts.value.some((host) => host.id === hostId)

  bindingResource.value = true
  try {
    const appId = parseInt(route.params.id as string)
    if (!alreadyInApplication) {
      await applicationsApi.addHosts(appId, [hostId])
      // 更新本地主机列表
      await updateLocalHosts([hostId])
    }
    applyResourceOverlay(hostId, resourceDef, pendingResourcePosition.value, !alreadyInApplication)
    
    // 自动保存画布布局
    await saveCanvasLayout()
    
    toastStore.success(t('applications.resourceBindingSuccess'))
    showResourceBindingModal.value = false
    resetPendingResource()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('applications.resourceBindingFailed'))
  } finally {
    bindingResource.value = false
  }
}

const applyLayout = (layout: 'grid' | 'horizontal' | 'vertical') => {
  selectedLayout.value = layout
  const updatedNodes = canvasNodes.value.map((node, index) => {
    let position
    if (layout === 'grid') {
      position = computeInitialPosition(index)
    } else if (layout === 'horizontal') {
      position = { x: 160 + index * 220, y: 200 }
    } else {
      position = { x: 220, y: 140 + index * 160 }
    }
    return {
      ...node,
      x: position.x,
      y: position.y
    }
  })
  canvasNodes.value = updatedNodes
  resourceNodes.value = resourceNodes.value.map((node) => {
    if (node.bindingHostId) {
      const match = updatedNodes.find((item) => item.bindingHostId === node.bindingHostId)
      return match ? { ...node, x: match.x, y: match.y } : node
    }
    const match = updatedNodes.find((item) => item.id === node.id)
    return match ? { ...node, x: match.x, y: match.y } : node
  })
}

const zoomIn = () => {
  if (logicFlowInstance.value?.zoom) {
    logicFlowInstance.value.zoom(true)
  }
}

const zoomOut = () => {
  if (logicFlowInstance.value?.zoom) {
    logicFlowInstance.value.zoom(false)
  }
}

const resetZoom = () => {
  if (logicFlowInstance.value?.resetZoom) {
    logicFlowInstance.value.resetZoom()
  } else if (logicFlowInstance.value?.setZoom) {
    logicFlowInstance.value.setZoom(1)
  }
}

const fitView = () => {
  if (logicFlowInstance.value?.fitView) {
    logicFlowInstance.value.fitView()
  }
}

const toggleCanvasFullscreen = () => {
  isCanvasFullscreen.value = !isCanvasFullscreen.value
  if (isCanvasFullscreen.value) {
    nextTick(() => {
      fitView()
    })
  }
}

const exitCanvasFullscreen = () => {
  if (isCanvasFullscreen.value) {
    isCanvasFullscreen.value = false
  }
}

// 左侧边栏拖动逻辑
const startResizeLeft = (e: MouseEvent) => {
  if (!isCanvasFullscreen.value) return
  e.preventDefault()
  isResizingLeft.value = true
  const startX = e.clientX
  const startWidth = leftSidebarWidth.value

  const handleMouseMove = (e: MouseEvent) => {
    if (!isResizingLeft.value) return
    const diff = e.clientX - startX
    const newWidth = Math.max(minSidebarWidth, Math.min(maxSidebarWidth, startWidth + diff))
    leftSidebarWidth.value = newWidth
  }

  const handleMouseUp = () => {
    isResizingLeft.value = false
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

// 右侧边栏拖动逻辑
const startResizeRight = (e: MouseEvent) => {
  if (!isCanvasFullscreen.value) return
  e.preventDefault()
  isResizingRight.value = true
  const startX = e.clientX
  const startWidth = rightSidebarWidth.value

  const handleMouseMove = (e: MouseEvent) => {
    if (!isResizingRight.value) return
    const diff = startX - e.clientX // 注意：右侧是反向的
    const newWidth = Math.max(minSidebarWidth, Math.min(maxSidebarWidth, startWidth + diff))
    rightSidebarWidth.value = newWidth
  }

  const handleMouseUp = () => {
    isResizingRight.value = false
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

const loadRelationships = async () => {
  try {
    const appId = parseInt(route.params.id as string)
    const response = await applicationsApi.getRelationships(appId)
    relationships.value = response.data || []
    syncCanvasEdgesFromRelationships()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('applications.loadRelationshipsFailed'))
  }
}

const loadApplication = async () => {
  const appId = parseInt(route.params.id as string)
  if (!appId) {
    router.push('/applications')
    return
  }

  loading.value = true
  try {
    const [appRes, graphRes, relationshipRes] = await Promise.all([
      applicationsApi.getApplication(appId),
      applicationsApi.getGraph(appId).catch(() => ({ data: { nodes: [], edges: [] } })),
      applicationsApi.getRelationships(appId).catch(() => ({ data: [] }))
    ])
    application.value = appRes.data
    relationships.value = relationshipRes.data || []
    
    // Load hosts from application
    if (application.value.hosts) {
      hosts.value = application.value.hosts
    }
    await loadAvailableHosts()
    syncCanvasData(graphRes.data || { nodes: [], edges: [] })
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('applications.loadFailed'))
    router.push('/applications')
  } finally {
    loading.value = false
  }
}

const loadAvailableHosts = async () => {
  try {
    const response = await hostsApi.getHosts({ per_page: 1000 })
    const allHosts = response.data || []
    // Filter out hosts already in the application
    const hostIds = new Set(hosts.value.map(h => h.id))
    availableHosts.value = allHosts.filter((h: any) => !hostIds.has(h.id))
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('applications.loadHostsFailed'))
  }
}

const closeAddHostModal = () => {
  showAddHostModal.value = false
  selectedHostIds.value = []
}

// 更新本地主机列表（从服务端获取新添加的主机信息）
const updateLocalHosts = async (hostIds: number[]) => {
  try {
    const response = await hostsApi.getHosts({ per_page: 1000 })
    const allHosts = response.data || []
    const newHosts = allHosts.filter((h: any) => hostIds.includes(h.id))
    // 添加新主机到 hosts.value
    const existingHostIds = new Set(hosts.value.map(h => h.id))
    newHosts.forEach((host: any) => {
      if (!existingHostIds.has(host.id)) {
        hosts.value.push(host)
      }
    })
    // 更新 availableHosts
    const hostIdsSet = new Set(hosts.value.map(h => h.id))
    availableHosts.value = allHosts.filter((h: any) => !hostIdsSet.has(h.id))
  } catch (error: any) {
    console.error('Failed to update local hosts:', error)
  }
}

const addHosts = async () => {
  if (selectedHostIds.value.length === 0) return
  
  // 先保存选中的主机ID，因为 closeAddHostModal 会清空它
  const hostIdsToAdd = [...selectedHostIds.value]
  
  // 关闭添加主机弹窗
  closeAddHostModal()
  
  // 从 availableHosts 中获取主机信息（这些主机还未添加到应用）
  const hostsToAdd = availableHosts.value.filter((h: any) => hostIdsToAdd.includes(h.id))
  
  // 将主机信息存储到 pendingHostsInfo 中，用于在资源选择弹窗中显示
  // 但不真正添加到 hosts.value，只有确认资源类型后才添加
  hostsToAdd.forEach((host: any) => {
    pendingHostsInfo.value.set(host.id, host)
  })
  
  // 为每个新添加的主机显示资源选择弹窗
  if (hostIdsToAdd.length > 0) {
    pendingResourceSelectionHosts.value = [...hostIdsToAdd]
    await nextTick()
    processNextResourceSelection()
  }
}

const processNextResourceSelection = async () => {
  if (pendingResourceSelectionHosts.value.length === 0) {
    // 清理待添加的主机信息
    pendingHostsInfo.value.clear()
    return
  }
  
  const hostId = pendingResourceSelectionHosts.value[0]
  pendingResourceSelectionHosts.value = pendingResourceSelectionHosts.value.slice(1)
  
  // 等待一下确保数据已更新
  await nextTick()
  
  // 优先从待添加的主机信息中查找，如果找不到再从已添加的主机中查找
  let host = pendingHostsInfo.value.get(hostId) || hosts.value.find(h => h.id === hostId)
  if (!host) {
    // 如果找不到主机，等待一下再试一次
    await new Promise(resolve => setTimeout(resolve, 100))
    host = pendingHostsInfo.value.get(hostId) || hosts.value.find(h => h.id === hostId)
    if (!host) {
      // 如果还是找不到主机，继续处理下一个
      await processNextResourceSelection()
      return
    }
  }
  
  // 显示资源选择弹窗（添加主机后选择资源类型）
  selectedResourceHostId.value = hostId
  pendingResourceDefinition.value = null
  pendingResourcePosition.value = null
  resourceBindingSearch.value = ''
  selectedResourceType.value = null
  showResourceBindingModal.value = true
}

const handleResourceSelected = (resource: ResourceDefinition) => {
  if (!selectedResourceHostId.value) return
  
  // 只保存选中的资源类型，不立即执行
  selectedResourceType.value = resource.key
}

const confirmResourceTypeSelection = async () => {
  if (!selectedResourceHostId.value || !selectedResourceType.value) {
    toastStore.error(t('applications.resourceBindingSelectNotice'))
    return
  }
  
  const hostId = selectedResourceHostId.value
  const resourceKey = selectedResourceType.value
  const resource = resourceLibrary.value.find(r => r.key === resourceKey)
  
  if (!resource) {
    toastStore.error(t('applications.resourceNotFound'))
    return
  }
  
  // 检查主机是否已在应用中
  const alreadyInApplication = hosts.value.some(h => h.id === hostId)
  
  bindingResource.value = true
  try {
    const appId = parseInt(route.params.id as string)
    
    // 如果主机还未添加到应用，先添加主机
    if (!alreadyInApplication) {
      await applicationsApi.addHosts(appId, [hostId])
    toastStore.success(t('applications.addHostSuccess'))
      // 更新本地主机列表
      await updateLocalHosts([hostId])
      // 从待添加列表中移除（因为已经真正添加了）
      pendingHostsInfo.value.delete(hostId)
      // 等待主机信息更新
      await nextTick()
    }
    
    // 确保主机信息已加载（优先从已添加的主机中查找，如果找不到再从待添加的主机中查找）
    let hostRecord = hosts.value.find(h => h.id === hostId)
    if (!hostRecord) {
      hostRecord = pendingHostsInfo.value.get(hostId)
    }
    if (!hostRecord) {
      toastStore.error(t('applications.hostNotFound'))
      return
    }
    
    // 计算位置
    const hostNode = canvasNodes.value.find(n => n.bindingHostId === hostId)
    const position = hostNode ? { x: hostNode.x, y: hostNode.y } : computeInitialPosition(canvasNodes.value.length)
    
    // 应用资源类型
    applyResourceOverlay(hostId, resource, position, !alreadyInApplication)
    
    // 等待画布更新
    await nextTick()
    
    // 自动保存画布布局
    await saveCanvasLayout()
    
    toastStore.success(t('applications.resourceBindingSuccess'))
    showResourceBindingModal.value = false
    selectedResourceHostId.value = null
    selectedResourceType.value = null
    
    // 处理下一个主机的资源选择
    await processNextResourceSelection()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('applications.resourceBindingFailed'))
  } finally {
    bindingResource.value = false
  }
}

const removeHost = async (hostId: number) => {
  confirmMessage.value = t('applications.confirmRemoveMessage')
  confirmAction.value = async () => {
    try {
      const appId = parseInt(route.params.id as string)
      await applicationsApi.removeHost(appId, hostId)
      
      // 更新本地状态：从 hosts 中移除
      hosts.value = hosts.value.filter(h => h.id !== hostId)
      // 从画布节点中移除
      canvasNodes.value = canvasNodes.value.filter(n => !idsEqual(n.bindingHostId, hostId))
      // 从资源节点中移除
      resourceNodes.value = resourceNodes.value.filter(n => !idsEqual(n.bindingHostId, hostId))
      // 从关系中移除
      relationships.value = relationships.value.filter(r => r.from_host_id !== hostId && r.to_host_id !== hostId)
      canvasEdges.value = canvasEdges.value.filter(e => {
        const sourceId = Number(e.source)
        const targetId = Number(e.target)
        return sourceId !== hostId && targetId !== hostId
      })
      // 更新可用主机列表
      await loadAvailableHosts()
      
      // 自动保存布局到服务端
      await saveCanvasLayout()
      
      clearCanvasSelection()
      toastStore.success(t('applications.removeHostSuccess'))
    } catch (error: any) {
      toastStore.error(error.response?.data?.message || t('applications.removeHostFailed'))
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

const closeAddRelationshipModal = () => {
  showAddRelationshipModal.value = false
  editingRelationshipId.value = null
  relationshipForm.value = {}
}

const addRelationship = async () => {
  adding.value = true
  try {
    const appId = parseInt(route.params.id as string)
    if (editingRelationshipId.value) {
      const response = await applicationsApi.updateRelationship(appId, editingRelationshipId.value, relationshipForm.value as Partial<HostRelationship>)
      toastStore.success(t('applications.updateRelationshipSuccess'))
      
      // 更新本地状态
      const updatedRelationship = response.data
      if (updatedRelationship) {
        const index = relationships.value.findIndex(r => r.id === editingRelationshipId.value)
        if (index >= 0) {
          relationships.value[index] = updatedRelationship
        }
        // 同步边数据
        syncCanvasEdgesFromRelationships()
      }
    } else {
      const response = await applicationsApi.createRelationship(appId, relationshipForm.value as HostRelationship)
    toastStore.success(t('applications.addRelationshipSuccess'))
      
      // 更新本地状态
      const newRelationship = response.data
      if (newRelationship) {
        relationships.value.push(newRelationship)
        // 同步边数据（确保所有关系都有对应的边）
        syncCanvasEdgesFromRelationships()
      }
    }
    closeAddRelationshipModal()
  } catch (error: any) {
    const messageKey = editingRelationshipId.value ? 'applications.updateRelationshipFailed' : 'applications.addRelationshipFailed'
    toastStore.error(error.response?.data?.message || t(messageKey))
  } finally {
    adding.value = false
  }
}

const openAddRelationshipModal = () => {
  editingRelationshipId.value = null
  relationshipForm.value = {}
  showAddRelationshipModal.value = true
}

const editRelationship = (relationship: any) => {
  relationshipForm.value = {
    from_host_id: relationship.from_host_id,
    to_host_id: relationship.to_host_id,
    relationship_type: relationship.relationship_type,
    description: relationship.description
  }
  editingRelationshipId.value = relationship.id
  showAddRelationshipModal.value = true
}

const deleteRelationship = (relationship: any) => {
  confirmMessage.value = t('applications.confirmRelationshipDelete')
  confirmAction.value = async () => {
    try {
      const appId = parseInt(route.params.id as string)
      await applicationsApi.deleteRelationship(appId, relationship.id)
      toastStore.success(t('applications.deleteRelationshipSuccess'))
      
      // 更新本地状态
      relationships.value = relationships.value.filter(r => r.id !== relationship.id)
      canvasEdges.value = canvasEdges.value.filter(e => Number(e.id) !== relationship.id)
    } catch (error: any) {
      toastStore.error(error.response?.data?.message || t('applications.deleteRelationshipFailed'))
    }
  }
  showConfirmModal.value = true
}

const onFullscreenKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    exitCanvasFullscreen()
  }
}

watch(isCanvasFullscreen, (fullscreen) => {
  const className = 'overflow-hidden'
  if (fullscreen) {
    document.body.classList.add(className)
    window.addEventListener('keydown', onFullscreenKeydown)
  } else {
    document.body.classList.remove(className)
    window.removeEventListener('keydown', onFullscreenKeydown)
  }
})

// 点击外部关闭样式菜单
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (showEdgeStyleMenu.value && !target.closest('.edge-style-menu-container')) {
    showEdgeStyleMenu.value = false
  }
}

onMounted(() => {
  loadApplication()
  document.addEventListener('click', handleClickOutside)
})

watch(showAddHostModal, (opened) => {
  if (opened) {
  loadAvailableHosts()
  }
})

watch(showResourceBindingModal, (opened) => {
  if (opened) {
    loadAvailableHosts()
  } else {
    resetPendingResource()
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
  document.body.classList.remove('overflow-hidden')
  window.removeEventListener('keydown', onFullscreenKeydown)
})

</script>