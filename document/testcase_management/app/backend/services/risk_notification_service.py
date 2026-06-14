"""
风险预警通知服务
每天18点扫描进行中的测试计划，计算风险并发送通知
"""
from sqlalchemy.orm import Session
from models import TestPlan, TestPlanExecutor, User, TestExecution, TestPlanTestCase, DingtalkBot
from services.notification_service import NotificationService
from services.dingtalk_service import DingtalkService
from typing import List, Dict, Optional
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


CHINESE_HOLIDAYS = {
    2026: {
        'holidays': [
            {'name': '元旦', 'dates': ['2026-01-01', '2026-01-02', '2026-01-03']},
            {'name': '春节', 'dates': ['2026-02-15', '2026-02-16', '2026-02-17', '2026-02-18', '2026-02-19', '2026-02-20', '2026-02-21', '2026-02-22', '2026-02-23']},
            {'name': '清明节', 'dates': ['2026-04-04', '2026-04-05', '2026-04-06']},
            {'name': '劳动节', 'dates': ['2026-05-01', '2026-05-02', '2026-05-03', '2026-05-04', '2026-05-05']},
            {'name': '端午节', 'dates': ['2026-06-19', '2026-06-20', '2026-06-21']},
            {'name': '中秋节', 'dates': ['2026-09-25', '2026-09-26', '2026-09-27']},
            {'name': '国庆节', 'dates': ['2026-10-01', '2026-10-02', '2026-10-03', '2026-10-04', '2026-10-05', '2026-10-06', '2026-10-07']}
        ],
        'workdays': ['2026-01-04', '2026-02-14', '2026-02-28', '2026-05-09', '2026-09-20', '2026-10-10']
    },
    2027: {
        'holidays': [
            {'name': '元旦', 'dates': ['2027-01-01', '2027-01-02', '2027-01-03']},
            {'name': '春节', 'dates': ['2027-02-07', '2027-02-08', '2027-02-09', '2027-02-10', '2027-02-11', '2027-02-12', '2027-02-13', '2027-02-14', '2027-02-15']},
            {'name': '清明节', 'dates': ['2027-04-04', '2027-04-05', '2027-04-06']},
            {'name': '劳动节', 'dates': ['2027-05-01', '2027-05-02', '2027-05-03', '2027-05-04', '2027-05-05']},
            {'name': '端午节', 'dates': ['2027-06-08', '2027-06-09', '2027-06-10']},
        ],
        'workdays': ['2027-01-04', '2027-02-06', '2027-02-20', '2027-05-08']
    }
}


def format_date_str(date) -> str:
    """格式化日期为 YYYY-MM-DD 字符串"""
    if not date:
        return None
    d = date if isinstance(date, datetime) else datetime.strptime(str(date)[:10], '%Y-%m-%d')
    return d.strftime('%Y-%m-%d')


def is_weekend(date_str: str) -> bool:
    """判断是否周末"""
    try:
        d = datetime.strptime(date_str[:10], '%Y-%m-%d')
        return d.weekday() in (5, 6)  # 周六、周日
    except:
        return False


def is_holiday(date_str: str, year: int) -> bool:
    """判断是否节假日"""
    try:
        date_formatted = format_date_str(date_str)
        if not date_formatted:
            return False
        year_config = CHINESE_HOLIDAYS.get(year, {})
        for holiday in year_config.get('holidays', []):
            if date_formatted in holiday.get('dates', []):
                return True
        return False
    except:
        return False


def is_workday(date_str: str, year: int) -> bool:
    """判断是否补班日"""
    try:
        date_formatted = format_date_str(date_str)
        if not date_formatted:
            return False
        year_config = CHINESE_HOLIDAYS.get(year, {})
        return date_formatted in year_config.get('workdays', [])
    except:
        return False


def is_non_working_day(date_str: str) -> bool:
    """判断是否非工作日"""
    if is_workday(date_str, datetime.now().year):
        return False
    if is_weekend(date_str):
        return True
    if is_holiday(date_str, datetime.now().year):
        return True
    return False


def get_work_days_in_range(start_date, end_date) -> int:
    """计算工作日数"""
    if not start_date or not end_date:
        return 0
    start = start_date if isinstance(start_date, datetime) else datetime.strptime(str(start_date)[:10], '%Y-%m-%d')
    end = end_date if isinstance(end_date, datetime) else datetime.strptime(str(end_date)[:10], '%Y-%m-%d')
    
    work_days = 0
    current = start
    while current <= end:
        if not is_non_working_day(format_date_str(current)):
            work_days += 1
        current += timedelta(days=1)
    return work_days


def get_elapsed_work_days(start_date, reference_date) -> int:
    """计算已过去的工作日数"""
    if not start_date or not reference_date:
        return 0
    start = start_date if isinstance(start_date, datetime) else datetime.strptime(str(start_date)[:10], '%Y-%m-%d')
    ref = reference_date if isinstance(reference_date, datetime) else datetime.strptime(str(reference_date)[:10], '%Y-%m-%d')
    
    if ref <= start:
        return 0
    
    work_days = 0
    current = start
    while current < ref:  # 注意：这里是 <，不包含reference_date，和前端保持一致
        if not is_non_working_day(format_date_str(current)):
            work_days += 1
        current += timedelta(days=1)
    return work_days


class RiskNotificationService:
    """风险预警通知服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.dingtalk_service = DingtalkService(db)
    
    def check_and_notify(self) -> Dict:
        """
        检查所有进行中的测试计划并发送风险预警通知
        """
        result = {
            'total_plans': 0,
            'risk_plans': 0,
            'notifications_sent': 0,
            'dingtalk_sent': 0,
            'details': []
        }
        
        now = datetime.now()
        
        # 查找IN_PROGRESS和PENDING的计划（需要在计算时过滤是否在周期内）
        plans = self.db.query(TestPlan).filter(
            TestPlan.status.in_(['IN_PROGRESS', 'PENDING'])
        ).all()
        
        result['total_plans'] = len(plans)
        logger.info(f"风险预警检查：共 {len(plans)} 个测试计划")
        
        # 按项目组分组收集需要发送的通知
        team_notifications = {}  # team_id -> [notification_data]
        
        for plan in plans:
            # 获取用例数量和执行数量
            total_cases = self.db.query(TestPlanTestCase).filter(
                TestPlanTestCase.test_plan_id == plan.id
            ).count()
            
            if total_cases == 0:
                continue
            
            executed_count = self.db.query(TestExecution).filter(
                TestExecution.test_plan_id == plan.id,
                TestExecution.result.isnot(None)
            ).count()
            
            logger.info(f"检查计划 {plan.name}: status={plan.status}, total_cases={total_cases}, executed_count={executed_count}")
            
            # 计算风险
            risk = self._calculate_risk(plan, total_cases, executed_count, now)
            
            if risk is None:
                logger.info(f"计划 {plan.name} 无风险")
                continue
            
            risk_type, risk_text, severity = risk
            result['risk_plans'] += 1
            logger.info(f"风险计划：{plan.name}, {risk_text}")
            
            # 获取负责人和执行人
            recipient_ids = self._get_recipients(plan)
            if not recipient_ids:
                logger.warning(f"计划 {plan.name} 没有负责人或执行人，跳过站内通知")
                continue
            
            # 发送站内通知（每个接收人都会收到）
            for user_id in recipient_ids:
                try:
                    notification = self.notification_service.create_notification(
                        notification_type='testplan',
                        event_type='risk_alert',
                        title=f"测试计划风险预警 - {plan.name}",
                        content=f"测试计划「{plan.name}」存在{risk_text}",
                        related_id=plan.id,
                        related_type='testplan',
                        sender_id=None,
                        recipient_user_ids=[user_id],
                        context={
                            'testplan_id': plan.id,
                            'project_id': plan.project_id,
                            'team_id': plan.team_id,
                            'risk_type': risk_type,
                            'risk_text': risk_text,
                            'severity': severity,
                            'plan_name': plan.name,
                            'operator': '',
                            'action': '风险预警',
                        }
                    )
                    if notification:
                        result['notifications_sent'] += 1
                except Exception as e:
                    logger.error(f"发送站内通知失败: {e}")
            
            # 收集需要钉钉通知的消息（按项目组收集）
            if plan.team_id:
                if plan.team_id not in team_notifications:
                    team_notifications[plan.team_id] = []
                team_notifications[plan.team_id].append({
                    'plan': plan,
                    'risk_type': risk_type,
                    'risk_text': risk_text,
                    'severity': severity
                })
            else:
                logger.warning(f"计划 {plan.name} 没有关联项目组，跳过钉钉通知")
            
            result['details'].append({
                'plan_id': plan.id,
                'plan_name': plan.name,
                'risk_type': risk_type,
                'risk_text': risk_text
            })
        
        # 发送钉钉通知（按项目组，每个项目组发一条消息，包含该组所有风险计划）
        logger.info(f"风险预警：{len(team_notifications)} 个项目组需要发送钉钉通知")
        for team_id, notifications in team_notifications.items():
            self._send_team_dingtalk_notifications(team_id, notifications)
            result['dingtalk_sent'] += len(notifications)
        
        logger.info(f"风险预警完成：{result}")
        return result
    
    def _calculate_risk(self, plan: TestPlan, total_cases: int, executed_count: int, now: datetime):
        """计算测试计划的风险等级"""
        if not plan.start_time or not plan.end_time:
            return None
        
        start_date = plan.start_time
        end_date = plan.end_time
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # 已过期（当前时间 > 结束时间）
        if now > end_date:
            actual_progress = (executed_count / total_cases) * 100 if total_cases > 0 else 0
            if actual_progress >= 100:
                return None  # 已完成
            # 计算逾期天数
            days = (now - end_date.replace(hour=0, minute=0, second=0)).days
            return ('overdue', f'逾期{days}天', 'danger')
        
        # 当前时间 < 开始时间（还未到开始时间），不预警
        if now < start_date:
            return None
        
        # 当前时间在开始和结束时间之间
        # status=PENDING 且在测试周期内但未开始
        if plan.status == 'PENDING':
            return ('not_started', '未开始执行', 'warning')
        
        total_days = get_work_days_in_range(plan.start_time, plan.end_time)
        if total_days == 0:
            return None
        
        elapsed_days = get_elapsed_work_days(plan.start_time, now)
        
        expected_progress = (elapsed_days / total_days) * 100
        actual_progress = (executed_count / total_cases) * 100
        progress_gap = expected_progress - actual_progress
        
        if progress_gap <= 0:
            return None  # 正常
        
        if progress_gap < 5:
            return ('slight_delay', '轻微滞后', 'warning')
        elif progress_gap < 10:
            return ('delay', '进度滞后', 'danger')
        else:
            return ('severe_delay', '严重滞后', 'danger')
    
    def _get_recipients(self, plan: TestPlan) -> List[int]:
        """获取通知接收人（负责人+执行人）"""
        recipient_ids = set()
        
        # 添加负责人
        if plan.reviewer_id:
            recipient_ids.add(plan.reviewer_id)
        
        # 添加执行人
        executors = self.db.query(TestPlanExecutor).filter(
            TestPlanExecutor.test_plan_id == plan.id
        ).all()
        
        for executor in executors:
            recipient_ids.add(executor.executor_id)
        
        return list(recipient_ids)
    
    def _send_team_dingtalk_notifications(self, team_id: int, notifications: List[Dict]):
        """发送项目组钉钉通知"""
        logger.info(f"开始发送钉钉通知: team_id={team_id}, 计划数={len(notifications)}")
        
# 查找该项目组且配置了testplan通知类型的钉钉机器人
        bots = self.db.query(DingtalkBot).filter(
            DingtalkBot.team_id == team_id,
            DingtalkBot.is_active == True
        ).all()
        
        # 过滤出配置了testplan类型的机器人
        import json
        matched_bots = []
        for bot in bots:
            try:
                types = json.loads(bot.notification_types) if bot.notification_types else []
                if not types or 'testplan' in types:
                    matched_bots.append(bot)
            except:
                matched_bots.append(bot)
        bots = matched_bots
        
        logger.info(f"找到 {len(bots)} 个配置了testplan的钉钉机器人")
        
        if not bots:
            return
        
        # 收集需要@的人员手机号（用于实际@通知）
        at_mobiles = set()
        for item in notifications:
            plan = item['plan']
            if plan.reviewer_id:
                reviewer = self.db.query(User).filter(User.id == plan.reviewer_id).first()
                if reviewer and reviewer.phone:
                    at_mobiles.add(reviewer.phone)
            executors = self.db.query(TestPlanExecutor).filter(
                TestPlanExecutor.test_plan_id == plan.id
            ).all()
            for ex in executors:
                executor = self.db.query(User).filter(User.id == ex.executor_id).first()
                if executor and executor.phone:
                    at_mobiles.add(executor.phone)
        
        at_mobiles_list = list(at_mobiles)
        
        # 构建消息内容（人名不带@前缀，避免重复@）
        lines = ["### 🔔 测试计划风险预警\n"]
        
        for item in notifications:
            plan = item['plan']
            risk_text = item['risk_text']
            severity = item['severity']
            
            mention_names = []
            if plan.reviewer_id:
                reviewer = self.db.query(User).filter(User.id == plan.reviewer_id).first()
                if reviewer:
                    mention_names.append(reviewer.username)
            executors = self.db.query(TestPlanExecutor).filter(
                TestPlanExecutor.test_plan_id == plan.id
            ).all()
            for ex in executors:
                executor = self.db.query(User).filter(User.id == ex.executor_id).first()
                if executor and executor.username not in mention_names:
                    mention_names.append(executor.username)
            
            mention_text = ' @' + ' @'.join(mention_names) if mention_names else ''
            severity_emoji = '🔴' if severity == 'danger' else '🟡'
            lines.append(f"- {severity_emoji} **{plan.name}**: {risk_text}{mention_text}")
        
        content = '\n'.join(lines)
        
        # 发送到每个机器人，使用at_mobiles触发实际@
        for bot in bots:
            try:
                from services.dingtalk_service import DingtalkService
                dingtalk_svc = DingtalkService(self.db)
                result = dingtalk_svc._send_markdown(bot, '测试计划风险预警', content, at_mobiles=at_mobiles_list)
                logger.info(f"钉钉发送结果: {result}")
                if result.get("success"):
                    logger.info(f"钉钉通知发送成功: 团队{team_id}, 计划数{len(notifications)}")
                else:
                    logger.error(f"钉钉通知发送失败: {result.get('error')}")
            except Exception as e:
                logger.error(f"钉钉通知发送异常: {e}")