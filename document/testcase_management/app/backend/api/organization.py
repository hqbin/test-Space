from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from models import Department, ProjectGroup, User, UserDepartment, UserProjectGroup, DepartmentManager
from auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from utils.logger import log_operation, LogAction, LogModule

router = APIRouter()

# ==================== 部门管理 ====================

class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    manager_ids: Optional[List[int]] = []
    project_group_ids: Optional[List[int]] = []

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    manager_ids: Optional[List[int]] = []
    project_group_ids: Optional[List[int]] = []

@router.get("/departments")
def list_departments(
    req: Request,
    page: int = 1,
    size: int = 10,
    search: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取部门列表"""
    query = db.query(Department)
    
    # 搜索功能
    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        query = query.filter(Department.name.ilike(search_pattern))
    
    total = query.count()
    departments = query.order_by(Department.id.asc()).offset((page - 1) * size).limit(size).all()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "records": [
                {
                    "id": d.id,
                    "name": d.name,
                    "description": d.description,
                    "manager_ids": [dm.user_id for dm in db.query(DepartmentManager).filter(DepartmentManager.department_id == d.id).all()],
                    "manager_names": [db.query(User).filter(User.id == dm.user_id).first().username for dm in db.query(DepartmentManager).filter(DepartmentManager.department_id == d.id).all()],
                    "project_group_ids": [pg.id for pg in db.query(ProjectGroup).filter(ProjectGroup.department_id == d.id).all()],
                    "project_group_names": [pg.name for pg in db.query(ProjectGroup).filter(ProjectGroup.department_id == d.id).all()],
                    "created_at": d.created_at
                } for d in departments
            ],
            "total": total
        }
    }

@router.post("/departments")
def create_department(
    req: Request,
    department: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建部门"""
    # 检查名称是否已存在
    existing = db.query(Department).filter(Department.name == department.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="部门名称已存在")
    
    # 检查部门负责人是否存在
    if department.manager_ids:
        for manager_id in department.manager_ids:
            manager = db.query(User).filter(User.id == manager_id).first()
            if not manager:
                raise HTTPException(status_code=404, detail=f"部门负责人ID {manager_id} 不存在")
    
    db_department = Department(
        name=department.name,
        description=department.description
    )
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    
    # 创建部门负责人关联
    if department.manager_ids:
        for manager_id in department.manager_ids:
            department_manager = DepartmentManager(
                department_id=db_department.id,
                user_id=manager_id
            )
            db.add(department_manager)
        db.commit()
    
    # 关联项目组
    if department.project_group_ids:
        for group_id in department.project_group_ids:
            project_group = db.query(ProjectGroup).filter(ProjectGroup.id == group_id).first()
            if project_group:
                project_group.department_id = db_department.id
        db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.ORGANIZATION,
        action=LogAction.CREATE,
        description=f"创建部门：{db_department.name}（ID: {db_department.id}）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": {
            "id": db_department.id,
            "name": db_department.name,
            "description": db_department.description,
            "manager_ids": department.manager_ids
        }
    }

@router.get("/departments/{dept_id}")
def get_department(
    dept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取部门详情"""
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": department.id,
            "name": department.name,
            "description": department.description,
            "manager_id": department.manager_id,
            "manager_name": db.query(User).filter(User.id == department.manager_id).first().username if department.manager_id else None,
            "created_at": department.created_at
        }
    }

@router.put("/departments/{dept_id}")
def update_department(
    req: Request,
    dept_id: int,
    department: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新部门"""
    db_department = db.query(Department).filter(Department.id == dept_id).first()
    if not db_department:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    old_name = db_department.name
    changes = []  # 记录变更内容
    
    if department.name and department.name != db_department.name:
        # 检查新名称是否与其他部门冲突
        existing = db.query(Department).filter(
            Department.name == department.name,
            Department.id != dept_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="部门名称已存在")
        changes.append(f"名称: {db_department.name} → {department.name}")
        db_department.name = department.name
    
    if department.description is not None and department.description != db_department.description:
        old_desc = db_department.description or "(空)"
        new_desc = department.description or "(空)"
        changes.append(f"描述: {old_desc} → {new_desc}")
        db_department.description = department.description
    
    if department.manager_ids is not None:
        # 检查部门负责人是否存在
        for manager_id in department.manager_ids:
            manager = db.query(User).filter(User.id == manager_id).first()
            if not manager:
                raise HTTPException(status_code=404, detail=f"部门负责人ID {manager_id} 不存在")
        
        # 获取旧的部门负责人
        old_managers = db.query(DepartmentManager).filter(DepartmentManager.department_id == dept_id).all()
        old_manager_ids = [m.user_id for m in old_managers]
        old_manager_names = [db.query(User).filter(User.id == m.user_id).first().username for m in old_managers]
        
        # 获取新的部门负责人
        new_manager_names = [db.query(User).filter(User.id == m_id).first().username for m_id in department.manager_ids]
        
        if set(old_manager_ids) != set(department.manager_ids):
            changes.append(f"部门负责人: {', '.join(old_manager_names) or '(空)'} → {', '.join(new_manager_names) or '(空)'}")
            
            # 删除旧的部门负责人关联
            db.query(DepartmentManager).filter(DepartmentManager.department_id == dept_id).delete()
            
            # 创建新的部门负责人关联
            for manager_id in department.manager_ids:
                department_manager = DepartmentManager(
                    department_id=dept_id,
                    user_id=manager_id
                )
                db.add(department_manager)
    
    if department.project_group_ids is not None:
        # 检查项目组是否存在
        for group_id in department.project_group_ids:
            project_group = db.query(ProjectGroup).filter(ProjectGroup.id == group_id).first()
            if not project_group:
                raise HTTPException(status_code=404, detail=f"项目组ID {group_id} 不存在")
        
        # 获取旧的关联项目组
        old_project_groups = db.query(ProjectGroup).filter(ProjectGroup.department_id == dept_id).all()
        old_group_ids = [g.id for g in old_project_groups]
        old_group_names = [g.name for g in old_project_groups]
        
        # 获取新的关联项目组
        new_group_names = [db.query(ProjectGroup).filter(ProjectGroup.id == g_id).first().name for g_id in department.project_group_ids]
        
        if set(old_group_ids) != set(department.project_group_ids):
            changes.append(f"关联项目组: {', '.join(old_group_names) or '(空)'} → {', '.join(new_group_names) or '(空)'}")
            
            # 先将所有项目组的department_id设为null
            for group in old_project_groups:
                group.department_id = None
            
            # 然后将新的项目组关联到当前部门
            for group_id in department.project_group_ids:
                project_group = db.query(ProjectGroup).filter(ProjectGroup.id == group_id).first()
                if project_group:
                    project_group.department_id = dept_id
    
    db.commit()
    db.refresh(db_department)
    
    # 只有在有实际变更时才记录日志
    if changes:
        change_detail = "；".join(changes)
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.ORGANIZATION,
            action=LogAction.UPDATE,
            description=f"更新部门：{old_name}（ID: {dept_id}，{change_detail}）",
            request=req
        )
    
    # 获取更新后的部门负责人
    updated_managers = db.query(DepartmentManager).filter(DepartmentManager.department_id == dept_id).all()
    updated_manager_ids = [m.user_id for m in updated_managers]
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": {
            "id": db_department.id,
            "name": db_department.name,
            "description": db_department.description,
            "manager_ids": updated_manager_ids
        }
    }

@router.delete("/departments/{dept_id}")
def delete_department(
    req: Request,
    dept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除部门"""
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    # 检查是否有项目组关联此部门
    project_group_count = db.query(ProjectGroup).filter(ProjectGroup.department_id == dept_id).count()
    if project_group_count > 0:
        raise HTTPException(status_code=400, detail=f"该部门下有 {project_group_count} 个项目组，无法删除")
    
    # 检查是否有用户关联此部门
    user_count = db.query(UserDepartment).filter(UserDepartment.department_id == dept_id).count()
    if user_count > 0:
        raise HTTPException(status_code=400, detail=f"该部门下有 {user_count} 个用户，无法删除")
    
    dept_name = department.name
    
    # 删除部门负责人关联
    db.query(DepartmentManager).filter(DepartmentManager.department_id == dept_id).delete()
    
    # 删除部门
    db.delete(department)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.ORGANIZATION,
        action=LogAction.DELETE,
        description=f"删除部门：{dept_name}（ID: {dept_id}）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }

# ==================== 项目组管理 ====================

class ProjectGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    department_id: int
    leader_id: Optional[int] = None

class ProjectGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[int] = None
    leader_id: Optional[int] = None

@router.get("/project-groups")
def list_project_groups(
    req: Request,
    page: int = 1,
    size: int = 10,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目组列表"""
    query = db.query(ProjectGroup)
    if department_id:
        query = query.filter(ProjectGroup.department_id == department_id)
    
    total = query.count()
    project_groups = query.order_by(ProjectGroup.id.asc()).offset((page - 1) * size).limit(size).all()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "records": [
                {
                    "id": pg.id,
                    "name": pg.name,
                    "description": pg.description,
                    "department_id": pg.department_id,
                    "department_name": db.query(Department).filter(Department.id == pg.department_id).first().name if pg.department_id else None,
                    "leader_id": pg.leader_id,
                    "leader_name": db.query(User).filter(User.id == pg.leader_id).first().username if pg.leader_id else None,
                    "created_at": pg.created_at
                } for pg in project_groups
            ],
            "total": total
        }
    }

@router.post("/project-groups")
def create_project_group(
    req: Request,
    project_group: ProjectGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建项目组"""
    # 检查部门是否存在
    department = db.query(Department).filter(Department.id == project_group.department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    # 检查项目组名称是否在部门内已存在
    existing = db.query(ProjectGroup).filter(
        ProjectGroup.name == project_group.name,
        ProjectGroup.department_id == project_group.department_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="项目组名称在该部门内已存在")
    
    # 检查项目组负责人是否存在
    if project_group.leader_id:
        leader = db.query(User).filter(User.id == project_group.leader_id).first()
        if not leader:
            raise HTTPException(status_code=404, detail="项目组负责人不存在")
    
    db_project_group = ProjectGroup(
        name=project_group.name,
        description=project_group.description,
        department_id=project_group.department_id,
        leader_id=project_group.leader_id
    )
    db.add(db_project_group)
    db.commit()
    db.refresh(db_project_group)
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.ORGANIZATION,
        action=LogAction.CREATE,
        description=f"创建项目组：{db_project_group.name}（ID: {db_project_group.id}，部门: {department.name}）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": {
            "id": db_project_group.id,
            "name": db_project_group.name,
            "description": db_project_group.description,
            "department_id": db_project_group.department_id,
            "leader_id": db_project_group.leader_id
        }
    }

@router.get("/project-groups/{pg_id}")
def get_project_group(
    pg_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目组详情"""
    project_group = db.query(ProjectGroup).filter(ProjectGroup.id == pg_id).first()
    if not project_group:
        raise HTTPException(status_code=404, detail="项目组不存在")
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": project_group.id,
            "name": project_group.name,
            "description": project_group.description,
            "department_id": project_group.department_id,
            "department_name": db.query(Department).filter(Department.id == project_group.department_id).first().name if project_group.department_id else None,
            "leader_id": project_group.leader_id,
            "leader_name": db.query(User).filter(User.id == project_group.leader_id).first().username if project_group.leader_id else None,
            "created_at": project_group.created_at
        }
    }

@router.put("/project-groups/{pg_id}")
def update_project_group(
    req: Request,
    pg_id: int,
    project_group: ProjectGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新项目组"""
    db_project_group = db.query(ProjectGroup).filter(ProjectGroup.id == pg_id).first()
    if not db_project_group:
        raise HTTPException(status_code=404, detail="项目组不存在")
    
    old_name = db_project_group.name
    changes = []  # 记录变更内容
    
    if project_group.name and project_group.name != db_project_group.name:
        # 检查新名称是否与同部门内其他项目组冲突
        existing = db.query(ProjectGroup).filter(
            ProjectGroup.name == project_group.name,
            ProjectGroup.department_id == (project_group.department_id or db_project_group.department_id),
            ProjectGroup.id != pg_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="项目组名称在该部门内已存在")
        changes.append(f"名称: {db_project_group.name} → {project_group.name}")
        db_project_group.name = project_group.name
    
    if project_group.description is not None and project_group.description != db_project_group.description:
        old_desc = db_project_group.description or "(空)"
        new_desc = project_group.description or "(空)"
        changes.append(f"描述: {old_desc} → {new_desc}")
        db_project_group.description = project_group.description
    
    if project_group.department_id is not None and project_group.department_id != db_project_group.department_id:
        # 检查部门是否存在
        department = db.query(Department).filter(Department.id == project_group.department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="部门不存在")
        # 检查新部门内是否有同名项目组
        existing = db.query(ProjectGroup).filter(
            ProjectGroup.name == db_project_group.name,
            ProjectGroup.department_id == project_group.department_id,
            ProjectGroup.id != pg_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="项目组名称在新部门内已存在")
        old_dept_name = db.query(Department).filter(Department.id == db_project_group.department_id).first().name
        new_dept_name = department.name
        changes.append(f"部门: {old_dept_name} → {new_dept_name}")
        db_project_group.department_id = project_group.department_id
    
    if project_group.leader_id is not None and project_group.leader_id != db_project_group.leader_id:
        # 检查项目组负责人是否存在
        leader = db.query(User).filter(User.id == project_group.leader_id).first()
        if not leader:
            raise HTTPException(status_code=404, detail="项目组负责人不存在")
        old_leader = db.query(User).filter(User.id == db_project_group.leader_id).first()
        old_leader_name = old_leader.username if old_leader else "(空)"
        new_leader_name = leader.username
        changes.append(f"项目组负责人: {old_leader_name} → {new_leader_name}")
        db_project_group.leader_id = project_group.leader_id
    
    db.commit()
    db.refresh(db_project_group)
    
    # 只有在有实际变更时才记录日志
    if changes:
        change_detail = "；".join(changes)
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.ORGANIZATION,
            action=LogAction.UPDATE,
            description=f"更新项目组：{old_name}（ID: {pg_id}，{change_detail}）",
            request=req
        )
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": {
            "id": db_project_group.id,
            "name": db_project_group.name,
            "description": db_project_group.description,
            "department_id": db_project_group.department_id,
            "leader_id": db_project_group.leader_id
        }
    }

@router.delete("/project-groups/{pg_id}")
def delete_project_group(
    req: Request,
    pg_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除项目组"""
    project_group = db.query(ProjectGroup).filter(ProjectGroup.id == pg_id).first()
    if not project_group:
        raise HTTPException(status_code=404, detail="项目组不存在")
    
    # 检查是否有用户关联此项目组
    user_count = db.query(UserProjectGroup).filter(UserProjectGroup.project_group_id == pg_id).count()
    if user_count > 0:
        raise HTTPException(status_code=400, detail=f"该项目组下有 {user_count} 个用户，无法删除")
    
    pg_name = project_group.name
    db.delete(project_group)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.ORGANIZATION,
        action=LogAction.DELETE,
        description=f"删除项目组：{pg_name}（ID: {pg_id}）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }

# ==================== 用户组织关联 ====================

class AssignDepartmentsRequest(BaseModel):
    department_ids: List[int] = []

@router.post("/users/{user_id}/departments")
def assign_user_department(
    req: Request,
    user_id: int,
    body: AssignDepartmentsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为用户分配部门（支持多个）"""
    department_ids = body.department_ids
    
    # 检查用户是否存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 删除用户现有的部门关联
    db.query(UserDepartment).filter(UserDepartment.user_id == user_id).delete()
    
    # 添加新的部门关联
    dept_names = []
    for dept_id in department_ids:
        department = db.query(Department).filter(Department.id == dept_id).first()
        if department:
            user_department = UserDepartment(user_id=user_id, department_id=dept_id)
            db.add(user_department)
            dept_names.append(department.name)
    
    db.commit()
    
    if dept_names:
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.ORGANIZATION,
            action=LogAction.ASSIGN,
            description=f"为用户 {user.username} 分配部门：{', '.join(dept_names)}",
            request=req
        )
    
    return {
        "code": 200,
        "message": "分配成功",
        "data": None
    }

@router.post("/users/{user_id}/project-groups")
def assign_user_project_group(
    req: Request,
    user_id: int,
    project_group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为用户分配项目组"""
    # 检查用户是否存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查项目组是否存在
    project_group = db.query(ProjectGroup).filter(ProjectGroup.id == project_group_id).first()
    if not project_group:
        raise HTTPException(status_code=404, detail="项目组不存在")
    
    # 检查用户是否已关联该项目组
    existing = db.query(UserProjectGroup).filter(
        UserProjectGroup.user_id == user_id,
        UserProjectGroup.project_group_id == project_group_id
    ).first()
    if existing:
        return {
            "code": 200,
            "message": "用户已在该项目组中",
            "data": None
        }
    
    # 添加项目组关联
    user_project_group = UserProjectGroup(user_id=user_id, project_group_id=project_group_id)
    db.add(user_project_group)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.ORGANIZATION,
        action=LogAction.ASSIGN,
        description=f"为用户 {user.username} 分配项目组：{project_group.name}",
        request=req
    )
    
    return {
        "code": 200,
        "message": "分配成功",
        "data": None
    }

@router.delete("/users/{user_id}/project-groups/{pg_id}")
def remove_user_project_group(
    req: Request,
    user_id: int,
    pg_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从项目组中移除用户"""
    # 检查关联是否存在
    user_project_group = db.query(UserProjectGroup).filter(
        UserProjectGroup.user_id == user_id,
        UserProjectGroup.project_group_id == pg_id
    ).first()
    if not user_project_group:
        raise HTTPException(status_code=404, detail="用户不在该项目组中")
    
    # 获取用户和项目组信息
    user = db.query(User).filter(User.id == user_id).first()
    project_group = db.query(ProjectGroup).filter(ProjectGroup.id == pg_id).first()
    
    # 删除关联
    db.delete(user_project_group)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.ORGANIZATION,
        action=LogAction.REMOVE,
        description=f"从项目组 {project_group.name} 中移除用户 {user.username}",
        request=req
    )
    
    return {
        "code": 200,
        "message": "移除成功",
        "data": None
    }


# ==================== 组织成员管理 ====================

@router.get("/departments/{dept_id}/members")
def get_department_members(
    dept_id: int,
    search: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组织成员列表"""
    # 检查组织是否存在
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="组织不存在")
    
    # 通过 user_departments 表查询组织成员
    user_depts = db.query(UserDepartment).filter(UserDepartment.department_id == dept_id).all()
    user_ids = [ud.user_id for ud in user_depts]
    
    members = []
    if user_ids:
        query = db.query(User).filter(User.id.in_(user_ids))
        
        # 添加搜索过滤
        if search and search.strip():
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_pattern),
                    User.full_name.ilike(search_pattern),
                    User.email.ilike(search_pattern)
                )
            )
        
        users = query.all()
        members = [
            {
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "email": u.email,
                "phone": u.phone,
                "status": u.status
            } for u in users
        ]
    
    return {
        "code": 200,
        "message": "success",
        "data": members
    }


@router.delete("/departments/{dept_id}/members/{user_id}")
def remove_department_member(
    req: Request,
    dept_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从组织中移除成员"""
    # 检查组织是否存在
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="组织不存在")
    
    # 检查用户是否在组织中
    user_dept = db.query(UserDepartment).filter(
        UserDepartment.department_id == dept_id,
        UserDepartment.user_id == user_id
    ).first()
    if not user_dept:
        raise HTTPException(status_code=404, detail="用户不在该组织中")
    
    # 获取用户信息
    user = db.query(User).filter(User.id == user_id).first()
    
    # 删除关联
    db.delete(user_dept)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.ORGANIZATION,
        action=LogAction.REMOVE,
        description=f"从组织 {department.name} 中移除成员 {user.username}",
        request=req
    )
    
    return {
        "code": 200,
        "message": "移除成功",
        "data": None
    }


@router.get("/departments/{dept_id}/available-users")
def get_available_users_for_department(
    dept_id: int,
    search: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取可添加到组织的用户列表（排除已在组织中的用户）"""
    # 检查组织是否存在
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="组织不存在")
    
    # 获取已在组织中的用户ID
    existing_user_ids = [ud.user_id for ud in db.query(UserDepartment).filter(UserDepartment.department_id == dept_id).all()]
    
    # 查询所有用户，排除已在组织中的
    query = db.query(User).filter(User.status == 1)  # 只查询启用的用户
    if existing_user_ids:
        query = query.filter(~User.id.in_(existing_user_ids))
    
    # 搜索功能
    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (User.username.ilike(search_pattern)) |
            (User.full_name.ilike(search_pattern)) |
            (User.email.ilike(search_pattern))
        )
    
    users = query.limit(50).all()  # 限制返回数量
    
    return {
        "code": 200,
        "message": "success",
        "data": [
            {
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "email": u.email
            } for u in users
        ]
    }


class AddDepartmentMembersRequest(BaseModel):
    user_ids: List[int]


@router.post("/departments/{dept_id}/members")
def add_department_members(
    req: Request,
    dept_id: int,
    body: AddDepartmentMembersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加组织成员"""
    # 检查组织是否存在
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="组织不存在")
    
    added_users = []
    for user_id in body.user_ids:
        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            continue
        
        # 检查用户是否已在组织中
        existing = db.query(UserDepartment).filter(
            UserDepartment.department_id == dept_id,
            UserDepartment.user_id == user_id
        ).first()
        if existing:
            continue
        
        # 添加关联
        user_dept = UserDepartment(department_id=dept_id, user_id=user_id)
        db.add(user_dept)
        added_users.append(user.username)
    
    db.commit()
    
    if added_users:
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.ORGANIZATION,
            action=LogAction.ASSIGN,
            description=f"向组织 {department.name} 添加成员：{', '.join(added_users)}",
            request=req
        )
    
    return {
        "code": 200,
        "message": f"成功添加 {len(added_users)} 个成员",
        "data": None
    }
