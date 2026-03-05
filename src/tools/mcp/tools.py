import asyncio
from concurrent.futures import ThreadPoolExecutor

from langchain_mcp_adapters.client import MultiServerMCPClient

from src.config import settings


def get_mcp_tools():
    with ThreadPoolExecutor(max_workers=1) as ex:
        return ex.submit(
            lambda: asyncio.run(_load_mcp_tools(settings.MCP_URL))
        ).result()


async def _load_mcp_tools(sse_url: str):
    client = MultiServerMCPClient(
        {
            "mcp": {
                "transport": "sse",
                "url": sse_url,
            }
        }
    )
    tools = await client.get_tools()
    return list(tools)
