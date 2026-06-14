"""
权限检查工具函数
"""
from sqlalchemy.orm import Session
from models import User, UserProject

def is_admin(user: User) -> bool:
    """检查用户是否是管理员"""
    return user.username in ('admin', 'super')

def has_project_access(user: User, project_id: int, db: Session) -> bool:
    """检查用户是否有项目访问权限"""
    # 管理员拥有所有权限
    if is_admin(user):
        return True
    
    # 检查用户是否被授权该项目
    user_project = db.query(UserProject).filter(
        UserProject.user_id == user.id,
        UserProject.project_id == project_id
    ).first()
    
    return user_project is not None

def get_user_project_ids(user: User, db: Session) -> list:
    """
    获取用户有权限的项目ID列表
    
    优先级：超级管理员 > 组织负责人 > content_permissions（PositionTag）
    """
    from utils.data_permission import (
        get_user_content_permission, get_user_organization_ids,
        get_organization_project_ids, get_user_team_ids, get_team_project_ids,
        get_managed_department_ids
    )
    
    # 管理员返回None表示所有项目
    if is_admin(user):
        return None
    
    # 组织负责人：看管理的所有组织下的全部用例库（不受 content_permissions 限制）
    managed_dept_ids = get_managed_department_ids(user, db)
    if managed_dept_ids:
        project_ids = get_organization_project_ids(managed_dept_ids, db)
        return list(project_ids)
    
    # 非组织负责人：按 content_permissions 配置
    permission_level = get_user_content_permission(user, 'testcase', db)
    
    if permission_level == 'all':
        # 组织可见：组织下所有用例库
        org_ids = get_user_organization_ids(user, db)
        if org_ids:
            project_ids = get_organization_project_ids(org_ids, db)
            return list(project_ids) if project_ids else []
        # 没有组织，回退到项目组的用例库
        team_ids = get_user_team_ids(user, db)
        return list(get_team_project_ids(team_ids, db))
    
    elif permission_level in ('project', 'personal'):
        # 项目组可见 / 仅个人：用户直接所属项目组的用例库
        team_ids = get_user_team_ids(user, db)
        project_ids = get_team_project_ids(team_ids, db)
        # 不能超出组织范围
        org_ids = get_user_organization_ids(user, db)
        if org_ids:
            org_project_ids = get_organization_project_ids(org_ids, db)
            if org_project_ids:
                project_ids = project_ids & org_project_ids
        return list(project_ids)
    
    return None


def is_executor(user_id: int, testplan_id: int, db: Session) -> bool:
    """
    检查用户是否为测试计划的执行人
    
    Args:
        user_id: 用户ID
        testplan_id: 测试计划ID
        db: 数据库会话
    
    Returns:
        bool: 是否为执行人
    """
    from models import TestPlanExecutor, User
    
    # 检查是否为超级管理员
    user = db.query(User).filter(User.id == user_id).first()
    if user and is_admin(user):
        return True
    
    # 检查是否为测试计划的执行人
    executor = db.query(TestPlanExecutor).filter(
        TestPlanExecutor.test_plan_id == testplan_id,
        TestPlanExecutor.executor_id == user_id
    ).first()
    
    return executor is not None


def require_executor(func):
    """
    执行人权限装饰器
    
    用于API端点，确保只有测试计划的执行人才能执行操作
    """
    from functools import wraps
    from fastapi import HTTPException, status
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 从kwargs中获取必要的参数
        current_user = kwargs.get('current_user')
        db = kwargs.get('db')
        
        # 尝试从不同的参数中获取testplan_id
        testplan_id = kwargs.get('testplan_id') or kwargs.get('test_plan_id')
        
        # 如果从路径参数中获取
        if not testplan_id and 'test_plan_id' in kwargs:
            testplan_id = kwargs['test_plan_id']
        
        # 如果从请求体中获取
        if not testplan_id:
            request_body = kwargs.get('execution_data') or kwargs.get('request_data')
            if request_body and hasattr(request_body, 'test_plan_id'):
                testplan_id = request_body.test_plan_id
        
        if not testplan_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法确定测试计划ID"
            )
        
        if not current_user or not db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未授权"
            )
        
        # 检查权限
        if not is_executor(current_user.id, testplan_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有测试计划的执行人才能执行此操作"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper


def can_delete_comment(user: User, comment_author_id: int) -> bool:
    """
    检查用户是否可以删除评论
    
    规则：只有管理员可以删除评论
    
    Args:
        user: 当前用户
        comment_author_id: 评论作者ID
    
    Returns:
        bool: 是否可以删除
    """
    return is_admin(user)


def can_delete_attachment(user: User, attachment_uploader_id: int, db: Session) -> bool:
    """
    检查用户是否可以删除附件
    
    规则：管理员或上传者本人可以删除
    
    Args:
        user: 当前用户
        attachment_uploader_id: 附件上传者ID
        db: 数据库会话
    
    Returns:
        bool: 是否可以删除
    """
    return is_admin(user) or user.id == attachment_uploader_id


def check_permission(user, permission: str) -> bool:
    """
    检查用户是否有特定权限
    
    超级管理员拥有所有权限
    
    Args:
        user: 当前用户（User对象或dict）
        permission: 权限标识符，如 "amlPatch.create"
    
    Returns:
        bool: 是否有权限
    """
    import logging
    from database import SessionLocal
    from models import User, UserRole, Role
    import json
    
    logger = logging.getLogger(__name__)
    
    if not user:
        return False
    
    if hasattr(user, 'username'):
        username = user.username
    else:
        username = user.get("username", "")
    
    logger.info(f"Checking permission for user: {username}, permission: {permission}")
    
    SUPER_ADMINS = ["admin"]
    
    if username in SUPER_ADMINS:
        logger.info("User is super admin")
        return True
    
    db = SessionLocal()
    try:
        user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
        role_ids = [ur.role_id for ur in user_roles]
        
        if not role_ids:
            logger.info("User has no roles")
            return False
        
        roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
        user_permissions = []
        for role in roles:
            if role.permissions:
                try:
                    perms = json.loads(role.permissions)
                    user_permissions.extend(perms)
                except:
                    pass
        
        user_permissions = list(set(user_permissions))
        logger.info(f"User permissions from roles: {user_permissions}")
        
        if permission in user_permissions:
            logger.info("Permission granted")
            return True
        
        logger.info("Permission denied")
        return False
    finally:
        db.close()
