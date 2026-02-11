from infrastructure.repositories.notification_repository import NotificationRepository
from domain import schemas
from infrastructure.websockets import manager
from fastapi.concurrency import run_in_threadpool
from infrastructure.cache.redis_client import cache_delete_prefix, cache_get_json, cache_set_json
from infrastructure.cache.redis_queue import enqueue_job

NOTIFICATIONS_TTL_SECONDS = 15

class NotificationService:
    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    def _cache_key(self, user_id: int, skip: int, limit: int) -> str:
        return f"notifications:{user_id}:{skip}:{limit}"

    def _cache_prefix(self, user_id: int) -> str:
        return f"notifications:{user_id}:"

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
        cache_delete_prefix(self._cache_prefix(user_id))
        enqueue_job("notification_queue", {"type": "notification", "user_id": user_id, "content": content})
        
        return notification

    def get_notifications(self, user_id: int, skip: int = 0, limit: int = 20):
        cache_key = self._cache_key(user_id, skip, limit)
        cached = cache_get_json(cache_key)
        if cached is not None:
            return [schemas.Notification.model_validate(item) for item in cached]
        results = self.notification_repo.get_by_user(user_id, skip, limit)
        serialized = [schemas.Notification.model_validate(item).model_dump() for item in results]
        cache_set_json(cache_key, serialized, NOTIFICATIONS_TTL_SECONDS)
        return results

    def get_grouped_notifications(self, user_id: int, limit: int = 50):
        results = self.notification_repo.get_by_user(user_id, 0, limit)
        groups = {}
        for item in results:
            key = (item.notification_type, item.content)
            if key not in groups:
                groups[key] = {
                    "content": item.content,
                    "notification_type": item.notification_type,
                    "latest_created_at": item.created_at,
                    "count": 0,
                    "unread_count": 0,
                    "notification_ids": []
                }
            group = groups[key]
            group["count"] += 1
            if not item.is_read:
                group["unread_count"] += 1
            group["notification_ids"].append(item.id)
            if item.created_at > group["latest_created_at"]:
                group["latest_created_at"] = item.created_at
        grouped_list = []
        for group in groups.values():
            grouped_list.append(schemas.NotificationGroup(
                content=group["content"],
                notification_type=group["notification_type"],
                latest_created_at=group["latest_created_at"],
                count=group["count"],
                unread_count=group["unread_count"],
                is_read=group["unread_count"] == 0,
                notification_ids=group["notification_ids"]
            ))
        grouped_list.sort(key=lambda g: g.latest_created_at, reverse=True)
        return grouped_list

    def mark_as_read(self, notification_id: int, user_id: int):
        notification = self.notification_repo.mark_as_read(notification_id, user_id)
        if notification:
            cache_delete_prefix(self._cache_prefix(user_id))
        return notification
        
    def mark_all_as_read(self, user_id: int):
        result = self.notification_repo.mark_all_as_read(user_id)
        cache_delete_prefix(self._cache_prefix(user_id))
        return result

    def mark_many_as_read(self, user_id: int, notification_ids: list[int]):
        result = self.notification_repo.mark_many_as_read(user_id, notification_ids)
        cache_delete_prefix(self._cache_prefix(user_id))
        return result
