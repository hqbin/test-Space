"""
重试装饰器

提供指数退避重试和数据库死锁重试功能
"""

import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple
import requests
from sqlalchemy.exc import OperationalError
from .exceptions import ExternalAPIError, DatabaseError

logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
):
    """
    指数退避重试装饰器
    
    用于外部API调用（如Zmind API）
    
    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        exponential_base: 指数基数
        
    Example:
        @retry_with_exponential_backoff(max_retries=3, base_delay=1)
        def call_external_api():
            response = requests.get(url)
            return response.json()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except requests.Timeout as e:
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} 超时，已重试{max_retries}次: {str(e)}"
                        )
                        raise ExternalAPIError(
                            service="External Service",
                            message="API调用超时，请稍后重试",
                            details={"attempts": max_retries + 1, "error": str(e)}
                        )
                    
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    logger.warning(
                        f"{func.__name__} 超时，{delay}秒后重试 "
                        f"(第{attempt + 1}次，共{max_retries}次)"
                    )
                    time.sleep(delay)
                    
                except requests.RequestException as e:
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} 失败，已重试{max_retries}次: {str(e)}"
                        )
                        raise ExternalAPIError(
                            service="External Service",
                            message=f"API调用失败: {str(e)}",
                            details={"attempts": max_retries + 1, "error": str(e)}
                        )
                    
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    logger.warning(
                        f"{func.__name__} 失败，{delay}秒后重试: {str(e)} "
                        f"(第{attempt + 1}次，共{max_retries}次)"
                    )
                    time.sleep(delay)
                    
                except Exception as e:
                    # 其他异常不重试，直接抛出
                    logger.error(f"{func.__name__} 发生未预期的错误: {str(e)}")
                    raise
            
            return None
        return wrapper
    return decorator


def retry_on_deadlock(max_retries: int = 3, delay: float = 1.0):
    """
    数据库死锁重试装饰器
    
    用于数据库操作
    
    Args:
        max_retries: 最大重试次数
        delay: 重试延迟时间（秒）
        
    Example:
        @retry_on_deadlock(max_retries=3)
        def save_data(db, data):
            with db.begin():
                db.add(data)
                db.commit()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                    
                except OperationalError as e:
                    error_msg = str(e).lower()
                    
                    if "deadlock" in error_msg:
                        if attempt == max_retries - 1:
                            logger.error(
                                f"{func.__name__} 数据库死锁，已重试{max_retries}次"
                            )
                            raise DatabaseError("数据库操作失败，请稍后重试")
                        
                        logger.warning(
                            f"{func.__name__} 数据库死锁，{delay}秒后重试 "
                            f"(第{attempt + 1}次，共{max_retries}次)"
                        )
                        time.sleep(delay)
                        
                        # 回滚事务
                        if 'db' in kwargs:
                            kwargs['db'].rollback()
                        elif len(args) > 0 and hasattr(args[0], 'rollback'):
                            args[0].rollback()
                    else:
                        # 不是死锁错误，直接抛出
                        raise
                        
                except Exception as e:
                    # 其他异常不重试，直接抛出
                    logger.error(f"{func.__name__} 发生未预期的错误: {str(e)}")
                    raise
            
            return None
        return wrapper
    return decorator


def retry_on_exception(
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    max_retries: int = 3,
    delay: float = 1.0
):
    """
    通用异常重试装饰器
    
    Args:
        exceptions: 需要重试的异常类型元组
        max_retries: 最大重试次数
        delay: 重试延迟时间（秒）
        
    Example:
        @retry_on_exception(exceptions=(ValueError, TypeError), max_retries=3)
        def process_data(data):
            return transform(data)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    if attempt == max_retries - 1:
                        logger.error(
                            f"{func.__name__} 失败，已重试{max_retries}次: {str(e)}"
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} 失败，{delay}秒后重试: {str(e)} "
                        f"(第{attempt + 1}次，共{max_retries}次)"
                    )
                    time.sleep(delay)
                    
                except Exception as e:
                    # 其他异常不重试，直接抛出
                    logger.error(f"{func.__name__} 发生未预期的错误: {str(e)}")
                    raise
            
            return None
        return wrapper
    return decorator


# 为API错误重试提供便捷别名
retry_on_api_error = retry_with_exponential_backoff
