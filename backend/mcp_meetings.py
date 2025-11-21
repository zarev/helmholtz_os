"""MCP-style helper to summarize next week's meeting participants.

The module reads an iCalendar source (local file path or URL), filters events
occurring in the next seven days, and aggregates participants into a JSON
report. Each participant entry includes a lightweight "mini profile" summarizing
what they're working on based on meeting titles.

Usage:
    python -m backend.mcp_meetings --ics data/calendar.ics --output report.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from icalendar import Calendar


def _load_calendar(source: str) -> Calendar:
    """Load an iCalendar from a local path or HTTP(S) URL."""
    if source.startswith("http://") or source.startswith("https://"):
        with urllib.request.urlopen(source) as resp:  # noqa: S310 - caller controls trusted URL
            data = resp.read()
    else:
        data = Path(source).read_bytes()
    return Calendar.from_ical(data)


def _decode_dt(value: Any) -> dt.datetime:
    """Coerce iCalendar date/time values to timezone-aware datetimes."""
    if isinstance(value, dt.datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=dt.timezone.utc)
        return value
    if isinstance(value, dt.date):
        return dt.datetime.combine(value, dt.time.min, tzinfo=dt.timezone.utc)
    raise TypeError(f"Unsupported date value: {value!r}")


def _iter_events(calendar: Calendar) -> Iterable[Any]:
    for component in calendar.walk():
        if component.name == "VEVENT":
            yield component


def _within_window(start: dt.datetime, window_start: dt.datetime, window_end: dt.datetime) -> bool:
    return window_start <= start <= window_end


def _normalize_attendees(raw_attendees: Any) -> List[Dict[str, Optional[str]]]:
    if raw_attendees is None:
        return []
    attendees = raw_attendees if isinstance(raw_attendees, list) else [raw_attendees]
    normalized: List[Dict[str, Optional[str]]] = []
    for attendee in attendees:
        name = None
        email = None
        if hasattr(attendee, "params"):
            name = attendee.params.get("CN")
        attendee_str = str(attendee)
        if attendee_str.lower().startswith("mailto:"):
            email = attendee_str[7:]
        else:
            email = attendee_str
        identifier = email or name
        if not identifier:
            continue
        normalized.append({"id": identifier, "name": name or email or identifier, "email": email})
    return normalized


def _mini_profile(participant: Dict[str, Any]) -> str:
    meetings = participant.get("meetings", [])
    titles = [meeting.get("title", "meeting") for meeting in meetings]
    unique_titles = list(dict.fromkeys(titles))  # preserve order, remove duplicates
    preview = ", ".join(unique_titles[:3]) if unique_titles else "upcoming meetings"
    return (
        f"{participant['name']} is attending {len(meetings)} meeting(s) this week. "
        f"Topics include {preview}."
    )


def build_meeting_participant_report(source: str, *, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """Build a participant-focused JSON-friendly report for the next week."""
    calendar = _load_calendar(source)
    now = now or dt.datetime.now(dt.timezone.utc)
    window_start = now
    window_end = now + dt.timedelta(days=7)

    participant_index: Dict[str, Dict[str, Any]] = {}
    for event in _iter_events(calendar):
        start_raw = event.decoded("dtstart")
        end_raw = event.decoded("dtend") if event.get("dtend") else None
        start = _decode_dt(start_raw)
        end = _decode_dt(end_raw) if end_raw else start + dt.timedelta(hours=1)

        if not _within_window(start, window_start, window_end):
            continue

        attendees = _normalize_attendees(event.get("attendee"))
        if not attendees:
            continue

        event_record = {
            "title": str(event.get("summary", "Untitled Meeting")),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "location": str(event.get("location")) if event.get("location") else None,
        }

        for attendee in attendees:
            participant = participant_index.setdefault(
                attendee["id"],
                {
                    "id": attendee["id"],
                    "name": attendee.get("name") or attendee["id"],
                    "email": attendee.get("email"),
                    "meetings": [],
                },
            )
            participant["meetings"].append(event_record)

    for participant in participant_index.values():
        participant["mini_profile"] = _mini_profile(participant)

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "participants": sorted(participant_index.values(), key=lambda p: p["name"].lower()),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate participant profiles from a calendar feed")
    parser.add_argument("--ics", required=True, help="Path or URL to an .ics calendar file")
    parser.add_argument("--output", help="Optional path to write JSON; prints to stdout if omitted")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    report = build_meeting_participant_report(args.ics)
    output = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
