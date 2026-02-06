
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from domain import schemas
from application.services.question_service import QuestionService
from application.services.user_service import UserService
from infrastructure.websockets import manager
from api import deps

router = APIRouter()

@router.post("/", response_model=schemas.Question)
async def create_question(
    question: schemas.QuestionCreate, 
    current_user: schemas.User = Depends(deps.get_current_user),
    question_service: QuestionService = Depends(deps.get_question_service),
    user_service: UserService = Depends(deps.get_user_service)
):
    # Check if receiver exists
    receiver = user_service.get_user(question.receiver_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    new_question = question_service.create_question(question, asker_id=current_user.id)
    
    # Notify receiver
    await manager.send_personal_message("Tienes una nueva pregunta", question.receiver_id)
    
    return new_question

@router.get("/received", response_model=List[schemas.QuestionDisplay])
def read_questions_received(
    skip: int = 0, 
    limit: int = 10, 
    current_user: schemas.User = Depends(deps.get_current_user),
    question_service: QuestionService = Depends(deps.get_question_service)
):
    return question_service.get_questions_received(current_user.id, skip, limit)

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
    current_user: schemas.User = Depends(deps.get_current_user),
    question_service: QuestionService = Depends(deps.get_question_service)
):
    return question_service.get_feed(current_user.id, skip, limit)

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