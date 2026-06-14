"""
通知触发辅助函数
在业务API中方便地触发通知
"""
from sqlalchemy.orm import Session
from services.notification_service import NotificationService
from typing import Optional, Dict, Any, List
from datetime import datetime
import re


def _build_detail_link(notification_type: str, related_id: Optional[int] = None, related_type: Optional[str] = None, event_type: Optional[str] = None) -> Optional[str]:
    """
    根据通知类型和关联ID构建前端详情页链接
    
    Returns:
        前端页面URL，如果无法构建则返回None
    """
    if not related_id:
        return None
    
    from config import settings
    base_url = settings.FRONTEND_URL.rstrip('/')
    
    # 测试计划提交审核时，链接指向报告审核页
    if notification_type == 'testplan' and event_type == 'submitted_for_review':
        try:
            from database import SessionLocal
            from models import Report
            db = SessionLocal()
            report = db.query(Report).filter(
                Report.test_plan_id == related_id,
                Report.status == 'PENDING_REVIEW'
            ).order_by(Report.id.desc()).first()
            db.close()
            if report:
                return f"{base_url}/reports/review/{report.id}"
        except Exception:
            pass
    
    path_map = {
        'testcase': '/testcases',
        'testplan': f'/testplans/{related_id}',
        'execution': f'/testplans/{related_id}',
        'report': f'/reports/review/{related_id}',
    }
    
    path = path_map.get(notification_type)
    if not path:
        return None
    
    return f"{base_url}{path}"


def _format_datetime_str(dt_str: Optional[str]) -> Optional[str]:
    """格式化日期时间字符串，去掉午夜时分秒（00:00:00）只保留日期"""
    if not dt_str:
        return dt_str
    return re.sub(r'\s+00:00:00$', '', str(dt_str))


def trigger_assignment_notification(
    db: Session,
    notification_type: str,
    event_type: str,
    title: str,
    content: str,
    related_id: int,
    related_type: str,
    sender_id: int,
    recipient_user_ids: List[int],
    project_id: Optional[int] = None,
    team_id: Optional[int] = None,
    extra_context: Optional[Dict[str, Any]] = None
):
    """
    触发任务分配通知（直接指定接收人）
    
    用于测试计划分配执行人、评审计划分配评审人等场景。
    跳过规则匹配，直接发送给指定用户。
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[trigger_assignment_notification] type={notification_type}, event={event_type}, sender_id={sender_id}, recipient_ids={recipient_user_ids}")
        
        # 排除发送人自己
        recipient_user_ids = [uid for uid in recipient_user_ids if uid != sender_id]
        if not recipient_user_ids:
            logger.info(f"[trigger_assignment_notification] 过滤后无接收人，跳过通知")
            return
        
        logger.info(f"[trigger_assignment_notification] 过滤后接收人: {recipient_user_ids}")
        
        # 构建 context，合并 project_id、team_id 和额外上下文
        ctx = {'project_id': project_id, 'team_id': team_id}
        if extra_context:
            ctx.update(extra_context)
        
        service = NotificationService(db)
        result = service.create_notification(
            notification_type=notification_type,
            event_type=event_type,
            title=title,
            content=content,
            related_id=related_id,
            related_type=related_type,
            sender_id=sender_id,
            recipient_user_ids=recipient_user_ids,
            context=ctx
        )
        logger.info(f"[trigger_assignment_notification] 通知创建结果: {result}")
    except Exception as e:
        import logging, traceback
        logging.getLogger(__name__).error(f"触发分配通知失败: {e}\n{traceback.format_exc()}")


def trigger_testcase_notification(
    db: Session,
    event_type: str,
    testcase_id: int,
    testcase_name: str,
    operator_name: str,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    changes: Optional[str] = None,
    project_id: Optional[int] = None
):
    """
    触发测试用例相关通知
    
    Args:
        db: 数据库会话
        event_type: 事件类型 (created/updated/deleted/status_changed)
        testcase_id: 用例ID
        testcase_name: 用例名称
        operator_name: 操作人
        old_value: 旧值（用于状态变更）
        new_value: 新值（用于状态变更）
        changes: 变更内容描述
    """
    try:
        service = NotificationService(db)
        
        # 构建标题
        action_map = {
            'created': '创建',
            'updated': '更新',
            'deleted': '删除',
            'status_changed': '状态变更'
        }
        action = action_map.get(event_type, event_type)
        title = f'测试用例 #{testcase_id} {action}'
        
        # 构建内容
        if event_type == 'status_changed' and old_value and new_value:
            content = f'用例"{testcase_name}"已被{operator_name}进行状态变更操作。\n\n'
            content += f'修改内容：状态从"{old_value}"变更为"{new_value}"\n\n'
            content += f'时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        elif changes:
            content = f'用例"{testcase_name}"已被{operator_name}进行{action}操作。\n\n'
            content += f'修改内容：{changes}\n\n'
            content += f'时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        else:
            content = f'用例"{testcase_name}"已被{operator_name}进行{action}操作。\n\n'
            content += f'时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        # 创建通知
        service.create_notification(
            notification_type='testcase',
            event_type=event_type,
            title=title,
            content=content,
            related_id=testcase_id,
            related_type='testcase',
            context={
                'case_id': testcase_id,
                'case_name': testcase_name,
                'action': action,
                'operator': operator_name,
                'old_status': old_value,
                'new_status': new_value,
                'changes': changes or '',
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'project_id': project_id
            }
        )
    except Exception as e:
        # 通知失败不应影响主业务流程
        print(f"触发用例通知失败: {e}")


def trigger_execution_notification(
    db: Session,
    event_type: str,
    execution_id: int,
    testcase_name: str,
    result: str,
    executor_name: str,
    remarks: Optional[str] = None,
    project_id: Optional[int] = None
):
    """
    触发测试执行相关通知
    
    Args:
        db: 数据库会话
        event_type: 事件类型 (result_updated/completed)
        execution_id: 执行ID
        testcase_name: 用例名称
        result: 执行结果
        executor_name: 执行人
        remarks: 备注
    """
    try:
        service = NotificationService(db)
        
        # 构建标题
        title = '测试执行结果更新'
        
        # 构建内容
        content = f'测试用例"{testcase_name}"的执行结果已更新。\n\n'
        content += f'执行结果：{result}\n'
        if remarks:
            content += f'备注：{remarks}\n'
        content += f'\n执行人：{executor_name}\n'
        content += f'时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        # 创建通知
        service.create_notification(
            notification_type='execution',
            event_type=event_type,
            title=title,
            content=content,
            related_id=execution_id,
            related_type='execution',
            context={
                'case_name': testcase_name,
                'result': result,
                'remarks': remarks or '',
                'executor': executor_name,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'project_id': project_id
            }
        )
    except Exception as e:
        print(f"触发执行通知失败: {e}")


def trigger_report_notification(
    db: Session,
    event_type: str,
    report_id: int,
    report_name: str,
    operator_name: str,
    total_cases: int = 0,
    passed: int = 0,
    failed: int = 0,
    pass_rate: float = 0.0,
    project_id: Optional[int] = None
):
    """
    触发测试报告相关通知（仅用于 generated 和 alert 事件，走规则匹配）
    
    注意：approved/rejected 事件已改为在 report.py 中直接调用
    NotificationService.create_notification()，不经过此函数。
    
    Args:
        db: 数据库会话
        event_type: 事件类型 (generated/alert)
        report_id: 报告ID
        report_name: 报告名称
        operator_name: 操作人
        total_cases: 总用例数
        passed: 通过数
        failed: 失败数
        pass_rate: 通过率
    """
    try:
        service = NotificationService(db)
        
        fail_rate = 100 - pass_rate
        
        if event_type == 'alert' and fail_rate > 50:
            # 异常告警
            title = '⚠️ 测试报告异常告警'
            content = f'测试报告"{report_name}"存在异常指标！\n\n'
            content += '异常详情：\n'
            content += f'- 失败率：{fail_rate:.1f}%（阈值：50%）\n'
            content += f'- 失败用例数：{failed}\n'
            content += f'- 总用例数：{total_cases}\n'
            content += '\n请及时关注并处理。\n\n'
            content += f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        else:
            # 正常生成
            title = f'测试报告 "{report_name}" 已生成'
            content = f'测试报告"{report_name}"已生成完成。\n\n'
            content += '报告摘要：\n'
            content += f'- 总用例数：{total_cases}\n'
            content += f'- 通过数：{passed}\n'
            content += f'- 失败数：{failed}\n'
            content += f'- 通过率：{pass_rate:.1f}%\n'
            content += f'\n生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        # 创建通知
        service.create_notification(
            notification_type='report',
            event_type=event_type,
            title=title,
            content=content,
            related_id=report_id,
            related_type='report',
            context={
                'report_name': report_name,
                'total_cases': total_cases,
                'passed': passed,
                'failed': failed,
                'pass_rate': pass_rate,
                'fail_rate': 100 - pass_rate if pass_rate > 0 else 0,
                'operator': operator_name,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'project_id': project_id
            }
        )
    except Exception as e:
        print(f"触发报告通知失败: {e}")
