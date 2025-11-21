# MCP Meetings App - Quickstart Guide

Get up and running with the MCP Meetings app in 5 minutes!

## What is this?

The MCP Meetings app is a Model Context Protocol (MCP) server that:
- 📅 Fetches your meetings for the next week
- 👥 Identifies all participants across your meetings
- 📝 Generates comprehensive profiles for each participant including mini bios
- 📊 Outputs structured JSON data

## Installation

```bash
# Install dependencies
pip install mcp google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Or install from the repository root
cd /path/to/helmholtz_os
pip install -r requirements.txt
```

## Quick Test

Run the test script to see it in action (uses mock data):

```bash
cd /path/to/helmholtz_os
python test_mcp_meetings.py
```

This will:
1. Fetch 5 sample meetings for the next week
2. Extract 8 unique participants
3. Generate profiles with mini bios
4. Save output to `/tmp/meeting_participants_output.json`

## Usage with MCP Client

### Option 1: Run as standalone server

```bash
python -m mcp_meetings.server
```

The server will start and listen for MCP protocol messages via stdio.

### Option 2: Configure with Claude Desktop (or other MCP client)

1. Add to your MCP client configuration (e.g., `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "meetings": {
      "command": "python",
      "args": ["-m", "mcp_meetings.server"],
      "cwd": "/path/to/helmholtz_os"
    }
  }
}
```

2. Restart your MCP client

3. You can now use the tools:
   - `get_next_week_meetings` - Get all meetings
   - `get_meeting_participants` - Get participants for specific meetings  
   - `generate_participant_profiles` - Get comprehensive participant data

## Available Tools

### 1. get_next_week_meetings

Get all meetings scheduled for the next 7 days.

**Example call:**
```
Tool: get_next_week_meetings
Parameters: { "calendar_id": "primary" }
```

### 2. get_meeting_participants

Get participant details for specific meeting IDs.

**Example call:**
```
Tool: get_meeting_participants
Parameters: { "meeting_ids": ["meeting_001", "meeting_002"] }
```

### 3. generate_participant_profiles

Generate comprehensive participant profiles with mini bios.

**Example call:**
```
Tool: generate_participant_profiles
Parameters: { 
  "calendar_id": "primary",
  "include_mini_profile": true
}
```

## Google Calendar Integration (Optional)

To connect to your actual Google Calendar:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Download credentials as `mcp_meetings/credentials.json`
5. Run the server - it will prompt for authorization on first use

**Without credentials**, the app uses realistic mock data for demonstration.

## Output Format

The `generate_participant_profiles` tool returns JSON like:

```json
{
  "total_meetings": 5,
  "total_participants": 8,
  "participants": [
    {
      "email": "alice@example.com",
      "name": "Alice Johnson",
      "role": "Software Engineer",
      "department": "Engineering",
      "miniProfile": "Experienced Software Engineer with a passion...",
      "meetings": [
        {
          "id": "meeting_001",
          "title": "Team Standup",
          "start": "2025-11-22T09:00:00"
        }
      ]
    }
  ]
}
```

## View Examples

Run the examples script to see common usage patterns:

```bash
python mcp_meetings/examples.py
```

## Troubleshooting

### "Module not found: mcp"
```bash
pip install mcp
```

### "No credentials.json found"
This is normal! The app will use mock data. To use real calendar data, follow the Google Calendar Integration steps above.

### Server not responding
Make sure you're running the server with stdio transport, not HTTP. The MCP protocol uses stdin/stdout for communication.

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [examples.py](examples.py) for usage patterns
- Configure Google Calendar integration for real data
- Customize participant profiles in `participant_profiler.py`

## Support

For issues or questions, check the main Helmholtz OS repository.
