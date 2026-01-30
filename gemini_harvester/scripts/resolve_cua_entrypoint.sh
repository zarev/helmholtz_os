#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d /opt/cua ]]; then
  echo "Expected /opt/cua to exist. Clone CUA into /opt/cua before running." >&2
  exit 1
fi

cd /opt/cua

if [[ ! -f .venv/bin/activate ]]; then
  echo "Expected /opt/cua/.venv to exist. Create the venv and install CUA before running." >&2
  exit 1
fi

# shellcheck disable=SC1091
. .venv/bin/activate

python -m cua.mcp.server --help || true
python -m cua.mcp --help || true
python -m cua --help || true

python -c "import cua, pkgutil; print([m.name for m in pkgutil.iter_modules(cua.__path__)])"
