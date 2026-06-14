"""
数据库错误处理器
提供统一的数据库错误分类和处理
"""
import logging
from datetime import datetime
from sqlalchemy.exc import (
    OperationalError,
    IntegrityError,
    DataError,
    ProgrammingError,
    TimeoutError as SQLTimeoutError
)

logger = logging.getLogger(__name__)


class DatabaseErrorHandler:
    """数据库错误处理器"""
    
    @staticmethod
    def classify_error(error):
        """
        分类数据库错误
        
        Args:
            error: 数据库异常对象
        
        Returns:
            tuple: (错误类型, 用户友好提示)
        """
        if isinstance(error, SQLTimeoutError):
            return "连接超时", "数据库连接超时，请稍后重试"
        
        elif isinstance(error, OperationalError):
            error_msg = str(error).lower()
            if "could not connect" in error_msg or "connection refused" in error_msg:
                return "连接失败", "无法连接到数据库服务器，请检查网络连接"
            elif "authentication failed" in error_msg or "password authentication failed" in error_msg:
                return "认证失败", "数据库认证失败，请检查配置"
            elif "timeout" in error_msg:
                return "查询超时", "数据库查询超时，请稍后重试"
            else:
                return "操作错误", "数据库操作失败，请联系管理员"
        
        elif isinstance(error, IntegrityError):
            error_msg = str(error).lower()
            if "unique constraint" in error_msg or "duplicate key" in error_msg:
                return "约束违反", "数据已存在，请检查输入"
            elif "foreign key constraint" in error_msg:
                return "约束违反", "关联数据不存在，请检查输入"
            else:
                return "约束违反", "数据完整性约束违反，请检查输入数据"
        
        elif isinstance(error, DataError):
            return "数据错误", "数据格式或类型错误，请检查输入"
        
        elif isinstance(error, ProgrammingError):
            return "编程错误", "SQL 语句错误，请联系管理员"
        
        else:
            return "未知错误", "数据库操作失败，请联系管理员"
    
    @staticmethod
    def log_database_error(error, sql=None, params=None, context=None):
        """
        记录数据库错误
        
        Args:
            error: 数据库异常对象
            sql: SQL 语句（可选）
            params: SQL 参数（可选）
            context: 上下文信息（可选）
        
        Returns:
            str: 用户友好的错误提示
        """
        error_type, user_message = DatabaseErrorHandler.classify_error(error)
        
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": str(error),
            "user_message": user_message,
        }
        
        if sql:
            log_data["sql"] = sql
        if params:
            log_data["params"] = params
        if context:
            log_data["context"] = context
        
        logger.error(f"数据库错误: {log_data}", exc_info=True)
        
        return user_message
