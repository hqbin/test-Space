from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import VersionNotifyGroup, VersionNotifyGroupMember, User
from auth import get_current_user, is_super_admin
from typing import Optional

router = APIRouter()


@router.get("")
def get_notify_groups(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(VersionNotifyGroup)
    if keyword:
        query = query.filter(VersionNotifyGroup.name.ilike(f"%{keyword}%"))
    total = query.count()
    groups = query.order_by(VersionNotifyGroup.created_at.desc()).offset((page - 1) * size).limit(size).all()

    if not groups:
        return {"code": 200, "message": "success", "data": {"records": [], "total": total, "page": page, "size": size}}

    # 批量统计成员数，替代逐条 count 查询
    group_ids = [g.id for g in groups]
    count_rows = db.query(
        VersionNotifyGroupMember.group_id,
        func.count(VersionNotifyGroupMember.id).label("cnt")
    ).filter(
        VersionNotifyGroupMember.group_id.in_(group_ids)
    ).group_by(VersionNotifyGroupMember.group_id).all()
    count_map = {row.group_id: row.cnt for row in count_rows}

    result = []
    for g in groups:
        result.append({
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "created_by": g.created_by,
            "member_count": count_map.get(g.id, 0),
            "created_at": g.created_at.isoformat() if g.created_at else None,
            "updated_at": g.updated_at.isoformat() if g.updated_at else None,
        })

    return {"code": 200, "message": "success", "data": {"records": result, "total": total, "page": page, "size": size}}


@router.get("/all")
def get_all_notify_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    groups = db.query(VersionNotifyGroup).order_by(VersionNotifyGroup.name).all()
    if not groups:
        return {"code": 200, "message": "success", "data": []}

    group_ids = [g.id for g in groups]

    # 一次 JOIN 拉取所有组的成员及用户信息，消除 N+1
    rows = db.query(
        VersionNotifyGroupMember,
        User
    ).join(
        User, User.id == VersionNotifyGroupMember.user_id
    ).filter(
        VersionNotifyGroupMember.group_id.in_(group_ids)
    ).all()

    # 按 group_id 分组
    members_by_group: dict = {g.id: [] for g in groups}
    for member, user in rows:
        members_by_group[member.group_id].append({
            "id": member.id,
            "user_id": member.user_id,
            "username": user.username,
            "full_name": user.full_name,
            "created_at": member.created_at.isoformat() if member.created_at else None
        })

    result = []
    for g in groups:
        member_details = members_by_group.get(g.id, [])
        result.append({
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "member_count": len(member_details),
            "members": member_details
        })

    return {"code": 200, "message": "success", "data": result}


@router.get("/{group_id}")
def get_notify_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    group = db.query(VersionNotifyGroup).filter(VersionNotifyGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="用户组不存在")

    # 一次 JOIN 查询替代逐条 user 查询
    rows = db.query(
        VersionNotifyGroupMember,
        User
    ).join(
        User, User.id == VersionNotifyGroupMember.user_id
    ).filter(
        VersionNotifyGroupMember.group_id == group_id
    ).all()

    member_details = []
    for m, user in rows:
        member_details.append({
            "id": m.id,
            "user_id": m.user_id,
            "username": user.username,
            "full_name": user.full_name,
            "created_at": m.created_at.isoformat() if m.created_at else None
        })

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "created_by": group.created_by,
            "members": member_details,
            "created_at": group.created_at.isoformat() if group.created_at else None,
            "updated_at": group.updated_at.isoformat() if group.updated_at else None,
        }
    }


@router.post("")
def create_notify_group(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="仅超级管理员可以管理通知用户组")

    safe_created_by = current_user.id if current_user.id and current_user.id > 0 else None

    group = VersionNotifyGroup(
        name=data.get("name", ""),
        description=data.get("description"),
        created_by=safe_created_by
    )
    db.add(group)
    db.flush()

    user_ids = data.get("user_ids", [])
    for uid in user_ids:
        member = VersionNotifyGroupMember(group_id=group.id, user_id=uid)
        db.add(member)

    db.commit()
    db.refresh(group)

    return {"code": 200, "message": "用户组创建成功", "data": {"id": group.id}}


@router.put("/{group_id}")
def update_notify_group(
    group_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="仅超级管理员可以管理通知用户组")

    group = db.query(VersionNotifyGroup).filter(VersionNotifyGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="用户组不存在")

    if "name" in data:
        group.name = data["name"]
    if "description" in data:
        group.description = data["description"]

    if "user_ids" in data:
        db.query(VersionNotifyGroupMember).filter(VersionNotifyGroupMember.group_id == group_id).delete()
        for uid in data["user_ids"]:
            member = VersionNotifyGroupMember(group_id=group_id, user_id=uid)
            db.add(member)

    db.commit()
    return {"code": 200, "message": "用户组更新成功"}


@router.delete("/{group_id}")
def delete_notify_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="仅超级管理员可以管理通知用户组")

    group = db.query(VersionNotifyGroup).filter(VersionNotifyGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="用户组不存在")

    db.query(VersionNotifyGroupMember).filter(VersionNotifyGroupMember.group_id == group_id).delete()
    db.delete(group)
    db.commit()

    return {"code": 200, "message": "用户组删除成功"}


@router.post("/{group_id}/members")
def add_group_members(
    group_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="仅超级管理员可以管理通知用户组")

    group = db.query(VersionNotifyGroup).filter(VersionNotifyGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="用户组不存在")

    user_ids = data.get("user_ids", [])
    added = 0
    for uid in user_ids:
        exists = db.query(VersionNotifyGroupMember).filter(
            VersionNotifyGroupMember.group_id == group_id,
            VersionNotifyGroupMember.user_id == uid
        ).first()
        if not exists:
            member = VersionNotifyGroupMember(group_id=group_id, user_id=uid)
            db.add(member)
            added += 1

    db.commit()
    return {"code": 200, "message": f"成功添加 {added} 个成员"}


@router.delete("/{group_id}/members/{user_id}")
def remove_group_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="仅超级管理员可以管理通知用户组")

    member = db.query(VersionNotifyGroupMember).filter(
        VersionNotifyGroupMember.group_id == group_id,
        VersionNotifyGroupMember.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")

    db.delete(member)
    db.commit()
    return {"code": 200, "message": "成员移除成功"}


@router.post("/members/move")
def move_members(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="仅超级管理员可以管理通知用户组")

    user_ids = data.get("user_ids", [])
    target_group_id = data.get("target_group_id")

    target_group = db.query(VersionNotifyGroup).filter(VersionNotifyGroup.id == target_group_id).first()
    if not target_group:
        raise HTTPException(status_code=404, detail="目标用户组不存在")

    moved = 0
    for uid in user_ids:
        db.query(VersionNotifyGroupMember).filter(
            VersionNotifyGroupMember.user_id == uid
        ).delete()
        member = VersionNotifyGroupMember(group_id=target_group_id, user_id=uid)
        db.add(member)
        moved += 1

    db.commit()
    return {"code": 200, "message": f"成功移动 {moved} 个用户"}
