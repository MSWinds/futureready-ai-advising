# backend/database/models.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class StudentSession(Base):
    """Model for storing student profile information and session data"""
    __tablename__ = "student_information_sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    form_data = Column(JSON)  # Store raw form input
    profile_summary = Column(String)  # Store generated profile summary
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to recommendation sessions
    recommendations = relationship("RecommendationSession", back_populates="student_session")

class RecommendationSession(Base):
    """Model for storing recommendation-related data"""
    __tablename__ = "recommendation_sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("student_information_sessions.session_id"), unique=True, index=True)
    search_queries = Column(JSON)  # Store both DB and internet queries
    search_results = Column(JSON)  # Store combined_responses
    recommendations = Column(JSON)  # Store final recommendations
    timestamp = Column(DateTime, default=datetime.utcnow())
    
    # Relationship to student session
    student_session = relationship("StudentSession", back_populates="recommendations")