
from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from infrastructure.db import models
from infrastructure.db.session import engine
from infrastructure.websockets import manager
from api.v1.endpoints import auth, users, questions, notifications, messages, reports
from api import deps

# Create tables
models.Base.metadata.create_all(bind=engine)

# Manual migration for new columns (safe to run multiple times)
from sqlalchemy import text
def run_migrations():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS bio VARCHAR"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_content_type VARCHAR"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_size INTEGER"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS only_followers_can_ask BOOLEAN DEFAULT FALSE"))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    user1_id INTEGER REFERENCES users(id),
                    user2_id INTEGER REFERENCES users(id),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS direct_messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id INTEGER REFERENCES conversations(id),
                    sender_id INTEGER REFERENCES users(id),
                    receiver_id INTEGER REFERENCES users(id),
                    reply_to_message_id INTEGER REFERENCES direct_messages(id),
                    content TEXT,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            conn.execute(text("ALTER TABLE direct_messages ADD COLUMN IF NOT EXISTS reply_to_message_id INTEGER"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_direct_messages_conversation_id ON direct_messages (conversation_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_direct_messages_sender_id ON direct_messages (sender_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_direct_messages_receiver_id ON direct_messages (receiver_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_direct_messages_created_at ON direct_messages (created_at)"))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS message_reactions (
                    id SERIAL PRIMARY KEY,
                    message_id INTEGER REFERENCES direct_messages(id),
                    user_id INTEGER REFERENCES users(id),
                    emoji VARCHAR,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_message_reactions_message_id ON message_reactions (message_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_message_reactions_message_id_emoji ON message_reactions (message_id, emoji)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_conversations_user1_id ON conversations (user1_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_conversations_user2_id ON conversations (user2_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications (user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications (created_at)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_questions_receiver_id ON questions (receiver_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_questions_created_at ON questions (created_at)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_answers_author_id ON answers (author_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_answers_created_at ON answers (created_at)"))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS answer_reports (
                    id SERIAL PRIMARY KEY,
                    reporter_id INTEGER REFERENCES users(id),
                    answer_id INTEGER REFERENCES answers(id),
                    reason TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_answer_reports_answer_id ON answer_reports (answer_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_answer_reports_reporter_id ON answer_reports (reporter_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_follows_follower_id ON follows (follower_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_follows_followed_id ON follows (followed_id)"))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_blocks (
                    id SERIAL PRIMARY KEY,
                    blocker_id INTEGER REFERENCES users(id),
                    blocked_id INTEGER REFERENCES users(id),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_blocks_blocker_id ON user_blocks (blocker_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_blocks_blocked_id ON user_blocks (blocked_id)"))
            conn.commit()
            print("Migrations executed successfully")
        except Exception as e:
            print(f"Migration warning: {e}")

run_migrations()

app = FastAPI(title="iWonder API", version="1.0.0")

app.add_middleware(GZipMiddleware, minimum_size=800)

# CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["questions"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["messages"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    # Ideally verify user here using token in query param if possible, 
    # but for now just connect.
    await manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except:
        manager.disconnect(websocket, user_id)

@app.get("/")
def read_root():
    return {"message": "Welcome to iWonder API"}
