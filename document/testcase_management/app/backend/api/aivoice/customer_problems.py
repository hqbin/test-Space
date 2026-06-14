from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import json

from database import get_db
from auth import get_current_user
from models import User
from models_aivoice import AiVoiceCustomerProblem
from schemas_aivoice import AiVoiceCustomerProblemCreate, AiVoiceCustomerProblemUpdate

router = APIRouter(prefix="/customer-problems", tags=["问题跟踪"])


def _serialize(cp):
    return {
        "id": cp.id,
        "problemType": cp.problemType or "qa",
        "issueId": cp.issueId,
        "firmwareVersion": cp.firmwareVersion,
        "description": cp.description,
        "classification": cp.classification,
        "confidence": cp.confidence,
        "status": cp.status or "开放",
        "linkedQaProblems": json.loads(cp.linkedQaProblems) if cp.linkedQaProblems else [],
        "workspaceId": cp.workspaceId or "AI Voice",
        "projectType": cp.projectType,
        "issueCreatedAt": cp.issueCreatedAt or "",
        "notes": cp.notes,
        "createdById": cp.createdById,
        "createdAt": cp.createdAt.isoformat() if cp.createdAt else None,
        "updatedAt": cp.updatedAt.isoformat() if cp.updatedAt else None,
    }


@router.get("")
def list_customer_problems(
    workspaceId: str = Query("AI Voice"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    problemType: Optional[str] = None,
    status: Optional[str] = None,
    classification: Optional[str] = None,
    projectType: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AiVoiceCustomerProblem).filter(AiVoiceCustomerProblem.workspaceId == workspaceId)
    if problemType:
        q = q.filter(AiVoiceCustomerProblem.problemType == problemType)
    if status:
        q = q.filter(AiVoiceCustomerProblem.status == status)
    if classification:
        q = q.filter(AiVoiceCustomerProblem.classification == classification)
    if projectType:
        q = q.filter(AiVoiceCustomerProblem.projectType == projectType)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(AiVoiceCustomerProblem.description.ilike(kw))
    q = q.order_by(desc(AiVoiceCustomerProblem.createdAt))
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


@router.get("/{problem_id}")
def get_customer_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    problem = db.query(AiVoiceCustomerProblem).filter(AiVoiceCustomerProblem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"code": 200, "message": "success", "data": _serialize(problem)}


@router.post("")
def create_customer_problem(
    data: AiVoiceCustomerProblemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    problem = AiVoiceCustomerProblem(
        problemType=data.problemType or "qa",
        issueId=data.issueId,
        firmwareVersion=data.firmwareVersion,
        description=data.description,
        classification=data.classification,
        confidence=data.confidence,
        status=data.status or "开放",
        linkedQaProblems=json.dumps(data.linkedQaProblems) if data.linkedQaProblems else "[]",
        workspaceId=data.workspaceId or "AI Voice",
        projectType=data.projectType,
        issueCreatedAt=data.issueCreatedAt or "",
        notes=data.notes,
        createdById=current_user.id,
    )
    db.add(problem)
    db.commit()
    db.refresh(problem)
    return {"code": 200, "message": "success", "data": {"id": problem.id}}


@router.put("/{problem_id}")
def update_customer_problem(
    problem_id: int,
    data: AiVoiceCustomerProblemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    problem = db.query(AiVoiceCustomerProblem).filter(AiVoiceCustomerProblem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="记录不存在")
    update_dict = data.model_dump(exclude_unset=True)
    if "linkedQaProblems" in update_dict and update_dict["linkedQaProblems"] is not None:
        update_dict["linkedQaProblems"] = json.dumps(update_dict["linkedQaProblems"])
    for key, value in update_dict.items():
        setattr(problem, key, value)
    db.commit()
    return {"code": 200, "message": "更新成功"}


@router.delete("/{problem_id}")
def delete_customer_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    problem = db.query(AiVoiceCustomerProblem).filter(AiVoiceCustomerProblem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(problem)
    db.commit()
    return {"code": 200, "message": "删除成功"}
