from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text, Integer
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
from database import get_db
from models import UserBehaviorTracker, User
from auth import get_current_user
import json

PAGE_NAME_MAP = {
    '/dashboard': '工作台',
    '/testcases': '测试用例',
    '/testcases/:testcaseId/detail': '用例详情',
    '/testplans': '测试计划',
    '/testplans/:id': '测试计划详情',
    '/testplans/:id/execution': '测试计划执行',
    '/testplans/:planId/testcases/:testcaseId': '用例执行详情',
    '/testplans/:planId/preview-report': '报告预览',
    '/reports': '测试报告',
    '/reports/review/:id': '报告评审',
    '/zmind': 'Zmind集成',
    '/users': '用户管理',
    '/projects': '用例库管理',
    '/projects/:projectId/modules': '模块管理',
    '/projects/:projectId/modules/:moduleId': '模块详情',
    '/notifications': '通知中心',
    '/analytics': '数据统计',
    '/behavior-tracker': '数据埋点',
    '/system-log': '系统日志',
    '/database': '数据库管理',
    '/permission-management': '权限管理',
    '/organization': '组织管理',
    '/notification-management': '通知管理',
    '/template-management': '模板管理',
    '/profile': '个人中心',
    '/review-plans': '用例评审',
    '/review-plans/:id': '评审计划详情',
    '/review-plans/:id/execution': '评审执行',
    '/review-plans/:planId/testcases/:testcaseId': '用例评审详情',
    '/icons': '图标列表',
    '/aml-patch': 'AML Patch管理',
    '/login': '登录',
    '/': '首页'
}


def get_page_name(page_path: str) -> str:
    """获取页面的翻译名称"""
    if not page_path:
        return '未知页面'
    # 先检查精确匹配
    if page_path in PAGE_NAME_MAP:
        return PAGE_NAME_MAP[page_path]
    # 检查前缀匹配
    for key, name in PAGE_NAME_MAP.items():
        prefix = key.replace('/:id', '').replace('/:testcaseId', '').replace('/:planId', '').replace('/:projectId', '').replace('/:moduleId', '')
        if page_path.startswith(prefix):
            return name
    # 如果是menu.xxx格式的key，返回中文
    if page_path.startswith('menu.'):
        return page_path.replace('menu.', '').replace('.', ' ')
    # 默认返回路径
    return page_path


def check_is_super(user) -> bool:
    """检查用户是否是超级管理员（兼容SuperUser对象）"""
    if hasattr(user, 'username'):
        return user.username in ('admin', 'super')
    return False


router = APIRouter(prefix="/api/behavior-tracker", tags=["行为追踪"])


class TrackerEventCreate(BaseModel):
    behavior_type: str
    page_path: str
    page_name: Optional[str] = None
    action_name: Optional[str] = None
    action_type: Optional[str] = None
    element_id: Optional[str] = None
    element_name: Optional[str] = None
    extra_data: Optional[str] = None


@router.post("/track")
def track_event(
    event: TrackerEventCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tracker = UserBehaviorTracker(
        user_id=current_user.id if hasattr(current_user, 'id') and current_user.id > 0 else None,
        username=current_user.username if hasattr(current_user, 'username') else 'unknown',
        behavior_type=event.behavior_type,
        page_path=event.page_path,
        page_name=event.page_name or get_page_name(event.page_path),
        action_name=event.action_name,
        action_type=event.action_type,
        element_id=event.element_id,
        element_name=event.element_name,
        extra_data=event.extra_data
    )
    db.add(tracker)
    db.commit()
    return {"success": True}


@router.get("/stats/overview")
def get_stats_overview(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    page_path: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not check_is_super(current_user):
        raise HTTPException(status_code=403, detail="只有超级管理员可以查看统计数据")

    base_query = db.query(UserBehaviorTracker).filter(
        UserBehaviorTracker.username.notin_(['super'])
    )

    if date_from:
        try:
            from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            base_query = base_query.filter(UserBehaviorTracker.created_at >= from_dt)
        except:
            pass

    if date_to:
        try:
            to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            to_dt = to_dt + timedelta(days=1)
            base_query = base_query.filter(UserBehaviorTracker.created_at < to_dt)
        except:
            pass

    if user_id:
        base_query = base_query.filter(UserBehaviorTracker.user_id == user_id)

    if page_path:
        base_query = base_query.filter(UserBehaviorTracker.page_path.like(f"%{page_path}%"))

    total_count = base_query.count()
    page_views = base_query.filter(UserBehaviorTracker.behavior_type == "page_view").count()
    clicks = base_query.filter(UserBehaviorTracker.behavior_type == "click").count()
    actions = base_query.filter(UserBehaviorTracker.behavior_type == "action").count()
    unique_users = base_query.with_entities(func.count(func.distinct(UserBehaviorTracker.username))).scalar() or 0

    return {
        "total_count": total_count,
        "page_views": page_views,
        "clicks": clicks,
        "actions": actions,
        "unique_users": unique_users,
        "date_from": date_from or "开始",
        "date_to": date_to or "至今"
    }


@router.get("/stats/by-page")
def get_stats_by_page(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not check_is_super(current_user):
        raise HTTPException(status_code=403, detail="只有超级管理员可以查看统计数据")

    filters = [
        UserBehaviorTracker.username.notin_(['super'])
    ]
    if date_from:
        try:
            from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            filters.append(UserBehaviorTracker.created_at >= from_dt)
        except:
            pass

    if date_to:
        try:
            to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            to_dt = to_dt + timedelta(days=1)
            filters.append(UserBehaviorTracker.created_at < to_dt)
        except:
            pass

    if search:
        filters.append(or_(
            UserBehaviorTracker.page_path.like(f"%{search}%"),
            UserBehaviorTracker.page_name.like(f"%{search}%")
        ))

# 使用ORM查询 - 数据库端聚合
    # PostgreSQL兼容的聚合查询
    query = db.query(
        UserBehaviorTracker.page_path,
        UserBehaviorTracker.page_name,
        func.count(UserBehaviorTracker.id).label('total_count'),
        func.count(func.distinct(UserBehaviorTracker.username)).label('unique_users'),
        func.sum(func.cast(UserBehaviorTracker.behavior_type == 'page_view', Integer)).label('page_views'),
        func.sum(func.cast(UserBehaviorTracker.behavior_type == 'click', Integer)).label('clicks'),
        func.sum(func.cast(UserBehaviorTracker.behavior_type == 'action', Integer)).label('actions')
    )

    if filters:
        query = query.filter(*filters)

    grouped = query.group_by(UserBehaviorTracker.page_path, UserBehaviorTracker.page_name).order_by(func.count(UserBehaviorTracker.id).desc()).all()

    result = []
    for r in grouped:
        result.append({
            "page_path": r.page_path,
            "page_name": r.page_name if r.page_name else get_page_name(r.page_path),
            "total_count": r.total_count,
            "page_views": r.page_views or 0,
            "clicks": r.clicks or 0,
            "actions": r.actions or 0,
            "unique_users": r.unique_users
        })

    result.sort(key=lambda x: x["total_count"], reverse=True)

    total = len(result)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": result[start:end]
    }


@router.get("/stats/by-action")
def get_stats_by_action(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(30),
    search: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not check_is_super(current_user):
        raise HTTPException(status_code=403, detail="只有超级管理员可以查看统计数据")

    filters = [
        UserBehaviorTracker.action_name != None,
        UserBehaviorTracker.action_name != '',
        UserBehaviorTracker.username.notin_(['super'])
    ]

    if date_from:
        try:
            from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            filters.append(UserBehaviorTracker.created_at >= from_dt)
        except:
            pass

    if date_to:
        try:
            to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            to_dt = to_dt + timedelta(days=1)
            filters.append(UserBehaviorTracker.created_at < to_dt)
        except:
            pass

    if search:
        filters.append(UserBehaviorTracker.action_name.like(f"%{search}%"))

    # 使用数据库端聚合查询
    results = db.query(
        UserBehaviorTracker.action_name,
        UserBehaviorTracker.action_type,
        UserBehaviorTracker.page_path,
        func.count(UserBehaviorTracker.id).label('total_count'),
        func.count(func.distinct(UserBehaviorTracker.username)).label('unique_users')
    ).filter(*filters).group_by(
        UserBehaviorTracker.action_name,
        UserBehaviorTracker.action_type,
        UserBehaviorTracker.page_path
    ).order_by(func.count(UserBehaviorTracker.id).desc()).limit(limit).all()

    result = []
    for r in results:
        result.append({
            "action_name": r.action_name,
            "action_type": r.action_type or "unknown",
            "page_path": r.page_path,
            "total_count": r.total_count,
            "unique_users": r.unique_users
        })

    return result


@router.get("/stats/by-user")
def get_stats_by_user(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not check_is_super(current_user):
        raise HTTPException(status_code=403, detail="只有超级管理员可以查看统计数据")

    filters = [
        UserBehaviorTracker.behavior_type == 'page_view',
        UserBehaviorTracker.username.notin_(['super'])
    ]

    if date_from:
        try:
            from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            filters.append(UserBehaviorTracker.created_at >= from_dt)
        except:
            pass

    if date_to:
        try:
            to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            to_dt = to_dt + timedelta(days=1)
            filters.append(UserBehaviorTracker.created_at < to_dt)
        except:
            pass

    if search:
        filters.append(UserBehaviorTracker.username.like(f"%{search}%"))

    # 使用数据库端聚合查询
    results = db.query(
        UserBehaviorTracker.username,
        UserBehaviorTracker.user_id,
        UserBehaviorTracker.page_path,
        UserBehaviorTracker.page_name,
        func.count(UserBehaviorTracker.id).label('visit_count')
    ).filter(*filters).group_by(
        UserBehaviorTracker.username,
        UserBehaviorTracker.user_id,
        UserBehaviorTracker.page_path,
        UserBehaviorTracker.page_name
    ).order_by(UserBehaviorTracker.username, func.count(UserBehaviorTracker.id).desc()).all()

    result = []
    for r in results:
        result.append({
            "username": r.username,
            "user_id": r.user_id,
            "page_path": r.page_path,
            "page_name": r.page_name if r.page_name else get_page_name(r.page_path),
            "visit_count": r.visit_count
        })

    result.sort(key=lambda x: (x["username"], x["visit_count"]), reverse=True)

    total = len(result)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": result[start:end]
    }


@router.get("/stats/by-date")
def get_stats_by_date(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not check_is_super(current_user):
        raise HTTPException(status_code=403, detail="只有超级管理员可以查看统计数据")

    filters = [
        UserBehaviorTracker.username.notin_(['super'])
    ]
    if date_from:
        try:
            from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            filters.append(UserBehaviorTracker.created_at >= from_dt)
        except:
            pass
    else:
        from_dt = datetime.now() - timedelta(days=30)
        filters.append(UserBehaviorTracker.created_at >= from_dt)

    if date_to:
        try:
            to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            to_dt = to_dt + timedelta(days=1)
            filters.append(UserBehaviorTracker.created_at < to_dt)
        except:
            pass

    # 使用ORM查询 - 数据库端聚合
    query = db.query(
        func.date(UserBehaviorTracker.created_at).label('date'),
        func.count(UserBehaviorTracker.id).label('total_count'),
        func.sum(func.cast(UserBehaviorTracker.behavior_type == 'page_view', Integer)).label('page_views'),
        func.sum(func.cast(UserBehaviorTracker.behavior_type == 'click', Integer)).label('clicks'),
        func.sum(func.cast(UserBehaviorTracker.behavior_type == 'action', Integer)).label('actions')
    ).filter(*filters).group_by(
        func.date(UserBehaviorTracker.created_at)
    ).order_by(func.date(UserBehaviorTracker.created_at))

    grouped = query.all()

    result = []
    for r in grouped:
        result.append({
            "date": r.date.strftime("%Y-%m-%d") if r.date else "unknown",
            "total_count": r.total_count,
            "page_views": r.page_views or 0,
            "clicks": r.clicks or 0,
            "actions": r.actions or 0
        })

    return result


@router.post("/cleanup")
def cleanup_old_records(
    days: int = Query(30, ge=7, le=365),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清理指定天数前的行为记录（默认30天）"""
    if not check_is_super(current_user):
        raise HTTPException(status_code=403, detail="只有超级管理员可以清理数据")

    try:
        cutoff = datetime.now() - timedelta(days=days)
        deleted = db.query(UserBehaviorTracker).filter(
            UserBehaviorTracker.created_at < cutoff
        ).delete()
        db.commit()
        return {
            "success": True,
            "message": f"已清理 {deleted} 条 {days} 天前的行为记录"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")


@router.get("/records")
def get_records(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    page_path: Optional[str] = Query(None),
    behavior_type: Optional[str] = Query(None),
    action_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not check_is_super(current_user):
        raise HTTPException(status_code=403, detail="只有超级管理员可以查看详细记录")

    query = db.query(UserBehaviorTracker).filter(
        UserBehaviorTracker.username.notin_(['super'])
    )

    if date_from:
        try:
            from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(UserBehaviorTracker.created_at >= from_dt)
        except:
            pass

    if date_to:
        try:
            to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            to_dt = to_dt + timedelta(days=1)
            query = query.filter(UserBehaviorTracker.created_at < to_dt)
        except:
            pass

    if username:
        query = query.filter(UserBehaviorTracker.username.like(f"%{username}%"))

    if page_path:
        query = query.filter(or_(
            UserBehaviorTracker.page_path.like(f"%{page_path}%"),
            UserBehaviorTracker.page_name.like(f"%{page_path}%")
        ))

    if behavior_type:
        query = query.filter(UserBehaviorTracker.behavior_type == behavior_type)

    if action_name:
        query = query.filter(UserBehaviorTracker.action_name.like(f"%{action_name}%"))

    total = query.count()
    records = query.order_by(UserBehaviorTracker.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for r in records:
        items.append({
            "id": r.id,
            "username": r.username,
            "behavior_type": r.behavior_type,
            "page_path": r.page_path,
            "page_name": r.page_name if r.page_name else get_page_name(r.page_path),
            "action_name": r.action_name,
            "action_type": r.action_type,
            "element_name": r.element_name,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "ip_address": r.ip_address
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }