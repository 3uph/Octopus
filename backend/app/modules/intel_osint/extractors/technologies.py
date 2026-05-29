"""Technology / cloud / SaaS provider detection from HTML, headers, DNS. Pure."""
from __future__ import annotations

import re

# signal -> (technology, category). Matched case-insensitively as substring.
_SIGNATURES: dict[str, tuple[str, str]] = {
    # web frameworks / servers
    "x-powered-by: php": ("PHP", "web"),
    "x-aspnet-version": ("ASP.NET", "web"),
    "x-drupal": ("Drupal", "web"),
    "wp-content": ("WordPress", "web"),
    "wp-json": ("WordPress", "web"),
    "/_next/": ("Next.js", "web"),
    "__nuxt": ("Nuxt", "web"),
    "ng-version": ("Angular", "web"),
    "react": ("React", "web"),
    "server: nginx": ("nginx", "web"),
    "server: apache": ("Apache", "web"),
    "server: microsoft-iis": ("IIS", "web"),
    # cloud / cdn
    "cloudflare": ("Cloudflare", "cloud"),
    "x-amz-": ("AWS", "cloud"),
    "amazonaws.com": ("AWS", "cloud"),
    "x-azure-ref": ("Azure", "cloud"),
    "azurewebsites.net": ("Azure", "cloud"),
    "windows-azure": ("Azure", "cloud"),
    "googleusercontent.com": ("GCP", "cloud"),
    "x-goog-": ("GCP", "cloud"),
    "akamai": ("Akamai", "cloud"),
    "fastly": ("Fastly", "cloud"),
    # SaaS / identity
    "outlook.com": ("Microsoft 365", "saas"),
    "protection.outlook.com": ("Microsoft 365", "saas"),
    "sharepoint.com": ("SharePoint", "saas"),
    "okta.com": ("Okta", "saas"),
    "auth0.com": ("Auth0", "saas"),
    "login.microsoftonline.com": ("Entra ID", "saas"),
    "salesforce.com": ("Salesforce", "saas"),
    "service-now.com": ("ServiceNow", "saas"),
    "atlassian.net": ("Atlassian", "saas"),
    "zendesk.com": ("Zendesk", "saas"),
    "powerbi.com": ("Power BI", "saas"),
    # devops / repos
    "github.com": ("GitHub", "repository"),
    "gitlab": ("GitLab", "repository"),
    "jenkins": ("Jenkins", "repository"),
    "kubernetes": ("Kubernetes", "cloud"),
    "x-kubernetes": ("Kubernetes", "cloud"),
}


def detect_technologies(haystack: str) -> list[tuple[str, str]]:
    """Return unique (technology, category) tuples detected in haystack."""
    low = (haystack or "").lower()
    found: dict[str, str] = {}
    for sig, (tech, cat) in _SIGNATURES.items():
        if sig in low:
            found[tech] = cat
    return sorted(found.items())


def detect_from_dns(records: dict[str, list[str]]) -> list[tuple[str, str]]:
    """Infer providers from DNS records (MX/TXT/CNAME/NS)."""
    blob = " ".join(
        v for key in ("MX", "TXT", "CNAME", "NS") for v in records.get(key, [])
    )
    return detect_technologies(blob)
