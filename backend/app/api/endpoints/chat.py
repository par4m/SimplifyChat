from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ...db.session import get_db
from ...models.chat import Conversation, Message
from ...schemas.chat import ConversationCreate, Conversation as ConversationSchema, MessageCreate, ChatSummary
from ...services.gemini import generate_summary

router = APIRouter()

@router.post("/chats", response_model=ConversationSchema)
async def create_conversation(
    conversation: ConversationCreate,
    db: AsyncSession = Depends(get_db)
):
    db_conversation = Conversation(**conversation.model_dump())
    db.add(db_conversation)
    await db.commit()
    await db.refresh(db_conversation)
    return db_conversation

@router.get("/chats/{conversation_id}", response_model=ConversationSchema)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@router.get("/users/{user_id}/chats", response_model=List[ConversationSchema])
async def get_user_chats(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Conversation).where(Conversation.user_id == user_id)
    
    if start_date:
        query = query.where(Conversation.created_at >= start_date)
    if end_date:
        query = query.where(Conversation.created_at <= end_date)
    
    query = query.order_by(desc(Conversation.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.delete("/chats/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.delete(conversation)
    await db.commit()
    return {"message": "Conversation deleted successfully"}

@router.post("/chats/{conversation_id}/messages", response_model=ConversationSchema)
async def add_message(
    conversation_id: UUID,
    message: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    db_message = Message(
        conversation_id=conversation_id,
        **message.model_dump()
    )
    db.add(db_message)
    await db.commit()
    await db.refresh(conversation)
    return conversation

@router.post("/chats/{conversation_id}/summarize", response_model=ChatSummary)
async def summarize_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return await generate_summary(conversation.messages, conversation.participants) 