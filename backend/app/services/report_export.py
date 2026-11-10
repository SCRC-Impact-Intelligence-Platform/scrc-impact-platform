"""Excel and PDF versions of the quarterly report."""

from html import escape
from io import BytesIO

import xlsxwriter

from app.models.publication import Publication
from app.services.citations import format_citations

_COLUMNS = (("#", 5), ("Title", 60), ("Authors", 40), ("Journal", 30), ("Date", 14),
            ("Researcher", 24), ("PMID", 12), ("DOI", 28), ("Citation", 80))


def period_label(year: int, quarter: int) -> str:
    months = ("Jan - Mar", "Apr - Jun", "Jul - Sep", "Oct - Dec")[quarter - 1]
    return f"Q{quarter} {year} ({months})"


def _excluded(report: dict) -> list[tuple[str, list[Publication]]]:
    return [
        (f"From {report['year']} with no month in the PubMed date", report["undated_publications"]),
        ("No readable publication date", report["no_date_publications"]),
    ]


def build_xlsx(report: dict, researcher_names: dict[int, str]) -> bytes:
    citations = format_citations(report["publications"])
    output = BytesIO()
    with xlsxwriter.Workbook(output, {"in_memory": True}) as workbook:
        bold, wrap = workbook.add_format({"bold": True}), workbook.add_format({"text_wrap": True, "valign": "top"})
        sheet = workbook.add_worksheet("Publications")
        sheet.freeze_panes(1, 0)
        for column, (heading, width) in enumerate(_COLUMNS):
            sheet.write_string(0, column, heading, bold)
            sheet.set_column(column, column, width, wrap)
        for row, p in enumerate(report["publications"], start=1):
            sheet.write_number(row, 0, row)
            values = (p.title, ", ".join(p.authors), p.journal or "", p.publication_date or "",
                      researcher_names.get(p.first_discovered_researcher_id, ""), p.pmid, p.doi or "",
                      citations[p.pmid])
            for column, value in enumerate(values, start=1):
                # write_string, so a title starting with "=" can't become a formula.
                sheet.write_string(row, column, value)
        excluded = workbook.add_worksheet("Not in a quarter")
        for column, (heading, width) in enumerate((("Reason", 45), ("Title", 60), ("Date", 18), ("PMID", 12))):
            excluded.write_string(0, column, heading, bold)
            excluded.set_column(column, column, width, wrap)
        row = 1
        for reason, publications in _excluded(report):
            for p in publications:
                for column, value in enumerate((reason, p.title, p.publication_date or "", p.pmid)):
                    excluded.write_string(row, column, value)
                row += 1
    return output.getvalue()


def build_pdf(report: dict) -> bytes:
    # Imported here because WeasyPrint needs the Pango system libraries at import time.
    from weasyprint import HTML

    label = escape(period_label(report["year"], report["quarter"]))
    citations = format_citations(report["publications"])
    items = "".join(f"<li>{escape(citations[p.pmid])}</li>" for p in report["publications"])
    notes = "".join(
        f"<p class='note'>{len(publications)} verified publication(s) not included: {escape(reason)}.</p>"
        for reason, publications in _excluded(report) if publications
    )
    count = len(report["publications"])
    html = f"""<!doctype html><meta charset="utf-8"><style>
      @page {{ size: letter; margin: 0.75in; }}
      body {{ font-family: sans-serif; font-size: 10.5pt; line-height: 1.4; }}
      h1 {{ font-size: 16pt; margin: 0 0 2pt; color: #0b4f9c; }}
      .sub {{ color: #555; margin: 0 0 14pt; }}
      li {{ margin-bottom: 7pt; }}
      .note {{ color: #8a5a00; font-size: 9.5pt; }}
    </style>
    <h1>Verified publications</h1><p class="sub">{label} &middot; {count} publication(s)</p>
    {notes}<ol>{items}</ol>"""
    return HTML(string=html).write_pdf()
