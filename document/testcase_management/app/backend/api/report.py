from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from datetime import datetime
from typing import Optional
import json
import os
import re
import threading
from database import get_db
from models import Report, User, TestExecution, TestPlan, TestPlanExecutor, TestPlanTestCase, ReportTemplate, TestCase
from schemas import ReportGenerate
from auth import get_current_user
from utils.data_permission import is_super_admin
from utils.logger import log_operation, LogAction, LogModule
from utils.notification_helper import trigger_report_notification, trigger_assignment_notification
from utils.testcase_utils import parse_steps_and_expected
from utils.report_conclusion import get_conclusion_and_criteria
from utils.export_task import start_export, get_task, get_task_status, set_progress
from fastapi.responses import FileResponse, StreamingResponse

router = APIRouter()


def _get_module_sort_key_with_fallback(module_path, sort_map):
    """模块排序辅助函数：支持子模块fallback - 匹配最长前缀的模块路径
    
    例如：
    - 模块路径 "ISDB/Setting/Network" 会依次尝试匹配:
      1. "ISDB/Setting/Network" (精确匹配)
      2. "ISDB/Setting" 
      3. "ISDB"
    
    返回的排序键会在匹配的父模块后追加 .9999999999 以确保子模块排在父模块的子用例之后
    """
    if not module_path:
        return "9999999999"
    # 尝试精确匹配
    if module_path in sort_map:
        return sort_map[module_path]
    # 尝试逐层匹配：从最长前缀到最短前缀
    parts = module_path.split('/')
    for i in range(len(parts) - 1, 0, -1):
        prefix = '/'.join(parts[:i])
        if prefix in sort_map:
            # 追加一个大的排序值，确保该路径下的所有用例排在已知子模块之后
            return sort_map[prefix] + '.9999999999'
    return "9999999999"


def _get_team_report_template(db, team_id, report_template_id=None):
    """获取报告模板的 criteria_config + selected_fields
    优先使用报告绑定的 template_id，没有则取项目组默认模板"""
    def _parse_template(template):
        result = {}
        if template.criteria_config:
            try:
                result = json.loads(template.criteria_config)
            except (json.JSONDecodeError, TypeError):
                result = {}
        if template.selected_fields:
            try:
                result['selected_fields'] = json.loads(template.selected_fields)
            except (json.JSONDecodeError, TypeError):
                pass
        return result or None

    # 优先使用报告指定的模板
    if report_template_id:
        template = db.query(ReportTemplate).filter(
            ReportTemplate.id == report_template_id
        ).first()
        if template:
            parsed = _parse_template(template)
            if parsed:
                return parsed
    # fallback: 项目组默认模板
    if not team_id:
        return None
    template = db.query(ReportTemplate).filter(
        ReportTemplate.team_id == team_id,
        ReportTemplate.is_default == True
    ).first()
    if not template:
        return None
    return _parse_template(template)


def _get_latest_executions(db, test_plan_id):
    """获取测试计划下每个用例的最新执行记录（去重，只统计关联用例）"""
    # 使用子查询一次获取有效的用例ID（排除NULL）
    linked_ids_subq = db.query(TestPlanTestCase.test_case_id).filter(
        TestPlanTestCase.test_plan_id == test_plan_id,
        TestPlanTestCase.test_case_id.isnot(None)
    ).subquery()
    
    linked_ids = {tc.id for tc in db.query(TestCase.id).filter(TestCase.id.in_(linked_ids_subq)).all()}
    
    if not linked_ids:
        return []
    
    # 子查询：每个test_case_id的最大executed_at（只查询关联用例）
    latest_subq = db.query(
        TestExecution.test_case_id,
        sa_func.max(TestExecution.id).label('max_id')
    ).filter(
        TestExecution.test_plan_id == test_plan_id,
        TestExecution.test_case_id.in_(linked_ids)
    ).group_by(
        TestExecution.test_case_id
    ).subquery()

    # 主查询：用max_id关联获取完整记录
    executions = db.query(TestExecution).join(
        latest_subq,
        TestExecution.id == latest_subq.c.max_id
    ).all()

    return executions


def _generate_report_snapshot(report, db):
    """生成报告快照数据，用于审核通过或拒绝时保存"""
    from models import TestPlan, TestCase
    
    # 获取测试计划信息
    test_plan = db.query(TestPlan).filter(TestPlan.id == report.test_plan_id).first()
    if not test_plan:
        return None
    
    # 获取执行数据（每个用例只取最新记录）
    executions = _get_latest_executions(db, report.test_plan_id)
    
    # 批量加载所有关联的测试用例（避免 N+1 查询）
    _tc_ids = [e.test_case_id for e in executions]
    _tc_map = {}
    if _tc_ids:
        _all_tcs = db.query(TestCase).filter(TestCase.id.in_(_tc_ids)).all()
        _tc_map = {tc.id: tc for tc in _all_tcs}
    
    # 从测试计划获取执行周期
    if test_plan.start_time and test_plan.end_time:
        test_cycle = f"{test_plan.start_time.strftime('%Y-%m-%d')} ~ {test_plan.end_time.strftime('%Y-%m-%d')}"
    else:
        test_cycle = ""
    
    # 从测试计划执行人表获取测试人员
    plan_executors = db.query(TestPlanExecutor, User).join(
        User, TestPlanExecutor.executor_id == User.id
    ).filter(TestPlanExecutor.test_plan_id == test_plan.id).all()
    
    if plan_executors:
        testers = [user.username for _, user in plan_executors]
        testers_str = ", ".join(testers)
    else:
        testers_str = ""
    
    # 获取审核人员
    reviewer = db.query(User).filter(User.id == test_plan.reviewer_id).first()
    reviewer_name = reviewer.username if reviewer else ""
    
    # 计算测试结论（与测试计划一致：passed / (total_plan_cases - NA - 协测)）
    # 只统计有效的用例ID（排除NULL）
    plan_total_cases = db.query(TestPlanTestCase).filter(
        TestPlanTestCase.test_plan_id == report.test_plan_id,
        TestPlanTestCase.test_case_id.isnot(None)
    ).join(TestCase, TestPlanTestCase.test_case_id == TestCase.id).count()
    na_cases = sum(1 for e in executions if e.result == 'NA')
    assist_cases = sum(1 for e in executions if (e.result or '').strip() == '协测')
    passed_cases = sum(1 for e in executions if e.result == 'PASS')
    valid_cases = plan_total_cases - na_cases - assist_cases
    pass_rate = (passed_cases / valid_cases * 100) if valid_cases > 0 else 0
    total_cases = plan_total_cases
    
    # 使用模板配置生成结论
    template_config = _get_team_report_template(db, test_plan.team_id, report.template_id)
    if pass_rate >= 95:
        test_conclusion = "测试通过"
    else:
        test_conclusion = "测试未通过"
    
    # 按模块统计测试结果（只统计主模块，子模块归入主模块）
    module_results = {}
    has_assist = False
    for execution in executions:
        test_case = _tc_map.get(execution.test_case_id)
        if test_case:
            module = (test_case.module or "未分类").split('/')[0].strip()
            if module not in module_results:
                module_results[module] = {
                    "test_cases": 0,
                    "pass": 0,
                    "fail": 0,
                    "block": 0,
                    "nt": 0,
                    "na": 0,
                    "assist": 0
                }
            module_results[module]["test_cases"] += 1
            result_val = (execution.result or '').strip()
            if result_val == 'PASS':
                module_results[module]["pass"] += 1
            elif result_val == 'FAIL':
                module_results[module]["fail"] += 1
            elif result_val == 'BLOCK':
                module_results[module]["block"] += 1
            elif result_val == 'NT':
                module_results[module]["nt"] += 1
            elif result_val == 'NA':
                module_results[module]["na"] += 1
            elif result_val == '协测':
                module_results[module]["assist"] += 1
                has_assist = True

    # 转换为列表格式
    # Passing rate = PASS / (总用例 - NA - 协测)
    test_results = []
    for module, result in module_results.items():
        effective_cases = result["test_cases"] - result["na"] - result["assist"]
        passing_rate = (result["pass"] / effective_cases * 100) if effective_cases > 0 else 0
        row = {
            "module": module,
            "test_cases": effective_cases,
            "pass": result["pass"],
            "fail": result["fail"],
            "block": result["block"],
            "nt": result["nt"],
            "na": result["na"],
            "passing_rate": f"{passing_rate:.2f}%"
        }
        if has_assist:
            row["assist"] = result["assist"]
        test_results.append(row)
    
    # 按模块sort_order排序（模块统计）
    from utils.module_sort import get_module_sort_map as _get_sort_map
    _sort_map = _get_sort_map(db, test_plan.project_id)
    test_results.sort(key=lambda r: _get_module_sort_key_with_fallback(r.get('module', ''), _sort_map))
    
    # 如果有 MpList 数据，解析测试统计并加入 MpList 模块行
    from utils.test_result_calc import parse_mplist_test_stats
    mplist_data_list = []
    if report.mplist_data:
        try:
            mplist_data_list = json.loads(report.mplist_data)
        except (json.JSONDecodeError, TypeError):
            pass
    if mplist_data_list and isinstance(mplist_data_list, dict) and mplist_data_list.get('headers'):
        mplist_stats = parse_mplist_test_stats(mplist_data_list)
        if mplist_stats and mplist_stats.get('has_stats'):
            if mplist_stats.get('has_assist'):
                has_assist = True
            mplist_row = {
                "module": "MpList",
                "test_cases": mplist_stats['test_cases'],
                "pass": mplist_stats['pass'],
                "fail": mplist_stats['fail'],
                "block": mplist_stats['block'],
                "nt": mplist_stats['nt'],
                "na": mplist_stats['na'],
                "passing_rate": f"{mplist_stats['passing_rate']:.2f}%"
            }
            if has_assist:
                mplist_row["assist"] = mplist_stats['assist']
                for r in test_results:
                    if "assist" not in r:
                        r["assist"] = 0
            test_results.append(mplist_row)

    # 准备用例详细情况
    test_cases = _build_test_cases_data(executions, db, test_plan.project_id, _tc_map)
    
    # 获取Zmind统计信息
    has_zmind_csv = report.zmind_pr_stats is not None
    zmind_stats = _get_zmind_stats_for_report(report, db, report.test_plan_id) if has_zmind_csv else {}
    
    # 获取issue列表
    issue_list = []
    if report.zmind_issue_list:
        try:
            issue_list = json.loads(report.zmind_issue_list)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # 获取mplist数据
    mplist_data_list = []
    if report.mplist_data:
        try:
            mplist_data_list = json.loads(report.mplist_data)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # 构建快照数据
    # 从已有快照中提取report_remark（在submit-review时存入）
    _existing_remark = ''
    if report.snapshot_data:
        try:
            _existing_snap = json.loads(report.snapshot_data)
            _existing_remark = _existing_snap.get('cover_data', {}).get('report_remark', '')
        except (json.JSONDecodeError, TypeError):
            pass
    
    snapshot = {
        "cover_data": {
            "project_name": report.project_name or "",
            "verify_env": report.verify_env or "",
            "release_note": report.release_note or "",
            "risk_assessment": report.risk_assessment or "",
            "report_remark": _existing_remark,
            "test_cycle": test_cycle,
            "testers": testers_str,
            "reviewer_name": reviewer_name,
            "test_conclusion": test_conclusion,
            "pass_rate": f"{pass_rate:.2f}%",
            "total_cases": total_cases,
            "passed_cases": passed_cases,
            "pass_rate_value": pass_rate
        },
        "test_results": test_results,
        "test_cases": test_cases,
        "zmind_stats": zmind_stats,
        "issue_list": issue_list,
        "mplist_data": mplist_data_list,
        "has_zmind_csv": has_zmind_csv,
        "has_assist": has_assist,
        "include_pr_closed": report.include_pr_closed or 0,
        "report_template_config": template_config,
        "snapshot_time": datetime.utcnow().isoformat()
    }
    
    return snapshot


def _natural_sort_key(case_number):
    """Python端自然排序key - 按编号末尾数字排序
    例如 STB1_SER_0001 → 提取 0001，OS10_ADV_0042 → 提取 0042
    """
    import re
    if not case_number:
        return (0,)
    # 提取末尾数字
    m = re.search(r'(\d+)$', case_number)
    if m:
        return (int(m.group(1)),)
    return (0,)


def _build_test_cases_data(executions, db, project_id=None, tc_map=None):
    """构建用例详细数据，解析steps JSON为可读文本，按Case前缀→模块→sort_order→case_number自然排序"""
    from models import TestCase
    from utils.module_sort import get_module_sort_map as _get_sort_map
    
    # 获取模块排序映射
    _sort_map = _get_sort_map(db, project_id) if project_id else {}
    
    # 如果没有传入预加载的 tc_map，批量加载（避免 N+1）
    if tc_map is None:
        _tc_ids = [e.test_case_id for e in executions]
        tc_map = {}
        if _tc_ids:
            _all_tcs = db.query(TestCase).filter(TestCase.id.in_(_tc_ids)).all()
            tc_map = {tc.id: tc for tc in _all_tcs}
    
    test_cases = []
    for execution in executions:
        test_case = tc_map.get(execution.test_case_id)
        if test_case:
            steps_list, expected_list = parse_steps_and_expected(test_case.steps, test_case.expected_result)
            test_cases.append({
                "case_number": test_case.case_number,
                "module": test_case.module,
                "name": test_case.name,
                "precondition": test_case.precondition or '',
                "steps": "\n".join(steps_list),
                "expected_result": "\n".join(expected_list),
                "level": test_case.level or '',
                "result": execution.result,
                "remark": execution.remarks or '',
                "sort_order": test_case.sort_order or 0,  # 保留sort_order用于快照和导出
                "primary_project_id": test_case.primary_project_id  # 用于模块排序
            })
    
    # 提取编号前缀Tag（如 TV_AD_, OS10_AD_）用于排序
    def _get_case_prefix(cn):
        if not cn:
            return 'zzz'  # 未知前缀放最后
        m = re.match(r'^([A-Za-z]+(?:_[A-Za-z]+)?)_?\d', cn or '')
        if m:
            return m.group(1).upper()
        return 'zzz'
    
    # 排序辅助函数：支持子模块fallback - 匹配最长前缀的模块路径
    def _get_module_sort_key(module_path):
        if not module_path:
            return "9999999999"
        if module_path in _sort_map:
            return _sort_map[module_path]
        parts = module_path.split('/')
        for i in range(len(parts) - 1, 0, -1):
            prefix = '/'.join(parts[:i])
            if prefix in _sort_map:
                return _sort_map[prefix] + '.9999999999'
        return "9999999999"
    
    # 排序：模块sort_order → Case前缀 → 用例sort_order → case_number自然排序
    test_cases.sort(key=lambda tc: (
        _get_module_sort_key(tc["module"] or ""),
        _get_case_prefix(tc["case_number"]),
        tc.get("sort_order", 0) or 0,
        _natural_sort_key(tc["case_number"])
    ))
    
    return test_cases


def _get_zmind_stats_for_report(report, db, test_plan_id):
    """获取报告的Zmind统计数据，优先使用CSV上传的数据，回退到TestCaseZmindLink"""
    from models import TestCaseZmindLink
    
    if report.zmind_pr_stats:
        try:
            return json.loads(report.zmind_pr_stats)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # 回退到从TestCaseZmindLink统计
    zmind_links = db.query(TestCaseZmindLink).filter(
        TestCaseZmindLink.test_plan_id == test_plan_id
    ).all()
    
    zmind_stats = {
        'open': 0, 'open_blocker': 0, 'open_critical': 0, 'open_major': 0,
        'open_minor': 0, 'open_enhancement': 0, 'blocker': 0, 'critical': 0,
        'major': 0, 'minor': 0, 'enhancement': 0, 'total_prs': len(zmind_links)
    }
    
    for link in zmind_links:
        severity = (link.zmind_issue_severity or '').lower()
        from utils.constants import CLOSED_STATUSES
        closed_lower = {s.lower() for s in CLOSED_STATUSES}
        is_open = link.zmind_issue_status.lower() not in closed_lower if link.zmind_issue_status else True
        
        for sev in ['blocker', 'critical', 'major', 'minor', 'enhancement']:
            if sev in severity:
                zmind_stats[sev] += 1
                if is_open:
                    zmind_stats[f'open_{sev}'] += 1
                break
        
        if is_open:
            zmind_stats['open'] += 1
    
    return zmind_stats

@router.post("/generate")
def generate_report(
    req: Request,
    report_data: ReportGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 获取测试计划的执行数据（每个用例只取最新记录）
    executions = _get_latest_executions(db, report_data.test_plan_id)
    
    # 计算统计数据（passed / (total_plan_cases - NA - 协测)）
    # 只统计有效的用例ID（排除NULL）
    plan_total_cases = db.query(TestPlanTestCase).filter(
        TestPlanTestCase.test_plan_id == report_data.test_plan_id,
        TestPlanTestCase.test_case_id.isnot(None)
    ).join(TestCase, TestPlanTestCase.test_case_id == TestCase.id).count()
    na_count = sum(1 for e in executions if e.result == 'NA')
    assist_count = sum(1 for e in executions if (e.result or '').strip() == '协测')
    total_cases = plan_total_cases
    passed = sum(1 for e in executions if e.result == 'PASS')
    failed = sum(1 for e in executions if e.result == 'FAIL')
    valid_cases = plan_total_cases - na_count - assist_count
    pass_rate = (passed / valid_cases * 100) if valid_cases > 0 else 0
    fail_rate = 100 - pass_rate
    
    db_report = Report(
        test_plan_id=report_data.test_plan_id,
        template_id=report_data.template_id,
        name=report_data.name,
        created_by=current_user.id
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    # 生成快照数据（在创建报告时就生成，避免每次打开详情页都要实时计算）
    snapshot = _generate_report_snapshot(db_report, db)
    if snapshot:
        db_report.snapshot_data = json.dumps(snapshot, ensure_ascii=False)
        db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.REPORTS,
        action=LogAction.GENERATE,
        description=f"生成测试报告：{db_report.name}（ID: {db_report.id}）",
        request=req
    )
    
    # 获取测试计划的project_id用于通知过滤
    _tp_for_notify = db.query(TestPlan).filter(TestPlan.id == report_data.test_plan_id).first()
    _notify_project_id = _tp_for_notify.project_id if _tp_for_notify else None
    
    # 触发通知
    trigger_report_notification(
        db=db,
        event_type='generated',
        report_id=db_report.id,
        report_name=db_report.name,
        operator_name=current_user.username,
        total_cases=total_cases,
        passed=passed,
        failed=failed,
        pass_rate=pass_rate,
        project_id=_notify_project_id
    )
    
    # 如果失败率超过50%，触发告警通知
    if fail_rate > 50:
        trigger_report_notification(
            db=db,
            event_type='alert',
            report_id=db_report.id,
            report_name=db_report.name,
            operator_name=current_user.username,
            total_cases=total_cases,
            passed=passed,
            failed=failed,
            pass_rate=pass_rate,
            project_id=_notify_project_id
        )
    
    return {"code": 200, "message": "success", "data": db_report}

@router.get("")
def list_reports(
    req: Request,
    page: int = 1,
    size: int = 10,
    project_ids: Optional[str] = None,
    team_id: Optional[int] = None,
    is_archived: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from models import TestPlan
    from utils.data_permission import apply_report_data_permission, is_super_admin
    
    # 构建查询
    query = db.query(Report)
    
    # 按项目组过滤（通过 TestPlan.team_id）
    if team_id:
        team_plan_ids = [tp.id for tp in db.query(TestPlan.id).filter(
            TestPlan.team_id == team_id
        ).all()]
        if team_plan_ids:
            query = query.filter(Report.test_plan_id.in_(team_plan_ids))
        else:
            return {
                "code": 200,
                "message": "success",
                "data": {"records": [], "total": 0}
            }
    
    # 支持多个用例库ID筛选（前端用例库下拉框）
    if project_ids:
        try:
            pid_list = [int(pid.strip()) for pid in project_ids.split(',') if pid.strip()]
            if pid_list:
                # Report 通过 test_plan_id 关联 TestPlan，TestPlan 有 project_id
                filtered_plan_ids = [tp.id for tp in db.query(TestPlan.id).filter(
                    TestPlan.project_id.in_(pid_list)
                ).all()]
                if filtered_plan_ids:
                    query = query.filter(Report.test_plan_id.in_(filtered_plan_ids))
                else:
                    query = query.filter(Report.id == -1)
        except (ValueError, TypeError):
            pass
    
    # 归档状态筛选
    if is_archived is not None:
        query = query.filter(Report.is_archived == is_archived)
    
    # 过滤掉进行中的报告（撤回审核后状态变为IN_PROGRESS，不显示在报告列表）
    query = query.filter(Report.status != 'IN_PROGRESS')
    
    # 应用数据权限过滤
    query = apply_report_data_permission(query, current_user, db)
    
    # 数据权限已经控制了用户能看到哪些报告
    # 待审核报告的审核操作权限由前端按钮控制（只有审核人和管理员能看到审核按钮）
    # 这里不再额外过滤待审核报告的可见性
    
    # 排序：归档的报告排在最后
    total = query.count()
    reports = query.order_by(Report.is_archived.desc(), Report.created_at.desc(), Report.id.desc()).offset((page - 1) * size).limit(size).all()
    
    # ── 批量预加载，避免 N+1 ──────────────────────────────────────────
    report_plan_ids = list({r.test_plan_id for r in reports if r.test_plan_id})
    
    # 1. 批量查测试计划
    plans_map = {}
    if report_plan_ids:
        plans = db.query(TestPlan).filter(TestPlan.id.in_(report_plan_ids)).all()
        plans_map = {p.id: p for p in plans}
    
    # 2. 批量查审核人
    reviewer_ids = list({p.reviewer_id for p in plans_map.values() if p.reviewer_id})
    reviewers_map = {}
    if reviewer_ids:
        reviewers = db.query(User).filter(User.id.in_(reviewer_ids)).all()
        reviewers_map = {u.id: u for u in reviewers}
    
    # 3. 批量查执行人
    executors_by_plan = {}
    if report_plan_ids:
        executor_rows = db.query(TestPlanExecutor, User).join(
            User, TestPlanExecutor.executor_id == User.id
        ).filter(TestPlanExecutor.test_plan_id.in_(report_plan_ids)).all()
        for exec_rec, user in executor_rows:
            executors_by_plan.setdefault(exec_rec.test_plan_id, []).append(user.username)
    
    # 4. 批量查关联用例（用于算总数和 pass_rate）
    plan_testcase_ids_map = {}
    if report_plan_ids:
        tc_rows = db.query(
            TestPlanTestCase.test_plan_id,
            TestPlanTestCase.test_case_id
        ).join(
            TestCase, TestPlanTestCase.test_case_id == TestCase.id
        ).filter(
            TestPlanTestCase.test_plan_id.in_(report_plan_ids),
            TestPlanTestCase.test_case_id.isnot(None)
        ).all()
        for row in tc_rows:
            plan_testcase_ids_map.setdefault(row.test_plan_id, set()).add(row.test_case_id)
    
    # 5. 批量查最新执行记录（所有 plan_id 一次取完，再 Python 侧去重）
    latest_exec_by_plan = {}  # plan_id -> {tc_id -> execution}
    if report_plan_ids:
        latest_subq = db.query(
            TestExecution.test_plan_id,
            TestExecution.test_case_id,
            sa_func.max(TestExecution.id).label('max_id')
        ).filter(
            TestExecution.test_plan_id.in_(report_plan_ids)
        ).group_by(
            TestExecution.test_plan_id,
            TestExecution.test_case_id
        ).subquery()
        
        all_execs = db.query(TestExecution).join(
            latest_subq, TestExecution.id == latest_subq.c.max_id
        ).all()
        
        for e in all_execs:
            linked = plan_testcase_ids_map.get(e.test_plan_id, set())
            if e.test_case_id in linked:
                latest_exec_by_plan.setdefault(e.test_plan_id, []).append(e)
    # ─────────────────────────────────────────────────────────────────
    
    # 为每个报告添加审核人信息、通过率、执行人、执行周期
    result_list = []
    for report in reports:
        report_dict = {
            "id": report.id,
            "test_plan_id": report.test_plan_id,
            "name": report.name,
            "status": report.status,
            "is_archived": report.is_archived or 0,
            "project_name": report.project_name,
            "verify_env": report.verify_env,
            "release_note": report.release_note,
            "reject_reason": report.reject_reason or '',
            "created_at": report.created_at,
            "created_by": report.created_by
        }
        
        test_plan = plans_map.get(report.test_plan_id)
        if test_plan:
            reviewer = reviewers_map.get(test_plan.reviewer_id)
            if reviewer:
                report_dict["reviewer_id"] = test_plan.reviewer_id
                report_dict["reviewer_name"] = reviewer.username
            
            if test_plan.start_time and test_plan.end_time:
                report_dict["test_cycle"] = f"{test_plan.start_time.strftime('%Y-%m-%d')} ~ {test_plan.end_time.strftime('%Y-%m-%d')}"
            else:
                report_dict["test_cycle"] = "-"
            
            executor_names = executors_by_plan.get(test_plan.id, [])
            report_dict["executors"] = ", ".join(executor_names) if executor_names else "-"
        else:
            report_dict["test_cycle"] = "-"
            report_dict["executors"] = "-"
        
        # 计算通过率（全部来自已预加载数据，零额外查询）
        linked_ids = plan_testcase_ids_map.get(report.test_plan_id, set())
        plan_total_cases = len(linked_ids)
        executions = latest_exec_by_plan.get(report.test_plan_id, [])
        
        if plan_total_cases > 0:
            na_cases = sum(1 for e in executions if e.result == 'NA')
            assist_cases = sum(1 for e in executions if (e.result or '').strip() == '协测')
            passed_cases = sum(1 for e in executions if e.result == 'PASS')
            valid_cases = plan_total_cases - na_cases - assist_cases
            pass_rate = (passed_cases / valid_cases * 100) if valid_cases > 0 else 0
            report_dict["pass_rate"] = f"{pass_rate:.2f}%"
        else:
            report_dict["pass_rate"] = "-"
        
        result_list.append(report_dict)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "records": result_list,
            "total": total
        }
    }

@router.get("/{report_id}")
def get_report_detail(
    req: Request,
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from models import TestPlan, TestCase
    from fastapi import HTTPException
    
    # 获取报告信息
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 获取测试计划信息
    test_plan = db.query(TestPlan).filter(TestPlan.id == report.test_plan_id).first()
    if not test_plan:
        raise HTTPException(status_code=404, detail="测试计划不存在")

    # 判断是否为超级管理员
    is_admin = is_super_admin(current_user)

    # 验证权限：超级管理员可以查看所有报告
    # 普通用户的查看权限由数据权限控制（列表接口已过滤），审核操作由前端按钮控制
    # 不再限制非审核人查看待审核报告详情
    
    # 如果有快照数据且报告已审核通过，使用快照数据
    # 对于待审核/已拒绝的报告，总是实时计算（确保数据最新且无重复）
    if report.snapshot_data and report.status == 'APPROVED':
        try:
            snapshot = json.loads(report.snapshot_data)
            cover_data = snapshot.get('cover_data', {})
            
            # 检查快照数据是否有重复（旧bug修复：对比test_cases数量与测试计划关联用例数）
            # 注意：删除用例后 plan_case_count 会变少，但仍应使用快照数据
            snapshot_case_count = len(snapshot.get('test_cases', []))
            plan_case_count = db.query(TestPlanTestCase).filter(
                TestPlanTestCase.test_plan_id == report.test_plan_id
            ).count()
            
            # 始终使用快照数据，因为：
            # 1. 快照中保存了完整的用例信息（包括已删除的用例）
            # 2. 删除用例后 plan_case_count 会变少，但 snapshot 仍然有效
            if snapshot_case_count > 0:
                report_data = {
                    "id": report.id,
                    "status": report.status,
                    "is_archived": report.is_archived or 0,
                    "project_name": cover_data.get('project_name', ''),
                    "verify_env": cover_data.get('verify_env', ''),
                    "release_note": cover_data.get('release_note', ''),
                    "risk_assessment": cover_data.get('risk_assessment', ''),
                    "report_remark": cover_data.get('report_remark', ''),
                    "test_cycle": cover_data.get('test_cycle', ''),
                    "testers": cover_data.get('testers', ''),
                    "reviewer_name": cover_data.get('reviewer_name', ''),
                    "reviewer_id": test_plan.reviewer_id,
                    "test_conclusion": cover_data.get('test_conclusion', ''),
                    "pass_rate": cover_data.get('pass_rate', '0%'),
                    "total_cases": cover_data.get('total_cases', 0),
                    "passed_cases": cover_data.get('passed_cases', 0)
                }
                
                return {
                    "code": 200,
                    "message": "success",
                    "data": {
                        "report": report_data,
                        "test_results": snapshot.get('test_results', []),
                        "test_cases": snapshot.get('test_cases', []),
                        "zmind_stats": snapshot.get('zmind_stats', {}),
                        "issue_list": snapshot.get('issue_list', []),
                        "mplist_data": snapshot.get('mplist_data', []),
                        "include_pr_closed": snapshot.get('include_pr_closed', 0),
                        "has_zmind_csv": snapshot.get('has_zmind_csv', False),
                        "has_assist": snapshot.get('has_assist', False),
                        "is_snapshot": True,
                        "report_template_config": _get_team_report_template(db, test_plan.team_id, report.template_id)
                    }
                }
        except (json.JSONDecodeError, TypeError):
            pass
    
    # 实时计算数据（无快照、待审核、快照有重复数据时）
    # 获取执行数据（每个用例只取最新记录）
    executions = _get_latest_executions(db, report.test_plan_id)
    
    # 批量加载所有关联的测试用例（避免 N+1 查询）
    _tc_ids_rt = [e.test_case_id for e in executions]
    _tc_map_rt = {}
    if _tc_ids_rt:
        from models import TestCase
        _all_tcs_rt = db.query(TestCase).filter(TestCase.id.in_(_tc_ids_rt)).all()
        _tc_map_rt = {tc.id: tc for tc in _all_tcs_rt}
    
    # 从测试计划获取执行周期
    if test_plan.start_time and test_plan.end_time:
        test_cycle = f"{test_plan.start_time.strftime('%Y-%m-%d')} ~ {test_plan.end_time.strftime('%Y-%m-%d')}"
    else:
        test_cycle = ""
    
    # 从测试计划执行人表获取测试人员
    plan_executors = db.query(TestPlanExecutor, User).join(
        User, TestPlanExecutor.executor_id == User.id
    ).filter(TestPlanExecutor.test_plan_id == test_plan.id).all()
    
    if plan_executors:
        testers = [user.username for _, user in plan_executors]
        testers_str = ", ".join(testers)
    else:
        testers_str = ""
    
    # 获取审核人员
    reviewer = db.query(User).filter(User.id == test_plan.reviewer_id).first()
    reviewer_name = reviewer.username if reviewer else ""
    
    # 计算测试结论（与测试计划一致：passed / (total_plan_cases - NA - 协测)）
    # 只统计有效的用例ID（排除NULL）
    plan_total_cases = db.query(TestPlanTestCase).filter(
        TestPlanTestCase.test_plan_id == report.test_plan_id,
        TestPlanTestCase.test_case_id.isnot(None)
    ).join(TestCase, TestPlanTestCase.test_case_id == TestCase.id).count()
    na_cases_count = sum(1 for e in executions if e.result == 'NA')
    assist_cases_count = sum(1 for e in executions if (e.result or '').strip() == '协测')
    passed_cases = sum(1 for e in executions if e.result == 'PASS')
    valid_cases = plan_total_cases - na_cases_count - assist_cases_count
    pass_rate = (passed_cases / valid_cases * 100) if valid_cases > 0 else 0
    total_cases = plan_total_cases
    
    # 使用模板配置判断结论
    template_config = _get_team_report_template(db, test_plan.team_id, report.template_id)
    if pass_rate >= 95:
        test_conclusion = "测试通过"
    else:
        test_conclusion = "测试未通过"
    
    # 按模块统计测试结果（只统计主模块，子模块归入主模块）
    module_results = {}
    has_assist_rt = False
    for execution in executions:
        test_case = _tc_map_rt.get(execution.test_case_id)
        if test_case:
            module = (test_case.module or "未分类").split('/')[0].strip()
            if module not in module_results:
                module_results[module] = {
                    "test_cases": 0,
                    "pass": 0,
                    "fail": 0,
                    "block": 0,
                    "nt": 0,
                    "na": 0,
                    "assist": 0
                }
            module_results[module]["test_cases"] += 1
            result_val = (execution.result or '').strip()
            if result_val == 'PASS':
                module_results[module]["pass"] += 1
            elif result_val == 'FAIL':
                module_results[module]["fail"] += 1
            elif result_val == 'BLOCK':
                module_results[module]["block"] += 1
            elif result_val == 'NT':
                module_results[module]["nt"] += 1
            elif result_val == 'NA':
                module_results[module]["na"] += 1
            elif result_val == '协测':
                module_results[module]["assist"] += 1
                has_assist_rt = True

    # 转换为列表格式
    # Passing rate = PASS / (总用例 - NA - 协测)
    test_results = []
    for module, result in module_results.items():
        effective_cases = result["test_cases"] - result["na"] - result["assist"]
        passing_rate = (result["pass"] / effective_cases * 100) if effective_cases > 0 else 0
        row = {
            "module": module,
            "test_cases": effective_cases,
            "pass": result["pass"],
            "fail": result["fail"],
            "block": result["block"],
            "nt": result["nt"],
            "na": result["na"],
            "passing_rate": f"{passing_rate:.2f}%"
        }
        if has_assist_rt:
            row["assist"] = result["assist"]
        test_results.append(row)
    
    # 按模块sort_order排序test_results
    from utils.module_sort import get_module_sort_map as _get_sort_map
    _sort_map = _get_sort_map(db, test_plan.project_id)
    test_results.sort(key=lambda r: _get_module_sort_key_with_fallback(r.get('module', ''), _sort_map))
    
    # 如果有 MpList 数据，解析测试统计并加入 MpList 模块行
    from utils.test_result_calc import parse_mplist_test_stats as _parse_mplist_stats

    # 准备用例详细情况
    test_cases = _build_test_cases_data(executions, db, test_plan.project_id, _tc_map_rt)
    
    # 构建报告数据
    # 从快照中提取report_remark（存储在snapshot的cover_data中）
    _report_remark = ''
    if report.snapshot_data:
        try:
            _snap = json.loads(report.snapshot_data)
            _report_remark = _snap.get('cover_data', {}).get('report_remark', '')
        except (json.JSONDecodeError, TypeError):
            pass
    
    report_data = {
        "id": report.id,
        "status": report.status,  # 确保包含status字段
        "is_archived": report.is_archived or 0,
        "project_name": report.project_name,
        "verify_env": report.verify_env,
        "release_note": report.release_note,
        "risk_assessment": report.risk_assessment or '',
        "report_remark": _report_remark,
        "test_cycle": test_cycle,
        "testers": testers_str,
        "reviewer_name": reviewer_name,
        "reviewer_id": test_plan.reviewer_id,
        "test_conclusion": test_conclusion,
        "pass_rate": f"{pass_rate:.2f}%",
        "total_cases": total_cases,
        "passed_cases": passed_cases
    }
    
    # 获取Zmind统计信息
    has_zmind_csv = report.zmind_pr_stats is not None
    zmind_stats = _get_zmind_stats_for_report(report, db, report.test_plan_id) if has_zmind_csv else {}
    
    # 获取issue列表
    issue_list = []
    if report.zmind_issue_list:
        try:
            issue_list = json.loads(report.zmind_issue_list)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # 获取mplist数据
    mplist_data = []
    if report.mplist_data:
        try:
            mplist_data = json.loads(report.mplist_data)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # 解析 MpList 测试统计
    if mplist_data and isinstance(mplist_data, dict) and mplist_data.get('headers'):
        _mp_stats = _parse_mplist_stats(mplist_data)
        if _mp_stats and _mp_stats.get('has_stats'):
            if _mp_stats.get('has_assist'):
                has_assist_rt = True
            mplist_row = {
                "module": "MpList",
                "test_cases": _mp_stats['test_cases'],
                "pass": _mp_stats['pass'],
                "fail": _mp_stats['fail'],
                "block": _mp_stats['block'],
                "nt": _mp_stats['nt'],
                "na": _mp_stats['na'],
                "passing_rate": f"{_mp_stats['passing_rate']:.2f}%"
            }
            if has_assist_rt:
                mplist_row["assist"] = _mp_stats['assist']
                for r in test_results:
                    if "assist" not in r:
                        r["assist"] = 0
            test_results.append(mplist_row)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "report": report_data,
            "test_results": test_results,
            "test_cases": test_cases,
            "zmind_stats": zmind_stats,
            "issue_list": issue_list,
            "mplist_data": mplist_data,
            "include_pr_closed": report.include_pr_closed or 0,
            "has_zmind_csv": has_zmind_csv,
            "has_assist": has_assist_rt,
            "is_snapshot": False,
            "report_template_config": _get_team_report_template(db, test_plan.team_id, report.template_id)
        }
    }

@router.post("/{report_id}/approve")
def approve_report(
    req: Request,
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from models import TestPlan
    from fastapi import HTTPException
    
    # 获取报告信息
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 获取测试计划信息
    test_plan = db.query(TestPlan).filter(TestPlan.id == report.test_plan_id).first()
    if not test_plan:
        raise HTTPException(status_code=404, detail="测试计划不存在")
    
    # 判断是否为超级管理员
    is_admin = is_super_admin(current_user)
    
    # 验证权限：超级管理员可以审核所有报告,普通用户只能审核自己负责的报告
    if not is_admin:
        if test_plan.reviewer_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限审核此报告")
    
    # 验证报告状态
    if report.status != 'PENDING_REVIEW':
        raise HTTPException(status_code=400, detail="报告已审核")
    
    # 生成并保存快照数据
    snapshot = _generate_report_snapshot(report, db)
    if snapshot:
        report.snapshot_data = json.dumps(snapshot, ensure_ascii=False)
    
    # 更新报告状态为通过
    report.status = 'APPROVED'
    report.reviewed_by = current_user.id
    report.reviewed_at = datetime.now()
    
    # 更新测试计划状态为完成
    test_plan.status = 'COMPLETED'
    
    db.commit()
    
    # 记录日志
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.REPORTS,
        action=LogAction.UPDATE,
        description=f"审核通过测试报告：{report.name}（ID: {report.id}）",
        request=req
    )
    
    # 触发通知 - 只通知报告创建者（不排除审核人自己，因为审核人≠提交人）
    if report.created_by:
        try:
            from services.notification_service import NotificationService
            # 获取报告统计数据
            total_cases = 0
            passed = 0
            failed = 0
            if report.snapshot_data:
                try:
                    snapshot = json.loads(report.snapshot_data)
                    total_cases = snapshot.get('total_cases', 0)
                    passed = snapshot.get('passed', 0)
                    failed = snapshot.get('failed', 0)
                except:
                    pass
            
            pass_rate = f"{(passed / total_cases * 100):.2f}" if total_cases > 0 else "0.00"
            
            svc = NotificationService(db)
            svc.create_notification(
                notification_type='report',
                event_type='approved',
                title=f'测试报告 "{report.name}" 审核通过',
                content=f'测试报告"{report.name}"已审核通过。\n\n'
                        f'审核人：{current_user.username}\n'
                        f'审核时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                related_id=report.id,
                related_type='report',
                sender_id=current_user.id,
                recipient_user_ids=[report.created_by],
                context={
                    'project_id': test_plan.project_id, 
                    'team_id': test_plan.team_id, 
                    'report_name': report.name, 
                    'operator': current_user.username,
                    'review_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'reviewer': current_user.username,
                    'pass_rate': pass_rate,
                    'total_cases': total_cases,
                    'passed': passed,
                    'failed': failed,
                }
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"审核通过通知失败: {e}")
    
    return {"code": 200, "message": "success", "data": {"status": "APPROVED"}}

@router.post("/{report_id}/reject")
def reject_report(
    req: Request,
    report_id: int,
    body: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from models import TestPlan
    from fastapi import HTTPException
    
    # 从body中获取reject_reason
    reject_reason = ''
    if body and isinstance(body, dict):
        reject_reason = body.get('reject_reason', '')
    
    # 获取报告信息
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 获取测试计划信息
    test_plan = db.query(TestPlan).filter(TestPlan.id == report.test_plan_id).first()
    if not test_plan:
        raise HTTPException(status_code=404, detail="测试计划不存在")
    
    # 判断是否为超级管理员
    is_admin = is_super_admin(current_user)
    
    # 验证权限：超级管理员可以审核所有报告,普通用户只能审核自己负责的报告
    if not is_admin:
        if test_plan.reviewer_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限审核此报告")
    
    # 验证报告状态
    if report.status != 'PENDING_REVIEW':
        raise HTTPException(status_code=400, detail="报告已审核")
    
    # 生成并保存快照数据
    snapshot = _generate_report_snapshot(report, db)
    if snapshot:
        report.snapshot_data = json.dumps(snapshot, ensure_ascii=False)
    
    # 更新报告状态为拒绝
    report.status = 'REJECTED'
    report.reviewed_by = current_user.id
    report.reviewed_at = datetime.now()
    report.reject_reason = reject_reason
    
    # 更新测试计划状态为审核不通过
    test_plan.status = 'REJECTED'
    
    db.commit()
    
    # 记录日志
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.REPORTS,
        action=LogAction.UPDATE,
        description=f"审核拒绝测试报告：{report.name}（ID: {report.id}）",
        request=req
    )
    
    # 触发通知 - 只通知报告创建者（不排除审核人自己）
    if report.created_by:
        try:
            from services.notification_service import NotificationService
            # 查询提交人信息
            submitter = db.query(User).filter(User.id == report.created_by).first()
            submitter_name = submitter.full_name or submitter.username if submitter else '未知'
            
            # 构建拒绝原因文本
            reason_text = ''
            if reject_reason:
                reason_text = f'拒绝原因：{reject_reason}\n'
            
            svc = NotificationService(db)
            svc.create_notification(
                notification_type='report',
                event_type='rejected',
                title=f'测试报告 "{report.name}" 审核未通过',
                content=f'测试报告"{report.name}"审核未通过，请重新提交。\n\n'
                        f'提交人：{submitter_name}\n'
                        f'{reason_text}'
                        f'审核人：{current_user.username}\n'
                        f'审核时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                related_id=report.id,
                related_type='report',
                sender_id=current_user.id,
                recipient_user_ids=[report.created_by],
                context={
                    'project_id': test_plan.project_id,
                    'team_id': test_plan.team_id,
                    'report_name': report.name,
                    'operator': current_user.username,
                    'reviewer': current_user.username,
                    'review_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'review_comment': reject_reason or '',
                }
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"审核拒绝通知失败: {e}")
    
    return {"code": 200, "message": "success", "data": {"status": "REJECTED"}}


@router.post("/{report_id}/archive")
def archive_report(
    req: Request,
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from models import TestPlan
    from fastapi import HTTPException
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    test_plan = db.query(TestPlan).filter(TestPlan.id == report.test_plan_id).first()
    if not test_plan:
        raise HTTPException(status_code=404, detail="测试计划不存在")
    
    is_admin = is_super_admin(current_user)
    
    if not is_admin:
        if test_plan.reviewer_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限归档此报告")
    
    if report.status != 'APPROVED':
        raise HTTPException(status_code=400, detail="只有审核通过的报告才能归档")
    
    if report.is_archived == 1:
        raise HTTPException(status_code=400, detail="报告已归档")
    
    report.is_archived = 1
    report.archived_at = datetime.now()
    
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.REPORTS,
        action=LogAction.UPDATE,
        description=f"归档测试报告：{report.name}（ID: {report.id}）",
        request=req
    )
    
    return {"code": 200, "message": "success", "data": {"is_archived": 1}}


@router.post("/{report_id}/unarchive")
def unarchive_report(
    req: Request,
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from models import TestPlan
    from fastapi import HTTPException
    
    is_admin = is_super_admin(current_user)
    
    if not is_admin:
        raise HTTPException(status_code=403, detail="只有超级管理员可以撤回归档")
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    if report.is_archived != 1:
        raise HTTPException(status_code=400, detail="报告未归档")
    
    report.is_archived = 0
    report.archived_at = None
    
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.REPORTS,
        action=LogAction.UPDATE,
        description=f"撤回归档测试报告：{report.name}（ID: {report.id}）",
        request=req
    )
    
    return {"code": 200, "message": "success", "data": {"is_archived": 0}}


@router.post("/{report_id}/withdraw")
def withdraw_report(
    req: Request,
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from models import TestPlan
    from fastapi import HTTPException
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    test_plan = db.query(TestPlan).filter(TestPlan.id == report.test_plan_id).first()
    if not test_plan:
        raise HTTPException(status_code=404, detail="测试计划不存在")
    
    is_admin = is_super_admin(current_user)
    
    if not is_admin:
        if test_plan.reviewer_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限撤回此报告")
    
    if report.status != 'APPROVED':
        raise HTTPException(status_code=400, detail="只有审核通过的报告才能撤回")
    
    report.is_archived = 0
    report.archived_at = None
    report.status = 'IN_PROGRESS'
    
    test_plan.status = 'IN_PROGRESS'
    
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.REPORTS,
        action=LogAction.UPDATE,
        description=f"撤回测试报告（变为进行中）：{report.name}（ID: {report.id}）",
        request=req
    )
    
    return {"code": 200, "message": "success", "data": {"status": "IN_PROGRESS", "is_archived": 0}}


@router.get("/{report_id}/export/excel")
def export_report_excel(
    req: Request,
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出测试报告为Excel格式，直接流式返回不保存到服务器"""
    from fastapi import HTTPException
    from fastapi.responses import StreamingResponse
    from models import TestPlan, TestCase
    from utils.report_excel import generate_report_excel_stream
    import os
    import io
    
    # 获取报告信息
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 获取测试计划信息
    test_plan = db.query(TestPlan).filter(TestPlan.id == report.test_plan_id).first()
    if not test_plan:
        raise HTTPException(status_code=404, detail="测试计划不存在")
    
    # 导出权限：有数据权限即可导出，不限制非审核人导出待审核报告
    
    # Logo路径
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'frontend', 'src', 'assets', 'images', 'whaletv-logo.png')
    
    # 如果报告已审核且有快照数据，使用快照数据
    # 注意：删除用例后 plan_case_count 会变少，但仍应使用快照数据
    _use_excel_snapshot = False
    if report.status in ['APPROVED', 'REJECTED'] and report.snapshot_data:
        try:
            snapshot = json.loads(report.snapshot_data)
            _sc = len(snapshot.get('test_cases', []))
            if _sc > 0:
                _use_excel_snapshot = True
        except (json.JSONDecodeError, TypeError):
            pass
    
    if _use_excel_snapshot:
        try:
            cover_data = snapshot.get('cover_data', {})
            
            # 构建报告数据
            report_data_dict = {
                'project_name': cover_data.get('project_name', ''),
                'logo_path': logo_path,
                'testers': cover_data.get('testers', '').replace(', ', '/'),  # Excel格式用/分隔
                'reviewer_name': cover_data.get('reviewer_name', ''),
                'verify_env': cover_data.get('verify_env', ''),
                'test_cycle': cover_data.get('test_cycle', '').replace(' ~ ', '-').replace('-', '/').replace('/', '-', 2) if cover_data.get('test_cycle') else '',
                'release_note': cover_data.get('release_note', ''),
                'risk_assessment': cover_data.get('risk_assessment', ''),
                'report_remark': cover_data.get('report_remark', ''),
                'pass_rate_value': cover_data.get('pass_rate_value', 0),
                'include_pr_closed': snapshot.get('include_pr_closed', 0),
                'has_zmind_csv': snapshot.get('has_zmind_csv', False),
                'has_assist': snapshot.get('has_assist', False),
                'issue_list': snapshot.get('issue_list', []),
                'mplist_data': snapshot.get('mplist_data', {}),
                'report_template_config': snapshot.get('report_template_config') or _get_team_report_template(db, test_plan.team_id, report.template_id)
            }
            
            # 转换test_cycle格式为Excel需要的格式
            test_cycle = cover_data.get('test_cycle', '')
            if test_cycle and ' ~ ' in test_cycle:
                parts = test_cycle.split(' ~ ')
                if len(parts) == 2:
                    report_data_dict['test_cycle'] = f"{parts[0].replace('-', '/')}-{parts[1].replace('-', '/')}"
            
            test_results = snapshot.get('test_results', [])
            zmind_stats = snapshot.get('zmind_stats', {})
            test_cases = snapshot.get('test_cases', [])
            
            # 如果快照中的test_results没有MpList统计，则补充（兼容旧快照）
            _has_mplist_in_results = any(r.get('module') == 'MpList' for r in test_results)
            if not _has_mplist_in_results:
                from utils.test_result_calc import parse_mplist_test_stats as _parse_mplist_stats_snap_excel
                mplist_data_raw = snapshot.get('mplist_data', {})
                if mplist_data_raw and isinstance(mplist_data_raw, dict) and mplist_data_raw.get('headers'):
                    _mp_stats = _parse_mplist_stats_snap_excel(mplist_data_raw)
                    if _mp_stats and _mp_stats.get('has_stats'):
                        if _mp_stats.get('has_assist'):
                            report_data_dict['has_assist'] = True
                        mplist_row = {
                            "module": "MpList",
                            "test_cases": _mp_stats['test_cases'],
                            "pass": _mp_stats['pass'],
                            "fail": _mp_stats['fail'],
                            "block": _mp_stats['block'],
                            "nt": _mp_stats['nt'],
                            "na": _mp_stats['na'],
                            "passing_rate": f"{_mp_stats['passing_rate']:.2f}%"
                        }
                        if report_data_dict.get('has_assist'):
                            mplist_row["assist"] = _mp_stats['assist']
                            for r in test_results:
                                if "assist" not in r:
                                    r["assist"] = 0
                        test_results.append(mplist_row)
            
            # 对快照用例数据重新排序（模块→Case前缀→sort_order→case_number自然排序）
            from utils.module_sort import get_module_sort_map as _get_excel_snap_sort_map
            _excel_snap_sort_map = _get_excel_snap_sort_map(db, test_plan.project_id)
            
            # Case前缀提取函数
            def _get_case_prefix(cn):
                if not cn:
                    return 'zzz'
                m = re.match(r'^([A-Za-z]+(?:_[A-Za-z]+)?)_?\d', cn or '')
                if m:
                    return m.group(1).upper()
                return 'zzz'
            
            # 模块fallback排序函数
            def _get_module_sort_key_fallback(module_path, sort_map):
                if not module_path:
                    return "9999999999"
                if module_path in sort_map:
                    return sort_map[module_path]
                parts = module_path.split('/')
                for i in range(len(parts) - 1, 0, -1):
                    prefix = '/'.join(parts[:i])
                    if prefix in sort_map:
                        return sort_map[prefix] + '.9999999999'
                return "9999999999"
            
            test_cases.sort(key=lambda tc: (
                _get_module_sort_key_fallback(tc.get("module", ""), _excel_snap_sort_map),
                _get_case_prefix(tc.get("case_number", "")),
                tc.get('sort_order', 0),
                _natural_sort_key(tc.get("case_number", ""))
            ))
            
            # 生成Excel到内存流
            excel_stream = generate_report_excel_stream(report_data_dict, test_results, zmind_stats, test_cases)
            
            # 记录日志
            log_operation(
                db=db,
                user_id=current_user.id,
                username=current_user.username,
                module=LogModule.REPORTS,
                action=LogAction.EXPORT,
                description=f"导出测试报告Excel（快照）：{report.name}（ID: {report.id}）",
                request=req
            )
            
            # URL编码文件名以支持中文（使用报告标题：项目名称 + Report）
            from urllib.parse import quote
            _excel_title = f"{report_data_dict.get('project_name', '')} Report".strip()
            safe_filename = quote(f"{_excel_title}.xlsx")
            
            # 返回流式响应
            return StreamingResponse(
                excel_stream,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"
                }
            )
        except (json.JSONDecodeError, TypeError):
            # 如果快照数据解析失败，回退到实时计算
            pass
    
    # 对于待审核的报告或没有快照数据的报告，实时计算数据
    # 获取执行数据（每个用例只取最新记录）
    executions = _get_latest_executions(db, report.test_plan_id)
    
    # 批量加载所有关联的测试用例（避免 N+1 查询）
    _tc_ids_ex = [e.test_case_id for e in executions]
    _tc_map_ex = {}
    if _tc_ids_ex:
        _all_tcs_ex = db.query(TestCase).filter(TestCase.id.in_(_tc_ids_ex)).all()
        _tc_map_ex = {tc.id: tc for tc in _all_tcs_ex}
    
    # 从测试计划获取执行周期
    if test_plan.start_time and test_plan.end_time:
        test_cycle = f"{test_plan.start_time.strftime('%Y/%m/%d')}-{test_plan.end_time.strftime('%Y/%m/%d')}"
    else:
        test_cycle = ""
    
    # 从测试计划执行人表获取测试人员
    plan_executors = db.query(TestPlanExecutor, User).join(
        User, TestPlanExecutor.executor_id == User.id
    ).filter(TestPlanExecutor.test_plan_id == test_plan.id).all()
    
    if plan_executors:
        testers = [user.username for _, user in plan_executors]
        testers_str = "/".join(testers)
    else:
        testers_str = ""
    
    # 获取审核人员
    reviewer = db.query(User).filter(User.id == test_plan.reviewer_id).first()
    reviewer_name = reviewer.username if reviewer else ""
    
    # 使用报告中用户填写的项目名称（与审核页面一致）
    project_name = report.project_name or ""
    
    # 计算测试结论（与测试计划一致：passed / (total_plan_cases - NA)）
    # 只统计有效的用例ID（排除NULL）
    plan_total_cases = db.query(TestPlanTestCase).filter(
        TestPlanTestCase.test_plan_id == report.test_plan_id,
        TestPlanTestCase.test_case_id.isnot(None)
    ).join(TestCase, TestPlanTestCase.test_case_id == TestCase.id).count()
    na_cases_count = sum(1 for e in executions if e.result == 'NA')
    total_cases = plan_total_cases
    passed_cases = sum(1 for e in executions if e.result == 'PASS')
    failed_cases = sum(1 for e in executions if e.result == 'FAIL')
    blocked_cases = sum(1 for e in executions if e.result == 'BLOCK')
    valid_cases = plan_total_cases - na_cases_count
    pass_rate = (passed_cases / valid_cases * 100) if valid_cases > 0 else 0
    
    # 按模块统计测试结果（只统计主模块，子模块归入主模块）
    module_results = {}
    for execution in executions:
        test_case = _tc_map_ex.get(execution.test_case_id)
        if test_case:
            module = (test_case.module or "未分类").split('/')[0].strip()
            if module not in module_results:
                module_results[module] = {
                    "test_cases": 0,
                    "pass": 0,
                    "fail": 0,
                    "block": 0,
                    "nt": 0,
                    "na": 0
                }
            module_results[module]["test_cases"] += 1
            if execution.result == 'PASS':
                module_results[module]["pass"] += 1
            elif execution.result == 'FAIL':
                module_results[module]["fail"] += 1
            elif execution.result == 'BLOCK':
                module_results[module]["block"] += 1
            elif execution.result == 'NT':
                module_results[module]["nt"] += 1
            elif execution.result == 'NA':
                module_results[module]["na"] += 1
    
    # 转换为列表格式
    test_results = []
    for module, result in module_results.items():
        effective_cases = result["test_cases"] - result["na"]
        test_results.append({
            "module": module,
            "test_cases": effective_cases,
            "pass": result["pass"],
            "fail": result["fail"],
            "block": result["block"],
            "nt": result["nt"],
            "na": result["na"]
        })
    
    # 按模块sort_order排序（模块统计，不需要用例级别的排序）
    from utils.module_sort import get_module_sort_map as _get_sort_map
    _sort_map = _get_sort_map(db, test_plan.project_id)
    test_results.sort(key=lambda r: _get_module_sort_key_with_fallback(r.get('module', ''), _sort_map))

    # 获取Zmind统计信息
    zmind_stats = _get_zmind_stats_for_report(report, db, test_plan.id)
    
    # 获取issue列表
    issue_list = []
    if report.zmind_issue_list:
        try:
            issue_list = json.loads(report.zmind_issue_list)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # 获取mplist数据
    mplist_data_for_excel = []
    if report.mplist_data:
        try:
            mplist_data_for_excel = json.loads(report.mplist_data)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # 如果有 MpList 数据，解析测试统计并加入 MpList 模块行
    from utils.test_result_calc import parse_mplist_test_stats as _parse_mplist_stats_excel
    _has_assist_excel = False
    if mplist_data_for_excel and isinstance(mplist_data_for_excel, dict) and mplist_data_for_excel.get('headers'):
        _mp_stats_excel = _parse_mplist_stats_excel(mplist_data_for_excel)
        if _mp_stats_excel and _mp_stats_excel.get('has_stats'):
            if _mp_stats_excel.get('has_assist'):
                _has_assist_excel = True
            mplist_row = {
                "module": "MpList",
                "test_cases": _mp_stats_excel['test_cases'],
                "pass": _mp_stats_excel['pass'],
                "fail": _mp_stats_excel['fail'],
                "block": _mp_stats_excel['block'],
                "nt": _mp_stats_excel['nt'],
                "na": _mp_stats_excel['na'],
                "passing_rate": f"{_mp_stats_excel['passing_rate']:.2f}%"
            }
            if _has_assist_excel:
                mplist_row["assist"] = _mp_stats_excel['assist']
                for r in test_results:
                    if "assist" not in r:
                        r["assist"] = 0
            test_results.append(mplist_row)
    
    # 构建报告数据
    # 从快照中提取report_remark
    _excel_remark = ''
    if report.snapshot_data:
        try:
            _snap = json.loads(report.snapshot_data)
            _excel_remark = _snap.get('cover_data', {}).get('report_remark', '')
        except (json.JSONDecodeError, TypeError):
            pass
    
    report_data_dict = {
        'project_name': project_name,
        'logo_path': logo_path,
        'testers': testers_str,
        'reviewer_name': reviewer_name,
        'verify_env': report.verify_env or '',
        'test_cycle': test_cycle,
        'release_note': report.release_note or '',
        'risk_assessment': report.risk_assessment or '',
        'report_remark': _excel_remark,
        'pass_rate_value': pass_rate,
        'include_pr_closed': report.include_pr_closed or 0,
        'has_zmind_csv': report.zmind_pr_stats is not None,
        'has_assist': _has_assist_excel,
        'issue_list': issue_list,
        'mplist_data': mplist_data_for_excel,
        'report_template_config': _get_team_report_template(db, test_plan.team_id, report.template_id)
    }
    
    # 准备用例详细数据
    test_cases = _build_test_cases_data(executions, db, test_plan.project_id, _tc_map_ex)
    
    # 生成Excel到内存流
    excel_stream = generate_report_excel_stream(report_data_dict, test_results, zmind_stats, test_cases)
    
    # 记录日志
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.REPORTS,
        action=LogAction.EXPORT,
        description=f"导出测试报告Excel：{report.name}（ID: {report.id}）",
        request=req
    )
    
    # URL编码文件名以支持中文（使用报告标题：项目名称 + Report）
    from urllib.parse import quote
    _excel_title = f"{project_name} Report".strip()
    safe_filename = quote(f"{_excel_title}.xlsx")
    
    # 返回流式响应
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"
        }
    )

@router.get("/{report_id}/export/pdf")
def export_report_pdf(
    req: Request,
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出测试报告为PDF格式，直接流式返回不保存到服务器"""
    from fastapi import HTTPException
    from fastapi.responses import StreamingResponse
    from models import TestPlan, TestCase
    from utils.report_pdf import generate_report_pdf_stream
    import os
    import io
    import logging
    import traceback
    
    logger = logging.getLogger(__name__)
    logger.info(f"[PDF导出] 开始导出报告ID: {report_id}, 用户: {current_user.username}")
    
    # 获取报告信息
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        logger.error(f"[PDF导出] 报告不存在, report_id: {report_id}")
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 获取测试计划信息
    test_plan = db.query(TestPlan).filter(TestPlan.id == report.test_plan_id).first()
    if not test_plan:
        logger.error(f"[PDF导出] 测试计划不存在, test_plan_id: {report.test_plan_id}")
        raise HTTPException(status_code=404, detail="测试计划不存在")
    
    logger.info(f"[PDF导出] 报告状态: {report.status}, snapshot_data存在: {bool(report.snapshot_data)}")
    
    # 导出权限：有数据权限即可导出，不限制非审核人导出待审核报告
    
    # Logo路径
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'frontend', 'src', 'assets', 'images', 'whaletv-logo.png')
    
    # 如果报告已审核且有快照数据，使用快照数据
    # 注意：删除用例后 plan_case_count 会变少，但仍应使用快照数据
    _use_pdf_snapshot = False
    if report.status in ['APPROVED', 'REJECTED'] and report.snapshot_data:
        try:
            snapshot = json.loads(report.snapshot_data)
            _sc = len(snapshot.get('test_cases', []))
            if _sc > 0:
                _use_pdf_snapshot = True
                logger.info(f"[PDF导出] 快照解析成功, test_cases数量: {_sc}")
            else:
                logger.warning(f"[PDF导出] 快照数据为空, test_cases数量: {_sc}")
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"[PDF导出] 快照解析失败: {e}")
    
    if _use_pdf_snapshot:
        try:
            cover_data = snapshot.get('cover_data', {})
            
            # 构建报告数据
            report_data_dict = {
                'project_name': cover_data.get('project_name', ''),
                'logo_path': logo_path,
                'testers': cover_data.get('testers', ''),
                'reviewer_name': cover_data.get('reviewer_name', ''),
                'verify_env': cover_data.get('verify_env', ''),
                'test_cycle': cover_data.get('test_cycle', ''),
                'release_note': cover_data.get('release_note', ''),
                'risk_assessment': cover_data.get('risk_assessment', ''),
                'report_remark': cover_data.get('report_remark', ''),
                'pass_rate_value': cover_data.get('pass_rate_value', 0),
                'include_pr_closed': snapshot.get('include_pr_closed', 0),
                'has_zmind_csv': snapshot.get('has_zmind_csv', False),
                'has_assist': snapshot.get('has_assist', False),
                'report_template_config': snapshot.get('report_template_config') or _get_team_report_template(db, test_plan.team_id, report.template_id)
            }
            
            # 转换test_results格式为PDF需要的格式
            _snap_has_assist = snapshot.get('has_assist', False)
            # 如果快照没有 has_assist 字段，从 test_results 数据中检测
            if not _snap_has_assist:
                _snap_has_assist = any(r.get('assist', 0) > 0 for r in snapshot.get('test_results', []))
                if _snap_has_assist:
                    report_data_dict['has_assist'] = True
            
            # 如果快照中的test_results没有MpList统计，则补充（兼容旧快照）
            _snap_test_results_raw = snapshot.get('test_results', [])
            _has_mplist_in_results = any(r.get('module') == 'MpList' for r in _snap_test_results_raw)
            if not _has_mplist_in_results:
                from utils.test_result_calc import parse_mplist_test_stats as _parse_mplist_stats_snap_pdf
                mplist_data_raw = snapshot.get('mplist_data', {})
                if mplist_data_raw and isinstance(mplist_data_raw, dict) and mplist_data_raw.get('headers'):
                    _mp_stats = _parse_mplist_stats_snap_pdf(mplist_data_raw)
                    if _mp_stats and _mp_stats.get('has_stats'):
                        if _mp_stats.get('has_assist'):
                            _snap_has_assist = True
                            report_data_dict['has_assist'] = True
                        mplist_row = {
                            "module": "MpList",
                            "test_cases": _mp_stats['test_cases'],
                            "pass": _mp_stats['pass'],
                            "fail": _mp_stats['fail'],
                            "block": _mp_stats['block'],
                            "nt": _mp_stats['nt'],
                            "na": _mp_stats['na'],
                            "passing_rate": f"{_mp_stats['passing_rate']:.2f}%"
                        }
                        if _snap_has_assist:
                            mplist_row["assist"] = _mp_stats['assist']
                            for r in _snap_test_results_raw:
                                if "assist" not in r:
                                    r["assist"] = 0
                        _snap_test_results_raw.append(mplist_row)
            
            test_results = []
            for result in _snap_test_results_raw:
                effective_cases = result.get('test_cases', 0)
                pass_count = result.get('pass', 0)
                passing_rate = (pass_count / effective_cases) if effective_cases > 0 else 0
                row = {
                    "module": result.get('module', ''),
                    "test_cases": effective_cases,
                    "pass": pass_count,
                    "fail": result.get('fail', 0),
                    "block": result.get('block', 0),
                    "nt": result.get('nt', 0),
                    "na": result.get('na', 0),
                    "passing_rate": f"{passing_rate:.4f}"
                }
                if _snap_has_assist:
                    row["assist"] = result.get('assist', 0)
                test_results.append(row)
            
            zmind_stats = snapshot.get('zmind_stats', {})
            test_cases = snapshot.get('test_cases', [])
            issue_list = snapshot.get('issue_list', [])
            mplist_data_for_pdf = snapshot.get('mplist_data', [])
            
            # 找出超长用例
            max_steps_len = 0
            max_steps_case = None
            for tc in test_cases:
                steps = tc.get('steps', '') or ''
                if len(steps) > max_steps_len:
                    max_steps_len = len(steps)
                    max_steps_case = tc.get('case_number', '')
            logger.info(f"[PDF导出] 用例steps最大长度: {max_steps_len}字符, case: {max_steps_case}")
            
            # 对快照用例数据重新排序（模块→Case前缀→sort_order→case_number自然排序）
            from utils.module_sort import get_module_sort_map as _get_snap_sort_map
            _snap_sort_map = _get_snap_sort_map(db, test_plan.project_id)
            
            def _get_case_prefix(cn):
                if not cn:
                    return 'zzz'
                m = re.match(r'^([A-Za-z]+(?:_[A-Za-z]+)?)_?\d', cn or '')
                if m:
                    return m.group(1).upper()
                return 'zzz'
            
            def _get_module_sort_key_fallback(module_path, sort_map):
                if not module_path:
                    return "9999999999"
                if module_path in sort_map:
                    return sort_map[module_path]
                parts = module_path.split('/')
                for i in range(len(parts) - 1, 0, -1):
                    prefix = '/'.join(parts[:i])
                    if prefix in sort_map:
                        return sort_map[prefix] + '.9999999999'
                return "9999999999"
            
            test_cases.sort(key=lambda tc: (
                _get_module_sort_key_fallback(tc.get("module", ""), _snap_sort_map),
                _get_case_prefix(tc.get("case_number", "")),
                tc.get('sort_order', 0),
                _natural_sort_key(tc.get("case_number", ""))
            ))
            
            logger.info(f"[PDF导出] 使用快照数据, test_results条数: {len(test_results)}, test_cases条数: {len(test_cases)}, zmind_stats: {zmind_stats}")
            
            try:
                # 生成PDF到内存流
                pdf_stream = generate_report_pdf_stream(report_data_dict, test_results, zmind_stats, test_cases, issue_list, mplist_data=mplist_data_for_pdf)
                logger.info(f"[PDF导出] PDF生成成功, report_id: {report_id}")
            except Exception as e:
                logger.error(f"[PDF导出] PDF生成失败: {str(e)}")
                logger.error(f"[PDF导出] 堆栈: {traceback.format_exc()}")
                raise
            
            # 记录日志
            log_operation(
                db=db,
                user_id=current_user.id,
                username=current_user.username,
                module=LogModule.REPORTS,
                action=LogAction.EXPORT,
                description=f"导出测试报告PDF（快照）：{report.name}（ID: {report.id}）",
                request=req
            )
            
            # URL编码文件名以支持中文（使用报告标题：项目名称 + Report）
            from urllib.parse import quote
            _pdf_title = f"{report_data_dict.get('project_name', '')} Report".strip()
            safe_filename = quote(f"{_pdf_title}.pdf")
            
            # 返回流式响应
            return StreamingResponse(
                pdf_stream,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"
                }
            )
        except (json.JSONDecodeError, TypeError):
            # 如果快照数据解析失败，回退到实时计算
            pass
    
    # 对于待审核的报告或没有快照数据的报告，实时计算数据
    # 获取执行数据（每个用例只取最新记录）
    executions = _get_latest_executions(db, report.test_plan_id)
    
    # 批量加载所有关联的测试用例（避免 N+1 查询）
    _tc_ids_pdf = [e.test_case_id for e in executions]
    _tc_map_pdf = {}
    if _tc_ids_pdf:
        _all_tcs_pdf = db.query(TestCase).filter(TestCase.id.in_(_tc_ids_pdf)).all()
        _tc_map_pdf = {tc.id: tc for tc in _all_tcs_pdf}
    
    # 从测试计划获取执行周期
    if test_plan.start_time and test_plan.end_time:
        test_cycle = f"{test_plan.start_time.strftime('%Y-%m-%d')} ~ {test_plan.end_time.strftime('%Y-%m-%d')}"
    else:
        test_cycle = ""
    
    # 从测试计划执行人表获取测试人员
    plan_executors = db.query(TestPlanExecutor, User).join(
        User, TestPlanExecutor.executor_id == User.id
    ).filter(TestPlanExecutor.test_plan_id == test_plan.id).all()
    
    if plan_executors:
        testers = [user.username for _, user in plan_executors]
        testers_str = ", ".join(testers)
    else:
        testers_str = ""
    
    # 获取审核人员
    reviewer = db.query(User).filter(User.id == test_plan.reviewer_id).first()
    reviewer_name = reviewer.username if reviewer else ""
    
    # 使用报告中用户填写的项目名称（与审核页面一致）
    project_name = report.project_name or ""
    
    # 计算测试结论（与测试计划一致：passed / (total_plan_cases - NA)）
    # 只统计有效的用例ID（排除NULL）
    plan_total_cases = db.query(TestPlanTestCase).filter(
        TestPlanTestCase.test_plan_id == report.test_plan_id,
        TestPlanTestCase.test_case_id.isnot(None)
    ).join(TestCase, TestPlanTestCase.test_case_id == TestCase.id).count()
    na_cases_count = sum(1 for e in executions if e.result == 'NA')
    total_cases = plan_total_cases
    passed_cases = sum(1 for e in executions if e.result == 'PASS')
    failed_cases = sum(1 for e in executions if e.result == 'FAIL')
    blocked_cases = sum(1 for e in executions if e.result == 'BLOCK')
    valid_cases = plan_total_cases - na_cases_count
    pass_rate = (passed_cases / valid_cases * 100) if valid_cases > 0 else 0
    
    if pass_rate >= 95:
        test_conclusion = "测试通过"
    else:
        test_conclusion = "测试未通过"
    
    # 按模块统计测试结果（只统计主模块，子模块归入主模块）
    module_results = {}
    _pdf_has_assist = False
    for execution in executions:
        test_case = _tc_map_pdf.get(execution.test_case_id)
        if test_case:
            module = (test_case.module or "未分类").split('/')[0].strip()
            if module not in module_results:
                module_results[module] = {
                    "test_cases": 0,
                    "pass": 0,
                    "fail": 0,
                    "block": 0,
                    "nt": 0,
                    "na": 0,
                    "assist": 0
                }
            module_results[module]["test_cases"] += 1
            result_val = (execution.result or '').strip()
            if result_val == 'PASS':
                module_results[module]["pass"] += 1
            elif result_val == 'FAIL':
                module_results[module]["fail"] += 1
            elif result_val == 'BLOCK':
                module_results[module]["block"] += 1
            elif result_val == 'NT':
                module_results[module]["nt"] += 1
            elif result_val == 'NA':
                module_results[module]["na"] += 1
            elif result_val == '协测':
                module_results[module]["assist"] += 1
                _pdf_has_assist = True
    
    # 转换为列表格式，修复百分比显示
    test_results = []
    for module, result in module_results.items():
        effective_cases = result["test_cases"] - result["na"] - result["assist"]
        passing_rate = (result["pass"] / effective_cases) if effective_cases > 0 else 0
        row = {
            "module": module,
            "test_cases": effective_cases,
            "pass": result["pass"],
            "fail": result["fail"],
            "block": result["block"],
            "nt": result["nt"],
            "na": result["na"],
            "passing_rate": f"{passing_rate:.4f}"
        }
        if _pdf_has_assist:
            row["assist"] = result["assist"]
        test_results.append(row)
    
    # 按模块sort_order排序（模块统计，不需要用例级别的排序）
    from utils.module_sort import get_module_sort_map as _get_sort_map
    _sort_map = _get_sort_map(db, test_plan.project_id)
    test_results.sort(key=lambda r: _get_module_sort_key_with_fallback(r.get('module', ''), _sort_map))

    # 获取Zmind统计信息
    zmind_stats = _get_zmind_stats_for_report(report, db, test_plan.id)
    
    # 构建报告数据
    # 从快照中提取report_remark
    _pdf_remark = ''
    if report.snapshot_data:
        try:
            _snap = json.loads(report.snapshot_data)
            _pdf_remark = _snap.get('cover_data', {}).get('report_remark', '')
        except (json.JSONDecodeError, TypeError):
            pass
    
    report_data_dict = {
        'project_name': project_name,
        'logo_path': logo_path,
        'testers': testers_str,
        'reviewer_name': reviewer_name,
        'verify_env': report.verify_env or '',
        'test_cycle': test_cycle,
        'release_note': report.release_note or '',
        'risk_assessment': report.risk_assessment or '',
        'report_remark': _pdf_remark,
        'pass_rate_value': pass_rate,
        'include_pr_closed': report.include_pr_closed or 0,
        'has_zmind_csv': report.zmind_pr_stats is not None,
        'has_assist': _pdf_has_assist,
        'report_template_config': _get_team_report_template(db, test_plan.team_id, report.template_id)
    }
    
    # 准备用例详细数据
    test_cases = _build_test_cases_data(executions, db, test_plan.project_id, _tc_map_pdf)
    
    # 获取issue列表
    issue_list = []
    if report.zmind_issue_list:
        try:
            issue_list = json.loads(report.zmind_issue_list)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # 获取mplist数据
    mplist_data_for_pdf = []
    if report.mplist_data:
        try:
            mplist_data_for_pdf = json.loads(report.mplist_data)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # 如果有 MpList 数据，解析测试统计并加入 MpList 模块行
    from utils.test_result_calc import parse_mplist_test_stats as _parse_mplist_stats_pdf
    if mplist_data_for_pdf and isinstance(mplist_data_for_pdf, dict) and mplist_data_for_pdf.get('headers'):
        _mp_stats_pdf = _parse_mplist_stats_pdf(mplist_data_for_pdf)
        if _mp_stats_pdf and _mp_stats_pdf.get('has_stats'):
            if _mp_stats_pdf.get('has_assist'):
                _pdf_has_assist = True
            mplist_row = {
                "module": "MpList",
                "test_cases": _mp_stats_pdf['test_cases'],
                "pass": _mp_stats_pdf['pass'],
                "fail": _mp_stats_pdf['fail'],
                "block": _mp_stats_pdf['block'],
                "nt": _mp_stats_pdf['nt'],
                "na": _mp_stats_pdf['na'],
                "passing_rate": f"{_mp_stats_pdf['passing_rate']:.2f}%"
            }
            if _pdf_has_assist:
                mplist_row["assist"] = _mp_stats_pdf['assist']
                for r in test_results:
                    if "assist" not in r:
                        r["assist"] = 0
            test_results.append(mplist_row)
    
    logger.info(f"[PDF导出] 实时计算模式, test_results条数: {len(test_results)}, test_cases条数: {len(test_cases)}, zmind_stats: {zmind_stats}")
    
    try:
        # 生成PDF到内存流
        pdf_stream = generate_report_pdf_stream(report_data_dict, test_results, zmind_stats, test_cases, issue_list, mplist_data=mplist_data_for_pdf)
        logger.info(f"[PDF导出] PDF生成成功, report_id: {report_id}")
    except Exception as e:
        logger.error(f"[PDF导出] PDF生成失败: {str(e)}")
        logger.error(f"[PDF导出] 堆栈: {traceback.format_exc()}")
        raise
    
    # 记录日志
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.REPORTS,
        action=LogAction.EXPORT,
        description=f"导出测试报告PDF：{report.name}（ID: {report.id}）",
        request=req
    )

    # URL编码文件名以支持中文（使用报告标题：项目名称 + Report）
    from urllib.parse import quote
    _pdf_title = f"{project_name} Report".strip()
    safe_filename = quote(f"{_pdf_title}.pdf")

    # 返回流式响应
    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"
        }
    )


# ==================== 异步导出接口（后台生成，避免大文件超时504） ====================

import os as _os
import uuid as _uuid
from database import SessionLocal as _SessionLocal
from utils.report_pdf import generate_report_pdf_stream as _generate_pdf_stream
from utils.report_excel import generate_report_excel_stream as _generate_excel_stream


def _save_pdf_to_file(report_id, db, current_user, export_dir, progress_callback=None):
    from fastapi import HTTPException
    import json, re, os

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    test_plan = db.query(TestPlan).filter(TestPlan.id == report.test_plan_id).first()
    if not test_plan:
        raise HTTPException(status_code=404, detail="测试计划不存在")

    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'frontend', 'src', 'assets', 'images', 'whaletv-logo.png')

    if progress_callback: progress_callback(5, '正在加载快照数据...')
    snapshot = json.loads(report.snapshot_data)
    cover_data = snapshot.get('cover_data', {})
    report_data_dict = {
        'project_name': cover_data.get('project_name', ''),
        'logo_path': logo_path,
        'testers': cover_data.get('testers', ''),
        'reviewer_name': cover_data.get('reviewer_name', ''),
        'verify_env': cover_data.get('verify_env', ''),
        'test_cycle': cover_data.get('test_cycle', ''),
        'release_note': cover_data.get('release_note', ''),
        'risk_assessment': cover_data.get('risk_assessment', ''),
        'report_remark': cover_data.get('report_remark', ''),
        'pass_rate_value': cover_data.get('pass_rate_value', 0),
        'include_pr_closed': snapshot.get('include_pr_closed', 0),
        'has_zmind_csv': snapshot.get('has_zmind_csv', False),
        'has_assist': snapshot.get('has_assist', False),
        'report_template_config': snapshot.get('report_template_config') or _get_team_report_template(db, test_plan.team_id, report.template_id)
    }
    test_results = snapshot.get('test_results', [])
    test_cases = snapshot.get('test_cases', [])
    issue_list = snapshot.get('issue_list', [])
    mplist_data = snapshot.get('mplist_data', [])
    zmind_stats = snapshot.get('zmind_stats', {})
    
    # 如果快照中的test_results没有MpList统计，则补充（兼容旧快照）
    _has_mplist_in_results = any(r.get('module') == 'MpList' for r in test_results)
    if not _has_mplist_in_results:
        from utils.test_result_calc import parse_mplist_test_stats as _parse_mplist_stats_async_pdf
        mplist_data_raw = snapshot.get('mplist_data', {})
        if mplist_data_raw and isinstance(mplist_data_raw, dict) and mplist_data_raw.get('headers'):
            _mp_stats = _parse_mplist_stats_async_pdf(mplist_data_raw)
            if _mp_stats and _mp_stats.get('has_stats'):
                if _mp_stats.get('has_assist'):
                    report_data_dict['has_assist'] = True
                mplist_row = {
                    "module": "MpList",
                    "test_cases": _mp_stats['test_cases'],
                    "pass": _mp_stats['pass'],
                    "fail": _mp_stats['fail'],
                    "block": _mp_stats['block'],
                    "nt": _mp_stats['nt'],
                    "na": _mp_stats['na'],
                    "passing_rate": f"{_mp_stats['passing_rate']:.2f}%"
                }
                if report_data_dict.get('has_assist'):
                    mplist_row["assist"] = _mp_stats['assist']
                    for r in test_results:
                        if "assist" not in r:
                            r["assist"] = 0
                test_results.append(mplist_row)

    if progress_callback: progress_callback(10, '正在排序用例...')
    from utils.module_sort import get_module_sort_map as _get_snap_sort_map
    _snap_sort_map = _get_snap_sort_map(db, test_plan.project_id)

    def _get_case_prefix(cn):
        if not cn: return 'zzz'
        m = re.match(r'^([A-Za-z]+(?:_[A-Za-z]+)?)_?\d', cn or '')
        return m.group(1).upper() if m else 'zzz'

    def _get_module_sort_key_fallback(module_path, sort_map):
        if not module_path: return "9999999999"
        if module_path in sort_map: return sort_map[module_path]
        parts = module_path.split('/')
        for i in range(len(parts) - 1, 0, -1):
            prefix = '/'.join(parts[:i])
            if prefix in sort_map: return sort_map[prefix] + '.9999999999'
        return "9999999999"

    test_cases.sort(key=lambda tc: (
        _get_module_sort_key_fallback(tc.get("module", ""), _snap_sort_map),
        _get_case_prefix(tc.get("case_number", "")),
        tc.get('sort_order', 0),
        _natural_sort_key(tc.get("case_number", ""))
    ))

    if progress_callback: progress_callback(15, '正在生成PDF内容...')
    pdf_stream = _generate_pdf_stream(report_data_dict, test_results, zmind_stats, test_cases, issue_list, mplist_data=mplist_data, progress_callback=progress_callback)

    if progress_callback: progress_callback(85, '正在写入PDF文件...')
    _pdf_title = f"{report_data_dict.get('project_name', '')} Report".strip()
    safe_filename = f"{_pdf_title}.pdf"
    file_path = os.path.join(export_dir, f"{_uuid.uuid4().hex}.pdf")
    with open(file_path, 'wb') as f:
        f.write(pdf_stream.getvalue())
    if progress_callback: progress_callback(95, '导出完成')
    return file_path, safe_filename


def _save_excel_to_file(report_id, db, current_user, export_dir, progress_callback=None):
    from fastapi import HTTPException
    import json, os

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    test_plan = db.query(TestPlan).filter(TestPlan.id == report.test_plan_id).first()
    if not test_plan:
        raise HTTPException(status_code=404, detail="测试计划不存在")

    if progress_callback: progress_callback(5, '正在加载快照数据...')
    snapshot = json.loads(report.snapshot_data)
    cover_data = snapshot.get('cover_data', {})
    test_cycle_raw = cover_data.get('test_cycle', '')
    test_cycle_excel = test_cycle_raw.replace(' ~ ', '-').replace('-', '/').replace('/', '-', 2) if test_cycle_raw else ''

    report_data_dict = {
        'project_name': cover_data.get('project_name', ''),
        'logo_path': os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'frontend', 'src', 'assets', 'images', 'whaletv-logo.png'),
        'testers': cover_data.get('testers', '').replace(', ', '/'),
        'reviewer_name': cover_data.get('reviewer_name', ''),
        'verify_env': cover_data.get('verify_env', ''),
        'test_cycle': test_cycle_excel,
        'release_note': cover_data.get('release_note', ''),
        'risk_assessment': cover_data.get('risk_assessment', ''),
        'report_remark': cover_data.get('report_remark', ''),
        'pass_rate_value': cover_data.get('pass_rate_value', 0),
        'include_pr_closed': snapshot.get('include_pr_closed', 0),
        'has_zmind_csv': snapshot.get('has_zmind_csv', False),
        'has_assist': snapshot.get('has_assist', False),
        'issue_list': snapshot.get('issue_list', []),
        'mplist_data': snapshot.get('mplist_data', {}),
        'report_template_config': snapshot.get('report_template_config') or _get_team_report_template(db, test_plan.team_id, report.template_id)
    }
    test_results = snapshot.get('test_results', [])
    test_cases = snapshot.get('test_cases', [])
    zmind_stats = snapshot.get('zmind_stats', {})
    
    # 如果快照中的test_results没有MpList统计，则补充（兼容旧快照）
    _has_mplist_in_results = any(r.get('module') == 'MpList' for r in test_results)
    if not _has_mplist_in_results:
        from utils.test_result_calc import parse_mplist_test_stats as _parse_mplist_stats_async_excel
        mplist_data_raw = snapshot.get('mplist_data', {})
        if mplist_data_raw and isinstance(mplist_data_raw, dict) and mplist_data_raw.get('headers'):
            _mp_stats = _parse_mplist_stats_async_excel(mplist_data_raw)
            if _mp_stats and _mp_stats.get('has_stats'):
                if _mp_stats.get('has_assist'):
                    report_data_dict['has_assist'] = True
                mplist_row = {
                    "module": "MpList",
                    "test_cases": _mp_stats['test_cases'],
                    "pass": _mp_stats['pass'],
                    "fail": _mp_stats['fail'],
                    "block": _mp_stats['block'],
                    "nt": _mp_stats['nt'],
                    "na": _mp_stats['na'],
                    "passing_rate": f"{_mp_stats['passing_rate']:.2f}%"
                }
                if report_data_dict.get('has_assist'):
                    mplist_row["assist"] = _mp_stats['assist']
                    for r in test_results:
                        if "assist" not in r:
                            r["assist"] = 0
                test_results.append(mplist_row)

    # 对用例数据排序（与其他导出路径保持一致：模块→Case前缀→sort_order→case_number自然排序）
    import re as _re
    from utils.module_sort import get_module_sort_map as _get_excel_async_sort_map
    _excel_async_sort_map = _get_excel_async_sort_map(db, test_plan.project_id)

    def _excel_async_case_prefix(cn):
        if not cn: return 'zzz'
        m = _re.match(r'^([A-Za-z]+(?:_[A-Za-z]+)?)_?\d', cn or '')
        return m.group(1).upper() if m else 'zzz'

    def _excel_async_module_sort_key(module_path):
        if not module_path: return "9999999999"
        if module_path in _excel_async_sort_map: return _excel_async_sort_map[module_path]
        parts = module_path.split('/')
        for i in range(len(parts) - 1, 0, -1):
            prefix = '/'.join(parts[:i])
            if prefix in _excel_async_sort_map: return _excel_async_sort_map[prefix] + '.9999999999'
        return "9999999999"

    test_cases.sort(key=lambda tc: (
        _excel_async_module_sort_key(tc.get("module", "")),
        _excel_async_case_prefix(tc.get("case_number", "")),
        tc.get('sort_order', 0),
        _natural_sort_key(tc.get("case_number", ""))
    ))

    if progress_callback: progress_callback(15, '正在生成Excel内容...')
    excel_stream = _generate_excel_stream(report_data_dict, test_results, zmind_stats, test_cases, progress_callback=progress_callback)

    if progress_callback: progress_callback(85, '正在写入Excel文件...')
    _excel_title = f"{report_data_dict.get('project_name', '')} Report".strip()
    safe_filename = f"{_excel_title}.xlsx"
    file_path = os.path.join(export_dir, f"{_uuid.uuid4().hex}.xlsx")
    with open(file_path, 'wb') as f:
        f.write(excel_stream.getvalue())
    if progress_callback: progress_callback(95, '导出完成')
    return file_path, safe_filename


@router.post("/{report_id}/export/async/{format}")
def start_async_export(
    report_id: int,
    format: str,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if format not in ('pdf', 'excel'):
        raise HTTPException(status_code=400, detail="不支持的导出格式，仅支持 pdf/excel")

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    if not report.snapshot_data:
        raise HTTPException(status_code=400, detail="报告尚未审核，请先审核后再导出")
    project_name = report.project_name or ""

    export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')
    os.makedirs(export_dir, exist_ok=True)

    def _background_pdf():
        _db = _SessionLocal()
        try:
            _prog = lambda p, m=None: set_progress(task_id, p, m)
            # 心跳线程：在 doc.build 阻塞期间持续推进进度，避免前端进度条卡死
            _stop_heartbeat = threading.Event()
            def _heartbeat():
                _p = 35
                while not _stop_heartbeat.is_set():
                    _stop_heartbeat.wait(5)
                    if _stop_heartbeat.is_set():
                        break
                    _p = min(_p + 3, 75)
                    set_progress(task_id, _p, '正在渲染PDF布局，请耐心等待...')
            _hb = threading.Thread(target=_heartbeat, daemon=True)
            _hb.start()
            try:
                return _save_pdf_to_file(report_id, _db, current_user, export_dir, progress_callback=_prog)
            finally:
                _stop_heartbeat.set()
        finally:
            _db.close()

    def _background_excel():
        _db = _SessionLocal()
        try:
            _prog = lambda p, m=None: set_progress(task_id, p, m)
            _stop_heartbeat = threading.Event()
            def _heartbeat():
                _p = 50
                while not _stop_heartbeat.is_set():
                    _stop_heartbeat.wait(5)
                    if _stop_heartbeat.is_set():
                        break
                    _p = min(_p + 3, 80)
                    set_progress(task_id, _p, '正在写入Excel文件，请耐心等待...')
            _hb = threading.Thread(target=_heartbeat, daemon=True)
            _hb.start()
            try:
                return _save_excel_to_file(report_id, _db, current_user, export_dir, progress_callback=_prog)
            finally:
                _stop_heartbeat.set()
        finally:
            _db.close()

    target_func = _background_pdf if format == 'pdf' else _background_excel
    task_id = start_export(report_id, format, f"{project_name} Report.{format}", target_func)
    return {"code": 200, "data": {"task_id": task_id}}


@router.get("/exports/tasks/{task_id}")
def get_export_task_status(task_id: str):
    status = get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="导出任务不存在")
    return {"code": 200, "data": status}


@router.get("/exports/tasks/{task_id}/download")
def download_export_task(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="导出任务不存在")
    if task.status == 'failed':
        raise HTTPException(status_code=500, detail=f"导出失败: {task.error}")
    if task.status != 'completed':
        raise HTTPException(status_code=400, detail="导出尚未完成")
    if not task.file_path or not os.path.exists(task.file_path):
        raise HTTPException(status_code=500, detail="导出文件不存在")

    from urllib.parse import quote
    safe_filename = quote(task.report_name or "report")

    media_type = "application/pdf" if task.format_type == 'pdf' else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def _cleanup_and_stream():
        with open(task.file_path, 'rb') as f:
            yield from f
        try:
            os.remove(task.file_path)
        except OSError:
            pass

    return StreamingResponse(
        _cleanup_and_stream(),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"}
    )
