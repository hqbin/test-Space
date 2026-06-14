"""
测试执行服务
"""
from sqlalchemy.orm import Session
from models import TestExecution, TestPlanExecutor, TestCase, User
from utils.exceptions import ValidationError, PermissionError, NotFoundError
from utils.permissions import is_executor
from typing import Optional, List


class ExecutionService:
    """测试执行服务"""
    
    @staticmethod
    def save_execution_result(
        testplan_id: int,
        testcase_id: int,
        user_id: int,
        result: str,
        db: Session,
        remarks: Optional[str] = None,
        actual_result: Optional[str] = None,
        failure_reason: Optional[str] = None,
        version_info: Optional[str] = None
    ) -> TestExecution:
        """
        保存测试执行结果
        
        策略：始终创建新记录，保留完整历史
        
        Args:
            testplan_id: 测试计划ID
            testcase_id: 测试用例ID
            user_id: 执行人ID
            result: 执行结果 (PASSED/FAILED/BLOCKED/SKIPPED)
            db: 数据库会话
            remarks: 备注
            actual_result: 实际结果
            failure_reason: 失败原因
        
        Returns:
            TestExecution: 执行记录
        
        Raises:
            PermissionError: 权限不足
            ValidationError: 验证失败
        """
        # 1. 权限检查
        if not is_executor(user_id, testplan_id, db):
            raise PermissionError("只有测试计划的执行人才能执行测试")
        
        # 2. 验证输入
        if result not in ['PASSED', 'FAILED', 'BLOCKED', 'SKIPPED']:
            raise ValidationError(f"无效的执行结果: {result}")
        
        # 如果结果为FAILED，failure_reason应该填写
        if result == 'FAILED' and not failure_reason:
            raise ValidationError("执行结果为失败时，必须填写失败原因")
        
        # 3. 检查测试用例是否存在
        testcase = db.query(TestCase).filter(TestCase.id == testcase_id).first()
        if not testcase:
            raise NotFoundError(f"测试用例不存在: {testcase_id}")
        
        # 4. 创建新的执行记录（不覆盖历史）
        execution = TestExecution(
            test_plan_id=testplan_id,
            test_case_id=testcase_id,
            executor_id=user_id,
            result=result,
            remarks=remarks,
            actual_result=actual_result,
            failure_reason=failure_reason,
            version_info=version_info
        )
        
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # 5. 更新测试计划状态：如果有执行记录且状态为PENDING，则改为IN_PROGRESS
        from models import TestPlan
        testplan = db.query(TestPlan).filter(TestPlan.id == testplan_id).first()
        if testplan and testplan.status == 'PENDING':
            testplan.status = 'IN_PROGRESS'
            db.commit()
        
        return execution
    
    @staticmethod
    def batch_mark_execution(
        testplan_id: int,
        testcase_ids: List[int],
        user_id: int,
        result: str,
        db: Session
    ) -> int:
        """
        批量标记执行结果
        
        Args:
            testplan_id: 测试计划ID
            testcase_ids: 测试用例ID列表
            user_id: 执行人ID
            result: 执行结果 (PASSED/SKIPPED/BLOCKED)
            db: 数据库会话
        
        Returns:
            int: 成功标记的数量
        
        Raises:
            PermissionError: 权限不足
            ValidationError: 验证失败
        """
        # 1. 权限检查
        if not is_executor(user_id, testplan_id, db):
            raise PermissionError("只有测试计划的执行人才能执行测试")
        
        # 2. 验证结果类型
        VALID_RESULTS = ['PASS', 'FAIL', 'NA', 'NT', 'BLOCK', '待确认', 'PASSED', 'SKIPPED', 'BLOCKED']
        if result not in VALID_RESULTS:
            raise ValidationError(f"批量操作只支持PASS/FAIL/NA/NT/BLOCK/待确认")
        
        # 3. 批量创建执行记录
        executions = []
        for testcase_id in testcase_ids:
            execution = TestExecution(
                test_plan_id=testplan_id,
                test_case_id=testcase_id,
                executor_id=user_id,
                result=result,
                remarks=f"批量标记为{result}"
            )
            executions.append(execution)
        
        db.bulk_save_objects(executions)
        db.commit()
        
        # 4. 更新测试计划状态：如果有执行记录且状态为PENDING，则改为IN_PROGRESS
        from models import TestPlan
        testplan = db.query(TestPlan).filter(TestPlan.id == testplan_id).first()
        if testplan and testplan.status == 'PENDING':
            testplan.status = 'IN_PROGRESS'
            db.commit()
        
        return len(executions)
    
    @staticmethod
    def get_execution_detail(execution_id: int, db: Session) -> Optional[TestExecution]:
        """
        获取执行记录详情
        
        Args:
            execution_id: 执行记录ID
            db: 数据库会话
        
        Returns:
            TestExecution: 执行记录
        """
        execution = db.query(TestExecution).filter(
            TestExecution.id == execution_id
        ).first()
        
        return execution
    
    @staticmethod
    def get_testplan_executions(
        testplan_id: int,
        db: Session,
        executor_id: Optional[int] = None,
        result: Optional[str] = None
    ) -> List[TestExecution]:
        """
        获取测试计划的所有执行记录
        
        Args:
            testplan_id: 测试计划ID
            db: 数据库会话
            executor_id: 执行人ID（可选）
            result: 执行结果（可选）
        
        Returns:
            list: 执行记录列表
        """
        query = db.query(TestExecution).filter(
            TestExecution.test_plan_id == testplan_id
        )
        
        if executor_id:
            query = query.filter(TestExecution.executor_id == executor_id)
        
        if result:
            query = query.filter(TestExecution.result == result)
        
        executions = query.order_by(TestExecution.executed_at.desc()).all()
        
        return executions
    
    @staticmethod
    def get_latest_execution(
        testplan_id: int,
        testcase_id: int,
        db: Session
    ) -> Optional[TestExecution]:
        """
        获取测试用例的最新执行记录
        
        Args:
            testplan_id: 测试计划ID
            testcase_id: 测试用例ID
            db: 数据库会话
        
        Returns:
            TestExecution: 最新执行记录
        """
        execution = db.query(TestExecution).filter(
            TestExecution.test_plan_id == testplan_id,
            TestExecution.test_case_id == testcase_id
        ).order_by(
            TestExecution.executed_at.desc()
        ).first()
        
        return execution
