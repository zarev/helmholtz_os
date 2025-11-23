# Helmholtz OS MCP server

This folder contains a minimal [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/specification) server that exposes a handful of sample tools, a resource, and a prompt over **stdio**. The same binary can be wired into Claude Code, Gemini CLI, or ChatGPT MCP integrations.

## Prerequisites

- Node.js 18+ (tested with Node 22)
- npm

## Install

```bash
cd mcp
npm install
```

## Run the server

```bash
npm start
```

The server speaks JSON-RPC/MCP over stdio, so it does not print banners to stdout. Status and errors are written to stderr.

### Available MCP primitives

- **Tools**
  - `say_hello` — returns `"Hello, <name>! ✨"`
  - `echo_markdown` — echoes input wrapped in a Markdown code block
- **Resource**
  - `server-info` at `memory:helmholtz-mcp/info` — short text describing the server
- **Prompt**
  - `hello_prompt` — returns a single user message asking the model to greet someone in an optional tone

## Client configuration examples

Point each client at the same server command (`node server.js` or the absolute path). All examples assume the repo is cloned locally and the working directory is `mcp/`.

### Claude Code (Claude Desktop)

Add or edit `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "helmholtz-os": {
      "command": "node",
      "args": ["/absolute/path/to/helmholtz_os/mcp/server.js"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

Restart Claude Desktop; the MCP tools should appear under integrations.

### Gemini CLI

Update your Gemini CLI profile (for example, `~/.config/gemini/config.json`):

```json
{
  "mcpServers": {
    "helmholtz-os": {
      "transport": "stdio",
      "command": "node",
      "args": ["/absolute/path/to/helmholtz_os/mcp/server.js"]
    }
  }
}
```

Then start Gemini CLI with that profile; the MCP tools will be available in the session.

### ChatGPT (Desktop / Web with MCP enabled)

In Settings → Developer → MCP, add a new MCP server:

- **Name:** `helmholtz-os`
- **Command:** `node`
- **Arguments:** `/absolute/path/to/helmholtz_os/mcp/server.js`
- **Transport:** stdio (default)

Once saved, ChatGPT should list the MCP tools alongside its built-in tools.

## Tips for compatibility

- Keep logs on **stderr** only; stdout is reserved for JSON-RPC traffic.
- Ensure every tool has a JSON Schema (the `zod` schemas are converted automatically by the SDK).
- If you change tools/resources/prompts at runtime, call the appropriate `send*ListChanged` method on `server.server` to notify clients.
