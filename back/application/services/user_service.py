
from infrastructure.repositories.user_repository import UserRepository
from application.services.notification_service import NotificationService
from domain import schemas
from core.security import get_password_hash
from fastapi.concurrency import run_in_threadpool

class UserService:
    def __init__(self, user_repo: UserRepository, notification_service: NotificationService):
        self.user_repo = user_repo
        self.notification_service = notification_service

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

    async def follow_user(self, follower_id: int, followed_id: int):
        if follower_id == followed_id:
            raise ValueError("Cannot follow yourself")
        
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
        
        return result

    def unfollow_user(self, follower_id: int, followed_id: int):
        if not self.user_repo.is_following(follower_id, followed_id):
            return # Idempotent
        return self.user_repo.unfollow(follower_id, followed_id)

    def search_users(self, query: str, skip: int = 0, limit: int = 10):
        return self.user_repo.search_users(query, skip, limit)

    def update_user(self, user_id: int, user_update: schemas.UserUpdate):
        return self.user_repo.update(user_id, user_update)