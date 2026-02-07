from sqlalchemy.orm import Session
from ..db import models
from domain import schemas

class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, notification: schemas.NotificationCreate):
        db_notification = models.Notification(
            user_id=notification.user_id,
            content=notification.content,
            notification_type=notification.notification_type
        )
        self.db.add(db_notification)
        self.db.commit()
        self.db.refresh(db_notification)
        return db_notification

    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 20):
        return self.db.query(models.Notification)\
            .filter(models.Notification.user_id == user_id)\
            .order_by(models.Notification.created_at.desc())\
            .offset(skip).limit(limit).all()

    def mark_as_read(self, notification_id: int, user_id: int):
        notification = self.db.query(models.Notification).filter(
            models.Notification.id == notification_id,
            models.Notification.user_id == user_id
        ).first()
        if notification:
            notification.is_read = True
            self.db.commit()
            return notification
        return None

    def mark_all_as_read(self, user_id: int):
        self.db.query(models.Notification).filter(
            models.Notification.user_id == user_id,
            models.Notification.is_read == False
        ).update({"is_read": True})
        self.db.commit()