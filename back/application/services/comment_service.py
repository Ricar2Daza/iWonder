from infrastructure.repositories.comment_repository import CommentRepository
from infrastructure.repositories.question_repository import QuestionRepository
from infrastructure.repositories.user_repository import UserRepository
from application.services.notification_service import NotificationService
from domain import schemas
from fastapi.concurrency import run_in_threadpool

class CommentService:
    def __init__(self, comment_repo: CommentRepository, question_repo: QuestionRepository, user_repo: UserRepository, notification_service: NotificationService):
        self.comment_repo = comment_repo
        self.question_repo = question_repo
        self.user_repo = user_repo
        self.notification_service = notification_service

    async def create_comment(self, comment: schemas.CommentCreate, user_id: int):
        new_comment = await run_in_threadpool(self.comment_repo.create, comment, user_id)
        
        # Notify answer author
        answer = await run_in_threadpool(self.question_repo.get_answer_by_id, comment.answer_id)
        if answer and answer.author_id != user_id:
             user = await run_in_threadpool(self.user_repo.get_by_id, user_id)
             username = user.username if user else "Alguien"
             await self.notification_service.create_notification(
                user_id=answer.author_id,
                content=f"{username} comentó tu respuesta",
                notification_type="comment"
             )
        
        return new_comment

    def get_comments(self, answer_id: int, skip: int = 0, limit: int = 10):
        return self.comment_repo.get_by_answer_id(answer_id, skip, limit)
    
    async def delete_comment(self, comment_id: int, user_id: int):
        comment = await run_in_threadpool(self.comment_repo.get_by_id, comment_id)
        if not comment:
            return False
        
        if comment.user_id != user_id:
            raise ValueError("Not authorized")
            
        await run_in_threadpool(self.comment_repo.delete, comment_id)
        return True