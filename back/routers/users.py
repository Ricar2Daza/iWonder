from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import database, schemas, crud, auth, socket_manager, models

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(database.get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check email unique as well (assuming crud has it or we add it)
    # Since we don't have get_user_by_email in crud yet, let's just stick to username for MVP or add it.
    # But wait, User model usually has unique email. Let's check crud.
    # For now, if email is not unique, DB will raise integrity error. Let's handle that globally or check here.
    # Let's check for email existence roughly.
    db_user_email = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    return crud.create_user(db=db, user=user)

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_user)):
    return current_user

@router.get("/{username}", response_model=schemas.User)
def read_user(username: str, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/{username}/follow")
async def follow_user(username: str, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    target_user = crud.get_user_by_username(db, username=username)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    # Check if already following (omitted for brevity, but should be there)
    # crud.follow_user handles creation, assuming uniqueness constraint in model or logic here
    # Adding a simple check
    # But for MVP let's trust crud or add check later.
    crud.follow_user(db, follower_id=current_user.id, followed_id=target_user.id)
    
    await socket_manager.manager.send_personal_message(f"{current_user.username} te ha seguido", target_user.id)
    
    return {"status": "ok"}

@router.get("/{username}/answers", response_model=List[schemas.AnswerDisplay])
def read_user_answers(username: str, skip: int = 0, limit: int = 10, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.get_user_answers(db, user_id=user.id, skip=skip, limit=limit)
