"""Attack-surface snapshot / drift (no ML)."""
import hashlib, logging
from datetime import datetime
from bson import ObjectId
from collections import defaultdict

logger = logging.getLogger(__name__)

DRIFT_WEIGHTS = {"assets": 1.0, "ports": 1.0, "certs": 1.0, "techs": 0.5, "vulns": 1.5}
HIGH_PORTS = {21,22,23,25,110,143,445,1433,1521,3306,3389,5432,5900,6379,9200,27017}
RISK_MULTIPLIER = 3

def _hash(snapshot):
    raw = repr(sorted((k, sorted(v) if isinstance(v, (list, set, tuple)) else v) for k, v in snapshot.items()))
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

def _snap_from_sets(assets, ports, certs, techs, vulns):
    return {"assets": sorted(set(assets or [])), "ports": sorted(set(ports or [])), "certs": sorted(set(certs or [])), "techs": sorted(set(techs or [])), "vulns": sorted(set(vulns or []))}

def _extract(assets, ports, ssls, techs, vulns):
    a = [(x.get("hostname") or str(x.get("_id",""))) for x in assets]
    p = [f"{(x.get('hostname') or x.get('asset_id',''))}:{x.get('port')}" for x in ports]
    c = [(x.get("fingerprint") or x.get("certificate_fingerprint") or x.get("sha256") or "") for x in ssls]
    c = [x for x in c if x]
    t = [f"{(x.get('hostname') or x.get('asset_id',''))}:{x.get('technology_name','')}" for x in techs]
    v = [f"{(x.get('hostname') or x.get('asset_id',''))}|{x.get('template_id') or x.get('cve') or x.get('_id','')}" for x in vulns]
    return _snap_from_sets(a, p, c, t, v)

async def _fetch(db, name, q):
    try:
        r = getattr(db, name).find(q)
        if hasattr(r, "to_list"): return await r.to_list(None)
        return list(r)
    except Exception:
        return []

async def snapshot_scan(db, scan_id):
    try:
        scan = await db.scans.find_one({"_id": ObjectId(str(scan_id))}) if True else None
        if not scan: return None
        pid = str(scan.get("project_id") or "")
        assets = await _fetch(db, "assets", {"project_id": pid})
        ports = await _fetch(db, "ports", {"project_id": pid, "state": "open"})
        ssls = await _fetch(db, "ssl_analysis", {"project_id": pid})
        techs = await _fetch(db, "technologies", {"project_id": pid})
        vulns = await _fetch(db, "vulnerabilities", {"project_id": pid})
        snap = _extract(assets, ports, ssls, techs, vulns)
        doc = {"project_id": pid, "scan_id": str(scan_id), "created_at": datetime.utcnow(), **snap, "hash": _hash(snap)}
        # keep vuln severity map for risk-weighted scoring
        doc["vuln_severity"] = {f"{(x.get('hostname') or x.get('asset_id',''))}|{x.get('template_id') or x.get('cve') or x.get('_id','')}": str(x.get("severity","")).lower() for x in vulns}
        await db.surface_snapshots.insert_one(doc)
        return doc
    except Exception:
        logger.exception("drift snapshot failed"); return None

def diff(prev, curr):
    out = {}
    for cat in DRIFT_WEIGHTS:
        a, b = set(prev.get(cat) or []), set(curr.get(cat) or [])
        out[cat] = {"added": sorted(b - a), "removed": sorted(a - b)}
    return out

def drift_score(prev, curr):
    """1 - weighted Jaccard complement in [0,1]; identical => 0."""
    num, den = 0.0, 0.0
    for cat, w in DRIFT_WEIGHTS.items():
        a, b = set(prev.get(cat) or []), set(curr.get(cat) or [])
        num += w * len(a & b); den += w * len(a | b)
    if den == 0: return 0.0, 0.0
    d = 1.0 - (num / den)
    d = max(0.0, min(1.0, d))
    # risk-weighted exposure: new high ports + new crit/high vulns x3, normalised by total weighted additions+1
    dff = diff(prev, curr)
    risk_hits = 0
    for key in dff["ports"]["added"]:
        try: port = int(str(key).rsplit(":",1)[1])
        except Exception: port = 0
        if port in HIGH_PORTS: risk_hits += 1
    sev_map = curr.get("vuln_severity") or prev.get("vuln_severity") or {}
    for key in dff["vulns"]["added"]:
        if str(sev_map.get(key,"")).lower() in ("critical","high"): risk_hits += 1
    total_added = sum(len(v["added"]) for v in dff.values()) + 1
    risk_weighted = min(1.0, (risk_hits * RISK_MULTIPLIER) / total_added)
    return d, risk_weighted

def exposure_window(snapshots):
    """snapshots: list of docs sorted by created_at. Returns TTR stats + open ages."""
    # track first appearance per vuln key
    first_seen, last_seen = {}, {}
    for s in snapshots:
        ts = s.get("created_at")
        for k in (s.get("vulns") or []):
            if k not in first_seen: first_seen[k] = ts
            last_seen[k] = ts
    ttrs, open_ages = [], []
    if not snapshots: return {"mean_ttr_seconds": 0, "median_ttr_seconds": 0, "remediated": [], "open": [], "open_age_seconds": []}
    last_ts = snapshots[-1].get("created_at")
    # presence per snapshot
    presence = [{k: i for i, k in enumerate(s.get("vulns") or [])} for s in snapshots]
    keys = set(first_seen)
    for k in sorted(keys):
        first_idx = next((i for i, s in enumerate(snapshots) if k in (s.get("vulns") or [])), None)
        last_idx = max((i for i, s in enumerate(snapshots) if k in (s.get("vulns") or [])), default=None)
        if first_idx is None: continue
        t0 = snapshots[first_idx].get("created_at")
        # remediated if absent after last seen and there is a later snapshot
        if last_idx is not None and last_idx < len(snapshots) - 1:
            t1 = snapshots[last_idx + 1].get("created_at")
            if t0 and t1:
                ttrs.append((t1 - t0).total_seconds())
                continue
        # still open
        if t0 and last_ts:
            age = (last_ts - t0).total_seconds()
            open_ages.append(age)
    import statistics
    mean_ttr = sum(ttrs)/len(ttrs) if ttrs else 0.0
    median_ttr = statistics.median(ttrs) if ttrs else 0.0
    return {"mean_ttr_seconds": mean_ttr, "median_ttr_seconds": median_ttr, "remediated": [{"vuln": k, "ttr_seconds": ttrs[i]} for i, k in enumerate(sorted(keys)) if i < len(ttrs)], "open": open_ages, "open_age_seconds": open_ages}

async def timeline(db, project_id):
    snaps = await _fetch(db, "surface_snapshots", {"project_id": str(project_id)})
    snaps = sorted(snaps, key=lambda s: s.get("created_at") or datetime.min)
    points = []
    for i in range(1, len(snaps)):
        d, rw = drift_score(snaps[i-1], snaps[i])
        points.append({"scan_id": snaps[i].get("scan_id"), "created_at": snaps[i].get("created_at"), "drift_score": round(d,4), "risk_weighted_exposure": round(rw,4), "diff": diff(snaps[i-1], snaps[i])})
    latest_diff = points[-1]["diff"] if points else {}
    return {"project_id": str(project_id), "snapshots": len(snaps), "timeline": points, "latest_diff": latest_diff, "exposure_window": exposure_window(snaps)}

async def exposure_windows(db, project_id):
    snaps = await _fetch(db, "surface_snapshots", {"project_id": str(project_id)})
    snaps = sorted(snaps, key=lambda s: s.get("created_at") or datetime.min)
    return {"project_id": str(project_id), **exposure_window(snaps)}
