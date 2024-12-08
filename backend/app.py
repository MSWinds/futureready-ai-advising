from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware 
from typing import List
import os
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from agents.profile_agent import ProfileAgent, StudentInfo

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM and agent
llm = OpenAI(model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
profile_agent = ProfileAgent(llm=llm)

# First Page
@app.websocket("/ws/profile")
async def profile_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        # Receive student info
        data = await websocket.receive_json()
        student_info = StudentInfo(**data)
        
        # Generate profile
        try:
            summary = await profile_agent.generate_profile_summary(student_info)
            await websocket.send_json({
                "type": "profile_summary",
                "payload": summary
            })
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "payload": f"Failed to generate profile: {str(e)}"
            })
            
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "payload": str(e)
        })
    finally:
        await websocket.close()