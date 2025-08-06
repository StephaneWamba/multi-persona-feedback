from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

Base = declarative_base()

# SQLAlchemy Models


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    session_id = Column(String, unique=True, index=True)
    # clarifying, creating_agents, active, completed
    status = Column(String, default="clarifying")
    context = Column(JSON)  # Store user input, clarifications, and context
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    # user, clarification, agent_response, system
    message_type = Column(String)
    content = Column(Text)
    agent_id = Column(String, nullable=True)  # For agent responses
    message_metadata = Column(JSON, nullable=True)  # Additional context (renamed from metadata)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    agent_id = Column(String, unique=True, index=True)
    name = Column(String)
    persona = Column(JSON)  # Full agent persona and knowledge
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Pydantic Models for API


class UserCreate(BaseModel):
    email: str
    username: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class SessionCreate(BaseModel):
    user_input: str
    pdf_content: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    status: str
    context: Dict[str, Any]


class ClarificationRequest(BaseModel):
    session_id: str
    user_response: str


class ClarificationResponse(BaseModel):
    session_id: str
    questions: List[str]
    status: str


class AgentGenerationRequest(BaseModel):
    session_id: str


class AgentGenerationResponse(BaseModel):
    session_id: str
    agents: List[Dict[str, Any]]
    status: str


class ConversationMessage(BaseModel):
    session_id: str
    message_type: str
    content: str
    agent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
