"""
系统通知服务
用于触发各种系统级别的通知
"""
from sqlalchemy.orm import Session
from models import User, Notification, NotificationRecipient, NotificationRule
from datetime import datetime
from typing import List, Optional


class SystemNotificationService:
    """系统通知服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def send_system_notification(
        self,
        event_type: str,
        title: str,
        content: str,
        recipient_user_ids: Optional[List[int]] = None,
        related_id: Optional[int] = None,
        related_type: Optional[str] = None
    ):
        """
        发送系统通知
        
        参数:
        - event_type: 事件类型（maintenance/feature_release/password_expiry等）
        - title: 通知标题
        - content: 通知内容
        - recipient_user_ids: 接收人用户ID列表（None表示发送给所有用户）
        - related_id: 关联对象ID
        - related_type: 关联对象类型
        """
        # 检查是否有启用的通知规则
        rule = self.db.query(NotificationRule).filter(
            NotificationRule.notification_type == 'system',
            NotificationRule.event_type == event_type,
            NotificationRule.is_active == True
        ).first()
        
        if not rule:
            # 没有启用的规则，不发送通知
            return None
        
        # 创建通知记录
        notification = Notification(
            title=title,
            content=content,
            notification_type='system',
            event_type=event_type,
            related_id=related_id,
            related_type=related_type,
            is_system=True,
            created_at=datetime.now()
        )
        self.db.add(notification)
        self.db.flush()
        
        # 确定接收人
        if recipient_user_ids is None:
            # 发送给所有用户：只查 id，避免加载全部 User 对象到内存
            recipient_user_ids = [
                row[0] for row in self.db.query(User.id).all()
            ]
        
        # 创建接收人记录
        for user_id in recipient_user_ids:
            recipient = NotificationRecipient(
                notification_id=notification.id,
                user_id=user_id,
                is_read=False,
                created_at=datetime.now()
            )
            self.db.add(recipient)
        
        self.db.commit()
        return notification.id
    
    def send_maintenance_notification(self, start_time: str, end_time: str, reason: str = "系统维护升级"):
        """发送系统维护通知"""
        title = "系统维护通知"
        content = f"系统将于 {start_time} 至 {end_time} 进行维护，期间无法访问。维护原因：{reason}。请提前保存工作，感谢您的理解与支持。"
        return self.send_system_notification(
            event_type='maintenance',
            title=title,
            content=content
        )
    
    def send_feature_release_notification(self, feature_name: str, description: str):
        """发送新功能上线通知"""
        title = f"新功能上线：{feature_name}"
        content = f"{description}\n欢迎体验新功能！"
        return self.send_system_notification(
            event_type='feature_release',
            title=title,
            content=content
        )
    
    def send_password_expiry_notification(self, user_ids: List[int], days_remaining: int):
        """发送密码即将过期通知"""
        title = "密码即将过期提醒"
        content = f"您的密码将在 {days_remaining} 天后过期，请及时修改密码以确保账号安全。"
        return self.send_system_notification(
            event_type='password_expiry',
            title=title,
            content=content,
            recipient_user_ids=user_ids
        )
    
    def send_permission_changed_notification(self, user_ids: List[int], permission_name: str, action: str):
        """发送权限变更通知"""
        title = "权限变更通知"
        action_text = "新增" if action == "add" else "移除"
        content = f"您的账号权限已更新，{action_text}'{permission_name}'权限。"
        return self.send_system_notification(
            event_type='permission_changed',
            title=title,
            content=content,
            recipient_user_ids=user_ids
        )
    
    def send_backup_completed_notification(self, backup_time: str, status: str = "成功"):
        """发送数据备份完成通知（仅发送给管理员）"""
        # 获取管理员用户
        admin_users = self.db.query(User).filter(
            User.username == 'admin'
        ).all()
        admin_ids = [user.id for user in admin_users]
        
        title = "数据备份完成"
        content = f"系统数据备份已完成，备份时间：{backup_time}，状态：{status}。"
        return self.send_system_notification(
            event_type='backup_completed',
            title=title,
            content=content,
            recipient_user_ids=admin_ids
        )
    
    def send_version_update_notification(self, version: str, changelog: str):
        """发送版本更新通知"""
        title = f"系统已升级至 {version}"
        content = f"更新内容：\n{changelog}\n\n请查看更新日志了解详情。"
        return self.send_system_notification(
            event_type='version_update',
            title=title,
            content=content
        )
    
    def send_daily_reminder_notification(self, user_ids: List[int], tasks: List[dict]):
        """发送每日任务提醒"""
        title = "每日任务提醒"
        task_list = "\n".join([f"- {task['name']}" for task in tasks])
        content = f"今日待办：\n{task_list}\n\n加油！"
        return self.send_system_notification(
            event_type='daily_reminder',
            title=title,
            content=content,
            recipient_user_ids=user_ids
        )
