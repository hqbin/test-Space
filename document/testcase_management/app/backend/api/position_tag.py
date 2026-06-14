from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import PositionTag, User
from auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
import json
from utils.logger import log_operation, LogAction, LogModule

router = APIRouter()

class PositionTagCreate(BaseModel):
    name: str
    description: Optional[str] = None
    content_permissions: Optional[List[str]] = []
    notification_permissions: Optional[List[str]] = []

class PositionTagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content_permissions: Optional[List[str]] = None
    notification_permissions: Optional[List[str]] = None

@router.get("")
def list_position_tags(
    req: Request,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据权限列表"""
    total = db.query(PositionTag).count()
    tags = db.query(PositionTag).order_by(PositionTag.id.asc()).offset((page - 1) * size).limit(size).all()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "records": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "content_permissions": json.loads(t.content_permissions) if t.content_permissions else [],
                    "notification_permissions": json.loads(t.notification_permissions) if t.notification_permissions else [],
                    "is_system": t.is_system if hasattr(t, 'is_system') else False,
                    "created_at": t.created_at
                } for t in tags
            ],
            "total": total
        }
    }

@router.post("")
def create_position_tag(
    req: Request,
    tag: PositionTagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建数据权限"""
    # 检查名称是否已存在
    existing = db.query(PositionTag).filter(PositionTag.name == tag.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="数据权限名称已存在")
    
    db_tag = PositionTag(
        name=tag.name,
        description=tag.description,
        content_permissions=json.dumps(tag.content_permissions) if tag.content_permissions else json.dumps([]),
        notification_permissions=json.dumps(tag.notification_permissions) if tag.notification_permissions else json.dumps([])
    )
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.POSITION_TAGS,
        action=LogAction.CREATE,
        description=f"创建数据权限：{db_tag.name}（ID: {db_tag.id}）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": {
            "id": db_tag.id,
            "name": db_tag.name,
            "description": db_tag.description,
            "content_permissions": json.loads(db_tag.content_permissions) if db_tag.content_permissions else [],
            "notification_permissions": json.loads(db_tag.notification_permissions) if db_tag.notification_permissions else []
        }
    }

@router.get("/{tag_id}")
def get_position_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据权限详情"""
    tag = db.query(PositionTag).filter(PositionTag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="数据权限不存在")
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": tag.id,
            "name": tag.name,
            "description": tag.description,
            "content_permissions": json.loads(tag.content_permissions) if tag.content_permissions else [],
            "notification_permissions": json.loads(tag.notification_permissions) if tag.notification_permissions else [],
            "is_system": tag.is_system if hasattr(tag, 'is_system') else False,
            "created_at": tag.created_at
        }
    }

@router.put("/{tag_id}")
def update_position_tag(
    req: Request,
    tag_id: int,
    tag: PositionTagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新数据权限"""
    db_tag = db.query(PositionTag).filter(PositionTag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="数据权限不存在")
    
    old_name = db_tag.name
    changes = []  # 记录变更内容
    
    if tag.name and tag.name != db_tag.name:
        # 检查新名称是否与其他数据权限冲突
        existing = db.query(PositionTag).filter(
            PositionTag.name == tag.name,
            PositionTag.id != tag_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="数据权限名称已存在")
        changes.append(f"名称: {db_tag.name} → {tag.name}")
        db_tag.name = tag.name
    
    if tag.description is not None and tag.description != db_tag.description:
        old_desc = db_tag.description or "(空)"
        new_desc = tag.description or "(空)"
        changes.append(f"描述: {old_desc} → {new_desc}")
        db_tag.description = tag.description
    
    if tag.content_permissions is not None:
        old_perms = json.loads(db_tag.content_permissions) if db_tag.content_permissions else []
        new_perms = tag.content_permissions
        if set(old_perms) != set(new_perms):
            changes.append(f"内容权限数量: {len(old_perms)} → {len(new_perms)}")
        db_tag.content_permissions = json.dumps(tag.content_permissions)
    
    if tag.notification_permissions is not None:
        old_perms = json.loads(db_tag.notification_permissions) if db_tag.notification_permissions else []
        new_perms = tag.notification_permissions
        if set(old_perms) != set(new_perms):
            changes.append(f"通知权限数量: {len(old_perms)} → {len(new_perms)}")
        db_tag.notification_permissions = json.dumps(tag.notification_permissions)
    
    db.commit()
    db.refresh(db_tag)
    
    # 只有在有实际变更时才记录日志
    if changes:
        change_detail = "；".join(changes)
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.POSITION_TAGS,
            action=LogAction.UPDATE,
            description=f"更新数据权限：{old_name}（ID: {tag_id}，{change_detail}）",
            request=req
        )
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": {
            "id": db_tag.id,
            "name": db_tag.name,
            "description": db_tag.description,
            "content_permissions": json.loads(db_tag.content_permissions) if db_tag.content_permissions else [],
            "notification_permissions": json.loads(db_tag.notification_permissions) if db_tag.notification_permissions else []
        }
    }

@router.delete("/{tag_id}")
def delete_position_tag(
    req: Request,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除数据权限"""
    db_tag = db.query(PositionTag).filter(PositionTag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="数据权限不存在")
    
    # 检查是否为系统预设
    if db_tag.is_system:
        raise HTTPException(status_code=400, detail="系统预设数据权限不能删除")
    
    # 检查是否有用户关联此数据权限
    user_count = db.query(User).filter(User.position_tag_id == tag_id).count()
    if user_count > 0:
        raise HTTPException(status_code=400, detail=f"该数据权限正在被 {user_count} 个用户使用，无法删除")
    
    tag_name = db_tag.name
    db.delete(db_tag)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.POSITION_TAGS,
        action=LogAction.DELETE,
        description=f"删除数据权限：{tag_name}（ID: {tag_id}）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }
