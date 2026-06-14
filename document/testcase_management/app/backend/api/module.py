from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from database import get_db
from models import Module, TestCase, Project, TestCaseZmindLink
from schemas import ModuleCreate, ModuleUpdate, ModuleResponse, ModuleTreeNode, ModuleSortRequest
from auth import get_current_user, has_permission, is_super_admin
from utils.logger import log_operation, LogAction, LogModule

router = APIRouter()

# PR排序：关闭状态排最后，其余按严重程度 Blocker>Critical>Major>Minor>Enhancement
# 关闭状态包含：Closed、Suspended、Pending、Device Issue、App Issue
from utils.constants import CLOSED_STATUSES as _CLOSED_STATUSES

_SEVERITY_ORDER = {'Blocker': 0, 'Critical': 1, 'Major': 2, 'Minor': 3, 'Enhancement': 4}

def _sort_pr_results(result):
    def sort_key(item):
        status = item.get('zmind_issue_status') or ''
        is_closed = 1 if status in _CLOSED_STATUSES else 0
        severity = _SEVERITY_ORDER.get(item.get('zmind_issue_severity') or '', 99)
        return (is_closed, severity)
    result.sort(key=sort_key)


@router.get("/modules")
def get_modules(
    project_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取项目的所有模块"""
    modules = db.query(Module).filter(
        Module.project_id == project_id
    ).order_by(Module.sort_order, Module.id).all()
    
    # 转换为字典列表
    modules_data = []
    for module in modules:
        modules_data.append({
            "id": module.id,
            "project_id": module.project_id,
            "name": module.name,
            "tag": module.tag,
            "parent_id": module.parent_id,
            "sort_order": module.sort_order,
            "created_at": module.created_at.isoformat() if module.created_at else None,
            "updated_at": module.updated_at.isoformat() if module.updated_at else None
        })
    
    return {"code": 200, "message": "success", "data": modules_data}


@router.get("/modules/tree")
def get_module_tree(
    project_id: int = None,
    project_ids: str = None,  # 新增：支持多个项目ID，逗号分隔
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取项目的模块树结构(包含用例数量)"""
    # 解析项目ID列表
    pid_list = []
    if project_ids:
        pid_list = [int(pid.strip()) for pid in project_ids.split(',') if pid.strip().isdigit()]
    elif project_id:
        pid_list = [project_id]
    
    if not pid_list:
        return {"code": 200, "message": "success", "data": []}
    
    # 获取所有模块（合并多个项目的模块）
    modules = db.query(Module).filter(
        Module.project_id.in_(pid_list)
    ).order_by(Module.sort_order, Module.id).all()
    
    # 预计算所有用例数量（按项目ID+模块路径分组）
    case_counts = {}
    case_count_query = db.query(
        TestCase.primary_project_id,
        TestCase.module,
        func.count(TestCase.id).label('count')
    ).filter(
        TestCase.primary_project_id.in_(pid_list)
    ).group_by(TestCase.primary_project_id, TestCase.module).all()
    for row in case_count_query:
        key = (row.primary_project_id, row.module)
        case_counts[key] = row.count
    
    # 构建树结构
    # 如果只有一个项目，返回真实的模块ID（用于模块管理的增删改）
    single_project = len(pid_list) == 1
    
    if single_project:
        # 单项目模式：递归构建多级树，返回真实ID
        module_map = {m.id: m for m in modules}
        project_id = pid_list[0]  # 单项目模式，project_id固定
        
        def build_node(module):
            """递归构建模块节点"""
            children_modules = sorted(
                [m for m in modules if m.parent_id == module.id],
                key=lambda m: (m.sort_order or 0, m.id)
            )
            # 构建完整路径
            path = get_module_path(module, module_map)
            # 使用预计算的用例数量（key格式: (project_id, module_path)）
            count = case_counts.get((project_id, path), 0)
            
            # 递归计算子模块的用例数量（累加）
            child_count = 0
            children = []
            for child in children_modules:
                child_node = build_node(child)
                child_count += child_node.get('count', 0)
                children.append(child_node)
            
            # 主模块的用例数量 = 自己 + 所有子模块的用例数量
            total_count = count + child_count
            
            return {
                "id": module.id,
                "name": module.name,
                "tag": module.tag if module.parent_id is None else None,  # 子模块不显示Tag
                "parent_id": module.parent_id,
                "sort_order": module.sort_order or 0,
                "requirement_link": module.requirement_link,
                "rd_owner": module.rd_owner if module.parent_id is None else None,  # 子模块不显示RD Owner
                "count": total_count,
                "path": path,
                "children": children
            }
        
        def get_module_path(module, module_map):
            """获取模块的完整路径"""
            parts = [module.name]
            current = module
            while current.parent_id and current.parent_id in module_map:
                current = module_map[current.parent_id]
                parts.insert(0, current.name)
            return '/'.join(parts)
        
        root_modules = sorted(
            [m for m in modules if m.parent_id is None],
            key=lambda m: (m.sort_order or 0, m.id)
        )
        tree = [build_node(m) for m in root_modules]
    else:
        # 多项目模式：每个用例库的模块树完全独立显示，不做合并
        # （不同库可以有相同Tag的模块，合并会导致数据混乱）
        
        # 按项目分组模块
        modules_by_project = {}
        for m in modules:
            if m.project_id not in modules_by_project:
                modules_by_project[m.project_id] = []
            modules_by_project[m.project_id].append(m)
        
        def get_module_path_mp(module, mod_map):
            """获取模块的完整路径"""
            parts = [module.name]
            current = module
            while current.parent_id and current.parent_id in mod_map:
                current = mod_map[current.parent_id]
                parts.insert(0, current.name)
            return '/'.join(parts)
        
        def build_node_mp(module, all_mods, mod_map, pid, path_prefix):
            """递归构建模块节点（多项目版本）"""
            children_modules = sorted(
                [m for m in all_mods if m.parent_id == module.id],
                key=lambda m: (m.sort_order or 0, m.id)
            )
            module_path = get_module_path_mp(module, mod_map)
            own_count = case_counts.get((pid, module_path), 0)
            
            # path 用 "pid:模块路径" 保证跨项目唯一
            unique_path = f"{path_prefix}/{module_path}"
            
            child_total = 0
            children = []
            for child in children_modules:
                child_node = build_node_mp(child, all_mods, mod_map, pid, path_prefix)
                child_total += child_node['count']
                children.append(child_node)
            
            return {
                "id": None,
                "name": module.name,
                "tag": module.tag,
                "parent_id": None,
                "sort_order": module.sort_order or 0,
                "requirement_link": module.requirement_link,
                "rd_owner": module.rd_owner,  # 主模块显示RD Owner
                "count": own_count + child_total,
                "path": unique_path,
                "children": children
            }
        
        # 每个项目分别构建完整递归树，直接拼接
        tree = []
        for pid, proj_mods in modules_by_project.items():
            mod_map = {m.id: m for m in proj_mods}
            path_prefix = f"p{pid}"
            roots = sorted(
                [m for m in proj_mods if m.parent_id is None],
                key=lambda m: (m.sort_order or 0, m.id)
            )
            for root_mod in roots:
                tree.append(build_node_mp(root_mod, proj_mods, mod_map, pid, path_prefix))
        
        # 按sort_order排序
        tree.sort(key=lambda x: x.get('sort_order', 0))
    
    # 统计选中项目的全部用例总数（包括未分配模块的用例）
    total_case_count = db.query(func.count(TestCase.id)).filter(
        TestCase.primary_project_id.in_(pid_list)
    ).scalar() or 0
    
    return {"code": 200, "message": "success", "data": tree, "total_count": total_case_count}


@router.get("/modules/flat")
def get_modules_flat(
    project_id: int = None,
    project_ids: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取模块的扁平列表，每个模块带完整路径（用于用例表单选择）"""
    pid_list = []
    if project_ids:
        pid_list = [int(pid.strip()) for pid in project_ids.split(',') if pid.strip().isdigit()]
    elif project_id:
        pid_list = [project_id]
    
    if not pid_list:
        return {"code": 200, "message": "success", "data": []}
    
    modules = db.query(Module).filter(
        Module.project_id.in_(pid_list)
    ).order_by(Module.sort_order, Module.id).all()
    
    module_map = {m.id: m for m in modules}
    
    def get_path(module):
        parts = [module.name]
        current = module
        while current.parent_id and current.parent_id in module_map:
            current = module_map[current.parent_id]
            parts.insert(0, current.name)
        return '/'.join(parts)
    
    result = []
    for m in modules:
        path = get_path(m)
        count = db.query(func.count(TestCase.id)).filter(
            TestCase.primary_project_id.in_(pid_list),
            TestCase.module == path
        ).scalar() or 0
        result.append({
            "path": path,
            "count": count
        })
    
    # 按路径排序
    result.sort(key=lambda x: x['path'])
    return {"code": 200, "message": "success", "data": result}


@router.post("/modules")
def create_module(
    module: ModuleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建模块"""
    # 检查同名模块
    existing = db.query(Module).filter(
        Module.project_id == module.project_id,
        Module.name == module.name,
        Module.parent_id == module.parent_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="模块名称已存在")
    
    # Tag唯一性校验（仅主模块可以设置Tag，子模块不显示Tag字段）
    if module.tag and module.parent_id is None:
        existing_tag = db.query(Module).filter(
            Module.project_id == module.project_id,
            Module.tag == module.tag,
            Module.parent_id.is_(None)
        ).first()
        if existing_tag:
            raise HTTPException(status_code=400, detail=f"模块Tag '{module.tag}' 已存在，请使用其他Tag")
    
    # 获取当前最大排序号
    max_sort = db.query(func.max(Module.sort_order)).filter(
        Module.project_id == module.project_id,
        Module.parent_id == module.parent_id
    ).scalar() or -1
    
    # 创建模块
    db_module = Module(
        project_id=module.project_id,
        name=module.name,
        tag=module.tag if module.parent_id is None else None,  # 只有主模块可以设置Tag
        parent_id=module.parent_id,
        sort_order=max_sort + 1,
        requirement_link=module.requirement_link,
        rd_owner=module.rd_owner if module.parent_id is None else None,  # 只有主模块可以设置RD Owner
        created_by=current_user.id if hasattr(current_user, 'id') else current_user.get("id")
    )
    
    db.add(db_module)
    db.commit()
    db.refresh(db_module)
    
    # 转换为字典
    module_data = {
        "id": db_module.id,
        "project_id": db_module.project_id,
        "name": db_module.name,
        "tag": db_module.tag,
        "parent_id": db_module.parent_id,
        "sort_order": db_module.sort_order,
        "requirement_link": db_module.requirement_link,
        "rd_owner": db_module.rd_owner,
        "created_at": db_module.created_at.isoformat() if db_module.created_at else None,
        "updated_at": db_module.updated_at.isoformat() if db_module.updated_at else None
    }
    
    return {"code": 200, "message": "创建成功", "data": module_data}


@router.put("/modules/{module_id}")
def update_module(
    module_id: int,
    module_update: ModuleUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新模块"""
    db_module = db.query(Module).filter(Module.id == module_id).first()
    
    if not db_module:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    # 更新名称
    if module_update.name is not None:
        # 检查同名
        existing = db.query(Module).filter(
            Module.project_id == db_module.project_id,
            Module.name == module_update.name,
            Module.parent_id == db_module.parent_id,
            Module.id != module_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="模块名称已存在")
        
        # 计算旧路径和新路径，更新测试用例中的module字段
        all_modules = db.query(Module).filter(
            Module.project_id == db_module.project_id
        ).all()
        module_map = {m.id: m for m in all_modules}
        
        def get_path(mod):
            parts = [mod.name]
            current = mod
            while current.parent_id and current.parent_id in module_map:
                current = module_map[current.parent_id]
                parts.insert(0, current.name)
            return '/'.join(parts)
        
        old_path = get_path(db_module)
        # 临时修改名称计算新路径
        old_name = db_module.name
        db_module.name = module_update.name
        module_map[db_module.id] = db_module
        new_path = get_path(db_module)
        
        # 更新所有以旧路径开头的用例（包括子模块下的用例）
        # 精确匹配当前模块路径的用例
        testcases = db.query(TestCase).filter(
            TestCase.primary_project_id == db_module.project_id,
            TestCase.module == old_path
        ).all()
        for tc in testcases:
            tc.module = new_path
        
        # 匹配以旧路径为前缀的子模块用例（旧路径/...）
        prefix = old_path + '/'
        child_testcases = db.query(TestCase).filter(
            TestCase.primary_project_id == db_module.project_id,
            TestCase.module.like(prefix + '%')
        ).all()
        for tc in child_testcases:
            tc.module = new_path + '/' + tc.module[len(prefix):]
    
    # 更新排序
    if module_update.sort_order is not None:
        db_module.sort_order = module_update.sort_order
    
    # 更新Tag（仅主模块可以设置Tag）
    if module_update.tag is not None and db_module.parent_id is None:
        # 检查用户是否有编辑模块Tag的权限
        if not is_super_admin(current_user) and not has_permission(current_user, db, 'testcases.editModuleTag'):
            raise HTTPException(status_code=403, detail="您没有编辑模块Tag的权限")
        
        # Tag唯一性校验
        existing_tag = db.query(Module).filter(
            Module.project_id == db_module.project_id,
            Module.tag == module_update.tag,
            Module.id != module_id,
            Module.parent_id.is_(None)
        ).first()
        if existing_tag:
            raise HTTPException(status_code=400, detail=f"模块Tag '{module_update.tag}' 已存在，请使用其他Tag")
        db_module.tag = module_update.tag
    
    # 更新原始需求链接
    if module_update.requirement_link is not None:
        db_module.requirement_link = module_update.requirement_link if module_update.requirement_link else None
    
    # 更新RD Owner（只有主模块可以设置）
    if module_update.rd_owner is not None and db_module.parent_id is None:
        db_module.rd_owner = module_update.rd_owner if module_update.rd_owner else None
    
    db.commit()
    db.refresh(db_module)
    
    # 转换为字典
    module_data = {
        "id": db_module.id,
        "project_id": db_module.project_id,
        "name": db_module.name,
        "tag": db_module.tag,
        "parent_id": db_module.parent_id,
        "sort_order": db_module.sort_order,
        "requirement_link": db_module.requirement_link,
        "rd_owner": db_module.rd_owner,
        "created_at": db_module.created_at.isoformat() if db_module.created_at else None,
        "updated_at": db_module.updated_at.isoformat() if db_module.updated_at else None
    }
    
    return {"code": 200, "message": "更新成功", "data": module_data}


@router.delete("/modules/{module_id}")
def delete_module(
    module_id: int,
    req: Request = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除模块"""
    db_module = db.query(Module).filter(Module.id == module_id).first()
    
    if not db_module:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    # 检查是否有子模块
    children = db.query(Module).filter(Module.parent_id == module_id).count()
    
    # 计算模块完整路径
    all_modules = db.query(Module).filter(
        Module.project_id == db_module.project_id
    ).all()
    module_map = {m.id: m for m in all_modules}
    
    def get_path(mod):
        parts = [mod.name]
        current = mod
        while current.parent_id and current.parent_id in module_map:
            current = module_map[current.parent_id]
            parts.insert(0, current.name)
        return '/'.join(parts)
    
    # 超管删除逻辑：允许删除带有子模块的主模块，整个模块树连同用例一起删除
    if is_super_admin(current_user) and db_module.parent_id is None and children > 0:
        # 递归获取所有子孙模块ID
        def get_all_child_ids(parent_id):
            child_ids = [parent_id]
            for m in all_modules:
                if m.parent_id == parent_id:
                    child_ids.extend(get_all_child_ids(m.id))
            return child_ids
        
        all_module_ids = get_all_child_ids(module_id)
        
        # 获取所有要删除的模块路径
        paths_to_delete = set()
        for mid in all_module_ids:
            mod = module_map.get(mid)
            if mod:
                paths_to_delete.add(get_path(mod))
        
        # 删除这些模块下的所有用例
        for path in paths_to_delete:
            db.query(TestCase).filter(
                TestCase.primary_project_id == db_module.project_id,
                or_(
                    TestCase.module == path,
                    TestCase.module.like(f"{path}/%")
                )
            ).delete(synchronize_session=False)
        
        # 删除所有子模块
        db.query(Module).filter(Module.id.in_(all_module_ids)).delete(synchronize_session=False)
        db.commit()
        
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.TESTCASES,
            action=LogAction.DELETE,
            description=f"删除模块（含子模块及用例）：{module_path}（ID: {module_id}，共 {len(all_module_ids)} 个模块）",
            request=req
        )
        
        return {"code": 200, "message": "删除成功（含子模块及用例）", "data": None}
    
    # 原有逻辑：普通用户或有子模块时不能删除
    if children > 0:
        raise HTTPException(status_code=400, detail="该模块下还有子模块,无法删除")
    
    module_path = get_path(db_module)
    case_count = db.query(func.count(TestCase.id)).filter(
        TestCase.primary_project_id == db_module.project_id,
        TestCase.module == module_path
    ).scalar()
    
    if case_count > 0:
        raise HTTPException(status_code=400, detail="该模块下还有用例,无法删除")
    
    db.delete(db_module)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.TESTCASES,
        action=LogAction.DELETE,
        description=f"删除模块：{module_path}（ID: {module_id}）",
        request=req
    )
    
    return {"code": 200, "message": "删除成功", "data": None}


@router.post("/modules/sort")
def sort_modules(
    sort_request: ModuleSortRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """批量更新模块排序"""
    for item in sort_request.module_orders:
        module_id = item.get("id")
        sort_order = item.get("sort_order")
        
        if module_id and sort_order is not None:
            db.query(Module).filter(Module.id == module_id).update(
                {"sort_order": sort_order}
            )
    
    db.commit()
    
    return {"code": 200, "message": "排序更新成功", "data": None}


@router.get("/modules/{module_id}/pr-links")
def get_module_pr_links(
    module_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取模块下所有用例关联的PR列表"""
    db_module = db.query(Module).filter(Module.id == module_id).first()
    if not db_module:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    # 构建模块路径（只沿父链向上查找，不加载全部模块）
    def get_path(mod):
        parts = [mod.name]
        current = mod
        while current.parent_id:
            parent = db.query(Module.id, Module.name, Module.parent_id).filter(Module.id == current.parent_id).first()
            if not parent:
                break
            parts.insert(0, parent.name)
            current = parent
        return '/'.join(parts)
    
    module_path = get_path(db_module)
    
    # 查找该模块及子模块下的所有用例ID
    case_ids = db.query(TestCase.id).filter(
        TestCase.primary_project_id == db_module.project_id,
        or_(
            TestCase.module == module_path,
            TestCase.module.like(module_path + '/%')
        )
    ).all()
    case_id_list = [c[0] for c in case_ids]
    
    if not case_id_list:
        return {"code": 200, "message": "success", "data": []}
    
    # 查找这些用例关联的PR
    links = db.query(TestCaseZmindLink).filter(
        TestCaseZmindLink.test_case_id.in_(case_id_list)
    ).order_by(TestCaseZmindLink.created_at.desc()).all()
    
    # 构建返回数据，包含用例信息
    result = []
    # 批量获取用例信息
    cases_map = {}
    if case_id_list:
        cases = db.query(TestCase.id, TestCase.case_number, TestCase.name, TestCase.module).filter(
            TestCase.id.in_(case_id_list)
        ).all()
        cases_map = {c[0]: {"case_number": c[1], "case_name": c[2], "module": c[3]} for c in cases}
    
    for link in links:
        case_info = cases_map.get(link.test_case_id, {})
        result.append({
            "id": link.id,
            "test_case_id": link.test_case_id,
            "case_number": case_info.get("case_number", ""),
            "case_name": case_info.get("case_name", ""),
            "case_module": case_info.get("module", ""),
            "zmind_issue_id": link.zmind_issue_id,
            "zmind_issue_subject": link.zmind_issue_subject,
            "zmind_issue_status": link.zmind_issue_status,
            "zmind_issue_severity": link.zmind_issue_severity,
            "test_plan_id": link.test_plan_id,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "created_by_name": link.created_by_name
        })
    
    _sort_pr_results(result)
    return {"code": 200, "message": "success", "data": result}


@router.get("/projects/{project_id}/all-pr-links")
def get_project_all_pr_links(
    project_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取整个用例库下所有用例关联的PR列表"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="用例库不存在")
    
    case_ids = db.query(TestCase.id).filter(
        TestCase.primary_project_id == project_id
    ).all()
    case_id_list = [c[0] for c in case_ids]
    
    if not case_id_list:
        return {"code": 200, "message": "success", "data": []}
    
    links = db.query(TestCaseZmindLink).filter(
        TestCaseZmindLink.test_case_id.in_(case_id_list)
    ).order_by(TestCaseZmindLink.created_at.desc()).all()
    
    cases_map = {}
    if case_id_list:
        cases = db.query(TestCase.id, TestCase.case_number, TestCase.name, TestCase.module).filter(
            TestCase.id.in_(case_id_list)
        ).all()
        cases_map = {c[0]: {"case_number": c[1], "case_name": c[2], "module": c[3]} for c in cases}
    
    result = []
    for link in links:
        case_info = cases_map.get(link.test_case_id, {})
        result.append({
            "id": link.id,
            "test_case_id": link.test_case_id,
            "case_number": case_info.get("case_number", ""),
            "case_name": case_info.get("case_name", ""),
            "case_module": case_info.get("module", ""),
            "zmind_issue_id": link.zmind_issue_id,
            "zmind_issue_subject": link.zmind_issue_subject,
            "zmind_issue_status": link.zmind_issue_status,
            "zmind_issue_severity": link.zmind_issue_severity,
            "test_plan_id": link.test_plan_id,
            "created_at": link.created_at.isoformat() if link.created_at else None,
            "created_by_name": link.created_by_name
        })
    
    _sort_pr_results(result)
    return {"code": 200, "message": "success", "data": result}
