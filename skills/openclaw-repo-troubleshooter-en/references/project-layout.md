# Project Layout

Core runtime modules live in `app/`:

- `app/main.py`
- `app/pipeline.py`
- `app/intake.py`
- `app/repo_reader.py`
- `app/reproducer.py`
- `app/analyzer.py`
- `app/reporter.py`
- `app/models.py`

## Safety model

- Local repos are copied into a run snapshot before execution
- Original repositories are not modified
- The skill uses real repositories, real logs, and real command execution
- No mock data or placeholder output is used

