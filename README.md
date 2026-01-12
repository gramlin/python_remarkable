# python_remarkable

Scripter som genererar filer i ReMarkable.

## Kalender till PDF (Google Calendar → Typst → ReMarkable)

Detta projekt laddar ner dina kalenderposter för en given vecka (måndag–söndag), renderar dem
med en Typst-mall och laddar upp PDF:en till ReMarkable Cloud.

### Förutsättningar

- Python 3.11+
- [Pipenv](https://pipenv.pypa.io/)
- [Typst](https://typst.app/docs/reference/cli/)
  - För Windows: Ladda ner från [releases](https://github.com/typst/typst/releases) och lägg till i PATH.
  - För WSL/Linux: `wget https://github.com/typst/typst/releases/latest/download/typst-x86_64-unknown-linux-musl.tar.xz && tar -xf typst-x86_64-unknown-linux-musl.tar.xz && sudo mv typst /usr/local/bin/`
- [rm_api](https://pypi.org/project/rm-api/) (för uppladdning till ReMarkable)
- Google Calendar API-uppgifter (`credentials.json`)

### Installera

```bash
pipenv install
```

Installera projektet i editable-läge (behövs för `python -m remarkable_calendar`):

```bash
pipenv install -e .
```

### Google Calendar OAuth

1. Skapa OAuth-klient i Google Cloud Console.
2. Ladda ner `credentials.json` och placera i projektets rot.
3. Kör första gången för att skapa `token.json`.

### Kör

#### Veckokalender

```bash
pipenv run python -m remarkable_calendar \
  --week 2024-04-08 \
  --calendar-id primary \
  --timezone Europe/Stockholm \
  --output output/kalender.pdf
```

För alla kalendrar:

```bash
pipenv run python -m remarkable_calendar \
  --week 2024-04-08 \
  --all-calendars \
  --timezone Europe/Stockholm
```

#### Veckosummering

Summering kan genereras för valfri period. Du anger startdatum (krävs) och ev. slutdatum.
Om slutdatum utelämnas används en vecka (7 dagar) från startdatum.

```bash
pipenv run python -m remarkable_calendar \
  --summary \
  --summary-start 2024-04-08 \
  --summary-end 2024-04-14 \
  --timezone Europe/Stockholm
```

#### Snabbskript för senaste veckan

Det finns två shellscript i projektets rot som genererar senaste veckan. De skickar vidare
alla extra argument till Python-kommandot, så du kan t.ex. lägga till `--upload` eller
`--all-calendars`.

```bash
./run_last_week_calendar.sh --timezone Europe/Stockholm
```

```bash
./run_last_week_summary.sh --timezone Europe/Stockholm
```

Om du får felet att `typst` inte hittas:

- Verifiera i samma miljö som du kör kommandot: `typst --version`
- Om du kör i WSL behöver Typst vara installerat i WSL (inte bara i Windows)
- Du kan ange sökväg explicit:

```bash
pipenv run python -m remarkable_calendar \
  --week 2024-04-08 \
  --typst-bin /path/to/typst \
  --output output/kalender.pdf
```

…eller via env var: `TYPST_BIN=/path/to/typst`.

För uppladdning till ReMarkable (kräver att du har en rm_api-tokenfil, t.ex. `token`):

```bash
pipenv run python -m remarkable_calendar \
  --week 2024-04-08 \
  --all-calendars \
  --upload \
  --remote-dir /Kalender \
  --rm-token-file token
```

### Anpassa Typst-mallen

Redigera `templates/week.typ` eller `templates/summary.typ` för att ändra layouten på PDF:en.
