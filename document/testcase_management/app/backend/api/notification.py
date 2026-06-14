"""
通知管理API
用户只能查看和标记自己的通知，不能发送通知
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from database import get_db
from models import User, Notification, NotificationRecipient
from auth import get_current_user
from pydantic import BaseModel
from typing import Optional
from services.notification_service import NotificationService
from utils.logger import log_operation, LogAction, LogModule

router = APIRouter()


@router.get("")
def get_notifications(
    req: Request,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    notification_type: Optional[str] = None,
    is_read: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的通知列表
    
    参数:
    - page: 页码
    - size: 每页数量
    - notification_type: 通知类型筛选 (testcase/testplan/execution/report)
    - is_read: 已读状态筛选 (true/false)
    """
    service = NotificationService(db)
    result = service.get_user_notifications(
        user_id=current_user.id,
        notification_type=notification_type,
        is_read=is_read,
        page=page,
        size=size
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": result
    }


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户未读通知数量"""
    service = NotificationService(db)
    count = service.get_unread_count(current_user.id)
    
    return {
        "code": 200,
        "message": "success",
        "data": {"count": count}
    }


@router.get("/preferences")
def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的通知偏好设置"""
    from models import UserNotificationPreference
    
    # 定义所有可用的通知事件类型
    notification_events = {
        'testcase': [
            {'event_type': 'created', 'label': '用例创建'},
            {'event_type': 'updated', 'label': '用例更新'},
            {'event_type': 'deleted', 'label': '用例删除'},
            {'event_type': 'review_invitation', 'label': '评审邀请'},
            {'event_type': 'review_submitted', 'label': '提交评审'},
            {'event_type': 'review_approved', 'label': '评审通过'},
            {'event_type': 'review_rejected', 'label': '评审拒绝'},
            {'event_type': 'review_commented', 'label': '评审意见'},
            {'event_type': 'referenced', 'label': '用例被引用'},
        ],
        'testplan': [
            {'event_type': 'assigned', 'label': '测试计划分配'},
            {'event_type': 'completed', 'label': '测试计划完成'},
            {'event_type': 'status_changed', 'label': '状态变更'},
            {'event_type': 'deadline_warning', 'label': '即将到期提醒'},
            {'event_type': 'deadline_extended', 'label': '延期通知'},
            {'event_type': 'reminder', 'label': '执行提醒'},
            {'event_type': 'progress_warning', 'label': '进度落后警告'},
            {'event_type': 'member_changed', 'label': '成员变更'},
            {'event_type': 'paused', 'label': '计划暂停'},
            {'event_type': 'reassigned', 'label': '重新分配'},
            {'event_type': 'collaboration_request', 'label': '协作请求'},
        ],
        'execution': [
            {'event_type': 'defect_created', 'label': '新缺陷创建'},
            {'event_type': 'defect_fixed', 'label': '缺陷已修复'},
            {'event_type': 'defect_closed', 'label': '缺陷已关闭'},
            {'event_type': 'defect_rejected', 'label': '缺陷被驳回'},
            {'event_type': 'defect_reminder', 'label': '缺陷提醒'},
            {'event_type': 'defect_reopened', 'label': '缺陷重新打开'},
            {'event_type': 'comment_added', 'label': '评论通知'},
            {'event_type': 'batch_fixed', 'label': '批量修复'},
        ],
        'report': [
            {'event_type': 'pending_review', 'label': '报告待审核'},
            {'event_type': 'approved', 'label': '报告已批准'},
            {'event_type': 'rejected', 'label': '报告被驳回'},
            {'event_type': 'weekly_report_reminder', 'label': '周报提醒'},
        ],
        'system': [
            {'event_type': 'maintenance', 'label': '系统维护'},
            {'event_type': 'feature_release', 'label': '新功能上线'},
            {'event_type': 'password_expiry', 'label': '密码过期提醒'},
            {'event_type': 'permission_changed', 'label': '权限变更'},
            {'event_type': 'backup_completed', 'label': '数据备份'},
            {'event_type': 'version_update', 'label': '版本更新'},
            {'event_type': 'daily_reminder', 'label': '每日任务提醒'},
        ]
    }
    
    # 获取用户现有的偏好设置
    existing_prefs = db.query(UserNotificationPreference).filter(
        UserNotificationPreference.user_id == current_user.id
    ).all()
    
    # 构建偏好设置字典
    pref_dict = {}
    for pref in existing_prefs:
        key = f"{pref.notification_type}:{pref.event_type}"
        pref_dict[key] = pref.is_enabled
    
    # 构建返回数据
    result = []
    for notif_type, events in notification_events.items():
        type_data = {
            'notification_type': notif_type,
            'label': {
                'testcase': '用例通知',
                'testplan': '计划通知',
                'execution': '执行通知',
                'report': '报告通知',
                'system': '系统通知'
            }.get(notif_type, notif_type),
            'events': []
        }
        
        for event in events:
            key = f"{notif_type}:{event['event_type']}"
            # 如果没有设置，默认为启用
            is_enabled = pref_dict.get(key, True)
            
            type_data['events'].append({
                'event_type': event['event_type'],
                'label': event['label'],
                'is_enabled': is_enabled
            })
        
        result.append(type_data)
    
    return {
        "code": 200,
        "message": "success",
        "data": result
    }


@router.get("/{notification_id}")
def get_notification_detail(
    req: Request,
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取通知详情"""
    # 查询通知
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 查询接收记录
    recipient = db.query(NotificationRecipient).filter(
        NotificationRecipient.notification_id == notification_id,
        NotificationRecipient.user_id == current_user.id
    ).first()
    
    if not recipient:
        raise HTTPException(status_code=403, detail="无权查看此通知")
    
    # 自动标记为已读
    if not recipient.is_read:
        service = NotificationService(db)
        service.mark_as_read(notification_id, current_user.id)
        recipient.is_read = True
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": notification.id,
            "title": notification.title,
            "content": notification.content,
            "notification_type": notification.notification_type,
            "event_type": notification.event_type,
            "related_id": notification.related_id,
            "related_type": notification.related_type,
            "is_read": recipient.is_read,
            "read_at": recipient.read_at,
            "created_at": notification.created_at
        }
    }


@router.put("/{notification_id}/read")
def mark_notification_as_read(
    req: Request,
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记通知为已读"""
    service = NotificationService(db)
    success = service.mark_as_read(notification_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="通知不存在或已读")
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.UPDATE,
        description=f"标记通知为已读（ID: {notification_id}）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "标记成功",
        "data": None
    }


@router.put("/read-all")
def mark_all_as_read(
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """全部标记为已读"""
    service = NotificationService(db)
    count = service.mark_all_as_read(current_user.id)
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.UPDATE,
        description=f"全部标记为已读（共{count}条）",
        request=req
    )
    
    return {
        "code": 200,
        "message": f"已标记{count}条通知为已读",
        "data": {"count": count}
    }


@router.delete("/{notification_id}")
def delete_notification(
    req: Request,
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除通知（仅删除接收记录，不删除通知本身）"""
    recipient = db.query(NotificationRecipient).filter(
        NotificationRecipient.notification_id == notification_id,
        NotificationRecipient.user_id == current_user.id
    ).first()
    
    if not recipient:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    db.delete(recipient)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.DELETE,
        description=f"删除通知（ID: {notification_id}）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }


@router.put("/preferences")
async def update_notification_preferences(
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新当前用户的通知偏好设置
    
    参数:
    - preferences: 偏好设置列表，格式: [
        {
            "notification_type": "testcase",
            "events": [
                {"event_type": "created", "is_enabled": true},
                {"event_type": "updated", "is_enabled": false}
            ]
        }
    ]
    """
    from models import UserNotificationPreference
    
    try:
        body = await req.json()
        preferences = body.get('preferences', [])
        
        for type_pref in preferences:
            notification_type = type_pref.get('notification_type')
            events = type_pref.get('events', [])
            
            for event_data in events:
                event_type = event_data.get('event_type')
                is_enabled = event_data.get('is_enabled', True)
                
                # 查找或创建偏好设置
                pref = db.query(UserNotificationPreference).filter(
                    UserNotificationPreference.user_id == current_user.id,
                    UserNotificationPreference.notification_type == notification_type,
                    UserNotificationPreference.event_type == event_type
                ).first()
                
                if pref:
                    pref.is_enabled = is_enabled
                else:
                    pref = UserNotificationPreference(
                        user_id=current_user.id,
                        notification_type=notification_type,
                        event_type=event_type,
                        is_enabled=is_enabled
                    )
                    db.add(pref)
        
        db.commit()
        
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.SYSTEM,
            action=LogAction.UPDATE,
            description=f"更新通知偏好设置",
            request=req
        )
        
        return {
            "code": 200,
            "message": "更新成功",
            "data": None
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
