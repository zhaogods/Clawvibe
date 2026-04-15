from __future__ import annotations

from pathlib import Path

from app.analyzer import diagnose
from app.intake import build_task
from app.models import AnalysisResult
from app.repo_reader import prepare_repository, scan_repository
from app.reporter import write_artifacts
from app.reproducer import build_execution_plan, execute_plan


def run_analysis(
    repo: str,
    error_log: str,
    steps: str,
    branch: str | None = None,
    runs_dir: str | Path = "runs",
    timeout_seconds: int = 180,
) -> AnalysisResult:
    task = build_task(repo, error_log, steps, branch)

    runs_root = Path(runs_dir)
    task_dir = runs_root / task.task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    repo_path, source_kind = prepare_repository(task, task_dir)
    summary = scan_repository(repo_path, task.error_log, source_kind, task.steps)
    plan = build_execution_plan(summary, task.steps)
    executions = execute_plan(repo_path, plan, timeout_seconds=timeout_seconds)
    diagnosis = diagnose(task, summary, executions)
    report_path = write_artifacts(task_dir, task, summary, executions, diagnosis, plan)

    return AnalysisResult(
        task=task,
        summary=summary,
        executions=executions,
        diagnosis=diagnosis,
        task_dir=str(task_dir),
        report_path=str(report_path),
        execution_plan=plan,
    )
