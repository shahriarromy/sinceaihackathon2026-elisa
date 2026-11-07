/**
 * API client for interacting with the Agents backend service.
 */

const BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api';

export interface HealthData {
  status: string;
  neo4j: string;
  mcp_endpoints: Record<string, string>;
}

export interface WorkOrderSequenceStep {
  time: string;
  label: string;
  kind: 'fault' | 'analysis' | 'field' | 'access' | 'accessBlock' | 'state' | 'recovery' | 'pending';
  wait?: string;
}

export interface IncidentRecord {
  id: string;
  title: string;
  status: 'open' | 'closed' | string;
  opened_at: string;
  closed_at: string | null;
  duration?: string;
  element_id: string;
  model?: string;
  site?: string;
  severity?: 'critical' | 'major' | 'minor' | 'info';
  lane_ref?: string;
  assertion_ref?: string;
  sequence?: WorkOrderSequenceStep[];
}

export interface KnownSolution {
  title: string;
  recommendation: string;
  source_ref: string;
  confidence: number;
  valid_from?: string | null;
  valid_to?: string | null;
}

export interface Agent1Report {
  summary: string;
  timeline: string[];
  symptoms: string[];
  problem_description: string;
  known_solution: KnownSolution | null;
  suggested_next_steps: string[];
  confidence: number;
  open_questions: string[];
}

export interface IngestResponse {
  assertions_created: string[];
  incidents_touched: string[];
  rag_ids_added: string[];
  message: string;
}

export async function getHealth(): Promise<HealthData> {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function getIncidents(): Promise<IncidentRecord[]> {
  const res = await fetch(`${BASE_URL}/incidents`);
  if (!res.ok) throw new Error(`Failed to load incidents: ${res.statusText}`);
  return res.json();
}

export async function getIncident(id: string): Promise<IncidentRecord> {
  const res = await fetch(`${BASE_URL}/incidents/${id}`);
  if (!res.ok) throw new Error(`Failed to load incident ${id}: ${res.statusText}`);
  return res.json();
}

export async function runAgent1Report(incidentId?: string, query?: string): Promise<Agent1Report> {
  const res = await fetch(`${BASE_URL}/agent1/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ incident_id: incidentId, query }),
  });
  if (!res.ok) throw new Error(`Agent 1 report failed: ${res.statusText}`);
  return res.json();
}

export async function triggerAgent2Ingest(
  sources: string[] = ['teams', 'email', 'sms'],
  incidentId?: string,
): Promise<IngestResponse> {
  const res = await fetch(`${BASE_URL}/agent2/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sources, incident_id: incidentId }),
  });
  if (!res.ok) throw new Error(`Knowledge collection failed: ${res.statusText}`);
  return res.json();
}

export async function triggerSeedGraph(): Promise<{ status: string; message?: string }> {
  const res = await fetch(`${BASE_URL}/seed-graph`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Seed graph failed: ${res.statusText}`);
  return res.json();
}
