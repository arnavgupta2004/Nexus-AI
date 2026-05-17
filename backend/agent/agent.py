import json
import asyncio
import uuid
from typing import Dict, AsyncGenerator
from agent.memory import memory_manager
from config import settings

class Agent:
    def __init__(self):
        self.pending_actions: Dict[str, asyncio.Event] = {}
        self.action_results: Dict[str, str] = {}
        self.mcp_clients = {}

    async def init_mcps(self):
        pass

    async def get_tools(self):
        return []

    async def call_tool(self, name: str, args: dict) -> str:
        raise RuntimeError(f"{name} is not connected to a real integration yet.")

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
        integration_status = (
            "No external integrations are connected in this running build. "
            "You cannot read Gmail, GitHub, Notion, or Google Calendar yet."
            if not available_tools
            else "External integrations are available only through the provided tools."
        )

        system_prompt = (
            "You are NexusAI, an autonomous agent. Only claim external facts from actual tool results. "
            "If Gmail, GitHub, Notion, or Google Calendar tools are unavailable or not connected, say so plainly. "
            "Never invent emails, issues, calendar events, Notion pages, senders, counts, or message contents. "
            f"{integration_status}"
        )
        
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
