from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from database import get_db
from models import User, SystemLog
from auth import get_current_user
from typing import Optional
from datetime import datetime

router = APIRouter()

@router.get("/logs")
def get_system_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    username: Optional[str] = None,
    module: Optional[str] = None,
    modules: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取系统日志列表（分页、筛选）
    """
    try:
        # 构建查询
        query = db.query(SystemLog)
        
        # 用户名筛选
        if username:
            query = query.filter(SystemLog.username.like(f'%{username}%'))
        
        # 模块筛选（支持单选和多选）
        if modules:
            module_list = [m.strip() for m in modules.split(',') if m.strip()]
            if module_list:
                query = query.filter(SystemLog.module.in_(module_list))
        elif module:
            query = query.filter(SystemLog.module == module)
        
        # 操作筛选
        if action:
            query = query.filter(SystemLog.action == action)
        
        # 日期范围筛选
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(SystemLog.created_at >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d 23:59:59')
                query = query.filter(SystemLog.created_at <= end_dt)
            except ValueError:
                pass
        
        # 关键词搜索（搜索描述、请求路径）
        if keyword:
            query = query.filter(
                or_(
                    SystemLog.description.like(f'%{keyword}%'),
                    SystemLog.request_path.like(f'%{keyword}%')
                )
            )
        
        # 总数
        total = query.count()
        
        # 分页查询（按时间倒序）
        logs = query.order_by(desc(SystemLog.created_at), desc(SystemLog.id)).offset((page - 1) * size).limit(size).all()
        
        # 转换为字典
        records = []
        for log in logs:
            records.append({
                'id': log.id,
                'user_id': log.user_id,
                'username': log.username,
                'module': log.module,
                'action': log.action,
                'description': log.description,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'request_method': log.request_method,
                'request_path': log.request_path,
                'request_params': log.request_params,
                'response_status': log.response_status,
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else None
            })
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "records": records,
                "total": total,
                "page": page,
                "size": size
            }
        }
    except Exception as e:
        print(f"[ERROR] 获取系统日志失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取系统日志失败: {str(e)}")

@router.get("/logs/modules")
def get_log_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有日志模块列表（用于筛选）
    """
    try:
        modules = db.query(SystemLog.module).distinct().all()
        module_list = [m[0] for m in modules if m[0]]
        return {
            "code": 200,
            "message": "success",
            "data": module_list
        }
    except Exception as e:
        print(f"[ERROR] 获取模块列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模块列表失败: {str(e)}")

@router.get("/logs/actions")
def get_log_actions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有操作类型列表（用于筛选）
    """
    try:
        actions = db.query(SystemLog.action).distinct().all()
        action_list = [a[0] for a in actions if a[0]]
        return {
            "code": 200,
            "message": "success",
            "data": action_list
        }
    except Exception as e:
        print(f"[ERROR] 获取操作类型列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取操作类型列表失败: {str(e)}")

@router.get("/logs/stats")
def get_log_stats(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取日志统计信息（最近N天）
    """
    try:
        from datetime import timedelta
        from sqlalchemy import func
        
        # 计算起始日期
        start_date = datetime.now() - timedelta(days=days)
        
        # 总操作数
        total_count = db.query(SystemLog).filter(SystemLog.created_at >= start_date).count()
        
        # 按模块统计
        module_stats = db.query(
            SystemLog.module,
            func.count(SystemLog.id).label('count')
        ).filter(
            SystemLog.created_at >= start_date
        ).group_by(SystemLog.module).all()
        
        # 按操作统计
        action_stats = db.query(
            SystemLog.action,
            func.count(SystemLog.id).label('count')
        ).filter(
            SystemLog.created_at >= start_date
        ).group_by(SystemLog.action).all()
        
        # 活跃用户统计
        user_stats = db.query(
            SystemLog.username,
            func.count(SystemLog.id).label('count')
        ).filter(
            SystemLog.created_at >= start_date
        ).group_by(SystemLog.username).order_by(desc('count')).limit(10).all()
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "total_count": total_count,
                "module_stats": [{"module": m[0], "count": m[1]} for m in module_stats],
                "action_stats": [{"action": a[0], "count": a[1]} for a in action_stats],
                "user_stats": [{"username": u[0], "count": u[1]} for u in user_stats]
            }
        }
    except Exception as e:
        print(f"[ERROR] 获取日志统计失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取日志统计失败: {str(e)}")
