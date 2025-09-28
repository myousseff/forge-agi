from fastapi import APIRouter, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from services.contracts.models import *
from .db import create_conversation, add_message, list_messages
from .filestore import LocalFileStore
from .memory import MemoryStore
from .tools_registry import REGISTRY
import requests
import os

router = APIRouter()

@router.post("/v1/agents", response_model=Conversation)
def create_agent():
    return create_conversation()

@router.post("/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # Enregistre le message user
    add_message(req.conversation_id, req.message.role, req.message.content, req.message.tool_name)
    # Appelle le worker
    worker_url = os.getenv("WORKER_URL", "http://worker:9000/agent/step")
    try:
        resp = requests.post(worker_url, json={"conversation_id": req.conversation_id}, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            return ChatResponse(messages=[Message(**m) for m in data.get("messages", [])])
    except Exception:
        # Worker non dispo : echo minimal
        msg = Message(role="assistant", content=f"Echo: {req.message.content}")
        add_message(req.conversation_id, msg.role, msg.content)
        return ChatResponse(messages=[msg])

@router.get("/v1/conversations/{id}", response_model=list[Message])
def get_conversation(id: str):
    return list_messages(id)

@router.post("/v1/files", response_model=FileInfo)
def upload_file(file: UploadFile = File(...)):
    store = LocalFileStore()
    content = file.file.read()
    return store.put(content, file.content_type or "application/octet-stream")

@router.post("/v1/memory/upsert")
def memory_upsert(req: MemoryUpsert):
    store = MemoryStore()
    count = store.upsert(req.items)
    return {"count": count}

@router.post("/v1/memory/query")
def memory_query(req: MemoryQuery):
    store = MemoryStore()
    results = store.query(req.query, req.top_k)
    return {"results": results}

@router.get("/v1/tools")
def list_tools():
    return list(REGISTRY.keys())

@router.post("/v1/tools/{name}/invoke")
def invoke_tool(name: str, args: dict):
    tool = REGISTRY.get(name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    try:
        result = tool.run(args)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
