from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserTeam
from auth import get_current_user
from utils.logger import log_operation, LogAction, LogModule
from utils.permission_sync import sync_user_team_permissions, remove_user_team_permissions
from pydantic import BaseModel
from typing import List

router = APIRouter()

class AssignTeamsRequest(BaseModel):
    user_id: int
    team_ids: List[int]

@router.post("/assign")
def assign_teams(
    request: AssignTeamsRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为用户分配项目组"""
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 删除现有的项目组关联
    db.query(UserTeam).filter(UserTeam.user_id == request.user_id).delete()
    
    # 添加新的项目组关联
    for team_id in request.team_ids:
        user_team = UserTeam(
            user_id=request.user_id,
            team_id=team_id
        )
        db.add(user_team)
    
    db.commit()
    
    # 自动同步用户的项目组权限
    sync_user_team_permissions(request.user_id, db)
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.USERS,
        action=LogAction.UPDATE,
        description=f"为用户 {user.username} 分配项目组（共 {len(request.team_ids)} 个）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": None
    }

class RemoveMemberRequest(BaseModel):
    user_id: int
    team_id: int

@router.post("/remove-member")
def remove_member(
    request: RemoveMemberRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从项目组中移除成员"""
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 删除用户与项目组的关联
    deleted = db.query(UserTeam).filter(
        UserTeam.user_id == request.user_id,
        UserTeam.team_id == request.team_id
    ).delete()
    
    if deleted == 0:
        raise HTTPException(status_code=404, detail="该用户不在此项目组中")
    
    db.commit()
    
    # 移除用户从该项目组继承的用例库权限
    remove_user_team_permissions(request.user_id, request.team_id, db)
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.USERS,
        action=LogAction.UPDATE,
        description=f"将用户 {user.username} 从项目组中移除",
        request=req
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": None
    }

@router.get("/{user_id}")
def get_user_teams(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的项目组列表"""
    from models import Team
    
    user_teams = db.query(UserTeam).filter(UserTeam.user_id == user_id).all()
    team_ids = [ut.team_id for ut in user_teams]
    
    teams = []
    if team_ids:
        teams_data = db.query(Team).filter(Team.id.in_(team_ids)).all()
        teams = [
            {
                "id": team.id,
                "name": team.name
            }
            for team in teams_data
        ]
    
    return {
        "code": 200,
        "message": "success",
        "data": teams
    }
