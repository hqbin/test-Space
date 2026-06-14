"""
数据统计分析 API - 提供全平台数据的可视化统计与自由筛选
支持：用例统计、计划统计、执行统计、用户统计、项目统计、趋势分析
"""
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, distinct, extract
from database import get_db
from models import (
    User, TestCase, TestPlan, TestExecution, TestPlanTestCase, TestPlanExecutor,
    Project, UserProject, Team, TeamProject, UserTeam, Report,
    ReviewPlan, ReviewPlanTestCase, Department, Module, TeamLeader, DepartmentManager, UserDepartment
)
from auth import get_current_user
from typing import Optional, List
from datetime import datetime, timedelta
import json

router = APIRouter()

SUPER_ADMINS = ['admin', 'super']


def _is_super_admin(user: User) -> bool:
    return user.username in SUPER_ADMINS


def _get_accessible_project_ids(db: Session, user: User, team_id: int = None) -> Optional[List[int]]:
    """获取用户可访问的项目ID列表，None表示不限制（超管）"""
    if _is_super_admin(user):
        if team_id:
            rows = db.query(TeamProject.project_id).filter(TeamProject.team_id == team_id).all()
            return [r.project_id for r in rows]
        return None

    if team_id:
        rows = db.query(TeamProject.project_id).filter(TeamProject.team_id == team_id).all()
        return [r.project_id for r in rows]

    rows = db.query(UserProject.project_id).filter(UserProject.user_id == user.id).all()
    return [r.project_id for r in rows]


def _apply_project_filter(query, project_id_col, project_ids: Optional[List[int]]):
    """应用项目过滤"""
    if project_ids is None:
        return query
    if not project_ids:
        return query.filter(False)
    return query.filter(project_id_col.in_(project_ids))


def _get_managed_dept_ids(db: Session, user: User) -> List[int]:
    """获取用户作为负责人管理的组织ID列表"""
    from models import DepartmentManager
    rows = db.query(DepartmentManager.department_id).filter(
        DepartmentManager.user_id == user.id
    ).all()
    return [r.department_id for r in rows]


@router.get("/overview")
def get_analytics_overview(
    team_id: Optional[int] = None,
    project_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """总览统计 - 核心指标卡片"""
    pids = _get_accessible_project_ids(db, current_user, team_id)
    if project_id:
        pids = [project_id] if (pids is None or project_id in pids) else []

    # 用例总数
    tc_q = db.query(func.count(TestCase.id))
    tc_q = _apply_project_filter(tc_q, TestCase.primary_project_id, pids)
    total_cases = tc_q.scalar() or 0

    # 测试计划总数
    tp_q = db.query(func.count(TestPlan.id))
    tp_q = _apply_project_filter(tp_q, TestPlan.project_id, pids)
    total_plans = tp_q.scalar() or 0

    # 执行记录总数（排除 ONGOING 中间状态）
    te_q = db.query(func.count(TestExecution.id)).filter(TestExecution.result != 'ONGOING')
    if pids is not None:
        te_q = te_q.join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        te_q = te_q.filter(TestPlan.project_id.in_(pids)) if pids else te_q.filter(False)
    total_executions = te_q.scalar() or 0

    # 报告总数
    rp_q = db.query(func.count(Report.id))
    if pids is not None:
        rp_q = rp_q.join(TestPlan, Report.test_plan_id == TestPlan.id)
        rp_q = rp_q.filter(TestPlan.project_id.in_(pids)) if pids else rp_q.filter(False)
    total_reports = rp_q.scalar() or 0

    # 活跃用户数（有执行记录的用户）
    au_q = db.query(func.count(distinct(TestExecution.executor_id)))
    if pids is not None:
        au_q = au_q.join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        au_q = au_q.filter(TestPlan.project_id.in_(pids)) if pids else au_q.filter(False)
    active_users = au_q.scalar() or 0

    # 用例通过率（排除 ONGOING 中间状态）
    pass_q = db.query(func.count(TestExecution.id)).filter(TestExecution.result == 'PASS')
    total_exec_q = db.query(func.count(TestExecution.id)).filter(
        TestExecution.result.isnot(None),
        TestExecution.result != 'ONGOING'
    )
    if pids is not None:
        pass_q = pass_q.join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        total_exec_q = total_exec_q.join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        if pids:
            pass_q = pass_q.filter(TestPlan.project_id.in_(pids))
            total_exec_q = total_exec_q.filter(TestPlan.project_id.in_(pids))
        else:
            pass_q = pass_q.filter(False)
            total_exec_q = total_exec_q.filter(False)
    pass_count = pass_q.scalar() or 0
    total_exec_count = total_exec_q.scalar() or 0
    pass_rate = round(pass_count / total_exec_count * 100, 1) if total_exec_count > 0 else 0

    return {
        "code": 200,
        "data": {
            "total_cases": total_cases,
            "total_plans": total_plans,
            "total_executions": total_executions,
            "total_reports": total_reports,
            "active_users": active_users,
            "pass_rate": pass_rate
        }
    }


@router.get("/testcase-stats")
def get_testcase_stats(
    team_id: Optional[int] = None,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """用例统计 - 按等级、状态、模块、自动化分布"""
    pids = _get_accessible_project_ids(db, current_user, team_id)
    if project_id:
        pids = [project_id] if (pids is None or project_id in pids) else []

    base_q = db.query(TestCase)
    base_q = _apply_project_filter(base_q, TestCase.primary_project_id, pids)

    # 按等级分布
    level_rows = db.query(TestCase.level, func.count(TestCase.id))
    level_rows = _apply_project_filter(level_rows, TestCase.primary_project_id, pids)
    level_rows = level_rows.group_by(TestCase.level).all()
    by_level = [{"name": r[0] or "未设置", "value": r[1]} for r in level_rows]

    # 按状态分布
    status_rows = db.query(TestCase.status, func.count(TestCase.id))
    status_rows = _apply_project_filter(status_rows, TestCase.primary_project_id, pids)
    status_rows = status_rows.group_by(TestCase.status).all()
    by_status = [{"name": r[0] or "未设置", "value": r[1]} for r in status_rows]

    # 按自动化分布
    auto_rows = db.query(TestCase.automation, func.count(TestCase.id))
    auto_rows = _apply_project_filter(auto_rows, TestCase.primary_project_id, pids)
    auto_rows = auto_rows.group_by(TestCase.automation).all()
    by_automation = []
    for r in auto_rows:
        auto_val = r[0]
        if auto_val == 'Y':
            name = "已自动化"
        elif auto_val and auto_val.startswith('N-'):
            name = "无法自动化"
        elif auto_val == 'N':
            name = "无法自动化"
        else:
            name = "未标记"
        by_automation.append({"name": name, "value": r[1]})

    # 按用例库（项目）分布 - Top 10
    proj_rows = db.query(Project.name, func.count(TestCase.id))
    proj_rows = proj_rows.join(Project, TestCase.primary_project_id == Project.id)
    proj_rows = _apply_project_filter(proj_rows, TestCase.primary_project_id, pids)
    proj_rows = proj_rows.group_by(Project.name).order_by(func.count(TestCase.id).desc()).limit(10).all()
    by_project = [{"name": r[0], "value": r[1]} for r in proj_rows]

    # 按模块分布 - Top 10
    mod_rows = db.query(TestCase.module, func.count(TestCase.id))
    mod_rows = _apply_project_filter(mod_rows, TestCase.primary_project_id, pids)
    mod_rows = mod_rows.group_by(TestCase.module).order_by(func.count(TestCase.id).desc()).limit(10).all()
    by_module = [{"name": r[0] or "未分类", "value": r[1]} for r in mod_rows]

    return {
        "code": 200,
        "data": {
            "by_level": by_level,
            "by_status": by_status,
            "by_automation": by_automation,
            "by_project": by_project,
            "by_module": by_module
        }
    }


@router.get("/execution-stats")
def get_execution_stats(
    team_id: Optional[int] = None,
    project_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行统计 - 按结果、执行人、计划分布"""
    pids = _get_accessible_project_ids(db, current_user, team_id)
    if project_id:
        pids = [project_id] if (pids is None or project_id in pids) else []

    base_q = db.query(TestExecution)
    if pids is not None:
        base_q = base_q.join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        base_q = _apply_project_filter(base_q, TestPlan.project_id, pids)

    if start_date:
        try:
            base_q = base_q.filter(TestExecution.executed_at >= datetime.strptime(start_date, '%Y-%m-%d'))
        except ValueError:
            pass
    if end_date:
        try:
            base_q = base_q.filter(TestExecution.executed_at <= datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
        except ValueError:
            pass

    # 按结果分布（排除 ONGOING 中间状态）
    result_q = db.query(TestExecution.result, func.count(TestExecution.id))
    result_q = result_q.filter(TestExecution.result != 'ONGOING')
    if pids is not None:
        result_q = result_q.join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        result_q = _apply_project_filter(result_q, TestPlan.project_id, pids)
    if start_date:
        try:
            result_q = result_q.filter(TestExecution.executed_at >= datetime.strptime(start_date, '%Y-%m-%d'))
        except ValueError:
            pass
    if end_date:
        try:
            result_q = result_q.filter(TestExecution.executed_at <= datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
        except ValueError:
            pass
    result_rows = result_q.group_by(TestExecution.result).all()
    by_result = [{"name": r[0] or "未执行", "value": r[1]} for r in result_rows]

    # 按执行人分布 - Top 10（基于首次执行去重，排除 ONGOING）
    # 第一步：每条用例在每个计划内的首次执行时间
    exec_by_executor_time_subq = db.query(
        TestExecution.test_plan_id,
        TestExecution.test_case_id,
        func.min(TestExecution.executed_at).label('first_executed_at')
    ).filter(TestExecution.result != 'ONGOING').group_by(
        TestExecution.test_plan_id,
        TestExecution.test_case_id
    ).subquery()

    # 第二步：关联找到首次执行的记录，确定是谁执行的
    exec_by_executor_subq = db.query(
        TestExecution.test_plan_id,
        TestExecution.executor_id,
        TestExecution.test_case_id,
        TestExecution.executed_at.label('first_executed_at')
    ).join(
        exec_by_executor_time_subq,
        and_(
            TestExecution.test_plan_id == exec_by_executor_time_subq.c.test_plan_id,
            TestExecution.test_case_id == exec_by_executor_time_subq.c.test_case_id,
            TestExecution.executed_at == exec_by_executor_time_subq.c.first_executed_at
        )
    ).filter(TestExecution.result != 'ONGOING').subquery()

    executor_q = db.query(User.full_name, User.username, func.count(exec_by_executor_subq.c.test_case_id))
    executor_q = executor_q.join(User, exec_by_executor_subq.c.executor_id == User.id)
    if pids is not None:
        executor_q = executor_q.join(TestPlan, exec_by_executor_subq.c.test_plan_id == TestPlan.id)
        executor_q = _apply_project_filter(executor_q, TestPlan.project_id, pids)
    if start_date:
        try:
            executor_q = executor_q.filter(exec_by_executor_subq.c.first_executed_at >= datetime.strptime(start_date, '%Y-%m-%d'))
        except ValueError:
            pass
    if end_date:
        try:
            executor_q = executor_q.filter(exec_by_executor_subq.c.first_executed_at < datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
        except ValueError:
            pass
    executor_rows = executor_q.group_by(User.id, User.full_name, User.username).order_by(func.count(exec_by_executor_subq.c.test_case_id).desc()).limit(10).all()
    by_executor = [{"name": r[1], "value": r[2]} for r in executor_rows]

    # 按测试计划分布 - 基于首次执行去重（排除 ONGOING）
    exec_by_plan_subq = db.query(
        TestExecution.test_plan_id,
        TestExecution.test_case_id,
        func.min(TestExecution.executed_at).label('first_executed_at')
    ).filter(TestExecution.result != 'ONGOING').group_by(
        TestExecution.test_plan_id,
        TestExecution.test_case_id
    ).subquery()

    plan_q = db.query(TestPlan.name, func.count(exec_by_plan_subq.c.test_case_id))
    plan_q = plan_q.join(TestPlan, exec_by_plan_subq.c.test_plan_id == TestPlan.id)
    if pids is not None:
        plan_q = _apply_project_filter(plan_q, TestPlan.project_id, pids)
    if start_date:
        try:
            plan_q = plan_q.filter(exec_by_plan_subq.c.first_executed_at >= datetime.strptime(start_date, '%Y-%m-%d'))
        except ValueError:
            pass
    if end_date:
        try:
            plan_q = plan_q.filter(exec_by_plan_subq.c.first_executed_at < datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
        except ValueError:
            pass
    plan_rows = plan_q.group_by(TestPlan.id, TestPlan.name).order_by(func.count(exec_by_plan_subq.c.test_case_id).desc()).limit(10).all()
    by_plan = [{"name": r[0], "value": r[1]} for r in plan_rows]

    return {
        "code": 200,
        "data": {
            "by_result": by_result,
            "by_executor": by_executor,
            "by_plan": by_plan
        }
    }


@router.get("/trend")
def get_trend_data(
    team_id: Optional[int] = None,
    project_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = "day",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """趋势分析 - 用例新增趋势、执行趋势（按天/周/月）"""
    pids = _get_accessible_project_ids(db, current_user, team_id)
    if project_id:
        pids = [project_id] if (pids is None or project_id in pids) else []

    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    except ValueError:
        start_dt = datetime.now() - timedelta(days=30)
        end_dt = datetime.now() + timedelta(days=1)

    # 根据粒度选择日期截断
    if granularity == "month":
        date_trunc = func.date_trunc('month', TestCase.created_at)
        exec_date_trunc = func.date_trunc('month', TestExecution.executed_at)
    elif granularity == "week":
        date_trunc = func.date_trunc('week', TestCase.created_at)
        exec_date_trunc = func.date_trunc('week', TestExecution.executed_at)
    else:
        date_trunc = func.date_trunc('day', TestCase.created_at)
        exec_date_trunc = func.date_trunc('day', TestExecution.executed_at)

    # 用例新增趋势
    tc_trend_q = db.query(date_trunc.label('date'), func.count(TestCase.id).label('count'))
    tc_trend_q = _apply_project_filter(tc_trend_q, TestCase.primary_project_id, pids)
    tc_trend_q = tc_trend_q.filter(TestCase.created_at >= start_dt, TestCase.created_at < end_dt)
    tc_trend_q = tc_trend_q.group_by('date').order_by('date')
    tc_trend = [{"date": r.date.strftime('%Y-%m-%d'), "count": r.count} for r in tc_trend_q.all()]

    # 执行趋势 - 去重统计（排除 ONGOING 中间状态）
    exec_trend_q = db.query(exec_date_trunc.label('date'),
        func.count(distinct(func.concat(TestExecution.test_plan_id, '-', TestExecution.test_case_id))).label('count'))
    exec_trend_q = exec_trend_q.filter(TestExecution.result != 'ONGOING')
    if pids is not None:
        exec_trend_q = exec_trend_q.join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        exec_trend_q = _apply_project_filter(exec_trend_q, TestPlan.project_id, pids)
    exec_trend_q = exec_trend_q.filter(TestExecution.executed_at >= start_dt, TestExecution.executed_at < end_dt)
    exec_trend_q = exec_trend_q.group_by('date').order_by('date')
    exec_trend = [{"date": r.date.strftime('%Y-%m-%d'), "count": r.count} for r in exec_trend_q.all()]

    # 执行结果趋势（通过/失败）- 去重统计
    pass_trend_q = db.query(
        exec_date_trunc.label('date'),
        func.count(distinct(case((TestExecution.result == 'PASS', func.concat(TestExecution.test_plan_id, '-', TestExecution.test_case_id))))).label('pass_count'),
        func.count(distinct(case((TestExecution.result == 'Fail', func.concat(TestExecution.test_plan_id, '-', TestExecution.test_case_id))))).label('fail_count')
    )
    if pids is not None:
        pass_trend_q = pass_trend_q.join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        pass_trend_q = _apply_project_filter(pass_trend_q, TestPlan.project_id, pids)
    pass_trend_q = pass_trend_q.filter(TestExecution.executed_at >= start_dt, TestExecution.executed_at < end_dt)
    pass_trend_q = pass_trend_q.group_by('date').order_by('date')
    pass_fail_trend = [{"date": r.date.strftime('%Y-%m-%d'), "pass": r.pass_count, "fail": r.fail_count} for r in pass_trend_q.all()]

    return {
        "code": 200,
        "data": {
            "case_trend": tc_trend,
            "execution_trend": exec_trend,
            "pass_fail_trend": pass_fail_trend
        }
    }


@router.get("/plan-stats")
def get_plan_stats(
    team_id: Optional[int] = None,
    project_id: Optional[int] = None,
    plan_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试计划统计 - 按状态、项目分布"""
    if plan_id:
        base_query = db.query(TestPlan).filter(TestPlan.id == plan_id)
    elif team_id:
        base_query = db.query(TestPlan).filter(TestPlan.team_id == team_id)
    else:
        pids = _get_accessible_project_ids(db, current_user, None)
        if project_id:
            pids = [project_id] if (pids is None or project_id in pids) else []
        base_query = db.query(TestPlan)
        if pids is not None:
            if pids:
                base_query = base_query.filter(TestPlan.project_id.in_(pids))
            else:
                base_query = base_query.filter(TestPlan.id == -1)
        else:
            base_query = _apply_project_filter(base_query, TestPlan.project_id, pids)

    # 按状态分布
    status_q = base_query.with_entities(TestPlan.status, func.count(TestPlan.id))
    status_rows = status_q.group_by(TestPlan.status).all()
    by_status = [{"name": r[0] or "未知", "value": r[1]} for r in status_rows]

    # 按项目分布 - Top 10
    proj_q = base_query.join(Project, TestPlan.project_id == Project.id)
    proj_q = proj_q.with_entities(Project.name, func.count(TestPlan.id))
    proj_rows = proj_q.group_by(Project.name).order_by(func.count(TestPlan.id).desc()).limit(10).all()
    by_project = [{"name": r[0], "value": r[1]} for r in proj_rows]

    # 各计划的用例数和执行进度
    if plan_id:
        plan_progress_q = base_query
    elif team_id:
        plan_progress_q = db.query(TestPlan).filter(
            TestPlan.team_id == team_id,
            TestPlan.status != 'COMPLETED'
        )
    else:
        pids = _get_accessible_project_ids(db, current_user, None)
        plan_progress_q = db.query(TestPlan)
        if pids is not None:
            if pids:
                plan_progress_q = plan_progress_q.filter(TestPlan.project_id.in_(pids))
            else:
                plan_progress_q = plan_progress_q.filter(TestPlan.id == -1)
        else:
            plan_progress_q = _apply_project_filter(plan_progress_q, TestPlan.project_id, pids)
        plan_progress_q = plan_progress_q.filter(TestPlan.status != 'COMPLETED')
    plan_progress_q = plan_progress_q.outerjoin(TestPlanTestCase, TestPlan.id == TestPlanTestCase.test_plan_id)
    plan_progress_q = plan_progress_q.with_entities(
        TestPlan.id,
        TestPlan.name,
        TestPlan.status,
        func.count(distinct(TestPlanTestCase.test_case_id)).label('case_count'),
    )
    plan_progress_q = plan_progress_q.group_by(TestPlan.id, TestPlan.name, TestPlan.status)
    plan_progress_q = plan_progress_q.order_by(TestPlan.id.desc())
    plan_rows = plan_progress_q.all()

    # 对齐测试计划列表页口径：
    # 1) 只统计当前仍关联在计划中的用例
    # 2) 每个用例仅取最新一条执行记录
    plan_ids = [r.id for r in plan_rows]
    linked_case_ids_by_plan = {pid: set() for pid in plan_ids}
    if plan_ids:
        linked_rows = db.query(
            TestPlanTestCase.test_plan_id,
            TestPlanTestCase.test_case_id
        ).filter(TestPlanTestCase.test_plan_id.in_(plan_ids)).all()
        for lr in linked_rows:
            linked_case_ids_by_plan.setdefault(lr.test_plan_id, set()).add(lr.test_case_id)

    latest_exec_by_plan_case = {pid: {} for pid in plan_ids}
    if plan_ids:
        exec_rows = db.query(
            TestExecution.test_plan_id,
            TestExecution.test_case_id,
            TestExecution.result,
            TestExecution.executed_at
        ).filter(TestExecution.test_plan_id.in_(plan_ids)).all()
        for er in exec_rows:
            linked_ids = linked_case_ids_by_plan.get(er.test_plan_id, set())
            if er.test_case_id not in linked_ids:
                continue
            case_map = latest_exec_by_plan_case.setdefault(er.test_plan_id, {})
            existing = case_map.get(er.test_case_id)
            if not existing:
                case_map[er.test_case_id] = er
                continue
            current_at = er.executed_at
            existing_at = existing.executed_at
            if current_at and existing_at and current_at > existing_at:
                case_map[er.test_case_id] = er
            elif current_at and not existing_at:
                case_map[er.test_case_id] = er

    plan_progress = []
    for row in plan_rows:
        latest_executions = latest_exec_by_plan_case.get(row.id, {}).values()
        exec_count = sum(
            1 for e in latest_executions
            if e.result != 'ONGOING' and e.result != 'PENDING'
        )
        plan_progress.append({
            "id": row.id,
            "name": row.name,
            "status": row.status,
            "case_count": row.case_count,
            "executed_count": exec_count,
            "progress": round(exec_count / row.case_count * 100, 1) if row.case_count > 0 else 0
        })

    return {
        "code": 200,
        "data": {
            "by_status": by_status,
            "by_project": by_project,
            "plan_progress": plan_progress
        }
    }


@router.get("/filters")
def get_filter_options(
    team_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取筛选选项 - 项目列表、项目组列表"""
    pids = _get_accessible_project_ids(db, current_user, team_id)

    # 项目列表
    proj_q = db.query(Project.id, Project.name)
    if pids is not None:
        proj_q = proj_q.filter(Project.id.in_(pids)) if pids else proj_q.filter(False)
    projects = [{"id": r.id, "name": r.name} for r in proj_q.order_by(Project.name).all()]

    # 项目组列表
    if _is_super_admin(current_user):
        teams = [{"id": t.id, "name": t.name} for t in db.query(Team.id, Team.name).filter(Team.status == 1).order_by(Team.name).all()]
    else:
        user_team_ids = [ut.team_id for ut in db.query(UserTeam.team_id).filter(UserTeam.user_id == current_user.id).all()]
        teams = [{"id": t.id, "name": t.name} for t in db.query(Team.id, Team.name).filter(Team.id.in_(user_team_ids), Team.status == 1).order_by(Team.name).all()] if user_team_ids else []

    return {
        "code": 200,
        "data": {
            "projects": projects,
            "teams": teams
        }
    }


@router.get("/testplans")
def get_testplans_for_analytics(
    team_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """数据统计页面专用的测试计划列表接口 - 根据用户角色返回不同范围的计划"""
    from models import TestPlanExecutor

    if not team_id:
        return {"code": 200, "data": {"records": [], "total": 0, "page": page, "size": size}}

    # 检查用户是否是该项目组负责人
    is_team_leader = db.query(TeamLeader).filter(
        TeamLeader.team_id == team_id,
        TeamLeader.user_id == current_user.id
    ).first() is not None

    is_admin = _is_super_admin(current_user)
    managed_dept_ids = _get_managed_dept_ids(db, current_user)
    is_org_manager = bool(managed_dept_ids)

    query = db.query(TestPlan).filter(TestPlan.team_id == team_id)

    # 项目组负责人或超管或组织负责人，可以看到该项目组下所有计划
    if not (is_team_leader or is_admin or is_org_manager):
        executor_plan_ids = db.query(TestPlanExecutor.test_plan_id).filter(
            TestPlanExecutor.executor_id == current_user.id
        ).distinct()
        from sqlalchemy import or_
        query = query.filter(
            or_(
                TestPlan.created_by == current_user.id,
                TestPlan.id.in_(executor_plan_ids)
            )
        )

    if search:
        query = query.filter(TestPlan.name.ilike(f'%{search}%'))

    total = query.count()
    plans = query.order_by(TestPlan.updated_at.desc(), TestPlan.id.desc()).offset((page - 1) * size).limit(size).all()

    return {
        "code": 200,
        "data": {
            "records": [{"id": p.id, "name": p.name, "status": p.status} for p in plans],
            "total": total,
            "page": page,
            "size": size
        }
    }


@router.get("/defect-density")
def get_defect_density(
    team_id: Optional[int] = None,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """缺陷密度 - 每个用例库的失败用例数/总用例数"""
    pids = _get_accessible_project_ids(db, current_user, team_id)
    if project_id:
        pids = [project_id] if (pids is None or project_id in pids) else []

    from models import TestCaseZmindLink

    exec_density_subq = db.query(
        TestExecution.test_plan_id,
        TestExecution.test_case_id,
        TestExecution.result,
        func.min(TestExecution.executed_at).label('first_executed_at')
    ).filter(TestExecution.result != 'ONGOING').group_by(
        TestExecution.test_plan_id,
        TestExecution.test_case_id,
        TestExecution.result
    ).subquery()

    # 按项目统计失败执行数 vs 总执行数
    q = db.query(
        Project.name,
        func.count(exec_density_subq.c.test_case_id).label('total_executed'),
        func.count(distinct(case((exec_density_subq.c.result == 'Fail', exec_density_subq.c.test_case_id)))).label('fail_cases')
    ).join(TestPlan, exec_density_subq.c.test_plan_id == TestPlan.id
    ).join(Project, TestPlan.project_id == Project.id)
    q = _apply_project_filter(q, TestPlan.project_id, pids)
    rows = q.group_by(Project.id, Project.name).order_by(func.count(distinct(case((exec_density_subq.c.result == 'Fail', exec_density_subq.c.test_case_id)))).desc()).limit(15).all()

    by_project = [{
        "name": r.name,
        "total": r.total_executed,
        "fail": r.fail_cases,
        "density": round(r.fail_cases / r.total_executed * 100, 1) if r.total_executed > 0 else 0
    } for r in rows]

    # 按模块统计
    mod_case_subq = db.query(
        TestExecution.test_case_id,
        func.min(TestExecution.executed_at).label('first_executed_at')
    ).filter(TestExecution.result != 'ONGOING').group_by(
        TestExecution.test_case_id
    ).subquery()

    mod_q = db.query(
        TestCase.module,
        func.count(distinct(mod_case_subq.c.test_case_id)).label('total_executed'),
        func.count(distinct(case((exec_density_subq.c.result == 'Fail', exec_density_subq.c.test_case_id)))).label('fail_cases')
    ).join(TestCase, mod_case_subq.c.test_case_id == TestCase.id
    ).join(TestExecution, func.and_(
        TestExecution.test_case_id == mod_case_subq.c.test_case_id,
        TestExecution.executed_at == mod_case_subq.c.first_executed_at,
        TestExecution.result != 'ONGOING'
    ))
    mod_q = _apply_project_filter(mod_q, TestCase.primary_project_id, pids)
    mod_rows = mod_q.group_by(TestCase.module).order_by(func.count(distinct(case((exec_density_subq.c.result == 'Fail', exec_density_subq.c.test_case_id)))).desc()).limit(15).all()

    by_module = [{
        "name": r.module or "未分类",
        "total": r.total_executed,
        "fail": r.fail_cases,
        "density": round(r.fail_cases / r.total_executed * 100, 1) if r.total_executed > 0 else 0
    } for r in mod_rows]

    return {"code": 200, "data": {"by_project": by_project, "by_module": by_module}}


@router.get("/coverage")
def get_test_coverage(
    team_id: Optional[int] = None,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试覆盖率 - 用例被测试计划覆盖的比例"""
    pids = _get_accessible_project_ids(db, current_user, team_id)
    if project_id:
        pids = [project_id] if (pids is None or project_id in pids) else []

    # 按项目统计覆盖率
    rows = []
    proj_q = db.query(Project.id, Project.name)
    if pids is not None:
        proj_q = proj_q.filter(Project.id.in_(pids)) if pids else proj_q.filter(False)
    for proj in proj_q.all():
        total = db.query(func.count(TestCase.id)).filter(TestCase.primary_project_id == proj.id).scalar() or 0
        covered = db.query(func.count(distinct(TestPlanTestCase.test_case_id))).join(
            TestPlan, TestPlanTestCase.test_plan_id == TestPlan.id
        ).filter(TestPlan.project_id == proj.id).scalar() or 0

        coverage_exec_subq = db.query(
            TestExecution.test_plan_id,
            TestExecution.test_case_id,
            func.min(TestExecution.executed_at).label('first_executed_at')
        ).filter(TestExecution.result != 'ONGOING').group_by(
            TestExecution.test_plan_id,
            TestExecution.test_case_id
        ).subquery()

        executed = db.query(func.count(coverage_exec_subq.c.test_case_id)).join(
            TestPlan, coverage_exec_subq.c.test_plan_id == TestPlan.id
        ).filter(TestPlan.project_id == proj.id).scalar() or 0
        if total > 0:
            rows.append({
                "name": proj.name,
                "total": total,
                "covered": covered,
                "executed": executed,
                "coverage_rate": round(covered / total * 100, 1),
                "execution_rate": round(executed / total * 100, 1)
            })

    rows.sort(key=lambda x: x["coverage_rate"], reverse=True)

    return {"code": 200, "data": {"by_project": rows[:15]}}


@router.get("/velocity")
def get_execution_velocity(
    team_id: Optional[int] = None,
    project_id: Optional[int] = None,
    plan_id: Optional[int] = None,
    plan_ids: Optional[str] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行效率 - 每人每天执行量"""
    from datetime import date

    user_provided_dates = start_date and end_date

    if not user_provided_dates:
        if not granularity:
            granularity = 'day'

        today = date.today()

        if granularity == 'day':
            start_date = today.strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        elif granularity == 'week':
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            start_date = monday.strftime('%Y-%m-%d')
            end_date = sunday.strftime('%Y-%m-%d')
        elif granularity == 'month':
            first_day = today.replace(day=1)
            if today.month == 12:
                last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            start_date = first_day.strftime('%Y-%m-%d')
            end_date = last_day.strftime('%Y-%m-%d')
        else:
            start_date = today.strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')

    if not start_date:
        start_date = date.today().strftime('%Y-%m-%d')
    if not end_date:
        end_date = date.today().strftime('%Y-%m-%d')

    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    except ValueError:
        start_dt = datetime.now() - timedelta(days=30)
        end_dt = datetime.now() + timedelta(days=1)

    # 第一步：每条用例在每个计划内的首次执行时间（无论是谁执行）
    first_exec_time_subq = db.query(
        TestExecution.test_plan_id,
        TestExecution.test_case_id,
        func.min(TestExecution.executed_at).label('first_executed_at')
    ).filter(TestExecution.result != 'ONGOING').group_by(
        TestExecution.test_plan_id,
        TestExecution.test_case_id
    ).subquery()

    # 第二步：关联找到首次执行的记录，确定是谁执行的
    first_exec_subq = db.query(
        TestExecution.test_plan_id,
        TestExecution.executor_id,
        TestExecution.test_case_id,
        TestExecution.executed_at.label('first_executed_at')
    ).join(
        first_exec_time_subq,
        and_(
            TestExecution.test_plan_id == first_exec_time_subq.c.test_plan_id,
            TestExecution.test_case_id == first_exec_time_subq.c.test_case_id,
            TestExecution.executed_at == first_exec_time_subq.c.first_executed_at
        )
    ).filter(TestExecution.result != 'ONGOING').subquery()

    # 构建基础过滤条件 - 当指定plan_id时，不应用数据权限过滤，返回该计划下所有成员的执行数据
    # 当指定plan_ids时（用户只能看到部分计划），按plan_ids过滤
    if plan_id:
        exec_count_per_user = db.query(
            User.id,
            User.username,
            func.count(first_exec_subq.c.test_case_id).label('total')
        ).join(User, first_exec_subq.c.executor_id == User.id).filter(
            first_exec_subq.c.test_plan_id == plan_id,
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt
        )
        exec_count_per_user = exec_count_per_user.group_by(User.id, User.username).order_by(func.count(first_exec_subq.c.test_case_id).desc()).limit(30)
    elif plan_ids:
        try:
            pid_list = [int(p.strip()) for p in plan_ids.split(',') if p.strip()]
            if pid_list:
                exec_count_per_user = db.query(
                    User.id,
                    User.username,
                    func.count(first_exec_subq.c.test_case_id).label('total')
                ).join(User, first_exec_subq.c.executor_id == User.id).filter(
                    first_exec_subq.c.test_plan_id.in_(pid_list),
                    first_exec_subq.c.first_executed_at >= start_dt,
                    first_exec_subq.c.first_executed_at < end_dt
                )
                exec_count_per_user = exec_count_per_user.group_by(User.id, User.username).order_by(func.count(first_exec_subq.c.test_case_id).desc()).limit(30)
            else:
                exec_count_per_user = db.query(User.id, User.username, func.literal(0).label('total')).filter(User.id == -1)
        except:
            exec_count_per_user = db.query(User.id, User.username, func.literal(0).label('total')).filter(User.id == -1)
    elif team_id:
        exec_count_per_user = db.query(
            User.id,
            User.username,
            func.count(first_exec_subq.c.test_case_id).label('total')
        ).join(User, first_exec_subq.c.executor_id == User.id)
        exec_count_per_user = exec_count_per_user.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
        exec_count_per_user = exec_count_per_user.filter(TestPlan.team_id == team_id)
        exec_count_per_user = exec_count_per_user.filter(first_exec_subq.c.first_executed_at >= start_dt, first_exec_subq.c.first_executed_at < end_dt)
        exec_count_per_user = exec_count_per_user.group_by(User.id, User.username).order_by(func.count(first_exec_subq.c.test_case_id).desc()).limit(30)
    else:
        pids = _get_accessible_project_ids(db, current_user, None)
        if project_id:
            pids = [project_id] if (pids is None or project_id in pids) else []
        if pids:
            exec_count_per_user = db.query(
                User.id,
                User.username,
                func.count(first_exec_subq.c.test_case_id).label('total')
            ).join(User, first_exec_subq.c.executor_id == User.id)
            exec_count_per_user = exec_count_per_user.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            exec_count_per_user = exec_count_per_user.filter(TestPlan.project_id.in_(pids))
            exec_count_per_user = exec_count_per_user.filter(first_exec_subq.c.first_executed_at >= start_dt, first_exec_subq.c.first_executed_at < end_dt)
            exec_count_per_user = exec_count_per_user.group_by(User.id, User.username).order_by(func.count(first_exec_subq.c.test_case_id).desc()).limit(30)
        else:
            exec_count_per_user = db.query(
                User.id,
                User.username,
                func.count(first_exec_subq.c.test_case_id).label('total')
            ).join(User, first_exec_subq.c.executor_id == User.id)
            exec_count_per_user = exec_count_per_user.filter(first_exec_subq.c.first_executed_at >= start_dt, first_exec_subq.c.first_executed_at < end_dt)
            exec_count_per_user = exec_count_per_user.group_by(User.id, User.username).order_by(func.count(first_exec_subq.c.test_case_id).desc()).limit(30)

    top_users = [r.username for r in exec_count_per_user.all()]

    # 构建子查询：基于首次执行时间统计每日数据
    user_daily_subq = db.query(
        first_exec_subq.c.executor_id,
        func.date_trunc('day', first_exec_subq.c.first_executed_at).label('date'),
        func.count(first_exec_subq.c.test_case_id).label('count')
    ).filter(
        first_exec_subq.c.first_executed_at >= start_dt,
        first_exec_subq.c.first_executed_at < end_dt
    )
    if plan_id:
        user_daily_subq = user_daily_subq.filter(first_exec_subq.c.test_plan_id == plan_id)
    elif team_id:
        user_daily_subq = user_daily_subq.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
        user_daily_subq = user_daily_subq.filter(TestPlan.team_id == team_id)
    elif pids is not None:
        user_daily_subq = user_daily_subq.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
        user_daily_subq = _apply_project_filter(user_daily_subq, TestPlan.project_id, pids)
    user_daily_subq = user_daily_subq.group_by(first_exec_subq.c.executor_id, 'date').subquery()

    user_data = {}
    if top_users:
        daily_q = db.query(
            User.full_name, User.username,
            func.date_trunc('day', user_daily_subq.c.date).label('date'),
            func.sum(user_daily_subq.c.count).label('count')
        ).join(User, user_daily_subq.c.executor_id == User.id).filter(
            User.username.in_(top_users)
        ).group_by(User.id, User.full_name, User.username, 'date').order_by('date')
        rows = daily_q.all()

        for r in rows:
            name = r.username
            if name not in user_data:
                user_data[name] = []
            user_data[name].append({"date": r.date.strftime('%Y-%m-%d'), "count": r.count})

    # 团队日均执行量（基于首次执行去重）
    team_daily_subq = db.query(
        func.date_trunc('day', first_exec_subq.c.first_executed_at).label('date'),
        func.count(first_exec_subq.c.test_case_id).label('count')
    ).filter(
        first_exec_subq.c.first_executed_at >= start_dt,
        first_exec_subq.c.first_executed_at < end_dt
    )
    if plan_id:
        team_daily_subq = team_daily_subq.filter(first_exec_subq.c.test_plan_id == plan_id)
    elif team_id:
        team_daily_subq = team_daily_subq.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
        team_daily_subq = team_daily_subq.filter(TestPlan.team_id == team_id)
    elif pids is not None:
        team_daily_subq = team_daily_subq.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
        _apply_project_filter(team_daily_subq, TestPlan.project_id, pids)
    team_daily_subq = team_daily_subq.group_by('date').subquery()

    team_q = db.query(
        func.date_trunc('day', team_daily_subq.c.date).label('date'),
        func.sum(team_daily_subq.c.count).label('count')
    ).group_by('date').order_by('date')
    team_daily = [{"date": r.date.strftime('%Y-%m-%d'), "count": r.count} for r in team_q.all()]

    return {"code": 200, "data": {"by_user": user_data, "team_daily": team_daily}}


@router.get("/case-age")
def get_case_age(
    team_id: Optional[int] = None,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """用例老化分析 - 长时间未更新的用例分布"""
    pids = _get_accessible_project_ids(db, current_user, team_id)
    if project_id:
        pids = [project_id] if (pids is None or project_id in pids) else []

    now = datetime.now()
    ranges = [
        ("< 30天", now - timedelta(days=30), now),
        ("30-90天", now - timedelta(days=90), now - timedelta(days=30)),
        ("90-180天", now - timedelta(days=180), now - timedelta(days=90)),
        ("180-365天", now - timedelta(days=365), now - timedelta(days=180)),
        ("> 365天", None, now - timedelta(days=365))
    ]

    age_distribution = []
    for label, start, end in ranges:
        q = db.query(func.count(TestCase.id))
        q = _apply_project_filter(q, TestCase.primary_project_id, pids)
        if start:
            q = q.filter(TestCase.updated_at >= start)
        q = q.filter(TestCase.updated_at < end)
        count = q.scalar() or 0
        age_distribution.append({"name": label, "value": count})

    # 最久未更新的用例 Top 10
    stale_q = db.query(TestCase.case_number, TestCase.name, TestCase.module, TestCase.updated_at, Project.name.label('project_name'))
    stale_q = stale_q.join(Project, TestCase.primary_project_id == Project.id)
    stale_q = _apply_project_filter(stale_q, TestCase.primary_project_id, pids)
    stale_q = stale_q.order_by(TestCase.updated_at.asc()).limit(10)
    stale_cases = [{
        "case_number": r.case_number,
        "name": r.name,
        "module": r.module,
        "project": r.project_name,
        "last_updated": r.updated_at.strftime('%Y-%m-%d') if r.updated_at else "未知"
    } for r in stale_q.all()]

    return {"code": 200, "data": {"age_distribution": age_distribution, "stale_cases": stale_cases}}


@router.get("/review-stats")
def get_review_stats(
    team_id: Optional[int] = None,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """评审统计 - 评审计划通过率、评审人效率"""
    pids = _get_accessible_project_ids(db, current_user, team_id)
    if project_id:
        pids = [project_id] if (pids is None or project_id in pids) else []

    # 评审结果分布
    result_q = db.query(ReviewPlanTestCase.review_status, func.count(ReviewPlanTestCase.id))
    result_q = result_q.join(ReviewPlan, ReviewPlanTestCase.review_plan_id == ReviewPlan.id)
    result_q = _apply_project_filter(result_q, ReviewPlan.project_id, pids)
    result_rows = result_q.group_by(ReviewPlanTestCase.review_status).all()
    by_result = [{"name": r[0] or "待评审", "value": r[1]} for r in result_rows]

    # 评审计划状态分布
    plan_q = db.query(ReviewPlan.status, func.count(ReviewPlan.id))
    plan_q = _apply_project_filter(plan_q, ReviewPlan.project_id, pids)
    plan_rows = plan_q.group_by(ReviewPlan.status).all()
    by_plan_status = [{"name": r[0] or "未知", "value": r[1]} for r in plan_rows]

    # 评审人效率 Top 10
    reviewer_q = db.query(
        User.full_name, User.username,
        func.count(ReviewPlanTestCase.id).label('total'),
        func.count(case((ReviewPlanTestCase.review_status == 'APPROVED', 1))).label('approved'),
        func.count(case((ReviewPlanTestCase.review_status == 'REJECTED', 1))).label('rejected')
    ).join(User, ReviewPlanTestCase.reviewer_id == User.id
    ).join(ReviewPlan, ReviewPlanTestCase.review_plan_id == ReviewPlan.id)
    reviewer_q = _apply_project_filter(reviewer_q, ReviewPlan.project_id, pids)
    reviewer_rows = reviewer_q.group_by(User.id, User.full_name, User.username).order_by(func.count(ReviewPlanTestCase.id).desc()).limit(10).all()
    by_reviewer = [{
        "name": r.username,
        "total": r.total,
        "approved": r.approved,
        "rejected": r.rejected
    } for r in reviewer_rows]

    return {"code": 200, "data": {"by_result": by_result, "by_plan_status": by_plan_status, "by_reviewer": by_reviewer}}


@router.get("/plan-ontime")
def get_plan_ontime(
    team_id: Optional[int] = None,
    project_id: Optional[int] = None,
    plan_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """计划按时完成率 - 逾期 vs 按时"""
    now = datetime.now()

    # 构建过滤条件
    if plan_id:
        base_filter = TestPlan.id == plan_id
    elif team_id:
        base_filter = TestPlan.team_id == team_id
    else:
        pids = _get_accessible_project_ids(db, current_user, None)
        if project_id:
            pids = [project_id] if (pids is None or project_id in pids) else []
        if pids:
            base_filter = TestPlan.project_id.in_(pids)
        else:
            base_filter = TestPlan.id == -1

    # 已完成的计划
    completed_q = db.query(TestPlan).filter(
        TestPlan.status.in_(['COMPLETED', 'CLOSED']),
        base_filter
    )
    completed = completed_q.all()

    ontime = 0
    overdue_completed = 0
    for p in completed:
        if p.end_time and p.updated_at and p.updated_at > p.end_time:
            overdue_completed += 1
        else:
            ontime += 1

    # 进行中但已逾期
    active_q = db.query(func.count(TestPlan.id)).filter(
        TestPlan.status.in_(['PENDING', 'IN_PROGRESS']),
        TestPlan.end_time < now,
        TestPlan.end_time.isnot(None),
        base_filter
    )
    overdue_active = active_q.scalar() or 0

    # 进行中未逾期
    active_ok_q = db.query(func.count(TestPlan.id)).filter(
        TestPlan.status.in_(['PENDING', 'IN_PROGRESS']),
        or_(TestPlan.end_time >= now, TestPlan.end_time.is_(None)),
        base_filter
    )
    active_ok = active_ok_q.scalar() or 0

    return {
        "code": 200,
        "data": {
            "summary": [
                {"name": "按时完成", "value": ontime},
                {"name": "逾期完成", "value": overdue_completed},
                {"name": "进行中(逾期)", "value": overdue_active},
                {"name": "进行中(正常)", "value": active_ok}
            ]
        }
    }


@router.get("/heatmap")
def get_execution_heatmap(
    team_id: Optional[int] = None,
    project_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行热力图 - 按星期几和小时统计执行量"""
    pids = _get_accessible_project_ids(db, current_user, team_id)
    if project_id:
        pids = [project_id] if (pids is None or project_id in pids) else []

    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    except ValueError:
        start_dt = datetime.now() - timedelta(days=90)
        end_dt = datetime.now() + timedelta(days=1)

    # 按星期几(0=周一) + 小时统计
    q = db.query(
        extract('dow', TestExecution.executed_at).label('dow'),
        extract('hour', TestExecution.executed_at).label('hour'),
        func.count(TestExecution.id).label('count')
    )
    if pids is not None:
        q = q.join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        q = _apply_project_filter(q, TestPlan.project_id, pids)
    q = q.filter(TestExecution.executed_at >= start_dt, TestExecution.executed_at < end_dt)
    q = q.group_by('dow', 'hour')
    rows = q.all()

    # 转换为 [dow, hour, count] 格式
    heatmap_data = []
    for r in rows:
        dow = int(r.dow)  # PostgreSQL: 0=Sunday, 1=Monday...
        # 转换为 0=Monday
        dow_adjusted = (dow - 1) % 7 if dow > 0 else 6
        heatmap_data.append([dow_adjusted, int(r.hour), r.count])

    return {"code": 200, "data": {"heatmap": heatmap_data}}


# ==================== 个人用户分析 ====================

@router.get("/user-list")
def get_user_list(
    team_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取可选用户列表"""
    def apply_search(query):
        if search:
            search_filter = or_(User.username.ilike(f'%{search}%'), User.full_name.ilike(f'%{search}%'))
            return query.filter(search_filter)
        return query

    if _is_super_admin(current_user):
        if team_id:
            user_ids = [ut.user_id for ut in db.query(UserTeam.user_id).filter(UserTeam.team_id == team_id).all()]
            users_query = db.query(User.id, User.username, User.full_name).filter(User.id.in_(user_ids), User.status == 1)
            users = apply_search(users_query).order_by(User.username).all() if user_ids else []
        else:
            users = apply_search(db.query(User.id, User.username, User.full_name).filter(User.status == 1)).order_by(User.username).all()
    elif team_id:
        # 选择了项目组：检查是否是该项目组的负责人或组织负责人
        is_team_leader = db.query(TeamLeader).filter(
            TeamLeader.team_id == team_id,
            TeamLeader.user_id == current_user.id
        ).first() is not None
        
        is_org_manager = False
        team = db.query(Team).filter(Team.id == team_id).first()
        if team and team.department_id:
            is_org_manager = db.query(DepartmentManager).filter(
                DepartmentManager.department_id == team.department_id,
                DepartmentManager.user_id == current_user.id
            ).first() is not None
        
        # 项目组负责人或组织负责人：返回该项目组下的用户
        if is_team_leader or is_org_manager:
            user_ids = [ut.user_id for ut in db.query(UserTeam.user_id).filter(UserTeam.team_id == team_id).all()]
            users_query = db.query(User.id, User.username, User.full_name).filter(User.id.in_(user_ids), User.status == 1)
            users = apply_search(users_query).order_by(User.username).all() if user_ids else []
        else:
            users = []
    else:
        users = []
        # 未选择项目组：不需要用户下拉框
        users = []

    return {
        "code": 200,
        "data": [{"id": u.id, "username": u.username, "full_name": u.full_name or u.username} for u in users]
    }


@router.get("/personal")
def get_personal_analytics(
    user_id: int,
    team_id: Optional[int] = None,
    project_id: Optional[int] = None,
    plan_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """个人综合分析"""
    from models import TestCaseHistory, Comment, ReviewPlanTestCase, ReviewPlan
    from datetime import date

    user_provided_dates = start_date and end_date

    if not user_provided_dates:
        if not granularity:
            granularity = 'day'

        today = date.today()

        if granularity == 'day':
            start_date = today.strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        elif granularity == 'week':
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            start_date = monday.strftime('%Y-%m-%d')
            end_date = sunday.strftime('%Y-%m-%d')
        elif granularity == 'month':
            first_day = today.replace(day=1)
            if today.month == 12:
                last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            start_date = first_day.strftime('%Y-%m-%d')
            end_date = last_day.strftime('%Y-%m-%d')
        else:
            start_date = today.strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')

    if not start_date:
        start_date = date.today().strftime('%Y-%m-%d')
    if not end_date:
        end_date = date.today().strftime('%Y-%m-%d')

    if plan_id:
        plan_filter = TestPlan.id == plan_id
        pids = None
    elif team_id:
        plan_filter = TestPlan.team_id == team_id
        pids = None
    else:
        pids = _get_accessible_project_ids(db, current_user, None)
        if project_id:
            pids = [project_id] if (pids is None or project_id in pids) else []
        if pids:
            plan_filter = TestPlan.project_id.in_(pids)
        else:
            plan_filter = TestPlan.id == -1

    # 日期范围
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    except ValueError:
        start_dt = datetime.now() - timedelta(days=90)
        end_dt = datetime.now() + timedelta(days=1)

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return {"code": 404, "message": "用户不存在"}

    # ---- 1. 个人概览 ----
    # 创建的用例数
    cases_created_q = db.query(func.count(TestCase.id)).filter(TestCase.created_by == user_id)
    if plan_id:
        cases_created_q = cases_created_q.join(TestPlanTestCase, TestCase.id == TestPlanTestCase.test_case_id)
        cases_created_q = cases_created_q.filter(TestPlanTestCase.test_plan_id == plan_id)
    else:
        cases_created_q = _apply_project_filter(cases_created_q, TestCase.primary_project_id, pids)
    cases_created = cases_created_q.scalar() or 0

    # 执行总数 - 基于首次执行去重（每条用例在该计划内只算第一次执行）
    # 第一步：每条用例在每个计划内的首次执行时间
    first_exec_time_subq = db.query(
        TestExecution.test_plan_id,
        TestExecution.test_case_id,
        func.min(TestExecution.executed_at).label('first_executed_at')
    ).filter(TestExecution.result != 'ONGOING').group_by(
        TestExecution.test_plan_id,
        TestExecution.test_case_id
    ).subquery()

    # 第二步：关联找到首次执行的记录，确定是谁执行的
    first_exec_subq = db.query(
        TestExecution.test_plan_id,
        TestExecution.executor_id,
        TestExecution.test_case_id,
        TestExecution.executed_at.label('first_executed_at')
    ).join(
        first_exec_time_subq,
        and_(
            TestExecution.test_plan_id == first_exec_time_subq.c.test_plan_id,
            TestExecution.test_case_id == first_exec_time_subq.c.test_case_id,
            TestExecution.executed_at == first_exec_time_subq.c.first_executed_at
        )
    ).filter(TestExecution.result != 'ONGOING').subquery()

    if plan_id:
        exec_q = db.query(func.count(first_exec_subq.c.test_case_id)).filter(
            first_exec_subq.c.executor_id == user_id,
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt,
            first_exec_subq.c.test_plan_id == plan_id
        )
    else:
        exec_q = db.query(func.count(first_exec_subq.c.test_case_id)).filter(
            first_exec_subq.c.executor_id == user_id,
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt
        )
        if team_id:
            exec_q = exec_q.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            exec_q = exec_q.filter(TestPlan.team_id == team_id)
        elif pids is not None:
            exec_q = exec_q.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            exec_q = _apply_project_filter(exec_q, TestPlan.project_id, pids)
    total_executions = exec_q.scalar() or 0

    # 通过数 - 基于首次执行去重（首次PASS即算通过）
    if plan_id:
        pass_q = db.query(func.count(first_exec_subq.c.test_case_id)).filter(
            first_exec_subq.c.executor_id == user_id,
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt,
            first_exec_subq.c.test_plan_id == plan_id
        )
    else:
        pass_q = db.query(func.count(first_exec_subq.c.test_case_id)).filter(
            first_exec_subq.c.executor_id == user_id,
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt
        )
        if team_id:
            pass_q = pass_q.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            pass_q = pass_q.filter(TestPlan.team_id == team_id)
        elif pids is not None:
            pass_q = pass_q.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            pass_q = _apply_project_filter(pass_q, TestPlan.project_id, pids)
    pass_count = pass_q.scalar() or 0
    pass_rate = round(pass_count / total_executions * 100, 1) if total_executions > 0 else 0

    # 发现的缺陷数 - 基于首次执行去重
    if plan_id:
        fail_q = db.query(func.count(first_exec_subq.c.test_case_id)).filter(
            first_exec_subq.c.executor_id == user_id,
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt,
            first_exec_subq.c.test_plan_id == plan_id
        )
    else:
        fail_q = db.query(func.count(first_exec_subq.c.test_case_id)).filter(
            first_exec_subq.c.executor_id == user_id,
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt
        )
        if team_id:
            fail_q = fail_q.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            fail_q = fail_q.filter(TestPlan.team_id == team_id)
        elif pids is not None:
            fail_q = fail_q.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            fail_q = _apply_project_filter(fail_q, TestPlan.project_id, pids)
    bugs_found = fail_q.scalar() or 0

    # 评审数
    review_q = db.query(func.count(ReviewPlanTestCase.id)).filter(
        ReviewPlanTestCase.reviewer_id == user_id,
        ReviewPlanTestCase.review_status != 'PENDING'
    )
    reviews_done = review_q.scalar() or 0

    # 评论数
    comment_q = db.query(func.count(Comment.id)).filter(
        Comment.author_id == user_id,
        Comment.is_deleted == False
    )
    comments_count = comment_q.scalar() or 0

    # 参与的计划数
    plans_involved_q = db.query(func.count(distinct(TestPlanExecutor.test_plan_id))).filter(
        TestPlanExecutor.executor_id == user_id
    )
    if plan_id:
        plans_involved_q = plans_involved_q.filter(TestPlanExecutor.test_plan_id == plan_id)
    plans_involved = plans_involved_q.scalar() or 0

    overview = {
        "user_name": target_user.username,
        "cases_created": cases_created,
        "total_executions": total_executions,
        "pass_rate": pass_rate,
        "bugs_found": bugs_found,
        "reviews_done": reviews_done,
        "comments_count": comments_count,
        "plans_involved": plans_involved
    }

    # ---- 2. 执行结果分布 - 基于首次执行去重（排除 ONGOING 中间状态）----
    # 每条用例在每个计划内的首次执行（无论谁执行）
    result_first_exec_time_subq = db.query(
        TestExecution.test_plan_id,
        TestExecution.test_case_id,
        TestExecution.result,
        func.min(TestExecution.executed_at).label('first_executed_at')
    ).filter(TestExecution.result != 'ONGOING').group_by(
        TestExecution.test_plan_id,
        TestExecution.test_case_id,
        TestExecution.result
    ).subquery()

    result_first_exec_subq = db.query(
        TestExecution.test_plan_id,
        TestExecution.executor_id,
        TestExecution.test_case_id,
        TestExecution.result,
        TestExecution.executed_at.label('first_executed_at')
    ).join(
        result_first_exec_time_subq,
        and_(
            TestExecution.test_plan_id == result_first_exec_time_subq.c.test_plan_id,
            TestExecution.test_case_id == result_first_exec_time_subq.c.test_case_id,
            TestExecution.result == result_first_exec_time_subq.c.result,
            TestExecution.executed_at == result_first_exec_time_subq.c.first_executed_at
        )
    ).filter(TestExecution.result != 'ONGOING').subquery()

    if plan_id:
        result_q = db.query(result_first_exec_subq.c.result, func.count(result_first_exec_subq.c.test_case_id)).filter(
            result_first_exec_subq.c.executor_id == user_id,
            result_first_exec_subq.c.first_executed_at >= start_dt,
            result_first_exec_subq.c.first_executed_at < end_dt,
            result_first_exec_subq.c.test_plan_id == plan_id
        )
    else:
        result_q = db.query(result_first_exec_subq.c.result, func.count(result_first_exec_subq.c.test_case_id)).filter(
            result_first_exec_subq.c.executor_id == user_id,
            result_first_exec_subq.c.first_executed_at >= start_dt,
            result_first_exec_subq.c.first_executed_at < end_dt
        )
        if team_id:
            result_q = result_q.join(TestPlan, result_first_exec_subq.c.test_plan_id == TestPlan.id)
            result_q = result_q.filter(TestPlan.team_id == team_id)
        elif pids is not None:
            result_q = result_q.join(TestPlan, result_first_exec_subq.c.test_plan_id == TestPlan.id)
            result_q = _apply_project_filter(result_q, TestPlan.project_id, pids)
    result_rows = result_q.group_by(result_first_exec_subq.c.result).all()
    exec_by_result = [{"name": r[0] or "未执行", "value": r[1]} for r in result_rows]

    # ---- 3. 每日执行趋势 - 基于首次执行去重（排除 ONGOING 中间状态）----
    if plan_id:
        daily_q = db.query(
            func.date_trunc('day', first_exec_subq.c.first_executed_at).label('date'),
            func.count(first_exec_subq.c.test_case_id).label('count')
        ).filter(
            first_exec_subq.c.executor_id == user_id,
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt,
            first_exec_subq.c.test_plan_id == plan_id
        ).group_by('date').order_by('date')
    else:
        daily_q = db.query(
            func.date_trunc('day', first_exec_subq.c.first_executed_at).label('date'),
            func.count(first_exec_subq.c.test_case_id).label('count')
        ).filter(
            first_exec_subq.c.executor_id == user_id,
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt
        )
        if team_id:
            daily_q = daily_q.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            daily_q = daily_q.filter(TestPlan.team_id == team_id)
        elif pids is not None:
            daily_q = daily_q.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            daily_q = _apply_project_filter(daily_q, TestPlan.project_id, pids)
        daily_q = daily_q.group_by('date').order_by('date')
    exec_trend = [{"date": r.date.strftime('%Y-%m-%d'), "count": r.count} for r in daily_q.all()]

    # 团队平均（用于对比）- 基于首次执行去重
    from sqlalchemy import case
    if plan_id:
        team_avg_q = db.query(
            func.date_trunc('day', first_exec_subq.c.first_executed_at).label('date'),
            case(
                (func.count(distinct(first_exec_subq.c.executor_id)) > 0,
                 func.count(first_exec_subq.c.test_case_id) * 1.0 / func.count(distinct(first_exec_subq.c.executor_id))),
                else_=0
            ).label('avg')
        ).filter(
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt,
            first_exec_subq.c.test_plan_id == plan_id
        ).group_by('date').order_by('date')
    else:
        team_avg_q = db.query(
            func.date_trunc('day', first_exec_subq.c.first_executed_at).label('date'),
            case(
                (func.count(distinct(first_exec_subq.c.executor_id)) > 0,
                 func.count(first_exec_subq.c.test_case_id) * 1.0 / func.count(distinct(first_exec_subq.c.executor_id))),
                else_=0
            ).label('avg')
        ).filter(
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt
        )
        if team_id:
            team_avg_q = team_avg_q.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            team_avg_q = team_avg_q.filter(TestPlan.team_id == team_id)
        elif pids is not None:
            team_avg_q = team_avg_q.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            team_avg_q = _apply_project_filter(team_avg_q, TestPlan.project_id, pids)
        team_avg_q = team_avg_q.group_by('date').order_by('date')
    team_avg_trend = [{"date": r.date.strftime('%Y-%m-%d'), "avg": round(float(r.avg), 1)} for r in team_avg_q.all()]

    # ---- 4. 参与的测试计划 ----
    plan_q = db.query(
        TestPlan.id, TestPlan.name, TestPlan.status,
        func.count(distinct(TestPlanTestCase.test_case_id)).label('total_cases')
    ).join(TestPlanExecutor, TestPlan.id == TestPlanExecutor.test_plan_id
    ).outerjoin(TestPlanTestCase, TestPlan.id == TestPlanTestCase.test_plan_id
    ).filter(TestPlanExecutor.executor_id == user_id)
    if plan_id:
        plan_q = plan_q.filter(TestPlan.id == plan_id)
    elif team_id:
        plan_q = plan_q.filter(TestPlan.team_id == team_id)
    else:
        plan_q = _apply_project_filter(plan_q, TestPlan.project_id, pids)
    plan_q = plan_q.group_by(TestPlan.id, TestPlan.name, TestPlan.status).order_by(TestPlan.id.desc()).limit(20)
    plan_rows = plan_q.all()

    plans_detail = []
    for p in plan_rows:
        my_exec = db.query(func.count(distinct(TestExecution.test_case_id))).filter(
            TestExecution.test_plan_id == p.id,
            TestExecution.executor_id == user_id,
            TestExecution.result != 'ONGOING'
        ).scalar() or 0
        my_pass = db.query(func.count(distinct(TestExecution.test_case_id))).filter(
            TestExecution.test_plan_id == p.id,
            TestExecution.executor_id == user_id,
            TestExecution.result == 'PASS'
        ).scalar() or 0
        my_total = db.query(func.count(distinct(TestExecution.test_case_id))).filter(
            TestExecution.test_plan_id == p.id,
            TestExecution.executor_id == user_id,
            TestExecution.result != 'ONGOING'
        ).scalar() or 0
        plans_detail.append({
            "name": p.name,
            "status": p.status,
            "total_cases": p.total_cases,
            "my_executed": my_exec,
            "my_pass_rate": round(my_pass / my_total * 100, 1) if my_total > 0 else 0
        })

    # ---- 5. 创建的用例分布 ----
    level_q = db.query(TestCase.level, func.count(TestCase.id)).filter(TestCase.created_by == user_id)
    level_q = _apply_project_filter(level_q, TestCase.primary_project_id, pids)
    level_rows = level_q.group_by(TestCase.level).all()
    cases_by_level = [{"name": r[0] or "未设置", "value": r[1]} for r in level_rows]

    module_q = db.query(TestCase.module, func.count(TestCase.id)).filter(TestCase.created_by == user_id)
    module_q = _apply_project_filter(module_q, TestCase.primary_project_id, pids)
    module_rows = module_q.group_by(TestCase.module).order_by(func.count(TestCase.id).desc()).limit(10).all()
    cases_by_module = [{"name": r[0] or "未分类", "value": r[1]} for r in module_rows]

    # ---- 6. 评审活动 ----
    rev_result_q = db.query(ReviewPlanTestCase.review_status, func.count(ReviewPlanTestCase.id)).filter(
        ReviewPlanTestCase.reviewer_id == user_id,
        ReviewPlanTestCase.review_status != 'PENDING'
    ).group_by(ReviewPlanTestCase.review_status).all()
    review_by_result = [{"name": r[0], "value": r[1]} for r in rev_result_q]

    # ---- 7. 执行按小时分布（工作习惯）- 基于首次执行去重 ----
    if plan_id:
        hour_q = db.query(
            extract('hour', first_exec_subq.c.first_executed_at).label('hour'),
            func.count(first_exec_subq.c.test_case_id).label('count')
        ).filter(
            first_exec_subq.c.executor_id == user_id,
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt,
            first_exec_subq.c.test_plan_id == plan_id
        ).group_by('hour').order_by('hour')
    else:
        hour_q = db.query(
            extract('hour', first_exec_subq.c.first_executed_at).label('hour'),
            func.count(first_exec_subq.c.test_case_id).label('count')
        ).filter(
            first_exec_subq.c.executor_id == user_id,
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt
        )
        if team_id:
            hour_q = hour_q.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            hour_q = hour_q.filter(TestPlan.team_id == team_id)
        elif pids is not None:
            hour_q = hour_q.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            hour_q = _apply_project_filter(hour_q, TestPlan.project_id, pids)
        hour_q = hour_q.group_by('hour').order_by('hour')
    hour_rows = hour_q.all()
    exec_by_hour = [{"hour": int(r.hour), "count": r.count} for r in hour_rows]

    # ---- 8. 每周执行分布（工作节奏）- 基于首次执行去重 ----
    if plan_id:
        dow_q = db.query(
            extract('dow', first_exec_subq.c.first_executed_at).label('dow'),
            func.count(first_exec_subq.c.test_case_id).label('count')
        ).filter(
            first_exec_subq.c.executor_id == user_id,
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt,
            first_exec_subq.c.test_plan_id == plan_id
        ).group_by('dow')
    else:
        dow_q = db.query(
            extract('dow', first_exec_subq.c.first_executed_at).label('dow'),
            func.count(first_exec_subq.c.test_case_id).label('count')
        ).filter(
            first_exec_subq.c.executor_id == user_id,
            first_exec_subq.c.first_executed_at >= start_dt,
            first_exec_subq.c.first_executed_at < end_dt
        )
        if team_id:
            dow_q = dow_q.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            dow_q = dow_q.filter(TestPlan.team_id == team_id)
        elif pids is not None:
            dow_q = dow_q.join(TestPlan, first_exec_subq.c.test_plan_id == TestPlan.id)
            dow_q = _apply_project_filter(dow_q, TestPlan.project_id, pids)
        dow_q = dow_q.group_by('dow')
    dow_rows = dow_q.all()
    exec_by_dow = []
    for r in dow_rows:
        dow = int(r.dow)
        dow_adjusted = (dow - 1) % 7 if dow > 0 else 6
        exec_by_dow.append({"dow": dow_adjusted, "count": r.count})
    exec_by_dow.sort(key=lambda x: x["dow"])

    return {
        "code": 200,
        "data": {
            "overview": overview,
            "exec_by_result": exec_by_result,
            "exec_trend": exec_trend,
            "team_avg_trend": team_avg_trend,
            "plans_detail": plans_detail,
            "cases_by_level": cases_by_level,
            "cases_by_module": cases_by_module,
            "review_by_result": review_by_result,
            "exec_by_hour": exec_by_hour,
            "exec_by_dow": exec_by_dow
        }
    }


@router.get("/pr-count")
def get_pr_count_by_user(
    team_id: Optional[int] = None,
    plan_id: Optional[int] = None,
    plan_ids: Optional[str] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """PR数量统计 - 按成员统计提交的PR数量"""
    from models import TestCaseZmindLink, TestPlan
    from datetime import date

    user_provided_dates = start_date and end_date

    if not user_provided_dates:
        if not granularity:
            granularity = 'day'

        today = date.today()

        if granularity == 'day':
            start_date = today.strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        elif granularity == 'week':
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            start_date = monday.strftime('%Y-%m-%d')
            end_date = sunday.strftime('%Y-%m-%d')
        elif granularity == 'month':
            first_day = today.replace(day=1)
            if today.month == 12:
                last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            start_date = first_day.strftime('%Y-%m-%d')
            end_date = last_day.strftime('%Y-%m-%d')
        else:
            start_date = today.strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')

    if not start_date:
        start_date = date.today().strftime('%Y-%m-%d')
    if not end_date:
        end_date = date.today().strftime('%Y-%m-%d')

    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    except ValueError:
        start_dt = datetime.now() - timedelta(days=30)
        end_dt = datetime.now() + timedelta(days=1)

    # 获取所有有执行记录的用户 - 当指定plan_id时，不应用数据权限过滤
    # 当指定plan_ids时（用户只能看到部分计划），按plan_ids过滤
    if plan_id:
        user_ids_query = db.query(distinct(TestExecution.executor_id)).filter(
            TestExecution.test_plan_id == plan_id
        )
    elif plan_ids:
        try:
            pid_list = [int(p.strip()) for p in plan_ids.split(',') if p.strip()]
            if pid_list:
                user_ids_query = db.query(distinct(TestExecution.executor_id)).filter(
                    TestExecution.test_plan_id.in_(pid_list)
                )
            else:
                user_ids_query = db.query(distinct(TestExecution.executor_id)).filter(TestExecution.id == -1)
        except:
            user_ids_query = db.query(distinct(TestExecution.executor_id)).filter(TestExecution.id == -1)
    elif team_id:
        user_ids_query = db.query(distinct(TestExecution.executor_id)).join(
            TestPlan, TestExecution.test_plan_id == TestPlan.id
        ).filter(TestPlan.team_id == team_id)
    else:
        pids = _get_accessible_project_ids(db, current_user, None)
        if pids:
            user_ids_query = db.query(distinct(TestExecution.executor_id)).join(
                TestPlan, TestExecution.test_plan_id == TestPlan.id
            ).filter(TestPlan.project_id.in_(pids))
        else:
            user_ids_query = db.query(distinct(TestExecution.executor_id))

    if start_date:
        user_ids_query = user_ids_query.filter(TestExecution.executed_at >= start_dt, TestExecution.executed_at < end_dt)
    executor_ids = [r[0] for r in user_ids_query.all()]

    # 也获取创建过用例的用户 - 当指定plan_id时，不应用数据权限过滤
    if plan_id:
        creator_ids_query = db.query(distinct(TestCase.created_by)).join(
            TestPlanTestCase, TestCase.id == TestPlanTestCase.test_case_id
        ).filter(TestPlanTestCase.test_plan_id == plan_id)
    elif plan_ids:
        try:
            pid_list = [int(p.strip()) for p in plan_ids.split(',') if p.strip()]
            if pid_list:
                creator_ids_query = db.query(distinct(TestCase.created_by)).join(
                    TestPlanTestCase, TestCase.id == TestPlanTestCase.test_case_id
                ).filter(TestPlanTestCase.test_plan_id.in_(pid_list))
            else:
                creator_ids_query = db.query(distinct(TestCase.created_by)).filter(False)
        except:
            creator_ids_query = db.query(distinct(TestCase.created_by)).filter(False)
    elif team_id:
        creator_ids_query = db.query(distinct(TestCase.created_by)).join(
            TestPlanTestCase, TestCase.id == TestPlanTestCase.test_case_id
        ).join(TestPlan, TestPlanTestCase.test_plan_id == TestPlan.id
        ).filter(TestPlan.team_id == team_id)
    else:
        pids = _get_accessible_project_ids(db, current_user, team_id)
        if pids is not None:
            creator_ids_query = db.query(distinct(TestCase.created_by)).filter(
                TestCase.primary_project_id.in_(pids)
            ) if pids else db.query(distinct(TestCase.created_by)).filter(False)
        else:
            creator_ids_query = db.query(distinct(TestCase.created_by))
    creator_ids = [r[0] for r in creator_ids_query.all()]

    # 合并用户ID
    all_user_ids = list(set(executor_ids + creator_ids))
    if not all_user_ids:
        return {"code": 200, "data": {"by_user": {}}}

    # 查询每个用户的PR数量 - 直接通过 TestCaseZmindLink.test_plan_id 统计
    # TestCaseZmindLink.test_plan_id 记录了PR关联的测试计划
    # 同时应用时间过滤
    user_pr_counts = {}

    if plan_id:
        pr_q = db.query(
            TestCaseZmindLink.created_by,
            func.count(TestCaseZmindLink.id).label('pr_count')
        ).filter(
            TestCaseZmindLink.test_plan_id == plan_id,
            TestCaseZmindLink.created_by.in_(all_user_ids),
            TestCaseZmindLink.created_at >= start_dt,
            TestCaseZmindLink.created_at < end_dt
        ).group_by(TestCaseZmindLink.created_by)
    elif plan_ids:
        try:
            pid_list = [int(p.strip()) for p in plan_ids.split(',') if p.strip()]
            if pid_list:
                pr_q = db.query(
                    TestCaseZmindLink.created_by,
                    func.count(TestCaseZmindLink.id).label('pr_count')
                ).filter(
                    TestCaseZmindLink.test_plan_id.in_(pid_list),
                    TestCaseZmindLink.created_by.in_(all_user_ids),
                    TestCaseZmindLink.created_at >= start_dt,
                    TestCaseZmindLink.created_at < end_dt
                ).group_by(TestCaseZmindLink.created_by)
            else:
                pr_q = db.query(TestCaseZmindLink.created_by, func.literal(0).label('pr_count')).filter(TestCaseZmindLink.id == -1)
        except:
            pr_q = db.query(TestCaseZmindLink.created_by, func.literal(0).label('pr_count')).filter(TestCaseZmindLink.id == -1)
    elif team_id:
        pr_q = db.query(
            TestCaseZmindLink.created_by,
            func.count(TestCaseZmindLink.id).label('pr_count')
        ).join(
            TestPlan, TestCaseZmindLink.test_plan_id == TestPlan.id
        ).filter(
            TestPlan.team_id == team_id,
            TestCaseZmindLink.created_by.in_(all_user_ids),
            TestCaseZmindLink.created_at >= start_dt,
            TestCaseZmindLink.created_at < end_dt
        ).group_by(TestCaseZmindLink.created_by)
    else:
        pids = _get_accessible_project_ids(db, current_user, None)
        if pids:
            pr_q = db.query(
                TestCaseZmindLink.created_by,
                func.count(TestCaseZmindLink.id).label('pr_count')
            ).join(
                TestPlan, TestCaseZmindLink.test_plan_id == TestPlan.id
            ).filter(
                TestPlan.project_id.in_(pids),
                TestCaseZmindLink.created_by.in_(all_user_ids),
                TestCaseZmindLink.created_at >= start_dt,
                TestCaseZmindLink.created_at < end_dt
            ).group_by(TestCaseZmindLink.created_by)
        else:
            pr_q = db.query(TestCaseZmindLink.created_by, func.literal(0).label('pr_count')).filter(TestCaseZmindLink.id == -1)

    for r in pr_q.all():
        if r.created_by:
            user = db.query(User.username).filter(User.id == r.created_by).first()
            if user:
                user_pr_counts[user.username] = r.pr_count

    return {"code": 200, "data": {"by_user": user_pr_counts}}


@router.post("/pr-check")
async def check_pr_in_platform(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传 Excel 文件，读取第一列 PR 号，
    在平台以下字段中搜索：
      - test_cases.remarks          (用例备注)
      - test_cases.archive_source   (用例归档来源)
      - test_executions.remarks     (执行备注)
      - test_executions.pr_links_snapshot (PR链接快照)
    返回每个 PR 的匹配详情列表
    """
    import io
    import openpyxl

    # ── 1. 读取 Excel，提取第一列 PR ──────────────────────────────────────────
    content = await file.read()
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        ws = wb.active
    except Exception:
        return {"code": 400, "message": "无法解析 Excel 文件，请确认格式正确"}

    pr_list = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        val = row[0] if row else None
        if val is not None and str(val).strip():
            pr_list.append(str(val).strip())

    if not pr_list:
        return {"code": 400, "message": "未在 Excel 第一列（第3行起）找到有效 PR 号"}

    if len(pr_list) > 2000:
        pr_list = pr_list[:2000]

    # ── 2. 逐个 PR 查询 ───────────────────────────────────────────────────────
    results = []

    for pr in pr_list:
        like = f"%{pr}%"
        hits = []

        # test_cases.remarks
        rows = db.query(
            TestCase.id, TestCase.case_number, TestCase.name,
            TestCase.remarks, TestCase.module, Project.name
        ).outerjoin(Project, TestCase.primary_project_id == Project.id
        ).filter(TestCase.remarks.ilike(like)).all()
        for r in rows:
            hits.append({
                "source": "用例备注",
                "testcase_id": r[0],
                "case_number": r[1] or "",
                "case_name": (r[2] or "").replace("\n", " ")[:100],
                "matched_text": (r[3] or "").replace("\n", " ")[:200],
                "plan_name": "",
                "result": "",
                "executed_at": "",
                "project": r[5] or "",
                "executor": "",
            })

        # test_cases.archive_source
        rows = db.query(
            TestCase.id, TestCase.case_number, TestCase.name,
            TestCase.archive_source, TestCase.module, Project.name
        ).outerjoin(Project, TestCase.primary_project_id == Project.id
        ).filter(TestCase.archive_source.ilike(like)).all()
        for r in rows:
            hits.append({
                "source": "用例归档来源",
                "testcase_id": r[0],
                "case_number": r[1] or "",
                "case_name": (r[2] or "").replace("\n", " ")[:100],
                "matched_text": (r[3] or "").replace("\n", " ")[:200],
                "plan_name": "",
                "result": "",
                "executed_at": "",
                "project": r[5] or "",
                "executor": "",
            })

        # test_executions.remarks
        rows = db.query(
            TestExecution.test_case_id,
            TestExecution.testcase_number,
            TestExecution.testcase_name,
            TestExecution.remarks,
            TestExecution.result,
            TestExecution.executed_at,
            TestPlan.name,
            Project.name,
            User.username,
        ).outerjoin(TestPlan, TestExecution.test_plan_id == TestPlan.id
        ).outerjoin(Project, TestPlan.project_id == Project.id
        ).outerjoin(User, TestExecution.executor_id == User.id
        ).filter(TestExecution.remarks.ilike(like)).all()
        for r in rows:
            hits.append({
                "source": "执行备注",
                "testcase_id": r[0],
                "case_number": r[1] or "",
                "case_name": (r[2] or "").replace("\n", " ")[:100],
                "matched_text": (r[3] or "").replace("\n", " ")[:200],
                "plan_name": r[6] or "",
                "result": r[4] or "",
                "executed_at": r[5].strftime("%Y-%m-%d %H:%M") if r[5] else "",
                "project": r[7] or "",
                "executor": r[8] or "",
            })

        # test_executions.pr_links_snapshot
        rows = db.query(
            TestExecution.test_case_id,
            TestExecution.testcase_number,
            TestExecution.testcase_name,
            TestExecution.pr_links_snapshot,
            TestExecution.result,
            TestExecution.executed_at,
            TestPlan.name,
            Project.name,
            User.username,
        ).outerjoin(TestPlan, TestExecution.test_plan_id == TestPlan.id
        ).outerjoin(Project, TestPlan.project_id == Project.id
        ).outerjoin(User, TestExecution.executor_id == User.id
        ).filter(TestExecution.pr_links_snapshot.ilike(like)).all()
        for r in rows:
            hits.append({
                "source": "PR链接快照",
                "testcase_id": r[0],
                "case_number": r[1] or "",
                "case_name": (r[2] or "").replace("\n", " ")[:100],
                "matched_text": (r[3] or "").replace("\n", " ")[:200],
                "plan_name": r[6] or "",
                "result": r[4] or "",
                "executed_at": r[5].strftime("%Y-%m-%d %H:%M") if r[5] else "",
                "project": r[7] or "",
                "executor": r[8] or "",
            })

        results.append({
            "pr": pr,
            "matched": len(hits) > 0,
            "hits": hits,
        })

    matched_count = sum(1 for r in results if r["matched"])
    return {
        "code": 200,
        "data": {
            "total": len(results),
            "matched_count": matched_count,
            "unmatched_count": len(results) - matched_count,
            "results": results,
        }
    }
