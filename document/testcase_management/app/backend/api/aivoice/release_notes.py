from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import json


class ImpactTagsUpdate(BaseModel):
    tags: list[str]

from database import get_db
from auth import get_current_user
from models import User
from models_aivoice import AiVoiceReleaseNote
from schemas_aivoice import AiVoiceReleaseNoteCreate, AiVoiceReleaseNoteUpdate, PagedResponse

router = APIRouter(prefix="/release-notes", tags=["发版说明"])


def _serialize(rn):
    data = {
        "id": rn.id,
        "version": rn.version,
        "parentVersion": rn.parentVersion or "",
        "branch": rn.branch or "",
        "commitHash": rn.commitHash,
        "commitMessage": rn.commitMessage,
        "author": rn.author,
        "changeDescription": rn.changeDescription,
        "affectedModules": json.loads(rn.affectedModules) if rn.affectedModules else [],
        "changeType": rn.changeType,
        "severity": rn.severity,
        "rdSmokeStatus": rn.rdSmokeStatus or "未测试",
        "testingNotes": rn.testingNotes,
        "regressionRisk": rn.regressionRisk,
        "affectedFeatures": json.loads(rn.affectedFeatures) if rn.affectedFeatures else [],
        "breakingChanges": rn.breakingChanges or False,
        "migrationType": rn.migrationType or "无",
        "workspaceId": rn.workspaceId or "AI Voice",
        "projectType": rn.projectType,
        "apkFileName": rn.apkFileName,
        "apkFileSize": rn.apkFileSize,
        "apkFilePath": rn.apkFilePath,
        "testReportFileName": rn.testReportFileName,
        "testReportFileSize": rn.testReportFileSize,
        "testReportFilePath": rn.testReportFilePath,
        "fixedPRs": json.loads(rn.fixedPRs) if rn.fixedPRs else [],
        "createdById": rn.createdById,
        "createdAt": rn.createdAt.isoformat() if rn.createdAt else None,
        "updatedAt": rn.updatedAt.isoformat() if rn.updatedAt else None,
    }
    return data


def _apply_filters(db_query, workspace_id: str, params: dict):
    q = db_query.filter(AiVoiceReleaseNote.workspaceId == workspace_id)
    if params.get("changeType"):
        q = q.filter(AiVoiceReleaseNote.changeType == params["changeType"])
    if params.get("severity"):
        q = q.filter(AiVoiceReleaseNote.severity == params["severity"])
    if params.get("branch"):
        q = q.filter(AiVoiceReleaseNote.branch == params["branch"])
    if params.get("rdSmokeStatus"):
        q = q.filter(AiVoiceReleaseNote.rdSmokeStatus == params["rdSmokeStatus"])
    if params.get("author"):
        q = q.filter(AiVoiceReleaseNote.author == params["author"])
    if params.get("projectType"):
        q = q.filter(AiVoiceReleaseNote.projectType == params["projectType"])
    if params.get("keyword"):
        kw = f"%{params['keyword']}%"
        q = q.filter(
            AiVoiceReleaseNote.version.ilike(kw) |
            AiVoiceReleaseNote.branch.ilike(kw) |
            AiVoiceReleaseNote.author.ilike(kw) |
            AiVoiceReleaseNote.changeDescription.ilike(kw) |
            AiVoiceReleaseNote.commitMessage.ilike(kw)
        )
    return q.order_by(desc(AiVoiceReleaseNote.createdAt))


@router.get("")
def list_release_notes(
    workspaceId: str = Query("AI Voice"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    changeType: Optional[str] = None,
    severity: Optional[str] = None,
    branch: Optional[str] = None,
    rdSmokeStatus: Optional[str] = None,
    author: Optional[str] = None,
    projectType: Optional[str] = None,
    keyword: Optional[str] = None,
    flat: Optional[bool] = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = {k: v for k, v in locals().items() if k in ("changeType", "severity", "branch", "rdSmokeStatus", "author", "projectType", "keyword") and v}
    query = _apply_filters(db.query(AiVoiceReleaseNote), workspaceId, filters)
    total = query.count()
    records = query.offset((page - 1) * pageSize).limit(pageSize).all()

    if flat:
        return {"code": 200, "message": "success", "data": {"data": [_serialize(r) for r in records], "total": total, "page": page, "pageSize": pageSize, "totalPages": (total + pageSize - 1) // pageSize}}

    parents = [r for r in records if not r.parentVersion]
    children = [r for r in records if r.parentVersion]
    child_map = {}
    for c in children:
        child_map.setdefault(c.parentVersion, []).append(_serialize(c))
    tree = []
    for p in parents:
        item = _serialize(p)
        item["children"] = sorted(child_map.get(p.version, []), key=lambda x: x["createdAt"], reverse=True)
        tree.append(item)
    for pv, cl in child_map.items():
        if not any(p.version == pv for p in parents):
            for c in cl:
                c["children"] = []
                tree.append(c)
    tree.sort(key=lambda x: x["createdAt"], reverse=True)

    return {"code": 200, "message": "success", "data": {"data": tree, "total": total, "page": page, "pageSize": pageSize, "totalPages": (total + pageSize - 1) // pageSize}}


@router.get("/parent-versions")
def get_parent_versions(
    projectType: Optional[str] = None,
    workspaceId: str = Query("AI Voice"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AiVoiceReleaseNote).filter(
        AiVoiceReleaseNote.workspaceId == workspaceId,
        AiVoiceReleaseNote.parentVersion == "",
    )
    if projectType:
        q = q.filter(AiVoiceReleaseNote.projectType == projectType)
    records = q.order_by(desc(AiVoiceReleaseNote.createdAt)).all()
    return {"code": 200, "message": "success", "data": [{"version": r.version, "projectType": r.projectType, "id": r.id} for r in records]}


@router.get("/eligible-for-qa")
def get_eligible_for_qa(
    projectType: Optional[str] = None,
    workspaceId: str = Query("AI Voice"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AiVoiceReleaseNote).filter(AiVoiceReleaseNote.workspaceId == workspaceId)
    if projectType:
        q = q.filter(AiVoiceReleaseNote.projectType == projectType)
    records = q.all()
    result = []
    for r in records:
        result.append({
            "id": r.id,
            "version": r.version,
            "parentVersion": r.parentVersion or "",
            "projectType": r.projectType,
            "changeDescription": r.changeDescription,
            "affectedModules": json.loads(r.affectedModules) if r.affectedModules else [],
            "regressionRisk": r.regressionRisk,
            "rdSmokeStatus": r.rdSmokeStatus or "未测试",
            "severity": r.severity,
            "qaEntryMode": "rd_smoke_passed" if r.rdSmokeStatus == "通过" else "urgent_override",
            "author": r.author,
            "branch": r.branch or "",
        })
    return {"code": 200, "message": "success", "data": result}


@router.get("/stats/summary")
def get_stats_summary(
    workspaceId: str = Query("AI Voice"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = db.query(AiVoiceReleaseNote).filter(AiVoiceReleaseNote.workspaceId == workspaceId).all()
    total = len(records)
    by_project = {}
    by_type = {}
    for r in records:
        pt = r.projectType or "unknown"
        by_project[pt] = by_project.get(pt, 0) + 1
        ct = r.changeType or "unknown"
        by_type[ct] = by_type.get(ct, 0) + 1
    return {"code": 200, "message": "success", "data": {"total": total, "byProject": by_project, "byType": by_type}}


@router.get("/impact-tags")
def get_impact_tags(
    workspaceId: str = Query("AI Voice"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from models_aivoice import AiVoiceSetting
    row = db.query(AiVoiceSetting).filter(AiVoiceSetting.key == f"release_note_impact_tags:{workspaceId}").first()
    if not row:
        return {"code": 200, "message": "success", "data": []}
    try:
        return {"code": 200, "message": "success", "data": json.loads(row.value)}
    except:
        return {"code": 200, "message": "success", "data": []}


@router.put("/impact-tags")
def update_impact_tags(
    body: ImpactTagsUpdate,
    workspaceId: str = Query("AI Voice"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from models_aivoice import AiVoiceSetting
    normalized = list(dict.fromkeys(t.strip() for t in body.tags if t.strip()))
    row = db.query(AiVoiceSetting).filter(AiVoiceSetting.key == f"release_note_impact_tags:{workspaceId}").first()
    if row:
        row.value = json.dumps(normalized)
    else:
        db.add(AiVoiceSetting(key=f"release_note_impact_tags:{workspaceId}", value=json.dumps(normalized)))
    db.commit()
    return {"code": 200, "message": "success", "data": normalized}


@router.get("/{note_id}")
def get_release_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(AiVoiceReleaseNote).filter(AiVoiceReleaseNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"code": 200, "message": "success", "data": _serialize(note)}


@router.post("")
def create_release_note(
    data: AiVoiceReleaseNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = AiVoiceReleaseNote(
        version=data.version,
        parentVersion=data.parentVersion or "",
        branch=data.branch or "",
        commitHash=data.commitHash,
        commitMessage=data.commitMessage,
        author=data.author,
        changeDescription=data.changeDescription,
        affectedModules=json.dumps(data.affectedModules) if data.affectedModules else "[]",
        changeType=data.changeType or "功能",
        severity=data.severity or "中",
        rdSmokeStatus=data.rdSmokeStatus or "未测试",
        testingNotes=data.testingNotes,
        regressionRisk=data.regressionRisk,
        affectedFeatures=json.dumps(data.affectedFeatures) if data.affectedFeatures else "[]",
        breakingChanges=data.breakingChanges or False,
        migrationType=data.migrationType or "无",
        workspaceId=data.workspaceId or "AI Voice",
        projectType=data.projectType,
        fixedPRs=json.dumps(data.fixedPRs) if data.fixedPRs else "[]",
        createdById=current_user.id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"code": 200, "message": "success", "data": {"id": note.id}}


@router.put("/{note_id}")
def update_release_note(
    note_id: int,
    data: AiVoiceReleaseNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(AiVoiceReleaseNote).filter(AiVoiceReleaseNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="记录不存在")
    update_dict = data.model_dump(exclude_unset=True)
    if "affectedModules" in update_dict and update_dict["affectedModules"] is not None:
        update_dict["affectedModules"] = json.dumps(update_dict["affectedModules"])
    if "affectedFeatures" in update_dict and update_dict["affectedFeatures"] is not None:
        update_dict["affectedFeatures"] = json.dumps(update_dict["affectedFeatures"])
    if "fixedPRs" in update_dict and update_dict["fixedPRs"] is not None:
        update_dict["fixedPRs"] = json.dumps(update_dict["fixedPRs"])
    for key, value in update_dict.items():
        setattr(note, key, value)
    db.commit()
    return {"code": 200, "message": "更新成功"}


@router.delete("/{note_id}")
def delete_release_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(AiVoiceReleaseNote).filter(AiVoiceReleaseNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(note)
    db.commit()
    return {"code": 200, "message": "删除成功"}
