from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from models import Team, UserTeam, User, TeamProject, Project, Department, DepartmentManager, TeamLeader
from auth import get_current_user
from utils.logger import log_operation, LogAction, LogModule
from utils.permission_sync import sync_team_members_permissions
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

# 请求模型
class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None
    department_id: Optional[int] = None
    leader_ids: Optional[List[int]] = None

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None
    leader_ids: Optional[List[int]] = None

class AssignProjectsRequest(BaseModel):
    team_id: int
    project_ids: List[int]

@router.get("")
def list_teams(
    page: int = 1,
    size: int = 10,
    search: str = None,
    department_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目组列表"""
    query = db.query(Team)
    
    # 按组织筛选
    if department_id:
        query = query.filter(Team.department_id == department_id)
    
    # 搜索功能
    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Team.name.ilike(search_pattern),
                Team.description.ilike(search_pattern)
            )
        )
    
    total = query.count()
    teams = query.order_by(Team.id.asc()).offset((page - 1) * size).limit(size).all()
    
    team_list = []
    for team in teams:
        # 统计该项目组的成员数量
        member_count = db.query(UserTeam).filter(UserTeam.team_id == team.id).count()
        
        # 获取该项目组的用例库
        team_projects = db.query(TeamProject).filter(TeamProject.team_id == team.id).all()
        project_ids = [tp.project_id for tp in team_projects]
        project_names = []
        if project_ids:
            projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
            project_names = [p.name for p in projects]
        
        # 获取负责人信息
        leader_records = db.query(TeamLeader).filter(TeamLeader.team_id == team.id).all()
        leader_ids = [tl.user_id for tl in leader_records]
        leader_names = []
        if leader_ids:
            leaders = db.query(User).filter(User.id.in_(leader_ids)).all()
            leader_names = [l.username for l in leaders]
        
        team_dict = {
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "status": team.status,
            "department_id": team.department_id,
            "leader_ids": leader_ids,
            "leader_names": leader_names,
            "leader_name": '、'.join(leader_names) if leader_names else None,
            "member_count": member_count,
            "projectNames": project_names,
            "created_at": team.created_at
        }
        team_list.append(team_dict)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "records": team_list,
            "total": total
        }
    }

@router.post("")
def create_team(
    team: TeamCreate,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建项目组"""
    # 检查名称是否已存在
    existing_team = db.query(Team).filter(Team.name == team.name).first()
    if existing_team:
        raise HTTPException(status_code=400, detail="项目组名称已存在")
    
    db_team = Team(
        name=team.name,
        description=team.description,
        department_id=team.department_id,
        status=1,
        created_by=current_user.id
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    
    # 保存负责人关联
    leader_ids = team.leader_ids or []
    for uid in leader_ids:
        db.add(TeamLeader(team_id=db_team.id, user_id=uid))
    if leader_ids:
        db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.TEAMS,
        action=LogAction.CREATE,
        description=f"创建项目组：{db_team.name}（ID: {db_team.id}）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": db_team.id,
            "name": db_team.name,
            "description": db_team.description,
            "status": db_team.status,
            "leader_ids": leader_ids,
            "created_at": db_team.created_at
        }
    }

@router.put("/{team_id}")
def update_team(
    team_id: int,
    team: TeamUpdate,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新项目组"""
    db_team = db.query(Team).filter(Team.id == team_id).first()
    if not db_team:
        raise HTTPException(status_code=404, detail="项目组不存在")
    
    # 检查名称是否与其他项目组重复
    if team.name and team.name != db_team.name:
        existing = db.query(Team).filter(Team.name == team.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="项目组名称已存在")
    
    old_name = db_team.name
    changes = []
    
    if team.name is not None and team.name != db_team.name:
        changes.append(f"名称: {db_team.name} → {team.name}")
        db_team.name = team.name
    
    if team.description is not None and team.description != db_team.description:
        changes.append(f"描述: {db_team.description or '(空)'} → {team.description or '(空)'}")
        db_team.description = team.description
    
    if team.status is not None and team.status != db_team.status:
        status_map = {0: "禁用", 1: "启用"}
        changes.append(f"状态: {status_map.get(db_team.status, db_team.status)} → {status_map.get(team.status, team.status)}")
        db_team.status = team.status
    
    if team.leader_ids is not None:
        old_leaders = db.query(TeamLeader).filter(TeamLeader.team_id == team_id).all()
        old_leader_ids = sorted([tl.user_id for tl in old_leaders])
        new_leader_ids = sorted(team.leader_ids)
        if old_leader_ids != new_leader_ids:
            # 获取旧负责人名称
            old_names = []
            if old_leader_ids:
                old_users = db.query(User).filter(User.id.in_(old_leader_ids)).all()
                old_names = [u.username for u in old_users]
            # 获取新负责人名称
            new_names = []
            if new_leader_ids:
                new_users = db.query(User).filter(User.id.in_(new_leader_ids)).all()
                new_names = [u.username for u in new_users]
            changes.append(f"负责人: {'、'.join(old_names) or '(无)'} → {'、'.join(new_names) or '(无)'}")
            # 更新关联表
            db.query(TeamLeader).filter(TeamLeader.team_id == team_id).delete()
            for uid in new_leader_ids:
                db.add(TeamLeader(team_id=team_id, user_id=uid))
    
    db.commit()
    db.refresh(db_team)
    
    if changes:
        change_detail = "；".join(changes)
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.TEAMS,
            action=LogAction.UPDATE,
            description=f"更新项目组：{old_name}（ID: {team_id}，{change_detail}）",
            request=req
        )
    
    return {"code": 200, "message": "success", "data": db_team}

@router.delete("/{team_id}")
def delete_team(
    team_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除项目组"""
    from models import TestPlan, TestSuite, DingtalkBot, CaseTemplate, ReportTemplate, ReviewPlan

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="项目组不存在")
    
    # 检查是否有用户关联
    member_count = db.query(UserTeam).filter(UserTeam.team_id == team_id).count()
    if member_count > 0:
        raise HTTPException(status_code=400, detail=f"该项目组还有 {member_count} 个成员，无法删除")
    
    # 检查是否有关联的业务数据
    plan_count = db.query(TestPlan).filter(TestPlan.team_id == team_id).count()
    if plan_count > 0:
        raise HTTPException(status_code=400, detail=f"该项目组还有 {plan_count} 个测试计划，无法删除")

    suite_count = db.query(TestSuite).filter(TestSuite.team_id == team_id).count()
    if suite_count > 0:
        raise HTTPException(status_code=400, detail=f"该项目组还有 {suite_count} 个测试套件，无法删除")

    review_count = db.query(ReviewPlan).filter(ReviewPlan.team_id == team_id).count()
    if review_count > 0:
        raise HTTPException(status_code=400, detail=f"该项目组还有 {review_count} 个评审计划，无法删除")

    # 清理可安全删除的关联数据
    team_name = team.name
    db.query(TeamLeader).filter(TeamLeader.team_id == team_id).delete()
    db.query(TeamProject).filter(TeamProject.team_id == team_id).delete()
    db.query(DingtalkBot).filter(DingtalkBot.team_id == team_id).delete()
    db.query(CaseTemplate).filter(CaseTemplate.team_id == team_id).delete()
    db.query(ReportTemplate).filter(ReportTemplate.team_id == team_id).delete()
    
    # 删除项目组
    db.delete(team)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.TEAMS,
        action=LogAction.DELETE,
        description=f"删除项目组：{team_name}（ID: {team_id}）",
        request=req
    )
    
    return {"code": 200, "message": "success", "data": None}

@router.get("/{team_id}/members")
def get_team_members(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目组成员列表"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="项目组不存在")
    
    # 获取成员
    user_teams = db.query(UserTeam).filter(UserTeam.team_id == team_id).all()
    user_ids = [ut.user_id for ut in user_teams]
    
    members = []
    if user_ids:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        members = [
            {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email
            }
            for user in users
        ]
    
    return {
        "code": 200,
        "message": "success",
        "data": members
    }


@router.post("/assign-projects")
def assign_projects_to_team(
    request: AssignProjectsRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为项目组授权用例库"""
    team = db.query(Team).filter(Team.id == request.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="项目组不存在")
    
    # 删除现有的用例库授权
    db.query(TeamProject).filter(TeamProject.team_id == request.team_id).delete()
    
    # 添加新的用例库授权
    for project_id in request.project_ids:
        team_project = TeamProject(
            team_id=request.team_id,
            project_id=project_id
        )
        db.add(team_project)
    
    db.commit()
    
    # 自动同步项目组成员的用例库权限
    sync_team_members_permissions(request.team_id, db)
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.TEAMS,
        action=LogAction.UPDATE,
        description=f"为项目组 {team.name} 授权用例库（共 {len(request.project_ids)} 个）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": None
    }

@router.get("/my-teams", name="get_my_teams")
def get_my_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户被授权的项目组列表 - 遵循权限优先级"""
    from utils.data_permission import (
        get_user_content_permission, get_user_organization_ids,
        get_user_team_ids, get_managed_department_ids, is_super_admin
    )
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[my-teams] user={current_user.username}(id={current_user.id}), position_tag_id={current_user.position_tag_id}")
    
    # 超级管理员可以看到所有项目组
    if is_super_admin(current_user):
        teams = db.query(Team).filter(Team.status == 1).all()
        logger.info(f"[my-teams] super admin, returning all {len(teams)} teams")
    else:
        # 组织负责人：看管理的所有组织下的项目组（不受 content_permissions 限制）
        managed_dept_ids = get_managed_department_ids(current_user, db)
        logger.info(f"[my-teams] managed_dept_ids={managed_dept_ids}")
        if managed_dept_ids:
            teams = db.query(Team).filter(
                Team.department_id.in_(managed_dept_ids),
                Team.status == 1
            ).all()
            logger.info(f"[my-teams] dept manager, returning {len(teams)} teams")
        else:
            # 非组织负责人：按 content_permissions 配置
            permission_level = get_user_content_permission(current_user, 'testcase', db)
            org_ids = get_user_organization_ids(current_user, db)
            team_ids = get_user_team_ids(current_user, db)
            logger.info(f"[my-teams] permission_level={permission_level}, org_ids={org_ids}, team_ids={team_ids}")
            
            if permission_level == 'all':
                # 组织可见：组织下所有项目组
                if org_ids:
                    teams = db.query(Team).filter(
                        Team.department_id.in_(org_ids),
                        Team.status == 1
                    ).all()
                    logger.info(f"[my-teams] all+org, returning {len(teams)} teams")
                else:
                    # 用户没有分配组织，尝试返回其所属项目组
                    if team_ids:
                        teams = db.query(Team).filter(Team.id.in_(team_ids), Team.status == 1).all()
                        logger.info(f"[my-teams] all+no_org+teams, returning {len(teams)} teams")
                    else:
                        # 既没有组织也没有项目组
                        # 如果用户没有分配数据权限标签，说明管理员还未配置，返回空
                        if not current_user.position_tag_id:
                            logger.info(f"[my-teams] all+no_org+no_teams+no_tag, returning empty")
                            teams = []
                        else:
                            teams = db.query(Team).filter(Team.status == 1).all()
                            logger.info(f"[my-teams] all+no_org+no_teams, returning all {len(teams)} teams")
            elif permission_level in ('project', 'personal'):
                # 项目组可见 / 仅个人：用户直接所属项目组
                if not team_ids:
                    logger.info(f"[my-teams] {permission_level}+no_teams, returning empty")
                    return {"code": 200, "message": "success", "data": []}
                teams = db.query(Team).filter(Team.id.in_(team_ids), Team.status == 1).all()
                logger.info(f"[my-teams] {permission_level}+teams, returning {len(teams)} teams")
            else:
                teams = db.query(Team).filter(Team.status == 1).all()
                logger.info(f"[my-teams] unknown permission, returning all {len(teams)} teams")
    
    team_list = []
    for team in teams:
        # 获取该项目组的用例库数量
        project_count = db.query(TeamProject).filter(TeamProject.team_id == team.id).count()
        
        team_list.append({
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "project_count": project_count
        })
    
    return {
        "code": 200,
        "message": "success",
        "data": team_list
    }


@router.get("/{team_id}/projects")
def get_team_projects(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目组的用例库列表"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="项目组不存在")
    
    # 获取项目组的用例库
    team_projects = db.query(TeamProject).filter(TeamProject.team_id == team_id).all()
    project_ids = [tp.project_id for tp in team_projects]
    
    projects = []
    if project_ids:
        projects_data = db.query(Project).filter(Project.id.in_(project_ids)).all()
        projects = [
            {
                "id": project.id,
                "name": project.name
            }
            for project in projects_data
        ]
    
    return {
        "code": 200,
        "message": "success",
        "data": projects
    }


@router.get("/{team_id}/user-role")
def get_user_role_in_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户在项目组中的角色
    返回: member(普通成员), leader(项目组负责人), org_manager(组织负责人), admin(超级管理员)
    """
    from utils.data_permission import is_super_admin

    # 超级管理员
    if is_super_admin(current_user):
        return {
            "code": 200,
            "message": "success",
            "data": {
                "role": "admin",
                "team_id": team_id
            }
        }
    
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="项目组不存在")
    
    # 检查是否是项目组负责人
    is_leader = db.query(TeamLeader).filter(
        TeamLeader.team_id == team_id,
        TeamLeader.user_id == current_user.id
    ).first()
    if is_leader:
        return {
            "code": 200,
            "message": "success",
            "data": {
                "role": "leader",
                "team_id": team_id
            }
        }
    
    # 检查是否是组织负责人
    if team.department_id:
        is_org_manager = db.query(DepartmentManager).filter(
            DepartmentManager.department_id == team.department_id,
            DepartmentManager.user_id == current_user.id
        ).first()
        if is_org_manager:
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "role": "org_manager",
                    "team_id": team_id,
                    "department_id": team.department_id
                }
            }
    
    # 普通成员
    return {
        "code": 200,
        "message": "success",
        "data": {
            "role": "member",
            "team_id": team_id
        }
    }


@router.get("/{team_id}/available-members")
def get_available_members_for_selection(
    team_id: int,
    selection_type: str = "executor",  # executor, reviewer, viewer
    search: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取可选择的成员列表（所有选择类型均限制在当前项目组下）
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="项目组不存在")
    
    # 所有选择类型（执行人、审核人、查看人）都限制在当前项目组下
    user_teams = db.query(UserTeam).filter(UserTeam.team_id == team_id).all()
    user_ids = list(set([ut.user_id for ut in user_teams]))
    
    if not user_ids:
        return {"code": 200, "message": "success", "data": []}
    
    query = db.query(User).filter(User.id.in_(user_ids), User.status == 1)
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    users = query.all()
    return {
        "code": 200,
        "message": "success",
        "data": [
            {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email
            }
            for user in users
        ]
    }


@router.get("/by-project/{project_id}")
def get_team_by_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据用例库ID获取对应的项目组"""
    team_project = db.query(TeamProject).filter(TeamProject.project_id == project_id).first()
    if not team_project:
        return {
            "code": 200,
            "message": "success",
            "data": None
        }
    
    team = db.query(Team).filter(Team.id == team_project.team_id).first()
    if not team:
        return {
            "code": 200,
            "message": "success",
            "data": None
        }
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": team.id,
            "name": team.name
        }
    }
