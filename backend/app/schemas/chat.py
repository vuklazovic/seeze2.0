from pydantic import BaseModel
from typing import Optional, Dict, Any


class UserQuery(BaseModel):
    query: str


class FunctionExecution(BaseModel):
    name: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]


class ChatResponse(BaseModel):
    success: bool
    user_query: str
    llm_response: Dict[str, Any]
    function_executed: Optional[FunctionExecution] = None
    error: Optional[str] = None