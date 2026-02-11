
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

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @field_validator('new_password')
    def password_strong(cls, v):
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$', v):
            raise ValueError('Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one number, and one special character')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_content_type: Optional[str] = None
    avatar_size: Optional[int] = None
    only_followers_can_ask: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

# Notification Schemas
class NotificationBase(BaseModel):
    content: str
    notification_type: str = "info"

class NotificationCreate(NotificationBase):
    user_id: int

class Notification(NotificationBase):
    id: int
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class NotificationGroup(BaseModel):
    content: str
    notification_type: str
    latest_created_at: datetime
    count: int
    unread_count: int
    is_read: bool
    notification_ids: List[int]

class NotificationReadMany(BaseModel):
    notification_ids: List[int]

class Conversation(BaseModel):
    id: int
    user1_id: int
    user2_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    reply_to_message_id: Optional[int] = None

class MessageReactionCreate(BaseModel):
    emoji: str

class MessageReactionSummary(BaseModel):
    emoji: str
    count: int

class Message(MessageBase):
    id: int
    conversation_id: int
    sender_id: int
    receiver_id: int
    reply_to_message_id: Optional[int] = None
    is_read: bool
    created_at: datetime
    reactions: List[MessageReactionSummary] = []

    class Config:
        from_attributes = True

class ConversationSummary(BaseModel):
    id: int
    other_user: User
    last_message: Optional[Message] = None

class ConversationStart(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

class UserUpdate(BaseModel):
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_content_type: Optional[str] = None
    avatar_size: Optional[int] = None
    only_followers_can_ask: Optional[bool] = None

class AvatarPresignRequest(BaseModel):
    filename: str
    content_type: str
    size: int

class AvatarPresignResponse(BaseModel):
    upload_url: str
    public_url: str
    key: str

class AvatarCleanupRequest(BaseModel):
    key: str

class UserProfile(User):
    followers_count: int = 0
    following_count: int = 0
    is_following: Optional[bool] = None
    is_blocked: Optional[bool] = None

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
    likes_count: int = 0
    is_liked: bool = False

    class Config:
        from_attributes = True

class AnswerReportBase(BaseModel):
    reason: str

class AnswerReportCreate(AnswerReportBase):
    pass

class AnswerReport(AnswerReportBase):
    id: int
    reporter_id: int
    answer_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    content: str
    answer_id: int

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: int
    created_at: datetime
    user: User

    class Config:
        from_attributes = True

# Token Schema
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
