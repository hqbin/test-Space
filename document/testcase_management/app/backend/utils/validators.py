"""
验证工具函数

提供文件上传、内容验证等功能
"""

from pathlib import Path
from typing import Set
from fastapi import UploadFile
from .exceptions import ValidationError, UploadError


# 允许的文件MIME类型
ALLOWED_MIME_TYPES: Set[str] = {
    # 图片
    'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp',
    # 文档
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain', 'text/csv',
    # 视频
    'video/mp4', 'video/x-msvideo', 'video/quicktime', 'video/x-ms-wmv',
    # 压缩文件
    'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
    'application/x-tar', 'application/gzip'
}

# 危险的文件扩展名（黑名单）
DANGEROUS_EXTENSIONS: Set[str] = {
    '.exe', '.bat', '.cmd', '.com', '.pif', '.scr',
    '.vbs', '.js', '.jar', '.msi', '.dll', '.sh', '.ps1'
}

# 最大文件大小（100MB）
MAX_FILE_SIZE = 100 * 1024 * 1024


def validate_file_upload(file: UploadFile, execution_id: int, db) -> bool:
    """
    验证文件上传
    
    Args:
        file: 上传的文件
        execution_id: 执行记录ID
        db: 数据库会话
        
    Returns:
        bool: 验证通过返回True
        
    Raises:
        UploadError: 验证失败时抛出异常
    """
    from models import TestExecutionAttachment
    from sqlalchemy import func
    
    # 1. 文件名验证
    if not file.filename or len(file.filename) > 255:
        raise UploadError("文件名无效或过长（最大255字符）")
    
    # 2. 文件扩展名验证
    ext = Path(file.filename).suffix.lower()
    if ext in DANGEROUS_EXTENSIONS:
        raise UploadError(f"不允许上传{ext}类型的文件")
    
    # 3. 文件大小验证
    if file.size and file.size > MAX_FILE_SIZE:
        raise UploadError("文件大小不能超过100MB")
    
    # 4. MIME类型验证
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise UploadError(f"不支持的文件类型: {file.content_type}")
    
    # 5. 附件数量验证
    existing_count = db.query(func.count(TestExecutionAttachment.id)).filter(
        TestExecutionAttachment.execution_id == execution_id,
        TestExecutionAttachment.is_deleted == False
    ).scalar()
    
    if existing_count >= 10:
        raise UploadError("每个执行记录最多上传10个附件")
    
    return True


def validate_comment_content(content: str) -> str:
    """
    验证评论内容
    
    Args:
        content: 评论内容
        
    Returns:
        str: 清理后的内容
        
    Raises:
        ValidationError: 验证失败时抛出异常
    """
    if not content or not content.strip():
        raise ValidationError("评论内容不能为空")
    
    if len(content) > 2000:
        raise ValidationError("评论内容不能超过2000字符")
    
    # 简单的HTML清理（移除script标签）
    import re
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    return content.strip()


def validate_execution_result(result: str, failure_reason: str = None) -> bool:
    """
    验证执行结果
    
    Args:
        result: 执行结果
        failure_reason: 失败原因
        
    Returns:
        bool: 验证通过返回True
        
    Raises:
        ValidationError: 验证失败时抛出异常
    """
    allowed_results = ['PASSED', 'FAILED', 'BLOCKED', 'SKIPPED']
    
    if result not in allowed_results:
        raise ValidationError(
            f"执行结果必须为{'/'.join(allowed_results)}之一",
            {"field": "result", "value": result}
        )
    
    if result == 'FAILED' and not failure_reason:
        raise ValidationError(
            "失败时必须填写失败原因",
            {"field": "failure_reason"}
        )
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除危险字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    import re
    
    # 移除路径分隔符和其他危险字符
    filename = re.sub(r'[/\\:*?"<>|]', '_', filename)
    
    # 限制长度
    name = Path(filename).stem[:200]
    ext = Path(filename).suffix[:20]
    
    return f"{name}{ext}"
