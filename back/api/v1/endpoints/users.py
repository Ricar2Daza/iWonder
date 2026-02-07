
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
    user_service: UserService = Depends(deps.get_user_service),
    current_user: Optional[schemas.UserProfile] = Depends(deps.get_current_user_optional)
):
    users = user_service.get_users(skip=skip, limit=limit)
    
    # Convert to Pydantic models and set is_following
    results = []
    for user in users:
        user_profile = schemas.UserProfile.model_validate(user)
        if current_user:
            user_profile.is_following = any(f.follower_id == current_user.id for f in user.followers)
        else:
            user_profile.is_following = False
        results.append(user_profile)
        
    return results

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
async def read_users_me(current_user: schemas.UserProfile = Depends(deps.get_current_user)):
    return current_user

@router.put("/me", response_model=schemas.UserProfile)
async def update_user_me(
    user_update: schemas.UserUpdate,
    current_user: schemas.UserProfile = Depends(deps.get_current_user),
    user_service: UserService = Depends(deps.get_user_service)
):
    updated_user = user_service.update_user(current_user.id, user_update)
    return updated_user

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
    
    # Use Pydantic's model_validate (V2) to convert SQLAlchemy model to Pydantic model
    # This avoids RecursionError that happens with jsonable_encoder on circular relationships
    user_profile = schemas.UserProfile.model_validate(db_user)
    
    if current_user:
        # Check if current_user follows db_user
        # db_user.followers is a list of Follow objects, not Users
        user_profile.is_following = any(f.follower_id == current_user.id for f in db_user.followers)
    else:
        user_profile.is_following = False
        
    return user_profile

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
        await user_service.follow_user(current_user.id, target_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
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
    question_service: QuestionService = Depends(deps.get_question_service),
    current_user: Optional[schemas.UserProfile] = Depends(deps.get_current_user_optional)
):
    user = user_service.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    viewer_id = current_user.id if current_user else None
    return question_service.get_user_answers(user.id, viewer_id, skip, limit)