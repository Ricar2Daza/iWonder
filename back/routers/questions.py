from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import database, schemas, crud, auth, socket_manager, models

router = APIRouter(
    prefix="/questions",
    tags=["questions"]
)

@router.post("/", response_model=schemas.Question)
async def create_question(question: schemas.QuestionCreate, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Check if receiver exists
    receiver = crud.get_user(db, question.receiver_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    new_question = crud.create_question(db=db, question=question, asker_id=current_user.id)
    
    # Notify receiver
    await socket_manager.manager.send_personal_message("Tienes una nueva pregunta", question.receiver_id)
    
    return new_question

@router.get("/received", response_model=List[schemas.QuestionDisplay])
def read_questions_received(skip: int = 0, limit: int = 10, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    questions = crud.get_questions_received(db, user_id=current_user.id, skip=skip, limit=limit)
    return questions

@router.post("/{question_id}/answer", response_model=schemas.Answer)
def create_answer(question_id: int, answer: schemas.AnswerCreate, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Verify question exists and belongs to user (only receiver can answer)
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to answer this question")
        
    return crud.create_answer(db=db, answer=answer, author_id=current_user.id)

@router.get("/feed", response_model=List[schemas.AnswerDisplay])
def get_feed(skip: int = 0, limit: int = 10, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    return crud.get_feed(db, user_id=current_user.id, skip=skip, limit=limit)
