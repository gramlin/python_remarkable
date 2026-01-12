from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from dateutil import parser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from zoneinfo import ZoneInfo

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


@dataclass(frozen=True)
class CalendarEvent:
    summary: str
    start: datetime
    end: datetime
    location: str | None
    description: str | None

    @property
    def is_all_day(self) -> bool:
        return self.start.time() == datetime.min.time() and self.end.time() == datetime.min.time()


def _parse_event_datetime(raw: dict, timezone: ZoneInfo) -> datetime:
    if "dateTime" in raw:
        return parser.isoparse(raw["dateTime"]).astimezone(timezone)
    parsed = parser.isoparse(raw["date"]).date()
    return datetime.combine(parsed, datetime.min.time(), tzinfo=timezone)


def get_calendar_service(credentials_path: Path, token_path: Path) -> object:
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return build("calendar", "v3", credentials=creds)


def fetch_week_events(
    service: object,
    calendar_id: str,
    week_start: datetime,
    timezone: ZoneInfo,
) -> list[CalendarEvent]:
    week_end = week_start + timedelta(days=7)
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=week_start.isoformat(),
            timeMax=week_end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = []
    for item in events_result.get("items", []):
        start = _parse_event_datetime(item["start"], timezone)
        end = _parse_event_datetime(item["end"], timezone)
        events.append(
            CalendarEvent(
                summary=item.get("summary", "(utan titel)"),
                start=start,
                end=end,
                location=item.get("location"),
                description=item.get("description"),
            )
        )
    return events


def group_events_by_day(events: Iterable[CalendarEvent], timezone: ZoneInfo) -> dict[str, list[CalendarEvent]]:
    grouped: dict[str, list[CalendarEvent]] = {}
    for event in events:
        day_key = event.start.astimezone(timezone).date().isoformat()
        grouped.setdefault(day_key, []).append(event)
    return grouped
