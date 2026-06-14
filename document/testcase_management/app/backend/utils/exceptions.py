"""
自定义异常类

定义了统一的异常体系，用于API错误处理
"""

from fastapi import HTTPException
from typing import Optional, Dict, Any


class BaseAPIException(HTTPException):
    """API异常基类"""
    
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "details": details or {}
            }
        )


class ValidationError(BaseAPIException):
    """验证错误 - 400"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=400,
            code="VALIDATION_ERROR",
            message=message,
            details=details
        )


class AuthenticationError(BaseAPIException):
    """认证错误 - 401"""
    
    def __init__(self, message: str = "认证失败，请重新登录"):
        super().__init__(
            status_code=401,
            code="AUTHENTICATION_ERROR",
            message=message
        )


class PermissionError(BaseAPIException):
    """权限错误 - 403"""
    
    def __init__(self, message: str = "您没有权限执行此操作"):
        super().__init__(
            status_code=403,
            code="PERMISSION_ERROR",
            message=message
        )


class NotFoundError(BaseAPIException):
    """资源不存在 - 404"""
    
    def __init__(self, resource: str, resource_id: Optional[int] = None):
        message = f"{resource}不存在"
        if resource_id:
            message = f"{resource} (ID: {resource_id}) 不存在"
        super().__init__(
            status_code=404,
            code="NOT_FOUND",
            message=message
        )


class ConcurrencyError(BaseAPIException):
    """并发冲突错误 - 409"""
    
    def __init__(self, message: str = "数据已被其他用户修改，请刷新后重试"):
        super().__init__(
            status_code=409,
            code="CONCURRENCY_ERROR",
            message=message
        )


class BusinessRuleError(BaseAPIException):
    """业务规则错误 - 422"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=422,
            code="BUSINESS_RULE_ERROR",
            message=message,
            details=details
        )


class DatabaseError(BaseAPIException):
    """数据库错误 - 500"""
    
    def __init__(self, message: str = "数据库操作失败，请稍后重试"):
        super().__init__(
            status_code=500,
            code="DATABASE_ERROR",
            message=message
        )


class ExternalAPIError(BaseAPIException):
    """外部API错误 - 502"""
    
    def __init__(
        self,
        service: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=502,
            code="EXTERNAL_API_ERROR",
            message=f"{service} API调用失败: {message}",
            details=details
        )


class UploadError(BaseAPIException):
    """文件上传错误 - 400"""
    
    def __init__(self, message: str):
        super().__init__(
            status_code=400,
            code="UPLOAD_ERROR",
            message=message
        )


class APIError(BaseAPIException):
    """通用API错误"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "API_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            details=details
        )
