# 跨平台调用方式

技能触发名为 `repo-troubleshooter-zh`。

当前仓库中的技能目录为 `skills/repo-troubleshooter-zh/`，以下命令路径与目录名一致。

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
