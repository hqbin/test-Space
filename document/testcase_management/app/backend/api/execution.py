from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
from models import TestExecution, User, TestCase
from schemas import TestExecutionCreate
from auth import get_current_user
from utils.logger import log_operation, LogAction, LogModule
from utils.notification_helper import trigger_execution_notification

router = APIRouter()

@router.post("")
async def execute_testcase(
    req: Request,
    execution: TestExecutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from models import TestPlan, TestCaseZmindLink
    import json

    # 验证测试结果值
    VALID_RESULTS = ['PASS', 'FAIL', 'NA', 'NT', 'BLOCK', 'ONGOING', '待确认']
    if execution.result not in VALID_RESULTS:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"测试结果必须是以下值之一: {', '.join(VALID_RESULTS)}"
        )

    # 冲突检测：检查该用例在当前计划中是否已有执行记录
    force_submit = False
    try:
        body_bytes = await req.body()
        body_str = body_bytes.decode('utf-8') if isinstance(body_bytes, bytes) else str(body_bytes)
        import logging
        logging.warning(f"请求体原始内容: {body_str[:500]}")
        req_body = json.loads(body_str)
        force_value = req_body.get('force', False)
        force_submit = bool(force_value) if isinstance(force_value, bool) else False
    except Exception as e:
        import logging
        logging.warning(f"读取请求体失败: {e}, body_bytes类型: {type(body_bytes)}")
        pass

    existing_exec = None
    if not force_submit:
        # 非强制模式才检测冲突：检查是否有其他人的执行记录
        current_user_id = int(current_user.id) if current_user.id else None
        
        existing_exec = db.query(TestExecution).filter(
            TestExecution.test_plan_id == execution.test_plan_id,
            TestExecution.test_case_id == execution.test_case_id,
            TestExecution.result.isnot(None),
            TestExecution.result != 'ONGOING'
        ).order_by(TestExecution.executed_at.desc()).first()

        if existing_exec and existing_exec.executor_id != current_user_id:
            executor = db.query(User).filter(User.id == existing_exec.executor_id).first()
            executor_name = executor.username if executor else "未知"
            return {
                "code": 409,
                "message": "该用例已被其他人执行，是否覆盖？",
                "data": {
                    "executor": executor_name,
                    "executed_at": existing_exec.executed_at.isoformat() if existing_exec.executed_at else None,
                    "result": existing_exec.result,
                    "remarks": existing_exec.remarks
                }
            }

    # 获取用例信息，保存快照
    testcase = db.query(TestCase).filter(TestCase.id == execution.test_case_id).first()
    if not testcase:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    # 获取当前关联的PR列表，保存快照
    pr_links = db.query(TestCaseZmindLink).filter(
        TestCaseZmindLink.test_case_id == execution.test_case_id
    ).all()
    
    pr_links_snapshot = []
    for link in pr_links:
        pr_links_snapshot.append({
            "zmind_issue_id": link.zmind_issue_id,
            "test_plan_id": link.test_plan_id
        })
    
    # 创建执行记录，包含用例快照和PR快照
    execution_data = execution.dict()
    execution_data['executor_id'] = current_user.id
    
    # 添加用例快照字段
    execution_data['testcase_number'] = testcase.case_number
    execution_data['testcase_name'] = testcase.name
    execution_data['testcase_module'] = testcase.module
    execution_data['testcase_sub_module'] = testcase.sub_module
    execution_data['testcase_level'] = testcase.level
    execution_data['testcase_precondition'] = testcase.precondition
    execution_data['testcase_steps'] = testcase.steps
    execution_data['testcase_expected_result'] = testcase.expected_result
    
    # 添加PR快照字段
    execution_data['pr_links_snapshot'] = json.dumps(pr_links_snapshot) if pr_links_snapshot else None
    
    db_execution = TestExecution(**execution_data)
    db.add(db_execution)
    db.commit()
    db.refresh(db_execution)
    
    # 更新测试计划状态
    if execution.test_plan_id:
        from models import TestPlanTestCase
        
        testplan = db.query(TestPlan).filter(TestPlan.id == execution.test_plan_id).first()
        if testplan:
            # 如果状态为PENDING，改为IN_PROGRESS
            if testplan.status == 'PENDING':
                testplan.status = 'IN_PROGRESS'
                db.commit()
            
            # 检查是否所有用例都已执行完成
            if testplan.status == 'IN_PROGRESS':
                # 获取测试计划的总用例数
                total_testcases = db.query(TestPlanTestCase).filter(
                    TestPlanTestCase.test_plan_id == execution.test_plan_id
                ).count()
                
                # 获取已执行的用例数（去重）
                executed_testcase_ids = db.query(TestExecution.test_case_id).filter(
                    TestExecution.test_plan_id == execution.test_plan_id
                ).distinct().all()
                executed_count = len(executed_testcase_ids)
                
                # 注意：不再自动设置为COMPLETED
                # 所有用例执行完成后，需要通过"提交审核"按钮进入审核流程
                # 只有审核通过后才会变为COMPLETED状态
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.EXECUTIONS,
        action=LogAction.EXECUTE,
        description=f"执行测试用例（编号: {testcase.case_number}，ID: {db_execution.id}，结果：{db_execution.result}）",
        request=req
    )
    
    # 触发通知
    # 获取project_id用于钉钉推送
    _exec_project_id = None
    if execution.test_plan_id:
        _exec_testplan = db.query(TestPlan).filter(TestPlan.id == execution.test_plan_id).first()
        if _exec_testplan:
            _exec_project_id = _exec_testplan.project_id
    trigger_execution_notification(
        db=db,
        event_type='result_updated',
        execution_id=db_execution.id,
        testcase_name=testcase.name,
        result=db_execution.result,
        executor_name=current_user.username,
        remarks=db_execution.remarks,
        project_id=_exec_project_id
    )
    
    return {"code": 200, "message": "success", "data": db_execution}

@router.get("")
def list_executions(
    req: Request,
    page: int = 1,
    size: int = 10,
    test_plan_id: int = None,
    test_case_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from models import TestPlan
    import json
    
    query = db.query(TestExecution)
    if test_plan_id:
        query = query.filter(TestExecution.test_plan_id == test_plan_id)
    if test_case_id:
        query = query.filter(TestExecution.test_case_id == test_case_id)
    
    # ONGOING 是过渡状态，不计入执行历史
    query = query.filter(TestExecution.result != 'ONGOING')
    
    total = query.count()
    executions = query.order_by(TestExecution.executed_at.desc(), TestExecution.id.desc()).offset((page - 1) * size).limit(size).all()
    
    # 添加执行人姓名和测试计划名称
    execution_list = []
    for execution in executions:
        # 解析PR快照
        pr_links_snapshot = []
        if execution.pr_links_snapshot:
            try:
                pr_links_snapshot = json.loads(execution.pr_links_snapshot)
            except:
                pr_links_snapshot = []
        
        execution_dict = {
            "id": execution.id,
            "test_plan_id": execution.test_plan_id,
            "test_case_id": execution.test_case_id,
            "executor_id": execution.executor_id,
            "result": execution.result,
            "remarks": execution.remarks,
            "actual_result": execution.actual_result,
            "failure_reason": execution.failure_reason,
            "zmind_issue_id": execution.zmind_issue_id,
            "zmind_issue_url": execution.zmind_issue_url,
            "executed_at": execution.executed_at,
            "executor_name": None,
            "test_plan_name": None,
            # 用例快照字段
            "testcase_number": execution.testcase_number,
            "testcase_name": execution.testcase_name,
            "testcase_module": execution.testcase_module,
            "testcase_sub_module": execution.testcase_sub_module,
            "testcase_level": execution.testcase_level,
            "testcase_precondition": execution.testcase_precondition,
            "testcase_steps": execution.testcase_steps,
            "testcase_expected_result": execution.testcase_expected_result,
            # PR快照
            "pr_links_snapshot": pr_links_snapshot,
            # 版本信息
            "version_info": execution.version_info,
        }
        
        # 查询执行人姓名
        if execution.executor_id:
            executor = db.query(User).filter(User.id == execution.executor_id).first()
            if executor:
                execution_dict["executor_name"] = executor.username
        
        # 查询测试计划名称
        if execution.test_plan_id:
            test_plan = db.query(TestPlan).filter(TestPlan.id == execution.test_plan_id).first()
            if test_plan:
                execution_dict["test_plan_name"] = test_plan.name
        
        execution_list.append(execution_dict)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "records": execution_list,
            "total": total
        }
    }


# ==================== 新增：增强的执行功能 ====================

from services import ExecutionService
from schemas import TestExecutionCreateEnhanced, BatchExecutionRequest
from fastapi import HTTPException, status
from utils.exceptions import ValidationError, PermissionError as PermError, NotFoundError


@router.post("/enhanced")
def execute_testcase_enhanced(
    req: Request,
    execution_data: TestExecutionCreateEnhanced,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    增强的测试执行接口
    
    支持：
    - 实际结果记录
    - 失败原因记录
    - 附件上传（通过单独的附件接口）
    - 自动创建执行历史
    """
    try:
        execution = ExecutionService.save_execution_result(
            testplan_id=execution_data.test_plan_id,
            testcase_id=execution_data.test_case_id,
            user_id=current_user.id,
            result=execution_data.result,
            db=db,
            remarks=execution_data.remarks,
            actual_result=execution_data.actual_result,
            failure_reason=execution_data.failure_reason,
            version_info=execution_data.version_info
        )
        
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.EXECUTIONS,
            action=LogAction.EXECUTE,
            description=f"执行测试用例（编号: {testcase.case_number}，ID: {execution.id}，结果：{execution.result}）",
            request=req
        )
        
        # 获取用例名称并触发通知
        from models import TestCase
        testcase = db.query(TestCase).filter(TestCase.id == execution.test_case_id).first()
        if testcase:
            _batch_project_id = None
            if execution.test_plan_id:
                _batch_tp = db.query(TestPlan).filter(TestPlan.id == execution.test_plan_id).first()
                if _batch_tp:
                    _batch_project_id = _batch_tp.project_id
            trigger_execution_notification(
                db=db,
                event_type='result_updated',
                execution_id=execution.id,
                testcase_name=testcase.name,
                result=execution.result,
                executor_name=current_user.username,
                remarks=execution_data.remarks,
                project_id=_batch_project_id
            )
        
        return {
            "code": 200,
            "message": "执行成功",
            "data": {
                "id": execution.id,
                "test_plan_id": execution.test_plan_id,
                "test_case_id": execution.test_case_id,
                "executor_id": execution.executor_id,
                "result": execution.result,
                "remarks": execution.remarks,
                "actual_result": execution.actual_result,
                "failure_reason": execution.failure_reason,
                "version_info": execution.version_info,
                "executed_at": execution.executed_at.isoformat()
            }
        }
    except (ValidationError, PermError, NotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/batch")
def batch_execute_testcases(
    req: Request,
    batch_data: BatchExecutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量标记执行结果
    
    支持批量标记为：PASSED、SKIPPED、BLOCKED
    """
    try:
        count = ExecutionService.batch_mark_execution(
            testplan_id=batch_data.test_plan_id,
            testcase_ids=batch_data.test_case_ids,
            user_id=current_user.id,
            result=batch_data.result,
            db=db
        )
        
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.EXECUTIONS,
            action=LogAction.EXECUTE,
            description=f"批量标记{count}个测试用例为{batch_data.result}",
            request=req
        )
        
        return {
            "code": 200,
            "message": f"成功标记{count}个用例",
            "data": {"count": count}
        }
    except (ValidationError, PermError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{execution_id}/detail")
def get_execution_detail(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取执行记录详情
    """
    try:
        execution = ExecutionService.get_execution_detail(execution_id, db)
        
        if not execution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="执行记录不存在")
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "id": execution.id,
                "test_plan_id": execution.test_plan_id,
                "test_case_id": execution.test_case_id,
                "executor_id": execution.executor_id,
                "result": execution.result,
                "remarks": execution.remarks,
                "actual_result": execution.actual_result,
                "failure_reason": execution.failure_reason,
                "zmind_issue_id": execution.zmind_issue_id,
                "zmind_issue_url": execution.zmind_issue_url,
                "executed_at": execution.executed_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/latest-remark")
def get_latest_execution_remark(
    test_plan_id: int,
    test_case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定测试计划中指定用例的最新执行备注
    
    用于在执行界面显示本次执行的历史备注
    备注跟着测试计划+用例，所有用户都可以查看
    """
    try:
        # 查询该测试计划中该用例的最新执行记录（不限制用户）
        execution = db.query(TestExecution).filter(
            TestExecution.test_plan_id == test_plan_id,
            TestExecution.test_case_id == test_case_id
        ).order_by(TestExecution.executed_at.desc()).first()
        
        if execution:
            # 获取执行人姓名
            executor = db.query(User).filter(User.id == execution.executor_id).first()
            executor_name = executor.username if executor else "未知"
            
            # 确保备注字段返回空字符串而不是None
            remarks = execution.remarks if execution.remarks else ""
            
            return {
                "code": 200,
                "message": "获取成功",
                "data": {
                    "remarks": remarks,
                    "result": execution.result,
                    "executed_at": execution.executed_at.isoformat(),
                    "executor_name": executor_name
                }
            }
        else:
            # 没有执行记录，返回空备注
            return {
                "code": 200,
                "message": "无执行记录",
                "data": {
                    "remarks": "",
                    "result": None,
                    "executed_at": None,
                    "executor_name": None
                }
            }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/latest-version-info")
def get_latest_version_info(
    test_plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定测试计划中最近一次填写的版本信息
    
    用于自动填充：同一计划内，用户填写一次后，后续用例自动带入
    """
    try:
        execution = db.query(TestExecution).filter(
            TestExecution.test_plan_id == test_plan_id,
            TestExecution.version_info.isnot(None),
            TestExecution.version_info != ''
        ).order_by(TestExecution.executed_at.desc()).first()
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "version_info": execution.version_info if execution else ""
            }
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
