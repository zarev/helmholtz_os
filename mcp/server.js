#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

export const sayHelloTool = async ({ name }) => ({
  content: [
    {
      type: "text",
      text: `Hello, ${name}! \u2728`,
    },
  ],
});

export const echoMarkdownTool = async ({ text }) => ({
  content: [
    {
      type: "text",
      text: `You said:\n\n\`\`\`\n${text}\n\`\`\``,
    },
  ],
});

export const serverInfoResource = async () => ({
  contents: [
    {
      uri: "memory:helmholtz-mcp/info",
      mimeType: "text/plain",
      text:
        "This MCP server exposes two sample tools (say_hello, echo_markdown) and a sample prompt (hello_prompt).",
    },
  ],
});

export const helloPrompt = async ({ name, tone }) => ({
  messages: [
    {
      role: "user",
      content: {
        type: "text",
        text: `Write a ${tone ?? "friendly"} greeting for ${name}. Keep it short.`,
      },
    },
  ],
});

export function createServer() {
  const server = new McpServer({
    name: "helmholtz-os-mcp-server",
    version: "0.1.0",
  });

  server.registerTool(
    "say_hello",
    {
      description: "Return a friendly greeting for the provided name.",
      inputSchema: {
        name: z.string().describe("Name to greet"),
      },
    },
    sayHelloTool
  );

  server.registerTool(
    "echo_markdown",
    {
      description: "Echo text back wrapped in a Markdown code block.",
      inputSchema: {
        text: z.string().describe("Text to echo"),
      },
    },
    echoMarkdownTool
  );

  server.registerResource(
    "server-info",
    "memory:helmholtz-mcp/info",
    {
      title: "MCP server description",
      description: "Static information about the Helmholtz OS MCP server.",
    },
    serverInfoResource
  );

  server.registerPrompt(
    "hello_prompt",
    {
      title: "Generate a greeting",
      description: "Construct a polite greeting message for the provided name.",
      argsSchema: {
        name: z.string().describe("Name to greet"),
        tone: z
          .string()
          .optional()
          .describe("Optional tone to use, e.g., friendly or formal"),
      },
    },
    helloPrompt
  );

  return server;
}

async function main() {
  const server = createServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Helmholtz OS MCP server is ready on stdio.");
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error("Failed to start MCP server:", error);
    process.exit(1);
  });
}
