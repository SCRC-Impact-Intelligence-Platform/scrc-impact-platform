"""Excel and PDF versions of a report."""

from html import escape
from io import BytesIO

import xlsxwriter

from app.enums import ReportType
from app.models.publication import Publication
from app.services.citations import format_citations
from app.services.report_data import is_grant

_COLUMNS = (("#", 5), ("Title", 60), ("Authors", 40), ("Journal", 30), ("Date", 14),
            ("Researcher", 24), ("PMID", 12), ("DOI", 28), ("Citation", 80))


_EXCLUDED_COLUMNS = (("Reason", 45), ("Title", 60), ("Date", 18), ("PMID", 12))

_ATTRIBUTED_COLUMNS = (("#", 5), ("Title", 60), ("Date", 14), ("PMID", 12),
                       ("Resources", 45), ("Grants", 35), ("Citation", 80))


def _write_header(sheet, columns, bold, wrap) -> None:
    for column, (heading, width) in enumerate(columns):
        sheet.write_string(0, column, heading, bold)
        sheet.set_column(column, column, width, wrap)


def _excluded(report: dict) -> list[tuple[str, list[Publication]]]:
    return [
        ("Dated only by a year this period covers in part", report["undated_publications"]),
        ("No readable publication date", report["no_date_publications"]),
    ]


def summary_rows(report: dict) -> list[tuple[str, int]]:
    s = report["attribution_summary"]
    return [
        ("Verified publications this period", len(report["publications"])),
        ("Attributed publications this period", s["attributed_in_period"]),
        ("Attributed to grants this period", s["grant_attributed_in_period"]),
        ("Attributed publications, all time", s["attributed_total"]),
        ("Attributed to grants, all time", s["grant_attributed_total"]),
    ]


def resource_label(resource: dict) -> str:
    return f"{resource['resource_name']} ({resource['criticality'].title()})"


def build_xlsx(report: dict, researcher_names: dict[int, str]) -> bytes:
    citations = format_citations(report["publications"])
    output = BytesIO()
    with xlsxwriter.Workbook(output, {"in_memory": True}) as workbook:
        bold, wrap = workbook.add_format({"bold": True}), workbook.add_format({"text_wrap": True, "valign": "top"})
        sheet = workbook.add_worksheet("Publications")
        sheet.freeze_panes(1, 0)
        _write_header(sheet, _COLUMNS, bold, wrap)
        for row, p in enumerate(report["publications"], start=1):
            sheet.write_number(row, 0, row)
            values = (p.title, ", ".join(p.authors), p.journal or "", p.publication_date or "",
                      researcher_names.get(p.first_discovered_researcher_id, ""), p.pmid, p.doi or "",
                      citations[p.pmid])
            for column, value in enumerate(values, start=1):
                # write_string, so a title starting with "=" can't become a formula.
                sheet.write_string(row, column, value)
        attributed = workbook.add_worksheet("Attributed publications")
        attributed.freeze_panes(1, 0)
        _write_header(attributed, _ATTRIBUTED_COLUMNS, bold, wrap)
        for row, item in enumerate(report["attributed_publications"], start=1):
            p, resources = item["publication"], item["resources"]
            attributed.write_number(row, 0, row)
            values = (p.title, p.publication_date or "", p.pmid,
                      "; ".join(map(resource_label, resources)),
                      "; ".join(r["resource_name"] for r in resources if is_grant(r)), citations[p.pmid])
            for column, value in enumerate(values, start=1):
                attributed.write_string(row, column, value)
        excluded = workbook.add_worksheet("Not in period")
        _write_header(excluded, _EXCLUDED_COLUMNS, bold, wrap)
        row = 1
        for reason, publications in _excluded(report):
            for p in publications:
                for column, value in enumerate((reason, p.title, p.publication_date or "", p.pmid)):
                    excluded.write_string(row, column, value)
                row += 1
    return output.getvalue()


REPORT_TITLES = {
    ReportType.ATTRIBUTED: "Attributed publications report",
    ReportType.VERIFIED: "Verified publications report",
    ReportType.BOTH: "Publications report",
}


def build_pdf(report: dict, report_type: ReportType = ReportType.BOTH) -> bytes:
    # Imported here because WeasyPrint needs the Pango system libraries at import time.
    from weasyprint import HTML

    label = escape(report["period_label"])
    if report["resource_name"]:
        label += f" &middot; Resource: {escape(report['resource_name'])}"
    title = escape(REPORT_TITLES[report_type])
    citations = format_citations(report["publications"])
    items = "".join(f"<li>{escape(citations[p.pmid])}</li>" for p in report["publications"])
    notes = "".join(
        f"<p class='note'>{len(publications)} verified publication(s) not included: {escape(reason)}.</p>"
        for reason, publications in _excluded(report) if publications
    )
    count = len(report["publications"])
    # Attribution counts, plus the verified count when both lists are in the report.
    rows = summary_rows(report)[(0 if report_type == ReportType.BOTH else 1):]
    summary = "".join(f"<tr><td>{escape(label)}</td><td class='n'>{value}</td></tr>"
                      for label, value in rows)
    attributed_items = "".join(
        f"<li>{escape(citations[item['publication'].pmid])}"
        f"<div class='res'>Resources: {escape('; '.join(map(resource_label, item['resources'])))}</div></li>"
        for item in report["attributed_publications"]
    )
    attributed = (f"<ol>{attributed_items}</ol>" if attributed_items
                  else "<p class='note'>No attributed publications in this period.</p>")
    sections = ""
    if report_type != ReportType.VERIFIED:
        sections += f"<h2>Summary</h2><table>{summary}</table><h2>Attributed publications</h2>{attributed}"
    if report_type != ReportType.ATTRIBUTED:
        sections += f"<h2>Verified publications</h2><p class='sub'>{count} publication(s)</p>{notes}<ol>{items}</ol>"
    html = f"""<!doctype html><meta charset="utf-8"><style>
      @page {{ size: letter; margin: 0.75in; }}
      body {{ font-family: sans-serif; font-size: 10.5pt; line-height: 1.4; }}
      h1 {{ font-size: 16pt; margin: 0 0 2pt; color: #0b4f9c; }}
      .sub {{ color: #555; margin: 0 0 14pt; }}
      li {{ margin-bottom: 7pt; }}
      .note {{ color: #8a5a00; font-size: 9.5pt; }}
      h2 {{ font-size: 12.5pt; margin: 16pt 0 6pt; color: #0b4f9c; }}
      table {{ border-collapse: collapse; margin-bottom: 6pt; }}
      td {{ padding: 2pt 14pt 2pt 0; }} td.n {{ text-align: right; font-weight: bold; }}
      .res {{ color: #444; font-size: 9.5pt; margin-top: 2pt; }}
    </style>
    <h1>{title}</h1><p class="sub">{label}</p>
    {sections}"""
    return HTML(string=html).write_pdf()
