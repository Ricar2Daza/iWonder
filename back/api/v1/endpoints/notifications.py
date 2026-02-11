from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from domain import schemas
from application.services.notification_service import NotificationService
from api import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.Notification])
def read_notifications(
    skip: int = 0,
    limit: int = 20,
    current_user: schemas.User = Depends(deps.get_current_user),
    notification_service: NotificationService = Depends(deps.get_notification_service)
):
    return notification_service.get_notifications(current_user.id, skip, limit)

@router.get("/grouped", response_model=List[schemas.NotificationGroup])
def read_grouped_notifications(
    limit: int = 50,
    current_user: schemas.User = Depends(deps.get_current_user),
    notification_service: NotificationService = Depends(deps.get_notification_service)
):
    return notification_service.get_grouped_notifications(current_user.id, limit)

@router.put("/{notification_id}/read", response_model=schemas.Notification)
def mark_notification_read(
    notification_id: int,
    current_user: schemas.User = Depends(deps.get_current_user),
    notification_service: NotificationService = Depends(deps.get_notification_service)
):
    notification = notification_service.mark_as_read(notification_id, current_user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.put("/read-all")
def mark_all_notifications_read(
    current_user: schemas.User = Depends(deps.get_current_user),
    notification_service: NotificationService = Depends(deps.get_notification_service)
):
    notification_service.mark_all_as_read(current_user.id)
    return {"status": "ok"}

@router.put("/read-many")
def mark_many_notifications_read(
    payload: schemas.NotificationReadMany,
    current_user: schemas.User = Depends(deps.get_current_user),
    notification_service: NotificationService = Depends(deps.get_notification_service)
):
    notification_service.mark_many_as_read(current_user.id, payload.notification_ids)
    return {"status": "ok"}
