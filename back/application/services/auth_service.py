
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.password_reset_repository import PasswordResetRepository
from core.security import verify_password, create_access_token, get_password_hash
from domain import schemas
from datetime import timedelta, datetime
import uuid
import logging
from pydantic import EmailStr
from infrastructure.cache.redis_queue import enqueue_job
from infrastructure.mail.reset_email import send_reset_email

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, user_repo: UserRepository, password_reset_repo: PasswordResetRepository):
        self.user_repo = user_repo
        self.password_reset_repo = password_reset_repo

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

    async def request_password_reset(self, email: str):
        user = self.user_repo.get_by_email(email)
        if not user:
            # Don't reveal if user exists
            return
        
        # Rate limit
        attempts = self.password_reset_repo.count_attempts_last_hour(user.id)
        if attempts >= 3:
            logger.warning(f"Rate limit exceeded for user {user.id}")
            return

        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        self.password_reset_repo.create(user.id, token, expires_at)
        
        queued = enqueue_job("email_queue", {"type": "reset_password", "email": email, "token": token})
        if not queued:
            await send_reset_email(email, token)

    def reset_password(self, token: str, new_password: str):
        reset = self.password_reset_repo.get_by_token(token)
        if not reset:
            raise ValueError("Invalid token")
        
        if reset.is_used:
            raise ValueError("Token already used")
            
        now = datetime.utcnow()
        if reset.expires_at.tzinfo is not None:
            now = datetime.now(reset.expires_at.tzinfo)
        if reset.expires_at < now:
            raise ValueError("Token expired")

        user = self.user_repo.get_by_id(reset.user_id)
        if not user:
            raise ValueError("User not found")
            
        hashed_password = get_password_hash(new_password)
        
        # Update user password using a new method in UserRepository (needs implementation or direct update)
        # Since I don't have update_password in UserRepository, I will add it or update manually if I had session access.
        # But UserRepository is abstraction. I should add update_password to UserRepository.
        # Wait, I have update_user in UserService which calls user_repo.update.
        # But I am in AuthService. I should rely on UserRepository to update password.
        
        self.user_repo.update_password(user.id, hashed_password)
        self.password_reset_repo.mark_as_used(reset.id)
