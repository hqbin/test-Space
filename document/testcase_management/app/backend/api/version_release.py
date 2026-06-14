from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import (
    VersionRelease, VersionItem, VersionNotifyTarget,
    VersionNotifyGroup, VersionNotifyGroupMember, User
)
from auth import get_current_user, is_super_admin
from datetime import datetime
from typing import Optional

router = APIRouter()


@router.get("")
def get_version_releases(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(VersionRelease)
    if status:
        query = query.filter(VersionRelease.status == status)
    if keyword:
        query = query.filter(
            VersionRelease.version_number.ilike(f"%{keyword}%") |
            VersionRelease.title.ilike(f"%{keyword}%")
        )
    total = query.count()
    items = query.order_by(VersionRelease.created_at.desc()).offset((page - 1) * size).limit(size).all()

    result = []
    for v in items:
        creator = db.query(User).filter(User.id == v.created_by).first() if v.created_by else None
        version_items = db.query(VersionItem).filter(VersionItem.version_id == v.id).order_by(VersionItem.sort_order).all()
        targets = db.query(VersionNotifyTarget).filter(VersionNotifyTarget.version_id == v.id).all()
        result.append({
            "id": v.id,
            "version_number": v.version_number,
            "title": v.title,
            "status": v.status,
            "notify_enabled": v.notify_enabled,
            "created_by": v.created_by,
            "created_by_name": creator.username if creator else None,
            "published_at": v.published_at.isoformat() if v.published_at else None,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "updated_at": v.updated_at.isoformat() if v.updated_at else None,
            "items": [
                {"id": i.id, "version_id": i.version_id, "item_type": i.item_type, "content": i.content, "sort_order": i.sort_order, "created_at": i.created_at.isoformat() if i.created_at else None}
                for i in version_items
            ],
            "targets": [
                {"target_type": t.target_type, "target_id": t.target_id}
                for t in targets
            ]
        })

    return {"code": 200, "message": "success", "data": {"records": result, "total": total, "page": page, "size": size}}


@router.get("/{version_id}")
def get_version_release(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    v = db.query(VersionRelease).filter(VersionRelease.id == version_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="版本不存在")

    creator = db.query(User).filter(User.id == v.created_by).first() if v.created_by else None
    version_items = db.query(VersionItem).filter(VersionItem.version_id == v.id).order_by(VersionItem.sort_order).all()
    targets = db.query(VersionNotifyTarget).filter(VersionNotifyTarget.version_id == v.id).all()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": v.id,
            "version_number": v.version_number,
            "title": v.title,
            "status": v.status,
            "notify_enabled": v.notify_enabled,
            "created_by": v.created_by,
            "created_by_name": creator.username if creator else None,
            "published_at": v.published_at.isoformat() if v.published_at else None,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "updated_at": v.updated_at.isoformat() if v.updated_at else None,
            "items": [
                {"id": i.id, "version_id": i.version_id, "item_type": i.item_type, "content": i.content, "sort_order": i.sort_order, "created_at": i.created_at.isoformat() if i.created_at else None}
                for i in version_items
            ],
            "targets": [
                {"target_type": t.target_type, "target_id": t.target_id}
                for t in targets
            ]
        }
    }


@router.post("")
def create_version_release(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="仅超级管理员可以管理版本发布")

    safe_created_by = current_user.id if current_user.id and current_user.id > 0 else None

    version = VersionRelease(
        version_number=data.get("version_number", ""),
        title=data.get("title", ""),
        status="draft",
        notify_enabled=False,
        created_by=safe_created_by
    )
    db.add(version)
    db.flush()

    items = data.get("items", [])
    for idx, item in enumerate(items):
        vi = VersionItem(
            version_id=version.id,
            item_type=item.get("item_type", "new"),
            content=item.get("content", ""),
            sort_order=item.get("sort_order", idx)
        )
        db.add(vi)

    db.commit()
    db.refresh(version)

    return {"code": 200, "message": "版本创建成功", "data": {"id": version.id}}


@router.put("/{version_id}")
def update_version_release(
    version_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="仅超级管理员可以管理版本发布")

    version = db.query(VersionRelease).filter(VersionRelease.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    if "version_number" in data:
        version.version_number = data["version_number"]
    if "title" in data:
        version.title = data["title"]

    if "items" in data:
        db.query(VersionItem).filter(VersionItem.version_id == version_id).delete()
        for idx, item in enumerate(data["items"]):
            vi = VersionItem(
                version_id=version_id,
                item_type=item.get("item_type", "new"),
                content=item.get("content", ""),
                sort_order=item.get("sort_order", idx)
            )
            db.add(vi)

    db.commit()
    return {"code": 200, "message": "版本更新成功"}


@router.delete("/{version_id}")
def delete_version_release(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="仅超级管理员可以管理版本发布")

    version = db.query(VersionRelease).filter(VersionRelease.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    db.query(VersionItem).filter(VersionItem.version_id == version_id).delete()
    db.query(VersionNotifyTarget).filter(VersionNotifyTarget.version_id == version_id).delete()
    db.delete(version)
    db.commit()

    return {"code": 200, "message": "版本删除成功"}


@router.post("/{version_id}/publish")
def publish_version(
    version_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="仅超级管理员可以管理版本发布")

    version = db.query(VersionRelease).filter(VersionRelease.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    notify_enabled = data.get("notify_enabled", False)
    targets = data.get("targets", [])

    version.status = "published"
    version.notify_enabled = notify_enabled
    version.published_at = datetime.now()

    db.query(VersionNotifyTarget).filter(VersionNotifyTarget.version_id == version_id).delete()
    if notify_enabled and targets:
        for t in targets:
            target = VersionNotifyTarget(
                version_id=version_id,
                target_type=t.get("type", "user"),
                target_id=t.get("id", 0)
            )
            db.add(target)

    db.commit()

    if notify_enabled and targets:
        safe_sender_id = current_user.id if current_user.id and current_user.id > 0 else None
        _send_version_notification(db, version, targets, safe_sender_id)

    return {"code": 200, "message": "版本发布成功"}


@router.post("/{version_id}/unpublish")
def unpublish_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="仅超级管理员可以管理版本发布")

    version = db.query(VersionRelease).filter(VersionRelease.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    version.status = "draft"
    version.published_at = None
    db.commit()

    return {"code": 200, "message": "版本已取消发布"}


def _send_version_notification(db: Session, version: VersionRelease, targets: list, sender_id: int):
    from services.notification_service import NotificationService

    user_ids = set()
    for t in targets:
        target_type = t.get("type", "user")
        target_id = t.get("id", 0)
        if target_type == "user":
            user_ids.add(target_id)
        elif target_type == "group":
            members = db.query(VersionNotifyGroupMember).filter(
                VersionNotifyGroupMember.group_id == target_id
            ).all()
            for m in members:
                user_ids.add(m.user_id)

    if not user_ids:
        return

    items = db.query(VersionItem).filter(VersionItem.version_id == version.id).order_by(VersionItem.sort_order).all()
    type_labels = {"new": "新增", "fix": "修复", "improve": "优化", "delete": "删除", "other": "其他"}
    content_lines = [f"版本 {version.version_number} - {version.title}"]
    for item in items:
        label = type_labels.get(item.item_type, item.item_type)
        content_lines.append(f"[{label}] {item.content}")

    title = f"新版本发布：{version.version_number}"
    content = "\n".join(content_lines)

    service = NotificationService(db)
    service.create_notification(
        notification_type="system",
        event_type="version_release",
        title=title,
        content=content,
        related_id=version.id,
        related_type="version_release",
        sender_id=sender_id,
        recipient_user_ids=list(user_ids)
    )
