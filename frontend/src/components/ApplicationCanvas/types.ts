export enum CanvasNodeType {
  HOST = 'host',
  NETWORK = 'network',
  STORAGE = 'storage',
  OBJECT_STORAGE = 'objectStorage',
  DATABASE = 'database',
  SERVICE = 'service',
  CUSTOM = 'custom',
}

export type CanvasNodeStatus = string

export interface CanvasNodeData {
  id: string | number
  /**
   * Node type to drive styling/icon
   */
  type: CanvasNodeType
  /**
   * Position on canvas
   */
  x: number
  y: number
  /**
   * Display label
   */
  label: string
  /**
   * Optional icon name or URL
   */
  icon?: string
  /**
   * Accent color for icon badge
   */
  color?: string
  /**
   * Optional host binding
   */
  bindingHostId?: number
  /**
   * Device status for styling
   */
  status?: CanvasNodeStatus
  /**
   * Additional metadata
   */
  data?: Record<string, any>
}

export enum EdgeType {
  POLYLINE = 'polyline',
  LINE = 'line',
  BEZIER = 'bezier',
}

export enum EdgeStyle {
  SOLID = 'solid',
  DASHED = 'dashed',
}

export enum EdgeWidth {
  THIN = 'thin',
  MEDIUM = 'medium',
  THICK = 'thick',
}

export interface CanvasEdgeData {
  id?: string | number
  source: string | number
  target: string | number
  relationshipType?: string
  label?: string
  description?: string
  // Edge style properties
  edgeType?: EdgeType | string
  strokeDasharray?: string
  strokeWidth?: number | EdgeWidth
  stroke?: string
  data?: Record<string, any>
}

export interface CanvasGraphData {
  nodes: CanvasNodeData[]
  edges: CanvasEdgeData[]
}

export const DEFAULT_NODE_WIDTH = 65 
export const DEFAULT_NODE_HEIGHT = 75

