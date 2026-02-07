
from fastapi.testclient import TestClient

def get_auth_headers(client: TestClient, username, email, password):
    # Create user if not exists (ignore error)
    res = client.post(
        "/api/v1/users/",
        json={"username": username, "email": email, "password": password}
    )
    if res.status_code != 200:
        print(f"Create user failed: {res.json()}")
    
    # Login
    response = client.post(
        "/api/v1/auth/token",
        data={"username": username, "password": password}
    )
    if response.status_code != 200:
        print(f"Login failed: {response.json()}")
        
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_comment_flow(client: TestClient):
    # Setup users
    headers_u1 = get_auth_headers(client, "user_one", "user1@example.com", "Password123!")
    headers_u2 = get_auth_headers(client, "user_two", "user2@example.com", "Password123!")
    
    # Get user 2 id
    users = client.get("/api/v1/users/").json()
    u2_id = [u["id"] for u in users if u["username"] == "user_two"][0]
    
    # U1 asks U2
    q_res = client.post(
        "/api/v1/questions/",
        json={"content": "Q?", "receiver_id": u2_id},
        headers=headers_u1
    )
    assert q_res.status_code == 200
    q_id = q_res.json()["id"]
    
    # U2 answers
    a_res = client.post(
        f"/api/v1/questions/{q_id}/answer",
        json={"content": "A!", "question_id": q_id},
        headers=headers_u2
    )
    assert a_res.status_code == 200
    a_id = a_res.json()["id"]
    
    # U1 comments
    c_res = client.post(
        f"/api/v1/questions/answers/{a_id}/comments",
        json={"content": "Nice!", "answer_id": a_id},
        headers=headers_u1
    )
    assert c_res.status_code == 200
    c_id = c_res.json()["id"]
    
    # U2 tries to delete U1's comment -> 403
    del_res = client.delete(
        f"/api/v1/questions/comments/{c_id}",
        headers=headers_u2
    )
    assert del_res.status_code == 403
    
    # U1 deletes -> 200
    del_res_2 = client.delete(
        f"/api/v1/questions/comments/{c_id}",
        headers=headers_u1
    )
    assert del_res_2.status_code == 200
