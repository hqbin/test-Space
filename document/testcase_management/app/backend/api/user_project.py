from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User, Project, UserProject
from auth import get_current_user
from typing import List
from pydantic import BaseModel
from utils.permissions import is_admin
from utils.logger import log_operation, LogAction, LogModule

router = APIRouter()

class UserProjectAssign(BaseModel):
    user_id: int
    project_ids: List[int]

@router.get("/user/{user_id}/projects")
def get_user_projects(
    req: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户被授权的项目列表（树形结构）"""
    from api.project import get_project_tree_recursive
    
    # 查询用户的项目授权
    user_projects = db.query(UserProject).filter(UserProject.user_id == user_id).all()
    project_ids = [up.project_id for up in user_projects]
    
    if not project_ids:
        return {"code": 200, "message": "success", "data": []}
    
    # 获取授权的项目
    authorized_projects = db.query(Project).filter(
        Project.id.in_(project_ids),
        Project.status == 1
    ).all()
    
    # 收集所有需要显示的项目ID（包括父节点）
    all_project_ids = set(project_ids)
    for project in authorized_projects:
        # 添加所有父节点
        if project.parent_id:
            parent = db.query(Project).filter(Project.id == project.parent_id).first()
            while parent:
                all_project_ids.add(parent.id)
                if parent.parent_id:
                    parent = db.query(Project).filter(Project.id == parent.parent_id).first()
                else:
                    break
    
    # 获取所有需要显示的项目
    projects = db.query(Project).filter(
        Project.id.in_(all_project_ids),
        Project.status == 1
    ).order_by(Project.level, Project.id).all()
    
    # 构建树形结构
    tree = get_project_tree_recursive(db, projects, None)
    
    return {
        "code": 200,
        "message": "success",
        "data": tree
    }

@router.get("/my-projects")
def get_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户被授权的项目列表（树形结构）- 遵循权限优先级"""
    from api.project import get_project_tree_recursive
    from utils.data_permission import (
        get_user_content_permission, get_user_organization_ids,
        get_organization_project_ids, get_user_team_ids, get_team_project_ids,
        get_managed_department_ids
    )
    
    # 管理员返回所有启用的项目
    if is_admin(current_user):
        projects = db.query(Project).filter(Project.status == 1).order_by(Project.level, Project.id).all()
    else:
        # 组织负责人：看管理的所有组织下的全部用例库
        managed_dept_ids = get_managed_department_ids(current_user, db)
        if managed_dept_ids:
            all_project_ids = get_organization_project_ids(managed_dept_ids, db)
        else:
            # 非组织负责人：按 content_permissions 配置
            permission_level = get_user_content_permission(current_user, 'testcase', db)
            
            if permission_level == 'all':
                org_ids = get_user_organization_ids(current_user, db)
                if org_ids:
                    all_project_ids = get_organization_project_ids(org_ids, db)
                else:
                    team_ids = get_user_team_ids(current_user, db)
                    all_project_ids = get_team_project_ids(team_ids, db)
            elif permission_level in ('project', 'personal'):
                team_ids = get_user_team_ids(current_user, db)
                all_project_ids = get_team_project_ids(team_ids, db)
                org_ids = get_user_organization_ids(current_user, db)
                if org_ids:
                    org_project_ids = get_organization_project_ids(org_ids, db)
                    if org_project_ids:
                        all_project_ids = all_project_ids & org_project_ids
            else:
                all_project_ids = set()
        
        if not all_project_ids:
            return {"code": 200, "message": "success", "data": []}
        
        # 获取授权的项目
        authorized_projects = db.query(Project).filter(
            Project.id.in_(all_project_ids),
            Project.status == 1
        ).all()
        
        # 收集所有需要显示的项目ID（包括父节点）
        all_display_ids = set(all_project_ids)
        for project in authorized_projects:
            # 添加所有父节点
            if project.parent_id:
                parent = db.query(Project).filter(Project.id == project.parent_id).first()
                while parent:
                    all_display_ids.add(parent.id)
                    if parent.parent_id:
                        parent = db.query(Project).filter(Project.id == parent.parent_id).first()
                    else:
                        break
        
        # 获取所有需要显示的项目
        projects = db.query(Project).filter(
            Project.id.in_(all_display_ids),
            Project.status == 1
        ).order_by(Project.level, Project.id).all()
    
    # 构建树形结构
    tree = get_project_tree_recursive(db, projects, None)
    
    return {
        "code": 200,
        "message": "success",
        "data": tree
    }

@router.post("/assign")
def assign_projects_to_user(
    req: Request,
    assignment: UserProjectAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为用户分配项目"""
    # 检查用户是否存在
    user = db.query(User).filter(User.id == assignment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 删除用户现有的项目授权
    db.query(UserProject).filter(UserProject.user_id == assignment.user_id).delete()
    
    # 添加新的项目授权
    project_names = []
    for project_id in assignment.project_ids:
        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            continue
        
        user_project = UserProject(
            user_id=assignment.user_id,
            project_id=project_id
        )
        db.add(user_project)
        project_names.append(project.name)
    
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.USER_PROJECTS,
        action=LogAction.ASSIGN,
        description=f"为用户 {user.username}（ID: {assignment.user_id}）分配项目：{', '.join(project_names)}",
        request=req
    )
    
    return {
        "code": 200,
        "message": "授权成功",
        "data": None
    }

@router.delete("/user/{user_id}/project/{project_id}")
def remove_project_from_user(
    req: Request,
    user_id: int,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """移除用户的项目授权"""
    user_project = db.query(UserProject).filter(
        UserProject.user_id == user_id,
        UserProject.project_id == project_id
    ).first()
    
    if not user_project:
        raise HTTPException(status_code=404, detail="授权不存在")
    
    user = db.query(User).filter(User.id == user_id).first()
    project = db.query(Project).filter(Project.id == project_id).first()
    
    db.delete(user_project)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.USER_PROJECTS,
        action=LogAction.DELETE,
        description=f"移除用户 {user.username if user else user_id} 的项目授权：{project.name if project else project_id}",
        request=req
    )
    
    return {
        "code": 200,
        "message": "移除成功",
        "data": None
    }
