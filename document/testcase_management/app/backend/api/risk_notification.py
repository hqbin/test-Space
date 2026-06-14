"""
风险预警通知API
提供手动触发风险预警检查的接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, SystemLog
from auth import get_current_user
from services.risk_notification_service import RiskNotificationService
from datetime import datetime

router = APIRouter()


@router.post("/trigger-risk-alert")
def trigger_risk_alert(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    手动触发风险预警通知（用于测试）
    需要登录认证
    """
    try:
        service = RiskNotificationService(db)
        result = service.check_and_notify()
        
        # 记录到系统日志
        log = SystemLog(
            user_id=current_user.id,
            username=current_user.username,
            module="定时任务",
            action="complete",
            description=f"手动触发风险预警任务完成: {result}",
            created_at=datetime.now()
        )
        db.add(log)
        db.commit()
        
        return {
            "code": 200,
            "message": "success",
            "data": result
        }
    except Exception as e:
        # 记录错误到系统日志
        log = SystemLog(
            user_id=current_user.id,
            username=current_user.username,
            module="定时任务",
            action="error",
            description=f"手动触发风险预警任务失败: {str(e)}",
            created_at=datetime.now()
        )
        db.add(log)
        db.commit()
        
        return {
            "code": 200,
            "message": "success",
            "data": {"error": str(e)}
        }