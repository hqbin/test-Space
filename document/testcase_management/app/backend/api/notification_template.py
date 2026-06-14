"""
通知模板管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from database import get_db
from models import User, NotificationTemplate
from auth import get_current_user
from pydantic import BaseModel
from typing import Optional
from utils.logger import log_operation, LogAction, LogModule

router = APIRouter()


class NotificationTemplateCreate(BaseModel):
    name: str
    notification_type: str
    title_template: str
    content_template: str
    is_system: bool = False


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    notification_type: Optional[str] = None
    title_template: Optional[str] = None
    content_template: Optional[str] = None


@router.get("")
def get_notification_templates(
    req: Request,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=1000),
    search: Optional[str] = None,
    notification_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取通知模板列表"""
    query = db.query(NotificationTemplate)
    
    # 搜索过滤
    if search:
        query = query.filter(NotificationTemplate.name.contains(search))
    
    # 类型过滤
    if notification_type:
        query = query.filter(NotificationTemplate.notification_type == notification_type)
    
    # 分页
    total = query.count()
    templates = query.order_by(NotificationTemplate.id.asc()).offset((page - 1) * size).limit(size).all()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "records": templates,
            "total": total,
            "page": page,
            "size": size
        }
    }


@router.post("")
def create_notification_template(
    req: Request,
    template_data: NotificationTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建通知模板"""
    # 检查模板名称是否已存在
    existing = db.query(NotificationTemplate).filter(
        NotificationTemplate.name == template_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="模板名称已存在")
    
    # 创建模板
    db_template = NotificationTemplate(
        name=template_data.name,
        notification_type=template_data.notification_type,
        title_template=template_data.title_template,
        content_template=template_data.content_template,
        is_system=template_data.is_system
    )
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.CREATE,
        description=f"创建通知模板：{template_data.name}",
        request=req
    )
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": db_template
    }


@router.put("/{template_id}")
def update_notification_template(
    req: Request,
    template_id: int,
    template_data: NotificationTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新通知模板"""
    db_template = db.query(NotificationTemplate).filter(
        NotificationTemplate.id == template_id
    ).first()
    
    if not db_template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 更新字段
    update_data = template_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_template, field, value)
    
    db.commit()
    db.refresh(db_template)
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.UPDATE,
        description=f"更新通知模板：{db_template.name}",
        request=req
    )
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": db_template
    }


@router.delete("/{template_id}")
def delete_notification_template(
    req: Request,
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除通知模板"""
    db_template = db.query(NotificationTemplate).filter(
        NotificationTemplate.id == template_id
    ).first()
    
    if not db_template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 系统模板不能删除
    if db_template.is_system:
        raise HTTPException(status_code=400, detail="系统模板不能删除")
    
    template_name = db_template.name
    db.delete(db_template)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.DELETE,
        description=f"删除通知模板：{template_name}",
        request=req
    )
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }
