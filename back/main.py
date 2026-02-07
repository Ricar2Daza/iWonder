
from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from infrastructure.db import models
from infrastructure.db.session import engine
from infrastructure.websockets import manager
from api.v1.endpoints import auth, users, questions, notifications
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
            conn.commit()
            print("Migrations executed successfully")
        except Exception as e:
            print(f"Migration warning: {e}")

run_migrations()

app = FastAPI(title="iWonder API", version="1.0.0")

# CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
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