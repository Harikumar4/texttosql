from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class UserMessage(BaseModel):
    type: str
    id: str
    session_id: Optional[str]
    payload: Dict[str, Any]  # user message here

class ChatReply(BaseModel):
    type: str
    id: str
    session_id: Optional[str]
    timestamp: datetime
    payload: Dict[str, Any]  # model response here"

# this file is not used in current implementation but generally used for validation 