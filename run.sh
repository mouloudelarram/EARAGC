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

# ── 5. Ensure a usable local Ollama model is available ───────────────────────
OLLAMA_MODEL="${OLLAMA_MODEL:-$(grep -E '^OLLAMA_MODEL=' .env 2>/dev/null | cut -d= -f2- || true)}"
if [ -z "${OLLAMA_MODEL}" ]; then
  OLLAMA_MODEL="llama3.1:latest"
fi

if curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
  if curl -fsS "http://localhost:11434/api/tags" | grep -Fq "\"name\":\s*\"${OLLAMA_MODEL}\""; then
    echo "📦  Ollama model already available on localhost: $OLLAMA_MODEL"
  elif curl -fsS "http://localhost:11434/api/tags" | grep -Fq '"name": "llama3.1:latest"'; then
    OLLAMA_MODEL="llama3.1:latest"
    echo "📦  Falling back to localhost Ollama model: $OLLAMA_MODEL"
  else
    echo "⚠️   No usable local Ollama model was found on localhost:11434."
    echo "   You can install one manually with: docker compose exec ollama ollama pull llama3.1:latest"
    echo "   or: curl -sS http://localhost:11434/api/tags"
  fi
elif docker compose exec -T ollama sh -lc "ollama list 2>/dev/null | grep -Fq '$OLLAMA_MODEL'" >/dev/null 2>&1; then
  echo "📦  Ollama model already available in the compose container: $OLLAMA_MODEL"
elif docker compose exec -T ollama sh -lc "ollama list 2>/dev/null | grep -Fq 'llama3.1:latest'" >/dev/null 2>&1; then
  OLLAMA_MODEL="llama3.1:latest"
  echo "📦  Falling back to compose Ollama model: $OLLAMA_MODEL"
else
  echo "⚠️   No local Ollama model matched '$OLLAMA_MODEL' or 'llama3.1:latest'."
  echo "   You can install one manually with: docker compose exec ollama ollama pull llama3.1:latest"
fi

# ── 6. Seed the database (optional, host-side script) ───────────────────────
if [ -f scripts/seed_database.py ]; then
  echo "🌱  Seeding the database..."
  python3 scripts/seed_database.py || \
    echo "⚠️   Seeding failed or skipped — you can run it manually later"
else
  echo "ℹ️   Seed script not present on this host; skipping automatic seeding"
fi

echo ""
echo "🎉  Stack is up!"
echo "   Frontend  → http://localhost:3000"
echo "   Backend   → http://localhost:8000"
echo "   API Docs  → http://localhost:8000/docs"
echo "   Health    → http://localhost:8000/health"

