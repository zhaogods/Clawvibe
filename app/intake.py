from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.models import TaskInput


def load_text(direct_value: str | None, file_path: str | None) -> str:
    if direct_value and file_path:
        raise ValueError("Use either direct text or a file path, not both.")
    if file_path:
        return read_text_with_fallback(Path(file_path))
    if direct_value:
        return direct_value.strip()
    return ""


def read_text_with_fallback(path: Path) -> str:
    encodings = ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "gbk")
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding).strip()
        except UnicodeDecodeError as error:
            last_error = error
            continue
    if last_error:
        raise last_error
    return path.read_text().strip()


def build_task(repo: str, error_log: str, steps: str, branch: str | None) -> TaskInput:
    if not repo.strip():
        raise ValueError("Repository path or URL is required.")
    if not error_log.strip():
        raise ValueError("Error log is required.")
    if not steps.strip():
        raise ValueError("Reproduction steps are required.")

    task_id = datetime.now().strftime("task_%Y%m%d_%H%M%S")
    return TaskInput(
        task_id=task_id,
        repo=repo.strip(),
        error_log=error_log.strip(),
        steps=steps.strip(),
        branch=branch.strip() if branch else None,
    )
