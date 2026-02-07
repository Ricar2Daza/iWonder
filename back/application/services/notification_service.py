from infrastructure.repositories.notification_repository import NotificationRepository
from domain import schemas
from infrastructure.websockets import manager
from fastapi.concurrency import run_in_threadpool

class NotificationService:
    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    async def create_notification(self, user_id: int, content: str, notification_type: str = "info"):
        # 1. Create in DB
        notification_in = schemas.NotificationCreate(
            user_id=user_id,
            content=content,
            notification_type=notification_type
        )
        notification = await run_in_threadpool(self.notification_repo.create, notification_in)
        
        # 2. Send via WebSocket (Real-time)
        # Send a JSON string to differentiate from simple text messages if needed, 
        # but for now let's keep it simple or format it.
        # "Notification: {content}"
        await manager.send_personal_message(content, user_id)
        
        return notification

    def get_notifications(self, user_id: int, skip: int = 0, limit: int = 20):
        return self.notification_repo.get_by_user(user_id, skip, limit)

    def mark_as_read(self, notification_id: int, user_id: int):
        return self.notification_repo.mark_as_read(notification_id, user_id)
        
    def mark_all_as_read(self, user_id: int):
        return self.notification_repo.mark_all_as_read(user_id)