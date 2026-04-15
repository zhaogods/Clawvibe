from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()


def find_runtime_root() -> Path:
    candidates = [
        SCRIPT_PATH.parents[1],  # skills/repo-troubleshooter-zh
        SCRIPT_PATH.parents[3],  # repository root when running inside this repo
    ]
    for candidate in candidates:
        if (candidate / "app" / "__init__.py").exists():
            return candidate
    raise RuntimeError(
        "Cannot locate runtime package 'app'. "
        "Expected either a bundled app/ directory in the skill root or a repository root containing app/."
    )


REPO_ROOT = find_runtime_root()
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
        description="使用 repo-troubleshooter-zh 技能分析真实仓库和真实错误日志。"
    )
    parser.add_argument("--repo", required=True, help="本地仓库路径或远程 Git URL")
    parser.add_argument("--branch", help="Git 分支")
    parser.add_argument("--error-log", help="直接传入错误日志文本")
    parser.add_argument("--error-file", help="错误日志文件路径")
    parser.add_argument("--steps", help="直接传入触发步骤")
    parser.add_argument("--steps-file", help="触发步骤文件路径")
    parser.add_argument("--runs-dir", default=str(REPO_ROOT / "runs"), help="运行产物输出目录")
    parser.add_argument("--timeout", type=int, default=180, help="单条命令超时时间（秒）")
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
