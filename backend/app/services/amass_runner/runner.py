"""Amass passive-mode subdomain enumeration runner.

Optional second source for Asset Discovery: mirrors the Subfinder runner's
contract ({"status", "message", "output", "domains"}). If the ``amass``
executable is not installed the runner reports a graceful error and the
discovery stage simply continues with Subfinder results.
"""

import asyncio
import logging
import os
import re
import shutil
import subprocess

logger = logging.getLogger(__name__)

GO_BIN = os.path.expanduser(r"~\go\bin")
TOOLS_DIR = os.path.expanduser(r"~\tools")

DOMAIN_LINE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)


def _find_amass() -> str | None:
    for name in ["amass.exe", "amass"]:
        found = shutil.which(name)
        if found and "python" not in found.lower():
            return found
    for path in [
        os.path.join(GO_BIN, "amass.exe"),
        os.path.join(TOOLS_DIR, "amass.exe"),
    ]:
        if os.path.isfile(path):
            return path
    return None


def _parse_amass_output(output: str, target: str) -> list[str]:
    """Amass passive output is one host per line (with tabs in verbose mode)."""
    target = (target or "").lower().strip(".")
    domains: list[str] = []
    for line in output.splitlines():
        host = line.strip().lower().split("\t")[0].split(" ")[0]
        if not host or host.startswith("#"):
            continue
        if DOMAIN_LINE.match(host) and (host == target or host.endswith("." + target)):
            domains.append(host)
    return domains


def _run_amass_sync(domain: str, amass: str, timeout: int) -> dict:
    # Passive mode only: OSINT lookups, no active DNS/edge probing against the target.
    command = [amass, "enum", "-d", domain, "-passive", "-silent"]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode == 0:
            domains = _parse_amass_output(stdout, domain)
            logger.info("amass completed for %s: %d subdomains found", domain, len(domains))
            return {
                "status": "success",
                "message": "amass completed successfully",
                "output": stdout,
                "domains": domains,
            }
        if "unknown command" in stderr.lower() and "passive" not in stderr.lower():
            return {"status": "error", "message": f"amass failed: {stderr[:300]}", "output": stderr, "domains": []}
        error_detail = stderr or f"exit code {result.returncode}"
        logger.warning("amass reported failure for %s: %s", domain, error_detail[:300])
        return {
            "status": "error",
            "message": f"amass failed: {error_detail[:300]}",
            "output": stderr,
            "domains": [],
        }

    except subprocess.TimeoutExpired:
        logger.warning("amass timed out after %ss (results so far are ignored)", timeout)
        return {"status": "error", "message": f"amass timed out after {timeout} seconds", "output": "", "domains": []}
    except FileNotFoundError:
        return {"status": "error", "message": "amass executable disappeared during scan", "output": "", "domains": []}
    except Exception as e:
        logger.error("amass error: %s: %s", type(e).__name__, e)
        return {"status": "error", "message": f"amass error: {type(e).__name__}", "output": "", "domains": []}


async def run_amass(domain: str, timeout: int = 240) -> dict:
    amass = _find_amass()
    if not amass:
        return {
            "status": "error",
            "message": "amass not found (install: go install -v github.com/owasp-amass/amass/v4/cmd/amass@latest)",
            "output": "",
            "domains": [],
        }
    logger.info("Running amass (passive) for domain: %s at %s", domain, amass)
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(_run_amass_sync, domain, amass, timeout),
            timeout=timeout + 10,
        )
        return result
    except asyncio.TimeoutError:
        logger.warning("amass execution timed out for domain: %s", domain)
        return {"status": "error", "message": "amass execution timed out", "output": "", "domains": []}
