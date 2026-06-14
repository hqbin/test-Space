from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import VersionRelease, VersionItem, User
from auth import get_current_user
from typing import Optional

router = APIRouter()


@router.get("")
def get_published_versions(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(VersionRelease).filter(VersionRelease.status == "published")
    total = query.count()
    versions = query.order_by(VersionRelease.published_at.desc()).offset((page - 1) * size).limit(size).all()

    result = []
    for v in versions:
        items = db.query(VersionItem).filter(VersionItem.version_id == v.id).order_by(VersionItem.sort_order).all()
        result.append({
            "id": v.id,
            "version_number": v.version_number,
            "title": v.title,
            "published_at": v.published_at.isoformat() if v.published_at else None,
            "items": [
                {"id": i.id, "item_type": i.item_type, "content": i.content, "sort_order": i.sort_order}
                for i in items
            ]
        })

    return {"code": 200, "message": "success", "data": {"records": result, "total": total}}
