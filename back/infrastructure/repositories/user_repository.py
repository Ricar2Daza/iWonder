
from sqlalchemy.orm import Session
from ..db import models
from domain import schemas

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int):
        return self.db.query(models.User).filter(models.User.id == user_id).first()

    def get_by_username(self, username: str):
        return self.db.query(models.User).filter(models.User.username == username).first()

    def get_by_email(self, email: str):
        return self.db.query(models.User).filter(models.User.email == email).first()

    def create(self, user: schemas.UserCreate, hashed_password: str):
        db_user = models.User(
            username=user.username, 
            email=user.email, 
            hashed_password=hashed_password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_all(self, skip: int = 0, limit: int = 10):
        return self.db.query(models.User).offset(skip).limit(limit).all()

    def follow(self, follower_id: int, followed_id: int):
        follow = models.Follow(follower_id=follower_id, followed_id=followed_id)
        self.db.add(follow)
        self.db.commit()
        return follow

    def is_following(self, follower_id: int, followed_id: int):
        return self.db.query(models.Follow).filter(
            models.Follow.follower_id == follower_id,
            models.Follow.followed_id == followed_id
        ).first() is not None