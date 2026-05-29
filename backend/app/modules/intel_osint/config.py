"""Intel OSINT configuration — env-driven with safe defaults.

All limits exist to keep collection passive and bounded. No aggressive
scanning, no fuzzing, no brute force. Timeouts + rate limits everywhere.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _b(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _i(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class IntelConfig:
    max_results_per_collector: int = _i("INTEL_MAX_RESULTS_PER_COLLECTOR", 100)
    http_timeout: int = _i("INTEL_HTTP_TIMEOUT", 10)
    max_crawl_pages: int = _i("INTEL_MAX_CRAWL_PAGES", 100)
    max_crawl_depth: int = _i("INTEL_MAX_CRAWL_DEPTH", 2)
    max_document_size_mb: int = _i("INTEL_MAX_DOCUMENT_SIZE_MB", 10)
    enable_document_download: bool = _b("INTEL_ENABLE_DOCUMENT_DOWNLOAD", True)
    enable_github: bool = _b("INTEL_ENABLE_GITHUB", True)
    enable_spanish_public_records: bool = _b("INTEL_ENABLE_SPANISH_PUBLIC_RECORDS", True)
    enable_social: bool = _b("INTEL_ENABLE_SOCIAL", True)
    enable_news: bool = _b("INTEL_ENABLE_NEWS", True)
    enable_leaks: bool = _b("INTEL_ENABLE_LEAKS", False)
    search_provider: str = os.environ.get("INTEL_SEARCH_PROVIDER", "disabled")
    search_api_key: str = os.environ.get("INTEL_SEARCH_API_KEY", "")
    github_token: str = os.environ.get("GITHUB_TOKEN", "")
    user_agent: str = os.environ.get("INTEL_USER_AGENT", "OctopusIntelligence/0.1")
    rate_limit_per_domain: int = _i("INTEL_RATE_LIMIT_PER_DOMAIN", 1)

    @property
    def max_document_size_bytes(self) -> int:
        return self.max_document_size_mb * 1024 * 1024


def get_intel_config() -> IntelConfig:
    return IntelConfig()
