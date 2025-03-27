from pydantic import BaseModel, UUID4
from typing import List, Optional
from datetime import datetime

class MessageBase(BaseModel):
    content: str
    sender: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: UUID4
    conversation_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    user_id: str
    participants: List[str]
    title: Optional[str] = None

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: UUID4
    created_at: datetime
    messages: List[Message] = []

    class Config:
        from_attributes = True

class ChatSummary(BaseModel):
    summary: str
    key_points: List[str]
    action_items: List[str] 