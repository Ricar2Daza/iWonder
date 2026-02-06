from fastapi.testclient import TestClient

def test_read_main(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to iWonder API"}

def test_create_user(client: TestClient):
    response = client.post(
        "/api/v1/users/",
        json={"username": "testuser", "email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data

def test_login_user(client: TestClient):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data["access_token"]

def test_create_question(client: TestClient):
    # First login
    token = test_login_user(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create another user to receive question
    client.post(
        "/api/v1/users/",
        json={"username": "receiver", "email": "receiver@example.com", "password": "password123"}
    )
    # Get receiver id (assuming it is 2, but let's fetch it)
    # Ideally we should have a get_user endpoint or return id
    # Since we cleared DB in fixture, ids start from 1.
    # testuser is 1, receiver is 2.
    
    response = client.post(
        "/api/v1/questions/",
        json={"content": "Hello?", "is_anonymous": True, "receiver_id": 2},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Hello?"
    assert data["receiver_id"] == 2

def test_get_questions_received(client: TestClient):
    # Login as receiver
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "receiver", "password": "password123"}
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/v1/questions/received", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["content"] == "Hello?"

def test_answer_question(client: TestClient):
    # Login as receiver
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "receiver", "password": "password123"}
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get question id
    questions = client.get("/api/v1/questions/received", headers=headers).json()
    q_id = questions[0]["id"]
    
    response = client.post(
        f"/api/v1/questions/{q_id}/answer",
        json={"content": "Hi there!", "question_id": q_id},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Hi there!"

def test_feed(client: TestClient):
    # Login as original user and follow receiver
    token = test_login_user(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Follow receiver (id 2)
    response = client.post("/api/v1/users/receiver/follow", headers=headers)
    assert response.status_code == 200
    
    # Get feed
    response = client.get("/api/v1/questions/feed", headers=headers)
    assert response.status_code == 200
    data = response.json()
    # Should see the answer from receiver
    assert len(data) >= 1
    assert data[0]["content"] == "Hi there!"
