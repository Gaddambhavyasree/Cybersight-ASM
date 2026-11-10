from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from fastapi.responses import Response
from app.database import get_database
from app.dependencies.auth import get_current_user
from app.schemas.report import ReportCreate, ReportItem, ReportList, ReportResponse
from app.services.report_service import build_report, list_reports, get_report, public, pdf_bytes

router = APIRouter(prefix="/api/reports", tags=["Reports"])


class AskPayload(BaseModel):
    question: str

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


@router.post("/{report_id}/ai-summary", response_model=ReportResponse)
async def regenerate_ai_summary(report_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    """(Re)generate the AI executive analysis for an existing report. Falls back
    to the deterministic local writer when no LLM key is configured."""
    from datetime import datetime
    from app.services.intelligence import ai_summary_service
    doc = await get_report(db, report_id, current_user)
    ai = await ai_summary_service.generate_report_summary(db, doc["scan_id"])
    await db.reports.update_one(
        {"_id": doc["_id"]},
        {"$set": {"data.ai_summary": ai["summary"], "data.ai_summary_source": ai["source"], "generated_at": datetime.utcnow()}},
    )
    updated = await db.reports.find_one({"_id": doc["_id"]})
    return public(updated, True)


@router.post("/{report_id}/ask")
async def ask_report(report_id: str, payload: AskPayload, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    """Grounded Q&A copilot over a completed scan. Answers cite only the collected data."""
    from app.services.intelligence import ai_summary_service
    doc = await get_report(db, report_id, current_user)
    question = (payload.question or "").strip()
    if not question:
        return {"answer": "Please ask a question about this scan.", "source": "none"}
    result = await ai_summary_service.answer_question(db, doc["scan_id"], question)
    return result
