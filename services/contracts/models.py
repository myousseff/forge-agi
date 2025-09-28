from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ConversationCreate(BaseModel):
    """Payload pour créer une conversation."""
    # Ajoute d'autres champs si besoin
    pass

class Conversation(BaseModel):
    """Conversation avec identifiant."""
    id: str
    created_at: Optional[datetime] = None

class Message(BaseModel):
    """Message d'une conversation."""
    role: Literal['user', 'assistant', 'tool']
    content: str
    tool_name: Optional[str] = None
    created_at: Optional[datetime] = None

class ChatRequest(BaseModel):
    """Requête de chat avec conversation et message utilisateur."""
    conversation_id: str
    message: Message

class ChatResponse(BaseModel):
    """Réponse de chat contenant la liste des messages."""
    messages: List[Message]

class FileInfo(BaseModel):
    """Informations sur un fichier uploadé."""
    file_id: str
    url: str
    mime: str
    size: int

class MemoryUpsert(BaseModel):
    """Upsert de mémoire (stub)."""
    items: List[Dict[str, Any]]

class MemoryQuery(BaseModel):
    """Query mémoire (stub)."""
    query: str
    top_k: int = 5
