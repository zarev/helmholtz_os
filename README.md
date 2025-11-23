# Helmholtz OS

This repository contains the Helmholtz OS project with multiple components.

## Components

### MCP Server

The MCP (Model Context Protocol) server is located in the `mcp/` directory. It provides a minimal server that exposes tools, resources, and prompts compatible with Claude Code, Gemini CLI, and ChatGPT MCP integrations.

#### Quick Start - Running the MCP Server

1. **Prerequisites**: Node.js 18+ (tested with Node 20+)

2. **Install dependencies**:
   ```bash
   cd mcp
   npm install
   ```

3. **Run tests** (optional):
   ```bash
   npm test
   ```

4. **Start the server**:
   ```bash
   npm start
   ```

   The server will output: `Helmholtz OS MCP server is ready on stdio.`

For detailed MCP server documentation, client configuration examples, and available tools, see [mcp/README.md](mcp/README.md).

### TOMO PoC

For information about the TOMO project (local menubar AI companion), see [README_TOMO.md](README_TOMO.md).

## Other Components

- `backend/` - FastAPI backend for the TOMO project
- `frontend/` - Frontend components
- `data/` - Data storage
- Various scraping and processing utilities
