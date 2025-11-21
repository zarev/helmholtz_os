# MCP Meetings App

An MCP (Model Context Protocol) server that provides tools to fetch meetings for the next week, extract participant information, and generate comprehensive profiles for each participant.

## Features

- **Get Next Week's Meetings**: Retrieve all meetings scheduled for the next 7 days
- **Extract Participants**: Get detailed information about meeting attendees
- **Generate Participant Profiles**: Create comprehensive JSON output with participant profiles including:
  - Name and contact information
  - Role and department
  - Meeting attendance status
  - Mini profile/bio for each person
  - List of meetings they're attending

## Installation

1. Install dependencies:
```bash
pip install mcp google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

2. (Optional) Set up Google Calendar API credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials
   - Download the credentials and save as `mcp_meetings/credentials.json`

   If you don't provide credentials, the app will use mock data for demonstration purposes.

## Usage

### Running the MCP Server

Run the server using:

```bash
python -m mcp_meetings.server
```

Or run it directly:

```bash
cd mcp_meetings
python server.py
```

### Available Tools

#### 1. `get_next_week_meetings`
Get all meetings scheduled for the next week.

**Parameters:**
- `calendar_id` (optional): Calendar ID to fetch from (default: "primary")

**Example Output:**
```json
{
  "total_meetings": 5,
  "meetings": [
    {
      "id": "meeting_001",
      "summary": "Team Standup",
      "start": {"dateTime": "2025-11-22T09:00:00"},
      "end": {"dateTime": "2025-11-22T09:30:00"},
      "location": "Conference Room A",
      "description": "Daily team standup meeting",
      "attendees": [...]
    }
  ]
}
```

#### 2. `get_meeting_participants`
Get detailed participant information for specific meetings.

**Parameters:**
- `meeting_ids` (required): Array of meeting IDs

**Example Output:**
```json
{
  "total_meetings": 1,
  "meetings": [
    {
      "meeting_id": "meeting_001",
      "participants": [
        {
          "email": "alice@example.com",
          "displayName": "Alice Johnson",
          "responseStatus": "accepted",
          "organizer": true,
          "optional": false
        }
      ]
    }
  ]
}
```

#### 3. `generate_participant_profiles`
Generate comprehensive JSON with participant profiles including mini bios.

**Parameters:**
- `calendar_id` (optional): Calendar ID (default: "primary")
- `include_mini_profile` (optional): Include mini profile for each participant (default: true)

**Example Output:**
```json
{
  "date_range": {
    "start": "2025-11-21T19:00:00",
    "end": "2025-11-28T19:00:00"
  },
  "total_meetings": 5,
  "total_participants": 8,
  "participants": [
    {
      "email": "alice@example.com",
      "name": "Alice Johnson",
      "initials": "AJ",
      "role": "Software Engineer",
      "department": "Engineering",
      "responseStatus": "accepted",
      "isOrganizer": true,
      "isOptional": false,
      "miniProfile": "Experienced Software Engineer with a passion for building scalable systems and mentoring team members.",
      "contactInfo": {
        "email": "alice@example.com",
        "hasProfilePicture": false
      },
      "meetings": [
        {
          "id": "meeting_001",
          "title": "Team Standup",
          "start": "2025-11-22T09:00:00",
          "end": "2025-11-22T09:30:00"
        }
      ]
    }
  ]
}
```

## MCP Client Configuration

To use this server with an MCP client (like Claude Desktop), add it to your MCP settings:

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

## Architecture

The MCP Meetings app consists of three main components:

1. **server.py**: Main MCP server that exposes tools and handles requests
2. **calendar_client.py**: Google Calendar API client for fetching meeting data
3. **participant_profiler.py**: Generates participant profiles with mini bios

## Mock Data

When Google Calendar credentials are not available, the app uses mock data for demonstration. The mock data includes:
- 5 sample meetings over the next week
- Various participants with different roles
- Realistic meeting times and locations

## Development

### Project Structure
```
mcp_meetings/
├── __init__.py
├── server.py                  # MCP server implementation
├── calendar_client.py         # Calendar API client
├── participant_profiler.py    # Profile generator
└── README.md                  # This file
```

### Testing

You can test the server by running it and using an MCP client to call the tools. The server will automatically fall back to mock data if credentials are not available.

## License

Part of the Helmholtz OS project.
