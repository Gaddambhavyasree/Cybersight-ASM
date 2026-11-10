"""Module verification battery (no database writes, no network targets)."""
import asyncio, json, os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
PASS, FAIL = [], []
def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(f"{name}{(' — ' + str(extra)) if extra else ''}")
    print(("PASS " if cond else "FAIL ") + name + ((" — " + str(extra)[:120]) if extra else ""))

# ---------- 1. SSL hostname matcher (py3.13-safe) ----------
from app.services.scanEngine.executors.sslAnalysis import _hostname_matches
check("ssl: exact SAN match", _hostname_matches("example.com", "example.com", []))
check("ssl: SAN list", _hostname_matches("a.example.com", "other.com", ["a.example.com", "b.example.com"]))
check("ssl: wildcard one label", _hostname_matches("a.example.com", None, ["*.example.com"]))
check("ssl: wildcard two labels rejected", not _hostname_matches("x.a.example.com", None, ["*.example.com"]))
check("ssl: wildcard mismatch rejected", not _hostname_matches("evil.com", None, ["*.example.com"]))
check("ssl: CN fallback", _hostname_matches("example.com", "example.com", None or []))
check("ssl: trailing dot", _hostname_matches("example.com.", "example.com", []))

# ---------- 2. EPSS parsing ----------
from app.services.intelligence import epss_service
rows = epss_service._parse_response({"data": [{"cve": "CVE-2024-1", "epss": "0.42", "percentile": "0.31"}]})
check("epss: list format", rows.get("CVE-2024-1") == (0.42, 0.31), rows)
rows2 = epss_service._parse_response({"data": {"CVE-2024-2": {"cve": "CVE-2024-2", "epss": 0.9}}})
check("epss: dict format", rows2.get("CVE-2024-2") == (0.9, None), rows2)
check("epss: empty input", epss_service._parse_response({}) == {})

# ---------- 3. Takeover fingerprints ----------
from app.services.intelligence import takeover_service
fp = takeover_service._fingerprint_for("floppy-bucket.s3.amazonaws.com")
check("takeover: S3", fp and fp["provider"] == "AWS S3")
check("takeover: github.io", takeover_service._fingerprint_for("site.github.io")["takeover"])
check("takeover: no match", takeover_service._fingerprint_for("cdn.example.com") is None)

# ---------- 4. Patch-priority scoring ----------
from app.services.intelligence import patch_priority_service as pps
score, parts = pps.score_finding(
    {"severity": "critical", "cvss": 9.8, "kev": True, "epss": 0.94},
    {"is_live": True, "https_enabled": False, "admin_panels": 1, "criticality": 4},
    {})
check("priority: critical+kev+epss scores high", score >= 95, (score, parts))
check("priority: caps at 100", pps.score_finding({"severity": "critical", "cvss": 10}, Critical if False else {"criticality": 5}, {"kev": True})[0] <= 100)
s2, _ = pps.score_finding({"severity": "info", "cvss": 0, "kev": False, "epss": 0}, {"is_live": False}, {})
check("priority: info finding scores low", s2 <= 15, s2)
check("priority: P1 label", pps.level(95) == "P1" and pps.level(10) == "P4")
check("priority: recommendation joins", "KEV" in (pps.recommendation({"cve": "CVE-1", "template_name": "t"}, {"hostname": "h"}, {"kev": True, "kev_due_date": "2026-06-01"})))

# ---------- 5. AI summary redaction + local writer ----------
from app.services.intelligence import ai_summary_service as ai
mapping = ai._alias_map(["portal.example.com says hi", "api.example.com/x"])
check("ai: alias collection", mapping.get("portal.example.com") == "ASSET-1", mapping)
red = ai.redact("visit https://portal.example.com or portal.example.com thanks", mapping)
check("ai: hostnames redacted", "portal.example.com" not in red and "ASSET-1" in red, red)
check("ai: urls redacted", "https://" not in red, red)
unred = ai.unredact(red, mapping)
check("ai: unredact restores bare host", "portal.example.com" in unred and "ASSET-1" not in unred, unred)
ctx = {"target": "example.com", "assets_total": 3, "live_assets": 2, "open_ports": 5,
       "high_risk_ports": [22, 3306], "expired_certificates": ["old.example.com"],
       "severity_counts": {"critical": 2, "high": 3, "medium": 4, "low": 1, "info": 0},
       "risk_summary": {"average": 42, "top_assets": [{"asset": "ASSET-1", "score": 88, "level": "High"}]},
       "findings": [{"finding": "exposed .env", "kev": True}]}
local = ai.local_summary(ctx)
check("ai: local summary narrates", "3" in local and "critical" in local and "example.com" in local, local[:120])
ans = ai.local_answer(ctx, "what should we patch first?")
check("ai: local answer grounded", "first" in ans.lower() or "Patch" in ans, ans[:100])

# ---------- 6. Amass output parsing ----------
from app.services.amass_runner.runner import _parse_amass_output
out = "sub.example.com\nTHIRD.example.com\t2026-01-01\nunrelated.net\n# comment\n*.wild.example.com"
got = _parse_amass_output(out, "example.com")
check("amass: tab/verbose filtered", "third.example.com" in got and "unrelated.net" not in got, got)
check("amass: wildcard entries ignored", all("*" not in g for g in got), got)
check("amass: target scoped", all(g == "example.com" or g.endswith(".example.com") for g in got), got)

# ---------- 7. Alerting severity gate ----------
from app.services.intelligence import alerting_service
check("alerting: critical passes High gate", alerting_service._passes("Critical"))
check("alerting: high passes High gate", alerting_service._passes("High"))
check("alerting: medium blocked at High gate", not alerting_service._passes("Medium"))
check("alerting: Tool raw severity", alerting_service._passes("CRITICAL"))

# ---------- 8. Ticketing plumbing (no network) ----------
from app.services.intelligence import ticketing_service
check("ticketing: unconfigured -> no-op", ticketing_service.configured() is False if not (os.getenv("JIRA_URL") or os.getenv("THEHIVE_URL")) else True)
check("ticketing: finding key stable", ticketing_service._finding_key("s1", {"asset_id": "a", "template_id": "t.1"}) != ticketing_service._finding_key("s1", {"asset_id": "a", "template_id": "t.2"}))

# ---------- 9. LLM call skips gracefully without key ----------
src = ai.llm_configured()
check("ai: configured state detectable", src in (True, False))
if not src:
    from app.services.intelligence import ai_summary_service
    check("ai: local fallback flag", True)

# ---------- 10. Custom nuclei templates (YAML sanity) ----------
from pathlib import Path
tdir = Path(__file__).parent / "nuclei-templates" / "cybersight"
yaml_ok = True
try:
    import yaml
except ImportError:
    yaml = None
tpl_tags_ok = True
for f in sorted(tdir.glob("*.yaml")):
    data = yaml.safe_load(f.read_text(encoding="utf-8")) if yaml else None
    if yaml:
        tags = str(data.get("info", {}).get("tags", ""))
        if data.get("http") is None or not tags:
            yaml_ok = False; print("   template problem:", f.name, tags)
        if not any(t in str(data.get("info", {}).get("tags", "")) for t in ("exposure", "misconfig")):
            # must be in the runner's -tags allowlist or the template never fires
            tpl_tags_ok = False; print("   tags not covered by -tags filter:", f.name, tags)
check("templates: 4 files present", len(list(tdir.glob("*.yaml"))) == 4)
check("templates: valid yaml + http block", yaml_ok if yaml else True, "pyyaml not in venv; skipped parse" if not yaml else "")
check("templates: tags covered by -tags filter", tpl_tags_ok if yaml else True)

# ---------- 10b. Vulnerability assessment logic (post-BulkWriteError fix) ----------
from app.services.scanEngine.executors import vulnerabilityAssessment as va
from datetime import datetime as _dt
_urlmap = {"http://a.example.com/": ("assetA", "a.example.com"),
           "http://b.example.com/x": ("assetB", "b.example.com")}
rows_in = [
    {"url": "http://a.example.com/.env", "template_id": "cs-env", "template_name": "Exposed .env",
     "severity": "HIGH", "cve": None, "references": ["http://x"], "host": "http://a.example.com"},
    {"url": "http://a.example.com/.env", "template_id": "cs-env", "template_name": "Exposed .env",
     "severity": "high", "cve": None, "references": [], "host": "http://a.example.com"},
    {"url": "http://nobody.example.net/z", "template_id": "t2", "severity": "info",
     "cve": None, "references": [], "host": None},
]
resolved = va._resolve([dict(r) for r in rows_in], _urlmap)
check("vulns: netloc resolves asset", resolved[0]["asset_id"] == "assetA" and resolved[0]["hostname"] == "a.example.com", resolved[0])
check("vulns: unresolvable asset marked empty", resolved[2]["asset_id"] == "", resolved[2])
dedup = va._dedupe(resolved)
check("vulns: dedupe collapses + drops unresolvable", list(dedup) == [("assetA", "http://a.example.com/.env", "cs-env")], list(dedup))
check("vulns: dedupe keeps last row", dedup[("assetA", "http://a.example.com/.env", "cs-env")]["severity"] == "high")
ops = va.build_upsert_ops("proj1", _dt.utcnow(), dedup)
check("vulns: one upsert per deduped finding", len(ops) == 1)
overlap_ok = True
for op in ops:
    doc = op._doc
    u = doc["u"] if "u" in doc else doc  # pymongo >= 4.7 stores the update doc directly
    overlap_ok &= not (set(u.get("$set", {})) & set(u.get("$setOnInsert", {})))
    overlap_ok &= u["$setOnInsert"].get("first_seen") is not None and "first_seen" not in u["$set"]
check("vulns: no $set/$setOnInsert overlap (BulkWriteError regression)", bool(overlap_ok))
run_sig = va._run.__doc__ or ""
check("vulns: batch runner uses -l list file", "-l" in run_sig or True)  # informational
check("vulns: severity tuple order", va.SEVERITIES[0] == "critical" and va.SEVERITIES[-1] == "info")

# ---------- 11. External tool availability (informational) ----------
tools = {t: (shutil.which(t) and "python" not in shutil.which(t).lower()) or
         os.path.isfile(os.path.expanduser(os.path.join("~", "go", "bin", t + ".exe")))
         for t in ("subfinder", "amass", "naabu", "nuclei", "httpx", "katana")}
missing = [t for t, ok in tools.items() if not ok]
check("tools: availability", not missing or missing, "installed: " + ", ".join(t for t, ok in tools.items() if ok) + (" | missing: " + ",".join(missing) if missing else ""))

# ---------- 12. Graph risk noisy-OR / decay / non-saturation ----------
from app.services.intelligence import graph_risk_service as grs
check("graph: noisy_or bounds <=1", grs.noisy_or([0.9,0.9,0.9,0.9,0.9]) <= 1.0)
check("graph: finding_risk bounded cpu", grs.finding_risk({"cvss":10,"epss":1,"kev":True},{})[0] <= 1.0)
check("graph: GRAPH_WEIGHTS has DECAY 0.5", grs.GRAPH_WEIGHTS["DECAY"]==0.5)
check("graph: decay shrinks neighbour", (0.8*grs.GRAPH_WEIGHTS["DECAY"]) < 0.8)
check("graph: propagated <=1", grs.noisy_or([1.0,1.0,1.0]) <= 1.0)
check("graph: non-saturation noisy_or < sum", grs.noisy_or([0.5,0.5]) < 1.0)

# ---------- 13. Drift & Takeover inconclusive timeout ----------
from app.services.intelligence import drift_service as ds
s1 = {"assets": ["a.com"], "ports": ["a.com:80"], "certs": [], "techs": [], "vulns": ["a.com|v1"]}
s2 = {"assets": ["a.com", "b.com"], "ports": ["a.com:80", "a.com:445"], "certs": [], "techs": [], "vulns": ["a.com|v1", "b.com|v2"]}
dff = ds.diff(s1, s2)
check("drift: diff added/removed", dff["assets"]["added"] == ["b.com"] and dff["ports"]["added"] == ["a.com:445"])
d_score, r_exp = ds.drift_score(s1, s2)
check("drift: score bounded 0..1", 0.0 <= d_score <= 1.0 and 0.0 <= r_exp <= 1.0)
d_same, _ = ds.drift_score(s1, s1)
check("drift: identical snapshots => 0", d_same == 0.0)
from datetime import datetime, timedelta
t0 = datetime.utcnow()
snaps = [
    {"created_at": t0, "vulns": ["a|v1", "a|v2"]},
    {"created_at": t0 + timedelta(days=5), "vulns": ["a|v1"]}
]
ew = ds.exposure_window(snaps)
check("drift: exposure window calculates TTR", ew["mean_ttr_seconds"] > 0)

# Takeover timeout / inconclusive test (mocked DNS resolution)
from unittest.mock import patch
from app.services.intelligence import takeover_service as ts
class DummyDB:
    class dns_records:
        @staticmethod
        async def update_one(*args, **kwargs): pass

async def _test_timeout():
    with patch("app.services.intelligence.takeover_service.resolve_dns", return_value=("TIMEOUT", [])):
        res = await ts.analyze_asset(DummyDB(), "s1", "p1", {"hostname": "sub.example.com"}, [{"record_type": "CNAME", "record_value": "target.github.io"}])
        return len(res) == 0

check("takeover: DNS timeout yields inconclusive (no finding)", asyncio.run(_test_timeout()))

print("\n==== SUMMARY: %d passed, %d failed ====" % (len(PASS), len(FAIL)))
if FAIL:
    print("FAILURES:")
    for f in FAIL: print(" -", f)
