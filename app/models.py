from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class TaskInput:
    task_id: str
    repo: str
    error_log: str
    steps: str
    branch: str | None = None
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RepositorySummary:
    source_kind: str
    repo_path: str
    repo_name: str
    tech_stack: str
    package_manager: str | None
    dependency_files: list[str]
    config_files: list[str]
    entrypoints: list[str]
    test_commands: list[str]
    related_files: list[str]
    top_level_dirs: list[str]
    readme_excerpt: str
    preflight_checks: list[str]
    scan_notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExecutionRecord:
    label: str
    command: str
    cwd: str
    started_at: str
    finished_at: str
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExecutionPlanStep:
    label: str
    kind: str
    command: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Diagnosis:
    error_type: str
    summary: str
    evidence: list[str]
    root_causes: list[str]
    related_files: list[str]
    fix_suggestions: list[str]
    verify_steps: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AnalysisResult:
    task: TaskInput
    summary: RepositorySummary
    executions: list[ExecutionRecord]
    diagnosis: Diagnosis
    task_dir: str
    report_path: str
    execution_plan: list[ExecutionPlanStep]

    def to_dict(self) -> dict:
        return {
            "task": self.task.to_dict(),
            "summary": self.summary.to_dict(),
            "executions": [record.to_dict() for record in self.executions],
            "diagnosis": self.diagnosis.to_dict(),
            "task_dir": self.task_dir,
            "report_path": self.report_path,
            "execution_plan": [step.to_dict() for step in self.execution_plan],
        }
