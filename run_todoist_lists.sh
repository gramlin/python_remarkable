#!/usr/bin/env bash
set -euo pipefail

pipenv run python -m remarkable_calendar \
  --todoist \
  --upload \
  --remote-dir "/02 TODO" \
  --todoist-token=2bc9a33373fc68497ae37c954f9c921ecbf5e511
  "$@"
