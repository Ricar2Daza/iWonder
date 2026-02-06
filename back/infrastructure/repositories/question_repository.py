
from sqlalchemy.orm import Session
from ..db import models
from domain import schemas

class QuestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_question(self, question: schemas.QuestionCreate, asker_id: int):
        db_question = models.Question(
            content=question.content,
            is_anonymous=question.is_anonymous,
            receiver_id=question.receiver_id,
            asker_id=asker_id
        )
        self.db.add(db_question)
        self.db.commit()
        self.db.refresh(db_question)
        return db_question

    def get_questions_received(self, user_id: int, skip: int = 0, limit: int = 10):
        # Filter only unanswered questions
        return self.db.query(models.Question)\
            .outerjoin(models.Answer)\
            .filter(models.Question.receiver_id == user_id)\
            .filter(models.Answer.id == None)\
            .order_by(models.Question.created_at.desc())\
            .offset(skip).limit(limit).all()

    def create_answer(self, answer: schemas.AnswerCreate, author_id: int):
        db_answer = models.Answer(
            content=answer.content,
            question_id=answer.question_id,
            author_id=author_id
        )
        self.db.add(db_answer)
        self.db.commit()
        self.db.refresh(db_answer)
        return db_answer

    def get_feed(self, user_id: int, skip: int = 0, limit: int = 10):
        # Feed should show answers from people I follow
        following = self.db.query(models.Follow).filter(models.Follow.follower_id == user_id).all()
        followed_ids = [f.followed_id for f in following]
        
        return self.db.query(models.Answer).filter(models.Answer.author_id.in_(followed_ids))\
            .order_by(models.Answer.created_at.desc())\
            .offset(skip).limit(limit).all()

    def get_user_answers(self, user_id: int, skip: int = 0, limit: int = 10):
        return self.db.query(models.Answer).filter(models.Answer.author_id == user_id)\
            .order_by(models.Answer.created_at.desc())\
            .offset(skip).limit(limit).all()
    
    def get_question_by_id(self, question_id: int):
        return self.db.query(models.Question).filter(models.Question.id == question_id).first()