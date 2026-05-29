"""Login portal + API surface detection from HTML/paths. Pure."""
from __future__ import annotations

import re

_PASSWORD_FIELD = re.compile(r"""<input[^>]*type\s*=\s*["']password["']""", re.IGNORECASE)
_FORM = re.compile(r"<form\b", re.IGNORECASE)

_LOGIN_HINTS = ("login", "signin", "sign-in", "auth", "sso", "iniciar sesi", "acceso", "entrar")

# Safe, well-known paths to probe (NO fuzzing, NO brute force)
SAFE_PROBE_PATHS = [
    "/robots.txt",
    "/sitemap.xml",
    "/login",
    "/admin",
    "/api",
    "/swagger",
    "/swagger.json",
    "/openapi.json",
    "/graphql",
    "/.well-known/security.txt",
    "/.well-known/openid-configuration",
]

API_SURFACE_PATHS = {"/api", "/swagger", "/swagger.json", "/openapi.json", "/graphql"}


def has_password_field(html: str) -> bool:
    return bool(_PASSWORD_FIELD.search(html or ""))


def looks_like_login(url: str, html: str) -> bool:
    low_url = url.lower()
    if any(h in low_url for h in _LOGIN_HINTS):
        return True
    if has_password_field(html) and _FORM.search(html or ""):
        return True
    low_html = (html or "").lower()
    return has_password_field(html) and any(h in low_html for h in _LOGIN_HINTS)


def is_api_surface(path: str) -> bool:
    return path.rstrip("/") in {p.rstrip("/") for p in API_SURFACE_PATHS}
