import json
import logging
import os
import shutil
import subprocess
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

GO_BIN = os.path.expanduser(r"~\go\bin")
TOOLS_DIR = os.path.expanduser(r"~\tools")


def _find_naabu() -> str | None:
    for name in ["naabu.exe", "naabu"]:
        found = shutil.which(name)
        if found:
            path = found
            if "Python" not in path and "python" not in path.lower():
                logger.info(f"Found naabu at: {path}")
                return path

    for path in [
        os.path.join(GO_BIN, "naabu.exe"),
        os.path.join(TOOLS_DIR, "naabu.exe"),
    ]:
        if os.path.isfile(path):
            logger.info(f"Found naabu at: {path}")
            return path

    logger.warning("naabu not found")
    return None


def _run_naabu_sync(hostname: str, naabu_path: str, timeout: int) -> list[dict]:
    command = [
        naabu_path,
        "-host", hostname,
        "-json",
        "-silent",
        # Keep Naabu's own network timeout below the process timeout.  The
        # subprocess timeout remains the final, non-negotiable safety bound.
        "-timeout", str(min(timeout, 10)),
        "-rate", "1000",
        "-top-ports", "1000",
        "-no-color",
    ]

    logger.info(f"Running naabu command for {hostname}: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        logger.info(f"naabu return code for {hostname}: {result.returncode}")
        logger.debug(f"naabu stdout for {hostname}: {result.stdout}")
        if result.stderr:
            logger.debug(f"naabu stderr for {hostname}: {result.stderr}")

        stdout = result.stdout.strip()
        ports = []

        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, command, output=result.stdout, stderr=result.stderr
            )

        if stdout:
            for line in stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    parsed = _parse_naabu_json(hostname, data)
                    if parsed:
                        ports.append(parsed)
                except json.JSONDecodeError as exc:
                    logger.warning("Invalid naabu JSON for %s: %s", hostname, exc)
                    continue

        return ports

    except subprocess.TimeoutExpired:
        logger.warning(f"naabu timed out for {hostname}")
        return []

    except subprocess.CalledProcessError as exc:
        logger.warning(
            "naabu failed for %s with exit code %s: %s",
            hostname,
            exc.returncode,
            (exc.stderr or exc.output or "").strip(),
        )
        return []

    except FileNotFoundError:
        raise

    except Exception as e:
        logger.warning(f"naabu error for {hostname}: {e}")
        return []


async def run_naabu_single(hostname: str, naabu_path: str, timeout: int = 60) -> list[dict]:
    return await asyncio.to_thread(_run_naabu_sync, hostname, naabu_path, timeout)


def _parse_naabu_json(hostname: str, data: dict) -> dict | None:
    port = data.get("port")
    if not port:
        return None

    protocol = data.get("protocol", "tcp")
    service = data.get("service", {}).get("name") if isinstance(data.get("service"), dict) else data.get("service")
    ip = data.get("ip")

    return {
        "hostname": hostname,
        "ip": ip,
        "port": port,
        "protocol": protocol,
        "state": "open",
        "service": service,
        "timestamp": datetime.utcnow(),
    }
