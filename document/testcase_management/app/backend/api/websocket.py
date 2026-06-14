"""
WebSocket通知端点
支持JWT认证、心跳检测、实时通知推送
"""
import json
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from database import get_db
from config import settings
from models import User
from services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter()

HEARTBEAT_INTERVAL = 30  # 秒
HEARTBEAT_TIMEOUT = 10   # 心跳响应超时


def _authenticate_token(token: str, db: Session) -> Optional[User]:
    """验证JWT token并返回用户"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None

        # 支持super用户
        if username == 'super':
            class SuperUser:
                def __init__(self):
                    self.id = -1
                    self.username = 'super'
                    self.status = 1
            return SuperUser()

        user = db.query(User).filter(User.username == username).first()
        return user if user and user.status == 1 else None
    except JWTError:
        return None


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket通知端点
    连接: ws://host/ws/notifications?token=xxx
    
    客户端消息格式:
      {"type": "ping"}              -> 心跳
      {"type": "mark_read", "id": 1} -> 标记已读（预留）
    
    服务端推送格式:
      {"type": "pong"}                          -> 心跳响应
      {"type": "notification", "data": {...}}   -> 新通知
      {"type": "unread_count", "count": 5}      -> 未读数更新
    """
    # 认证
    db = next(get_db())
    try:
        user = _authenticate_token(token, db)
        if not user:
            await websocket.close(code=4003, reason="unauthorized")
            return
    finally:
        db.close()

    await websocket.accept()
    await ws_manager.connect(websocket, user.id)

    try:
        while True:
            # 等待客户端消息（心跳或指令）
            try:
                raw = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=HEARTBEAT_INTERVAL + HEARTBEAT_TIMEOUT
                )
                msg = json.loads(raw)
                msg_type = msg.get("type", "")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

            except asyncio.TimeoutError:
                # 超时未收到消息，发送ping检测
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
            except json.JSONDecodeError:
                continue

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WebSocket异常 user_id={user.id}: {e}")
    finally:
        ws_manager.disconnect(user.id)
