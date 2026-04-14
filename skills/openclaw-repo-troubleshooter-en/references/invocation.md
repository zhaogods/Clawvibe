# Cross-Platform Invocation

## Python entry

```bash
python skills/openclaw-repo-troubleshooter-en/scripts/analyze_repo.py --repo <repo> --error-file <error.txt> --steps "<command>"
```

## Windows

### PowerShell

```powershell
.\skills\openclaw-repo-troubleshooter-en\scripts\run-skill.ps1 --repo <repo> --error-file <error.txt> --steps "<command>"
```

### cmd.exe

```cmd
skills\openclaw-repo-troubleshooter-en\scripts\run-skill.cmd --repo <repo> --error-file <error.txt> --steps "npm run dev"
```

## Linux / macOS

```bash
sh skills/openclaw-repo-troubleshooter-en/scripts/run-skill.sh --repo <repo> --error-file <error.txt> --steps "npm run dev"
```

