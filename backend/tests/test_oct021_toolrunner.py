"""OCT-021: ToolRunner base — injection tests, allowlist, sanitization.

These are the most security-critical tests in the project.
No network calls, no subprocess execution of real tools.
"""
from __future__ import annotations

import pytest
from typing import Any

from app.tool_runners.base import (
    ALLOWED_BINARIES,
    BinaryNotAllowedError,
    RawOutput,
    ReconMode,
    Target,
    TargetKind,
    TargetSanitizationError,
    ToolRunPlan,
    ToolRunner,
    ToolRunnerError,
    assert_binary_allowed,
    sanitize_target,
    sanitize_targets,
)
from app.tool_runners.base.sanitizer import (
    sanitize_cidr,
    sanitize_domain,
    sanitize_ip,
    sanitize_url,
)


# ---------------------------------------------------------------------------
# Minimal concrete ToolRunner for testing (never executes real binary)
# ---------------------------------------------------------------------------

class _EchoRunner(ToolRunner):
    binary_name = "subfinder"  # in allowlist

    def _build_args(self, targets: list[Target], mode: ReconMode) -> list[str]:
        return ["-d", targets[0].value, "-silent"] if targets else ["-silent"]

    def parse(self, raw: RawOutput) -> list[dict[str, Any]]:
        return []


# ---------------------------------------------------------------------------
# Injection tests — the core security requirement of OCT-021
# ---------------------------------------------------------------------------

INJECTION_PAYLOADS_DOMAIN = [
    "; rm -rf /",
    "&& cat /etc/passwd",
    "| id",
    "`whoami`",
    "$(reboot)",
    "evil\ncommand",
    "evil\rcommand",
    "evil\x00null",
    "evil\ttab",
    "a" * 2049,  # too long
    "evil domain",  # space in domain
    "--flag",  # flag injection
    "-flag",
    "../../etc/passwd",
    "evil;more",
    "evil&&more",
    "evil||more",
    "evil>file",
    "evil<file",
    "evil\\path",
    "${IFS}cat",
    "%(HELO)s",
    "' OR '1'='1",
    'evil"quote',
]

INJECTION_PAYLOADS_URL = [
    "javascript:alert(1)",
    "ftp://evil.com",
    "file:///etc/passwd",
    "data:text/html,<script>",
    "; rm -rf /",
    "http://",  # no host
    "//evil",   # no scheme
    "",
]


class TestDomainSanitizer:
    @pytest.mark.parametrize("payload", INJECTION_PAYLOADS_DOMAIN)
    def test_rejects_injection_payload(self, payload: str):
        with pytest.raises((TargetSanitizationError, ValueError)):
            sanitize_domain(payload)

    def test_accepts_valid_domain(self):
        assert sanitize_domain("example.com") == "example.com"

    def test_accepts_subdomain(self):
        assert sanitize_domain("api.example.com") == "api.example.com"

    def test_lowercases(self):
        assert sanitize_domain("EXAMPLE.COM") == "example.com"

    def test_accepts_wildcard_domain(self):
        result = sanitize_domain("*.example.com")
        assert "example.com" in result

    def test_rejects_empty(self):
        with pytest.raises(TargetSanitizationError):
            sanitize_domain("")

    def test_rejects_single_dot(self):
        with pytest.raises(TargetSanitizationError):
            sanitize_domain(".")


class TestIPSanitizer:
    def test_accepts_valid_ipv4(self):
        assert sanitize_ip("192.168.1.1") == "192.168.1.1"

    def test_accepts_valid_ipv6(self):
        assert sanitize_ip("::1") == "::1"

    def test_rejects_injection(self):
        with pytest.raises(TargetSanitizationError):
            sanitize_ip("192.168.1.1; rm -rf /")

    def test_rejects_not_an_ip(self):
        with pytest.raises(TargetSanitizationError):
            sanitize_ip("not.an.ip")


class TestCIDRSanitizer:
    def test_accepts_valid_cidr(self):
        assert sanitize_cidr("10.0.0.0/8") == "10.0.0.0/8"

    def test_rejects_injection(self):
        with pytest.raises(TargetSanitizationError):
            sanitize_cidr("10.0.0.0/8; evil")

    def test_rejects_invalid(self):
        with pytest.raises(TargetSanitizationError):
            sanitize_cidr("not-a-cidr")


class TestURLSanitizer:
    @pytest.mark.parametrize("payload", INJECTION_PAYLOADS_URL)
    def test_rejects_bad_urls(self, payload: str):
        with pytest.raises((TargetSanitizationError, ValueError)):
            sanitize_url(payload)

    def test_accepts_http(self):
        assert sanitize_url("http://example.com") == "http://example.com"

    def test_accepts_https(self):
        assert sanitize_url("https://api.example.com/path") == "https://api.example.com/path"


class TestAllowlist:
    def test_known_binary_allowed(self):
        exe = assert_binary_allowed("subfinder")
        assert exe == "subfinder"

    def test_unknown_binary_rejected(self):
        with pytest.raises(BinaryNotAllowedError):
            assert_binary_allowed("definitely_not_a_real_tool_xyz")

    def test_curl_not_allowed(self):
        with pytest.raises(BinaryNotAllowedError):
            assert_binary_allowed("curl")

    def test_wget_not_allowed(self):
        with pytest.raises(BinaryNotAllowedError):
            assert_binary_allowed("wget")

    def test_sh_not_allowed(self):
        with pytest.raises(BinaryNotAllowedError):
            assert_binary_allowed("sh")

    def test_bash_not_allowed(self):
        with pytest.raises(BinaryNotAllowedError):
            assert_binary_allowed("bash")

    def test_python_not_allowed(self):
        with pytest.raises(BinaryNotAllowedError):
            assert_binary_allowed("python")


class TestRunnerPlan:
    def setup_method(self):
        self.runner = _EchoRunner()

    def test_plan_returns_plan_object(self):
        targets = [Target("example.com", TargetKind.DOMAIN)]
        plan = self.runner.plan(targets, ReconMode.PASSIVE)
        assert isinstance(plan, ToolRunPlan)

    def test_plan_args_is_list(self):
        targets = [Target("example.com", TargetKind.DOMAIN)]
        plan = self.runner.plan(targets, ReconMode.PASSIVE)
        assert isinstance(plan.args, list)
        assert all(isinstance(a, str) for a in plan.args)

    def test_plan_no_shell_metacharacters_in_args(self):
        targets = [Target("example.com", TargetKind.DOMAIN)]
        plan = self.runner.plan(targets, ReconMode.PASSIVE)
        for arg in plan.args:
            assert ";" not in arg
            assert "&&" not in arg
            assert "`" not in arg
            assert "$(" not in arg

    def test_plan_dry_run_allowed(self):
        targets = [Target("example.com", TargetKind.DOMAIN)]
        plan = self.runner.plan(targets, ReconMode.DRY_RUN)
        assert plan.mode == ReconMode.DRY_RUN

    def test_run_in_dry_run_raises(self):
        targets = [Target("example.com", TargetKind.DOMAIN)]
        plan = self.runner.plan(targets, ReconMode.DRY_RUN)
        with pytest.raises(ToolRunnerError):
            self.runner.run(plan)

    def test_plan_rejects_malicious_target(self):
        with pytest.raises(TargetSanitizationError):
            targets = [Target("; rm -rf /", TargetKind.DOMAIN)]
            self.runner.plan(targets, ReconMode.PASSIVE)


class TestNoShellTrue:
    """Verify shell=True is never used in actual subprocess calls."""

    def _find_shell_true_calls(self, module) -> list[str]:
        """Use AST to find any Call where keyword shell=True is passed."""
        import ast, inspect, textwrap
        source = inspect.getsource(module)
        tree = ast.parse(textwrap.dedent(source))
        violations = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant):
                    if kw.value.value is True:
                        violations.append(f"line {node.lineno}: shell=True in call")
        return violations

    def test_runner_py_no_shell_true_in_calls(self):
        from app.tool_runners.base import runner as runner_mod
        violations = self._find_shell_true_calls(runner_mod)
        assert not violations, f"shell=True in subprocess call: {violations}"

    def test_sanitizer_py_no_shell_true(self):
        from app.tool_runners.base import sanitizer as san_mod
        violations = self._find_shell_true_calls(san_mod)
        assert not violations, f"shell=True found: {violations}"

    def test_runner_explicitly_uses_shell_false(self):
        import inspect
        from app.tool_runners.base import runner as runner_mod
        source = inspect.getsource(runner_mod)
        assert "shell=False" in source
