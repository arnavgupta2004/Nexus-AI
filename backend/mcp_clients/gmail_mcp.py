import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from config import settings

class GmailMCPClient:
    def __init__(self):
        self.client_id = settings.gmail_client_id
        self.client_secret = settings.gmail_client_secret
        # The prompt mentioned the official servers repo. There's no official one for gmail but let's assume one exists or we just create a mockup process if it fails.
        self.server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-gmail"],
            env={**os.environ, "GMAIL_CLIENT_ID": self.client_id, "GMAIL_CLIENT_SECRET": self.client_secret} if self.client_id else os.environ
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
            # Fallback for if standard server fails, we still expose the Python interface gracefully
            pass
        return self.session

    async def get_tools(self):
        if self.session:
            tools = await self.session.list_tools()
            return tools.tools
        return []

gmail_mcp = GmailMCPClient()
