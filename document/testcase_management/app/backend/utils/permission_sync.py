"""
权限同步工具
自动同步项目组的用例库权限到用户
"""
from sqlalchemy.orm import Session
from models import UserTeam, TeamProject, UserProject
import logging

logger = logging.getLogger(__name__)


def sync_user_team_permissions(user_id: int, db: Session):
    """
    同步单个用户的项目组权限
    当用户加入项目组时调用
    """
    try:
        # 获取用户所属的项目组
        user_teams = db.query(UserTeam).filter(UserTeam.user_id == user_id).all()
        team_ids = [ut.team_id for ut in user_teams]
        
        if not team_ids:
            logger.info(f"用户 {user_id} 未加入任何项目组，无需同步")
            return
        
        # 获取这些项目组的所有用例库
        team_projects = db.query(TeamProject).filter(TeamProject.team_id.in_(team_ids)).all()
        team_project_ids = set([tp.project_id for tp in team_projects])
        
        if not team_project_ids:
            logger.info(f"用户 {user_id} 的项目组没有授权任何用例库")
            return
        
        # 获取用户已有的用例库权限
        existing_user_projects = db.query(UserProject).filter(UserProject.user_id == user_id).all()
        existing_project_ids = set([up.project_id for up in existing_user_projects])
        
        # 计算需要添加的用例库
        projects_to_add = team_project_ids - existing_project_ids
        
        # 添加缺失的用例库权限
        added_count = 0
        for project_id in projects_to_add:
            user_project = UserProject(
                user_id=user_id,
                project_id=project_id
            )
            db.add(user_project)
            added_count += 1
        
        if added_count > 0:
            db.commit()
            logger.info(f"为用户 {user_id} 添加了 {added_count} 个用例库权限")
        else:
            logger.info(f"用户 {user_id} 已有所有项目组用例库权限")
            
    except Exception as e:
        logger.error(f"同步用户 {user_id} 权限失败: {str(e)}")
        db.rollback()
        raise


def sync_team_members_permissions(team_id: int, db: Session):
    """
    同步项目组所有成员的权限
    当项目组授权用例库时调用
    """
    try:
        # 获取项目组成员
        user_teams = db.query(UserTeam).filter(UserTeam.team_id == team_id).all()
        user_ids = [ut.user_id for ut in user_teams]
        
        if not user_ids:
            logger.info(f"项目组 {team_id} 没有成员，无需同步")
            return
        
        # 获取项目组用例库
        team_projects = db.query(TeamProject).filter(TeamProject.team_id == team_id).all()
        project_ids = [tp.project_id for tp in team_projects]
        
        if not project_ids:
            logger.info(f"项目组 {team_id} 没有授权任何用例库")
            return
        
        # 为每个成员添加权限
        total_added = 0
        for user_id in user_ids:
            for project_id in project_ids:
                # 检查是否已有权限
                existing = db.query(UserProject).filter(
                    UserProject.user_id == user_id,
                    UserProject.project_id == project_id
                ).first()
                
                if not existing:
                    user_project = UserProject(
                        user_id=user_id,
                        project_id=project_id
                    )
                    db.add(user_project)
                    total_added += 1
        
        if total_added > 0:
            db.commit()
            logger.info(f"为项目组 {team_id} 的成员添加了 {total_added} 个用例库权限")
        else:
            logger.info(f"项目组 {team_id} 的成员已有所有用例库权限")
            
    except Exception as e:
        logger.error(f"同步项目组 {team_id} 成员权限失败: {str(e)}")
        db.rollback()
        raise


def remove_user_team_permissions(user_id: int, team_id: int, db: Session):
    """
    移除用户从项目组继承的权限
    当用户离开项目组时调用
    注意：只移除通过该项目组获得的权限，保留直接授权和其他项目组的权限
    """
    try:
        # 获取该项目组的用例库
        team_projects = db.query(TeamProject).filter(TeamProject.team_id == team_id).all()
        team_project_ids = set([tp.project_id for tp in team_projects])
        
        if not team_project_ids:
            logger.info(f"项目组 {team_id} 没有授权任何用例库，无需移除权限")
            return
        
        # 获取用户其他项目组的用例库（不包括当前离开的项目组）
        other_user_teams = db.query(UserTeam).filter(
            UserTeam.user_id == user_id,
            UserTeam.team_id != team_id
        ).all()
        other_team_ids = [ut.team_id for ut in other_user_teams]
        
        other_team_project_ids = set()
        if other_team_ids:
            other_team_projects = db.query(TeamProject).filter(
                TeamProject.team_id.in_(other_team_ids)
            ).all()
            other_team_project_ids = set([tp.project_id for tp in other_team_projects])
        
        # 计算需要移除的用例库（只在当前项目组有，其他项目组没有的）
        projects_to_remove = team_project_ids - other_team_project_ids
        
        # 移除权限
        removed_count = 0
        for project_id in projects_to_remove:
            user_project = db.query(UserProject).filter(
                UserProject.user_id == user_id,
                UserProject.project_id == project_id
            ).first()
            
            if user_project:
                db.delete(user_project)
                removed_count += 1
        
        if removed_count > 0:
            db.commit()
            logger.info(f"移除用户 {user_id} 的 {removed_count} 个用例库权限")
        else:
            logger.info(f"用户 {user_id} 没有需要移除的权限")
            
    except Exception as e:
        logger.error(f"移除用户 {user_id} 权限失败: {str(e)}")
        db.rollback()
        raise
