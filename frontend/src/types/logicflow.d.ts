declare module '@logicflow/core' {
  export type GraphConfigData = any
  export const h: any

  export class RectNode {
    [key: string]: any
  }

  export class RectNodeModel {
    [key: string]: any
  }

  export class PolylineEdgeModel {
    [key: string]: any
  }

  export default class LogicFlow {
    constructor(options: any)
    register(config: any): void
    render(data: GraphConfigData): void
    addNode(node: any): void
    addEdge(edge: any): void
    deleteNode(id: string): void
    deleteEdge(id: string): void
    clearData(): void
    updateEditConfig(config: any): void
    on(eventName: string, callback: (payload: any) => void): void
    off(eventName: string, callback?: (payload: any) => void): void
    graphModel?: { clearData?: () => void }
    zoom(delta: number, point?: { x: number; y: number }): void
    zoomTo(zoomRatio: number, point?: { x: number; y: number }): void
    getZoom(): number
    resetZoom(): void
    fitView(): void
    getPointByClient(x: number, y: number): {
      domOverlayPosition: { x: number; y: number }
      canvasOverlayPosition: { x: number; y: number }
    }
    getSnapshot(): string | Promise<string>
    getGraphSnapshot(): string | Promise<string>
  }
}

