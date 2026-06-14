"""
进度统计API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from models import User
from services import ProgressService
from schemas import ExecutionProgressSave

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/testplans/{testplan_id}/statistics")
def get_progress_statistics(
    testplan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取测试计划的进度统计
    
    返回8个统计维度：
    - total: 总用例数
    - executed: 已执行数
    - not_executed: 未执行数
    - passed: 通过数
    - failed: 失败数
    - blocked: 阻塞数
    - skipped: 跳过数
    - progress_percentage: 执行进度百分比
    """
    try:
        stats = ProgressService.calculate_progress_statistics(testplan_id, db)
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/execution-progress")
def save_execution_progress(
    progress_data: ExecutionProgressSave,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    保存执行进度
    
    用于记录用户在测试执行过程中的位置，下次进入时从上次位置继续
    """
    try:
        progress = ProgressService.save_execution_progress(
            testplan_id=progress_data.testplan_id,
            user_id=current_user.id,
            current_testcase_id=progress_data.current_testcase_id,
            current_index=progress_data.current_index,
            db=db,
            sort_order=progress_data.sort_order
        )
        
        return {
            "code": 200,
            "message": "保存成功",
            "data": {
                "testplan_id": progress.testplan_id,
                "user_id": progress.user_id,
                "current_testcase_id": progress.current_testcase_id,
                "current_index": progress.current_index,
                "last_access_time": progress.last_access_time.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/testplans/{testplan_id}/execution-progress")
def get_execution_progress(
    testplan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取执行进度
    """
    try:
        progress = ProgressService.get_execution_progress(testplan_id, current_user.id, db)
        
        if not progress:
            return {
                "code": 200,
                "message": "无进度记录",
                "data": None
            }
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "testplan_id": progress.testplan_id,
                "user_id": progress.user_id,
                "current_testcase_id": progress.current_testcase_id,
                "current_index": progress.current_index,
                "sort_order": progress.sort_order,
                "last_access_time": progress.last_access_time.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/testplans/{testplan_id}/testcases/{testcase_id}/history")
def get_execution_history(
    testplan_id: int,
    testcase_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取测试用例的执行历史
    """
    try:
        executions = ProgressService.get_execution_history(
            testplan_id=testplan_id,
            testcase_id=testcase_id,
            db=db,
            limit=limit
        )
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": [
                {
                    "id": exe.id,
                    "result": exe.result,
                    "executor_id": exe.executor_id,
                    "remarks": exe.remarks,
                    "actual_result": exe.actual_result,
                    "failure_reason": exe.failure_reason,
                    "executed_at": exe.executed_at.isoformat()
                }
                for exe in executions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
