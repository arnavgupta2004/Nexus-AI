# NexusAI

A personal autonomous agent connecting to Gmail, Google Calendar, GitHub, and Notion via MCP.

## Architecture

```text
+-----------------------+      +---------------------------+       +-------------------+
|                       |      |                           |       |                   |
|  React + Tailwind UI  | <==> |  FastAPI + Gemini Agent   | <===> | SQLite Memory DB  |
|                       |      |                           |       |                   |
+-------------------+---+      +-------------+-------------+       +-------------------+
                    |                        |
             (Human-in-loop              (MCP Tools)
                Approval)                    |
                                     +-------+--------+
                                     |                |
                              +------+---+       +----+-----+
                              |  Gmail   |       | Calendar |
                              +----------+       +----------+
                              |  GitHub  |       |  Notion  |
                              +----------+       +----------+
```

## Setup Instructions

### Environment Variables
Copy `backend/.env.example` to `backend/.env` and fill out your backend secrets:
- Gemini API key
- Google OAuth client ID/secret for Gmail and Calendar
- `GOOGLE_REFRESH_TOKEN` after completing the local Google OAuth flow
- GitHub personal access token
- Notion API key
- `NOTION_PARENT_PAGE_ID` or `NOTION_DATABASE_ID` if you want NexusAI to create Notion pages

For local frontend development, copy `frontend/.env.example` to `frontend/.env`.

### Google OAuth
1. Start the backend.
2. Request an auth URL:
   ```bash
   curl -X POST http://localhost:8000/auth/google/url \
     -H "Content-Type: application/json" \
     -d '{"redirect_uri":"http://localhost:8000/auth/google/callback"}'
   ```
3. Open the returned URL, approve access, and copy the returned `refresh_token`.
4. Add it to `backend/.env` as `GOOGLE_REFRESH_TOKEN`, then restart the backend.

### Integration Status
Check which integrations are active:
```bash
curl http://localhost:8000/integrations/status
```

### Backend
Required tools: Python 3.10+
1. Navigate to `backend/`
2. Create virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend
Required tools: Node 18+, npm
1. Navigate to `frontend/`
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run dev server:
   ```bash
   npm run dev
   ```

## Tech Stack
- Frontend: React + Tailwind CSS
- Backend: Python + FastAPI
- Agent Brain: Gemini API
- Tools: Model Context Protocol (MCP) clients connecting to external services.
