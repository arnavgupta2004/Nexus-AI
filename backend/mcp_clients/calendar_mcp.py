import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from config import settings

class CalendarMCPClient:
    def __init__(self):
        self.client_id = settings.google_calendar_client_id
        self.client_secret = settings.google_calendar_client_secret
        self.server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-calendar"],
            env={**os.environ, "GOOGLE_CALENDAR_CLIENT_ID": self.client_id, "GOOGLE_CALENDAR_CLIENT_SECRET": self.client_secret} if self.client_id else os.environ
        )
        self.client_context = None
        self.session = None

    async def connect(self):
        if not self.client_id:
            return None
        try:
            self.client_context = stdio_client(self.server_params)
            read, write = await self.client_context.__aenter__()
            self.session = ClientSession(read, write)
            await self.session.__aenter__()
            await self.session.initialize()
        except:
            pass
        return self.session

    async def get_tools(self):
        if self.session:
            tools = await self.session.list_tools()
            return tools.tools
        return []

calendar_mcp = CalendarMCPClient()
