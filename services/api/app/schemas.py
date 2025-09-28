from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class SpecValidateRequest(BaseModel):
    schema_version: str
    spec: Dict[str, Any]


class SpecValidateResponse(BaseModel):
    valid: bool
    errors: Optional[List[str]] = None
