from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from api import auth, testcase, testplan, execution, report, zmind, user, project, validation, user_project, role, system_log, attachment, comment, progress, testcase_attachment, team, user_team, module, notification, notification_rule, notification_template, dashboard, system_notification, review_plan, position_tag, organization, case_template, case_check, dingtalk_bot, test_suite, report_template, analytics, external_execution, naming_rule, aml_patch, risk_notification, database_admin
from api import behavior_tracker
from api import aml_patch_api
from api import version_release, version_notify_group, version_info
from api import task_overview
from api.dashboard_v2 import router as dashboard_v2_router
from api import websocket as ws_api
from database import engine, Base

# 注册 AI语音测试 模型，确保表被创建
from models_aivoice import (
    AiVoiceReleaseNote, AiVoiceVersionRecord, AiVoiceCustomerProblem,
    AiVoiceVersionIssue, AiVoiceTestCase, AiVoiceSetting,
    AiVoiceProjectWorkspace, AiVoiceWorkspaceModule, AiVoiceWorkspaceGroup,
    AiRecommendHistory
)
from config import settings
from utils.config_validator import validate_database_config
import os
import logging
import traceback
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def log_scheduled_task(db, module, action, description):
    """记录定时任务执行结果到系统日志"""
    from models import SystemLog
    log = SystemLog(
        user_id=None,
        username="system",
        module=module,
        action=action,
        description=description,
        created_at=datetime.now()
    )
    db.add(log)
    db.commit()


# 所有文件数据已改为存储到数据库，不再需要 data 目录
# 头像以 base64 data URL 存储在数据库中

# 验证数据库配置
try:
    validate_database_config(settings)
except ValueError as e:
    logger.error(f"数据库配置验证失败: {str(e)}")
    logger.error("请检查 .env 文件中的 DATABASE_URL 配置")
    raise

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 初始化默认角色模板
def init_default_role_templates():
    from sqlalchemy.orm import Session
    from models import RoleTemplate
    import json
    
    db = Session(bind=engine)
    try:
        # 检查是否已有模板
        existing_templates = db.query(RoleTemplate).count()
        if existing_templates > 0:
            return
        
        # 默认模板数据
        default_templates = [
            {
                "name": "系统管理员",
                "description": "拥有系统所有权限，包括管理功能和测试功能，以及完整的工作台权限管理",
                "permissions": [
                    'dashboard', 'testcases', 'testplans', 'reports', 'validation',
                    'users', 'projects', 'permissionManagement', 'organization', 'notificationManagement', 'systemLog',
                    'testcases.create', 'testcases.edit', 'testcases.delete', 'testcases.import', 'testcases.export',
                    'testcases.moduleManage', 'testcases.importAutoCreate',
                    'testplans.create', 'testplans.edit', 'testplans.delete',
                    'reports.generate', 'reports.exportPdf', 'reports.exportExcel', 'reports.delete',
                    'validation.validate',
                    'users.create', 'users.edit', 'users.delete',
                    'projects.create', 'projects.edit', 'projects.delete',
                    'permissionManagement.createRole', 'permissionManagement.editRole', 'permissionManagement.deleteRole',
                    'organization.create', 'organization.edit', 'organization.manageTeams', 'organization.manageMembers', 'organization.delete',
                    'notificationManagement.createRule', 'notificationManagement.editRule', 'notificationManagement.deleteRule',
                    'notificationManagement.createTemplate', 'notificationManagement.editTemplate', 'notificationManagement.deleteTemplate',
                    'testcases.deleteReviewPlan',
                    'dashboard.projectCards', 'dashboard.prList', 'dashboard.reviewPlans', 'dashboard.testPlans', 'dashboard.userTasks',
                    'dashboard.overview', 'dashboard.testcases', 'dashboard.testplans', 'dashboard.execution', 'dashboard.reports'
                ],
                "is_system": True
            },
            {
                "name": "测试人员",
                "description": "拥有测试相关的所有权限，包括测试用例、测试计划和报告，以及测试相关的工作台权限管理",
                "permissions": [
                    'dashboard', 'testcases', 'testplans', 'reports', 'validation',
                    'testcases.create', 'testcases.edit', 'testcases.delete', 'testcases.import', 'testcases.export',
                    'testcases.moduleManage', 'testcases.importAutoCreate',
                    'testplans.create', 'testplans.edit', 'testplans.delete',
                    'reports.generate', 'reports.exportPdf', 'reports.exportExcel', 'reports.delete',
                    'validation.validate',
                    'testcases.deleteReviewPlan',
                    'dashboard.projectCards', 'dashboard.prList', 'dashboard.reviewPlans', 'dashboard.testPlans', 'dashboard.userTasks',
                    'dashboard.overview', 'dashboard.testcases', 'dashboard.testplans', 'dashboard.execution', 'dashboard.reports'
                ],
                "is_system": True
            },
            {
                "name": "查看人员",
                "description": "仅拥有查看权限，无法进行修改操作，工作台权限管理也仅限于查看",
                "permissions": [
                    'dashboard', 'testcases', 'testplans', 'reports', 'validation',
                    'dashboard.projectCards', 'dashboard.prList', 'dashboard.reviewPlans', 'dashboard.testPlans', 'dashboard.userTasks',
                    'dashboard.overview', 'dashboard.testcases', 'dashboard.testplans', 'dashboard.execution', 'dashboard.reports'
                ],
                "is_system": True
            },
            {
                "name": "项目经理",
                "description": "拥有项目管理和测试功能的权限，以及完整的工作台数据查看权限",
                "permissions": [
                    'dashboard', 'testcases', 'testplans', 'reports', 'validation',
                    'projects.create', 'projects.edit', 'projects.delete',
                    'testcases.create', 'testcases.edit', 'testcases.import', 'testcases.export',
                    'testcases.moduleManage', 'testcases.importAutoCreate',
                    'testplans.create', 'testplans.edit',
                    'reports.generate', 'reports.exportPdf', 'reports.exportExcel',
                    'dashboard.projectCards', 'dashboard.prList', 'dashboard.reviewPlans', 'dashboard.testPlans', 'dashboard.userTasks',
                    'dashboard.overview', 'dashboard.testcases', 'dashboard.testplans', 'dashboard.execution', 'dashboard.reports'
                ],
                "is_system": True
            }
        ]
        
        # 添加默认模板
        for template_data in default_templates:
            template = RoleTemplate(
                name=template_data["name"],
                description=template_data["description"],
                permissions=json.dumps(template_data["permissions"]),
                is_system=template_data["is_system"]
            )
            db.add(template)
        
        db.commit()
        print("默认角色模板初始化完成")
    except Exception as e:
        print(f"初始化默认角色模板失败: {e}")
        db.rollback()
    finally:
        db.close()

# 初始化默认角色模板
init_default_role_templates()

# 自动清理90天前的系统日志
import asyncio
from datetime import datetime, timedelta
import pytz


async def cleanup_old_behavior_tracker():
    """定期清理30天前的行为追踪数据"""
    while True:
        try:
            from sqlalchemy.orm import Session
            from models import UserBehaviorTracker
            db = Session(bind=engine)
            try:
                cutoff = datetime.now() - timedelta(days=30)
                deleted = db.query(UserBehaviorTracker).filter(
                    UserBehaviorTracker.created_at < cutoff
                ).delete()
                db.commit()
                if deleted > 0:
                    logger.info(f"自动清理行为追踪数据：删除了 {deleted} 条30天前的记录")
            except Exception as e:
                logger.error(f"清理行为追踪数据失败: {e}")
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"清理行为追踪任务异常: {e}")
        # 每24小时执行一次
        await asyncio.sleep(86400)


async def cleanup_old_logs():
    """定期清理90天前的系统日志"""
    while True:
        try:
            from sqlalchemy.orm import Session
            from models import SystemLog
            db = Session(bind=engine)
            try:
                cutoff = datetime.now() - timedelta(days=90)
                deleted = db.query(SystemLog).filter(SystemLog.created_at < cutoff).delete()
                db.commit()
                if deleted > 0:
                    logger.info(f"自动清理系统日志：删除了 {deleted} 条90天前的记录")
            except Exception as e:
                logger.error(f"清理系统日志失败: {e}")
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"清理日志任务异常: {e}")
        # 每24小时执行一次
        await asyncio.sleep(86400)


async def risk_notification_task():
    """每天18点执行风险预警通知任务"""
    while True:
        try:
            # 计算下一次执行时间（每天18:00）
            now = datetime.now()
            next_run = now.replace(hour=18, minute=0, second=0, microsecond=0)
            if now.hour >= 18:
                next_run += timedelta(days=1)
            
            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"风险预警任务：等待 {wait_seconds} 秒后执行")
            await asyncio.sleep(wait_seconds)
            
            # 执行风险检查
            try:
                from sqlalchemy.orm import Session
                from services.risk_notification_service import RiskNotificationService
                db = Session(bind=engine)
                try:
                    service = RiskNotificationService(db)
                    result = service.check_and_notify()
                    logger.info(f"风险预警任务执行完成: {result}")
                    log_scheduled_task(db, "定时任务", "complete", f"风险预警任务执行完成: {result}")
                except Exception as e:
                    logger.error(f"风险预警任务执行失败: {e}")
                    log_scheduled_task(db, "定时任务", "error", f"风险预警任务执行失败: {str(e)}")
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"风险预警任务异常: {e}")
        except Exception as e:
            logger.error(f"风险预警任务循环异常: {e}")
            await asyncio.sleep(3600)


async def aml_patch_sync_task():
    """每天凌晨2点执行AML Patch同步任务（同步状态不为3的记录）"""
    while True:
        try:
            now = datetime.now()
            next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if now.hour >= 2:
                next_run += timedelta(days=1)

            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"AML Patch同步任务：等待 {wait_seconds} 秒后执行")
            await asyncio.sleep(wait_seconds)

            try:
                from sqlalchemy.orm import Session
                from api.aml_patch import _sync_patch_to_zmind, _send_sync_failure_notification
                from models import AmlPatch
                db = Session(bind=engine)
                try:
                    patches = db.query(AmlPatch).filter(
                        AmlPatch.zmind_numbers.isnot(None),
                        AmlPatch.zmind_numbers != '',
                        AmlPatch.zmind_numbers != '[]',
                        AmlPatch.sync_status != 3
                    ).all()

                    success_count = 0
                    failed_count = 0
                    all_failed_details = []
                    for patch in patches:
                        try:
                            failed_details = _sync_patch_to_zmind(patch, db)
                            if failed_details:
                                all_failed_details.extend(failed_details)
                                failed_count += 1
                            else:
                                success_count += 1
                        except Exception:
                            failed_count += 1
                            all_failed_details.append({
                                "patch_id": patch.id,
                                "error": "同步异常"
                            })

                    result = f"AML Patch同步完成: 成功{success_count}条, 失败{failed_count}条"
                    logger.info(result)
                    log_scheduled_task(db, "定时任务", "complete", result)
                    
                    # 发送失败通知
                    if all_failed_details:
                        _send_sync_failure_notification(
                            db, 
                            all_failed_details, 
                            total_count=len(patches),
                            success_count=success_count
                        )
                except Exception as e:
                    logger.error(f"AML Patch同步任务执行失败: {e}")
                    log_scheduled_task(db, "定时任务", "error", f"AML Patch同步任务执行失败: {str(e)}")
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"AML Patch同步任务异常: {e}")
        except Exception as e:
            logger.error(f"AML Patch同步任务循环异常: {e}")
            await asyncio.sleep(3600)


async def zmind_pr_sync_task():
    """每天凌晨3点执行Zmind PR同步任务"""
    while True:
        try:
            # 计算下一次执行时间（每天3:00）
            now = datetime.now()
            next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if now.hour >= 3:
                next_run += timedelta(days=1)
            
            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"Zmind PR同步任务：等待 {wait_seconds} 秒后执行")
            await asyncio.sleep(wait_seconds)
            
            # 执行PR同步
            try:
                from sqlalchemy.orm import Session
                from services.zmind_sync_service import ZmindSyncService
                db = Session(bind=engine)
                try:
                    service = ZmindSyncService(db)
                    result = service.sync_all_pr_status()
                    logger.info(f"Zmind PR同步任务执行完成: {result}")
                    log_scheduled_task(db, "定时任务", "complete", f"Zmind PR同步任务执行完成: {result}")
                except Exception as e:
                    logger.error(f"Zmind PR同步任务执行失败: {e}")
                    log_scheduled_task(db, "定时任务", "error", f"Zmind PR同步任务执行失败: {str(e)}")
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Zmind PR同步任务异常: {e}")
        except Exception as e:
            logger.error(f"Zmind PR同步任务循环异常: {e}")
            await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app):
    # startup - 启动定时任务（使用独立线程避免阻塞事件循环）
    import threading
    
    def run_task(coro):
        """在新事件循环中运行异步任务"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()
    
    # 使用独立线程运行定时任务，避免阻塞FastAPI主线程
    threading.Thread(target=run_task, args=(cleanup_old_logs(),), daemon=True).start()
    threading.Thread(target=run_task, args=(cleanup_old_behavior_tracker(),), daemon=True).start()
    threading.Thread(target=run_task, args=(risk_notification_task(),), daemon=True).start()
    threading.Thread(target=run_task, args=(aml_patch_sync_task(),), daemon=True).start()
    threading.Thread(target=run_task, args=(zmind_pr_sync_task(),), daemon=True).start()
    
    yield
    # shutdown（如需清理资源可在此处添加）

# 生产环境关闭 API 文档
_is_production = os.getenv("APP_ENV", "").lower() == "production"

app = FastAPI(
    title="测试用例管理平台",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)

# 添加代理头处理中间件
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    """处理代理头，确保正确获取客户端真实IP"""
    async def dispatch(self, request: Request, call_next):
        # 如果有X-Forwarded-For或X-Real-IP头，更新request.client
        forwarded_for = request.headers.get('X-Forwarded-For')
        real_ip = request.headers.get('X-Real-IP')
        
        if real_ip:
            # X-Real-IP优先级最高
            request.scope['client'] = (real_ip, 0)
        elif forwarded_for:
            # X-Forwarded-For取第一个IP（客户端真实IP）
            client_ip = forwarded_for.split(',')[0].strip()
            request.scope['client'] = (client_ip, 0)
        
        response = await call_next(request)
        return response

app.add_middleware(ProxyHeadersMiddleware)

# 添加反爬中间件
if settings.ANTI_BOT_ENABLED:
    from middleware.anti_bot import AntiBotMiddleware
    app.add_middleware(AntiBotMiddleware)

if settings.RATE_LIMIT_ENABLED:
    from middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware,
                       default_limit=settings.RATE_LIMIT_DEFAULT,
                       login_limit=settings.RATE_LIMIT_LOGIN)

if settings.REQUEST_SIGN_ENABLED:
    from middleware.request_sign import RequestSignMiddleware
    app.add_middleware(RequestSignMiddleware, secret=settings.REQUEST_SIGN_SECRET)

# 添加Gzip压缩中间件（提升响应速度）
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理器
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常: {str(exc)}")
    logger.error(f"异常堆栈: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"}
    )

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(testcase.router, prefix="/api/testcases", tags=["测试用例"])
app.include_router(testcase_attachment.router, prefix="/api/testcase-attachments", tags=["测试用例附件"])
app.include_router(testplan.router, prefix="/api/testplans", tags=["测试计划"])
app.include_router(risk_notification.router, prefix="/api/testplans", tags=["风险预警"])
app.include_router(test_suite.router, prefix="/api/test-suites", tags=["测试套件"])
app.include_router(execution.router, prefix="/api/executions", tags=["测试执行"])
app.include_router(report.router, prefix="/api/reports", tags=["报告"])
app.include_router(zmind.router, prefix="/api/zmind", tags=["Zmind集成"])
app.include_router(user.router, prefix="/api/users", tags=["用户管理"])
app.include_router(project.router, prefix="/api/projects", tags=["项目管理"])
app.include_router(validation.router, prefix="/api/validation", tags=["用例校对"])
app.include_router(user_project.router, prefix="/api/user-projects", tags=["用户项目授权"])
app.include_router(role.router, prefix="/api/roles", tags=["角色管理"])
app.include_router(system_log.router, prefix="/api/system", tags=["系统日志"])
app.include_router(notification.router, prefix="/api/notifications", tags=["通知管理"])
app.include_router(notification_rule.router, prefix="/api/notification-rules", tags=["通知规则管理"])
app.include_router(notification_template.router, prefix="/api/notification-templates", tags=["通知模板管理"])
app.include_router(system_notification.router, prefix="/api/system-notifications", tags=["系统通知"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["工作台统计"])
app.include_router(team.router, prefix="/api/teams", tags=["项目组管理"])
app.include_router(user_team.router, prefix="/api/user-teams", tags=["用户项目组"])
# 新增路由
app.include_router(attachment.router, tags=["附件管理"])
app.include_router(comment.router, tags=["评论管理"])
app.include_router(progress.router, tags=["进度统计"])
app.include_router(module.router, prefix="/api", tags=["模块管理"])
app.include_router(review_plan.router, prefix="/api/review-plans", tags=["评审计划管理"])
app.include_router(position_tag.router, prefix="/api/position-tags", tags=["职位Tag管理"])
app.include_router(organization.router, prefix="/api/organization", tags=["组织管理"])
app.include_router(case_template.router, prefix="/api", tags=["用例模板管理"])
app.include_router(report_template.router, prefix="/api", tags=["报告模板管理"])
app.include_router(case_check.router, prefix="/api", tags=["用例校对"])
app.include_router(dingtalk_bot.router, prefix="/api/dingtalk-bots", tags=["钉钉机器人配置"])
app.include_router(dashboard_v2_router, prefix="/api/dashboard/v2", tags=["工作台v2"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["数据统计分析"])
app.include_router(database_admin.router, prefix="/api", tags=["数据库管理"])
app.include_router(external_execution.router, prefix="/api/external-executions", tags=["外部执行接口"])
app.include_router(naming_rule.router, prefix="/api/naming-rule", tags=["命名规则配置"])
app.include_router(ws_api.router, tags=["WebSocket通知"])
app.include_router(aml_patch.router, prefix="/api", tags=["AML Patch管理"])
app.include_router(aml_patch_api.router, prefix="/api", tags=["AML Patch API（独立认证）"])
app.include_router(behavior_tracker.router, tags=["行为追踪"])
app.include_router(version_release.router, prefix="/api/version-releases", tags=["版本发布管理"])
app.include_router(version_notify_group.router, prefix="/api/version-notify-groups", tags=["版本通知用户组"])
app.include_router(version_info.router, prefix="/api/version-info", tags=["版本信息查询"])
app.include_router(task_overview.router, prefix="/api/task-overviews", tags=["任务总览"])

from api import captcha
app.include_router(captcha.router, prefix="/api/captcha", tags=["验证码"])

from api.aivoice import aivoice_router
app.include_router(aivoice_router, prefix="/api/aivoice", tags=["AI语音测试"])




@app.get("/")
def read_root():
    return {"message": "测试用例管理平台 API", "version": "1.0.0"}

@app.get("/api/agent/latest-version.json")
def get_agent_latest_version():
    """ADB Tool代理最新版本信息"""
    return {"version": "1.0.0", "name": "adb-agent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT,
        timeout_keep_alive=300,  # 5分钟keep-alive超时
        limit_concurrency=500,
        backlog=2048
    )
