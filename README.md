# NexusAI

A personal autonomous agent connecting to Gmail, Google Calendar, GitHub, and Notion via MCP.

## Architecture

```text
+-----------------------+      +---------------------------+       +-------------------+
|                       |      |                           |       |                   |
|  React + Tailwind UI  | <==> |  FastAPI + Claude Agent   | <===> | SQLite Memory DB  |
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
Copy `.env.example` to `.env` and fill out your secrets:
- Anthropic API Key for Claude
- OAuth keys for Gmail and Google Calendar
- Personal Access Tokens / API Keys for GitHub and Notion

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
- Agent Brain: Claude API
- Tools: Model Context Protocol (MCP) clients connecting to external services.
