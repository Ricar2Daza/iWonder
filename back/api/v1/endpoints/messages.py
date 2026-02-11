from typing import List
from fastapi import APIRouter, Depends, HTTPException
from domain import schemas
from application.services.message_service import MessageService
from application.services.user_service import UserService
from api import deps
from infrastructure.cache.rate_limit import is_rate_limited

router = APIRouter()

@router.get("/conversations", response_model=List[schemas.ConversationSummary])
def list_conversations(
    current_user: schemas.User = Depends(deps.get_current_user),
    message_service: MessageService = Depends(deps.get_message_service)
):
    return message_service.list_conversations(current_user.id)

@router.post("/start", response_model=schemas.ConversationSummary)
def start_conversation(
    payload: schemas.ConversationStart,
    current_user: schemas.User = Depends(deps.get_current_user),
    user_service: UserService = Depends(deps.get_user_service),
    message_service: MessageService = Depends(deps.get_message_service)
):
    if payload.user_id:
        other_user = user_service.get_user(payload.user_id)
    elif payload.username:
        other_user = user_service.get_user_by_username(payload.username)
    else:
        raise HTTPException(status_code=400, detail="Missing user target")

    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")
    if other_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Invalid user")
    if user_service.is_blocked_between(current_user.id, other_user.id):
        raise HTTPException(status_code=403, detail="Blocked")

    conversation = message_service.get_or_create_conversation(current_user.id, other_user.id)
    return message_service.get_conversation_summary(conversation.id, current_user.id)

@router.get("/conversations/{conversation_id}/messages", response_model=List[schemas.Message])
def get_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 50,
    before: str | None = None,
    include_reactions: bool = True,
    current_user: schemas.User = Depends(deps.get_current_user),
    message_service: MessageService = Depends(deps.get_message_service)
):
    try:
        messages = message_service.get_messages(conversation_id, current_user.id, skip, limit, before, include_reactions)
        message_service.mark_read(conversation_id, current_user.id)
        return messages
    except ValueError:
        raise HTTPException(status_code=403, detail="Not authorized")

@router.post("/conversations/{conversation_id}/messages", response_model=schemas.Message)
async def send_message(
    conversation_id: int,
    payload: schemas.MessageCreate,
    current_user: schemas.User = Depends(deps.get_current_user),
    message_service: MessageService = Depends(deps.get_message_service)
):
    try:
        if is_rate_limited(f"rl:msg:{current_user.id}", 30, 10):
            raise HTTPException(status_code=429, detail="Too many messages")
        return await message_service.create_message(
            conversation_id,
            current_user.id,
            payload.content,
            payload.reply_to_message_id
        )
    except ValueError:
        raise HTTPException(status_code=403, detail="Not authorized")

@router.put("/conversations/{conversation_id}/read")
def mark_read(
    conversation_id: int,
    current_user: schemas.User = Depends(deps.get_current_user),
    message_service: MessageService = Depends(deps.get_message_service)
):
    try:
        message_service.mark_read(conversation_id, current_user.id)
        return {"status": "ok"}
    except ValueError:
        raise HTTPException(status_code=403, detail="Not authorized")

@router.post("/messages/{message_id}/reactions")
def add_reaction(
    message_id: int,
    payload: schemas.MessageReactionCreate,
    current_user: schemas.User = Depends(deps.get_current_user),
    message_service: MessageService = Depends(deps.get_message_service)
):
    try:
        reactions = message_service.add_reaction(message_id, current_user.id, payload.emoji)
        return {"reactions": reactions}
    except ValueError:
        raise HTTPException(status_code=403, detail="Not authorized")

@router.delete("/messages/{message_id}/reactions")
def remove_reaction(
    message_id: int,
    payload: schemas.MessageReactionCreate,
    current_user: schemas.User = Depends(deps.get_current_user),
    message_service: MessageService = Depends(deps.get_message_service)
):
    try:
        reactions = message_service.remove_reaction(message_id, current_user.id, payload.emoji)
        return {"reactions": reactions}
    except ValueError:
        raise HTTPException(status_code=403, detail="Not authorized")

@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: schemas.User = Depends(deps.get_current_user),
    message_service: MessageService = Depends(deps.get_message_service)
):
    try:
        message_service.delete_conversation(conversation_id, current_user.id)
        return {"status": "ok"}
    except ValueError:
        raise HTTPException(status_code=403, detail="Not authorized")

@router.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    current_user: schemas.User = Depends(deps.get_current_user),
    message_service: MessageService = Depends(deps.get_message_service)
):
    try:
        message_service.delete_message(message_id, current_user.id)
        return {"status": "ok"}
    except ValueError:
        raise HTTPException(status_code=403, detail="Not authorized")
