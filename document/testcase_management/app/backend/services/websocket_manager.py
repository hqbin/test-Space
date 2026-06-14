"""
WebSocket连接管理器
管理所有在线用户的WebSocket连接，支持心跳检测和消息推送
"""
import json
import asyncio
import logging
from typing import Dict, Optional, List, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket连接管理器（单例）"""

    def __init__(self):
        # user_id -> WebSocket
        self._connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """注册用户连接，如果已有旧连接则关闭"""
        old = self._connections.get(user_id)
        if old:
            try:
                await old.close(code=4001, reason="new_connection")
            except Exception:
                pass
        self._connections[user_id] = websocket
        logger.info(f"WebSocket连接: user_id={user_id}, 在线人数={len(self._connections)}")

    def disconnect(self, user_id: int):
        """移除用户连接"""
        self._connections.pop(user_id, None)
        logger.info(f"WebSocket断开: user_id={user_id}, 在线人数={len(self._connections)}")

    async def send_to_user(self, user_id: int, message: Dict[str, Any]) -> bool:
        """推送消息给指定用户，返回是否成功"""
        ws = self._connections.get(user_id)
        if not ws:
            return False
        try:
            await ws.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"推送失败 user_id={user_id}: {e}")
            self.disconnect(user_id)
            return False

    async def send_to_users(self, user_ids: List[int], message: Dict[str, Any]):
        """批量推送消息"""
        tasks = [self.send_to_user(uid, message) for uid in user_ids]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast(self, message: Dict[str, Any]):
        """广播给所有在线用户"""
        await self.send_to_users(list(self._connections.keys()), message)

    def get_online_user_ids(self) -> List[int]:
        """获取所有在线用户ID"""
        return list(self._connections.keys())

    @property
    def online_count(self) -> int:
        return len(self._connections)


# 全局单例
ws_manager = WebSocketManager()
