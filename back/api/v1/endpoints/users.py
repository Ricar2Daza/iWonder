
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from domain import schemas
from application.services.user_service import UserService
from application.services.question_service import QuestionService
from infrastructure.websockets import manager
from api import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.UserProfile])
def read_users(
    skip: int = 0, 
    limit: int = 10, 
    user_service: UserService = Depends(deps.get_user_service)
):
    return user_service.get_users(skip=skip, limit=limit)

@router.post("/", response_model=schemas.UserProfile)
def create_user(
    user: schemas.UserCreate, 
    user_service: UserService = Depends(deps.get_user_service)
):
    db_user = user_service.get_user_by_username(user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check email logic if implemented in service/repo
    # For now assume username check is enough for this MVP step or add email check
    # user_service.get_user_by_email...
    
    return user_service.create_user(user)

@router.get("/me", response_model=schemas.UserProfile)
async def read_users_me(current_user: schemas.UserProfile    = Depends(deps.get_current_user)):
    return current_user

@router.get("/search", response_model=List[schemas.UserProfile])
def search_users(
    q: str,
    skip: int = 0, 
    limit: int = 10, 
    user_service: UserService = Depends(deps.get_user_service)
):
    return user_service.search_users(q, skip, limit)

@router.get("/{username}", response_model=schemas.UserProfile)
def read_user(
    username: str, 
    user_service: UserService = Depends(deps.get_user_service),
    current_user: Optional[schemas.UserProfile] = Depends(deps.get_current_user_optional)
):
    db_user = user_service.get_user_by_username(username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Manually populate computed fields if they are not automatic
    # Pydantic's from_attributes should handle properties like followers_count if they exist on the model
    # But for is_following we need to check manually
    
    user_data = jsonable_encoder(db_user)
    
    # Ensure counts are present (in case jsonable_encoder misses properties)
    user_data['followers_count'] = db_user.followers_count
    user_data['following_count'] = db_user.following_count
    
    if current_user:
        # Check if current_user follows db_user
        # We need to access the relationship. 
        # Assuming db_user.followers is a list of User objects
        user_data['is_following'] = any(u.id == current_user.id for u in db_user.followers)
    else:
        user_data['is_following'] = False
        
    return user_data

@router.post("/{username}/follow")
async def follow_user(
    username: str, 
    current_user: schemas.UserProfile = Depends(deps.get_current_user),
    user_service: UserService = Depends(deps.get_user_service)
):
    target_user = user_service.get_user_by_username(username)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        user_service.follow_user(current_user.id, target_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    await manager.send_personal_message(f"{current_user.username} te ha seguido", target_user.id)
    
    return {"status": "ok"}

@router.post("/{username}/unfollow")
async def unfollow_user(
    username: str, 
    current_user: schemas.UserProfile = Depends(deps.get_current_user),
    user_service: UserService = Depends(deps.get_user_service)
):
    target_user = user_service.get_user_by_username(username)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_service.unfollow_user(current_user.id, target_user.id)
    
    return {"status": "ok"}

@router.get("/{username}/answers", response_model=List[schemas.AnswerDisplay])
def read_user_answers(
    username: str, 
    skip: int = 0, 
    limit: int = 10, 
    user_service: UserService = Depends(deps.get_user_service),
    question_service: QuestionService = Depends(deps.get_question_service)
):
    user = user_service.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return question_service.get_user_answers(user.id, skip, limit)