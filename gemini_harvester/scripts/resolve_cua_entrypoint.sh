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

python -m mcp_server --help 2>&1 | head -5 || true
python -m cua.mcp.server --help 2>&1 | head -5 || true
python -m cua.mcp --help 2>&1 | head -5 || true
python -m cua --help 2>&1 | head -5 || true

echo ""
echo "Available CUA submodules:"
python -c "import cua_mcp_server, pkgutil; print([m.name for m in pkgutil.iter_modules(cua_mcp_server.__path__)])" 2>/dev/null || echo "Could not list cua_mcp_server submodules"
