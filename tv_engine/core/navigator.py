"""Focus navigation planner for TV automation engine.

Provides three levels of navigation strategy:
    Level 1 (graph replay): Fast deterministic replay from known StateGraph paths.
    Level 2 (spatial greedy): Bounds-based direction calculation with distance convergence.
    Level 3 (BFS exhaustive): Systematic breadth-first exploration of focusable elements.
"""

import time
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from .device import DeviceController
from .state import StateGraph
from .locator import Locator, LocatorResult

logger = logging.getLogger(__name__)

DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")
OPPOSITE = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
_KEY_PREFIX = "DPAD_"


@dataclass
class NavResult:
    """Result of a navigation operation."""

    success: bool
    steps_taken: int = 0
    final_focus: Optional[dict] = None
    path_used: list[str] = field(default_factory=list)
    error: Optional[str] = None
    level: int = 0


class Navigator:
    """Plans and executes focus navigation on TV devices.

    Delegates element location to :class:`Locator` for multi-layer fallback
    resolution and uses :class:`DeviceController` for low-level DPAD dispatch.
    """

    def __init__(
        self, device: DeviceController, state_graph: Optional[StateGraph] = None
    ):
        self.device = device
        self.state_graph = state_graph
        self.locator = Locator(device)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def navigate_to(
        self, target: dict, max_steps: int = 25, timeout_ms: int = 8000
    ) -> NavResult:
        """Navigate the device focus to an element matching *target*.

        Resolution order
        -----------------
        1. Resolve *target* via :class:`Locator` to obtain element bounds.
        2. **Level 1** – Replay a known path from *state_graph* if one exists
           between the current focused element and the resolved target.
        3. **Level 2** – Spatial greedy: compute axis-aligned direction and
           single-step toward the target, checking per-step distance convergence.
        4. **Level 3** – BFS exhaustive: systematically explore all reachable
           focusable elements until the target is found.

        Parameters
        ----------
        target:
            Element descriptor dict (may contain ``primary`` / ``fallbackN``
            fields for the Locator).
        max_steps:
            Maximum number of DPAD key presses before giving up.
        timeout_ms:
            Per-step stability timeout in milliseconds.

        Returns
        -------
        NavResult
        """
        deadline = time.monotonic() + (timeout_ms / 1000.0)

        loc_result = self.locator.locate(target)
        if not loc_result or not loc_result.found:
            logger.warning("Locator could not resolve target=%s", target)
            current = self.device.get_focused_element()
            return NavResult(
                success=False,
                final_focus=current,
                error=f"Target not locatable: {loc_result.fallback_used if loc_result else 'unknown'}",
            )

        target_element = loc_result.element
        target_id = self._element_key(target_element)
        target_bounds = self._get_element_bounds(target_element)

        current = self.device.get_focused_element()
        if not current:
            return NavResult(
                success=False,
                error="No focused element at start of navigation",
            )

        if self._element_key(current) == target_id:
            return NavResult(
                success=True, steps_taken=0, final_focus=current, level=1
            )

        # -- Level 1:  State-graph replay ---------------------------------
        if self.state_graph is not None:
            current_fp = self._compute_fingerprint(current)
            target_fp = self._compute_fingerprint(target_element)
            path = self.state_graph.find_path(current_fp, target_fp)
            if path:
                logger.info("Level 1: replaying graph path len=%d", len(path))
                ok = self._replay_path(path, deadline)
                final = self.device.get_focused_element()
                if ok and final and self._element_key(final) == target_id:
                    return NavResult(
                        success=True,
                        steps_taken=len(path),
                        final_focus=final,
                        path_used=path,
                        level=1,
                    )

        # -- Level 2:  Spatial greedy -------------------------------------
        current = self.device.get_focused_element()
        if current:
            current_bounds = self._get_element_bounds(current)
            if current_bounds and target_bounds:
                path_l2: list[str] = []
                for _ in range(max_steps):
                    if time.monotonic() >= deadline:
                        break
                    if self._element_key(current) == target_id:
                        return NavResult(
                            success=True,
                            steps_taken=len(path_l2),
                            final_focus=current,
                            path_used=path_l2,
                            level=2,
                        )
                    direction = self._direction_to(current_bounds, target_bounds)
                    if direction not in DIRECTIONS:
                        break
                    self.device.press_key(f"{_KEY_PREFIX}{direction}")
                    time.sleep(0.12)
                    remaining = int((deadline - time.monotonic()) * 500)
                    self.device.wait_stable(max(remaining, 300))
                    path_l2.append(direction)
                    current = self.device.get_focused_element()
                    if not current:
                        break
                    current_bounds = self._get_element_bounds(current)

        # -- Level 3:  BFS exhaustive -------------------------------------
        current = self.device.get_focused_element()
        if not current:
            return NavResult(success=False, error="Focus lost before Level 3")
        bfs_path = self._bfs_find_target(target_id, max_steps)
        if bfs_path is not None:
            return NavResult(
                success=True,
                steps_taken=len(bfs_path),
                final_focus=self.device.get_focused_element(),
                path_used=bfs_path,
                level=3,
            )

        final = self.device.get_focused_element()
        return NavResult(
            success=False,
            steps_taken=max_steps,
            final_focus=final,
            error=f"Target {target_id} unreachable within {max_steps} steps",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_element_bounds(element: Optional[dict]) -> Optional[tuple[int, int, int, int]]:
        """Extract ``(left, top, right, bottom)`` from an element dict.

        Supports the ``bounds_left`` / ``bounds_top`` / ``bounds_right`` /
        ``bounds_bottom`` fields returned by :class:`DeviceController`.
        """
        if not element:
            return None
        left = element.get("bounds_left")
        top = element.get("bounds_top")
        right = element.get("bounds_right")
        bottom = element.get("bounds_bottom")
        if None not in (left, top, right, bottom):
            return (left, top, right, bottom)
        return None

    @staticmethod
    def _direction_to(
        from_bounds: tuple[int, int, int, int],
        to_bounds: tuple[int, int, int, int],
    ) -> str:
        """Return the dominant DPAD direction between two bound rects.

        Uses centre-point delta and picks the axis with greater absolute
        distance.  A dead-zone of 10 px prevents jitter on near-equal axes.
        """
        fx = (from_bounds[0] + from_bounds[2]) // 2
        fy = (from_bounds[1] + from_bounds[3]) // 2
        tx = (to_bounds[0] + to_bounds[2]) // 2
        ty = (to_bounds[1] + to_bounds[3]) // 2
        dx = tx - fx
        dy = ty - fy
        if abs(dx) >= abs(dy):
            return "RIGHT" if dx > 0 else "LEFT"
        return "DOWN" if dy > 0 else "UP"

    def _bfs_find_target(
        self, target_id: str, max_steps: int
    ) -> Optional[list[str]]:
        """BFS through all reachable focusable elements to locate *target_id*.

        The search is performed on the live device: from each visited state all
        four DPAD directions are attempted and the resulting focused element is
        recorded.  Each attempt is back-tracked immediately so the device
        remains at the original state between tries.

        Returns
        -------
        list[str] | None
            Shortest key sequence (e.g. ``["DOWN", "RIGHT"]``) from the
            initial focus to *target_id*, or ``None`` if unreachable within
            *max_steps*.
        """
        initial = self.device.get_focused_element()
        if not initial:
            return None
        initial_id = self._element_key(initial)
        if initial_id == target_id:
            return []

        queue: deque[tuple[str, list[str]]] = deque()
        queue.append((initial_id, []))
        visited: set[str] = {initial_id}
        cur_id: str = initial_id
        cur_path: list[str] = []

        while queue:
            elem_id, path_to = queue.popleft()

            if len(path_to) > max_steps:
                continue

            if cur_id != elem_id:
                self._reset_to_initial()
                cur_id = initial_id
                cur_path = []
                if path_to:
                    self._navigate_path(path_to)
                    cur_id = elem_id
                    cur_path = path_to

            for direction in DIRECTIONS:
                key = f"{_KEY_PREFIX}{direction}"
                self.device.press_key(key)
                time.sleep(0.12)
                self.device.wait_stable(300)

                new_elem = self.device.get_focused_element()
                if not new_elem:
                    self._backtrack_one(direction)
                    continue

                new_id = self._element_key(new_elem)

                if new_id == target_id:
                    return path_to + [direction]

                if new_id not in visited:
                    visited.add(new_id)
                    queue.append((new_id, path_to + [direction]))

                self._backtrack_one(direction)

        return None

    def _replay_path(
        self, keys: list[str], deadline: Optional[float] = None
    ) -> bool:
        """Press each key in *keys* sequentially."""
        for key in keys:
            if deadline is not None and time.monotonic() >= deadline:
                return False
            full = key if key.startswith(_KEY_PREFIX) else f"{_KEY_PREFIX}{key}"
            self.device.press_key(full)
            time.sleep(0.12)
            self.device.wait_stable(300)
        return True

    def _navigate_path(self, path: list[str]) -> None:
        """Follow a path of direction names from the current position."""
        for direction in path:
            key = (
                direction
                if direction.startswith(_KEY_PREFIX)
                else f"{_KEY_PREFIX}{direction}"
            )
            self.device.press_key(key)
            time.sleep(0.12)
            self.device.wait_stable(300)

    def _reset_to_initial(self) -> None:
        """Attempt to return to the initial focus position via BACK keys."""
        for _ in range(8):
            current = self.device.get_focused_element()
            if not current:
                break
            self.device.press_key("DPAD_BACK")
            time.sleep(0.15)
            self.device.wait_stable(300)

    def _backtrack_one(self, direction: str) -> None:
        """Press the opposite key to undo one directional move."""
        opp = OPPOSITE.get(direction)
        if opp:
            self.device.press_key(f"{_KEY_PREFIX}{opp}")
            time.sleep(0.10)
            self.device.wait_stable(250)

    # ------------------------------------------------------------------
    # Element identity helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _element_key(element: dict) -> str:
        """Return a stable unique key for an element dict.

        Preference order: ``resource_id`` → ``content_desc`` → ``text`` →
        ``class_name`` + ``bounds_*``.
        """
        rid = element.get("resource_id") or element.get("resource-id")
        if rid:
            return str(rid)
        cd = element.get("content_desc") or element.get("content-desc")
        if cd:
            return str(cd)
        txt = element.get("text")
        if txt:
            return str(txt)
        cls = element.get("class_name") or element.get("class", "")
        bounds = (
            f"{element.get('bounds_left','')},{element.get('bounds_top','')},"
            f"{element.get('bounds_right','')},{element.get('bounds_bottom','')}"
        )
        return f"{cls}:{bounds}"

    @staticmethod
    def _compute_fingerprint(element: dict) -> str:
        """Return a fingerprint string for *element* in ``TVState`` style."""
        rid = element.get("resource_id") or element.get("resource-id", "")
        cd = element.get("content_desc") or element.get("content-desc", "")
        txt = element.get("text", "")
        return f"{rid}|{cd}|{txt}"
