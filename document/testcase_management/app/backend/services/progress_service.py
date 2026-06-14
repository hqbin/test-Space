"""
进度统计服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import TestPlanTestCase, TestExecution, TestExecutionProgress
from typing import Optional


class ProgressService:
    """进度统计服务"""
    
    @staticmethod
    def calculate_progress_statistics(testplan_id: int, db: Session) -> dict:
        """
        实时计算测试进度统计
        
        Args:
            testplan_id: 测试计划ID
            db: 数据库会话
        
        Returns:
            dict: 统计结果
        """
        # 1. 获取总用例数
        total_cases = db.query(func.count(TestPlanTestCase.id)).filter(
            TestPlanTestCase.test_plan_id == testplan_id
        ).scalar() or 0
        
        # 2. 获取每个用例的最新执行结果
        # 使用子查询获取每个用例的最新执行记录
        from sqlalchemy import and_
        
        # 子查询：获取每个用例的最新执行时间
        latest_execution_subquery = db.query(
            TestExecution.test_case_id,
            func.max(TestExecution.executed_at).label('latest_time')
        ).filter(
            TestExecution.test_plan_id == testplan_id
        ).group_by(
            TestExecution.test_case_id
        ).subquery()
        
        # 主查询：获取最新执行记录的结果
        latest_executions = db.query(
            TestExecution.test_case_id,
            TestExecution.result
        ).join(
            latest_execution_subquery,
            and_(
                TestExecution.test_case_id == latest_execution_subquery.c.test_case_id,
                TestExecution.executed_at == latest_execution_subquery.c.latest_time
            )
        ).filter(
            TestExecution.test_plan_id == testplan_id
        ).all()
        
        # 3. 统计各状态数量
        stats = {
            'total': total_cases,
            'executed': 0,
            'not_executed': 0,
            'passed': 0,
            'failed': 0,
            'blocked': 0,
            'skipped': 0,
            'progress_percentage': 0.0
        }
        
        # 统计已执行的用例
        executed_cases = set()
        for test_case_id, result in latest_executions:
            executed_cases.add(test_case_id)
            
            if result == 'PASSED':
                stats['passed'] += 1
            elif result == 'FAILED':
                stats['failed'] += 1
            elif result == 'BLOCKED':
                stats['blocked'] += 1
            elif result == 'SKIPPED':
                stats['skipped'] += 1
        
        stats['executed'] = len(executed_cases)
        stats['not_executed'] = total_cases - stats['executed']
        
        # 计算进度百分比
        if total_cases > 0:
            stats['progress_percentage'] = round(
                (stats['executed'] / total_cases) * 100, 2
            )
        
        return stats
    
    @staticmethod
    def save_execution_progress(
        testplan_id: int,
        user_id: int,
        current_testcase_id: Optional[int],
        current_index: int,
        db: Session,
        sort_order: Optional[list] = None
    ) -> TestExecutionProgress:
        """
        保存执行进度
        
        Args:
            testplan_id: 测试计划ID
            user_id: 用户ID
            current_testcase_id: 当前测试用例ID
            current_index: 当前索引
            db: 数据库会话
            sort_order: 自定义排序
        
        Returns:
            TestExecutionProgress: 进度记录
        """
        from datetime import datetime
        
        # 查找现有进度记录
        progress = db.query(TestExecutionProgress).filter(
            TestExecutionProgress.testplan_id == testplan_id,
            TestExecutionProgress.user_id == user_id
        ).first()
        
        if progress:
            # 更新现有记录
            progress.current_testcase_id = current_testcase_id
            progress.current_index = current_index
            if sort_order is not None:
                progress.sort_order = sort_order
            progress.last_access_time = datetime.now()
        else:
            # 创建新记录
            progress = TestExecutionProgress(
                testplan_id=testplan_id,
                user_id=user_id,
                current_testcase_id=current_testcase_id,
                current_index=current_index,
                sort_order=sort_order,
                last_access_time=datetime.now()
            )
            db.add(progress)
        
        db.commit()
        db.refresh(progress)
        
        return progress
    
    @staticmethod
    def get_execution_progress(
        testplan_id: int,
        user_id: int,
        db: Session
    ) -> Optional[TestExecutionProgress]:
        """
        获取执行进度
        
        Args:
            testplan_id: 测试计划ID
            user_id: 用户ID
            db: 数据库会话
        
        Returns:
            TestExecutionProgress: 进度记录
        """
        progress = db.query(TestExecutionProgress).filter(
            TestExecutionProgress.testplan_id == testplan_id,
            TestExecutionProgress.user_id == user_id
        ).first()
        
        return progress
    
    @staticmethod
    def get_execution_history(
        testplan_id: int,
        testcase_id: int,
        db: Session,
        limit: int = 10
    ) -> list:
        """
        获取测试用例的执行历史
        
        Args:
            testplan_id: 测试计划ID
            testcase_id: 测试用例ID
            db: 数据库会话
            limit: 返回记录数量限制
        
        Returns:
            list: 执行历史记录
        """
        executions = db.query(TestExecution).filter(
            TestExecution.test_plan_id == testplan_id,
            TestExecution.test_case_id == testcase_id
        ).order_by(
            TestExecution.executed_at.desc()
        ).limit(limit).all()
        
        return executions
