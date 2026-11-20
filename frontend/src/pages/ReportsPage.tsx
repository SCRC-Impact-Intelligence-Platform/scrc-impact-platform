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
  type QuarterlyReport,
  periodLabel,
  recentPeriods,
  REPORT_TYPES,
  reportExportUrl,
  reportsApi,
  type ReportGrant,
  type ReportParams,
  type ReportType,
  type ReportingPeriod,
} from '../features/reports/api'

const PERIOD_COUNT = 8
const keyOf = ({ year, quarter }: ReportingPeriod) => `${year}-Q${quarter}`

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

function SummaryStats({ report }: { report: QuarterlyReport }) {
  const s = report.attribution_summary
  const stats = [
    ['Verified this quarter', report.publications.length],
    ['Attributed this quarter', s.attributed_in_period],
    ['Attributed to grants this quarter', s.grant_attributed_in_period],
    ['Attributed, all time', s.attributed_total],
    ['Attributed to grants, all time', s.grant_attributed_total],
  ] as const
  return (
    <dl className="grid grid-cols-2 gap-px border-b border-slate-200 bg-slate-200 sm:grid-cols-3 lg:grid-cols-5">
      {stats.map(([label, value]) => (
        <div key={label} className="bg-white px-5 py-3">
          <dt className="text-xs text-slate-500">{label}</dt>
          <dd className="text-xl font-bold text-slate-900">{value}</dd>
        </div>
      ))}
    </dl>
  )
}

const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
// Parsed as a local date: new Date('2026-10-01') would be UTC midnight, the day before in California.
const awardDate = (iso: string) => {
  const [year, month, day] = iso.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString('en-US', { dateStyle: 'medium' })
}

function GrantsReceived({ grants }: { grants: ReportGrant[] }) {
  if (grants.length === 0) return null
  return (
    <div className="border-b border-slate-200">
      <h3 className="px-5 pt-4 text-sm font-semibold text-slate-900">
        Grants received ({grants.length})
      </h3>
      <ul className="divide-y divide-slate-100">
        {grants.map((g) => (
          <li key={g.id} className="px-5 py-3 text-sm">
            <p className="font-medium text-slate-900">{g.title}</p>
            <p className="mt-1 text-xs text-slate-500">
              {[
                g.funder,
                g.amount !== null && usd.format(Number(g.amount)),
                `Awarded ${awardDate(g.award_date)}`,
                g.researcher_name,
              ]
                .filter(Boolean)
                .join(' · ')}
            </p>
          </li>
        ))}
      </ul>
    </div>
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

const fieldLabel = 'block space-y-1.5 text-sm font-semibold text-slate-800'
const selectClass = `${inputClass} font-normal`
const exportButton =
  'inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-blue-800 hover:bg-blue-50'

export default function ReportsPage() {
  // Recomputed each render so a tab left open across a quarter boundary picks up the new quarter.
  const periods = recentPeriods(PERIOD_COUNT)
  const [chosenPeriod, setChosenPeriod] = useState(keyOf(periods[0]))
  // If the chosen period rolled off the list, fall back to the newest one.
  const periodKey = periods.some((p) => keyOf(p) === chosenPeriod)
    ? chosenPeriod
    : keyOf(periods[0])
  const [reportType, setReportType] = useState<ReportType>('LEADERSHIP')
  const [resourceId, setResourceId] = useState<number | null>(null)
  const params: ReportParams = {
    reportType,
    period: periods.find((p) => keyOf(p) === periodKey)!,
    resourceId,
  }

  // The report only runs when "Generate Report" is pressed, not on every select change.
  const [generated, setGenerated] = useState<ReportParams | null>(null)
  const report = useQuery({
    queryKey: ['reports', 'quarterly', generated?.period, generated?.resourceId],
    queryFn: () => reportsApi.quarterly(generated!),
    enabled: generated !== null,
  })
  const researchers = useQuery({ queryKey: ['researchers'], queryFn: researchersApi.list })
  const resources = useQuery({ queryKey: ['resources'], queryFn: resourcesApi.list })
  const nameFor = (id: number | null) => researcherName(researchers.data, id)
  const sortedResources = [...(resources.data ?? [])].sort((a, b) => a.name.localeCompare(b.name))
  const typeLabel = (type: ReportType) => REPORT_TYPES.find((t) => t.value === type)!.label

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
          const same =
            generated &&
            keyOf(generated.period) === periodKey &&
            generated.resourceId === resourceId
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
          <span className="block">Reporting Period</span>
          <select
            className={selectClass}
            value={periodKey}
            onChange={(e) => setChosenPeriod(e.target.value)}
          >
            {periods.map((p) => (
              <option key={keyOf(p)} value={keyOf(p)}>
                {periodLabel(p)}
              </option>
            ))}
          </select>
        </label>
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
          <button type="submit" className={primaryButton} disabled={report.isFetching}>
            Generate Report
          </button>
          <a className={exportButton} href={reportExportUrl(params, 'pdf')} download>
            Export PDF
          </a>
          <a className={exportButton} href={reportExportUrl(params, 'xlsx')} download>
            Export Excel
          </a>
        </div>
        <p className="border-t border-slate-200 pt-4 text-sm leading-relaxed text-slate-600">
          Verified publications are included in all report exports and can be filtered by period,
          department, or resource.
        </p>
      </form>

      {generated && (
        <div className="panel overflow-hidden">
          <div className="border-b border-slate-200 p-5">
            <h2 className="text-lg font-bold text-slate-900">
              {typeLabel(generated.reportType)} report · {periodLabel(generated.period)}
            </h2>
            {report.data && (
              <p className="muted mt-1 text-sm">
                {report.data.resource_name && <>Resource: {report.data.resource_name} · </>}
                {report.data.publications.length} verified publication
                {report.data.publications.length === 1 ? '' : 's'}
              </p>
            )}
          </div>
          {report.data && (
            <>
              <SummaryStats report={report.data} />
              <GrantsReceived grants={report.data.grants_received} />
              <AttributedList items={report.data.attributed_publications} />
              <h3 className="px-5 pt-4 text-sm font-semibold text-slate-900">
                All verified publications
              </h3>
              <ExcludedNote
                publications={report.data.undated_publications}
                reason={`from ${report.data.year} with no month in the PubMed date couldn't be placed in a quarter.`}
              />
              <ExcludedNote
                publications={report.data.no_date_publications}
                reason="with no readable publication date can't be placed in any report period."
              />
            </>
          )}
          {report.isPending ? (
            <p className="p-6 text-sm text-slate-500">Generating report…</p>
          ) : report.isError ? (
            <div className="space-y-3 p-6">
              <Feedback message={report.error.message} />
              <button className={secondaryButton} onClick={() => void report.refetch()}>
                Retry
              </button>
            </div>
          ) : report.data.publications.length === 0 ? (
            <div className="space-y-2 p-8 text-center">
              <FileText className="mx-auto text-slate-400" />
              <p className="font-medium text-slate-800">No verified publications in this period</p>
            </div>
          ) : (
            <ol className="divide-y divide-slate-100">
              {report.data.publications.map((p, index) => (
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
        </div>
      )}
    </section>
  )
}
