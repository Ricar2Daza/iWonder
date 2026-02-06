import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
from fastapi.testclient import TestClient

# Adjust import based on how pytest runs. 
# Usually if run from 'back' folder, it works if back is package or we add to path.
# But better to treat 'back' as a package.
import sys
import os
# Add the project root (parent of 'back') to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from back.infrastructure.db.session import Base

from back.api.deps import get_db
from back.main import app

# Use SQLite in-memory for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        # remove file if exists
        try:
            if os.path.exists("./test.db"):
                os.remove("./test.db")
        except PermissionError:
            pass

@pytest.fixture(scope="module")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
