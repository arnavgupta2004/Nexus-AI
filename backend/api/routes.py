from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import settings
from agent.agent import nexus_agent
from agent.memory import memory_manager
from integrations import google_oauth, gmail_client, calendar_client, github_client, notion_client

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

class ApprovalRequest(BaseModel):
    call_id: str

class GoogleAuthUrlRequest(BaseModel):
    redirect_uri: str = "http://localhost:8000/auth/google/callback"
    state: str | None = None

class GoogleTokenRequest(BaseModel):
    code: str
    redirect_uri: str = "http://localhost:8000/auth/google/callback"

@app.post("/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(
        nexus_agent.process_message(request.message),
        media_type="text/event-stream"
    )

@app.get("/memory")
async def memory():
    tasks = memory_manager.get_tasks()
    history = memory_manager.get_history()
    preferences = memory_manager.get_preferences()
    return {"tasks": tasks, "history": history, "preferences": preferences}

@app.get("/integrations/status")
async def integrations_status():
    return {
        "google_oauth_client": google_oauth.is_configured(),
        "google_refresh_token": google_oauth.has_refresh_token(),
        "gmail": gmail_client.is_configured(),
        "calendar": calendar_client.is_configured(),
        "github": github_client.is_configured(),
        "notion": notion_client.is_configured(),
        "notion_create_target": bool(settings.notion_database_id or settings.notion_parent_page_id),
    }

@app.post("/auth/google/url")
async def google_auth_url(request: GoogleAuthUrlRequest):
    if not google_oauth.is_configured():
        raise HTTPException(status_code=400, detail="Google OAuth client ID/secret are not configured.")
    return {"url": google_oauth.get_auth_url(request.redirect_uri, request.state)}

@app.get("/auth/google/callback")
async def google_callback(code: str, request: Request):
    redirect_uri = str(request.url.include_query_params())
    redirect_uri = redirect_uri.split("?")[0]
    token = await google_oauth.exchange_code(code, redirect_uri)
    return {
        "message": "Google OAuth completed. Put the refresh_token into backend/.env as GOOGLE_REFRESH_TOKEN, then restart the backend.",
        "refresh_token": token.get("refresh_token"),
        "has_refresh_token": bool(token.get("refresh_token")),
        "scope": token.get("scope"),
    }

@app.post("/auth/google/token")
async def google_token(request: GoogleTokenRequest):
    token = await google_oauth.exchange_code(request.code, request.redirect_uri)
    return {
        "message": "Put refresh_token into backend/.env as GOOGLE_REFRESH_TOKEN, then restart the backend.",
        "refresh_token": token.get("refresh_token"),
        "has_refresh_token": bool(token.get("refresh_token")),
        "scope": token.get("scope"),
    }

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
