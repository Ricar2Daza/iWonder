
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from core.config import settings
from domain import schemas
from infrastructure.db.session import SessionLocal
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.question_repository import QuestionRepository
from infrastructure.repositories.notification_repository import NotificationRepository
from infrastructure.repositories.comment_repository import CommentRepository
from infrastructure.repositories.password_reset_repository import PasswordResetRepository
from application.services.user_service import UserService
from application.services.question_service import QuestionService
from application.services.auth_service import AuthService
from application.services.notification_service import NotificationService
from application.services.comment_service import CommentService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_question_repository(db: Session = Depends(get_db)) -> QuestionRepository:
    return QuestionRepository(db)

def get_notification_repository(db: Session = Depends(get_db)) -> NotificationRepository:
    return NotificationRepository(db)

def get_comment_repository(db: Session = Depends(get_db)) -> CommentRepository:
    return CommentRepository(db)

def get_password_reset_repository(db: Session = Depends(get_db)) -> PasswordResetRepository:
    return PasswordResetRepository(db)

def get_notification_service(notification_repo: NotificationRepository = Depends(get_notification_repository)) -> NotificationService:
    return NotificationService(notification_repo)

def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
    notification_service: NotificationService = Depends(get_notification_service)
) -> UserService:
    return UserService(user_repo, notification_service)

def get_question_service(
    question_repo: QuestionRepository = Depends(get_question_repository),
    notification_service: NotificationService = Depends(get_notification_service)
) -> QuestionService:
    return QuestionService(question_repo, notification_service)

def get_comment_service(
    comment_repo: CommentRepository = Depends(get_comment_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    notification_service: NotificationService = Depends(get_notification_service)
) -> CommentService:
    return CommentService(comment_repo, question_repo, user_repo, notification_service)

def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    password_reset_repo: PasswordResetRepository = Depends(get_password_reset_repository)
) -> AuthService:
    return AuthService(user_repo, password_reset_repo)

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    user_repo: UserRepository = Depends(get_user_repository)
) -> schemas.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = user_repo.get_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

def get_current_user_optional(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="api/v1/auth/token", auto_error=False)),
    user_repo: UserRepository = Depends(get_user_repository)
) -> Optional[schemas.User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user = user_repo.get_by_username(username=username)
    return user