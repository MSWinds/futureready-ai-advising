# db.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from .models import Base, StudentSession, RecommendationSession
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

# Load environment variables
load_dotenv()
connection_string = os.getenv("DB_CONNECTION").replace("psycopg2", "asyncpg")

# Database setup using asyncpg
engine = create_async_engine(connection_string, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Async: Create tables on startup
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Database dependency for async sessions
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Async helper function to save session
async def save_session(form_data: dict, summary: str, db: AsyncSession) -> uuid.UUID:
    from .models import StudentSession
    try:
        session = StudentSession(
            form_data=form_data,
            profile_summary=summary,
            timestamp=datetime.utcnow()
        )   
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session.session_id
    except Exception as e:
        await db.rollback()
        raise e

async def verify_session(
    session_id: str,
    db: AsyncSession
) -> Tuple[bool, Optional[str], Optional[StudentSession]]:
    """
    Verify session validity and return status
    Returns: (is_valid, error_message, session_object)
    """
    try:
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            return False, "Invalid session ID format", None

        stmt = select(StudentSession).where(
            StudentSession.session_id == session_uuid
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return False, "Session not found", None

        # Check if session is expired (1 hour)
        if datetime.utcnow() - session.timestamp > timedelta(hours=1):
            return False, "Session expired", None

        return True, None, session

    except Exception as e:
        return False, f"Error verifying session: {str(e)}", None

# New function to save recommendation session
async def save_recommendation_session(
    session_id: str,
    search_queries: Dict,
    search_results: Dict,
    recommendations: Dict,
    db: AsyncSession
) -> Optional[Dict]:
    """Save recommendation session data and return saved data"""
    try:
        session_uuid = uuid.UUID(session_id) if isinstance(session_id, str) else session_id
        
        # Check if recommendation session exists
        stmt = select(RecommendationSession).where(
            RecommendationSession.session_id == session_uuid
        )
        result = await db.execute(stmt)
        existing_rec_session = result.scalar_one_or_none()
        
        if existing_rec_session:
            # Update existing session
            existing_rec_session.search_queries = search_queries
            existing_rec_session.search_results = search_results
            existing_rec_session.recommendations = recommendations
            existing_rec_session.timestamp = datetime.utcnow()
            saved_session = existing_rec_session
        else:
            # Create new session
            new_rec_session = RecommendationSession(
                session_id=session_uuid,
                search_queries=search_queries,
                search_results=search_results,
                recommendations=recommendations
            )
            db.add(new_rec_session)
            saved_session = new_rec_session
        
        await db.commit()
        await db.refresh(saved_session)

        return {
            "session_id": str(saved_session.session_id),
            "recommendations": saved_session.recommendations,
            "timestamp": saved_session.timestamp.isoformat()
        }

    except Exception as e:
        await db.rollback()
        raise e

# Get recommendation session with verification
async def get_verified_recommendation_session(
    session_id: str,
    db: AsyncSession
) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Retrieve verified recommendation session data
    Returns: (recommendation_data, error_message)
    """
    try:
        # First verify the session
        is_valid, error_message, _ = await verify_session(session_id, db)
        if not is_valid:
            return None, error_message

        # Get recommendation data
        session_uuid = uuid.UUID(session_id)
        stmt = select(RecommendationSession).where(
            RecommendationSession.session_id == session_uuid
        )
        result = await db.execute(stmt)
        rec_session = result.scalar_one_or_none()
        
        if rec_session:
            return {
                "session_id": str(rec_session.session_id),
                "recommendations": rec_session.recommendations,
                "timestamp": rec_session.timestamp.isoformat()
            }, None

        return None, "No recommendations found for this session"

    except Exception as e:
        return None, f"Error retrieving recommendations: {str(e)}"