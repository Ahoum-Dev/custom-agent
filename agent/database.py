"""
Database models and connection management for call transcripts
"""
import os
import asyncio
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import asyncpg

Base = declarative_base()

class CallTranscript(Base):
    __tablename__ = "call_transcripts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(255), unique=True, nullable=False)
    facilitator_name = Column(String(255), nullable=False)
    facilitator_phone = Column(String(20), nullable=False)
    call_start_time = Column(DateTime, nullable=False)
    call_end_time = Column(DateTime, nullable=True)
    call_duration_seconds = Column(Integer, nullable=True)
    call_status = Column(String(50), nullable=False, default="initiated")  # initiated, connected, completed, failed
    full_transcript = Column(Text, nullable=True)
    agent_summary = Column(Text, nullable=True)
    onboarding_completed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ConversationTurn(Base):
    __tablename__ = "conversation_turns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(255), nullable=False)
    speaker_role = Column(String(20), nullable=False)  # agent, user
    text_content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    confidence_score = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv(
            "DATABASE_URL", 
            "postgresql+asyncpg://user:password@localhost:5432/calling_agent"
        )
        self.engine = create_async_engine(self.database_url)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession)
    
    async def create_tables(self):
        """Create all tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def save_call_transcript(self, call_data: dict) -> int:
        """Save a new call transcript record"""
        async with self.async_session() as session:
            transcript = CallTranscript(**call_data)
            session.add(transcript)
            await session.commit()
            await session.refresh(transcript)
            return transcript.id
    
    async def update_call_status(self, call_id: str, status: str, **kwargs):
        """Update call status and other fields"""
        async with self.async_session() as session:
            result = await session.execute(
                "UPDATE call_transcripts SET call_status = :status, updated_at = :updated_at WHERE call_id = :call_id",
                {"status": status, "updated_at": datetime.utcnow(), "call_id": call_id}
            )
            
            # Update additional fields if provided
            if kwargs:
                update_fields = ", ".join([f"{k} = :{k}" for k in kwargs.keys()])
                query = f"UPDATE call_transcripts SET {update_fields}, updated_at = :updated_at WHERE call_id = :call_id"
                kwargs.update({"updated_at": datetime.utcnow(), "call_id": call_id})
                await session.execute(query, kwargs)
            
            await session.commit()
    
    async def save_conversation_turn(self, call_id: str, speaker_role: str, text_content: str, timestamp: datetime, confidence_score: str = None):
        """Save a conversation turn"""
        async with self.async_session() as session:
            turn = ConversationTurn(
                call_id=call_id,
                speaker_role=speaker_role,
                text_content=text_content,
                timestamp=timestamp,
                confidence_score=confidence_score
            )
            session.add(turn)
            await session.commit()
    
    async def get_call_transcript(self, call_id: str) -> Optional[dict]:
        """Get call transcript by call_id"""
        async with self.async_session() as session:
            result = await session.execute(
                "SELECT * FROM call_transcripts WHERE call_id = :call_id",
                {"call_id": call_id}
            )
            row = result.first()
            return dict(row) if row else None
    
    async def get_conversation_turns(self, call_id: str) -> List[dict]:
        """Get all conversation turns for a call"""
        async with self.async_session() as session:
            result = await session.execute(
                "SELECT * FROM conversation_turns WHERE call_id = :call_id ORDER BY timestamp",
                {"call_id": call_id}
            )
            return [dict(row) for row in result.fetchall()]

# Global database manager instance
db_manager = DatabaseManager()
