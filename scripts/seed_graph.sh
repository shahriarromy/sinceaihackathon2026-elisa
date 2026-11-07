#!/usr/bin/env bash
set -euo pipefail

# Load environment variables if .env exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${ROOT_DIR}/.env" ]; then
    set -a
    source "${ROOT_DIR}/.env"
    set +a
fi

NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-hackathon_secret_password}"
NEO4J_HOST="${NEO4J_HOST:-localhost}"
NEO4J_PORT="${NEO4J_PORT:-7687}"
SEED_FILE="${1:-${ROOT_DIR}/data/seed/knowledge_graph_seed.cypher}"

if [ ! -f "$SEED_FILE" ]; then
    echo "Error: Seed file not found at $SEED_FILE"
    exit 1
fi

echo "=========================================================="
echo "Seeding Neo4j knowledge graph using: $SEED_FILE"
echo "=========================================================="

if command -v cypher-shell >/dev/null 2>&1; then
    echo "Using host cypher-shell..."
    cypher-shell -a "bolt://${NEO4J_HOST}:${NEO4J_PORT}" -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" < "$SEED_FILE"
elif command -v docker >/dev/null 2>&1; then
    echo "Using cypher-shell inside Docker container 'ops-neo4j'..."
    docker compose -f "${ROOT_DIR}/docker-compose.yml" exec -T neo4j cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" < "$SEED_FILE"
else
    echo "Error: Neither cypher-shell nor docker could be used to load seed data."
    exit 1
fi

echo "=========================================================="
echo "Neo4j seed completed successfully!"
echo "=========================================================="
