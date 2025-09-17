#!/usr/bin/env bash
set -euo pipefail

# Ensure python virtual environment exists
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

# Upgrade pip and install backend dependencies (including test extras)
pip install --upgrade pip
pip install -r requirements.txt || true  # legacy app deps if needed
pip install -e backend[test]

# Run database migrations (defaults to SQLite unless ISOFLICKER_DATABASE_URL is set)
alembic -c backend/alembic.ini upgrade head || true

# Install frontend dependencies
pushd frontend >/dev/null
npm install
popd >/dev/null

echo "Bootstrap complete. Activate the venv with 'source .venv/bin/activate'."
