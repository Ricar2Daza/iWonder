
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.user_block_repository import UserBlockRepository
from application.services.notification_service import NotificationService
from domain import schemas
from core.security import get_password_hash
from fastapi.concurrency import run_in_threadpool
from infrastructure.cache.redis_client import cache_delete_prefix

class UserService:
    def __init__(self, user_repo: UserRepository, notification_service: NotificationService, block_repo: UserBlockRepository):
        self.user_repo = user_repo
        self.notification_service = notification_service
        self.block_repo = block_repo

    def create_user(self, user: schemas.UserCreate):
        hashed_password = get_password_hash(user.password)
        return self.user_repo.create(user, hashed_password)

    def get_user(self, user_id: int):
        return self.user_repo.get_by_id(user_id)

    def get_user_by_username(self, username: str):
        return self.user_repo.get_by_username(username)
    
    def get_user_by_email(self, email: str):
        return self.user_repo.get_by_email(email)

    def get_users(self, skip: int = 0, limit: int = 10):
        return self.user_repo.get_all(skip, limit)

    def get_following_users(self, user_id: int, skip: int = 0, limit: int = 50):
        return self.user_repo.get_following_users(user_id, skip, limit)

    async def follow_user(self, follower_id: int, followed_id: int):
        if follower_id == followed_id:
            raise ValueError("Cannot follow yourself")
        if self.is_blocked_between(follower_id, followed_id):
            raise ValueError("Blocked")
        
        is_following = await run_in_threadpool(self.user_repo.is_following, follower_id, followed_id)
        if is_following:
            return # Idempotent
        
        result = await run_in_threadpool(self.user_repo.follow, follower_id, followed_id)
        
        # Get follower name for notification
        follower = await run_in_threadpool(self.get_user, follower_id)
        await self.notification_service.create_notification(
            user_id=followed_id, 
            content=f"{follower.username} te ha seguido", 
            notification_type="follow"
        )
        cache_delete_prefix("profile:")
        
        return result

    def unfollow_user(self, follower_id: int, followed_id: int):
        if not self.user_repo.is_following(follower_id, followed_id):
            return # Idempotent
        result = self.user_repo.unfollow(follower_id, followed_id)
        cache_delete_prefix("profile:")
        cache_delete_prefix("search_users:")
        return result
        return result

    def search_users(self, query: str, skip: int = 0, limit: int = 10):
        return self.user_repo.search_users(query, skip, limit)

    def update_user(self, user_id: int, user_update: schemas.UserUpdate):
        updated = self.user_repo.update(user_id, user_update)
        cache_delete_prefix("profile:")
        cache_delete_prefix("search_users:")
        return updated

    def is_following(self, follower_id: int, followed_id: int):
        return self.user_repo.is_following(follower_id, followed_id)

    def block_user(self, blocker_id: int, blocked_id: int):
        if blocker_id == blocked_id:
            raise ValueError("Cannot block yourself")
        result = self.block_repo.create(blocker_id, blocked_id)
        cache_delete_prefix("profile:")
        cache_delete_prefix("search_users:")
        return result

    def unblock_user(self, blocker_id: int, blocked_id: int):
        self.block_repo.delete(blocker_id, blocked_id)
        cache_delete_prefix("profile:")
        cache_delete_prefix("search_users:")

    def is_blocking(self, blocker_id: int, blocked_id: int) -> bool:
        return self.block_repo.is_blocking(blocker_id, blocked_id)

    def is_blocked_between(self, user_id: int, other_user_id: int) -> bool:
        return self.is_blocking(user_id, other_user_id) or self.is_blocking(other_user_id, user_id)
