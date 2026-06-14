"""
测试用例附件 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User, TestCase, TestCaseHistory
from auth import get_current_user, security
from services.testcase_attachment_service import TestCaseAttachmentService
from utils.logger import log_operation, LogAction, LogModule
import base64
from urllib.parse import quote

router = APIRouter()

# 附件大小限制 100MB
MAX_FILE_SIZE = 100 * 1024 * 1024

@router.post("/{test_case_id}/attachments")
async def upload_attachment(
    test_case_id: int,
    file: UploadFile = File(...),
    description: str = Form(None),
    req: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传测试用例附件（存储到数据库）"""
    # 检查测试用例是否存在
    testcase = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not testcase:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    # 读取文件内容
    contents = await file.read()
    
    # 验证文件大小
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过100MB")
    
    # 转换为Base64
    file_base64 = base64.b64encode(contents).decode('utf-8')
    file_extension = file.filename.rsplit('.', 1)[-1] if '.' in file.filename else ''
    
    try:
        # 创建附件记录（存储到数据库）
        attachment = TestCaseAttachmentService.create_attachment(
            db=db,
            test_case_id=test_case_id,
            file_name=file.filename,
            file_data=file_base64,
            file_size=len(contents),
            file_type=file.content_type or "application/octet-stream",
            file_extension=file_extension,
            uploader_id=current_user.id,
            description=description
        )
        
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.TESTCASES,
            action=LogAction.CREATE,
            description=f"上传附件：{file.filename} 到测试用例 {testcase.name}（ID: {test_case_id}）",
            request=req
        )
        
        # 记录附件上传历史
        db.add(TestCaseHistory(
            testcase_id=test_case_id,
            field_name='上传附件',
            old_value=None,
            new_value=file.filename,
            changed_by=current_user.id,
            changed_by_name=current_user.username
        ))
        db.commit()
        
        return {
            "code": 200,
            "message": "上传成功",
            "data": {
                "id": attachment.id,
                "file_name": attachment.file_name,
                "file_size": attachment.file_size,
                "upload_time": attachment.upload_time,
                "description": attachment.description
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.get("/{test_case_id}/attachments")
def get_attachments(
    test_case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取测试用例的所有附件"""
    testcase = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not testcase:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    attachments = TestCaseAttachmentService.get_attachments(db, test_case_id)
    
    return {
        "code": 200,
        "message": "success",
        "data": [
            {
                "id": att.id,
                "file_name": att.file_name,
                "file_size": att.file_size,
                "file_type": att.file_type,
                "upload_time": att.upload_time,
                "uploader_id": att.uploader_id,
                "description": att.description
            }
            for att in attachments
        ]
    }

@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载附件（从数据库读取）"""
    attachment = TestCaseAttachmentService.get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    
    # 从数据库读取Base64数据
    # 注意：空文件的 file_data 是空字符串 ""，需用 is None 判断而非 not
    if attachment.file_data is None:
        raise HTTPException(status_code=404, detail="附件数据不存在")
    
    file_data = base64.b64decode(attachment.file_data)
    
    encoded_name = quote(attachment.file_name, safe='')
    return Response(
        content=file_data,
        media_type=attachment.file_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"
        }
    )

@router.get("/attachments/{attachment_id}/preview")
def preview_attachment(
    attachment_id: int,
    token: str = None,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """预览附件（内联显示，支持query param传token用于img/iframe）"""
    from jose import JWTError, jwt as jose_jwt
    from config import settings as app_settings
    
    # 优先用 Authorization header，其次用 query param token
    auth_token = None
    if credentials:
        auth_token = credentials.credentials
    elif token:
        auth_token = token
    
    if not auth_token:
        raise HTTPException(status_code=401, detail="未提供认证信息")
    
    try:
        payload = jose_jwt.decode(auth_token, app_settings.SECRET_KEY, algorithms=[app_settings.ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="无效的token")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的token")
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    attachment = TestCaseAttachmentService.get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    
    if attachment.file_data is None:
        raise HTTPException(status_code=404, detail="附件数据不存在")
    
    file_data = base64.b64decode(attachment.file_data)
    
    encoded_name = quote(attachment.file_name, safe='')
    return Response(
        content=file_data,
        media_type=attachment.file_type,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{encoded_name}"
        }
    )

@router.delete("/attachments/{attachment_id}")
def delete_attachment(
    attachment_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除附件"""
    attachment = TestCaseAttachmentService.get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    
    file_name = attachment.file_name
    test_case_id = attachment.test_case_id
    
    # 软删除
    TestCaseAttachmentService.delete_attachment(db, attachment_id)
    
    # 记录附件删除历史
    db.add(TestCaseHistory(
        testcase_id=test_case_id,
        field_name='删除附件',
        old_value=file_name,
        new_value=None,
        changed_by=current_user.id,
        changed_by_name=current_user.full_name or current_user.username
    ))
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.TESTCASES,
        action=LogAction.DELETE,
        description=f"删除附件：{file_name}（测试用例ID: {test_case_id}）",
        request=req
    )
    
    return {"code": 200, "message": "删除成功", "data": None}
