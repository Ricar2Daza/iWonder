
from typing import List, Optional
from pathlib import Path
from uuid import uuid4
import mimetypes
import boto3
from botocore.config import Config
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from core.config import settings
from domain import schemas
from application.services.user_service import UserService
from application.services.question_service import QuestionService
from infrastructure.websockets import manager
from api import deps

router = APIRouter()

def _get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name=settings.R2_REGION,
        config=Config(signature_version="s3v4"),
    )

def _build_public_url(key: str):
    base = (settings.R2_PUBLIC_BASE_URL or "").rstrip("/")
    return f"{base}/{key}"

def _extract_r2_key(url: Optional[str]):
    if not url or not settings.R2_PUBLIC_BASE_URL:
        return None
    base = settings.R2_PUBLIC_BASE_URL.rstrip("/")
    if not url.startswith(base + "/"):
        return None
    return url[len(base) + 1:]

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
    update_data = user_update.model_dump(exclude_unset=True)
    old_avatar_url = current_user.avatar_url
    new_avatar_url = update_data.get("avatar_url") if "avatar_url" in update_data else None

    updated_user = user_service.update_user(current_user.id, user_update)

    if "avatar_url" in update_data and old_avatar_url:
        should_delete = (not new_avatar_url) or (new_avatar_url != old_avatar_url)
        if should_delete:
            key = _extract_r2_key(old_avatar_url)
            if key and settings.R2_BUCKET and settings.R2_ENDPOINT_URL and settings.R2_ACCESS_KEY_ID and settings.R2_SECRET_ACCESS_KEY:
                client = _get_r2_client()
                client.delete_object(Bucket=settings.R2_BUCKET, Key=key)

    return updated_user
    
@router.post("/me/avatar/presign", response_model=schemas.AvatarPresignResponse)
def create_avatar_presign(
    payload: schemas.AvatarPresignRequest,
    current_user: schemas.UserProfile = Depends(deps.get_current_user)
):
    if not settings.R2_ENDPOINT_URL or not settings.R2_ACCESS_KEY_ID or not settings.R2_SECRET_ACCESS_KEY or not settings.R2_BUCKET or not settings.R2_PUBLIC_BASE_URL:
        raise HTTPException(status_code=500, detail="R2 not configured")

    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if payload.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    if payload.size <= 0 or payload.size > settings.R2_MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large")

    ext = Path(payload.filename).suffix
    if not ext:
        ext = mimetypes.guess_extension(payload.content_type) or ""

    key = f"avatars/{current_user.id}/{uuid4().hex}{ext}"
    client = _get_r2_client()

    upload_url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.R2_BUCKET,
            "Key": key,
            "ContentType": payload.content_type,
        },
        ExpiresIn=settings.R2_PRESIGN_EXPIRES_SECONDS,
    )

    public_url = _build_public_url(key)

    return schemas.AvatarPresignResponse(upload_url=upload_url, public_url=public_url, key=key)

@router.post("/me/avatar/cleanup")
def cleanup_avatar_object(
    payload: schemas.AvatarCleanupRequest,
    current_user: schemas.UserProfile = Depends(deps.get_current_user)
):
    if not settings.R2_ENDPOINT_URL or not settings.R2_ACCESS_KEY_ID or not settings.R2_SECRET_ACCESS_KEY or not settings.R2_BUCKET:
        raise HTTPException(status_code=500, detail="R2 not configured")

    allowed_prefix = f"avatars/{current_user.id}/"
    if not payload.key.startswith(allowed_prefix):
        raise HTTPException(status_code=403, detail="Not allowed")

    client = _get_r2_client()
    client.delete_object(Bucket=settings.R2_BUCKET, Key=payload.key)

    return {"status": "ok"}

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