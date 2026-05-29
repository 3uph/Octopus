"""OCT-001: Verify monorepo folder structure and module READMEs exist."""
import os
from pathlib import Path

def _repo_root() -> Path:
    """Find repo root by walking up from this file until 'backend' + 'docs' exist.

    Computed at call time (not import) and marker-based, so it is immune to
    CWD changes or env mutations from other tests.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "backend").is_dir() and (parent / "docs").is_dir():
            return parent
    return here.parent.parent.parent


def _exists(rel: str) -> bool:
    return (_repo_root() / rel).exists()


ROOT = _repo_root()


REQUIRED_DIRS = [
    "backend/app/core/config",
    "backend/app/core/security",
    "backend/app/core/logging",
    "backend/app/core/permissions",
    "backend/app/api/routes",
    "backend/app/api/dependencies",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/services",
    "backend/app/utils",
    "backend/app/modules/companies",
    "backend/app/modules/programs",
    "backend/app/modules/audits",
    "backend/app/modules/scope_parser",
    "backend/app/modules/scope_gate",
    "backend/app/modules/discovery",
    "backend/app/modules/dns",
    "backend/app/modules/http_probe",
    "backend/app/modules/crawling",
    "backend/app/modules/js_analysis",
    "backend/app/modules/scanning",
    "backend/app/modules/prioritization",
    "backend/app/modules/intelligence",
    "backend/app/modules/ai",
    "backend/app/modules/reporting",
    "backend/app/modules/evidence",
    "backend/app/modules/integrations",
    "backend/app/workers/jobs",
    "backend/app/workers/queues",
    "backend/app/workers/schedules",
    "backend/app/tool_runners/base",
    "backend/app/tool_runners/projectdiscovery",
    "backend/app/tool_runners/tomnomnom",
    "backend/app/tool_runners/scanners",
    "backend/app/tool_runners/secrets",
    "backend/app/tool_runners/screenshots",
    "backend/app/database/migrations/versions",
    "backend/app/database/repositories",
    "frontend/src/app",
    "frontend/src/components/ui",
    "frontend/src/components/layout",
    "frontend/src/components/tables",
    "frontend/src/components/forms",
    "frontend/src/components/charts",
    "frontend/src/features/companies",
    "frontend/src/features/programs",
    "frontend/src/features/audits",
    "frontend/src/features/scope",
    "frontend/src/features/assets",
    "frontend/src/features/intelligence",
    "frontend/src/features/recon",
    "frontend/src/features/jobs",
    "frontend/src/features/dashboard",
    "frontend/src/features/findings",
    "frontend/src/features/evidence",
    "frontend/src/features/settings",
    "prompts/scope_parser",
    "prompts/recon_summary",
    "prompts/js_analysis",
    "prompts/intelligence/company_summary",
    "prompts/intelligence/hunting_hypotheses",
    "infra/docker",
    "infra/compose",
    "infra/scripts",
    "docs/decisions",
]

MODULE_READMES = [
    "backend/app/modules/companies/README.md",
    "backend/app/modules/programs/README.md",
    "backend/app/modules/audits/README.md",
    "backend/app/modules/scope_parser/README.md",
    "backend/app/modules/scope_gate/README.md",
    "backend/app/modules/discovery/README.md",
    "backend/app/modules/dns/README.md",
    "backend/app/modules/http_probe/README.md",
    "backend/app/modules/crawling/README.md",
    "backend/app/modules/js_analysis/README.md",
    "backend/app/modules/scanning/README.md",
    "backend/app/modules/prioritization/README.md",
    "backend/app/modules/intelligence/README.md",
    "backend/app/modules/ai/README.md",
    "backend/app/modules/reporting/README.md",
    "backend/app/modules/evidence/README.md",
    "backend/app/modules/integrations/README.md",
    "backend/app/tool_runners/base/README.md",
    "backend/app/tool_runners/projectdiscovery/README.md",
    "backend/app/tool_runners/tomnomnom/README.md",
    "backend/app/tool_runners/scanners/README.md",
    "backend/app/tool_runners/secrets/README.md",
    "backend/app/tool_runners/screenshots/README.md",
]

ADRS = [
    "docs/decisions/ADR-001-dramatiq-job-framework.md",
    "docs/decisions/ADR-002-nextjs-frontend.md",
    "docs/decisions/ADR-003-sqlalchemy-alembic.md",
    "docs/decisions/ADR-004-multi-tenant-column.md",
    "docs/decisions/ADR-005-llm-provider-abstract.md",
]


def test_required_dirs_exist():
    missing = [d for d in REQUIRED_DIRS if not _exists(d)]
    assert not missing, f"Missing dirs: {missing}"


def test_module_readmes_exist():
    missing = [f for f in MODULE_READMES if not _exists(f)]
    assert not missing, f"Missing READMEs: {missing}"


def test_module_readmes_not_empty():
    for rel in MODULE_READMES:
        p = ROOT / rel
        assert p.exists(), f"Missing: {rel}"
        assert p.stat().st_size > 10, f"README too small (empty?): {rel}"


def test_adrs_exist():
    missing = [f for f in ADRS if not _exists(f)]
    assert not missing, f"Missing ADRs: {missing}"


def test_gitignore_exists():
    assert _exists(".gitignore"), "Missing .gitignore"


def test_implementation_rules_exist():
    assert _exists("docs/development_guidelines/IMPLEMENTATION_RULES.md")
