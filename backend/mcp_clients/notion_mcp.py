import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from config import settings

class NotionMCPClient:
    def __init__(self):
        self.api_key = settings.notion_api_key
        # Assuming there is a community Notion MCP server like @modelcontextprotocol/server-notion
        # Or an equivalent Python package like mcp-server-notion
        self.server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-notion"],
            env={**os.environ, "NOTION_API_KEY": self.api_key} if self.api_key else os.environ
        )
        self.client_context = None
        self.session = None

    async def connect(self):
        if not self.api_key:
            return None
        self.client_context = stdio_client(self.server_params)
        read, write = await self.client_context.__aenter__()
        self.session = ClientSession(read, write)
        await self.session.__aenter__()
        await self.session.initialize()
        return self.session

    async def get_tools(self):
        if self.session:
            tools = await self.session.list_tools()
            return tools.tools
        return []

notion_mcp = NotionMCPClient()
