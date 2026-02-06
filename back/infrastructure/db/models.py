
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Questions asked by this user
    questions_asked = relationship("Question", back_populates="asker", foreign_keys="Question.asker_id")
    # Questions received by this user
    questions_received = relationship("Question", back_populates="receiver", foreign_keys="Question.receiver_id")
    
    answers = relationship("Answer", back_populates="author")
    
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

class Follow(Base):
    __tablename__ = "follows"

    follower_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    followed_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    followed = relationship("User", foreign_keys=[followed_id], back_populates="followers")