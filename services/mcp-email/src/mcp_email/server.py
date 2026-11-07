"""FastMCP Email channel service reading dummy email text files."""

import email
from email import policy
import logging
import os
import re
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
logger = logging.getLogger("mcp-email")

# Locate data directory
DATA_DIR = os.getenv("DATA_DIR", "/data")
if not os.path.exists(DATA_DIR):
    local_candidates = [
        Path("./data/email"),
        Path("../../data/email"),
        Path("../../../data/email"),
    ]
    for cand in local_candidates:
        if cand.exists():
            DATA_DIR = str(cand.resolve())
            break

logger.info(f"Using DATA_DIR: {DATA_DIR}")

mcp = FastMCP("mcp-email")


class EmailItem(BaseModel):
    id: str = Field(description="Email ID, e.g. TH-E-001")
    timestamp: str = Field(description="ISO timestamp / date header")
    participants: List[str] = Field(description="Sender and recipient(s)")
    author: str = Field(description="Sender display name/address")
    recipient: str = Field(description="Recipient display name/address")
    subject: str = Field(description="Subject header")
    body: str = Field(description="Email body text")
    source_type: str = "email"


def _load_emails() -> Dict[str, EmailItem]:
    """Load and parse all RFC822/plaintext email files from DATA_DIR."""
    data_path = Path(DATA_DIR)
    emails: Dict[str, EmailItem] = {}
    if not data_path.exists():
        logger.warning(f"Data directory {DATA_DIR} does not exist")
        return emails

    for filepath in sorted(data_path.glob("*.txt")):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            msg = email.message_from_string(content, policy=policy.default)
            msg_id = filepath.stem
            # Check Message-ID header if present
            raw_msg_id = msg.get("Message-ID", "")
            m = re.search(r"<([^@>]+)", raw_msg_id)
            if m:
                msg_id = m.group(1)

            author = str(msg.get("From", "Unknown")).strip('"\' \t\r\n')
            recipient = str(msg.get("To", "Unknown")).strip('"\' \t\r\n')
            subject = str(msg.get("Subject", "")).strip()
            date_str = str(msg.get("Date", "")).strip()
            body = msg.get_body(preferencelist=("plain",))
            body_text = body.get_content() if body else content.split("\n\n", 1)[-1]

            participants = [p.strip() for p in [author, recipient] if p.strip()]

            item = EmailItem(
                id=msg_id,
                timestamp=date_str,
                participants=participants,
                author=author,
                recipient=recipient,
                subject=subject,
                body=body_text.strip(),
                source_type="email",
            )
            emails[msg_id] = item
        except Exception as e:
            logger.error(f"Error parsing email {filepath}: {e}")

    return emails


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Service health endpoint."""
    items = _load_emails()
    return JSONResponse({
        "status": "healthy",
        "channel": "email",
        "data_dir": DATA_DIR,
        "email_count": len(items),
    })


@mcp.tool(name="list_emails", description="List emails, optionally filtered by timestamp")
def list_emails(since: Optional[str] = None) -> List[Dict[str, Any]]:
    """List available emails, optionally filtered by since."""
    items = list(_load_emails().values())
    if since:
        items = [e for e in items if e.timestamp >= since]
    items.sort(key=lambda x: x.timestamp)
    return [e.model_dump() for e in items]


@mcp.tool(name="get_email", description="Get full email content and metadata by ID")
def get_email(id: str) -> Dict[str, Any]:
    """Retrieve a single email by ID."""
    emails = _load_emails()
    if id in emails:
        return emails[id].model_dump()
    raise ValueError(f"Email {id} not found")


@mcp.tool(name="get_latest_emails", description="Get the most recent n emails")
def get_latest_emails(n: int = 5) -> List[Dict[str, Any]]:
    """Retrieve latest n emails ordered by timestamp descending."""
    items = list(_load_emails().values())
    items.sort(key=lambda x: x.timestamp, reverse=True)
    return [e.model_dump() for e in items[:n]]


def main():
    logger.info("Starting mcp-email on 0.0.0.0:8000")
    mcp.run(transport="sse", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
