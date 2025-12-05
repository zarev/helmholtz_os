\# MCP and Gemini CLI Contributor Guide



This document explains how to run the MCP (Model Context Protocol) example in this repository and how to connect it from Gemini CLI. It is aimed at new contributors who want to test MCP-based tools locally.



This guide focuses on how to use that example as a contributor.



---



\## 1. Prerequisites



\### 1.1. Repository and dependencies



Clone the repository and move into it:



git clone https://github.com/zarev/helmholtz\_os.git

cd helmholtz\_os



If you use a Python virtual environment, activate it here. The MCP example itself is a Node.js project, but other parts of the repo use Python.



\### 1.2. Node.js and npm



The MCP example lives under the mcp/ folder and is implemented in Node.js.



Check that Node.js and npm are available:



node -v

npm -v



Node.js 18+ is recommended.



\### 1.3. Gemini CLI



Check that Gemini CLI is installed and available:



gemini --version



\### 1.4. Gemini API key



For Gemini CLI, set the GEMINI\_API\_KEY environment variable.
The Gemini API Key is provided from the Institut.



macOS / Linux (bash/zsh):



export GEMINI\_API\_KEY="YOUR\_API\_KEY\_HERE"

echo "$GEMINI\_API\_KEY"



Windows (Command Prompt):



setx GEMINI\_API\_KEY "YOUR\_API\_KEY\_HERE"

REM open a new terminal after this

echo %GEMINI\_API\_KEY%



Windows (PowerShell):



\[System.Environment]::SetEnvironmentVariable("GEMINI\_API\_KEY","YOUR\_API\_KEY\_HERE","User")

$env:GEMINI\_API\_KEY



You should see a non-empty value when you echo it.



---



\## 2. Running the MCP example server



The minimal MCP example is described in mcp/README.md. In short, from the repository root:



cd mcp

npm install

npm test   # optional but recommended

npm start



If everything works, you should see logs indicating that the MCP server is running over stdio (JSON-RPC). Leave this terminal window open while you connect clients.



If npm start fails, double-check:



\- you are in the mcp/ directory

\- npm install completed successfully



---



\## 3. Connecting from Gemini CLI



Open a second terminal window, go to the repository root, and start Gemini CLI:



cd path/to/helmholtz\_os

gemini



Gemini CLI should pick up your GEMINI\_API\_KEY from the environment and allow you to chat normally.



Depending on your version and configuration of Gemini CLI, MCP integration may be:



\- configured via a CLI flag, or

\- configured via a local config file that registers the MCP server.



The general pattern is:



1\. The MCP server runs (for example, via npm start in mcp/).

2\. Gemini CLI is configured to connect to that server over stdio.

3\. Tools/resources exposed by the MCP server become available inside Gemini CLI.



Once configured, you should see MCP-related tools listed or be able to call them according to the Gemini CLI documentation.



---



\## 4. What you should see



From the minimal MCP example (PR #25), the server exposes:



\- one or more sample tools

\- a sample resource (e.g. server info)

\- a sample prompt



When Gemini CLI is correctly connected:



\- the MCP server terminal shows incoming requests

\- the tools/resources appear in Gemini CLI

\- calling a tool returns a structured result coming from the MCP server



If you do not see any tools:



\- make sure the MCP server is still running

\- confirm the MCP configuration in Gemini CLI points to the correct command

\- check for errors in the MCP server terminal



---



\## 5. Troubleshooting tips



\- Node or npm not found: install Node.js, add it to your PATH, then reopen your terminal.

\- Gemini CLI not found: reinstall Gemini CLI and confirm "gemini --version" works.

\- GEMINI\_API\_KEY not set: re-set the variable, open a new terminal, then check with echo.

\- MCP server crashes on start: run "npm test" in mcp/ first and inspect any error messages.

\- No MCP tools visible in Gemini CLI: double-check the MCP configuration in Gemini CLI and verify the MCP server terminal shows connections.



---



\## 6. How this fits into Helmholtz OS / Moxy



This MCP example is a small building block for the larger Helmholtz OS / “Moxy” lab operator:



\- It shows how tools, resources, and prompts can be exposed via MCP.

\- It provides a concrete way to connect external services and LLMs (Gemini CLI in this case).

\- Future agents (meeting tools, browsing agents, publication harvesters, etc.) can follow the same integration pattern, using MCP to talk to LLM clients.



This document is intended as a contributor-level guide: once you can run this MCP example and connect it from Gemini CLI, you have a working baseline for experimenting with more advanced MCP-based agents in this repository.



