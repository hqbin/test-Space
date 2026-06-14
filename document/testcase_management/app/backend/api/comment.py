"""
评论管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from models import User, Comment
from services import CommentService
from schemas import CommentCreate
from utils.permissions import can_delete_comment
from utils.exceptions import NotFoundError, ValidationError
from utils.logger import log_operation, LogAction, LogModule

router = APIRouter(prefix="/api/comments", tags=["comments"])


@router.post("")
def create_comment(
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建评论
    
    - 支持评论测试计划、测试用例、测试执行记录
    - 支持无限层级嵌套回复
    - 支持@username提及功能
    """
    try:
        comment = CommentService.create_comment(
            entity_type=comment_data.entity_type,
            entity_id=comment_data.entity_id,
            content=comment_data.content,
            author_id=current_user.id,
            db=db,
            parent_id=comment_data.parent_id
        )
        
        return {
            "code": 200,
            "message": "评论成功",
            "data": {
                "id": comment.id,
                "entity_type": comment.entity_type,
                "entity_id": comment.entity_id,
                "parent_id": comment.parent_id,
                "content": comment.content,
                "author_id": comment.author_id,
                "created_at": comment.created_at.isoformat()
            }
        }
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/counts/{entity_type}")
def get_comment_counts(
    entity_type: str,
    entity_ids: str = Query(None, description="实体ID列表，用逗号分隔"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量获取评论数量
    
    - entity_type: 实体类型
    - entity_ids: 实体ID列表，用逗号分隔
    """
    try:
        from sqlalchemy import func
        
        if entity_type not in ['testplan', 'testcase', 'execution', 'review_testcase']:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的实体类型: {entity_type}")
        
        if not entity_ids:
            return {"code": 200, "message": "success", "data": {}}
        
        # 限制最多500个ID，防止请求过大
        id_list = entity_ids.split(',')
        if len(id_list) > 500:
            id_list = id_list[:500]
        
        ids = [int(i.strip()) for i in id_list if i.strip()]
        
        if not ids:
            return {"code": 200, "message": "success", "data": {}}
        
        # 批量查询评论数量
        results = db.query(
            Comment.entity_id,
            func.count(Comment.id).label('count')
        ).filter(
            Comment.entity_type == entity_type,
            Comment.entity_id.in_(ids),
            Comment.is_deleted == False
        ).group_by(Comment.entity_id).all()
        
        # 构建映射
        counts = {r.entity_id: r.count for r in results}
        
        # 返回所有ID的数量（没有评论的返回0）
        response = {}
        for entity_id in ids:
            response[entity_id] = counts.get(entity_id, 0)
        
        return {"code": 200, "message": "success", "data": response}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{entity_type}/{entity_id}")
def get_comments(
    entity_type: str,
    entity_id: int,
    build_tree: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取评论列表
    
    - entity_type: testplan/testcase/execution
    - build_tree: 是否构建树形结构（默认true）
    """
    try:
        comments = CommentService.get_comments(
            entity_type=entity_type,
            entity_id=entity_id,
            db=db,
            build_tree=build_tree
        )
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": comments
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除评论（软删除）
    
    权限：只有管理员可以删除评论
    """
    try:
        # 权限检查
        if not can_delete_comment(current_user, None):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有管理员可以删除评论")
        
        CommentService.delete_comment(comment_id, db)
        
        log_operation(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            module=LogModule.SYSTEM,
            action=LogAction.DELETE,
            description=f"删除评论（ID: {comment_id}）",
            request=req
        )
        
        return {
            "code": 200,
            "message": "删除成功"
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
