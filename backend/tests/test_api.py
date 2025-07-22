import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

@pytest.fixture
def auth_headers():
    return {"x-email-header": "test@test.com"}

class TestAPI:
    def test_auth_endpoint(self, client):
        response = client.get("/auth/")
        assert response.status_code == 200
        assert "Authentication Required" in response.text

    def test_llm_providers_endpoint(self, client, auth_headers):
        response = client.get("/api/llm/providers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_mcp_tools_endpoint(self, client, auth_headers):
        response = client.get("/api/mcp/tools", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_chat_message_endpoint(self, client, auth_headers):
        payload = {
            "message": "Hello",
            "llm_provider": "openai-gpt4",
            "selected_tools": []
        }
        response = client.post("/api/chat/message", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert 'response' in data
        assert 'provider_used' in data

    def test_chat_message_no_provider(self, client, auth_headers):
        payload = {
            "message": "Hello",
            "llm_provider": "",
            "selected_tools": []
        }
        response = client.post("/api/chat/message", json=payload, headers=auth_headers)
        assert response.status_code == 400

    def test_mcp_validate_endpoint(self, client, auth_headers):
        payload = {"tool_ids": ["calculator", "nonexistent"]}
        response = client.post("/api/mcp/validate", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2