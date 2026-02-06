
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

    def delete_question(self, question_id: int, user_id: int):
        question = self.get_question(question_id)
        if not question:
            raise ValueError("Question not found")
        
        # Allow deletion if user is the receiver (it's on their profile or inbox)
        # We could also allow asker to delete if it's not answered yet, but requirement focuses on receiver
        if question.receiver_id != user_id:
             raise ValueError("Not authorized to delete this question")
             
        return self.question_repo.delete_question(question_id)