"""
数据库重试装饰器
提供数据库操作的自动重试机制
"""
import time
import logging
from functools import wraps
from sqlalchemy.exc import OperationalError, DBAPIError

logger = logging.getLogger(__name__)


def db_retry(max_retries=3, delay=2):
    """
    数据库操作重试装饰器
    
    Args:
        max_retries: 最大重试次数，默认 3 次
        delay: 重试间隔（秒），默认 2 秒
    
    Returns:
        装饰器函数
    
    Example:
        @db_retry(max_retries=3, delay=2)
        def get_user(db, user_id):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DBAPIError) as e:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"数据库操作失败，{delay}秒后重试 "
                            f"(尝试 {attempt + 1}/{max_retries}): {str(e)}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"数据库操作失败，已达最大重试次数 "
                            f"({max_retries}): {str(e)}"
                        )
                        raise
        return wrapper
    return decorator
