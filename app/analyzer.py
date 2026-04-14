from __future__ import annotations

import re
from pathlib import Path

from app.models import Diagnosis, ExecutionRecord, RepositorySummary, TaskInput


def diagnose(task: TaskInput, summary: RepositorySummary, executions: list[ExecutionRecord]) -> Diagnosis:
    execution_text = "\n".join(
        [record.stderr or record.stdout for record in executions if (record.stderr or record.stdout)]
    )
    combined_text = "\n".join([task.error_log, execution_text]).strip()

    error_type = classify_error(combined_text)
    summary_text = build_human_summary(error_type, combined_text)
    evidence = collect_evidence(task, summary, executions, combined_text)
    root_causes = infer_root_causes(error_type, summary, combined_text, executions)
    fix_suggestions = suggest_fixes(error_type, summary, combined_text)
    verify_steps = build_verify_steps(summary, task.steps, error_type)

    return Diagnosis(
        error_type=error_type,
        summary=summary_text,
        evidence=evidence,
        root_causes=root_causes,
        related_files=summary.related_files,
        fix_suggestions=fix_suggestions,
        verify_steps=verify_steps,
    )


def classify_error(text: str) -> str:
    lowered = text.lower()
    if "the following arguments are required" in lowered or lowered.startswith("usage:"):
        return "cli_input_error"
    if "eoferror: eof when reading a line" in lowered:
        return "interactive_input_error"
    if "is not recognized as an internal or external command" in lowered or "command not found" in lowered:
        return "tool_missing_error"
    if any(token in lowered for token in ["modulenotfounderror", "no module named", "cannot find module"]):
        return "dependency_or_import_error"
    if any(token in lowered for token in ["filenotfounderror", "enoent", "no such file or directory"]):
        return "config_or_path_error"
    if any(token in lowered for token in ["permission denied", "eacces", "eperm", "operation not permitted"]):
        return "permission_error"
    if any(token in lowered for token in ["syntaxerror", "unexpected token"]):
        return "syntax_error"
    if any(token in lowered for token in ["address already in use", "eaddrinuse"]):
        return "port_conflict"
    if any(token in lowered for token in ["connection refused", "econnrefused"]):
        return "service_dependency_error"
    if "traceback" in lowered or "error" in lowered:
        return "runtime_error"
    return "unknown_error"


def build_human_summary(error_type: str, text: str) -> str:
    summaries = {
        "cli_input_error": "报错不是业务逻辑失败，而是命令行参数不完整，程序在参数校验阶段直接退出。",
        "interactive_input_error": "报错不是业务逻辑崩溃，而是程序需要交互输入，但当前执行环境没有提供输入流。",
        "tool_missing_error": "报错不是业务逻辑错误，而是当前运行依赖的命令行工具不存在，通常意味着依赖还没安装完整。",
        "dependency_or_import_error": "报错更像依赖缺失或导入路径错误，系统需要先确认依赖是否安装以及入口路径是否正确。",
        "config_or_path_error": "报错更像配置文件缺失、环境变量缺失或路径引用错误。",
        "permission_error": "报错更像权限不足，问题可能不在业务逻辑，而在执行环境或文件访问权限。",
        "syntax_error": "报错发生在代码解释阶段，优先检查语法错误或不兼容写法。",
        "port_conflict": "服务启动时端口被占用，优先确认当前端口是否已被其他进程使用。",
        "service_dependency_error": "当前服务依赖的外部服务不可达，问题可能在数据库、缓存或上游服务。",
        "runtime_error": "报错发生在运行阶段，需要结合真实执行日志和仓库上下文做进一步定位。",
        "unknown_error": "当前日志不足以直接判断错误类型，需要补充执行日志或更完整的堆栈信息。",
    }
    return summaries[error_type]


def collect_evidence(
    task: TaskInput,
    summary: RepositorySummary,
    executions: list[ExecutionRecord],
    combined_text: str,
) -> list[str]:
    evidence: list[str] = []

    if summary.tech_stack != "unknown":
        evidence.append(f"仓库识别结果为 {summary.tech_stack}。")
    for check in summary.preflight_checks[:2]:
        evidence.append(check)
    if summary.related_files:
        evidence.append(f"错误日志关联到文件: {', '.join(summary.related_files[:5])}。")
    for record in executions:
        if record.returncode != 0 or record.timed_out:
            evidence.append(
                f"命令 `{record.command}` 实际执行失败，退出码为 {record.returncode}。"
            )
            excerpt = extract_first_error_line(record.stderr or record.stdout)
            if excerpt:
                evidence.append(f"失败日志首条关键信息: {excerpt}")
            break
    if not evidence:
        evidence.append("当前结论主要来自用户提供的原始报错日志。")
    return evidence


def infer_root_causes(
    error_type: str,
    summary: RepositorySummary,
    text: str,
    executions: list[ExecutionRecord],
) -> list[str]:
    causes: list[str] = []
    missing_module = extract_missing_module(text)
    missing_path = extract_missing_path(text)
    permission_path = extract_permission_path(text)

    if error_type == "dependency_or_import_error":
        if missing_module:
            causes.append(f"缺少模块 `{missing_module}`，依赖未安装或安装环境不一致。")
            causes.append(f"模块 `{missing_module}` 的导入路径可能与当前启动方式不匹配。")
        else:
            causes.append("依赖未安装或当前解释器环境与项目要求不一致。")
            causes.append("入口脚本的导入路径与仓库目录结构不匹配。")
    elif error_type == "cli_input_error":
        causes.append("执行命令缺少必填参数，程序尚未真正进入业务逻辑。")
    elif error_type == "interactive_input_error":
        causes.append("程序运行到 `input()` 等交互逻辑时，没有拿到终端输入。")
        causes.append("当前命令适合人工交互执行，不适合直接在无输入环境中运行。")
    elif error_type == "tool_missing_error":
        causes.append("当前脚本依赖的命令行工具未安装，或没有进入项目依赖环境。")
        missing_tool = extract_missing_tool(text)
        if missing_tool:
            causes.append(f"缺少可执行工具 `{missing_tool}`，通常来自 `node_modules/.bin` 或全局环境。")
    elif error_type == "config_or_path_error":
        if missing_path:
            causes.append(f"路径 `{missing_path}` 在当前工作目录下不存在。")
        causes.append("配置文件、环境变量文件或运行所需资源文件缺失。")
    elif error_type == "permission_error":
        causes.append("执行账户无权访问文件、目录或端口。")
        if permission_path:
            causes.append(f"当前失败直接发生在路径 `{permission_path}` 的访问或写入阶段。")
    elif error_type == "syntax_error":
        causes.append("代码文件中存在语法错误或解释器版本与语法不兼容。")
    elif error_type == "port_conflict":
        causes.append("目标端口已被其他进程占用。")
    elif error_type == "service_dependency_error":
        causes.append("项目依赖的外部服务未启动或连接配置错误。")
    else:
        causes.append("需要结合更完整的执行日志进一步缩小范围。")

    if not summary.entrypoints:
        causes.append("仓库中未识别到明确入口，可能导致启动命令选择错误。")
    return causes[:5]


def suggest_fixes(error_type: str, summary: RepositorySummary, text: str) -> list[str]:
    suggestions: list[str] = []
    missing_module = extract_missing_module(text)
    permission_path = extract_permission_path(text)
    python_requirements = next((dep for dep in summary.dependency_files if dep.endswith("requirements.txt")), None)
    node_package = next((dep for dep in summary.dependency_files if dep.endswith("package.json")), None)

    if error_type == "dependency_or_import_error":
        if summary.tech_stack in {"python", "hybrid"} and python_requirements:
            suggestions.append(f"先重新执行 `python -m pip install -r \"{python_requirements}\"`，确认依赖完整安装。")
        if summary.tech_stack in {"node", "hybrid"} and node_package:
            package_dir = Path(node_package).parent
            if str(package_dir) == ".":
                suggestions.append("先重新执行 `npm install` 或对应包管理器安装命令。")
            else:
                suggestions.append(f"先在 `{package_dir}` 目录执行 `npm install` 或对应包管理器安装命令。")
        if missing_module:
            suggestions.append(f"检查仓库内是否存在 `{missing_module}` 对应模块，以及导入路径是否正确。")
    elif error_type == "cli_input_error":
        suggestions.append("补齐命令行必填参数后再执行，先确保程序能进入真实业务流程。")
    elif error_type == "interactive_input_error":
        suggestions.append("改用支持交互输入的终端环境运行，或使用仓库提供的非交互命令入口。")
        suggestions.append("优先检查 `start.py`、CLI 参数说明和 README 中给出的实际启动方式。")
    elif error_type == "tool_missing_error":
        suggestions.append("先安装项目依赖，再重新执行启动命令。")
        if summary.package_manager:
            suggestions.append(f"优先执行 `{summary.package_manager} install`，再重新运行当前脚本。")
        missing_tool = extract_missing_tool(text)
        if missing_tool:
            suggestions.append(f"检查 `{missing_tool}` 是否在 `package.json` 依赖中声明，并确认包管理器安装是否成功。")
    elif error_type == "config_or_path_error":
        suggestions.append("检查 `.env`、`.env.example`、配置文件和相对路径是否与启动目录一致。")
        if summary.config_files:
            suggestions.append(f"优先检查这些配置文件: {', '.join(summary.config_files[:5])}。")
    elif error_type == "permission_error":
        suggestions.append("检查当前执行用户是否有目标文件、目录或端口的访问权限。")
        if permission_path:
            suggestions.append(f"优先检查路径 `{permission_path}` 是否被占用、只读或被其他进程锁定。")
    elif error_type == "syntax_error":
        suggestions.append("打开报错指向的代码文件，先修正语法问题，再重新执行启动命令。")
    elif error_type == "port_conflict":
        suggestions.append("释放占用端口的进程，或修改项目配置中的监听端口。")
    elif error_type == "service_dependency_error":
        suggestions.append("确认数据库、缓存或上游服务已启动，并检查连接配置。")
    else:
        suggestions.append("先补充完整执行日志，再根据失败命令缩小排查范围。")

    if summary.related_files:
        suggestions.append(f"优先检查相关文件: {', '.join(summary.related_files[:5])}。")
    return suggestions[:6]


def build_verify_steps(summary: RepositorySummary, steps_text: str, error_type: str) -> list[str]:
    steps: list[str] = []
    original_command = extract_primary_command(steps_text)
    if summary.tech_stack in {"python", "hybrid"}:
        requirements_file = next((dep for dep in summary.dependency_files if dep.endswith("requirements.txt")), None)
        if requirements_file:
            steps.append(f"重新执行 `python -m pip install -r \"{requirements_file}\"`，确认依赖安装无报错。")
        rerun_command = original_command or next((f"python {entry}" for entry in summary.entrypoints if entry.endswith(".py")), None)
        if rerun_command:
            steps.append(f"重新执行 `{rerun_command}`，确认启动阶段不再报错。")
    if summary.tech_stack in {"node", "hybrid"}:
        runner = summary.package_manager or "npm"
        package_file = next((dep for dep in summary.dependency_files if dep.endswith("package.json")), None)
        if package_file:
            package_dir = Path(package_file).parent
            if str(package_dir) == ".":
                steps.append(f"重新执行 `{runner} install`，确认依赖安装无报错。")
            else:
                steps.append(f"在 `{package_dir}` 目录重新执行 `{runner} install`，确认依赖安装无报错。")
        rerun_command = normalize_node_command(original_command, runner)
        if not rerun_command:
            script_entry = next((entry for entry in summary.entrypoints if "script:" in entry), None)
            if script_entry:
                script_name = script_entry.split("script:", 1)[1]
                rerun_command = f"{runner} {script_name}" if runner in {"yarn", "pnpm"} else f"npm run {script_name}"
        if rerun_command:
            steps.append(f"重新执行 `{rerun_command}`，确认启动阶段不再报错。")
    if not steps:
        steps.append("修复后重新执行导致原始报错的命令，确认相同错误不再出现。")
    return steps[:5]


def extract_primary_command(steps_text: str) -> str | None:
    for raw_line in steps_text.splitlines():
        line = raw_line.strip().lstrip("-*").strip()
        if not line:
            continue
        if line.startswith("$"):
            line = line[1:].strip()
        if line:
            return line
    return None


def normalize_node_command(command: str | None, runner: str) -> str | None:
    if not command:
        return None
    lowered = command.lower()
    if lowered.startswith("npm run "):
        script = command.split(" ", 2)[2]
        return f"{runner} {script}" if runner in {"pnpm", "yarn"} else command
    if lowered.startswith("npm "):
        script = command.split(" ", 1)[1]
        return f"{runner} {script}" if runner in {"pnpm", "yarn"} else command
    if lowered.startswith(("pnpm ", "yarn ")):
        script = command.split(" ", 1)[1]
        return f"{runner} {script}" if runner in {"pnpm", "yarn"} else f"npm run {script}"
    return command


def extract_missing_module(text: str) -> str | None:
    patterns = [
        r"No module named ['\"]?([A-Za-z0-9_.-]+)['\"]?",
        r"Cannot find module ['\"]([^'\"]+)['\"]",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_missing_path(text: str) -> str | None:
    patterns = [
        r"No such file or directory: ['\"]([^'\"]+)['\"]",
        r"ENOENT: no such file or directory, .* ['\"]([^'\"]+)['\"]",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_permission_path(text: str) -> str | None:
    patterns = [
        r"open '([^']+)'",
        r"path:\s*'([^']+)'",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_missing_tool(text: str) -> str | None:
    match = re.search(r"'([^']+)' is not recognized as an internal or external command", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"([A-Za-z0-9._-]+): command not found", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def extract_first_error_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:200]
    return ""
