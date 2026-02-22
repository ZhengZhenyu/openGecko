declare module 'frappe-gantt' {
  interface GanttTask {
    id: string
    name: string
    start: string
    end: string
    progress?: number
    dependencies?: string
    custom_class?: string
    [key: string]: unknown
  }

  type ViewMode = 'Quarter Day' | 'Half Day' | 'Day' | 'Week' | 'Month' | 'Year'

  interface GanttOptions {
    view_mode?: ViewMode
    date_format?: string
    language?: string
    popup_trigger?: string
    custom_popup_html?: ((task: GanttTask) => string) | null
    on_click?: (task: GanttTask) => void
    on_date_change?: (task: GanttTask, start: Date, end: Date) => void
    on_progress_change?: (task: GanttTask, progress: number) => void
    on_view_change?: (mode: ViewMode) => void
    header_height?: number
    column_width?: number
    step?: number
    bar_height?: number
    bar_corner_radius?: number
    arrow_curve?: number
    padding?: number
  }

  class Gantt {
    constructor(
      element: HTMLElement | string,
      tasks: GanttTask[],
      options?: GanttOptions
    )
    change_view_mode(mode: ViewMode): void
    refresh(tasks: GanttTask[]): void
  }

  export default Gantt
}
