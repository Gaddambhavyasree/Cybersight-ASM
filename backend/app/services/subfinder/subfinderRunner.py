import asyncio
import logging
import shutil
import subprocess
import os
from app.services.subfinder.subfinderParser import parse_subfinder_output

logger = logging.getLogger(__name__)

GO_BIN = os.path.expanduser(r"~\go\bin")
TOOLS_DIR = os.path.expanduser(r"~\tools")

FREE_SOURCES = [
    "crtsh", "rapiddns", "threatcrowd", "anubis", "sitedossier",
]


def _find_subfinder() -> str | None:
    for name in ["subfinder.exe", "subfinder"]:
        found = shutil.which(name)
        if found:
            return found

    for path in [
        os.path.join(GO_BIN, "subfinder.exe"),
        os.path.join(TOOLS_DIR, "subfinder.exe"),
    ]:
        if os.path.isfile(path):
            return path

    return None


def _run_subfinder_sync(domain: str, subfinder: str, timeout: int) -> dict:
    command = [subfinder, "-d", domain, "-silent", "-s", ",".join(FREE_SOURCES)]

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
            domains = parse_subfinder_output(stdout)
            logger.info(f"subfinder completed for {domain}: {len(domains)} subdomains found")
            return {
                "status": "success",
                "message": "subfinder completed successfully",
                "output": stdout,
                "domains": domains,
            }
        else:
            error_detail = stderr or f"exit code {result.returncode}"
            logger.error(f"subfinder failed: {error_detail}")
            return {
                "status": "error",
                "message": f"subfinder failed: {error_detail}",
                "output": stderr,
                "domains": [],
            }

    except subprocess.TimeoutExpired:
        logger.error(f"subfinder timed out after {timeout}s for domain: {domain}")
        return {
            "status": "error",
            "message": f"subfinder timed out after {timeout} seconds",
            "output": "",
            "domains": [],
        }

    except FileNotFoundError:
        msg = f"subfinder executable not found at: {subfinder}"
        logger.error(msg)
        return {"status": "error", "message": msg, "output": "", "domains": []}

    except Exception as e:
        msg = f"subfinder error: {type(e).__name__}: {e}" if str(e) else f"subfinder error: {type(e).__name__}"
        logger.error(msg)
        return {"status": "error", "message": msg, "output": "", "domains": []}


async def run_subfinder(domain: str, timeout: int = 120) -> dict:
    logger.info(f"Running subfinder for domain: {domain}")

    subfinder = _find_subfinder()
    if not subfinder:
        msg = "subfinder not found. Install: go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
        logger.error(msg)
        return {"status": "error", "message": msg, "output": "", "domains": []}

    logger.info(f"Using subfinder at: {subfinder}")

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(_run_subfinder_sync, domain, subfinder, timeout),
            timeout=timeout + 10,
        )
        return result
    except asyncio.TimeoutError:
        logger.error(f"subfinder execution timed out for domain: {domain}")
        return {
            "status": "error",
            "message": "subfinder execution timed out",
            "output": "",
            "domains": [],
        }
