# db.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from .models import Base, StudentSession, RecommendationSession
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
from typing import Optional, Dict

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
            profile_summary=summary
        )
        db.add(session)
        await db.commit()  # Make sure we commit the transaction
        await db.refresh(session)
        return session.session_id
    except Exception as e:
        await db.rollback()  # Explicitly rollback on error
        raise e

# New function to save recommendation session
async def save_recommendation_session(
    session_id: str,
    search_queries: Dict,
    search_results: Dict,
    recommendations: Dict,
    db: AsyncSession
) -> None:
    """Save recommendation session data"""
    try:
        # Convert string session_id to UUID if needed
        session_uuid = uuid.UUID(session_id) if isinstance(session_id, str) else session_id
        
        # Check if recommendation session already exists
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
        else:
            # Create new session
            new_rec_session = RecommendationSession(
                session_id=session_uuid,
                search_queries=search_queries,
                search_results=search_results,
                recommendations=recommendations
            )
            db.add(new_rec_session)
        
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e

# New function to get recommendation session
async def get_recommendation_session(
    session_id: str,
    db: AsyncSession
) -> Optional[Dict]:
    """Retrieve recommendation session data by session_id"""
    try:
        # Convert string session_id to UUID if needed
        session_uuid = uuid.UUID(session_id) if isinstance(session_id, str) else session_id
        
        stmt = select(RecommendationSession).where(
            RecommendationSession.session_id == session_uuid
        )
        result = await db.execute(stmt)
        rec_session = result.scalar_one_or_none()
        
        if rec_session:
            return {
                "session_id": str(rec_session.session_id),
                "search_queries": rec_session.search_queries,
                "search_results": rec_session.search_results,
                "recommendations": rec_session.recommendations,
                "timestamp": rec_session.timestamp.isoformat()
            }
        return None
    except Exception as e:
        raise e