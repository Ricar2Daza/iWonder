from sqlalchemy.orm import Session
from ..db import models


class AnswerReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, reporter_id: int, answer_id: int, reason: str):
        report = models.AnswerReport(
            reporter_id=reporter_id,
            answer_id=answer_id,
            reason=reason
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report
