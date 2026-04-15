from __future__ import annotations

import subprocess
from pathlib import Path

from app.models import ExecutionPlanStep, ExecutionRecord, RepositorySummary, utc_now_iso

ALLOWED_PREFIXES = (
    "python ",
    "python3 ",
    "py ",
    "node ",
    "npm ",
    "pnpm ",
    "yarn ",
)

def build_execution_plan(summary: RepositorySummary, steps: str) -> list[ExecutionPlanStep]:
    plan: list[ExecutionPlanStep] = []

    user_commands = extract_commands_from_steps(steps)
    for index, command in enumerate(user_commands, start=1):
        plan.append(ExecutionPlanStep(label=f"user-step-{index}", kind="user", command=command))

    if summary.tech_stack in {"python", "hybrid"}:
        requirements_file = next((name for name in summary.dependency_files if name.endswith("requirements.txt")), None)
        pyproject_file = next((name for name in summary.dependency_files if name.endswith("pyproject.toml")), None)
        if requirements_file:
            plan.append(
                ExecutionPlanStep(
                    label="install-python-deps",
                    kind="prerequisite",
                    command=f"python -m pip install -r \"{requirements_file}\"",
                )
            )
        elif pyproject_file:
            install_target = str(Path(pyproject_file).parent)
            install_target = "." if install_target == "." else install_target
            plan.append(
                ExecutionPlanStep(
                    label="install-python-project",
                    kind="prerequisite",
                    command=f"python -m pip install \"{install_target}\"",
                )
            )

        python_entrypoint = next(
            (entry for entry in summary.entrypoints if entry.endswith(".py")),
            None,
        )
        if python_entrypoint:
            plan.append(
                ExecutionPlanStep(
                    label="run-python-entrypoint",
                    kind="system",
                    command=f"python {python_entrypoint}",
                )
            )

    if summary.tech_stack in {"node", "hybrid"}:
        runner = summary.package_manager or "npm"
        if runner == "pnpm":
            plan.append(ExecutionPlanStep(label="install-node-deps", kind="prerequisite", command="pnpm install"))
        elif runner == "yarn":
            plan.append(ExecutionPlanStep(label="install-node-deps", kind="prerequisite", command="yarn install"))
        else:
            plan.append(ExecutionPlanStep(label="install-node-deps", kind="prerequisite", command="npm install"))

        script_entries = [entry for entry in summary.entrypoints if "script:" in entry]
        if script_entries:
            script_name = script_entries[0].split("script:", 1)[1]
            if runner == "yarn":
                plan.append(ExecutionPlanStep(label=f"run-{script_name}", kind="system", command=f"yarn {script_name}"))
            elif runner == "pnpm":
                plan.append(ExecutionPlanStep(label=f"run-{script_name}", kind="system", command=f"pnpm {script_name}"))
            else:
                plan.append(ExecutionPlanStep(label=f"run-{script_name}", kind="system", command=f"npm run {script_name}"))
        else:
            node_entrypoint = next(
                (entry for entry in summary.entrypoints if entry.endswith((".js", ".ts"))),
                None,
            )
            if node_entrypoint:
                plan.append(
                    ExecutionPlanStep(
                        label="run-node-entrypoint",
                        kind="system",
                        command=f"node {node_entrypoint}",
                    )
                )

    return dedupe_plan(plan)


def dedupe_plan(plan: list[ExecutionPlanStep]) -> list[ExecutionPlanStep]:
    seen: set[str] = set()
    result: list[ExecutionPlanStep] = []
    for step in plan:
        if step.command in seen:
            continue
        seen.add(step.command)
        result.append(step)
    return result


def extract_commands_from_steps(steps: str) -> list[str]:
    commands: list[str] = []
    for raw_line in steps.splitlines():
        line = raw_line.strip()
        line = line.lstrip("-*").strip()
        if line.startswith("$"):
            line = line[1:].strip()
        if not line:
            continue
        lowered = line.lower()
        if lowered.startswith(ALLOWED_PREFIXES):
            commands.append(line)
    return commands[:3]


def execute_plan(repo_path: Path, plan: list[ExecutionPlanStep], timeout_seconds: int = 180) -> list[ExecutionRecord]:
    records: list[ExecutionRecord] = []
    for step in plan:
        started_at = utc_now_iso()
        try:
            result = subprocess.run(
                step.command,
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=True,
                timeout=timeout_seconds,
            )
            record = ExecutionRecord(
                label=step.label,
                command=step.command,
                cwd=str(repo_path),
                started_at=started_at,
                finished_at=utc_now_iso(),
                returncode=result.returncode,
                stdout=result.stdout or "",
                stderr=result.stderr or "",
            )
        except subprocess.TimeoutExpired as error:
            record = ExecutionRecord(
                label=step.label,
                command=step.command,
                cwd=str(repo_path),
                started_at=started_at,
                finished_at=utc_now_iso(),
                returncode=-1,
                stdout=(error.stdout or ""),
                stderr=(error.stderr or ""),
                timed_out=True,
            )
        records.append(record)

        if should_stop_after(record):
            break

    return records


def should_stop_after(record: ExecutionRecord) -> bool:
    if record.timed_out:
        return True
    if record.label.startswith("user-step-") and record.returncode != 0:
        return True
    if record.label.startswith("install-") and record.returncode != 0:
        return True
    return False
