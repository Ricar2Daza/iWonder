from sqlalchemy.orm import Session
from ..db import models


class UserBlockRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, blocker_id: int, blocked_id: int):
        existing = self.db.query(models.UserBlock).filter(
            models.UserBlock.blocker_id == blocker_id,
            models.UserBlock.blocked_id == blocked_id
        ).first()
        if existing:
            return existing
        block = models.UserBlock(blocker_id=blocker_id, blocked_id=blocked_id)
        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)
        return block

    def delete(self, blocker_id: int, blocked_id: int):
        self.db.query(models.UserBlock).filter(
            models.UserBlock.blocker_id == blocker_id,
            models.UserBlock.blocked_id == blocked_id
        ).delete()
        self.db.commit()

    def is_blocking(self, blocker_id: int, blocked_id: int) -> bool:
        return self.db.query(models.UserBlock).filter(
            models.UserBlock.blocker_id == blocker_id,
            models.UserBlock.blocked_id == blocked_id
        ).first() is not None
