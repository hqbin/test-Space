from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import json

from database import get_db
from auth import get_current_user
from models import User
from models_aivoice import AiVoiceVersionIssue
from schemas_aivoice import AiVoiceVersionIssueCreate, AiVoiceVersionIssueUpdate

router = APIRouter(prefix="/version-issues", tags=["版本问题"])


def _serialize(vi):
    return {
        "id": vi.id,
        "versionRecordId": vi.versionRecordId,
        "title": vi.title,
        "description": vi.description,
        "precondition": vi.precondition or "",
        "testEnvironment": vi.testEnvironment or "",
        "status": vi.status or "待处理",
        "severity": vi.severity or "中",
        "linkedPR": vi.linkedPR,
        "reporter": vi.reporter,
        "assignee": vi.assignee,
        "resolution": vi.resolution,
        "attachments": json.loads(vi.attachments) if vi.attachments else [],
        "syncedProblemId": vi.syncedProblemId or "",
        "createdById": vi.createdById,
        "createdAt": vi.createdAt.isoformat() if vi.createdAt else None,
        "updatedAt": vi.updatedAt.isoformat() if vi.updatedAt else None,
    }


@router.get("")
def list_version_issues(
    versionRecordId: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AiVoiceVersionIssue)
    if versionRecordId:
        q = q.filter(AiVoiceVersionIssue.versionRecordId == versionRecordId)
    if status:
        q = q.filter(AiVoiceVersionIssue.status == status)
    q = q.order_by(desc(AiVoiceVersionIssue.createdAt))
    total = q.count()
    records = q.offset((page - 1) * pageSize).limit(pageSize).all()
    return {
        "code": 200,
        "message": "success",
        "data": {
            "data": [_serialize(r) for r in records],
            "total": total,
            "page": page,
            "pageSize": pageSize,
            "totalPages": (total + pageSize - 1) // pageSize,
        },
    }


@router.get("/{issue_id}")
def get_version_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = db.query(AiVoiceVersionIssue).filter(AiVoiceVersionIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"code": 200, "message": "success", "data": _serialize(issue)}


@router.post("")
def create_version_issue(
    data: AiVoiceVersionIssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = AiVoiceVersionIssue(
        versionRecordId=data.versionRecordId,
        title=data.title,
        description=data.description,
        precondition=data.precondition or "",
        testEnvironment=data.testEnvironment or "",
        status=data.status or "待处理",
        severity=data.severity or "中",
        linkedPR=data.linkedPR,
        reporter=data.reporter,
        assignee=data.assignee,
        resolution=data.resolution,
        attachments=json.dumps(data.attachments) if data.attachments else "[]",
        syncedProblemId=data.syncedProblemId or "",
        createdById=current_user.id,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return {"code": 200, "message": "success", "data": {"id": issue.id}}


@router.put("/{issue_id}")
def update_version_issue(
    issue_id: int,
    data: AiVoiceVersionIssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = db.query(AiVoiceVersionIssue).filter(AiVoiceVersionIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="记录不存在")
    update_dict = data.model_dump(exclude_unset=True)
    if "attachments" in update_dict and update_dict["attachments"] is not None:
        update_dict["attachments"] = json.dumps(update_dict["attachments"])
    for key, value in update_dict.items():
        setattr(issue, key, value)
    db.commit()
    return {"code": 200, "message": "更新成功"}


@router.delete("/{issue_id}")
def delete_version_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = db.query(AiVoiceVersionIssue).filter(AiVoiceVersionIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(issue)
    db.commit()
    return {"code": 200, "message": "删除成功"}
