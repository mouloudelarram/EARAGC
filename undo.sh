#!/usr/bin/env bash
# =============================================================================
# undo.sh — Tear down and clean up EVERYTHING created by run.sh
# =============================================================================
set -euo pipefail

echo "🧹  Undoing Enterprise RAG Copilot setup..."
echo ""

# ── Safety prompt ─────────────────────────────────────────────────────────────
read -r -p "⚠️   This will DELETE containers, volumes, images, and generated files. Continue? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

# ── 1. Stop and remove containers + networks ──────────────────────────────────
echo "🛑  Stopping and removing containers..."
docker compose down --remove-orphans || true

# ── 2. Remove Docker volumes (database data + Ollama models) ──────────────────
echo "🗑️   Removing Docker volumes (postgres_data, ollama_data)..."
docker volume rm earagc_postgres_data earagc_ollama_data 2>/dev/null || \
docker volume rm "$(basename "$PWD")_postgres_data" "$(basename "$PWD")_ollama_data" 2>/dev/null || \
  echo "   ℹ️   Volumes not found or already removed — skipping"

# ── 3. Remove Docker images built by this project ─────────────────────────────
echo "🗑️   Removing Docker images built for this project..."
docker rmi earagc-backend earagc-frontend 2>/dev/null || \
docker rmi "$(basename "$PWD")-backend" "$(basename "$PWD")-frontend" 2>/dev/null || \
  echo "   ℹ️   Images not found or already removed — skipping"

# ── 4. Remove dangling images left after build ────────────────────────────���───
echo "🗑️   Pruning dangling Docker images..."
docker image prune -f || true

# ── 5. Remove .env created by run.sh ──────────────────────────────────────────
if [ -f .env ]; then
  rm -f .env
  echo "🗑️   Removed .env"
else
  echo "   ℹ️   No .env file found — skipping"
fi

# ── 6. Remove generated evaluation results ────────────────────────────────────
if [ -f data/evaluation/results.json ]; then
  rm -f data/evaluation/results.json
  echo "🗑️   Removed data/evaluation/results.json"
fi

# ── 7. Remove uploaded / ingested documents ───────────────────────────────────
read -r -p "🗂️   Remove all files in data/documents/? [y/N] " confirm_docs
if [[ "$confirm_docs" =~ ^[Yy]$ ]]; then
  rm -rf data/documents/*
  echo "🗑️   Cleared data/documents/"
else
  echo "   ⏭️   Keeping data/documents/ — skipped"
fi

# ── 8. Remove __pycache__ and .pyc files created at runtime ───────────────────
echo "🗑️   Cleaning Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# ── 9. Remove node_modules (frontend — installed during Docker build) ──────────
read -r -p "📦  Remove frontend/node_modules/? [y/N] " confirm_nm
if [[ "$confirm_nm" =~ ^[Yy]$ ]]; then
  rm -rf frontend/node_modules
  echo "🗑️   Removed frontend/node_modules/"
else
  echo "   ⏭️   Keeping frontend/node_modules/ — skipped"
fi

echo ""
echo "✅  Cleanup complete. The workspace is back to its original state."
echo "   Run ./run.sh whenever you want to start fresh."

