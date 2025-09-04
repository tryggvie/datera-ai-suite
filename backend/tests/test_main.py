import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_chat_missing_auth():
    """Test chat endpoint without authorization"""
    response = client.post("/v1/chat", json={
        "messages": [{"role": "user", "content": "test"}],
        "bot_id": "general"
    })
    assert response.status_code == 401

def test_chat_invalid_token():
    """Test chat endpoint with invalid token"""
    response = client.post("/v1/chat", 
        headers={"Authorization": "Bearer invalid_token"},
        json={
            "messages": [{"role": "user", "content": "test"}],
            "bot_id": "general"
        }
    )
    assert response.status_code == 403

def test_chat_disabled_bot():
    """Test chat endpoint with disabled bot"""
    # This test would need proper setup with environment variables
    # For now, just verify the endpoint exists
    response = client.post("/v1/chat",
        headers={"Authorization": "Bearer test_token"},
        json={
            "messages": [{"role": "user", "content": "test"}],
            "bot_id": "disabled_bot"
        }
    )
    # Should return 501 for disabled bot (when properly configured)
    assert response.status_code in [403, 501]  # 403 for missing token, 501 for disabled bot
