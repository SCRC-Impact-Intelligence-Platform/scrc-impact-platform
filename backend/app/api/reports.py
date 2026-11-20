from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import ReportType
from app.models.resource import Resource
from app.schemas.report import QuarterlyReportResponse
from app.services.quarterly_report import quarterly_report_data, researcher_names
from app.services.report_export import build_pdf, build_xlsx

router = APIRouter(prefix="/reports", tags=["Reports"])

Year = Annotated[int, Query(ge=1900, le=2100)]
Quarter = Annotated[int, Query(ge=1, le=4)]
ResourceId = Annotated[int | None, Query(description="Only publications attributed to this resource")]
_MEDIA_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


@router.get("/quarterly", response_model=QuarterlyReportResponse)
def quarterly_report(year: Year, quarter: Quarter, resource_id: ResourceId = None, db: Session = Depends(get_db)):
    return quarterly_report_data(db, year, quarter, _resource(db, resource_id))


@router.get("/quarterly/export", response_class=Response)
def export_quarterly_report(
    year: Year,
    quarter: Quarter,
    format: Literal["xlsx", "pdf"],
    resource_id: ResourceId = None,
    report_type: ReportType = ReportType.LEADERSHIP,
    db: Session = Depends(get_db),
):
    """The quarterly report as an Excel workbook or PDF (``report_type`` sets the PDF title)."""
    report = quarterly_report_data(db, year, quarter, _resource(db, resource_id))
    if format == "xlsx":
        content = build_xlsx(report, researcher_names(db, report["publications"]))
    else:
        content = build_pdf(report, report_type)
    filename = f"verified-publications-{year}-Q{quarter}.{format}"
    return Response(
        content, media_type=_MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _resource(db: Session, resource_id: int | None) -> Resource | None:
    if resource_id is None:
        return None
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(404, "Resource not found")
    return resource
