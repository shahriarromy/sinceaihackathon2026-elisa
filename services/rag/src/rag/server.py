"""FastMCP RAG service wrapping ChromaDB with offline ONNX MiniLM embeddings."""

import hashlib
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.utils import embedding_functions
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("rag-mcp")

# Environment variables
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ops_knowledge")

mcp = FastMCP("rag-mcp")

_client = None
_collection = None


def get_collection():
    """Return active Chroma collection, connecting to remote HTTP or local fallback."""
    global _client, _collection
    if _collection is not None:
        return _collection

    ef = embedding_functions.DefaultEmbeddingFunction()

    # Try HttpClient first
    try:
        logger.info(f"Connecting to Chroma at {CHROMA_HOST}:{CHROMA_PORT}...")
        _client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        # Test heartbeat
        _client.heartbeat()
        logger.info("Connected to remote ChromaDB successfully.")
    except Exception as e:
        logger.warning(f"Remote ChromaDB not reachable ({e}). Using local persistent client fallback.")
        local_dir = os.getenv("CHROMA_LOCAL_PATH", "./chroma_data")
        os.makedirs(local_dir, exist_ok=True)
        _client = chromadb.PersistentClient(path=local_dir)

    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


class RAGSearchResult(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any]
    distance: float


class RAGAddResult(BaseModel):
    id: str
    status: str


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Service health check returning collection stats."""
    try:
        col = get_collection()
        count = col.count()
        return JSONResponse({
            "status": "healthy",
            "service": "rag-mcp",
            "collection": COLLECTION_NAME,
            "document_count": count,
        })
    except Exception as e:
        logger.error(f"Healthcheck failed: {e}")
        return JSONResponse({"status": "unhealthy", "error": str(e)}, status_code=503)


@mcp.tool(name="rag_search", description="Search ops knowledge RAG store by query and optional entity filter")
def rag_search(query: str, entity_id: Optional[str] = None, k: int = 5) -> List[Dict[str, Any]]:
    """Search ops_knowledge collection with cosine similarity and optional entity_id filter."""
    col = get_collection()
    n_results = max(k * 2 if entity_id else k, 1)

    query_res = col.query(
        query_texts=[query],
        n_results=min(n_results, max(col.count(), 1)),
        include=["documents", "metadatas", "distances"],
    )

    results: List[Dict[str, Any]] = []
    ids = query_res.get("ids", [[]])[0]
    docs = query_res.get("documents", [[]])[0]
    metas = query_res.get("metadatas", [[]])[0]
    dists = query_res.get("distances", [[]])[0]

    for doc_id, doc, meta, dist in zip(ids, docs, metas, dists):
        meta_dict = meta or {}
        # Apply entity_id filter if provided
        if entity_id:
            e_ids = [e.strip() for e in str(meta_dict.get("entity_ids", "")).split(",") if e.strip()]
            if entity_id not in e_ids and entity_id not in doc:
                continue

        results.append(
            RAGSearchResult(
                id=doc_id,
                text=doc,
                metadata=meta_dict,
                distance=float(dist) if dist is not None else 0.0,
            ).model_dump()
        )
        if len(results) >= k:
            break

    return results


@mcp.tool(name="rag_add", description="Add or update a knowledge chunk in RAG store idempotently")
def rag_add(text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Idempotently add a document with scalar metadata to Chroma ops_knowledge collection."""
    col = get_collection()

    source_ref = str(metadata.get("source_ref", "")).strip()
    source_type = str(metadata.get("source_type", "unknown")).strip()
    author = str(metadata.get("author", "unknown")).strip()
    timestamp = str(metadata.get("timestamp", "")).strip()
    incident_id = str(metadata.get("incident_id", "")).strip()
    kind = str(metadata.get("kind", "troubleshooting_knowledge")).strip()

    raw_entity_ids = metadata.get("entity_ids", "")
    if isinstance(raw_entity_ids, list):
        entity_ids = ",".join(str(e) for e in raw_entity_ids)
    else:
        entity_ids = str(raw_entity_ids)

    # Deterministic ID hash based on source_ref or content
    seed_str = f"{source_type}:{source_ref}" if source_ref else text
    doc_id = f"rag-{hashlib.sha256(seed_str.encode('utf-8')).hexdigest()[:16]}"

    clean_metadata = {
        "source_type": source_type,
        "source_ref": source_ref,
        "author": author,
        "timestamp": timestamp,
        "entity_ids": entity_ids,
        "incident_id": incident_id,
        "kind": kind,
    }

    col.upsert(
        ids=[doc_id],
        documents=[text],
        metadatas=[clean_metadata],
    )

    logger.info(f"Upserted document {doc_id} from {source_ref}")
    return RAGAddResult(id=doc_id, status="upserted").model_dump()


@mcp.tool(name="rag_list_sources", description="List all indexed sources and counts in the RAG store")
def rag_list_sources() -> Dict[str, Any]:
    """Retrieve summary of all indexed sources in the collection."""
    col = get_collection()
    total = col.count()
    if total == 0:
        return {"total_documents": 0, "sources": []}

    all_data = col.get(include=["metadatas"])
    sources_map: Dict[str, Dict[str, Any]] = {}

    for meta in all_data.get("metadatas", []):
        if not meta:
            continue
        ref = meta.get("source_ref", "unknown")
        if ref not in sources_map:
            sources_map[ref] = {
                "source_ref": ref,
                "source_type": meta.get("source_type", "unknown"),
                "author": meta.get("author", "unknown"),
                "timestamp": meta.get("timestamp", ""),
                "entity_ids": meta.get("entity_ids", ""),
            }

    return {
        "total_documents": total,
        "sources": list(sources_map.values()),
    }


def ingest_seed_data() -> Dict[str, int]:
    """Load dummy Teams, Email, and SMS files into ops_knowledge collection."""
    logger.info("Ingesting seed dummy channel files into RAG...")
    col = get_collection()
    root_candidates = [
        Path("./data"),
        Path("../../data"),
        Path("../../../data"),
    ]
    data_root = None
    for cand in root_candidates:
        if cand.exists() and (cand / "teams").exists():
            data_root = cand
            break

    if not data_root:
        logger.warning("Could not find data root directory for seed ingestion")
        return {"ingested": 0}

    ingested = 0

    # 1. Teams
    teams_dir = data_root / "teams"
    if teams_dir.exists():
        for f in sorted(teams_dir.glob("*.json")):
            try:
                raw = json.loads(f.read_text(encoding="utf-8"))
                tid = raw.get("thread_id", f.stem)
                topic = raw.get("topic", "")
                messages = raw.get("messages", [])
                body_parts = [f"Topic: {topic}"]
                authors = set()
                for m in messages:
                    author = m.get("author", "")
                    if author:
                        authors.add(author)
                    body_parts.append(f"[{m.get('timestamp')}] {author}: {m.get('text')}")
                text = "\n\n".join(body_parts)

                # Extract potential entity IDs mentioned
                entities = re.findall(r"\b(TRN-\d+|AGR-\d+|MWR-\d+|TX-\d+|MW-\d+|SFP-[A-Z0-9]+)\b", text)
                rag_add(
                    text=text,
                    metadata={
                        "source_type": "teams",
                        "source_ref": f"teams/{f.name}",
                        "author": ", ".join(sorted(authors)),
                        "timestamp": messages[0].get("timestamp", "") if messages else "",
                        "entity_ids": ",".join(sorted(set(entities))),
                        "incident_id": "WO-2026-0312-007" if "TRN-042" in text else "",
                        "kind": "troubleshooting_knowledge",
                    },
                )
                ingested += 1
            except Exception as e:
                logger.error(f"Error indexing Teams {f}: {e}")

    # 2. Email
    email_dir = data_root / "email"
    if email_dir.exists():
        for f in sorted(email_dir.glob("*.txt")):
            try:
                content = f.read_text(encoding="utf-8")
                subject_m = re.search(r"^Subject:\s*(.*)$", content, re.MULTILINE)
                author_m = re.search(r"^From:\s*(.*)$", content, re.MULTILINE)
                date_m = re.search(r"^Date:\s*(.*)$", content, re.MULTILINE)

                subject = subject_m.group(1).strip() if subject_m else ""
                author = author_m.group(1).strip() if author_m else ""
                date_str = date_m.group(1).strip() if date_m else ""

                entities = re.findall(r"\b(TRN-\d+|AGR-\d+|MWR-\d+|SAL-\d+|KEM-\d+|SOD-\d+|INA-\d+)\b", content)
                kind = "access_information" if "barrier" in content.lower() or "gate" in content.lower() or "key" in content.lower() else "troubleshooting_knowledge"

                rag_add(
                    text=content,
                    metadata={
                        "source_type": "email",
                        "source_ref": f"email/{f.name}",
                        "author": author,
                        "timestamp": date_str,
                        "entity_ids": ",".join(sorted(set(entities))),
                        "incident_id": "",
                        "kind": kind,
                    },
                )
                ingested += 1
            except Exception as e:
                logger.error(f"Error indexing Email {f}: {e}")

    # 3. SMS
    sms_dir = data_root / "sms"
    if sms_dir.exists():
        for f in sorted(sms_dir.glob("*.json")):
            try:
                raw = json.loads(f.read_text(encoding="utf-8"))
                cid = raw.get("conversation_id", f.stem)
                messages = raw.get("messages", [])
                body_parts = [f"SMS {cid}"]
                authors = set()
                for m in messages:
                    author = m.get("from", "")
                    if author:
                        authors.add(author)
                    body_parts.append(f"[{m.get('timestamp')}] {author}: {m.get('text')}")
                text = "\n\n".join(body_parts)

                entities = re.findall(r"\b(TRN-\d+|AGR-\d+|MWR-\d+|SAL-\d+|KEM-\d+|SOD-\d+|INA-\d+)\b", text)
                rag_add(
                    text=text,
                    metadata={
                        "source_type": "sms",
                        "source_ref": f"sms/{f.name}",
                        "author": ", ".join(sorted(authors)),
                        "timestamp": messages[0].get("timestamp", "") if messages else "",
                        "entity_ids": ",".join(sorted(set(entities))),
                        "incident_id": "",
                        "kind": "access_information",
                    },
                )
                ingested += 1
            except Exception as e:
                logger.error(f"Error indexing SMS {f}: {e}")

    logger.info(f"Seed ingestion complete. Ingested {ingested} items. Total in collection: {col.count()}")
    return {"ingested": ingested, "total": col.count()}


@mcp.custom_route("/ingest_seed", methods=["POST", "GET"])
async def ingest_seed_endpoint(request: Request) -> JSONResponse:
    """Trigger seed ingestion of all dummy channel documents into RAG."""
    stats = ingest_seed_data()
    return JSONResponse({"status": "success", "stats": stats})


def ingest_seed_cli():
    """CLI entrypoint for manual seed ingestion."""
    stats = ingest_seed_data()
    print(f"Seed ingestion complete: {stats}")


def main():
    logger.info("Starting rag-mcp on 0.0.0.0:8000")
    # On first startup, run seed ingestion if empty
    try:
        col = get_collection()
        if col.count() == 0:
            logger.info("Collection is empty; running automatic seed ingestion...")
            ingest_seed_data()
    except Exception as e:
        logger.warning(f"Could not auto-ingest seed on start: {e}")

    mcp.run(transport="sse", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
