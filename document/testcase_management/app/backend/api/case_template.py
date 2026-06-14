"""
用例模板管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from io import BytesIO

from database import get_db
from auth import get_current_user
from models import User
from services import case_template_service
from schemas import CaseTemplateUpdate, CaseTemplateResponse, CaseTemplateListItem
from utils.logger import log_operation, LogAction, LogModule

router = APIRouter()


@router.get("/teams/{team_id}/templates")
def get_templates(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目组下的所有模板"""
    templates = case_template_service.get_templates_by_team(db, team_id)
    return {"code": 200, "message": "success", "data": templates}


@router.post("/teams/{team_id}/templates")
def create_template(
    team_id: int,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传并创建模板"""
    template = case_template_service.create_template(
        db=db,
        team_id=team_id,
        name=name,
        file=file,
        user_id=current_user.id
    )
    return {"code": 200, "message": "success", "data": case_template_service.get_template_by_id(db, template.id)}


@router.get("/templates/{template_id}")
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板详情"""
    template = case_template_service.get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"code": 200, "message": "success", "data": template}


@router.put("/templates/{template_id}")
def update_template(
    template_id: int,
    data: CaseTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新模板"""
    # 转换 fields 为字典列表
    fields_dict = None
    if data.fields:
        fields_dict = [f.model_dump() for f in data.fields]
    
    template = case_template_service.update_template(
        db=db,
        template_id=template_id,
        name=data.name,
        fields=fields_dict
    )
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"code": 200, "message": "success", "data": template}


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除模板"""
    # 获取模板名称用于日志
    template_info = case_template_service.get_template_by_id(db, template_id)
    template_name = template_info.get('name', str(template_id)) if template_info else str(template_id)
    
    success = case_template_service.delete_template(db, template_id)
    if not success:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.SYSTEM,
        action=LogAction.DELETE,
        description=f"删除用例模板：{template_name}（ID: {template_id}）",
        request=req
    )
    
    return {"code": 200, "message": "success", "data": {"success": True}}


@router.put("/templates/{template_id}/default")
def set_default_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """设为默认模板"""
    success = case_template_service.set_default_template(db, template_id)
    if not success:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"code": 200, "message": "success", "data": {"success": True}}


@router.get("/templates/{template_id}/download")
def download_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载模板文件"""
    from urllib.parse import quote
    
    result = case_template_service.get_template_file(db, template_id)
    if not result:
        raise HTTPException(status_code=404, detail="模板文件不存在")
    
    file_content, file_name = result
    
    # 确定 MIME 类型
    if file_name.endswith('.xlsx'):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        media_type = "application/vnd.ms-excel"
    
    encoded_name = quote(file_name)
    
    return StreamingResponse(
        BytesIO(file_content),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"
        }
    )


@router.get("/teams/{team_id}/templates/default")
def get_default_template(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目组的默认模板"""
    template = case_template_service.get_default_template(db, team_id)
    return {"code": 200, "message": "success", "data": {"default_template": template}}
