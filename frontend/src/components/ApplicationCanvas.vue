<template>
  <div class="application-canvas">
    <div ref="canvasWrapper" class="application-canvas__wrapper"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch, nextTick } from 'vue'
import LogicFlow, { GraphConfigData, RectNode, RectNodeModel, h } from '@logicflow/core'
import '@logicflow/core/dist/style/index.css'

import {
  CanvasEdgeData,
  CanvasNodeData,
  CanvasNodeType,
  EdgeType,
  DEFAULT_NODE_HEIGHT,
  DEFAULT_NODE_WIDTH,
} from './ApplicationCanvas/types'

const props = withDefaults(
  defineProps<{
    nodes: CanvasNodeData[]
    edges: CanvasEdgeData[]
    readonly?: boolean
  }>(),
  {
    nodes: () => [],
    edges: () => [],
    readonly: false
  }
)

const emit = defineEmits<{
  'canvas:ready': [LogicFlow]
  'node:click': [CanvasNodeData]
  'edge:click': [CanvasEdgeData]
  'node:moved': [CanvasNodeData]
  'node:removed': [CanvasNodeData]
  'edge:added': [CanvasEdgeData]
  'edge:removed': [CanvasEdgeData]
  'blank:click': []
}>()

const canvasWrapper = ref<HTMLDivElement | null>(null)
let lf: LogicFlow | null = null
const registeredInstances = new WeakSet<LogicFlow>()
let isInternalDrag = false

const TYPE_COLOR_MAP: Record<CanvasNodeType, string> = {
  [CanvasNodeType.HOST]: '#2563eb',
  [CanvasNodeType.NETWORK]: '#0ea5e9',
  [CanvasNodeType.STORAGE]: '#a855f7',
  [CanvasNodeType.OBJECT_STORAGE]: '#f97316',
  [CanvasNodeType.DATABASE]: '#ef4444',
  [CanvasNodeType.SERVICE]: '#6366f1',
  [CanvasNodeType.CUSTOM]: '#0f172a',
}

const TYPE_TINT_MAP: Record<CanvasNodeType, string> = {
  [CanvasNodeType.HOST]: '#eef2ff',
  [CanvasNodeType.NETWORK]: '#f0f9ff',
  [CanvasNodeType.STORAGE]: '#faf5ff',
  [CanvasNodeType.OBJECT_STORAGE]: '#fff7ed',
  [CanvasNodeType.DATABASE]: '#fef2f2',
  [CanvasNodeType.SERVICE]: '#eef2ff',
  [CanvasNodeType.CUSTOM]: '#f8fafc',
}

const TYPE_ICON_PATHS: Record<CanvasNodeType, string[]> = {
  [CanvasNodeType.HOST]: [
    'M9 17.25v1.007a3 3 0 0 1-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0 1 15 18.257V17.25m6-12V15a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 15V5.25m18 0A2.25 2.25 0 0 0 18.75 3H5.25A2.25 2.25 0 0 0 3 5.25m18 0V12a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 12V5.25',
  ],
  [CanvasNodeType.NETWORK]: [
    'M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 0 1 3 12c0-1.605.42-3.113 1.157-4.418',
  ],
  [CanvasNodeType.STORAGE]: [
    'M5.25 14.25h13.5m-13.5 0a3 3 0 0 1-3-3m3 3a3 3 0 1 0 0 6h13.5a3 3 0 1 0 0-6m-16.5-3a3 3 0 0 1 3-3h13.5a3 3 0 0 1 3 3m-19.5 0a4.5 4.5 0 0 1 .9-2.7L5.737 5.1a3.375 3.375 0 0 1 2.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 0 1 .9 2.7m0 0a3 3 0 0 1-3 3m0 3h.008v.008h-.008v-.008Zm0-6h.008v.008h-.008v-.008Zm-3 6h.008v.008h-.008v-.008Zm0-6h.008v.008h-.008v-.008Z',
  ],
  [CanvasNodeType.OBJECT_STORAGE]: [
    'M2.25 15a4.5 4.5 0 0 0 4.5 4.5H18a3.75 3.75 0 0 0 1.332-7.257 3 3 0 0 0-3.758-3.848 5.25 5.25 0 0 0-10.233 2.33A4.502 4.502 0 0 0 2.25 15Z',
  ],
  [CanvasNodeType.DATABASE]: [
    'M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125',
  ],
  [CanvasNodeType.SERVICE]: [
    'M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z',
    'M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z',
  ],
  [CanvasNodeType.CUSTOM]: [
    'M12 6v12',
    'M6 12h12',
  ],
}

const normalizeNodeType = (value: unknown): CanvasNodeType => {
  if (!value) return CanvasNodeType.CUSTOM
  
  // 如果已经是 CanvasNodeType 枚举值，直接返回
  if (typeof value === 'string' && Object.values(CanvasNodeType).includes(value as CanvasNodeType)) {
    return value as CanvasNodeType
  }
  
  if (typeof value === 'string') {
    const normalized = value.trim()
    const lower = normalized.toLowerCase()
    switch (lower) {
      case 'host':
      case 'hosts':
        return CanvasNodeType.HOST
      case 'network':
      case 'networks':
        return CanvasNodeType.NETWORK
      case 'storage':
      case 'storages':
        return CanvasNodeType.STORAGE
      case 'objectstorage':
      case 'object_storage':
      case 'object-storage':
      case 'objectstoragebucket':
      case 'object':
      case 'bucket':
        return CanvasNodeType.OBJECT_STORAGE
      case 'database':
      case 'databases':
        return CanvasNodeType.DATABASE
      case 'service':
      case 'services':
        return CanvasNodeType.SERVICE
      case 'custom':
        return CanvasNodeType.CUSTOM
      default:
        return CanvasNodeType.CUSTOM
    }
  }
  return CanvasNodeType.CUSTOM
}

const initCanvas = () => {
  if (!canvasWrapper.value) return

  lf = new LogicFlow({
    container: canvasWrapper.value,
    isSilentMode: props.readonly,
    grid: {
      visible: true,
      type: 'mesh',
      size: 20
    },
    keyboard: {
      enabled: false
    }
  })

  registerCustomNodes(lf)
  lf.updateEditConfig({
    isSilentMode: props.readonly,
    // Allow background drag for panning while nodes remain draggable individually
    stopMoveGraph: false,
    nodeDraggable: !props.readonly,
    edgeDraggable: !props.readonly,
    adjustNodePosition: true,
    // Enable anchor dragging and auto-snap
    adjustEdgeStartAndEnd: true,
    hoverOutline: false,
  })
  renderGraph()
  attachEventHandlers()
  emit('canvas:ready', lf)
}

const renderGraph = () => {
  if (!lf) return
  
  // 创建节点 ID 集合，用于验证边的 source/target 是否存在
  const nodeIdSet = new Set<string>()
  const nodesData = props.nodes.map((node) => {
    // 优先使用保存的图标类型，如果没有则默认使用 HOST 类型
    const savedIcon = node.icon || node.data?.iconType
    const iconType = savedIcon 
      ? (typeof savedIcon === 'string' ? normalizeNodeType(savedIcon) : (savedIcon as CanvasNodeType))
      : CanvasNodeType.HOST
    const rawType = normalizeNodeType(node.type || CanvasNodeType.HOST)
    // 优先使用保存的自定义颜色
    const customColor = node.data?.customColor || node.data?.color || node.color
    const nodeId = String(node.id)
    nodeIdSet.add(nodeId)
    return {
      id: nodeId,
      type: 'device-node',
      x: node.x,
      y: node.y,
      text: node.label,
      properties: {
        label: node.label,
        icon: iconType,
        color: node.color,
        customColor,
        iconType,
        bindingHostId: node.bindingHostId,
        status: node.status,
        data: node.data || {},
        rawType,
      },
    }
  })
  
  // 过滤边，只保留 source 和 target 都存在的边
  const edgesData = props.edges
    .filter((edge) => {
      const sourceId = String(edge.source)
      const targetId = String(edge.target)
      const sourceExists = nodeIdSet.has(sourceId)
      const targetExists = nodeIdSet.has(targetId)
      if (!sourceExists || !targetExists) {
        console.warn(`Edge ${edge.id} references non-existent nodes: source=${sourceId} (exists: ${sourceExists}), target=${targetId} (exists: ${targetExists})`)
        return false
      }
      return true
    })
    .map((edge) => {
      // 确定边的类型，使用 !== undefined 检查保留空字符串
      const edgeType = edge.edgeType !== undefined ? edge.edgeType : EdgeType.POLYLINE
      // 确定边的样式，使用 !== undefined 检查保留空字符串
      const strokeDasharray = edge.strokeDasharray !== undefined 
        ? edge.strokeDasharray 
        : (edge.data?.dashed ? '5 5' : '')
      const strokeWidth = edge.strokeWidth !== undefined
        ? (typeof edge.strokeWidth === 'number' 
          ? edge.strokeWidth 
          : edge.strokeWidth === 'thin' 
            ? 1 
            : edge.strokeWidth === 'thick' 
              ? 3 
              : 2)
        : 2
      const stroke = edge.stroke !== undefined 
        ? edge.stroke 
        : (edge.data?.stroke !== undefined ? edge.data.stroke : '#94a3b8')
      
      return {
        id: edge.id ? String(edge.id) : undefined,
        type: edgeType,
        sourceNodeId: String(edge.source),
        targetNodeId: String(edge.target),
        text: edge.label || edge.relationshipType,
        properties: {
          relationshipType: edge.relationshipType,
          description: edge.description,
          edgeType,
          strokeDasharray,
          strokeWidth,
          stroke,
          data: edge.data || {},
        },
        style: {
          strokeDasharray,
          strokeWidth,
          stroke,
        },
      }
    })
  
  const data: GraphConfigData = {
    nodes: nodesData,
    edges: edgesData,
  }
  lf.render(data)
  
  // 确保样式正确应用 - 在渲染后更新所有边的样式
  // 添加延迟，确保 LogicFlow 完全渲染完成后再更新样式
  nextTick(() => {
    setTimeout(() => {
      props.edges.forEach((edge) => {
        if (edge.id) {
          try {
            const edgeModel = lf?.getEdgeModelById(String(edge.id))
            if (edgeModel) {
              // 明确检查每个样式属性是否存在，同时更新 style 和 properties，保持数据一致
              const currentStyle = edgeModel.style || {}
              const currentProperties = edgeModel.properties || {}
              
              // 构建要更新的样式对象
              const styleToUpdate: Record<string, any> = {}
              const propertiesToUpdate: Record<string, any> = {}
              
              // 检查并更新 edgeType
              if (edge.edgeType !== undefined && (currentProperties.edgeType !== edge.edgeType || edgeModel.type !== edge.edgeType)) {
                propertiesToUpdate.edgeType = edge.edgeType
                if (edgeModel.setProperties) {
                  edgeModel.setProperties({ edgeType: edge.edgeType })
                }
              }
              
              // 检查并更新 strokeDasharray
              if (edge.strokeDasharray !== undefined && currentStyle.strokeDasharray !== edge.strokeDasharray) {
                styleToUpdate.strokeDasharray = edge.strokeDasharray
                propertiesToUpdate.strokeDasharray = edge.strokeDasharray
              }
              
              // 检查并更新 strokeWidth
              if (edge.strokeWidth !== undefined && currentStyle.strokeWidth !== edge.strokeWidth) {
                styleToUpdate.strokeWidth = edge.strokeWidth
                propertiesToUpdate.strokeWidth = edge.strokeWidth
              }
              
              // 检查并更新 stroke
              if (edge.stroke !== undefined && currentStyle.stroke !== edge.stroke) {
                styleToUpdate.stroke = edge.stroke
                propertiesToUpdate.stroke = edge.stroke
              }
              
              // 如果有样式需要更新
              if (Object.keys(styleToUpdate).length > 0) {
                if (typeof edgeModel.updateStyle === 'function') {
                  edgeModel.updateStyle(styleToUpdate)
                } else {
                  // 如果 updateStyle 不存在，直接设置 style 属性
                  Object.assign(edgeModel.style || {}, styleToUpdate)
                  edgeModel.updateAttributes()
                }
              }
              
              // 如果有属性需要更新
              if (Object.keys(propertiesToUpdate).length > 0 && edgeModel.setProperties) {
                edgeModel.setProperties(propertiesToUpdate)
              }
            }
          } catch (error) {
            console.warn(`Failed to update style for edge ${edge.id}:`, error)
          }
        }
      })
    }, 100) // 100ms 延迟，确保 LogicFlow 完全渲染完成
  })
}

const registerCustomNodes = (instance: LogicFlow) => {
  if (registeredInstances.has(instance)) {
    return
  }

  const createIconNodes = (iconType: CanvasNodeType, cx: number, cy: number, stroke: string, size: number) => {
    const nodes: any[] = []
    // 确保 iconType 是有效的 CanvasNodeType
    const validIconType = iconType && Object.values(CanvasNodeType).includes(iconType) 
      ? iconType 
      : CanvasNodeType.CUSTOM
    const paths = TYPE_ICON_PATHS[validIconType] || TYPE_ICON_PATHS[CanvasNodeType.CUSTOM]
    if (paths && paths.length > 0) {
        nodes.push(
        h(
          'svg',
          {
            x: cx - size / 2,
            y: cy - size / 2,
            width: size,
            height: size,
            viewBox: '0 0 24 24',
            fill: 'none',
            stroke,
            'stroke-width': 1.5,
          },
          paths.map((d) =>
          h('path', {
              d,
              'stroke-linecap': 'round',
              'stroke-linejoin': 'round',
            })
          )
        )
      )
      return nodes
    }

    const fallbackRadius = size / 3
        nodes.push(
          h('circle', {
            cx,
            cy,
        r: fallbackRadius,
            stroke,
        'stroke-width': 1.5,
            fill: 'none',
          }),
          h('line', {
            x1: cx,
        y1: cy - fallbackRadius * 0.6,
            x2: cx,
        y2: cy + fallbackRadius * 0.6,
            stroke,
        'stroke-width': 1.5,
        'stroke-linecap': 'round',
          }),
          h('line', {
        x1: cx - fallbackRadius * 0.6,
            y1: cy,
        x2: cx + fallbackRadius * 0.6,
            y2: cy,
            stroke,
        'stroke-width': 1.5,
        'stroke-linecap': 'round',
          })
        )
    return nodes
  }

  class DeviceNodeModel extends RectNodeModel {
    setAttributes() {
      const self = this as any
      if (typeof super.setAttributes === 'function') {
        super.setAttributes()
      }
      self.width = DEFAULT_NODE_WIDTH
      self.height = DEFAULT_NODE_HEIGHT
      if (self.text) {
        self.text.editable = false
        self.text.value = ''
      }
      self.draggable = true
    }

    getDefaultAnchor() {
      const self = this as any
      const { x, y, width, height } = self
      const radius = Math.min(width, height) / 2
      const diagonalOffset = radius * Math.SQRT1_2
      return [
        { x, y: y - radius, id: `${self.id}_top`, type: 'top' },
        { x: x + radius, y, id: `${self.id}_right`, type: 'right' },
        { x, y: y + radius, id: `${self.id}_bottom`, type: 'bottom' },
        { x: x - radius, y, id: `${self.id}_left`, type: 'left' },
        { x: x + diagonalOffset, y: y - diagonalOffset, id: `${self.id}_top_right`, type: 'top-right' },
        { x: x + diagonalOffset, y: y + diagonalOffset, id: `${self.id}_bottom_right`, type: 'bottom-right' },
        { x: x - diagonalOffset, y: y + diagonalOffset, id: `${self.id}_bottom_left`, type: 'bottom-left' },
        { x: x - diagonalOffset, y: y - diagonalOffset, id: `${self.id}_top_left`, type: 'top-left' },
      ]
    }

    getAnchors() {
      return this.getDefaultAnchor()
    }

    getAnchorStyle() {
      const style = typeof super.getAnchorStyle === 'function' ? super.getAnchorStyle() : {}
      return {
        ...style,
        r: 2.5,
        stroke: '#2563eb',
        'stroke-width': 1.5,
        fill: '#ffffff',
      }
    }
  }

  class DeviceNodeView extends RectNode {
    getShape() {
      const { model } = (this as any).props
      const { x, y, width, height } = model
      const properties = typeof (model as any).getProperties === 'function'
        ? (model as any).getProperties()
        : (model as any).properties || {}
      // 优先使用保存的图标类型，如果没有则默认使用 HOST 类型，不再回退到 rawType
      const savedIcon = properties.icon || properties.iconType
      const iconType = savedIcon
        ? (typeof savedIcon === 'string' ? normalizeNodeType(savedIcon) : (savedIcon as CanvasNodeType))
        : CanvasNodeType.HOST
      const rawType = normalizeNodeType(properties.rawType || properties.type || CanvasNodeType.HOST)
      // 优先使用保存的自定义颜色
      const nodeColor = properties.customColor || properties.color || TYPE_COLOR_MAP[rawType] || '#2563eb'
      const hostData = properties.data || {}
      const hostname = hostData.hostname || hostData.name || ''
      const ip = hostData.ip || hostData.ip_address || ''
      const primaryLabel =
        properties.label ||
        model.getText()?.value ||
        hostname ||
        ip ||
        'Resource'
      const secondaryLabel =
        ip && ip !== primaryLabel ? ip : (hostData.vendor || '')
      const status = properties.status || hostData.device_type || hostData.os_type || ''
      const radius = Math.min(width, height) / 2
      const outerRadius = radius
      const innerRadius = radius * 0.78
      const labelY = y + innerRadius + 20
      const secondaryY = labelY + 16
      const statusY = secondaryLabel ? secondaryY + 16 : labelY + 16
      const tintColor = TYPE_TINT_MAP[rawType] || '#f8fafc'

      const tooltipLines = [primaryLabel]
      if (secondaryLabel && secondaryLabel !== primaryLabel) {
        tooltipLines.push(secondaryLabel)
      }
      if (status && status !== primaryLabel && status !== secondaryLabel) {
        tooltipLines.push(status)
      }
      const titleNode = tooltipLines.length > 0 ? h('title', {}, tooltipLines.join('\n')) : null

      const modelAny = model as any
      const isSelected =
        (typeof modelAny.getState === 'function' && modelAny.getState() === 'selected') ||
        modelAny.state === 'selected' ||
        (modelAny.graphModel?.selectElement?.id === modelAny.id) ||
        !!modelAny.isSelected

      const highlightCircle = h('circle', {
        cx: x,
        cy: y,
        r: outerRadius,
        fill: '#ffffff',
        stroke: isSelected ? nodeColor : '#e2e8f0',
        'stroke-width': isSelected ? 2.5 : 1.5,
        opacity: isSelected ? 0.6 : 1,
      })

      const headerClip = h('circle', {
        cx: x,
        cy: y,
        r: innerRadius + 6,
        fill: tintColor,
        opacity: 0.9,
      })

      const innerCircle = h('circle', {
        cx: x,
        cy: y,
        r: innerRadius,
        fill: isSelected ? (TYPE_TINT_MAP[rawType] || '#e0f2fe') : '#ffffff',
        stroke: '#ffffff',
        'stroke-width': 4,
      })

      const iconCircle = h('circle', {
        cx: x,
        cy: y,
        r: innerRadius * 0.88,
        fill: nodeColor,
        opacity: 0.96,
      })

      const iconNodes = createIconNodes(iconType, x, y, '#ffffff', innerRadius * 1.35)

      const labelText = h('text', {
        x,
        y: labelY,
        'text-anchor': 'middle',
        'dominant-baseline': 'middle',
        'font-size': 14,
        fill: '#0f172a',
        'font-family': 'Inter, sans-serif',
        'font-weight': 600,
      }, primaryLabel)

      const secondaryText = secondaryLabel
        ? h('text', {
            x,
            y: secondaryY,
            'text-anchor': 'middle',
            'dominant-baseline': 'middle',
            'font-size': 12,
            fill: '#4b5563',
            'font-family': 'Inter, sans-serif',
          }, secondaryLabel)
        : null

      const statusText = status
        ? (() => {
            const paddingX = 16
            const paddingY = 8
            const approximateWidth = Math.max(status.length * 7 + paddingX * 2, 80)
            const badgeX = x - approximateWidth / 2
            const badgeY = statusY - paddingY
            return h('g', {}, [
              h('rect', {
                x: badgeX,
                y: badgeY,
                width: approximateWidth,
                height: paddingY * 2,
                rx: 999,
                ry: 999,
                fill: '#f1f5f9',
              }),
              h('text', {
                x,
                y: statusY,
                'text-anchor': 'middle',
                'dominant-baseline': 'middle',
                'font-size': 12,
                fill: '#475569',
                'font-family': 'Inter, sans-serif',
                'font-weight': 500,
              }, status)
            ])
          })()
        : null

      return h('g', { className: 'application-device-node' }, [
        highlightCircle,
        headerClip,
        innerCircle,
        iconCircle,
        ...iconNodes,
        labelText,
        secondaryText,
        statusText,
        titleNode,
      ].filter(Boolean))
    }
  }

  instance.register({
    type: 'device-node',
    view: DeviceNodeView,
    model: DeviceNodeModel,
  })
  registeredInstances.add(instance)
}

onMounted(() => {
  nextTick(() => initCanvas())
})

onBeforeUnmount(() => {
  if (lf) {
    try {
      lf.graphModel?.clearData?.()
    } catch (error) {
      console.warn('Failed to cleanup LogicFlow instance', error)
    }
    lf = null
  }
})

watch(
  () => [props.nodes, props.edges, props.readonly],
  () => {
    if (!lf) {
      nextTick(() => initCanvas())
      return
    }
    if (isInternalDrag) {
      return
    }
    lf.updateEditConfig({
      isSilentMode: props.readonly,
      stopMoveGraph: false,
      nodeDraggable: !props.readonly,
      edgeDraggable: !props.readonly,
      adjustNodePosition: true,
    })
    renderGraph()
  },
  { deep: true, flush: 'post' }
)

const attachEventHandlers = () => {
  if (!lf) return

  lf.on('node:click', ({ data }: { data: any }) => {
    const node = mapLfNodeToCanvasNode(data)
    emit('node:click', node)
  })

  lf.on('edge:click', ({ data }: { data: any }) => {
    const edge = mapLfEdgeToCanvasEdge(data)
    emit('edge:click', edge)
  })

  lf.on('node:mousemove', ({ data }: { data: any }) => {
    isInternalDrag = true
    const node = mapLfNodeToCanvasNode(data)
    emit('node:moved', node)
    requestAnimationFrame(() => {
      isInternalDrag = false
    })
  })

  // 跟踪正在调整的边（锚点移动）
  // LogicFlow 在拖动锚点时，会先触发 edge:delete，然后触发 edge:add
  // 我们需要跟踪这个过程，避免误删除关系
  let adjustingEdgeId: string | null = null
  let adjustingEdgeData: any = null

  lf.on('edge:delete', ({ data }: { data: any }) => {
    const edgeId = data?.id ? String(data.id) : null
    // 如果边有ID，可能是锚点调整，先保存数据
    if (edgeId) {
      adjustingEdgeId = edgeId
      adjustingEdgeData = data
      // 不立即触发删除事件，等待 edge:add 确认
      return
    }
    // 没有ID的边，直接删除
    const edge = mapLfEdgeToCanvasEdge(data)
    emit('edge:removed', edge)
  })

  lf.on('edge:add', ({ data }: { data: any }) => {
    const edgeId = data?.id ? String(data.id) : null
    // 如果这是正在调整的边，说明是锚点移动，只更新source/target
    if (adjustingEdgeId && edgeId === adjustingEdgeId) {
      const edge = mapLfEdgeToCanvasEdge(data)
      emit('edge:added', { ...edge, _isAdjusting: true })
      adjustingEdgeId = null
      adjustingEdgeData = null
      return
    }
    // 正常添加边
    const edge = mapLfEdgeToCanvasEdge(data)
    emit('edge:added', edge)
  })

  lf.on('blank:click', () => {
    // 如果点击空白区域时还有未处理的调整，说明调整被取消，需要恢复删除
    if (adjustingEdgeId && adjustingEdgeData) {
      const edge = mapLfEdgeToCanvasEdge(adjustingEdgeData)
      emit('edge:removed', edge)
    }
    adjustingEdgeId = null
    adjustingEdgeData = null
    emit('blank:click')
  })

  lf.on('node:delete', ({ data }: { data: any }) => {
    const node = mapLfNodeToCanvasNode(data)
    emit('node:removed', node)
  })
}

const mapLfNodeToCanvasNode = (node: any): CanvasNodeData => {
  const properties = node.properties || {}
  const iconType = normalizeNodeType(properties.icon || properties.iconType || properties.rawType)
  return {
    id: node.id,
    type: iconType,
    x: node.x,
    y: node.y,
    label: properties.label || node.text?.value || '',
    icon: iconType,
    color: properties.customColor || properties.color,
    bindingHostId: properties.bindingHostId,
    status: properties.status,
    data: {
      ...(properties.data || {}),
      iconType,
      customColor: properties.customColor || properties.color,
    },
  }
}

const mapLfEdgeToCanvasEdge = (edge: any): CanvasEdgeData => {
  const properties = edge.properties || {}
  const style = edge.style || {}
  return {
    id: edge.id,
    source: edge.sourceNodeId,
    target: edge.targetNodeId,
    relationshipType: properties.relationshipType,
    label: edge.text?.value || properties.relationshipType || '',
    description: properties.description,
    // 使用 !== undefined 检查保留空字符串和 falsy 值
    edgeType: properties.edgeType !== undefined ? properties.edgeType : (edge.type !== undefined ? edge.type : EdgeType.POLYLINE),
    strokeDasharray: style.strokeDasharray !== undefined ? style.strokeDasharray : (properties.strokeDasharray !== undefined ? properties.strokeDasharray : ''),
    strokeWidth: style.strokeWidth !== undefined ? style.strokeWidth : (properties.strokeWidth !== undefined ? properties.strokeWidth : 2),
    stroke: style.stroke !== undefined ? style.stroke : (properties.stroke !== undefined ? properties.stroke : '#94a3b8'),
    data: properties.data || {},
  }
}

const addNode = (node: CanvasNodeData) => {
  if (!lf) return
  const iconType = normalizeNodeType(node.icon || node.data?.iconType || node.type)
  lf.addNode({
    id: String(node.id),
    type: 'device-node',
    x: node.x,
    y: node.y,
    text: node.label,
    properties: {
      label: node.label,
      icon: node.icon,
      color: node.color,
      customColor: node.data?.customColor ?? node.color,
      iconType,
      bindingHostId: node.bindingHostId,
      status: node.status,
      data: node.data || {},
      rawType: iconType,
    },
  })
}

const addEdge = (edge: CanvasEdgeData) => {
  if (!lf) return
  const edgeType = edge.edgeType || EdgeType.POLYLINE
  const strokeDasharray = edge.strokeDasharray || ''
  const strokeWidth = typeof edge.strokeWidth === 'number' 
    ? edge.strokeWidth 
    : edge.strokeWidth === 'thin' 
      ? 1 
      : edge.strokeWidth === 'thick' 
        ? 3 
        : 2
  const stroke = edge.stroke || '#94a3b8'
  
  lf.addEdge({
    id: edge.id ? String(edge.id) : undefined,
    type: edgeType,
    sourceNodeId: String(edge.source),
    targetNodeId: String(edge.target),
    text: edge.label || edge.relationshipType,
    properties: {
      relationshipType: edge.relationshipType,
      description: edge.description,
      edgeType,
      strokeDasharray,
      strokeWidth,
      stroke,
      data: edge.data || {},
    },
    style: {
      strokeDasharray,
      strokeWidth,
      stroke,
    },
  })
}

const removeNode = (id: string | number) => {
  if (!lf) return
  lf.deleteNode(String(id))
}

const removeEdge = (id: string | number) => {
  if (!lf) return
  lf.deleteEdge(String(id))
}

const clear = () => {
  lf?.clearData()
}

defineExpose({
  addNode,
  addEdge,
  removeNode,
  removeEdge,
  clear,
  getLogicFlow: () => lf,
})

</script>

<style scoped>
.application-canvas {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.application-canvas__wrapper {
  flex: 1;
  min-height: 400px;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
  background-color: #ffffff;
}
</style>

