from fastapi import APIRouter, Depends, HTTPException
from domain import schemas
from application.services.answer_report_service import AnswerReportService
from api import deps

router = APIRouter()


@router.post("/answers/{answer_id}", response_model=schemas.AnswerReport)
def report_answer(
    answer_id: int,
    payload: schemas.AnswerReportCreate,
    current_user: schemas.User = Depends(deps.get_current_user),
    report_service: AnswerReportService = Depends(deps.get_answer_report_service)
):
    try:
        return report_service.create_report(current_user.id, answer_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
