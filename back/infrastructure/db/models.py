
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from infrastructure.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    bio = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    avatar_content_type = Column(String, nullable=True)
    avatar_size = Column(Integer, nullable=True)
    only_followers_can_ask = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Questions asked by this user
    questions_asked = relationship("Question", back_populates="asker", foreign_keys="Question.asker_id")
    # Questions received by this user
    questions_received = relationship("Question", back_populates="receiver", foreign_keys="Question.receiver_id")
    
    answers = relationship("Answer", back_populates="author")
    comments = relationship("Comment", back_populates="user")
    liked_answers = relationship("AnswerLike", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    password_resets = relationship("PasswordReset", back_populates="user")
   
    # Follow system
    followers = relationship(
        "Follow",
        foreign_keys="Follow.followed_id",
        back_populates="followed"
    )
    following = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower"
    )

    @property
    def followers_count(self):
        return len(self.followers)

    @property
    def following_count(self):
        return len(self.following)

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, index=True)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    asker_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))

    asker = relationship("User", back_populates="questions_asked", foreign_keys=[asker_id])
    receiver = relationship("User", back_populates="questions_received", foreign_keys=[receiver_id])
    
    answers = relationship("Answer", back_populates="question")

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    question_id = Column(Integer, ForeignKey("questions.id"))
    author_id = Column(Integer, ForeignKey("users.id"))

    question = relationship("Question", back_populates="answers")
    author = relationship("User", back_populates="answers")
    likes = relationship("AnswerLike", back_populates="answer")
    comments = relationship("Comment", back_populates="answer")
    reports = relationship("AnswerReport", back_populates="answer")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user_id = Column(Integer, ForeignKey("users.id"))
    answer_id = Column(Integer, ForeignKey("answers.id"))

    user = relationship("User", back_populates="comments")
    answer = relationship("Answer", back_populates="comments")

class Follow(Base):
    __tablename__ = "follows"

    follower_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    followed_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    followed = relationship("User", foreign_keys=[followed_id], back_populates="followers")

class UserBlock(Base):
    __tablename__ = "user_blocks"

    id = Column(Integer, primary_key=True, index=True)
    blocker_id = Column(Integer, ForeignKey("users.id"))
    blocked_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    blocker = relationship("User", foreign_keys=[blocker_id])
    blocked = relationship("User", foreign_keys=[blocked_id])

class AnswerLike(Base):
    __tablename__ = "answer_likes"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    answer_id = Column(Integer, ForeignKey("answers.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="liked_answers")
    answer = relationship("Answer", back_populates="likes")

class AnswerReport(Base):
    __tablename__ = "answer_reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"))
    answer_id = Column(Integer, ForeignKey("answers.id"))
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reporter = relationship("User")
    answer = relationship("Answer", back_populates="reports")


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True))
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="password_resets")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notification_type = Column(String, default="info") # follow, question, answer, like
    
    user = relationship("User", back_populates="notifications")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"))
    user2_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
    messages = relationship("DirectMessage", back_populates="conversation")

class DirectMessage(Base):
    __tablename__ = "direct_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    reply_to_message_id = Column(Integer, ForeignKey("direct_messages.id"), nullable=True)
    content = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
    reply_to = relationship("DirectMessage", remote_side=[id])
    reactions = relationship("MessageReaction", back_populates="message", cascade="all, delete-orphan")

class MessageReaction(Base):
    __tablename__ = "message_reactions"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("direct_messages.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    emoji = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship("DirectMessage", back_populates="reactions")
    user = relationship("User")
