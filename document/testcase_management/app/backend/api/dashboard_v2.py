"""
工作台 v2 API - 新版工作台卡片数据
支持5个卡片模块：用例库信息、PR关联列表、评审计划、测试计划、用户任务统计

数据权限层级：
- 超管(admin): 看所有数据
- 组织负责人(DepartmentManager): 看该组织下所有数据
- 项目组负责人(Team.leader_id): 看该项目组下所有数据
- 普通用户: 只看自己相关的数据
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, distinct
from database import get_db
from models import (
    User, TestCase, TestPlan, TestExecution, TestPlanTestCase, TestPlanExecutor,
    Project, UserProject, UserTeam, Team, TeamProject, ReviewPlan, ReviewPlanTestCase,
    TestCaseZmindLink, TestCaseProject, Department, UserDepartment, DepartmentManager,
    TeamLeader
)
from auth import get_current_user
from typing import Optional, List, Set, Tuple
import json

router = APIRouter()

SUPER_ADMINS = ['admin', 'super']


def _is_super_admin(user: User) -> bool:
    return user.username in SUPER_ADMINS


def _get_managed_dept_ids(db: Session, user: User) -> List[int]:
    """获取用户作为负责人管理的组织ID列表"""
    rows = db.query(DepartmentManager.department_id).filter(
        DepartmentManager.user_id == user.id
    ).all()
    return [r.department_id for r in rows]


def _get_led_team_ids(db: Session, user: User) -> List[int]:
    """获取用户作为负责人的项目组ID列表"""
    rows = db.query(TeamLeader.team_id).filter(
        TeamLeader.user_id == user.id
    ).all()
    team_ids = [r.team_id for r in rows]
    # 过滤只保留启用的项目组
    if team_ids:
        active = db.query(Team.id).filter(Team.id.in_(team_ids), Team.status == 1).all()
        return [t.id for t in active]
    return []


def _dept_ids_to_project_ids(db: Session, dept_ids: List[int]) -> List[int]:
    """组织ID -> 项目组 -> 用例库ID"""
    if not dept_ids:
        return []
    team_ids = [t.id for t in db.query(Team.id).filter(
        Team.department_id.in_(dept_ids), Team.status == 1
    ).all()]
    if not team_ids:
        return []
    return [tp.project_id for tp in db.query(TeamProject.project_id).filter(
        TeamProject.team_id.in_(team_ids)
    ).all()]


def _team_ids_to_project_ids(db: Session, team_ids: List[int]) -> List[int]:
    """项目组ID -> 用例库ID"""
    if not team_ids:
        return []
    return [tp.project_id for tp in db.query(TeamProject.project_id).filter(
        TeamProject.team_id.in_(team_ids)
    ).all()]


def _dept_ids_to_user_ids(db: Session, dept_ids: List[int]) -> List[int]:
    """组织ID -> 用户ID列表"""
    if not dept_ids:
        return []
    rows = db.query(UserDepartment.user_id).filter(
        UserDepartment.department_id.in_(dept_ids)
    ).all()
    return list(set([r.user_id for r in rows]))


def _team_ids_to_user_ids(db: Session, team_ids: List[int]) -> List[int]:
    """项目组ID -> 用户ID列表"""
    if not team_ids:
        return []
    rows = db.query(UserTeam.user_id).filter(
        UserTeam.team_id.in_(team_ids)
    ).all()
    return list(set([r.user_id for r in rows]))


def get_dashboard_scope(db: Session, user: User, team_id: int = None) -> dict:
    """
    计算当前用户的工作台数据范围

    当传入 team_id 时：
    - 超管/组织负责人：直接按该项目组过滤
    - 其他用户：按该项目组过滤（前提是用户属于该项目组）

    当不传 team_id 时（保持原逻辑）：
    - 超级管理员：看所有数据
    - 组织负责人：看管理的所有组织下的全部数据
    - 其他：按 content_permissions 配置

    返回:
        {
            "level": "super" | "dept_manager" | "team_leader" | "personal",
            "project_ids": list[int] | None,  # None=不限制
            "user_ids": list[int] | None,      # None=不限制
            "dept_ids": list[int],             # 管理的组织ID
            "team_ids": list[int],             # 管理的项目组ID
        }
    """
    from utils.data_permission import (
        get_user_content_permission, get_user_organization_ids,
        get_user_team_ids, get_team_project_ids, get_organization_project_ids
    )

    # 如果传入了 team_id，按项目组过滤
    if team_id:
        pids = list(set(_team_ids_to_project_ids(db, [team_id])))
        uids = list(set(_team_ids_to_user_ids(db, [team_id])))
        # 超管和组织负责人可以看任何项目组
        if _is_super_admin(user) or _get_managed_dept_ids(db, user):
            return {
                "level": "team_leader",
                "project_ids": pids,
                "user_ids": uids,
                "dept_ids": [],
                "team_ids": [team_id],
            }
        # 其他用户：验证是否属于该项目组
        user_team_ids = list(get_user_team_ids(user, db))
        if team_id in user_team_ids:
            return {
                "level": "team_leader",
                "project_ids": pids,
                "user_ids": uids,
                "dept_ids": [],
                "team_ids": [team_id],
            }
        # 用户不属于该项目组，返回空
        return {
            "level": "personal",
            "project_ids": [],
            "user_ids": [user.id],
            "dept_ids": [],
            "team_ids": [],
        }
    
    # 以下为不传 team_id 时的原逻辑

    # 1. 超管：看所有数据
    if _is_super_admin(user):
        return {
            "level": "super",
            "project_ids": None,
            "user_ids": None,
            "dept_ids": [],
            "team_ids": [],
        }

    # 2. 组织负责人：看管理的所有组织下的全部数据（不受 content_permissions 限制）
    managed_dept_ids = _get_managed_dept_ids(db, user)
    if managed_dept_ids:
        pids = list(set(_dept_ids_to_project_ids(db, managed_dept_ids)))
        uids = list(set(_dept_ids_to_user_ids(db, managed_dept_ids)))
        return {
            "level": "dept_manager",
            "project_ids": pids,
            "user_ids": uids,
            "dept_ids": managed_dept_ids,
            "team_ids": [],
        }

    # 3. 非组织负责人：按 content_permissions 配置
    permission_level = get_user_content_permission(user, 'testcase', db)
    
    if permission_level == 'personal':
        # 仅个人：只看自己的数据
        return {
            "level": "personal",
            "project_ids": [],
            "user_ids": [user.id],
            "dept_ids": [],
            "team_ids": [],
        }
    
    if permission_level == 'project':
        # 项目组可见：看自己直接所属项目组的数据
        team_ids = list(get_user_team_ids(user, db))
        pids = list(set(_team_ids_to_project_ids(db, team_ids))) if team_ids else []
        uids = list(set(_team_ids_to_user_ids(db, team_ids))) if team_ids else [user.id]
        return {
            "level": "team_leader",
            "project_ids": pids,
            "user_ids": uids,
            "dept_ids": [],
            "team_ids": team_ids,
        }
    
    # permission_level == 'all'：组织可见

    # 项目组负责人：看负责的项目组数据
    led_team_ids = _get_led_team_ids(db, user)
    if led_team_ids:
        pids = list(set(_team_ids_to_project_ids(db, led_team_ids)))
        uids = list(set(_team_ids_to_user_ids(db, led_team_ids)))
        return {
            "level": "team_leader",
            "project_ids": pids,
            "user_ids": uids,
            "dept_ids": [],
            "team_ids": led_team_ids,
        }

    # 普通用户（权限为all）：看所属组织下所有数据
    org_ids = get_user_organization_ids(user, db)
    if org_ids:
        pids = list(get_organization_project_ids(org_ids, db))
        uids = list(set(_dept_ids_to_user_ids(db, list(org_ids))))
        return {
            "level": "dept_manager",
            "project_ids": pids,
            "user_ids": uids,
            "dept_ids": list(org_ids),
            "team_ids": [],
        }
    
    # 没有组织：回退到项目组
    team_ids = list(get_user_team_ids(user, db))
    pids = list(set(_team_ids_to_project_ids(db, team_ids))) if team_ids else []
    return {
        "level": "personal",
        "project_ids": pids,
        "user_ids": [user.id],
        "dept_ids": [],
        "team_ids": team_ids,
    }



@router.get("/project-cards")
def get_project_cards(
    team_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    卡片1: 用例库信息卡片
    """
    scope = get_dashboard_scope(db, current_user, team_id=team_id)

    if scope["level"] == "personal":
        # 普通用户：只看自己直接所属项目组关联的用例库
        from utils.data_permission import get_user_team_ids as _get_user_team_ids
        user_team_ids = list(_get_user_team_ids(current_user, db))
        project_ids = list(set(_team_ids_to_project_ids(db, user_team_ids))) if user_team_ids else []
        if not project_ids:
            return {"code": 200, "data": []}
    elif scope["project_ids"] is None:
        # 超管：所有项目
        project_ids = None
    else:
        project_ids = scope["project_ids"]
        if not project_ids:
            return {"code": 200, "data": []}

    # 查询项目
    q = db.query(Project).filter(Project.status == 1)
    if project_ids is not None:
        q = q.filter(Project.id.in_(project_ids))
    projects = q.order_by(Project.name).all()

    cards = []
    for proj in projects:
        # 该用例库下所有用例ID（通过关联表）
        case_ids_q = db.query(TestCaseProject.test_case_id).filter(
            TestCaseProject.project_id == proj.id
        )
        case_ids = [c.test_case_id for c in case_ids_q.all()]

        if not case_ids:
            # 回退到 primary_project_id
            case_ids_q2 = db.query(TestCase.id).filter(
                TestCase.primary_project_id == proj.id
            )
            case_ids = [c.id for c in case_ids_q2.all()]

        total = len(case_ids)

        if total == 0:
            cards.append({
                "project_id": proj.id,
                "project_name": proj.name,
                "total": 0, "l1": 0, "l2": 0, "l3": 0, "l4": 0,
                "auto_done": 0, "auto_na": 0, "auto_pending": 0,
                "review_pending": 0, "review_rejected": 0
            })
            continue

        # 等级统计
        level_counts = db.query(
            TestCase.level, func.count(TestCase.id)
        ).filter(TestCase.id.in_(case_ids)).group_by(TestCase.level).all()
        level_map = {lv: cnt for lv, cnt in level_counts}

        # 自动化统计
        auto_done = db.query(func.count(TestCase.id)).filter(
            TestCase.id.in_(case_ids),
            TestCase.automation == 'D'  # 自动化已完成
        ).scalar() or 0
        
        auto_na = db.query(func.count(TestCase.id)).filter(
            TestCase.id.in_(case_ids),
            TestCase.automation.like('N-%')
        ).scalar() or 0
        
        auto_pending = db.query(func.count(TestCase.id)).filter(
            TestCase.id.in_(case_ids),
            or_(TestCase.automation == '', TestCase.automation.is_(None))
        ).scalar() or 0

        # 评审统计
        review_pending = db.query(func.count(TestCase.id)).filter(
            TestCase.id.in_(case_ids),
            TestCase.status == 'PENDING'
        ).scalar() or 0

        review_rejected = db.query(func.count(TestCase.id)).filter(
            TestCase.id.in_(case_ids),
            TestCase.status == 'REJECTED'
        ).scalar() or 0

        cards.append({
            "project_id": proj.id,
            "project_name": proj.name,
            "total": total,
            "l1": level_map.get("L1", 0),
            "l2": level_map.get("L2", 0),
            "l3": level_map.get("L3", 0),
            "l4": level_map.get("L4", 0),
            "auto_done": auto_done,
            "auto_na": auto_na,
            "auto_pending": auto_pending,
            "review_pending": review_pending,
            "review_rejected": review_rejected
        })

    return {"code": 200, "data": cards}


@router.get("/pr-list")
def get_pr_list(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    team_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    卡片2: 用例关联PR数
    """
    scope = get_dashboard_scope(db, current_user, team_id=team_id)

    query = db.query(
        TestCase.id,
        TestCase.case_number,
        TestCase.name.label("case_name"),
        TestCase.level,
        TestCase.module,
        TestCase.steps,
        TestCase.expected_result,
        TestCase.primary_project_id,
        func.count(TestCaseZmindLink.id).label("pr_count")
    ).join(
        TestCaseZmindLink, TestCaseZmindLink.test_case_id == TestCase.id
    )

    if scope["level"] == "personal":
        # 普通用户：只看自己创建的用例
        query = query.filter(TestCase.created_by == current_user.id)
    elif scope["project_ids"] is not None:
        if scope["project_ids"]:
            query = query.filter(TestCase.primary_project_id.in_(scope["project_ids"]))
        else:
            return {"code": 200, "data": {"records": [], "total": 0, "page": page, "size": size}}

    query = query.group_by(
        TestCase.id, TestCase.case_number, TestCase.name, TestCase.level,
        TestCase.module, TestCase.steps, TestCase.expected_result,
        TestCase.primary_project_id
    ).having(func.count(TestCaseZmindLink.id) > 0).order_by(
        func.count(TestCaseZmindLink.id).desc(), TestCase.id.asc()
    )

    total = query.count()
    records = query.offset((page - 1) * size).limit(size).all()

    # 项目名称映射
    pid_set = list(set([r.primary_project_id for r in records if r.primary_project_id]))
    proj_map = {}
    if pid_set:
        projs = db.query(Project.id, Project.name).filter(Project.id.in_(pid_set)).all()
        proj_map = {p.id: p.name for p in projs}

    items = []
    for r in records:
        items.append({
            "testcase_id": r.id,
            "case_number": r.case_number,
            "case_name": r.case_name,
            "level": r.level or "",
            "module": r.module or "",
            "steps": r.steps or "",
            "expected_result": r.expected_result or "",
            "project_name": proj_map.get(r.primary_project_id, ""),
            "pr_count": r.pr_count
        })

    return {
        "code": 200,
        "data": {
            "records": items,
            "total": total,
            "page": page,
            "size": size
        }
    }


@router.get("/review-plans")
def get_review_plans(
    team_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    卡片3: 用例评审计划卡片
    仅显示状态为"待评审"和"进行中"的评审计划
    """
    scope = get_dashboard_scope(db, current_user, team_id=team_id)

    query = db.query(ReviewPlan).filter(
        ReviewPlan.status.in_(['PENDING', 'IN_PROGRESS'])
    )

    # 如果传了 team_id，直接按 team_id 过滤
    if team_id:
        query = query.filter(ReviewPlan.team_id == team_id)
    elif scope["level"] == "personal":
        # 普通用户：只看自己创建的或自己是评审人的
        query = query.filter(
            or_(
                ReviewPlan.created_by == current_user.id,
                ReviewPlan.reviewer_ids.like('%' + str(current_user.id) + '%')
            )
        )
    elif scope["project_ids"] is not None:
        if scope["project_ids"]:
            query = query.filter(ReviewPlan.project_id.in_(scope["project_ids"]))
        else:
            return {"code": 200, "data": []}

    plans = query.order_by(ReviewPlan.created_at.desc()).all()

    items = []
    for plan in plans:
        # 统计进度
        total_cases = db.query(func.count(ReviewPlanTestCase.id)).filter(
            ReviewPlanTestCase.review_plan_id == plan.id
        ).scalar() or 0

        reviewed_cases = db.query(func.count(ReviewPlanTestCase.id)).filter(
            ReviewPlanTestCase.review_plan_id == plan.id,
            ReviewPlanTestCase.review_status != 'PENDING'
        ).scalar() or 0

        progress = round((reviewed_cases / total_cases * 100) if total_cases > 0 else 0, 1)

        # 获取项目名称
        proj = db.query(Project.name).filter(Project.id == plan.project_id).first()

        # 获取创建人名称
        creator = db.query(User.username).filter(User.id == plan.created_by).first()
        creator_name = creator.username if creator else ""

        # 获取评审人名称
        reviewer_names = []
        if plan.reviewer_ids:
            try:
                r_ids = json.loads(plan.reviewer_ids)
                if r_ids:
                    reviewers = db.query(User.username).filter(User.id.in_(r_ids)).all()
                    reviewer_names = [r.username for r in reviewers]
            except (json.JSONDecodeError, TypeError):
                pass

        items.append({
            "id": plan.id,
            "name": plan.name,
            "project_name": proj.name if proj else "",
            "status": plan.status,
            "creator": creator_name,
            "reviewers": reviewer_names,
            "total_cases": total_cases,
            "reviewed_cases": reviewed_cases,
            "progress": progress,
            "start_time": plan.start_time.isoformat() if plan.start_time else None,
            "end_time": plan.end_time.isoformat() if plan.end_time else None,
            "created_at": plan.created_at.isoformat() if plan.created_at else None
        })

    return {"code": 200, "data": items}


@router.get("/test-plans")
def get_test_plans(
    team_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    卡片4: 测试计划卡片
    仅显示状态为"待执行"、"进行中"和"待评审"的测试计划
    """
    scope = get_dashboard_scope(db, current_user, team_id=team_id)

    query = db.query(TestPlan).filter(
        TestPlan.status.in_(['PENDING', 'IN_PROGRESS', 'IN_REVIEW'])
    )

    # 如果传了 team_id，直接按 team_id 过滤（优先使用 plan 上的 team_id 字段）
    if team_id:
        query = query.filter(TestPlan.team_id == team_id)
    elif scope["level"] == "personal":
        # 普通用户：只看自己创建的或自己是执行人的
        executor_plan_ids = db.query(TestPlanExecutor.test_plan_id).filter(
            TestPlanExecutor.executor_id == current_user.id
        ).distinct()
        query = query.filter(
            or_(
                TestPlan.created_by == current_user.id,
                TestPlan.id.in_(executor_plan_ids),
                TestPlan.reviewer_id == current_user.id
            )
        )
    elif scope["project_ids"] is not None:
        if scope["project_ids"]:
            query = query.filter(TestPlan.project_id.in_(scope["project_ids"]))
        else:
            return {"code": 200, "data": []}

    plans = query.order_by(TestPlan.created_at.desc()).all()

    items = []
    for plan in plans:
        # 统计进度
        total_cases = db.query(func.count(TestPlanTestCase.id)).filter(
            TestPlanTestCase.test_plan_id == plan.id
        ).scalar() or 0

        executed_cases = db.query(func.count(distinct(TestExecution.test_case_id))).filter(
            TestExecution.test_plan_id == plan.id
        ).scalar() or 0

        progress = round((executed_cases / total_cases * 100) if total_cases > 0 else 0, 1)

        # 获取项目组名称（优先使用计划自身的team_id）
        team_name = ""
        if plan.team_id:
            team_row = db.query(Team.name).filter(Team.id == plan.team_id).first()
            team_name = team_row.name if team_row else ""
        else:
            # 兜底：通过TeamProject关联表查
            team_row = db.query(Team.name).join(
                TeamProject, TeamProject.team_id == Team.id
            ).filter(
                TeamProject.project_id == plan.project_id
            ).first()
            team_name = team_row.name if team_row else ""

        # 获取创建人
        creator = db.query(User.username).filter(User.id == plan.created_by).first()
        creator_name = creator.username if creator else ""

        # 获取执行人
        executors = db.query(User.username).join(
            TestPlanExecutor, TestPlanExecutor.executor_id == User.id
        ).filter(TestPlanExecutor.test_plan_id == plan.id).all()
        executor_names = [e.username for e in executors]

        # 获取审核人
        reviewer_name = ""
        if plan.reviewer_id:
            reviewer = db.query(User.username).filter(User.id == plan.reviewer_id).first()
            reviewer_name = reviewer.username if reviewer else ""

        items.append({
            "id": plan.id,
            "name": plan.name,
            "team_name": team_name,
            "status": plan.status,
            "creator": creator_name,
            "executors": executor_names,
            "reviewer": reviewer_name,
            "total_cases": total_cases,
            "executed_cases": executed_cases,
            "progress": progress,
            "start_time": plan.start_time.isoformat() if plan.start_time else None,
            "end_time": plan.end_time.isoformat() if plan.end_time else None,
            "created_at": plan.created_at.isoformat() if plan.created_at else None
        })

    return {"code": 200, "data": items}


@router.get("/user-tasks")
def get_user_tasks(
    team_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    卡片5: 用户任务数量统计
    """
    scope = get_dashboard_scope(db, current_user, team_id=team_id)

    # 确定要展示哪些用户
    if scope["level"] == "super":
        # 超管：所有活跃用户
        target_user_ids = [u.id for u in db.query(User.id).filter(User.status == 1).all()]
    elif scope["level"] == "personal":
        # 普通用户：只看自己
        target_user_ids = [current_user.id]
    else:
        # 组织/项目组负责人：看管辖范围内的用户
        target_user_ids = scope["user_ids"] or []

    if not target_user_ids:
        return {"code": 200, "data": []}

    # 构建用户->组织名映射
    user_dept_map = {}
    ud_rows = db.query(
        UserDepartment.user_id, Department.name
    ).join(
        Department, Department.id == UserDepartment.department_id
    ).filter(
        UserDepartment.user_id.in_(target_user_ids)
    ).all()
    for row in ud_rows:
        if row.user_id not in user_dept_map:
            user_dept_map[row.user_id] = []
        user_dept_map[row.user_id].append(row.name)

    # 构建用户->项目组名映射
    user_team_map = {}
    ut_rows = db.query(
        UserTeam.user_id, Team.name
    ).join(
        Team, Team.id == UserTeam.team_id
    ).filter(
        UserTeam.user_id.in_(target_user_ids),
        Team.status == 1
    ).all()
    for row in ut_rows:
        if row.user_id not in user_team_map:
            user_team_map[row.user_id] = []
        user_team_map[row.user_id].append(row.name)

    # 查询每个用户的进行中任务数
    results = db.query(
        User.id,
        User.username,
        User.full_name,
        func.count(distinct(TestPlan.id)).label("task_count")
    ).join(
        TestPlanExecutor, TestPlanExecutor.executor_id == User.id
    ).join(
        TestPlan, TestPlan.id == TestPlanExecutor.test_plan_id
    ).filter(
        User.id.in_(target_user_ids),
        User.status == 1,
        TestPlan.status.in_(['PENDING', 'IN_PROGRESS', 'IN_REVIEW'])
    ).group_by(
        User.id, User.username, User.full_name
    ).order_by(
        func.count(distinct(TestPlan.id)).desc()
    ).all()

    # 也包含没有任务的用户
    users_with_tasks = {r.id for r in results}
    no_task_filter = ~User.id.in_(users_with_tasks) if users_with_tasks else True
    no_task_users = db.query(
        User.id, User.username, User.full_name
    ).filter(
        User.id.in_(target_user_ids),
        User.status == 1,
        no_task_filter
    ).all()

    items = []
    for r in results:
        if r.task_count > 0:
            dept_names = user_dept_map.get(r.id, [])
            team_names = user_team_map.get(r.id, [])
            items.append({
                "user_id": r.id,
                "username": r.username,
                "full_name": r.full_name or r.username,
                "department_names": dept_names,
                "team_names": team_names,
                "task_count": r.task_count
            })

    return {"code": 200, "data": items}
