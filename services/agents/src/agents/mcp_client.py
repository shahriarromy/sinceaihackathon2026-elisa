"""MultiServerMCPClient configuration and tool discovery for Agent 1 and Agent 2."""

import logging
from typing import Dict, List, Optional
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from agents.config import (
    RAG_MCP_URL,
    TEAMS_MCP_URL,
    EMAIL_MCP_URL,
    SMS_MCP_URL,
    NEO4J_MCP_RO_URL,
    NEO4J_MCP_RW_URL,
)

logger = logging.getLogger("agents.mcp_client")


def create_mcp_connections() -> Dict[str, Dict[str, str]]:
    """Return dictionary of MCP server connections with SSE transport."""
    return {
        "rag": {"url": RAG_MCP_URL, "transport": "sse"},
        "teams": {"url": TEAMS_MCP_URL, "transport": "sse"},
        "email": {"url": EMAIL_MCP_URL, "transport": "sse"},
        "sms": {"url": SMS_MCP_URL, "transport": "sse"},
        "neo4j_ro": {"url": NEO4J_MCP_RO_URL, "transport": "sse"},
        "neo4j_rw": {"url": NEO4J_MCP_RW_URL, "transport": "sse"},
    }


def get_mcp_client(connections: Optional[Dict[str, Dict[str, str]]] = None) -> MultiServerMCPClient:
    """Create and return configured MultiServerMCPClient."""
    conns = connections or create_mcp_connections()
    return MultiServerMCPClient(connections=conns, handle_tool_errors=True)


async def get_agent1_tools(client: MultiServerMCPClient) -> List[BaseTool]:
    """Retrieve tools for Agent 1: read-only Neo4j and RAG store."""
    tools: List[BaseTool] = []
    for server_name in ["rag", "neo4j_ro"]:
        try:
            server_tools = await client.get_tools(server_name=server_name)
            tools.extend(server_tools)
        except Exception as e:
            logger.warning(f"Could not load tools from server '{server_name}': {e}")
    return tools


async def get_agent2_tools(client: MultiServerMCPClient) -> List[BaseTool]:
    """Retrieve tools for Agent 2: RAG, channel MCPs (teams, email, sms), and writeable Neo4j."""
    tools: List[BaseTool] = []
    for server_name in ["rag", "teams", "email", "sms", "neo4j_rw"]:
        try:
            server_tools = await client.get_tools(server_name=server_name)
            tools.extend(server_tools)
        except Exception as e:
            logger.warning(f"Could not load tools from server '{server_name}': {e}")
    return tools
