import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.contracts.models import Message

client = TestClient(app)

def test_create_conversation():
    resp = client.post("/v1/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data

def test_chat():
    # Crée une conversation
    resp = client.post("/v1/agents")
    conv_id = resp.json()["id"]
    # Envoie un message
    msg = {"role": "user", "content": "Bonjour"}
    chat_req = {"conversation_id": conv_id, "message": msg}
    resp = client.post("/v1/chat", json=chat_req)
    assert resp.status_code == 200
    data = resp.json()
    assert "messages" in data
