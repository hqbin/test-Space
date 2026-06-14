"""
登录安全模块
- 登录失败次数限制与账户临时锁定
- 密码强度校验
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from models import LoginAttempt

# ==================== 配置 ====================
MAX_FAILED_ATTEMPTS = 5          # 最大连续失败次数
LOCKOUT_MINUTES = 15             # 锁定时长（分钟）

# ==================== 密码强度 ====================
MIN_PASSWORD_LENGTH = 8

def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    校验密码强度
    要求：至少8位，包含大写、小写、数字、特殊字符中的至少3种
    
    Returns:
        (is_valid, error_message)
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"密码长度不能少于{MIN_PASSWORD_LENGTH}位"

    categories = 0
    if re.search(r'[A-Z]', password):
        categories += 1
    if re.search(r'[a-z]', password):
        categories += 1
    if re.search(r'\d', password):
        categories += 1
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]', password):
        categories += 1

    if categories < 3:
        return False, "密码需包含大写字母、小写字母、数字、特殊字符中的至少3种"

    return True, None


# ==================== 登录锁定 ====================

def _get_recent_failures(db: Session, username: str):
    """
    获取最近一次成功登录之后的连续失败记录
    如果没有成功记录，则取所有失败记录
    """
    # 找最后一次成功登录的时间
    last_success_time = db.query(sa_func.max(LoginAttempt.created_at)).filter(
        LoginAttempt.username == username,
        LoginAttempt.success == True
    ).scalar()

    query = db.query(LoginAttempt).filter(
        LoginAttempt.username == username,
        LoginAttempt.success == False
    )
    if last_success_time:
        query = query.filter(LoginAttempt.created_at > last_success_time)

    return query.order_by(LoginAttempt.created_at.desc()).all()


def check_account_locked(db: Session, username: str) -> Tuple[bool, int]:
    """
    检查账户是否被锁定
    
    逻辑：从最后一次成功登录之后，连续失败 >= MAX_FAILED_ATTEMPTS 次，
    且最后一次失败距今 < LOCKOUT_MINUTES 分钟，则锁定。
    
    Returns:
        (is_locked, remaining_seconds)
    """
    failures = _get_recent_failures(db, username)
    
    if len(failures) < MAX_FAILED_ATTEMPTS:
        return False, 0

    # 最后一次失败的时间（failures[0] 是最新的）
    last_fail_time = failures[0].created_at
    unlock_at = last_fail_time + timedelta(minutes=LOCKOUT_MINUTES)
    now = datetime.utcnow()

    if now < unlock_at:
        remaining = int((unlock_at - now).total_seconds())
        return True, remaining

    # 锁定已过期
    return False, 0


def record_login_attempt(db: Session, username: str, ip_address: str, success: bool):
    """记录登录尝试"""
    attempt = LoginAttempt(
        username=username,
        ip_address=ip_address,
        success=success
    )
    db.add(attempt)
    db.commit()


def get_failed_count(db: Session, username: str) -> int:
    """获取最后一次成功登录之后的连续失败次数"""
    failures = _get_recent_failures(db, username)
    return len(failures)
