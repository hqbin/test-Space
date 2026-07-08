"""BFS state-graph explorer for mapping TV app navigation.

Automatically discovers all reachable focus states of a TV application
by performing a breadth-first traversal over the device's focusable elements.
The resulting :class:`StateGraph` can be persisted, diffed, and later
replayed by the :class:`Navigator` for fast Level-1 path planning.
"""

import json
import time
import logging
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from collections import deque

from .device import DeviceController
from .state import TVState, StateGraph
from .navigator import Navigator, NavResult

logger = logging.getLogger(__name__)

_DEFAULT_MAX_STATES = 100
_DEFAULT_TIMEOUT_S = 300
_STEP_SLEEP = 0.15
_STABLE_WAIT = 500


@dataclass
class GraphDiff:
    """Describes differences between two :class:`StateGraph` instances."""

    new_states: list[dict] = field(default_factory=list)
    removed_states: list[dict] = field(default_factory=list)
    changed_transitions: list[dict] = field(default_factory=list)
    changed_elements: list[dict] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(
            self.new_states
            or self.removed_states
            or self.changed_transitions
            or self.changed_elements
        )


class Explorer:
    """BFS state-graph explorer for mapping TV app navigation.

    The exploration algorithm:

    1. Captures the initial device state (activity, focused element, focusable
       elements) and computes a fingerprint.
    2. For each focusable element in the current state, attempts to navigate
       to it and presses CENTER.
    3. Records the resulting state and transition in the graph.
    4. Backtracks to the previous state using :class:`Navigator`.
    5. Repeats until all reachable states have been visited or limits are hit.

    Parameters
    ----------
    device:
        Connected device controller.
    """

    def __init__(self, device: DeviceController):
        self.device = device
        self._navigator = Navigator(device)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def explore(
        self,
        package: str,
        max_states: int = _DEFAULT_MAX_STATES,
        timeout_s: int = _DEFAULT_TIMEOUT_S,
    ) -> StateGraph:
        """Run BFS exploration of *package* up to *max_states* states.

        Parameters
        ----------
        package:
            Android package name (e.g. ``"com.example.tvlauncher"``).
            Used for metadata only; the device should already be on the
            target app's activity.
        max_states:
            Maximum number of unique states to explore.
        timeout_s:
            Total wall-clock timeout in seconds.

        Returns
        -------
        StateGraph
            Populated graph with all discovered states and transitions.
        """
        deadline = time.monotonic() + timeout_s
        logger.info(
            "Starting BFS explore for %s (max_states=%d, timeout=%ds)",
            package,
            max_states,
            timeout_s,
        )

        graph = StateGraph()
        state_queue: deque[str] = deque()
        visited_states: set[str] = set()
        state_count = 0

        # ── Initial state ────────────────────────────────────────────
        initial_state = self._capture_current_state()
        if initial_state is None:
            logger.error("Could not capture initial device state")
            return graph

        initial_fp = initial_state.fingerprint()
        graph.add_state(initial_state)
        visited_states.add(initial_fp)
        state_queue.append(initial_fp)
        state_count += 1
        logger.debug("Initial state fingerprint: %s", initial_fp)

        while state_queue and state_count < max_states:
            if time.monotonic() >= deadline:
                logger.warning("Explore deadline reached after %d states", state_count)
                break

            current_fp = state_queue.popleft()
            current_state = graph.nodes.get(current_fp)
            if current_state is None:
                continue

            logger.debug("Exploring state %s", current_fp)
            focusable_ids = list(current_state.focusable_ids)

            for elem_id in focusable_ids:
                if time.monotonic() >= deadline or state_count >= max_states:
                    break

                # ── Navigate to element ──────────────────────────────
                nav_target = {
                    "primary": {"by": "resource_id", "value": elem_id}
                }
                nav_result = self._navigator.navigate_to(
                    nav_target, max_steps=15
                )
                if not nav_result.success:
                    # Fallback: try content_desc.
                    nav_target = {
                        "primary": {
                            "by": "content_desc",
                            "value": elem_id,
                        }
                    }
                    nav_result = self._navigator.navigate_to(
                        nav_target, max_steps=15
                    )
                if not nav_result.success:
                    logger.debug("Could not navigate to %s, skipping", elem_id)
                    continue

                time.sleep(_STEP_SLEEP)
                self.device.wait_stable(_STABLE_WAIT)

                # ── Press CENTER to trigger transition ───────────────
                self.device.press_key("DPAD_CENTER")
                time.sleep(_STEP_SLEEP)
                self.device.wait_stable(_STABLE_WAIT)

                # ── Capture resulting state ──────────────────────────
                new_state = self._capture_current_state()
                if new_state is None:
                    logger.debug("No state captured after CENTER on %s", elem_id)
                    self._navigate_back_to(current_state)
                    continue

                new_fp = new_state.fingerprint()
                transition_key = f"CENTER:{elem_id}"

                graph.add_transition(current_fp, new_fp, transition_key)

                if new_fp not in visited_states:
                    visited_states.add(new_fp)
                    graph.add_state(new_state)
                    state_queue.append(new_fp)
                    state_count += 1
                    logger.info(
                        "Discovered state %d/%d: %s",
                        state_count,
                        max_states,
                        new_fp,
                    )

                # ── Backtrack to original state ──────────────────────
                self._navigate_back_to(current_state)

            # Verify we are back at the current state after processing
            # all its elements.
            verify_state = self._capture_current_state()
            if verify_state is None or verify_state.fingerprint() != current_fp:
                logger.debug(
                    "Lost position after state %s; re-navigating", current_fp
                )
                self._navigate_to_state(current_state)

        logger.info(
            "Explore complete: %d states, %d transitions",
            len(graph.nodes),
            len(graph.edges),
        )
        return graph

    def diff(self, old_graph: StateGraph, new_graph: StateGraph) -> GraphDiff:
        """Compare two state graphs and return the differences.

        Identifies new / removed states, changed transitions, and elements
        whose focusable set has changed between matching states.

        Parameters
        ----------
        old_graph:
            Baseline graph.
        new_graph:
            Current graph.

        Returns
        -------
        GraphDiff
        """
        diff_result = GraphDiff()

        old_fps = set(old_graph.nodes.keys())
        new_fps = set(new_graph.nodes.keys())

        for fp in new_fps - old_fps:
            state = new_graph.nodes[fp]
            diff_result.new_states.append(asdict(state))

        for fp in old_fps - new_fps:
            state = old_graph.nodes[fp]
            diff_result.removed_states.append(asdict(state))

        shared = old_fps & new_fps
        for fp in shared:
            old_state = old_graph.nodes[fp]
            new_state = new_graph.nodes[fp]
            if old_state.focusable_ids != new_state.focusable_ids:
                diff_result.changed_elements.append(
                    {
                        "fingerprint": fp,
                        "old_count": len(old_state.focusable_ids),
                        "new_count": len(new_state.focusable_ids),
                        "old_elements": sorted(old_state.focusable_ids),
                        "new_elements": sorted(new_state.focusable_ids),
                    }
                )

        old_transitions = self._flatten_transitions(old_graph)
        new_transitions = self._flatten_transitions(new_graph)
        old_t_set = set(old_transitions)
        new_t_set = set(new_transitions)

        for t in new_t_set - old_t_set:
            diff_result.changed_transitions.append(
                {
                    "source": t[0],
                    "key": t[1],
                    "target": t[2],
                    "change": "added",
                }
            )
        for t in old_t_set - new_t_set:
            diff_result.changed_transitions.append(
                {
                    "source": t[0],
                    "key": t[1],
                    "target": t[2],
                    "change": "removed",
                }
            )

        return diff_result

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @staticmethod
    def save_graph(graph: StateGraph, filepath: str) -> None:
        """Serialize *graph* to a JSON file at *filepath*.

        Parameters
        ----------
        graph:
            The state graph to persist.
        filepath:
            Destination file path (``.json`` extension recommended).
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        serialized = graph.to_json()
        serialized["_meta"] = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
        }

        path.write_text(
            json.dumps(serialized, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        logger.info(
            "StateGraph saved to %s (%d states)", filepath, len(graph.nodes)
        )

    @staticmethod
    def load_graph(filepath: str) -> StateGraph:
        """Deserialize a :class:`StateGraph` from a JSON file.

        Parameters
        ----------
        filepath:
            Path to the JSON graph file.

        Returns
        -------
        StateGraph
        """
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"Graph file not found: {filepath}")

        raw = json.loads(path.read_text(encoding="utf-8"))
        graph = StateGraph.from_json(raw)

        logger.info(
            "StateGraph loaded from %s (%d states, %d transitions)",
            filepath,
            len(graph.nodes),
            len(graph.edges),
        )
        return graph

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _capture_current_state(self) -> Optional[TVState]:
        """Snapshot the current device state as a :class:`TVState`."""
        try:
            activity = self.device.get_current_activity() or ""
            focused = self.device.get_focused_element()
            focusables = self.device.get_focusable_elements() or []
            screenshot = self.device.screenshot()

            return TVState(
                activity=activity,
                focused_id=(focused or {}).get("resource_id", ""),
                focused_desc=(focused or {}).get("content_desc", ""),
                focused_text=(focused or {}).get("text", ""),
                focusable_ids=frozenset(
                    self._element_id(el) for el in focusables if el
                ),
                screenshot_hash=(
                    self._compute_phash(screenshot) if screenshot else ""
                ),
            )
        except Exception:
            logger.exception("Failed to capture device state")
            return None

    def _navigate_back_to(self, target_state: TVState) -> None:
        """Navigate the device back to *target_state* using BACK keys."""
        for _ in range(10):
            current = self._capture_current_state()
            if current and current.fingerprint() == target_state.fingerprint():
                return
            self.device.press_key("DPAD_BACK")
            time.sleep(_STEP_SLEEP)
            self.device.wait_stable(_STABLE_WAIT)

    def _navigate_to_state(self, target_state: TVState) -> bool:
        """Attempt to reach *target_state* via the :class:`Navigator`."""
        nav_target = {
            "primary": {
                "by": "resource_id",
                "value": target_state.focused_id,
            }
        }
        result = self._navigator.navigate_to(nav_target, max_steps=20)
        return result.success

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _element_id(element: dict) -> str:
        """Return a stable string identifier for an element dict."""
        rid = element.get("resource_id") or element.get("resource-id", "")
        if rid:
            return str(rid)
        cd = element.get("content_desc") or element.get("content-desc", "")
        if cd:
            return str(cd)
        txt = element.get("text", "")
        if txt:
            return str(txt)
        cls = element.get("class_name") or element.get("class", "")
        bounds = (
            f"{element.get('bounds_left','')},{element.get('bounds_top','')},"
            f"{element.get('bounds_right','')},{element.get('bounds_bottom','')}"
        )
        return f"{cls}:{bounds}"

    @staticmethod
    def _compute_phash(image: Any) -> str:
        """Compute a perceptual hash string for the given image.

        Returns an empty string if ``image`` is ``None`` or if the
        ``imagehash`` library is unavailable.
        """
        if image is None:
            return ""
        try:
            from PIL import Image as PILImage
            import imagehash

            if isinstance(image, PILImage.Image):
                return str(imagehash.phash(image))
            pil_image = (
                PILImage.open(image)
                if isinstance(image, (str, Path))
                else image
            )
            if hasattr(pil_image, "convert"):
                return str(imagehash.phash(pil_image.convert("RGB")))
        except ImportError:
            logger.debug("imagehash not available; phash omitted")
        except Exception:
            logger.exception("phash computation failed")
        return ""

    @staticmethod
    def _flatten_transitions(
        graph: StateGraph,
    ) -> list[tuple[str, str, str]]:
        """Convert the edge map into flat ``(src, key, dst)`` triples.

        ``StateGraph.edges`` is ``dict[tuple[str, str], str]`` keyed by
        ``(from_fp, to_fp)`` with the transition key as value.
        """
        result: list[tuple[str, str, str]] = []
        for (src, dst), key in graph.edges.items():
            result.append((src, key, dst))
        return result
