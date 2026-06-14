from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from typing import Optional
from datetime import datetime
from database import get_db
from models import TaskOverview, TaskOverviewPlan, TaskOverviewViewer, TestPlan, TestPlanTestCase, TestExecution, TestCase, User
from schemas import TaskOverviewCreate, TaskOverviewUpdate, TaskOverviewAddPlans
from auth import get_current_user
from utils.logger import log_operation, LogAction, LogModule
from utils.data_permission import apply_task_overview_data_permission
import json

router = APIRouter()


def _compute_overview_status(plan_statuses):
    if not plan_statuses:
        return "PENDING"
    if all(s == "COMPLETED" for s in plan_statuses):
        return "COMPLETED"
    if all(s == "PENDING" for s in plan_statuses):
        return "PENDING"
    return "IN_PROGRESS"


def _build_overview_response(db, overview, plan_ids=None):
    if plan_ids is None:
        rows = db.query(TaskOverviewPlan.test_plan_id).filter(
            TaskOverviewPlan.task_overview_id == overview.id
        ).all()
        plan_ids = [r[0] for r in rows]

    creator = db.query(User).filter(User.id == overview.created_by).first()
    viewer_rows = db.query(TaskOverviewViewer.viewer_id).filter(
        TaskOverviewViewer.task_overview_id == overview.id
    ).all()
    viewer_ids = [r[0] for r in viewer_rows]
    viewers = db.query(User).filter(User.id.in_(viewer_ids)).all() if viewer_ids else []
    viewer_names = [u.username for u in viewers]

    viewer_id_set = set(viewer_ids)

    plan_data = []
    total_testcases = 0
    total_executed = 0
    total_passed = 0
    total_failed = 0
    total_blocked = 0
    total_na = 0
    total_nt = 0
    total_assist = 0
    all_plan_statuses = []
    min_start = None
    max_end = None

    if plan_ids:
        plans = db.query(TestPlan).filter(TestPlan.id.in_(plan_ids)).all()
        plan_map = {p.id: p for p in plans}

        tc_counts = db.query(
            TestPlanTestCase.test_plan_id,
            sa_func.count(TestPlanTestCase.id)
        ).join(
            TestCase, TestPlanTestCase.test_case_id == TestCase.id
        ).filter(
            TestPlanTestCase.test_plan_id.in_(plan_ids)
        ).group_by(TestPlanTestCase.test_plan_id).all()
        tc_count_map = {r[0]: r[1] for r in tc_counts}

        valid_tc_by_plan = {}
        for pid in plan_ids:
            tcs = db.query(TestPlanTestCase.test_case_id).join(
                TestCase, TestPlanTestCase.test_case_id == TestCase.id
            ).filter(
                TestPlanTestCase.test_plan_id == pid
            ).all()
            valid_tc_by_plan[pid] = set(r[0] for r in tcs)

        all_executions = db.query(TestExecution).filter(
            TestExecution.test_plan_id.in_(plan_ids)
        ).order_by(TestExecution.test_plan_id, TestExecution.test_case_id,
                    TestExecution.executed_at.desc()).all()

        exec_by_plan = {}
        for e in all_executions:
            valid_set = valid_tc_by_plan.get(e.test_plan_id, set())
            if e.test_case_id not in valid_set:
                continue
            key = (e.test_plan_id, e.test_case_id)
            if key not in exec_by_plan:
                exec_by_plan[key] = e

        plan_exec_map = {}
        for (p_id, tc_id), exec_rec in exec_by_plan.items():
            if p_id not in plan_exec_map:
                plan_exec_map[p_id] = {}
            plan_exec_map[p_id][tc_id] = exec_rec

        for pid in plan_ids:
            plan = plan_map.get(pid)
            if not plan:
                continue
            total = tc_count_map.get(pid, 0)
            total_testcases += total
            all_plan_statuses.append(plan.status)

            if plan.start_time and (min_start is None or plan.start_time < min_start):
                min_start = plan.start_time
            if plan.end_time and (max_end is None or plan.end_time > max_end):
                max_end = plan.end_time

            plan_execs = plan_exec_map.get(pid, {})
            executed = sum(1 for e in plan_execs.values() if e.result not in ('ONGOING', 'PENDING'))
            passed = sum(1 for e in plan_execs.values() if e.result == 'PASS')
            failed = sum(1 for e in plan_execs.values() if e.result == 'FAIL')
            blocked = sum(1 for e in plan_execs.values() if e.result == 'BLOCK')
            na = sum(1 for e in plan_execs.values() if e.result == 'NA')
            nt = sum(1 for e in plan_execs.values() if e.result == 'NT')
            assist = sum(1 for e in plan_execs.values() if e.result == 'ASSIST')

            total_executed += executed
            total_passed += passed
            total_failed += failed
            total_blocked += blocked
            total_na += na
            total_nt += nt
            total_assist += assist

            plan_data.append({
                "id": plan.id,
                "name": plan.name,
                "status": plan.status,
                "total_testcases": total,
                "executed": executed,
                "passed": passed,
                "failed": failed,
                "blocked": blocked,
                "na": na,
                "nt": nt,
                "assist": assist,
                "start_time": plan.start_time.strftime("%Y-%m-%d") if plan.start_time else None,
                "end_time": plan.end_time.strftime("%Y-%m-%d") if plan.end_time else None,
            })

    status = _compute_overview_status(all_plan_statuses)
    valid_cases = total_testcases - total_na - total_assist
    executed_pct = round(total_executed / total_testcases * 100, 2) if total_testcases > 0 else 0.00
    pass_rate = round(total_passed / valid_cases * 100, 2) if valid_cases > 0 else 0.00

    return {
        "id": overview.id,
        "project_id": overview.project_id,
        "team_id": overview.team_id,
        "name": overview.name,
        "description": overview.description,
        "start_time": overview.start_time.strftime("%Y-%m-%d %H:%M:%S") if overview.start_time else None,
        "end_time": overview.end_time.strftime("%Y-%m-%d %H:%M:%S") if overview.end_time else None,
        "status": status,
        "total_testcases": total_testcases,
        "statistics": {
            "executed": total_executed,
            "passed": total_passed,
            "failed": total_failed,
            "blocked": total_blocked,
            "na": total_na,
            "nt": total_nt,
            "assist": total_assist,
            "executed_pct": executed_pct
        },
        "pass_rate": pass_rate,
        "executed_pct": executed_pct,
        "execution_period_start": min_start.strftime("%Y-%m-%d") if min_start else None,
        "execution_period_end": max_end.strftime("%Y-%m-%d") if max_end else None,
        "creator_id": overview.created_by,
        "creator_name": creator.username if creator else "",
        "viewer_ids": viewer_ids,
        "viewer_names": viewer_names,
        "plan_ids": plan_ids,
        "plans": plan_data,
        "created_at": overview.created_at.strftime("%Y-%m-%d %H:%M:%S") if overview.created_at else None,
        "updated_at": overview.updated_at.strftime("%Y-%m-%d %H:%M:%S") if overview.updated_at else None,
    }


@router.get("")
def list_task_overviews(
    req: Request,
    page: int = 1,
    size: int = 10,
    project_id: Optional[int] = None,
    team_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(TaskOverview)

    if project_id:
        query = query.filter(TaskOverview.project_id == project_id)
    if team_id:
        query = query.filter(TaskOverview.team_id == team_id)
    if search:
        query = query.filter(TaskOverview.name.ilike(f"%{search}%"))

    # 应用数据权限过滤（与测试计划 Tab 保持一致）
    query = apply_task_overview_data_permission(query, current_user, db)

    total = query.count()
    overviews = query.order_by(TaskOverview.created_at.desc()).offset(
        (page - 1) * size).limit(size).all()

    result = []
    for ov in overviews:
        row = _build_overview_response(db, ov)
        result.append(row)

    if status:
        result = [r for r in result if r["status"] == status]

    return {
        "code": 200,
        "data": {
            "items": result,
            "total": total,
            "page": page,
            "size": size
        }
    }


@router.post("")
def create_task_overview(
    req: Request,
    body: TaskOverviewCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.id

    overview = TaskOverview(
        project_id=body.project_id,
        team_id=body.team_id,
        name=body.name,
        description=body.description,
        created_by=user_id,
    )

    db.add(overview)
    db.flush()

    plan_ids = body.plan_ids or []
    for pid in plan_ids:
        plan = db.query(TestPlan).filter(TestPlan.id == pid).first()
        if plan:
            db.add(TaskOverviewPlan(task_overview_id=overview.id, test_plan_id=pid))

    viewer_ids = body.viewer_ids or []
    for vid in viewer_ids:
        db.add(TaskOverviewViewer(task_overview_id=overview.id, viewer_id=vid))

    db.commit()
    db.refresh(overview)

    log_operation(db, user_id, current_user.username,
                  LogModule.TESTPLANS, LogAction.CREATE,
                  f"创建任务总览: {overview.name} (ID: {overview.id})",
                  req)

    response = _build_overview_response(db, overview)
    return {"code": 200, "data": response}


@router.get("/{overview_id}")
def get_task_overview_detail(
    overview_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    overview = db.query(TaskOverview).filter(TaskOverview.id == overview_id).first()
    if not overview:
        raise HTTPException(status_code=404, detail="任务总览不存在")

    response = _build_overview_response(db, overview)
    return {"code": 200, "data": response}


@router.put("/{overview_id}")
def update_task_overview(
    overview_id: int,
    req: Request,
    body: TaskOverviewUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    overview = db.query(TaskOverview).filter(TaskOverview.id == overview_id).first()
    if not overview:
        raise HTTPException(status_code=404, detail="任务总览不存在")

    if overview.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="只有创建人才能编辑该任务总览")

    if body.name is not None:
        overview.name = body.name
    if body.description is not None:
        overview.description = body.description

    if body.plan_ids is not None:
        db.query(TaskOverviewPlan).filter(
            TaskOverviewPlan.task_overview_id == overview.id
        ).delete()
        for pid in body.plan_ids:
            plan = db.query(TestPlan).filter(TestPlan.id == pid).first()
            if plan:
                db.add(TaskOverviewPlan(task_overview_id=overview.id, test_plan_id=pid))

    if body.viewer_ids is not None:
        db.query(TaskOverviewViewer).filter(
            TaskOverviewViewer.task_overview_id == overview.id
        ).delete()
        for vid in body.viewer_ids:
            db.add(TaskOverviewViewer(task_overview_id=overview.id, viewer_id=vid))

    db.commit()
    db.refresh(overview)

    log_operation(db, current_user.id, current_user.username,
                  LogModule.TESTPLANS, LogAction.UPDATE,
                  f"编辑任务总览: {overview.name} (ID: {overview.id})",
                  req)

    response = _build_overview_response(db, overview)
    return {"code": 200, "data": response}


@router.delete("/{overview_id}")
def delete_task_overview(
    overview_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    overview = db.query(TaskOverview).filter(TaskOverview.id == overview_id).first()
    if not overview:
        raise HTTPException(status_code=404, detail="任务总览不存在")

    if overview.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="只有创建人才能删除该任务总览")

    name = overview.name
    db.delete(overview)
    db.commit()

    log_operation(db, current_user.id, current_user.username,
                  LogModule.TESTPLANS, LogAction.DELETE,
                  f"删除任务总览: {name} (ID: {overview_id})",
                  req)

    return {"code": 200, "message": "删除成功"}


@router.post("/{overview_id}/plans")
def add_plans_to_overview(
    overview_id: int,
    req: Request,
    body: TaskOverviewAddPlans,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    overview = db.query(TaskOverview).filter(TaskOverview.id == overview_id).first()
    if not overview:
        raise HTTPException(status_code=404, detail="任务总览不存在")

    if overview.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="只有创建人才能修改该任务总览")

    existing = set(r[0] for r in db.query(TaskOverviewPlan.test_plan_id).filter(
        TaskOverviewPlan.task_overview_id == overview.id
    ).all())

    for pid in body.plan_ids:
        if pid not in existing:
            plan = db.query(TestPlan).filter(TestPlan.id == pid).first()
            if plan:
                db.add(TaskOverviewPlan(task_overview_id=overview.id, test_plan_id=pid))

    db.commit()

    response = _build_overview_response(db, overview)
    return {"code": 200, "data": response}


@router.delete("/{overview_id}/plans/{plan_id}")
def remove_plan_from_overview(
    overview_id: int,
    plan_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    overview = db.query(TaskOverview).filter(TaskOverview.id == overview_id).first()
    if not overview:
        raise HTTPException(status_code=404, detail="任务总览不存在")

    if overview.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="只有创建人才能修改该任务总览")

    db.query(TaskOverviewPlan).filter(
        TaskOverviewPlan.task_overview_id == overview_id,
        TaskOverviewPlan.test_plan_id == plan_id
    ).delete()
    db.commit()

    response = _build_overview_response(db, overview)
    return {"code": 200, "data": response}
