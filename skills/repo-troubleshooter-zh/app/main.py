from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.intake import load_text
from app.pipeline import run_analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a real repository and a real error log, then produce a troubleshooting report."
    )
    parser.add_argument("--repo", required=True, help="Git URL or local repository path")
    parser.add_argument("--branch", help="Git branch to clone")
    parser.add_argument("--error-log", help="Inline error log text")
    parser.add_argument("--error-file", help="Path to a text file containing the error log")
    parser.add_argument("--steps", help="Inline reproduction steps")
    parser.add_argument("--steps-file", help="Path to a text file containing reproduction steps")
    parser.add_argument("--runs-dir", default="runs", help="Directory where task artifacts are stored")
    parser.add_argument("--timeout", type=int, default=180, help="Command timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Print unified JSON output to stdout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        error_log = load_text(args.error_log, args.error_file)
        steps = load_text(args.steps, args.steps_file)
        result = run_analysis(
            repo=args.repo,
            error_log=error_log,
            steps=steps,
            branch=args.branch,
            runs_dir=args.runs_dir,
            timeout_seconds=args.timeout,
        )

        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(f"Task ID: {result.task.task_id}")
            print(f"Repository path: {result.summary.repo_path}")
            print(f"Report written to: {result.report_path}")
        return 0
    except Exception as error:
        print(f"Fatal error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
