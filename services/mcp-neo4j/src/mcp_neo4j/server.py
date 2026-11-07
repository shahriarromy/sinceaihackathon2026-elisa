"""FastMCP Neo4j service providing streamable HTTP/SSE transport."""

import logging
import os
import sys
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from neo4j import GraphDatabase, Driver
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import JSONResponse

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("mcp-neo4j")

# Read environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "hackathon_secret_password")
READ_ONLY = os.getenv("READ_ONLY", "false").lower() in ("true", "1", "yes")

server_name = "neo4j-ro" if READ_ONLY else "neo4j-rw"
mcp = FastMCP(server_name)

_driver: Optional[Driver] = None


def get_driver() -> Driver:
    """Return active Neo4j driver instance, initializing if needed."""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return _driver


# Pydantic models for structured I/O
class CypherQueryResult(BaseModel):
    records: List[Dict[str, Any]] = Field(default_factory=list, description="Rows returned by query")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Execution summary")


class SchemaResult(BaseModel):
    labels: List[str] = Field(default_factory=list, description="Node labels present in database")
    relationship_types: List[str] = Field(default_factory=list, description="Relationship types")
    property_keys: List[str] = Field(default_factory=list, description="Known property keys")


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Healthcheck endpoint verifying Neo4j connectivity."""
    try:
        driver = get_driver()
        driver.verify_connectivity()
        return JSONResponse({
            "status": "healthy",
            "service": server_name,
            "read_only": READ_ONLY,
            "neo4j_uri": NEO4J_URI,
        })
    except Exception as e:
        logger.error(f"Healthcheck failed: {e}")
        return JSONResponse(
            {
                "status": "unhealthy",
                "service": server_name,
                "error": str(e),
            },
            status_code=503,
        )


@mcp.tool(name="get_schema", description="Inspect Neo4j database schema, node labels and relationships")
def get_schema() -> Dict[str, Any]:
    """Retrieve node labels, relationship types, and property keys from Neo4j."""
    driver = get_driver()
    with driver.session() as session:
        labels_res = session.run("CALL db.labels()")
        labels = [r[0] for r in labels_res]

        rel_res = session.run("CALL db.relationshipTypes()")
        rels = [r[0] for r in rel_res]

        prop_res = session.run("CALL db.propertyKeys()")
        props = [r[0] for r in prop_res]

        return SchemaResult(labels=labels, relationship_types=rels, property_keys=props).model_dump()


@mcp.tool(name="read_cypher", description="Execute a read-only Cypher query against the knowledge graph")
def read_cypher(query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute a Cypher query with read transaction semantics."""
    parameters = params or {}
    # Safety check for write keywords in read-only mode
    if READ_ONLY:
        upper = query.upper()
        write_keywords = ["CREATE ", "MERGE ", "DELETE ", "SET ", "DROP ", "REMOVE "]
        if any(kw in upper for kw in write_keywords):
            raise ValueError(f"Write operations are forbidden on {server_name}")

    driver = get_driver()
    with driver.session() as session:
        result = session.run(query, parameters)
        records = [r.data() for r in result]
        return CypherQueryResult(records=records).model_dump()


if not READ_ONLY:
    @mcp.tool(name="write_cypher", description="Execute a write Cypher query to modify or insert into the knowledge graph")
    def write_cypher(query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a Cypher write query."""
        parameters = params or {}
        driver = get_driver()
        with driver.session() as session:
            result = session.run(query, parameters)
            records = [r.data() for r in result]
            summary = result.consume()
            counters = summary.counters
            summary_dict = {
                "nodes_created": counters.nodes_created,
                "nodes_deleted": counters.nodes_deleted,
                "relationships_created": counters.relationships_created,
                "relationships_deleted": counters.relationships_deleted,
                "properties_set": counters.properties_set,
            }
            return CypherQueryResult(records=records, summary=summary_dict).model_dump()


def main():
    logger.info(f"Starting {server_name} on 0.0.0.0:8000 (read_only={READ_ONLY})")
    mcp.run(transport="sse", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
