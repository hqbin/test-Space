"""
通知服务 - 核心业务逻辑
负责通知的创建、发送、规则匹配等
"""
from sqlalchemy.orm import Session
from models import (
    Notification, NotificationRecipient, NotificationRule,
    NotificationTemplate, User, Role, UserRole, UserProject,
    TestPlan, TestPlanExecutor, UserNotificationPreference
)
from utils.data_permission import is_super_admin
from typing import List, Dict, Any, Optional
import json
from datetime import datetime


class NotificationService:
    """通知服务类"""
    
    # 通知类型常量
    TYPE_TESTCASE = 'testcase'
    TYPE_TESTPLAN = 'testplan'
    TYPE_EXECUTION = 'execution'
    TYPE_REPORT = 'report'
    
    # 事件类型常量
    EVENT_CREATED = 'created'
    EVENT_UPDATED = 'updated'
    EVENT_DELETED = 'deleted'
    EVENT_STATUS_CHANGED = 'status_changed'
    EVENT_COMPLETED = 'completed'
    EVENT_STARTED = 'started'
    EVENT_CANCELLED = 'cancelled'
    EVENT_RESULT_UPDATED = 'result_updated'
    EVENT_GENERATED = 'generated'
    EVENT_ALERT = 'alert'
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_notification(
        self,
        notification_type: str,
        event_type: str,
        title: str,
        content: str,
        related_id: Optional[int] = None,
        related_type: Optional[str] = None,
        sender_id: Optional[int] = None,
        recipient_user_ids: Optional[List[int]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Notification]:
        """
        创建通知
        
        Args:
            notification_type: 通知类型
            event_type: 事件类型
            title: 通知标题
            content: 通知内容
            related_id: 关联对象ID
            related_type: 关联对象类型
            sender_id: 发送人ID（系统通知为None）
            recipient_user_ids: 指定接收人ID列表（如果为None则根据规则自动匹配）
            context: 上下文数据，用于规则匹配
        
        Returns:
            创建的通知对象，如果没有接收人则返回None
        """
        # 确定接收人
        if recipient_user_ids is None:
            # 根据规则自动匹配接收人
            recipient_user_ids = self._match_recipients(
                notification_type, event_type, context or {}
            )
        
        # 如果没有接收人（没有启用的规则或没有符合条件的接收人），不创建通知
        if not recipient_user_ids:
            return None
        
        # 尝试通过匹配规则的模板渲染标题和内容（无论是否有接收人都要渲染模板）
        context_for_render = context or {}
        rendered_title, rendered_content = self._render_template(
            notification_type, event_type, title, content, context_for_render
        )

        # 兜底：sender_id 必须指向真实存在的 users.id，否则违反外键约束。
        # 例如 super 是虚拟超管账号（id=-1），不在 users 表中，需当作系统通知处理。
        safe_sender_id = sender_id
        if safe_sender_id is not None:
            from models import User as _User
            exists = self.db.query(_User.id).filter(_User.id == safe_sender_id).first()
            if not exists:
                safe_sender_id = None

        # 创建通知记录
        notification = Notification(
            title=rendered_title,
            content=rendered_content,
            notification_type=notification_type,
            event_type=event_type,
            related_id=related_id,
            related_type=related_type,
            sender_id=safe_sender_id,
            is_system=safe_sender_id is None
        )
        self.db.add(notification)
        self.db.flush()
        
        # 创建接收人记录
        for user_id in recipient_user_ids:
            recipient = NotificationRecipient(
                notification_id=notification.id,
                user_id=user_id,
                is_read=False
            )
            self.db.add(recipient)
        
        self.db.commit()
        
        # 钉钉推送（异步方式，失败不影响主流程）
        try:
            self._push_to_dingtalk(notification, context or {}, recipient_user_ids)
        except Exception as e:
            print(f"钉钉推送异常（不影响主流程）: {e}")
        
        # WebSocket实时推送（异步方式，失败不影响主流程）
        try:
            self._push_to_websocket(notification, recipient_user_ids)
        except Exception as e:
            print(f"WebSocket推送异常（不影响主流程）: {e}")
        
        return notification
    
    def _match_recipients(
        self,
        notification_type: str,
        event_type: str,
        context: Dict[str, Any]
    ) -> List[int]:
        """
        根据规则匹配接收人
        
        Args:
            notification_type: 通知类型
            event_type: 事件类型
            context: 上下文数据
        
        Returns:
            接收人用户ID列表
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 查找匹配的规则
        rules = self.db.query(NotificationRule).filter(
            NotificationRule.notification_type == notification_type,
            NotificationRule.event_type == event_type,
            NotificationRule.is_active == True
        ).all()
        
        logger.info(f"[_match_recipients] type={notification_type}, event={event_type}, 找到 {len(rules)} 条规则, context keys={list(context.keys())}")
        
        # 如果没有启用的通知规则，不发送通知
        if not rules:
            logger.info(f"[_match_recipients] 没有匹配的活跃规则，跳过")
            return []
        
        recipient_ids = set()
        directly_specified_user_ids = set()  # 规则中直接指定的用户，跳过项目权限过滤
        
        for rule in rules:
            # 检查触发条件
            if not self._check_trigger_condition(rule, context):
                logger.info(f"[_match_recipients] 规则 #{rule.id} '{rule.name}' 触发条件不满足, trigger_condition={rule.trigger_condition}, context project_id={context.get('project_id')}")
                continue
            
            logger.info(f"[_match_recipients] 规则 #{rule.id} '{rule.name}' 触发条件满足, recipient_type={rule.recipient_type}")
            
            # 根据接收人类型获取用户ID
            if rule.recipient_type == 'role':
                # 按角色获取用户
                role_ids = json.loads(rule.recipient_roles) if rule.recipient_roles else []
                for role_id in role_ids:
                    user_ids = self._get_users_by_role(role_id)
                    recipient_ids.update(user_ids)
            
            elif rule.recipient_type == 'user':
                # 指定用户——直接指定的用户不需要项目权限过滤
                user_ids = json.loads(rule.recipient_users) if rule.recipient_users else []
                recipient_ids.update(user_ids)
                directly_specified_user_ids.update(user_ids)
            
            elif rule.recipient_type == 'mixed':
                # 混合模式
                if rule.recipient_roles:
                    role_ids = json.loads(rule.recipient_roles)
                    for role_id in role_ids:
                        user_ids = self._get_users_by_role(role_id)
                        recipient_ids.update(user_ids)
                
                if rule.recipient_users:
                    user_ids = json.loads(rule.recipient_users)
                    recipient_ids.update(user_ids)
                    directly_specified_user_ids.update(user_ids)
        
        # 应用项目权限过滤（直接指定的用户跳过过滤）
        logger.info(f"[_match_recipients] 规则匹配后候选接收人: {list(recipient_ids)}, 直接指定用户: {list(directly_specified_user_ids)}")
        need_filter_ids = [uid for uid in recipient_ids if uid not in directly_specified_user_ids]
        skip_filter_ids = [uid for uid in recipient_ids if uid in directly_specified_user_ids]
        
        filtered_ids = self._filter_by_project_permission(
            need_filter_ids, 
            notification_type, 
            context
        )
        # 合并：直接指定的用户 + 过滤后的角色用户
        recipient_ids = list(set(skip_filter_ids + filtered_ids))
        logger.info(f"[_match_recipients] 项目权限过滤后: {recipient_ids}")
        
        # 应用用户偏好过滤
        recipient_ids = self._filter_by_user_preference(
            recipient_ids,
            notification_type
        )
        logger.info(f"[_match_recipients] 最终接收人: {list(recipient_ids)}")
        
        return recipient_ids
    
    def _check_trigger_condition(
        self,
        rule: NotificationRule,
        context: Dict[str, Any]
    ) -> bool:
        """
        检查触发条件是否满足
        
        Args:
            rule: 通知规则
            context: 上下文数据
        
        Returns:
            是否满足条件
        """
        if not rule.trigger_condition:
            return True
        
        try:
            conditions = json.loads(rule.trigger_condition)
            
            # 检查每个条件
            for key, expected_value in conditions.items():
                actual_value = context.get(key)
                
                # 支持多种匹配方式
                if isinstance(expected_value, list):
                    # 列表匹配：实际值在列表中
                    if actual_value not in expected_value:
                        return False
                elif isinstance(expected_value, dict):
                    # 复杂条件匹配
                    operator = expected_value.get('operator', 'eq')
                    value = expected_value.get('value')
                    
                    if operator == 'eq' and actual_value != value:
                        return False
                    elif operator == 'ne' and actual_value == value:
                        return False
                    elif operator == 'gt' and not (actual_value > value):
                        return False
                    elif operator == 'gte' and not (actual_value >= value):
                        return False
                    elif operator == 'lt' and not (actual_value < value):
                        return False
                    elif operator == 'lte' and not (actual_value <= value):
                        return False
                    elif operator == 'contains' and value not in str(actual_value):
                        return False
                else:
                    # 简单相等匹配（兼容类型差异，如 int vs str）
                    if actual_value != expected_value:
                        # 尝试数值比较
                        try:
                            if int(actual_value) == int(expected_value):
                                continue
                        except (ValueError, TypeError):
                            pass
                        return False
            
            return True
        except:
            return True
    
    def _render_template(
        self,
        notification_type: str,
        event_type: str,
        default_title: str,
        default_content: str,
        context: Dict[str, Any]
    ) -> tuple:
        """
        根据匹配规则的模板渲染通知标题和内容
        如果规则关联了模板，使用模板渲染；否则使用默认标题和内容
        
        Args:
            notification_type: 通知类型
            event_type: 事件类型
            default_title: 默认标题
            default_content: 默认内容
            context: 上下文变量
        
        Returns:
            (rendered_title, rendered_content) 元组
        """
        # 查找匹配的规则（取第一个有模板的）
        rules = self.db.query(NotificationRule).filter(
            NotificationRule.notification_type == notification_type,
            NotificationRule.event_type == event_type,
            NotificationRule.is_active == True,
            NotificationRule.template_id.isnot(None)
        ).all()
        
        if not rules:
            return default_title, default_content
        
        # 取第一个匹配规则的模板
        template_id = rules[0].template_id
        template = self.db.query(NotificationTemplate).filter(
            NotificationTemplate.id == template_id
        ).first()
        
        if not template:
            return default_title, default_content
        
        # 将模板中的 {variable} 格式转换为 format() 所需的格式
        def convert_template(template_str):
            import re
            return re.sub(r'\{(\w+)\}', r'{\1}', template_str)
        
        converted_title = convert_template(template.title_template)
        converted_content = convert_template(template.content_template)
        
        # 使用 context 变量渲染模板
        title_ok = False
        content_ok = False
        rendered_title = converted_title
        rendered_content = converted_content
        
        try:
            rendered_title = converted_title.format(**context)
            title_ok = True
        except (KeyError, ValueError, IndexError) as e:
            # 标题渲染失败，保留原始模板
            pass
        
        try:
            rendered_content = converted_content.format(**context)
            content_ok = True
        except (KeyError, ValueError, IndexError) as e:
            # 内容渲染失败，保留原始模板而不是系统默认
            pass
        
        return rendered_title, rendered_content
    
    def _get_users_by_role(self, role_id: int) -> List[int]:
        """
        根据角色ID获取用户ID列表
        
        Args:
            role_id: 角色ID
        
        Returns:
            用户ID列表
        """
        user_roles = self.db.query(UserRole).filter(
            UserRole.role_id == role_id
        ).all()
        
        return [ur.user_id for ur in user_roles]
    
    def _filter_by_project_permission(
        self,
        user_ids: List[int],
        notification_type: str,
        context: Dict[str, Any]
    ) -> List[int]:
        """
        根据项目权限过滤接收人
        
        规则：
        1. 超级管理员（admin）可以接收所有通知
        2. 其他用户只能接收所属项目组的通知
        3. 测试工程师只能接收与自己相关的通知（分配给自己的测试计划）
        
        Args:
            user_ids: 候选用户ID列表
            notification_type: 通知类型
            context: 上下文数据（包含project_id, testplan_id, executor_id等）
        
        Returns:
            过滤后的用户ID列表
        """
        if not user_ids:
            return []
        
        # 获取通知关联的项目ID
        project_id = context.get('project_id')
        testplan_id = context.get('testplan_id')
        executor_id = context.get('executor_id')
        
        # 如果没有项目信息，尝试从testplan获取
        if not project_id and testplan_id:
            testplan = self.db.query(TestPlan).filter(TestPlan.id == testplan_id).first()
            if testplan:
                project_id = testplan.project_id
        
        # 如果还是没有项目信息，返回所有用户（系统级通知）
        if not project_id:
            return user_ids
        
        filtered_users = []
        
        for user_id in user_ids:
            # 查询用户信息
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                continue
            
            # 超级管理员可以接收所有通知
            if is_super_admin(user):
                filtered_users.append(user_id)
                continue
            
            # 检查用户是否有该项目的权限
            has_project_permission = self.db.query(UserProject).filter(
                UserProject.user_id == user_id,
                UserProject.project_id == project_id
            ).first() is not None
            
            if not has_project_permission:
                continue
            
            # 检查用户角色
            user_roles = self.db.query(UserRole).filter(
                UserRole.user_id == user_id
            ).all()
            
            role_names = []
            for ur in user_roles:
                role = self.db.query(Role).filter(Role.id == ur.role_id).first()
                if role:
                    role_names.append(role.name)
            
            # 测试工程师需要额外检查是否与自己相关
            if 'tester' in role_names or '测试工程师' in role_names:
                # 用例通知：有项目权限即可接收
                if notification_type == 'testcase':
                    filtered_users.append(user_id)
                # 对于测试计划相关的通知，检查是否分配给该用户
                elif testplan_id:
                    is_executor = self.db.query(TestPlanExecutor).filter(
                        TestPlanExecutor.test_plan_id == testplan_id,
                        TestPlanExecutor.executor_id == user_id
                    ).first() is not None
                    
                    if is_executor:
                        filtered_users.append(user_id)
                # 对于执行相关的通知，检查executor_id
                elif executor_id and executor_id == user_id:
                    filtered_users.append(user_id)
                # 其他类型的通知，测试工程师不接收
            else:
                # 非测试工程师，有项目权限即可接收
                filtered_users.append(user_id)
        
        return filtered_users
    
    def _filter_by_user_preference(
        self,
        user_ids: List[int],
        notification_type: str
    ) -> List[int]:
        """
        根据用户偏好过滤接收人
        
        Args:
            user_ids: 候选用户ID列表
            notification_type: 通知类型
        
        Returns:
            过滤后的用户ID列表
        """
        if not user_ids:
            return []
        
        filtered_users = []
        
        for user_id in user_ids:
            # 查询用户对该类型通知的偏好设置
            preference = self.db.query(UserNotificationPreference).filter(
                UserNotificationPreference.user_id == user_id,
                UserNotificationPreference.notification_type == notification_type
            ).first()
            
            # 如果没有偏好设置，默认启用
            if not preference or preference.is_enabled:
                filtered_users.append(user_id)
        
        return filtered_users
    
    def _push_to_dingtalk(self, notification, context: Dict[str, Any], recipient_user_ids: List[int] = None):
        """根据匹配的通知规则推送到钉钉（每条通知只推一次）"""
        from services.dingtalk_service import DingtalkService
        
        # 查找匹配的规则
        rules = self.db.query(NotificationRule).filter(
            NotificationRule.notification_type == notification.notification_type,
            NotificationRule.event_type == notification.event_type,
            NotificationRule.is_active == True
        ).all()
        
        dingtalk_service = DingtalkService(self.db)
        project_id = context.get('project_id')
        team_id = context.get('team_id')
        
        # 获取接收人手机号用于@
        at_mobiles = []
        if recipient_user_ids:
            users = self.db.query(User).filter(User.id.in_(recipient_user_ids)).all()
            at_mobiles = [u.phone for u in users if u.phone]
        
        # 只推一次：找到第一条启用了钉钉的规则就推送，避免多条规则导致重复推送
        for rule in rules:
            notification_method = rule.notification_method or 'internal'
            if notification_method in ('dingtalk', 'both'):
                dingtalk_service.push_notification(notification, rule, project_id, team_id=team_id, at_mobiles=at_mobiles)
                break
    
    def _push_to_websocket(self, notification, recipient_user_ids: List[int]):
        """通过WebSocket推送实时通知给在线用户"""
        import asyncio
        from services.websocket_manager import ws_manager
        
        message = {
            "type": "notification",
            "data": {
                "id": notification.id,
                "title": notification.title,
                "content": notification.content,
                "notification_type": notification.notification_type,
                "event_type": notification.event_type,
                "related_id": notification.related_id,
                "created_at": notification.created_at.isoformat() if notification.created_at else None
            }
        }
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(ws_manager.send_to_users(recipient_user_ids, message))
            else:
                loop.run_until_complete(ws_manager.send_to_users(recipient_user_ids, message))
        except RuntimeError:
            # 没有事件循环时跳过WebSocket推送
            pass
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """
        标记通知为已读
        """
        recipient = self.db.query(NotificationRecipient).filter(
            NotificationRecipient.notification_id == notification_id,
            NotificationRecipient.user_id == user_id
        ).first()
        
        if recipient and not recipient.is_read:
            recipient.is_read = True
            recipient.read_at = datetime.now()
            self.db.commit()
            return True
        
        return False
    
    def mark_all_as_read(self, user_id: int) -> int:
        """
        标记用户所有通知为已读
        
        Args:
            user_id: 用户ID
        
        Returns:
            标记数量
        """
        recipients = self.db.query(NotificationRecipient).filter(
            NotificationRecipient.user_id == user_id,
            NotificationRecipient.is_read == False
        ).all()
        
        count = 0
        for recipient in recipients:
            recipient.is_read = True
            recipient.read_at = datetime.now()
            count += 1
        
        self.db.commit()
        return count
    
    def get_user_notifications(
        self,
        user_id: int,
        notification_type: Optional[str] = None,
        is_read: Optional[bool] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """
        获取用户通知列表
        
        Args:
            user_id: 用户ID
            notification_type: 通知类型筛选
            is_read: 已读状态筛选
            page: 页码
            size: 每页数量
        
        Returns:
            通知列表和总数
        """
        # 构建查询
        query = self.db.query(
            Notification, NotificationRecipient
        ).join(
            NotificationRecipient,
            Notification.id == NotificationRecipient.notification_id
        ).filter(
            NotificationRecipient.user_id == user_id
        )
        
        # 应用筛选
        if notification_type:
            query = query.filter(Notification.notification_type == notification_type)
        
        if is_read is not None:
            query = query.filter(NotificationRecipient.is_read == is_read)
        
        # 排序
        query = query.order_by(Notification.created_at.desc(), Notification.id.desc())
        
        # 总数
        total = query.count()
        
        # 分页
        notifications = query.offset((page - 1) * size).limit(size).all()
        
        # 格式化结果
        records = []
        for notification, recipient in notifications:
            records.append({
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'notification_type': notification.notification_type,
                'event_type': notification.event_type,
                'related_id': notification.related_id,
                'related_type': notification.related_type,
                'is_read': recipient.is_read,
                'read_at': recipient.read_at,
                'created_at': notification.created_at
            })
        
        return {
            'records': records,
            'total': total,
            'page': page,
            'size': size
        }
    
    def get_unread_count(self, user_id: int) -> int:
        """
        获取用户未读通知数量
        
        Args:
            user_id: 用户ID
        
        Returns:
            未读数量
        """
        count = self.db.query(NotificationRecipient).filter(
            NotificationRecipient.user_id == user_id,
            NotificationRecipient.is_read == False
        ).count()
        
        return count
