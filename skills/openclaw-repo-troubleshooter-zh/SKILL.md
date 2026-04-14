---
name: openclaw-repo-troubleshooter-zh
description: 使用真实仓库、真实错误日志和真实命令执行来分析仓库报错，并输出结构化排障结果。适用于需要检查本地或克隆仓库、复现用户提供的失败命令、捕获真实 stdout/stderr、分类错误并生成 Markdown/JSON 排障结果，且不能直接修改源仓库的场景。
---

# OpenClaw 仓库排障助手

## 概述

使用这个技能可以把当前项目里的仓库排障流程封装成一个可复用的中文技能包。
它面向真实排障工作：真实仓库输入、真实日志、真实命令、真实输出。

## 工作流

1. 准备 3 类输入：
   - 仓库路径或 Git URL
   - 原始错误日志
   - 用户触发步骤

2. 调用技能入口：

```powershell
python skills/openclaw-repo-troubleshooter-zh/scripts/analyze_repo.py --repo <repo> --error-file <error.txt> --steps "<command>"
```

- Windows PowerShell:
  `.\skills\openclaw-repo-troubleshooter-zh\scripts\run-skill.ps1 --repo <repo> --error-file <error.txt> --steps "<command>"`
- Windows cmd:
  `skills\openclaw-repo-troubleshooter-zh\scripts\run-skill.cmd --repo <repo> --error-file <error.txt> --steps "<command>"`
- Linux / macOS:
  `sh skills/openclaw-repo-troubleshooter-zh/scripts/run-skill.sh --repo <repo> --error-file <error.txt> --steps "<command>"`

3. 读取运行结果：
   - `result.json`
   - `final_report.md`

4. 使用结构化结果：
   - 解释错误
   - 查看前置检查
   - 查看真实执行结果
   - 查看根因、修复建议、验证步骤

## 规则

- 只使用真实仓库。
- 只使用真实错误日志。
- 只使用真实命令执行。
- 不伪造结果。
- 不直接修改源仓库；系统会在本地快照副本中执行。

## 输入

- `--repo`
  本地仓库路径或 Git URL
- `--error-log` 或 `--error-file`
  原始错误文本
- `--steps` 或 `--steps-file`
  原始触发步骤
- `--branch`
  可选远程分支
- `--runs-dir`
  可选输出目录

## 输出

主要输出：

- `result.json`
- `final_report.md`

参见：
- [references/output-contract.md](references/output-contract.md)
- [references/project-layout.md](references/project-layout.md)
- [references/invocation.md](references/invocation.md)

## 入口脚本

- `scripts/analyze_repo.py`
  Python 主入口，包装统一排障流程
- `scripts/run-skill.ps1`
  Windows PowerShell 启动器
- `scripts/run-skill.cmd`
  Windows cmd 启动器
- `scripts/run-skill.sh`
  Linux/macOS shell 启动器

## 说明

- 对本地仓库，系统会先复制到运行目录的快照副本，再执行命令。
- 当前对 Python 和 Node 仓库支持最好。
- 同一次运行会同时输出面向人类的 Markdown 报告和面向程序的 JSON 结果。

