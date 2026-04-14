from __future__ import annotations

import json
from pathlib import Path

from app.models import Diagnosis, ExecutionPlanStep, ExecutionRecord, RepositorySummary, TaskInput


def write_artifacts(
    task_dir: Path,
    task: TaskInput,
    summary: RepositorySummary,
    executions: list[ExecutionRecord],
    diagnosis: Diagnosis,
    execution_plan: list[ExecutionPlanStep],
) -> Path:
    task_dir.mkdir(parents=True, exist_ok=True)

    write_json(task_dir / "input.json", task.to_dict())
    write_json(task_dir / "repo_summary.json", summary.to_dict())
    write_json(task_dir / "executions.json", [record.to_dict() for record in executions])
    write_json(task_dir / "diagnosis.json", diagnosis.to_dict())
    write_json(
        task_dir / "result.json",
        build_result_payload(task, summary, executions, diagnosis, task_dir, execution_plan),
    )

    report_path = task_dir / "final_report.md"
    report_path.write_text(render_report(task, summary, executions, diagnosis, execution_plan), encoding="utf-8")
    return report_path


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_result_payload(
    task: TaskInput,
    summary: RepositorySummary,
    executions: list[ExecutionRecord],
    diagnosis: Diagnosis,
    task_dir: Path,
    execution_plan: list[ExecutionPlanStep],
) -> dict:
    return {
        "task_id": task.task_id,
        "repo": task.repo,
        "branch": task.branch,
        "task_dir": str(task_dir),
        "tech_stack": summary.tech_stack,
        "package_manager": summary.package_manager,
        "error_type": diagnosis.error_type,
        "error_summary": diagnosis.summary,
        "preflight_checks": summary.preflight_checks,
        "dependency_files": summary.dependency_files,
        "entrypoints": summary.entrypoints,
        "related_files": diagnosis.related_files,
        "execution_plan": [
            step.to_dict()
            for step in execution_plan
        ],
        "executions": [record.to_dict() for record in executions],
        "root_causes": diagnosis.root_causes,
        "fix_suggestions": diagnosis.fix_suggestions,
        "verify_steps": diagnosis.verify_steps,
    }


def render_report(
    task: TaskInput,
    summary: RepositorySummary,
    executions: list[ExecutionRecord],
    diagnosis: Diagnosis,
    execution_plan: list[ExecutionPlanStep],
) -> str:
    execution_section = render_executions(executions)
    execution_plan_section = render_execution_plan(execution_plan)
    evidence = "\n".join(f"- {item}" for item in diagnosis.evidence) or "- 无"
    causes = "\n".join(f"- {item}" for item in diagnosis.root_causes) or "- 无"
    suggestions = "\n".join(f"- {item}" for item in diagnosis.fix_suggestions) or "- 无"
    verify_steps = "\n".join(f"- {item}" for item in diagnosis.verify_steps) or "- 无"
    related_files = "\n".join(f"- `{item}`" for item in diagnosis.related_files) or "- 无"
    dependency_files = "\n".join(f"- `{item}`" for item in summary.dependency_files) or "- 无"
    config_files = "\n".join(f"- `{item}`" for item in summary.config_files) or "- 无"
    entrypoints = "\n".join(f"- `{item}`" for item in summary.entrypoints) or "- 无"
    preflight_checks = "\n".join(f"- {item}" for item in summary.preflight_checks) or "- 无"

    return f"""# 排障报告

## 任务信息

- 任务 ID: `{task.task_id}`
- 仓库来源: `{task.repo}`
- 分支: `{task.branch or 'default'}`

## 原始报错

```text
{task.error_log}
```

## 用户触发步骤

```text
{task.steps}
```

## 报错解释

{diagnosis.summary}

## 仓库摘要

- 技术栈: `{summary.tech_stack}`
- 包管理器: `{summary.package_manager or 'unknown'}`
- 仓库路径: `{summary.repo_path}`

### 依赖文件

{dependency_files}

### 配置文件

{config_files}

### 入口信息

{entrypoints}

### 相关文件

{related_files}

### 前置检查

{preflight_checks}

## 执行计划

{execution_plan_section}

## 真实执行结果

{execution_section}

## 诊断依据

{evidence}

## 高概率根因

{causes}

## 修复建议

{suggestions}

## 验证步骤

{verify_steps}
"""


def render_executions(executions: list[ExecutionRecord]) -> str:
    if not executions:
        return "未执行任何命令。"

    sections: list[str] = []
    for record in executions:
        status = "timeout" if record.timed_out else f"exit={record.returncode}"
        sections.append(
            f"""### {record.label}

- 命令: `{record.command}`
- 目录: `{record.cwd}`
- 结果: `{status}`

#### stdout

```text
{trim_text(record.stdout)}
```

#### stderr

```text
{trim_text(record.stderr)}
```
"""
        )
    return "\n".join(sections)


def render_execution_plan(execution_plan: list[ExecutionPlanStep]) -> str:
    if not execution_plan:
        return "未生成执行计划。"

    groups = {
        "user": "用户原始步骤",
        "prerequisite": "前置安装步骤",
        "system": "系统补充步骤",
    }
    sections: list[str] = []
    for kind, title in groups.items():
        items = [step for step in execution_plan if step.kind == kind]
        if not items:
            continue
        body = "\n".join(f"- `{step.command}`" for step in items)
        sections.append(f"### {title}\n\n{body}")
    return "\n\n".join(sections)


def trim_text(text: str, limit: int = 4000) -> str:
    text = text.strip()
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]..."
