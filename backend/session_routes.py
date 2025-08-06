from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Session as SessionModel, Conversation, Agent, SessionCreate, SessionResponse, ClarificationRequest, ClarificationResponse, AgentGenerationRequest, AgentGenerationResponse
from auth import get_current_user
import uuid
import os
from openai import OpenAI
from typing import List, Dict, Any
import json

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_session_id() -> str:
    """Generate a unique session ID"""
    return str(uuid.uuid4())


def analyze_context_for_clarification(user_input: str, pdf_content: str = None) -> List[str]:
    """
    Use LLM to analyze user input and generate intelligent clarifying questions
    No templates - pure LLM intelligence
    """
    context = f"User input: {user_input}"
    if pdf_content:
        # Limit PDF content
        context += f"\nPDF content: {pdf_content[:1000]}..."

    prompt = f"""
    Analyze this user's request for multi-persona feedback and generate 2-4 intelligent clarifying questions.
    
    Context: {context}
    
    Generate questions that would help understand:
    - The user's specific goals and concerns
    - Their knowledge level and background
    - What kind of feedback they're seeking
    - Any ambiguities that would affect agent creation
    
    Return ONLY a JSON array of questions, no explanations:
    ["Question 1?", "Question 2?", "Question 3?"]
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )

        questions_text = response.choices[0].message.content.strip()
        # Extract JSON array from response
        if questions_text.startswith('[') and questions_text.endswith(']'):
            questions = json.loads(questions_text)
        else:
            # Fallback if JSON parsing fails
            questions = [
                "What specific aspect of this topic concerns you most?",
                "What kind of feedback are you looking for - technical, strategic, or user experience?",
                "What's your background with this topic?"
            ]

        return questions[:4]  # Limit to 4 questions max

    except Exception as e:
        # Fallback questions if LLM fails
        return [
            "What specific aspect of this topic concerns you most?",
            "What kind of feedback are you looking for?",
            "What's your background with this topic?"
        ]


def determine_agent_creation_ready(context: Dict[str, Any]) -> bool:
    """
    Use LLM to determine if we have enough context to create agents
    """
    clarifications = context.get('clarifications', [])
    user_input = context.get('user_input', '')

    if len(clarifications) < 2:
        return False

    prompt = f"""
    Based on this conversation context, determine if we have enough information to create meaningful AI agents.
    
    User's original input: {user_input}
    Clarifications provided: {clarifications}
    
    Answer with ONLY 'yes' or 'no':
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=10
        )

        answer = response.choices[0].message.content.strip().lower()
        return answer == 'yes'

    except Exception:
        # Default to yes if we have at least 3 clarifications
        return len(clarifications) >= 3


@router.post("/start", response_model=SessionResponse)
async def start_session(
    session_data: SessionCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new feedback session with clarification phase"""

    # Generate session ID
    session_id = generate_session_id()

    # Analyze context and generate clarifying questions
    questions = analyze_context_for_clarification(
        session_data.user_input,
        session_data.pdf_content
    )

    # Create session record
    session = SessionModel(
        session_id=session_id,
        user_id=1,  # TODO: Get actual user ID from current_user
        status="clarifying",
        context={
            "user_input": session_data.user_input,
            "pdf_content": session_data.pdf_content,
            "clarifications": [],
            "questions_asked": questions
        }
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    # Store initial questions in conversation
    for question in questions:
        conversation = Conversation(
            session_id=session_id,
            message_type="clarification",
            content=question,
            message_metadata={"question_index": questions.index(question)}
        )
        db.add(conversation)

    db.commit()

    return SessionResponse(
        session_id=session_id,
        status="clarifying",
        context=session.context
    )


@router.post("/clarify", response_model=ClarificationResponse)
async def provide_clarification(
    clarification: ClarificationRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Provide clarification and get next questions or move to agent creation"""

    # Get session
    session = db.query(SessionModel).filter(
        SessionModel.session_id == clarification.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Store user's clarification response
    conversation = Conversation(
        session_id=clarification.session_id,
        message_type="user",
        content=clarification.user_response
    )
    db.add(conversation)

    # Update session context
    session.context["clarifications"].append(clarification.user_response)

    # Check if ready for agent creation
    if determine_agent_creation_ready(session.context):
        session.status = "creating_agents"
        db.commit()

        return ClarificationResponse(
            session_id=clarification.session_id,
            questions=[],
            status="ready_for_agents"
        )
    else:
        # Generate follow-up questions
        follow_up_questions = analyze_context_for_clarification(
            session.context["user_input"],
            session.context.get("pdf_content")
        )

        # Store new questions
        for question in follow_up_questions:
            conversation = Conversation(
                session_id=clarification.session_id,
                message_type="clarification",
                content=question,
                message_metadata={
                    "question_index": follow_up_questions.index(question)})
            db.add(conversation)

        session.context["questions_asked"].extend(follow_up_questions)
        db.commit()

        return ClarificationResponse(
            session_id=clarification.session_id,
            questions=follow_up_questions,
            status="clarifying"
        )


@router.get("/{session_id}/status", response_model=SessionResponse)
async def get_session_status(
    session_id: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current session status and context"""

    session = db.query(SessionModel).filter(
        SessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        session_id=session.session_id,
        status=session.status,
        context=session.context
    )
