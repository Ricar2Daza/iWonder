
from sqlalchemy.orm import Session
from datetime import datetime
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

    def get_questions_received_before(self, user_id: int, before_created_at: datetime, before_id: int, limit: int = 10):
        return self.db.query(models.Question)\
            .outerjoin(models.Answer)\
            .filter(models.Question.receiver_id == user_id)\
            .filter(models.Answer.id == None)\
            .filter(
                (models.Question.created_at < before_created_at) |
                ((models.Question.created_at == before_created_at) & (models.Question.id < before_id))
            )\
            .order_by(models.Question.created_at.desc(), models.Question.id.desc())\
            .limit(limit).all()

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

    def get_feed_before(self, user_id: int, before_created_at: datetime, before_id: int, limit: int = 10):
        following = self.db.query(models.Follow).filter(models.Follow.follower_id == user_id).all()
        followed_ids = [f.followed_id for f in following]

        return self.db.query(models.Answer).filter(models.Answer.author_id.in_(followed_ids))\
            .filter(
                (models.Answer.created_at < before_created_at) |
                ((models.Answer.created_at == before_created_at) & (models.Answer.id < before_id))
            )\
            .order_by(models.Answer.created_at.desc(), models.Answer.id.desc())\
            .limit(limit).all()

    def get_user_answers(self, user_id: int, skip: int = 0, limit: int = 10):
        return self.db.query(models.Answer).filter(models.Answer.author_id == user_id)\
            .order_by(models.Answer.created_at.desc())\
            .offset(skip).limit(limit).all()

    def get_user_answers_before(self, user_id: int, before_created_at: datetime, before_id: int, limit: int = 10):
        return self.db.query(models.Answer).filter(models.Answer.author_id == user_id)\
            .filter(
                (models.Answer.created_at < before_created_at) |
                ((models.Answer.created_at == before_created_at) & (models.Answer.id < before_id))
            )\
            .order_by(models.Answer.created_at.desc(), models.Answer.id.desc())\
            .limit(limit).all()
    
    def get_question_by_id(self, question_id: int):
        return self.db.query(models.Question).filter(models.Question.id == question_id).first()

    def get_answer_by_id(self, answer_id: int):
        return self.db.query(models.Answer).filter(models.Answer.id == answer_id).first()

    def delete_question(self, question_id: int):
        question = self.get_question_by_id(question_id)
        if question:
            # Manually delete answers if cascade is not set in DB (SQLAlchemy usually needs cascade='all, delete' in relationship or ON DELETE CASCADE in DB)
            # Assuming DB might not have cascade set up perfect, let's explicit delete answers first? 
            # Or rely on models. 
            # Let's try simple delete. If it fails due to FK, we fix.
            # Usually better to delete answers first.
            self.db.query(models.Answer).filter(models.Answer.question_id == question_id).delete()
            self.db.delete(question)
            self.db.commit()
            return True
        return False

    def like_answer(self, user_id: int, answer_id: int):
        # Check if already liked
        existing = self.db.query(models.AnswerLike).filter(
            models.AnswerLike.user_id == user_id, 
            models.AnswerLike.answer_id == answer_id
        ).first()
        if existing:
            return existing
            
        like = models.AnswerLike(user_id=user_id, answer_id=answer_id)
        self.db.add(like)
        self.db.commit()
        return like

    def unlike_answer(self, user_id: int, answer_id: int):
        self.db.query(models.AnswerLike).filter(
            models.AnswerLike.user_id == user_id,
            models.AnswerLike.answer_id == answer_id
        ).delete()
        self.db.commit()
