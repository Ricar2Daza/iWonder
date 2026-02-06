from sqlalchemy.orm import Session
from . import models, schemas, utils

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = utils.get_password_hash(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_question(db: Session, question: schemas.QuestionCreate, asker_id: int):
    db_question = models.Question(
        content=question.content,
        is_anonymous=question.is_anonymous,
        receiver_id=question.receiver_id,
        asker_id=asker_id
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def get_questions_received(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.Question)\
        .outerjoin(models.Answer)\
        .filter(models.Question.receiver_id == user_id)\
        .filter(models.Answer.id == None)\
        .order_by(models.Question.created_at.desc())\
        .offset(skip).limit(limit).all()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_answer(db: Session, answer: schemas.AnswerCreate, author_id: int):
    db_answer = models.Answer(
        content=answer.content,
        question_id=answer.question_id,
        author_id=author_id
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer

def follow_user(db: Session, follower_id: int, followed_id: int):
    follow = models.Follow(follower_id=follower_id, followed_id=followed_id)
    db.add(follow)
    db.commit()
    return follow

def get_feed(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    # Feed should show answers from people I follow
    # First get list of people I follow
    following = db.query(models.Follow).filter(models.Follow.follower_id == user_id).all()
    followed_ids = [f.followed_id for f in following]
    
    # Get answers where author_id is in followed_ids
    return db.query(models.Answer).filter(models.Answer.author_id.in_(followed_ids))\
        .order_by(models.Answer.created_at.desc())\
        .offset(skip).limit(limit).all()

def get_user_answers(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.Answer).filter(models.Answer.author_id == user_id)\
        .order_by(models.Answer.created_at.desc())\
        .offset(skip).limit(limit).all()
