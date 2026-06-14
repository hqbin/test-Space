"""
Shared utility for generating report conclusions and release criteria
based on report template configuration.

Template config format:
{
    "rules": [
        {"metric": "testcase_pass_rate", "operator": ">=", "value": 95},
        {"metric": "open_pr_count", "sub_rules": [
            {"level": "Blocker", "operator": "=", "value": 0},
            {"level": "Critical", "operator": "=", "value": 0},
            {"level": "Major", "operator": "<=", "value": 5}
        ]},
        {"metric": "pr_closure_rate", "sub_rules": [
            {"level": "Blocker", "operator": ">=", "value": 100},
            {"level": "Critical", "operator": ">=", "value": 98},
            {"level": "Major", "operator": ">=", "value": 90}
        ]}
    ],
    "conclusion_pass": "Therefore, the test results meet the product release standards.",
    "conclusion_fail": "Therefore, the test results fail to meet the product release criteria."
}
"""


def _compare(actual, operator, threshold):
    """Compare actual value against threshold using operator."""
    if operator == '>=':
        return actual >= threshold
    elif operator == '<=':
        return actual <= threshold
    elif operator == '=':
        return actual == threshold
    elif operator == '>':
        return actual > threshold
    elif operator == '<':
        return actual < threshold
    elif operator == '!=':
        return actual != threshold
    return False


def _format_operator(op):
    """Format operator for display."""
    return op


def get_zmind_conclusion(template_config, zmind_stats, include_pr_closed):
    """
    根据模板配置计算 Zmind 表格的 OK/NG 结论。
    优先使用模板中的 pr_closure_rate / open_pr_count 规则，
    无模板时回退到硬编码默认值。
    返回 'OK' 或 'NG'。
    """
    open_blocker = zmind_stats.get('open_blocker', 0)
    open_critical = zmind_stats.get('open_critical', 0)
    open_major = zmind_stats.get('open_major', 0)

    blocker_total = zmind_stats.get('blocker', 0)
    critical_total = zmind_stats.get('critical', 0)
    major_total = zmind_stats.get('major', 0)

    blocker_cr = ((blocker_total - open_blocker) / blocker_total * 100) if blocker_total > 0 else 100
    critical_cr = ((critical_total - open_critical) / critical_total * 100) if critical_total > 0 else 100
    major_cr = ((major_total - open_major) / major_total * 100) if major_total > 0 else 100

    rules = (template_config or {}).get('rules', []) if template_config else []

    if include_pr_closed:
        pr_rule = next((r for r in rules if r.get('metric') == 'pr_closure_rate'), None)
        if pr_rule and pr_rule.get('sub_rules'):
            all_met = True
            for sr in pr_rule['sub_rules']:
                level = (sr.get('level') or '').lower()
                op = sr.get('operator', '>=')
                val = sr.get('value', 100)
                if level == 'blocker':
                    actual = blocker_cr
                elif level == 'critical':
                    actual = critical_cr
                elif level == 'major':
                    actual = major_cr
                else:
                    continue
                if not _compare(actual, op, val):
                    all_met = False
            return 'OK' if all_met else 'NG'
        else:
            return 'OK' if (blocker_cr >= 100 and critical_cr >= 98 and major_cr >= 90) else 'NG'
    else:
        open_rule = next((r for r in rules if r.get('metric') == 'open_pr_count'), None)
        if open_rule and open_rule.get('sub_rules'):
            all_met = True
            for sr in open_rule['sub_rules']:
                level = (sr.get('level') or '').lower()
                op = sr.get('operator', '=')
                val = sr.get('value', 0)
                if level == 'blocker':
                    actual = open_blocker
                elif level == 'critical':
                    actual = open_critical
                elif level == 'major':
                    actual = open_major
                else:
                    continue
                if not _compare(actual, op, val):
                    all_met = False
            return 'OK' if all_met else 'NG'
        else:
            return 'OK' if (open_blocker == 0 and open_critical == 0 and open_major <= 5) else 'NG'


def generate_conclusion_from_template(template_config, pass_rate, zmind_stats=None,
                                       has_zmind_csv=False, include_pr_closed=0,
                                       html_escape=False):
    """
    Generate conclusion and release_criteria from template config.
    
    Args:
        template_config: dict with 'rules', 'conclusion_pass', 'conclusion_fail'
        pass_rate: float, e.g. 95.60
        zmind_stats: dict with zmind PR statistics
        has_zmind_csv: bool
        include_pr_closed: int (0 or 1)
        html_escape: bool, if True escape < > & for PDF HTML rendering
    
    Returns:
        (conclusion: str, release_criteria: str)
    """
    if not template_config or 'rules' not in template_config:
        return None, None

    rules = template_config.get('rules', [])
    conclusion_pass_text = template_config.get('conclusion_pass',
        'Therefore, the test results meet the product release standards.')
    conclusion_fail_text = template_config.get('conclusion_fail',
        'Therefore, the test results fail to meet the product release criteria.')

    passing_rate_str = f'{pass_rate:.2f}%'
    all_met = True
    criteria_parts = []
    actual_parts = []

    # Helper for HTML escaping
    def esc(s):
        if html_escape:
            return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return s

    for rule in rules:
        metric = rule.get('metric', '')

        if metric == 'testcase_pass_rate':
            op = rule.get('operator', '>=')
            val = rule.get('value', 95)
            met = _compare(pass_rate, op, val)
            if not met:
                all_met = False
            criteria_parts.append(f'Testcase pass rate {esc(op)}{val}%')

        elif metric == 'open_pr_count':
            sub_rules = rule.get('sub_rules', [])
            pr_parts = []
            for sr in sub_rules:
                level = sr.get('level', '')
                op = sr.get('operator', '=')
                val = sr.get('value', 0)
                # Get actual open count from zmind_stats
                if has_zmind_csv and zmind_stats:
                    actual = zmind_stats.get(f'open_{level.lower()}', 0)
                else:
                    actual = 0
                met = _compare(actual, op, val)
                if not met:
                    all_met = False
                pr_parts.append(f'{level}{esc(op)}{val}')
            if pr_parts:
                criteria_parts.append(f'Open PR:{",".join(pr_parts)}')

        elif metric == 'pr_closure_rate':
            sub_rules = rule.get('sub_rules', [])
            pr_parts = []
            for sr in sub_rules:
                level = sr.get('level', '')
                op = sr.get('operator', '>=')
                val = sr.get('value', 100)
                # Calculate closure rate
                if has_zmind_csv and zmind_stats:
                    total = zmind_stats.get(level.lower(), 0)
                    open_count = zmind_stats.get(f'open_{level.lower()}', 0)
                    actual = ((total - open_count) / total * 100) if total > 0 else 100
                else:
                    actual = 100
                met = _compare(actual, op, val)
                if not met:
                    all_met = False
                pr_parts.append(f'{level}{esc(op)}{val}%')
            if pr_parts:
                criteria_parts.append(f'PR closure rate: {",".join(pr_parts)}')

    # Build release criteria string
    release_criteria = ';'.join(criteria_parts) + '。' if criteria_parts else ''

    # Build conclusion string
    meets_word = 'Meets' if all_met else 'Fails to meet'
    result_text = conclusion_pass_text if all_met else conclusion_fail_text

    # Build the actual data part
    if has_zmind_csv and zmind_stats:
        open_blocker = zmind_stats.get('open_blocker', 0)
        open_critical = zmind_stats.get('open_critical', 0)
        open_major = zmind_stats.get('open_major', 0)
        actual_str = (f'The test case pass rate has achieved {passing_rate_str},'
                      f'with Blocker PR={open_blocker},Critical PR={open_critical},'
                      f'Major PR={open_major}; ')
    else:
        actual_str = f'The test case pass rate has achieved {passing_rate_str}; '

    # Build standard string (the criteria part after "test standard of")
    standard_str = ' & '.join(criteria_parts) if criteria_parts else ''
    if html_escape:
        standard_str = standard_str  # already escaped in criteria_parts

    conclusion = (f'{actual_str}'
                  f'{meets_word} the test standard of {standard_str}；'
                  f' {result_text}')

    return conclusion, release_criteria


def generate_conclusion_default(pass_rate, zmind_stats=None, has_zmind_csv=False,
                                 include_pr_closed=0, html_escape=False):
    """
    Generate conclusion using the default hardcoded thresholds (fallback).
    Used when no template is configured.
    """
    passing_rate_str = f'{pass_rate:.2f}%'
    pass_rate_met = pass_rate >= 95

    def esc(s):
        if html_escape:
            return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return s

    if has_zmind_csv and zmind_stats:
        open_blocker = zmind_stats.get('open_blocker', 0)
        open_critical = zmind_stats.get('open_critical', 0)
        open_major = zmind_stats.get('open_major', 0)

        if include_pr_closed:
            blocker_total = zmind_stats.get('blocker', 0)
            critical_total = zmind_stats.get('critical', 0)
            major_total = zmind_stats.get('major', 0)
            blocker_cr = ((blocker_total - open_blocker) / blocker_total * 100) if blocker_total > 0 else 100
            critical_cr = ((critical_total - open_critical) / critical_total * 100) if critical_total > 0 else 100
            major_cr = ((major_total - open_major) / major_total * 100) if major_total > 0 else 100

            all_met = pass_rate_met and blocker_cr >= 100 and critical_cr >= 98 and major_cr >= 90
            meets_word = 'Meets' if all_met else 'Fails to meet'
            result_word = 'meet' if all_met else 'fail to meet'
            pr_standard = f'PR closure rate: Blocker=100%,Critical{esc(">=")}98%,Major{esc(">=")}90%'
            release_criteria = f'Testcase pass rate {esc(">=")}95%;PR closure rate: Blocker=100%,Critical{esc(">=")}98%,Major{esc(">=")}90%。'
        else:
            all_met = pass_rate_met and open_blocker == 0 and open_critical == 0 and open_major <= 5
            meets_word = 'Meets' if all_met else 'Fails to meet'
            result_word = 'meet' if all_met else 'fail to meet'
            pr_standard = f'Open PR:Blocker=0,Critical=0,Major{esc("<=5")}'
            release_criteria = f'Testcase pass rate {esc(">=")}95%;Open PR:Blocker=0,Critical=0,Major{esc("<=5")}。'

        conclusion = (f'The test case pass rate has achieved {passing_rate_str},'
                      f'with Blocker PR={open_blocker},Critical PR={open_critical},Major PR={open_major}; '
                      f'{meets_word} the test standard of Testcase Pass {esc(">=")}95% & {pr_standard}；'
                      f' Therefore, the test results {result_word} the product release criteria.')
    else:
        meets_word = 'Meets' if pass_rate_met else 'Fails to meet'
        result_word = 'meet' if pass_rate_met else 'fail to meet'
        conclusion = (f'The test case pass rate has achieved {passing_rate_str}; '
                      f'{meets_word} the test standard of Testcase Pass {esc(">=")}95%；'
                      f' Therefore, the test results {result_word} the product release criteria.')
        release_criteria = f'Testcase pass rate {esc(">=")}95%。'

    return conclusion, release_criteria


def get_conclusion_and_criteria(template_config, pass_rate, zmind_stats=None,
                                 has_zmind_csv=False, include_pr_closed=0,
                                 html_escape=False):
    """
    Main entry point: try template-based conclusion first, fall back to default.
    Returns (conclusion, release_criteria) tuple.
    """
    if template_config:
        result = generate_conclusion_from_template(
            template_config, pass_rate, zmind_stats,
            has_zmind_csv, include_pr_closed, html_escape
        )
        if result[0] is not None:
            return result

    return generate_conclusion_default(
        pass_rate, zmind_stats, has_zmind_csv,
        include_pr_closed, html_escape
    )


def get_selected_fields(template_config):
    """
    Extract selected_fields from template config.
    Returns None if no template or no selected_fields (meaning show all).
    """
    if not template_config:
        return None
    fields = template_config.get('selected_fields')
    if not fields or not isinstance(fields, list) or len(fields) == 0:
        return None
    return fields


def is_field_visible(selected_fields, field_key):
    """
    Check if a field should be visible based on selected_fields.
    If selected_fields is None, all fields are visible.
    field_key=None means the field is always visible (not configurable).
    """
    if field_key is None:
        return True  # Non-configurable fields always show
    if selected_fields is None:
        return True  # No template = show all
    return field_key in selected_fields


def filter_cover_rows(cover_rows_with_keys, selected_fields):
    """
    Filter cover rows based on selected_fields.
    
    Args:
        cover_rows_with_keys: list of (field_key, label, value) tuples
            field_key=None means always visible
        selected_fields: list of field keys or None (show all)
    
    Returns:
        list of (label, value) tuples after filtering
    """
    return [
        (label, value)
        for field_key, label, value in cover_rows_with_keys
        if is_field_visible(selected_fields, field_key)
    ]
