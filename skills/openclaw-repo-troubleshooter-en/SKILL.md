---
name: openclaw-repo-troubleshooter-en
description: Analyze real repository errors with real command execution and structured troubleshooting output. Use when Codex needs to inspect a local or cloned repository, replay a user-provided failing command, capture real stdout/stderr, classify the failure, and produce Markdown/JSON troubleshooting results without modifying the source repository.
---

# OpenClaw Repo Troubleshooter

## Overview

Use this skill to run the repository troubleshooter in this project as a reusable English skill package.
It is designed for real debugging work: real repo input, real logs, real commands, real outputs.

## Workflow

1. Gather three required inputs:
   - repository path or Git URL
   - raw error log
   - user trigger steps

2. Run one of the packaged entry scripts:

```powershell
python skills/openclaw-repo-troubleshooter-en/scripts/analyze_repo.py --repo <repo> --error-file <error.txt> --steps "<command>"
```

- Windows PowerShell:
  `.\skills\openclaw-repo-troubleshooter-en\scripts\run-skill.ps1 --repo <repo> --error-file <error.txt> --steps "<command>"`
- Windows cmd:
  `skills\openclaw-repo-troubleshooter-en\scripts\run-skill.cmd --repo <repo> --error-file <error.txt> --steps "<command>"`
- Linux / macOS:
  `sh skills/openclaw-repo-troubleshooter-en/scripts/run-skill.sh --repo <repo> --error-file <error.txt> --steps "<command>"`

3. Read the emitted result files from the run directory:
   - `result.json`
   - `final_report.md`

4. Use the structured result to:
   - explain the error
   - inspect preflight checks
   - review real execution results
   - inspect root causes, fix suggestions, and verify steps

## Rules

- Use real repositories only.
- Use real error logs only.
- Use real command execution only.
- Do not fabricate results.
- Do not modify the source repository directly; the wrapped app runs against a local snapshot copy.

## Inputs

- `--repo`
  Local repository path or Git URL
- `--error-log` or `--error-file`
  Raw error text
- `--steps` or `--steps-file`
  Original user trigger steps
- `--branch`
  Optional remote branch
- `--runs-dir`
  Optional custom output root

## Outputs

Primary outputs:

- `result.json`
- `final_report.md`

See:
- [references/output-contract.md](references/output-contract.md)
- [references/project-layout.md](references/project-layout.md)
- [references/invocation.md](references/invocation.md)

## Entry Scripts

- `scripts/analyze_repo.py`
  Python entrypoint that wraps the unified pipeline
- `scripts/run-skill.ps1`
  Windows PowerShell launcher
- `scripts/run-skill.cmd`
  Windows cmd launcher
- `scripts/run-skill.sh`
  Linux/macOS shell launcher

## Notes

- For local repositories, the wrapped app snapshots the source repository into a run directory before executing commands.
- The skill is currently strongest on Python and Node repositories.
- The skill emits both human-readable and machine-readable outputs from the same run.

