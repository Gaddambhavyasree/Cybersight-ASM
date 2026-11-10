"""Subdomain dangling-DNS / takeover-risk detection.

Purely observational: when a subdomain's C (or A) chain points into a known
cloud provider zone but the remote resource no longer resolves or serves the
provider's "resource not found" signature, the entry is flagged as dangling or
takeover-exploitable.
"""

import logging
import dns.resolver

logger = logging.getLogger(__name__)

# provider fingerprint table:
FINGERPRINTS = [
    {"suffix": "github.io", "sig": "there isn't a github pages site here", "takeover": True, "provider": "GitHub Pages", "statuses": [404]},
    {"suffix": "s3.amazonaws.com", "sig": "nosuchbucket", "takeover": True, "provider": "AWS S3", "statuses": [404]},
    {"suffix": "herokuapp.com", "sig": "no such app", "takeover": True, "provider": "Heroku", "statuses": [404]},
    {"suffix": "firebaseapp.com", "sig": "site not found", "takeover": False, "provider": "Firebase Hosting", "statuses": [404]},
    {"suffix": "web.app", "sig": "site not found", "takeover": False, "provider": "Firebase Hosting", "statuses": [404]},
    {"suffix": "azurewebsites.net", "sig": "404 web site not found", "takeover": True, "provider": "Azure App Service", "statuses": [404]},
    {"suffix": "blob.core.windows.net", "sig": "blobnotfound", "takeover": True, "provider": "Azure Blob Storage", "statuses": [404]},
    {"suffix": "azureedge.net", "sig": "resource not found", "takeover": False, "provider": "Azure CDN", "statuses": [404]},
    {"suffix": "cloudapp.azure.com", "sig": "", "takeover": False, "provider": "Azure Cloud"},
    {"suffix": "cloudfront.net", "sig": "error 403: the request could not be satisfied", "takeover": False, "provider": "AWS CloudFront", "statuses": [403]},
    {"suffix": "netlify.app", "sig": "not found - request id", "takeover": True, "provider": "Netlify", "statuses": [404]},
    {"suffix": "netlify.global.ssl.fastly.net", "sig": "fastly error: unknown domain", "takeover": False, "provider": "Netlify (Fastly)", "statuses": [404]},
    {"suffix": "zendesk.com", "sig": "help center closed", "takeover": True, "provider": "Zendesk", "statuses": [404]},
    {"suffix": "wordpress.com", "sig": "do you want to register", "takeover": True, "provider": "WordPress.com", "statuses": [404]},
    {"suffix": "tumblr.com", "sig": "there's nothing here", "takeover": True, "provider": "Tumblr", "statuses": [404]},
    {"suffix": "shopify.com", "sig": "sorry, this shop is currently unavailable", "takeover": True, "provider": "Shopify", "statuses": [404]},
    {"suffix": "pantheon.io", "sig": "the gods are wise", "takeover": True, "provider": "Pantheon", "statuses": [404]},
    {"suffix": "surge.sh", "sig": "project not found", "takeover": True, "provider": "Surge", "statuses": [404]},
    # 10 additional fingerprints (can-i-take-over-xyz knowledge)
    {"suffix": "fastly.net", "sig": "fastly error: unknown domain", "takeover": True, "provider": "Fastly", "statuses": [404]},
    {"suffix": "bitbucket.io", "sig": "repository not found", "takeover": True, "provider": "Bitbucket", "statuses": [404]},
    {"suffix": "ghost.io", "sig": "the thing you were looking for is no longer here", "takeover": True, "provider": "Ghost", "statuses": [404]},
    {"suffix": "readme.io", "sig": "project doesnt exist", "takeover": True, "provider": "ReadMe", "statuses": [404]},
    {"suffix": "helpscoutdocs.com", "sig": "no settings found for this domain", "takeover": True, "provider": "Help Scout", "statuses": [404]},
    {"suffix": "cargo.site", "sig": "cargo site not found", "takeover": True, "provider": "Cargo", "statuses": [404]},
    {"suffix": "webflow.io", "sig": "the page you are looking for doesn't exist", "takeover": True, "provider": "Webflow", "statuses": [404]},
    {"suffix": "unbouncepages.com", "sig": "the requested url was not found on this server", "takeover": True, "provider": "Unbounce", "statuses": [404]},
    {"suffix": "statuspage.io", "sig": "better status communication", "takeover": True, "provider": "Statuspage", "statuses": [404]},
    {"suffix": "vercel.app", "sig": "404: page_not_found", "takeover": True, "provider": "Vercel", "statuses": [404]},
]


def _fingerprint_for(value: str):
    value = (value or "").lower().strip(".")
    for fp in FINGERPRINTS:
        if value.endswith(fp["suffix"]):
            return fp
    return None


def resolve_dns(hostname: str) -> tuple[str, list[str]]:
    """Separate DNS resolution via dnspython."""
    try:
        answers = dns.resolver.resolve(hostname, 'A')
        return "NOERROR", [str(r) for r in answers]
    except dns.resolver.NXDOMAIN:
        return "NXDOMAIN", []
    except dns.resolver.NoAnswer:
        return "NOERROR", []
    except dns.resolver.Timeout:
        return "TIMEOUT", []
    except Exception:
        return "ERROR", []


async def _probe(client, hostname: str):
    """Read-only probe of the third-party host. Returns (reachable, status, body_sig_match)."""
    try:
        response = await client.get(f"https://{hostname}/", follow_redirects=True, timeout=8)
        body = (response.text or "")[:4000].lower()
        return "http-ok", response.status_code, body
    except Exception:
        return "unreachable", None, ""


async def analyze_asset(db, scan_id: str, project_id: str, asset: dict, records: list[dict]) -> list[dict]:
    """Inspect DNS records for one asset. Returns a list of detection dicts."""
    import httpx
    from datetime import datetime

    hostname = (asset.get("hostname") or "").lower().strip(".")
    candidates = []
    seen = set()
    for record in records:
        value = (record.get("record_value") or "").lower().strip(".")
        if record.get("record_type", "").upper() != "CNAME" or not value:
            continue
        if not value or value in seen or value.endswith(hostname):
            continue
        seen.add(value)
        fp = _fingerprint_for(value)
        if fp:
            candidates.append((value, fp))

    detections = []
    if not candidates:
        return detections

    now = datetime.utcnow()

    async with httpx.AsyncClient() as client:
        for value, fp in candidates:
            # 1. DNS Resolution check first
            dns_status, ips = resolve_dns(value)
            if dns_status == "TIMEOUT":
                logger.info("Takeover check timeout for %s -> inconclusive", value)
                continue  # Timeouts labeled inconclusive; no finding created
            
            condition = None
            confidence = "low"
            rule_fired = ""
            status_code = None
            sig_match = False

            if dns_status == "NXDOMAIN":
                condition = "dangling"
                confidence = "high"
                rule_fired = "dns_nxdomain"
                detail = f"{value} points to {fp['provider']} but target domain does not resolve (NXDOMAIN)."
                takeover = fp["takeover"]
            else:
                # 2. HTTP Probe
                state, status_code, body = await _probe(client, value)
                if state == "unreachable":
                    logger.info("Takeover check HTTP unreachable for %s -> inconclusive", value)
                    continue  # Timeout / unreachable labeled inconclusive; no finding created

                # Verify required HTTP status codes and body signature
                statuses = fp.get("statuses")
                status_ok = (status_code in statuses) if statuses else True
                sig_match = bool(fp["sig"]) and (fp["sig"] in body) and status_ok

                if sig_match:
                    condition = "takeover_possible" if fp["takeover"] else "dangling"
                    confidence = "high" if status_ok else "medium"
                    rule_fired = "http_status_and_body_signature" if status_ok else "body_signature_match"
                    detail = f"{value} ({fp['provider']}) returned status {status_code} and deployment-missing signature."
                    takeover = fp["takeover"]
                else:
                    # Resource is live or signature didn't match; update DNS record status
                    await db.dns_records.update_one(
                        {"project_id": project_id, "asset_id": str(asset.get("_id")), "record_type": "CNAME", "record_value": value},
                        {"$set": {"takeover_checked": now.isoformat(), "takeover_status": "resolved", "updated_at": now}},
                    )
                    continue

            evidence = {"provider": fp["provider"], "cname": value, "dns_status": dns_status,
                        "http_status": status_code, "signature_matched": sig_match, "rule_fired": rule_fired}
            detections.append({"host": hostname, "record_value": value, "provider": fp["provider"],
                               "condition": condition, "confidence": confidence, "rule": rule_fired,
                               "takeover": takeover, "detail": detail, "evidence": evidence})

            await db.dns_records.update_one(
                {"project_id": project_id, "asset_id": str(asset.get("_id")), "record_type": "CNAME", "record_value": value},
                {"$set": {"dangling": condition in ("dangling", "takeover_possible"),
                          "takeover_possible": takeover,
                          "takeover_provider": fp["provider"],
                          "takeover_status": condition,
                          "confidence": confidence,
                          "rule": rule_fired,
                          "takeover_evidence": detail,
                          "takeover_checked": now,
                          "updated_at": now}},
            )
            logger.info("Takeover check: %s -> %s (%s, confidence=%s)", hostname, condition, fp["provider"], confidence)

    return detections


LEVEL_FOR_CONDITION = {"dangling": "medium", "takeover_possible": "high"}
