from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from models import (
    Project, User, UserProject, TestCase, TestPlan, TestExecution, Report, 
    TestCaseZmindLink, TestCaseProject, TeamProject, Team, UserTeam,
    TestPlanTestCase, TestPlanExecutor, TestCaseAttachment, TestCaseHistory,
    Module, ReviewPlan, ReviewPlanTestCase, TestExecutionProgress, Comment
)
from schemas import ProjectCreate
from auth import get_current_user, has_permission, is_super_admin
from utils.permissions import get_user_project_ids
from utils.logger import log_operation, LogAction, LogModule
from typing import Optional, List

router = APIRouter()

def build_project_path(db: Session, parent_id: Optional[int], project_id: int) -> str:
    """构建项目路径"""
    if not parent_id:
        return str(project_id)
    
    parent = db.query(Project).filter(Project.id == parent_id).first()
    if not parent:
        return str(project_id)
    
    return f"{parent.path}/{project_id}"

def get_project_tree_recursive(db: Session, projects: List[Project], parent_id: Optional[int] = None) -> List[dict]:
    """递归构建项目树"""
    result = []
    for project in projects:
        if project.parent_id == parent_id:
            project_dict = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "level": project.level,
                "project_type": project.project_type,
                "parent_id": project.parent_id,
                "group_name": project.group_name,
                "category_name": project.category_name,
                "status": project.status,
                "created_at": project.created_at,
                "children": get_project_tree_recursive(db, projects, project.id)
            }
            result.append(project_dict)
    return result

@router.get("/tree")
def get_project_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目树形结构"""
    project_ids = get_user_project_ids(current_user, db)
    
    if project_ids is None:
        # 超级管理员，获取所有项目
        projects = db.query(Project).filter(Project.status == 1).order_by(Project.level, Project.id).all()
    elif not project_ids:
        return {"code": 200, "message": "success", "data": []}
    else:
        # 获取用户有权限的项目
        authorized_projects = db.query(Project).filter(
            Project.id.in_(project_ids),
            Project.status == 1
        ).all()
        
        # 收集所有需要显示的项目ID（包括父节点）
        all_project_ids = set(project_ids)
        for project in authorized_projects:
            # 添加所有父节点
            if project.parent_id:
                parent = db.query(Project).filter(Project.id == project.parent_id).first()
                while parent:
                    all_project_ids.add(parent.id)
                    if parent.parent_id:
                        parent = db.query(Project).filter(Project.id == parent.parent_id).first()
                    else:
                        break
        
        # 获取所有需要显示的项目
        projects = db.query(Project).filter(
            Project.id.in_(all_project_ids),
            Project.status == 1
        ).order_by(Project.level, Project.id).all()
    
    tree = get_project_tree_recursive(db, projects, None)
    
    return {
        "code": 200,
        "message": "success",
        "data": tree
    }

@router.get("")
def list_projects(
    page: int = 1,
    size: int = 10,
    level: Optional[int] = None,
    parent_id: Optional[int] = None,
    project_type: Optional[str] = None,
    team_id: Optional[int] = None,
    keyword: Optional[str] = None,
    id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目列表（支持筛选）"""
    project_ids = get_user_project_ids(current_user, db)
    
    query = db.query(Project)
    
    # 条件过滤（精确查询优先）
    if id is not None:
        query = query.filter(Project.id == id)
    elif project_ids is not None and project_ids:
        query = query.filter(Project.id.in_(project_ids))
    elif project_ids is not None and not project_ids:
        return {
            "code": 200,
            "message": "success",
            "data": {"records": [], "total": 0}
        }
    
    if level is not None:
        query = query.filter(Project.level == level)
    if parent_id is not None:
        query = query.filter(Project.parent_id == parent_id)
    if project_type:
        query = query.filter(Project.project_type == project_type)
    
    # 按项目组筛选
    if team_id:
        team_project_ids = [tp.project_id for tp in db.query(TeamProject.project_id).filter(TeamProject.team_id == team_id).all()]
        if team_project_ids:
            query = query.filter(Project.id.in_(team_project_ids))
        else:
            return {
                "code": 200,
                "message": "success",
                "data": {"records": [], "total": 0}
            }
    
    # 关键词搜索
    if keyword and keyword.strip():
        search_pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Project.name.ilike(search_pattern),
                Project.description.ilike(search_pattern)
            )
        )
    elif level is None and parent_id is None and project_type is None and team_id is None and (keyword is None or not keyword.strip()):
        # 如果没有任何筛选条件且keyword为空，检查是否需要按ID精确查询
        pass  # 不做特殊处理
    
    total = query.count()
    projects = query.order_by(Project.id.desc()).offset((page - 1) * size).limit(size).all()
    
    result = []
    for project in projects:
        # 获取该用例库已授权的项目组
        team_projects = db.query(TeamProject).filter(TeamProject.project_id == project.id).all()
        team_ids = [tp.team_id for tp in team_projects]
        authorized_teams = []
        if team_ids:
            teams = db.query(Team).filter(Team.id.in_(team_ids)).all()
            authorized_teams = [{"id": t.id, "name": t.name} for t in teams]
        
        project_dict = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "tag": project.tag,
            "level": project.level,
            "project_type": project.project_type,
            "parent_id": project.parent_id,
            "path": project.path,
            "group_name": project.group_name,
            "category_name": project.category_name,
            "status": project.status,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "created_by": project.created_by,
            "creator_name": None,
            "authorized_teams": authorized_teams
        }
        
        if project.created_by:
            creator = db.query(User).filter(User.id == project.created_by).first()
            if creator:
                project_dict["creator_name"] = creator.username
        
        result.append(project_dict)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "records": result,
            "total": total
        }
    }

@router.get("/{project_id}/children")
def get_project_children(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目的子项目"""
    children = db.query(Project).filter(
        Project.parent_id == project_id,
        Project.status == 1
    ).all()
    
    result = []
    for child in children:
        result.append({
            "id": child.id,
            "name": child.name,
            "description": child.description,
            "level": child.level,
            "project_type": child.project_type,
            "status": child.status
        })
    
    return {
        "code": 200,
        "message": "success",
        "data": result
    }

@router.post("")
def create_project(
    project: ProjectCreate,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建项目"""
    if not project.name or not project.name.strip():
        raise HTTPException(status_code=400, detail="项目名称不能为空")
    
    # 用例库Tag必填校验
    if not project.tag or not project.tag.strip():
        raise HTTPException(status_code=400, detail="用例库Tag不能为空，用于生成用例编号")
    
    # Tag唯一性校验
    project.tag = project.tag.strip().upper()
    existing = db.query(Project).filter(Project.tag == project.tag).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"用例库Tag '{project.tag}' 已存在，请使用其他Tag")
    
    # 如果有父项目，获取父项目信息
    group_name = project.group_name
    category_name = project.category_name
    
    if project.parent_id:
        parent = db.query(Project).filter(Project.id == project.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="父项目不存在")
        
        # 自动设置层级
        if not project.level:
            project.level = parent.level + 1
        
        # 继承小组和分类信息
        if parent.project_type == "GROUP":
            group_name = parent.name
        elif parent.project_type == "CATEGORY":
            group_name = parent.group_name
            category_name = parent.name
        else:
            group_name = parent.group_name
            category_name = parent.category_name
    
    # 创建项目
    db_project = Project(
        name=project.name,
        description=project.description,
        tag=project.tag,
        parent_id=project.parent_id,
        level=project.level or 3,
        project_type=project.project_type or "PRODUCT",
        group_name=group_name,
        category_name=category_name,
        status=project.status or 1,
        created_by=current_user.id
    )
    
    db.add(db_project)
    db.flush()  # 获取ID但不提交
    
    # 构建路径
    db_project.path = build_project_path(db, project.parent_id, db_project.id)
    
    db.commit()
    db.refresh(db_project)
    
    # 自动为创建者添加项目关联
    from datetime import datetime
    user_project = UserProject(
        user_id=current_user.id,
        project_id=db_project.id,
        created_at=datetime.now()
    )
    db.add(user_project)
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.PROJECTS,
        action=LogAction.CREATE,
        description=f"创建项目：{db_project.name}（类型: {db_project.project_type}, ID: {db_project.id}）",
        request=req
    )
    
    return {
        "code": 200, 
        "message": "success", 
        "data": {
            "id": db_project.id,
            "name": db_project.name,
            "description": db_project.description,
            "status": db_project.status,
            "created_at": db_project.created_at
        }
    }

@router.put("/{project_id}")
def update_project(
    project_id: int,
    project: ProjectCreate,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新项目"""
    if not project.name or not project.name.strip():
        raise HTTPException(status_code=400, detail="项目名称不能为空")
    
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # Tag必填校验
    if not project.tag or not project.tag.strip():
        raise HTTPException(status_code=400, detail="用例库Tag不能为空，用于生成用例编号")
    
    # Tag唯一性校验和权限检查
    project.tag = project.tag.strip().upper()
    if project.tag != db_project.tag:
        # 检查用户是否有编辑Tag的权限
        if not is_super_admin(current_user) and not has_permission(current_user, db, 'projects.editTag'):
            raise HTTPException(status_code=403, detail="您没有编辑用例库Tag的权限")
        
        existing = db.query(Project).filter(
            Project.tag == project.tag,
            Project.id != project_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"用例库Tag '{project.tag}' 已存在，请使用其他Tag")
    
    old_name = db_project.name
    changes = []
    
    # 记录变更
    if project.name != db_project.name:
        changes.append(f"项目名: {db_project.name} → {project.name}")
    if project.description != db_project.description:
        old_desc = db_project.description[:30] + "..." if db_project.description and len(db_project.description) > 30 else (db_project.description or "(空)")
        new_desc = project.description[:30] + "..." if project.description and len(project.description) > 30 else (project.description or "(空)")
        changes.append(f"描述: {old_desc} → {new_desc}")
    if project.tag != db_project.tag:
        old_tag = db_project.tag or "(未设置)"
        new_tag = project.tag or "(未设置)"
        changes.append(f"Tag: {old_tag} → {new_tag}")
    
    # 更新字段
    for key, value in project.dict(exclude_unset=True).items():
        if value is not None:
            setattr(db_project, key, value)
    
    # 如果父项目改变，重新构建路径
    if project.parent_id and project.parent_id != db_project.parent_id:
        db_project.path = build_project_path(db, project.parent_id, project_id)
    
    db.commit()
    db.refresh(db_project)
    
    if changes:
        change_detail = "；".join(changes)
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.PROJECTS,
            action=LogAction.UPDATE,
            description=f"更新项目：{old_name}（ID: {project_id}，{change_detail}）",
            request=req
        )
    
    return {"code": 200, "message": "success", "data": db_project}

@router.patch("/{project_id}/status")
def toggle_project_status(
    project_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换项目状态"""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db_project.status = 0 if db_project.status == 1 else 1
    db.commit()
    db.refresh(db_project)
    
    status_text = "启用" if db_project.status == 1 else "禁用"
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.PROJECTS,
        action=LogAction.UPDATE,
        description=f"{status_text}项目：{db_project.name}",
        request=req
    )
    
    return {"code": 200, "message": f"项目已{status_text}", "data": db_project}

@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除项目（需先删除关联的测试计划）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查是否有子项目
    children_count = db.query(Project).filter(Project.parent_id == project_id).count()
    if children_count > 0:
        raise HTTPException(status_code=400, detail=f"该项目下还有{children_count}个子项目，请先删除子项目")
    
    # 检查是否有关联的测试计划
    test_plan_count = db.query(TestPlan).filter(TestPlan.project_id == project_id).count()
    if test_plan_count > 0:
        plan_names = [
            tp.name for tp in 
            db.query(TestPlan.name).filter(TestPlan.project_id == project_id).limit(5).all()
        ]
        names_str = "、".join(plan_names)
        if test_plan_count > 5:
            names_str += f" 等共 {test_plan_count} 个"
        raise HTTPException(
            status_code=400, 
            detail=f"该用例库下还有 {test_plan_count} 个测试计划（{names_str}），请先删除测试计划后再删除用例库"
        )
    
    project_name = project.name
    
    try:
        # 1. 获取项目下的所有测试用例ID（通过test_case_projects关联）
        test_case_ids = [
            tcp.test_case_id for tcp in 
            db.query(TestCaseProject.test_case_id).filter(TestCaseProject.project_id == project_id).all()
        ]
        
        # 2. 获取项目下的所有测试计划ID（此时应为空，因为上面已检查）
        test_plan_ids = [tp.id for tp in db.query(TestPlan.id).filter(TestPlan.project_id == project_id).all()]
        
        # 3. 清理测试计划相关数据
        if test_plan_ids:
            db.query(TestExecutionProgress).filter(TestExecutionProgress.testplan_id.in_(test_plan_ids)).delete(synchronize_session=False)
            db.query(TestExecution).filter(TestExecution.test_plan_id.in_(test_plan_ids)).delete(synchronize_session=False)
            db.query(Report).filter(Report.test_plan_id.in_(test_plan_ids)).delete(synchronize_session=False)
            db.query(TestPlanTestCase).filter(TestPlanTestCase.test_plan_id.in_(test_plan_ids)).delete(synchronize_session=False)
            db.query(TestPlanExecutor).filter(TestPlanExecutor.test_plan_id.in_(test_plan_ids)).delete(synchronize_session=False)
            db.query(TestCaseZmindLink).filter(TestCaseZmindLink.test_plan_id.in_(test_plan_ids)).delete(synchronize_session=False)
            db.query(TestPlan).filter(TestPlan.project_id == project_id).delete(synchronize_session=False)
        
        # 4. 清理测试用例相关数据
        if test_case_ids:
            # 4a. 先清理其他项目中引用这些用例的执行记录和关联
            db.query(TestExecution).filter(TestExecution.test_case_id.in_(test_case_ids)).delete(synchronize_session=False)
            db.query(TestPlanTestCase).filter(TestPlanTestCase.test_case_id.in_(test_case_ids)).delete(synchronize_session=False)
            # 4b. 清理用例自身的附属数据
            db.query(TestCaseZmindLink).filter(TestCaseZmindLink.test_case_id.in_(test_case_ids)).delete(synchronize_session=False)
            db.query(TestCaseAttachment).filter(TestCaseAttachment.test_case_id.in_(test_case_ids)).delete(synchronize_session=False)
            db.query(TestCaseHistory).filter(TestCaseHistory.testcase_id.in_(test_case_ids)).delete(synchronize_session=False)
            db.query(ReviewPlanTestCase).filter(ReviewPlanTestCase.testcase_id.in_(test_case_ids)).delete(synchronize_session=False)
            db.query(Comment).filter(Comment.entity_type == 'testcase', Comment.entity_id.in_(test_case_ids)).delete(synchronize_session=False)
        
        # 5. 删除评审计划（先删关联，再删计划）
        db.query(ReviewPlanTestCase).filter(
            ReviewPlanTestCase.review_plan_id.in_(
                db.query(ReviewPlan.id).filter(ReviewPlan.project_id == project_id)
            )
        ).delete(synchronize_session=False)
        db.query(ReviewPlan).filter(ReviewPlan.project_id == project_id).delete(synchronize_session=False)
        
        # 6. 删除模块
        db.query(Module).filter(Module.project_id == project_id).delete(synchronize_session=False)
        
        # 7. 删除用例-项目关联
        db.query(TestCaseProject).filter(TestCaseProject.project_id == project_id).delete(synchronize_session=False)
        
        # 8. 删除主项目为此项目的测试用例
        db.query(TestCase).filter(TestCase.primary_project_id == project_id).delete(synchronize_session=False)
        
        # 9. 删除项目组-用例库关联
        db.query(TeamProject).filter(TeamProject.project_id == project_id).delete(synchronize_session=False)
        
        # 10. 删除用户-项目关联
        db.query(UserProject).filter(UserProject.project_id == project_id).delete(synchronize_session=False)
        
        # 11. 删除项目
        db.delete(project)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.PROJECTS,
        action=LogAction.DELETE,
        description=f"删除项目：{project_name}（ID: {project_id}）",
        request=req
    )
    
    return {"code": 200, "message": "success", "data": None}


@router.get("/user-teams")
def get_user_accessible_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户可访问的项目组列表 - 遵循权限优先级"""
    from utils.data_permission import (
        get_user_content_permission, get_user_organization_ids,
        get_user_team_ids, get_managed_department_ids, is_super_admin
    )

    # 超级管理员可以看到所有项目组
    if is_super_admin(current_user):
        teams = db.query(Team).filter(Team.status == 1).all()
    else:
        # 组织负责人：看管理的所有组织下的项目组
        managed_dept_ids = get_managed_department_ids(current_user, db)
        if managed_dept_ids:
            teams = db.query(Team).filter(
                Team.department_id.in_(managed_dept_ids),
                Team.status == 1
            ).all()
        else:
            # 非组织负责人：按 content_permissions 配置
            permission_level = get_user_content_permission(current_user, 'testcase', db)
            
            if permission_level == 'all':
                org_ids = get_user_organization_ids(current_user, db)
                if org_ids:
                    teams = db.query(Team).filter(
                        Team.department_id.in_(org_ids),
                        Team.status == 1
                    ).all()
                else:
                    team_ids = get_user_team_ids(current_user, db)
                    if not team_ids:
                        return {"code": 200, "message": "success", "data": []}
                    teams = db.query(Team).filter(Team.id.in_(team_ids), Team.status == 1).all()
            elif permission_level in ('project', 'personal'):
                team_ids = get_user_team_ids(current_user, db)
                if not team_ids:
                    return {"code": 200, "message": "success", "data": []}
                teams = db.query(Team).filter(Team.id.in_(team_ids), Team.status == 1).all()
            else:
                teams = db.query(Team).filter(Team.status == 1).all()
    
    result = [{"id": t.id, "name": t.name} for t in teams]
    
    return {
        "code": 200,
        "message": "success",
        "data": result
    }


@router.put("/{project_id}/teams")
def update_project_teams(
    project_id: int,
    team_ids: List[int],
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用例库的授权项目组"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="用例库不存在")
    
    # 删除现有的项目组授权
    db.query(TeamProject).filter(TeamProject.project_id == project_id).delete()
    
    # 添加新的项目组授权
    for team_id in team_ids:
        team = db.query(Team).filter(Team.id == team_id).first()
        if team:
            team_project = TeamProject(
                team_id=team_id,
                project_id=project_id
            )
            db.add(team_project)
    
    db.commit()
    
    log_operation(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        module=LogModule.PROJECTS,
        action=LogAction.UPDATE,
        description=f"更新用例库 {project.name} 的授权项目组（共 {len(team_ids)} 个）",
        request=req
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": None
    }
