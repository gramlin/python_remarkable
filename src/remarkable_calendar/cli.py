from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

from remarkable_calendar.google_calendar import (
    CalendarEvent,
    fetch_events_in_range,
    fetch_week_events,
    get_all_calendar_ids,
    get_calendar_service,
    group_events_by_day,
)
from remarkable_calendar.remarkable import upload_pdf_with_rmapi
from remarkable_calendar.typst import TypstConfig, compile_typst

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
        "--all-calendars",
        action="store_true",
        help="Hämta händelser från alla kalendrar istället för bara en specifik.",
    )
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
        default=None,
        help="Sökväg till Typst-mall.",
    )
    parser.add_argument(
        "--typst-bin",
        default=None,
        help="Sökväg till Typst-binär (om 'typst' inte finns i PATH). Kan även sättas via TYPST_BIN.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Sökväg till genererad PDF. Standard blir output/YYYY-WW.pdf",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Skapa en veckosummering med summary.typ.",
    )
    parser.add_argument(
        "--summary-start",
        default=None,
        help="Startdatum för veckosummering (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--summary-end",
        default=None,
        help="Slutdatum för veckosummering (YYYY-MM-DD). Om utelämnad används en vecka.",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Ladda upp PDF till ReMarkable via rm_api.",
    )
    parser.add_argument(
        "--remote-dir",
        default=None,
        help="Mapp i ReMarkable där PDF ska laddas upp.",
    )
    parser.add_argument(
        "--rm-token-file",
        default="token",
        help="Sökväg till rm_api-tokenfil (default: token).",
    )
    parser.add_argument(
        "--rm-sync-dir",
        default="sync",
        help="Sökväg till rm_api sync-katalog (default: sync).",
    )
    parser.add_argument(
        "--rm-log-file",
        default="rm_api.log",
        help="Sökväg till rm_api log-fil (default: rm_api.log).",
    )
    return parser.parse_args()


def week_start_for(date_value: date, timezone: ZoneInfo) -> datetime:
    start = date_value - timedelta(days=date_value.weekday())
    return datetime.combine(start, datetime.min.time(), tzinfo=timezone)


def serialize_events_for_range(
    events: Iterable[CalendarEvent],
    range_start: datetime,
    range_end: datetime,
    timezone: ZoneInfo,
) -> dict:
    # Filter out week number calendars
    filtered_events = [
        event for event in events 
        if not (event.calendar_name and 
                ("veckonummer" in event.calendar_name.lower() or 
                 "week number" in event.calendar_name.lower()))
    ]
    grouped = group_events_by_day(filtered_events, timezone)
    days = []
    total_days = (range_end.date() - range_start.date()).days + 1
    for offset in range(total_days):
        current_day = range_start + timedelta(days=offset)
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
                    "calendar": event.calendar_name,
                    "location": event.location,
                    "description": event.description,
                }
            )
        days.append(
            {
                "date": key,
                "weekday": WEEKDAY_NAMES[current_day.weekday()],
                "events": formatted,
            }
        )
    week_number = range_start.isocalendar().week
    return {
        "week_start": range_start.date().isoformat(),
        "week_end": range_end.date().isoformat(),
        "week_number": week_number,
        "days": days,
    }


def resolve_output_path(output_arg: str | None, week_start: datetime) -> Path:
    if output_arg:
        return Path(output_arg)
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    year, week, _ = week_start.isocalendar()
    return output_dir / f"{year}-{week:02d}.pdf"


def resolve_summary_output_path(
    output_arg: str | None,
    range_start: datetime,
) -> Path:
    if output_arg:
        return Path(output_arg)
    year, week, _ = range_start.isocalendar()
    output_dir = Path(str(year))
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"Veckosummering vecka {year}{week:02d}.pdf"


def parse_date_arg(value: str, label: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Ogiltigt {label}. Använd formatet YYYY-MM-DD.") from exc


def resolve_template_path(template_arg: str | None, use_summary: bool) -> Path:
    if template_arg:
        return Path(template_arg)
    return Path("templates/summary.typ" if use_summary else "templates/week.typ")


def serialize_events(
    events: Iterable[CalendarEvent],
    week_start: datetime,
    timezone: ZoneInfo,
) -> dict:
    return serialize_events_for_range(events, week_start, week_start + timedelta(days=6), timezone)


def main() -> None:
    args = parse_args()
    timezone = ZoneInfo(args.timezone)
    use_summary = args.summary or args.summary_start or args.summary_end
    if use_summary:
        if not args.summary_start:
            raise ValueError("Ange --summary-start för veckosummering.")
        start_date = parse_date_arg(args.summary_start, "startdatum")
        if args.summary_end:
            end_date = parse_date_arg(args.summary_end, "slutdatum")
        else:
            end_date = start_date + timedelta(days=6)
        if end_date < start_date:
            raise ValueError("Slutdatum måste vara samma som eller efter startdatum.")
        range_start = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone)
        range_end = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone)
        template_path = resolve_template_path(args.template, use_summary=True)
        output_path = resolve_summary_output_path(args.output, range_start)
    else:
        if args.week:
            date_value = datetime.strptime(args.week, "%Y-%m-%d").date()
        else:
            date_value = datetime.now(timezone).date()
        week_start = week_start_for(date_value, timezone)
        range_start = week_start
        range_end = week_start + timedelta(days=6)
        template_path = resolve_template_path(args.template, use_summary=False)
        output_path = resolve_output_path(args.output, week_start)

    service = get_calendar_service(Path(args.credentials), Path(args.token))
    if args.all_calendars:
        calendar_ids = get_all_calendar_ids(service)
    else:
        calendar_ids = [args.calendar_id]
    if use_summary:
        events = fetch_events_in_range(service, calendar_ids, range_start, range_end, timezone)
        data = serialize_events_for_range(events, range_start, range_end, timezone)
    else:
        events = fetch_week_events(service, calendar_ids, range_start, timezone)
        data = serialize_events(events, range_start, timezone)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    data_path = output_path.with_suffix(".json")
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    compile_typst(
        template_path,
        data_path,
        output_path,
        config=TypstConfig(typst_bin=args.typst_bin),
    )

    if args.upload:
        upload_pdf_with_rmapi(
            output_path,
            args.remote_dir,
            token_file=args.rm_token_file,
            sync_dir=args.rm_sync_dir,
            log_file=args.rm_log_file,
        )

    print(f"Skapade PDF: {output_path}")


if __name__ == "__main__":
    main()
