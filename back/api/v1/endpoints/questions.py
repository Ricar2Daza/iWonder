
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from domain import schemas
from application.services.question_service import QuestionService
from application.services.user_service import UserService
from application.services.comment_service import CommentService
from infrastructure.websockets import manager
from api import deps
from infrastructure.cache.rate_limit import is_rate_limited

router = APIRouter()

@router.post("/", response_model=schemas.Question)
async def create_question(
    question: schemas.QuestionCreate, 
    current_user: schemas.User = Depends(deps.get_current_user),
    question_service: QuestionService = Depends(deps.get_question_service),
    user_service: UserService = Depends(deps.get_user_service)
):
    if is_rate_limited(f"rl:question:{current_user.id}", 10, 60):
        raise HTTPException(status_code=429, detail="Too many questions")
    # Check if receiver exists
    receiver = user_service.get_user(question.receiver_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    if user_service.is_blocked_between(current_user.id, receiver.id):
        raise HTTPException(status_code=403, detail="Blocked")
    if receiver.only_followers_can_ask and receiver.id != current_user.id:
        if not user_service.is_following(current_user.id, receiver.id):
            raise HTTPException(status_code=403, detail="Only followers can ask this user")
    
    new_question = await question_service.create_question(question, asker_id=current_user.id)
    
    return new_question

@router.get("/received", response_model=List[schemas.QuestionDisplay])
def read_questions_received(
    skip: int = 0, 
    limit: int = 10, 
    before: str | None = None,
    current_user: schemas.User = Depends(deps.get_current_user),
    question_service: QuestionService = Depends(deps.get_question_service)
):
    return question_service.get_questions_received(current_user.id, skip, limit, before)

@router.post("/{question_id}/answer", response_model=schemas.Answer)
def create_answer(
    question_id: int, 
    answer: schemas.AnswerCreate, 
    current_user: schemas.User = Depends(deps.get_current_user),
    question_service: QuestionService = Depends(deps.get_question_service)
):
    question = question_service.get_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if question.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to answer this question")
        
    return question_service.create_answer(answer, author_id=current_user.id)

@router.get("/feed", response_model=List[schemas.AnswerDisplay])
def get_feed(
    skip: int = 0, 
    limit: int = 10, 
    before: str | None = None,
    current_user: schemas.User = Depends(deps.get_current_user),
    question_service: QuestionService = Depends(deps.get_question_service)
):
    return question_service.get_feed(current_user.id, skip, limit, before)

@router.delete("/{question_id}")
def delete_question(
    question_id: int,
    current_user: schemas.User = Depends(deps.get_current_user),
    question_service: QuestionService = Depends(deps.get_question_service)
):
    try:
        question_service.delete_question(question_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return {"status": "ok"}

@router.post("/answers/{answer_id}/like")
def like_answer(
    answer_id: int,
    current_user: schemas.User = Depends(deps.get_current_user),
    question_service: QuestionService = Depends(deps.get_question_service)
):
    question_service.like_answer(current_user.id, answer_id)
    return {"status": "ok"}

@router.delete("/answers/{answer_id}/like")
def unlike_answer(
    answer_id: int,
    current_user: schemas.User = Depends(deps.get_current_user),
    question_service: QuestionService = Depends(deps.get_question_service)
):
    question_service.unlike_answer(current_user.id, answer_id)
    return {"status": "ok"}

@router.post("/answers/{answer_id}/comments", response_model=schemas.Comment)
async def create_comment(
    answer_id: int,
    comment: schemas.CommentBase,
    current_user: schemas.User = Depends(deps.get_current_user),
    comment_service: CommentService = Depends(deps.get_comment_service)
):
    # Ensure answer_id in path matches body or ignore body answer_id
    comment_in = schemas.CommentCreate(content=comment.content, answer_id=answer_id)
    return await comment_service.create_comment(comment_in, user_id=current_user.id)

@router.get("/answers/{answer_id}/comments", response_model=List[schemas.Comment])
def get_comments(
    answer_id: int,
    skip: int = 0,
    limit: int = 20,
    comment_service: CommentService = Depends(deps.get_comment_service)
):
    return comment_service.get_comments(answer_id, skip, limit)

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: schemas.User = Depends(deps.get_current_user),
    comment_service: CommentService = Depends(deps.get_comment_service)
):
    try:
        success = await comment_service.delete_comment(comment_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Comment not found")
    except ValueError:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
        
    return {"status": "ok"}
