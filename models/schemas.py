from typing import Optional, Dict, Any
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: Optional[str] = None
    image_url: Optional[str] = None
    thread_id: str
    # 用户确认的interrupt操作
    interrupt_decision: Optional[Dict[str, Any]] = None