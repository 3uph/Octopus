"""Abstract ToolRunner base class.

ALL tool execution in Octopus must go through a subclass of ToolRunner.
Key security properties enforced here:
- shell=True is NEVER used
- Commands are always constructed as lists, never concatenated strings
- Binary name must be in the allowlist before execution
- Targets must pass sanitization before any command is built
- Execution is sandboxed with timeout and output size limits

Only the worker service may call run(). The API never calls run() directly.
"""
from __future__ import annotations

import abc
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from .allowlist import assert_binary_allowed
from .sanitizer import sanitize_targets
from .types import RawOutput, ReconMode, Target, ToolRunPlan

logger = get_logger(__name__)

# Safety limits
_DEFAULT_TIMEOUT_S = 300          # 5 minutes per tool run
_MAX_OUTPUT_BYTES = 50 * 1024 * 1024  # 50 MB


class ToolRunnerError(Exception):
    """Base error for tool runner failures."""


class ToolExecutionError(ToolRunnerError):
    """Raised when the tool exits with a non-zero code."""


class OutputSizeLimitError(ToolRunnerError):
    """Raised when tool output exceeds the size limit."""


class ToolRunner(abc.ABC):
    """Abstract base for all tool runners.

    Subclass responsibility:
    - Implement _build_args() to return the argument list for the binary.
    - Implement parse() to normalize raw output into records.
    - Never use shell=True.
    - Never build commands from string concatenation with user input.
    """

    #: Subclasses MUST set this to a key in ALLOWED_BINARIES
    binary_name: str

    def __init__(
        self,
        timeout_s: int = _DEFAULT_TIMEOUT_S,
        max_output_bytes: int = _MAX_OUTPUT_BYTES,
    ) -> None:
        self._timeout_s = timeout_s
        self._max_output_bytes = max_output_bytes
        # Validate allowlist at construction time, not at run time
        self._executable = assert_binary_allowed(self.binary_name)

    @abc.abstractmethod
    def _build_args(self, targets: list[Target], mode: ReconMode) -> list[str]:
        """Return the full argument list for the tool (excluding binary name).

        MUST return a list of strings. MUST NOT use shell=True or string concat.
        """

    @abc.abstractmethod
    def parse(self, raw: RawOutput) -> list[dict[str, Any]]:
        """Parse raw output file into normalized records."""

    def plan(
        self,
        targets: list[Target],
        mode: ReconMode,
        *,
        blocked_targets: list[Target] | None = None,
    ) -> ToolRunPlan:
        """Build and return the execution plan without running anything.

        Safe to call anytime — no network, no subprocess, no side effects.
        """
        clean_targets = sanitize_targets(targets)
        args = [self._executable] + self._build_args(clean_targets, mode)

        # Verify no shell characters crept into any arg
        for arg in args:
            if any(c in arg for c in (";", "&&", "||", "|", "`", "$(")):
                raise ToolRunnerError(
                    f"Shell metacharacter detected in arg: {arg!r}"
                )

        return ToolRunPlan(
            tool_name=self.binary_name,
            targets=clean_targets,
            args=args,
            mode=mode,
            blocked_targets=blocked_targets or [],
            dry_run_description=(
                f"Would run: {' '.join(args[:3])}... "
                f"against {len(clean_targets)} targets in {mode} mode"
            ),
        )

    def run(self, plan: ToolRunPlan) -> RawOutput:
        """Execute the planned command. ONLY called from worker service.

        Never uses shell=True. Args come from plan() which sanitized targets.
        """
        if plan.mode == ReconMode.DRY_RUN:
            raise ToolRunnerError("Cannot run() in DRY_RUN mode — use plan() only.")

        logger.info(
            "Executing %s (mode=%s, targets=%d)",
            self.binary_name,
            plan.mode.value,
            len(plan.targets),
        )

        out_dir = Path(tempfile.mkdtemp(prefix=f"octopus_{self.binary_name}_"))
        stdout_path = out_dir / "stdout.txt"
        stderr_path = out_dir / "stderr.txt"

        with stdout_path.open("wb") as stdout_f, stderr_path.open("wb") as stderr_f:
            try:
                result = subprocess.run(  # noqa: S603 — intentional, no shell
                    plan.args,
                    stdout=stdout_f,
                    stderr=stderr_f,
                    timeout=self._timeout_s,
                    shell=False,  # explicit — never True
                    check=False,
                )
            except subprocess.TimeoutExpired:
                raise ToolRunnerError(
                    f"{self.binary_name} timed out after {self._timeout_s}s"
                )
            except FileNotFoundError:
                raise ToolRunnerError(
                    f"Binary not found in PATH: {self._executable}"
                )

        # Enforce output size limit
        size = stdout_path.stat().st_size
        if size > self._max_output_bytes:
            raise OutputSizeLimitError(
                f"Output size {size} exceeds limit {self._max_output_bytes}"
            )

        return RawOutput(
            path=stdout_path,
            tool_name=self.binary_name,
            exit_code=result.returncode,
            stdout_lines=sum(1 for _ in stdout_path.open()),
            stderr_path=stderr_path,
        )
