from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import ReportType
from app.models.resource import Resource
from app.schemas.report import ReportResponse
from app.services.periods import MonthRange
from app.services.report_data import report_data, researcher_names
from app.services.report_export import build_pdf, build_xlsx

router = APIRouter(prefix="/reports", tags=["Reports"])

Month = Annotated[str, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="YYYY-MM, inclusive")]
ResourceId = Annotated[int | None, Query(description="Only publications attributed to this resource")]
_MEDIA_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


def _period(start: Month, end: Month) -> MonthRange:
    try:
        return MonthRange.parse(start, end)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


Period = Annotated[MonthRange, Depends(_period)]


@router.get("", response_model=ReportResponse)
def report(period: Period, resource_id: ResourceId = None, db: Session = Depends(get_db)):
    """Verified publications from ``start`` to ``end`` (a quarter, a year or any range of months)."""
    return report_data(db, period, _resource(db, resource_id))


@router.get("/export", response_class=Response)
def export_report(
    period: Period,
    format: Literal["xlsx", "pdf"],
    resource_id: ResourceId = None,
    report_type: ReportType = ReportType.BOTH,
    db: Session = Depends(get_db),
):
    """The report as an Excel workbook (all lists) or a PDF (the lists ``report_type`` picks)."""
    data = report_data(db, period, _resource(db, resource_id))
    if format == "xlsx":
        content = build_xlsx(data, researcher_names(db, data["publications"]))
    else:
        content = build_pdf(data, report_type)
    filename = f"publications-{period.slug()}.{format}"
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
