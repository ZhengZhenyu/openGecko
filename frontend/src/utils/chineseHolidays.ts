/**
 * 中国节假日数据工具
 *
 * 数据来源
 * --------
 * 法定节假日（isOffDay: true = 假期，false = 调休补班）：
 *   NateScarlet/holiday-cn — MIT 开源项目，每日自动抓取国务院公告
 *   JSON CDN: https://cdn.jsdelivr.net/gh/NateScarlet/holiday-cn@master/{year}.json
 *   数据格式: { year, papers, days: [{ name, date, isOffDay }] }
 *
 * 传统节日（非法定假期，公历日期按农历换算）：
 *   静态内置，每年人工维护一次。
 *
 * 缓存策略
 * --------
 * 法定节假日数据缓存到 localStorage，key = `holiday-cn-{year}`，
 * 附带 `_fetchedAt` 时间戳，超过 CACHE_TTL_MS 后自动重新拉取。
 */

// ──────────────────────────────────────────────────────────────
// 类型定义
// ──────────────────────────────────────────────────────────────

/** FullCalendar 兼容的节假日事件对象 */
export interface HolidayEvent {
  id: string
  title: string
  start: string
  end: string   // exclusive（FullCalendar allDay 惯例）
  allDay: true
  display: 'block'
  editable: false
  color: string
  backgroundColor: string
  borderColor: string
  textColor: string
  classNames: string[]
  extendedProps: { isHoliday: true; holidayType: 'publicHoliday' | 'traditional' }
}

/** holiday-cn JSON 单条记录 */
interface HolidayCNDay {
  name: string
  date: string      // YYYY-MM-DD
  isOffDay: boolean // true = 假期，false = 调休补班
}

/** holiday-cn JSON 年度文件结构 */
interface HolidayCNYear {
  year: number
  papers: string[]
  days: HolidayCNDay[]
}

// ──────────────────────────────────────────────────────────────
// 配置
// ──────────────────────────────────────────────────────────────

const CACHE_TTL_MS = 24 * 60 * 60 * 1000 // 24 小时

const CDN_URL = (year: number) =>
  `https://cdn.jsdelivr.net/gh/NateScarlet/holiday-cn@master/${year}.json`

// ──────────────────────────────────────────────────────────────
// 传统节日静态数据（非法定假期，仅标注名称）
//   每年 12 月前后按农历换算更新一次即可
// ──────────────────────────────────────────────────────────────

interface TraditionalHoliday {
  name: string
  date: string // YYYY-MM-DD
}

const TRADITIONAL_HOLIDAYS: TraditionalHoliday[] = [
  // 2025
  { name: '腊八节', date: '2025-01-07' },
  { name: '元宵节', date: '2025-02-12' },
  { name: '七夕',   date: '2025-08-29' },
  { name: '重阳节', date: '2025-10-29' },
  { name: '冬至',   date: '2025-12-22' },
  // 2026
  { name: '腊八节', date: '2026-01-27' },
  { name: '元宵节', date: '2026-03-03' },
  { name: '七夕',   date: '2026-08-26' },
  { name: '重阳节', date: '2026-10-17' },
  { name: '冬至',   date: '2026-12-22' },
  // 2027
  { name: '腊八节', date: '2027-01-16' },
  { name: '元宵节', date: '2027-02-20' },
  { name: '七夕',   date: '2027-08-16' },
  { name: '重阳节', date: '2027-10-07' },
  { name: '冬至',   date: '2027-12-22' },
]

// ──────────────────────────────────────────────────────────────
// 内置 Fallback（holiday-cn 拉取失败时使用）
// 数据来源：国务院办公厅节假日放假通知
// ──────────────────────────────────────────────────────────────

const FALLBACK_HOLIDAYS: Record<number, HolidayCNDay[]> = {
  2025: [
    { name: '元旦',       date: '2025-01-01', isOffDay: true },
    { name: '春节',       date: '2025-01-28', isOffDay: true },
    { name: '春节',       date: '2025-01-29', isOffDay: true },
    { name: '春节',       date: '2025-01-30', isOffDay: true },
    { name: '春节',       date: '2025-01-31', isOffDay: true },
    { name: '春节',       date: '2025-02-01', isOffDay: true },
    { name: '春节',       date: '2025-02-02', isOffDay: true },
    { name: '春节',       date: '2025-02-03', isOffDay: true },
    { name: '春节',       date: '2025-02-04', isOffDay: true },
    { name: '春节前补班',  date: '2025-01-26', isOffDay: false },
    { name: '春节后补班',  date: '2025-02-08', isOffDay: false },
    { name: '清明节',     date: '2025-04-04', isOffDay: true },
    { name: '清明节',     date: '2025-04-05', isOffDay: true },
    { name: '清明节',     date: '2025-04-06', isOffDay: true },
    { name: '劳动节',     date: '2025-05-01', isOffDay: true },
    { name: '劳动节',     date: '2025-05-02', isOffDay: true },
    { name: '劳动节',     date: '2025-05-03', isOffDay: true },
    { name: '劳动节',     date: '2025-05-04', isOffDay: true },
    { name: '劳动节',     date: '2025-05-05', isOffDay: true },
    { name: '劳动节前补班', date: '2025-04-27', isOffDay: false },
    { name: '端午节',     date: '2025-05-31', isOffDay: true },
    { name: '端午节',     date: '2025-06-01', isOffDay: true },
    { name: '端午节',     date: '2025-06-02', isOffDay: true },
    { name: '国庆节',     date: '2025-10-01', isOffDay: true },
    { name: '国庆节',     date: '2025-10-02', isOffDay: true },
    { name: '国庆节',     date: '2025-10-03', isOffDay: true },
    { name: '国庆节',     date: '2025-10-04', isOffDay: true },
    { name: '国庆节',     date: '2025-10-05', isOffDay: true },
    { name: '国庆节',     date: '2025-10-06', isOffDay: true },
    { name: '国庆节',     date: '2025-10-07', isOffDay: true },
    { name: '国庆节',     date: '2025-10-08', isOffDay: true },
    { name: '国庆前补班',  date: '2025-09-28', isOffDay: false },
    { name: '国庆后补班',  date: '2025-10-11', isOffDay: false },
  ],
  2026: [
    { name: '元旦',       date: '2026-01-01', isOffDay: true },
    { name: '元旦',       date: '2026-01-02', isOffDay: true },
    { name: '元旦',       date: '2026-01-03', isOffDay: true },
    { name: '春节',       date: '2026-02-17', isOffDay: true },
    { name: '春节',       date: '2026-02-18', isOffDay: true },
    { name: '春节',       date: '2026-02-19', isOffDay: true },
    { name: '春节',       date: '2026-02-20', isOffDay: true },
    { name: '春节',       date: '2026-02-21', isOffDay: true },
    { name: '春节',       date: '2026-02-22', isOffDay: true },
    { name: '春节',       date: '2026-02-23', isOffDay: true },
    { name: '春节',       date: '2026-02-24', isOffDay: true },
    { name: '春节前补班',  date: '2026-02-15', isOffDay: false },
    { name: '春节后补班',  date: '2026-02-28', isOffDay: false },
    { name: '清明节',     date: '2026-04-04', isOffDay: true },
    { name: '清明节',     date: '2026-04-05', isOffDay: true },
    { name: '清明节',     date: '2026-04-06', isOffDay: true },
    { name: '劳动节',     date: '2026-05-01', isOffDay: true },
    { name: '劳动节',     date: '2026-05-02', isOffDay: true },
    { name: '劳动节',     date: '2026-05-03', isOffDay: true },
    { name: '劳动节',     date: '2026-05-04', isOffDay: true },
    { name: '劳动节',     date: '2026-05-05', isOffDay: true },
    { name: '端午节',     date: '2026-06-19', isOffDay: true },
    { name: '端午节',     date: '2026-06-20', isOffDay: true },
    { name: '端午节',     date: '2026-06-21', isOffDay: true },
    { name: '中秋节',     date: '2026-09-25', isOffDay: true },
    { name: '中秋节',     date: '2026-09-26', isOffDay: true },
    { name: '中秋节',     date: '2026-09-27', isOffDay: true },
    { name: '国庆节',     date: '2026-10-01', isOffDay: true },
    { name: '国庆节',     date: '2026-10-02', isOffDay: true },
    { name: '国庆节',     date: '2026-10-03', isOffDay: true },
    { name: '国庆节',     date: '2026-10-04', isOffDay: true },
    { name: '国庆节',     date: '2026-10-05', isOffDay: true },
    { name: '国庆节',     date: '2026-10-06', isOffDay: true },
    { name: '国庆节',     date: '2026-10-07', isOffDay: true },
    { name: '中秋前补班',  date: '2026-09-27', isOffDay: false },
    { name: '国庆后补班',  date: '2026-10-10', isOffDay: false },
  ],
}

// ──────────────────────────────────────────────────────────────
// localStorage 缓存读写
// ──────────────────────────────────────────────────────────────

function cacheKey(year: number) {
  return `holiday-cn-${year}`
}

function readCache(year: number): HolidayCNDay[] | null {
  try {
    const raw = localStorage.getItem(cacheKey(year))
    if (!raw) return null
    const { data, fetchedAt } = JSON.parse(raw) as { data: HolidayCNDay[]; fetchedAt: number }
    if (Date.now() - fetchedAt > CACHE_TTL_MS) return null
    return data
  } catch {
    return null
  }
}

function writeCache(year: number, data: HolidayCNDay[]) {
  try {
    localStorage.setItem(cacheKey(year), JSON.stringify({ data, fetchedAt: Date.now() }))
  } catch {
    // localStorage 可能已满，忽略
  }
}

// ──────────────────────────────────────────────────────────────
// 远程拉取
// ──────────────────────────────────────────────────────────────

async function fetchYearData(year: number): Promise<HolidayCNDay[]> {
  const cached = readCache(year)
  if (cached) return cached

  try {
    const res = await fetch(CDN_URL(year), { signal: AbortSignal.timeout(5000) })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json: HolidayCNYear = await res.json()
    writeCache(year, json.days)
    return json.days
  } catch {
    // 网络失败 → 使用内置 fallback
    return FALLBACK_HOLIDAYS[year] ?? []
  }
}

// ──────────────────────────────────────────────────────────────
// 颜色
// ──────────────────────────────────────────────────────────────

const TYPE_COLOR: Record<string, string> = {
  publicHoliday: '#ef4444',
  traditional:   '#f59e0b',
}
const TYPE_BG: Record<string, string> = {
  publicHoliday: 'rgba(239,68,68,0.14)',
  traditional:   'rgba(245,158,11,0.12)',
}
const TYPE_TEXT: Record<string, string> = {
  publicHoliday: '#b91c1c',
  traditional:   '#92400e',
}

function toEvent(
  name: string,
  date: string,
  type: 'publicHoliday' | 'traditional',
): HolidayEvent {
  const d = new Date(date)
  const end = new Date(d)
  end.setDate(end.getDate() + 1)
  return {
    id: `holiday-${type}-${date}-${name}`,
    title: name,
    start: date,
    end: end.toISOString().slice(0, 10),
    allDay: true,
    display: 'block',
    editable: false,
    color: 'transparent',
    backgroundColor: 'transparent',
    borderColor: 'transparent',
    textColor: 'transparent',
    classNames: [`holiday-${type}`],
    extendedProps: { isHoliday: true, holidayType: type },
  } as HolidayEvent
}

/**
 * 将 HolidayCNDay 数组按节假日名称把**连续日期**合并为跨天区间。
 *
 * 规则： isOffDay: true（法定假期）同名连续天合并为一条 publicHoliday 事件。
 * 调休补班（isOffDay: false）不显示。
 */
function mergeToDayRanges(days: HolidayCNDay[]): HolidayEvent[] {
  const sorted = [...days].sort((a, b) => a.date.localeCompare(b.date))
  const events: HolidayEvent[] = []

  // ── 法定假期：按名称合并连续区间 ──
  const offDays = sorted.filter(d => d.isOffDay)
  let i = 0
  while (i < offDays.length) {
    const { name, date } = offDays[i]
    let j = i + 1
    // 向后找同名且日期连续的记录
    while (
      j < offDays.length &&
      offDays[j].name === name &&
      dayDiff(offDays[j - 1].date, offDays[j].date) === 1
    ) {
      j++
    }
    // [i, j) 为同一段连续假期
    const lastDate = offDays[j - 1].date
    const end = addOneDay(lastDate) // exclusive end
    events.push({
      id: `holiday-publicHoliday-${date}-${name}`,
      title: name,
      start: date,
      end,
      allDay: true,
      display: 'block',
      editable: false,
      color: 'transparent',
      backgroundColor: 'transparent',
      borderColor: 'transparent',
      textColor: 'transparent',
      classNames: ['holiday-publicHoliday'],
      extendedProps: { isHoliday: true, holidayType: 'publicHoliday' },
    } as HolidayEvent)
    i = j
  }

  return events
}

/** 两个 YYYY-MM-DD 日期相差的天数 */
function dayDiff(a: string, b: string): number {
  return Math.round((new Date(b).getTime() - new Date(a).getTime()) / 86400000)
}

function addOneDay(dateStr: string): string {
  const d = new Date(dateStr)
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
}

// ──────────────────────────────────────────────────────────────
// 公开 API
// ──────────────────────────────────────────────────────────────

/**
 * 异步加载指定年份列表的节假日事件，用于传给 FullCalendar。
 *
 * - 法定节假日：从 holiday-cn CDN 拉取，localStorage 缓存 24h，
 *   失败时降级到内置 fallback；同名连续天合并为跨天区间事件
 * - 调休补班（isOffDay: false）不显示
 * - 传统节日：静态内置，无需网络
 *
 * @param years 需要加载的年份列表，默认为当前年份及后一年
 */
export async function loadHolidayEvents(years?: number[]): Promise<HolidayEvent[]> {
  const now = new Date()
  const targetYears = years ?? [now.getFullYear(), now.getFullYear() + 1]

  // 并发拉取所有年份
  const allDays = (await Promise.all(targetYears.map(fetchYearData))).flat()

  // 去重（同一天同名）
  const seen = new Set<string>()
  const uniqueDays: HolidayCNDay[] = []
  for (const day of allDays) {
    const key = `${day.date}-${day.name}-${day.isOffDay}`
    if (!seen.has(key)) {
      seen.add(key)
      uniqueDays.push(day)
    }
  }

  // 合并连续假期为跨天区间
  const events = mergeToDayRanges(uniqueDays)

  // 追加传统节日
  for (const t of TRADITIONAL_HOLIDAYS) {
    const year = parseInt(t.date.slice(0, 4))
    if (targetYears.includes(year)) {
      events.push(toEvent(t.name, t.date, 'traditional'))
    }
  }

  return events
}

/**
 * 统一的节假日事件渲染器，供所有 FullCalendar 视图的 eventContent 回调使用。
 * 对节假日事件返回显式 DOM 节点（色条 + 名称文字）；对非节假日返回 null（调用方继续走自己的逻辑）。
 */
export function renderHolidayContent(
  arg: { event: { title: string; extendedProps: Record<string, unknown> } },
): { domNodes: Node[] } | null {
  const { isHoliday, holidayType } = arg.event.extendedProps as {
    isHoliday?: boolean
    holidayType?: 'publicHoliday' | 'traditional'
  }
  if (!isHoliday) return null

  const type = holidayType ?? 'publicHoliday'
  const bg     = TYPE_BG[type]
  const border = TYPE_COLOR[type]
  const color  = TYPE_TEXT[type]

  const wrapper = document.createElement('div')
  wrapper.style.cssText = `width:100%;height:100%;display:flex;align-items:center;background:${bg};border-left:3px solid ${border};padding:0 5px;border-radius:3px;box-sizing:border-box;overflow:hidden;cursor:default;`
  const titleEl = document.createElement('span')
  titleEl.style.cssText = `font-size:9px;font-weight:600;color:${color};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;letter-spacing:0.03em;flex:1;min-width:0;`
  titleEl.textContent = arg.event.title
  wrapper.appendChild(titleEl)
  return { domNodes: [wrapper] }
}

/**
 * 强制清除指定年份（或全部）的本地缓存，下次调用 loadHolidayEvents 时重新从 CDN 拉取。
 */
export function clearHolidayCache(year?: number) {
  if (year !== undefined) {
    localStorage.removeItem(cacheKey(year))
  } else {
    const keys = Object.keys(localStorage).filter(k => k.startsWith('holiday-cn-'))
    keys.forEach(k => localStorage.removeItem(k))
  }
}
