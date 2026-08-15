#!/usr/bin/env bash
# =============================================================================
# run.sh — Bootstrap and start the Enterprise RAG Copilot stack
# =============================================================================
set -euo pipefail

echo "🚀  Starting Enterprise RAG Copilot..."

# ── 1. Copy .env if it doesn't exist ──────────────────────────────────────────
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    echo "✅  .env created from .env.example"
  else
    echo "⚠️   No .env.example found — skipping .env creation"
  fi
else
  echo "ℹ️   .env already exists — skipping"
fi

# ── 2. Ensure data directories exist ──────────────────────────────────────────
mkdir -p data/documents data/evaluation
echo "✅  data/documents and data/evaluation directories ensured"

# ── 3. Build & start all Docker services ──────────────────────────────────────
echo "🔨  Building and starting Docker services (this may take a few minutes)..."
docker compose up --build -d

# ── 4. Wait for backend to be healthy ─────────────────────────────────────────
echo "⏳  Waiting for backend to be ready..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅  Backend is healthy"
    break
  fi
  echo "   Attempt $i/30 — retrying in 5s..."
  sleep 5
done

# ── 5. Pull Ollama model ───────────────────────────────────────────────────────
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2}"
echo "📦  Pulling Ollama model: $OLLAMA_MODEL ..."
docker compose exec -T ollama ollama pull "$OLLAMA_MODEL" || \
  echo "⚠️   Could not pull model — you may need to pull it manually"

# ── 6. Seed the database (optional) ───────────────────────────────────────────
if [ -f scripts/seed_database.py ]; then
  echo "🌱  Seeding the database..."
  docker compose exec -T backend python scripts/seed_database.py || \
    echo "⚠️   Seeding failed or skipped — you can run it manually later"
fi

echo ""
echo "🎉  Stack is up!"
echo "   Frontend  → http://localhost:3000"
echo "   Backend   → http://localhost:8000"
echo "   API Docs  → http://localhost:8000/docs"
echo "   Health    → http://localhost:8000/health"

