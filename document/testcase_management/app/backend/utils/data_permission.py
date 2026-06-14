"""
数据权限过滤工具

权限优先级（从高到低）：
1. 超级管理员 - 看所有数据
2. 组织负责人 - 看管理的所有组织下的全部数据（不受 content_permissions 限制）
3. content_permissions（PositionTag 数据权限配置）：
   - all: 组织可见 - 用户所属组织（部门）下的全部数据
   - project: 项目组可见 - 用户所属项目组下的数据
   - personal: 仅个人 - 个人创建/分配/授权的数据

所有权限都基于组织，不能超出组织范围
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Set
from models import User, PositionTag, UserTeam, TeamProject, UserDepartment, Team, Department, TeamLeader
import json
import logging

logger = logging.getLogger(__name__)

# 超级管理员账号列表
SUPER_ADMINS = ['admin', 'super']


def is_super_admin(user: User) -> bool:
    """检查是否是超级管理员"""
    return user.username in SUPER_ADMINS


def get_managed_department_ids(user: User, db: Session) -> Set[int]:
    """
    获取用户作为组织负责人管理的组织ID列表
    
    Args:
        user: 当前用户
        db: 数据库会话
    
    Returns:
        管理的组织ID集合（空集合表示不是组织负责人）
    """
    from models import DepartmentManager
    rows = db.query(DepartmentManager.department_id).filter(
        DepartmentManager.user_id == user.id
    ).all()
    return {r.department_id for r in rows}


def is_dept_manager(user: User, db: Session) -> bool:
    """检查用户是否是任何组织的负责人"""
    return len(get_managed_department_ids(user, db)) > 0


def get_user_content_permission(user: User, module: str, db: Session) -> str:
    """
    获取用户对指定模块的数据权限级别
    
    Args:
        user: 当前用户
        module: 模块名称 (testcase, testplan, report, notification)
        db: 数据库会话
    
    Returns:
        权限级别: 'all', 'project', 'personal'
    """
    # 超级管理员拥有所有权限
    if is_super_admin(user):
        return 'all'
    
    # 没有分配数据权限标签，默认为组织可见
    if not user.position_tag_id:
        return 'all'
    
    # 获取用户的数据权限配置
    position_tag = db.query(PositionTag).filter(PositionTag.id == user.position_tag_id).first()
    if not position_tag or not position_tag.content_permissions:
        return 'all'
    
    try:
        permissions = json.loads(position_tag.content_permissions)
        # 格式: ["testcase:all", "report:project", "testplan:personal"]
        for perm in permissions:
            if ':' in perm:
                perm_module, perm_level = perm.split(':', 1)
                if perm_module == module:
                    return perm_level
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"解析数据权限配置失败: {e}")
    
    return 'all'


def get_user_organization_ids(user: User, db: Session) -> Set[int]:
    """
    获取用户所属的组织（部门）ID列表
    
    Args:
        user: 当前用户
        db: 数据库会话
    
    Returns:
        组织ID集合
    """
    org_ids = set()
    
    # 从 user_departments 表获取用户所属部门
    user_depts = db.query(UserDepartment).filter(UserDepartment.user_id == user.id).all()
    for ud in user_depts:
        org_ids.add(ud.department_id)
    
    return org_ids


def get_user_team_ids(user: User, db: Session) -> Set[int]:
    """
    获取用户直接所属的项目组ID列表
    
    包括：
    1. 用户作为成员加入的项目组
    2. 用户作为项目组负责人的项目组
    
    注意：不包含组织负责人管理的项目组，组织负责人的逻辑在上层单独处理

    Args:
        user: 当前用户
        db: 数据库会话

    Returns:
        项目组ID集合
    """
    # 用户作为成员加入的项目组
    user_teams = db.query(UserTeam).filter(UserTeam.user_id == user.id).all()
    team_ids = {ut.team_id for ut in user_teams}

    # 用户作为项目组负责人的项目组
    led_teams = db.query(TeamLeader.team_id).filter(
        TeamLeader.user_id == user.id
    ).all()
    for t in led_teams:
        team_ids.add(t.team_id)

    return team_ids



def get_organization_project_ids(org_ids: Set[int], db: Session) -> Set[int]:
    """
    获取组织下所有项目组关联的用例库ID
    
    Args:
        org_ids: 组织ID集合
        db: 数据库会话
    
    Returns:
        用例库ID集合
    """
    if not org_ids:
        return set()
    
    # 获取组织下的所有项目组
    teams = db.query(Team).filter(Team.department_id.in_(org_ids)).all()
    team_ids = {t.id for t in teams}
    
    if not team_ids:
        return set()
    
    # 获取项目组关联的用例库
    team_projects = db.query(TeamProject).filter(TeamProject.team_id.in_(team_ids)).all()
    return {tp.project_id for tp in team_projects}


def get_team_project_ids(team_ids: Set[int], db: Session) -> Set[int]:
    """
    获取项目组关联的用例库ID
    
    Args:
        team_ids: 项目组ID集合
        db: 数据库会话
    
    Returns:
        用例库ID集合
    """
    if not team_ids:
        return set()
    
    team_projects = db.query(TeamProject).filter(TeamProject.team_id.in_(team_ids)).all()
    return {tp.project_id for tp in team_projects}


def get_accessible_project_ids(user: User, module: str, db: Session) -> Optional[Set[int]]:
    """
    根据用户的数据权限获取可访问的用例库ID列表
    
    优先级：超级管理员 > 组织负责人 > content_permissions
    
    Args:
        user: 当前用户
        module: 模块名称 (testcase, testplan, report)
        db: 数据库会话
    
    Returns:
        可访问的用例库ID集合，None表示不限制（超级管理员）
    """
    # 超级管理员不限制
    if is_super_admin(user):
        return None
    
    # 组织负责人：看管理的所有组织下的全部数据（不受 content_permissions 限制）
    managed_dept_ids = get_managed_department_ids(user, db)
    if managed_dept_ids:
        return get_organization_project_ids(managed_dept_ids, db)
    
    # 非组织负责人：按 content_permissions 配置
    permission_level = get_user_content_permission(user, module, db)
    
    # 获取用户所属组织
    org_ids = get_user_organization_ids(user, db)
    
    if permission_level == 'all':
        # 组织可见：返回组织下所有项目组的用例库
        if org_ids:
            org_project_ids = get_organization_project_ids(org_ids, db)
            # 如果组织存在但没有关联项目，不应返回空集合导致无数据
            # 而是回退到不限制（返回None）
            return org_project_ids if org_project_ids else None
        else:
            # 用户没有分配组织，尝试返回其项目组的用例库
            team_ids = get_user_team_ids(user, db)
            if team_ids:
                team_project_ids = get_team_project_ids(team_ids, db)
                return team_project_ids if team_project_ids else None
            # 用户既没有组织也没有项目组，不限制数据访问
            return None
    
    elif permission_level == 'project':
        # 项目组可见：返回用户直接所属项目组的用例库
        team_ids = get_user_team_ids(user, db)
        project_ids = get_team_project_ids(team_ids, db)
        
        # 但不能超出组织范围
        if org_ids:
            org_project_ids = get_organization_project_ids(org_ids, db)
            return project_ids & org_project_ids if org_project_ids else project_ids
        
        return project_ids
    
    elif permission_level == 'personal':
        # 仅个人：返回空集合，需要在具体查询中额外处理 created_by 等条件
        return set()
    
    return None


def apply_testcase_data_permission(query, user: User, db: Session):
    """
    对测试用例查询应用数据权限过滤
    
    Args:
        query: SQLAlchemy查询对象
        user: 当前用户
        db: 数据库会话
    
    Returns:
        过滤后的查询对象
    """
    from models import TestCase
    
    if is_super_admin(user):
        return query
    
    # 组织负责人：直接按管理的组织过滤，不受 content_permissions 限制
    managed_dept_ids = get_managed_department_ids(user, db)
    if managed_dept_ids:
        org_project_ids = get_organization_project_ids(managed_dept_ids, db)
        if org_project_ids:
            return query.filter(TestCase.primary_project_id.in_(org_project_ids))
        return query.filter(TestCase.id == -1)
    
    permission_level = get_user_content_permission(user, 'testcase', db)
    project_ids = get_accessible_project_ids(user, 'testcase', db)
    
    if permission_level == 'personal':
        # 仅个人：个人创建的用例
        org_ids = get_user_organization_ids(user, db)
        if org_ids:
            org_project_ids = get_organization_project_ids(org_ids, db)
            if org_project_ids:
                # 个人创建的，且在组织范围内
                query = query.filter(
                    TestCase.created_by == user.id,
                    TestCase.primary_project_id.in_(org_project_ids)
                )
            else:
                query = query.filter(TestCase.created_by == user.id)
        else:
            query = query.filter(TestCase.created_by == user.id)
    elif project_ids is not None:
        if project_ids:
            query = query.filter(TestCase.primary_project_id.in_(project_ids))
        else:
            # 空集合，返回空结果
            query = query.filter(TestCase.id == -1)
    
    return query


def apply_testplan_data_permission(query, user: User, db: Session):
    """
    对测试计划查询应用数据权限过滤
    
    Args:
        query: SQLAlchemy查询对象
        user: 当前用户
        db: 数据库会话
    
    Returns:
        过滤后的查询对象
    """
    from models import TestPlan, TestPlanExecutor, TestPlanViewer
    
    logger.info(f"[testplan_perm] user={user.username}(id={user.id})")
    
    if is_super_admin(user):
        logger.info(f"[testplan_perm] super admin, no filter")
        return query
    
    # 组织负责人：直接按管理的组织过滤，不受 content_permissions 限制
    managed_dept_ids = get_managed_department_ids(user, db)
    if managed_dept_ids:
        org_project_ids = get_organization_project_ids(managed_dept_ids, db)
        logger.info(f"[testplan_perm] dept manager, managed_dept_ids={managed_dept_ids}, org_project_ids={org_project_ids}")
        if org_project_ids:
            return query.filter(TestPlan.project_id.in_(org_project_ids))
        return query.filter(TestPlan.id == -1)
    
    permission_level = get_user_content_permission(user, 'testplan', db)
    project_ids = get_accessible_project_ids(user, 'testplan', db)
    logger.info(f"[testplan_perm] permission_level={permission_level}, project_ids={project_ids}")
    
    if permission_level == 'personal':
        # 仅个人：个人创建的 或 被分配为执行人/查看人的测试计划
        executor_plan_ids = db.query(TestPlanExecutor.test_plan_id).filter(
            TestPlanExecutor.executor_id == user.id
        ).distinct()
        viewer_plan_ids = db.query(TestPlanViewer.test_plan_id).filter(
            TestPlanViewer.viewer_id == user.id
        ).distinct()
        
        personal_filter = or_(
            TestPlan.created_by == user.id,
            TestPlan.id.in_(executor_plan_ids),
            TestPlan.id.in_(viewer_plan_ids)
        )
        
        # 限制在组织范围内
        org_ids = get_user_organization_ids(user, db)
        if org_ids:
            org_project_ids = get_organization_project_ids(org_ids, db)
            if org_project_ids:
                query = query.filter(
                    personal_filter,
                    TestPlan.project_id.in_(org_project_ids)
                )
            else:
                query = query.filter(personal_filter)
        else:
            query = query.filter(personal_filter)
    elif project_ids is not None:
        if project_ids:
            query = query.filter(TestPlan.project_id.in_(project_ids))
        else:
            query = query.filter(TestPlan.id == -1)
    # project_ids is None 表示不限制
    
    return query


def apply_task_overview_data_permission(query, user: User, db: Session):
    """
    对任务总览查询应用数据权限过滤

    TaskOverview 必填 team_id（project_id 为可选且前端未传，通常为 NULL），
    因此权限过滤基于 team_id 而非 project_id。

    权限规则与测试计划保持一致：
    - 超级管理员：不限制
    - 组织负责人：只看管辖组织下所有项目组的任务总览
    - all 权限：用户所属组织下全部项目组的任务总览
    - project 权限：用户直属项目组的任务总览
    - personal 权限：创建人是自己 OR 被指定为查看人（TaskOverviewViewer）

    Args:
        query: SQLAlchemy查询对象（针对 TaskOverview 模型）
        user: 当前用户
        db: 数据库会话

    Returns:
        过滤后的查询对象
    """
    from models import TaskOverview, TaskOverviewViewer

    logger.info(f"[task_overview_perm] user={user.username}(id={user.id})")

    if is_super_admin(user):
        logger.info(f"[task_overview_perm] super admin, no filter")
        return query

    # 组织负责人：看管辖组织下所有项目组的任务总览
    managed_dept_ids = get_managed_department_ids(user, db)
    if managed_dept_ids:
        managed_teams = db.query(Team).filter(Team.department_id.in_(managed_dept_ids)).all()
        managed_team_ids = {t.id for t in managed_teams}
        logger.info(f"[task_overview_perm] dept manager, managed_dept_ids={managed_dept_ids}, team_ids={managed_team_ids}")
        if managed_team_ids:
            return query.filter(TaskOverview.team_id.in_(managed_team_ids))
        return query.filter(TaskOverview.id == -1)

    permission_level = get_user_content_permission(user, 'testplan', db)
    logger.info(f"[task_overview_perm] permission_level={permission_level}")

    if permission_level == 'personal':
        # 仅个人：创建人是自己 OR 被指定为查看人
        viewer_overview_ids = db.query(TaskOverviewViewer.task_overview_id).filter(
            TaskOverviewViewer.viewer_id == user.id
        ).distinct()

        personal_filter = or_(
            TaskOverview.created_by == user.id,
            TaskOverview.id.in_(viewer_overview_ids)
        )

        # 限制在所属组织的项目组范围内
        org_ids = get_user_organization_ids(user, db)
        if org_ids:
            org_teams = db.query(Team).filter(Team.department_id.in_(org_ids)).all()
            org_team_ids = {t.id for t in org_teams}
            if org_team_ids:
                query = query.filter(
                    personal_filter,
                    TaskOverview.team_id.in_(org_team_ids)
                )
            else:
                query = query.filter(personal_filter)
        else:
            query = query.filter(personal_filter)

    elif permission_level == 'project':
        # 项目组可见：用户直属的项目组
        team_ids = get_user_team_ids(user, db)
        # 限制在组织范围内
        org_ids = get_user_organization_ids(user, db)
        if org_ids:
            org_teams = db.query(Team).filter(Team.department_id.in_(org_ids)).all()
            org_team_ids = {t.id for t in org_teams}
            team_ids = team_ids & org_team_ids if org_team_ids else team_ids
        if team_ids:
            query = query.filter(TaskOverview.team_id.in_(team_ids))
        else:
            query = query.filter(TaskOverview.id == -1)

    else:
        # all 权限：组织下全部项目组
        org_ids = get_user_organization_ids(user, db)
        if org_ids:
            org_teams = db.query(Team).filter(Team.department_id.in_(org_ids)).all()
            org_team_ids = {t.id for t in org_teams}
            if org_team_ids:
                query = query.filter(TaskOverview.team_id.in_(org_team_ids))
            # org_team_ids 为空说明组织下暂无项目组，不限制，让用户看到数据

    return query


def apply_report_data_permission(query, user: User, db: Session):
    """
    对测试报告查询应用数据权限过滤
    
    Args:
        query: SQLAlchemy查询对象
        user: 当前用户
        db: 数据库会话
    
    Returns:
        过滤后的查询对象
    """
    from models import Report, TestPlan
    
    if is_super_admin(user):
        return query
    
    # 组织负责人：直接按管理的组织过滤，不受 content_permissions 限制
    managed_dept_ids = get_managed_department_ids(user, db)
    if managed_dept_ids:
        org_project_ids = get_organization_project_ids(managed_dept_ids, db)
        if org_project_ids:
            test_plan_ids = [tp.id for tp in db.query(TestPlan.id).filter(
                TestPlan.project_id.in_(org_project_ids)
            ).all()]
            if test_plan_ids:
                return query.filter(Report.test_plan_id.in_(test_plan_ids))
        return query.filter(Report.id == -1)
    
    permission_level = get_user_content_permission(user, 'report', db)
    project_ids = get_accessible_project_ids(user, 'report', db)
    
    if permission_level == 'personal':
        # 仅个人：个人创建的报告，限制在组织范围内
        org_ids = get_user_organization_ids(user, db)
        if org_ids:
            org_project_ids = get_organization_project_ids(org_ids, db)
            if org_project_ids:
                org_plan_ids = [tp.id for tp in db.query(TestPlan.id).filter(
                    TestPlan.project_id.in_(org_project_ids)
                ).all()]
                if org_plan_ids:
                    query = query.filter(
                        Report.created_by == user.id,
                        Report.test_plan_id.in_(org_plan_ids)
                    )
                else:
                    query = query.filter(Report.created_by == user.id)
            else:
                query = query.filter(Report.created_by == user.id)
        else:
            query = query.filter(Report.created_by == user.id)
    elif project_ids is not None:
        if project_ids:
            # Report 通过 test_plan_id 关联到 TestPlan，TestPlan 有 project_id
            # 获取这些项目下的测试计划ID
            test_plan_ids = db.query(TestPlan.id).filter(TestPlan.project_id.in_(project_ids)).all()
            test_plan_id_list = [tp.id for tp in test_plan_ids]
            if test_plan_id_list:
                query = query.filter(Report.test_plan_id.in_(test_plan_id_list))
            else:
                query = query.filter(Report.id == -1)
        else:
            query = query.filter(Report.id == -1)
    
    return query
