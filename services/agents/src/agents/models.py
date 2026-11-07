"""Pydantic models for agents service requests and responses."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "healthy"
    neo4j: str
    mcp_endpoints: Dict[str, str]


class Agent1ReportRequest(BaseModel):
    incident_id: Optional[str] = Field(None, description="Incident or WorkOrder ID, e.g. WO-2026-0312-007")
    query: Optional[str] = Field(None, description="Free-text incident description or symptoms")


class KnownSolution(BaseModel):
    title: str
    recommendation: str
    source_ref: str
    confidence: float
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None


class Agent1ReportResponse(BaseModel):
    summary: str
    timeline: List[str] = Field(default_factory=list)
    symptoms: List[str] = Field(default_factory=list)
    problem_description: str
    known_solution: Optional[KnownSolution] = None
    suggested_next_steps: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    open_questions: List[str] = Field(default_factory=list)


class Agent2IngestRequest(BaseModel):
    sources: Optional[List[str]] = Field(default=["teams", "email", "sms"], description="Channels to ingest")
    limit: Optional[int] = Field(None, description="Max items per channel")
    incident_id: Optional[str] = Field(None, description="Target incident ID to associate with captured knowledge")


class ContextAssertionRecord(BaseModel):
    id: str
    text: str
    kind: str
    entities: List[str] = Field(default_factory=list)
    source_ref: str
    confidence: float


class Agent2IngestResponse(BaseModel):
    assertions_created: List[ContextAssertionRecord] = Field(default_factory=list)
    incidents_touched: List[str] = Field(default_factory=list)
    rag_ids_added: List[str] = Field(default_factory=list)


class RAGSearchRequest(BaseModel):
    query: str
    entity_id: Optional[str] = None
    k: int = 5
