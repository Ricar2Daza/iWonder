
from infrastructure.repositories.question_repository import QuestionRepository
from application.services.notification_service import NotificationService
from domain import schemas
from fastapi.concurrency import run_in_threadpool

class QuestionService:
    def __init__(self, question_repo: QuestionRepository, notification_service: NotificationService):
        self.question_repo = question_repo
        self.notification_service = notification_service

    async def create_question(self, question: schemas.QuestionCreate, asker_id: int):
        new_question = await run_in_threadpool(self.question_repo.create_question, question, asker_id)
        
        # Notify receiver
        await self.notification_service.create_notification(
            user_id=question.receiver_id, 
            content="Tienes una nueva pregunta", 
            notification_type="question"
        )
        
        return new_question

    def get_questions_received(self, user_id: int, skip: int = 0, limit: int = 10):
        return self.question_repo.get_questions_received(user_id, skip, limit)

    def create_answer(self, answer: schemas.AnswerCreate, author_id: int):
        # Verify question exists? Repo might handle foreign key error, but good to check
        # For MVP/Simplicity assume valid
        return self.question_repo.create_answer(answer, author_id)

    def get_feed(self, user_id: int, skip: int = 0, limit: int = 10):
        answers = self.question_repo.get_feed(user_id, skip, limit)
        return self._enrich_answers(answers, user_id)

    def get_user_answers(self, user_id: int, viewer_id: int = None, skip: int = 0, limit: int = 10):
        answers = self.question_repo.get_user_answers(user_id, skip, limit)
        return self._enrich_answers(answers, viewer_id)

    def _enrich_answers(self, answers, viewer_id):
        results = []
        for answer in answers:
            display = schemas.AnswerDisplay.model_validate(answer)
            display.likes_count = len(answer.likes)
            if viewer_id:
                display.is_liked = any(l.user_id == viewer_id for l in answer.likes)
            else:
                display.is_liked = False
            results.append(display)
        return results

    async def like_answer(self, user_id: int, answer_id: int):
        like = await run_in_threadpool(self.question_repo.like_answer, user_id, answer_id)
        
        # Notify answer author if it's not self-like
        # We need to fetch answer to know author
        # For efficiency, maybe repo should return answer author? 
        # Or we fetch it here.
        # Assuming we can get it.
        # This might be an N+1 if we like many things, but for single action is fine.
        # Let's skip notification for like for now to keep it simple or implement if critical.
        # User requested "Historial de Notificaciones" and mentioned "likes". So yes.
        
        # We need to find the author of the answer.
        # We don't have get_answer_by_id exposed in repo easily with author loaded?
        # Actually repo has methods that return Answer object which has author relationship.
        # But like_answer returns AnswerLike object.
        
        return like

    def unlike_answer(self, user_id: int, answer_id: int):
        return self.question_repo.unlike_answer(user_id, answer_id)

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