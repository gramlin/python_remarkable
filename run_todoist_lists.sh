#!/usr/bin/env bash
set -euo pipefail

pipenv run python -m remarkable_calendar \
  --todoist \
  --upload \
  --remote-dir /Todoist \
  "$@"
