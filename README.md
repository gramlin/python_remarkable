# python_remarkable

Scripter som genererar filer i ReMarkable.

## Kalender till PDF (Google Calendar → Typst → ReMarkable)

Detta projekt laddar ner dina kalenderposter för en given vecka (måndag–söndag), renderar dem
med en Typst-mall och laddar upp PDF:en till ReMarkable Cloud.

### Förutsättningar

- Python 3.11+
- [Pipenv](https://pipenv.pypa.io/)
- [Typst](https://typst.app/docs/reference/cli/)
- [rmapi](https://github.com/juruen/rmapi) (för uppladdning till ReMarkable)
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

```bash
pipenv run python -m remarkable_calendar \
  --week 2024-04-08 \
  --calendar-id primary \
  --timezone Europe/Stockholm \
  --output output/kalender.pdf
```

För uppladdning till ReMarkable:

```bash
pipenv run python -m remarkable_calendar \
  --week 2024-04-08 \
  --upload \
  --remote-dir /Kalender
```

### Anpassa Typst-mallen

Redigera `templates/week.typ` för att ändra layouten på PDF:en.
