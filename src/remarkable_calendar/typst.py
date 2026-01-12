from __future__ import annotations

import subprocess
import shutil
from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class TypstConfig:
    typst_bin: str | None = None


def _resolve_typst_bin(typst_bin: str | None) -> str:
    configured = typst_bin or os.environ.get("TYPST_BIN")
    if configured:
        return configured
    resolved = shutil.which("typst")
    if resolved:
        return resolved
    raise RuntimeError(
        "Hittade inte 'typst' i PATH. Installera Typst och/eller lägg till det i PATH.\n\n"
        "Tips:\n"
        "- Verifiera i samma miljö som du kör kommandot: 'typst --version'\n"
        "- Om du kör i WSL behöver Typst vara installerat i WSL (inte bara i Windows).\n"
        "- Du kan även ange sökväg via --typst-bin eller miljövariabeln TYPST_BIN."
    )


def compile_typst(
    template_path: Path,
    data_path: Path,
    output_pdf: Path,
    config: TypstConfig | None = None,
) -> None:
    typst_exe = _resolve_typst_bin(config.typst_bin if config else None)
    # Make data path relative to template directory
    data_rel = Path(os.path.relpath(str(data_path), str(template_path.parent)))
    command = [
        typst_exe,
        "compile",
        "--root",
        ".",
        "--input",
        f"data={data_rel}",
        str(template_path),
        str(output_pdf),
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Typst-kompilering misslyckades:\n"
            f"{result.stdout}\n{result.stderr}"
        )
