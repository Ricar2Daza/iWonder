
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.password_reset_repository import PasswordResetRepository
from core.security import verify_password, create_access_token, get_password_hash
from core.config import settings
from domain import schemas
from datetime import timedelta, datetime
import uuid
import logging
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

logger = logging.getLogger(__name__)

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS
)

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
        
        # Send email
        await self._send_reset_email(email, token)

    async def _send_reset_email(self, email: str, token: str):
        reset_link = f"http://localhost:3000/reset-password?token={token}"
        
        html = f"""
        <p>Has solicitado restablecer tu contraseña en iWonder.</p>
        <p>Haz clic en el siguiente enlace para continuar:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>Si no solicitaste este cambio, puedes ignorar este correo.</p>
        <p>Este enlace expirará en 1 hora.</p>
        """

        message = MessageSchema(
            subject="Restablecimiento de Contraseña - iWonder",
            recipients=[email],
            body=html,
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        try:
            await fm.send_message(message)
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            # Fallback to console for development if email fails (e.g. bad credentials)
            print(f"FAILED TO SEND EMAIL. Link: {reset_link}")

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