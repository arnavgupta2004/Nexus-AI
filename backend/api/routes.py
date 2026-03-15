from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import settings
from agent.agent import nexus_agent
from agent.memory import memory_manager

app = FastAPI(title="NexusAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    model: str = "gemini"

class ApprovalRequest(BaseModel):
    call_id: str

@app.post("/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(
        nexus_agent.process_message(request.message, request.model),
        media_type="text/event-stream"
    )

@app.get("/memory")
async def memory():
    tasks = memory_manager.get_tasks()
    history = memory_manager.get_history()
    return {"tasks": tasks, "history": history}

@app.post("/approve")
async def approve(req: ApprovalRequest):
    success = await nexus_agent.approve_action(req.call_id)
    return {"success": success}

@app.post("/reject")
async def reject(req: ApprovalRequest):
    success = await nexus_agent.reject_action(req.call_id)
    return {"success": success}

@app.get("/eval")
async def evaluate():
    test_tasks = [
        "Check my GitHub issues and add the top 3 as tasks in Notion",
        "Find all unread emails from this week and summarize them",
        "Schedule a 1hr focus block tomorrow for my most overdue GitHub issue",
        "Draft a reply to the latest email in my inbox and wait for my approval before sending",
        "Read my latest email, find any mentioned GitHub repos, and star them"
    ]
    
    return {
        "success_rate": "Evaluation runner framework setup.",
        "eval_tasks": test_tasks,
        "details": "To execute full evaluations, implement an automated orchestrator that posts these to the /chat endpoint and parses tool calls for correctness."
    }
