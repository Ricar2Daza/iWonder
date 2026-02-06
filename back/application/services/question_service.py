
from infrastructure.repositories.question_repository import QuestionRepository
from domain import schemas

class QuestionService:
    def __init__(self, question_repo: QuestionRepository):
        self.question_repo = question_repo

    def create_question(self, question: schemas.QuestionCreate, asker_id: int):
        return self.question_repo.create_question(question, asker_id)

    def get_questions_received(self, user_id: int, skip: int = 0, limit: int = 10):
        return self.question_repo.get_questions_received(user_id, skip, limit)

    def create_answer(self, answer: schemas.AnswerCreate, author_id: int):
        # Verify question exists? Repo might handle foreign key error, but good to check
        # For MVP/Simplicity assume valid
        return self.question_repo.create_answer(answer, author_id)

    def get_feed(self, user_id: int, skip: int = 0, limit: int = 10):
        return self.question_repo.get_feed(user_id, skip, limit)

    def get_user_answers(self, user_id: int, skip: int = 0, limit: int = 10):
        return self.question_repo.get_user_answers(user_id, skip, limit)

    def get_question(self, question_id: int):
        return self.question_repo.get_question_by_id(question_id)