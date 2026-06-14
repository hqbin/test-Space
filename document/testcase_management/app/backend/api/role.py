from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import Role, User, UserRole
from auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
import json
from utils.logger import log_operation, LogAction, LogModule

router = APIRouter()

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Optional[List[str]] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

@router.get("")
def list_roles(
    req: Request,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色列表"""
    total = db.query(Role).count()
    roles = db.query(Role).order_by(Role.id.asc()).offset((page - 1) * size).limit(size).all()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "records": [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "permissions": json.loads(r.permissions) if r.permissions else [],
                    "is_system": r.is_system if hasattr(r, 'is_system') else False,
                    "created_at": r.created_at
                } for r in roles
            ],
            "total": total
        }
    }

@router.post("")
def create_role(
    req: Request,
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建角色"""
    # 检查角色名是否已存在
    existing = db.query(Role).filter(Role.name == role.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="角色名已存在")
    
    db_role = Role(
        name=role.name,
        description=role.description,
        permissions=json.dumps(role.permissions) if role.permissions else json.dumps([])
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.ROLES,
        action=LogAction.CREATE,
        description=f"创建角色：{db_role.name}（ID: {db_role.id}）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": {
            "id": db_role.id,
            "name": db_role.name,
            "description": db_role.description,
            "permissions": json.loads(db_role.permissions) if db_role.permissions else []
        }
    }

@router.put("/{role_id}")
def update_role(
    req: Request,
    role_id: int,
    role: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新角色"""
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    old_name = db_role.name
    changes = []  # 记录变更内容
    
    if role.name and role.name != db_role.name:
        # 检查新名称是否与其他角色冲突
        existing = db.query(Role).filter(
            Role.name == role.name,
            Role.id != role_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="角色名已存在")
        changes.append(f"角色名: {db_role.name} → {role.name}")
        db_role.name = role.name
    
    if role.description is not None and role.description != db_role.description:
        old_desc = db_role.description or "(空)"
        new_desc = role.description or "(空)"
        changes.append(f"描述: {old_desc} → {new_desc}")
        db_role.description = role.description
    
    if role.permissions is not None:
        old_perms = json.loads(db_role.permissions) if db_role.permissions else []
        new_perms = role.permissions
        if set(old_perms) != set(new_perms):
            changes.append(f"权限数量: {len(old_perms)} → {len(new_perms)}")
        db_role.permissions = json.dumps(role.permissions)
    
    db.commit()
    db.refresh(db_role)
    
    # 只有在有实际变更时才记录日志
    if changes:
        change_detail = "；".join(changes)
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.ROLES,
            action=LogAction.UPDATE,
            description=f"更新角色：{old_name}（ID: {role_id}，{change_detail}）",
            request=req
        )
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": {
            "id": db_role.id,
            "name": db_role.name,
            "description": db_role.description,
            "permissions": json.loads(db_role.permissions) if db_role.permissions else []
        }
    }

@router.delete("/{role_id}")
def delete_role(
    req: Request,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除角色"""
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 检查是否为系统默认角色
    if db_role.is_system:
        raise HTTPException(status_code=400, detail="系统默认角色不能删除")
    
    # 检查是否有用户使用该角色
    user_count = db.query(UserRole).filter(UserRole.role_id == role_id).count()
    if user_count > 0:
        raise HTTPException(status_code=400, detail=f"该角色正在被 {user_count} 个用户使用，无法删除")
    
    role_name = db_role.name
    db.delete(db_role)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.ROLES,
        action=LogAction.DELETE,
        description=f"删除角色：{role_name}（ID: {role_id}）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }

@router.get("/user/{user_id}/roles")
def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的角色列表"""
    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    role_ids = [ur.role_id for ur in user_roles]
    
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all() if role_ids else []
    
    return {
        "code": 200,
        "message": "success",
        "data": [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "permissions": json.loads(r.permissions) if r.permissions else []
            } for r in roles
        ]
    }

@router.post("/user/{user_id}/roles")
def assign_roles_to_user(
    req: Request,
    user_id: int,
    role_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为用户分配角色"""
    # 检查用户是否存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 删除用户现有的角色
    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    
    # 添加新的角色
    role_names = []
    for role_id in role_ids:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            continue
        
        user_role = UserRole(user_id=user_id, role_id=role_id)
        db.add(user_role)
        role_names.append(role.name)
    
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.ROLES,
        action=LogAction.ASSIGN,
        description=f"为用户 {user.username} 分配角色：{', '.join(role_names)}",
        request=req
    )
    
    return {
        "code": 200,
        "message": "分配成功",
        "data": None
    }


# ==================== 角色模板相关API ====================
from models import RoleTemplate

class RoleTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Optional[List[str]] = []

class RoleTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

@router.get("/role-templates")
def get_role_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色模板列表"""
    templates = db.query(RoleTemplate).all()
    
    return {
        "code": 200,
        "message": "success",
        "data": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "permissions": json.loads(t.permissions) if t.permissions else [],
                "is_system": t.is_system if hasattr(t, 'is_system') else False,
                "created_at": t.created_at
            } for t in templates
        ]
    }

@router.post("/role-templates")
def create_role_template(
    req: Request,
    template: RoleTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建角色模板"""
    # 检查模板名是否已存在
    existing = db.query(RoleTemplate).filter(RoleTemplate.name == template.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板名称已存在")
    
    db_template = RoleTemplate(
        name=template.name,
        description=template.description,
        permissions=json.dumps(template.permissions) if template.permissions else json.dumps([])
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.ROLES,
        action=LogAction.CREATE,
        description=f"创建角色模板：{db_template.name}（ID: {db_template.id}）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": {
            "id": db_template.id,
            "name": db_template.name,
            "description": db_template.description,
            "permissions": json.loads(db_template.permissions) if db_template.permissions else []
        }
    }

@router.put("/role-templates/{template_id}")
def update_role_template(
    req: Request,
    template_id: int,
    template: RoleTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新角色模板"""
    db_template = db.query(RoleTemplate).filter(RoleTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    old_name = db_template.name
    changes = []  # 记录变更内容
    
    if template.name and template.name != db_template.name:
        # 检查新名称是否与其他模板冲突
        existing = db.query(RoleTemplate).filter(
            RoleTemplate.name == template.name,
            RoleTemplate.id != template_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="模板名称已存在")
        changes.append(f"模板名: {db_template.name} → {template.name}")
        db_template.name = template.name
    
    if template.description is not None and template.description != db_template.description:
        old_desc = db_template.description or "(空)"
        new_desc = template.description or "(空)"
        changes.append(f"描述: {old_desc} → {new_desc}")
        db_template.description = template.description
    
    if template.permissions is not None:
        old_perms = json.loads(db_template.permissions) if db_template.permissions else []
        new_perms = template.permissions
        if set(old_perms) != set(new_perms):
            changes.append(f"权限数量: {len(old_perms)} → {len(new_perms)}")
        db_template.permissions = json.dumps(template.permissions)
    
    db.commit()
    db.refresh(db_template)
    
    # 只有在有实际变更时才记录日志
    if changes:
        change_detail = "；".join(changes)
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.ROLES,
            action=LogAction.UPDATE,
            description=f"更新角色模板：{old_name}（ID: {template_id}，{change_detail}）",
            request=req
        )
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": {
            "id": db_template.id,
            "name": db_template.name,
            "description": db_template.description,
            "permissions": json.loads(db_template.permissions) if db_template.permissions else []
        }
    }

@router.delete("/role-templates/{template_id}")
def delete_role_template(
    req: Request,
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除角色模板"""
    db_template = db.query(RoleTemplate).filter(RoleTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查是否为系统默认模板
    if db_template.is_system:
        raise HTTPException(status_code=400, detail="系统默认模板不能删除")
    
    template_name = db_template.name
    db.delete(db_template)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.ROLES,
        action=LogAction.DELETE,
        description=f"删除角色模板：{template_name}（ID: {template_id}）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }
