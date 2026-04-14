# 跨平台调用方式

## Python 入口

```bash
python skills/openclaw-repo-troubleshooter-zh/scripts/analyze_repo.py --repo <repo> --error-file <error.txt> --steps "<command>"
```

## Windows

### PowerShell

```powershell
.\skills\openclaw-repo-troubleshooter-zh\scripts\run-skill.ps1 --repo <repo> --error-file <error.txt> --steps "<command>"
```

### cmd.exe

```cmd
skills\openclaw-repo-troubleshooter-zh\scripts\run-skill.cmd --repo <repo> --error-file <error.txt> --steps "npm run dev"
```

## Linux / macOS

```bash
sh skills/openclaw-repo-troubleshooter-zh/scripts/run-skill.sh --repo <repo> --error-file <error.txt> --steps "npm run dev"
```

