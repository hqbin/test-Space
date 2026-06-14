from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import get_db
from auth import get_current_user
from models import User
from models_aivoice import AiVoiceProjectWorkspace, AiVoiceWorkspaceGroup, AiVoiceWorkspaceModule
from schemas_aivoice import AiVoiceProjectWorkspaceCreate, AiVoiceProjectWorkspaceUpdate, AiVoiceWorkspaceGroupCreate, AiVoiceWorkspaceGroupUpdate

router = APIRouter(prefix="/workspaces", tags=["工作区管理"])


@router.get("")
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspaces = db.query(AiVoiceProjectWorkspace).all()
    result = []
    for w in workspaces:
        groups = db.query(AiVoiceWorkspaceGroup).filter(AiVoiceWorkspaceGroup.workspaceId == w.id).all()
        result.append({
            "id": w.id,
            "name": w.name,
            "builtin": w.builtin or False,
            "groups": [{"id": g.id, "name": g.name, "projectType": g.projectType, "builtin": g.builtin or False} for g in groups],
            "createdAt": w.createdAt.isoformat() if w.createdAt else None,
            "updatedAt": w.updatedAt.isoformat() if w.updatedAt else None,
        })
    return {"code": 200, "message": "success", "data": result}


@router.post("")
def create_workspace(
    data: AiVoiceProjectWorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = AiVoiceProjectWorkspace(
        id=data.id,
        name=data.name,
        builtin=data.builtin or False,
        createdById=current_user.id,
    )
    db.add(ws)
    db.commit()
    return {"code": 200, "message": "success", "data": {"id": ws.id}}


@router.put("/{workspace_id}")
def update_workspace(
    workspace_id: str,
    data: AiVoiceProjectWorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = db.query(AiVoiceProjectWorkspace).filter(AiVoiceProjectWorkspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="工作区不存在")
    if data.name is not None:
        ws.name = data.name
    db.commit()
    return {"code": 200, "message": "更新成功"}


@router.delete("/{workspace_id}")
def delete_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = db.query(AiVoiceProjectWorkspace).filter(AiVoiceProjectWorkspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="工作区不存在")
    db.query(AiVoiceWorkspaceGroup).filter(AiVoiceWorkspaceGroup.workspaceId == workspace_id).delete()
    db.query(AiVoiceWorkspaceModule).filter(AiVoiceWorkspaceModule.workspaceId == workspace_id).delete()
    db.delete(ws)
    db.commit()
    return {"code": 200, "message": "删除成功"}


@router.post("/{workspace_id}/groups")
def create_group(
    workspace_id: str,
    data: AiVoiceWorkspaceGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = AiVoiceWorkspaceGroup(
        id=data.id,
        workspaceId=workspace_id,
        name=data.name,
        projectType=data.projectType,
        builtin=data.builtin or False,
    )
    db.add(group)
    db.commit()
    return {"code": 200, "message": "success", "data": {"id": group.id}}


@router.put("/groups/{group_id}")
def update_group(
    group_id: str,
    data: AiVoiceWorkspaceGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.query(AiVoiceWorkspaceGroup).filter(AiVoiceWorkspaceGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    if data.name is not None:
        group.name = data.name
    if data.projectType is not None:
        group.projectType = data.projectType
    db.commit()
    return {"code": 200, "message": "更新成功"}


@router.delete("/groups/{group_id}")
def delete_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.query(AiVoiceWorkspaceGroup).filter(AiVoiceWorkspaceGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    db.delete(group)
    db.commit()
    return {"code": 200, "message": "删除成功"}
