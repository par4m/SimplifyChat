from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import logging
from sqlalchemy.orm import selectinload

from ...db.session import get_db
from ...models.chat import Conversation, Message
from ...schemas.chat import ConversationCreate, Conversation as ConversationSchema, MessageCreate, ChatSummary
from ...services.gemini import generate_summary

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/chats", response_model=ConversationSchema)
async def create_conversation(
    conversation: ConversationCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        db_conversation = Conversation(**conversation.model_dump())
        db.add(db_conversation)
        await db.commit()
        await db.refresh(db_conversation)
        
        # Load the messages relationship
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == db_conversation.id)
        )
        db_conversation = result.scalar_one()
        
        return db_conversation
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")

@router.get("/chats/{conversation_id}", response_model=ConversationSchema)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except Exception as e:
        logger.error(f"Error retrieving conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation: {str(e)}")

@router.get("/users/{user_id}/chats", response_model=List[ConversationSchema])
async def get_user_chats(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        query = select(Conversation).options(selectinload(Conversation.messages)).where(Conversation.user_id == user_id)
        
        if start_date:
            query = query.where(Conversation.created_at >= start_date)
        if end_date:
            query = query.where(Conversation.created_at <= end_date)
        
        query = query.order_by(desc(Conversation.created_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error retrieving chats for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user chats: {str(e)}")

@router.delete("/chats/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        await db.delete(conversation)
        await db.commit()
        return {"message": "Conversation deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

@router.post("/chats/{conversation_id}/messages", response_model=ConversationSchema)
async def add_message(
    conversation_id: UUID,
    message: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
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
        
        # Reload the conversation with messages
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one()
        
        return conversation
    except Exception as e:
        logger.error(f"Error adding message to conversation {conversation_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")

@router.post("/chats/{conversation_id}/summarize", response_model=ChatSummary)
async def summarize_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return await generate_summary(conversation.messages, conversation.participants)
    except Exception as e:
        logger.error(f"Error summarizing conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}") 