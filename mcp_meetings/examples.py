"""Example usage of the MCP Meetings server.

This script demonstrates how to interact with the MCP server programmatically.
"""

import asyncio
import json


async def example_get_meetings():
    """Example: Get next week's meetings."""
    print("\n=== Example 1: Get Next Week's Meetings ===\n")
    
    # In a real MCP client, you would call the tool like this:
    tool_name = "get_next_week_meetings"
    arguments = {
        "calendar_id": "primary"
    }
    
    print(f"Tool: {tool_name}")
    print(f"Arguments: {json.dumps(arguments, indent=2)}")
    print("\nThis would return:")
    print("""
{
  "total_meetings": 5,
  "meetings": [
    {
      "id": "meeting_001",
      "summary": "Team Standup",
      "start": {"dateTime": "2025-11-22T09:00:00"},
      "end": {"dateTime": "2025-11-22T09:30:00"},
      "location": "Conference Room A",
      "attendees": [...]
    },
    ...
  ]
}
    """)


async def example_get_participants():
    """Example: Get participants for specific meetings."""
    print("\n=== Example 2: Get Meeting Participants ===\n")
    
    tool_name = "get_meeting_participants"
    arguments = {
        "meeting_ids": ["meeting_001", "meeting_002"]
    }
    
    print(f"Tool: {tool_name}")
    print(f"Arguments: {json.dumps(arguments, indent=2)}")
    print("\nThis would return:")
    print("""
{
  "total_meetings": 2,
  "meetings": [
    {
      "meeting_id": "meeting_001",
      "participants": [
        {
          "email": "alice@example.com",
          "displayName": "Alice Johnson",
          "responseStatus": "accepted",
          "organizer": true
        },
        ...
      ]
    },
    ...
  ]
}
    """)


async def example_generate_profiles():
    """Example: Generate comprehensive participant profiles."""
    print("\n=== Example 3: Generate Participant Profiles ===\n")
    
    tool_name = "generate_participant_profiles"
    arguments = {
        "calendar_id": "primary",
        "include_mini_profile": True
    }
    
    print(f"Tool: {tool_name}")
    print(f"Arguments: {json.dumps(arguments, indent=2)}")
    print("\nThis would return:")
    print("""
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
      "miniProfile": "Experienced Software Engineer with a passion for building scalable systems...",
      "contactInfo": {
        "email": "alice@example.com"
      },
      "meetings": [
        {
          "id": "meeting_001",
          "title": "Team Standup",
          "start": "2025-11-22T09:00:00",
          "end": "2025-11-22T09:30:00"
        },
        ...
      ]
    },
    ...
  ]
}
    """)


async def example_use_case():
    """Example: Common use case - Get all participant info for the week."""
    print("\n=== Example 4: Common Use Case ===\n")
    print("Use Case: I want to prepare for my meetings next week")
    print("          by understanding who will attend and their backgrounds.\n")
    
    print("Step 1: Call generate_participant_profiles")
    print("  -> Returns all meetings with participant profiles\n")
    
    print("Step 2: Process the data")
    print("  -> Filter by specific days")
    print("  -> Group by department")
    print("  -> Identify key stakeholders\n")
    
    print("Step 3: Use the information")
    print("  -> Prepare talking points for each participant")
    print("  -> Understand team dynamics")
    print("  -> Plan meeting agendas accordingly")


async def main():
    """Run all examples."""
    print("=" * 80)
    print("MCP Meetings Server - Usage Examples")
    print("=" * 80)
    
    await example_get_meetings()
    await example_get_participants()
    await example_generate_profiles()
    await example_use_case()
    
    print("\n" + "=" * 80)
    print("For more information, see the README.md file")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
