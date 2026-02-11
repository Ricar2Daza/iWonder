from infrastructure.repositories.answer_report_repository import AnswerReportRepository
from infrastructure.repositories.question_repository import QuestionRepository
from domain import schemas


class AnswerReportService:
    def __init__(self, report_repo: AnswerReportRepository, question_repo: QuestionRepository):
        self.report_repo = report_repo
        self.question_repo = question_repo

    def create_report(self, reporter_id: int, answer_id: int, report: schemas.AnswerReportCreate):
        answer = self.question_repo.get_answer_by_id(answer_id)
        if not answer:
            raise ValueError("Answer not found")
        return self.report_repo.create(reporter_id, answer_id, report.reason)
