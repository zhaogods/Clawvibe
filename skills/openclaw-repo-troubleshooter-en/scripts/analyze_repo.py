from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.intake import load_text
from app.pipeline import run_analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the OpenClaw repo troubleshooter skill against a real repository and error log."
    )
    parser.add_argument("--repo", required=True, help="Local repository path or remote Git URL")
    parser.add_argument("--branch", help="Git branch to clone")
    parser.add_argument("--error-log", help="Inline error log text")
    parser.add_argument("--error-file", help="Path to a text file containing the error log")
    parser.add_argument("--steps", help="Inline reproduction steps")
    parser.add_argument("--steps-file", help="Path to a text file containing reproduction steps")
    parser.add_argument("--runs-dir", default=str(REPO_ROOT / "runs"), help="Directory where troubleshooting artifacts are written")
    parser.add_argument("--timeout", type=int, default=180, help="Per-command timeout in seconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    error_log = load_text(args.error_log, args.error_file)
    steps = load_text(args.steps, args.steps_file)
    result = run_analysis(
        repo=args.repo,
        branch=args.branch,
        error_log=error_log,
        steps=steps,
        runs_dir=args.runs_dir,
        timeout_seconds=args.timeout,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

