from dataclasses import dataclass
from typing import TypedDict, Optional

@dataclass
class AgentMessageCreated:
    conversation_id: str
    message_id: str
    role: str
    content: str

class ToolCalled(TypedDict):
    conversation_id: str
    tool: str
    args: dict

class FileUploaded(TypedDict):
    file_id: str
    url: str
    mime: str
    size: int

class RunFinished(TypedDict):
    run_id: str
    status: str
