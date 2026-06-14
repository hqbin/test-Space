from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import Optional, List
from database import get_db
from auth import get_current_user
from models import AmlPatch, AmlProject, User, Role, UserRole, Notification, NotificationRecipient, DingtalkBot
from utils.permissions import check_permission
from utils.logger import log_operation, LogAction, LogModule
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/aml-patch", tags=["aml-patch"])


class AmlPatchCreate(BaseModel):
    project: str
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


class AmlPatchUpdate(BaseModel):
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

    @field_validator('is_odm_exclusive')
    @classmethod
    def validate_is_odm_exclusive(cls, v):
        if not v:
            return v
        if v not in ['是', '否']:
            raise ValueError('该ODM专属必须是 是 或 否')
        return v.strip()

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
    import json
    if isinstance(zmind_numbers, str):
        try:
            return json.loads(zmind_numbers)
        except:
            return []
    return zmind_numbers or []


def _sync_patch_to_zmind(patch, db):
    import requests
    import urllib3
    import time
    from config import ZMIND_API_KEY, ZMIND_API_URL

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    zmind_http = requests.Session()
    zmind_http.verify = False
    ZMIND_TIMEOUT = 300
    MAX_RETRIES = 5

    headers = {
        'X-Redmine-API-Key': ZMIND_API_KEY,
        'Content-Type': 'application/json'
    }

    zmind_numbers = parse_zmind_numbers(patch.zmind_numbers)
    if not zmind_numbers:
        return []

    notes = f"Auto-sync from TeVaMaT: https://tms.zeasn.com/aml-patch\nID：{patch.id}\nRoot Cause: {patch.root_cause or ''}\nSolution: {patch.patch_solution or ''}\n推荐测试范围: {patch.impact_scope or ''}\n该ODM专属: {patch.is_odm_exclusive or ''}\nPatch提供人: {patch.patch_provider or ''}\nAml SRI自测结果: {patch.aml_sri_result or ''}\n备注: {patch.remarks or ''}"
    update_data = {"issue": {"notes": notes}}

    def _put(zmind_num):
        try:
            r = zmind_http.put(
                f"{ZMIND_API_URL}/issues/{zmind_num}.json",
                headers=headers,
                json=update_data,
                timeout=ZMIND_TIMEOUT
            )
            if r.status_code in [200, 204]:
                return True, None
            if r.status_code == 404:
                return False, f"Zmind Issue #{zmind_num} 不存在"
            if r.status_code == 429:
                retry_after = r.headers.get('Retry-After')
                if retry_after:
                    time.sleep(min(int(retry_after), 60))
                return False, f"请求过于频繁，被限流"
            # 尝试获取错误详情
            try:
                error_data = r.json()
                error_msg = error_data.get('errors', [r.text[:200]])[0] if isinstance(error_data.get('errors'), list) else r.text[:200]
            except:
                error_msg = f"HTTP {r.status_code}: {r.text[:200]}"
            return False, error_msg
        except requests.exceptions.Timeout:
            return False, "Zmind API 请求超时"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到 Zmind API"
        except Exception as e:
            return False, str(e)[:200]

    failed = {}  # {zmind_num: error_msg}
    for zmind_num in zmind_numbers:
        success, error = _put(zmind_num)
        if not success:
            failed[zmind_num] = error

    for attempt in range(MAX_RETRIES - 1):
        if not failed:
            break
        time.sleep(min(2 ** attempt, 30))
        still_failed = {}
        for zmind_num, old_error in failed.items():
            success, error = _put(zmind_num)
            if not success:
                still_failed[zmind_num] = error
        failed = still_failed

    patch.sync_status = 3 if not failed else 2
    db.commit()
    
    # 返回失败的 Zmind 号列表（包含具体原因）
    failed_details = [{"patch_id": patch.id, "zmind_num": num, "error": error} for num, error in failed.items()]
    if failed_details:
        logger.warning(f"AML Patch Zmind同步失败: Patch ID={patch.id}, 失败详情={failed_details}, sync_status={patch.sync_status}")
    else:
        logger.info(f"AML Patch Zmind同步成功: Patch ID={patch.id}, sync_status={patch.sync_status}")
    return failed_details


def _send_sync_failure_notification(db, failed_details, total_count=1, success_count=0):
    """发送同步失败通知（系统通知 + 钉钉通知）"""
    import json
    
    if not failed_details:
        logger.info("_send_sync_failure_notification: 没有失败详情，跳过通知")
        return
    
    logger.info(f"_send_sync_failure_notification: 开始发送通知, failed_details={failed_details}, total_count={total_count}, success_count={success_count}")
    
    try:
        from datetime import datetime
        
        failed_count = len(failed_details)
        if total_count == 1:
            total_count = failed_count + success_count
        
        # 1. 创建系统通知
        admin_ids = set()
        super_admin = db.query(User).filter(User.username == 'admin', User.status == 1).first()
        if super_admin:
            admin_ids.add(super_admin.id)
        
        admin_roles = db.query(Role).filter(
            Role.name.contains('管理员') | Role.name.contains('Admin')
        ).all()
        if admin_roles:
            role_ids = [r.id for r in admin_roles]
            user_roles = db.query(UserRole).filter(UserRole.role_id.in_(role_ids)).all()
            for ur in user_roles:
                admin_ids.add(ur.user_id)
        
        logger.info(f"_send_sync_failure_notification: 找到管理员IDs={admin_ids}")
        
        if admin_ids:
            failed_summary = "\n".join([
                f"- Patch #{d.get('patch_id')}" + 
                (f" → Zmind #{d.get('zmind_num')}: {d.get('error')}" if d.get('zmind_num') else f": {d.get('error')}")
                for d in failed_details[:20]
            ])
            if len(failed_details) > 20:
                failed_summary += f"\n... 还有 {len(failed_details) - 20} 条失败记录"
            
            notification = Notification(
                title="AML Patch Zmind同步失败",
                content=f"Zmind同步完成，共 {total_count} 条记录，成功 {success_count} 条，失败 {failed_count} 条。\n\n失败详情：\n{failed_summary}",
                notification_type='system',
                event_type='zmind_sync_failed',
                is_system=True,
                created_at=datetime.now()
            )
            db.add(notification)
            db.flush()
            
            for uid in admin_ids:
                recipient = NotificationRecipient(
                    notification_id=notification.id,
                    user_id=uid,
                    is_read=False,
                    created_at=datetime.now()
                )
                db.add(recipient)
            
            db.commit()
            logger.info(f"_send_sync_failure_notification: 系统通知已创建, notification_id={notification.id}")
        
        # 2. 发送钉钉通知
        bots = db.query(DingtalkBot).filter(DingtalkBot.is_active == True).all()
        logger.info(f"_send_sync_failure_notification: 活跃的钉钉机器人数量={len(bots)}")
        
        system_bots = []
        for bot in bots:
            try:
                types = json.loads(bot.notification_types) if bot.notification_types else []
                logger.info(f"_send_sync_failure_notification: 机器人 {bot.name}(ID={bot.id}), notification_types={types}")
            except (json.JSONDecodeError, TypeError):
                types = []
                logger.warning(f"_send_sync_failure_notification: 机器人 {bot.name}(ID={bot.id}) notification_types解析失败")
            if 'system' in types:
                system_bots.append(bot)
        
        logger.info(f"_send_sync_failure_notification: 配置了system类型的机器人数量={len(system_bots)}")
        
        if system_bots:
            from api.dingtalk_bot import _send_dingtalk_message
            
            failed_lines = []
            for d in failed_details[:10]:
                if d.get('zmind_num'):
                    failed_lines.append(f"- Patch #{d.get('patch_id')} → Zmind #{d.get('zmind_num')}: {d.get('error')}")
                else:
                    failed_lines.append(f"- Patch #{d.get('patch_id')}: {d.get('error')}")
            
            dingtalk_content = (
                f"### AML Patch Zmind同步失败  \n\n"
                f"**同步总数：** {total_count}  \n"
            )
            if success_count > 0:
                dingtalk_content += f"**成功：** {success_count}  \n"
            dingtalk_content += (
                f"**失败：** {failed_count}  \n\n"
                f"**失败详情：**  \n" + "  \n".join(failed_lines)
            )
            if len(failed_details) > 10:
                dingtalk_content += f"  \n\n... 还有 {len(failed_details) - 10} 条失败记录，请登录系统查看完整列表。"
            
            title = "【AML Patch】Zmind同步失败"
            
            sent_webhooks = set()
            for bot in system_bots:
                if bot.webhook_url in sent_webhooks:
                    continue
                logger.info(f"_send_sync_failure_notification: 发送钉钉通知到 {bot.name}(ID={bot.id})")
                result = _send_dingtalk_message(bot, title, dingtalk_content)
                logger.info(f"_send_sync_failure_notification: 钉钉通知结果={result}")
                sent_webhooks.add(bot.webhook_url)
        else:
            logger.warning("_send_sync_failure_notification: 没有配置system类型的钉钉机器人")
    except Exception as e:
        logger.error(f"_send_sync_failure_notification: 发送通知异常: {e}", exc_info=True)


def patch_to_dict(p):
    return {
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


class AmlProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


@router.get("/projects", response_model=dict)
def get_aml_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    projects = db.query(AmlProject).order_by(AmlProject.name).all()
    return {"data": [{"id": p.id, "name": p.name, "description": p.description} for p in projects]}


@router.post("/projects", response_model=dict)
def create_aml_project(
    project_data: AmlProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    existing = db.query(AmlProject).filter(AmlProject.name == project_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="项目已存在")
    
    project = AmlProject(
        name=project_data.name,
        description=project_data.description,
        created_by=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.AML_PATCH,
        action=LogAction.CREATE,
        description=f"创建AML项目: {project.name}",
        request=request
    )
    
    return {"id": project.id, "name": project.name, "description": project.description}


@router.get("", response_model=dict)
def get_aml_patches(
    project: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
    # 按更新时间降序排序（包含年月日时分秒），空值排最后
    patches = query.order_by(AmlPatch.updated_at.desc().nullslast()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": [patch_to_dict(p) for p in patches]
    }


@router.get("/export")
def export_aml_patches(
    project: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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


@router.get("/{patch_id}", response_model=dict)
def get_aml_patch_detail(
    patch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patch = db.query(AmlPatch).filter(AmlPatch.id == patch_id).first()
    if not patch:
        raise HTTPException(status_code=404, detail="AML Patch不存在")
    
    return patch_to_dict(patch)


@router.post("", response_model=dict)
def create_aml_patch(
    patch_data: AmlPatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not check_permission(current_user, "amlPatch.create"):
        raise HTTPException(status_code=403, detail="没有权限创建AML Patch")

    try:
        import json
        from config import ZMIND_API_KEY, ZMIND_API_URL
        import requests
        import urllib3

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
            created_by=current_user.id
        )
        db.add(patch)
        db.commit()
        db.refresh(patch)

        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.AML_PATCH,
            action=LogAction.CREATE,
            description=f"创建AML Patch: ID={patch.id}, 项目={patch.project}",
            request=request
        )

        if patch_data.zmind_numbers:
            try:
                failed_details = _sync_patch_to_zmind(patch, db)
                if failed_details:
                    _send_sync_failure_notification(db, failed_details)
            except Exception as e:
                pass

        return patch_to_dict(patch)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}\n{traceback.format_exc()}")


@router.put("/{patch_id}", response_model=dict)
def update_aml_patch(
    patch_id: int,
    patch_data: AmlPatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not check_permission(current_user, "amlPatch.edit"):
        raise HTTPException(status_code=403, detail="没有权限编辑AML Patch")

    try:
        import json
        from config import ZMIND_API_KEY, ZMIND_API_URL
        import requests
        import urllib3

        patch = db.query(AmlPatch).filter(AmlPatch.id == patch_id).first()
        if not patch:
            raise HTTPException(status_code=404, detail="AML Patch不存在")

        sync_fields = ['root_cause', 'patch_solution', 'impact_scope', 'is_odm_exclusive', 'patch_provider', 'aml_sri_result', 'remarks']
        need_sync = False

        # 记录原始值用于比较
        old_values = {
            'root_cause': patch.root_cause,
            'patch_solution': patch.patch_solution,
            'impact_scope': patch.impact_scope,
            'is_odm_exclusive': patch.is_odm_exclusive,
            'patch_provider': patch.patch_provider,
            'aml_sri_result': patch.aml_sri_result,
            'remarks': patch.remarks
        }

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

        # 记录调试信息
        logger.info(f"AML Patch编辑调试: ID={patch.id}, need_sync={need_sync}, zmind_numbers={patch.zmind_numbers}")
        if need_sync:
            changed_fields = []
            for field in sync_fields:
                old_val = old_values.get(field)
                new_val = getattr(patch, field)
                if old_val != new_val:
                    changed_fields.append(f"{field}: '{old_val}' -> '{new_val}'")
            logger.info(f"AML Patch编辑同步触发: 变更字段={changed_fields}")

        patch.updated_by = current_user.id
        db.commit()
        db.refresh(patch)

        if need_sync:
            patch.sync_status = 1
            db.commit()
            zmind_nums = parse_zmind_numbers(patch.zmind_numbers)
            if zmind_nums:
                try:
                    failed_details = _sync_patch_to_zmind(patch, db)
                    if failed_details:
                        _send_sync_failure_notification(db, failed_details)
                except Exception as e:
                    pass
        else:
            db.commit()
        
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.AML_PATCH,
            action=LogAction.UPDATE,
            description=f"更新AML Patch: ID={patch.id}, 项目={patch.project}, need_sync={need_sync}, zmind_nums={patch.zmind_numbers}",
            request=request
        )

        return patch_to_dict(patch)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}\n{traceback.format_exc()}")


@router.delete("/{patch_id}", response_model=dict)
def delete_aml_patch(
    patch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    if not check_permission(current_user, "amlPatch.delete"):
        raise HTTPException(status_code=403, detail="没有权限删除AML Patch")
    
    patch = db.query(AmlPatch).filter(AmlPatch.id == patch_id).first()
    if not patch:
        raise HTTPException(status_code=404, detail="AML Patch不存在")
    
    patch_project = patch.project
    db.delete(patch)
    db.commit()

    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.AML_PATCH,
        action=LogAction.DELETE,
        description=f"删除AML Patch: ID={patch_id}, 项目={patch_project}",
        request=request
    )
    
    return {"message": "删除成功"}


@router.post("/sync")
def sync_to_zmind(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """同步 AML Patch 到 Zmind（异步处理，SSE 实时通知前端）"""
    import json
    import requests
    import urllib3
    from config import ZMIND_API_KEY, ZMIND_API_URL
    from fastapi.responses import StreamingResponse
    
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    zmind_http = requests.Session()
    zmind_http.verify = False
    ZMIND_TIMEOUT = 300
    
    def generate_sse():
        try:
            def send_event(event_type, data):
                return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            
            def send_progress(current, total, status, message, patch_id=None, zmind_num=None):
                return send_event('progress', {
                    "current": current,
                    "total": total,
                    "status": status,
                    "message": message,
                    "patch_id": patch_id,
                    "zmind_num": zmind_num
                })
            
            send_event('status', {"status": "started", "message": "开始同步..."})
            
            patches = db.query(AmlPatch).filter(
                AmlPatch.zmind_numbers.isnot(None),
                AmlPatch.zmind_numbers != '',
                AmlPatch.zmind_numbers != '[]',
                AmlPatch.sync_status != 3
            ).order_by(AmlPatch.updated_at.desc()).all()
            
            total = len(patches)
            success_count = 0
            failed_count = 0
            failed_details = []
            
            yield send_progress(0, total, "processing", f"找到 {total} 条待同步记录")
            
            headers = {
                'X-Redmine-API-Key': ZMIND_API_KEY,
                'Content-Type': 'application/json'
            }
            
            for idx, patch in enumerate(patches):
                try:
                    zmind_numbers = parse_zmind_numbers(patch.zmind_numbers)
                    if not zmind_numbers:
                        yield send_progress(idx + 1, total, "skip", f"Patch #{patch.id} 无 Zmind 号，跳过")
                        continue
                    
                    yield send_progress(idx + 1, total, "processing", f"正在同步 Patch #{patch.id} ({', '.join(zmind_numbers)})", patch.id)
                    
                    all_success = True
                    for zmind_num in zmind_numbers:
                        try:
                            existing_response = zmind_http.get(
                                f"{ZMIND_API_URL}/issues/{zmind_num}.json",
                                headers=headers,
                                timeout=ZMIND_TIMEOUT
                            )
                            
                            if existing_response.status_code == 404:
                                failed_details.append({
                                    "patch_id": patch.id,
                                    "zmind_num": zmind_num,
                                    "error": f"Zmind Issue #{zmind_num} 不存在"
                                })
                                all_success = False
                                continue
                            
                            if existing_response.status_code != 200:
                                failed_details.append({
                                    "patch_id": patch.id,
                                    "zmind_num": zmind_num,
                                    "error": f"获取 Issue 失败: HTTP {existing_response.status_code}"
                                })
                                all_success = False
                                continue

                            update_data = {
                                "issue": {
                                    "notes": f"Auto-sync from TeVaMaT: https://tms.zeasn.com/aml-patch\nID：{patch.id}\nRoot Cause: {patch.root_cause or ''}\nSolution: {patch.patch_solution or ''}\n推荐测试范围: {patch.impact_scope or ''}\n该ODM专属: {patch.is_odm_exclusive or ''}\nPatch提供人: {patch.patch_provider or ''}\nAml SRI自测结果: {patch.aml_sri_result or ''}\n备注: {patch.remarks or ''}"
                                }
                            }
                            
                            update_response = zmind_http.put(
                                f"{ZMIND_API_URL}/issues/{zmind_num}.json",
                                headers=headers,
                                json=update_data,
                                timeout=ZMIND_TIMEOUT
                            )
                            
                            if update_response.status_code in [200, 204]:
                                yield send_event('zmind_success', {
                                    "patch_id": patch.id,
                                    "zmind_num": zmind_num,
                                    "message": f"成功同步到 Zmind #{zmind_num}"
                                })
                            else:
                                try:
                                    error_data = update_response.json()
                                    error_msg = error_data.get('errors', [update_response.text])[0]
                                except:
                                    error_msg = update_response.text[:200]
                                failed_details.append({
                                    "patch_id": patch.id,
                                    "zmind_num": zmind_num,
                                    "error": error_msg
                                })
                                all_success = False
                                
                        except requests.exceptions.Timeout:
                            failed_details.append({
                                "patch_id": patch.id,
                                "zmind_num": zmind_num,
                                "error": "Zmind API 超时"
                            })
                            all_success = False
                        except Exception as e:
                            failed_details.append({
                                "patch_id": patch.id,
                                "zmind_num": zmind_num,
                                "error": str(e)
                            })
                            all_success = False
                    
                    if all_success:
                        patch.sync_status = 3
                        db.commit()
                        success_count += 1
                        yield send_progress(idx + 1, total, "success", f"Patch #{patch.id} 同步完成")
                    else:
                        patch.sync_status = 2
                        db.commit()
                        failed_count += 1
                        yield send_progress(idx + 1, total, "failed", f"Patch #{patch.id} 部分 Zmind 号同步失败")
                        
                except Exception as e:
                    failed_count += 1
                    failed_details.append({
                        "patch_id": patch.id,
                        "error": str(e)
                    })
                    yield send_progress(idx + 1, total, "error", f"Patch #{patch.id} 同步失败: {str(e)}")
            
            # 如果有失败记录，发送通知
            if failed_count > 0:
                _send_sync_failure_notification(db, failed_details, total, success_count)

            yield send_event('complete', {
                "total": total,
                "success": success_count,
                "failed": failed_count,
                "details": failed_details,
                "message": f"同步完成！成功 {success_count} 条，失败 {failed_count} 条"
            })
            
        except Exception as e:
            yield send_event('error', {"message": f"同步过程出错: {str(e)}"})
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )