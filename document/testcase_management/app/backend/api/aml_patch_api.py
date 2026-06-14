"""
AML Patch 独立API - 支持账号密码认证

提供完整的CRUD操作，不依赖JWT Token认证
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import Optional, List
from database import get_db
from models import AmlPatch, AmlProject, User
from utils.aml_patch_validators import validate_patch_data, format_validation_errors
from utils.permissions import check_permission
from utils.logger import log_operation, LogAction, LogModule
from api.aml_patch import _sync_patch_to_zmind, _send_sync_failure_notification
import json
import re

router = APIRouter(prefix="/aml-patch-api", tags=["aml-patch-api"])


class AmlPatchApiLoginRequest(BaseModel):
    username: str
    password: str


class AmlPatchApiLoginResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[int] = None
    username: Optional[str] = None


class AmlPatchApiCreate(BaseModel):
    project: str
    feature_branch: str
    corresponding_directory: str
    commit_record: str
    zmind_numbers: List[str]
    amlogic_jira: str
    patch_provider: str
    is_odm_exclusive: str
    root_cause: str
    patch_solution: str
    impact_scope: str
    aml_sri_result: str
    zeasn_merge_record: Optional[str] = None
    remarks: Optional[str] = None

    @field_validator('project')
    @classmethod
    def validate_project(cls, v):
        if not v or not v.strip():
            raise ValueError('项目不能为空')
        return v.strip().strip()

    @field_validator('zmind_numbers')
    @classmethod
    def validate_zmind_numbers(cls, v):
        if not v or not isinstance(v, list) or len(v) == 0:
            raise ValueError('Zmind号不能为空')
        return v

    @field_validator('feature_branch')
    @classmethod
    def validate_feature_branch(cls, v):
        if not v or not v.strip():
            raise ValueError('代码分支不能为空')
        return v.strip()

    @field_validator('corresponding_directory')
    @classmethod
    def validate_corresponding_directory(cls, v):
        if not v or not v.strip():
            raise ValueError('代码路径不能为空')
        return v.strip()

    @field_validator('commit_record')
    @classmethod
    def validate_commit_record(cls, v):
        if not v or not v.strip():
            raise ValueError('commit message不能为空')
        return v.strip()

    @field_validator('amlogic_jira')
    @classmethod
    def validate_amlogic_jira(cls, v):
        if not v or not v.strip():
            raise ValueError('Amlogic Jira不能为空')
        return v.strip()

    @field_validator('patch_provider')
    @classmethod
    def validate_patch_provider(cls, v):
        if not v or not v.strip():
            raise ValueError('patch提供人不能为空')
        return v.strip()

    @field_validator('is_odm_exclusive')
    @classmethod
    def validate_is_odm_exclusive(cls, v):
        if not v or not v.strip():
            raise ValueError('该ODM专属不能为空')
        if v not in ['是', '否']:
            raise ValueError('该ODM专属必须是 是 或 否')
        return v.strip()

    @field_validator('root_cause')
    @classmethod
    def validate_root_cause(cls, v):
        if not v or not v.strip():
            raise ValueError('Root Cause不能为空')
        return v.strip()

    @field_validator('patch_solution')
    @classmethod
    def validate_patch_solution(cls, v):
        if not v or not v.strip():
            raise ValueError('解决方案不能为空')
        return v.strip()

    @field_validator('impact_scope')
    @classmethod
    def validate_impact_scope(cls, v):
        if not v or not v.strip():
            raise ValueError('推荐测试范围不能为空')
        return v.strip()

    @field_validator('aml_sri_result')
    @classmethod
    def validate_aml_sri_result(cls, v):
        if not v or not v.strip():
            raise ValueError('Aml SRI自测结果不能为空')
        valid_options = ['Pass', 'Failed', '无法测试', '未测试']
        if v not in valid_options:
            raise ValueError(f'Aml SRI自测结果必须是: {", ".join(valid_options)}')
        return v.strip()


class AmlPatchApiUpdate(BaseModel):
    project: Optional[str] = None
    feature_branch: Optional[str] = None
    corresponding_directory: Optional[str] = None
    commit_record: Optional[str] = None
    zmind_numbers: Optional[List[str]] = None
    amlogic_jira: Optional[str] = None
    patch_provider: Optional[str] = None
    is_odm_exclusive: Optional[str] = None
    root_cause: Optional[str] = None
    patch_solution: Optional[str] = None
    impact_scope: Optional[str] = None
    aml_sri_result: Optional[str] = None
    zeasn_merge_record: Optional[str] = None
    remarks: Optional[str] = None

    @field_validator('project')
    @classmethod
    def validate_project(cls, v):
        if v and v.strip():
            return v.strip()
        return v

    @field_validator('zmind_numbers')
    @classmethod
    def validate_zmind_numbers(cls, v):
        if v and isinstance(v, list) and len(v) > 0:
            return v
        return v

    @field_validator('feature_branch')
    @classmethod
    def validate_feature_branch(cls, v):
        if v and v.strip():
            return v.strip()
        return v

    @field_validator('corresponding_directory')
    @classmethod
    def validate_corresponding_directory(cls, v):
        if v and v.strip():
            return v.strip()
        return v

    @field_validator('commit_record')
    @classmethod
    def validate_commit_record(cls, v):
        if v and v.strip():
            return v.strip()
        return v

    @field_validator('amlogic_jira')
    @classmethod
    def validate_amlogic_jira(cls, v):
        if v and v.strip():
            return v.strip()
        return v

    @field_validator('patch_provider')
    @classmethod
    def validate_patch_provider(cls, v):
        if v and v.strip():
            return v.strip()
        return v

    @field_validator('is_odm_exclusive')
    @classmethod
    def validate_is_odm_exclusive(cls, v):
        if not v:
            return v
        if v not in ['是', '否']:
            raise ValueError('该ODM专属必须是 是 或 否')
        return v.strip()

    @field_validator('root_cause')
    @classmethod
    def validate_root_cause(cls, v):
        if v and v.strip():
            return v.strip()
        return v

    @field_validator('patch_solution')
    @classmethod
    def validate_patch_solution(cls, v):
        if v and v.strip():
            return v.strip()
        return v

    @field_validator('impact_scope')
    @classmethod
    def validate_impact_scope(cls, v):
        if v and v.strip():
            return v.strip()
        return v

    @field_validator('aml_sri_result')
    @classmethod
    def validate_aml_sri_result(cls, v):
        if not v:
            return v
        valid_options = ['Pass', 'Failed', '无法测试', '未测试']
        if v not in valid_options:
            raise ValueError(f'Aml SRI自测结果必须是: {", ".join(valid_options)}')
        return v.strip()


def parse_zmind_numbers(zmind_numbers):
    if isinstance(zmind_numbers, str):
        try:
            return json.loads(zmind_numbers)
        except:
            return []
    return zmind_numbers or []


def patch_to_dict(p):
    result = {
        "id": p.id,
        "project": p.project,
        "feature_branch": p.feature_branch,
        "corresponding_directory": p.corresponding_directory,
        "commit_record": p.commit_record,
        "zmind_numbers": parse_zmind_numbers(p.zmind_numbers),
        "amlogic_jira": p.amlogic_jira,
        "patch_provider": p.patch_provider,
        "is_odm_exclusive": p.is_odm_exclusive,
        "root_cause": p.root_cause,
        "patch_solution": p.patch_solution,
        "impact_scope": p.impact_scope,
        "aml_sri_result": p.aml_sri_result,
        "zeasn_merge_record": p.zeasn_merge_record,
        "remarks": p.remarks,
        "sync_status": p.sync_status,
        "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else None,
        "updated_at": p.updated_at.strftime("%Y-%m-%d %H:%M:%S") if p.updated_at else None,
        "created_by": p.created_by
    }
    return result


def verify_password(plain_password: str, hashed_password: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def authenticate_user(username: str, password: str, db: Session) -> Optional[User]:
    """验证用户账号密码"""
    if not username or not password:
        return None
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    
    if user.status == 0:
        return None
    
    if not verify_password(password, user.password):
        return None
    
    return user


def get_authenticated_user(request: AmlPatchApiLoginRequest, db: Session) -> User:
    """获取认证用户依赖"""
    user = authenticate_user(request.username, request.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return user


@router.post("/login", response_model=AmlPatchApiLoginResponse)
def login(
    credentials: AmlPatchApiLoginRequest,
    db: Session = Depends(get_db),
    request: Request = None
):
    """AML Patch API登录接口 - 账号密码认证"""
    user = authenticate_user(credentials.username, credentials.password, db)
    
    if not user:
        return AmlPatchApiLoginResponse(
            success=False,
            message="用户名或密码错误"
        )

    log_operation(
        db=db,
        user_id=user.id,
        username=user.username,
        module=LogModule.AML_PATCH,
        action=LogAction.LOGIN,
        description=f"AML Patch API登录成功",
        request=request,
        response_status=200
    )
    
    return AmlPatchApiLoginResponse(
        success=True,
        message="登录成功",
        user_id=user.id,
        username=user.username
    )


@router.get("/projects")
def get_aml_projects(
    username: str = Query(..., description="用户名"),
    password: str = Query(..., description="密码"),
    db: Session = Depends(get_db),
    request: Request = None
):
    """获取AML项目列表 - 需要认证"""
    user = authenticate_user(username, password, db)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    projects = db.query(AmlProject).order_by(AmlProject.name).all()

    log_operation(
        db=db,
        user_id=user.id,
        username=user.username,
        module=LogModule.AML_PATCH,
        action=LogAction.VIEW,
        description=f"查询AML项目列表",
        request=request
    )
    
    return {"data": [{"id": p.id, "name": p.name, "description": p.description} for p in projects]}


@router.get("")
def get_aml_patches(
    username: str = Query(..., description="用户名"),
    password: str = Query(..., description="密码"),
    project: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    request: Request = None
):
    """查询AML Patch列表 - 需要认证"""
    user = authenticate_user(username, password, db)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    query = db.query(AmlPatch)
    
    if project:
        query = query.filter(AmlPatch.project == project)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (AmlPatch.feature_branch.contains(search_pattern)) |
            (AmlPatch.corresponding_directory.contains(search_pattern)) |
            (AmlPatch.commit_record.contains(search_pattern)) |
            (AmlPatch.zmind_numbers.contains(search_pattern)) |
            (AmlPatch.amlogic_jira.contains(search_pattern)) |
            (AmlPatch.patch_provider.contains(search_pattern)) |
            (AmlPatch.root_cause.contains(search_pattern)) |
            (AmlPatch.patch_solution.contains(search_pattern)) |
            (AmlPatch.impact_scope.contains(search_pattern)) |
            (AmlPatch.remarks.contains(search_pattern))
        )
    
    total = query.count()
    patches = query.order_by(AmlPatch.updated_at.desc().nullslast()).offset((page - 1) * page_size).limit(page_size).all()

    log_operation(
        db=db,
        user_id=user.id,
        username=user.username,
        module=LogModule.AML_PATCH,
        action=LogAction.SEARCH,
        description=f"查询AML Patch列表: 项目={project or '全部'}, 搜索={search or '无'}, 结果数={total}",
        request=request
    )
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": [patch_to_dict(p) for p in patches]
    }


@router.get("/{identifier}")
def get_aml_patch_by_identifier(
    identifier: int,
    username: str = Query(..., description="用户名"),
    password: str = Query(..., description="密码"),
    db: Session = Depends(get_db),
    request: Request = None
):
    """根据序号(ID)查询AML Patch详情"""
    user = authenticate_user(username, password, db)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    patch = db.query(AmlPatch).filter(AmlPatch.id == identifier).first()
    if not patch:
        raise HTTPException(status_code=404, detail="AML Patch不存在")

    log_operation(
        db=db,
        user_id=user.id,
        username=user.username,
        module=LogModule.AML_PATCH,
        action=LogAction.VIEW,
        description=f"查看AML Patch详情: ID={patch.id}, 项目={patch.project}",
        request=request
    )

    return patch_to_dict(patch)


@router.post("")
def create_aml_patch(
    patch_data: AmlPatchApiCreate,
    username: str = Query(..., description="用户名"),
    password: str = Query(..., description="密码"),
    db: Session = Depends(get_db),
    request: Request = None
):
    """创建AML Patch - 需要认证+权限"""
    user = authenticate_user(username, password, db)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not check_permission(user, "amlPatch.create"):
        raise HTTPException(status_code=403, detail="没有权限创建AML Patch")

    validation_data = patch_data.model_dump(exclude_none=True)
    validation_errors = validate_patch_data(validation_data)
    if validation_errors:
        formatted_errors = format_validation_errors(validation_errors)
        raise HTTPException(status_code=400, detail=formatted_errors)

    try:
        patch = AmlPatch(
            project=patch_data.project,
            feature_branch=patch_data.feature_branch,
            corresponding_directory=patch_data.corresponding_directory,
            commit_record=patch_data.commit_record,
            zmind_numbers=json.dumps(patch_data.zmind_numbers or []) if patch_data.zmind_numbers else None,
            amlogic_jira=patch_data.amlogic_jira,
            patch_provider=patch_data.patch_provider,
            is_odm_exclusive=patch_data.is_odm_exclusive,
            root_cause=patch_data.root_cause,
            patch_solution=patch_data.patch_solution,
            impact_scope=patch_data.impact_scope,
            aml_sri_result=patch_data.aml_sri_result,
            zeasn_merge_record=patch_data.zeasn_merge_record,
            remarks=patch_data.remarks,
            sync_status=1,
            created_by=user.id
        )
        db.add(patch)
        db.commit()
        db.refresh(patch)

        log_operation(
            db=db,
            user_id=user.id,
            username=user.username,
            module=LogModule.AML_PATCH,
            action=LogAction.CREATE,
            description=f"API创建AML Patch: ID={patch.id}, 项目={patch.project}",
            request=request
        )

        if patch_data.zmind_numbers:
            try:
                failed_details = _sync_patch_to_zmind(patch, db)
                if failed_details:
                    _send_sync_failure_notification(db, failed_details)
            except Exception:
                pass

        return patch_to_dict(patch)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.put("/{identifier}")
def update_aml_patch(
    identifier: int,
    patch_data: AmlPatchApiUpdate,
    username: str = Query(..., description="用户名"),
    password: str = Query(..., description="密码"),
    db: Session = Depends(get_db),
    request: Request = None
):
    """根据序号更新AML Patch - 需要认证+权限"""
    user = authenticate_user(username, password, db)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not check_permission(user, "amlPatch.edit"):
        raise HTTPException(status_code=403, detail="没有权限编辑AML Patch")

    try:
        patch = db.query(AmlPatch).filter(AmlPatch.id == identifier).first()
        if not patch:
            raise HTTPException(status_code=404, detail="AML Patch不存在")

        sync_fields = ['root_cause', 'patch_solution', 'impact_scope', 'is_odm_exclusive', 'patch_provider', 'aml_sri_result', 'remarks']
        need_sync = False

        if patch_data.project is not None:
            patch.project = patch_data.project
        if patch_data.feature_branch is not None:
            patch.feature_branch = patch_data.feature_branch
        if patch_data.corresponding_directory is not None:
            patch.corresponding_directory = patch_data.corresponding_directory
        if patch_data.commit_record is not None:
            patch.commit_record = patch_data.commit_record
        if patch_data.zmind_numbers is not None:
            patch.zmind_numbers = json.dumps(patch_data.zmind_numbers)
        if patch_data.amlogic_jira is not None:
            patch.amlogic_jira = patch_data.amlogic_jira
        if patch_data.patch_provider is not None:
            if patch.patch_provider != patch_data.patch_provider and 'patch_provider' in sync_fields:
                need_sync = True
            patch.patch_provider = patch_data.patch_provider
        if patch_data.is_odm_exclusive is not None:
            if patch.is_odm_exclusive != patch_data.is_odm_exclusive and 'is_odm_exclusive' in sync_fields:
                need_sync = True
            patch.is_odm_exclusive = patch_data.is_odm_exclusive
        if patch_data.root_cause is not None:
            if patch.root_cause != patch_data.root_cause and 'root_cause' in sync_fields:
                need_sync = True
            patch.root_cause = patch_data.root_cause
        if patch_data.patch_solution is not None:
            if patch.patch_solution != patch_data.patch_solution and 'patch_solution' in sync_fields:
                need_sync = True
            patch.patch_solution = patch_data.patch_solution
        if patch_data.impact_scope is not None:
            if patch.impact_scope != patch_data.impact_scope and 'impact_scope' in sync_fields:
                need_sync = True
            patch.impact_scope = patch_data.impact_scope
        if patch_data.aml_sri_result is not None:
            if patch.aml_sri_result != patch_data.aml_sri_result and 'aml_sri_result' in sync_fields:
                need_sync = True
            patch.aml_sri_result = patch_data.aml_sri_result
        if patch_data.zeasn_merge_record is not None:
            patch.zeasn_merge_record = patch_data.zeasn_merge_record
        if patch_data.remarks is not None:
            if patch.remarks != patch_data.remarks and 'remarks' in sync_fields:
                need_sync = True
            patch.remarks = patch_data.remarks

        patch.updated_by = user.id

        if need_sync:
            patch.sync_status = 1
            db.commit()
            zmind_nums = json.loads(patch.zmind_numbers) if patch.zmind_numbers else []
            if zmind_nums:
                try:
                    failed_details = _sync_patch_to_zmind(patch, db)
                    if failed_details:
                        _send_sync_failure_notification(db, failed_details)
                except Exception:
                    pass
        else:
            db.commit()
        db.refresh(patch)

        log_operation(
            db=db,
            user_id=user.id,
            username=user.username,
            module=LogModule.AML_PATCH,
            action=LogAction.UPDATE,
            description=f"API更新AML Patch: ID={patch.id}, 项目={patch.project}",
            request=request
        )

        return patch_to_dict(patch)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/{identifier}")
def delete_aml_patch(
    identifier: int,
    username: str = Query(..., description="用户名"),
    password: str = Query(..., description="密码"),
    db: Session = Depends(get_db),
    request: Request = None
):
    """根据序号删除AML Patch - 需要认证+权限"""
    user = authenticate_user(username, password, db)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not check_permission(user, "amlPatch.delete"):
        raise HTTPException(status_code=403, detail="没有权限删除AML Patch")

    patch = db.query(AmlPatch).filter(AmlPatch.id == identifier).first()
    if not patch:
        raise HTTPException(status_code=404, detail="AML Patch不存在")

    patch_project = patch.project
    db.delete(patch)
    db.commit()

    log_operation(
        db=db,
        user_id=user.id,
        username=user.username,
        module=LogModule.AML_PATCH,
        action=LogAction.DELETE,
        description=f"API删除AML Patch: ID={identifier}, 项目={patch_project}",
        request=request
    )

    return {"message": "删除成功", "id": identifier}


@router.get("/export")
def export_aml_patches(
    username: str = Query(..., description="用户名"),
    password: str = Query(..., description="密码"),
    project: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    request: Request = None
):
    """导出AML Patch - 需要认证"""
    user = authenticate_user(username, password, db)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    query = db.query(AmlPatch)

    if project:
        query = query.filter(AmlPatch.project == project)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (AmlPatch.feature_branch.contains(search_pattern)) |
            (AmlPatch.corresponding_directory.contains(search_pattern)) |
            (AmlPatch.commit_record.contains(search_pattern)) |
            (AmlPatch.zmind_numbers.contains(search_pattern)) |
            (AmlPatch.amlogic_jira.contains(search_pattern)) |
            (AmlPatch.patch_provider.contains(search_pattern)) |
            (AmlPatch.root_cause.contains(search_pattern)) |
            (AmlPatch.patch_solution.contains(search_pattern)) |
            (AmlPatch.impact_scope.contains(search_pattern)) |
            (AmlPatch.remarks.contains(search_pattern))
        )

    patches = query.order_by(AmlPatch.updated_at.desc().nullslast()).all()

    log_operation(
        db=db,
        user_id=user.id,
        username=user.username,
        module=LogModule.AML_PATCH,
        action=LogAction.EXPORT,
        description=f"导出AML Patch: 项目={project or '全部'}, 搜索={search or '无'}, 导出数量={len(patches)}",
        request=request
    )

    import csv
    import io
    from fastapi.responses import StreamingResponse

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        '序号', '项目', '代码分支', '代码路径', 'commit message', 'Zmind号',
        'Amlogic Jira', 'patch提供人', '该ODM专属',
        'Root Cause', '解决方案', '推荐测试范围', 'Aml SRI自测结果',
        'Zeasn合入记录', '备注', '更新时间'
    ])

    for p in patches:
        zmind_nums = ';'.join(str(n) for n in parse_zmind_numbers(p.zmind_numbers)) if p.zmind_numbers else ''
        writer.writerow([
            p.id,
            p.project or '',
            p.feature_branch or '',
            p.corresponding_directory or '',
            p.commit_record or '',
            zmind_nums,
            p.amlogic_jira or '',
            p.patch_provider or '',
            p.is_odm_exclusive or '',
            p.root_cause or '',
            p.patch_solution or '',
            p.impact_scope or '',
            p.aml_sri_result or '',
            p.zeasn_merge_record or '',
            p.remarks or '',
            p.updated_at.strftime("%Y-%m-%d %H:%M:%S") if p.updated_at else ''
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=aml_patch_export.csv"}
    )