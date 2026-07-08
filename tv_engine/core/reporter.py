"""HTML report generator for TV automation suites.

Generates self-contained bilingual (zh/en) HTML reports matching Test Space's
glass-panel design language as specified in AUTOMATION_DESIGN.md section 6.
All CSS and JS is inlined — each report is a single zero-dependency HTML file.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── Data models ─────────────────────────────────────────────────────────


@dataclass
class StepResult:
    """Result of a single test step."""

    step_id: str
    desc: str
    action: str
    status: str  # passed | failed | healed | skipped | running
    duration_ms: int
    error: Optional[str] = None
    heal_log: Optional[list[dict]] = None
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    screenshot_ref: Optional[str] = None
    locator_used: Optional[str] = None


@dataclass
class CaseResult:
    """Result of a single test case."""

    case_id: str
    name: str
    author: str = ""
    priority: str = "P2"
    tags: list[str] = field(default_factory=list)
    description: str = ""
    status: str = "passed"  # passed | failed | aborted
    duration_ms: int = 0
    passed: int = 0
    failed: int = 0
    healed: int = 0
    skipped: int = 0
    total: int = 0
    steps: list[StepResult] = field(default_factory=list)
    device_serial: str = ""
    device_info: str = ""
    app_version: str = ""


@dataclass
class SuiteResult:
    """Result of an entire suite run."""

    run_id: str
    title: str = "Test Space Automation Report"
    started_at: str = ""
    ended_at: str = ""
    device_serial: str = ""
    device_info: str = ""
    app_package: str = ""
    app_version: str = ""
    total: int = 0
    passed: int = 0
    failed: int = 0
    healed: int = 0
    skipped: int = 0
    duration_ms: int = 0
    cases: list[CaseResult] = field(default_factory=list)
    previous_run: Optional[dict[str, int]] = None  # {passed, failed, healed, total}


# ── Reporter ────────────────────────────────────────────────────────────


class Reporter:
    """Self-contained bilingual HTML report generator.

    Parameters
    ----------
    output_dir:
        Root directory under which per-run report folders are created.
    """

    _COLORS = {
        "passed": "#22c55e",
        "failed": "#ef4444",
        "healed": "#f97316",
        "skipped": "#94a3b8",
        "running": "#3b82f6",
    }

    _STATUS_ICONS = {
        "passed": "&#x2714;",
        "failed": "&#x2718;",
        "healed": "&#x1f527;",
        "skipped": "&#x23ed;",
        "running": "&#x23f3;",
    }

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Suite report ────────────────────────────────────────────────────

    def generate_suite_report(self, suite_result: SuiteResult, output_path: str) -> str:
        """Generate the top-level suite ``index.html``.

        Returns the absolute path of the generated file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        metric_cards = self._render_metric_cards(suite_result)
        case_cards = self._render_case_cards(suite_result.cases)
        status_bar = self._render_status_bar(suite_result)
        tag_filters = self._render_tag_filters(suite_result.cases)
        trend_html = self._render_trend_comparison(suite_result)
        device_info = self._format_device_info(suite_result)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self._escape(suite_result.title)}</title>
{self._inline_css()}
<style>
.glass-header{{background:rgba(255,255,255,0.85);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-bottom:1px solid rgba(0,0,0,0.06);position:sticky;top:0;z-index:100;padding:16px 32px;}}
.metric-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;padding:24px 32px;}}
.metric-card{{border-radius:16px;padding:20px;color:#fff;box-shadow:0 4px 20px rgba(0,0,0,0.08);transition:transform 0.2s;}}
.metric-card:hover{{transform:translateY(-2px);}}
.metric-card .num{{font-size:36px;font-weight:700;line-height:1.2;}}
.metric-card .label{{font-size:14px;opacity:0.9;margin-top:4px;}}
.bg-passed{{background:linear-gradient(135deg,#22c55e,#16a34a);}}
.bg-failed{{background:linear-gradient(135deg,#ef4444,#dc2626);}}
.bg-healed{{background:linear-gradient(135deg,#f97316,#ea580c);}}
.bg-total{{background:linear-gradient(135deg,#3b82f6,#2563eb);}}
.bg-skipped{{background:linear-gradient(135deg,#94a3b8,#64748b);}}
.status-bar{{height:8px;border-radius:4px;background:#e2e8f0;overflow:hidden;margin:0 32px;}}
.status-bar-fill{{height:100%;transition:width 0.6s ease;}}
.filter-bar{{padding:16px 32px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;}}
.filter-btn{{padding:6px 14px;border-radius:20px;border:1px solid #e2e8f0;background:#fff;cursor:pointer;font-size:13px;transition:all 0.2s;}}
.filter-btn.active{{background:#3b82f6;color:#fff;border-color:#3b82f6;}}
.filter-btn:hover{{border-color:#3b82f6;}}
.sort-select{{padding:6px 12px;border-radius:8px;border:1px solid #e2e8f0;font-size:13px;background:#fff;}}
.case-card{{background:#fff;border-radius:16px;padding:16px 20px;margin:0 32px 12px;box-shadow:0 2px 8px rgba(0,0,0,0.04);transition:box-shadow 0.2s;cursor:pointer;}}
.case-card:hover{{box-shadow:0 4px 16px rgba(0,0,0,0.08);}}
.case-card .status-icon{{font-size:20px;margin-right:10px;}}
.case-card .case-title{{font-weight:600;font-size:15px;}}
.case-card .case-meta{{font-size:12px;color:#64748b;margin-top:4px;}}
.tag{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;}}
.trend-section{{padding:24px 32px;}}
</style>
</head>
<body style="margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f2f5;color:#1e293b;">
<div class="glass-header">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
    <div>
      <h1 style="margin:0;font-size:20px;font-weight:600;" data-i18n="suite_title">{self._escape(suite_result.title)}</h1>
      <div style="font-size:13px;color:#64748b;margin-top:4px;">
        <span data-i18n="run_time">执行时间</span>: {suite_result.started_at or '-'}
        &nbsp;|&nbsp; <span data-i18n="device">设备</span>: {device_info}
        &nbsp;|&nbsp; <span data-i18n="duration">耗时</span>: {self._format_duration(suite_result.duration_ms)}
      </div>
    </div>
    <div style="display:flex;gap:8px;align-items:center;">
      <button onclick="toggleLang()" style="padding:6px 14px;border-radius:8px;border:1px solid #e2e8f0;background:#fff;cursor:pointer;font-size:13px;">中/EN</button>
    </div>
  </div>
</div>

<div class="metric-grid">
  {metric_cards}
</div>

{status_bar}

<div class="filter-bar">
  <span style="font-size:13px;color:#64748b;" data-i18n="filter_tag">标签筛选</span>:
  {tag_filters}
  <span style="margin-left:16px;font-size:13px;color:#64748b;" data-i18n="sort">排序</span>:
  <select class="sort-select" onchange="sortCases(this.value)">
    <option value="priority" data-i18n="sort_priority">优先级</option>
    <option value="duration" data-i18n="sort_duration">耗时</option>
    <option value="status" data-i18n="sort_status">状态</option>
  </select>
</div>

<div id="case-list">
  {case_cards}
</div>

{trend_html}

{self._inline_js_i18n()}
<script>
let currentTag = 'all';
function filterByTag(tag) {{
  currentTag = tag;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.dataset.tag === tag));
  applyFilters();
}}
function sortCases(by) {{
  applyFilters();
}}
function applyFilters() {{
  const sortBy = document.querySelector('.sort-select').value;
  const cards = Array.from(document.querySelectorAll('.case-card'));
  const list = document.getElementById('case-list');
  cards.forEach(c => {{
    const tags = (c.dataset.tags || '').split(',');
    c.style.display = (currentTag === 'all' || tags.includes(currentTag)) ? '' : 'none';
  }});
  const visible = cards.filter(c => c.style.display !== 'none');
  visible.sort((a, b) => {{
    if (sortBy === 'priority') return (a.dataset.priority || 'P2').localeCompare(b.dataset.priority || 'P2');
    if (sortBy === 'duration') return parseInt(b.dataset.duration || '0') - parseInt(a.dataset.duration || '0');
    return (a.dataset.status || '').localeCompare(b.dataset.status || '');
  }});
  visible.forEach(c => list.appendChild(c));
}}
</script>
</body>
</html>"""

        output_path.write_text(html, encoding="utf-8")
        logger.info("Suite report generated: %s", output_path)
        return str(output_path.resolve())

    def _render_metric_cards(self, sr: SuiteResult) -> str:
        cards = [
            ("total", str(sr.total), "bg-total", "suite_total"),
            ("passed", str(sr.passed), "bg-passed", "suite_passed"),
            ("failed", str(sr.failed), "bg-failed", "suite_failed"),
            ("healed", str(sr.healed), "bg-healed", "suite_healed"),
        ]
        parts = []
        for key, value, bg_class, i18n_key in cards:
            parts.append(
                f'<div class="metric-card {bg_class}">'
                f'<div class="num">{value}</div>'
                f'<div class="label" data-i18n="{i18n_key}">{i18n_key}</div>'
                f"</div>"
            )
        return "\n".join(parts)

    def _render_status_bar(self, sr: SuiteResult) -> str:
        total = max(sr.total, 1)
        p_pct = sr.passed / total * 100
        f_pct = sr.failed / total * 100
        h_pct = sr.healed / total * 100
        s_pct = sr.skipped / total * 100
        return (
            f'<div class="status-bar">'
            f'<div class="status-bar-fill" style="width:{p_pct}%;background:#22c55e;display:inline-block;"></div>'
            f'<div class="status-bar-fill" style="width:{h_pct}%;background:#f97316;display:inline-block;"></div>'
            f'<div class="status-bar-fill" style="width:{f_pct}%;background:#ef4444;display:inline-block;"></div>'
            f'<div class="status-bar-fill" style="width:{s_pct}%;background:#94a3b8;display:inline-block;"></div>'
            f"</div>"
        )

    def _render_tag_filters(self, cases: list[CaseResult]) -> str:
        all_tags: set[str] = set()
        for c in cases:
            all_tags.update(c.tags)
        sorted_tags = sorted(all_tags)
        buttons = ['<button class="filter-btn active" data-tag="all" onclick="filterByTag(\'all\')" data-i18n="all">全部</button>']
        for tag in sorted_tags:
            buttons.append(
                f'<button class="filter-btn" data-tag="{self._escape(tag)}" onclick="filterByTag(\'{self._escape(tag)}\')">{self._escape(tag)}</button>'
            )
        return " ".join(buttons)

    def _render_case_cards(self, cases: list[CaseResult]) -> str:
        parts = []
        for case in cases:
            icon = self._STATUS_ICONS.get(case.status, "&#x2753;")
            color = self._COLORS.get(case.status, "#94a3b8")
            tags_html = "".join(f'<span class="tag">{self._escape(t)}</span>' for t in case.tags)
            parts.append(
                f'<div class="case-card" data-tags="{",".join(case.tags)}" data-priority="{self._escape(case.priority)}" '
                f'data-duration="{case.duration_ms}" data-status="{case.status}" '
                f'onclick="location.href=\'./{self._escape(case.case_id)}/report.html\'">'
                f'<div style="display:flex;align-items:center;justify-content:space-between;">'
                f'<div style="display:flex;align-items:center;">'
                f'<span class="status-icon" style="color:{color}">{icon}</span>'
                f'<span class="case-title">{self._escape(case.name)}</span>'
                f'</div>'
                f'<span style="font-size:13px;color:#64748b;">{self._format_duration(case.duration_ms)}</span>'
                f'</div>'
                f'<div style="margin-top:6px;">{tags_html}</div>'
                f'<div class="case-meta">'
                f'{self._escape(case.author) if case.author else "-"}'
                f' &middot; {case.passed}/{case.total} <span data-i18n="steps_passed">步骤通过</span>'
                f'</div>'
                f"</div>"
            )
        return "\n".join(parts)

    def _render_trend_comparison(self, sr: SuiteResult) -> str:
        prev = sr.previous_run
        if prev is None:
            return ""
        new_failed = sr.failed - prev.get("failed", 0)
        new_healed = sr.healed - prev.get("healed", 0)
        new_total = sr.total - prev.get("total", 0)
        lines = [
            f'<div class="trend-section">'
            f'<h3 style="font-size:15px;margin:0 0 8px;" data-i18n="trend_title">与上次执行对比</h3>'
            f'<p style="font-size:13px;color:#64748b;margin:0;">'
        ]
        if new_failed != 0:
            sign = "+" if new_failed > 0 else ""
            color = "#ef4444" if new_failed > 0 else "#22c55e"
            lines.append(f'<span data-i18n="new_failed">新增失败</span>: <span style="color:{color}">{sign}{new_failed}</span> ')
        if new_healed != 0:
            lines.append(f'<span data-i18n="new_healed">新增修复</span>: {new_healed:+} ')
        if new_total != 0:
            lines.append(f'<span data-i18n="new_cases">新增用例</span>: {new_total:+}')
        if len(lines) == 2:
            lines.append('<span data-i18n="no_change">与上次执行无变化</span>')
        lines.append("</p></div>")
        return "\n".join(lines)

    # ── Case report ─────────────────────────────────────────────────────

    def generate_case_report(self, case_result: CaseResult, output_dir: str) -> str:
        """Generate a detailed case-level HTML report.

        Includes step timeline, before/after screenshots, AI heal records in
        orange, failure analysis with screenshot comparison, and diff overlay.
        Returns the absolute path of the generated file.
        """
        case_dir = Path(output_dir)
        case_dir.mkdir(parents=True, exist_ok=True)
        output_path = case_dir / "report.html"

        step_timeline = self._render_step_timeline(case_result)
        meta_tags = "".join(f'<span class="tag">{self._escape(t)}</span>' for t in case_result.tags)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self._escape(case_result.name)}</title>
{self._inline_css()}
<style>
.timeline{{position:relative;padding-left:32px;margin:24px 0;}}
.timeline::before{{content:'';position:absolute;left:12px;top:0;bottom:0;width:2px;background:#e2e8f0;}}
.step-card{{background:#fff;border-radius:16px;padding:16px 20px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,0.04);position:relative;}}
.step-card::before{{content:'';position:absolute;left:-24px;top:20px;width:12px;height:12px;border-radius:50%;border:2px solid #e2e8f0;background:#fff;}}
.step-card.status-passed::before{{background:#22c55e;border-color:#22c55e;}}
.step-card.status-failed::before{{background:#ef4444;border-color:#ef4444;}}
.step-card.status-healed::before{{background:#f97316;border-color:#f97316;}}
.step-card.status-skipped::before{{background:#94a3b8;border-color:#94a3b8;}}
.screenshot-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:8px;}}
.screenshot-grid img{{width:100%;border-radius:8px;border:1px solid #e2e8f0;}}
.heal-badge{{display:inline-block;padding:2px 10px;border-radius:10px;font-size:11px;background:#fef3c7;color:#d97706;font-weight:500;margin-left:6px;}}
.diff-overlay{{position:relative;}}
</style>
</head>
<body style="margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f2f5;color:#1e293b;">
<div class="glass-header" style="padding:12px 24px;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
    <div style="display:flex;align-items:center;gap:12px;">
      <a href="../index.html" style="color:#3b82f6;text-decoration:none;font-size:14px;" data-i18n="back_to_suite">&larr; 返回套件报告</a>
      <h1 style="margin:0;font-size:18px;font-weight:600;">{self._escape(case_result.name)}</h1>
    </div>
    <div style="font-size:13px;color:#64748b;">
      {meta_tags}
    </div>
  </div>
  <div style="font-size:12px;color:#64748b;margin-top:4px;">
    <span data-i18n="author">作者</span>: {self._escape(case_result.author) or '-'}
    &nbsp;|&nbsp; <span data-i18n="priority">优先级</span>: {self._escape(case_result.priority)}
    &nbsp;|&nbsp; <span data-i18n="duration">耗时</span>: {self._format_duration(case_result.duration_ms)}
  </div>
</div>

<div style="padding:16px 24px;">
  <div class="timeline">
    {step_timeline}
  </div>
</div>

{self._inline_js_i18n()}
</body>
</html>"""

        output_path.write_text(html, encoding="utf-8")
        logger.info("Case report generated: %s", output_path)
        return str(output_path.resolve())

    def _render_step_timeline(self, case: CaseResult) -> str:
        parts = []
        for step in case.steps:
            icon = self._STATUS_ICONS.get(step.status, "&#x2753;")
            color = self._COLORS.get(step.status, "#94a3b8")
            heal_badge = ""
            heal_details = ""

            if step.heal_log:
                for log_entry in step.heal_log:
                    phase = log_entry.get("phase", "?")
                    method = log_entry.get("method", "?")
                    conf = log_entry.get("confidence", 0)
                    desc = log_entry.get("description", "")
                    heal_badge = '<span class="heal-badge">AI</span>'
                    heal_details = (
                        f'<div style="margin-top:8px;padding:8px 12px;background:#fffbeb;border-radius:8px;font-size:12px;color:#92400e;">'
                        f'<div><span data-i18n="heal_phase">修复阶段</span>: {phase} &middot; '
                        f'<span data-i18n="heal_method">方式</span>: {method} &middot; '
                        f'<span data-i18n="confidence">置信度</span>: {conf}</div>'
                        f'<div>{self._escape(desc)}</div>'
                        f'</div>'
                    )

            error_html = ""
            if step.error:
                error_html = (
                    f'<div style="margin-top:8px;padding:8px 12px;background:#fef2f2;border-radius:8px;font-size:12px;color:#991b1b;">'
                    f'<strong data-i18n="error">错误</strong>: {self._escape(step.error)}'
                    f'</div>'
                )

            screenshots_html = ""
            screens = []
            if step.screenshot_before:
                rel = self._relative_screenshot_path(step.screenshot_before)
                screens.append(f'<div><span style="font-size:11px;color:#64748b;" data-i18n="before">操作前</span><br><img src="{rel}" loading="lazy"></div>')
            if step.screenshot_after:
                rel = self._relative_screenshot_path(step.screenshot_after)
                screens.append(f'<div><span style="font-size:11px;color:#64748b;" data-i18n="after">操作后</span><br><img src="{rel}" loading="lazy"></div>')
            if step.screenshot_ref and step.status in ("failed", "healed"):
                rel = self._relative_screenshot_path(step.screenshot_ref)
                screens.append(f'<div><span style="font-size:11px;color:#64748b;" data-i18n="reference">参考</span><br><img src="{rel}" loading="lazy"></div>')
            if screens:
                screenshots_html = f'<div class="screenshot-grid">{" ".join(screens)}</div>'

            parts.append(
                f'<div class="step-card status-{step.status}">'
                f'<div style="display:flex;align-items:center;justify-content:space-between;">'
                f'<div style="display:flex;align-items:center;gap:6px;">'
                f'<span style="color:{color}">{icon}</span>'
                f'<strong style="font-size:13px;">{self._escape(step.step_id)}</strong>'
                f'<span style="font-size:13px;color:#475569;">{self._escape(step.desc)}</span>'
                f'{heal_badge}'
                f'</div>'
                f'<span style="font-size:12px;color:#94a3b8;">{self._format_duration(step.duration_ms)}</span>'
                f'</div>'
                f'<div style="font-size:12px;color:#94a3b8;margin-top:2px;">'
                f'<span data-i18n="action">操作</span>: {self._escape(step.action)}'
                f'{" &middot; " + self._escape(step.locator_used) if step.locator_used else ""}'
                f'</div>'
                f'{error_html}'
                f'{heal_details}'
                f'{screenshots_html}'
                f"</div>"
            )
        return "\n".join(parts)

    def _relative_screenshot_path(self, abs_path: str) -> str:
        """Convert an absolute screenshot path to one relative to the report."""
        if not abs_path:
            return ""
        try:
            rel = os.path.relpath(abs_path, self.output_dir)
            return rel.replace("\\", "/")
        except ValueError:
            return abs_path

    # ── Screenshot diff ─────────────────────────────────────────────────

    def _generate_screenshot_diff(self, expected_path: str, actual_path: str) -> str:
        """Generate a pixel-diff overlay image using Pillow.

        Returns a base64-encoded PNG data URI of the diff overlay (red
        semi-transparent mask on the actual screenshot).
        """
        try:
            from PIL import Image, ImageChops, ImageDraw
        except ImportError:
            logger.warning("Pillow not available for screenshot diff")
            return ""

        try:
            expected = Image.open(expected_path).convert("RGB")
            actual = Image.open(actual_path).convert("RGB")
        except Exception:
            logger.exception("Failed to open screenshots for diff")
            return ""

        if expected.size != actual.size:
            actual = actual.resize(expected.size, Image.LANCZOS)

        diff = ImageChops.difference(expected, actual).convert("L")
        threshold = 30
        mask = diff.point(lambda p: 255 if p > threshold else 0)

        if not mask.getbbox():
            return ""

        overlay = actual.convert("RGBA")
        red_overlay = Image.new("RGBA", overlay.size, (255, 0, 0, 80))
        overlay = Image.composite(red_overlay, overlay, mask)

        buf = io.BytesIO()
        overlay.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64}"

    # ── Export helpers ──────────────────────────────────────────────────

    def export_pdf(self, html_path: str, output_path: str) -> bool:
        """Export an HTML report to PDF.

        Uses ``weasyprint`` if available, otherwise falls back to a headless
        Chrome/Puppeteer subprocess call.

        Returns ``True`` on success.
        """
        try:
            import weasyprint
            weasyprint.HTML(filename=html_path).write_pdf(output_path)
            logger.info("PDF exported: %s", output_path)
            return True
        except ImportError:
            pass

        try:
            subprocess.run(
                [
                    "npx",
                    "-y",
                    "html-pdf-node",
                    "--html",
                    html_path,
                    "--output",
                    output_path,
                ],
                capture_output=True,
                timeout=60,
            )
            logger.info("PDF exported (html-pdf-node): %s", output_path)
            return True
        except Exception:
            logger.warning("PDF export unavailable; install weasyprint or html-pdf-node")
            return False

    def export_json_summary(self, suite_result: SuiteResult, output_path: str) -> str:
        """Export a machine-readable JSON summary of the suite run.

        Returns the absolute path of the written JSON file.
        """
        summary = {
            "run_id": suite_result.run_id,
            "status": "passed" if suite_result.failed == 0 else "partial_fail",
            "total": suite_result.total,
            "passed": suite_result.passed,
            "failed": suite_result.failed,
            "healed": suite_result.healed,
            "skipped": suite_result.skipped,
            "duration_ms": suite_result.duration_ms,
            "failed_cases": [
                c.case_id for c in suite_result.cases if c.status in ("failed", "aborted")
            ],
            "healed_cases": [
                c.case_id for c in suite_result.cases if c.status == "healed"
            ],
            "report_url": str(Path(output_path).resolve()),
        }

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("JSON summary exported: %s", output_path)
        return str(out.resolve())

    # ── Internal helpers ────────────────────────────────────────────────

    @staticmethod
    def _inline_css() -> str:
        """Return a ``<style>`` block with the glass-panel design system."""
        return """<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Noto Sans SC',sans-serif;background:#f0f2f5;color:#1e293b;line-height:1.6;}
a{color:#3b82f6;text-decoration:none;}
a:hover{text-decoration:underline;}
img{max-width:100%;height:auto;}
</style>"""

    @staticmethod
    def _inline_js_i18n() -> str:
        """Return a ``<script>`` block with bilingual (zh/en) i18n support."""
        return """<script>
const i18n = {
  zh: {
    suite_title:"测试报告",suite_total:"总用例数",suite_passed:"通过",suite_failed:"失败",
    suite_healed:"AI修复",run_time:"执行时间",device:"设备",duration:"耗时",
    filter_tag:"标签筛选",sort:"排序",sort_priority:"优先级",sort_duration:"耗时",sort_status:"状态",
    all:"全部",steps_passed:"步通过",trend_title:"与上次执行对比",
    new_failed:"新增失败",new_healed:"新增修复",new_cases:"新增用例",no_change:"与上次执行无变化",
    back_to_suite:"返回套件报告",author:"作者",priority:"优先级",
    before:"操作前",after:"操作后",reference:"参考",action:"操作",
    error:"错误",heal_phase:"修复阶段",heal_method:"方式",confidence:"置信度"
  },
  en: {
    suite_title:"Test Report",suite_total:"Total",suite_passed:"Passed",suite_failed:"Failed",
    suite_healed:"Healed",run_time:"Run Time",device:"Device",duration:"Duration",
    filter_tag:"Filter",sort:"Sort",sort_priority:"Priority",sort_duration:"Duration",sort_status:"Status",
    all:"All",steps_passed:"passed",trend_title:"vs Previous Run",
    new_failed:"New Failed",new_healed:"New Healed",new_cases:"New Cases",no_change:"No change from previous run",
    back_to_suite:"Back to Suite",author:"Author",priority:"Priority",
    before:"Before",after:"After",reference:"Reference",action:"Action",
    error:"Error",heal_phase:"Phase",heal_method:"Method",confidence:"Confidence"
  }
};
let lang = 'zh';
function toggleLang() {
  lang = lang === 'zh' ? 'en' : 'zh';
  document.querySelectorAll('[data-i18n]').forEach(function(el) {
    var key = el.getAttribute('data-i18n');
    var val = i18n[lang][key];
    if (val !== undefined) el.textContent = val;
  });
}
</script>"""

    @staticmethod
    def _escape(text: Any) -> str:
        """HTML-escape a string value."""
        if text is None:
            return ""
        s = str(text)
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    @staticmethod
    def _format_duration(ms: int) -> str:
        """Format a millisecond duration as a human-readable string."""
        if ms < 1000:
            return f"{ms}ms"
        seconds = ms / 1000
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"

    @staticmethod
    def _format_device_info(sr: SuiteResult) -> str:
        parts = []
        if sr.device_serial:
            parts.append(sr.device_serial)
        if sr.device_info:
            parts.append(sr.device_info)
        if sr.app_package:
            parts.append(sr.app_package)
            if sr.app_version:
                parts[-1] += f" v{sr.app_version}"
        return " / ".join(parts) if parts else "-"
