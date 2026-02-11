from sqlalchemy.orm import Session
from ..db import models

class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, conversation_id: int):
        return self.db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()

    def get_or_create(self, user1_id: int, user2_id: int):
        u1, u2 = (user1_id, user2_id) if user1_id < user2_id else (user2_id, user1_id)
        conversation = self.db.query(models.Conversation).filter(
            models.Conversation.user1_id == u1,
            models.Conversation.user2_id == u2
        ).first()
        if conversation:
            return conversation
        conversation = models.Conversation(user1_id=u1, user2_id=u2)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_for_user(self, user_id: int, skip: int = 0, limit: int = 50):
        return self.db.query(models.Conversation).filter(
            (models.Conversation.user1_id == user_id) | (models.Conversation.user2_id == user_id)
        ).order_by(models.Conversation.created_at.desc()).offset(skip).limit(limit).all()

    def delete_conversation(self, conversation_id: int):
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            return None
        self.db.delete(conversation)
        self.db.commit()
        return conversation