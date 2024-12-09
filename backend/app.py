# app.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import os
from dotenv import load_dotenv
from sqlalchemy import make_url
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from agents.profile_agent import ProfileAgent, StudentInfo
from agents.search_agent import SearchAgent
from agents.recommendation_agent import RecommendationAgent
from database.db import AsyncSessionLocal, init_db, save_session, save_recommendation_session
from contextlib import asynccontextmanager
import uuid
from tavily import TavilyClient
from datetime import datetime

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
search_agent = SearchAgent(llm=llm, hybrid_index=vector_store, tavily_client=tavily)
recommendation_agent = RecommendationAgent(llm=llm)

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
    
    async with AsyncSessionLocal() as db:
        try:
            data = await websocket.receive_json()
            session_id = data.get('session_id')
            
            from database.models import StudentSession
            session = await db.get(StudentSession, uuid.UUID(session_id))
            
            if session:
                await websocket.send_json({
                    "type": "valid",
                    "payload": {"session_id": session_id}
                })
            else:
                await websocket.send_json({
                    "type": "invalid",
                    "payload": "Session not found"
                })
                
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "payload": str(e)
            })
        finally:
            await websocket.close()

@app.websocket("/ws/recommendations/{session_id}")
async def recommendation_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    async with AsyncSessionLocal() as db:
        try:
            # Get student profile
            from database.models import StudentSession
            session = await db.get(StudentSession, uuid.UUID(session_id))
            
            if not session:
                await websocket.send_json({
                    "type": "error",
                    "payload": "Session not found"
                })
                return

            # Send status update
            await websocket.send_json({
                "type": "status",
                "payload": "Starting search process..."
            })

            # Execute search
            search_results = await search_agent.execute_combined_search(
                session.profile_summary
            )

            # Send status update
            await websocket.send_json({
                "type": "status",
                "payload": "Generating recommendations..."
            })

            # Generate recommendations
            recommendations = await recommendation_agent.generate_recommendations(
                search_results,
                session.profile_summary
            )

            # Save to database
            await save_recommendation_session(
                session_id=session_id,
                search_queries=search_results["queries"],
                search_results=search_results["results"],
                recommendations=recommendations,
                db=db
            )

            # Send final response
            await websocket.send_json({
                "type": "recommendations",
                "payload": {
                    "recommendations": recommendations,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "payload": str(e)
            })
        finally:
            await websocket.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}