"""Test script for MCP Meetings functionality."""

import asyncio
import json
from datetime import datetime

from mcp_meetings.calendar_client import CalendarClient
from mcp_meetings.participant_profiler import ParticipantProfiler


async def test_calendar_client():
    """Test the calendar client."""
    print("=" * 80)
    print("Testing Calendar Client")
    print("=" * 80)
    
    client = CalendarClient()
    
    # Test getting next week's meetings
    print("\n1. Getting next week's meetings...")
    meetings = await client.get_next_week_meetings()
    print(f"Found {len(meetings)} meetings")
    
    for i, meeting in enumerate(meetings, 1):
        print(f"\nMeeting {i}:")
        print(f"  Title: {meeting['summary']}")
        print(f"  Start: {meeting['start'].get('dateTime', 'N/A')}")
        print(f"  Attendees: {len(meeting.get('attendees', []))}")
    
    # Test getting participants for first meeting
    if meetings:
        print(f"\n2. Getting participants for first meeting...")
        meeting_id = meetings[0]['id']
        participants = await client.get_meeting_participants(meeting_id)
        print(f"Found {len(participants)} participants:")
        for participant in participants:
            print(f"  - {participant.get('displayName', participant.get('email', 'Unknown'))}")


async def test_participant_profiler():
    """Test the participant profiler."""
    print("\n" + "=" * 80)
    print("Testing Participant Profiler")
    print("=" * 80)
    
    profiler = ParticipantProfiler()
    
    # Sample participant data
    sample_participants = [
        {
            'email': 'alice@example.com',
            'displayName': 'Alice Johnson',
            'responseStatus': 'accepted',
            'organizer': True,
            'optional': False
        },
        {
            'email': 'bob@example.com',
            'displayName': 'Bob Smith',
            'responseStatus': 'tentative',
            'organizer': False,
            'optional': False
        }
    ]
    
    print("\nGenerating profiles for sample participants...")
    for participant in sample_participants:
        profile = await profiler.generate_profile(participant, include_mini_profile=True)
        print(f"\n{profile['name']} ({profile['email']}):")
        print(f"  Role: {profile['role']}")
        print(f"  Department: {profile['department']}")
        print(f"  Mini Profile: {profile['miniProfile']}")


async def test_full_workflow():
    """Test the full workflow: meetings -> participants -> profiles."""
    print("\n" + "=" * 80)
    print("Testing Full Workflow")
    print("=" * 80)
    
    client = CalendarClient()
    profiler = ParticipantProfiler()
    
    # Get meetings
    print("\n1. Fetching next week's meetings...")
    meetings = await client.get_next_week_meetings()
    print(f"Found {len(meetings)} meetings")
    
    # Collect all unique participants
    print("\n2. Collecting all participants...")
    all_participants = {}
    
    for meeting in meetings:
        meeting_id = meeting.get('id')
        meeting_title = meeting.get('summary', 'Untitled')
        
        # Get attendees from meeting data
        attendees = meeting.get('attendees', [])
        
        for attendee in attendees:
            email = attendee.get('email')
            if email and email not in all_participants:
                # Create participant object
                participant = {
                    'email': email,
                    'displayName': email.split('@')[0].replace('.', ' ').title(),
                    'responseStatus': 'accepted',
                    'organizer': False,
                    'optional': False
                }
                
                # Generate profile
                profile = await profiler.generate_profile(participant, include_mini_profile=True)
                all_participants[email] = profile
                all_participants[email]['meetings'] = []
            
            # Add meeting to participant's list
            if email in all_participants:
                all_participants[email]['meetings'].append({
                    'id': meeting_id,
                    'title': meeting_title,
                    'start': meeting.get('start', {}).get('dateTime', ''),
                    'end': meeting.get('end', {}).get('dateTime', '')
                })
    
    print(f"Found {len(all_participants)} unique participants")
    
    # Generate final output
    print("\n3. Generating final JSON output...")
    result = {
        'date_range': {
            'start': datetime.now().isoformat(),
            'end': datetime.now().isoformat()
        },
        'total_meetings': len(meetings),
        'total_participants': len(all_participants),
        'participants': list(all_participants.values())
    }
    
    # Print formatted JSON
    print("\nFinal Output:")
    print(json.dumps(result, indent=2, default=str))
    
    # Save to file
    output_file = '/tmp/meeting_participants_output.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nOutput saved to: {output_file}")


async def main():
    """Run all tests."""
    print("MCP Meetings - Functionality Tests")
    print("=" * 80)
    
    await test_calendar_client()
    await test_participant_profiler()
    await test_full_workflow()
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
