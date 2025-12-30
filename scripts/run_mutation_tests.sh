#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Running mutation tests for broca/memory with coverage-aware runner..."
#
# NOTE: mutmut CLI options vary by version; this repo uses `setup.cfg` to configure:
# - paths_to_mutate
# - tests_dirs
# - runner (with coverage + branch coverage)
#
# So the most portable invocation is simply `mutmut run`.
mutmut run --max-children 1
echo "Mutation testing complete. Results:"
mutmut results
