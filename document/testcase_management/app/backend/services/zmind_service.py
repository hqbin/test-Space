"""
Zmind集成服务
"""
from sqlalchemy.orm import Session
from models import TestExecution, TestCase, TestPlan, User, TestCaseZmindLink
from utils.exceptions import APIError, NotFoundError
from utils.retry import retry_on_api_error
from typing import Optional
import requests
from config import settings

# 从settings实例获取配置
ZMIND_API_URL = settings.ZMIND_API_URL
ZMIND_API_KEY = settings.ZMIND_API_KEY


class ZmindService:
    """Zmind集成服务"""
    
    @staticmethod
    @retry_on_api_error(max_retries=3, base_delay=1)
    def create_zmind_issue(
        execution_id: int,
        db: Session,
        title: Optional[str] = None,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        issue_type: str = "Bug",
        priority: str = "Medium",
        assignee: Optional[str] = None
    ) -> dict:
        """
        创建Zmind问题单
        
        自动重试3次，超时300秒
        
        Args:
            execution_id: 执行记录ID
            db: 数据库会话
            title: 问题单标题（可选，默认使用用例名称）
            description: 问题单描述（可选，自动生成）
            project_id: Zmind项目ID
            issue_type: 问题类型
            priority: 优先级
            assignee: 指派人
        
        Returns:
            dict: 问题单信息 {issue_id, issue_url, title, status}
        
        Raises:
            NotFoundError: 执行记录不存在
            APIError: API调用失败
        """
        # 1. 获取执行记录
        execution = db.query(TestExecution).filter(
            TestExecution.id == execution_id
        ).first()
        
        if not execution:
            raise NotFoundError(f"执行记录不存在: {execution_id}")
        
        # 2. 获取相关信息
        testcase = db.query(TestCase).filter(TestCase.id == execution.test_case_id).first()
        testplan = db.query(TestPlan).filter(TestPlan.id == execution.test_plan_id).first()
        executor = db.query(User).filter(User.id == execution.executor_id).first()
        
        # 3. 准备问题单数据
        if not title:
            title = testcase.name if testcase else "测试失败"
        
        if not description:
            description = ZmindService._generate_issue_description(
                execution, testcase, testplan, executor
            )
        
        zmind_data = {
            'title': title,
            'description': description,
            'project_id': project_id,
            'issue_type': issue_type,
            'priority': priority,
            'assignee': assignee
        }
        
        # 4. 调用Zmind API
        try:
            # 获取用户的API Key
            api_key = executor.zmind_api_key if executor else ZMIND_API_KEY
            
            if not api_key:
                raise APIError("未配置Zmind API Key")
            
            response = requests.post(
                f"{ZMIND_API_URL}/issues",
                json=zmind_data,
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=300  # 300秒超时
            )
            response.raise_for_status()
            
            result = response.json()
            issue_id = result.get('id') or result.get('issue_id')
            issue_url = result.get('url') or result.get('issue_url')
            
            # 5. 保存关联关系到执行记录
            execution.zmind_issue_id = str(issue_id)
            execution.zmind_issue_url = issue_url
            db.commit()
            
            # 6. 在用例库中也添加关联
            link = TestCaseZmindLink(
                test_case_id=testcase.id,
                zmind_issue_id=str(issue_id),
                zmind_issue_subject=title,
                zmind_issue_status='Open',
                created_by=execution.executor_id
            )
            db.add(link)
            db.commit()
            
            return {
                'issue_id': str(issue_id),
                'issue_url': issue_url,
                'title': title,
                'status': 'Open'
            }
            
        except requests.Timeout:
            raise APIError("Zmind API调用超时，请稍后重试")
        except requests.RequestException as e:
            raise APIError(f"Zmind API调用失败: {str(e)}")
    
    @staticmethod
    def _generate_issue_description(
        execution: TestExecution,
        testcase: Optional[TestCase],
        testplan: Optional[TestPlan],
        executor: Optional[User]
    ) -> str:
        """
        生成Zmind问题单描述
        
        Args:
            execution: 执行记录
            testcase: 测试用例
            testplan: 测试计划
            executor: 执行人
        
        Returns:
            str: 问题单描述
        """
        description_parts = []
        
        if testcase:
            description_parts.append(f"**测试用例ID**: {testcase.id}")
            description_parts.append(f"**测试用例名称**: {testcase.name}")
            description_parts.append("")
            
            if testcase.precondition:
                description_parts.append(f"**前置条件**:")
                description_parts.append(testcase.precondition)
                description_parts.append("")
            
            if testcase.steps:
                description_parts.append(f"**测试步骤**:")
                description_parts.append(testcase.steps)
                description_parts.append("")
            
            if testcase.expected_result:
                description_parts.append(f"**预期结果**:")
                description_parts.append(testcase.expected_result)
                description_parts.append("")
        
        if execution.actual_result:
            description_parts.append(f"**实际结果**:")
            description_parts.append(execution.actual_result)
            description_parts.append("")
        
        if execution.failure_reason:
            description_parts.append(f"**失败原因**:")
            description_parts.append(execution.failure_reason)
            description_parts.append("")
        
        if testplan:
            description_parts.append(f"**测试计划**: {testplan.name}")
        
        if executor:
            description_parts.append(f"**执行人**: {executor.username}")
        
        description_parts.append(f"**执行时间**: {execution.executed_at}")
        
        return "\n".join(description_parts)
    
    @staticmethod
    def get_zmind_issue_status(issue_id: str, api_key: str) -> Optional[dict]:
        """
        获取Zmind问题单状态
        
        Args:
            issue_id: 问题单ID
            api_key: API Key
        
        Returns:
            dict: 问题单信息
        """
        try:
            response = requests.get(
                f"{ZMIND_API_URL}/issues/{issue_id}",
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            raise APIError(f"获取Zmind问题单状态失败: {str(e)}")
    
    @staticmethod
    def sync_zmind_issue_status(execution_id: int, db: Session) -> bool:
        """
        同步Zmind问题单状态
        
        Args:
            execution_id: 执行记录ID
            db: 数据库会话
        
        Returns:
            bool: 是否成功
        """
        execution = db.query(TestExecution).filter(
            TestExecution.id == execution_id
        ).first()
        
        if not execution or not execution.zmind_issue_id:
            return False
        
        executor = db.query(User).filter(User.id == execution.executor_id).first()
        if not executor or not executor.zmind_api_key:
            return False
        
        try:
            issue_info = ZmindService.get_zmind_issue_status(
                execution.zmind_issue_id,
                executor.zmind_api_key
            )
            
            # 更新用例库中的关联状态
            link = db.query(TestCaseZmindLink).filter(
                TestCaseZmindLink.zmind_issue_id == execution.zmind_issue_id
            ).first()
            
            if link:
                link.zmind_issue_status = issue_info.get('status', 'Unknown')
                db.commit()
            
            return True
            
        except Exception:
            return False
