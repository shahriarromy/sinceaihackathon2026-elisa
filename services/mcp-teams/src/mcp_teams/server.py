"""FastMCP Teams channel service reading Teams conversations."""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("mcp-teams")

# Locate data directory
DATA_DIR = os.getenv("DATA_DIR", "/data")
if not os.path.exists(DATA_DIR):
    local_candidates = [
        Path("./data/teams"),
        Path("../../data/teams"),
        Path("../../../data/teams"),
    ]
    for cand in local_candidates:
        if cand.exists():
            DATA_DIR = str(cand.resolve())
            break

logger.info(f"Using DATA_DIR: {DATA_DIR}")

mcp = FastMCP("mcp-teams")


class TeamsMessage(BaseModel):
    seq: int
    timestamp: str
    author: str
    role: Optional[str] = None
    text: str


class ConversationItem(BaseModel):
    id: str = Field(description="Conversation thread ID")
    timestamp: str = Field(description="Timestamp of conversation (earliest message)")
    latest_timestamp: str = Field(description="Timestamp of latest message in thread")
    participants: List[str] = Field(description="List of participant names")
    subject: str = Field(description="Topic/subject of conversation")
    body: str = Field(description="Formatted full text body of conversation")
    source_type: str = "teams"
    messages: List[TeamsMessage] = Field(default_factory=list)


def _load_conversations() -> Dict[str, ConversationItem]:
    """Load and parse all conversation json files from DATA_DIR."""
    data_path = Path(DATA_DIR)
    conversations: Dict[str, ConversationItem] = {}
    if not data_path.exists():
        logger.warning(f"Data directory {DATA_DIR} does not exist")
        return conversations

    for filepath in sorted(data_path.glob("*.json")):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
            thread_id = raw.get("thread_id") or filepath.stem
            topic = raw.get("topic", "")
            participants = raw.get("participants", [])
            raw_msgs = raw.get("messages", [])

            messages = [
                TeamsMessage(
                    seq=m.get("seq", i + 1),
                    timestamp=m.get("timestamp", ""),
                    author=m.get("author", "Unknown"),
                    role=m.get("role"),
                    text=m.get("text", ""),
                )
                for i, m in enumerate(raw_msgs)
            ]

            first_ts = messages[0].timestamp if messages else ""
            last_ts = messages[-1].timestamp if messages else ""

            body_lines = [f"Topic: {topic}"]
            for m in messages:
                role_info = f" ({m.role})" if m.role else ""
                body_lines.append(f"[{m.timestamp}] {m.author}{role_info}:\n{m.text}")
            full_body = "\n\n".join(body_lines)

            item = ConversationItem(
                id=thread_id,
                timestamp=first_ts,
                latest_timestamp=last_ts,
                participants=participants,
                subject=topic,
                body=full_body,
                source_type="teams",
                messages=messages,
            )
            conversations[thread_id] = item
        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")

    return conversations


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Service health endpoint."""
    convs = _load_conversations()
    return JSONResponse({
        "status": "healthy",
        "channel": "teams",
        "data_dir": DATA_DIR,
        "conversation_count": len(convs),
    })


@mcp.tool(name="list_conversations", description="List Teams conversations, optionally after a timestamp")
def list_conversations(since: Optional[str] = None) -> List[Dict[str, Any]]:
    """List available Teams conversations, optionally filtered by since."""
    convs = _load_conversations()
    items = list(convs.values())
    if since:
        items = [c for c in items if (c.latest_timestamp >= since or c.timestamp >= since)]
    items.sort(key=lambda x: x.timestamp)
    return [c.model_dump() for c in items]


@mcp.tool(name="get_conversation", description="Get full details of a Teams conversation by ID")
def get_conversation(id: str) -> Dict[str, Any]:
    """Retrieve a single Teams conversation by thread ID."""
    convs = _load_conversations()
    if id in convs:
        return convs[id].model_dump()
    raise ValueError(f"Conversation {id} not found in Teams data")


@mcp.tool(name="get_latest_conversations", description="Get the most recent n Teams conversations")
def get_latest_conversations(n: int = 5) -> List[Dict[str, Any]]:
    """Retrieve latest n conversations ordered by timestamp descending."""
    convs = _load_conversations()
    items = list(convs.values())
    items.sort(key=lambda x: x.latest_timestamp or x.timestamp, reverse=True)
    return [c.model_dump() for c in items[:n]]


def main():
    logger.info("Starting mcp-teams on 0.0.0.0:8000")
    mcp.run(transport="sse", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
