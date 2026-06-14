"""
测试报告模板 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
import json

from database import get_db
from auth import get_current_user
from models import User, ReportTemplate
from utils.logger import log_operation, LogAction, LogModule

router = APIRouter()


@router.get("/teams/{team_id}/report-templates")
def get_report_templates(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目组下的所有报告模板"""
    templates = db.query(ReportTemplate).filter(
        ReportTemplate.team_id == team_id
    ).order_by(ReportTemplate.is_default.desc(), ReportTemplate.created_at.desc()).all()

    result = []
    for t in templates:
        creator = db.query(User).filter(User.id == t.created_by).first()
        result.append({
            "id": t.id,
            "team_id": t.team_id,
            "name": t.name,
            "description": t.description or "",
            "selected_fields": json.loads(t.selected_fields) if t.selected_fields else [],
            "criteria_config": json.loads(t.criteria_config) if t.criteria_config else {},
            "is_default": t.is_default,
            "created_by": t.created_by,
            "created_by_name": creator.username if creator else "",
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        })
    return {"code": 200, "message": "success", "data": result}


@router.post("/teams/{team_id}/report-templates")
def create_report_template(
    team_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建报告模板"""
    template = ReportTemplate(
        team_id=team_id,
        name=data.get("name", ""),
        description=data.get("description", ""),
        selected_fields=json.dumps(data.get("selected_fields", []), ensure_ascii=False),
        criteria_config=json.dumps(data.get("criteria_config", {}), ensure_ascii=False),
        is_default=data.get("is_default", False),
        created_by=current_user.id
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return {"code": 200, "message": "success", "data": {"id": template.id}}


@router.put("/report-templates/{template_id}")
def update_report_template(
    template_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新报告模板"""
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if "name" in data:
        template.name = data["name"]
    if "description" in data:
        template.description = data["description"]
    if "selected_fields" in data:
        template.selected_fields = json.dumps(data["selected_fields"], ensure_ascii=False)
    if "criteria_config" in data:
        template.criteria_config = json.dumps(data["criteria_config"], ensure_ascii=False)
    if "is_default" in data:
        template.is_default = data["is_default"]

    db.commit()
    return {"code": 200, "message": "success", "data": {"id": template.id}}


@router.delete("/report-templates/{template_id}")
def delete_report_template(
    template_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除报告模板"""
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    template_name = template.name
    db.delete(template)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.DELETE,
        description=f"删除报告模板：{template_name}（ID: {template_id}）",
        request=req
    )
    
    return {"code": 200, "message": "success", "data": {"success": True}}


@router.put("/report-templates/{template_id}/default")
def set_default_report_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """设为默认报告模板"""
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 取消同项目组下其他默认模板
    db.query(ReportTemplate).filter(
        ReportTemplate.team_id == template.team_id,
        ReportTemplate.id != template_id
    ).update({"is_default": False})

    template.is_default = True
    db.commit()
    return {"code": 200, "message": "success", "data": {"success": True}}


@router.get("/teams/{team_id}/report-templates/default")
def get_default_report_template(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目组的默认报告模板"""
    template = db.query(ReportTemplate).filter(
        ReportTemplate.team_id == team_id,
        ReportTemplate.is_default == True
    ).first()

    if not template:
        return {"code": 200, "message": "success", "data": None}

    return {"code": 200, "message": "success", "data": {
        "id": template.id,
        "name": template.name,
        "selected_fields": json.loads(template.selected_fields) if template.selected_fields else [],
        "criteria_config": json.loads(template.criteria_config) if template.criteria_config else {},
    }}
