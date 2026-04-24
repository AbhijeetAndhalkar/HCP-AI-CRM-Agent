from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import engine, Base
import models
from agent import agent_executor
from fastapi import HTTPException
from langchain_core.messages import HumanMessage

# Initialize the MySQL tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="HCP AI CRM")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=False, # MUST be False if allow_origins is "*"
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class ChatRequest(BaseModel):
    messages: list  # This will now receive the array from React

@app.get("/")
def read_root():
    return {"message": "Welcome to the HCP AI CRM API"}

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        # We pass the entire list of messages to the LangGraph executor
        # LangGraph knows how to read this history to maintain context
        result = agent_executor.invoke({"messages": req.messages})
        
        # Get the very last message (the AI's newest response)
        ai_response = result["messages"][-1].content
        
        return {"response": ai_response}
    except Exception as e:
        print(f"Backend Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
