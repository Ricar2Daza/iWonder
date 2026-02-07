
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
from application.services.user_service import UserService
from application.services.question_service import QuestionService
from application.services.auth_service import AuthService

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

def get_user_service(user_repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(user_repo)

def get_question_service(question_repo: QuestionRepository = Depends(get_question_repository)) -> QuestionService:
    return QuestionService(question_repo)

def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)

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