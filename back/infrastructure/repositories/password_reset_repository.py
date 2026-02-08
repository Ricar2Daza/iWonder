from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..db import models
from sqlalchemy import func

class PasswordResetRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, token: str, expires_at: datetime):
        db_reset = models.PasswordReset(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        self.db.add(db_reset)
        self.db.commit()
        self.db.refresh(db_reset)
        return db_reset

    def get_by_token(self, token: str):
        return self.db.query(models.PasswordReset).filter(models.PasswordReset.token == token).first()

    def mark_as_used(self, reset_id: int):
        reset = self.db.query(models.PasswordReset).filter(models.PasswordReset.id == reset_id).first()
        if reset:
            reset.is_used = True
            self.db.commit()
            self.db.refresh(reset)
        return reset

    def count_attempts_last_hour(self, user_id: int):
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        return self.db.query(models.PasswordReset).filter(
            models.PasswordReset.user_id == user_id,
            models.PasswordReset.created_at >= one_hour_ago
        ).count()
