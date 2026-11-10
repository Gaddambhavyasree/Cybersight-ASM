import logging

logger = logging.getLogger(__name__)


def parse_subfinder_output(output: str) -> list[str]:
    if not output:
        return []

    domains = []
    for line in output.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "." in line:
            domains.append(line.lower())

    return domains


def deduplicate_domains(domains: list[str]) -> list[str]:
    seen = set()
    unique = []
    for domain in domains:
        if domain not in seen:
            seen.add(domain)
            unique.append(domain)
    return unique


def validate_domain(domain: str) -> bool:
    if not domain or len(domain) > 253:
        return False
    if "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False
    return True


def clean_domains(raw_domains: list[str]) -> list[str]:
    validated = [d for d in raw_domains if validate_domain(d)]
    return deduplicate_domains(validated)
