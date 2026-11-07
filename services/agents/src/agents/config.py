"""Configuration settings for agents service loaded from environment."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Try loading .env from repo root or local directory
for parent in Path(__file__).resolve().parents:
    env_candidate = parent / ".env"
    if env_candidate.exists():
        load_dotenv(env_candidate)
        break
else:
    load_dotenv()

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "hackathon_secret_password")

# LLM configuration (OpenAI compatible endpoint)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# MCP service URLs (SSE endpoints)
RAG_MCP_URL = os.getenv("RAG_MCP_URL", "http://rag-mcp:8000/sse")
TEAMS_MCP_URL = os.getenv("TEAMS_MCP_URL", "http://mcp-teams:8000/sse")
EMAIL_MCP_URL = os.getenv("EMAIL_MCP_URL", "http://mcp-email:8000/sse")
SMS_MCP_URL = os.getenv("SMS_MCP_URL", "http://mcp-sms:8000/sse")
NEO4J_MCP_RO_URL = os.getenv("NEO4J_MCP_RO_URL", "http://neo4j-mcp-ro:8000/sse")
NEO4J_MCP_RW_URL = os.getenv("NEO4J_MCP_RW_URL", "http://neo4j-mcp-rw:8000/sse")

# State tracking storage path
STATE_STORAGE_PATH = os.getenv("STATE_STORAGE_PATH", "./processed_items.json")
