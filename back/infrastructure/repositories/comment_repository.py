from sqlalchemy.orm import Session
from ..db import models
from domain import schemas

class CommentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, comment: schemas.CommentCreate, user_id: int):
        db_comment = models.Comment(
            content=comment.content,
            answer_id=comment.answer_id,
            user_id=user_id
        )
        self.db.add(db_comment)
        self.db.commit()
        self.db.refresh(db_comment)
        return db_comment

    def get_by_answer_id(self, answer_id: int, skip: int = 0, limit: int = 10):
        return self.db.query(models.Comment)\
            .filter(models.Comment.answer_id == answer_id)\
            .order_by(models.Comment.created_at.asc())\
            .offset(skip).limit(limit).all()

    def get_by_id(self, comment_id: int):
        return self.db.query(models.Comment).filter(models.Comment.id == comment_id).first()

    def delete(self, comment_id: int):
        comment = self.db.query(models.Comment).filter(models.Comment.id == comment_id).first()
        if comment:
            self.db.delete(comment)
            self.db.commit()
            return True
        return False