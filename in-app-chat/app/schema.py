from pydantic import BaseModel
from typing import List, Literal, Optional,Dict,Any
from datetime import datetime
from uuid import UUID

class ChatMessage(BaseModel):
    from_user: UUID
    text: str
    timestamp: str


class WebSocketMessage(BaseModel):
    to: UUID
    booking_id: UUID
    message: str


class ChatSchema(BaseModel):
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    booking_id: UUID
    messages: List[ChatMessage]
    status: str
    created_at: datetime
    updated: Optional[datetime]


class ChatMetadataResponse(BaseModel):
    chat_id: str
    participants: List[str]
    booking_id: str
    created_at: Optional[str]
    status: str
    message_count: int

class ChartMessageSchema(BaseModel):
    id: int
    booking_id: str
    sender_id: str
    receiver_id: str 
    messages: List[Dict[str, Any]]


class UpdateMessageRequest(BaseModel):
    # message_id: str
    updates: dict  # Any fields to update in the message object
    sender_id: Optional[str] = None  # ID of the sender
    receiver_id: Optional[str] = None  # ID of the receiver


class BulkChatSaveRequest(BaseModel):
    sender_id: str
    receiver_id: str
    messages: Optional[List[dict]] = []