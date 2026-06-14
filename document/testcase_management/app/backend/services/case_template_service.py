"""
用例模板服务
"""
import json
import base64
import re
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
import pandas as pd
from io import BytesIO

from models import CaseTemplate, User, Team


def parse_excel_headers(file_content: bytes, file_name: str) -> List[dict]:
    """
    解析 Excel 文件表头，提取字段配置
    
    Args:
        file_content: 文件二进制内容
        file_name: 文件名（用于判断格式）
    
    Returns:
        字段配置列表
    """
    try:
        # 根据文件扩展名选择引擎
        if file_name.endswith('.xlsx'):
            df = pd.read_excel(BytesIO(file_content), engine='openpyxl', nrows=0)
        else:
            df = pd.read_excel(BytesIO(file_content), engine='xlrd', nrows=0)
        
        fields = []
        for idx, col in enumerate(df.columns):
            original_name = str(col).strip()
            # 检查是否带星号（必填标记）
            required = '*' in original_name
            # 去除星号作为显示名称
            name = re.sub(r'\*', '', original_name).strip()
            
            fields.append({
                "index": idx,
                "original_name": original_name,
                "name": name,
                "required": required,
                "field_type": "string",
                "enum_values": None,
                "format_check": None
            })
        
        return fields
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析Excel文件失败: {str(e)}")


def create_template(
    db: Session,
    team_id: int,
    name: str,
    file: UploadFile,
    user_id: int
) -> CaseTemplate:
    """
    创建用例模板
    """
    # 验证项目组存在
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="项目组不存在")
    
    # 验证文件格式
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx 和 .xls 格式")
    
    # 读取文件内容
    file_content = file.file.read()
    file.file.seek(0)
    
    # 解析表头
    fields = parse_excel_headers(file_content, file.filename)
    
    if not fields:
        raise HTTPException(status_code=400, detail="Excel文件表头为空")
    
    # Base64 编码文件内容
    file_data = base64.b64encode(file_content).decode('utf-8')
    
    # 创建模板
    template = CaseTemplate(
        team_id=team_id,
        name=name or file.filename.rsplit('.', 1)[0],
        file_name=file.filename,
        file_data=file_data,
        fields=json.dumps({"fields": fields}, ensure_ascii=False),
        is_default=False,
        created_by=user_id
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


def get_templates_by_team(db: Session, team_id: int) -> List[dict]:
    """
    获取项目组下的所有模板
    """
    templates = db.query(CaseTemplate).filter(
        CaseTemplate.team_id == team_id
    ).order_by(CaseTemplate.created_at.desc()).all()
    
    result = []
    for t in templates:
        fields_data = json.loads(t.fields) if t.fields else {"fields": []}
        
        # 获取创建人名称
        creator = db.query(User).filter(User.id == t.created_by).first() if t.created_by else None
        
        result.append({
            "id": t.id,
            "name": t.name,
            "file_name": t.file_name,
            "is_default": t.is_default,
            "field_count": len(fields_data.get("fields", [])),
            "created_at": t.created_at,
            "created_by_name": creator.username if creator else None
        })
    return result


def get_template_by_id(db: Session, template_id: int) -> Optional[dict]:
    """
    获取模板详情
    """
    template = db.query(CaseTemplate).filter(CaseTemplate.id == template_id).first()
    if not template:
        return None
    
    fields_data = json.loads(template.fields) if template.fields else {"fields": []}
    creator = db.query(User).filter(User.id == template.created_by).first() if template.created_by else None
    
    return {
        "id": template.id,
        "team_id": template.team_id,
        "name": template.name,
        "file_name": template.file_name,
        "fields": fields_data.get("fields", []),
        "is_default": template.is_default,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
        "created_by": template.created_by,
        "created_by_name": creator.username if creator else None
    }


def update_template(
    db: Session,
    template_id: int,
    name: Optional[str] = None,
    fields: Optional[List[dict]] = None
) -> Optional[dict]:
    """
    更新模板
    """
    template = db.query(CaseTemplate).filter(CaseTemplate.id == template_id).first()
    if not template:
        return None
    
    if name:
        template.name = name
    
    if fields is not None:
        template.fields = json.dumps({"fields": fields}, ensure_ascii=False)
    
    db.commit()
    db.refresh(template)
    
    return get_template_by_id(db, template_id)


def delete_template(db: Session, template_id: int) -> bool:
    """
    删除模板
    """
    template = db.query(CaseTemplate).filter(CaseTemplate.id == template_id).first()
    if not template:
        return False
    
    db.delete(template)
    db.commit()
    return True


def set_default_template(db: Session, template_id: int) -> bool:
    """
    设置默认模板
    """
    template = db.query(CaseTemplate).filter(CaseTemplate.id == template_id).first()
    if not template:
        return False
    
    # 取消同项目组下其他模板的默认状态
    db.query(CaseTemplate).filter(
        CaseTemplate.team_id == template.team_id,
        CaseTemplate.id != template_id
    ).update({"is_default": False})
    
    # 设置当前模板为默认
    template.is_default = True
    db.commit()
    
    return True


def get_template_file(db: Session, template_id: int) -> Optional[tuple]:
    """
    获取模板文件内容
    
    Returns:
        (file_content, file_name) 或 None
    """
    template = db.query(CaseTemplate).filter(CaseTemplate.id == template_id).first()
    if not template or not template.file_data:
        return None
    
    file_content = base64.b64decode(template.file_data)
    return (file_content, template.file_name)


def get_default_template(db: Session, team_id: int) -> Optional[dict]:
    """
    获取项目组的默认模板
    """
    template = db.query(CaseTemplate).filter(
        CaseTemplate.team_id == team_id,
        CaseTemplate.is_default == True
    ).first()
    
    if not template:
        return None
    
    return get_template_by_id(db, template.id)
