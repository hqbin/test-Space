from datetime import datetime, timedelta
from typing import Optional, List
import json
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from config import settings
from database import get_db
from models import User, UserRole, Role

security = HTTPBearer(auto_error=False)

# 超级管理员账号列表 - 这些账号拥有所有权限，不受角色系统控制
SUPER_ADMINS = ['admin', 'super']

def is_super_admin(user: User) -> bool:
    """检查用户是否是超级管理员"""
    return user.username in SUPER_ADMINS

def get_user_permissions(user: User, db: Session) -> List[str]:
    """获取用户的所有权限列表"""
    if is_super_admin(user):
        return []
    
    user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
    role_ids = [ur.role_id for ur in user_roles]
    
    if not role_ids:
        return []
    
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
    permissions = []
    for role in roles:
        if role.permissions:
            perms = json.loads(role.permissions)
            permissions.extend(perms)
    
    return list(set(permissions))

def has_permission(user: User, db: Session, permission: str) -> bool:
    """检查用户是否有特定权限"""
    if is_super_admin(user):
        return True
    
    permissions = get_user_permissions(user, db)
    return permission in permissions

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 无 token 或无效格式时返回 401
    if credentials is None:
        raise credentials_exception

    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if username == "super":
        class SuperUser:
            def __init__(self):
                self.id = -1
                self.username = "super"
                self.email = "super@admin.com"
                self.full_name = "super"
                self.phone = None
                self.avatar = None
                self.status = 1
                self.department = None
                self.password = ""
                self.must_change_password = False
                self.position_tag_id = None
                self.zmind_api_key = None
        return SuperUser()

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
