from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from database import get_db
from models import TestSuite, TestSuiteTestCase, User, TestCase
from auth import get_current_user, has_permission, is_super_admin
from utils.logger import log_operation, LogAction, LogModule
from urllib.parse import quote

router = APIRouter()


@router.get("")
def list_suites(
    req: Request,
    team_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(TestSuite)
    if team_id:
        query = query.filter(TestSuite.team_id == team_id)
    if keyword:
        query = query.filter(TestSuite.name.ilike(f"%{keyword}%"))
    
    total = query.count()
    suites = query.order_by(TestSuite.updated_at.desc(), TestSuite.id.desc()).offset((page - 1) * size).limit(size).all()
    
    suite_ids = [s.id for s in suites]
    
    # 批量查询用例数
    case_counts = {}
    if suite_ids:
        rows = db.query(
            TestSuiteTestCase.test_suite_id,
            func.count(TestSuiteTestCase.id)
        ).filter(
            TestSuiteTestCase.test_suite_id.in_(suite_ids)
        ).group_by(TestSuiteTestCase.test_suite_id).all()
        case_counts = dict(rows)
    
    # 批量查询创建人
    creator_ids = list(set(s.created_by for s in suites if s.created_by))
    creators = {}
    if creator_ids:
        users = db.query(User).filter(User.id.in_(creator_ids)).all()
        creators = {u.id: u.username for u in users}
    
    records = []
    for s in suites:
        records.append({
            "id": s.id,
            "team_id": s.team_id,
            "name": s.name,
            "description": s.description,
            "created_by": s.created_by,
            "creator_name": creators.get(s.created_by, ""),
            "case_count": case_counts.get(s.id, 0),
            "created_at": s.created_at,
            "updated_at": s.updated_at
        })
    
    return {"code": 200, "message": "success", "data": {"records": records, "total": total}}


@router.post("")
async def create_suite(
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    body = await req.json()
    name = body.get("name", "").strip()
    team_id = body.get("team_id")
    description = body.get("description", "")
    test_case_ids = body.get("test_case_ids", [])
    
    if not name:
        raise HTTPException(status_code=400, detail="套件名称不能为空")
    if not team_id:
        raise HTTPException(status_code=400, detail="必须指定项目组")
    
    suite = TestSuite(
        team_id=team_id,
        name=name,
        description=description,
        created_by=current_user.id
    )
    db.add(suite)
    db.commit()
    db.refresh(suite)
    
    if test_case_ids:
        for tc_id in test_case_ids:
            db.add(TestSuiteTestCase(test_suite_id=suite.id, test_case_id=tc_id))
        db.commit()
    
    return {"code": 200, "message": "success", "data": {
        "id": suite.id, "name": suite.name, "case_count": len(test_case_ids)
    }}


@router.get("/{suite_id}")
def get_suite(
    suite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")
    
    # 获取关联用例ID
    links = db.query(TestSuiteTestCase).filter(TestSuiteTestCase.test_suite_id == suite_id).all()
    test_case_ids = [l.test_case_id for l in links]
    
    # 获取关联用例详情
    test_cases = []
    pending_count = 0
    if test_case_ids:
        from models import TestCase
        cases = db.query(TestCase).filter(TestCase.id.in_(test_case_ids)).all()
        # 获取用例创建人
        case_creator_ids = list(set(c.created_by for c in cases if c.created_by))
        case_creators = {}
        if case_creator_ids:
            users = db.query(User).filter(User.id.in_(case_creator_ids)).all()
            case_creators = {u.id: u.username for u in users}
        
        for c in cases:
            if c.status == 'PENDING':
                pending_count += 1
            test_cases.append({
                "id": c.id,
                "case_number": c.case_number,
                "name": c.name,
                "module": c.module,
                "sub_module": getattr(c, 'sub_module', None),
                "level": c.level,
                "status": c.status,
                "precondition": c.precondition,
                "steps": c.steps,
                "expected_result": c.expected_result,
                "creator_name": case_creators.get(c.created_by, ""),
            })
    
    creator = db.query(User).filter(User.id == suite.created_by).first() if suite.created_by else None
    
    return {"code": 200, "message": "success", "data": {
        "id": suite.id,
        "team_id": suite.team_id,
        "name": suite.name,
        "description": suite.description,
        "created_by": suite.created_by,
        "creator_name": creator.username if creator else "",
        "test_case_ids": test_case_ids,
        "test_cases": test_cases,
        "case_count": len(test_case_ids),
        "pending_count": pending_count,
        "created_at": suite.created_at,
        "updated_at": suite.updated_at
    }}


@router.put("/{suite_id}")
async def update_suite(
    req: Request,
    suite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")
    
    body = await req.json()
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="套件名称不能为空")
    
    suite.name = name
    suite.description = body.get("description", "")
    
    # 更新关联用例
    if "test_case_ids" in body:
        db.query(TestSuiteTestCase).filter(TestSuiteTestCase.test_suite_id == suite_id).delete()
        for tc_id in body["test_case_ids"]:
            db.add(TestSuiteTestCase(test_suite_id=suite_id, test_case_id=tc_id))
    
    db.commit()
    db.refresh(suite)
    
    case_count = db.query(TestSuiteTestCase).filter(TestSuiteTestCase.test_suite_id == suite_id).count()
    
    return {"code": 200, "message": "success", "data": {
        "id": suite.id, "name": suite.name, "case_count": case_count
    }}


@router.delete("/{suite_id}/cases/{case_id}")
def unlink_case(
    suite_id: int,
    case_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")
    
    link = db.query(TestSuiteTestCase).filter(
        TestSuiteTestCase.test_suite_id == suite_id,
        TestSuiteTestCase.test_case_id == case_id
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="该用例未关联到此套件")
    
    db.delete(link)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.TESTCASES,
        action=LogAction.REMOVE,
        description=f"从测试套件 {suite.name}（ID: {suite_id}）移除用例（ID: {case_id}）",
        request=req
    )
    
    return {"code": 200, "message": "success"}


@router.delete("/{suite_id}")
def delete_suite(
    suite_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")
    
    suite_name = suite.name
    db.query(TestSuiteTestCase).filter(TestSuiteTestCase.test_suite_id == suite_id).delete()
    db.delete(suite)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.TESTCASES,
        action=LogAction.DELETE,
        description=f"删除测试套件：{suite_name}（ID: {suite_id}）",
        request=req
    )
    
    return {"code": 200, "message": "success"}


@router.get("/{suite_id}/export/excel")
def export_suite_excel(
    suite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出测试套件为Excel格式，包含汇总页和每个主模块独立Sheet"""
    # 权限检查
    if not is_super_admin(current_user) and not has_permission(current_user, db, 'testcases.export'):
        raise HTTPException(status_code=403, detail="您没有导出测试用例的权限")

    from utils.suite_excel import generate_suite_excel_stream
    from utils.module_sort import get_module_sort_map
    from utils.testcase_utils import parse_steps_and_expected

    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")

    # 获取关联用例
    links = db.query(TestSuiteTestCase).filter(
        TestSuiteTestCase.test_suite_id == suite_id
    ).all()
    case_ids = [l.test_case_id for l in links]

    if not case_ids:
        raise HTTPException(status_code=400, detail="套件中没有用例，无法导出")

    cases = db.query(TestCase).filter(TestCase.id.in_(case_ids)).all()

    # 收集所有涉及的项目ID，用于模块排序
    project_ids = list(set(c.primary_project_id for c in cases if c.primary_project_id))
    sort_map = get_module_sort_map(db, project_ids) if project_ids else {}

    # 按主模块分组（与报告逻辑一致：取 '/' 前的部分）
    module_cases_map = {}
    for c in cases:
        main_module = (c.module or "未分类").split('/')[0].strip()
        if main_module not in module_cases_map:
            module_cases_map[main_module] = []
        steps_list, expected_list = parse_steps_and_expected(c.steps, c.expected_result)
        module_cases_map[main_module].append({
            "case_number": c.case_number,
            "module": c.module or "",
            "sub_module": getattr(c, 'sub_module', '') or "",
            "name": c.name,
            "precondition": c.precondition or "",
            "steps": "\n".join(steps_list),
            "expected_result": "\n".join(expected_list),
            "level": c.level or "",
            "remarks": c.remarks or "",
        })

    # 排序主模块（使用模块排序工具，与报告一致）
    sorted_modules = sorted(
        module_cases_map.keys(),
        key=lambda m: sort_map.get(m, '9999999999')
    )

    # 每个模块内的用例按 case_number 排序
    for mod in sorted_modules:
        module_cases_map[mod].sort(key=lambda x: x.get('case_number', ''))

    # 生成Excel
    output = generate_suite_excel_stream(suite.name, module_cases_map, sorted_modules)

    filename = f"{suite.name}.xlsx"
    encoded_filename = quote(filename)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )
