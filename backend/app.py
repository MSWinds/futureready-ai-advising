# app.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import os
from dotenv import load_dotenv
from sqlalchemy import make_url, select
from sqlalchemy.orm import selectinload
from llama_index.llms.openai import OpenAI
from openai import AsyncOpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core import VectorStoreIndex
from agents.profile_agent import ProfileAgent, StudentInfo
from agents.search_agent import SearchAgent
from agents.recommendation_agent import RecommendationAgent
from database.db import AsyncSessionLocal, init_db, save_session, save_recommendation_session
from database.models import StudentSession, RecommendationSession
from contextlib import asynccontextmanager
import uuid
import json
from tavily import TavilyClient
from datetime import datetime
import asyncio

# Load environment variables
load_dotenv()

# Lifespan for database initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass

# Initialize FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Database and vector store setup
connection_string = os.getenv("DB_CONNECTION") 
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
url = make_url(connection_string)

# Create embedding model
embedding_model = OpenAIEmbedding(model="text-embedding-3-large")

# Set up vector store
vector_store = PGVectorStore.from_params(
    database='ai_advising_db',
    host=url.host,
    password=url.password,
    port=url.port,
    user=url.username,
    table_name="alumni_records",
    embed_dim=3072,
    hybrid_search=True,
    text_search_config="english",
)
hybrid_index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
    embed_model=embedding_model
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
llm = OpenAI(model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
profile_agent = ProfileAgent(llm=llm)
search_agent = SearchAgent(llm=llm, hybrid_index=hybrid_index, tavily_client=tavily)
recommendation_agent = RecommendationAgent(llm=AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")))

async def save_recommendations_background(
    session_id: str,
    search_queries: Dict,
    search_results: Dict,
    recommendations: Dict
):
    """Background task to save recommendations to database"""
    async with AsyncSessionLocal() as db:
        try:
            await save_recommendation_session(
                session_id=session_id,
                search_queries=search_queries,
                search_results=search_results,
                recommendations=recommendations,
                db=db
            )
        except Exception as e:
            print(f"Background save failed: {e}")

@app.websocket("/ws/profile")
async def profile_websocket(websocket: WebSocket):
    await websocket.accept()
    async with AsyncSessionLocal() as db:
        try:
            data = await websocket.receive_json()
            student_info = StudentInfo(**data)
            summary = await profile_agent.generate_profile_summary(student_info)
            
            session_id = await save_session(
                form_data=data,
                summary=summary,
                db=db
            )
            
            await websocket.send_json({
                "type": "profile_summary",
                "payload": {
                    "summary": summary,
                    "session_id": str(session_id)
                }
            })
            
        except Exception as e:
            error_message = str(e)
            if "Failed to save session" not in error_message:
                error_message = f"Error processing request: {error_message}"
            
            await websocket.send_json({
                "type": "error",
                "payload": error_message
            })
        finally:
            await websocket.close()

@app.websocket("/ws/verify_session")
async def verify_session(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Get session data from frontend
        data = await websocket.receive_json()
        session_id = data.get('session_id')
        student_summary = data.get('summary')  # Frontend needs to send this too

        if not session_id:
            await websocket.send_json({
                "type": "error",
                "payload": "No session ID provided"
            })
            return

        try:
            # Just verify UUID format
            uuid.UUID(session_id)
        except ValueError:
            await websocket.send_json({
                "type": "error",
                "payload": "Invalid session ID format"
            })
            return

        try:
            # Generate recommendations directly
            await websocket.send_json({
                "type": "status",
                "payload": {
                    "phase": "init",
                    "message": "Starting search process...",
                    "progress": 0.1
                }
            })

            # Execute search
            search_results = await asyncio.wait_for(
                search_agent.execute_combined_search(student_summary),
                timeout=60
            )

            await websocket.send_json({
                "type": "status",
                "payload": {
                    "phase": "recommendation",
                    "message": "Generating recommendations...",
                    "progress": 0.6
                }
            })

            # Generate recommendations
            recommendations = await asyncio.wait_for(
                recommendation_agent.generate_recommendations(
                    search_results,
                    student_summary
                ),
                timeout=90
            )

            if recommendations.get("status") == "error":
                raise ValueError(recommendations.get("error"))

            # Prepare response data
            recommendation_data = {
                "recommendations": [rec.dict() for rec in recommendations["recommendations"]],
                "timestamp": datetime.utcnow().isoformat()
            }

            # Send final recommendations
            await websocket.send_json({
                "type": "recommendations",
                "payload": recommendation_data
            })

        except asyncio.TimeoutError:
            await websocket.send_json({
                "type": "error",
                "payload": "Operation timed out. Please try again."
            })
        except Exception as e:
            print(f"Error in recommendation generation: {e}")
            await websocket.send_json({
                "type": "error",
                "payload": str(e)
            })

    except Exception as e:
        print(f"Session verification error: {e}")
        await websocket.send_json({
            "type": "error",
            "payload": str(e)
        })
    finally:
        await websocket.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}