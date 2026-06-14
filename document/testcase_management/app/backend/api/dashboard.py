"""
工作台统计API - 根据测试执行情况提供数据
支持角色权限和项目组双重权限控制
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from database import get_db
from models import User, TestCase, TestPlan, TestExecution, TestPlanTestCase, TestPlanExecutor, Project, UserProject, UserTeam, Team, TeamProject, Notification, NotificationRecipient, ReviewPlan, ReviewPlanTestCase
from auth import get_current_user
from utils.data_permission import is_super_admin
from datetime import datetime, timedelta
from typing import Optional
import json

router = APIRouter()


def get_user_role(db: Session, user: User) -> str:
    """获取用户角色类型"""
    if is_super_admin(user):
        return 'admin'
    
    from models import UserRole, Role
    user_role = db.query(UserRole).filter(UserRole.user_id == user.id).first()
    if user_role:
        role = db.query(Role).filter(Role.id == user_role.role_id).first()
        if role:
            role_name = role.name
            if '测试经理' in role_name or '经理' in role_name:
                return 'test_manager'
            elif '组长' in role_name:
                return 'test_leader'
            elif 'RD' in role_name or '开发' in role_name:
                return 'rd'
            elif 'PM' in role_name or '产品' in role_name:
                return 'pm'
    
    return 'tester'


def get_user_project_ids(db: Session, user: User) -> list:
    """获取用户可访问的项目ID列表"""
    user_projects = db.query(UserProject.project_id).filter(UserProject.user_id == user.id).all()
    return [up.project_id for up in user_projects]


def get_user_team_ids(db: Session, user: User) -> list:
    """获取用户所属的项目组ID列表"""
    user_teams = db.query(UserTeam.team_id).filter(UserTeam.user_id == user.id).all()
    return [ut.team_id for ut in user_teams]


def get_team_project_ids(db: Session, team_ids: list) -> list:
    """获取项目组关联的项目ID列表"""
    if not team_ids:
        return []
    team_projects = db.query(TeamProject.project_id).filter(TeamProject.team_id.in_(team_ids)).all()
    return [tp.project_id for tp in team_projects]


@router.get("/stats")
def get_dashboard_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取工作台统计数据
    根据用户角色和项目组权限返回不同的统计信息
    """
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    user_role = get_user_role(db, current_user)
    user_project_ids = get_user_project_ids(db, current_user)
    user_team_ids = get_user_team_ids(db, current_user)
    team_project_ids = get_team_project_ids(db, user_team_ids)
    
    accessible_project_ids = list(set(user_project_ids + team_project_ids))
    
    stats = {}
    
    stats['testplans'] = get_testplan_stats(db, current_user, user_role, accessible_project_ids, start_dt, end_dt)
    
    if user_role in ['tester', 'rd']:
        stats['my_progress'] = get_my_progress(db, current_user, accessible_project_ids)
        stats['todo'] = get_todo_list(db, current_user, accessible_project_ids)
        stats['defects'] = get_defect_stats(db, current_user, accessible_project_ids)
        stats['trend'] = get_execution_trend(db, current_user, accessible_project_ids, start_dt, end_dt)
        stats['my_testcases'] = get_my_testcases(db, current_user, accessible_project_ids)
    
    if user_role in ['test_leader', 'test_manager']:
        stats['project_progress'] = get_project_progress(db, current_user, user_team_ids, accessible_project_ids)
        stats['high_risk_defects'] = get_high_risk_defects(db, current_user, accessible_project_ids)
        stats['case_coverage'] = get_case_coverage(db, current_user, accessible_project_ids)
        stats['team_efficiency'] = get_team_efficiency(db, current_user, user_team_ids, start_dt, end_dt)
        stats['team_workload'] = get_team_workload(db, current_user, user_team_ids)
        stats['review_pending'] = get_review_pending(db, current_user, accessible_project_ids)
    
    if user_role == 'test_manager':
        stats['global_status'] = get_global_status(db, current_user, accessible_project_ids)
        stats['defect_trend'] = get_defect_trend(db, current_user, accessible_project_ids, start_dt, end_dt)
        stats['resource_load'] = get_resource_load(db, current_user)
    
    if user_role == 'admin':
        stats['global_status'] = get_global_status(db, current_user, None)
        stats['defect_trend'] = get_defect_trend(db, current_user, None, start_dt, end_dt)
        stats['resource_load'] = get_resource_load(db, current_user)
        stats['system_health'] = get_system_health(db)
        stats['team_workload'] = get_team_workload_admin(db)
    
    stats['notifications'] = get_notifications(db, current_user)
    
    if user_role in ['tester', 'rd']:
        stats['quick_actions'] = get_quick_actions(db, current_user, user_role)
    
    return {
        "code": 200,
        "message": "success",
        "data": stats
    }


def get_testplan_stats(db: Session, user: User, role: str, project_ids: list, start_dt: datetime, end_dt: datetime) -> dict:
    """获取测试计划统计"""
    query = db.query(TestPlan)
    
    if project_ids and role != 'admin':
        query = query.filter(TestPlan.project_id.in_(project_ids))
    
    if role not in ['admin', 'test_manager']:
        query = query.join(TestPlanExecutor).filter(TestPlanExecutor.executor_id == user.id)
    
    total = query.count()
    pending = query.filter(TestPlan.status == 'PENDING').count()
    in_progress = query.filter(TestPlan.status == 'IN_PROGRESS').count()
    in_review = query.filter(TestPlan.status == 'IN_REVIEW').count()
    completed = query.filter(TestPlan.status == 'COMPLETED').count()
    
    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'in_review': in_review,
        'completed': completed
    }


def get_my_progress(db: Session, user: User, project_ids: list) -> dict:
    """获取个人测试进度"""
    my_testplans = db.query(TestPlan.id).join(TestPlanExecutor).filter(
        TestPlanExecutor.executor_id == user.id
    )
    
    if project_ids:
        my_testplans = my_testplans.filter(TestPlan.project_id.in_(project_ids))
    
    my_testplan_ids = [tp.id for tp in my_testplans.all()]
    
    if not my_testplan_ids:
        return {'total': 0, 'executed': 0, 'rate': 0}
    
    total_cases = db.query(func.count(TestPlanTestCase.id)).filter(
        TestPlanTestCase.test_plan_id.in_(my_testplan_ids)
    ).scalar() or 0
    
    executed_cases = db.query(func.count(TestExecution.id.distinct())).filter(
        and_(
            TestExecution.test_plan_id.in_(my_testplan_ids),
            TestExecution.executor_id == user.id
        )
    ).scalar() or 0
    
    rate = round((executed_cases / total_cases * 100) if total_cases > 0 else 0, 1)
    
    return {
        'total': total_cases,
        'executed': executed_cases,
        'rate': rate
    }


def get_todo_list(db: Session, user: User, project_ids: list) -> dict:
    """获取待办任务列表"""
    my_testplans = db.query(TestPlan.id).join(TestPlanExecutor).filter(
        TestPlanExecutor.executor_id == user.id
    )
    
    if project_ids:
        my_testplans = my_testplans.filter(TestPlan.project_id.in_(project_ids))
    
    my_testplan_ids = [tp.id for tp in my_testplans.all()]
    
    if not my_testplan_ids:
        return {'count': 0, 'list': []}
    
    all_testcase_ids = db.query(TestPlanTestCase.test_case_id).filter(
        TestPlanTestCase.test_plan_id.in_(my_testplan_ids)
    ).all()
    all_testcase_ids = [tc.test_case_id for tc in all_testcase_ids]
    
    executed_testcase_ids = db.query(TestExecution.test_case_id.distinct()).filter(
        and_(
            TestExecution.test_plan_id.in_(my_testplan_ids),
            TestExecution.executor_id == user.id
        )
    ).all()
    executed_testcase_ids = [tc[0] for tc in executed_testcase_ids]
    
    pending_testcase_ids = list(set(all_testcase_ids) - set(executed_testcase_ids))
    
    # 按模块sort_order → sort_order → case_number自然排序
    from utils.module_sort import build_module_sort_key_expr
    from sqlalchemy import text
    natural_sort = text("""
        LPAD(COALESCE(SUBSTRING(test_cases.case_number FROM '(\d+)$'), '0'), 20, '0')
    """)
    module_sort = build_module_sort_key_expr(db, project_ids)
    pending_cases = db.query(TestCase).filter(
        TestCase.id.in_(pending_testcase_ids)
    ).order_by(module_sort, TestCase.sort_order.asc(), natural_sort, TestCase.id.asc()).limit(10).all()
    
    return {
        'count': len(pending_testcase_ids),
        'list': [
            {
                'id': case.id,
                'case_number': case.case_number,
                'name': case.name,
                'level': case.level
            }
            for case in pending_cases
        ]
    }


def get_defect_stats(db: Session, user: User, project_ids: list) -> dict:
    """获取缺陷统计"""
    my_testplans = db.query(TestPlan.id).join(TestPlanExecutor).filter(
        TestPlanExecutor.executor_id == user.id
    )
    
    if project_ids:
        my_testplans = my_testplans.filter(TestPlan.project_id.in_(project_ids))
    
    my_testplan_ids = [tp.id for tp in my_testplans.all()]
    
    if not my_testplan_ids:
        return {'new': 0, 'fixed': 0}
    
    new_defects = db.query(func.count(TestExecution.id)).filter(
        and_(
            TestExecution.test_plan_id.in_(my_testplan_ids),
            TestExecution.executor_id == user.id,
            TestExecution.result == 'FAIL'
        )
    ).scalar() or 0
    
    passed_cases = db.query(func.count(TestExecution.id)).filter(
        and_(
            TestExecution.test_plan_id.in_(my_testplan_ids),
            TestExecution.executor_id == user.id,
            TestExecution.result == 'PASS'
        )
    ).scalar() or 0
    
    return {
        'new': new_defects,
        'fixed': passed_cases
    }


def get_execution_trend(db: Session, user: User, project_ids: list, start_dt: datetime, end_dt: datetime) -> dict:
    """获取执行趋势数据"""
    my_testplans = db.query(TestPlan.id).join(TestPlanExecutor).filter(
        TestPlanExecutor.executor_id == user.id
    )
    
    if project_ids:
        my_testplans = my_testplans.filter(TestPlan.project_id.in_(project_ids))
    
    my_testplan_ids = [tp.id for tp in my_testplans.all()]
    
    if not my_testplan_ids:
        return {'dates': [], 'values': [], 'current': 0, 'change': 0}
    
    dates = []
    values = []
    
    current_dt = start_dt
    while current_dt <= end_dt:
        date_str = current_dt.strftime('%Y-%m-%d')
        dates.append(date_str)
        
        day_executions = db.query(func.count(TestExecution.id)).filter(
            and_(
                TestExecution.test_plan_id.in_(my_testplan_ids),
                TestExecution.executor_id == user.id,
                func.date(TestExecution.executed_at) == current_dt.date()
            )
        ).scalar() or 0
        
        values.append(day_executions)
        current_dt += timedelta(days=1)
    
    current_rate = values[-1] if values else 0
    previous_rate = values[-8] if len(values) >= 8 else (values[0] if values else 0)
    change = round(((current_rate - previous_rate) / previous_rate * 100) if previous_rate > 0 else 0, 1)
    
    return {
        'dates': dates,
        'values': values,
        'current': current_rate,
        'change': change
    }


def get_my_testcases(db: Session, user: User, project_ids: list) -> dict:
    """获取我的用例统计"""
    query = db.query(TestCase)
    
    if project_ids:
        query = query.filter(TestCase.primary_project_id.in_(project_ids))
    
    created = query.filter(TestCase.created_by == user.id).count()
    updated = query.filter(TestCase.updated_by == user.id).count()
    pending_review = query.filter(
        and_(
            TestCase.created_by == user.id,
            TestCase.status == 'PENDING'
        )
    ).count()
    
    return {
        'created': created,
        'updated': updated,
        'pending_review': pending_review
    }


def get_project_progress(db: Session, user: User, team_ids: list, project_ids: list) -> dict:
    """获取项目进度"""
    query = db.query(TestPlan)
    
    if project_ids:
        query = query.filter(TestPlan.project_id.in_(project_ids))
    
    testplans = query.all()
    
    if not testplans:
        return {'rate': 0, 'remaining_days': 0}
    
    completion_rates = []
    for tp in testplans:
        total = db.query(func.count(TestPlanTestCase.id)).filter(
            TestPlanTestCase.test_plan_id == tp.id
        ).scalar() or 0
        
        executed = db.query(func.count(TestExecution.id.distinct())).filter(
            TestExecution.test_plan_id == tp.id
        ).scalar() or 0
        
        if total > 0:
            completion_rates.append((executed / total) * 100)
    
    avg_rate = round(sum(completion_rates) / len(completion_rates) if completion_rates else 0, 1)
    
    remaining_days = 0
    active_testplans = [tp for tp in testplans if tp.status in ['PENDING', 'IN_PROGRESS'] and tp.end_time]
    if active_testplans:
        end_dates = [tp.end_time for tp in active_testplans if tp.end_time]
        if end_dates:
            max_end = max(end_dates)
            remaining_days = max(0, (max_end - datetime.now()).days)
    
    return {
        'rate': avg_rate,
        'remaining_days': remaining_days
    }


def get_high_risk_defects(db: Session, user: User, project_ids: list) -> dict:
    """获取高风险缺陷"""
    query = db.query(TestExecution).filter(TestExecution.result == 'FAIL')
    
    if project_ids:
        query = query.join(TestPlan).filter(TestPlan.project_id.in_(project_ids))
    
    count = query.count()
    
    high_risk = query.limit(10).all()
    
    return {
        'count': count,
        'list': [
            {
                'id': f'DEF-{e.id}',
                'name': e.remarks or '执行失败',
                'testplan_id': e.test_plan_id
            }
            for e in high_risk
        ]
    }


def get_case_coverage(db: Session, user: User, project_ids: list) -> dict:
    """获取用例覆盖率"""
    query = db.query(TestCase)
    
    if project_ids:
        query = query.filter(TestCase.primary_project_id.in_(project_ids))
    
    total_cases = query.count()
    
    executed_query = db.query(TestExecution.test_case_id.distinct())
    if project_ids:
        executed_query = executed_query.join(TestPlan).filter(TestPlan.project_id.in_(project_ids))
    
    executed_cases = executed_query.count()
    
    coverage_rate = round((executed_cases / total_cases * 100) if total_cases > 0 else 0, 1)
    
    return {
        'current': coverage_rate,
        'target': 90,
        'gap': max(0, total_cases - executed_cases)
    }


def get_team_efficiency(db: Session, user: User, team_ids: list, start_dt: datetime, end_dt: datetime) -> dict:
    """获取团队效率"""
    if not team_ids:
        return {'avg_time': 0, 'pass_rate': 0, 'change': 0}
    
    team_members = db.query(UserTeam.user_id).filter(UserTeam.team_id.in_(team_ids)).all()
    member_ids = [tm.user_id for tm in team_members]
    
    if not member_ids:
        return {'avg_time': 0, 'pass_rate': 0, 'change': 0}
    
    executions = db.query(TestExecution).filter(
        and_(
            TestExecution.executor_id.in_(member_ids),
            TestExecution.executed_at >= start_dt,
            TestExecution.executed_at <= end_dt
        )
    ).all()
    
    if not executions:
        return {'avg_time': 0, 'pass_rate': 0, 'change': 0}
    
    passed = len([e for e in executions if e.result == 'PASS'])
    pass_rate = round((passed / len(executions) * 100), 1)
    
    return {
        'avg_time': 2.1,
        'pass_rate': pass_rate,
        'change': 0
    }


def get_team_workload(db: Session, user: User, team_ids: list) -> dict:
    """获取团队工作负载"""
    if not team_ids:
        return {'members': [], 'workloads': []}
    
    team_members = db.query(User).join(UserTeam).filter(
        UserTeam.team_id.in_(team_ids)
    ).all()
    
    members = []
    workloads = []
    
    for member in team_members:
        members.append(member.username)
        
        assigned_count = db.query(func.count(TestPlanTestCase.id)).join(TestPlan).join(
            TestPlanExecutor, TestPlanExecutor.test_plan_id == TestPlan.id
        ).filter(
            TestPlanExecutor.executor_id == member.id,
            TestPlan.status.in_(['PENDING', 'IN_PROGRESS'])
        ).scalar() or 0
        
        workloads.append(min(assigned_count * 10, 100))
    
    return {
        'members': members,
        'workloads': workloads
    }


def get_review_pending(db: Session, user: User, project_ids: list) -> dict:
    """获取待评审用例"""
    query = db.query(ReviewPlanTestCase).filter(
        ReviewPlanTestCase.review_status == 'PENDING'
    )
    
    if project_ids:
        query = query.join(ReviewPlan).filter(ReviewPlan.project_id.in_(project_ids))
    
    pending_cases = query.limit(10).all()
    
    count = query.count()
    
    return {
        'count': count,
        'list': [
            {
                'id': pc.id,
                'name': f'用例-{pc.testcase_id}',
                'reviewer': '待分配'
            }
            for pc in pending_cases
        ]
    }


def get_global_status(db: Session, user: User, project_ids: list) -> dict:
    """获取全局状态"""
    query = db.query(TestPlan)
    
    if project_ids:
        query = query.filter(TestPlan.project_id.in_(project_ids))
    
    project_count = query.filter(TestPlan.status.in_(['PENDING', 'IN_PROGRESS'])).count()
    
    testplans = query.all()
    completion_rates = []
    
    for tp in testplans:
        total = db.query(func.count(TestPlanTestCase.id)).filter(
            TestPlanTestCase.test_plan_id == tp.id
        ).scalar() or 0
        
        executed = db.query(func.count(TestExecution.id.distinct())).filter(
            TestExecution.test_plan_id == tp.id
        ).scalar() or 0
        
        if total > 0:
            completion_rates.append((executed / total) * 100)
    
    avg_completion = round(sum(completion_rates) / len(completion_rates) if completion_rates else 0, 1)
    
    return {
        'project_count': project_count,
        'avg_completion': avg_completion
    }


def get_defect_trend(db: Session, user: User, project_ids: list, start_dt: datetime, end_dt: datetime) -> dict:
    """获取缺陷趋势"""
    dates = []
    new_defects = []
    fixed_defects = []
    
    current_dt = start_dt
    while current_dt <= end_dt:
        date_str = current_dt.strftime('%Y-%m-%d')
        dates.append(date_str)
        
        fail_query = db.query(func.count(TestExecution.id)).filter(
            and_(
                TestExecution.result == 'FAIL',
                func.date(TestExecution.executed_at) == current_dt.date()
            )
        )
        
        pass_query = db.query(func.count(TestExecution.id)).filter(
            and_(
                TestExecution.result == 'PASS',
                func.date(TestExecution.executed_at) == current_dt.date()
            )
        )
        
        if project_ids:
            fail_query = fail_query.join(TestPlan).filter(TestPlan.project_id.in_(project_ids))
            pass_query = pass_query.join(TestPlan).filter(TestPlan.project_id.in_(project_ids))
        
        new_defects.append(fail_query.scalar() or 0)
        fixed_defects.append(pass_query.scalar() or 0)
        
        current_dt += timedelta(days=1)
    
    return {
        'dates': dates,
        'new_defects': new_defects,
        'fixed_defects': fixed_defects
    }


def get_resource_load(db: Session, user: User) -> dict:
    """获取资源负载"""
    active_testplans = db.query(TestPlan).filter(
        TestPlan.status.in_(['PENDING', 'IN_PROGRESS'])
    ).count()
    
    total_testplans = db.query(TestPlan).count() or 1
    env_usage = min(round((active_testplans / total_testplans) * 100, 1), 100)
    
    return {
        'env_usage': env_usage
    }


def get_system_health(db: Session) -> dict:
    """获取系统健康度"""
    return {
        'api_time': 200,
        'error_rate': 0.2
    }


def get_team_workload_admin(db: Session) -> dict:
    """管理员获取所有团队工作负载"""
    teams = db.query(Team).filter(Team.status == 1).limit(10).all()
    
    members = []
    workloads = []
    
    for team in teams:
        team_members = db.query(User).join(UserTeam).filter(
            UserTeam.team_id == team.id
        ).limit(5).all()
        
        for member in team_members:
            members.append(member.username)
            
            assigned_count = db.query(func.count(TestPlanTestCase.id)).join(TestPlan).join(
                TestPlanExecutor, TestPlanExecutor.test_plan_id == TestPlan.id
            ).filter(
                TestPlanExecutor.executor_id == member.id,
                TestPlan.status.in_(['PENDING', 'IN_PROGRESS'])
            ).scalar() or 0
            
            workloads.append(min(assigned_count * 10, 100))
    
    return {
        'members': members[:15],
        'workloads': workloads[:15]
    }


def get_notifications(db: Session, user: User) -> dict:
    """获取通知"""
    notifications = db.query(Notification).join(NotificationRecipient).filter(
        NotificationRecipient.user_id == user.id
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    unread_count = db.query(func.count(NotificationRecipient.id)).filter(
        and_(
            NotificationRecipient.user_id == user.id,
            NotificationRecipient.is_read == False
        )
    ).scalar() or 0
    
    return {
        'unread': unread_count,
        'list': [
            {
                'id': n.id,
                'title': n.title,
                'is_read': nr.is_read,
                'created_at': n.created_at.isoformat() if n.created_at else None
            }
            for n, nr in [(n, db.query(NotificationRecipient).filter(
                and_(
                    NotificationRecipient.notification_id == n.id,
                    NotificationRecipient.user_id == user.id
                )
            ).first()) for n in notifications]
        ]
    }


def get_quick_actions(db: Session, user: User, role: str) -> dict:
    """获取快捷操作"""
    actions = []
    
    if role == 'tester':
        actions = [
            {'name': '新建用例', 'path': '/testcases'},
            {'name': '开始执行', 'path': '/executions'},
            {'name': '查看报告', 'path': '/reports'}
        ]
    elif role == 'rd':
        actions = [
            {'name': '查看缺陷', 'path': '/executions'},
            {'name': '我的用例', 'path': '/testcases'}
        ]
    
    return {'actions': actions}
