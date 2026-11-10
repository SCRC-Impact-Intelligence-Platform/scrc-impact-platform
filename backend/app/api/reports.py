from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.report import QuarterlyReportResponse
from app.services.quarterly_report import quarterly_report_data, researcher_names
from app.services.report_export import build_pdf, build_xlsx

router = APIRouter(prefix="/reports", tags=["Reports"])

Year = Annotated[int, Query(ge=1900, le=2100)]
Quarter = Annotated[int, Query(ge=1, le=4)]
_MEDIA_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


@router.get("/quarterly", response_model=QuarterlyReportResponse)
def quarterly_report(year: Year, quarter: Quarter, db: Session = Depends(get_db)):
    return quarterly_report_data(db, year, quarter)


@router.get("/quarterly/export", response_class=Response)
def export_quarterly_report(
    year: Year,
    quarter: Quarter,
    format: Literal["xlsx", "pdf"],
    db: Session = Depends(get_db),
):
    """The quarterly report as an Excel workbook or PDF."""
    report = quarterly_report_data(db, year, quarter)
    if format == "xlsx":
        content = build_xlsx(report, researcher_names(db, report["publications"]))
    else:
        content = build_pdf(report)
    filename = f"verified-publications-{year}-Q{quarter}.{format}"
    return Response(
        content, media_type=_MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
