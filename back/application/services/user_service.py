
from infrastructure.repositories.user_repository import UserRepository
from domain import schemas
from core.security import get_password_hash

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

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

    def follow_user(self, follower_id: int, followed_id: int):
        if follower_id == followed_id:
            raise ValueError("Cannot follow yourself")
        if self.user_repo.is_following(follower_id, followed_id):
             # idempotent or raise error? let's just return current state or follow object
             # For now, just follow
             pass
        return self.user_repo.follow(follower_id, followed_id)