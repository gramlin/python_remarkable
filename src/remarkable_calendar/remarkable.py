from __future__ import annotations

import subprocess
from pathlib import Path


def upload_pdf_with_rmapi(pdf_path: Path, remote_dir: str | None = None) -> None:
    destination = pdf_path.name
    if remote_dir:
        destination = f"{remote_dir.rstrip('/')}/{pdf_path.name}"
    command = ["rmapi", "put", str(pdf_path), destination]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Uppladdning till ReMarkable misslyckades via rmapi:\n"
            f"{result.stdout}\n{result.stderr}"
        )
