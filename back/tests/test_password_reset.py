import pytest
from datetime import datetime, timedelta
from infrastructure.db import models
from core.security import get_password_hash

def test_password_reset_flow(client, db):
    # 1. Create a user
    email = "reset@example.com"
    password = "OldPassword123!"
    # Ensure user doesn't exist
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        db.delete(existing)
        db.commit()

    user = models.User(
        email=email,
        username="resetuser",
        hashed_password=get_password_hash(password),
        # full_name="Reset User",
        # is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 2. Request reset for non-existent email
    response = client.post("/api/v1/auth/forgot-password", json={"email": "wrong@example.com"})
    assert response.status_code == 200
    assert response.json()["message"] == "If the email exists, a password reset link has been sent."

    # 3. Request reset for existing email
    response = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert response.status_code == 200
    
    # Verify token created in DB
    reset_entry = db.query(models.PasswordReset).filter(models.PasswordReset.user_id == user.id).order_by(models.PasswordReset.created_at.desc()).first()
    assert reset_entry is not None
    assert reset_entry.is_used is False
    token = reset_entry.token

    # 4. Rate limiting
    # We already made 1 request. Let's make 2 more (total 3).
    client.post("/api/v1/auth/forgot-password", json={"email": email})
    client.post("/api/v1/auth/forgot-password", json={"email": email})
    
    # Verify we have 3 tokens
    count = db.query(models.PasswordReset).filter(models.PasswordReset.user_id == user.id).count()
    assert count == 3

    # 4th request should still return 200 but NOT create a new token
    response = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert response.status_code == 200
    final_count = db.query(models.PasswordReset).filter(models.PasswordReset.user_id == user.id).count()
    assert final_count == 3

    # 5. Reset with invalid token
    response = client.post("/api/v1/auth/reset-password", json={
        "token": "invalid_token",
        "new_password": "NewPassword123!",
        "confirm_password": "NewPassword123!"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid token"

    # 6. Reset with valid token
    # Use the latest token
    new_password = "NewPassword123!"
    response = client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": new_password,
        "confirm_password": new_password
    })
    assert response.status_code == 200
    assert response.json()["message"] == "Password has been reset successfully."

    # Verify password changed (try login)
    login_response = client.post("/api/v1/auth/token", data={
        "username": "resetuser",
        "password": new_password
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

    # Verify old password doesn't work
    login_response_old = client.post("/api/v1/auth/token", data={
        "username": "resetuser",
        "password": password
    })
    assert login_response_old.status_code == 401

    # 7. Reuse token
    response = client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "new_password": "AnotherPassword123!",
        "confirm_password": "AnotherPassword123!"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Token already used"

    # 8. Weak password
    # Create a new token manually for testing
    user_reset = models.PasswordReset(
        user_id=user.id,
        token="weak_pass_token",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db.add(user_reset)
    db.commit()

    response = client.post("/api/v1/auth/reset-password", json={
        "token": "weak_pass_token",
        "new_password": "weak",
        "confirm_password": "weak"
    })
    # This should be 422 Unprocessable Entity due to Pydantic validation
    assert response.status_code == 422

    # 9. Mismatched passwords
    response = client.post("/api/v1/auth/reset-password", json={
        "token": "weak_pass_token",
        "new_password": "NewPassword123!",
        "confirm_password": "MismatchPassword123!"
    })
    assert response.status_code == 400
    assert "Passwords do not match" in response.json()["detail"]

    # 10. Expired token
    expired_token = models.PasswordReset(
        user_id=user.id,
        token="expired_token",
        expires_at=datetime.utcnow() - timedelta(hours=1)
    )
    db.add(expired_token)
    db.commit()

    response = client.post("/api/v1/auth/reset-password", json={
        "token": "expired_token",
        "new_password": "NewPassword123!",
        "confirm_password": "NewPassword123!"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Token expired"
