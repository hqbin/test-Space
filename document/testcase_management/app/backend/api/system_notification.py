"""
系统通知API
用于管理员手动触发系统通知
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import get_current_user
from utils.permissions import is_admin
from pydantic import BaseModel
from typing import Optional, List
from services.system_notification_service import SystemNotificationService
from utils.logger import log_operation, LogAction, LogModule

router = APIRouter()


class MaintenanceNotificationRequest(BaseModel):
    start_time: str
    end_time: str
    reason: Optional[str] = "系统维护升级"


class FeatureReleaseRequest(BaseModel):
    feature_name: str
    description: str


class VersionUpdateRequest(BaseModel):
    version: str
    changelog: str


@router.post("/maintenance")
def send_maintenance_notification(
    request: MaintenanceNotificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送系统维护通知（仅管理员）"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="仅管理员可以发送系统通知")
    
    service = SystemNotificationService(db)
    notification_id = service.send_maintenance_notification(
        start_time=request.start_time,
        end_time=request.end_time,
        reason=request.reason
    )
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.CREATE,
        description=f"发送系统维护通知"
    )
    
    return {
        "code": 200,
        "message": "系统维护通知已发送",
        "data": {"notification_id": notification_id}
    }


@router.post("/feature-release")
def send_feature_release_notification(
    request: FeatureReleaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送新功能上线通知（仅管理员）"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="仅管理员可以发送系统通知")
    
    service = SystemNotificationService(db)
    notification_id = service.send_feature_release_notification(
        feature_name=request.feature_name,
        description=request.description
    )
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.CREATE,
        description=f"发送新功能上线通知：{request.feature_name}"
    )
    
    return {
        "code": 200,
        "message": "新功能上线通知已发送",
        "data": {"notification_id": notification_id}
    }


@router.post("/version-update")
def send_version_update_notification(
    request: VersionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送版本更新通知（仅管理员）"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="仅管理员可以发送系统通知")
    
    service = SystemNotificationService(db)
    notification_id = service.send_version_update_notification(
        version=request.version,
        changelog=request.changelog
    )
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.CREATE,
        description=f"发送版本更新通知：{request.version}"
    )
    
    return {
        "code": 200,
        "message": "版本更新通知已发送",
        "data": {"notification_id": notification_id}
    }


@router.post("/backup-completed")
def send_backup_completed_notification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送数据备份完成通知（仅管理员）"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="仅管理员可以发送系统通知")
    
    from datetime import datetime
    service = SystemNotificationService(db)
    backup_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    notification_id = service.send_backup_completed_notification(
        backup_time=backup_time,
        status="成功"
    )
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.CREATE,
        description=f"发送数据备份完成通知"
    )
    
    return {
        "code": 200,
        "message": "数据备份完成通知已发送",
        "data": {"notification_id": notification_id}
    }
