"""
main.py - FastAPI Application Entry Point

PURPOSE:
This is the core server file that runs the Backend. It uses FastAPI to create REST API endpoints 
that the frontend (React) communicates with. It also initializes the database and sets up CORS 
(Cross-Origin Resource Sharing) so the frontend can securely send requests.

HOW IT WORKS AT A GLANCE:
- `Base.metadata.create_all()`: Automatically creates the MySQL tables if they don't exist yet.
- `app = FastAPI(...)`: Initializes the web server.
- `CORSMiddleware`: Allows the React frontend (running on a different port) to talk to this backend.
- `@app.post("/chat")`: The main endpoint. It receives the entire conversation history from the frontend, 
  passes it to the LangGraph AI Agent (`agent_executor`), and returns the AI's response.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import engine, Base
import models
from agent import agent_executor
from fastapi import HTTPException

# 1. INITIALIZE DATABASE
# Connects to MySQL and ensures all tables defined in models.py exist.
Base.metadata.create_all(bind=engine)

# 2. CREATE FASTAPI APP
app = FastAPI(title="HCP AI CRM")

# 3. CONFIGURE CORS
# Crucial for local development when frontend runs on localhost:5173 and backend on localhost:8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted to the actual frontend URL
    allow_credentials=False, # MUST be False if allow_origins is "*"
    allow_methods=["*"],  # Allows GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Allows all headers
)

# 4. DEFINE DATA SCHEMAS
class ChatRequest(BaseModel):
    """
    Pydantic Model to validate the incoming POST request payload.
    We expect a list of message objects (the chat history).
    """
    messages: list

# 5. DEFINE ENDPOINTS
@app.get("/")
def read_root():
    """Health check endpoint to verify the server is running."""
    return {"message": "Welcome to the HCP AI CRM API"}

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """
    The core AI endpoint.
    Receives the chat history, feeds it to LangGraph, and returns the AI's latest message.
    """
    try:
        # We pass the entire list of messages to the LangGraph executor.
        # LangGraph knows how to read this history to maintain context and determine next steps.
        result = agent_executor.invoke({"messages": req.messages})
        
        # Extract the very last message from the updated state (this is the AI's newest response)
        ai_response = result["messages"][-1].content
        
        return {"response": ai_response}
    except Exception as e:
        print(f"Backend Error: {e}")
        # Return a clean 500 error to the frontend if something goes wrong
        raise HTTPException(status_code=500, detail=str(e))
