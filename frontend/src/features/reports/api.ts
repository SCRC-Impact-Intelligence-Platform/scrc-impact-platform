import { apiRequest, BASE } from '../../app/api'
import type { ResourceType } from '../directory/api'
import type { Publication, ResourceAttribution } from '../publications/api'

export type ReportResourceAttribution = ResourceAttribution & { resource_type: ResourceType }

export type AttributedPublication = {
  publication: Publication
  resources: ReportResourceAttribution[]
}

export type AttributionSummary = {
  /** Publications in the quarter attributed to at least one resource. */
  attributed_in_period: number
  /** ...of which at least one attributed resource is a grant (FUNDING). */
  grant_attributed_in_period: number
  /** All verified attributed publications, whatever their date. */
  attributed_total: number
  grant_attributed_total: number
}

export type QuarterlyReport = {
  year: number
  quarter: number
  /** The resource filter, when one was applied. */
  resource_id: number | null
  resource_name: string | null
  publications: Publication[]
  /** Verified publications from the year whose date has no month; not in any quarter. */
  undated_publications: Publication[]
  /** Verified publications with no readable year; not in any report period. */
  no_date_publications: Publication[]
  /** The quarter's publications that have resource attributions, in the same order. */
  attributed_publications: AttributedPublication[]
  attribution_summary: AttributionSummary
}

export type ReportingPeriod = { year: number; quarter: number }

const QUARTER_MONTHS = ['Jan – Mar', 'Apr – Jun', 'Jul – Sep', 'Oct – Dec']

export const periodLabel = ({ year, quarter }: ReportingPeriod) =>
  `Q${quarter} ${year} (${QUARTER_MONTHS[quarter - 1]})`

/** The current calendar quarter followed by the `count - 1` quarters before it. */
export function recentPeriods(count: number, today = new Date()): ReportingPeriod[] {
  let year = today.getFullYear()
  let quarter = Math.floor(today.getMonth() / 3) + 1
  const periods: ReportingPeriod[] = []
  for (let i = 0; i < count; i++) {
    periods.push({ year, quarter })
    if (--quarter === 0) {
      quarter = 4
      year--
    }
  }
  return periods
}

export type ReportType = 'LEADERSHIP' | 'NIH' | 'CIRM' | 'ADVANCEMENT'

export const REPORT_TYPES: { value: ReportType; label: string }[] = [
  { value: 'LEADERSHIP', label: 'Leadership' },
  { value: 'NIH', label: 'NIH' },
  { value: 'CIRM', label: 'CIRM' },
  { value: 'ADVANCEMENT', label: 'Advancement' },
]

/** Everything chosen in the Report Builder form. */
export type ReportParams = {
  reportType: ReportType
  period: ReportingPeriod
  resourceId: number | null
}

const reportQuery = ({ period, resourceId }: ReportParams) => {
  const query = new URLSearchParams({ year: String(period.year), quarter: String(period.quarter) })
  if (resourceId !== null) query.set('resource_id', String(resourceId))
  return query
}

/** Same-origin link to the report's Excel or PDF download. */
export const reportExportUrl = (params: ReportParams, format: 'xlsx' | 'pdf') => {
  const query = reportQuery(params)
  query.set('format', format)
  query.set('report_type', params.reportType)
  return `${BASE}/reports/quarterly/export?${query}`
}

export const reportsApi = {
  quarterly: (params: ReportParams) =>
    apiRequest<QuarterlyReport>(`/reports/quarterly?${reportQuery(params)}`),
}
