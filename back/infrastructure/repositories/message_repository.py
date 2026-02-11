from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from ..db import models

class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, conversation_id: int, sender_id: int, receiver_id: int, content: str, reply_to_message_id: int | None = None):
        message = models.DirectMessage(
            conversation_id=conversation_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            reply_to_message_id=reply_to_message_id,
            content=content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_by_conversation(self, conversation_id: int, skip: int = 0, limit: int = 50):
        return self.db.query(models.DirectMessage).filter(
            models.DirectMessage.conversation_id == conversation_id
        ).order_by(models.DirectMessage.created_at.asc()).offset(skip).limit(limit).all()

    def get_by_conversation_before(self, conversation_id: int, before_created_at: datetime, before_id: int, limit: int = 50):
        return self.db.query(models.DirectMessage).filter(
            models.DirectMessage.conversation_id == conversation_id
        ).filter(
            (models.DirectMessage.created_at < before_created_at) |
            ((models.DirectMessage.created_at == before_created_at) & (models.DirectMessage.id < before_id))
        ).order_by(models.DirectMessage.created_at.desc(), models.DirectMessage.id.desc()).limit(limit).all()

    def get_by_id(self, message_id: int):
        return self.db.query(models.DirectMessage).filter(models.DirectMessage.id == message_id).first()

    def get_last_message(self, conversation_id: int):
        return self.db.query(models.DirectMessage).filter(
            models.DirectMessage.conversation_id == conversation_id
        ).order_by(models.DirectMessage.created_at.desc()).first()

    def mark_read(self, conversation_id: int, user_id: int):
        self.db.query(models.DirectMessage).filter(
            models.DirectMessage.conversation_id == conversation_id,
            models.DirectMessage.receiver_id == user_id,
            models.DirectMessage.is_read == False
        ).update({"is_read": True})
        self.db.commit()

    def delete_message(self, message_id: int, user_id: int):
        message = self.get_by_id(message_id)
        if not message:
            return None
        if message.sender_id != user_id:
            raise ValueError("Not authorized")
        self.db.query(models.MessageReaction).filter(
            models.MessageReaction.message_id == message_id
        ).delete()
        self.db.delete(message)
        self.db.commit()
        return message

    def delete_by_conversation(self, conversation_id: int):
        message_ids = [m.id for m in self.db.query(models.DirectMessage.id).filter(
            models.DirectMessage.conversation_id == conversation_id
        ).all()]
        if message_ids:
            self.db.query(models.MessageReaction).filter(
                models.MessageReaction.message_id.in_(message_ids)
            ).delete(synchronize_session=False)
        self.db.query(models.DirectMessage).filter(
            models.DirectMessage.conversation_id == conversation_id
        ).delete()
        self.db.commit()

    def add_reaction(self, message_id: int, user_id: int, emoji: str):
        exists = self.db.query(models.MessageReaction).filter(
            models.MessageReaction.message_id == message_id,
            models.MessageReaction.user_id == user_id,
            models.MessageReaction.emoji == emoji
        ).first()
        if exists:
            return exists
        reaction = models.MessageReaction(message_id=message_id, user_id=user_id, emoji=emoji)
        self.db.add(reaction)
        self.db.commit()
        return reaction

    def remove_reaction(self, message_id: int, user_id: int, emoji: str):
        self.db.query(models.MessageReaction).filter(
            models.MessageReaction.message_id == message_id,
            models.MessageReaction.user_id == user_id,
            models.MessageReaction.emoji == emoji
        ).delete()
        self.db.commit()

    def get_reaction_summary(self, message_id: int):
        rows = self.db.query(models.MessageReaction.emoji, func.count(models.MessageReaction.id)).filter(
            models.MessageReaction.message_id == message_id
        ).group_by(models.MessageReaction.emoji).all()
        return [{"emoji": r[0], "count": r[1]} for r in rows]
