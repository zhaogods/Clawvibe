from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

from app.models import RepositorySummary, TaskInput

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "dist",
    "build",
    "runs",
    "tmp",
}


def is_remote_repo(repo: str) -> bool:
    repo = repo.strip()
    return repo.startswith(("http://", "https://", "git@")) or repo.endswith(".git")


def prepare_repository(task: TaskInput, task_dir: Path) -> tuple[Path, str]:
    repo_target = task_dir / "repo"
    if is_remote_repo(task.repo):
        command = ["git", "clone", "--depth", "1"]
        if task.branch:
            command.extend(["--branch", task.branch])
        command.extend([task.repo, str(repo_target)])
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                "Failed to clone repository.\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        write_source_metadata(task_dir, {"source_kind": "remote"})
        return repo_target, "remote"

    local_repo = Path(task.repo).expanduser().resolve()
    if not local_repo.exists():
        raise FileNotFoundError(f"Repository path does not exist: {local_repo}")
    if local_repo.is_file():
        raise ValueError(f"Repository path must be a directory: {local_repo}")
    write_source_metadata(task_dir, inspect_local_source_state(local_repo))
    copy_local_repository(local_repo, repo_target)
    return repo_target, "local_snapshot"


def scan_repository(repo_path: Path, error_log: str, source_kind: str, steps: str = "") -> RepositorySummary:
    files = list(iter_files(repo_path))
    package_json_files = find_files_by_name(files, "package.json")
    pyproject_files = find_files_by_name(files, "pyproject.toml")
    requirements_files = find_files_by_name(files, "requirements.txt")
    poetry_lock_files = find_files_by_name(files, "poetry.lock")
    package_lock_files = find_files_by_name(files, "package-lock.json")
    yarn_lock_files = find_files_by_name(files, "yarn.lock")
    pnpm_lock_files = find_files_by_name(files, "pnpm-lock.yaml")

    package_json = choose_primary_file(repo_path, package_json_files)
    pyproject = choose_primary_file(repo_path, pyproject_files)
    requirements = choose_primary_file(repo_path, requirements_files)
    poetry_lock = choose_primary_file(repo_path, poetry_lock_files)
    package_lock = choose_primary_file(repo_path, package_lock_files)
    yarn_lock = choose_primary_file(repo_path, yarn_lock_files)
    pnpm_lock = choose_primary_file(repo_path, pnpm_lock_files)

    related_files = detect_related_files(repo_path, files, error_log, steps, package_json_files)
    context_dir = infer_context_dir(related_files)
    tech_stack = detect_tech_stack(package_json_files, pyproject_files, requirements_files, steps, related_files)
    package_manager = detect_package_manager(
        tech_stack,
        package_json_files,
        requirements_files,
        pyproject_files,
        poetry_lock_files,
        package_lock_files,
        yarn_lock_files,
        pnpm_lock_files,
    )
    dependency_files = rank_paths_for_context(
        repo_path,
        [
            *requirements_files,
            *pyproject_files,
            *poetry_lock_files,
            *package_json_files,
            *package_lock_files,
            *yarn_lock_files,
            *pnpm_lock_files,
        ],
        context_dir,
    )
    config_files = find_config_files(repo_path, files, context_dir)
    entrypoints = detect_entrypoints(repo_path, files, package_json_files, pyproject_files, tech_stack, context_dir)
    test_commands = detect_test_commands(package_json, tech_stack, package_manager)
    top_level_dirs = sorted([p.name for p in repo_path.iterdir() if p.is_dir() and p.name not in SKIP_DIRS])[:20]
    readme_excerpt = read_readme_excerpt(repo_path)
    source_meta = load_source_metadata(repo_path)
    preflight_checks = build_preflight_checks(tech_stack, package_manager, source_meta)
    scan_notes = build_scan_notes(tech_stack, package_manager, entrypoints, related_files, context_dir)

    return RepositorySummary(
        source_kind=source_kind,
        repo_path=str(repo_path),
        repo_name=repo_path.name,
        tech_stack=tech_stack,
        package_manager=package_manager,
        dependency_files=dependency_files,
        config_files=config_files,
        entrypoints=entrypoints,
        test_commands=test_commands,
        related_files=related_files,
        top_level_dirs=top_level_dirs,
        readme_excerpt=readme_excerpt,
        preflight_checks=preflight_checks,
        scan_notes=scan_notes,
    )


def iter_files(repo_path: Path):
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)
        for file_name in files:
            yield root_path / file_name


def copy_local_repository(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "node_modules",
            "runs",
            "tmp",
        ),
    )


def inspect_local_source_state(local_repo: Path) -> dict:
    has_root_node_modules = (local_repo / "node_modules").exists()
    has_root_venv = any((local_repo / name).exists() for name in (".venv", "venv"))
    return {
        "source_kind": "local",
        "source_repo_path": str(local_repo),
        "has_root_node_modules": has_root_node_modules,
        "has_root_python_env": has_root_venv,
    }


def write_source_metadata(task_dir: Path, payload: dict) -> None:
    (task_dir / "source_meta.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_source_metadata(repo_path: Path) -> dict:
    meta_path = repo_path.parent / "source_meta.json"
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def build_preflight_checks(tech_stack: str, package_manager: str | None, source_meta: dict) -> list[str]:
    checks: list[str] = []
    if source_meta.get("source_kind") == "local":
        checks.append("当前任务在本地仓库快照副本中执行，原仓库文件不会被修改。")

    if tech_stack in {"node", "hybrid"}:
        if source_meta.get("has_root_node_modules"):
            checks.append("源仓库根目录已检测到 `node_modules`。")
        else:
            runner = package_manager or "npm"
            checks.append(f"源仓库根目录未检测到 `node_modules`，首次运行前应优先执行 `{runner} install`。")

    if tech_stack in {"python", "hybrid"}:
        if source_meta.get("has_root_python_env"):
            checks.append("源仓库根目录已检测到 Python 虚拟环境目录。")
        else:
            checks.append("源仓库根目录未检测到 Python 虚拟环境目录，运行前应确认解释器和依赖环境已准备好。")

    return checks


def detect_tech_stack(
    package_json: list[Path],
    pyproject: list[Path],
    requirements: list[Path],
    steps: str,
    related_files: list[str],
) -> str:
    step_stack = infer_stack_from_steps(steps)
    if step_stack:
        return step_stack

    related_text = " ".join(related_files).lower()
    if ".py" in related_text:
        return "python"
    if any(token in related_text for token in [".js", ".ts", ".tsx", ".jsx"]):
        return "node"

    has_node = bool(package_json)
    has_python = bool(pyproject) or bool(requirements)
    if has_node and has_python:
        return "hybrid"
    if has_node:
        return "node"
    if has_python:
        return "python"
    return "unknown"


def detect_package_manager(
    tech_stack: str,
    package_json: list[Path],
    requirements: list[Path],
    pyproject: list[Path],
    poetry_lock: list[Path],
    package_lock: list[Path],
    yarn_lock: list[Path],
    pnpm_lock: list[Path],
) -> str | None:
    if tech_stack in {"node", "hybrid"}:
        declared = detect_declared_node_package_manager(package_json)
        if declared:
            return declared
        if pnpm_lock:
            return "pnpm"
        if yarn_lock:
            return "yarn"
        if package_json:
            return "npm"
    if tech_stack in {"python", "hybrid"}:
        if poetry_lock and shutil.which("poetry"):
            return "poetry"
        if pyproject or requirements:
            return "pip"
    return None


def detect_declared_node_package_manager(package_json_files: list[Path]) -> str | None:
    for package_json in package_json_files[:3]:
        try:
            package_data = json.loads(package_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        package_manager = str(package_data.get("packageManager", "")).lower()
        if package_manager.startswith("pnpm@"):
            return "pnpm"
        if package_manager.startswith("yarn@"):
            return "yarn"
        if package_manager.startswith("npm@"):
            return "npm"
    return None


def find_config_files(repo_path: Path, files: list[Path], context_dir: str | None) -> list[str]:
    names = {
        ".env",
        ".env.example",
        ".env.sample",
        "config.yaml",
        "config.yml",
        "config.json",
        "settings.py",
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
    }
    candidates = [path for path in files if path.name in names]
    return rank_paths_for_context(repo_path, candidates, context_dir)[:20]


def detect_entrypoints(
    repo_path: Path,
    files: list[Path],
    package_json_files: list[Path],
    pyproject_files: list[Path],
    tech_stack: str,
    context_dir: str | None,
) -> list[str]:
    entrypoints: list[str] = []
    common_python = ["main.py", "app.py", "manage.py", "run.py", "server.py", "start.py", "web_ui.py", "app/main.py", "run_openclaw_deliverable.py"]
    common_node = ["server.js", "app.js", "index.js", "src/index.js", "src/main.js"]

    for package_json in prioritize_paths(package_json_files, repo_path, context_dir)[:3]:
        try:
            package_data = json.loads(package_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            package_data = {}
        scripts = package_data.get("scripts", {})
        for key in ("dev", "start", "serve", "build"):
            if key in scripts:
                rel_parent = package_json.parent.relative_to(repo_path)
                prefix = "" if str(rel_parent) == "." else f"{rel_parent}\\"
                entrypoints.append(f"{prefix}script:{key}")

    for pyproject in prioritize_paths(pyproject_files, repo_path, context_dir)[:3]:
        try:
            pyproject_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError:
            pyproject_data = {}
        project = pyproject_data.get("project", {})
        scripts = project.get("scripts", {})
        for name in scripts.keys():
            rel_parent = pyproject.parent.relative_to(repo_path)
            prefix = "" if str(rel_parent) == "." else f"{rel_parent}\\"
            entrypoints.append(f"{prefix}script:{name}")

    for candidate in common_python + common_node:
        if (repo_path / candidate).exists():
            entrypoints.append(candidate)

    for path in files:
        rel = str(path.relative_to(repo_path))
        if path.suffix == ".py" and path.name.startswith(("run_", "start_", "main_", "cli")):
            entrypoints.append(rel)

    ranked = rank_string_paths(entrypoints, context_dir)
    return list(dict.fromkeys(ranked))


def detect_test_commands(package_json: Path | None, tech_stack: str, package_manager: str | None) -> list[str]:
    commands: list[str] = []
    if package_json and package_json.exists():
        try:
            package_data = json.loads(package_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            package_data = {}
        scripts = package_data.get("scripts", {})
        if "test" in scripts:
            runner = package_manager or "npm"
            commands.append(f"{runner} test" if runner != "npm" else "npm test")
    if tech_stack in {"python", "hybrid"}:
        commands.append("python -m pytest")
    return commands


def detect_related_files(
    repo_path: Path,
    files: list[Path],
    error_log: str,
    steps: str,
    package_json_files: list[Path],
) -> list[str]:
    matches: list[str] = []
    seen: set[str] = set()

    for rel in extract_step_related_files(repo_path, files, package_json_files, steps):
        if rel not in seen:
            seen.add(rel)
            matches.append(rel)

    patterns = [
        r'File "([^"]+)"',
        r"\(([^()]+\.(?:py|js|ts|tsx|jsx)):\d+:\d+\)",
        r"([A-Za-z0-9_./\\-]+\.(?:py|js|ts|tsx|jsx)):\d+",
        r"path:\s*'([^']+)'",
        r"open '([^']+)'",
    ]

    for pattern in patterns:
        for raw_match in re.findall(pattern, error_log):
            resolved = resolve_error_path(repo_path, raw_match)
            if resolved and resolved not in seen:
                seen.add(resolved)
                matches.append(resolved)
                continue

            match = raw_match.replace("\\", "/").split("/")[-1]
            for path in files:
                if path.name == match:
                    rel = str(path.relative_to(repo_path))
                    if rel not in seen:
                        seen.add(rel)
                        matches.append(rel)

    keywords = extract_keywords(error_log)
    for path in files:
        rel = str(path.relative_to(repo_path))
        lowered = rel.lower()
        if not is_code_or_config_file(path):
            continue
        if any(keyword in lowered for keyword in keywords):
            if rel not in seen:
                seen.add(rel)
                matches.append(rel)
        if len(matches) >= 12:
            break

    return matches[:12]


def extract_step_related_files(
    repo_path: Path,
    files: list[Path],
    package_json_files: list[Path],
    steps: str,
) -> list[str]:
    matches: list[str] = []
    file_map = {str(path.relative_to(repo_path)).replace("/", "\\"): path for path in files}

    for raw_line in steps.splitlines():
        line = raw_line.strip().lstrip("-*").strip()
        if not line:
            continue
        if line.startswith("$"):
            line = line[1:].strip()

        script_path = extract_script_path_from_command(line)
        if script_path:
            rel = normalize_repo_relative_path(repo_path, script_path)
            if rel:
                matches.append(rel)

        npm_script = extract_npm_script_name(line)
        if npm_script:
            for package_json in package_json_files[:3]:
                try:
                    package_data = json.loads(package_json.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                scripts = package_data.get("scripts", {})
                command = scripts.get(npm_script)
                if not command:
                    continue
                matches.append(str(package_json.relative_to(repo_path)))
                for script_target in extract_script_targets(command):
                    rel = normalize_repo_relative_path(repo_path, str(package_json.parent / script_target))
                    if rel:
                        matches.append(rel)
                break

    return list(dict.fromkeys(matches))


def extract_script_path_from_command(command: str) -> str | None:
    patterns = [
        r"python(?:3)?\s+(?:-B\s+)?([A-Za-z0-9_./\\-]+\.py)",
        r"node\s+([A-Za-z0-9_./\\-]+\.(?:js|mjs|cjs|ts))",
    ]
    for pattern in patterns:
        match = re.search(pattern, command)
        if match:
            return match.group(1)
    return None


def extract_npm_script_name(command: str) -> str | None:
    patterns = [
        r"npm\s+run\s+([A-Za-z0-9:_-]+)",
        r"pnpm\s+([A-Za-z0-9:_-]+)",
        r"yarn\s+([A-Za-z0-9:_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, command)
        if match:
            return match.group(1)
    return None


def extract_script_targets(command: str) -> list[str]:
    targets = re.findall(r"([A-Za-z0-9_./\\-]+\.(?:ts|js|mjs|cjs|py))", command)
    return list(dict.fromkeys(targets))


def normalize_repo_relative_path(repo_path: Path, raw_path: str) -> str | None:
    candidate = Path(raw_path.replace("/", "\\"))
    if not candidate.is_absolute():
        candidate = (repo_path / candidate).resolve()
    try:
        repo_resolved = repo_path.resolve()
        if str(candidate).lower().startswith(str(repo_resolved).lower()):
            return str(candidate.relative_to(repo_resolved))
    except OSError:
        return None
    return None


def is_code_or_config_file(path: Path) -> bool:
    relevant_suffixes = {
        ".py",
        ".js",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".jsx",
        ".json",
        ".toml",
        ".yaml",
        ".yml",
    }
    if path.suffix.lower() in relevant_suffixes:
        return True
    return path.name in {
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "Dockerfile",
    }


def resolve_error_path(repo_path: Path, raw_match: str) -> str | None:
    candidate = Path(raw_match.strip().strip("'\""))
    try:
        if candidate.is_absolute():
            resolved = candidate.resolve()
            repo_resolved = repo_path.resolve()
            if str(resolved).lower().startswith(str(repo_resolved).lower()):
                return str(resolved.relative_to(repo_resolved))
    except OSError:
        return None
    return None


def extract_keywords(error_log: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", error_log)
    stopwords = {
        "error",
        "exception",
        "traceback",
        "module",
        "cannot",
        "failed",
        "file",
        "line",
        "node",
        "python",
    }
    keywords: list[str] = []
    for token in tokens:
        token_lower = token.lower()
        if token_lower in stopwords:
            continue
        if token_lower not in keywords:
            keywords.append(token_lower)
    return keywords[:12]


def read_readme_excerpt(repo_path: Path) -> str:
    readmes = []
    for path in iter_files(repo_path):
        if path.name in {"README.md", "README.rst", "README.txt"}:
            readmes.append(path)
    readmes.sort(key=lambda p: len(p.relative_to(repo_path).parts))
    for candidate in readmes[:3]:
        content = candidate.read_text(encoding="utf-8", errors="ignore").splitlines()
        excerpt = "\n".join(content[:20]).strip()
        if excerpt:
            return excerpt
    return ""


def find_files_by_name(files: list[Path], name: str) -> list[Path]:
    return sorted([path for path in files if path.name == name], key=lambda p: len(p.parts))


def choose_primary_file(repo_path: Path, files: list[Path]) -> Path | None:
    if not files:
        return None
    files = sorted(files, key=lambda p: len(p.relative_to(repo_path).parts))
    return files[0]


def infer_stack_from_steps(steps: str) -> str | None:
    lowered = steps.lower()
    if any(token in lowered for token in ["python ", "python3 ", "py "]):
        return "python"
    if any(token in lowered for token in ["npm ", "pnpm ", "yarn ", "node "]):
        return "node"
    return None


def infer_context_dir(related_files: list[str]) -> str | None:
    counts: dict[str, int] = {}
    for rel in related_files:
        parts = Path(rel).parts
        if len(parts) > 1:
            top = parts[0]
            counts[top] = counts.get(top, 0) + 1
    if not counts:
        return None
    top, score = max(counts.items(), key=lambda item: item[1])
    if score >= 2:
        return top
    return None


def rank_paths_for_context(repo_path: Path, paths: list[Path], context_dir: str | None) -> list[str]:
    prioritized = prioritize_paths(paths, repo_path, context_dir)
    return [str(path.relative_to(repo_path)) for path in prioritized]


def prioritize_paths(paths: list[Path], repo_path: Path, context_dir: str | None) -> list[Path]:
    def sort_key(path: Path):
        rel = str(path.relative_to(repo_path))
        in_context = 0 if context_dir and rel.startswith(f"{context_dir}\\") else 1
        depth = len(path.relative_to(repo_path).parts)
        return (in_context, depth, rel.lower())

    return sorted(paths, key=sort_key)


def rank_string_paths(paths: list[str], context_dir: str | None) -> list[str]:
    def sort_key(rel: str):
        in_context = 0 if context_dir and rel.startswith(f"{context_dir}\\") else 1
        depth = len(Path(rel).parts)
        return (in_context, depth, rel.lower())

    return sorted(paths, key=sort_key)


def build_scan_notes(
    tech_stack: str,
    package_manager: str | None,
    entrypoints: list[str],
    related_files: list[str],
    context_dir: str | None,
) -> list[str]:
    notes = [f"Detected tech stack: {tech_stack}."]
    if package_manager:
        notes.append(f"Selected package manager: {package_manager}.")
    if context_dir:
        notes.append(f"Detected task context directory: {context_dir}.")
    if entrypoints:
        notes.append(f"Detected entrypoints: {', '.join(entrypoints[:4])}.")
    if related_files:
        notes.append(f"Matched related files from the error log: {', '.join(related_files[:6])}.")
    return notes
