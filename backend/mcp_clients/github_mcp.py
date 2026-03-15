import os
import contextlib
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from config import settings

class GitHubMCPClient:
    def __init__(self):
        self.token = settings.github_token
        self.server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={**os.environ, "GITHUB_PERSONAL_ACCESS_TOKEN": self.token} if self.token else os.environ
        )
        self.client_context = None
        self.session = None

    async def connect(self):
        if not self.token:
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

github_mcp = GitHubMCPClient()
