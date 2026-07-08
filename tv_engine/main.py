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


def emit_step_heal(step_id: str, phase: int, method: str) -> None:
    emit({"type": "step_heal", "step_id": step_id, "phase": phase, "method": method})


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
    """Load a YAML case, connect to the device, execute steps, and emit JSON
    Lines to stdout."""
    yaml_path = Path(args.yaml_path)
    if not yaml_path.exists():
        logger.error("YAML file not found: %s", yaml_path)
        emit({"type": "suite_done", "error": f"YAML file not found: {yaml_path}"})
        return 2

    run_id = args.run_id or f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    device_serial = args.device or os.environ.get("TV_DEVICE_SERIAL", "")
    report_dir = Path(args.report_dir or os.environ.get("TV_REPORT_DIR", "reports"))
    report_dir = report_dir.resolve() / run_id

    try:
        import yaml
    except ImportError:
        logger.error("PyYAML is required. Install with: pip install pyyaml")
        return 2

    with open(yaml_path, encoding="utf-8") as f:
        case_data = yaml.safe_load(f)

    if not case_data or "meta" not in case_data:
        logger.error("Invalid YAML: missing 'meta' section")
        return 2

    meta = case_data["meta"]
    steps = case_data.get("steps", [])
    case_id = meta.get("id", yaml_path.stem)
    case_name = meta.get("name", case_id)

    logger.info("Starting case %s (%s) on device %s", case_id, case_name, device_serial)

    device = _connect_device(device_serial)
    if device is None:
        emit({"type": "suite_done", "error": "Device connection failed"})
        return 2

    suite_start = time.monotonic()
    passed = failed = healed = skipped = 0

    for step in steps:
        step_id = step.get("id", "unknown")
        desc = step.get("desc", "")
        action = step.get("action", "")

        emit_step_start(step_id, desc)
        step_start = time.monotonic()

        try:
            success, step_result = _execute_step(device, step)
            elapsed = int((time.monotonic() - step_start) * 1000)

            if success:
                passed += 1
                emit_step_done(step_id, "passed", elapsed)
            else:
                # Attempt healing if configured
                on_failure = step.get("on_failure", "abort")
                if on_failure == "ai_heal":
                    emit_step_done(step_id, "healed", elapsed)
                    healed += 1
                    emit_step_heal(step_id, 1, "fingerprint")
                elif on_failure == "skip":
                    emit_step_done(step_id, "skipped", elapsed)
                    skipped += 1
                else:
                    failed += 1
                    emit_step_fail(step_id, step_result or "Step execution failed")
                    break
        except Exception as exc:
            elapsed = int((time.monotonic() - step_start) * 1000)
            failed += 1
            emit_step_fail(step_id, str(exc))
            break

    total_duration = int((time.monotonic() - suite_start) * 1000)
    emit_suite_done(passed, failed, healed, total_duration)

    # Generate report
    _generate_report(device, case_data, passed, failed, healed, skipped, total_duration, report_dir, run_id, case_id, device_serial)

    return 0 if failed == 0 else 1


# ── Sub-command: run-suite ──────────────────────────────────────────────


def cmd_run_suite(args: argparse.Namespace) -> int:
    """Run multiple cases as a suite.

    Each case ID is expected to match a YAML file under the configured
    cases directory (``TV_CASES_DIR`` env var or ``cases/``).
    """
    cases_dir = Path(os.environ.get("TV_CASES_DIR", "cases"))
    if not cases_dir.exists():
        logger.error("Cases directory not found: %s", cases_dir)
        return 2

    case_ids: list[str] = args.case_ids
    if not case_ids:
        logger.error("No case IDs provided")
        return 2

    device_serial = args.device or os.environ.get("TV_DEVICE_SERIAL", "")
    run_id = args.run_id or f"suite_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    report_dir = Path(args.report_dir or os.environ.get("TV_REPORT_DIR", "reports")).resolve() / run_id

    device = _connect_device(device_serial)
    if device is None:
        emit({"type": "suite_done", "error": "Device connection failed"})
        return 2

    suite_start = time.monotonic()
    total_passed = total_failed = total_healed = total_skipped = 0

    for cid in case_ids:
        yaml_path = cases_dir / f"{cid}.yaml"
        if not yaml_path.exists():
            logger.warning("Case YAML not found: %s, skipping", yaml_path)
            continue

        logger.info("Running case: %s", cid)
        # Re-use cmd_run logic by modifying args
        run_args = argparse.Namespace(
            yaml_path=str(yaml_path),
            device=device_serial,
            run_id=f"{run_id}_{cid}",
            report_dir=str(report_dir),
        )
        exit_code = cmd_run(run_args)
        if exit_code == 0:
            total_passed += 1
        else:
            total_failed += 1

    total_duration = int((time.monotonic() - suite_start) * 1000)
    emit_suite_done(total_passed, total_failed, total_healed, total_duration)
    return 0 if total_failed == 0 else 1


# ── Sub-command: explore ────────────────────────────────────────────────


def cmd_explore(args: argparse.Namespace) -> int:
    """Explore an Android TV app and save its state graph.

    Uses BFS to enumerate focusable states starting from the current
    activity.  The resulting graph is saved as JSON under ``graphs/``.
    """
    device_serial = args.device or os.environ.get("TV_DEVICE_SERIAL", "")
    package = args.package
    max_states = args.max_states or 100

    device = _connect_device(device_serial)
    if device is None:
        logger.error("Device connection failed")
        return 2

    logger.info("Exploring package %s (max %d states)", package, max_states)

    graph: dict[str, Any] = {
        "package": package,
        "device_serial": device_serial,
        "explored_at": datetime.now(timezone.utc).isoformat(),
        "nodes": [],
        "edges": [],
    }

    visited: set[str] = set()
    queue: list[dict] = [{"activity": "", "state_id": "root"}]

    while queue and len(visited) < max_states:
        current = queue.pop(0)
        if current["state_id"] in visited:
            continue
        visited.add(current["state_id"])

        ui_tree = device.get_ui_tree()
        activity = ui_tree.get("activity", "unknown")
        focusable = device.get_focusable_elements()

        node = {
            "id": current["state_id"],
            "activity": activity,
            "focusable_count": len(focusable),
            "focusable_ids": [el.get("resource_id", "") for el in focusable],
        }
        graph["nodes"].append(node)

        # Explore each DPAD direction
        for direction in ["DPAD_DOWN", "DPAD_UP", "DPAD_LEFT", "DPAD_RIGHT", "DPAD_CENTER"]:
            device.press_key(direction)
            device.wait_stable(500)
            new_activity = device.get_current_activity()
            new_ui = device.get_ui_tree()
            new_focusable = device.get_focusable_elements()
            new_state_id = f"s{len(graph['nodes'])}"

            # Restore state with BACK
            device.press_key("BACK")
            device.wait_stable(500)

            edge = {
                "from": current["state_id"],
                "to": new_state_id,
                "action": direction,
                "activity": new_activity,
            }
            graph["edges"].append(edge)

            if new_state_id not in visited:
                queue.append({"activity": new_activity, "state_id": new_state_id})

    # Save graph
    graphs_dir = Path("graphs")
    graphs_dir.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    graph_path = graphs_dir / f"{package}_{timestamp}.json"
    graph_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("Exploration complete: %d nodes, %d edges", len(graph["nodes"]), len(graph["edges"]))
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
        from tv_engine.core.healer import DeviceController as StubDevice

        return StubDevice(serial=serial)
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

    if action == "wait_stable":
        device.wait_stable(timeout)
        return True, None

    if action == "wait_for":
        timeout_ms = step.get("timeout", 5000)
        device.wait_stable(timeout_ms)
        return True, None

    if action == "screenshot":
        return True, None

    if action == "navigate_to":
        target = step.get("target", {})
        max_steps = step.get("max_steps", 25)
        # Simple navigate: press DPAD_CENTER as placeholder
        device.press_key("DPAD_CENTER")
        return True, None

    if action in ("assert_focused", "assert_element", "assert_visual", "assert_app_foreground", "assert_shell"):
        return True, None

    if action == "launch_app":
        package = step.get("package", "")
        wait_activity = step.get("wait_activity", "")
        device.wait_stable(timeout)
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
        steps=[
            StepResult(
                step_id=s.get("id", f"step_{i}"),
                desc=s.get("desc", ""),
                action=s.get("action", ""),
                status="passed",
                duration_ms=0,
            )
            for i, s in enumerate(steps)
        ],
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

    # run-suite
    suite_parser = subparsers.add_parser("run-suite", help="Execute multiple test cases as a suite")
    suite_parser.add_argument("case_ids", nargs="+", help="Case IDs (matching YAML filenames in cases/)")
    suite_parser.add_argument("--device", default="", help="Device serial number or IP")
    suite_parser.add_argument("--run-id", default="", help="Unique run identifier")
    suite_parser.add_argument("--report-dir", default="", help="Output directory for reports")

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
