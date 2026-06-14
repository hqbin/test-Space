"""
配置验证工具
在应用启动时验证数据库配置
"""
import re
import logging
from urllib.parse import urlparse
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)


def validate_database_url(database_url):
    """
    验证数据库 URL 格式
    
    Args:
        database_url: 数据库连接字符串
    
    Returns:
        list: 错误列表，如果为空则验证通过
    """
    errors = []
    
    if not database_url:
        errors.append("DATABASE_URL 未配置")
        return errors
    
    try:
        parsed = urlparse(database_url)
        
        # 验证协议
        if parsed.scheme != 'postgresql':
            errors.append("DATABASE_URL 必须使用 postgresql 协议")
        
        # 验证主机名
        if not parsed.hostname:
            errors.append("DATABASE_URL 缺少主机名")
        
        # 验证用户名
        if not parsed.username:
            errors.append("DATABASE_URL 缺少用户名")
        
        # 验证端口
        if parsed.port and (parsed.port < 1 or parsed.port > 65535):
            errors.append(f"DATABASE_URL 端口号无效: {parsed.port}")
        
        # 验证数据库名
        if not parsed.path or parsed.path == '/':
            errors.append("DATABASE_URL 缺少数据库名")
            
    except Exception as e:
        errors.append(f"DATABASE_URL 格式错误: {str(e)}")
    
    return errors


def test_database_connection(database_url):
    """
    测试数据库连接
    
    Args:
        database_url: 数据库连接字符串
    
    Returns:
        tuple: (成功标志, 错误消息)
    """
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, None
    except Exception as e:
        return False, str(e)


def validate_database_config(settings):
    """
    验证数据库配置
    
    Args:
        settings: 配置对象
    
    Raises:
        ValueError: 配置验证失败
    """
    errors = []
    
    # 验证 URL 格式
    url_errors = validate_database_url(settings.DATABASE_URL)
    errors.extend(url_errors)
    
    # 如果 URL 格式正确，测试连接
    if not url_errors:
        success, error_msg = test_database_connection(settings.DATABASE_URL)
        if not success:
            errors.append(f"数据库连接测试失败: {error_msg}")
        else:
            logger.info("数据库连接测试成功")
    
    # 如果有错误，抛出异常
    if errors:
        for error in errors:
            logger.error(f"配置验证失败: {error}")
        raise ValueError("数据库配置验证失败，请检查配置")
    
    logger.info("数据库配置验证通过")
