from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

    @field_validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must be alphanumeric')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserProfile(User):
    followers_count: int = 0
    following_count: int = 0
    is_following: Optional[bool] = None

    class Config:
        from_attributes = True

# Question Schemas
class QuestionBase(BaseModel):
    content: str
    is_anonymous: bool = False
    receiver_id: int

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    asker_id: Optional[int]
    created_at: datetime
    # We might want to hide asker if anonymous, handled in logic or specific schema

    class Config:
        from_attributes = True

class QuestionDisplay(BaseModel):
    id: int
    content: str
    is_anonymous: bool
    created_at: datetime
    receiver: User
    asker: Optional[User] = None # Will be null if anonymous or really null

    class Config:
        from_attributes = True

# Answer Schemas
class AnswerBase(BaseModel):
    content: str
    question_id: int

class AnswerCreate(AnswerBase):
    pass

class Answer(AnswerBase):
    id: int
    author_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AnswerDisplay(BaseModel):
    id: int
    content: str
    created_at: datetime
    question: QuestionDisplay
    author: User

    class Config:
        from_attributes = True

# Token Schema
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None