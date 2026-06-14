"""
通知规则管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from database import get_db
from models import User, NotificationRule
from auth import get_current_user
from pydantic import BaseModel
from typing import Optional
from utils.logger import log_operation, LogAction, LogModule

router = APIRouter()


class NotificationRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    notification_type: str
    event_type: str
    recipient_type: str
    recipient_roles: Optional[str] = None
    recipient_users: Optional[str] = None
    notification_method: Optional[str] = 'internal'
    template_id: Optional[int] = None
    trigger_condition: Optional[str] = None
    is_active: bool = True


class NotificationRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    notification_type: Optional[str] = None
    event_type: Optional[str] = None
    recipient_type: Optional[str] = None
    recipient_roles: Optional[str] = None
    recipient_users: Optional[str] = None
    notification_method: Optional[str] = None
    template_id: Optional[int] = None
    trigger_condition: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("")
def get_notification_rules(
    req: Request,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    notification_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取通知规则列表"""
    query = db.query(NotificationRule)
    
    # 搜索过滤
    if search:
        query = query.filter(NotificationRule.name.contains(search))
    
    # 类型过滤
    if notification_type:
        query = query.filter(NotificationRule.notification_type == notification_type)
    
    # 分页
    total = query.count()
    rules = query.order_by(NotificationRule.id.asc()).offset((page - 1) * size).limit(size).all()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "records": rules,
            "total": total,
            "page": page,
            "size": size
        }
    }


@router.post("")
def create_notification_rule(
    req: Request,
    rule_data: NotificationRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建通知规则"""
    # 检查规则名称是否已存在
    existing = db.query(NotificationRule).filter(
        NotificationRule.name == rule_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="规则名称已存在")
    
    # 创建规则
    db_rule = NotificationRule(
        name=rule_data.name,
        description=rule_data.description,
        notification_type=rule_data.notification_type,
        event_type=rule_data.event_type,
        recipient_type=rule_data.recipient_type,
        recipient_roles=rule_data.recipient_roles,
        recipient_users=rule_data.recipient_users,
        notification_method=rule_data.notification_method,
        template_id=rule_data.template_id,
        trigger_condition=rule_data.trigger_condition,
        is_active=rule_data.is_active
    )
    
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.CREATE,
        description=f"创建通知规则：{rule_data.name}",
        request=req
    )
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": db_rule
    }


@router.put("/{rule_id}")
def update_notification_rule(
    req: Request,
    rule_id: int,
    rule_data: NotificationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新通知规则"""
    db_rule = db.query(NotificationRule).filter(NotificationRule.id == rule_id).first()
    
    if not db_rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    # 更新字段
    update_data = rule_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_rule, field, value)
    
    db.commit()
    db.refresh(db_rule)
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.UPDATE,
        description=f"更新通知规则：{db_rule.name}",
        request=req
    )
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": db_rule
    }


@router.delete("/{rule_id}")
def delete_notification_rule(
    req: Request,
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除通知规则"""
    db_rule = db.query(NotificationRule).filter(NotificationRule.id == rule_id).first()
    
    if not db_rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    rule_name = db_rule.name
    db.delete(db_rule)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.DELETE,
        description=f"删除通知规则：{rule_name}",
        request=req
    )
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }
