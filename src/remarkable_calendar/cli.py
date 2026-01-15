from __future__ import annotations

import argparse
import json
import os
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
from remarkable_calendar.todoist import fetch_projects, fetch_tasks
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
    parser.add_argument(
        "--todoist",
        action="store_true",
        help="Skapa Todoist-listor som PDF.",
    )
    parser.add_argument(
        "--todoist-token",
        default=None,
        help="Todoist API-token (alternativt via TODOIST_API_TOKEN).",
    )
    parser.add_argument(
        "--todoist-projects",
        default="Personligt,Arbete,Cure,Handla",
        help="Kommaseparerad lista med Todoist-projekt som ska exporteras.",
    )
    parser.add_argument(
        "--todoist-template",
        default="templates/todoist.typ",
        help="Sökväg till Typst-mall för Todoist-listor.",
    )
    parser.add_argument(
        "--todoist-output-dir",
        default="output/todoist",
        help="Katalog för genererade Todoist-PDF:er.",
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
        day_events = sorted(grouped.get(key, []), key=lambda e: e.start)
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


def _slugify_filename(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in ("-", "_") else "-" for char in value)
    return "-".join(filter(None, safe.split("-"))).strip("-") or "todoist"


def _resolve_todoist_token(arg_value: str | None) -> str:
    token = arg_value or os.environ.get("TODOIST_API_TOKEN")
    if not token:
        raise ValueError("Todoist-token saknas. Ange --todoist-token eller TODOIST_API_TOKEN.")
    return token


def _parse_todoist_projects(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def generate_todoist_documents(args: argparse.Namespace) -> None:
    token = _resolve_todoist_token(args.todoist_token)
    project_names = _parse_todoist_projects(args.todoist_projects)
    if not project_names:
        raise ValueError("Ange minst ett Todoist-projekt i --todoist-projects.")

    projects = fetch_projects(token)
    project_lookup = {project.name.casefold(): project for project in projects}

    missing = [name for name in project_names if name.casefold() not in project_lookup]
    if missing:
        raise ValueError(
            "Hittade inte följande Todoist-projekt: "
            + ", ".join(missing)
            + ". Kontrollera projektnamnen i Todoist."
        )

    template_path = Path(args.todoist_template)
    output_dir = Path(args.todoist_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for name in project_names:
        project = project_lookup[name.casefold()]
        print(f"\nBearbetar projekt: {project.name}")
        print(f"Hämtar uppgifter från Todoist...")
        tasks = fetch_tasks(token, project.project_id)
        print(f"Hittade {len(tasks)} uppgifter")
        data = {
            "project_name": project.name,
            "generated_at": datetime.now().isoformat(timespec="minutes"),
            "items": [
                {
                    "content": task.content,
                    "description": task.description,
                    "due": task.due,
                }
                for task in tasks
            ],
        }
        output_path = output_dir / f"{_slugify_filename(project.name)}.pdf"
        data_path = output_path.with_suffix(".json")
        print(f"Sparar data till: {data_path}")
        data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Kompilerar PDF med Typst...")
        compile_typst(
            template_path,
            data_path,
            output_path,
            config=TypstConfig(typst_bin=args.typst_bin),
        )
        print(f"✓ PDF skapad: {output_path}")

        if args.upload:
            print(f"\nLaddar upp till reMarkable...")
            upload_pdf_with_rmapi(
                output_path,
                args.remote_dir,
                token_file=args.rm_token_file,
                sync_dir=args.rm_sync_dir,
                log_file=args.rm_log_file,
            )


def main() -> None:
    args = parse_args()
    if args.todoist:
        generate_todoist_documents(args)
        return
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
