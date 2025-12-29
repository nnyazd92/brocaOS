#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Running mutation tests for broca/memory with coverage-aware runner..."
mutmut run --paths-to-mutate broca/memory --tests-dir tests --runner "python -m pytest --maxfail=1 --disable-warnings --cov=broca --cov-branch"
echo "Mutation testing complete. Results:"
mutmut results
