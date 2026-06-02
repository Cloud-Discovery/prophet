<template>
  <div class="px-4 py-6 sm:px-0">
    <div class="mb-4 flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 flex items-center">
          <ServerIcon class="h-7 w-7 mr-2 text-gray-700" />
          {{ $t('hosts.title') }}
        </h1>
        <p class="mt-1 text-sm text-gray-500">{{ $t('hosts.subtitle') }}</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <!-- View Toggle -->
        <div class="flex items-center border border-gray-300 rounded-md overflow-hidden">
          <button
            @click="viewMode = 'list'"
            :class="viewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'"
            class="px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
            :title="$t('hosts.listView')"
          >
            <Bars3Icon class="h-4 w-4" />
          </button>
          <button
            @click="viewMode = 'tree'"
            :class="viewMode === 'tree' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'"
            class="px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 border-l border-gray-300"
            :title="$t('hosts.treeView')"
          >
            <Squares2X2Icon class="h-4 w-4" />
          </button>
        </div>
        
        <!-- Enhanced Search with Field Selector -->
        <div class="relative flex-1 min-w-[300px] max-w-lg" ref="searchContainer">
          <div 
            class="relative w-full"
            @click="handleSearchContainerClick"
          >
            <!-- Search Input Container -->
            <div 
              class="flex items-center w-full px-3 py-2 border border-gray-300 rounded-md bg-white shadow-sm focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 transition-all cursor-text"
              :class="{ 'ring-2 ring-blue-500 border-blue-500': showFieldDropdown || showValueDropdown }"
            >
              <!-- Field Tag (if selected) -->
              <div v-if="searchField !== 'all'" class="flex items-center mr-2 px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                <span>{{ getFieldLabel(searchField) }}</span>
                <button
                  @click.stop="clearField"
                  class="ml-1.5 hover:bg-blue-200 rounded-full p-0.5"
                >
                  <XMarkIcon class="h-3 w-3" />
                </button>
              </div>
              
              <!-- Search Icon -->
              <MagnifyingGlassIcon class="h-5 w-5 text-gray-400 flex-shrink-0" />
              
              <!-- Input or Value Selector -->
              <div class="flex-1 ml-2 min-w-0">
                <input
                  v-if="searchField === 'all' || searchField !== 'tag'"
                  v-model="searchQuery"
                  type="text"
                  :placeholder="getSearchPlaceholder()"
                  class="w-full border-0 p-0 text-sm focus:outline-none focus:ring-0"
                  @input="debouncedSearch"
                  @keyup.enter="loadHosts(1)"
                  @focus="handleInputFocus"
                  @keydown.escape="showFieldDropdown = false; showValueDropdown = false"
                />
                <div
                  v-else-if="searchField === 'tag'"
                  @click.stop="showValueDropdown = !showValueDropdown"
                  class="flex items-center justify-between cursor-pointer min-h-[20px]"
                >
                  <span class="text-sm" :class="searchQuery ? 'text-gray-900' : 'text-gray-400'">
                    {{ searchQuery || $t('hosts.selectTag') }}
                  </span>
                  <ChevronDownIcon 
                    class="h-4 w-4 text-gray-400 transition-transform flex-shrink-0"
                    :class="{ 'rotate-180': showValueDropdown }"
                  />
                </div>
              </div>
              
              <!-- Clear Button -->
              <button
                v-if="searchQuery || searchField !== 'all'"
                @click.stop="clearSearch"
                class="ml-2 text-gray-400 hover:text-gray-600 focus:outline-none flex-shrink-0"
                type="button"
              >
                <XMarkIcon class="h-4 w-4" />
              </button>
            </div>
            
            <!-- Field Selection Dropdown -->
            <div
              v-if="showFieldDropdown && searchField === 'all'"
              class="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
            >
              <div class="py-1">
                <button
                  v-for="field in searchFields"
                  :key="field.value"
                  @click="selectField(field.value)"
                  class="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                >
                  <div class="w-2 h-2 rounded-full bg-orange-500 mr-3 flex-shrink-0"></div>
                  <span>{{ field.label }}</span>
                </button>
              </div>
            </div>
            
            <!-- Value Selection Dropdown (for tag) -->
            <div
              v-if="showValueDropdown && searchField === 'tag'"
              class="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
            >
              <div class="py-1">
                <button
                  @click="selectTagValue('')"
                  class="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                >
                  {{ $t('hosts.all') }}
                </button>
                <button
                  v-for="tag in availableTags"
                  :key="tag.id"
                  @click="selectTagValue(tag.name)"
                  class="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                >
                  <div class="w-2 h-2 rounded-full mr-3 flex-shrink-0" :style="{ backgroundColor: tag.color || '#6B7280' }"></div>
                  <span>{{ tag.name }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Primary Actions -->
        <div class="flex items-center gap-2">
          <button
            @click="loadHosts(1)"
            :disabled="loading"
            class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            :title="$t('common.refresh')"
          >
            <ArrowPathIcon :class="{ 'animate-spin': loading }" class="h-4 w-4" />
          </button>
          
          <button
            @click="openCreateModal"
            class="inline-flex items-center px-3 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            :title="$t('hosts.addHost')"
          >
            <PlusIcon class="h-4 w-4" />
          </button>
          
          <!-- Batch Actions Menu (when hosts selected) -->
          <div v-if="selectedHosts.length > 0" class="relative z-30">
            <Menu as="div" class="relative inline-block text-left">
              <MenuButton class="inline-flex items-center px-3 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">
                <span class="mr-2">{{ $t('common.batchOperation') }} ({{ selectedHosts.length }})</span>
                <ChevronDownIcon class="h-4 w-4" />
              </MenuButton>
              <MenuItems class="absolute right-0 z-50 mt-2 w-56 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                  <div class="py-1">
                    <MenuItem v-slot="{ active }">
                      <button
                        @click="openBatchCredentialsModal"
                        :class="[active ? 'bg-gray-100' : '', 'flex items-center w-full px-4 py-2 text-sm text-gray-700']"
                      >
                        <PencilIcon class="h-4 w-4 mr-3 text-gray-400" />
                        {{ $t('hosts.batchUpdateCredentials') }}
                      </button>
                    </MenuItem>
                    <MenuItem v-slot="{ active }">
                      <button
                        @click="handleBatchCollect"
                        :class="[active ? 'bg-gray-100' : '', 'flex items-center w-full px-4 py-2 text-sm text-gray-700']"
                      >
                        <CpuChipIcon class="h-4 w-4 mr-3 text-gray-400" />
                        {{ $t('hosts.batchCollect') }}
                      </button>
                    </MenuItem>
                  <MenuItem v-slot="{ active }">
                    <button
                      @click="openBatchAddToAppModal"
                      :class="[active ? 'bg-gray-100' : '', 'flex items-center w-full px-4 py-2 text-sm text-gray-700']"
                    >
                      <Squares2X2Icon class="h-4 w-4 mr-3 text-gray-400" />
                      {{ $t('hosts.batchAddToApplication') }}
                    </button>
                  </MenuItem>
                  <MenuItem v-slot="{ active }">
                    <button
                      @click="openBatchTagManagementModal"
                      :class="[active ? 'bg-gray-100' : '', 'flex items-center w-full px-4 py-2 text-sm text-gray-700']"
                    >
                      <TagIcon class="h-4 w-4 mr-3 text-gray-400" />
                      {{ $t('hosts.batchManageTags') }}
                    </button>
                  </MenuItem>
                  <MenuItem v-slot="{ active }">
                    <button
                      @click="openExportModal"
                      :class="[active ? 'bg-gray-100' : '', 'flex items-center w-full px-4 py-2 text-sm text-gray-700']"
                    >
                      <ArrowDownTrayIcon class="h-4 w-4 mr-3 text-gray-400" />
                      {{ $t('hosts.batchExportExcel') }}
                    </button>
                  </MenuItem>
                  <div class="border-t border-gray-200 my-1"></div>
                  <MenuItem v-slot="{ active }">
                    <button
                      @click="openBatchDeleteModal"
                      :class="[active ? 'bg-red-50' : '', 'flex items-center w-full px-4 py-2 text-sm text-red-700']"
                    >
                      <TrashIcon class="h-4 w-4 mr-3 text-red-400" />
                      {{ $t('hosts.batchDelete') }}
                      </button>
                    </MenuItem>
                  </div>
                </MenuItems>
            </Menu>
          </div>
          
          <!-- Column Customization -->
          <Menu as="div" class="relative inline-block text-left">
            <MenuButton class="inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 hover:border-gray-400 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200">
              <Bars3BottomLeftIcon class="h-5 w-5" />
            </MenuButton>
            <MenuItems class="absolute right-0 z-50 mt-2 w-[420px] origin-top-right rounded-xl bg-white shadow-2xl ring-1 ring-gray-200 focus:outline-none overflow-hidden">
              <!-- Header -->
              <div class="bg-gradient-to-br from-blue-300 to-indigo-400 px-5 py-4">
                <div class="flex items-center justify-between mb-3">
                  <div class="flex items-center gap-2.5">
                    <div class="p-1.5 bg-white/20 rounded-lg backdrop-blur-sm">
                      <Bars3BottomLeftIcon class="h-4 w-4 text-white" />
                  </div>
                    <span class="text-base font-semibold text-white">{{ $t('hosts.selectColumns') }}</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <button
                      @click.stop="selectAllColumns"
                      class="px-3 py-1.5 text-xs font-semibold text-white bg-white/20 hover:bg-white/30 rounded-lg backdrop-blur-sm transition-all duration-200"
                    >
                      {{ $t('common.selectAll') }}
                    </button>
                    <button
                      @click.stop="deselectAllColumns"
                      class="px-3 py-1.5 text-xs font-semibold text-white bg-white/20 hover:bg-white/30 rounded-lg backdrop-blur-sm transition-all duration-200"
                    >
                      {{ $t('common.deselectAll') }}
                    </button>
                  </div>
                </div>
                <!-- Search -->
                <div class="relative">
                  <MagnifyingGlassIcon class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-white z-10" />
                  <input
                    v-model="columnSearchQuery"
                    type="text"
                    :placeholder="$t('common.search')"
                    class="w-full pl-9 pr-9 py-2 bg-white/20 backdrop-blur-sm border border-white/30 rounded-lg text-sm text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-white/50 transition-all relative z-0"
                    @click.stop
                    @keydown.escape="columnSearchQuery = ''"
                  />
                  <button
                    v-if="columnSearchQuery"
                    @click.stop="columnSearchQuery = ''"
                    class="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/70 hover:text-white z-10 transition-colors"
                  >
                    <XMarkIcon class="h-4 w-4" />
                  </button>
                </div>
                <!-- Selected count and view toggle -->
                <div class="mt-2.5 flex items-center justify-between">
                  <div class="text-xs text-white/90">
                    {{ $t('hosts.selectedColumnsCount', { count: visibleColumnsCount, total: availableColumns.length }) }}
                  </div>
                  <button
                    @click.stop="showGroupedView = !showGroupedView"
                    class="px-2 py-1 text-xs font-medium text-white/90 hover:text-white hover:bg-white/20 rounded transition-colors"
                    :title="showGroupedView ? $t('hosts.showListView') : $t('hosts.showGroupedView')"
                  >
                    <Bars3Icon v-if="showGroupedView" class="h-3.5 w-3.5" />
                    <Squares2X2Icon v-else class="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
              <!-- Templates -->
              <div v-if="!columnSearchQuery" class="px-5 py-3 border-b border-gray-200 bg-gray-50">
                <div class="text-xs font-semibold text-gray-600 mb-2">{{ $t('hosts.columnTemplates') }}</div>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="template in columnTemplates"
                    :key="template.id"
                    @click.stop="applyTemplate(template)"
                    class="px-2.5 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 transition-all"
                    :title="template.description"
                  >
                    {{ template.name }}
                  </button>
                </div>
              </div>
              <!-- Column List -->
              <Transition
                mode="out-in"
                enter-active-class="transition-opacity duration-150 ease-out"
                enter-from-class="opacity-0"
                enter-to-class="opacity-100"
                leave-active-class="transition-opacity duration-100 ease-in"
                leave-from-class="opacity-100"
                leave-to-class="opacity-0"
              >
                <div v-if="filteredColumns.length === 0" key="empty" class="px-5 py-8 text-center">
                  <MagnifyingGlassIcon class="h-10 w-10 mx-auto text-gray-300 mb-2" />
                  <p class="text-sm text-gray-500">{{ $t('hosts.noColumnsFound') }}</p>
                </div>
                <!-- Grouped View -->
                <div v-else-if="showGroupedView && !columnSearchQuery" key="grouped" class="max-h-[360px] overflow-y-auto custom-scrollbar">
                  <div class="py-3">
                    <div v-for="categoryKey in Object.keys(groupedColumns)" :key="categoryKey" class="relative">
                      <div class="sticky top-0 z-20 px-5 py-2 bg-gray-50 border-b border-gray-100">
                        <div class="flex items-center gap-2">
                          <CpuChipIcon v-if="categoryKey === 'hardware'" class="h-4 w-4 text-gray-500" />
                          <TagIcon v-else-if="categoryKey === 'metadata'" class="h-4 w-4 text-gray-500" />
                          <InformationCircleIcon v-else class="h-4 w-4 text-gray-500" />
                          <span class="text-xs font-semibold text-gray-700">{{ (columnCategories as any)[categoryKey]?.label || categoryKey }}</span>
                          <span class="text-xs text-gray-500">({{ groupedColumns[categoryKey].length }})</span>
                        </div>
                      </div>
                <label
                        v-for="column in groupedColumns[categoryKey]"
                  :key="column.key"
                        class="flex items-center px-5 py-3 hover:bg-blue-50/50 cursor-pointer transition-all duration-150 group border-l-4 border-transparent hover:border-blue-500 relative"
                        :class="{ 'bg-blue-50/30 border-blue-500': isColumnVisible(column.key) }"
                >
                        <div class="relative flex items-center flex-1">
                          <!-- Custom Checkbox -->
                          <div class="relative flex items-center mr-3">
                    <input
                      type="checkbox"
                      v-model="visibleColumns"
                      :value="column.key"
                              class="sr-only"
                            />
                            <div
                              class="w-5 h-5 rounded border-2 flex items-center justify-center transition-all duration-200"
                              :class="isColumnVisible(column.key) 
                                ? 'bg-blue-500 border-blue-500 shadow-sm' 
                                : 'bg-white border-gray-300 group-hover:border-blue-400'"
                            >
                              <CheckIcon
                                v-if="isColumnVisible(column.key)"
                                class="h-3.5 w-3.5 text-white"
                              />
                            </div>
                          </div>
                          <span 
                            class="text-sm select-none transition-colors flex-1"
                            :class="isColumnVisible(column.key) 
                              ? 'text-gray-900 font-semibold' 
                              : 'text-gray-700 group-hover:text-gray-900'"
                            :title="column.description"
                          >
                            {{ column.label }}
                          </span>
                          <!-- Required badge -->
                          <span
                            v-if="column.required || ['checkbox', 'ip', 'operation'].includes(column.key)"
                            class="ml-2 px-2 py-0.5 text-xs font-medium text-gray-500 bg-gray-100 rounded"
                          >
                            {{ $t('common.required') }}
                          </span>
                  </div>
                </label>
                    </div>
                  </div>
                </div>
                <!-- List View -->
                <div v-else key="list" class="py-3 max-h-[360px] overflow-y-auto custom-scrollbar">
                  <label
                    v-for="column in filteredColumns"
                    :key="column.key"
                    class="flex items-center px-5 py-3 hover:bg-blue-50/50 cursor-pointer transition-all duration-150 group border-l-4 border-transparent hover:border-blue-500"
                    :class="{ 'bg-blue-50/30 border-blue-500': isColumnVisible(column.key) }"
                  >
                    <div class="relative flex items-center flex-1">
                      <!-- Custom Checkbox -->
                      <div class="relative flex items-center mr-3">
                        <input
                          type="checkbox"
                          v-model="visibleColumns"
                          :value="column.key"
                          class="sr-only"
                        />
                        <div
                          class="w-5 h-5 rounded border-2 flex items-center justify-center transition-all duration-200"
                          :class="isColumnVisible(column.key) 
                            ? 'bg-blue-500 border-blue-500 shadow-sm' 
                            : 'bg-white border-gray-300 group-hover:border-blue-400'"
                        >
                          <CheckIcon
                            v-if="isColumnVisible(column.key)"
                            class="h-3.5 w-3.5 text-white"
                          />
                        </div>
                      </div>
                      <span 
                        class="text-sm select-none transition-colors flex-1"
                        :class="isColumnVisible(column.key) 
                          ? 'text-gray-900 font-semibold' 
                          : 'text-gray-700 group-hover:text-gray-900'"
                        :title="column.description"
                      >
                        {{ column.label }}
                      </span>
                      <!-- Required badge -->
                      <span
                        v-if="column.required || ['checkbox', 'ip', 'operation'].includes(column.key)"
                        class="ml-2 px-2 py-0.5 text-xs font-medium text-gray-500 bg-gray-100 rounded"
                      >
                        {{ $t('common.required') }}
                      </span>
                    </div>
                  </label>
                </div>
              </Transition>
              <!-- Footer -->
              <div class="px-5 py-3 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
                <button
                  @click.stop="resetColumnsToDefault"
                  class="px-3 py-1.5 text-xs font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
                >
                  {{ $t('hosts.resetToDefault') }}
                </button>
                <div class="text-xs text-gray-500">
                  {{ $t('hosts.pressEscToClose') }}
                </div>
              </div>
            </MenuItems>
          </Menu>
          
          <!-- More Actions Menu -->
          <Menu as="div" class="relative inline-block text-left">
            <MenuButton class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
              <EllipsisVerticalIcon class="h-5 w-5" />
            </MenuButton>
              <MenuItems class="absolute right-0 z-10 mt-2 w-56 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                <div class="py-1">
                  <MenuItem v-slot="{ active }">
                    <button
                      @click="openDataImportModal"
                      :class="[active ? 'bg-gray-100' : '', 'flex items-center w-full px-4 py-2 text-sm text-gray-700']"
                    >
                      <ArrowUpTrayIcon class="h-4 w-4 mr-3 text-gray-400" />
                      {{ $t('hosts.dataImport') }}
                    </button>
                  </MenuItem>
                </div>
              </MenuItems>
          </Menu>
        </div>
      </div>
    </div>
    
    <!-- Filters Panel -->
    <div v-if="viewMode === 'list'" class="mb-4 bg-white shadow sm:rounded-md">
      <!-- Active Filters Tags -->
      <div v-if="hasActiveFilters" class="px-4 pt-3 pb-2 border-b border-gray-200">
        <div class="flex items-center flex-wrap gap-2">
          <span class="text-xs font-medium text-gray-500">{{ $t('hosts.activeFilters') }}:</span>
          <span
            v-for="filter in activeFilters"
            :key="filter.key"
            class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
          >
            {{ filter.label }}: {{ filter.value }}
            <button
              @click="removeFilter(filter.key)"
              class="ml-1.5 inline-flex items-center justify-center w-4 h-4 rounded-full hover:bg-blue-200 focus:outline-none"
            >
              <XMarkIcon class="w-3 h-3" />
            </button>
          </span>
          <button
            @click="clearFilters"
            class="text-xs text-gray-600 hover:text-gray-900 underline"
          >
            {{ $t('hosts.clearAll') }}
          </button>
        </div>
      </div>
      
      <!-- Filter Controls -->
      <div class="p-4">
        <div class="flex items-center justify-between mb-3">
          <button
            @click="showFilters = !showFilters"
            class="flex items-center text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            <FunnelIcon class="h-4 w-4 mr-2" />
            {{ $t('hosts.filters') }}
            <ChevronDownIcon 
              :class="['ml-2 h-4 w-4 transition-transform', showFilters ? 'rotate-180' : '']" 
            />
          </button>
          <div class="flex items-center gap-2">
            <!-- Quick Filters -->
            <div class="flex items-center gap-1">
              <button
                @click="applyQuickFilter('not_collected')"
                class="px-2 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
              >
                {{ $t('hosts.notCollected') }}
              </button>
              <button
                @click="applyQuickFilter('collecting')"
                class="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded hover:bg-blue-200"
              >
                {{ $t('hosts.collecting') }}
              </button>
              <button
                @click="applyQuickFilter('completed')"
                class="px-2 py-1 text-xs font-medium text-green-700 bg-green-100 rounded hover:bg-green-200"
              >
                {{ $t('common.completed') }}
              </button>
            </div>
          </div>
        </div>
        
        <!-- Collapsible Filter Options -->
        <div v-show="showFilters" class="mt-4 space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            <!-- OS Type Filter -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">{{ $t('hosts.osType') }}</label>
              <select
                v-model="filters.os_type"
                @change="loadHosts(1)"
                class="w-full px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">{{ $t('hosts.all') }}</option>
                <option value="linux">{{ $t('hosts.linux') }}</option>
                <option value="windows">{{ $t('hosts.windows') }}</option>
                <option value="VMware ESXi">{{ $t('hosts.vmware') }}</option>
                <option value="VM">{{ $t('hosts.vm') }}</option>
              </select>
            </div>
            
            <!-- Device Type Filter -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">{{ $t('hosts.deviceType') }}</label>
              <select
                v-model="filters.device_type"
                @change="loadHosts(1)"
                class="w-full px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">{{ $t('hosts.all') }}</option>
                <option value="host">{{ $t('hosts.host') }}</option>
                <option value="vm">{{ $t('hosts.vm') }}</option>
                <option value="network_device">{{ $t('hosts.networkDevice') }}</option>
              </select>
            </div>
            
            <!-- Collection Status Filter -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">{{ $t('hosts.collectionStatus') }}</label>
              <select
                v-model="filters.collection_status"
                @change="loadHosts(1)"
                class="w-full px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">{{ $t('hosts.all') }}</option>
                <option value="not_collected">{{ $t('hosts.notCollected') }}</option>
                <option value="collecting">{{ $t('hosts.collecting') }}</option>
                <option value="completed">{{ $t('common.completed') }}</option>
                <option value="failed">{{ $t('common.failed') }}</option>
              </select>
            </div>
            
            <!-- Source Filter -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">{{ $t('hosts.source') }}</label>
              <select
                v-model="filters.source"
                @change="loadHosts(1)"
                class="w-full px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">{{ $t('hosts.all') }}</option>
                <option value="scan">{{ $t('hosts.scan') }}</option>
                <option value="platform">{{ $t('hosts.platform') }}</option>
                <option value="manual">{{ $t('hosts.manual') }}</option>
              </select>
            </div>
            
            <!-- Physical/Virtual Filter -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">{{ $t('hosts.deviceNature') }}</label>
              <select
                v-model="filters.is_physical"
                @change="loadHosts(1)"
                class="w-full px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">{{ $t('hosts.all') }}</option>
                <option value="true">{{ $t('hosts.physical') }}</option>
                <option value="false">{{ $t('hosts.virtual') }}</option>
              </select>
            </div>
            
            <!-- Tag Filter -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">{{ $t('hosts.tags') }}</label>
              <select
                v-model="filters.tag_id"
                @change="loadHosts(1)"
                class="w-full px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">{{ $t('hosts.all') }}</option>
                <option v-for="tag in availableTags" :key="tag.id" :value="tag.id">
                  {{ tag.name }}
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Tree View -->
    <div v-if="viewMode === 'tree'" class="bg-white shadow sm:rounded-md overflow-hidden relative">
      <LoadingOverlay :loading="loadingTree" :text="$t('common.loading')" />
      <div v-if="!loadingTree && treeData.length === 0" class="text-center py-8 text-gray-500">
        <ServerIcon class="h-12 w-12 mx-auto text-gray-300 mb-2" />
        <p>{{ $t('hosts.noPlatformHosts') }}</p>
      </div>
      <div v-else-if="!loadingTree" class="overflow-y-auto max-h-[calc(100vh-300px)] p-4">
        <div v-for="platform in treeData" :key="platform.platform_id" class="mb-4">
          <!-- Platform Level -->
          <div class="flex items-center mb-2 p-3 bg-blue-50 rounded-lg border border-blue-200 hover:bg-blue-100 transition-colors">
            <!-- Expand/Collapse Button -->
            <button
              @click="togglePlatformExpand(platform.platform_id!)"
              class="mr-2 p-1 hover:bg-blue-200 rounded transition-colors"
              :title="expandedPlatforms.has(platform.platform_id!) ? $t('hosts.collapse') : $t('hosts.expand')"
            >
              <ChevronDownIcon 
                v-if="expandedPlatforms.has(platform.platform_id!)"
                class="h-4 w-4 text-blue-700"
              />
              <ChevronRightIcon 
                v-else
                class="h-4 w-4 text-blue-700"
              />
            </button>
            
            <!-- Platform Checkbox -->
            <input
              type="checkbox"
              :ref="(el: any) => {
                if (el && platform.platform_id) {
                  platformCheckboxRefs.set(platform.platform_id, el)
                  el.indeterminate = isPlatformPartiallySelected(platform)
                }
              }"
              :checked="isPlatformAllSelected(platform)"
              @click.stop="togglePlatformSelection(platform)"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
            />
            
            <CloudIcon class="h-5 w-5 mr-2 text-blue-600" />
            <div class="flex-1">
              <h3 class="text-sm font-semibold text-blue-900">{{ platform.platform_name }}</h3>
              <p class="text-xs text-blue-600">{{ platform.platform_type.toUpperCase() }}</p>
            </div>
            <span class="text-xs text-blue-600 mr-2">
              {{ platform.esxi_hosts.reduce((sum: number, esxi: any) => sum + esxi.vms.length, 0) }}{{ $t('hosts.vmCount') }}
            </span>
          </div>
          
          <!-- ESXi Hosts Level (only show if platform is expanded) -->
          <div v-if="expandedPlatforms.has(platform.platform_id!)" v-for="esxi in platform.esxi_hosts" :key="esxi.esxi_name" class="ml-6 mb-3">
            <div class="flex items-center mb-1 p-2 bg-gray-50 rounded border border-gray-200 hover:bg-gray-100 transition-colors">
              <!-- Expand/Collapse Button -->
              <button
                @click="toggleESXiExpand(esxi.esxi_name)"
                class="mr-2 p-1 hover:bg-gray-200 rounded transition-colors"
                :title="expandedESXiHosts.has(esxi.esxi_name) ? $t('hosts.collapse') : $t('hosts.expand')"
              >
                <ChevronDownIcon 
                  v-if="expandedESXiHosts.has(esxi.esxi_name)"
                  class="h-4 w-4 text-gray-600"
                />
                <ChevronRightIcon 
                  v-else
                  class="h-4 w-4 text-gray-600"
                />
              </button>
              
              <!-- ESXi Checkbox -->
              <input
                type="checkbox"
                :ref="(el: any) => {
                  if (el && esxi.esxi_name) {
                    esxiCheckboxRefs.set(esxi.esxi_name, el)
                    el.indeterminate = isESXiPartiallySelected(esxi)
                  }
                }"
                :checked="isESXiAllSelected(esxi)"
                @click.stop="toggleESXiSelection(esxi)"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
              />
              
              <ServerIcon class="h-4 w-4 mr-2 text-gray-600" />
              <div class="flex-1">
                <h4 class="text-sm font-medium text-gray-900">{{ esxi.esxi_name }}</h4>
                <p v-if="esxi.esxi_ip" class="text-xs text-gray-500">{{ esxi.esxi_ip }}</p>
              </div>
              <span class="text-xs text-gray-600">{{ esxi.vms.length }}{{ $t('hosts.vmCount') }}</span>
            </div>
            
            <!-- VMs Level (only show if ESXi is expanded) -->
            <div v-if="expandedESXiHosts.has(esxi.esxi_name)" class="ml-8 space-y-1">
              <div
                v-for="vm in esxi.vms"
                :key="vm.id"
                class="flex items-center p-2 hover:bg-gray-50 rounded border border-gray-100 cursor-pointer transition-colors"
                :class="{ 'bg-blue-50 border-blue-200': selectedHosts.includes(vm.id!) }"
                @click.stop="toggleHostSelection(vm.id!)"
              >
                <input
                  type="checkbox"
                  :checked="selectedHosts.includes(vm.id!)"
                  @click.stop="toggleHostSelection(vm.id!)"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-3"
                />
                <div class="flex-1 min-w-0">
                  <div class="flex items-center space-x-2">
                    <span class="text-sm font-medium text-gray-900">{{ vm.ip }}</span>
                    <span v-if="vm.hostname" class="text-sm text-gray-500">({{ vm.hostname }})</span>
                  </div>
                  <div class="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                    <span v-if="vm.os_type">{{ vm.os_type }}</span>
                    <span v-if="vm.cpu_cores">{{ vm.cpu_cores }}{{ $t('hosts.cores') }}</span>
                    <span v-if="vm.memory_total">{{ formatGB(vm.memory_total) }}</span>
                  </div>
                </div>
                <div class="flex items-center space-x-1">
                  <button
                    v-if="vm.id"
                    @click.stop="viewHost(vm.id)"
                    class="text-blue-600 hover:text-blue-900 p-1 rounded hover:bg-blue-50"
                    :title="$t('hosts.viewDetails')"
                  >
                    <EyeIcon class="h-4 w-4" />
                  </button>
                  <button
                    @click.stop="editHost(vm)"
                    class="text-indigo-600 hover:text-indigo-900 p-1 rounded hover:bg-indigo-50"
                    :title="$t('common.edit')"
                  >
                    <PencilIcon class="h-4 w-4" />
                  </button>
                  <button
                    v-if="vm.id"
                    @click.stop="collectHost(vm.id)"
                    :disabled="vm.collection_status === 'collecting'"
                    class="text-green-600 hover:text-green-900 p-1 rounded hover:bg-green-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    :title="$t('hosts.collect')"
                  >
                    <CpuChipIcon class="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- List View -->
    <div v-else class="bg-white shadow sm:rounded-md overflow-hidden relative">
      <LoadingOverlay :loading="loading" :text="$t('common.loading')" />
      <div class="overflow-x-auto max-h-[calc(100vh-300px)] overflow-y-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50 sticky top-0 z-20">
            <tr>
              <th
                v-for="(columnKey, index) in visibleColumns"
                :key="columnKey"
                :draggable="columnKey !== 'checkbox' && columnKey !== 'ip' && columnKey !== 'operation'"
                @dragstart="handleHeaderDragStart($event, columnKey)"
                @dragover="handleHeaderDragOver($event, index)"
                @dragleave="handleHeaderDragLeave"
                @drop="handleHeaderDrop($event, index)"
                @dragend="handleHeaderDragEnd($event)"
                class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap transition-colors group"
                :class="{
                  'sticky left-0 bg-gray-50 z-10': columnKey === 'checkbox',
                  'sticky right-0 bg-gray-50 z-10': columnKey === 'operation',
                  'cursor-move hover:bg-gray-100': columnKey !== 'checkbox' && columnKey !== 'ip' && columnKey !== 'operation',
                  'border-l-2 border-blue-500': dragOverHeaderIndex === index && draggedHeaderColumn !== columnKey,
                }"
              >
                <div class="flex items-center gap-2">
                  <span v-if="columnKey === 'checkbox'">
                <input
                  type="checkbox"
                  :checked="allSelected"
                  @change="toggleSelectAll"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                  </span>
                  <span v-else class="flex items-center gap-1.5 flex-1">
                    <Bars3Icon
                      v-if="columnKey !== 'checkbox' && columnKey !== 'ip' && columnKey !== 'operation'"
                      class="h-3.5 w-3.5 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                    />
                    <span>{{ getColumnLabel(columnKey) }}</span>
                  </span>
                </div>
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-if="!loading && hosts.length === 0" class="text-center py-8">
              <td :colspan="visibleColumns.length + 1" class="px-4 py-4 text-gray-500">
                <ServerIcon class="h-12 w-12 mx-auto text-gray-300 mb-2" />
                <p>{{ $t('hosts.noHosts') }}</p>
              </td>
            </tr>
            <tr 
              v-else 
              v-for="host in hosts" 
              :key="host.id" 
              class="hover:bg-gray-50 group cursor-pointer transition-colors"
              :class="{ 'bg-blue-50 hover:bg-blue-100': selectedHosts.includes(host.id!) }"
              @click="toggleHostSelection(host.id!)"
            >
              <td
                v-for="columnKey in visibleColumns"
                :key="columnKey"
                class="px-4 py-4 text-sm transition-colors"
                :class="{
                  'whitespace-nowrap': columnKey !== 'collection_status',
                  'sticky left-0 bg-white group-hover:bg-gray-50 z-10': columnKey === 'checkbox',
                  'sticky right-0 bg-white group-hover:bg-gray-50 z-10': columnKey === 'operation',
                  'bg-blue-50 group-hover:bg-blue-100': (columnKey === 'checkbox' || columnKey === 'operation') && selectedHosts.includes(host.id!),
                  'text-gray-500': columnKey !== 'ip' && columnKey !== 'checkbox' && columnKey !== 'operation',
                  'text-gray-900 font-medium': columnKey === 'ip',
                }"
                @click.stop="columnKey === 'tags' || columnKey === 'operation'"
              >
                <!-- Checkbox -->
                <template v-if="columnKey === 'checkbox'">
                  <input
                    type="checkbox"
                    :value="host.id"
                    v-model="selectedHosts"
                    class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </template>
                <!-- IP -->
                <template v-else-if="columnKey === 'ip'">
                  {{ host.ip }}
                </template>
                <!-- Hostname -->
                <template v-else-if="columnKey === 'hostname'">
                  {{ host.hostname || '-' }}
                </template>
                <!-- OS Type -->
                <template v-else-if="columnKey === 'os_type'">
                  <span class="capitalize">{{ host.os_type || '-' }}</span>
                </template>
                <!-- Distribution -->
                <template v-else-if="columnKey === 'distribution'">
                  {{ host.distribution || '-' }}
                </template>
                <!-- OS Version -->
                <template v-else-if="columnKey === 'os_version'">
                  {{ host.os_version || '-' }}
                </template>
                <!-- Device Type -->
                <template v-else-if="columnKey === 'device_type'">
                  <span class="inline-flex items-center">
                    <ComputerDesktopIcon v-if="host.is_physical" class="h-4 w-4 mr-1 text-gray-400" />
                    <CloudIcon v-else class="h-4 w-4 mr-1 text-gray-400" />
                    {{ host.is_physical ? $t('hosts.physical') : $t('hosts.virtual') }}
                  </span>
                </template>
                <!-- CPU Cores -->
                <template v-else-if="columnKey === 'cpu_cores'">
                  {{ host.cpu_cores ? `${host.cpu_cores}${$t('hosts.cores')}` : '-' }}
                </template>
                <!-- Memory -->
                <template v-else-if="columnKey === 'memory'">
                  {{ host.memory_total ? formatGB(host.memory_total) : '-' }}
                </template>
                <!-- Disk -->
                <template v-else-if="columnKey === 'disk'">
                  {{ host.disk_total_size ? formatGB(host.disk_total_size) : '-' }}
                </template>
                <!-- Collection Status -->
                <template v-else-if="columnKey === 'collection_status'">
                  <div class="flex flex-col gap-1">
                    <span
                      :class="getCollectionStatusClass(host.collection_status)"
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium w-fit"
                    >
                      <component
                        :is="getCollectionStatusIcon(host.collection_status)"
                        class="h-3.5 w-3.5 mr-1"
                      />
                      {{ getCollectionStatusText(host.collection_status) }}
                    </span>
                    <div v-if="host.collection_status === 'failed' && host.error_message" class="mt-1">
                      <button
                        @click.stop="toggleHostError(host.id)"
                        class="flex items-center text-xs text-red-600 hover:text-red-800 transition-colors"
                      >
                        <ExclamationTriangleIcon class="h-3 w-3 mr-1 flex-shrink-0" />
                        <span class="truncate max-w-[200px]">{{ $t('hosts.viewError') }}</span>
                        <ChevronDownIcon 
                          class="h-3 w-3 ml-1 flex-shrink-0 transition-transform"
                          :class="{ 'rotate-180': expandedErrors.has(host.id) }"
                        />
                      </button>
                      <Transition
                        enter-active-class="transition ease-out duration-200"
                        enter-from-class="opacity-0 transform scale-95"
                        enter-to-class="opacity-100 transform scale-100"
                        leave-active-class="transition ease-in duration-150"
                        leave-from-class="opacity-100 transform scale-100"
                        leave-to-class="opacity-0 transform scale-95"
                      >
                        <div v-if="expandedErrors.has(host.id)" class="mt-1 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800 break-words whitespace-pre-wrap max-w-full max-h-[200px] overflow-y-auto overflow-x-hidden z-10 relative">
                          {{ host.error_message }}
                        </div>
                      </Transition>
                    </div>
                  </div>
                </template>
                <!-- Source -->
                <template v-else-if="columnKey === 'source'">
                  <span class="inline-flex items-center">
                    <component
                      :is="getSourceIcon(host.source)"
                      class="h-4 w-4 mr-1"
                      :class="getSourceIconColor(host.source)"
                    />
                    {{ getSourceText(host.source) }}
                  </span>
                </template>
                <!-- Tags -->
                <template v-else-if="columnKey === 'tags'">
                  <div class="flex flex-wrap gap-1 items-center">
                    <span
                      v-for="tag in host.tags"
                      :key="tag.id"
                      class="inline-flex items-center px-2 py-1 text-xs font-medium rounded text-white group/tag relative"
                      :style="{ backgroundColor: tag.color || '#6B7280' }"
                    >
                      {{ tag.name }}
                      <button
                        v-if="host.id"
                        @click.stop="removeHostTag(host.id, tag.id!)"
                        class="ml-1 opacity-0 group-hover/tag:opacity-100 hover:bg-black/20 rounded p-0.5 transition-opacity"
                        :title="$t('hosts.removeTag')"
                      >
                        <XMarkIcon class="h-3 w-3" />
                      </button>
                    </span>
                    <button
                      v-if="host.id"
                      @click.stop="showHostTagManagementModal(host)"
                      class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                      :title="$t('hosts.manageTags')"
                    >
                      <TagIcon class="h-3 w-3 mr-1" />
                      {{ $t('hosts.manageTags') }}
                    </button>
                  </div>
                </template>
                <!-- Operation -->
                <template v-else-if="columnKey === 'operation'">
                  <div class="flex items-center space-x-1">
                    <button
                      v-if="host.id"
                      @click="viewHost(host.id)"
                      class="text-blue-600 hover:text-blue-900 p-1 rounded hover:bg-blue-50"
                      :title="$t('hosts.viewDetails')"
                    >
                      <EyeIcon class="h-5 w-5" />
                    </button>
                    <button
                      v-if="host.id && host.os_type !== 'VMware ESXi'"
                      @click="editHost(host)"
                      class="text-indigo-600 hover:text-indigo-900 p-1 rounded hover:bg-indigo-50"
                      :title="$t('common.edit')"
                    >
                      <PencilIcon class="h-5 w-5" />
                    </button>
                    <button
                      v-if="host.id && host.os_type !== 'VMware ESXi'"
                      @click="collectHost(host.id)"
                      :disabled="host.collection_status === 'collecting'"
                      class="text-green-600 hover:text-green-900 p-1 rounded hover:bg-green-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      :title="$t('hosts.collect')"
                    >
                      <CpuChipIcon class="h-5 w-5" />
                    </button>
                    <button
                      v-if="host.id"
                      @click="deleteHost(host.id)"
                      class="text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50"
                      :title="$t('common.delete')"
                    >
                      <TrashIcon class="h-5 w-5" />
                    </button>
                  </div>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div v-if="pagination && pagination.total > 0" class="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
        <div class="flex items-center space-x-4">
          <div class="flex items-center space-x-2">
            <label class="text-sm text-gray-700">{{ $t('common.perPage') }}:</label>
            <select
              v-model.number="perPage"
              @change="loadHosts(1)"
              class="px-2 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
          <p class="text-sm text-gray-700">
            {{ $t('common.page') }} <span class="font-medium">{{ (pagination.page - 1) * pagination.per_page + 1 }}</span>
            {{ $t('common.of') }} <span class="font-medium">{{ Math.min(pagination.page * pagination.per_page, pagination.total) }}</span>
            {{ $t('common.total') }} <span class="font-medium">{{ pagination.total }}</span> {{ $t('common.items') }}
          </p>
        </div>
        <div class="flex items-center space-x-2">
          <button
            @click="loadHosts(pagination.page - 1)"
            :disabled="pagination.page <= 1"
            class="relative inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ $t('common.previous') }}
          </button>
          <span class="text-sm text-gray-700">
            {{ $t('common.page') }} {{ pagination.page }} {{ $t('common.of') }} {{ pagination.pages }}
          </span>
          <button
            @click="loadHosts(pagination.page + 1)"
            :disabled="pagination.page >= pagination.pages"
            class="relative inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ $t('common.next') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Host Modal -->
    <Modal :open="showCreateModal" @close="closeCreateModal" :title="editingHostId ? $t('hosts.editHostTitle') : $t('hosts.addHostTitle')" max-width="lg">
      <form @submit.prevent="saveHost" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('hosts.ip') }} *</label>
          <input
            v-model="hostForm.ip"
            type="text"
            required
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('hosts.hostname') }}</label>
          <input
            v-model="hostForm.hostname"
            type="text"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ $t('hosts.osType') }}</label>
            <select
              v-model="hostForm.os_type"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">{{ $t('hosts.pleaseSelect') }}</option>
              <option value="linux">Linux</option>
              <option value="windows">Windows</option>
              <option value="vmware">VMware</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ $t('hosts.deviceType') }}</label>
            <select
              v-model="hostForm.device_type"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">{{ $t('hosts.pleaseSelect') }}</option>
              <option value="server">{{ $t('hosts.server') }}</option>
              <option value="network">{{ $t('hosts.networkDevice') }}</option>
              <option value="storage">{{ $t('hosts.storageDevice') }}</option>
            </select>
          </div>
        </div>
        <div>
          <label class="flex items-center">
            <input
              v-model="hostForm.is_physical"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span class="ml-2 text-sm text-gray-700">{{ $t('hosts.physical') }}</span>
          </label>
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
          @click="saveHost"
          :disabled="saving"
          class="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto disabled:opacity-50"
        >
          {{ saving ? $t('hosts.saving') : $t('common.save') }}
        </button>
      </template>
    </Modal>

    <!-- Host Details Modal -->
    <Modal :open="showDetailModal" @close="closeDetailModal" :title="$t('hosts.hostDetails')" max-width="6xl">
      <div v-if="hostDetail" class="space-y-6 max-h-[calc(100vh-200px)] overflow-y-auto">
        <!-- Basic Information -->
          <div>
          <h3 class="text-sm font-medium text-gray-700 mb-3 flex items-center">
            <InformationCircleIcon class="h-4 w-4 mr-2" />
            {{ $t('hosts.basicInfo') }}
          </h3>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label class="text-xs font-medium text-gray-500">{{ $t('hosts.ipAddress') }}</label>
            <p class="mt-1 text-sm text-gray-900">{{ hostDetail.ip }}</p>
          </div>
          <div>
              <label class="text-xs font-medium text-gray-500">{{ $t('hosts.hostname') }}</label>
            <p class="mt-1 text-sm text-gray-900">{{ hostDetail.hostname || '-' }}</p>
          </div>
          <div>
              <label class="text-xs font-medium text-gray-500">{{ $t('hosts.macAddress') }}</label>
            <p class="mt-1 text-sm text-gray-900">{{ hostDetail.mac || '-' }}</p>
          </div>
          <div>
              <label class="text-xs font-medium text-gray-500">{{ $t('hosts.osType') }}</label>
            <p class="mt-1 text-sm text-gray-900">{{ hostDetail.os_type || '-' }}</p>
          </div>
          <div>
              <label class="text-xs font-medium text-gray-500">{{ $t('hosts.osVersion') }}</label>
            <p class="mt-1 text-sm text-gray-900">{{ hostDetail.os_version || '-' }}</p>
          </div>
          <div>
              <label class="text-xs font-medium text-gray-500">{{ $t('hosts.deviceType') }}</label>
            <p class="mt-1 text-sm text-gray-900">{{ hostDetail.device_type || '-' }}</p>
          </div>
          <div>
              <label class="text-xs font-medium text-gray-500">{{ $t('hosts.cpuInfo') }}</label>
            <p class="mt-1 text-sm text-gray-900">{{ hostDetail.cpu_info || '-' }}</p>
          </div>
          <div>
              <label class="text-xs font-medium text-gray-500">{{ $t('hosts.cpuCores') }}</label>
            <p class="mt-1 text-sm text-gray-900">{{ hostDetail.cpu_cores || '-' }}</p>
          </div>
          <div>
              <label class="text-xs font-medium text-gray-500">{{ $t('hosts.memoryTotal') }}</label>
              <p class="mt-1 text-sm text-gray-900">{{ hostDetail.memory_total ? formatGB(hostDetail.memory_total) : '-' }}</p>
          </div>
          <div>
              <label class="text-xs font-medium text-gray-500">{{ $t('hosts.memoryFree') }}</label>
              <p class="mt-1 text-sm text-gray-900">{{ hostDetail.memory_free ? formatGB(hostDetail.memory_free) : '-' }}</p>
          </div>
          <div>
              <label class="text-xs font-medium text-gray-500">{{ $t('hosts.vendor') }}</label>
              <p class="mt-1 text-sm text-gray-900">{{ hostDetail.vendor || '-' }}</p>
          </div>
          <div>
              <label class="text-xs font-medium text-gray-500">{{ $t('hosts.source') }}</label>
              <p class="mt-1 text-sm text-gray-900">{{ getSourceText(hostDetail.source) }}</p>
          </div>
        </div>
        </div>
        
        <!-- Network Interfaces -->
        <div v-if="hostDetail.network_interfaces && hostDetail.network_interfaces.length > 0">
          <h3 class="text-sm font-medium text-gray-700 mb-3 flex items-center">
            <GlobeAltIcon class="h-4 w-4 mr-2" />
            {{ $t('hosts.networkInterfaces') }}
          </h3>
          <div class="border border-gray-200 rounded-lg overflow-hidden">
            <div class="max-h-[50vh] overflow-y-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.interface') }}</th>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.macAddress') }}</th>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">IPv4</th>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">IPv6</th>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.gateway') }}</th>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">MTU</th>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.status') }}</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="nic in hostDetail.network_interfaces" :key="nic.id">
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                    {{ nic.interface }}
                    <span v-if="nic.is_default" class="ml-1 text-xs text-blue-600">({{ $t('hosts.default') }})</span>
                  </td>
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{{ nic.macaddress || '-' }}</td>
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{{ nic.ipv4_address || '-' }}</td>
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{{ nic.ipv6_address || '-' }}</td>
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{{ nic.gateway || '-' }}</td>
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{{ nic.mtu || '-' }}</td>
                  <td class="px-3 py-2 whitespace-nowrap text-sm">
                    <span :class="nic.active ? 'text-green-600' : 'text-gray-400'">
                      {{ nic.active ? $t('hosts.active') : $t('hosts.inactive') }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
            </div>
          </div>
        </div>
        
        <!-- Disks -->
        <div v-if="hostDetail.disks && hostDetail.disks.length > 0">
          <h3 class="text-sm font-medium text-gray-700 mb-3 flex items-center">
            <CircleStackIcon class="h-4 w-4 mr-2" />
            {{ $t('hosts.disks') }}
          </h3>
          <div class="border border-gray-200 rounded-lg overflow-hidden">
            <div class="max-h-[50vh] overflow-y-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.device') }}</th>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.vendor') }}</th>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.model') }}</th>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.size') }}</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="disk in hostDetail.disks" :key="disk.id">
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{{ disk.device }}</td>
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{{ disk.vendor || '-' }}</td>
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{{ disk.model || '-' }}</td>
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{{ disk.size_gb ? `${disk.size_gb} GB` : '-' }}</td>
                </tr>
              </tbody>
            </table>
            </div>
          </div>
        </div>
        
        <!-- Partitions -->
        <div v-if="hostDetail.partitions && hostDetail.partitions.length > 0">
          <h3 class="text-sm font-medium text-gray-700 mb-3 flex items-center">
            <Squares2X2Icon class="h-4 w-4 mr-2" />
            {{ $t('hosts.partitions') }}
          </h3>
          <div class="border border-gray-200 rounded-lg overflow-hidden">
            <div class="max-h-[50vh] overflow-y-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.device') }}</th>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.filesystem') }}</th>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.totalSize') }}</th>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.availableSize') }}</th>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.usedSize') }}</th>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ $t('hosts.usage') }}</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="partition in hostDetail.partitions" :key="partition.id">
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{{ partition.device }}</td>
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{{ partition.fstype || '-' }}</td>
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{{ partition.size_total_gb ? `${partition.size_total_gb} GB` : '-' }}</td>
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{{ partition.size_available_gb ? `${partition.size_available_gb} GB` : '-' }}</td>
                  <td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{{ partition.size_used_gb ? `${partition.size_used_gb} GB` : '-' }}</td>
                  <td class="px-3 py-2 whitespace-nowrap text-sm">
                    <div class="flex items-center">
                      <div class="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div
                          class="h-2 rounded-full"
                          :class="getUsageColor(partition.size_available_ratio)"
                          :style="{ width: `${(1 - (partition.size_available_ratio || 0)) * 100}%` }"
                        ></div>
                      </div>
                      <span class="text-xs text-gray-600">{{ Math.round((1 - (partition.size_available_ratio || 0)) * 100) }}%</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            </div>
          </div>
        </div>
        
        <!-- Credentials -->
        <div v-if="hostDetail.credentials" class="mt-4">
          <h3 class="text-sm font-medium text-gray-700 mb-2 flex items-center">
            <LockClosedIcon class="h-4 w-4 mr-2" />
            {{ $t('hosts.credentials') }}
          </h3>
          <div class="bg-gray-50 p-3 rounded">
            <p class="text-sm"><span class="font-medium">{{ $t('hosts.username') }}:</span> {{ hostDetail.credentials.username }}</p>
            <p v-if="hostDetail.credentials.password" class="text-sm"><span class="font-medium">{{ $t('auth.password') }}:</span> {{ hostDetail.credentials.password }}</p>
            <p v-if="hostDetail.credentials.ssh_port" class="text-sm"><span class="font-medium">{{ $t('hosts.sshPort') }}:</span> {{ hostDetail.credentials.ssh_port }}</p>
            <p v-if="hostDetail.credentials.key_path" class="text-sm"><span class="font-medium">{{ $t('hosts.keyPath') }}:</span> {{ hostDetail.credentials.key_path }}</p>
          </div>
        </div>
        
        <!-- Scan Ports -->
        <div v-if="hostDetail.scan_ports && (hostDetail.scan_ports.tcp?.length > 0 || hostDetail.scan_ports.udp?.length > 0)">
          <h3 class="text-sm font-medium text-gray-700 mb-2 flex items-center">
            <GlobeAltIcon class="h-4 w-4 mr-2" />
            {{ $t('hosts.scanPorts') }}
          </h3>
          <div class="bg-gray-50 p-3 rounded">
            <div v-if="hostDetail.scan_ports.tcp && hostDetail.scan_ports.tcp.length > 0" class="mb-2">
              <span class="text-xs font-medium text-blue-600">TCP:</span>
              <span class="text-sm text-gray-700 ml-2">{{ hostDetail.scan_ports.tcp.join(', ') }}</span>
        </div>
            <div v-if="hostDetail.scan_ports.udp && hostDetail.scan_ports.udp.length > 0">
              <span class="text-xs font-medium text-green-600">UDP:</span>
              <span class="text-sm text-gray-700 ml-2">{{ hostDetail.scan_ports.udp.join(', ') }}</span>
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

    <!-- Missing Credentials Modal -->
    <Modal :open="showMissingCredentialsModal" @close="showMissingCredentialsModal = false" :title="$t('hosts.missingCredentials')" max-width="md">
      <div class="space-y-4">
        <p class="text-sm text-gray-600">{{ $t('hosts.missingCredentialsMessage') }}</p>
        <div class="max-h-60 overflow-y-auto">
          <ul class="list-disc list-inside space-y-2">
            <li v-for="host in missingCredentialsHosts" :key="host.id" class="text-sm text-gray-700">
              {{ host.ip }} ({{ host.hostname || '-' }})
            </li>
          </ul>
        </div>
      </div>
      <template #footer>
        <button
          type="button"
          @click="showMissingCredentialsModal = false"
          class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
        >
          {{ $t('common.close') }}
        </button>
        <button
          type="button"
          @click="openBatchCredentialsModalFromMissing"
          class="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto"
        >
          {{ $t('hosts.updateNow') }}
        </button>
      </template>
    </Modal>

    <!-- Batch Update Credentials Modal -->
    <Modal :open="showBatchCredentialsModal" @close="closeBatchCredentialsModal" :title="$t('hosts.batchUpdateCredentials')" max-width="md">
      <form @submit.prevent="saveBatchCredentials" class="space-y-4">
        <div v-if="selectedHosts.length > 0 || missingCredentialsHosts.length > 0">
          <label class="block text-sm font-medium text-gray-700">{{ $t('hosts.selectedHosts') }}</label>
          <div class="mt-1 max-h-32 overflow-y-auto bg-gray-50 p-2 rounded text-sm">
            <div v-for="hostId in (missingCredentialsHosts.length > 0 ? missingCredentialsHosts.map((h: any) => h.id) : selectedHosts)" :key="hostId" class="text-gray-600">
              {{ hosts.find((h: Host) => h.id === hostId)?.ip || hostId }}
            </div>
          </div>
        </div>
        <div>
          <label class="flex items-center">
            <input
              v-model="batchCredentialsForm.applyToAll"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span class="ml-2 text-sm text-gray-700">{{ $t('hosts.applyToAll') }}</span>
          </label>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('hosts.username') }} *</label>
          <input
            v-model="batchCredentialsForm.username"
            type="text"
            required
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('auth.password') }}</label>
          <input
            v-model="batchCredentialsForm.password"
            type="password"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ $t('hosts.sshPort') }}</label>
            <input
              v-model.number="batchCredentialsForm.ssh_port"
              type="number"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">{{ $t('hosts.keyPath') }}</label>
            <input
              v-model="batchCredentialsForm.key_path"
              type="text"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </form>
      <template #footer>
        <button
          type="button"
          @click="closeBatchCredentialsModal"
          class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
        >
          {{ $t('common.cancel') }}
        </button>
        <button
          type="button"
          @click="saveBatchCredentials"
          :disabled="saving"
          class="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto disabled:opacity-50"
        >
          {{ saving ? $t('hosts.saving') : $t('common.save') }}
        </button>
      </template>
    </Modal>

    <!-- Confirm Modal -->
    <ConfirmModal
      :open="showConfirmModal"
      @close="showConfirmModal = false"
      @confirm="handleConfirm"
      :title="$t('hosts.confirmDelete')"
      :message="confirmMessage"
    />

    <!-- Tag Management Modal -->
    <Modal :open="showTagManagementModal" @close="closeTagManagementModal" :title="$t('hosts.manageTags')" max-width="md">
      <div v-if="tagManagementTarget" class="space-y-4">
        <div>
          <p class="text-sm text-gray-600 mb-3">
            {{ $t('hosts.manageTagsFor') }}: <span class="font-semibold">{{ tagManagementTarget.ip }} {{ tagManagementTarget.hostname ? `(${tagManagementTarget.hostname})` : '' }}</span>
          </p>
  </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('hosts.selectTags') }}</label>
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
          <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('hosts.currentTags') }}</label>
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
          @click="saveHostTags"
          :disabled="saving"
          class="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto disabled:opacity-50"
        >
          {{ saving ? $t('settings.saving') : $t('common.save') }}
        </button>
      </template>
    </Modal>

    <!-- Batch Tag Management Modal -->
    <Modal :open="showBatchTagManagementModal" @close="closeBatchTagManagementModal" :title="$t('hosts.batchManageTags')" max-width="md">
      <div class="space-y-4">
        <div>
          <p class="text-sm text-gray-600 mb-3">
            {{ $t('hosts.batchManageTagsFor') }}: <span class="font-semibold">{{ selectedHosts.length }} {{ $t('hosts.selectedHosts') }}</span>
          </p>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('hosts.selectTags') }}</label>
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
                <span v-if="batchHostTagsMap.has(tag.id)" class="ml-2 text-xs text-gray-500">({{ $t('hosts.currentTags') }})</span>
              </div>
            </label>
          </div>
        </div>
        
        <div class="bg-blue-50 border border-blue-200 rounded-md p-3">
          <p class="text-xs text-blue-800">
            {{ $t('hosts.batchTagManageHint') }}
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
          @click="saveBatchHostTags"
          :disabled="saving"
          class="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto disabled:opacity-50"
        >
          {{ saving ? $t('settings.saving') : $t('common.save') }}
        </button>
      </template>
    </Modal>

    <!-- Export Hosts Modal -->
    <Modal
      :open="showExportModal"
      @close="closeExportModal"
      :title="$t('hosts.exportModalTitle')"
      max-width="6xl"
    >
      <div v-if="exportConfigLoading" class="py-10">
        <LoadingOverlay :loading="true" :text="$t('hosts.loadingExportConfig')" />
      </div>
      <div v-else class="space-y-6">
        <div>
          <h3 class="text-sm font-medium text-gray-700 mb-3">{{ $t('hosts.exportTemplate') }}</h3>
          <div class="grid gap-3 sm:grid-cols-2">
            <label
              v-for="template in exportTemplateOptions"
              :key="template.id"
              class="flex items-start space-x-3 rounded-lg border border-gray-200 p-3 hover:border-blue-400 cursor-pointer transition"
            >
              <input
                type="radio"
                name="export-template"
                :value="template.id"
                v-model="selectedTemplate"
                class="mt-1 h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <div>
                <p class="text-sm font-medium text-gray-900">
                  {{ template.nameKey ? t(template.nameKey) : template.name }}
                </p>
                <p v-if="template.descriptionKey || template.description" class="mt-1 text-xs text-gray-500">
                  {{ template.descriptionKey ? t(template.descriptionKey) : template.description }}
                </p>
              </div>
            </label>
          </div>
        </div>
        
        <div>
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-medium text-gray-700">{{ $t('hosts.exportSelectFields') }}</h3>
            <button
              type="button"
              class="text-sm text-blue-600 hover:text-blue-800"
              @click="selectAllExportFields"
            >
              {{ $t('hosts.exportSelectAllFields') }}
            </button>
          </div>
          <div class="space-y-4 max-h-[50vh] overflow-y-auto pr-1">
            <div
              v-for="category in exportFieldsByCategory"
              :key="category.id"
              class="border border-gray-200 rounded-lg"
            >
              <div class="px-3 py-2 bg-gray-50 border-b border-gray-200">
                <h4 class="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                  {{ t(category.labelKey) }}
                </h4>
              </div>
              <div class="p-3 grid grid-cols-1 md:grid-cols-2 gap-2">
                <label
                  v-for="field in category.fields"
                  :key="field.key"
                  class="inline-flex items-center space-x-2 rounded-md px-2 py-1 hover:bg-gray-50"
                >
                  <input
                    type="checkbox"
                    :value="field.key"
                    v-model="selectedExportFields"
                    class="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                  />
                  <span class="text-sm text-gray-700">{{ t(field.labelKey) }}</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 w-full">
          <p class="text-sm text-gray-500">
            {{ t('hosts.exportSelectedCount', { count: selectedHosts.length }) }}
          </p>
          <div class="flex flex-col sm:flex-row gap-2 sm:ml-auto">
            <button
              type="button"
              @click="closeExportModal"
              class="inline-flex justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
            >
              {{ $t('common.cancel') }}
            </button>
            <button
              type="button"
              @click="submitExport('selected')"
              :disabled="exportLoading || selectedHosts.length === 0"
              class="inline-flex justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="exportLoading" class="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
              {{ $t('hosts.exportSelectedButton') }}
            </button>
            <button
              type="button"
              @click="submitExport('all')"
              :disabled="exportLoading"
              class="inline-flex justify-center rounded-md bg-gray-800 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="exportLoading" class="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
              {{ $t('hosts.exportAllButton') }}
            </button>
          </div>
        </div>
      </template>
    </Modal>

    <!-- Batch Add To Application Modal -->
    <Modal
      :open="showBatchAddToAppModal"
      @close="closeBatchAddToAppModal"
      :title="$t('hosts.batchAddToApplication')"
      max-width="md"
    >
      <div v-if="loadingApplications" class="py-10">
        <LoadingOverlay :loading="true" :text="$t('applications.loading')" />
      </div>
      <div v-else class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('applications.selectApplication') }} *</label>
          <select
            v-model="selectedApplicationId"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option v-for="app in applicationsOptions" :key="app.id" :value="app.id">
              {{ app.name }} ({{ app.host_count ?? (app.hosts?.length || 0) }} {{ $t('applications.hostUnit') }})
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">{{ $t('applications.relationshipType') }}</label>
          <select
            v-model="selectedRelationshipType"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="member">{{ $t('applications.member') }}</option>
            <option value="depends_on">{{ $t('applications.dependsOn') }}</option>
            <option value="connects_to">{{ $t('applications.connectsTo') }}</option>
            <option value="runs_on">{{ $t('applications.runsOn') }}</option>
          </select>
        </div>
        <div class="border border-gray-200 rounded-md bg-gray-50 p-3">
          <p class="text-sm text-gray-600">
            {{ $t('hosts.selectedHostCount', { count: selectedHosts.length }) }}
          </p>
          <ul class="mt-2 max-h-32 overflow-y-auto text-sm text-gray-500">
            <li
              v-for="hostId in selectedHosts"
              :key="hostId"
              class="truncate"
            >
              {{ getHostDisplayLabel(hostId) }}
            </li>
          </ul>
        </div>
      </div>
      <template #footer>
        <button
          type="button"
          @click="closeBatchAddToAppModal"
          class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto transition-colors"
        >
          {{ $t('common.cancel') }}
        </button>
        <button
          type="button"
          @click="batchAddHostsToApplication"
          :disabled="addingToApplication || !selectedApplicationId"
          class="inline-flex w-full justify-center rounded-md bg-purple-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 sm:ml-3 sm:w-auto disabled:opacity-50 transition-colors"
        >
          {{ addingToApplication ? $t('applications.adding') : $t('applications.confirmAdd') }}
        </button>
      </template>
    </Modal>

    <!-- Batch Delete Confirmation Modal -->
    <Modal :open="showBatchDeleteModal" @close="closeBatchDeleteModal" :title="$t('hosts.batchDelete')" max-width="md">
      <div class="space-y-4">
        <div class="bg-red-50 border border-red-200 rounded-md p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <ExclamationTriangleIcon class="h-5 w-5 text-red-400" />
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800">
                {{ $t('hosts.batchDeleteWarning') }}
              </h3>
              <div class="mt-2 text-sm text-red-700">
                <p>{{ $t('hosts.batchDeleteMessage', { count: selectedHosts.length }) }}</p>
              </div>
            </div>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            {{ $t('hosts.batchDeleteConfirmLabel') }}
          </label>
          <input
            type="text"
            v-model="batchDeleteConfirmText"
            :placeholder="$t('hosts.batchDeleteConfirmPlaceholder')"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-red-500 focus:border-red-500"
            @keyup.enter="batchDeleteConfirmText === 'DELETE' && handleBatchDelete()"
          />
          <p class="mt-1 text-xs text-gray-500">
            {{ $t('hosts.batchDeleteConfirmHint') }}
          </p>
        </div>

        <div class="bg-yellow-50 border border-yellow-200 rounded-md p-3">
          <p class="text-xs text-yellow-800">
            {{ $t('hosts.batchDeleteIrreversible') }}
          </p>
        </div>
      </div>
      <template #footer>
        <button
          type="button"
          @click="closeBatchDeleteModal"
          class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
        >
          {{ $t('common.cancel') }}
        </button>
        <button
          type="button"
          @click="handleBatchDelete"
          :disabled="saving || batchDeleteConfirmText !== 'DELETE'"
          class="inline-flex w-full justify-center rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 sm:ml-3 sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ saving ? $t('common.deleting') : $t('hosts.batchDeleteButton') }}
        </button>
      </template>
    </Modal>

    <!-- Data Import Modal -->
    <Modal
      :open="showDataImportModal"
      @close="closeDataImportModal"
      :title="$t('hosts.dataImportTitle')"
      max-width="6xl"
    >
      <div v-if="importMetadataLoading" class="py-12">
        <LoadingOverlay :loading="true" :text="$t('hosts.loadingImportMetadata')" />
      </div>
      <div v-else class="space-y-6">
        <section class="border border-gray-200 rounded-lg p-4">
          <h3 class="text-sm font-semibold text-gray-700 mb-2">{{ $t('hosts.importStepTemplate') }}</h3>
          <p class="text-xs text-gray-500 mb-4">{{ $t('hosts.importStepTemplateDescription') }}</p>
          <div class="grid gap-3 sm:grid-cols-3">
            <label class="flex items-start space-x-3 rounded-lg border border-gray-200 p-3 hover:border-blue-400 cursor-pointer transition">
              <input
                type="radio"
                value="empty"
                v-model="importTemplateOption"
                class="mt-1 h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <div>
                <p class="text-sm font-medium text-gray-900">{{ $t('hosts.importTemplateOptionEmpty') }}</p>
                <p class="text-xs text-gray-500 mt-1">{{ $t('hosts.importTemplateOptionEmptyDesc') }}</p>
              </div>
            </label>
            <label class="flex items-start space-x-3 rounded-lg border border-gray-200 p-3 hover:border-blue-400 cursor-pointer transition">
              <input
                type="radio"
                value="not_collected"
                v-model="importTemplateOption"
                class="mt-1 h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <div>
                <p class="text-sm font-medium text-gray-900">{{ $t('hosts.importTemplateOptionNotCollected') }}</p>
                <p class="text-xs text-gray-500 mt-1">{{ $t('hosts.importTemplateOptionNotCollectedDesc') }}</p>
              </div>
            </label>
            <label class="flex items-start space-x-3 rounded-lg border border-gray-200 p-3 hover:border-blue-400 cursor-pointer transition">
              <input
                type="radio"
                value="filtered"
                v-model="importTemplateOption"
                class="mt-1 h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <div>
                <p class="text-sm font-medium text-gray-900">{{ $t('hosts.importTemplateOptionFiltered') }}</p>
                <p class="text-xs text-gray-500 mt-1">{{ $t('hosts.importTemplateOptionFilteredDesc') }}</p>
              </div>
            </label>
          </div>
          <div class="mt-4">
            <button
              type="button"
              @click="downloadImportTemplate"
              :disabled="templateDownloading"
              class="inline-flex items-center px-3 py-2 text-sm font-semibold rounded-md text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span
                v-if="templateDownloading"
                class="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"
              ></span>
              {{ $t('hosts.downloadTemplateButton') }}
            </button>
          </div>
        </section>

        <section class="border border-gray-200 rounded-lg p-4">
          <h3 class="text-sm font-semibold text-gray-700 mb-2">{{ $t('hosts.importStepUpload') }}</h3>
          <p class="text-xs text-gray-500 mb-4">{{ $t('hosts.importStepUploadDescription') }}</p>
          <div class="space-y-3">
            <input
              ref="fileInput"
              type="file"
              accept=".csv"
              @change="handleFileSelect"
              class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <p class="text-xs text-gray-500">
              <span v-if="selectedFile">{{ $t('hosts.selectedFileLabel', { name: selectedFile.name }) }}</span>
              <span v-else>{{ $t('hosts.noFileSelected') }}</span>
            </p>
            <div class="flex flex-wrap items-center gap-2">
              <button
                type="button"
                @click="handleImport"
                :disabled="!selectedFile || importing"
                class="inline-flex items-center px-3 py-2 text-sm font-semibold rounded-md text-white bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span
                  v-if="importing"
                  class="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"
                ></span>
                {{ importing ? $t('hosts.importing') : $t('hosts.startImportButton') }}
              </button>
            </div>
          </div>
        </section>

        <section class="border border-gray-200 rounded-lg p-4">
          <h3 class="text-sm font-semibold text-gray-700 mb-3">{{ $t('hosts.importFieldListTitle') }}</h3>
          <div class="grid gap-3 md:grid-cols-2">
            <div
              v-for="column in importColumnsSorted"
              :key="column.key"
              class="rounded-lg border border-dashed border-gray-200 p-3 bg-white"
            >
              <div class="flex items-center justify-between mb-1">
                <p class="text-sm font-medium text-gray-900">
                  {{ column.labelKey ? t(column.labelKey) : column.key }}
                </p>
                <span
                  class="text-xs font-semibold"
                  :class="column.required ? 'text-red-500' : 'text-gray-400'"
                >
                  {{ column.required ? $t('hosts.importFieldRequired') : $t('hosts.importFieldOptional') }}
                </span>
              </div>
              <p v-if="column.descriptionKey" class="text-xs text-gray-500">
                {{ t(column.descriptionKey) }}
              </p>
              <p v-if="column.example" class="text-xs text-gray-400 mt-1">
                {{ $t('hosts.importFieldExample', { example: column.example }) }}
              </p>
            </div>
          </div>
        </section>

        <section v-if="importResult" class="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <h3 class="text-sm font-semibold text-gray-700 mb-2">{{ $t('hosts.importResultTitle') }}</h3>
          <p class="text-sm" :class="importHasErrors ? 'text-yellow-700' : 'text-green-700'">
            {{ importResult.message }}
          </p>
          <p v-if="importResult.data" class="text-xs text-gray-600 mt-1">
            {{ $t('hosts.importResultSummary', { created: importResult.data.created || 0, updated: importResult.data.updated || 0, errors: importErrors.length }) }}
          </p>
          <div v-if="importHasErrors" class="mt-3 border border-yellow-200 bg-yellow-50 rounded">
            <div class="px-3 py-2 border-b border-yellow-200">
              <p class="text-xs font-semibold text-yellow-800">{{ $t('hosts.importErrorsTitle') }}</p>
            </div>
            <div class="border border-yellow-200 rounded-lg overflow-hidden">
              <div class="max-h-[50vh] overflow-y-auto">
                <table class="min-w-full divide-y divide-yellow-200 text-xs">
                  <thead class="bg-yellow-100 sticky top-0 z-10">
                  <tr>
                    <th class="px-3 py-2 text-left font-medium text-yellow-800 whitespace-nowrap">{{ $t('hosts.importErrorRow') }}</th>
                    <th class="px-3 py-2 text-left font-medium text-yellow-800 whitespace-nowrap">{{ $t('hosts.importErrorIp') }}</th>
                    <th class="px-3 py-2 text-left font-medium text-yellow-800">{{ $t('hosts.importErrorMessage') }}</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-yellow-200">
                  <tr
                    v-for="errorItem in importErrors"
                    :key="`${errorItem.row}-${errorItem.ip}-${errorItem.error}`"
                  >
                    <td class="px-3 py-2 text-yellow-900 whitespace-nowrap">{{ errorItem.row }}</td>
                    <td class="px-3 py-2 text-yellow-900 whitespace-nowrap">{{ errorItem.ip }}</td>
                    <td class="px-3 py-2 text-yellow-900">{{ errorItem.error }}</td>
                  </tr>
                </tbody>
              </table>
              </div>
            </div>
          </div>
        </section>
      </div>
      <template #footer>
        <div class="flex justify-end">
          <button
            type="button"
            @click="closeDataImportModal"
            class="inline-flex justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
          >
            {{ $t('common.close') }}
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick, Transition } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { hostsApi, type Host } from '@/api/hosts'
import { applicationsApi } from '@/api/applications'
import { importApi } from '@/api/import'
import { tagsApi } from '@/api/tags'
import Modal from '@/components/Modal.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import LoadingOverlay from '@/components/LoadingOverlay.vue'

interface ExportFieldDefinition {
  key: string
  labelKey: string
  category: string
}

interface ExportCategoryDefinition {
  id: string
  labelKey: string
}

interface ExportTemplateOption {
  id: string
  nameKey?: string
  name?: string
  descriptionKey?: string
  description?: string
  fields: string[]
}

interface ImportColumnDefinition {
  key: string
  labelKey?: string
  descriptionKey?: string
  required?: boolean
  example?: string
}
import { useToastStore } from '@/stores/toast'
import { useSettingsStore } from '@/stores/settings'
import {
  ServerIcon,
  MagnifyingGlassIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  PlusIcon,
  CpuChipIcon,
  ComputerDesktopIcon,
  CloudIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  MagnifyingGlassCircleIcon,
  CloudArrowUpIcon,
  DocumentTextIcon,
  ArrowPathIcon,
  Bars3Icon,
  Bars3BottomLeftIcon,
  Squares2X2Icon,
  EllipsisVerticalIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  FunnelIcon,
  InformationCircleIcon,
  GlobeAltIcon,
  CircleStackIcon,
  LockClosedIcon,
  XMarkIcon,
  TagIcon,
  ExclamationTriangleIcon,
  CheckIcon,
} from '@heroicons/vue/24/outline'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'

const { t } = useI18n()
const toastStore = useToastStore()
const settingsStore = useSettingsStore()
const route = useRoute()

const hosts = ref<Host[]>([])
const loading = ref(false)
const loadingTree = ref(false)
const searchQuery = ref('')
const searchField = ref('all')
const selectedHosts = ref<number[]>([])
const highlightedHostId = ref<number | null>(null)
const viewMode = ref<'list' | 'tree'>('list')
const treeData = ref<any[]>([])
// Track expanded/collapsed state for platforms and ESXi hosts
const expandedPlatforms = ref<Set<number>>(new Set())
const expandedESXiHosts = ref<Set<string>>(new Set())
const expandedErrors = ref<Set<number>>(new Set())
const showCreateModal = ref(false)
const showDetailModal = ref(false)
const showMissingCredentialsModal = ref(false)
const showBatchCredentialsModal = ref(false)
const showTagManagementModal = ref(false)
const tagManagementTarget = ref<Host | null>(null)
const selectedTagIds = ref<number[]>([])
const showBatchTagManagementModal = ref(false)
const batchSelectedTagIds = ref<number[]>([])
const batchHostTagsMap = ref<Map<number, boolean>>(new Map()) // Track which tags are currently on hosts
const showBatchDeleteModal = ref(false)
const batchDeleteConfirmText = ref('')
const missingCredentialsHosts = ref<Array<{id: number, ip: string, hostname?: string}>>([])
const showBatchAddToAppModal = ref(false)
const applicationsOptions = ref<any[]>([])
const selectedApplicationId = ref<number | null>(null)
const selectedRelationshipType = ref('member')
const loadingApplications = ref(false)
const addingToApplication = ref(false)
const batchCredentialsForm = ref({
  username: '',
  password: '',
  ssh_port: 22,
  key_path: '',
  applyToAll: true
})
const hostForm = ref<Partial<Host>>({})
const hostDetail = ref<any>(null)
const editingHostId = ref<number | null>(null)
const saving = ref(false)
const pagination = ref<any>(null)
const perPage = ref(settingsStore.defaultPageSize)
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const importing = ref(false)
const importResult = ref<any>(null)
const showDataImportModal = ref(false)
const importTemplateOption = ref<'empty' | 'not_collected' | 'filtered'>('empty')
const templateDownloading = ref(false)
const importMetadata = ref<ImportColumnDefinition[]>([])
const importMetadataLoading = ref(false)
const importMetadataLoaded = ref(false)
const showConfirmModal = ref(false)
const confirmAction = ref<(() => void) | null>(null)
const confirmMessage = ref('')
const filters = ref({
  os_type: '',
  device_type: '',
  collection_status: '',
  source: '',
  is_physical: '',
  tag_id: '',
})
const availableTags = ref<Array<{id: number, name: string, color?: string}>>([])
const showFilters = ref(false)
const showFieldDropdown = ref(false)
const showValueDropdown = ref(false)
const searchContainer = ref<HTMLElement | null>(null)
const showExportModal = ref(false)
const exportTemplatesList = ref<ExportTemplateOption[]>([])
const exportFieldDefinitionsMap = ref<Record<string, ExportFieldDefinition>>({})
const exportCategoriesList = ref<ExportCategoryDefinition[]>([])
const exportDefaultTemplate = ref('summary')
const exportTemplatesLoaded = ref(false)
const exportConfigLoading = ref(false)
const exportLoading = ref(false)
const selectedTemplate = ref<string>('summary')
const selectedExportFields = ref<string[]>([])

let applyingExportTemplate = false

// Column visibility management
const STORAGE_KEY_COLUMNS = 'hosts_table_visible_columns'
const defaultVisibleColumns = ['checkbox', 'ip', 'hostname', 'os_type', 'distribution', 'os_version', 'device_type', 'cpu_cores', 'memory', 'disk', 'collection_status', 'source', 'tags', 'operation']

// Load visible columns from localStorage or use defaults
const loadVisibleColumns = (): string[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY_COLUMNS)
    if (stored) {
      const parsed = JSON.parse(stored)
      // Ensure required columns are always visible and in correct order
      const required = ['checkbox', 'ip', 'operation']
      // Merge required columns at the beginning, then saved columns, then operation at the end
      const savedWithoutRequired = parsed.filter((col: string) => !required.includes(col))
      return ['checkbox', 'ip', ...savedWithoutRequired, 'operation']
    }
  } catch (e) {
    console.warn('Failed to load column preferences:', e)
  }
  return defaultVisibleColumns
}

const visibleColumns = ref<string[]>(loadVisibleColumns())

// Save to localStorage when changed, but ensure required columns are always included
watch(visibleColumns, (newVal, oldVal) => {
  try {
    // Ensure required columns are always included
    const required = ['checkbox', 'ip', 'operation']
    const filtered = newVal.filter(col => !required.includes(col))
    
    // Only save if the value actually changed (to avoid infinite loops)
    // Check both content and order
    if (oldVal && JSON.stringify(newVal) === JSON.stringify(oldVal)) {
      return
    }
    
    // Save the filtered columns (required columns are always first)
    localStorage.setItem(STORAGE_KEY_COLUMNS, JSON.stringify(filtered))
  } catch (e) {
    console.warn('Failed to save column preferences:', e)
  }
}, { deep: true })

// Column categories
const columnCategories = {
  basic: { label: t('hosts.columnCategory.basic'), icon: 'info' },
  hardware: { label: t('hosts.columnCategory.hardware'), icon: 'cpu' },
  status: { label: t('hosts.columnCategory.status'), icon: 'status' },
  metadata: { label: t('hosts.columnCategory.metadata'), icon: 'tag' },
}

// Available columns configuration with categories and descriptions
const availableColumns = computed(() => [
  { key: 'checkbox', label: t('common.select'), category: 'basic', description: t('hosts.columnDesc.checkbox'), required: true },
  { key: 'ip', label: t('hosts.ip'), category: 'basic', description: t('hosts.columnDesc.ip'), required: true },
  { key: 'hostname', label: t('hosts.hostname'), category: 'basic', description: t('hosts.columnDesc.hostname') },
  { key: 'os_type', label: t('hosts.osType'), category: 'basic', description: t('hosts.columnDesc.osType') },
  { key: 'distribution', label: t('hosts.distribution'), category: 'basic', description: t('hosts.columnDesc.distribution') },
  { key: 'os_version', label: t('hosts.osVersion'), category: 'basic', description: t('hosts.columnDesc.osVersion') },
  { key: 'device_type', label: t('hosts.deviceType'), category: 'basic', description: t('hosts.columnDesc.deviceType') },
  { key: 'cpu_cores', label: t('hosts.cpuCores'), category: 'hardware', description: t('hosts.columnDesc.cpuCores') },
  { key: 'memory', label: t('hosts.memory'), category: 'hardware', description: t('hosts.columnDesc.memory') },
  { key: 'disk', label: t('hosts.disk'), category: 'hardware', description: t('hosts.columnDesc.disk') },
  { key: 'collection_status', label: t('hosts.collectionStatus'), category: 'status', description: t('hosts.columnDesc.collectionStatus') },
  { key: 'source', label: t('hosts.source'), category: 'status', description: t('hosts.columnDesc.source') },
  { key: 'tags', label: t('hosts.tags'), category: 'metadata', description: t('hosts.columnDesc.tags') },
])

// Column templates
const columnTemplates = computed(() => [
  {
    id: 'basic',
    name: t('hosts.columnTemplate.basic'),
    description: t('hosts.columnTemplate.basicDesc'),
    columns: ['checkbox', 'ip', 'hostname', 'os_type', 'device_type', 'operation']
  },
  {
    id: 'detailed',
    name: t('hosts.columnTemplate.detailed'),
    description: t('hosts.columnTemplate.detailedDesc'),
    columns: ['checkbox', 'ip', 'hostname', 'os_type', 'distribution', 'os_version', 'device_type', 'cpu_cores', 'memory', 'disk', 'collection_status', 'source', 'tags', 'operation']
  },
  {
    id: 'hardware',
    name: t('hosts.columnTemplate.hardware'),
    description: t('hosts.columnTemplate.hardwareDesc'),
    columns: ['checkbox', 'ip', 'hostname', 'cpu_cores', 'memory', 'disk', 'operation']
  }
])

// Column search query
const columnSearchQuery = ref('')

// Filtered columns based on search
const filteredColumns = computed(() => {
  if (!columnSearchQuery.value.trim()) {
    return availableColumns.value
  }
  const query = columnSearchQuery.value.toLowerCase().trim()
  return availableColumns.value.filter(column => 
    column.label.toLowerCase().includes(query) ||
    column.key.toLowerCase().includes(query) ||
    column.description?.toLowerCase().includes(query)
  )
})

// Grouped columns by category
const groupedColumns = computed(() => {
  const groups: Record<string, typeof availableColumns.value> = {}
  filteredColumns.value.forEach(column => {
    const category = column.category || 'basic'
    if (!groups[category]) {
      groups[category] = []
    }
    groups[category].push(column)
  })
  return groups
})

// Show grouped view
const showGroupedView = ref(true)

// Visible columns count (excluding required columns for display)
const visibleColumnsCount = computed(() => {
  const required = ['checkbox', 'ip', 'operation']
  return visibleColumns.value.filter(col => !required.includes(col)).length
})

// Helper to check if column is visible
const isColumnVisible = (key: string) => visibleColumns.value.includes(key)

// Select all columns (ensure required columns are always included)
const selectAllColumns = () => {
  const allColumnKeys = availableColumns.value.map(col => col.key)
  const required = ['checkbox', 'ip', 'operation']
  // Merge all columns with required ones, ensuring no duplicates
  visibleColumns.value = [...new Set([...required, ...allColumnKeys])]
}

// Deselect all columns (keep only required ones)
const deselectAllColumns = () => {
  const required = ['checkbox', 'ip', 'operation']
  visibleColumns.value = required
}

// Reset columns to default
const resetColumnsToDefault = () => {
  visibleColumns.value = [...defaultVisibleColumns]
}

// Apply column template
const applyTemplate = (template: typeof columnTemplates.value[0]) => {
  visibleColumns.value = [...template.columns]
}

// Get column label by key
const getColumnLabel = (key: string): string => {
  const column = availableColumns.value.find(col => col.key === key)
  if (!column) return key
  return column.label
}

// Drag and drop handlers for table header
const draggedHeaderColumn = ref<string | null>(null)
const dragOverHeaderIndex = ref<number | null>(null)

const handleHeaderDragStart = (event: DragEvent, columnKey: string) => {
  draggedHeaderColumn.value = columnKey
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', columnKey)
  }
  // Add visual feedback
  if (event.target) {
    (event.target as HTMLElement).classList.add('opacity-50')
  }
}

const handleHeaderDragOver = (event: DragEvent, index: number) => {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
  dragOverHeaderIndex.value = index
}

const handleHeaderDragLeave = () => {
  dragOverHeaderIndex.value = null
}

const handleHeaderDragEnd = (event: DragEvent) => {
  draggedHeaderColumn.value = null
  dragOverHeaderIndex.value = null
  // Remove visual feedback
  if (event.target) {
    (event.target as HTMLElement).classList.remove('opacity-50')
  }
}

const handleHeaderDrop = (event: DragEvent, targetIndex: number) => {
  event.preventDefault()
  if (!draggedHeaderColumn.value) return
  
  const currentIndex = visibleColumns.value.indexOf(draggedHeaderColumn.value)
  if (currentIndex === -1 || currentIndex === targetIndex) {
    handleHeaderDragEnd(event)
    return
  }
  
  // Reorder columns - preserve required columns position
  const required = ['checkbox', 'ip', 'operation']
  const isDraggedRequired = required.includes(draggedHeaderColumn.value)
  const targetColumn = visibleColumns.value[targetIndex]
  const isTargetRequired = required.includes(targetColumn)
  
  // Don't allow moving required columns
  if (isDraggedRequired || isTargetRequired) {
    handleHeaderDragEnd(event)
    return
  }
  
  // Reorder columns
  const newColumns = [...visibleColumns.value]
  newColumns.splice(currentIndex, 1)
  newColumns.splice(targetIndex, 0, draggedHeaderColumn.value)
  visibleColumns.value = newColumns
  
  handleHeaderDragEnd(event)
}

const searchFields = computed(() => [
  { value: 'all', label: t('hosts.searchAll') },
  { value: 'ip', label: t('hosts.ip') },
  { value: 'hostname', label: t('hosts.hostname') },
  { value: 'mac', label: t('hosts.macAddress') },
  { value: 'vendor', label: t('hosts.vendor') },
  { value: 'tag', label: t('hosts.tags') },
])

const allSelected = computed(() => {
  return hosts.value.length > 0 && selectedHosts.value.length === hosts.value.length
})

const exportTemplateOptions = computed(() => {
  const templates = exportTemplatesList.value.map(template => ({
    id: template.id,
    nameKey: template.nameKey,
    name: template.name,
    descriptionKey: template.descriptionKey,
    description: template.description,
    fields: template.fields,
  }))
  return [
    ...templates,
    {
      id: 'custom',
      nameKey: 'hosts.exportTemplateCustom',
      fields: [],
    },
  ]
})

const exportFieldsByCategory = computed(() => {
  return exportCategoriesList.value
    .map(category => ({
      ...category,
      fields: Object.values(exportFieldDefinitionsMap.value).filter(
        field => field.category === category.id
      ),
    }))
    .filter(category => category.fields.length > 0)
})

const allExportFieldKeys = computed(() => Object.keys(exportFieldDefinitionsMap.value))

const importColumnsSorted = computed(() => {
  const columns = [...importMetadata.value]
  return columns.sort((a, b) => {
    const aRequired = a.required ? 1 : 0
    const bRequired = b.required ? 1 : 0
    if (aRequired !== bRequired) {
      return bRequired - aRequired
    }
    return a.key.localeCompare(b.key)
  })
})

const importErrors = computed(() => importResult.value?.data?.errors || [])
const importHasErrors = computed(() => importErrors.value.length > 0)

let searchTimeout: ReturnType<typeof setTimeout> | null = null
let collectingPollInterval: ReturnType<typeof setInterval> | null = null

const buildHostQueryParams = (page?: number, includePaging = true) => {
  const params: Record<string, any> = {}
  
  if (includePaging) {
    params.page = page ?? pagination.value?.page ?? 1
    params.per_page = perPage.value
  }
  
  if (searchQuery.value) {
    if (searchField.value === 'tag') {
      const tag = availableTags.value.find(tagItem => tagItem.name === searchQuery.value)
      if (tag) {
        params.tag_id = tag.id
      }
    } else if (searchField.value === 'all') {
      params.search = searchQuery.value
    } else {
      params.search = searchQuery.value
      params.search_field = searchField.value
    }
  }
  
  if (filters.value.os_type) params.os_type = filters.value.os_type
  if (filters.value.device_type) params.device_type = filters.value.device_type
  if (filters.value.collection_status) params.collection_status = filters.value.collection_status
  if (filters.value.source) params.source = filters.value.source
  if (filters.value.is_physical) params.is_physical = filters.value.is_physical
  if (filters.value.tag_id) {
    const tagIdNumber = Number(filters.value.tag_id)
    if (!Number.isNaN(tagIdNumber)) {
      params.tag_id = tagIdNumber
    }
  }
  
  return params
}

const buildExportFilters = () => {
  const params = buildHostQueryParams(undefined, false)
  return params
}

const loadImportMetadata = async () => {
  if (importMetadataLoaded.value || importMetadataLoading.value) {
    return
  }
  importMetadataLoading.value = true
  try {
    const response: any = await importApi.getHostImportMetadata()
    if (response && response.code === 200) {
      const columns = (response.data?.columns || []).map((column: any) => ({
        key: column.key,
        labelKey: column.label_key,
        descriptionKey: column.description_key,
        required: column.required,
        example: column.example,
      }))
      importMetadata.value = columns
      importMetadataLoaded.value = true
    }
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.loadFailed'))
  } finally {
    importMetadataLoading.value = false
  }
}

const openDataImportModal = async () => {
  importTemplateOption.value = 'empty'
  selectedFile.value = null
  importResult.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  await loadImportMetadata()
  showDataImportModal.value = true
}

const closeDataImportModal = () => {
  showDataImportModal.value = false
  templateDownloading.value = false
  importing.value = false
  importTemplateOption.value = 'empty'
  selectedFile.value = null
  importResult.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const downloadImportTemplate = async () => {
  templateDownloading.value = true
  try {
    const params: Record<string, any> = { template: true }
    if (importTemplateOption.value === 'not_collected') {
      params.prepopulate = 'not_collected'
    } else if (importTemplateOption.value === 'filtered') {
      params.prepopulate = 'filtered'
      Object.assign(params, buildExportFilters())
    } else {
      params.prepopulate = 'none'
    }
    
    const response: any = await hostsApi.exportHostsCSV(params)
    const blob =
      response instanceof Blob
        ? response
        : new Blob([response], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const suffix =
      importTemplateOption.value === 'empty'
        ? 'template'
        : importTemplateOption.value
    link.download = `host_import_${suffix}_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    toastStore.success(t('hosts.templateDownloadSuccess'))
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('hosts.templateDownloadFailed'))
  } finally {
    templateDownloading.value = false
  }
}

const applyRouteQuery = () => {
  const { search, search_field, highlightHostId } = route.query
  if (typeof search === 'string' && search.trim() !== '') {
    searchQuery.value = search
    if (typeof search_field === 'string' && search_field.trim() !== '') {
      searchField.value = search_field as string
    }
  }
  if (typeof highlightHostId === 'string') {
    const parsed = Number(highlightHostId)
    if (!Number.isNaN(parsed)) {
      highlightedHostId.value = parsed
    }
  }
}

const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadHosts(1)
  }, 500)
}

const loadHosts = async (page = 1) => {
  loading.value = true
  try {
    const params = buildHostQueryParams(page, true)
    const response: any = await hostsApi.getHosts(params)
    
    if (response && response.code === 200) {
      hosts.value = Array.isArray(response.data) ? response.data : []
      pagination.value = response.pagination || null
    } else {
      hosts.value = []
      pagination.value = null
      console.warn('Unexpected response format from getHosts:', response)
    }
    
    if (highlightedHostId.value) {
      const highlightId = highlightedHostId.value
      const targetHost = hosts.value.find((h: any) => h.id === highlightId)
      if (targetHost) {
        selectedHosts.value = [highlightId]
      }
    }
    
    const hasCollectingHosts = hosts.value.some((h: any) => h.collection_status === 'collecting')
    if (hasCollectingHosts) {
      startCollectingPoll()
    } else {
      stopCollectingPoll()
    }
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const getSearchPlaceholder = () => {
  if (searchField.value === 'all') {
    return t('hosts.searchPlaceholder')
  }
  const fieldMap: Record<string, string> = {
    'ip': t('hosts.searchIPPlaceholder'),
    'hostname': t('hosts.searchHostnamePlaceholder'),
    'mac': t('hosts.searchMACPlaceholder'),
    'vendor': t('hosts.searchVendorPlaceholder'),
  }
  return fieldMap[searchField.value] || t('hosts.searchPlaceholder')
}

const getFieldLabel = (field: string) => {
  const fieldMap: Record<string, string> = {
    'ip': t('hosts.ip'),
    'hostname': t('hosts.hostname'),
    'mac': t('hosts.macAddress'),
    'vendor': t('hosts.vendor'),
    'tag': t('hosts.tags'),
  }
  return fieldMap[field] || field
}

const selectField = (field: string) => {
  searchField.value = field
  searchQuery.value = ''
  showFieldDropdown.value = false
  
  // If tag field, automatically show value dropdown after a short delay
  if (field === 'tag') {
    // Use nextTick to ensure DOM is updated
    setTimeout(() => {
      showValueDropdown.value = true
    }, 150)
  }
}

const selectTagValue = (tagName: string) => {
  searchQuery.value = tagName
  showValueDropdown.value = false
  loadHosts(1)
}

const clearField = () => {
  searchField.value = 'all'
  searchQuery.value = ''
  loadHosts(1)
}

const clearSearch = () => {
  if (searchQuery.value) {
    // Clear search value only
    searchQuery.value = ''
    if (searchField.value === 'tag') {
      showValueDropdown.value = false
    }
    loadHosts(1)
  } else {
    // Clear field selection
    clearField()
  }
}

const handleInputFocus = () => {
  if (searchField.value === 'all') {
    showFieldDropdown.value = true
  }
}

const handleSearchContainerClick = () => {
  // If clicking on the input or container, show field dropdown if field is 'all'
  if (searchField.value === 'all' && !showFieldDropdown.value) {
    showFieldDropdown.value = true
  }
}

const clearFilters = () => {
  filters.value = {
    os_type: '',
    device_type: '',
    collection_status: '',
    source: '',
    is_physical: '',
    tag_id: '',
  }
  loadHosts(1)
}

const removeFilter = (key: string) => {
  if (key === 'tag_id') {
    filters.value.tag_id = ''
  } else {
    (filters.value as any)[key] = ''
  }
  loadHosts(1)
}

const applyQuickFilter = (status: string) => {
  filters.value.collection_status = status
  showFilters.value = false
  loadHosts(1)
}

const activeFilters = computed(() => {
  const result: Array<{key: string, label: string, value: string}> = []
  
  if (filters.value.os_type) {
    result.push({
      key: 'os_type',
      label: t('hosts.osType'),
      value: filters.value.os_type.charAt(0).toUpperCase() + filters.value.os_type.slice(1)
    })
  }
  
  if (filters.value.device_type) {
    result.push({
      key: 'device_type',
      label: t('hosts.deviceType'),
      value: filters.value.device_type === 'host' ? t('hosts.host') : t('hosts.networkDevice')
    })
  }
  
  if (filters.value.collection_status) {
    const statusMap: Record<string, string> = {
      'not_collected': t('hosts.notCollected'),
      'collecting': t('hosts.collecting'),
      'completed': t('common.completed'),
      'failed': t('common.failed'),
    }
    result.push({
      key: 'collection_status',
      label: t('hosts.collectionStatus'),
      value: statusMap[filters.value.collection_status] || filters.value.collection_status
    })
  }
  
  if (filters.value.source) {
    result.push({
      key: 'source',
      label: t('hosts.source'),
      value: getSourceText(filters.value.source)
    })
  }
  
  if (filters.value.is_physical) {
    result.push({
      key: 'is_physical',
      label: t('hosts.deviceNature'),
      value: filters.value.is_physical === 'true' ? t('hosts.physical') : t('hosts.virtual')
    })
  }
  
  if (filters.value.tag_id) {
    const tag = availableTags.value.find(t => t.id === parseInt(filters.value.tag_id))
    if (tag) {
      result.push({
        key: 'tag_id',
        label: t('hosts.tags'),
        value: tag.name
      })
    }
  }
  
  return result
})

const hasActiveFilters = computed(() => {
  return activeFilters.value.length > 0
})

const getUsageColor = (ratio: number | null | undefined) => {
  if (!ratio) return 'bg-gray-400'
  const usage = 1 - ratio
  if (usage >= 0.9) return 'bg-red-500'
  if (usage >= 0.7) return 'bg-yellow-500'
  return 'bg-green-500'
}

const loadTreeData = async () => {
  loadingTree.value = true
  try {
    const response: any = await hostsApi.getHostsTree()
    if (response && response.code === 200) {
      treeData.value = response.data || []
    } else if (Array.isArray(response)) {
      treeData.value = response
    } else if (response && response.data) {
      treeData.value = response.data
    }
    
    // Auto-expand all platforms and ESXi hosts by default
    if (treeData.value.length > 0) {
      treeData.value.forEach((platform: any) => {
        if (platform.platform_id) {
          expandedPlatforms.value.add(platform.platform_id)
        }
        if (platform.esxi_hosts) {
          platform.esxi_hosts.forEach((esxi: any) => {
            if (esxi.esxi_name) {
              expandedESXiHosts.value.add(esxi.esxi_name)
            }
          })
        }
      })
    }
    
    // Update checkbox indeterminate states after loading
    nextTick(() => {
      updateCheckboxIndeterminateStates()
    })
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.loadFailed'))
    treeData.value = []
  } finally {
    loadingTree.value = false
  }
}

const startCollectingPoll = () => {
  if (collectingPollInterval) {
    return
  }
  collectingPollInterval = setInterval(() => {
    loadHosts(pagination.value?.page || 1)
    if (viewMode.value === 'tree') {
      loadTreeData()
    }
  }, 4000)
}

const stopCollectingPoll = () => {
  if (collectingPollInterval) {
    clearInterval(collectingPollInterval)
    collectingPollInterval = null
  }
}

const toggleHostSelection = (hostId: number) => {
  const index = selectedHosts.value.indexOf(hostId)
  if (index > -1) {
    selectedHosts.value.splice(index, 1)
  } else {
    selectedHosts.value.push(hostId)
  }
  
  // Update indeterminate state after selection change
  nextTick(() => {
    updateCheckboxIndeterminateStates()
  })
}

const toggleSelectAll = () => {
  if (allSelected.value) {
    selectedHosts.value = []
  } else {
    selectedHosts.value = hosts.value.map(h => h.id!).filter(Boolean)
  }
}

// Platform expand/collapse
const togglePlatformExpand = (platformId: number) => {
  if (expandedPlatforms.value.has(platformId)) {
    expandedPlatforms.value.delete(platformId)
  } else {
    expandedPlatforms.value.add(platformId)
  }
}

// ESXi host expand/collapse
const toggleESXiExpand = (esxiName: string) => {
  if (expandedESXiHosts.value.has(esxiName)) {
    expandedESXiHosts.value.delete(esxiName)
  } else {
    expandedESXiHosts.value.add(esxiName)
  }
}

// Get all VM IDs from a platform
const getPlatformVMIds = (platform: any): number[] => {
  const vmIds: number[] = []
  for (const esxi of platform.esxi_hosts || []) {
    for (const vm of esxi.vms || []) {
      if (vm.id) {
        vmIds.push(vm.id)
      }
    }
  }
  return vmIds
}

// Get all VM IDs from an ESXi host
const getESXiVMIds = (esxi: any): number[] => {
  const vmIds: number[] = []
  for (const vm of esxi.vms || []) {
    if (vm.id) {
      vmIds.push(vm.id)
    }
  }
  return vmIds
}

// Check if all VMs in a platform are selected
const isPlatformAllSelected = (platform: any): boolean => {
  const vmIds = getPlatformVMIds(platform)
  if (vmIds.length === 0) return false
  return vmIds.every(id => selectedHosts.value.includes(id))
}

// Check if some (but not all) VMs in a platform are selected
const isPlatformPartiallySelected = (platform: any): boolean => {
  const vmIds = getPlatformVMIds(platform)
  if (vmIds.length === 0) return false
  const selectedCount = vmIds.filter(id => selectedHosts.value.includes(id)).length
  return selectedCount > 0 && selectedCount < vmIds.length
}

// Toggle selection for all VMs in a platform
const togglePlatformSelection = (platform: any) => {
  const vmIds = getPlatformVMIds(platform)
  const allSelected = isPlatformAllSelected(platform)
  
  if (allSelected) {
    // Deselect all
    vmIds.forEach(id => {
      const index = selectedHosts.value.indexOf(id)
      if (index > -1) {
        selectedHosts.value.splice(index, 1)
      }
    })
  } else {
    // Select all
    vmIds.forEach(id => {
      if (!selectedHosts.value.includes(id)) {
        selectedHosts.value.push(id)
      }
    })
  }
  
  // Update indeterminate state after selection change
  nextTick(() => {
    updateCheckboxIndeterminateStates()
  })
}

// Check if all VMs in an ESXi host are selected
const isESXiAllSelected = (esxi: any): boolean => {
  const vmIds = getESXiVMIds(esxi)
  if (vmIds.length === 0) return false
  return vmIds.every(id => selectedHosts.value.includes(id))
}

// Check if some (but not all) VMs in an ESXi host are selected
const isESXiPartiallySelected = (esxi: any): boolean => {
  const vmIds = getESXiVMIds(esxi)
  if (vmIds.length === 0) return false
  const selectedCount = vmIds.filter(id => selectedHosts.value.includes(id)).length
  return selectedCount > 0 && selectedCount < vmIds.length
}

// Toggle selection for all VMs in an ESXi host
const toggleESXiSelection = (esxi: any) => {
  const vmIds = getESXiVMIds(esxi)
  const allSelected = isESXiAllSelected(esxi)
  
  if (allSelected) {
    // Deselect all
    vmIds.forEach(id => {
      const index = selectedHosts.value.indexOf(id)
      if (index > -1) {
        selectedHosts.value.splice(index, 1)
      }
    })
  } else {
    // Select all
    vmIds.forEach(id => {
      if (!selectedHosts.value.includes(id)) {
        selectedHosts.value.push(id)
      }
    })
  }
  
  // Update indeterminate state after selection change
  nextTick(() => {
    updateCheckboxIndeterminateStates()
  })
}

// Store checkbox refs for updating indeterminate state
const platformCheckboxRefs = new Map<number, HTMLInputElement>()
const esxiCheckboxRefs = new Map<string, HTMLInputElement>()

// Update all checkbox indeterminate states
const updateCheckboxIndeterminateStates = () => {
  // Update platform checkboxes
  treeData.value.forEach((platform: any) => {
    if (platform.platform_id) {
      const checkbox = platformCheckboxRefs.get(platform.platform_id)
      if (checkbox) {
        checkbox.indeterminate = isPlatformPartiallySelected(platform)
      }
    }
  })
  
  // Update ESXi checkboxes
  treeData.value.forEach((platform: any) => {
    if (platform.esxi_hosts) {
      platform.esxi_hosts.forEach((esxi: any) => {
        if (esxi.esxi_name) {
          const checkbox = esxiCheckboxRefs.get(esxi.esxi_name)
          if (checkbox) {
            checkbox.indeterminate = isESXiPartiallySelected(esxi)
          }
        }
      })
    }
  })
}

const openCreateModal = () => {
  hostForm.value = {
    is_physical: false,
  }
  editingHostId.value = null
  showCreateModal.value = true
}

const editHost = (host: Host) => {
  hostForm.value = { ...host }
  editingHostId.value = host.id!
  showCreateModal.value = true
}

const closeCreateModal = () => {
  showCreateModal.value = false
  hostForm.value = {}
  editingHostId.value = null
}

const saveHost = async () => {
  saving.value = true
  try {
    if (editingHostId.value) {
      await hostsApi.updateHost(editingHostId.value, hostForm.value)
      toastStore.success(t('hosts.updateSuccess'))
    } else {
      await hostsApi.createHost(hostForm.value as Host)
      toastStore.success(t('hosts.saveSuccess'))
    }
    closeCreateModal()
    loadHosts(pagination.value?.page || 1)
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.saveFailed'))
  } finally {
    saving.value = false
  }
}

const viewHost = async (id: number) => {
  try {
    const [hostRes, credRes] = await Promise.all([
      hostsApi.getHost(id),
      hostsApi.getCredentials(id).catch(() => null),
    ])
    // getHost returns data with include_details=true, so it should have disks, partitions, network_interfaces
    hostDetail.value = {
      ...hostRes.data,
      credentials: credRes?.data || null,
    }
    showDetailModal.value = true
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.loadFailed'))
  }
}

const closeDetailModal = () => {
  showDetailModal.value = false
  hostDetail.value = null
}

const collectHost = async (id: number) => {
  try {
    await hostsApi.batchCollect([id])
    toastStore.success(t('hosts.collectTaskCreated'))
  } catch (error: any) {
    // Check if error is about missing credentials
    if (error.response?.data?.code === 400 && error.response?.data?.data?.missing_credentials) {
      const missing = error.response.data.data.missing_credentials
      showMissingCredentialsModal.value = true
      missingCredentialsHosts.value = missing
      return
    }
    toastStore.error(error.response?.data?.message || t('messages.operationFailed'))
  }
}

const handleBatchCollect = async () => {
  if (selectedHosts.value.length === 0) return
  try {
    await hostsApi.batchCollect(selectedHosts.value)
    toastStore.success(t('hosts.batchCollectSuccess', { count: selectedHosts.value.length }))
    selectedHosts.value = []
  } catch (error: any) {
    // Check if error is about missing credentials
    if (error.response?.data?.code === 400 && error.response?.data?.data?.missing_credentials) {
      const missing = error.response.data.data.missing_credentials
      showMissingCredentialsModal.value = true
      missingCredentialsHosts.value = missing
      return
    }
    toastStore.error(error.response?.data?.message || t('messages.operationFailed'))
  }
}

const deleteHost = async (id: number) => {
  confirmMessage.value = t('hosts.confirmDeleteMessage')
  confirmAction.value = async () => {
    try {
      await hostsApi.deleteHost(id)
      toastStore.success(t('hosts.deleteSuccess'))
      loadHosts(pagination.value?.page || 1)
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

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
    importResult.value = null
  }
}

const handleImport = async () => {
  if (!selectedFile.value) return
  importing.value = true
  try {
    const response = await importApi.importHostsFromCSV(selectedFile.value)
    importResult.value = response
    
    // Check if there are errors in the response
    const hasErrors = response.data?.errors && response.data.errors.length > 0
    
    if (!hasErrors) {
      toastStore.success(response.message || t('hosts.importSuccess'))
      setTimeout(() => {
        closeDataImportModal()
      }, 2000)
    } else {
      // Show warning with error details
      const errorCount = response.data.errors.length
      const errorMessage = response.message || 
        t('hosts.importWithErrors', { count: errorCount })
      toastStore.warning(errorMessage)
    }
    loadHosts(1)
  } catch (error: any) {
    // Handle error response
    const errorMessage = error.response?.data?.message || 
                        error.message || 
                        t('messages.operationFailed')
    toastStore.error(errorMessage)
    console.error('Import error:', error)
  } finally {
    importing.value = false
  }
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

const getCollectionStatusIcon = (status?: string) => {
  const iconMap: Record<string, any> = {
    'not_collected': ClockIcon,
    'collecting': CpuChipIcon,
    'completed': CheckCircleIcon,
    'failed': XCircleIcon,
  }
  return iconMap[status || 'not_collected'] || ClockIcon
}

const toggleHostError = (hostId: number) => {
  if (expandedErrors.value.has(hostId)) {
    expandedErrors.value.delete(hostId)
  } else {
    expandedErrors.value.add(hostId)
  }
}

const getCollectionStatusText = (status?: string) => {
  const textMap: Record<string, string> = {
    'not_collected': t('hosts.notCollected'),
    'collecting': t('hosts.collecting'),
    'completed': t('common.completed'),
    'failed': t('common.failed'),
  }
  return textMap[status || 'not_collected'] || status || ''
}

const getSourceIcon = (source?: string) => {
  const iconMap: Record<string, any> = {
    'scan': MagnifyingGlassCircleIcon,
    'platform': CloudArrowUpIcon,
    'manual': DocumentTextIcon,
  }
  return iconMap[source || 'manual'] || DocumentTextIcon
}

const getSourceIconColor = (source?: string) => {
  const colorMap: Record<string, string> = {
    'scan': 'text-blue-500',
    'platform': 'text-purple-500',
    'manual': 'text-gray-500',
  }
  return colorMap[source || 'manual'] || 'text-gray-500'
}

const getSourceText = (source?: string) => {
  const textMap: Record<string, string> = {
    'scan': t('hosts.scan'),
    'platform': t('hosts.platform'),
    'manual': t('hosts.manual'),
  }
  return textMap[source || 'manual'] || source || ''
}

const formatBytes = (bytes: number, unit: 'GB' | 'MB' = 'GB'): string => {
  if (!bytes || bytes === 0) return '-'
  if (unit === 'GB') {
    const gb = bytes / (1024 * 1024 * 1024)
    return gb >= 1 ? `${gb.toFixed(2)}GB` : `${(gb * 1024).toFixed(2)}MB`
  } else {
    const mb = bytes / (1024 * 1024)
    return `${mb.toFixed(2)}MB`
  }
}

// Format GB value (value is already in GB from database)
const formatGB = (gb: number): string => {
  if (!gb || gb === 0) return '-'
  return `${gb.toFixed(2)} GB`
}

const openBatchCredentialsModal = () => {
  if (selectedHosts.value.length === 0) return
  batchCredentialsForm.value = {
    username: '',
    password: '',
    ssh_port: 22,
    key_path: '',
    applyToAll: true
  }
  showBatchCredentialsModal.value = true
}

const openBatchCredentialsModalFromMissing = () => {
  showMissingCredentialsModal.value = false
  batchCredentialsForm.value = {
    username: '',
    password: '',
    ssh_port: 22,
    key_path: '',
    applyToAll: true
  }
  showBatchCredentialsModal.value = true
}

const closeBatchCredentialsModal = () => {
  showBatchCredentialsModal.value = false
  batchCredentialsForm.value = {
    username: '',
    password: '',
    ssh_port: 22,
    key_path: '',
    applyToAll: true
  }
  missingCredentialsHosts.value = []
}

const saveBatchCredentials = async () => {
  saving.value = true
  try {
    const hostIds = missingCredentialsHosts.value.length > 0 
      ? missingCredentialsHosts.value.map(h => h.id)
      : selectedHosts.value
    
    if (hostIds.length === 0) {
      toastStore.error(t('hosts.selectedHosts'))
      return
    }
    
    const credentials: any = {}
    if (batchCredentialsForm.value.username) {
      credentials.username = batchCredentialsForm.value.username
    }
    if (batchCredentialsForm.value.password) {
      credentials.password = batchCredentialsForm.value.password
    }
    if (batchCredentialsForm.value.ssh_port) {
      credentials.ssh_port = batchCredentialsForm.value.ssh_port
    }
    if (batchCredentialsForm.value.key_path) {
      credentials.key_path = batchCredentialsForm.value.key_path
    }
    
    await hostsApi.batchUpdateCredentials(hostIds, credentials)
    toastStore.success(t('hosts.credentialsUpdated', { count: hostIds.length }))
    closeBatchCredentialsModal()
    if (missingCredentialsHosts.value.length > 0) {
      // Retry collection after updating credentials
      try {
        await hostsApi.batchCollect(hostIds)
        toastStore.success(t('hosts.collectTaskCreated'))
      } catch (error: any) {
        toastStore.error(error.response?.data?.message || t('messages.operationFailed'))
      }
    }
    selectedHosts.value = []
    loadHosts(pagination.value?.page || 1)
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.operationFailed'))
  } finally {
    saving.value = false
  }
}

// Watch view mode changes
watch(viewMode, (newMode) => {
  if (newMode === 'tree') {
    loadTreeData()
  }
})

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
    // Silently fail - tags are optional
    console.warn('Failed to load tags:', error)
  }
}

const showHostTagManagementModal = (host: Host) => {
  tagManagementTarget.value = host
  selectedTagIds.value = host.tags?.map(tag => tag.id!).filter(Boolean) || []
  showTagManagementModal.value = true
}

const closeTagManagementModal = () => {
  showTagManagementModal.value = false
  tagManagementTarget.value = null
  selectedTagIds.value = []
}

const saveHostTags = async () => {
  if (!tagManagementTarget.value || !tagManagementTarget.value.id) return
  
  saving.value = true
  try {
    const hostId = tagManagementTarget.value.id
    const currentTagIds = tagManagementTarget.value.tags?.map(tag => tag.id!).filter(Boolean) || []
    
    // Remove tags that are not in selectedTagIds
    for (const tagId of currentTagIds) {
      if (!selectedTagIds.value.includes(tagId)) {
        await tagsApi.removeHostTag(hostId, tagId)
      }
    }
    
    // Add tags that are in selectedTagIds but not in currentTagIds
    const tagsToAdd = selectedTagIds.value.filter(tagId => !currentTagIds.includes(tagId))
    if (tagsToAdd.length > 0) {
      await tagsApi.addHostTags(hostId, tagsToAdd)
    }
    
    toastStore.success(t('hosts.tagsUpdated'))
    closeTagManagementModal()
    loadHosts(pagination.value?.page || 1)
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.saveFailed'))
  } finally {
    saving.value = false
  }
}

const removeHostTag = async (hostId: number, tagId: number) => {
  try {
    await tagsApi.removeHostTag(hostId, tagId)
    toastStore.success(t('hosts.tagRemoved'))
    loadHosts(pagination.value?.page || 1)
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.operationFailed'))
  }
}

// Export configuration and actions
const loadExportTemplates = async () => {
  exportConfigLoading.value = true
  try {
    const response: any = await hostsApi.getExportTemplates()
    if (response && response.code === 200) {
      const data = response.data || {}
      exportFieldDefinitionsMap.value = Object.entries(data.fields || {}).reduce(
        (acc: Record<string, ExportFieldDefinition>, [key, value]: [string, any]) => {
          acc[key] = {
            key,
            labelKey: value.label_key || '',
            category: value.category || 'basic',
          }
          return acc
        },
        {}
      )
      exportCategoriesList.value = (data.categories || []).map((category: any) => ({
        id: category.id,
        labelKey: category.label_key || '',
      }))
      exportTemplatesList.value = (data.templates || []).map((template: any) => ({
        id: template.id,
        nameKey: template.name_key,
        name: template.name,
        descriptionKey: template.description_key,
        description: template.description,
        fields: template.fields || [],
      }))
      exportDefaultTemplate.value = data.default_template || 'summary'
      exportTemplatesLoaded.value = true
    }
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('hosts.exportFailed'))
  } finally {
    exportConfigLoading.value = false
  }
}

const applyExportTemplate = (templateId: string) => {
  const template = exportTemplatesList.value.find(item => item.id === templateId)
  if (!template) {
    selectedTemplate.value = 'custom'
    return
  }
  applyingExportTemplate = true
  selectedTemplate.value = templateId
  selectedExportFields.value = [...template.fields]
  nextTick(() => {
    applyingExportTemplate = false
  })
}

const openExportModal = async () => {
  if (!exportTemplatesLoaded.value && !exportConfigLoading.value) {
    await loadExportTemplates()
  }
  
  if (!exportTemplatesLoaded.value) {
    return
  }
  
  const defaultTemplateId =
    exportTemplatesList.value.find(template => template.id === exportDefaultTemplate.value)?.id ||
    exportTemplatesList.value[0]?.id ||
    'custom'
  
  if (defaultTemplateId && defaultTemplateId !== 'custom') {
    applyExportTemplate(defaultTemplateId)
  } else {
    selectedTemplate.value = 'custom'
    selectedExportFields.value = [...allExportFieldKeys.value]
  }
  
  showExportModal.value = true
}

const closeExportModal = () => {
  showExportModal.value = false
  exportLoading.value = false
}

const selectAllExportFields = () => {
  selectedExportFields.value = [...allExportFieldKeys.value]
  selectedTemplate.value = 'custom'
}

const submitExport = async (mode: 'selected' | 'all') => {
  if (selectedExportFields.value.length === 0) {
    toastStore.warning(t('hosts.exportNoFieldsSelected'))
    return
  }
  
  if (mode === 'selected' && selectedHosts.value.length === 0) {
    toastStore.warning(t('hosts.noHostsSelected'))
    return
  }
  
  const payload: any = {
    host_ids: mode === 'selected' ? selectedHosts.value : [],
    fields: selectedExportFields.value,
  }
  
  if (selectedTemplate.value && selectedTemplate.value !== 'custom') {
    payload.template = selectedTemplate.value
  }
  
  if (mode === 'all') {
    payload.select_all = true
    payload.filters = buildExportFilters()
  }
  
  exportLoading.value = true
  try {
    const response: any = await hostsApi.exportHostsExcel(payload)
    const blob =
      response instanceof Blob
        ? response
        : new Blob([response], {
            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `hosts_export_${new Date().toISOString().split('T')[0]}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    toastStore.success(t('hosts.exportSuccess'))
    closeExportModal()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('hosts.exportFailed'))
  } finally {
    exportLoading.value = false
  }
}

watch(
  selectedTemplate,
  newValue => {
    if (applyingExportTemplate) {
      return
    }
    if (!exportTemplatesLoaded.value) {
      return
    }
    if (newValue === 'custom') {
      return
    }
    applyExportTemplate(newValue)
  }
)

watch(
  selectedExportFields,
  () => {
    if (!exportTemplatesLoaded.value) {
      return
    }
    if (applyingExportTemplate) {
      return
    }
    selectedTemplate.value = 'custom'
  },
  { deep: true }
)

const openBatchTagManagementModal = async () => {
  if (selectedHosts.value.length === 0) {
    toastStore.warning(t('hosts.noHostsSelected'))
    return
  }
  
  // Load current tags from selected hosts and pre-select them
  await loadBatchHostCurrentTags()
  showBatchTagManagementModal.value = true
}

const closeBatchTagManagementModal = () => {
  showBatchTagManagementModal.value = false
  batchSelectedTagIds.value = []
  batchHostTagsMap.value.clear()
}

const loadBatchHostCurrentTags = async () => {
  try {
    // Get all tags from selected hosts
    const hostTagsSet = new Set<number>()
    batchHostTagsMap.value.clear()
    
    for (const hostId of selectedHosts.value) {
      try {
        const host = hosts.value.find(h => h.id === hostId)
        if (host && host.tags) {
          for (const tag of host.tags) {
            if (tag.id) {
              hostTagsSet.add(tag.id)
              // If tag exists on at least one host, mark it
              if (!batchHostTagsMap.value.has(tag.id)) {
                batchHostTagsMap.value.set(tag.id, true)
              }
            }
          }
        }
      } catch (error) {
        console.error(`Failed to load tags for host ${hostId}:`, error)
      }
    }
    
    // Pre-select tags that exist on any selected host
    batchSelectedTagIds.value = Array.from(hostTagsSet)
  } catch (error: any) {
    console.error('Failed to load batch host current tags:', error)
    batchSelectedTagIds.value = []
  }
}

const loadApplicationsForBatch = async () => {
  loadingApplications.value = true
  try {
    const response = await applicationsApi.getApplications()
    applicationsOptions.value = response.data || []
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('applications.loadFailed'))
    applicationsOptions.value = []
  } finally {
    loadingApplications.value = false
  }
}

const openBatchAddToAppModal = async () => {
  if (selectedHosts.value.length === 0) {
    toastStore.warning(t('hosts.noHostsSelected'))
    return
  }
  await loadApplicationsForBatch()
  if (applicationsOptions.value.length === 0) {
    toastStore.info(t('applications.noAppsForSelection'))
    return
  }
  selectedApplicationId.value = applicationsOptions.value[0]?.id ?? null
  selectedRelationshipType.value = 'member'
  showBatchAddToAppModal.value = true
}

const closeBatchAddToAppModal = () => {
  showBatchAddToAppModal.value = false
  selectedApplicationId.value = null
  selectedRelationshipType.value = 'member'
}

const batchAddHostsToApplication = async () => {
  if (!selectedApplicationId.value) {
    toastStore.warning(t('applications.selectApplicationFirst'))
    return
  }
  if (selectedHosts.value.length === 0) {
    toastStore.warning(t('hosts.noHostsSelected'))
    return
  }
  addingToApplication.value = true
  try {
    await applicationsApi.addHosts(
      selectedApplicationId.value,
      selectedHosts.value,
      selectedRelationshipType.value
    )
    toastStore.success(t('applications.batchAddSuccess', { count: selectedHosts.value.length }))
    closeBatchAddToAppModal()
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('applications.batchAddFailed'))
  } finally {
    addingToApplication.value = false
  }
}

const getHostDisplayLabel = (hostId: number) => {
  const host = hosts.value.find(item => item.id === hostId)
  if (!host) return `${hostId}`
  if (host.hostname) {
    return `${host.ip} - ${host.hostname}`
  }
  return host.ip || `${hostId}`
}

const saveBatchHostTags = async () => {
  if (selectedHosts.value.length === 0) {
    return
  }
  
  saving.value = true
  try {
    let addSuccessCount = 0
    let removeSuccessCount = 0
    let failCount = 0
    
    // Get tags that need to be added and removed
    // Add: tags selected but not currently on hosts
    const tagsToAdd = batchSelectedTagIds.value.filter(tagId => !batchHostTagsMap.value.has(tagId))
    // Remove: tags currently on hosts but not selected
    const tagsToRemove = Array.from(batchHostTagsMap.value.keys()).filter(tagId => !batchSelectedTagIds.value.includes(tagId))
    
    // Process each host
    for (const hostId of selectedHosts.value) {
      try {
        // Add new tags
        if (tagsToAdd.length > 0) {
          try {
            await tagsApi.addHostTags(hostId, tagsToAdd)
          } catch (error: any) {
            console.error(`Failed to add tags to host ${hostId}:`, error)
          }
        }
        
        // Remove unselected tags
        for (const tagId of tagsToRemove) {
          try {
            await tagsApi.removeHostTag(hostId, tagId)
          } catch (error: any) {
            // Ignore errors if tag doesn't exist on host
            console.warn(`Failed to remove tag ${tagId} from host ${hostId}:`, error)
          }
        }
        
        addSuccessCount++
        removeSuccessCount++
      } catch (error: any) {
        console.error(`Failed to update tags for host ${hostId}:`, error)
        failCount++
      }
    }
    
    // Show success messages only if there were changes
    if (tagsToAdd.length === 0 && tagsToRemove.length === 0) {
      toastStore.info(t('hosts.noTagChanges'))
    } else {
      const messages: string[] = []
      if (tagsToAdd.length > 0 && addSuccessCount > 0) {
        messages.push(t('hosts.batchTagsAdded', { count: addSuccessCount }))
      }
      if (tagsToRemove.length > 0 && removeSuccessCount > 0) {
        messages.push(t('hosts.batchTagsRemoved', { count: removeSuccessCount }))
      }
      if (messages.length > 0) {
        toastStore.success(messages.join(', '))
      }
    }
    if (failCount > 0) {
      toastStore.error(t('hosts.batchTagsFailed', { count: failCount }))
    }
    
    closeBatchTagManagementModal()
    selectedHosts.value = []
    loadHosts(pagination.value?.page || 1)
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.operationFailed'))
  } finally {
    saving.value = false
  }
}

const openBatchDeleteModal = () => {
  if (selectedHosts.value.length === 0) {
    toastStore.warning(t('hosts.noHostsSelected'))
    return
  }
  batchDeleteConfirmText.value = ''
  showBatchDeleteModal.value = true
}

const closeBatchDeleteModal = () => {
  showBatchDeleteModal.value = false
  batchDeleteConfirmText.value = ''
}

const handleBatchDelete = async () => {
  if (selectedHosts.value.length === 0) {
    return
  }
  
  if (batchDeleteConfirmText.value !== 'DELETE') {
    toastStore.error(t('hosts.batchDeleteConfirmError'))
    return
  }
  
  saving.value = true
  try {
    const response: any = await hostsApi.batchDeleteHosts(selectedHosts.value)
    
    if (response && response.code === 200) {
      const deletedCount = response.data?.deleted_count || 0
      const failedIds = response.data?.failed_ids || []
      
      if (deletedCount > 0) {
        toastStore.success(t('hosts.batchDeleteSuccess', { count: deletedCount }))
      }
      if (failedIds.length > 0) {
        toastStore.error(t('hosts.batchDeleteFailed', { count: failedIds.length }))
      }
      
      closeBatchDeleteModal()
      selectedHosts.value = []
      loadHosts(pagination.value?.page || 1)
    } else {
      toastStore.error(response?.message || t('messages.operationFailed'))
    }
  } catch (error: any) {
    toastStore.error(error.response?.data?.message || t('messages.operationFailed'))
  } finally {
    saving.value = false
  }
}

// Close dropdowns when clicking outside
const handleClickOutside = (e: MouseEvent) => {
  if (searchContainer.value && !searchContainer.value.contains(e.target as Node)) {
    showFieldDropdown.value = false
    showValueDropdown.value = false
  }
}

onMounted(() => {
  applyRouteQuery()
  loadHosts()
  loadTags()
  if (viewMode.value === 'tree') {
    loadTreeData()
  }
  
  // Setup click outside handler for search dropdowns
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  stopCollectingPoll()
})
</script>
