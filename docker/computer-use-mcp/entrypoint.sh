#!/bin/sh
set -eu

GEMINI_DIR="${HOME:-/root}/.gemini"
SETTINGS_FILE="${GEMINI_DIR}/settings.json"

if [ ! -f "${SETTINGS_FILE}" ]; then
  mkdir -p "${GEMINI_DIR}"
  cat > "${SETTINGS_FILE}" <<'JSON'
{
  "mcpServers": {
    "computer-use": {
      "command": "npx",
      "args": ["-y", "computer-use-mcp"],
      "timeout": 600000,
      "trust": false
    }
  }
}
JSON
fi

exec computer-use-mcp
