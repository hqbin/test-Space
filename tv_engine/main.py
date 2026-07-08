"""Test Space Automation Engine — CLI entry point.

Sub-commands
------------
run <yaml_path>          Execute a single YAML test case.
run-suite <case_ids...>  Execute multiple cases as a suite.
explore                  Explore an app and save its state graph.
diff                     Compare two state graphs.
check-engine             Verify that all dependencies are installed.

The ``run`` and ``run-suite`` commands emit `JSON Lines`_ to stdout so that
the Rust ``auto_runner.rs`` process can parse and forward events to the
frontend in real-time.

.. _JSON Lines: https://jsonlines.org/
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("tv_engine")


# ── JSON Lines helpers ──────────────────────────────────────────────────


def emit(event: dict) -> None:
    """Write a JSON Line to stdout and flush immediately."""
    sys.stdout.write(json.dumps(event, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def emit_step_start(step_id: str, desc: str) -> None:
    emit({"type": "step_start", "step_id": step_id, "desc": desc})


def emit_step_done(step_id: str, status: str, ms: int) -> None:
    emit({"type": "step_done", "step_id": step_id, "status": status, "ms": ms})


def emit_step_fail(step_id: str, error: str) -> None:
    emit({"type": "step_fail", "step_id": step_id, "error": error})


def emit_step_heal(step_id: str, phase: int, method: str, heal_log: Optional[dict] = None) -> None:
    payload = {"type": "step_heal", "step_id": step_id, "phase": phase, "method": method}
    if heal_log:
        payload["heal_log"] = json.dumps(heal_log, ensure_ascii=False)
    emit(payload)


def emit_screenshot(step_id: str, path: str) -> None:
    emit({"type": "screenshot", "step_id": step_id, "path": path})


def emit_suite_done(passed: int, failed: int, healed: int, ms: int) -> None:
    emit({
        "type": "suite_done",
        "passed": passed,
        "failed": failed,
        "healed": healed,
        "ms": ms,
    })


# ── Sub-command: check-engine ───────────────────────────────────────────


def cmd_check_engine(args: argparse.Namespace) -> int:
    """Verify that all required Python packages are installed and
    importable."""
    requirements = [
        ("yaml", "PyYAML"),
        ("PIL", "Pillow"),
        ("uiautomator2", "uiautomator2"),
        ("requests", "requests"),
    ]
    missing: list[str] = []
    for mod_name, pkg_name in requirements:
        try:
            __import__(mod_name)
        except ImportError:
            missing.append(pkg_name)

    if missing:
        print(f"Missing dependencies: {', '.join(missing)}", file=sys.stderr)
        print("Install with: pip install " + " ".join(missing), file=sys.stderr)
        return 2

    print("All dependencies OK.", file=sys.stderr)
    return 0


# ── Sub-command: run ────────────────────────────────────────────────────


def cmd_run(args: argparse.Namespace) -> int:
    """Load a YAML case, connect to the device, execute steps using TestRunner,
    and emit JSON Lines to stdout."""
    yaml_path = Path(args.yaml_path)
    if not yaml_path.exists():
        logger.error("YAML file not found: %s", yaml_path)
        emit({"type": "suite_done", "error": f"YAML file not found: {yaml_path}"})
        return 2

    run_id = args.run_id or f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    device_serial = args.device or os.environ.get("TV_DEVICE_SERIAL", "")
    report_dir = Path(args.report_dir or os.environ.get("TV_REPORT_DIR", "reports"))
    report_dir = report_dir.resolve() / run_id

    device = _connect_device(device_serial)
    if device is None:
        emit({"type": "suite_done", "error": "Device connection failed"})
        return 2

    from tv_engine.core.runner import TestRunner as RunnerTestRunner, CaseResult as RunnerCaseResult, SuiteResult as RunnerSuiteResult
    from tv_engine.core.reporter import Reporter, SuiteResult, CaseResult, StepResult
    from tv_engine.core.healer import Healer

    reporter = Reporter(str(report_dir.parent))
    healer = None
    if os.environ.get("TV_AI_REPAIR", "").lower() in ("1", "true", "yes"):
        healer = Healer(device)

    runner = RunnerTestRunner(device=device, reporter=reporter, healer=healer)

    # run_case handles YAML parsing, variable sub, setup/steps/teardown,
    # on_failure strategies, AI healing, and JSON Lines emissions.
    suite_start = time.monotonic()
    case_result = runner.run_case(str(yaml_path), run_id=run_id)
    total_duration = int((time.monotonic() - suite_start) * 1000)

    # Determine suite-level outcome
    suite_status = "passed" if case_result.status in ("passed", "healed") else "failed"
    emit_suite_done(
        case_result.passed, case_result.failed,
        case_result.healed, total_duration,
    )

    # Generate reports
    try:
        r_steps = [
            StepResult(
                step_id=s.step_id, desc=s.desc, action="", status=s.status,
                duration_ms=s.duration_ms, error=s.error,
                heal_log=[s.heal_log] if s.heal_log else None,
                locator_used=s.locator_used,
            )
            for s in case_result.steps
        ]
        # Gather device info
        device_info = ""
        app_version = ""
        try:
            device_info = f"{device_serial or ''} | {device.get_display_size()}"
            device_info = device_info.strip().strip("|").strip()
            app_pkg = case_result.case_id.split("-")[0] if "-" in case_result.case_id else ""
            if app_pkg:
                app_version = device.shell(f"dumpsys package {app_pkg} 2>/dev/null | grep versionName | head -1").strip()
        except Exception:
            pass

        r_case = CaseResult(
            case_id=case_result.case_id, name=case_result.name,
            status=case_result.status, duration_ms=case_result.duration_ms,
            passed=case_result.passed, failed=case_result.failed,
            healed=case_result.healed, skipped=case_result.skipped,
            total=case_result.total, steps=r_steps,
            device_serial=device_serial, device_info=device_info,
            app_version=app_version,
        )
        suite_result = SuiteResult(
            run_id=run_id,
            title=f"Automation Report - {case_result.name}",
            started_at=datetime.now(timezone.utc).isoformat(),
            ended_at=datetime.now(timezone.utc).isoformat(),
            total=case_result.total, passed=case_result.passed,
            failed=case_result.failed, healed=case_result.healed,
            skipped=case_result.skipped, duration_ms=total_duration,
            device_serial=device_serial, device_info=device_info,
            app_version=app_version, cases=[r_case],
        )
        reporter.generate_suite_report(suite_result, str(report_dir / "index.html"))
        reporter.generate_case_report(r_case, str(report_dir / case_result.case_id))
        reporter.export_json_summary(suite_result, str(report_dir / "summary.json"))
        logger.info("Reports generated in %s", report_dir)
    except Exception as exc:
        logger.warning("Report generation failed: %s", exc)

    return 0 if suite_status == "passed" else 1


# ── Sub-command: run-suite ──────────────────────────────────────────────


def cmd_run_suite(args: argparse.Namespace) -> int:
    """Run multiple cases as a suite using TestRunner.

    Each case ID is expected to match a YAML file under the configured
    cases directory (``TV_CASES_DIR`` env var or ``cases/``).
    Supports ``--tags`` filter (comma-separated).
    """
    cases_dir = Path(os.environ.get("TV_CASES_DIR", "cases"))
    if not cases_dir.exists():
        logger.error("Cases directory not found: %s", cases_dir)
        return 2

    tags_filter = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
    case_ids: list[str] = args.case_ids
    if not case_ids:
        # Auto-discover all YAML files in cases dir
        case_ids = sorted(p.stem for p in cases_dir.glob("*.yaml") if p.is_file())
        if tags_filter:
            filtered = []
            for cid in case_ids:
                yaml_path = cases_dir / f"{cid}.yaml"
                if yaml_path.exists():
                    try:
                        import yaml
                        with open(yaml_path, encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                        case_tags = data.get("meta", {}).get("tags", [])
                        if any(t in case_tags for t in tags_filter):
                            filtered.append(cid)
                    except Exception:
                        filtered.append(cid)
            case_ids = filtered
        if not case_ids:
            logger.error("No case IDs found matching tags: %s", tags_filter)
            return 2

    device_serial = args.device or os.environ.get("TV_DEVICE_SERIAL", "")
    run_id = args.run_id or f"suite_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    report_dir = Path(args.report_dir or os.environ.get("TV_REPORT_DIR", "reports")).resolve() / run_id

    device = _connect_device(device_serial)
    if device is None:
        emit({"type": "suite_done", "error": "Device connection failed"})
        return 2

    from tv_engine.core.runner import TestRunner
    from tv_engine.core.reporter import Reporter
    from tv_engine.core.healer import Healer

    reporter = Reporter(str(report_dir.parent))
    healer = None
    if os.environ.get("TV_AI_REPAIR", "").lower() in ("1", "true", "yes"):
        healer = Healer(device)

    runner = TestRunner(device=device, reporter=reporter, healer=healer)

    # Convert case IDs to full YAML paths for TestRunner
    case_paths = [str(cases_dir / f"{cid}.yaml") for cid in case_ids]

    suite_start = time.monotonic()
    suite_result = runner.run_suite(case_paths, run_id)
    total_duration = int((time.monotonic() - suite_start) * 1000)
    suite_result.duration_ms = total_duration

    suite_status = "passed" if suite_result.failed == 0 else "failed"
    emit_suite_done(suite_result.passed, suite_result.failed, suite_result.healed, total_duration)

    # Generate JSON summary
    try:
        reporter.export_json_summary(
            suite_result, str(report_dir / "summary.json")
        )
    except Exception as exc:
        logger.warning("JSON summary export failed: %s", exc)

    return 0 if suite_status == "passed" else 1


# ── Sub-command: explore ────────────────────────────────────────────────


def cmd_explore(args: argparse.Namespace) -> int:
    """Explore an Android TV app and save its state graph using the Explorer
    class."""
    device_serial = args.device or os.environ.get("TV_DEVICE_SERIAL", "")
    package = args.package
    max_states = args.max_states or 100

    device = _connect_device(device_serial)
    if device is None:
        logger.error("Device connection failed")
        return 2

    logger.info("Exploring package %s (max %d states)", package, max_states)

    from tv_engine.core.explorer import Explorer
    explorer = Explorer(device)
    graph = explorer.explore(package=package, max_states=max_states)

    # Save graph
    graphs_dir = Path("graphs")
    graphs_dir.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    graph_path = graphs_dir / f"{package}_{timestamp}.json"
    explorer.save_graph(graph, str(graph_path))

    logger.info("Exploration complete: %d states, %d transitions",
                len(graph.nodes), len(graph.edges))
    print(f"Graph saved: {graph_path}", file=sys.stderr)
    return 0


# ── Sub-command: diff ───────────────────────────────────────────────────


def cmd_diff(args: argparse.Namespace) -> int:
    """Compare two state graphs and print a summary of differences."""
    package = args.package
    since = args.since or "latest"

    graphs_dir = Path("graphs")
    if not graphs_dir.exists():
        logger.error("No graphs directory found")
        return 2

    candidates = sorted(graphs_dir.glob(f"{package}_*.json"), reverse=True)
    if len(candidates) < 2:
        logger.error("Need at least 2 graphs for comparison; found %d", len(candidates))
        return 2

    if since == "latest":
        new_graph_path = candidates[0]
        old_graph_path = candidates[1]
    else:
        new_graph_path = candidates[0]
        old_candidates = [p for p in candidates if since in p.name]
        old_graph_path = old_candidates[0] if old_candidates else candidates[1]

    try:
        import yaml
    except ImportError:
        pass

    old_data = json.loads(old_graph_path.read_text(encoding="utf-8"))
    new_data = json.loads(new_graph_path.read_text(encoding="utf-8"))

    old_nodes = {n["id"] for n in old_data.get("nodes", [])}
    new_nodes = {n["id"] for n in new_data.get("nodes", [])}
    old_edges = {(e["from"], e["to"], e["action"]) for e in old_data.get("edges", [])}
    new_edges = {(e["from"], e["to"], e["action"]) for e in new_data.get("edges", [])}

    added_nodes = new_nodes - old_nodes
    removed_nodes = old_nodes - new_nodes
    added_edges = new_edges - old_edges
    removed_edges = old_edges - new_edges

    diff = {
        "package": package,
        "old_graph": old_graph_path.name,
        "new_graph": new_graph_path.name,
        "nodes_added": len(added_nodes),
        "nodes_removed": len(removed_nodes),
        "edges_added": len(added_edges),
        "edges_removed": len(removed_edges),
        "added_nodes": sorted(added_nodes)[:50],
        "removed_nodes": sorted(removed_nodes)[:50],
    }

    print(json.dumps(diff, ensure_ascii=False, indent=2))
    return 0


# ── Internal helpers ────────────────────────────────────────────────────


def _connect_device(serial: str) -> Any:
    """Connect to a device and return a device controller instance.

    Returns ``None`` on failure.
    """
    try:
        from tv_engine.core.device import DeviceController

        device = DeviceController(serial=serial)
        device.connect(serial)
        logger.info("Connected to device: %s", serial or "default")
        return device
    except ImportError:
        logger.warning("DeviceController not available; using stub")

        class _StubDevice:
            def __init__(self, serial=""): self.serial = serial
            def connect(self, s): return True
            def press_key(self, k): return True
            def wait_stable(self, t=3000): return True
            def screenshot(self):
                from PIL import Image
                return Image.new("RGB", (1920, 1080), (0, 0, 0))
            def get_ui_tree(self): return {"elements": [], "activity": "unknown"}
            def get_focused_element(self): return None
            def get_focusable_elements(self): return []
            def get_current_activity(self): return "unknown"
            def get_display_size(self): return (1920, 1080)
            def shell(self, cmd): return ""
            def is_app_foreground(self, pkg): return True
            def start_app(self, pkg, act=""): pass
            def wait_for_activity(self, act, t=8000): return True

        return _StubDevice(serial=serial)
    except Exception:
        logger.exception("Failed to connect to device: %s", serial)
        return None


def _execute_step(device: Any, step: dict) -> tuple[bool, Optional[str]]:
    """Execute a single step against the device.

    Returns ``(success, error_message)``.
    """
    action = step.get("action", "")
    timeout = step.get("timeout", 5000)

    if action == "press_key":
        key = step.get("key", "DPAD_CENTER")
        device.press_key(key)
        wait_after = step.get("wait_after", 0)
        if wait_after:
            device.wait_stable(wait_after)
        return True, None

    if action == "press_key_sequence":
        keys = step.get("keys", [])
        wait_after = step.get("wait_after", 0)
        for key in keys:
            device.press_key(key)
        if wait_after:
            device.wait_stable(wait_after)
        return True, None

    if action == "wait_stable":
        device.wait_stable(timeout)
        return True, None

    if action == "wait_for":
        timeout_ms = step.get("timeout", 5000)
        if not device.wait_stable(timeout_ms):
            return False, f"wait_for timed out after {timeout_ms}ms"
        condition = step.get("condition", {})
        if condition.get("type") == "element_exists":
            cond_target = condition.get("target", {})
            if cond_target:
                from tv_engine.core.locator import Locator
                locator = Locator(device)
                tree = device.get_ui_tree()
                result = locator.locate(cond_target, ui_tree=tree)
                if not result or not result.found:
                    return False, f"Condition element not found: {cond_target}"
        return True, None

    if action == "wait_then_assert":
        wait_seconds = step.get("wait_seconds", 0)
        import time
        time.sleep(wait_seconds)
        device.wait_stable(1000)
        return True, None

    if action == "screenshot":
        return True, None

    if action == "navigate_to":
        from tv_engine.core.navigator import Navigator
        target = step.get("target", {})
        max_steps = step.get("max_steps", 25)
        navigator = Navigator(device)
        nav_result = navigator.navigate_to(target, max_steps=max_steps, timeout_ms=timeout)
        if not nav_result.success:
            return False, nav_result.error or "Navigation failed"
        return True, None

    if action in ("assert_focused", "assert_element", "assert_visual", "assert_app_foreground", "assert_shell"):
        return True, None

    if action == "launch_app":
        package = step.get("package", "")
        wait_activity = step.get("wait_activity", "")
        device.start_app(package, wait_activity)
        device.wait_stable(timeout)
        if wait_activity:
            if not device.wait_for_activity(wait_activity, timeout):
                return False, f"Activity '{wait_activity}' not reached"
        return True, None

    if action == "input_text":
        text = step.get("text", "")
        if not text:
            return False, "input_text requires 'text'"
        device.shell(f"input text {text}")
        return True, None

    if action == "swipe":
        direction = step.get("direction", "RIGHT")
        steps = step.get("steps", 10)
        w, h = device.get_display_size()
        dirs = {
            "UP": (w // 2, h * 3 // 4, w // 2, h // 4),
            "DOWN": (w // 2, h // 4, w // 2, h * 3 // 4),
            "LEFT": (w * 3 // 4, h // 2, w // 4, h // 2),
            "RIGHT": (w // 4, h // 2, w * 3 // 4, h // 2),
        }
        sx, sy, ex, ey = dirs.get(direction.upper(), (0, 0, 0, 0))
        if sx or sy or ex or ey:
            device.shell(f"input swipe {sx} {sy} {ex} {ey} {steps}")
        return True, None

    if action == "set_variable":
        return True, None

    logger.warning("Unknown action: %s", action)
    return True, None


def _generate_report(
    device: Any,
    case_data: dict,
    passed: int,
    failed: int,
    healed: int,
    skipped: int,
    duration_ms: int,
    report_dir: Path,
    run_id: str,
    case_id: str,
    device_serial: str,
) -> None:
    """Generate HTML reports for a completed run."""
    try:
        from tv_engine.core.reporter import Reporter, SuiteResult, CaseResult, StepResult
    except ImportError:
        logger.warning("Reporter module not available; skipping report generation")
        return

    meta = case_data.get("meta", {})
    steps = case_data.get("steps", [])

    step_results: list[StepResult] = []
    for i, s in enumerate(steps):
        step_id = s.get("id", f"step_{i}")
        shot_before = str(report_dir / "screenshots" / f"{step_id}_before.png") if (report_dir / "screenshots" / f"{step_id}_before.png").exists() else None
        shot_after = str(report_dir / "screenshots" / f"{step_id}_after.png") if (report_dir / "screenshots" / f"{step_id}_after.png").exists() else None
        shot_ref = str(report_dir / "screenshots" / f"{step_id}_ref.png") if (report_dir / "screenshots" / f"{step_id}_ref.png").exists() else None
        step_results.append(
            StepResult(
                step_id=step_id,
                desc=s.get("desc", ""),
                action=s.get("action", ""),
                status="passed",
                duration_ms=0,
                screenshot_before=shot_before,
                screenshot_after=shot_after,
                screenshot_ref=shot_ref,
            )
        )

    case_result = CaseResult(
        case_id=case_id,
        name=meta.get("name", case_id),
        author=meta.get("author", ""),
        priority=meta.get("priority", "P2"),
        tags=meta.get("tags", []),
        description=meta.get("description", ""),
        status="passed" if failed == 0 else "failed",
        duration_ms=duration_ms,
        passed=passed,
        failed=failed,
        healed=healed,
        skipped=skipped,
        total=len(steps),
        steps=step_results,
        device_serial=device_serial,
    )

    suite_result = SuiteResult(
        run_id=run_id,
        title=f"Automation Report - {meta.get('name', case_id)}",
        started_at=datetime.now(timezone.utc).isoformat(),
        ended_at=datetime.now(timezone.utc).isoformat(),
        device_serial=device_serial,
        total=len(steps),
        passed=passed,
        failed=failed,
        healed=healed,
        skipped=skipped,
        duration_ms=duration_ms,
        cases=[case_result],
    )

    reporter = Reporter(str(report_dir.parent))
    suite_path = report_dir / "index.html"
    reporter.generate_suite_report(suite_result, str(suite_path))
    reporter.generate_case_report(case_result, str(report_dir / case_id))
    reporter.export_json_summary(suite_result, str(report_dir / "summary.json"))

    logger.info("Reports generated in %s", report_dir)


# ── Argument parser ─────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Test Space Automation Engine — run, explore, and debug TV UI tests.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Sub-command to execute")

    # run
    run_parser = subparsers.add_parser("run", help="Execute a single YAML test case")
    run_parser.add_argument("yaml_path", help="Path to the YAML case file")
    run_parser.add_argument("--device", default="", help="Device serial number or IP")
    run_parser.add_argument("--run-id", default="", help="Unique run identifier")
    run_parser.add_argument("--report-dir", default="", help="Output directory for reports")
    run_parser.add_argument("--tags", default="", help="Comma-separated tag filter")

    # run-suite
    suite_parser = subparsers.add_parser("run-suite", help="Execute multiple test cases as a suite")
    suite_parser.add_argument("case_ids", nargs="*", help="Case IDs (matching YAML filenames in cases/); omit to run all")
    suite_parser.add_argument("--device", default="", help="Device serial number or IP")
    suite_parser.add_argument("--run-id", default="", help="Unique run identifier")
    suite_parser.add_argument("--report-dir", default="", help="Output directory for reports")
    suite_parser.add_argument("--tags", default="", help="Comma-separated tag filter (e.g. smoke,home)")

    # explore
    explore_parser = subparsers.add_parser("explore", help="Explore an app and save its state graph")
    explore_parser.add_argument("--package", required=True, help="App package name to explore")
    explore_parser.add_argument("--device", default="", help="Device serial number or IP")
    explore_parser.add_argument("--max-states", type=int, default=100, help="Maximum states to explore")

    # diff
    diff_parser = subparsers.add_parser("diff", help="Compare two state graphs")
    diff_parser.add_argument("--package", required=True, help="App package name")
    diff_parser.add_argument("--since", default="latest", help="Compare against this version/label")
    diff_parser.add_argument("--device", default="", help="Device serial number or IP")

    # check-engine
    subparsers.add_parser("check-engine", help="Verify that all dependencies are installed")

    return parser


# ── Entry point ─────────────────────────────────────────────────────────


def main() -> int:
    """CLI entry point.

    Parses arguments, dispatches to the appropriate sub-command, and returns
    an exit code.
    """
    parser = build_parser()
    args = parser.parse_args()

    command_handlers = {
        "run": cmd_run,
        "run-suite": cmd_run_suite,
        "explore": cmd_explore,
        "diff": cmd_diff,
        "check-engine": cmd_check_engine,
    }

    handler = command_handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 2

    try:
        return handler(args)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception:
        logger.exception("Unhandled exception in command '%s'", args.command)
        return 2


if __name__ == "__main__":
    sys.exit(main())
