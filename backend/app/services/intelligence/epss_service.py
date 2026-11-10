"""EPSS (Exploit Prediction Scoring System) enrichment service.

Fetches exploit-likelihood scores for CVEs from the FIRST EPSS API. EPSS data
is public and free — no API key is required. Results are returned as a map of
``CVE-XXXX-YYYY`` -> ``(score, percentile)`` where score is the probability of
exploitation in the next 30 days (0-1).
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

EPSS_URL = "https://api.first.org/data/v1/epss"
# EPSS returns `data`: [{cve, epss, percentile, date}, ...] either as
# {"data": [...], "total": N} or (deprecated format) {"data": {"CVE-...": {...}}}.


def _coerce(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_response(payload: dict) -> dict:
    out = {}
    if not isinstance(payload, dict):
        return out
    data = payload.get("data")
    rows = data if isinstance(data, list) else (list(data.values()) if isinstance(data, dict) else [])
    for row in rows:
        if not isinstance(row, dict):
            continue
        cve = str(row.get("cve") or "").upper()
        if not cve:
            continue
        score = _coerce(row.get("epss"))
        percentile = _coerce(row.get("percentile"))
        if score is not None or percentile is not None:
            out[cve] = (score, percentile)
    return out


async def fetch_epss(client, cves: list[str], batch_size: int = 50) -> dict:
    """Fetch EPSS scores for the given CVE IDs. Best-effort, never raises."""
    unique = sorted({str(c).upper() for c in cves if c})
    out: dict = {}
    if not unique:
        return out
    # Prefer the batch endpoint: up to 100 CVEs per call.
    for start in range(0, len(unique), 100):
        chunk = unique[start:start + 100]
        try:
            response = await client.post(EPSS_URL, json={"cve": list(chunk)})
            response.raise_for_status()
            out.update(_parse_response(response.json()))
            continue
        except Exception:
            pass
        # Fallback: sequential single-CVE lookups.
        for idx in range(0, len(chunk), batch_size):
            sub = chunk[idx:idx + batch_size]
            results = await asyncio.gather(*[_fetch_single(client, c) for c in sub])
            for cve, scores in zip(sub, results):
                if scores:
                    out[cve] = scores
    if out:
        logger.info("EPSS enrichment fetched %d/%d CVE scores", len(out), len(unique))
    return out


async def _fetch_single(client, cve: str):
    try:
        response = await client.get(EPSS_URL, params={"cve": cve})
        response.raise_for_status()
        return _parse_response(response.json()).get(cve)
    except Exception:
        return None
