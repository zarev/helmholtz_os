import datetime as dt
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.mcp_meetings import build_meeting_participant_report


def test_build_report_filters_next_week_and_profiles():
    sample_path = Path(__file__).parent / "data" / "sample_meetings.ics"
    fixed_now = dt.datetime(2024, 8, 1, 9, 0, tzinfo=dt.timezone.utc)

    report = build_meeting_participant_report(str(sample_path), now=fixed_now)

    participants = {participant["name"]: participant for participant in report["participants"]}

    assert "Alice Adams" in participants
    assert "Bob Brown" in participants
    assert "Carol Chen" in participants
    assert "Outside Person" not in participants

    assert participants["Alice Adams"]["meetings"][0]["title"] == "Product Sync"
    assert len(participants["Bob Brown"]["meetings"]) == 2

    for participant in participants.values():
        assert participant["mini_profile"].startswith(participant["name"])
        assert "meeting" in participant["mini_profile"].lower()
