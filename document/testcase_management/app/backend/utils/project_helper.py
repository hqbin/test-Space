"""
项目层级查询辅助函数
用于支持父项目查询子项目数据的功能
"""

from sqlalchemy.orm import Session
from models import Project
from typing import List, Optional


def get_project_ids_with_children(db: Session, project_id: int) -> List[int]:
    """
    获取项目ID列表，包括该项目及其所有子孙项目
    
    如果是父项目（GROUP或CATEGORY），返回该项目及其所有子项目的ID列表
    如果是产品线（PRODUCT），只返回该项目的ID
    
    Args:
        db: 数据库会话
        project_id: 项目ID
        
    Returns:
        项目ID列表
    """
    # 获取选中的项目
    selected_project = db.query(Project).filter(Project.id == project_id).first()
    
    if not selected_project:
        return []
    
    # 如果是父项目（GROUP或CATEGORY），查询该项目及其所有子项目
    if selected_project.project_type in ['GROUP', 'CATEGORY']:
        # 查询所有path以当前项目path开头的项目（包括自己和所有子孙项目）
        child_projects = db.query(Project).filter(
            Project.path.like(f"{selected_project.path}%")
        ).all()
        
        # 返回所有相关项目的ID列表
        return [p.id for p in child_projects]
    else:
        # 如果是产品线（PRODUCT），只返回该项目的ID
        return [project_id]


def get_project_filter_description(db: Session, project_id: Optional[int]) -> str:
    """
    获取项目过滤的描述信息
    
    Args:
        db: 数据库会话
        project_id: 项目ID
        
    Returns:
        描述信息
    """
    if not project_id:
        return "所有项目"
    
    selected_project = db.query(Project).filter(Project.id == project_id).first()
    
    if not selected_project:
        return f"项目ID: {project_id}"
    
    if selected_project.project_type == 'GROUP':
        return f"小组「{selected_project.name}」及其所有子项目"
    elif selected_project.project_type == 'CATEGORY':
        return f"分类「{selected_project.name}」及其所有子项目"
    else:
        return f"产品线「{selected_project.name}」"
