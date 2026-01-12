from __future__ import annotations

import subprocess
from pathlib import Path


def compile_typst(template_path: Path, data_path: Path, output_pdf: Path) -> None:
    command = [
        "typst",
        "compile",
        "--input",
        f"data={data_path}",
        str(template_path),
        str(output_pdf),
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Typst-kompilering misslyckades:\n"
            f"{result.stdout}\n{result.stderr}"
        )
