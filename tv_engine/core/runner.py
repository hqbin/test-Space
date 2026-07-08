"""YAML test-case runner for the TV automation engine.

Orchestrates end-to-end execution of YAML-defined test cases:

- Parses YAML and resolves variable substitutions
- Executes setup / steps / teardown lifecycle
- Dispatches actions via a built-in registry
- Applies *on_failure* strategies (skip / abort / retry / ai_heal)
- Emits real-time JSON Lines to stdout for the Rust/Tauri frontend
- Delegates reporting to :class:`Reporter` and AI healing to :class:`Healer`
"""

import copy
import json
import sys
import time
import uuid
import logging
import traceback
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

from .device import DeviceController
from .reporter import Reporter
from .reporter import StepResult as RStepResult
from .reporter import CaseResult as RCaseResult
from .reporter import SuiteResult as RSuiteResult
from .healer import Healer

logger = logging.getLogger(__name__)

# ── Result containers (local to the runner) ────────────────────────────────


@dataclass
class StepResult:
    """Outcome of a single YAML step execution."""

    status: str = "running"  # passed | failed | healed | skipped
    step_id: str = ""
    desc: str = ""
    duration_ms: int = 0
    error: Optional[str] = None
    heal_log: Optional[dict] = None
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    locator_used: Optional[str] = None


@dataclass
class CaseResult:
    """Aggregated result for an entire YAML test case."""

    case_id: str = ""
    name: str = ""
    status: str = "running"  # passed | failed | aborted
    steps: list[StepResult] = field(default_factory=list)
    total: int = 0
    passed: int = 0
    failed: int = 0
    healed: int = 0
    skipped: int = 0
    duration_ms: int = 0
    error: Optional[str] = None


@dataclass
class SuiteResult:
    """Aggregated result for a suite of test cases."""

    run_id: str = ""
    status: str = "running"
    results: dict[str, CaseResult] = field(default_factory=dict)
    total: int = 0
    passed: int = 0
    failed: int = 0
    healed: int = 0
    skipped: int = 0
    duration_ms: int = 0
    started_at: str = ""
    ended_at: str = ""


# ── Simple action registry ─────────────────────────────────────────────────


class ActionRegistry:
    """Maps action names to handler callables.

    Handlers receive ``(device, step, context, timeout)`` keyword arguments.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[..., None]] = {}

    def register(self, name: str, handler: Callable[..., None]) -> None:
        self._handlers[name] = handler

    def get(self, name: str) -> Optional[Callable[..., None]]:
        return self._handlers.get(name)

    def load_builtins(self) -> None:
        """Register the standard TV automation actions.

        Action handler modules under ``tv_engine/actions/`` are imported
        lazily and silently skipped if they do not yet exist – this allows
        the runner to function even when the full set of action files has
        not been created.
        """
        _builtins: list[tuple[str, str, str]] = [
            ("press_key", "press_key", "handle_press_key"),
            ("press_key_sequence", "press_key", "handle_press_key_sequence"),
            ("navigate_to", "navigate", "handle_navigate_to"),
            ("wait_for", "wait", "handle_wait_for"),
            ("wait_stable", "wait", "handle_wait_stable"),
            ("wait_then_assert", "wait", "handle_wait_then_assert"),
            ("assert_focused", "assert_actions", "handle_assert_focused"),
            ("assert_app_foreground", "assert_actions", "handle_assert_app_foreground"),
            ("assert_element", "assert_actions", "handle_assert_element"),
            ("assert_visual", "assert_actions", "handle_assert_visual"),
            ("assert_shell", "assert_actions", "handle_assert_shell"),
            ("launch_app", "launch_app", "handle_launch_app"),
            ("screenshot", "screenshot", "handle_screenshot"),
            ("input_text", "input_text", "handle_input_text"),
            ("swipe", "swipe", "handle_swipe"),
            ("set_variable", "set_variable", "handle_set_variable"),
        ]
        for action_name, module_name, func_name in _builtins:
            try:
                mod = __import__(
                    f"tv_engine.actions.{module_name}",
                    fromlist=[func_name],
                )
                handler = getattr(mod, func_name, None)
                if handler is not None:
                    self.register(action_name, handler)
            except (ImportError, AttributeError):
                logger.debug("Action %s not available (module %s)", action_name, module_name)


# ── Runner ─────────────────────────────────────────────────────────────────


class TestRunner:
    """Core execution engine for YAML-based TV automation test cases.

    Parameters
    ----------
    device:
        Connected device controller instance.
    reporter:
        Report generator.
    healer:
        Optional AI healer for automatic failure remediation.
    """

    def __init__(
        self,
        device: DeviceController,
        reporter: Reporter,
        healer: Optional[Healer] = None,
    ):
        self.device = device
        self.reporter = reporter
        self.healer = healer
        self.registry = ActionRegistry()
        self.registry.load_builtins()
        self._stopped = False
        self._last_run_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_case(self, yaml_path: str, run_id: Optional[str] = None) -> CaseResult:
        """Load a YAML file from *yaml_path* and execute it.

        Parameters
        ----------
        yaml_path:
            Path to a ``.yaml`` / ``.yml`` file on disk.
        run_id:
            Unique run identifier.  Auto-generated if omitted.

        Returns
        -------
        CaseResult
        """
        path = Path(yaml_path)
        if not path.is_file():
            raise FileNotFoundError(f"YAML case file not found: {yaml_path}")
        yaml_content = path.read_text(encoding="utf-8")
        case_id = path.stem
        _run_id = run_id or str(uuid.uuid4())
        return self.run_case_from_content(yaml_content, case_id, _run_id)

    def run_case_from_content(
        self, yaml_content: str, case_id: str, run_id: str
    ) -> CaseResult:
        """Parse and execute a YAML test case from its raw string content.

        Execution flow
        ----------------
        1. Parse YAML & substitute variables.
        2. Execute each *setup* step (failures abort immediately).
        3. Execute each *steps* entry with the configured *on_failure* strategy.
        4. Execute each *teardown* step (best-effort, errors are logged only).
        5. Generate a report fragment via *reporter*.

        Parameters
        ----------
        yaml_content:
            Raw YAML string.
        case_id:
            Logical case identifier (e.g. ``TC-HOME-001``).
        run_id:
            Unique run identifier.

        Returns
        -------
        CaseResult
        """
        try:
            parsed = yaml.safe_load(yaml_content)
        except yaml.YAMLError as exc:
            self.emit("case_fail", case_id=case_id, error=f"YAML parse error: {exc}")
            return CaseResult(
                case_id=case_id, status="failed", error=f"YAML parse error: {exc}"
            )

        if not isinstance(parsed, dict):
            self.emit("case_fail", case_id=case_id, error="Empty YAML document")
            return CaseResult(case_id=case_id, status="failed", error="Empty YAML document")

        meta = parsed.get("meta", {})
        case_id = meta.get("id", case_id)
        case_name = meta.get("name", case_id)
        variables = parsed.get("variables", {})
        context: dict[str, Any] = dict(variables)

        result = CaseResult(case_id=case_id, name=case_name)
        self._last_run_id = run_id
        self.emit("case_start", case_id=case_id, run_id=run_id)

        loop_start = time.monotonic()

        try:
            # ── Setup ─────────────────────────────────────────────────
            for step in parsed.get("setup", []):
                if self._stopped:
                    break
                step = self._substitute(step, context)
                sr = self._execute_action(step, context)
                result.steps.append(sr)
                self._accumulate(result, sr)
                if sr.status == "failed":
                    raise RuntimeError(f"Setup step {sr.step_id} failed: {sr.error}")

            # ── Test steps ────────────────────────────────────────────
            for step in parsed.get("steps", []):
                if self._stopped:
                    break
                step = self._substitute(step, context)
                sr = self._execute_action(step, context)
                result.steps.append(sr)
                self._accumulate(result, sr)

                if sr.status == "failed":
                    strategy = step.get("on_failure", "abort")
                    self.emit(
                        "step_fail",
                        case_id=case_id,
                        step_id=sr.step_id,
                        strategy=strategy,
                        error=sr.error,
                    )
                    handled = self._handle_failure(
                        strategy, step, sr, context, case_id, run_id
                    )
                    if not handled:
                        break

            # ── Teardown ──────────────────────────────────────────────
            self._run_teardown(parsed.get("teardown", []), context)

        except Exception as exc:
            logger.exception("Unhandled exception during case execution")
            result.error = traceback.format_exc()
            result.status = "failed"

        finally:
            result.duration_ms = int((time.monotonic() - loop_start) * 1000)
            if result.status == "running":
                result.status = "passed" if result.failed == 0 else "failed"

            self.emit(
                "case_done",
                case_id=case_id,
                status=result.status,
                steps=len(result.steps),
                passed=result.passed,
                failed=result.failed,
                healed=result.healed,
                skipped=result.skipped,
                ms=result.duration_ms,
            )

            self._report_case(result)

        return result

    def run_suite(self, case_ids: list[str], run_id: str) -> SuiteResult:
        """Execute a suite of YAML test cases sequentially.

        Parameters
        ----------
        case_ids:
            List of YAML file paths to execute.
        run_id:
            Unique run identifier.

        Returns
        -------
        SuiteResult
        """
        suite = SuiteResult(
            run_id=run_id,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self._last_run_id = run_id
        self.emit("suite_start", run_id=run_id, case_count=len(case_ids))
        suite_start = time.monotonic()

        for cid in case_ids:
            if self._stopped:
                break
            case_result = self.run_case(cid, run_id=run_id)
            suite.results[case_result.case_id] = case_result
            self._accumulate_suite(suite, case_result)

        suite.duration_ms = int((time.monotonic() - suite_start) * 1000)
        suite.ended_at = datetime.now(timezone.utc).isoformat()

        if suite.failed > 0:
            suite.status = "failed"
        elif suite.healed > 0:
            suite.status = "healed"
        else:
            suite.status = "passed"

        self.emit(
            "suite_done",
            run_id=run_id,
            status=suite.status,
            total=suite.total,
            passed=suite.passed,
            failed=suite.failed,
            healed=suite.healed,
            skipped=suite.skipped,
            ms=suite.duration_ms,
        )

        self._report_suite(suite)
        return suite

    def stop(self) -> None:
        """Signal the runner to stop after the current step completes."""
        self._stopped = True
        logger.info("TestRunner received stop signal")

    # ------------------------------------------------------------------
    # Real-time event emission (JSON Lines consumed by Rust / frontend)
    # ------------------------------------------------------------------

    def emit(self, event_type: str, **kwargs: Any) -> None:
        """Print a JSON line to stdout for the Rust/Tauri layer.

        Format: ``{"type": "<event_type>", "ts": "<ISO-8601>", ...}``
        """
        payload = {
            "type": event_type,
            "ts": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        }
        line = json.dumps(payload, default=str, ensure_ascii=False)
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    # ------------------------------------------------------------------
    # Internal:  action execution & failure handling
    # ------------------------------------------------------------------

    def _take_screenshot(self, step_id: str, label: str) -> Optional[str]:
        """Take a screenshot and save it to the report directory.

        Returns the absolute file path, or ``None`` on failure.
        """
        try:
            from datetime import datetime as dt
            run_id = self._last_run_id or "unknown"
            shot_dir = self.reporter.output_dir / run_id / "screenshots"
            shot_dir.mkdir(parents=True, exist_ok=True)
            slug = f"{step_id}_{label}_{dt.now().strftime('%H%M%S%f')}"
            # Sanitize filename
            safe = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in slug)
            path = str(shot_dir / f"{safe}.png")
            img = self.device.screenshot()
            if img:
                img.save(path)
                self.emit("screenshot", step_id=step_id, path=path)
                return path
        except Exception as exc:
            logger.debug("Screenshot failed: %s", exc)
        return None

    def _execute_action(self, step: dict, context: dict) -> StepResult:
        """Look up the action in the registry and execute it."""
        step_id = step.get("id", step.get("action", "unknown"))
        desc = step.get("desc", "")
        action_name = step.get("action", "")
        timeout = step.get("timeout", 15000)

        self.emit("step_start", step_id=step_id, desc=desc, action=action_name)
        start = time.monotonic()

        sr = StepResult(step_id=step_id, desc=desc)

        # Auto screenshot before step
        sr.screenshot_before = self._take_screenshot(step_id, "before")

        try:
            handler = self.registry.get(action_name)
            if handler is None:
                raise ValueError(f"Unknown action: {action_name}")

            handler(
                device=self.device,
                step=step,
                context=context,
                timeout=timeout,
            )

            sr.status = "passed"
            sr.locator_used = str(context.get("_locator_used", ""))

        except Exception as exc:
            sr.status = "failed"
            sr.error = str(exc)
            logger.debug("Step %s failed: %s", step_id, sr.error)

        finally:
            # Auto screenshot after step
            sr.screenshot_after = self._take_screenshot(step_id, "after")
            sr.duration_ms = int((time.monotonic() - start) * 1000)
            event = "step_done" if sr.status == "passed" else "step_fail"
            self.emit(
                event,
                step_id=step_id,
                status=sr.status,
                ms=sr.duration_ms,
                error=sr.error,
            )

        return sr

    def _handle_failure(
        self,
        strategy: str,
        step: dict,
        sr: StepResult,
        context: dict,
        case_id: str,
        run_id: str,
    ) -> bool:
        """Apply the *on_failure* strategy.

        Returns ``True`` if execution should continue, ``False`` to abort.
        """
        strategy = strategy or "abort"

        if strategy == "skip":
            sr.status = "skipped"
            self._adjust_after_skip(result_accumulator=None, sr=sr)
            logger.info("Step %s skipped per on_failure=skip", sr.step_id)
            return True

        if strategy == "retry":
            max_retries = step.get("retry_count", 2)
            for attempt in range(1, max_retries + 1):
                if self._stopped:
                    return False
                logger.info(
                    "Retry %d/%d for step %s", attempt, max_retries, sr.step_id
                )
                retry_sr = self._execute_action(step, context)
                if retry_sr.status == "passed":
                    sr.status = "passed"
                    sr.error = None
                    return True
            sr.error = (sr.error or "") + f" (retried {max_retries}x, all failed)"
            return False

        if strategy == "ai_heal":
            if self.healer is None:
                logger.warning("ai_heal requested but no Healer configured; aborting")
                return False
            try:
                heal_result = self.healer.heal(
                    step=step,
                    error=sr.error or "",
                    context=context,
                )
                if heal_result.success:
                    sr.status = "healed"
                    sr.heal_log = {
                        "phase": heal_result.phase,
                        "method": heal_result.method,
                        "confidence": heal_result.confidence,
                        "description": heal_result.description,
                        "repair_actions": [
                            asdict(a) if hasattr(a, "_asdict") else dict(a)
                            for a in (heal_result.repair_actions or [])
                        ],
                    }
                    self.emit(
                        "step_heal",
                        step_id=sr.step_id,
                        phase=heal_result.phase,
                        method=heal_result.method,
                        confidence=heal_result.confidence,
                    )
                    return True
                logger.warning("Healer failed to remediate step %s", sr.step_id)
            except Exception as exc:
                logger.exception("Healer raised exception")
                sr.error = (sr.error or "") + f"; healer error: {exc}"
            return False

        return False  # abort

    def _run_teardown(self, steps: list[dict], context: dict) -> None:
        """Execute teardown steps in fire-and-forget fashion."""
        for step in steps:
            if self._stopped:
                break
            try:
                step = self._substitute(step, context)
                self._execute_action(step, context)
            except Exception:
                logger.exception("Teardown step failed (non-fatal)")

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------

    def _report_case(self, result: CaseResult) -> None:
        """Convert a runner ``CaseResult`` and hand it to the ``Reporter``."""
        try:
            r_steps = [
                RStepResult(
                    step_id=s.step_id,
                    desc=s.desc,
                    action="",
                    status=s.status,
                    duration_ms=s.duration_ms,
                    error=s.error,
                    heal_log=[s.heal_log] if s.heal_log else None,
                    screenshot_before=s.screenshot_before,
                    screenshot_after=s.screenshot_after,
                    locator_used=s.locator_used,
                )
                for s in result.steps
            ]
            r_case = RCaseResult(
                case_id=result.case_id,
                name=result.name,
                status=result.status,
                duration_ms=result.duration_ms,
                passed=result.passed,
                failed=result.failed,
                healed=result.healed,
                skipped=result.skipped,
                total=result.total,
                steps=r_steps,
            )
            # Reporter does not have add_case; we store for suite report.
            self._last_case = r_case
        except Exception as exc:
            logger.warning("Failed to report case: %s", exc)

    def _report_suite(self, result: SuiteResult) -> None:
        """Generate a suite report via the ``Reporter``."""
        try:
            r_cases: list[RCaseResult] = []
            for cr in result.results.values():
                r_steps = [
                    RStepResult(
                        step_id=s.step_id,
                        desc=s.desc,
                        action="",
                        status=s.status,
                        duration_ms=s.duration_ms,
                        error=s.error,
                        heal_log=[s.heal_log] if s.heal_log else None,
                        locator_used=s.locator_used,
                    )
                    for s in cr.steps
                ]
                r_cases.append(
                    RCaseResult(
                        case_id=cr.case_id,
                        name=cr.name,
                        status=cr.status,
                        duration_ms=cr.duration_ms,
                        passed=cr.passed,
                        failed=cr.failed,
                        healed=cr.healed,
                        skipped=cr.skipped,
                        total=cr.total,
                        steps=r_steps,
                    )
                )
            r_suite = RSuiteResult(
                run_id=result.run_id,
                started_at=result.started_at,
                ended_at=result.ended_at,
                total=result.total,
                passed=result.passed,
                failed=result.failed,
                healed=result.healed,
                skipped=result.skipped,
                duration_ms=result.duration_ms,
                cases=r_cases,
            )
            output_path = str(
                Path(self.reporter.output_dir)
                / result.run_id
                / "index.html"
            )
            self.reporter.generate_suite_report(r_suite, output_path)
        except Exception as exc:
            logger.warning("Failed to generate suite report: %s", exc)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _accumulate(result: CaseResult, sr: StepResult) -> None:
        result.total += 1
        if sr.status == "passed":
            result.passed += 1
        elif sr.status == "failed":
            result.failed += 1
        elif sr.status == "healed":
            result.healed += 1
        elif sr.status == "skipped":
            result.skipped += 1

    @staticmethod
    def _adjust_after_skip(
        result_accumulator: Optional[CaseResult], sr: StepResult
    ) -> None:
        """Adjust counters when a step transitions from failed → skipped."""
        if result_accumulator:
            result_accumulator.failed = max(0, result_accumulator.failed - 1)
            result_accumulator.skipped += 1

    @staticmethod
    def _accumulate_suite(suite: SuiteResult, cr: CaseResult) -> None:
        suite.total += 1
        if cr.status == "passed":
            suite.passed += 1
        elif cr.status == "failed":
            suite.failed += 1
        elif cr.status == "healed":
            suite.healed += 1
        elif cr.status == "skipped":
            suite.skipped += 1

    @staticmethod
    def _substitute(step: dict, context: dict) -> dict:
        """Replace ``{{var}}`` placeholders in *step* with values from context."""
        if not context:
            return step
        result = copy.deepcopy(step)

        def _walk(value: Any) -> Any:
            if isinstance(value, str):
                for k, v in context.items():
                    placeholder = "{{" + str(k) + "}}"
                    if placeholder in value:
                        value = value.replace(placeholder, str(v))
                return value
            if isinstance(value, dict):
                return {k: _walk(v) for k, v in value.items()}
            if isinstance(value, list):
                return [_walk(v) for v in value]
            return value

        return _walk(result)
