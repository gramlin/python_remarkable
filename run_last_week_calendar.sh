#!/usr/bin/env bash
set -euo pipefail

week_date=$(date -d "monday last week" +%Y-%m-%d)

pipenv run python -m remarkable_calendar \
  --week "$week_date" \
  --all-calendars \
  --upload \
  --remote-dir "/01 Planering" \
  "$@"
