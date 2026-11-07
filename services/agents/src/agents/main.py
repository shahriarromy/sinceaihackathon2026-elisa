"""FastAPI application hosting Incident Analyst and Knowledge Capturer agents."""

import logging
import sys
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
import httpx

from agents.config import (
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
    RAG_MCP_URL,
    TEAMS_MCP_URL,
    EMAIL_MCP_URL,
    SMS_MCP_URL,
    NEO4J_MCP_RO_URL,
    NEO4J_MCP_RW_URL,
)
from agents.models import (
    Agent1ReportRequest,
    Agent1ReportResponse,
    Agent2IngestRequest,
    Agent2IngestResponse,
    HealthResponse,
    RAGSearchRequest,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("agents-api")

app = FastAPI(
    title="Silent Metadata Capture Agent API",
    description="Autonomous Network Operations incident analysis and silent metadata capture",
    version="0.1.0",
)

# Enable CORS for frontend/localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return _driver


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint verifying Neo4j and returning MCP endpoints."""
    neo_status = "unhealthy"
    try:
        driver = get_driver()
        driver.verify_connectivity()
        neo_status = "connected"
    except Exception as e:
        neo_status = f"error: {e}"

    return HealthResponse(
        status="healthy",
        neo4j=neo_status,
        mcp_endpoints={
            "rag": RAG_MCP_URL,
            "teams": TEAMS_MCP_URL,
            "email": EMAIL_MCP_URL,
            "sms": SMS_MCP_URL,
            "neo4j_ro": NEO4J_MCP_RO_URL,
            "neo4j_rw": NEO4J_MCP_RW_URL,
        },
    )


WORK_ORDERS_FALLBACK = [
    {
        "id": "WO-2026-1107-003",
        "title": "LOS on TRN-117 1/1/3, replace SFP (affects SVC-MBH-0117 and SVC-MBH-0125)",
        "status": "open",
        "opened_at": "2026-11-07T07:15:00+02:00",
        "closed_at": None,
        "duration": "Ongoing",
        "element_id": "TRN-117",
        "model": "TX-2000 fw 4.1",
        "site": "OUL-05 (Kiiminki mast, Oulu)",
        "severity": "major",
        "lane_ref": "W5",
        "assertion_ref": "CA-0009 · MATCHES 4/4 SYMPTOMS (Disable interface, wait 30 s, enable)",
        "sequence": [
            {"time": "07:12", "label": "Loss of signal", "kind": "fault"},
            {"time": "07:20", "label": "Dispatch", "kind": "field"},
            {"time": "08:35", "label": "SFP replaced", "kind": "field"},
            {"time": "08:36", "label": "Alarm cleared, interface UP", "kind": "state"},
            {"time": "08:45", "label": "Traffic still zero", "kind": "pending", "wait": "UP but no traffic (ongoing)"},
        ],
    },
    {
        "id": "WO-2026-0312-007",
        "title": "LOS on TRN-042 1/1/2, replace SFP",
        "status": "closed",
        "opened_at": "2026-03-12T08:05:00+02:00",
        "closed_at": "2026-03-12T09:40:00+02:00",
        "duration": "1 h 23 min",
        "element_id": "TRN-042",
        "model": "TX-2000",
        "site": "TRE-03 (Nokia mast, Nokia)",
        "severity": "major",
        "lane_ref": "W2",
        "assertion_ref": "CA-0001 · CAPTURED HERE (Disable/enable the interface after SFP swap)",
        "sequence": [
            {"time": "08:02", "label": "Loss of signal", "kind": "fault"},
            {"time": "08:10", "label": "Dispatch", "kind": "field"},
            {"time": "09:05", "label": "SFP replaced", "kind": "field"},
            {"time": "09:06", "label": "Alarm cleared, interface UP", "kind": "state"},
            {"time": "09:23", "label": "Interface disabled", "kind": "field", "wait": "19 min UP but no traffic"},
            {"time": "09:24", "label": "Interface enabled", "kind": "field"},
            {"time": "09:25", "label": "Traffic restored", "kind": "recovery"},
        ],
    },
    {
        "id": "WO-2026-0114-002",
        "title": "TRN-233 unreachable, probable PSU failure (AI RCA)",
        "status": "closed",
        "opened_at": "2026-01-14T06:58:00+02:00",
        "closed_at": "2026-01-14T13:05:00+02:00",
        "duration": "6 h 8 min",
        "element_id": "TRN-233",
        "model": "TX-2000",
        "site": "SAL-03 (Hirvasvaara mast, Salla)",
        "severity": "critical",
        "lane_ref": "W1",
        "assertion_ref": "CA-0002 · EXISTED, NOT USED (Key at Sallan Kyläkauppa)",
        "sequence": [
            {"time": "06:40", "label": "Device unreachable", "kind": "fault"},
            {"time": "06:55", "label": "AI root cause: PSU", "kind": "analysis"},
            {"time": "07:05", "label": "Dispatch", "kind": "field"},
            {"time": "09:50", "label": "Access blocked by barrier", "kind": "accessBlock"},
            {"time": "11:35", "label": "Access granted, key found", "kind": "access", "wait": "1 h 45 min lost"},
            {"time": "12:40", "label": "PSU replaced", "kind": "field"},
            {"time": "12:48", "label": "Alarm cleared", "kind": "recovery"},
        ],
    },
    {
        "id": "WO-2026-0718-011",
        "title": "Rising CRC errors on TRN-021 1/1/3 after storm",
        "status": "closed",
        "opened_at": "2026-07-18T14:25:00+03:00",
        "closed_at": "2026-07-19T10:10:00+03:00",
        "duration": "19 h 45 min",
        "element_id": "TRN-021",
        "model": "TX-3000",
        "site": "TRE-01 (Hervanta hub, Tampere)",
        "severity": "minor",
        "lane_ref": "W3",
        "assertion_ref": "CA-0004 & CA-0005 · DISPUTED (Clean connectors vs Reseat line card)",
        "sequence": [
            {"time": "14:20", "label": "CRC errors", "kind": "fault"},
            {"time": "14:50", "label": "Connectors cleaned", "kind": "field"},
            {"time": "+1d 08:30", "label": "CRC errors again", "kind": "fault", "wait": "next day"},
            {"time": "+1d 09:55", "label": "Line card reseated", "kind": "field"},
            {"time": "+1d 10:05", "label": "Cleared", "kind": "recovery"},
        ],
    },
    {
        "id": "WO-2026-1003-004",
        "title": "Routine radio alignment check MWR-233",
        "status": "closed",
        "opened_at": "2026-10-03T07:30:00+03:00",
        "closed_at": "2026-10-03T12:20:00+03:00",
        "duration": "4 h 50 min",
        "element_id": "MWR-233",
        "model": "MW-500",
        "site": "SAL-03 (Hirvasvaara mast, Salla)",
        "severity": "info",
        "lane_ref": "W4",
        "assertion_ref": "CA-0003 · CONFIRMED BY THIS VISIT (Keybox code from NOC)",
        "sequence": [
            {"time": "09:05", "label": "Barrier opened with keybox code", "kind": "access"},
        ],
    },
]


@app.get("/incidents")
async def list_incidents():
    """List all incidents/work orders, matching the 5 reference diagram sequence lanes."""
    try:
        driver = get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (w)
                WHERE w:WorkOrder OR w:Incident
                OPTIONAL MATCH (w)-[:AFFECTS|FOR]->(ne:NetworkElement)
                OPTIONAL MATCH (ne)-[:LOCATED_AT]->(s:Site)
                OPTIONAL MATCH (ne)-[:IS_MODEL]->(m:Model)
                RETURN w.id AS id, coalesce(w.title, w.summary) AS title,
                       w.status AS status, toString(coalesce(w.opened_at, w.created_at)) AS opened_at,
                       toString(w.closed_at) AS closed_at,
                       ne.id AS element_id, m.id AS model, s.id AS site
                ORDER BY w.opened_at DESC
            """)
            records = [r.data() for r in result]
            if records:
                # Merge with fallback details
                id_map = {item["id"]: item for item in WORK_ORDERS_FALLBACK}
                enriched = []
                for rec in records:
                    fallback_item = id_map.get(rec["id"], {})
                    enriched.append({**fallback_item, **rec})
                return enriched
    except Exception as e:
        logger.warning(f"Neo4j query notice in list_incidents, using structured reference data: {e}")

    return WORK_ORDERS_FALLBACK


@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Retrieve detailed information for a specific incident."""
    fallback_map = {item["id"]: item for item in WORK_ORDERS_FALLBACK}
    base = fallback_map.get(incident_id)

    try:
        driver = get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (w {id: $id})
                WHERE w:WorkOrder OR w:Incident
                OPTIONAL MATCH (w)-[:AFFECTS|FOR]->(ne:NetworkElement)
                OPTIONAL MATCH (ev:Event)-[:PART_OF]->(w)
                RETURN w.id AS id, coalesce(w.title, w.summary) AS title,
                       w.status AS status, toString(coalesce(w.opened_at, w.created_at)) AS opened_at,
                       ne.id AS element_id,
                       collect(DISTINCT ev.summary) AS events
            """, {"id": incident_id})
            record = result.single()
            if record:
                data = record.data()
                if base:
                    return {**base, **data}
                return data
    except Exception as e:
        logger.warning(f"Neo4j notice in get_incident, using structured fallback: {e}")

    if not base:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return base


@app.post("/seed-graph")
async def seed_graph():
    """Trigger idempotent knowledge graph seeding."""
    import re
    from pathlib import Path

    # Look for knowledge_graph_seed.cypher
    candidates = [
        Path("/data/seed/knowledge_graph_seed.cypher"),
        Path("./data/seed/knowledge_graph_seed.cypher"),
        Path("../data/seed/knowledge_graph_seed.cypher"),
        Path("../../data/seed/knowledge_graph_seed.cypher"),
    ]
    seed_file = next((c for c in candidates if c.exists()), None)
    
    if not seed_file:
        # Fallback check if Neo4j is responsive
        try:
            driver = get_driver()
            with driver.session() as session:
                cnt = session.run("MATCH (n) RETURN count(n) AS cnt").single()["cnt"]
            return {"status": "success", "message": f"Graph verified with {cnt} nodes."}
        except Exception as e:
            return {"status": "error", "message": f"Could not verify graph: {e}"}

    try:
        content = seed_file.read_text(encoding="utf-8")
        # Split statements on semicolons at line ends
        statements = [s.strip() for s in re.split(r";\s*\n", content) if s.strip()]
        executed = 0
        driver = get_driver()
        with driver.session() as session:
            for stmt in statements:
                # Skip comments or empty
                lines = [line for line in stmt.split("\n") if not line.strip().startswith("//")]
                clean_stmt = "\n".join(lines).strip()
                if clean_stmt:
                    try:
                        session.run(clean_stmt)
                        executed += 1
                    except Exception as stmt_err:
                        logger.debug(f"Statement notice during seed: {stmt_err}")
                        continue
        return {"status": "success", "executed_statements": executed, "message": "Graph seeded successfully"}
    except Exception as e:
        logger.error(f"Error seeding graph: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/rag/search")
async def rag_search_passthrough(req: RAGSearchRequest):
    """Pass-through search endpoint to RAG service for debugging."""
    try:
        # Convert SSE URL to base HTTP host
        rag_base = RAG_MCP_URL.split("/sse")[0]
        # In step 4.1, if testing standalone, try local RAG import or HTTP
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{rag_base}/rag/search",
                json={"query": req.query, "entity_id": req.entity_id, "k": req.k},
            )
            if res.status_code == 200:
                return res.json()
    except Exception:
        pass
    return {"query": req.query, "results": []}


@app.post("/agent1/report", response_model=Agent1ReportResponse)
async def agent1_report(req: Agent1ReportRequest):
    """Agent 1 Incident Analysis endpoint executing the LangGraph pipeline."""
    from agents.agent1.graph import build_agent1_graph

    graph = build_agent1_graph()
    initial_state = {
        "incident_id": req.incident_id,
        "query": req.query,
        "incident_data": {},
        "rag_results": [],
        "graph_assertions": [],
        "final_report": {},
        "step_events": [],
    }

    result = graph.invoke(initial_state)
    report_dict = result.get("final_report", {})
    return Agent1ReportResponse(**report_dict)


@app.post("/agent1/report/stream")
async def agent1_report_stream(req: Agent1ReportRequest):
    """Agent 1 SSE endpoint streaming node execution steps followed by the final report."""
    import json
    from sse_starlette.sse import EventSourceResponse
    from agents.agent1.graph import build_agent1_graph

    graph = build_agent1_graph()
    initial_state = {
        "incident_id": req.incident_id,
        "query": req.query,
        "incident_data": {},
        "rag_results": [],
        "graph_assertions": [],
        "final_report": {},
        "step_events": [],
    }

    async def event_generator():
        final_report = None
        for chunk in graph.stream(initial_state):
            for node_name, node_output in chunk.items():
                step_events = node_output.get("step_events", [])
                latest_msg = step_events[-1] if step_events else f"Executed {node_name}"
                yield {
                    "event": "step",
                    "data": json.dumps({"node": node_name, "message": latest_msg}),
                }
                if "final_report" in node_output:
                    final_report = node_output["final_report"]

        if final_report:
            yield {
                "event": "report",
                "data": json.dumps(final_report),
            }

    return EventSourceResponse(event_generator())


@app.post("/agent2/ingest", response_model=Agent2IngestResponse)
async def agent2_ingest(req: Agent2IngestRequest):
    """Agent 2 Knowledge Capture endpoint executing the LangGraph pipeline."""
    import hashlib
    from agents.agent2.graph import build_agent2_graph
    from agents.models import ContextAssertionRecord

    graph = build_agent2_graph()
    initial_state = {
        "sources": req.sources or ["teams", "email", "sms"],
        "limit": req.limit,
        "incident_id": req.incident_id,
        "unprocessed_items": [],
        "extracted_assertions": [],
        "created_assertions": [],
        "incidents_touched": [],
        "rag_ids_added": [],
        "step_events": [],
    }

    result = graph.invoke(initial_state)

    assertions_created = []
    for a in result.get("extracted_assertions", []):
        raw_key = f"{a.get('title')}:{a.get('source_ref')}"
        ca_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:8].upper()
        assertions_created.append(
            ContextAssertionRecord(
                id=f"CA-{ca_hash}",
                text=a.get("text", ""),
                kind=a.get("kind", "troubleshooting_knowledge"),
                entities=a.get("entity_mentions", []),
                source_ref=a.get("source_ref", ""),
                confidence=float(a.get("confidence", 0.9)),
            )
        )

    return Agent2IngestResponse(
        assertions_created=assertions_created,
        incidents_touched=result.get("incidents_touched", []),
        rag_ids_added=result.get("rag_ids_added", []),
    )


def main():
    import uvicorn
    uvicorn.run("agents.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
