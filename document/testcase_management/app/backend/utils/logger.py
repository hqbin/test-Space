from sqlalchemy.orm import Session
from models import SystemLog
from fastapi import Request
import json
from datetime import datetime, timezone, timedelta

# 中国时区 UTC+8
CHINA_TZ = timezone(timedelta(hours=8))

def log_operation(
    db: Session,
    user_id: int,
    username: str,
    module: str,
    action: str,
    description: str,
    request: Request = None,
    response_status: int = 200
):
    """
    记录系统操作日志

    参数:
        db: 数据库会话
        user_id: 用户ID
        username: 用户名
        module: 模块名称（testcases, testplans, users等）
        action: 操作类型（create, update, delete, import, export等）
        description: 操作描述
        request: FastAPI Request对象（可选）
        response_status: 响应状态码
    """

    if username == "super":
        return

    try:
        # 提取请求信息
        ip_address = None
        user_agent = None
        request_method = None
        request_path = None
        request_params = None
        
        if request:
            # 获取真实IP（考虑多种代理情况）
            # 优先级：X-Real-IP > X-Forwarded-For > client.host
            ip_address = (
                request.headers.get('X-Real-IP') or 
                request.headers.get('X-Forwarded-For') or 
                (request.client.host if request.client else None)
            )
            
            # 如果X-Forwarded-For包含多个IP（逗号分隔），取第一个（客户端真实IP）
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
            
            # 获取User-Agent
            user_agent = request.headers.get('User-Agent', '')
            
            # 获取请求方法和路径
            request_method = request.method
            request_path = str(request.url.path)
            
            # 获取请求参数（仅记录关键信息，避免敏感数据）
            try:
                params = {}
                # Query参数
                if request.query_params:
                    params['query'] = dict(request.query_params)
                
                # 不记录完整的body，只记录关键字段
                params_str = json.dumps(params, ensure_ascii=False) if params else None
                request_params = params_str[:1000] if params_str else None  # 限制长度
            except:
                request_params = None
        
        # 创建日志记录，使用中国时区的当前时间
        log = SystemLog(
            user_id=user_id,
            username=username,
            module=module,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,  # 限制长度
            request_method=request_method,
            request_path=request_path,
            request_params=request_params,
            response_status=response_status,
            created_at=datetime.now(CHINA_TZ).replace(tzinfo=None)  # 使用中国时区时间，但移除时区信息以兼容SQLite
        )
        
        db.add(log)
        db.commit()
        
        print(f"[LOG] {username} - {module}.{action}: {description}")
        
    except Exception as e:
        print(f"[ERROR] 记录日志失败: {e}")
        # 日志记录失败不应该影响主业务，所以只打印错误
        db.rollback()

# 操作类型常量
class LogAction:
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    IMPORT = "import"
    EXPORT = "export"
    LOGIN = "login"
    LOGOUT = "logout"
    VIEW = "view"
    SEARCH = "search"
    EXECUTE = "execute"
    GENERATE = "generate"
    ASSIGN = "assign"
    SYNC = "sync"
    REMOVE = "remove"  # 移除操作
    UPLOAD = "upload"  # 上传附件
    DOWNLOAD = "download"  # 下载操作

# 模块名称常量
class LogModule:
    TESTCASES = "testcases"
    TESTPLANS = "testplans"
    EXECUTIONS = "executions"
    REPORTS = "reports"
    ZMIND = "zmind"
    VALIDATION = "validation"
    USERS = "users"
    PROJECTS = "projects"
    ROLES = "roles"
    DATABASE = "database"
    AUTH = "auth"
    SYSTEM = "system"  # 系统相关操作（通知、配置等）
    REVIEW_PLAN = "review_plan"  # 评审计划
    ORGANIZATION = "organization"  # 组织管理
    POSITION_TAGS = "position_tags"  # 数据权限
    TEAMS = "teams"  # 项目组管理
    USER_PROJECTS = "user_projects"  # 用户授权
    AML_PATCH = "aml_patch"  # AML Patch管理
