from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime
import json

from database import get_db
from auth import get_current_user
from models import User
from models_aivoice import AiVoiceVersionRecord
from schemas_aivoice import AiVoiceVersionRecordCreate, AiVoiceVersionRecordUpdate

router = APIRouter(prefix="/version-records", tags=["版本记录"])

VERSION_STATUS_FLOW = ["待测试", "测试中", "阻塞", "待结论", "可发布", "已发布"]
RELEASE_DECISIONS = ["待评估", "可发布", "有条件发布", "不可发布"]


def _serialize(vr):
    return {
        "id": vr.id,
        "releaseNoteId": vr.releaseNoteId,
        "qaEarlyInterventionReason": vr.qaEarlyInterventionReason,
        "qaEarlyInterventionOwner": vr.qaEarlyInterventionOwner,
        "versionNumber": vr.versionNumber,
        "parentVersion": vr.parentVersion or "",
        "firmwareVersion": vr.firmwareVersion,
        "linkedIssues": json.loads(vr.linkedIssues) if vr.linkedIssues else [],
        "changeDescription": vr.changeDescription,
        "modifiedModules": json.loads(vr.modifiedModules) if vr.modifiedModules else [],
        "riskLevel": vr.riskLevel,
        "smokeTestResult": vr.smokeTestResult,
        "voiceRegressionResult": vr.voiceRegressionResult,
        "systemRegressionResult": vr.systemRegressionResult,
        "workspaceId": vr.workspaceId or "AI Voice",
        "projectType": vr.projectType,
        "testCycle": vr.testCycle,
        "prototypeSource": vr.prototypeSource,
        "prototypeFileName": vr.prototypeFileName,
        "prototypeFilePath": vr.prototypeFilePath,
        "prototypeFileSize": vr.prototypeFileSize,
        "testResultFileName": vr.testResultFileName,
        "testResultFilePath": vr.testResultFilePath,
        "testResultFileSize": vr.testResultFileSize,
        "languageModel": vr.languageModel,
        "versionStatus": vr.versionStatus or "待测试",
        "releaseDecision": vr.releaseDecision or "待评估",
        "conclusionSummary": vr.conclusionSummary,
        "remainingRisks": vr.remainingRisks,
        "nextActions": vr.nextActions,
        "conclusionOwner": vr.conclusionOwner,
        "conclusionUpdatedAt": vr.conclusionUpdatedAt.isoformat() if vr.conclusionUpdatedAt else None,
        "notes": vr.notes,
        "createdById": vr.createdById,
        "createdAt": vr.createdAt.isoformat() if vr.createdAt else None,
        "updatedAt": vr.updatedAt.isoformat() if vr.updatedAt else None,
    }


@router.get("")
def list_version_records(
    workspaceId: str = Query("AI Voice"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    versionStatus: Optional[str] = None,
    projectType: Optional[str] = None,
    riskLevel: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AiVoiceVersionRecord).filter(AiVoiceVersionRecord.workspaceId == workspaceId)
    if versionStatus:
        q = q.filter(AiVoiceVersionRecord.versionStatus == versionStatus)
    if projectType:
        q = q.filter(AiVoiceVersionRecord.projectType == projectType)
    if riskLevel:
        q = q.filter(AiVoiceVersionRecord.riskLevel == riskLevel)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(AiVoiceVersionRecord.versionNumber.ilike(kw) | AiVoiceVersionRecord.changeDescription.ilike(kw))
    q = q.order_by(desc(AiVoiceVersionRecord.createdAt))
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


@router.get("/{record_id}")
def get_version_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(AiVoiceVersionRecord).filter(AiVoiceVersionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"code": 200, "message": "success", "data": _serialize(record)}


@router.post("")
def create_version_record(
    data: AiVoiceVersionRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = AiVoiceVersionRecord(
        releaseNoteId=data.releaseNoteId,
        qaEarlyInterventionReason=data.qaEarlyInterventionReason,
        qaEarlyInterventionOwner=data.qaEarlyInterventionOwner,
        versionNumber=data.versionNumber,
        parentVersion=data.parentVersion or "",
        firmwareVersion=data.firmwareVersion,
        linkedIssues=json.dumps(data.linkedIssues) if data.linkedIssues else "[]",
        changeDescription=data.changeDescription,
        modifiedModules=json.dumps(data.modifiedModules) if data.modifiedModules else "[]",
        riskLevel=data.riskLevel or "中",
        smokeTestResult=data.smokeTestResult or "未测试",
        voiceRegressionResult=data.voiceRegressionResult or "未测试",
        systemRegressionResult=data.systemRegressionResult or "未测试",
        workspaceId=data.workspaceId or "AI Voice",
        projectType=data.projectType,
        testCycle=data.testCycle,
        prototypeSource=data.prototypeSource,
        languageModel=data.languageModel,
        notes=data.notes,
        versionStatus="待测试",
        createdById=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"code": 200, "message": "success", "data": {"id": record.id}}


@router.put("/{record_id}")
def update_version_record(
    record_id: int,
    data: AiVoiceVersionRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(AiVoiceVersionRecord).filter(AiVoiceVersionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    update_dict = data.model_dump(exclude_unset=True)
    if "linkedIssues" in update_dict and update_dict["linkedIssues"] is not None:
        update_dict["linkedIssues"] = json.dumps(update_dict["linkedIssues"])
    if "modifiedModules" in update_dict and update_dict["modifiedModules"] is not None:
        update_dict["modifiedModules"] = json.dumps(update_dict["modifiedModules"])
    for key, value in update_dict.items():
        setattr(record, key, value)
    db.commit()
    return {"code": 200, "message": "更新成功"}


@router.delete("/{record_id}")
def delete_version_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(AiVoiceVersionRecord).filter(AiVoiceVersionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"code": 200, "message": "删除成功"}


@router.post("/{record_id}/transition")
def transition_status(
    record_id: int,
    targetStatus: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(AiVoiceVersionRecord).filter(AiVoiceVersionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    current_idx = VERSION_STATUS_FLOW.index(record.versionStatus) if record.versionStatus in VERSION_STATUS_FLOW else -1
    target_idx = VERSION_STATUS_FLOW.index(targetStatus) if targetStatus in VERSION_STATUS_FLOW else -1
    if target_idx < 0:
        raise HTTPException(status_code=400, detail=f"无效的目标状态: {targetStatus}")
    if target_idx <= current_idx:
        raise HTTPException(status_code=400, detail="状态只能向前流转")
    record.versionStatus = targetStatus
    db.commit()
    return {"code": 200, "message": f"状态已更新为: {targetStatus}"}


@router.get("/status-flow/options")
def get_status_flow_options():
    return {"code": 200, "message": "success", "data": VERSION_STATUS_FLOW}


@router.get("/release-decisions/options")
def get_release_decisions():
    return {"code": 200, "message": "success", "data": RELEASE_DECISIONS}
