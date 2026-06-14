from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import json

from database import get_db
from auth import get_current_user
from models import User
from models_aivoice import AiVoiceTestCase
from schemas_aivoice import AiVoiceTestCaseCreate, AiVoiceTestCaseUpdate

router = APIRouter(prefix="/knowledge-base", tags=["知识库"])


def _serialize(tc):
    return {
        "id": tc.id,
        "caseId": tc.caseId or "",
        "caseName": tc.caseName,
        "description": tc.description or "",
        "precondition": tc.precondition or "",
        "steps": json.loads(tc.steps) if tc.steps else [],
        "expectedResult": tc.expectedResult or "",
        "category": tc.category,
        "module": tc.module or "",
        "priority": tc.priority or "中",
        "workspaceId": tc.workspaceId or "AI Voice",
        "projectType": tc.projectType,
        "tags": json.loads(tc.tags) if tc.tags else [],
        "createdById": tc.createdById,
        "createdAt": tc.createdAt.isoformat() if tc.createdAt else None,
        "updatedAt": tc.updatedAt.isoformat() if tc.updatedAt else None,
    }


@router.get("")
def list_test_cases(
    workspaceId: str = Query("AI Voice"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    projectType: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AiVoiceTestCase).filter(AiVoiceTestCase.workspaceId == workspaceId)
    if category:
        q = q.filter(AiVoiceTestCase.category == category)
    if projectType:
        q = q.filter(AiVoiceTestCase.projectType == projectType)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(AiVoiceTestCase.caseName.ilike(kw) | AiVoiceTestCase.description.ilike(kw))
    q = q.order_by(desc(AiVoiceTestCase.createdAt))
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


@router.get("/{case_id}")
def get_test_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tc = db.query(AiVoiceTestCase).filter(AiVoiceTestCase.id == case_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"code": 200, "message": "success", "data": _serialize(tc)}


@router.post("")
def create_test_case(
    data: AiVoiceTestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tc = AiVoiceTestCase(
        caseId=data.caseId or "",
        caseName=data.caseName,
        description=data.description or "",
        precondition=data.precondition or "",
        steps=json.dumps(data.steps) if data.steps else "[]",
        expectedResult=data.expectedResult or "",
        category=data.category,
        module=data.module or "",
        priority=data.priority or "中",
        workspaceId=data.workspaceId or "AI Voice",
        projectType=data.projectType,
        tags=json.dumps(data.tags) if data.tags else "[]",
        createdById=current_user.id,
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return {"code": 200, "message": "success", "data": {"id": tc.id}}


@router.put("/{case_id}")
def update_test_case(
    case_id: int,
    data: AiVoiceTestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tc = db.query(AiVoiceTestCase).filter(AiVoiceTestCase.id == case_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="记录不存在")
    update_dict = data.model_dump(exclude_unset=True)
    if "steps" in update_dict and update_dict["steps"] is not None:
        update_dict["steps"] = json.dumps(update_dict["steps"])
    if "tags" in update_dict and update_dict["tags"] is not None:
        update_dict["tags"] = json.dumps(update_dict["tags"])
    for key, value in update_dict.items():
        setattr(tc, key, value)
    db.commit()
    return {"code": 200, "message": "更新成功"}


@router.delete("/{case_id}")
def delete_test_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tc = db.query(AiVoiceTestCase).filter(AiVoiceTestCase.id == case_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(tc)
    db.commit()
    return {"code": 200, "message": "删除成功"}
