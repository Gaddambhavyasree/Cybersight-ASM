from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from app.database import get_database
from app.dependencies.auth import get_current_user
from app.schemas.report import ReportCreate, ReportItem, ReportList, ReportResponse
from app.services.report_service import build_report, list_reports, get_report, public, pdf_bytes

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.post("", response_model=ReportResponse, status_code=201)
async def generate(data: ReportCreate, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    return public(await build_report(db, data.scan_id, data.report_type, current_user, data.name), True)

@router.get("", response_model=ReportList)
async def listing(page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=200), search: str | None = None, report_type: str | None = None, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    return await list_reports(db, current_user, page, per_page, search, report_type)

@router.get("/{report_id}/json")
async def download_json(report_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    doc = await get_report(db, report_id, current_user)
    import json
    return Response(content=json.dumps(public(doc, True), default=str), media_type="application/json", headers={"Content-Disposition": f'attachment; filename="{doc["name"].replace(" ", "_")}.json"'})

@router.get("/{report_id}/pdf")
async def download_pdf(report_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    doc = await get_report(db, report_id, current_user)
    return Response(content=pdf_bytes(doc), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{doc["name"].replace(" ", "_")}.pdf"'})

@router.get("/{report_id}", response_model=ReportResponse)
async def detail(report_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    return public(await get_report(db, report_id, current_user), True)

@router.delete("/{report_id}")
async def remove(report_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    doc = await get_report(db, report_id, current_user)
    await db.reports.delete_one({"_id": doc["_id"]})
    return {"message": "Report deleted"}
