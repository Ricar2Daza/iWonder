
from infrastructure.repositories.user_repository import UserRepository
from core.security import verify_password, create_access_token
from domain import schemas
from datetime import timedelta

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def authenticate_user(self, username: str, password: str):
        user = self.user_repo.get_by_username(username)
        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        return user

    def create_token(self, user: schemas.User):
        access_token_expires = timedelta(minutes=30) # Could be from settings
        access_token = create_access_token(
            data={"sub": user.username, "id": user.id}, expires_delta=access_token_expires
        )
        return access_token