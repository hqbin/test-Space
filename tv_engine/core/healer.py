"""AI self-healing system for TV automation.

Implements a 3-phase repair strategy as defined in AUTOMATION_DESIGN.md section 5:
Phase 1 - Fast local repair (no LLM, millisecond level)
Phase 2 - LLM visual repair (with AI provider, second level)
Phase 3 - Local re-exploration (heavy repair for PATH_CHANGED)
"""

from __future__ import annotations

import difflib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class AIProvider:
    """AI provider configuration matching Test Space aiSettings.ts schema.

    Read from the existing Test Space ``aiSettings`` store (SQLite ``app_settings`` table).
    """

    provider: str  # 'azure' | 'openai' | 'deepseek' | 'custom'
    endpoint: str
    api_key: str
    model: str

    def is_configured(self) -> bool:
        """Return True if all required fields are present and non-empty."""
        return bool(self.api_key.strip() and self.endpoint.strip() and self.model.strip())


@dataclass
class HealResult:
    """Result of a single healing attempt."""

    success: bool
    phase: int  # 1, 2, or 3
    method: str  # 'fingerprint' | 'semantic' | 'popup' | 'llm' | 're_explore'
    confidence: float  # 0-1
    description: str  # human-readable summary
    repair_actions: list[dict] = field(default_factory=list)
    new_target: Optional[dict] = None
    update_suggestion: Optional[str] = None


class DeviceController:
    """Stub for :mod:`tv_engine.core.device.DeviceController`.

    Replace with the real implementation when ``device.py`` is available.
    """

    def __init__(self, serial: str = ""):
        self.serial = serial

    def get_ui_tree(self) -> dict:
        return {"elements": [], "activity": "com.example.tv.MainActivity"}

    def get_focused_element(self) -> Optional[dict]:
        return None

    def get_focusable_elements(self) -> list[dict]:
        return []

    def press_key(self, key: str) -> bool:
        return True

    def screenshot(self) -> Any:
        from PIL import Image
        return Image.new("RGB", (1920, 1080), (0, 0, 0))

    def get_current_activity(self) -> str:
        return "com.example.tv.MainActivity"

    def wait_stable(self, timeout: int = 3000) -> bool:
        return True


class Healer:
    """3-phase AI self-healing system.

    Each phase is attempted in order of increasing cost:

    **Phase 1** — Fast local repair (no LLM):
        1a. Multi-attribute fingerprint match — try all fallback levels
        1b. Semantic similarity match — edit distance on element properties
        1c. Popup detection & auto-close — detect dialogs, close them, retry

    **Phase 2** — LLM visual repair (if an *AI provider* is configured):
        2a. Build multimodal prompt
        2b. Call AI provider, parse JSON response
        2c. Execute repair action, verify result

    **Phase 3** — Local re-exploration (for ``PATH_CHANGED``):
        3a. From current activity, re-explore reachable states
        3b. Find matching state, update local graph
        3c. Replan navigation path
    """

    def __init__(self, device: DeviceController, ai_provider: Optional[AIProvider] = None):
        self.device = device
        self.ai_provider = ai_provider

    # ── Public API ──────────────────────────────────────────────────────

    def heal(self, step: dict, error: str, context: dict) -> HealResult:
        """Run the full 3-phase healing pipeline against *step*.

        Parameters
        ----------
        step:
            The step definition (from parsed YAML).
        error:
            The error message that triggered the heal.
        context:
            Runtime context (current screenshot path, UI tree, activity,
            reference screenshot path, …).

        Returns
        -------
        HealResult
            The result of the best healing attempt.
        """
        phases: list[tuple[str, Any]] = [
            ("phase1_local", self._phase1_local),
            ("phase2_llm", lambda: self._phase2_llm(step, error, context)),
            ("phase3_re_explore", lambda: self._phase3_re_explore(step, context)),
        ]

        last_result = HealResult(
            success=False,
            phase=0,
            method="none",
            confidence=0.0,
            description="All healing phases exhausted",
        )

        for phase_name, phase_fn in phases:
            try:
                result = phase_fn(step, context) if phase_name == "phase1_local" else phase_fn()
                if result is None:
                    continue
                last_result = result
                if result.success:
                    logger.info("Heal succeeded in %s: %s", phase_name, result.description)
                    return result
            except Exception:
                logger.exception("Heal phase %s failed with exception", phase_name)

        return last_result

    # ── Phase 1: Fast local repair (no LLM) ─────────────────────────────

    def _phase1_local(self, step: dict, context: dict) -> Optional[HealResult]:
        """Run all Phase-1 strategies in order."""
        strategies: list[tuple[str, Any, int]] = [
            ("fingerprint", self._phase1a_fingerprint, 1),
            ("semantic", self._phase1b_semantic, 1),
            ("popup", self._phase1c_popup_internal, 1),
        ]

        for method_name, strategy_fn, phase in strategies:
            try:
                result = strategy_fn(step, context) if method_name != "popup" else strategy_fn()
                if result is None:
                    continue
                if isinstance(result, bool):
                    if result:
                        return HealResult(
                            success=True,
                            phase=phase,
                            method=method_name,
                            confidence=0.85,
                            description="Popup detected and auto-closed",
                            repair_actions=[{"action": "close_popup"}],
                        )
                    continue
                if result.success:
                    return result
            except Exception:
                logger.exception("Phase 1 strategy %s failed", method_name)

        return None

    def _phase1a_fingerprint(self, step: dict) -> Optional[HealResult]:
        """Multi-attribute fingerprint match — try all fallback levels.

        Iterates over ``step["target"]`` fallback levels (``primary``,
        ``fallback1``, … *fallback3*) and attempts to locate the element with
        each.  Returns a :class:`HealResult` on the first success.
        """
        target = step.get("target", {})
        fallback_keys = ["primary", "fallback1", "fallback2", "fallback3"]
        elements = self.device.get_focusable_elements()

        for level in fallback_keys:
            locator = target.get(level)
            if not locator:
                continue
            by = locator.get("by", "")
            value = locator.get("value", "")

            matched = self._match_elements(elements, by, value)
            if matched is not None:
                return HealResult(
                    success=True,
                    phase=1,
                    method="fingerprint",
                    confidence=0.95,
                    description=f"Element found via {level} ({by}={value})",
                    repair_actions=[{"level": level, "by": by, "value": value}],
                    new_target={level: locator},
                    update_suggestion=f"Consider updating target: {level} matched successfully",
                )

        return None

    def _match_elements(self, elements: list[dict], by: str, value: Any) -> Optional[dict]:
        """Match *elements* against a single locator criterion."""
        value_str = str(value).lower().strip()
        for el in elements:
            el_id = str(el.get("resource_id", "")).lower().strip()
            el_desc = str(el.get("content_desc", "")).lower().strip()
            el_text = str(el.get("text", "")).lower().strip()

            if by == "resource_id" and el_id == value_str:
                return el
            if by == "content_desc" and el_desc == value_str:
                return el
            if by == "text" and el_text == value_str:
                return el
            if by == "text_contains" and value_str in el_text:
                return el
            if by == "index":
                try:
                    idx = int(value)
                    if elements.index(el) == idx:
                        return el
                except (ValueError, IndexError):
                    continue
            if by in ("class_and_index",):
                cls = str(locator.get("class", "")) if isinstance(value, dict) else ""
                idx = int(locator.get("index", 0)) if isinstance(value, dict) else 0
                if el.get("class_name") == cls and elements.index(el) == idx:
                    return el

        return None

    def _phase1b_semantic(self, step: dict, context: dict) -> Optional[HealResult]:
        """Semantic similarity match — edit distance on element properties.

        Computes the *edit distance* (ratio) between each focusable element's
        ``resource_id``, ``content_desc``, and ``text`` and the target values
        from *step*.  The best match above the threshold (0.8) is returned.
        """
        target = step.get("target", {})
        elements = self.device.get_focusable_elements()
        if not elements:
            return None

        all_values: list[str] = []
        for level in ("primary", "fallback1", "fallback2", "fallback3"):
            loc = target.get(level)
            if loc:
                val = str(loc.get("value", ""))
                if val:
                    all_values.append(val.lower().strip())

        if not all_values:
            return None

        best_score = 0.0
        best_element: Optional[dict] = None
        best_value = ""

        for el in elements:
            el_fields = [
                str(el.get("resource_id", "")).lower().strip(),
                str(el.get("content_desc", "")).lower().strip(),
                str(el.get("text", "")).lower().strip(),
            ]
            for field in el_fields:
                if not field:
                    continue
                for expected in all_values:
                    score = self._similarity(field, expected)
                    if score > best_score:
                        best_score = score
                        best_element = el
                        best_value = expected

        if best_element is not None and best_score >= 0.8:
            return HealResult(
                success=True,
                phase=1,
                method="semantic",
                confidence=round(best_score, 4),
                description=f"Semantic match: score={best_score:.2f} value='{best_value}'",
                repair_actions=[{"element": best_element}],
                new_target={"primary": {"by": "resource_id", "value": best_element.get("resource_id", "")}},
                update_suggestion=f"Semantic match found: '{best_value}' -> '{best_element.get('resource_id', '')}'",
            )

        return None

    def _similarity(self, a: str, b: str) -> float:
        """Return ``difflib`` ratio (0-1) between two strings."""
        return difflib.SequenceMatcher(None, a, b).ratio()

    def _phase1c_popup_internal(self, step: dict = None, context: dict = None) -> bool:
        """Detect and auto-close unexpected dialogs.

        Inspects the current UI tree for ``Dialog``, ``AlertDialog``, or
        ``PopupWindow`` nodes.  If any are found, presses BACK (or attempts
        to locate a close/dismiss button) to dismiss them.

        Returns ``True`` if a popup was detected and closed.
        """
        return self._phase1c_popup()

    def _phase1c_popup(self) -> bool:
        """Detect and auto-close unexpected dialogs."""
        ui_tree = self.device.get_ui_tree()
        elements = ui_tree.get("elements", [])

        popup_keywords = ("dialog", "alertdialog", "popupwindow", "dialog_title")
        popup_found = False

        for el in elements:
            class_name = str(el.get("class_name", "")).lower()
            resource_id = str(el.get("resource_id", "")).lower()
            if any(kw in class_name or kw in resource_id for kw in popup_keywords):
                popup_found = True
                break

        if not popup_found:
            return False

        close_button = self._find_close_button(elements)
        if close_button:
            logger.info("Closing popup via button: %s", close_button.get("resource_id"))
            self.device.press_key("DPAD_CENTER")
            self.device.wait_stable(500)
            return True

        logger.info("No close button found, pressing BACK")
        self.device.press_key("BACK")
        self.device.wait_stable(800)
        return True

    def _find_close_button(self, elements: list[dict]) -> Optional[dict]:
        """Find a close/dismiss button among UI elements."""
        keywords = ("close", "cancel", "dismiss", "ok", "confirm", "got it", "知道了", "关闭", "取消")
        for el in elements:
            text = str(el.get("text", "")).lower().strip()
            desc = str(el.get("content_desc", "")).lower().strip()
            rid = str(el.get("resource_id", "")).lower().strip()
            combined = f"{text} {desc} {rid}"
            if any(kw in combined for kw in keywords):
                return el
            if "close" in rid or "cancel" in rid:
                return el
        return None

    # ── Phase 2: LLM visual repair ──────────────────────────────────────

    def _phase2_llm(self, step: dict, error: str, context: dict) -> Optional[HealResult]:
        """Build a multimodal prompt, call the AI provider, and execute the
        suggested repair action.

        Returns ``None`` if the AI provider is not configured or the call
        fails.
        """
        if not self.ai_provider or not self.ai_provider.is_configured():
            return None

        ref_screenshot = context.get("ref_screenshot_path", "")
        current_screenshot = context.get("current_screenshot_path", "")
        ui_tree = context.get("ui_tree", self.device.get_ui_tree())

        messages = self._build_llm_prompt(step, error, ref_screenshot, current_screenshot, ui_tree)
        try:
            response_text = self._call_llm(messages)
        except Exception:
            logger.exception("LLM call failed, falling back")
            return None

        try:
            repair = self._parse_llm_response(response_text)
        except (json.JSONDecodeError, ValueError, KeyError):
            logger.exception("Failed to parse LLM response")
            return None

        confidence = float(repair.get("confidence", 0.5))
        repair_action = repair.get("repair_action", "")
        new_target = repair.get("new_target")

        if repair_action and new_target:
            self._execute_repair_action(repair_action, repair.get("additional_steps", []))
            return HealResult(
                success=True,
                phase=2,
                method="llm",
                confidence=confidence,
                description=repair.get("analysis", "LLM-guided repair executed"),
                repair_actions=[repair],
                new_target=new_target,
                update_suggestion=repair.get("update_suggestion"),
            )

        return HealResult(
            success=False,
            phase=2,
            method="llm",
            confidence=confidence,
            description=repair.get("analysis", "LLM repair proposed no actionable fix"),
            repair_actions=[repair],
        )

    def _build_llm_prompt(
        self,
        step: dict,
        error: str,
        ref_screenshot: str,
        current_screenshot: str,
        ui_tree: dict,
    ) -> list[dict]:
        """Build the multimodal message list for the LLM call.

        Returns a list of message dicts compatible with the OpenAI chat
        completions format.  Image references are encoded as base64 data URIs
        when the corresponding screenshot paths exist.
        """
        step_yaml = json.dumps(step, ensure_ascii=False, indent=2)
        ui_summary = self._summarize_ui_tree(ui_tree)

        system_prompt = (
            "You are an Android TV UI automation repair expert.\n"
            "Analyze why the automation step failed and provide a repair plan."
        )

        user_content: list[dict] = [
            {"type": "text", "text": f"## Step Definition\n```json\n{step_yaml}\n```"},
            {"type": "text", "text": f"## Error\n{error}"},
        ]

        for label, path in [("Reference screenshot (success case)", ref_screenshot),
                             ("Current screenshot (failure case)", current_screenshot)]:
            if path:
                try:
                    from PIL import Image
                    import base64, io
                    img = Image.open(path)
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                    user_content.append({"type": "text", "text": f"### {label}"})
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    })
                except Exception:
                    user_content.append({"type": "text", "text": f"### {label}\n[Image unavailable: {path}]"})

        user_content.append({"type": "text", "text": f"## Current UI Tree Summary\n{ui_summary}"})
        user_content.append({
            "type": "text",
            "text": (
                "\nRespond in JSON format:\n"
                "{\n"
                '  "failure_type": "UI_ELEMENT_MOVED|UI_ELEMENT_RENAMED|UI_ELEMENT_MISSING|'
                "NAVIGATION_PATH_CHANGED|PAGE_LOAD_TIMEOUT|UNEXPECTED_DIALOG|APP_CRASH_OR_ANR\",\n"
                '  "analysis": "reason (one sentence)",\n'
                '  "repair_action": "navigate_to|press_key|wait_for|...",\n'
                '  "new_target": {"primary": {"by": "...", "value": "..."}},\n'
                '  "additional_steps": [],\n'
                '  "confidence": 0.85,\n'
                '  "update_suggestion": "..."\n'
                "}"
            ),
        })

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

    def _summarize_ui_tree(self, ui_tree: dict, max_chars: int = 3000) -> str:
        """Extract and truncate the core UI tree nodes to *max_chars*."""
        elements = ui_tree.get("elements", [])
        lines: list[str] = []
        for el in elements[:100]:
            rid = el.get("resource_id", "")
            desc = el.get("content_desc", "")
            text = el.get("text", "")
            cls = el.get("class_name", "")
            bounds = el.get("bounds", "")
            focused = el.get("focused", False)
            line = f"  {cls} id={rid} desc={desc} text={text} bounds={bounds} focused={focused}"
            lines.append(line)

        summary = f"Activity: {ui_tree.get('activity', 'unknown')}\nElements:\n" + "\n".join(lines)
        if len(summary) > max_chars:
            summary = summary[:max_chars] + "\n... (truncated)"
        return summary

    def _call_llm(self, messages: list[dict]) -> str:
        """Call the configured AI provider and return the response text."""
        import requests

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.ai_provider.api_key}",
        }

        payload = {
            "model": self.ai_provider.model,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.3,
        }

        endpoint = self.ai_provider.endpoint.rstrip("/")
        if not endpoint.endswith("/chat/completions"):
            if "openai.azure.com" in endpoint:
                endpoint = endpoint.rstrip("/") + "/chat/completions"
            else:
                endpoint = endpoint.rstrip("/") + "/chat/completions"

        resp = requests.post(endpoint, headers=headers, json=payload, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _parse_llm_response(self, response: str) -> dict:
        """Parse the LLM response string into a repair dict.

        Attempts to extract a JSON block from the response using a regex
        fallback if the raw text is not valid JSON.
        """
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise

    def _execute_repair_action(self, action: str, additional_steps: list[dict]) -> None:
        """Execute a repair action returned by the LLM."""
        action_map: dict[str, Any] = {
            "press_key": lambda kw: self.device.press_key(kw.get("key", "DPAD_CENTER")),
            "navigate_to": lambda kw: self.device.press_key("DPAD_CENTER"),
            "wait_for": lambda kw: self.device.wait_stable(kw.get("timeout", 3000)),
            "close_popup": lambda kw: self._phase1c_popup(),
        }
        handler = action_map.get(action)
        if handler:
            handler({})

        for step_def in additional_steps:
            sub_action = step_def.get("action", "")
            sub_handler = action_map.get(sub_action)
            if sub_handler:
                sub_handler(step_def)

    # ── Phase 3: Local re-exploration ───────────────────────────────────

    def _phase3_re_explore(self, step: dict, context: dict) -> Optional[HealResult]:
        """Re-explore from the current activity to find the target element.

        From the current activity, enumerates reachable focusable elements and
        tries to locate a state that matches the step's target.  If a match is
        found the local graph is updated and a navigation path is re-planned.
        """
        current_activity = self.device.get_current_activity()
        target = step.get("target", {})
        elements = self.device.get_focusable_elements()

        if not elements:
            return None

        matched = None
        for level in ("primary", "fallback1", "fallback2", "fallback3"):
            loc = target.get(level)
            if not loc:
                continue
            by = loc.get("by", "")
            value = loc.get("value", "")
            matched = self._match_elements(elements, by, value)
            if matched is not None:
                break

        if matched is not None:
            return HealResult(
                success=True,
                phase=3,
                method="re_explore",
                confidence=0.80,
                description=f"Re-explored from {current_activity}, found matching element",
                repair_actions=[{"activity": current_activity, "element": matched}],
                new_target={"primary": {"by": "resource_id", "value": matched.get("resource_id", "")}},
                update_suggestion=f"Navigation path changed from {current_activity}; consider re-recording",
            )

        return HealResult(
            success=False,
            phase=3,
            method="re_explore",
            confidence=0.0,
            description=f"Re-exploration from {current_activity} found no matching element",
            update_suggestion="Full re-exploration recommended for this activity",
        )
