"""
外部执行接口 - 提供给外部系统调用，通过计划ID和用例编号提交测试结果
使用账号密码认证，内置请求频率限制
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import get_db
from models import TestPlan, TestCase, TestExecution, TestPlanTestCase, TestCaseZmindLink, User
from auth import verify_password
from utils.logger import log_operation, LogAction, LogModule
from utils.notification_helper import trigger_execution_notification
import json
import time
import threading

router = APIRouter()

# ============ 简易内存限流器 ============
class RateLimiter:
    """基于滑动窗口的内存限流，按IP限制"""
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = {}  # ip -> [timestamp, ...]
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            if key not in self._requests:
                self._requests[key] = []
            # 清理过期记录
            self._requests[key] = [
                t for t in self._requests[key]
                if now - t < self.window_seconds
            ]
            if len(self._requests[key]) >= self.max_requests:
                return False
            self._requests[key].append(now)
            return True

    def get_remaining(self, key: str) -> int:
        now = time.time()
        with self._lock:
            if key not in self._requests:
                return self.max_requests
            valid = [t for t in self._requests[key] if now - t < self.window_seconds]
            return max(0, self.max_requests - len(valid))

# 全局限流：每个IP每分钟最多30次请求
rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
# 登录失败限流：每个IP每分钟最多5次失败
login_fail_limiter = RateLimiter(max_requests=5, window_seconds=60)


class ExternalExecutionRequest(BaseModel):
    username: str  # 登录账号
    password: str  # 登录密码
    plan_id: int  # 测试计划ID
    case_number: str  # 用例编号
    result: str  # 执行结果: PASS/FAIL/NA/NT/BLOCK/待确认
    remarks: Optional[str] = None  # 执行备注
    version_info: Optional[str] = None  # 版本信息
    overwrite: Optional[int] = 1  # 是否覆盖已有结果: 0=不覆盖，1=覆盖，默认1


def _get_client_ip(request: Request) -> str:
    """获取客户端真实IP"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


@router.post("")
def external_execute(
    req: Request,
    body: ExternalExecutionRequest,
    db: Session = Depends(get_db),
):
    """
    外部执行接口 - 通过账号密码 + 计划ID + 用例编号提交测试结果

    POST /api/external-executions
    Body: {
        "username": "your_username",
        "password": "your_password",
        "plan_id": 1,
        "case_number": "TC-001",
        "result": "PASS",
        "remarks": "备注",
        "version_info": "v1.0"
    }
    """
    client_ip = _get_client_ip(req)

    # 1. 请求频率检查
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁，请稍后再试（每分钟最多30次）"
        )

    # 2. 登录失败次数检查
    if login_fail_limiter.get_remaining(client_ip) <= 0:
        raise HTTPException(
            status_code=429,
            detail="登录失败次数过多，请1分钟后再试"
        )

    # 3. 验证账号密码
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password):
        login_fail_limiter.is_allowed(client_ip)  # 记录一次失败
        raise HTTPException(status_code=401, detail="账号或密码错误")

    if user.status != 1:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    # 4. 验证执行结果值
    VALID_RESULTS = ['PASS', 'FAIL', 'NA', 'NT', 'BLOCK', '待确认']
    if body.result not in VALID_RESULTS:
        raise HTTPException(
            status_code=400,
            detail=f"执行结果必须是以下值之一: {', '.join(VALID_RESULTS)}"
        )

    # 5. 查找测试计划
    testplan = db.query(TestPlan).filter(TestPlan.id == body.plan_id).first()
    if not testplan:
        raise HTTPException(status_code=404, detail=f"测试计划不存在（ID: {body.plan_id}）")

    # 6. 检查计划状态
    status_msg = {
        'COMPLETED': '该测试计划已完成，无法提交执行结果',
        'IN_REVIEW': '该测试计划正在审核中，无法提交执行结果',
        'CANCELLED': '该测试计划已取消，无法提交执行结果',
    }
    if testplan.status in status_msg:
        raise HTTPException(status_code=400, detail=status_msg[testplan.status])

    # 7. 通过用例编号查找用例
    testcase = db.query(TestCase).filter(TestCase.case_number == body.case_number).first()
    if not testcase:
        raise HTTPException(status_code=404, detail=f"用例编号不存在: {body.case_number}")

    # 8. 验证该用例属于该计划
    plan_case = db.query(TestPlanTestCase).filter(
        TestPlanTestCase.test_plan_id == body.plan_id,
        TestPlanTestCase.test_case_id == testcase.id
    ).first()
    if not plan_case:
        raise HTTPException(
            status_code=400,
            detail=f"用例 {body.case_number} 不属于计划（ID: {body.plan_id}）"
        )

    # 9. 检查是否覆盖已有结果
    if body.overwrite == 0:
        existing_execution = db.query(TestExecution).filter(
            TestExecution.test_plan_id == body.plan_id,
            TestExecution.test_case_id == testcase.id
        ).order_by(TestExecution.executed_at.desc()).first()
        if existing_execution:
            return {
                "code": 200,
                "message": "已有测试结果，不覆盖",
                "data": {
                    "execution_id": existing_execution.id,
                    "plan_id": body.plan_id,
                    "plan_name": testplan.name,
                    "case_number": body.case_number,
                    "case_name": testcase.name,
                    "result": existing_execution.result,
                    "executor": user.username,
                    "executed_at": str(existing_execution.executed_at)
                }
            }

    # 11. 获取PR关联快照
    pr_links = db.query(TestCaseZmindLink).filter(
        TestCaseZmindLink.test_case_id == testcase.id
    ).all()
    pr_links_snapshot = []
    for link in pr_links:
        pr_links_snapshot.append({
            "zmind_issue_id": link.zmind_issue_id,
            "test_plan_id": link.test_plan_id
        })

    # 12. 创建执行记录
    db_execution = TestExecution(
        test_plan_id=body.plan_id,
        test_case_id=testcase.id,
        executor_id=user.id,
        result=body.result,
        remarks=body.remarks,
        version_info=body.version_info,
        testcase_number=testcase.case_number,
        testcase_name=testcase.name,
        testcase_module=testcase.module,
        testcase_sub_module=testcase.sub_module,
        testcase_level=testcase.level,
        testcase_precondition=testcase.precondition,
        testcase_steps=testcase.steps,
        testcase_expected_result=testcase.expected_result,
        pr_links_snapshot=json.dumps(pr_links_snapshot) if pr_links_snapshot else None
    )
    db.add(db_execution)
    db.commit()
    db.refresh(db_execution)

    # 13. 自动更新用例的自动化状态为 D
    if testcase.automation != 'D':
        old_automation = testcase.automation
        testcase.automation = 'D'
        db.commit()
        log_operation(
            db=db,
            user_id=user.id,
            username=user.username,
            module=LogModule.TESTCASES,
            action=LogAction.UPDATE,
            description=f"[外部接口] 执行测试用例时自动更新自动化状态：{testcase.case_number}（{old_automation or '空'} → D）",
            request=req
        )

    # 14. 更新计划状态：PENDING -> IN_PROGRESS
    if testplan.status == 'PENDING':
        testplan.status = 'IN_PROGRESS'
        db.commit()

    # 15. 记录操作日志（执行结果）
    log_operation(
        db=db,
        user_id=user.id,
        username=user.username,
        module=LogModule.EXECUTIONS,
        action=LogAction.EXECUTE,
        description=f"[外部接口] 执行测试用例（计划ID: {body.plan_id}，用例编号: {body.case_number}，结果: {body.result}）",
        request=req
    )

    # 16. 触发通知
    trigger_execution_notification(
        db=db,
        event_type='result_updated',
        execution_id=db_execution.id,
        testcase_name=testcase.name,
        result=db_execution.result,
        executor_name=user.username,
        remarks=db_execution.remarks,
        project_id=testplan.project_id
    )

    return {
        "code": 200,
        "message": "执行结果提交成功",
        "data": {
            "execution_id": db_execution.id,
            "plan_id": body.plan_id,
            "plan_name": testplan.name,
            "case_number": body.case_number,
            "case_name": testcase.name,
            "result": body.result,
            "executor": user.username,
            "executed_at": str(db_execution.executed_at)
        }
    }
