import { apiRequest, BASE } from '../../app/api'
import type { ResourceType } from '../directory/api'
import type { Publication, ResourceAttribution } from '../publications/api'

export type ReportResourceAttribution = ResourceAttribution & { resource_type: ResourceType }

export type AttributedPublication = {
  publication: Publication
  resources: ReportResourceAttribution[]
}

export type AttributionSummary = {
  /** Publications in the period attributed to at least one resource. */
  attributed_in_period: number
  /** ...of which at least one attributed resource is a grant (FUNDING). */
  grant_attributed_in_period: number
  /** All verified attributed publications, whatever their date. */
  attributed_total: number
  grant_attributed_total: number
}

export type Report = {
  /** The period, as inclusive "YYYY-MM" months. */
  start: YearMonth
  end: YearMonth
  /** e.g. "Q1 2026 (Jan – Mar)", "FY 2025–26 (Jul 2025 – Jun 2026)". */
  period_label: string
  /** The resource filter, when one was applied. */
  resource_id: number | null
  resource_name: string | null
  publications: Publication[]
  /** Verified publications dated only by a year the period covers in part; can't be placed. */
  undated_publications: Publication[]
  /** Verified publications with no readable year; not in any report period. */
  no_date_publications: Publication[]
  /** The period's publications that have resource attributions, in the same order. */
  attributed_publications: AttributedPublication[]
  attribution_summary: AttributionSummary
}

/** A calendar month, "YYYY-MM". */
export type YearMonth = string

/** An inclusive range of months. */
export type ReportingPeriod = { start: YearMonth; end: YearMonth }

export type PeriodType = 'QUARTER' | 'CALENDAR_YEAR' | 'FISCAL_YEAR' | 'CUSTOM'

export const PERIOD_TYPES: { value: PeriodType; label: string }[] = [
  { value: 'QUARTER', label: 'Quarter' },
  { value: 'CALENDAR_YEAR', label: 'Calendar year' },
  { value: 'FISCAL_YEAR', label: 'Fiscal year (Jul – Jun)' },
  { value: 'CUSTOM', label: 'Custom range' },
]

export type PeriodOption = ReportingPeriod & { label: string }

export const MONTH_NAMES = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ')

export const yearMonth = (year: number, month: number): YearMonth =>
  `${year}-${String(month).padStart(2, '0')}`

/** The current quarter, calendar year or fiscal year (Jul – Jun), then the `count - 1` before it. */
export function recentPeriods(
  type: Exclude<PeriodType, 'CUSTOM'>,
  count: number,
  today = new Date(),
): PeriodOption[] {
  const length = type === 'QUARTER' ? 3 : 12
  // Months are counted from year 0, so a period's first month is a remainder away from now.
  const now = today.getFullYear() * 12 + today.getMonth()
  const current = now - ((now - (type === 'FISCAL_YEAR' ? 6 : 0)) % length)
  return Array.from({ length: count }, (_, i) => {
    const first = current - i * length
    const last = first + length - 1
    const [sy, sm, ey, em] = [Math.floor(first / 12), first % 12, Math.floor(last / 12), last % 12]
    const label =
      type === 'QUARTER'
        ? `Q${sm / 3 + 1} ${sy} (${MONTH_NAMES[sm]} – ${MONTH_NAMES[em]})`
        : type === 'CALENDAR_YEAR'
          ? `${sy} (Jan – Dec)`
          : `FY ${sy}–${String(ey % 100).padStart(2, '0')} (Jul ${sy} – Jun ${ey})`
    return { start: yearMonth(sy, sm + 1), end: yearMonth(ey, em + 1), label }
  })
}

/** Which publication lists the report shows and exports. */
export type ReportType = 'ATTRIBUTED' | 'VERIFIED' | 'BOTH'

export const REPORT_TYPES: { value: ReportType; label: string; title: string }[] = [
  { value: 'BOTH', label: 'Attributed and all verified', title: 'Publications report' },
  {
    value: 'ATTRIBUTED',
    label: 'Attributed publications',
    title: 'Attributed publications report',
  },
  { value: 'VERIFIED', label: 'All verified publications', title: 'Verified publications report' },
]

export const hasAttributed = (type: ReportType) => type !== 'VERIFIED'
export const hasVerified = (type: ReportType) => type !== 'ATTRIBUTED'

/** Everything chosen in the Report Builder form. */
export type ReportParams = {
  reportType: ReportType
  period: ReportingPeriod
  resourceId: number | null
}

const reportQuery = ({ period, resourceId }: ReportParams) => {
  const query = new URLSearchParams({ start: period.start, end: period.end })
  if (resourceId !== null) query.set('resource_id', String(resourceId))
  return query
}

/** Same-origin link to the report's Excel or PDF download. */
export const reportExportUrl = (params: ReportParams, format: 'xlsx' | 'pdf') => {
  const query = reportQuery(params)
  query.set('format', format)
  query.set('report_type', params.reportType)
  return `${BASE}/reports/export?${query}`
}

export const reportsApi = {
  get: (params: ReportParams) => apiRequest<Report>(`/reports?${reportQuery(params)}`),
}
