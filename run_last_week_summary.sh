#!/usr/bin/env bash
set -euo pipefail

summary_start=$(date -d "monday last week" +%Y-%m-%d)
summary_end=$(date -d "sunday last week" +%Y-%m-%d)

pipenv run python -m remarkable_calendar \
  --summary \
  --summary-start "$summary_start" \
  --summary-end "$summary_end" \
  --all-calendars \
  --upload \
  --remote-dir "/01 Planering/2026 Arki" \
  "$@"
