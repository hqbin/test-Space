"""
附件服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import TestExecutionAttachment, TestExecution, User
from utils.exceptions import ValidationError, NotFoundError, UploadError
from utils.validators import validate_file_upload
from datetime import datetime
import uuid
import base64
from typing import Optional


class AttachmentService:
    """附件管理服务"""
    
    @staticmethod
    def upload_attachment(
        execution_id: int,
        file,
        uploader_id: int,
        db: Session,
        description: Optional[str] = None
    ) -> TestExecutionAttachment:
        """
        上传附件（存储到数据库）
        
        Args:
            execution_id: 测试执行记录ID
            file: 上传的文件对象
            uploader_id: 上传者ID
            db: 数据库会话
            description: 附件描述
        
        Returns:
            TestExecutionAttachment: 附件记录
        
        Raises:
            NotFoundError: 执行记录不存在
            ValidationError: 验证失败
            UploadError: 上传失败
        """
        # 1. 检查执行记录是否存在
        execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
        if not execution:
            raise NotFoundError(f"测试执行记录不存在: {execution_id}")
        
        # 2. 检查附件数量限制
        existing_count = db.query(func.count(TestExecutionAttachment.id)).filter(
            TestExecutionAttachment.execution_id == execution_id,
            TestExecutionAttachment.is_deleted == False
        ).scalar()
        
        if existing_count >= 10:
            raise ValidationError("每个执行记录最多上传10个附件")
        
        # 3. 验证文件
        file_content = file.file.read()
        file.file.seek(0)  # 重置文件指针
        
        validate_file_upload(
            filename=file.filename,
            content=file_content,
            max_size=100 * 1024 * 1024  # 100MB
        )
        
        try:
            # 4. 转换为Base64存储到数据库
            file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # 5. 创建数据库记录
            from pathlib import Path
            attachment = TestExecutionAttachment(
                execution_id=execution_id,
                file_name=file.filename,
                file_data=file_base64,
                file_path=None,  # 不再使用文件路径
                file_size=len(file_content),
                file_type=file.content_type or 'application/octet-stream',
                file_extension=Path(file.filename).suffix,
                uploader_id=uploader_id,
                description=description
            )
            
            db.add(attachment)
            db.commit()
            db.refresh(attachment)
            
            return attachment
            
        except Exception as e:
            raise UploadError(f"文件上传失败: {str(e)}")
    
    @staticmethod
    def get_attachments(execution_id: int, db: Session) -> list[TestExecutionAttachment]:
        """
        获取执行记录的所有附件
        
        Args:
            execution_id: 测试执行记录ID
            db: 数据库会话
        
        Returns:
            list: 附件列表
        """
        attachments = db.query(TestExecutionAttachment).filter(
            TestExecutionAttachment.execution_id == execution_id,
            TestExecutionAttachment.is_deleted == False
        ).order_by(TestExecutionAttachment.upload_time.desc()).all()
        
        return attachments
    
    @staticmethod
    def get_attachment(attachment_id: int, db: Session) -> Optional[TestExecutionAttachment]:
        """
        获取单个附件
        
        Args:
            attachment_id: 附件ID
            db: 数据库会话
        
        Returns:
            TestExecutionAttachment: 附件记录
        """
        attachment = db.query(TestExecutionAttachment).filter(
            TestExecutionAttachment.id == attachment_id,
            TestExecutionAttachment.is_deleted == False
        ).first()
        
        return attachment
    
    @staticmethod
    def delete_attachment(attachment_id: int, user_id: int, db: Session) -> bool:
        """
        删除附件（软删除）
        
        Args:
            attachment_id: 附件ID
            user_id: 操作用户ID
            db: 数据库会话
        
        Returns:
            bool: 是否成功
        
        Raises:
            NotFoundError: 附件不存在
        """
        attachment = db.query(TestExecutionAttachment).filter(
            TestExecutionAttachment.id == attachment_id
        ).first()
        
        if not attachment:
            raise NotFoundError(f"附件不存在: {attachment_id}")
        
        # 软删除
        attachment.is_deleted = True
        db.commit()
        
        return True
