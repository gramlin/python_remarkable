from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

from remarkable_calendar.google_calendar import (
    CalendarEvent,
    fetch_week_events,
    get_calendar_service,
    group_events_by_day,
)
from remarkable_calendar.remarkable import upload_pdf_with_rmapi
from remarkable_calendar.typst import compile_typst

WEEKDAY_NAMES = [
    "Måndag",
    "Tisdag",
    "Onsdag",
    "Torsdag",
    "Fredag",
    "Lördag",
    "Söndag",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hämta kalenderposter från Google Calendar och skapa en PDF för ReMarkable."
    )
    parser.add_argument(
        "--week",
        type=str,
        help="Datum i veckan (YYYY-MM-DD). Veckan börjar alltid på måndag.",
    )
    parser.add_argument("--calendar-id", default="primary", help="Google Calendar ID")
    parser.add_argument(
        "--timezone",
        default="Europe/Stockholm",
        help="Tidszon för vecka och tider.",
    )
    parser.add_argument(
        "--credentials",
        default="credentials.json",
        help="Sökväg till Google OAuth credentials.json",
    )
    parser.add_argument(
        "--token",
        default="token.json",
        help="Sökväg till sparad OAuth token.json",
    )
    parser.add_argument(
        "--template",
        default="templates/week.typ",
        help="Sökväg till Typst-mall.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Sökväg till genererad PDF. Standard blir output/week-YYYY-WW.pdf",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Ladda upp PDF till ReMarkable via rmapi.",
    )
    parser.add_argument(
        "--remote-dir",
        default=None,
        help="Mapp i ReMarkable där PDF ska laddas upp.",
    )
    return parser.parse_args()


def week_start_for(date_value: date, timezone: ZoneInfo) -> datetime:
    start = date_value - timedelta(days=date_value.weekday())
    return datetime.combine(start, datetime.min.time(), tzinfo=timezone)


def serialize_events(
    events: Iterable[CalendarEvent],
    week_start: datetime,
    timezone: ZoneInfo,
) -> dict:
    grouped = group_events_by_day(events, timezone)
    days = []
    for offset in range(7):
        current_day = week_start + timedelta(days=offset)
        key = current_day.date().isoformat()
        day_events = grouped.get(key, [])
        formatted = []
        for event in day_events:
            if event.is_all_day:
                time_label = "Hela dagen"
            else:
                time_label = f"{event.start.strftime('%H:%M')}–{event.end.strftime('%H:%M')}"
            formatted.append(
                {
                    "summary": event.summary,
                    "time": time_label,
                    "location": event.location,
                    "description": event.description,
                }
            )
        days.append(
            {
                "date": key,
                "weekday": WEEKDAY_NAMES[offset],
                "events": formatted,
            }
        )
    week_number = week_start.isocalendar().week
    return {
        "week_start": week_start.date().isoformat(),
        "week_end": (week_start + timedelta(days=6)).date().isoformat(),
        "week_number": week_number,
        "days": days,
    }


def resolve_output_path(output_arg: str | None, week_start: datetime) -> Path:
    if output_arg:
        return Path(output_arg)
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"week-{week_start.date().isoformat()}-v{week_start.isocalendar().week}.pdf"


def main() -> None:
    args = parse_args()
    timezone = ZoneInfo(args.timezone)
    if args.week:
        date_value = datetime.strptime(args.week, "%Y-%m-%d").date()
    else:
        date_value = datetime.now(timezone).date()

    week_start = week_start_for(date_value, timezone)

    service = get_calendar_service(Path(args.credentials), Path(args.token))
    events = fetch_week_events(service, args.calendar_id, week_start, timezone)

    data = serialize_events(events, week_start, timezone)
    output_path = resolve_output_path(args.output, week_start)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data_path = output_path.with_suffix(".json")
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    compile_typst(Path(args.template), data_path, output_path)

    if args.upload:
        upload_pdf_with_rmapi(output_path, args.remote_dir)

    print(f"Skapade PDF: {output_path}")


if __name__ == "__main__":
    main()
