"""Configuration for MCP Meetings app."""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Calendar settings
CALENDAR_ID = os.getenv("MCP_CALENDAR_ID", "primary")
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.pickle")

# Server settings
SERVER_NAME = "mcp-meetings"
SERVER_VERSION = "0.1.0"

# Google Calendar API scopes
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Profile generation settings
INCLUDE_MINI_PROFILE_DEFAULT = True
