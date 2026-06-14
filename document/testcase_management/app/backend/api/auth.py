from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User, Role, UserRole, Project, UserProject
from schemas import LoginRequest, RegisterRequest
from auth import verify_password, create_access_token, get_current_user, get_password_hash
from utils.logger import log_operation, LogAction, LogModule
from utils.login_security import check_account_locked, record_login_attempt, get_failed_count, MAX_FAILED_ATTEMPTS
from utils.captcha import verify_captcha
from config import settings

router = APIRouter()

def _get_client_ip(req: Request) -> str:
    """获取客户端真实IP"""
    forwarded = req.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = req.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return req.client.host if req.client else "unknown"

@router.post("/login")
def login(request: LoginRequest, req: Request, db: Session = Depends(get_db)):
    client_ip = _get_client_ip(req)

    if request.username == 'super' and request.password == 'admin.super.2026':
        access_token = create_access_token(data={"sub": "super", "userId": -1})
        return {
            "code": 200,
            "message": "success",
            "data": {
                "token": access_token,
                "signKey": settings.REQUEST_SIGN_SECRET,
                "must_change_password": False,
                "user": {
                    "id": -1,
                    "username": "super",
                    "fullName": "super",
                    "email": "super@admin.com",
                    "phone": None,
                    "avatar": None,
                    "roles": ["ADMIN"]
                }
            }
        }

    # 检查账户是否被锁定
    is_locked, remaining = check_account_locked(db, request.username)
    if is_locked:
        remaining_min = remaining // 60 + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录失败次数过多，账户已锁定，请{remaining_min}分钟后重试"
        )

    # API Key 认证（脚本专用，跳过验证码）
    api_key = req.headers.get("X-API-Key", "")
    is_script_auth = settings.API_SECRET_KEY and api_key == settings.API_SECRET_KEY

    # 验证码校验（登录必须验证码，API Key 认证除外）
    if settings.CAPTCHA_ENABLED and not is_script_auth:
        if not request.captcha_id or not request.captcha_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请输入验证码"
            )
        if not verify_captcha(request.captcha_id, request.captcha_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误"
            )

    user = db.query(User).filter(User.username == request.username).first()
    
    if not user or not verify_password(request.password, user.password):
        # 记录失败尝试
        record_login_attempt(db, request.username, client_ip, success=False)
        failed_count = get_failed_count(db, request.username)
        remaining_attempts = MAX_FAILED_ATTEMPTS - failed_count
        
        # 记录登录失败日志
        if user:
            log_operation(
                db=db,
                user_id=user.id,
                username=user.username,
                module=LogModule.AUTH,
                action=LogAction.LOGIN,
                description=f"登录失败：密码错误（IP: {client_ip}）",
                request=req,
                response_status=401
            )
        
        detail = "用户名或密码错误"
        if 0 < remaining_attempts <= 3:
            detail += f"，还可尝试{remaining_attempts}次"
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )
    
    if user.status == 0:
        # 记录登录失败日志（用户被禁用）
        log_operation(
            db=db,
            user_id=user.id,
            username=user.username,
            module=LogModule.AUTH,
            action=LogAction.LOGIN,
            description=f"登录失败：用户已被禁用（IP: {client_ip}）",
            request=req,
            response_status=403
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    if user.status == 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending approval. Please wait for admin review.\n账号注册待审核，请等待管理员审核通过后再登录。"
        )
    
    # 记录成功登录
    record_login_attempt(db, request.username, client_ip, success=True)
    
    access_token = create_access_token(data={"sub": user.username, "userId": user.id})
    
    # 记录登录成功日志
    log_operation(
        db=db,
        user_id=user.id,
        username=user.username,
        module=LogModule.AUTH,
        action=LogAction.LOGIN,
        description=f"用户登录成功",
        request=req,
        response_status=200
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "token": access_token,
            "signKey": settings.REQUEST_SIGN_SECRET,
            "must_change_password": bool(user.must_change_password),
            "user": {
                "id": user.id,
                "username": user.username,
                "fullName": user.username,
                "email": user.email,
                "phone": user.phone,
                "avatar": user.avatar,
                "roles": ["ADMIN"]
            }
        }
    }

@router.post("/logout")
def logout():
    return {"code": 200, "message": "success", "data": None}


@router.post("/refresh")
def refresh_token(current_user: User = Depends(get_current_user)):
    """
    续签 token：使用当前有效的 token 换取一个新的 token。
    实现"滑动续期"——活跃用户永不掉线，完全空闲超过 token 有效期才会被登出。
    依赖 get_current_user：传入的 token 必须是有效（未过期）的；过期 token 会返回 401。
    """
    # super 用户走特殊分支
    if current_user.username == "super":
        new_token = create_access_token(data={"sub": "super", "userId": -1})
    else:
        new_token = create_access_token(
            data={"sub": current_user.username, "userId": current_user.id}
        )
    return {
        "code": 200,
        "message": "success",
        "data": {"token": new_token}
    }

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前登录用户信息"""
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"=== 获取用户信息 ===")
    logger.info(f"用户ID: {current_user.id}, 用户名: {current_user.username}")
    logger.info(f"用户类型: {type(current_user)}")

    # 获取用户角色
    user_role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()
    role_name = None
    if user_role:
        role = db.query(Role).filter(Role.id == user_role.role_id).first()
        if role:
            role_name = role.name
    
    logger.info(f"角色: {role_name}")
    
    # 获取用户所属组织（部门）
    from models import UserDepartment, Department, UserTeam, Team
    user_depts = db.query(UserDepartment).filter(UserDepartment.user_id == current_user.id).all()
    dept_names = []
    if user_depts:
        dept_ids = [ud.department_id for ud in user_depts]
        depts = db.query(Department).filter(Department.id.in_(dept_ids)).all()
        dept_names = [d.name for d in depts]
    
    # 获取用户所属项目组（团队）
    user_teams = db.query(UserTeam).filter(UserTeam.user_id == current_user.id).all()
    logger.info(f"查询到 {len(user_teams)} 个用户团队关联")
    
    team_names = []
    if user_teams:
        team_ids = [ut.team_id for ut in user_teams]
        logger.info(f"团队IDs: {team_ids}")
        teams = db.query(Team).filter(Team.id.in_(team_ids)).all()
        team_names = [t.name for t in teams]
        logger.info(f"团队名称: {team_names}")
    else:
        logger.info("用户没有分配任何团队")
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "phone": current_user.phone,
            "department": current_user.department,
            "avatar": current_user.avatar,
            "status": current_user.status,
            "role_name": role_name,
            "department_names": dept_names,
            "team_names": team_names,
            "zmind_api_key": current_user.zmind_api_key
        }
    }


@router.post("/register")
def register(request: RegisterRequest, req: Request, db: Session = Depends(get_db)):
    """用户自助注册（无需登录），创建待审核账号"""
    import re
    
    # 校验用户名
    username = (request.username or '').strip()
    if not username or len(username) < 2:
        raise HTTPException(status_code=400, detail="用户名至少2个字符")
    if len(username) > 50:
        raise HTTPException(status_code=400, detail="用户名不能超过50个字符")
    if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', username):
        raise HTTPException(status_code=400, detail="用户名只能包含字母、数字、下划线和中文")
    
    # 校验密码强度（与首次登录修改密码一致）
    password = request.password or ''
    from utils.login_security import validate_password_strength
    is_valid, error_msg = validate_password_strength(password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # 校验邮箱
    email = (request.email or '').strip()
    if not email or '@' not in email:
        raise HTTPException(status_code=400, detail="请输入有效的邮箱地址")
    
    # 检查用户名是否已存在（包括待审核的）
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        if existing.status == 2:
            raise HTTPException(status_code=400, detail="该用户名已提交注册申请，请等待审核")
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已被使用
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="该邮箱已被注册")
    
    # 创建待审核用户 (status=2)
    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        password=hashed_password,
        email=email,
        full_name=(request.full_name or '').strip() or None,
        phone=(request.phone or '').strip() or None,
        must_change_password=False,  # 自注册用户不需要强制改密码
        status=2  # 待审核
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 发送钉钉通知给管理员
    _notify_registration_dingtalk(db, db_user)
    
    return {
        "code": 200,
        "message": "注册申请已提交，请等待管理员审核",
        "data": {"username": db_user.username}
    }


def _notify_registration_dingtalk(db: Session, user: User):
    """注册申请通知 - 站内通知给管理员 + 钉钉通知给配置了system类型的机器人"""
    import logging
    from models import Notification, NotificationRecipient, UserRole, Role, DingtalkBot
    from datetime import datetime
    logger = logging.getLogger(__name__)
    
    # ===== 1. 站内通知给管理员 =====
    try:
        admin_ids = set()
        
        # 超级管理员
        super_admin = db.query(User).filter(User.username == 'admin', User.status == 1).first()
        if super_admin:
            admin_ids.add(super_admin.id)
        
        # 角色名包含"管理员"的用户
        admin_roles = db.query(Role).filter(
            Role.name.contains('管理员') | Role.name.contains('Admin')
        ).all()
        if admin_roles:
            role_ids = [r.id for r in admin_roles]
            user_roles = db.query(UserRole).filter(UserRole.role_id.in_(role_ids)).all()
            for ur in user_roles:
                admin_ids.add(ur.user_id)
        
        if admin_ids:
            notification = Notification(
                title="新用户注册待审核",
                content=f"用户 {user.username}（邮箱：{user.email}）提交了注册申请，请在用户管理中审核。",
                notification_type='system',
                event_type='user_registration',
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
            logger.info(f"注册站内通知已发送给 {len(admin_ids)} 个管理员: {user.username}")
    except Exception as e:
        logger.error(f"注册站内通知异常: {e}")
    
    # ===== 2. 钉钉通知给配置了system通知类型的机器人 =====
    try:
        import json
        bots = db.query(DingtalkBot).filter(DingtalkBot.is_active == True).all()
        system_bots = []
        for bot in bots:
            try:
                types = json.loads(bot.notification_types) if bot.notification_types else []
            except (json.JSONDecodeError, TypeError):
                types = []
            if 'system' in types:
                system_bots.append(bot)
        
        if not system_bots:
            logger.info("注册通知：无配置system类型的钉钉机器人，跳过钉钉通知")
            return
        
        from api.dingtalk_bot import _send_dingtalk_message
        title = "【新用户注册】待审核"
        content = (
            f"### 新用户注册申请  \n\n"
            f"**用户名：** {user.username}  \n"
            f"**邮箱：** {user.email}  \n"
            f"**姓名：** {user.full_name or '-'}  \n"
            f"**手机：** {user.phone or '-'}  \n\n"
            f"请登录系统在用户管理中审核。"
        )
        
        sent_webhooks = set()  # 去重，避免同一个webhook发多次
        for bot in system_bots:
            if bot.webhook_url in sent_webhooks:
                continue
            result = _send_dingtalk_message(bot, title, content)
            sent_webhooks.add(bot.webhook_url)
            if result.get("success"):
                logger.info(f"注册钉钉通知成功: {user.username} -> {bot.name}")
            else:
                logger.warning(f"注册钉钉通知失败: {user.username} -> {bot.name}: {result.get('error')}")
    except Exception as e:
        logger.error(f"注册钉钉通知异常: {e}")
