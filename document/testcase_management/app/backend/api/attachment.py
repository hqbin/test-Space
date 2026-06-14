"""
附件管理API
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from models import User
from services import AttachmentService
from utils.permissions import can_delete_attachment
from utils.exceptions import NotFoundError, ValidationError, UploadError
from utils.logger import log_operation, LogAction, LogModule
import base64
from urllib.parse import quote

router = APIRouter(prefix="/api/attachments", tags=["attachments"])


@router.post("/executions/{execution_id}/upload")
async def upload_attachment(
    execution_id: int,
    file: UploadFile = File(...),
    description: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传附件（存储到数据库）
    
    - 单个文件最大10MB
    - 每个执行记录最多10个附件
    - 支持所有常见文件类型
    """
    try:
        attachment = AttachmentService.upload_attachment(
            execution_id=execution_id,
            file=file,
            uploader_id=current_user.id,
            db=db,
            description=description
        )
        
        return {
            "code": 200,
            "message": "上传成功",
            "data": {
                "id": attachment.id,
                "file_name": attachment.file_name,
                "file_size": attachment.file_size,
                "file_type": attachment.file_type,
                "upload_time": attachment.upload_time.isoformat()
            }
        }
    except (NotFoundError, ValidationError, UploadError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"上传失败: {str(e)}")


@router.get("/executions/{execution_id}")
def get_attachments(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取执行记录的所有附件
    """
    try:
        attachments = AttachmentService.get_attachments(execution_id, db)
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": [
                {
                    "id": att.id,
                    "file_name": att.file_name,
                    "file_size": att.file_size,
                    "file_type": att.file_type,
                    "file_extension": att.file_extension,
                    "upload_time": att.upload_time.isoformat(),
                    "uploader_id": att.uploader_id,
                    "description": att.description
                }
                for att in attachments
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    下载附件（从数据库读取）
    """
    try:
        attachment = AttachmentService.get_attachment(attachment_id, db)
        
        if not attachment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件不存在")
        
        # 从数据库读取Base64数据
        # 空文件的 file_data 是空字符串 ""，需用 is None 判断而非 not
        if attachment.file_data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件数据不存在")
        
        file_data = base64.b64decode(attachment.file_data)
        
        encoded_name = quote(attachment.file_name, safe='')
        return Response(
            content=file_data,
            media_type=attachment.file_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{attachment_id}")
def delete_attachment(
    attachment_id: int,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除附件（软删除）
    
    权限：管理员或上传者本人
    """
    try:
        attachment = AttachmentService.get_attachment(attachment_id, db)
        
        if not attachment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件不存在")
        
        # 权限检查
        if not can_delete_attachment(current_user, attachment.uploader_id, db):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除此附件")
        
        attachment_name = attachment.filename if hasattr(attachment, 'filename') else f"ID:{attachment_id}"
        
        AttachmentService.delete_attachment(attachment_id, current_user.id, db)
        
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.SYSTEM,
            action=LogAction.DELETE,
            description=f"删除附件：{attachment_name}（ID: {attachment_id}）",
            request=req
        )
        
        return {
            "code": 200,
            "message": "删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
