import json
import asyncio
import uuid
from typing import Dict, Any, AsyncGenerator
from anthropic import AsyncAnthropic
from agent.memory import memory_manager
from config import settings

class Agent:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.pending_actions: Dict[str, asyncio.Event] = {}
        self.action_results: Dict[str, str] = {}
        self.mcp_clients = {}

    async def init_mcps(self):
        pass

    async def get_tools(self):
        return [
                {
                    "name": "gmail__read_emails",
                    "description": "Read unread emails",
                    "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}}
                },
                {
                    "name": "gmail__send_email",
                    "description": "Send an email",
                    "input_schema": {"type": "object", "properties": {"to": {"type": "string"}, "body": {"type": "string"}}}
                },
                {
                    "name": "github__list_issues",
                    "description": "Read github issues",
                    "input_schema": {"type": "object", "properties": {"repo": {"type": "string"}}}
                },
                {
                    "name": "notion__create_page",
                    "description": "Create a notion page",
                    "input_schema": {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}}}
                },
                {
                    "name": "calendar__schedule_event",
                    "description": "Schedule a calendar event",
                    "input_schema": {"type": "object", "properties": {"title": {"type": "string"}, "time": {"type": "string"}}}
                }
            ]

    async def call_tool(self, name: str, args: dict) -> str:
        await asyncio.sleep(2)
        if "read_emails" in name:
            return "You have 1 unread email from your boss asking about the GitHub issue #42."
        elif "list_issues" in name:
            return "Issue #42: Fix memory leak in production. Overdue by 2 days."
        elif "schedule_event" in name:
            return "Event scheduled for tomorrow."
        return f"Simulated success for {name} with args {args}"

    async def process_message(self, message: str, provider: str = "gemini") -> AsyncGenerator[str, None]:
        if provider == "gemini":
            async for chunk in self.process_message_gemini(message):
                yield chunk
            return

        if message:
            memory_manager.add_message("user", message)
        
        system_prompt = (
            "You are NexusAI, an autonomous agent. You connect to Gmail, GitHub, Notion, "
            "and Google Calendar via Tools. Break tasks down. ALWAYS wait for results after calling a tool."
        )
        
        while True:
            history = memory_manager.get_history()
            
            yield json.dumps({"type": "status", "content": "Thinking..."}) + "\n"
            
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                system=system_prompt,
                messages=history,
                tools=await self.get_tools()
            )
            
            assistant_content = []
            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
                    
            memory_manager.add_message("assistant", assistant_content)
            
            tool_calls = [c for c in response.content if c.type == "tool_use"]
            text_blocks = [c.text for c in response.content if c.type == "text"]
            
            if text_blocks:
                yield json.dumps({"type": "text", "content": "\n".join(text_blocks)}) + "\n"
            
            if not tool_calls:
                break
                
            tool_results = []
            for tool_call in tool_calls:
                yield json.dumps({"type": "tool_start", "tool": tool_call.name, "input": tool_call.input}) + "\n"
                
                is_write = any(w in tool_call.name.lower() for w in ["write", "send", "create", "update", "delete", "post", "add", "schedule"])
                
                if is_write:
                    call_id = tool_call.id
                    event = asyncio.Event()
                    self.pending_actions[call_id] = event
                    self.action_results[call_id] = None
                    
                    yield json.dumps({"type": "pause", "call_id": call_id, "tool": tool_call.name, "input": tool_call.input}) + "\n"
                    
                    await event.wait()
                    
                    decision = self.action_results.pop(call_id)
                    del self.pending_actions[call_id]
                    
                    if decision == "rejected":
                        result = "User REJECTED this action. Do not try again."
                        yield json.dumps({"type": "tool_result", "tool": tool_call.name, "result": result, "status": "rejected"}) + "\n"
                        tool_results.append({"type": "tool_result", "tool_use_id": call_id, "content": result})
                        continue
                
                try:
                    res = await self.call_tool(tool_call.name, tool_call.input)
                    yield json.dumps({"type": "tool_result", "tool": tool_call.name, "result": res, "status": "success"}) + "\n"
                    tool_results.append({"type": "tool_result", "tool_use_id": tool_call.id, "content": res})
                except Exception as e:
                    error_msg = f"Error: {e}"
                    yield json.dumps({"type": "tool_error", "tool": tool_call.name, "error": error_msg}) + "\n"
                    tool_results.append({"type": "tool_result", "tool_use_id": tool_call.id, "content": error_msg})
            
            memory_manager.add_message("user", tool_results)

    async def process_message_gemini(self, message: str) -> AsyncGenerator[str, None]:
        from google import genai
        from google.genai import types
        
        if not hasattr(self, "gemini_client"):
            self.gemini_client = genai.Client(api_key=settings.gemini_api_key)
            
        if message:
            memory_manager.add_message("user", message)
            
        system_prompt = (
            "You are NexusAI, an autonomous agent. You connect to Gmail, GitHub, Notion, "
            "and Google Calendar via Tools. Break tasks down. ALWAYS wait for results after calling a tool."
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

            anthropic_tools = await self.get_tools()
            gemini_tools = []
            for t in anthropic_tools:
                gemini_tools.append(types.FunctionDeclaration(
                    name=t["name"],
                    description=t["description"],
                    parameters=t["input_schema"]
                ))
            tool_config = types.Tool(function_declarations=gemini_tools)
            
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=[tool_config],
                temperature=0.0
            )
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=gemini_history,
                config=config
            )
            
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
