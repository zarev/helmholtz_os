"""MCP Server for Meeting and Participant Information.

This server provides tools to:
1. Get meetings for the next week
2. Extract participant information from meetings
3. Generate JSON with participant profiles
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .calendar_client import CalendarClient
from .participant_profiler import ParticipantProfiler


# Initialize the MCP server
app = Server("mcp-meetings")

# Initialize clients
calendar_client = None
participant_profiler = None


def initialize_clients():
    """Initialize calendar and profiler clients."""
    global calendar_client, participant_profiler
    
    # Initialize calendar client
    calendar_client = CalendarClient()
    
    # Initialize participant profiler
    participant_profiler = ParticipantProfiler()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_next_week_meetings",
            description="Get all meetings scheduled for the next week",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID to fetch meetings from (default: 'primary')",
                        "default": "primary"
                    }
                }
            }
        ),
        Tool(
            name="get_meeting_participants",
            description="Get detailed participant information for specific meetings",
            inputSchema={
                "type": "object",
                "properties": {
                    "meeting_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of meeting IDs to get participants for"
                    }
                },
                "required": ["meeting_ids"]
            }
        ),
        Tool(
            name="generate_participant_profiles",
            description="Generate comprehensive JSON with participant profiles including mini bios",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID to fetch meetings from (default: 'primary')",
                        "default": "primary"
                    },
                    "include_mini_profile": {
                        "type": "boolean",
                        "description": "Include mini profile for each participant",
                        "default": True
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "get_next_week_meetings":
        calendar_id = arguments.get("calendar_id", "primary")
        meetings = await calendar_client.get_next_week_meetings(calendar_id)
        
        result = {
            "total_meetings": len(meetings),
            "meetings": meetings
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
    
    elif name == "get_meeting_participants":
        meeting_ids = arguments.get("meeting_ids", [])
        
        participants_data = []
        for meeting_id in meeting_ids:
            participants = await calendar_client.get_meeting_participants(meeting_id)
            participants_data.append({
                "meeting_id": meeting_id,
                "participants": participants
            })
        
        result = {
            "total_meetings": len(participants_data),
            "meetings": participants_data
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
    
    elif name == "generate_participant_profiles":
        calendar_id = arguments.get("calendar_id", "primary")
        include_mini_profile = arguments.get("include_mini_profile", True)
        
        # Get all meetings for next week
        meetings = await calendar_client.get_next_week_meetings(calendar_id)
        
        # Collect all unique participants across meetings
        all_participants = {}
        
        for meeting in meetings:
            meeting_id = meeting.get("id")
            meeting_title = meeting.get("summary", "Untitled")
            
            # Get participants for this meeting
            participants = await calendar_client.get_meeting_participants(meeting_id)
            
            for participant in participants:
                email = participant.get("email")
                if email and email not in all_participants:
                    # Generate profile for this participant
                    profile = await participant_profiler.generate_profile(
                        participant,
                        include_mini_profile=include_mini_profile
                    )
                    all_participants[email] = profile
                
                # Track which meetings this participant is in
                if email in all_participants:
                    if "meetings" not in all_participants[email]:
                        all_participants[email]["meetings"] = []
                    all_participants[email]["meetings"].append({
                        "id": meeting_id,
                        "title": meeting_title,
                        "start": meeting.get("start", {}).get("dateTime", ""),
                        "end": meeting.get("end", {}).get("dateTime", "")
                    })
        
        result = {
            "date_range": {
                "start": datetime.now().isoformat(),
                "end": (datetime.now() + timedelta(days=7)).isoformat()
            },
            "total_meetings": len(meetings),
            "total_participants": len(all_participants),
            "participants": list(all_participants.values())
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server."""
    # Initialize clients
    initialize_clients()
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
