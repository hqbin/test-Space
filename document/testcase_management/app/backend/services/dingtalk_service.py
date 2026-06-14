"""
钉钉消息推送服务
负责根据通知规则将消息推送到对应的钉钉机器人
"""
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests as http_requests
import logging
from sqlalchemy.orm import Session
from models import DingtalkBot, NotificationRule, Notification, Team
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class DingtalkService:
    """钉钉推送服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _generate_sign(self, secret: str, timestamp: str) -> str:
        """生成加签签名"""
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        return urllib.parse.quote_plus(base64.b64encode(hmac_code))
    
    def _build_webhook_url(self, bot: DingtalkBot) -> str:
        """构建带签名的Webhook URL"""
        url = bot.webhook_url
        if bot.security_type == "sign":
            timestamp = str(round(time.time() * 1000))
            sign = self._generate_sign(bot.security_value, timestamp)
            url = f"{url}&timestamp={timestamp}&sign={sign}"
        return url
    
    def _send_markdown(self, bot: DingtalkBot, title: str, content: str, at_mobiles: List[str] = None) -> Dict:
        """发送Markdown消息到钉钉"""
        url = self._build_webhook_url(bot)
        
        # 关键词模式：确保标题包含关键词（标题不在消息卡片内显示，只用于推送通知摘要）
        if bot.security_type == "keyword":
            if bot.security_value not in content and bot.security_value not in title:
                title = f"{title} {bot.security_value}"
        
        # 在内容末尾添加@提醒（Markdown格式需要在text中包含@手机号）
        if at_mobiles:
            at_text = " ".join([f"@{mobile}" for mobile in at_mobiles])
            content = f"{content}\n\n{at_text}"
        
        payload = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": content},
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": False
            }
        }
        
        try:
            resp = http_requests.post(url, json=payload, timeout=5)
            result = resp.json()
            if result.get("errcode") != 0:
                return {"success": False, "error": result.get("errmsg", "未知错误")}
            return {"success": True}
        except http_requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时（5秒）"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def push_notification(
        self,
        notification: Notification,
        rule: NotificationRule,
        project_id: Optional[int] = None,
        team_id: Optional[int] = None,
        at_mobiles: Optional[List[str]] = None
    ) -> None:
        """
        根据通知规则推送到钉钉
        
        Args:
            notification: 通知对象
            rule: 匹配的通知规则
            project_id: 项目ID（用于兼容旧逻辑）
            team_id: 项目组ID（优先使用）
            at_mobiles: 需要@的手机号列表
        """
        try:
            # 检查规则的通知方式是否包含钉钉
            notification_method = rule.notification_method or 'internal'
            if notification_method not in ('dingtalk', 'both'):
                return
            
            # 查找匹配的钉钉机器人（优先使用 team_id）
            bots = self._find_matching_bots(notification.notification_type, project_id, team_id)
            
            if not bots:
                logger.info(f"通知 #{notification.id} 没有匹配的钉钉机器人")
                return
            
            # 构建Markdown消息
            title, content = self._build_message(notification)
            
            # 推送到每个匹配的机器人
            for bot in bots:
                result = self._send_markdown(bot, title, content, at_mobiles=at_mobiles)
                if result["success"]:
                    logger.info(f"钉钉推送成功: 通知#{notification.id} -> 机器人'{bot.name}'")
                    self._update_dingtalk_status(notification.id, "sent")
                else:
                    logger.error(f"钉钉推送失败: 通知#{notification.id} -> 机器人'{bot.name}': {result['error']}")
                    self._update_dingtalk_status(notification.id, "failed", result["error"])
                    
        except Exception as e:
            logger.error(f"钉钉推送异常: 通知#{notification.id}: {e}")
            self._update_dingtalk_status(notification.id, "failed", str(e))
    
    def _find_matching_bots(self, notification_type: str, project_id: Optional[int] = None, team_id: Optional[int] = None) -> List[DingtalkBot]:
        """查找匹配的钉钉机器人"""
        query = self.db.query(DingtalkBot).filter(DingtalkBot.is_active == True)
        
        # 优先使用 team_id，其次从 project_id 查找 team_id
        target_team_id = team_id
        if not target_team_id and project_id:
            from models import TeamProject
            tp = self.db.query(TeamProject).filter(TeamProject.project_id == project_id).first()
            if tp:
                target_team_id = tp.team_id
        
        if target_team_id:
            # 通过项目组ID查找机器人
            query = query.filter(DingtalkBot.team_id == target_team_id)
        elif project_id:
            # 兼容旧逻辑：如果没有 team_id，降级为通过项目ID查找（可能找到多个项目组的机器人）
            from models import TeamProject
            team_ids = [tp.team_id for tp in 
                       self.db.query(TeamProject).filter(TeamProject.project_id == project_id).all()]
            if team_ids:
                query = query.filter(DingtalkBot.team_id.in_(team_ids))
            else:
                return []
        
        bots = query.all()
        
        # 过滤通知类型匹配的机器人
        matched = []
        for bot in bots:
            try:
                types = json.loads(bot.notification_types) if bot.notification_types else []
                if not types or notification_type in types:
                    matched.append(bot)
            except:
                matched.append(bot)
        
        return matched
    
    def _build_message(self, notification: Notification) -> tuple:
        """构建钉钉Markdown消息"""
        type_labels = {
            'testcase': '测试用例', 'testplan': '测试计划',
            'execution': '测试执行', 'report': '测试报告', 'system': '系统'
        }
        type_label = type_labels.get(notification.notification_type, notification.notification_type)
        
        title = f"【{type_label}】{notification.title}"
        
        # 钉钉 Markdown 换行需要两个换行符或行尾两个空格
        # 将模板渲染后的 \n 转换为钉钉 Markdown 的换行
        body = notification.content or ''
        # 先处理连续换行（段落间距）
        body = body.replace('\r\n', '\n')
        # 每行末尾加两个空格实现 Markdown 换行
        lines = body.split('\n')
        body = '  \n'.join(lines)
        
        content = f"### {notification.title}  \n\n{body}"
        
        # 添加详情跳转链接
        try:
            from utils.notification_helper import _build_detail_link
            link = _build_detail_link(
                notification.notification_type,
                notification.related_id,
                notification.related_type,
                event_type=notification.event_type
            )
            if link:
                content += f"  \n\n---  \n[👉 点击查看详情]({link})"
        except Exception as e:
            logger.warning(f"构建详情链接失败: {e}")
        
        return title, content
    
    def _update_dingtalk_status(self, notification_id: int, status: str, error: str = None):
        """更新通知的钉钉推送状态"""
        try:
            notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
            if notification:
                notification.dingtalk_status = status
                if error:
                    notification.dingtalk_error = error[:500]
                self.db.commit()
        except Exception as e:
            logger.error(f"更新钉钉状态失败: {e}")
