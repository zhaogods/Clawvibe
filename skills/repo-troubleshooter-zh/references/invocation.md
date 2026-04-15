# 跨平台调用方式

技能触发名为 `repo-troubleshooter-zh`。

当前仓库中的技能目录为 `skills/repo-troubleshooter-zh/`，以下命令路径与目录名一致。

重要约束：

- 不要使用 `cd <dir> && python ...` 这类链式命令。
- 优先直接调用脚本路径。
- 如果执行器会拒绝复杂解释器调用，优先改用 `run-skill.sh`、`run-skill.ps1` 或 `run-skill.cmd`。

## Python 入口

```bash
python skills/repo-troubleshooter-zh/scripts/analyze_repo.py --repo <repo> --error-file <error.txt> --steps "<command>"
```

## Windows

### PowerShell

```powershell
.\skills\repo-troubleshooter-zh\scripts\run-skill.ps1 --repo <repo> --error-file <error.txt> --steps "<command>"
```

### cmd.exe

```cmd
skills\repo-troubleshooter-zh\scripts\run-skill.cmd --repo <repo> --error-file <error.txt> --steps "npm run dev"
```

## Linux / macOS

```bash
sh skills/repo-troubleshooter-zh/scripts/run-skill.sh --repo <repo> --error-file <error.txt> --steps "npm run dev"
```

## 已安装 openclaw 的直接调用示例

如果技能位于已安装的 openclaw 目录中，直接调用绝对路径，不要先 `cd`：

```bash
sh /usr/lib/node_modules/openclaw/skills/repo-troubleshooter-zh/scripts/run-skill.sh --repo /tmp/ClawRadar --error-file /tmp/test_error.txt --steps-file /tmp/test_steps.txt --runs-dir /tmp/test_runs
```

或：

```bash
python /usr/lib/node_modules/openclaw/skills/repo-troubleshooter-zh/scripts/analyze_repo.py --repo /tmp/ClawRadar --error-file /tmp/test_error.txt --steps-file /tmp/test_steps.txt --runs-dir /tmp/test_runs
```

不要使用：

```bash
cd /usr/lib/node_modules/openclaw && python skills/repo-troubleshooter-zh/scripts/analyze_repo.py --repo /tmp/ClawRadar --error-file /tmp/test_error.txt --steps-file /tmp/test_steps.txt --runs-dir /tmp/test_runs
```
