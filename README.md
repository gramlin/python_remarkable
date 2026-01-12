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
- [rmapi](https://github.com/juruen/rmapi) (för uppladdning till ReMarkable)
  - För Linux/WSL: `wget https://github.com/juruen/rmapi/releases/latest/download/rmapi-linux-x64.deb && sudo dpkg -i rmapi-linux-x64.deb` (om det inte fungerar, ladda ner manuellt från [releases](https://github.com/juruen/rmapi/releases), eller bygg från källa: `git clone https://github.com/juruen/rmapi.git && cd rmapi && go build && sudo mv rmapi /usr/local/bin/`, eller installera via Go: `go install github.com/juruen/rmapi@latest`)
  - För Windows: Ladda ner `rmapi-windows-x64.zip` från [releases](https://github.com/juruen/rmapi/releases) och lägg till i PATH.
  - Notera: Detta är ett separat verktyg, inte ett Python-paket – installera inte via pip.
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

För alla kalendrar:

```bash
pipenv run python -m remarkable_calendar \
  --week 2024-04-08 \
  --all-calendars \
  --timezone Europe/Stockholm
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

För uppladdning till ReMarkable:

```bash
pipenv run python -m remarkable_calendar \
  --week 2024-04-08 \
  --all-calendars \
  --upload \
  --remote-dir /Kalender
```

### Anpassa Typst-mallen

Redigera `templates/week.typ` för att ändra layouten på PDF:en.
