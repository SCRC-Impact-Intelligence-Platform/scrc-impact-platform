import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ExternalLink, FileText } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import type { Criticality } from '../features/attributions/api'
import {
  Feedback,
  inputClass,
  primaryButton,
  secondaryButton,
} from '../features/directory/DirectoryUI'
import { researcherName, researchersApi, resourcesApi } from '../features/directory/api'
import { pubmedUrl, type Publication } from '../features/publications/api'
import {
  type AttributedPublication,
  MONTH_NAMES,
  PERIOD_TYPES,
  type PeriodType,
  recentPeriods,
  type Report,
  REPORT_TYPES,
  reportExportUrl,
  reportsApi,
  type ReportParams,
  type ReportType,
  hasAttributed,
  hasVerified,
  type ReportingPeriod,
  type YearMonth,
  yearMonth,
} from '../features/reports/api'

const plural = (n: number, noun: string) => `${n} ${noun}${n === 1 ? '' : 's'}`
const keyOf = ({ start, end }: ReportingPeriod) => `${start}_${end}`

/** Month and year selects; works in every browser, unlike <input type="month">. */
function MonthPicker({
  label,
  value,
  onChange,
  years,
}: {
  label: string
  value: YearMonth
  onChange: (value: YearMonth) => void
  years: number[]
}) {
  const [year, month] = value.split('-').map(Number)
  return (
    <fieldset className="min-w-44 flex-1 space-y-1">
      <legend className="text-xs font-medium text-slate-500">{label}</legend>
      <div className="flex gap-2">
        <select
          aria-label={`${label} month`}
          className={selectClass}
          value={month}
          onChange={(e) => onChange(yearMonth(year, Number(e.target.value)))}
        >
          {MONTH_NAMES.map((name, i) => (
            <option key={name} value={i + 1}>
              {name}
            </option>
          ))}
        </select>
        <select
          aria-label={`${label} year`}
          className={selectClass}
          value={year}
          onChange={(e) => onChange(yearMonth(Number(e.target.value), month))}
        >
          {years.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
      </div>
    </fieldset>
  )
}

/** Verified publications that a report had to leave out, so its totals can be checked. */
function ExcludedNote({ publications, reason }: { publications: Publication[]; reason: string }) {
  if (publications.length === 0) return null
  return (
    <details className="border-b border-amber-200 bg-amber-50 px-5 py-3 text-sm text-amber-900">
      <summary className="cursor-pointer">
        {publications.length} verified publication{publications.length === 1 ? '' : 's'} {reason}
      </summary>
      <ul className="mt-2 list-disc space-y-1 pl-5">
        {publications.map((p) => (
          <li key={p.id}>
            {p.title} ({p.publication_date ?? 'no date'}, PMID {p.pmid})
          </li>
        ))}
      </ul>
    </details>
  )
}

function SummaryStats({ report, showVerified }: { report: Report; showVerified: boolean }) {
  const s = report.attribution_summary
  const stats: [string, number][] = [
    ['Attributed this period', s.attributed_in_period],
    ['Attributed to grants this period', s.grant_attributed_in_period],
    ['Attributed, all time', s.attributed_total],
    ['Attributed to grants, all time', s.grant_attributed_total],
  ]
  if (showVerified) stats.unshift(['Verified this period', report.publications.length])
  return (
    <dl
      className={`grid grid-cols-2 gap-px border-b border-slate-200 bg-slate-200 sm:grid-cols-3 ${
        showVerified ? 'lg:grid-cols-5' : 'lg:grid-cols-4'
      }`}
    >
      {stats.map(([label, value]) => (
        <div key={label} className="bg-white px-5 py-3">
          <dt className="text-xs text-slate-500">{label}</dt>
          <dd className="text-xl font-bold text-slate-900">{value}</dd>
        </div>
      ))}
    </dl>
  )
}

const criticalityLabel = (c: Criticality) => c.charAt(0) + c.slice(1).toLowerCase()

function AttributedList({ items }: { items: AttributedPublication[] }) {
  return (
    <div className="border-b border-slate-200">
      <h3 className="px-5 pt-4 text-sm font-semibold text-slate-900">
        Attributed publications ({items.length})
      </h3>
      {items.length === 0 ? (
        <p className="px-5 py-3 text-sm text-slate-500">
          No attributed publications in this period.
        </p>
      ) : (
        <ul className="divide-y divide-slate-100">
          {items.map(({ publication: p, resources }) => (
            <li key={p.id} className="px-5 py-3 text-sm">
              <p className="font-medium text-slate-900">{p.title}</p>
              <p className="mt-1 flex flex-wrap gap-1.5">
                {resources.map((r) => (
                  <span
                    key={r.resource_id}
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      r.resource_type === 'FUNDING'
                        ? 'bg-emerald-50 text-emerald-800'
                        : 'bg-slate-100 text-slate-700'
                    }`}
                  >
                    {r.resource_name} · {criticalityLabel(r.criticality)}
                  </span>
                ))}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function VerifiedList({
  report,
  nameFor,
}: {
  report: Report
  nameFor: (id: number | null) => string
}) {
  return (
    <>
      <h3 className="px-5 pt-4 text-sm font-semibold text-slate-900">All verified publications</h3>
      <ExcludedNote
        publications={report.undated_publications}
        reason="dated only by a year this period covers in part couldn't be placed in it."
      />
      <ExcludedNote
        publications={report.no_date_publications}
        reason="with no readable publication date can't be placed in any report period."
      />
      {report.publications.length === 0 ? (
        <div className="space-y-2 p-8 text-center">
          <FileText className="mx-auto text-slate-400" />
          <p className="font-medium text-slate-800">No verified publications in this period</p>
        </div>
      ) : (
        <ol className="divide-y divide-slate-100">
          {report.publications.map((p, index) => (
            <li key={p.id} className="flex gap-4 px-5 py-4 text-sm">
              <span className="w-6 shrink-0 text-right text-slate-400">{index + 1}.</span>
              <div className="min-w-0">
                <p className="font-semibold text-slate-900">{p.title}</p>
                <p className="mt-1 text-slate-600">{p.authors.join(', ')}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {p.journal || 'Unknown journal'} · {p.publication_date} ·{' '}
                  {nameFor(p.first_discovered_researcher_id)} ·{' '}
                  <a
                    className="text-blue-700 underline underline-offset-2"
                    href={pubmedUrl(p.pmid)}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    PMID {p.pmid} <ExternalLink size={11} className="inline" />
                  </a>
                </p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </>
  )
}

const fieldLabel = 'block space-y-1.5 text-sm font-semibold text-slate-800'
const selectClass = `${inputClass} font-normal`
const exportButton =
  'inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-blue-800 hover:bg-blue-50'

export default function ReportsPage() {
  const today = new Date()
  const [reportType, setReportType] = useState<ReportType>('BOTH')
  const [periodType, setPeriodType] = useState<PeriodType>('QUARTER')
  // Recomputed each render so a tab left open across a quarter or year boundary picks up the new one.
  const options =
    periodType === 'CUSTOM' ? [] : recentPeriods(periodType, periodType === 'QUARTER' ? 8 : 6)
  const [chosenKey, setChosenKey] = useState<string | null>(null)
  // Newest option unless another one is chosen (and still listed).
  const chosen = options.find((o) => keyOf(o) === chosenKey) ?? options[0]
  const [customStart, setCustomStart] = useState(yearMonth(today.getFullYear(), 1))
  const [customEnd, setCustomEnd] = useState(yearMonth(today.getFullYear(), today.getMonth() + 1))
  const customYears = Array.from({ length: 10 }, (_, i) => today.getFullYear() - i)
  // "YYYY-MM" strings compare in date order.
  const customValid = customStart <= customEnd
  const period: ReportingPeriod | null =
    periodType === 'CUSTOM'
      ? customValid
        ? { start: customStart, end: customEnd }
        : null
      : { start: chosen.start, end: chosen.end }
  const [resourceId, setResourceId] = useState<number | null>(null)
  const params: ReportParams | null = period && { reportType, period, resourceId }

  // The report only runs when "Generate Report" is pressed, not on every select change.
  const [generated, setGenerated] = useState<ReportParams | null>(null)
  const report = useQuery({
    queryKey: ['reports', generated?.period.start, generated?.period.end, generated?.resourceId],
    queryFn: () => reportsApi.get(generated!),
    enabled: generated !== null,
  })
  const researchers = useQuery({ queryKey: ['researchers'], queryFn: researchersApi.list })
  const resources = useQuery({ queryKey: ['resources'], queryFn: resourcesApi.list })
  const nameFor = (id: number | null) => researcherName(researchers.data, id)
  const sortedResources = [...(resources.data ?? [])].sort((a, b) => a.name.localeCompare(b.name))
  const typeTitle = (type: ReportType) => REPORT_TYPES.find((t) => t.value === type)!.title

  return (
    <section className="space-y-6">
      <PageHeader
        title="Report Builder"
        description="Generate reports for leadership, NIH, CIRM, or advancement."
      />
      <form
        className="panel max-w-md space-y-4 p-6"
        onSubmit={(event) => {
          event.preventDefault()
          if (!params) return
          const same =
            generated &&
            keyOf(generated.period) === keyOf(params.period) &&
            generated.resourceId === params.resourceId
          // Same filters again: refetch so newly verified publications show up.
          if (same) void report.refetch()
          setGenerated(params)
        }}
      >
        <h2 className="text-xl font-bold text-[#102c49]">Report Builder</h2>
        <label className={fieldLabel}>
          <span className="block">Report Type</span>
          <select
            className={selectClass}
            value={reportType}
            onChange={(e) => setReportType(e.target.value as ReportType)}
          >
            {REPORT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
        <label className={fieldLabel}>
          <span className="block">Period Type</span>
          <select
            className={selectClass}
            value={periodType}
            onChange={(e) => {
              setPeriodType(e.target.value as PeriodType)
              setChosenKey(null)
            }}
          >
            {PERIOD_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
        {periodType === 'CUSTOM' ? (
          <div className="space-y-1.5">
            <span className="block text-sm font-semibold text-slate-800">Reporting Period</span>
            <div className="flex flex-wrap gap-3">
              <MonthPicker
                label="From"
                value={customStart}
                onChange={setCustomStart}
                years={customYears}
              />
              <MonthPicker
                label="To"
                value={customEnd}
                onChange={setCustomEnd}
                years={customYears}
              />
            </div>
            {!customValid && (
              <p role="alert" className="text-sm text-red-700">
                The end month must be the same as or after the start month.
              </p>
            )}
          </div>
        ) : (
          <label className={fieldLabel}>
            <span className="block">Reporting Period</span>
            <select
              className={selectClass}
              value={keyOf(chosen)}
              onChange={(e) => setChosenKey(e.target.value)}
            >
              {options.map((o) => (
                <option key={keyOf(o)} value={keyOf(o)}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
        )}
        <label className={fieldLabel}>
          <span className="block">Department</span>
          {/* Researchers have no department yet, so there is nothing to filter by. */}
          <select className={selectClass} defaultValue="">
            <option value="">All Departments</option>
          </select>
        </label>
        <label className={fieldLabel}>
          <span className="block">Resource</span>
          <select
            className={selectClass}
            value={resourceId ?? ''}
            onChange={(e) => setResourceId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">All Resources</option>
            {sortedResources.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
                {r.is_active ? '' : ' (inactive)'}
              </option>
            ))}
          </select>
        </label>
        <div className="flex flex-wrap gap-2 pt-1">
          <button type="submit" className={primaryButton} disabled={!params || report.isFetching}>
            Generate Report
          </button>
          {(['pdf', 'xlsx'] as const).map((format) => {
            const text = format === 'pdf' ? 'Export PDF' : 'Export Excel'
            return params ? (
              <a
                key={format}
                className={exportButton}
                href={reportExportUrl(params, format)}
                download
              >
                {text}
              </a>
            ) : (
              <span
                key={format}
                aria-disabled="true"
                className={`${exportButton} cursor-not-allowed opacity-50`}
              >
                {text}
              </span>
            )
          })}
        </div>
        <p className="border-t border-slate-200 pt-4 text-sm leading-relaxed text-slate-600">
          Report Type picks the attributed publications, all verified publications, or both. Every
          report can be filtered by period, department, or resource.
        </p>
      </form>

      {generated && (
        <div className="panel overflow-hidden">
          <div className="border-b border-slate-200 p-5">
            <h2 className="text-lg font-bold text-slate-900">
              {typeTitle(generated.reportType)}
              {report.data && <> · {report.data.period_label}</>}
            </h2>
            {report.data && (
              <p className="muted mt-1 text-sm">
                {report.data.resource_name && <>Resource: {report.data.resource_name} · </>}
                {hasVerified(generated.reportType)
                  ? plural(report.data.publications.length, 'verified publication')
                  : plural(report.data.attributed_publications.length, 'attributed publication')}
              </p>
            )}
          </div>
          {report.isPending ? (
            <p className="p-6 text-sm text-slate-500">Generating report…</p>
          ) : report.isError ? (
            <div className="space-y-3 p-6">
              <Feedback message={report.error.message} />
              <button className={secondaryButton} onClick={() => void report.refetch()}>
                Retry
              </button>
            </div>
          ) : (
            <>
              {hasAttributed(generated.reportType) && (
                <>
                  <SummaryStats
                    report={report.data}
                    showVerified={generated.reportType === 'BOTH'}
                  />
                  <AttributedList items={report.data.attributed_publications} />
                </>
              )}
              {hasVerified(generated.reportType) && (
                <VerifiedList report={report.data} nameFor={nameFor} />
              )}
            </>
          )}
        </div>
      )}
    </section>
  )
}
