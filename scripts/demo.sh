#!/usr/bin/env bash
set -euo pipefail

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
AGENTS_URL="${AGENTS_URL:-http://localhost:8000}"

echo -e "${BLUE}========================================================================${NC}"
echo -e "${BOLD}${BLUE}   Since AI Hackathon 2026 - Silent Metadata Capture Acceptance Demo   ${NC}"
echo -e "${BLUE}========================================================================${NC}"

format_json() {
    if command -v jq >/dev/null 2>&1; then
        jq "$@"
    else
        python3 -m json.tool
    fi
}

# Check if running in local unit test mode
if [[ "${1:-}" == "--local" ]]; then
    echo -e "${YELLOW}Running acceptance test in standalone local mode (without Docker)...${NC}"
    cd "${ROOT_DIR}/services/agents"
    uv run python test_end_to_end_cycle.py
    uv run python test_sal03_access.py
    echo -e "${GREEN}✓ Local acceptance cycle verified successfully!${NC}"
    exit 0
fi

# Step 0: Check service availability
echo -e "\n${BOLD}[Stage 0] Verifying Agents REST API health at ${AGENTS_URL}...${NC}"
HEALTH_STATUS=0
for i in {1..10}; do
    if curl -s -f "${AGENTS_URL}/health" >/dev/null 2>&1; then
        HEALTH_STATUS=1
        break
    fi
    echo "Waiting for ${AGENTS_URL}/health (attempt $i/10)..."
    sleep 2
done

if [ $HEALTH_STATUS -eq 0 ]; then
    echo -e "${RED}Error: Cannot connect to Agents API at ${AGENTS_URL}${NC}"
    echo -e "Make sure the containers are started:\n  ${YELLOW}docker compose up -d${NC}"
    echo -e "Or run in local mode:\n  ${YELLOW}./scripts/demo.sh --local${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Agents service is healthy!${NC}"
curl -s "${AGENTS_URL}/health" | format_json .

# Step 1: Initial query for TRN-042 incident before knowledge capture
echo -e "\n${BOLD}${BLUE}========================================================================${NC}"
echo -e "${BOLD}[Stage 1] Querying Agent 1 for TRN-042 incident BEFORE knowledge ingestion...${NC}"
echo -e "${YELLOW}Expected outcome: No known solution found; suggested steps note missing workaround.${NC}"
echo -e "${BLUE}========================================================================${NC}"

BEFORE_REPORT=$(curl -s -X POST "${AGENTS_URL}/agent1/report" \
    -H "Content-Type: application/json" \
    -d '{"incident_id": "WO-2026-0312-007", "query": "LOS on TRN-042 1/1/2, replace SFP"}')

echo "$BEFORE_REPORT" | format_json '{summary: .summary, known_solution: .known_solution, suggested_next_steps: .suggested_next_steps, confidence: .confidence}'

# Step 2: Trigger Agent 2 to capture silent metadata from Teams, Email, SMS
echo -e "\n${BOLD}${BLUE}========================================================================${NC}"
echo -e "${BOLD}[Stage 2] Triggering Agent 2 Knowledge Capturer (POST /agent2/ingest)...${NC}"
echo -e "${YELLOW}Expected outcome: Captures Teams & Email conversations, writes assertions & RAG.${NC}"
echo -e "${BLUE}========================================================================${NC}"

INGEST_RES=$(curl -s -X POST "${AGENTS_URL}/agent2/ingest" \
    -H "Content-Type: application/json" \
    -d '{"sources": ["teams", "email", "sms"]}')

echo "$INGEST_RES" | format_json .

# Step 3: Query Agent 1 again for TRN-042 incident
echo -e "\n${BOLD}${BLUE}========================================================================${NC}"
echo -e "${BOLD}[Stage 3] Querying Agent 1 for TRN-042 incident AFTER knowledge ingestion...${NC}"
echo -e "${YELLOW}Expected outcome: Workaround proposed: disable/re-enable interface before hardware swap.${NC}"
echo -e "${BLUE}========================================================================${NC}"

AFTER_REPORT=$(curl -s -X POST "${AGENTS_URL}/agent1/report" \
    -H "Content-Type: application/json" \
    -d '{"incident_id": "WO-2026-0312-007", "query": "LOS on TRN-042 1/1/2, replace SFP"}')

echo "$AFTER_REPORT" | format_json '{summary: .summary, known_solution: .known_solution, suggested_next_steps: .suggested_next_steps, confidence: .confidence}'

# Step 4: Test locked-barrier access scenario
echo -e "\n${BOLD}${BLUE}========================================================================${NC}"
echo -e "${BOLD}[Stage 4] Querying Agent 1 for SAL-03 locked-barrier incident...${NC}"
echo -e "${YELLOW}Expected outcome: Proposes active NOC keybox code (superseding village shop key).${NC}"
echo -e "${BLUE}========================================================================${NC}"

BARRIER_REPORT=$(curl -s -X POST "${AGENTS_URL}/agent1/report" \
    -H "Content-Type: application/json" \
    -d '{"incident_id": "WO-2026-0114-002", "query": "Locked barrier on Hirvasvaarantie access road"}')

echo "$BARRIER_REPORT" | format_json '{summary: .summary, known_solution: .known_solution, suggested_next_steps: .suggested_next_steps, confidence: .confidence}'

echo -e "\n${GREEN}========================================================================${NC}"
echo -e "${BOLD}${GREEN} Acceptance Demo Completed Successfully! ${NC}"
echo -e "${GREEN}========================================================================${NC}"
