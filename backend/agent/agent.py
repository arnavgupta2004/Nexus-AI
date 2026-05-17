import json
import asyncio
import uuid
from typing import Dict, AsyncGenerator
from agent.memory import memory_manager
from config import settings
from integrations import gmail_client, calendar_client, github_client, notion_client

class Agent:
    def __init__(self):
        self.pending_actions: Dict[str, asyncio.Event] = {}
        self.action_results: Dict[str, str] = {}
        self.mcp_clients = {}

    async def init_mcps(self):
        pass

    async def get_tools(self):
        tools = [
            {
                "name": "memory__save_preference",
                "description": "Save a durable user preference or stable fact the user explicitly asks NexusAI to remember.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "Short stable key, e.g. preferred_github_repo."},
                        "value": {"type": "string", "description": "Preference or fact to remember."},
                    },
                    "required": ["key", "value"],
                },
            },
            {
                "name": "memory__get_preferences",
                "description": "Read saved durable user preferences.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]
        if gmail_client.is_configured():
            tools.extend([
                {
                    "name": "gmail__list_unread_emails",
                    "description": "List unread Gmail messages with sender, subject, date, snippet, and estimated count.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Gmail search query. Defaults to is:unread."},
                            "max_results": {"type": "integer", "description": "Maximum emails to return, 1-25."}
                        },
                    },
                },
                {
                    "name": "gmail__get_email",
                    "description": "Get a Gmail message by message ID.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "message_id": {"type": "string"}
                        },
                        "required": ["message_id"],
                    },
                },
                {
                    "name": "gmail__send_email",
                    "description": "Send an email from the connected Gmail account.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "to": {"type": "string"},
                            "subject": {"type": "string"},
                            "body": {"type": "string"},
                        },
                        "required": ["to", "subject", "body"],
                    },
                },
            ])
        if calendar_client.is_configured():
            tools.extend([
                {
                    "name": "calendar__list_events",
                    "description": "List Google Calendar events from the connected calendar.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "calendar_id": {"type": "string", "description": "Calendar ID. Defaults to primary."},
                            "time_min": {"type": "string", "description": "RFC3339 lower bound."},
                            "time_max": {"type": "string", "description": "RFC3339 upper bound."},
                            "max_results": {"type": "integer"},
                        },
                    },
                },
                {
                    "name": "calendar__schedule_event",
                    "description": "Create a Google Calendar event.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "start_time": {"type": "string", "description": "RFC3339 date-time, e.g. 2026-05-18T10:00:00+05:30."},
                            "end_time": {"type": "string", "description": "RFC3339 date-time."},
                            "calendar_id": {"type": "string"},
                            "timezone_name": {"type": "string"},
                            "description": {"type": "string"},
                        },
                        "required": ["title", "start_time", "end_time"],
                    },
                },
            ])
        if github_client.is_configured():
            tools.extend([
                {
                    "name": "github__list_issues",
                    "description": "List issues for a GitHub repository in owner/repo format.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "repo": {"type": "string", "description": "Repository in owner/repo format."},
                            "state": {"type": "string", "description": "open, closed, or all."},
                            "limit": {"type": "integer"},
                        },
                        "required": ["repo"],
                    },
                },
                {
                    "name": "github__get_issue",
                    "description": "Get one GitHub issue by number.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "repo": {"type": "string"},
                            "issue_number": {"type": "integer"},
                        },
                        "required": ["repo", "issue_number"],
                    },
                },
                {
                    "name": "github__create_issue",
                    "description": "Create a GitHub issue.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "repo": {"type": "string"},
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                        },
                        "required": ["repo", "title"],
                    },
                },
            ])
        if notion_client.is_configured():
            tools.extend([
                {
                    "name": "notion__search",
                    "description": "Search pages/databases visible to the connected Notion integration.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "integer"},
                        },
                    },
                },
                {
                    "name": "notion__create_page",
                    "description": "Create a Notion page using NOTION_DATABASE_ID, NOTION_PARENT_PAGE_ID, or an explicit parent page ID.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "parent_id": {"type": "string"},
                        },
                        "required": ["title"],
                    },
                },
            ])
        return tools

    async def call_tool(self, name: str, args: dict) -> str:
        if name == "gmail__list_unread_emails":
            result = await gmail_client.list_unread_emails(
                query=args.get("query") or "is:unread",
                max_results=int(args.get("max_results") or 10),
            )
        elif name == "memory__save_preference":
            memory_manager.save_preference(args["key"], args["value"])
            result = {"saved": True, "key": args["key"], "value": args["value"]}
        elif name == "memory__get_preferences":
            result = memory_manager.get_preferences()
        elif name == "gmail__get_email":
            result = await gmail_client.get_email(args["message_id"])
        elif name == "gmail__send_email":
            result = await gmail_client.send_email(args["to"], args["subject"], args["body"])
        elif name == "calendar__list_events":
            result = await calendar_client.list_events(
                calendar_id=args.get("calendar_id") or "primary",
                time_min=args.get("time_min"),
                time_max=args.get("time_max"),
                max_results=int(args.get("max_results") or 10),
            )
        elif name == "calendar__schedule_event":
            result = await calendar_client.schedule_event(
                title=args["title"],
                start_time=args["start_time"],
                end_time=args["end_time"],
                calendar_id=args.get("calendar_id") or "primary",
                timezone_name=args.get("timezone_name") or "Asia/Kolkata",
                description=args.get("description") or "",
            )
        elif name == "github__list_issues":
            result = await github_client.list_issues(
                repo=args["repo"],
                state=args.get("state") or "open",
                limit=int(args.get("limit") or 10),
            )
        elif name == "github__get_issue":
            result = await github_client.get_issue(args["repo"], int(args["issue_number"]))
        elif name == "github__create_issue":
            result = await github_client.create_issue(
                repo=args["repo"],
                title=args["title"],
                body=args.get("body") or "",
            )
        elif name == "notion__search":
            result = await notion_client.search(
                query=args.get("query") or "",
                limit=int(args.get("limit") or 10),
            )
        elif name == "notion__create_page":
            result = await notion_client.create_page(
                title=args["title"],
                content=args.get("content") or "",
                parent_id=args.get("parent_id"),
            )
        else:
            raise RuntimeError(f"Unknown tool: {name}")

        return json.dumps(result, ensure_ascii=False)

    async def process_message(self, message: str) -> AsyncGenerator[str, None]:
        from google import genai
        from google.genai import types

        if not settings.gemini_api_key:
            yield json.dumps({
                "type": "text",
                "content": "Gemini is not configured yet. Add GEMINI_API_KEY to backend/.env, then restart the backend server."
            }) + "\n"
            return

        if not hasattr(self, "gemini_client"):
            try:
                self.gemini_client = genai.Client(api_key=settings.gemini_api_key)
            except Exception as e:
                yield json.dumps({
                    "type": "text",
                    "content": f"Gemini client setup failed: {e}"
                }) + "\n"
                return
            
        if message:
            memory_manager.add_message("user", message)

        available_tools = await self.get_tools()
        external_tools = [tool for tool in available_tools if not tool["name"].startswith("memory__")]
        integration_status = (
            "No external integrations are connected in this running build. "
            "You cannot read Gmail, GitHub, Notion, or Google Calendar yet. "
            if not external_tools
            else "External integrations are available only through the provided tools. "
        )
        integration_status += f"Available tools: {', '.join(tool['name'] for tool in available_tools)}."

        system_prompt = (
            "You are NexusAI, a concise personal assistant. Answer the user's exact request directly. "
            "Do not introduce yourself unless the user asks who you are. "
            "Do not list your capabilities unless the user explicitly asks what you can do. "
            "Do not use Markdown formatting; write plain text only. "
            "Only claim external facts from actual tool results. "
            "When the user explicitly asks you to remember a stable preference or fact, use memory__save_preference. "
            "Use memory__get_preferences when saved preferences would help answer the user. "
            "If Gmail, GitHub, Notion, or Google Calendar tools are unavailable or not connected, say so plainly. "
            "Never invent emails, issues, calendar events, Notion pages, senders, counts, or message contents. "
            f"{integration_status}"
        )
        
        final_text_blocks = []
        used_tools = []
        task_status = "completed"

        try:
            async for chunk in self._process_message(message, system_prompt, available_tools, types):
                try:
                    payload = json.loads(chunk)
                    if payload.get("type") == "text":
                        final_text_blocks.append(payload.get("content", ""))
                    elif payload.get("type") == "tool_start":
                        used_tools.append(payload.get("tool", "unknown"))
                    elif payload.get("type") == "tool_error":
                        task_status = "failed"
                except json.JSONDecodeError:
                    pass
                yield chunk
        finally:
            if message:
                summary = "\n".join(text for text in final_text_blocks if text).strip()
                if used_tools:
                    summary = f"{summary}\nTools used: {', '.join(used_tools)}".strip()
                if not summary:
                    summary = "No final response was produced."
                memory_manager.save_task(
                    description=message,
                    result_summary=summary[:2000],
                    status=task_status,
                )

    async def _process_message(self, message: str, system_prompt: str, available_tools: list, types) -> AsyncGenerator[str, None]:
        while True:
            history = memory_manager.get_history()
            yield json.dumps({"type": "status", "content": "Thinking..."}) + "\n"
            
            gemini_history = []
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                if isinstance(msg["content"], str):
                    gemini_history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
                elif isinstance(msg["content"], list):
                    parts = []
                    for c in msg["content"]:
                        if c.get("type") == "text":
                            parts.append(types.Part.from_text(text=c["text"]))
                        elif c.get("type") == "tool_use":
                            parts.append(types.Part.from_function_call(name=c["name"], args=c["input"]))
                        elif c.get("type") == "tool_result":
                            parts.append(types.Part.from_function_response(name=c.get("tool", "unknown"), response={"result": c["content"]}))
                    gemini_history.append(types.Content(role=role, parts=parts))

            gemini_tools = []
            for t in available_tools:
                gemini_tools.append(types.FunctionDeclaration(
                    name=t["name"],
                    description=t["description"],
                    parameters=t["input_schema"]
                ))
            tools = [types.Tool(function_declarations=gemini_tools)] if gemini_tools else None
            
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=tools,
                temperature=0.0
            )
            
            try:
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=gemini_history,
                    config=config
                )
            except Exception as e:
                yield json.dumps({
                    "type": "text",
                    "content": f"Gemini request failed: {e}"
                }) + "\n"
                return
            
            assistant_content = []
            text_blocks = []
            tool_calls = []
            
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        text_blocks.append(part.text)
                        assistant_content.append({"type": "text", "text": part.text})
                    elif part.function_call:
                        call_id = f"call_{uuid.uuid4().hex[:8]}"
                        args = dict(part.function_call.args) if part.function_call.args else {}
                        assistant_content.append({
                            "type": "tool_use",
                            "id": call_id,
                            "name": part.function_call.name,
                            "input": args
                        })
                        tool_calls.append({"id": call_id, "name": part.function_call.name, "input": args})
                        
            memory_manager.add_message("assistant", assistant_content)
            
            if text_blocks:
                yield json.dumps({"type": "text", "content": "\n".join(text_blocks)}) + "\n"
                
            if not tool_calls:
                break
                
            tool_results = []
            for tc in tool_calls:
                yield json.dumps({"type": "tool_start", "tool": tc["name"], "input": tc["input"]}) + "\n"
                is_write = any(w in tc["name"].lower() for w in ["write", "send", "create", "update", "delete", "post", "add", "schedule"])
                
                if is_write:
                    call_id = tc["id"]
                    event = asyncio.Event()
                    self.pending_actions[call_id] = event
                    self.action_results[call_id] = None
                    
                    yield json.dumps({"type": "pause", "call_id": call_id, "tool": tc["name"], "input": tc["input"]}) + "\n"
                    await event.wait()
                    decision = self.action_results.pop(call_id)
                    del self.pending_actions[call_id]
                    
                    if decision == "rejected":
                        result = "User REJECTED this action. Do not try again."
                        yield json.dumps({"type": "tool_result", "tool": tc["name"], "result": result, "status": "rejected"}) + "\n"
                        tool_results.append({"type": "tool_result", "tool_use_id": call_id, "tool": tc["name"], "content": result})
                        continue
                try:
                    res = await self.call_tool(tc["name"], tc["input"])
                    yield json.dumps({"type": "tool_result", "tool": tc["name"], "result": res, "status": "success"}) + "\n"
                    tool_results.append({"type": "tool_result", "tool_use_id": tc["id"], "tool": tc["name"], "content": res})
                except Exception as e:
                    error_msg = f"Error: {e}"
                    yield json.dumps({"type": "tool_error", "tool": tc["name"], "error": error_msg}) + "\n"
                    tool_results.append({"type": "tool_result", "tool_use_id": tc["id"], "tool": tc["name"], "content": error_msg})
                    
            memory_manager.add_message("user", tool_results)

    async def approve_action(self, call_id: str):
        if call_id in self.pending_actions:
            self.action_results[call_id] = "approved"
            self.pending_actions[call_id].set()
            return True
        return False
        
    async def reject_action(self, call_id: str):
        if call_id in self.pending_actions:
            self.action_results[call_id] = "rejected"
            self.pending_actions[call_id].set()
            return True
        return False

nexus_agent = Agent()
