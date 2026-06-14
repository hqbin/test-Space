"""
评论服务
"""
from sqlalchemy.orm import Session
from models import Comment, User
from utils.exceptions import ValidationError, NotFoundError
from typing import Optional, List
import re


class CommentService:
    """评论管理服务"""
    
    @staticmethod
    def create_comment(
        entity_type: str,
        entity_id: int,
        content: str,
        author_id: int,
        db: Session,
        parent_id: Optional[int] = None
    ) -> Comment:
        """
        创建评论
        
        Args:
            entity_type: 实体类型 (testplan/testcase/execution)
            entity_id: 实体ID
            content: 评论内容
            author_id: 作者ID
            db: 数据库会话
            parent_id: 父评论ID（可选）
        
        Returns:
            Comment: 评论记录
        
        Raises:
            ValidationError: 验证失败
        """
        # 1. 验证
        if not content.strip():
            raise ValidationError("评论内容不能为空")
        
        if entity_type not in ['testplan', 'testcase', 'execution', 'review_testcase']:
            raise ValidationError(f"不支持的实体类型: {entity_type}")
        
        # 2. 如果有父评论，检查父评论是否存在
        if parent_id:
            parent_comment = db.query(Comment).filter(Comment.id == parent_id).first()
            if not parent_comment:
                raise NotFoundError(f"父评论不存在: {parent_id}")
        
        # 3. 解析@提及
        mentioned_users = CommentService._parse_mentions(content)
        
        # 4. 创建评论
        comment = Comment(
            entity_type=entity_type,
            entity_id=entity_id,
            parent_id=parent_id,
            content=content,
            author_id=author_id
        )
        
        db.add(comment)
        db.commit()
        db.refresh(comment)
        
        # 5. 发送通知（可选，这里暂时跳过）
        # for username in mentioned_users:
        #     CommentService._send_mention_notification(username, comment.id, db)
        
        return comment
    
    @staticmethod
    def get_comments(
        entity_type: str,
        entity_id: int,
        db: Session,
        build_tree: bool = True
    ) -> List[dict]:
        """
        获取评论列表
        
        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            db: 数据库会话
            build_tree: 是否构建树形结构
        
        Returns:
            list: 评论列表（树形或平铺）
        """
        # 获取所有评论
        comments = db.query(Comment).filter(
            Comment.entity_type == entity_type,
            Comment.entity_id == entity_id,
            Comment.is_deleted == False
        ).order_by(Comment.created_at).all()
        
        if not build_tree:
            # 返回平铺列表
            return [CommentService._comment_to_dict(c, db) for c in comments]
        
        # 构建树形结构
        return CommentService._build_comment_tree(comments, db)
    
    @staticmethod
    def delete_comment(comment_id: int, db: Session) -> bool:
        """
        删除评论（软删除）
        
        Args:
            comment_id: 评论ID
            db: 数据库会话
        
        Returns:
            bool: 是否成功
        
        Raises:
            NotFoundError: 评论不存在
        """
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        
        if not comment:
            raise NotFoundError(f"评论不存在: {comment_id}")
        
        # 软删除
        comment.is_deleted = True
        db.commit()
        
        return True
    
    @staticmethod
    def _parse_mentions(content: str) -> List[str]:
        """
        解析评论中的@提及
        
        Args:
            content: 评论内容
        
        Returns:
            list: 被提及的用户名列表
        """
        pattern = r'@(\w+)'
        mentions = re.findall(pattern, content)
        return list(set(mentions))  # 去重
    
    @staticmethod
    def _build_comment_tree(comments: List[Comment], db: Session) -> List[dict]:
        """
        构建评论树
        
        Args:
            comments: 评论列表
            db: 数据库会话
        
        Returns:
            list: 树形结构的评论列表
        """
        # 构建字典映射
        comment_dict = {}
        for comment in comments:
            comment_data = CommentService._comment_to_dict(comment, db)
            comment_data['children'] = []
            comment_dict[comment.id] = comment_data
        
        # 构建树形结构
        tree = []
        for comment in comments:
            comment_data = comment_dict[comment.id]
            
            if comment.parent_id is None:
                # 根评论
                tree.append(comment_data)
            else:
                # 子评论
                parent = comment_dict.get(comment.parent_id)
                if parent:
                    parent['children'].append(comment_data)
        
        return tree
    
    @staticmethod
    def _comment_to_dict(comment: Comment, db: Session) -> dict:
        """
        将评论对象转换为字典
        
        Args:
            comment: 评论对象
            db: 数据库会话
        
        Returns:
            dict: 评论字典
        """
        # 获取作者信息
        author = db.query(User).filter(User.id == comment.author_id).first()
        author_name = author.username if author else "未知用户"
        
        return {
            'id': comment.id,
            'entity_type': comment.entity_type,
            'entity_id': comment.entity_id,
            'parent_id': comment.parent_id,
            'content': comment.content,
            'author_id': comment.author_id,
            'author_name': author_name,
            'is_deleted': comment.is_deleted,
            'created_at': comment.created_at,
            'updated_at': comment.updated_at
        }
