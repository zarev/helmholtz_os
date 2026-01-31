# CUA MCP setup for Gemini CLI

This repository uses Gemini CLI for automation (see `gemini_harvester/`). The included Dockerfile installs repo dependencies and CUA in the same image, and `docker-compose.yml` runs that image for both the FastAPI app and Gemini CLI.

## 1) Build the container image

The repository includes a Dockerfile that installs Python dependencies, Gemini CLI, the CUA repo in `/opt/cua`, and configures the app runtime. Build it with docker-compose:

```bash
docker-compose build
```

The compose file already defines an `app` service for the FastAPI backend and a `gemini` service for Gemini CLI. Keep the `db` service as-is, and adjust only if your environment needs different paths or credentials.

## 2) Resolve the CUA MCP entrypoint in the container

Once the image is built and running, resolve the MCP entrypoint. You can use the helper script in this repo:

```bash
docker-compose run --rm gemini ./scripts/resolve_cua_entrypoint.sh
```

The script tries the common modules and then prints the available CUA submodules. Use the first module that responds to `--help` as the MCP entrypoint.

## 3) Configure Gemini CLI MCP settings

Gemini CLI reads MCP server config from a settings file. This repository already includes a project-level settings file under `gemini_harvester/.gemini/settings.json`. Update the `args` module if your resolved entrypoint differs.

```json
{
  "mcpServers": {
    "cua": {
      "command": "/opt/cua/.venv/bin/python",
      "args": ["-m", "cua.mcp.server"],
      "cwd": "/opt/cua",
      "timeout": 600000,
      "trust": false
    }
  }
}
```

## 4) Verify in Gemini CLI

Inside the container:

1. Start Gemini CLI: `gemini`.
2. Run the MCP status command in Gemini CLI.
3. Ask: “List the tools available from the MCP server named cua.”

If tools appear, the wiring is correct.

## 5) Operational guidance

- Treat CUA MCP as a privileged local capability inside the container.
- Keep `trust: false` until you are confident in your safety boundaries.
- Log tool invocations at the Gemini CLI layer if you need traceability.
