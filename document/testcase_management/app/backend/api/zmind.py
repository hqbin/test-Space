"""
Zmind API 集成
提供与 Zmind (Redmine) 系统的交互功能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import requests
import urllib3
import logging
from database import get_db
from auth import get_current_user
from models import User, TestPlan
from config import ZMIND_API_URL, ZMIND_API_KEY

# 禁用SSL警告（Zmind内网服务，verify=False时不显示警告）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

router = APIRouter()
logger = logging.getLogger(__name__)

# Zmind 服务器响应较慢，超时设置需要宽裕
ZMIND_TIMEOUT = 300  # 普通请求5分钟
ZMIND_UPLOAD_TIMEOUT = 300  # 文件上传5分钟

# 创建专用的HTTP客户端，跳过SSL验证（Zmind内网HTTPS证书兼容性问题）
zmind_http = requests.Session()
zmind_http.verify = False

class ZmindIssueCreate(BaseModel):
    """创建 Zmind Issue 的请求模型"""
    subject: str
    description: str
    tracker_id: int = 1  # Tracker类型，默认PR
    priority_id: int = 2  # 默认 Medium
    severity: str = "Minor"  # Severity 字段值
    issue_version: str = ""  # Issue Version 字段值（手动输入）
    tevama_id: Optional[str] = None  # TeVaMat ID 字段值（自定义字段ID: 40）
    testcase_id: Optional[int] = None  # 关联的测试用例 ID
    project_id: str  # Zmind项目ID
    assigned_to_id: Optional[int] = None  # 指派人ID
    fixed_version_id: Optional[int] = None  # 目标版本ID (Fixed Version自定义字段)
    category_id: Optional[int] = None  # 类别ID
    phase: Optional[str] = None  # Phase自定义字段（字段ID: 21）
    side_effect: Optional[str] = None  # Side Effect自定义字段（字段ID: 5）
    due_date: Optional[str] = None  # 计划完成日期 (YYYY-MM-DD格式)


class ZmindFieldOption(BaseModel):
    """Zmind 字段选项"""
    id: int
    name: str


class ZmindProjectOption(BaseModel):
    """Zmind 项目选项"""
    id: str
    name: str


class UserApiKeyUpdate(BaseModel):
    """更新用户API Key"""
    zmind_api_key: str


class TestPlanZmindProjectUpdate(BaseModel):
    """更新测试计划的Zmind项目"""
    zmind_project_id: str


@router.put("/api-key")
def update_user_api_key(
    data: UserApiKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新当前用户的Zmind API Key"""
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        user.zmind_api_key = data.zmind_api_key
        db.commit()
        
        return {
            "code": 200,
            "message": "API Key 更新成功",
            "data": None
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.get("/api-key")
def get_user_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的Zmind API Key"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "zmind_api_key": user.zmind_api_key or ""
        }
    }


@router.get("/projects")
def get_zmind_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户可访问的Zmind项目列表"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not user.zmind_api_key:
        raise HTTPException(status_code=400, detail="请先配置Zmind API Key")
    
    try:
        headers = {
            'X-Redmine-API-Key': user.zmind_api_key,
            'Content-Type': 'application/json'
        }
        
        # 分页获取所有项目（带重试，应对偶发网络抖动）
        all_projects = []
        offset = 0
        limit = 100
        
        while True:
            # 单次请求最多重试3次
            response = None
            for attempt in range(3):
                try:
                    response = zmind_http.get(
                        f"{ZMIND_API_URL}/projects.json?limit={limit}&offset={offset}",
                        headers=headers,
                        timeout=ZMIND_TIMEOUT
                    )
                    if response.status_code == 200:
                        break
                    if response.status_code == 403:
                        # 区分限流 403（Nginx HTML）和权限 403（Redmine JSON）
                        # 限流时 Content-Type 是 text/html，需要等待后重试
                        content_type = response.headers.get('Content-Type', '')
                        if 'text/html' in content_type:
                            logger.warning(f"Zmind限流(尝试{attempt+1}/3)，等待后重试")
                            if attempt < 2:
                                import time; time.sleep(1.5 * (attempt + 1))
                            continue
                        else:
                            # 真正的权限 403，不重试
                            break
                    if response.status_code == 401:
                        break
                    logger.warning(f"获取项目列表失败(尝试{attempt+1}/3) status={response.status_code}")
                except requests.exceptions.RequestException as e:
                    logger.warning(f"获取项目列表异常(尝试{attempt+1}/3): {e}")
                    response = None
                if attempt < 2:
                    import time; time.sleep(0.5 * (attempt + 1))
            
            if response is not None and response.status_code == 200:
                data = response.json()
                projects = data.get('projects', [])
                total_count = data.get('total_count', 0)
                
                all_projects.extend(projects)
                
                # 如果已获取所有项目,退出循环
                if len(projects) < limit or len(all_projects) >= total_count:
                    break
                
                offset += limit
            else:
                status = response.status_code if response is not None else 'N/A'
                body = response.text[:200] if response is not None else '无响应'
                logger.error(f"获取Zmind项目列表失败 status={status}, body={body}")
                raise HTTPException(status_code=500, detail=f"获取项目列表失败（Zmind返回{status}）")
        
        # 构建项目层级结构
        project_dict = {}
        root_projects = []
        
        # 第一遍：创建所有项目的字典
        for p in all_projects:
            project_dict[p.get('id')] = {
                'id': str(p.get('id')),
                'name': p.get('name'),
                'identifier': p.get('identifier'),
                'parent_id': p.get('parent', {}).get('id') if p.get('parent') else None,
                'children': []
            }
        
        # 第二遍：构建层级关系
        for project_id, project in project_dict.items():
            if project['parent_id']:
                # 有父项目，添加到父项目的children中
                parent = project_dict.get(project['parent_id'])
                if parent:
                    parent['children'].append(project)
            else:
                # 没有父项目，是根项目
                root_projects.append(project)
        
        # 递归函数：将层级结构转换为带缩进的扁平列表
        def flatten_projects(projects, level=0):
            result = []
            for p in sorted(projects, key=lambda x: x['name']):
                # 添加缩进标识
                indent = '　' * level  # 使用全角空格作为缩进
                display_name = f"{indent}{p['name']}" if level > 0 else p['name']
                
                result.append({
                    'id': p['id'],
                    'name': display_name,
                    'identifier': p['identifier'],
                    'level': level
                })
                
                # 递归处理子项目
                if p['children']:
                    result.extend(flatten_projects(p['children'], level + 1))
            
            return result
        
        # 转换为扁平列表
        flat_projects = flatten_projects(root_projects)
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": flat_projects
        }
            
    except HTTPException:
        raise
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="连接Zmind超时，请稍后重试")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="无法连接Zmind服务器，请检查网络")
    except Exception as e:
        logger.error(f"获取Zmind项目列表异常: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@router.put("/testplans/{test_plan_id}/zmind-project")
def update_testplan_zmind_project(
    test_plan_id: int,
    data: TestPlanZmindProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新测试计划的Zmind项目ID"""
    try:
        test_plan = db.query(TestPlan).filter(TestPlan.id == test_plan_id).first()
        if not test_plan:
            raise HTTPException(status_code=404, detail="测试计划不存在")
        
        test_plan.zmind_project_id = data.zmind_project_id
        db.commit()
        
        return {
            "code": 200,
            "message": "Zmind项目设置成功",
            "data": None
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.get("/testplans/{test_plan_id}/zmind-project")
def get_testplan_zmind_project(
    test_plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取测试计划的Zmind项目ID"""
    test_plan = db.query(TestPlan).filter(TestPlan.id == test_plan_id).first()
    if not test_plan:
        raise HTTPException(status_code=404, detail="测试计划不存在")
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "zmind_project_id": test_plan.zmind_project_id or ""
        }
    }


@router.get("/projects/{project_id}/required-fields")
def get_project_required_fields(
    project_id: str,
    tracker_id: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定项目的必填字段信息"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not user.zmind_api_key:
        raise HTTPException(status_code=400, detail="请先配置Zmind API Key")
    
    try:
        headers = {
            'X-Redmine-API-Key': user.zmind_api_key,
            'Content-Type': 'application/json'
        }
        
        # 发送最小化的Issue创建请求来检测必填字段
        test_data = {
            "issue": {
                "project_id": project_id,
                "tracker_id": tracker_id,
                "subject": "[TEST] Detecting required fields",
                "description": "Test issue for detecting required fields"
            }
        }
        
        response = zmind_http.post(
            f"{ZMIND_API_URL}/issues.json",
            headers=headers,
            json=test_data,
            timeout=ZMIND_TIMEOUT
        )
        
        required_fields = []
        field_mapping = {
            "Severity": {"id": 1, "type": "custom"},
            "Issue Version": {"id": 3, "type": "custom"},
            "Phase": {"id": 21, "type": "custom"},
            "Fixed Version": {"id": 4, "type": "custom"},
            "Priority": {"id": "priority_id", "type": "standard"},
            "Assigned to": {"id": "assigned_to_id", "type": "standard"},
            "Category": {"id": "category_id", "type": "standard"},
            "Due date": {"id": "due_date", "type": "standard"}
        }
        
        # 中文字段名映射
        chinese_field_mapping = {
            "类别": "Category",
            "严重程度": "Severity",
            "Phase": "Phase",
            "Issue": "Issue Version",
            "Issue Version": "Issue Version",
            "优先级": "Priority",
            "指派给": "Assigned to",
            "目标版本": "Fixed Version",
            "计划完成日期": "Due date"
        }
        
        if response.status_code == 422:
            # 验证失败，解析错误信息获取必填字段
            try:
                error_data = response.json()
            except ValueError:
                error_data = {}
            errors = error_data.get('errors', [])

            # 删除可能创建的测试Issue
            try:
                issue = error_data.get('issue') or (error_data.get('data', {}).get('issue'))
                if issue and issue.get('id'):
                    zmind_http.delete(
                        f"{ZMIND_API_URL}/issues/{issue['id']}.json",
                        headers=headers,
                        timeout=ZMIND_TIMEOUT
                    )
            except Exception:
                pass  # 删除失败不影响主流程

            for error in errors:
                # 解析错误信息，提取字段名
                # 错误格式: "字段名 不能为空字符" 或 "Field name can't be blank"
                if '不能为空' in error or "can't be blank" in error or '不能为空字符' in error:
                    # 提取字段名（取第一个空格前的内容）
                    field_name = error.split(' ')[0].strip()

                    # 检查是否为中文字段名并映射到英文
                    if field_name in chinese_field_mapping:
                        field_name = chinese_field_mapping[field_name]

                    # 尝试匹配已知字段
                    for known_field, field_info in field_mapping.items():
                        if field_name in known_field or known_field in error:
                            if known_field not in required_fields:
                                required_fields.append(known_field)
                            break
                    else:
                        # 未知字段，直接添加
                        if field_name not in required_fields:
                            required_fields.append(field_name)

        elif response.status_code in [200, 201]:
            # 创建成功，删除测试Issue
            try:
                issue = response.json().get('issue', {})
                if issue.get('id'):
                    zmind_http.delete(
                        f"{ZMIND_API_URL}/issues/{issue['id']}.json",
                        headers=headers,
                        timeout=ZMIND_TIMEOUT
                    )
            except Exception:
                pass  # 删除失败不影响结果
        
        # 构建返回数据
        result = {
            "required_fields": required_fields,
            "field_info": {}
        }
        
        for field_name in required_fields:
            if field_name in field_mapping:
                result["field_info"][field_name] = field_mapping[field_name]
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": result
        }
            
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="连接Zmind超时，请稍后重试")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="无法连接Zmind服务器，请检查网络")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"获取必填字段失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取必填字段失败: {str(e)}")


@router.get("/projects/{project_id}/fields")
def get_project_fields(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定项目的可用字段信息"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not user.zmind_api_key:
        raise HTTPException(status_code=400, detail="请先配置Zmind API Key")
    
    try:
        headers = {
            'X-Redmine-API-Key': user.zmind_api_key,
            'Content-Type': 'application/json'
        }

        def zmind_get_with_retry(url, max_retries=3):
            """带重试的 Zmind GET 请求，应对偶发网络抖动和限流"""
            last_exc = None
            for attempt in range(max_retries):
                try:
                    resp = zmind_http.get(url, headers=headers, timeout=ZMIND_TIMEOUT)
                    if resp.status_code == 200:
                        return resp
                    if resp.status_code == 403:
                        # 区分限流 403（Nginx HTML）和权限 403（Redmine JSON）
                        content_type = resp.headers.get('Content-Type', '')
                        if 'text/html' in content_type:
                            logger.warning(f"Zmind限流(尝试{attempt+1}/{max_retries})，等待后重试 url={url}")
                            if attempt < max_retries - 1:
                                import time; time.sleep(1.5 * (attempt + 1))
                            continue
                        else:
                            return resp  # 真正的权限 403，不重试
                    if resp.status_code in (401, 404):
                        return resp
                    logger.warning(f"Zmind请求失败(尝试{attempt+1}/{max_retries}) status={resp.status_code} url={url}")
                    if attempt < max_retries - 1:
                        import time; time.sleep(0.5 * (attempt + 1))
                except requests.exceptions.RequestException as e:
                    last_exc = e
                    logger.warning(f"Zmind请求异常(尝试{attempt+1}/{max_retries}) {e} url={url}")
                    if attempt < max_retries - 1:
                        import time; time.sleep(0.5 * (attempt + 1))
            if last_exc:
                raise last_exc
            return resp

        # Zmind 服务器有请求频率限制，并发请求会触发 403
        # 必须串行发送，并在请求之间加短暂间隔
        import time

        project_response = zmind_get_with_retry(f"{ZMIND_API_URL}/projects/{project_id}.json")
        time.sleep(0.3)

        # 获取成员（分页）
        all_members = []
        offset = 0
        limit = 100
        while True:
            resp = zmind_get_with_retry(
                f"{ZMIND_API_URL}/projects/{project_id}/memberships.json?limit={limit}&offset={offset}"
            )
            if resp.status_code != 200:
                break
            data = resp.json()
            memberships = data.get('memberships', [])
            total_count = data.get('total_count', 0)
            for m in memberships:
                if 'user' in m and m['user']:
                    user_info = m['user']
                    uid = user_info.get('id')
                    uname = user_info.get('name', '')
                    if uid:
                        all_members.append({'id': uid, 'name': uname})
            if len(memberships) < limit or len(all_members) >= total_count:
                break
            offset += limit
            time.sleep(0.3)
        time.sleep(0.3)

        # 获取版本
        resp = zmind_get_with_retry(f"{ZMIND_API_URL}/projects/{project_id}/versions.json")
        versions = []
        if resp.status_code == 200:
            versions = [{'id': v['id'], 'name': v['name']} for v in resp.json().get('versions', [])]
        time.sleep(0.3)

        # 获取类别
        resp = zmind_get_with_retry(f"{ZMIND_API_URL}/projects/{project_id}/issue_categories.json")
        categories = []
        if resp.status_code == 200:
            categories = [{'id': c['id'], 'name': c['name']} for c in resp.json().get('issue_categories', [])]

        if project_response.status_code != 200:
            logger.error(f"获取Zmind项目信息失败 project_id={project_id}, status={project_response.status_code}, body={project_response.text[:200]}")
            raise HTTPException(status_code=500, detail=f"获取项目信息失败（Zmind返回{project_response.status_code}）")

        resp_json = project_response.json()
        if 'project' not in resp_json:
            logger.error(f"Zmind项目响应格式异常 project_id={project_id}, body={project_response.text[:300]}")
            raise HTTPException(status_code=500, detail="获取项目信息失败（Zmind响应格式异常）")
        project_data = resp_json['project']

        # 获取trackers
        trackers = [
            {'id': t['id'], 'name': t['name']}
            for t in project_data.get('trackers', [])
        ]
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "trackers": trackers,
                "members": all_members,
                "versions": versions,
                "categories": categories
            }
        }
            
    except HTTPException:
        raise
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="连接Zmind超时，请稍后重试")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="无法连接Zmind服务器，请检查网络")
    except Exception as e:
        logger.error(f"获取项目字段失败 project_id={project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取项目字段失败: {str(e)}")


@router.get("/causes-categories")
def get_causes_categories(
    current_user: User = Depends(get_current_user)
):
    """获取Causes Category列表（自定义字段17的可选值）"""
    # 这些是从Zmind系统中常见的Causes Category选项
    # 实际值可能需要从Redmine API获取或配置
    return {
        "code": 200,
        "message": "获取成功",
        "data": [
            {"id": "Code Defect", "name": "Code Defect"},
            {"id": "Configuration Issue", "name": "Configuration Issue"},
            {"id": "Design Issue", "name": "Design Issue"},
            {"id": "Environment Issue", "name": "Environment Issue"},
            {"id": "Data Issue", "name": "Data Issue"},
            {"id": "Third Party Issue", "name": "Third Party Issue"},
            {"id": "Others", "name": "Others"}
        ]
    }


@router.get("/causes-categories")
def get_causes_categories2(
    current_user: User = Depends(get_current_user)
):
    """获取Causes Category列表（自定义字段17的可选值）"""
    # 这些是从Zmind系统中常见的Causes Category选项
    # 实际值可能需要从Redmine API获取或配置
    return {
        "code": 200,
        "message": "获取成功",
        "data": [
            {"id": "Code Defect", "name": "Code Defect"},
            {"id": "Configuration Issue", "name": "Configuration Issue"},
            {"id": "Design Issue", "name": "Design Issue"},
            {"id": "Environment Issue", "name": "Environment Issue"},
            {"id": "Data Issue", "name": "Data Issue"},
            {"id": "Third Party Issue", "name": "Third Party Issue"},
            {"id": "Others", "name": "Others"}
        ]
    }


@router.get("/side-effects")
def get_side_effects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取Side Effect列表（Side Effect字段ID: 5的可选值）
    
    custom_fields.json 需要管理员权限，普通用户无法访问。
    Side Effect 字段（ID: 5）是 Redmine 标准布尔型自定义字段，固定值为 No/Yes。
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not user.zmind_api_key:
        raise HTTPException(status_code=400, detail="请先配置Zmind API Key")
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": [
            {"id": "NO", "name": "NO"},
            {"id": "YES", "name": "YES"}
        ]
    }


@router.get("/phases")
def get_phases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取Phase列表（Phase字段ID: 21的可选值）"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not user.zmind_api_key:
        raise HTTPException(status_code=400, detail="请先配置Zmind API Key")
    
    try:
        headers = {
            'X-Redmine-API-Key': user.zmind_api_key,
            'Content-Type': 'application/json'
        }
        
        # 尝试从自定义字段API获取Phase选项
        response = zmind_http.get(
            f"{ZMIND_API_URL}/custom_fields.json",
            headers=headers,
            timeout=ZMIND_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            custom_fields = data.get('custom_fields', [])
            
            # 查找Phase字段（ID: 21）
            phase_field = None
            for field in custom_fields:
                if field['id'] == 21 or field['name'] == 'Phase':
                    phase_field = field
                    break
            
            if phase_field and 'possible_values' in phase_field:
                # 从API获取的Phase选项
                phases = []
                for val in phase_field['possible_values']:
                    value = val['value'] if isinstance(val, dict) else val
                    phases.append({"id": value, "name": value})
                return {
                    "code": 200,
                    "message": "获取成功",
                    "data": phases
                }
        
        # 如果API调用失败或没有找到Phase字段，返回默认选项
        # 这些值是从项目实际使用中收集的常见Phase值
        return {
            "code": 200,
            "message": "获取成功",
            "data": [
                {"id": "FFC", "name": "FFC"},
                {"id": "EIT", "name": "EIT"},
                {"id": "SVT", "name": "SVT"},
                {"id": "PP", "name": "PP"},
                {"id": "MP", "name": "MP"}
            ]
        }
    except Exception as e:
        # 如果发生错误，返回默认选项（记录日志便于排查）
        logger.warning(f"获取Phase列表失败，使用默认值: {e}")
        return {
            "code": 200,
            "message": "获取成功",
            "data": [
                {"id": "FFC", "name": "FFC"},
                {"id": "EIT", "name": "EIT"},
                {"id": "SVT", "name": "SVT"},
                {"id": "PP", "name": "PP"},
                {"id": "MP", "name": "MP"}
            ]
        }


@router.get("/priorities")
def get_priorities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取优先级列表"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not user.zmind_api_key:
        raise HTTPException(status_code=400, detail="请先配置Zmind API Key")
    
    try:
        headers = {
            'X-Redmine-API-Key': user.zmind_api_key,
            'Content-Type': 'application/json'
        }

        # 带重试
        response = None
        for attempt in range(3):
            try:
                response = zmind_http.get(
                    f"{ZMIND_API_URL}/enumerations/issue_priorities.json",
                    headers=headers,
                    timeout=ZMIND_TIMEOUT
                )
                if response.status_code == 200:
                    break
                if response.status_code in (401, 403):
                    break
            except requests.exceptions.RequestException as e:
                logger.warning(f"获取优先级失败(尝试{attempt+1}/3): {e}")
                response = None
            if attempt < 2:
                import time; time.sleep(0.5 * (attempt + 1))

        if response is not None and response.status_code == 200:
            data = response.json()
            priorities = data.get('issue_priorities', [])
            return {
                "code": 200,
                "message": "获取成功",
                "data": [
                    {"id": p.get('id'), "name": p.get('name')}
                    for p in priorities
                ]
            }
        else:
            status = response.status_code if response is not None else 'N/A'
            logger.error(f"获取Zmind优先级失败 status={status}")
            # 返回默认值，不让整个弹窗失败
            return {
                "code": 200,
                "message": "获取成功（默认值）",
                "data": [
                    {"id": 1, "name": "Low"},
                    {"id": 2, "name": "Normal"},
                    {"id": 3, "name": "High"},
                    {"id": 4, "name": "Urgent"},
                    {"id": 5, "name": "Immediate"}
                ]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取优先级异常: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取优先级失败: {str(e)}")


@router.get("/severities")
def get_severities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取严重程度列表（从自定义字段获取）"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not user.zmind_api_key:
        raise HTTPException(status_code=400, detail="请先配置Zmind API Key")
    
    try:
        headers = {
            'X-Redmine-API-Key': user.zmind_api_key,
            'Content-Type': 'application/json'
        }
        
        # 尝试从自定义字段API获取Severity选项
        response = zmind_http.get(
            f"{ZMIND_API_URL}/custom_fields.json",
            headers=headers,
            timeout=ZMIND_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            custom_fields = data.get('custom_fields', [])
            
            # 查找Severity字段（ID: 1）
            severity_field = None
            for field in custom_fields:
                if field['id'] == 1 or field['name'] == 'Severity':
                    severity_field = field
                    break
            
            if severity_field and 'possible_values' in severity_field:
                SEVERITY_ORDER = ["Blocker", "Critical", "Major", "Minor", "Enhancement"]
                severities = []
                for val in severity_field['possible_values']:
                    value = val['value'] if isinstance(val, dict) else val
                    severities.append({"id": value, "name": value})
                # 按指定顺序排序，未知值排到末尾
                severities.sort(key=lambda x: SEVERITY_ORDER.index(x['id']) if x['id'] in SEVERITY_ORDER else len(SEVERITY_ORDER))
                return {
                    "code": 200,
                    "message": "获取成功",
                    "data": severities
                }
        
        # 如果API调用失败或没有找到Severity字段，返回默认选项
        return {
            "code": 200,
            "message": "获取成功",
            "data": [
                {"id": "Blocker", "name": "Blocker"},
                {"id": "Critical", "name": "Critical"},
                {"id": "Major", "name": "Major"},
                {"id": "Minor", "name": "Minor"},
                {"id": "Enhancement", "name": "Enhancement"}
            ]
        }
    except Exception as e:
        logger.warning(f"获取Severity列表失败，使用默认值: {e}")
        return {
            "code": 200,
            "message": "获取成功",
            "data": [
                {"id": "Blocker", "name": "Blocker"},
                {"id": "Critical", "name": "Critical"},
                {"id": "Major", "name": "Major"},
                {"id": "Minor", "name": "Minor"},
                {"id": "Enhancement", "name": "Enhancement"}
            ]
        }


@router.get("/versions")
def get_versions(
    current_user: User = Depends(get_current_user)
):
    """获取版本列表"""
    # 返回常见的版本选项
    return {
        "code": 200,
        "message": "获取成功",
        "data": [
            {"id": "1", "name": "1.0"},
            {"id": "2", "name": "2.0"},
            {"id": "3", "name": "3.0"}
        ]
    }


@router.post("/issues/{issue_id}/attachments")
def upload_issue_attachment(
    issue_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传附件到Zmind Issue（使用用户的API Key）"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not user.zmind_api_key:
        raise HTTPException(status_code=400, detail="请先配置Zmind API Key")

    try:
        headers = {
            'X-Redmine-API-Key': user.zmind_api_key,
            'Content-Type': 'application/octet-stream'
        }

        file_content = file.file.read()
        filename = file.filename

        logger.info(f"上传附件到Issue {issue_id}: {filename}, 大小: {len(file_content)} bytes")

        upload_url = f"{ZMIND_API_URL}/uploads.json?filename={filename}"
        upload_token = None
        upload_attempts = 0

        for attempt in range(3):
            upload_attempts = attempt + 1
            try:
                upload_response = zmind_http.post(
                    upload_url,
                    headers=headers,
                    data=file_content,
                    timeout=ZMIND_UPLOAD_TIMEOUT
                )

                if upload_response.status_code == 201:
                    upload_data = upload_response.json()
                    upload_token = upload_data.get('upload', {}).get('token')
                    if upload_token:
                        logger.info(f"上传文件成功（尝试{upload_attempts}次）")
                        break
                    else:
                        last_error = "获取上传token失败"
                elif upload_response.status_code == 422:
                    last_error = "422 Unprocessable Entity"
                else:
                    last_error = f"HTTP {upload_response.status_code}"
            except requests.exceptions.RequestException as e:
                last_error = f"{type(e).__name__}: {str(e)}"

            if attempt < 2:
                wait_time = 2 ** attempt
                logger.warning(f"上传文件失败（{last_error}），{wait_time}s后重试")
                import time
                time.sleep(wait_time)

        if not upload_token:
            logger.error(f"文件上传失败（重试{upload_attempts}次）：{last_error}")
            raise HTTPException(status_code=500, detail=f"文件上传失败: {last_error}")

        attach_attempts = 0
        for attempt in range(3):
            attach_attempts = attempt + 1
            try:
                headers['Content-Type'] = 'application/json'
                attach_data = {
                    "issue": {
                        "uploads": [{
                            "token": upload_token,
                            "filename": filename,
                            "content_type": file.content_type or "application/octet-stream"
                        }]
                    }
                }

                attach_response = zmind_http.put(
                    f"{ZMIND_API_URL}/issues/{issue_id}.json",
                    headers=headers,
                    json=attach_data,
                    timeout=ZMIND_TIMEOUT
                )

                if attach_response.status_code in [200, 204]:
                    logger.info(f"关联附件成功（尝试{attach_attempts}次）")
                    return {
                        "code": 200,
                        "message": "附件上传成功",
                        "data": {
                            "filename": filename,
                            "size": len(file_content),
                            "upload_attempts": upload_attempts,
                            "attach_attempts": attach_attempts
                        }
                    }
                else:
                    last_error = f"HTTP {attach_response.status_code}"
            except requests.exceptions.RequestException as e:
                last_error = f"{type(e).__name__}: {str(e)}"

            if attempt < 2:
                wait_time = 2 ** attempt
                logger.warning(f"关联附件失败（{last_error}），{wait_time}s后重试")
                import time
                time.sleep(wait_time)

        logger.error(f"关联附件失败（重试{attach_attempts}次）：{last_error}")
        raise HTTPException(status_code=500, detail=f"附件关联失败: {last_error}")

    except HTTPException:
        raise
    except requests.exceptions.SSLError as e:
        logger.error(f"上传附件SSL错误: {str(e)}")
        raise HTTPException(status_code=500, detail="Zmind SSL连接异常，文件可能过大或网络不稳定，请稍后重试")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="上传附件超时，请稍后重试")
    except Exception as e:
        logger.error(f"上传附件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传附件失败: {str(e)}")


@router.get("/issues/{issue_id}")
def get_issue(
    issue_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取 Zmind Issue 详情（使用全局API Key）"""
    try:
        # 使用配置文件中的全局API Key
        if not ZMIND_API_KEY:
            raise HTTPException(status_code=400, detail="系统未配置Zmind API Key")
        
        headers = {
            'X-Redmine-API-Key': ZMIND_API_KEY,
            'Content-Type': 'application/json'
        }
        
        response = zmind_http.get(
            f"{ZMIND_API_URL}/issues/{issue_id}.json",
            headers=headers,
            timeout=ZMIND_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            issue = data.get('issue', {})
            
            return {
                "code": 200,
                "message": "获取成功",
                "data": {
                    "id": issue.get('id'),
                    "subject": issue.get('subject'),
                    "description": issue.get('description'),
                    "status": issue.get('status', {}).get('name'),
                    "priority": issue.get('priority', {}).get('name'),
                    "assigned_to": issue.get('assigned_to', {}).get('name') if issue.get('assigned_to') else None,
                    "created_on": issue.get('created_on'),
                    "updated_on": issue.get('updated_on'),
                    "url": f"https://zmind.whaletv.com/issues/{issue_id}"
                }
            }
        else:
            raise HTTPException(status_code=404, detail=f"Issue {issue_id} 不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Issue 失败: {str(e)}")


@router.post("/issues")
def create_issue(
    issue_data: ZmindIssueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建 Zmind Issue"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not user.zmind_api_key:
        raise HTTPException(status_code=400, detail="请先配置Zmind API Key")
    
    try:
        headers = {
            'X-Redmine-API-Key': user.zmind_api_key,
            'Content-Type': 'application/json'
        }
        
        # 构建自定义字段列表
        custom_fields = [
            {
                "id": 1,  # Severity 字段
                "value": issue_data.severity
            },
            {
                "id": 3,  # Issue Version 字段
                "value": issue_data.issue_version
            }
        ]
        
        # 添加TeVaMat ID自定义字段（如果提供）
        if issue_data.tevama_id:
            custom_fields.append({
                "id": 40,  # TeVaMat ID 字段
                "value": issue_data.tevama_id
            })
        
        # 添加Phase自定义字段（如果提供）
        if issue_data.phase:
            custom_fields.append({
                "id": 21,  # Phase 字段
                "value": issue_data.phase
            })
        
        # 添加Side Effect自定义字段（如果提供）
        if issue_data.side_effect:
            custom_fields.append({
                "id": 5,  # Side Effect 字段
                "value": issue_data.side_effect
            })
        
        # 构建 Redmine API 请求数据
        redmine_data = {
            "issue": {
                "project_id": issue_data.project_id,
                "subject": issue_data.subject,
                "description": issue_data.description,
                "priority_id": issue_data.priority_id,
                "tracker_id": issue_data.tracker_id,
                "custom_fields": custom_fields
            }
        }
        
        # 添加可选字段
        if issue_data.assigned_to_id:
            redmine_data["issue"]["assigned_to_id"] = issue_data.assigned_to_id
        
        if issue_data.category_id:
            redmine_data["issue"]["category_id"] = issue_data.category_id
        
        if issue_data.due_date:
            redmine_data["issue"]["due_date"] = issue_data.due_date
        
        if issue_data.fixed_version_id:
            redmine_data["issue"]["fixed_version_id"] = issue_data.fixed_version_id
        
        import logging
        request_url = f"{ZMIND_API_URL}/issues.json"
        logging.info(f"创建Issue请求: POST {request_url}")
        logging.info(f"请求数据: {redmine_data}")
        
        response = zmind_http.post(
            request_url,
            headers=headers,
            json=redmine_data,
            timeout=ZMIND_TIMEOUT
        )
        
        logging.info(f"Redmine响应: status={response.status_code}, body={response.text[:500]}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            issue = data.get('issue')
            
            if not issue or not issue.get('id'):
                # Redmine 返回了200但不是标准的创建响应（如返回了issues列表）
                import logging
                logging.error(f"Redmine返回了{response.status_code}但响应格式异常, 响应: {str(data)[:500]}")
                raise HTTPException(status_code=500, detail=f"Redmine响应格式异常，Issue可能未创建成功，请到Zmind确认")
            
            issue_id = issue.get('id')
            
            # 防御：如果Redmine没返回有效的issue id
            if not issue_id:
                import logging
                logging.error(f"Redmine返回了{response.status_code}但没有issue id, 响应: {data}")
                raise HTTPException(status_code=500, detail=f"Redmine创建成功但未返回Issue ID，响应: {str(data)[:500]}")
            
            return {
                "code": 200,
                "message": "PR 创建成功",
                "data": {
                    "id": issue_id,
                    "subject": issue.get('subject'),
                    "url": f"https://zmind.whaletv.com/issues/{issue_id}"
                }
            }
        else:
            error_data = response.json() if response.text else {}
            errors = error_data.get('errors', [])
            error_msg = ', '.join(errors) if errors else response.text
            import logging
            logging.error(f"Redmine创建Issue失败, status={response.status_code}, 响应: {response.text[:500]}")
            raise HTTPException(status_code=400, detail=f"创建失败: {error_msg}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建 PR 失败: {str(e)}")


class PrNumbersRequest(BaseModel):
    """通过PR号批量查询Issue"""
    pr_numbers: str  # 逗号分隔的PR号，如 "330891,327631,330791"


@router.post("/fetch-issues-by-pr")
def fetch_issues_by_pr_numbers(
    data: PrNumbersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """根据PR号批量查询Zmind Issue，返回与CSV解析相同格式的stats和issues"""
    if not ZMIND_API_KEY:
        raise HTTPException(status_code=400, detail="系统未配置Zmind API Key")

    # 解析PR号
    raw_numbers = [n.strip() for n in data.pr_numbers.split(',') if n.strip()]
    if not raw_numbers:
        raise HTTPException(status_code=400, detail="请输入至少一个PR号")

    from utils.constants import OPEN_STATUS_ORDER
    OPEN_STATUSES = set(OPEN_STATUS_ORDER)
    SEVERITY_KEYS = ['Blocker', 'Critical', 'Major', 'Minor', 'Enhancement']
    SEVERITY_ORDER = {s: i for i, s in enumerate(SEVERITY_KEYS)}

    headers = {
        'X-Redmine-API-Key': ZMIND_API_KEY,
        'Content-Type': 'application/json'
    }

    issues = []
    errors = []
    stats = {s: {'open': 0, 'total': 0} for s in SEVERITY_KEYS}

    # Zmind 服务器有请求频率限制，需要控制并发并带重试
    import concurrent.futures
    import time

    def fetch_single_pr(pr_num):
        max_retries = 3
        last_error = None
        for attempt in range(max_retries):
            try:
                response = zmind_http.get(
                    f"{ZMIND_API_URL}/issues/{pr_num}.json",
                    headers=headers,
                    timeout=ZMIND_TIMEOUT
                )
                if response.status_code == 200:
                    return response.json().get('issue', {}), None
                if response.status_code == 403:
                    content_type = response.headers.get('Content-Type', '')
                    if 'text/html' in content_type:
                        logger.warning(f"PR#{pr_num} Zmind限流(尝试{attempt+1}/{max_retries})，等待后重试")
                        if attempt < max_retries - 1:
                            time.sleep(1.5 * (attempt + 1))
                        continue
                    else:
                        return None, f"PR#{pr_num}: 无权访问"
                if response.status_code in (401, 404):
                    return None, f"PR#{pr_num}: 不存在或无权访问"
                logger.warning(f"PR#{pr_num} 请求失败(尝试{attempt+1}/{max_retries}) status={response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
            except Exception as e:
                last_error = e
                logger.warning(f"PR#{pr_num} 请求异常(尝试{attempt+1}/{max_retries}) {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
        return None, f"PR#{pr_num}: {str(last_error) if last_error else '查询失败，请稍后重试'}"

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(raw_numbers), 3)) as executor:
        future_map = {}
        for pr_num in raw_numbers:
            time.sleep(0.3)
            future_map[executor.submit(fetch_single_pr, pr_num)] = pr_num
        for future in concurrent.futures.as_completed(future_map):
            pr_num = future_map[future]
            issue_data, error = future.result()
            if error:
                errors.append(error)
                continue

            # 提取severity（自定义字段ID=1）
            severity = ''
            custom_fields = issue_data.get('custom_fields', [])
            for cf in custom_fields:
                if cf.get('id') == 1 or cf.get('name') == 'Severity':
                    severity = cf.get('value', '')
                    break

            status_name = issue_data.get('status', {}).get('name', '')
            tracker_name = issue_data.get('tracker', {}).get('name', '')
            category_name = issue_data.get('category', {}).get('name', '') if issue_data.get('category') else ''
            priority_name = issue_data.get('priority', {}).get('name', '')
            subject = issue_data.get('subject', '')
            assignee = issue_data.get('assigned_to', {}).get('name', '') if issue_data.get('assigned_to') else ''
            author = issue_data.get('author', {}).get('name', '') if issue_data.get('author') else ''

            issue = {
                'pr_number': str(issue_data.get('id', pr_num)),
                'tracker': tracker_name,
                'category': category_name,
                'severity': severity,
                'status': status_name,
                'priority': priority_name,
                'subject': subject,
                'assignee': assignee,
                'author': author
            }
            issues.append(issue)

            # 统计
            if severity:
                matched = None
                for sk in SEVERITY_KEYS:
                    if sk.lower() == severity.lower():
                        matched = sk
                        break
                if matched:
                    stats[matched]['total'] += 1
                    if status_name in OPEN_STATUSES:
                        stats[matched]['open'] += 1

    # 排序：Open状态优先，然后按Severity排序
    issues.sort(key=lambda x: (
        0 if x['status'] in OPEN_STATUSES else 1,
        SEVERITY_ORDER.get(x['severity'], len(SEVERITY_KEYS))
    ))

    # 构建与parse_zmind_csv相同格式的stats
    result_stats = {}
    for s in SEVERITY_KEYS:
        key = s.lower()
        result_stats[key] = stats[s]['total']
        result_stats[f'open_{key}'] = stats[s]['open']
    result_stats['total_prs'] = sum(stats[s]['total'] for s in SEVERITY_KEYS)
    result_stats['open'] = sum(stats[s]['open'] for s in SEVERITY_KEYS)

    return {
        "code": 200,
        "message": "查询完成",
        "data": {
            "stats": result_stats,
            "issues": issues,
            "errors": errors,
            "total_requested": len(raw_numbers),
            "total_found": len(issues)
        }
    }
