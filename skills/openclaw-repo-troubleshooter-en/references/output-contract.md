# Output Contract

The skill writes a task directory under the provided `runs/` root.

Each run emits:

- `input.json`
- `repo_summary.json`
- `executions.json`
- `diagnosis.json`
- `result.json`
- `final_report.md`

## `result.json`

Top-level fields:

- `task`
- `summary`
- `executions`
- `diagnosis`
- `task_dir`
- `report_path`
- `execution_plan`

## `execution_plan.kind`

- `user`
- `prerequisite`
- `system`

## Report sections

`final_report.md` contains:

1. Task information
2. Original error
3. User trigger steps
4. Error explanation
5. Repository summary
6. Preflight checks
7. Execution plan
8. Real execution results
9. Diagnosis evidence
10. Root causes
11. Fix suggestions
12. Verify steps

