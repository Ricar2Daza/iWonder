import json
from fastapi.concurrency import run_in_threadpool
from domain import schemas
from infrastructure.cache.redis_client import cache_delete, cache_delete_prefix, cache_get_json, cache_set_json
from infrastructure.repositories.conversation_repository import ConversationRepository
from infrastructure.repositories.message_repository import MessageRepository
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.user_block_repository import UserBlockRepository
from infrastructure.websockets import manager
from datetime import datetime

CONVERSATIONS_TTL_SECONDS = 10
MESSAGES_TTL_SECONDS = 10

class MessageService:
    def __init__(self, conversation_repo: ConversationRepository, message_repo: MessageRepository, user_repo: UserRepository, block_repo: UserBlockRepository):
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.user_repo = user_repo
        self.block_repo = block_repo

    def _conversation_cache_key(self, user_id: int) -> str:
        return f"conversations:{user_id}"

    def _messages_cache_prefix(self, conversation_id: int) -> str:
        return f"messages:{conversation_id}:"

    def _messages_cache_key(self, conversation_id: int, skip: int, limit: int, before: str | None, include_reactions: bool) -> str:
        return f"messages:{conversation_id}:{skip}:{limit}:{before or ''}:{int(include_reactions)}"

    def _get_other_user_id(self, conversation, user_id: int):
        if conversation.user1_id == user_id:
            return conversation.user2_id
        if conversation.user2_id == user_id:
            return conversation.user1_id
        raise ValueError("Not authorized")

    def get_or_create_conversation(self, user_id: int, other_user_id: int):
        other_user = self.user_repo.get_by_id(other_user_id)
        if not other_user:
            raise ValueError("User not found")
        if self.block_repo.is_blocking(user_id, other_user_id) or self.block_repo.is_blocking(other_user_id, user_id):
            raise ValueError("Blocked")
        conversation = self.conversation_repo.get_or_create(user_id, other_user_id)
        cache_delete([self._conversation_cache_key(user_id), self._conversation_cache_key(other_user_id)])
        return conversation

    def get_conversation_summary(self, conversation_id: int, user_id: int):
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError("Not found")
        other_user_id = self._get_other_user_id(conversation, user_id)
        other_user = self.user_repo.get_by_id(other_user_id)
        if not other_user:
            raise ValueError("Not found")
        last_message = self.message_repo.get_last_message(conversation_id)
        return schemas.ConversationSummary(
            id=conversation.id,
            other_user=schemas.User.model_validate(other_user),
            last_message=schemas.Message.model_validate(last_message) if last_message else None
        )

    def list_conversations(self, user_id: int):
        cache_key = self._conversation_cache_key(user_id)
        cached = cache_get_json(cache_key)
        if cached is not None:
            return [schemas.ConversationSummary.model_validate(item) for item in cached]
        conversations = self.conversation_repo.get_for_user(user_id)
        results = []
        for conversation in conversations:
            other_user_id = self._get_other_user_id(conversation, user_id)
            other_user = self.user_repo.get_by_id(other_user_id)
            if not other_user:
                continue
            last_message = self.message_repo.get_last_message(conversation.id)
            summary = schemas.ConversationSummary(
                id=conversation.id,
                other_user=schemas.User.model_validate(other_user),
                last_message=schemas.Message.model_validate(last_message) if last_message else None
            )
            results.append(summary)
        cache_set_json(cache_key, [item.model_dump() for item in results], CONVERSATIONS_TTL_SECONDS)
        return results

    def _build_message_schema(self, message, include_reactions: bool = True):
        message_data = schemas.Message.model_validate(message).model_dump()
        if include_reactions:
            message_data["reactions"] = self.message_repo.get_reaction_summary(message.id)
        else:
            message_data["reactions"] = []
        return schemas.Message(**message_data)

    def get_messages(self, conversation_id: int, user_id: int, skip: int = 0, limit: int = 50, before: str | None = None, include_reactions: bool = True):
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError("Not found")
        self._get_other_user_id(conversation, user_id)
        cache_key = self._messages_cache_key(conversation_id, skip, limit, before, include_reactions)
        cached = cache_get_json(cache_key)
        if cached is not None:
            return [schemas.Message.model_validate(item) for item in cached]
        if before:
            before_created_at, before_id = self._parse_cursor(before)
            messages = self.message_repo.get_by_conversation_before(conversation_id, before_created_at, before_id, limit)
            messages = list(reversed(messages))
        else:
            messages = self.message_repo.get_by_conversation(conversation_id, skip, limit)
        results = [self._build_message_schema(m, include_reactions) for m in messages]
        cache_set_json(cache_key, [item.model_dump() for item in results], MESSAGES_TTL_SECONDS)
        return results

    async def create_message(self, conversation_id: int, sender_id: int, content: str, reply_to_message_id: int | None = None):
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError("Not found")
        receiver_id = self._get_other_user_id(conversation, sender_id)
        if self.block_repo.is_blocking(sender_id, receiver_id) or self.block_repo.is_blocking(receiver_id, sender_id):
            raise ValueError("Blocked")
        new_message = await run_in_threadpool(
            self.message_repo.create,
            conversation_id,
            sender_id,
            receiver_id,
            content,
            reply_to_message_id
        )
        sender = self.user_repo.get_by_id(sender_id)
        sender_payload = None
        if sender:
            sender_payload = {
                "id": sender.id,
                "username": sender.username,
                "avatar_url": sender.avatar_url
            }
        message_schema = self._build_message_schema(new_message)
        payload = json.dumps({
            "type": "dm",
            "conversation_id": conversation_id,
            "message": message_schema.model_dump(),
            "sender": sender_payload
        })
        try:
            await manager.send_personal_message(payload, receiver_id)
            if receiver_id != sender_id:
                await manager.send_personal_message(payload, sender_id)
        except Exception:
            pass
        cache_delete_prefix(self._messages_cache_prefix(conversation_id))
        cache_delete([self._conversation_cache_key(sender_id), self._conversation_cache_key(receiver_id)])
        return message_schema


    def mark_read(self, conversation_id: int, user_id: int):
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError("Not found")
        self._get_other_user_id(conversation, user_id)
        self.message_repo.mark_read(conversation_id, user_id)
        cache_delete_prefix(self._messages_cache_prefix(conversation_id))

    def delete_message(self, message_id: int, user_id: int):
        message = self.message_repo.get_by_id(message_id)
        if not message:
            raise ValueError("Not found")
        conversation = self.conversation_repo.get_by_id(message.conversation_id)
        if not conversation:
            raise ValueError("Not found")
        self._get_other_user_id(conversation, user_id)
        deleted = self.message_repo.delete_message(message_id, user_id)
        cache_delete_prefix(self._messages_cache_prefix(message.conversation_id))
        cache_delete([self._conversation_cache_key(conversation.user1_id), self._conversation_cache_key(conversation.user2_id)])
        return deleted

    def delete_conversation(self, conversation_id: int, user_id: int):
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError("Not found")
        self._get_other_user_id(conversation, user_id)
        self.message_repo.delete_by_conversation(conversation_id)
        deleted = self.conversation_repo.delete_conversation(conversation_id)
        cache_delete_prefix(self._messages_cache_prefix(conversation_id))
        cache_delete([self._conversation_cache_key(conversation.user1_id), self._conversation_cache_key(conversation.user2_id)])
        return deleted

    def add_reaction(self, message_id: int, user_id: int, emoji: str):
        message = self.message_repo.get_by_id(message_id)
        if not message:
            raise ValueError("Not found")
        conversation = self.conversation_repo.get_by_id(message.conversation_id)
        if not conversation:
            raise ValueError("Not found")
        self._get_other_user_id(conversation, user_id)
        self.message_repo.add_reaction(message_id, user_id, emoji)
        cache_delete_prefix(self._messages_cache_prefix(message.conversation_id))
        return self.message_repo.get_reaction_summary(message_id)

    def remove_reaction(self, message_id: int, user_id: int, emoji: str):
        message = self.message_repo.get_by_id(message_id)
        if not message:
            raise ValueError("Not found")
        conversation = self.conversation_repo.get_by_id(message.conversation_id)
        if not conversation:
            raise ValueError("Not found")
        self._get_other_user_id(conversation, user_id)
        self.message_repo.remove_reaction(message_id, user_id, emoji)
        cache_delete_prefix(self._messages_cache_prefix(message.conversation_id))
        return self.message_repo.get_reaction_summary(message_id)

    def _parse_cursor(self, cursor: str):
        raw_created_at, raw_id = cursor.split("|", 1)
        return datetime.fromisoformat(raw_created_at), int(raw_id)
