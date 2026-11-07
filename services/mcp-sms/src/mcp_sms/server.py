"""FastMCP SMS channel service reading dummy SMS conversations."""

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
logger = logging.getLogger("mcp-sms")

# Locate data directory
DATA_DIR = os.getenv("DATA_DIR", "/data")
if not os.path.exists(DATA_DIR):
    local_candidates = [
        Path("./data/sms"),
        Path("../../data/sms"),
        Path("../../../data/sms"),
    ]
    for cand in local_candidates:
        if cand.exists():
            DATA_DIR = str(cand.resolve())
            break

logger.info(f"Using DATA_DIR: {DATA_DIR}")

mcp = FastMCP("mcp-sms")


class SMSMessage(BaseModel):
    seq: int
    timestamp: str
    from_user: str = Field(alias="from")
    to_users: List[str] = Field(alias="to")
    text: str

    model_config = {"populate_by_name": True}


class SMSConversationItem(BaseModel):
    id: str = Field(description="Conversation/thread ID")
    timestamp: str = Field(description="Earliest message timestamp")
    latest_timestamp: str = Field(description="Latest message timestamp")
    participants: List[str] = Field(description="Participants in conversation")
    subject: str = Field(description="Summary / channel name")
    body: str = Field(description="Formatted conversation text")
    source_type: str = "sms"
    messages: List[SMSMessage] = Field(default_factory=list)


def _load_sms_conversations() -> Dict[str, SMSConversationItem]:
    """Load and parse SMS JSON files from DATA_DIR."""
    data_path = Path(DATA_DIR)
    conversations: Dict[str, SMSConversationItem] = {}
    if not data_path.exists():
        logger.warning(f"Data directory {DATA_DIR} does not exist")
        return conversations

    for filepath in sorted(data_path.glob("*.json")):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)

            conv_id = raw.get("conversation_id") or filepath.stem
            participants = raw.get("participants", [])
            raw_msgs = raw.get("messages", [])

            messages = [
                SMSMessage(
                    seq=m.get("seq", i + 1),
                    timestamp=m.get("timestamp", ""),
                    from_user=m.get("from", "Unknown"),
                    to_users=m.get("to", []),
                    text=m.get("text", ""),
                )
                for i, m in enumerate(raw_msgs)
            ]

            first_ts = messages[0].timestamp if messages else ""
            last_ts = messages[-1].timestamp if messages else ""

            body_lines = [f"SMS Conversation {conv_id} between {', '.join(participants)}:"]
            for m in messages:
                body_lines.append(f"[{m.timestamp}] {m.from_user} -> {', '.join(m.to_users)}:\n{m.text}")
            full_body = "\n\n".join(body_lines)

            item = SMSConversationItem(
                id=conv_id,
                timestamp=first_ts,
                latest_timestamp=last_ts,
                participants=participants,
                subject=f"SMS conversation {conv_id}",
                body=full_body,
                source_type="sms",
                messages=messages,
            )
            conversations[conv_id] = item
        except Exception as e:
            logger.error(f"Error parsing SMS file {filepath}: {e}")

    return conversations


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Service health endpoint."""
    items = _load_sms_conversations()
    return JSONResponse({
        "status": "healthy",
        "channel": "sms",
        "data_dir": DATA_DIR,
        "conversation_count": len(items),
    })


@mcp.tool(name="list_messages", description="List SMS conversations, optionally after a timestamp")
def list_messages(since: Optional[str] = None) -> List[Dict[str, Any]]:
    """List available SMS messages/conversations, optionally filtered by since."""
    items = list(_load_sms_conversations().values())
    if since:
        items = [s for s in items if (s.latest_timestamp >= since or s.timestamp >= since)]
    items.sort(key=lambda x: x.timestamp)
    return [s.model_dump() for s in items]


@mcp.tool(name="get_message", description="Get full SMS conversation by ID")
def get_message(id: str) -> Dict[str, Any]:
    """Retrieve a single SMS conversation by ID."""
    convs = _load_sms_conversations()
    if id in convs:
        return convs[id].model_dump()
    raise ValueError(f"SMS conversation {id} not found")


@mcp.tool(name="get_latest_messages", description="Get the most recent n SMS conversations")
def get_latest_messages(n: int = 5) -> List[Dict[str, Any]]:
    """Retrieve latest n SMS conversations ordered by timestamp descending."""
    items = list(_load_sms_conversations().values())
    items.sort(key=lambda x: x.latest_timestamp or x.timestamp, reverse=True)
    return [s.model_dump() for s in items[:n]]


def main():
    logger.info("Starting mcp-sms on 0.0.0.0:8000")
    mcp.run(transport="sse", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
