import json
import logging
import os
import shutil
import subprocess
from datetime import datetime

logger = logging.getLogger(__name__)

GO_BIN = os.path.expanduser(r"~\go\bin")
TOOLS_DIR = os.path.expanduser(r"~\tools")


def _find_httpx() -> str | None:
    for name in ["httpx.exe", "httpx"]:
        found = shutil.which(name)
        if found:
            path = found
            if "Python" not in path and "python" not in path.lower():
                return path

    for path in [
        os.path.join(GO_BIN, "httpx.exe"),
        os.path.join(TOOLS_DIR, "httpx.exe"),
    ]:
        if os.path.isfile(path):
            return path

    return None


def run_httpx_single(hostname: str, httpx_path: str, timeout: int = 15) -> dict:
    command = [
        httpx_path,
        "-u", hostname,
        "-json",
        "-silent",
        "-follow-redirects",
        "-timeout", str(timeout),
        "-no-color",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout + 10,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        stdout = result.stdout.strip()

        if result.returncode == 0 and stdout:
            for line in stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    return _parse_httpx_json(hostname, data)
                except json.JSONDecodeError:
                    continue

        return _offline_result(hostname)

    except subprocess.TimeoutExpired:
        logger.warning(f"httpx timed out for {hostname}")
        return _offline_result(hostname)

    except FileNotFoundError:
        raise

    except Exception as e:
        logger.warning(f"httpx error for {hostname}: {e}")
        return _offline_result(hostname)


def run_httpx_technology_single(hostname: str, httpx_path: str, timeout: int = 60) -> list[dict]:
    """Run HTTPX technology detection with a hard subprocess deadline."""
    command = [
        httpx_path, "-u", hostname, "-json", "-silent", "-tech-detect",
        "-cdn", "-server", "-follow-redirects", "-no-color",
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode != 0:
            logger.warning("httpx technology detection failed for %s: %s", hostname, result.stderr.strip())
            return []
        found = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            try:
                found.extend(_parse_technology_json(hostname, json.loads(line)))
            except json.JSONDecodeError:
                logger.warning("Invalid HTTPX technology JSON for %s", hostname)
        return found
    except subprocess.TimeoutExpired:
        logger.warning("httpx technology detection timed out for %s", hostname)
        return []
    except FileNotFoundError:
        raise
    except Exception:
        logger.exception("httpx technology detection error for %s", hostname)
        return []


def _parse_technology_json(hostname: str, data: dict) -> list[dict]:
    values = []
    for key, category in (("webserver", "Web Server"), ("cdn", "CDN"), ("framework", "Framework"),
                          ("language", "Programming Language"), ("cms", "CMS"),
                          ("reverse_proxy", "Reverse Proxy"), ("os", "Operating System")):
        value = data.get(key)
        if value:
            values.extend(_technology_values(value, category))
    for value in data.get("technologies", data.get("tech", [])) or []:
        if isinstance(value, dict):
            values.append({"name": str(value.get("name") or value.get("technology") or "").strip(),
                           "category": value.get("category") or "Technology",
                           "version": value.get("version")})
        elif value:
            values.append({"name": str(value).strip(), "category": "Technology", "version": None})
    # Some HTTPX versions return a technology map instead of categorized fields.
    for value in data.get("tech-detect", []) or []:
        values.extend(_technology_values(value, "Technology"))
    return [{**item, "hostname": hostname, "confidence": 1.0} for item in values if item.get("name")]


def _technology_values(value, category: str) -> list[dict]:
    items = value if isinstance(value, list) else [value]
    result = []
    for item in items:
        if isinstance(item, dict):
            name = item.get("name") or item.get("technology") or item.get("value")
            version = item.get("version")
        else:
            name, version = str(item), None
        if name:
            result.append({"name": str(name).strip(), "category": category, "version": version})
    return result

def _parse_httpx_json(hostname: str, data: dict) -> dict:
    status_code = data.get("status_code")
    scheme = data.get("scheme", "http")
    port = data.get("port")

    final_url = data.get("final_url", "")
    if not final_url:
        port_str = f":{port}" if port and port not in (80, 443) else ""
        final_url = f"{scheme}://{hostname}{port_str}"

    tls = data.get("tls", {})
    certificate = data.get("certificate", {})

    ip_raw = data.get("ip", "")
    if not ip_raw:
        ip_raw = data.get("a", [""])
        if isinstance(ip_raw, list):
            ip_raw = ip_raw[0] if ip_raw else ""

    return {
        "hostname": hostname,
        "ip": ip_raw or None,
        "http_status": status_code,
        "https_enabled": scheme == "https",
        "final_url": final_url,
        "page_title": _clean_title(data.get("title", "")),
        "web_server": data.get("webserver", "") or None,
        "content_length": data.get("content_length"),
        "response_time": data.get("response_time", {}).get("seconds") if isinstance(data.get("response_time"), dict) else None,
        "redirect_location": _extract_redirect(data),
        "is_live": True,
        "last_http_check": datetime.utcnow(),
    }


def _extract_redirect(data: dict) -> str | None:
    location = data.get("location", "")
    if location:
        return location

    final_url = data.get("final_url", "")
    input_url = data.get("url", "") or data.get("input", "")
    if final_url and input_url and final_url != input_url:
        return final_url

    return None


def _clean_title(title: str) -> str | None:
    if not title:
        return None
    return title.strip()[:500]


def _offline_result(hostname: str) -> dict:
    return {
        "hostname": hostname,
        "ip": None,
        "http_status": None,
        "https_enabled": False,
        "final_url": None,
        "page_title": None,
        "web_server": None,
        "content_length": None,
        "response_time": None,
        "redirect_location": None,
        "is_live": False,
        "last_http_check": datetime.utcnow(),
    }
