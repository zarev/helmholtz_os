"""Google Calendar client for fetching meetings."""

import os
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# If modifying these scopes, delete the token.pickle file.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


class CalendarClient:
    """Client for interacting with Google Calendar API."""
    
    def __init__(self):
        """Initialize the calendar client."""
        self.service = None
        self.credentials = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API."""
        # Check if we have stored credentials
        creds = None
        token_path = os.path.join(os.path.dirname(__file__), 'token.pickle')
        credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
        
        # Try to load saved credentials
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # If credentials.json doesn't exist, use mock data for demo
                if not os.path.exists(credentials_path):
                    print("Warning: No credentials.json found. Using mock calendar data.")
                    self.service = None
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        if creds:
            self.service = build('calendar', 'v3', credentials=creds)
    
    async def get_next_week_meetings(self, calendar_id: str = 'primary') -> List[Dict]:
        """
        Get all meetings for the next week.
        
        Args:
            calendar_id: Calendar ID to fetch from (default: 'primary')
        
        Returns:
            List of meeting dictionaries
        """
        # If no service (mock mode), return sample data
        if not self.service:
            return self._get_mock_meetings()
        
        # Calculate time range (next 7 days)
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=7)).isoformat() + 'Z'
        
        try:
            # Call the Calendar API
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format the events
            meetings = []
            for event in events:
                meeting = {
                    'id': event.get('id'),
                    'summary': event.get('summary', 'No Title'),
                    'start': event.get('start', {}),
                    'end': event.get('end', {}),
                    'location': event.get('location', ''),
                    'description': event.get('description', ''),
                    'attendees': event.get('attendees', [])
                }
                meetings.append(meeting)
            
            return meetings
        
        except Exception as e:
            print(f"Error fetching meetings: {e}")
            return self._get_mock_meetings()
    
    async def get_meeting_participants(self, meeting_id: str, calendar_id: str = 'primary') -> List[Dict]:
        """
        Get participants for a specific meeting.
        
        Args:
            meeting_id: ID of the meeting
            calendar_id: Calendar ID (default: 'primary')
        
        Returns:
            List of participant dictionaries
        """
        # If no service (mock mode), return sample data
        if not self.service:
            return self._get_mock_participants()
        
        try:
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=meeting_id
            ).execute()
            
            attendees = event.get('attendees', [])
            
            participants = []
            for attendee in attendees:
                participant = {
                    'email': attendee.get('email'),
                    'displayName': attendee.get('displayName', attendee.get('email', '').split('@')[0]),
                    'responseStatus': attendee.get('responseStatus', 'needsAction'),
                    'organizer': attendee.get('organizer', False),
                    'optional': attendee.get('optional', False)
                }
                participants.append(participant)
            
            return participants
        
        except Exception as e:
            print(f"Error fetching participants for meeting {meeting_id}: {e}")
            return self._get_mock_participants()
    
    def _get_mock_meetings(self) -> List[Dict]:
        """Return mock meeting data for demo purposes."""
        now = datetime.now()
        
        return [
            {
                'id': 'meeting_001',
                'summary': 'Team Standup',
                'start': {'dateTime': (now + timedelta(days=1, hours=9)).isoformat()},
                'end': {'dateTime': (now + timedelta(days=1, hours=9, minutes=30)).isoformat()},
                'location': 'Conference Room A',
                'description': 'Daily team standup meeting',
                'attendees': [
                    {'email': 'alice@example.com'},
                    {'email': 'bob@example.com'},
                    {'email': 'charlie@example.com'}
                ]
            },
            {
                'id': 'meeting_002',
                'summary': 'Product Planning',
                'start': {'dateTime': (now + timedelta(days=2, hours=14)).isoformat()},
                'end': {'dateTime': (now + timedelta(days=2, hours=15, minutes=30)).isoformat()},
                'location': 'Virtual - Zoom',
                'description': 'Q4 product planning session',
                'attendees': [
                    {'email': 'alice@example.com'},
                    {'email': 'david@example.com'},
                    {'email': 'emma@example.com'}
                ]
            },
            {
                'id': 'meeting_003',
                'summary': '1:1 with Manager',
                'start': {'dateTime': (now + timedelta(days=3, hours=10)).isoformat()},
                'end': {'dateTime': (now + timedelta(days=3, hours=10, minutes=30)).isoformat()},
                'location': 'Office',
                'description': 'Weekly 1:1 meeting',
                'attendees': [
                    {'email': 'bob@example.com'},
                    {'email': 'manager@example.com'}
                ]
            },
            {
                'id': 'meeting_004',
                'summary': 'Client Demo',
                'start': {'dateTime': (now + timedelta(days=4, hours=15)).isoformat()},
                'end': {'dateTime': (now + timedelta(days=4, hours=16)).isoformat()},
                'location': 'Client Office',
                'description': 'Product demo for client',
                'attendees': [
                    {'email': 'alice@example.com'},
                    {'email': 'charlie@example.com'},
                    {'email': 'frank@example.com'}
                ]
            },
            {
                'id': 'meeting_005',
                'summary': 'Engineering Review',
                'start': {'dateTime': (now + timedelta(days=5, hours=11)).isoformat()},
                'end': {'dateTime': (now + timedelta(days=5, hours=12)).isoformat()},
                'location': 'Engineering Lab',
                'description': 'Technical architecture review',
                'attendees': [
                    {'email': 'bob@example.com'},
                    {'email': 'david@example.com'},
                    {'email': 'emma@example.com'},
                    {'email': 'grace@example.com'}
                ]
            }
        ]
    
    def _get_mock_participants(self) -> List[Dict]:
        """Return mock participant data for demo purposes."""
        return [
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
                'responseStatus': 'accepted',
                'organizer': False,
                'optional': False
            },
            {
                'email': 'charlie@example.com',
                'displayName': 'Charlie Davis',
                'responseStatus': 'tentative',
                'organizer': False,
                'optional': False
            }
        ]
