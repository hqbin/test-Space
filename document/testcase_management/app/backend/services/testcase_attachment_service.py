"""
测试用例附件服务
"""
from sqlalchemy.orm import Session
from models import TestCaseAttachment
from typing import List, Optional
from datetime import datetime

class TestCaseAttachmentService:
    """测试用例附件服务"""
    
    @staticmethod
    def create_attachment(
        db: Session,
        test_case_id: int,
        file_name: str,
        file_data: str,  # Base64编码的文件数据
        file_size: int,
        file_type: str,
        file_extension: str,
        uploader_id: int,
        description: str = None
    ) -> TestCaseAttachment:
        """创建附件记录（存储到数据库）"""
        attachment = TestCaseAttachment(
            test_case_id=test_case_id,
            file_name=file_name,
            file_data=file_data,
            file_path=None,  # 不再使用文件路径
            file_size=file_size,
            file_type=file_type,
            file_extension=file_extension,
            uploader_id=uploader_id,
            description=description,
            upload_time=datetime.now()
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        return attachment
    
    @staticmethod
    def get_attachments(db: Session, test_case_id: int) -> List[TestCaseAttachment]:
        """获取测试用例的所有附件"""
        return db.query(TestCaseAttachment).filter(
            TestCaseAttachment.test_case_id == test_case_id,
            TestCaseAttachment.is_deleted == False
        ).all()
    
    @staticmethod
    def delete_attachment(db: Session, attachment_id: int) -> bool:
        """删除附件（软删除）"""
        attachment = db.query(TestCaseAttachment).filter(
            TestCaseAttachment.id == attachment_id
        ).first()
        
        if attachment:
            attachment.is_deleted = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_attachment(db: Session, attachment_id: int) -> Optional[TestCaseAttachment]:
        """获取单个附件"""
        return db.query(TestCaseAttachment).filter(
            TestCaseAttachment.id == attachment_id,
            TestCaseAttachment.is_deleted == False
        ).first()
