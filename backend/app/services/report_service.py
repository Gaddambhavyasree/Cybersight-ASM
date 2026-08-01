import html
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException

TYPES = {"executive", "technical", "asset_inventory", "vulnerability"}
COLLECTIONS = ("assets", "ports", "technologies", "dns_records", "ssl_analysis", "web_assets", "vulnerabilities", "threat_intelligence")

def _safe(value):
    """Convert Mongo values in report payloads into API/JSON-safe values."""
    if isinstance(value, ObjectId): return str(value)
    if isinstance(value, datetime): return value.isoformat()
    if isinstance(value, dict): return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [_safe(v) for v in value]
    return value

async def _scan(db, scan_id, user):
    try: oid = ObjectId(scan_id)
    except Exception: raise HTTPException(404, "Completed scan not found")
    scan = await db.scans.find_one({"_id": oid, "status": "completed"})
    if not scan: raise HTTPException(404, "Completed scan not found")
    if str(user.get("role", "")).lower() != "admin":
        try: project_id = ObjectId(str(scan["project_id"]))
        except Exception: raise HTTPException(404, "Completed scan not found")
        project = await db.projects.find_one({"_id": project_id, "created_by": str(user["_id"])})
        if not project: raise HTTPException(404, "Completed scan not found")
    return scan

async def build_report(db, scan_id, report_type, user, name=None):
    if report_type not in TYPES: raise HTTPException(400, "Unsupported report type")
    scan = await _scan(db, scan_id, user); q = {"scan_id": scan_id}
    rows = {kind: await db[kind].find(q).to_list(None) for kind in COLLECTIONS}
    assets = rows["assets"] or await db.assets.find({"project_id": str(scan["project_id"])}).to_list(None)
    risks = [a.get("risk_score", 0) for a in assets]
    counts = {"assets": len(assets), "live_assets": sum(bool(a.get("is_live")) for a in assets), "open_ports": sum(p.get("state") == "open" for p in rows["ports"]), "technologies": len(rows["technologies"]), "dns_records": len(rows["dns_records"]), "ssl": len(rows["ssl_analysis"]), "web_assets": len(rows["web_assets"]), "vulnerabilities": len(rows["vulnerabilities"]), "critical_vulnerabilities": sum(str(v.get("severity", "")).lower() == "critical" for v in rows["vulnerabilities"]), "threat_intelligence": len(rows["threat_intelligence"])}
    risk_score = round(sum(risks) / len(risks)) if risks else 0
    recommendations = []
    if counts["critical_vulnerabilities"]: recommendations.append("Patch critical vulnerabilities immediately")
    if any(p.get("port") in {21, 23, 445, 3389, 3306, 5432, 6379, 27017} for p in rows["ports"]): recommendations.append("Close or restrict unnecessary high-risk ports")
    if any(s.get("expired") for s in rows["ssl_analysis"]): recommendations.append("Renew expired SSL certificates")
    if any(not s.get("hsts_enabled") for s in rows["ssl_analysis"]): recommendations.append("Enable HSTS on HTTPS services")
    summary = f"The assessment discovered {counts['assets']} assets, {counts['live_assets']} live hosts, {counts['critical_vulnerabilities']} critical vulnerabilities, and an overall risk score of {risk_score}."
    data = _safe({"summary": summary, "statistics": {**counts, "risk_score": risk_score}, "assets": assets, "ports": rows["ports"], "technologies": rows["technologies"], "dns_records": rows["dns_records"], "ssl_analysis": rows["ssl_analysis"], "web_assets": rows["web_assets"], "vulnerabilities": rows["vulnerabilities"], "threat_intelligence": rows["threat_intelligence"], "recommendations": recommendations, "generated_at": datetime.utcnow()})
    now = datetime.utcnow(); doc = {"scan_id": scan_id, "project_id": str(scan["project_id"]), "project_name": scan.get("project_name"), "scan_name": scan.get("scan_name", "Scan"), "name": name or f"{scan.get('scan_name', 'Scan')} - {report_type.replace('_', ' ').title()}", "report_type": report_type, "generated_by": str(user.get("_id")), "generated_at": now, "status": "completed", "data": data}
    result = await db.reports.insert_one(doc); doc["_id"] = result.inserted_id
    return doc

def public(doc, include_data=False):
    out = {k: v for k, v in doc.items() if include_data or k != "data"}; out["id"] = str(out.pop("_id")); return out

async def list_reports(db, user, page=1, per_page=25, search=None, report_type=None):
    q = {} if str(user.get("role", "")).lower() == "admin" else {"generated_by": str(user["_id"])}
    if report_type: q["report_type"] = report_type
    if search: q["$or"] = [{"name": {"$regex": search, "$options": "i"}}, {"project_name": {"$regex": search, "$options": "i"}}, {"scan_name": {"$regex": search, "$options": "i"}}]
    total = await db.reports.count_documents(q); docs = await db.reports.find(q).sort("generated_at", -1).skip((page - 1) * per_page).limit(per_page).to_list(per_page)
    return {"records": [public(x) for x in docs], "total": total, "page": page, "per_page": per_page}

async def get_report(db, report_id, user):
    try: oid = ObjectId(report_id)
    except Exception: raise HTTPException(404, "Report not found")
    doc = await db.reports.find_one({"_id": oid});
    if not doc or (str(user.get("role", "")).lower() != "admin" and doc.get("generated_by") != str(user["_id"])): raise HTTPException(404, "Report not found")
    return doc

def pdf_bytes(doc):
    # Use ReportLab for a real paginated document rather than a raw one-line PDF stream.
    from io import BytesIO
    from textwrap import wrap
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    d = doc.get("data", {}); buffer = BytesIO(); pdf = canvas.Canvas(buffer, pagesize=letter); width, height = letter
    page = 1
    def header():
        pdf.setFillColor(colors.HexColor("#0f172a")); pdf.rect(0, height - 58, width, 58, fill=1, stroke=0)
        pdf.setFillColor(colors.HexColor("#38bdf8")); pdf.setFont("Helvetica-Bold", 16); pdf.drawString(42, height - 35, "CyberSight ASM")
        pdf.setFillColor(colors.HexColor("#94a3b8")); pdf.setFont("Helvetica", 8); pdf.drawRightString(width - 42, height - 33, "SECURITY ASSESSMENT REPORT")
    def footer():
        pdf.setStrokeColor(colors.HexColor("#cbd5e1")); pdf.line(42, 35, width - 42, 35); pdf.setFillColor(colors.HexColor("#64748b")); pdf.setFont("Helvetica", 8); pdf.drawString(42, 22, "CyberSight ASM - Confidential"); pdf.drawRightString(width - 42, 22, f"Page {page}")
    def new_page():
        nonlocal page; footer(); pdf.showPage(); page += 1; header()
    header(); y = height - 100
    pdf.setFillColor(colors.HexColor("#0f172a")); pdf.setFont("Helvetica-Bold", 22); pdf.drawString(42, y, str(doc.get("name", "ASM Report"))[:85]); y -= 28
    pdf.setFont("Helvetica", 10); pdf.setFillColor(colors.HexColor("#475569")); pdf.drawString(42, y, f"Project: {doc.get('project_name') or '--'}"); y -= 16; pdf.drawString(42, y, f"Scan: {doc.get('scan_name') or '--'}"); y -= 16; pdf.drawString(42, y, f"Generated: {doc.get('generated_at') or '--'}"); y -= 36
    def section(title):
        nonlocal y
        if y < 90: new_page(); y = height - 90
        pdf.setFillColor(colors.HexColor("#0284c7")); pdf.setFont("Helvetica-Bold", 13); pdf.drawString(42, y, title); y -= 20
    def text_block(value, bold=False):
        nonlocal y
        pdf.setFillColor(colors.HexColor("#334155")); pdf.setFont("Helvetica-Bold" if bold else "Helvetica", 9)
        for raw in str(value or "--").splitlines() or ["--"]:
            for line in wrap(raw.encode("latin-1", "replace").decode("latin-1"), 105) or [""]:
                if y < 58: new_page(); y = height - 85; pdf.setFillColor(colors.HexColor("#334155")); pdf.setFont("Helvetica", 9)
                pdf.drawString(48, y, line); y -= 13
    section("Executive Summary"); text_block(d.get("summary", "No summary available.")); y -= 12
    section("Statistics")
    for key, value in d.get("statistics", {}).items(): text_block(f"{key.replace('_', ' ').title()}: {value}")
    y -= 12; section("Recommendations")
    recommendations = d.get("recommendations", []) or ["No recommendations were generated."]
    for item in recommendations: text_block(f"- {item}")
    footer(); pdf.save(); return buffer.getvalue()
