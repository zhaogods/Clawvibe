# Clawvibe

**让新手也看懂报错：我用 OpenClaw 做了个会读仓库、会复现、会给补丁的 vibe coding 助手**

Clawvibe 是一个基于 OpenClaw 工作流思想构建的真实排障项目。  
输入仓库路径、错误日志和触发步骤后，系统会在**不修改源仓库**的前提下，复制仓库快照、执行真实命令、捕获真实日志，并输出结构化排障结果。

## 项目特点

- 真实仓库输入
- 真实错误日志
- 真实命令执行
- 真实运行结果
- 本地仓库快照执行，不直接改动源仓库
- 同时输出 Markdown 报告和 JSON 结果

## 解决的问题

新手面对陌生开源仓库时，通常卡在这些地方：

- 报错看不懂
- 不知道仓库该从哪里看
- 不知道先运行什么命令
- 不知道真正相关的文件在哪里
- 不知道修复后该怎么验证

Clawvibe 的目标很直接：

> 把“看见报错”到“知道怎么修”之间的路径缩短。

## 当前能力

当前版本已经支持：

- 接收真实仓库路径或 Git URL
- 读取真实错误日志
- 读取真实触发步骤
- 扫描仓库结构
- 识别 Python / Node 技术栈
- 识别依赖文件、配置文件、入口信息
- 生成并执行真实命令
- 输出前置检查、执行计划、诊断依据、根因、修复建议、验证步骤

## 输出内容

每次分析会生成一个任务目录，位于 `runs/<task_id>/`，其中包括：

- `input.json`
- `repo_summary.json`
- `executions.json`
- `diagnosis.json`
- `result.json`
- `final_report.md`

其中：

- `result.json`
  面向程序消费的统一结构化输出
- `final_report.md`
  面向人类阅读的排障报告

## 执行计划结构

系统会把执行计划统一分成三类：

- `user`
  用户原始步骤
- `prerequisite`
  前置安装步骤
- `system`
  系统补充步骤

这让输出更适合调试、前端展示和比赛演示。

## 目录结构

```text
app/
├─ main.py
├─ pipeline.py
├─ intake.py
├─ repo_reader.py
├─ reproducer.py
├─ analyzer.py
├─ reporter.py
└─ models.py

skills/
├─ openclaw-repo-troubleshooter-en/
└─ openclaw-repo-troubleshooter-zh/

runs/
tmp/
```

## 快速使用

### 直接运行主程序

```powershell
python -B app/main.py --repo <repo> --error-file <error.txt> --steps "<command>" --json
```

### 使用技能入口

英文版：

```powershell
.\skills\openclaw-repo-troubleshooter-en\scripts\run-skill.ps1 --repo <repo> --error-file <error.txt> --steps "<command>"
```

中文版：

```powershell
.\skills\openclaw-repo-troubleshooter-zh\scripts\run-skill.ps1 --repo <repo> --error-file <error.txt> --steps "<command>"
```

Linux/macOS：

```bash
sh skills/openclaw-repo-troubleshooter-en/scripts/run-skill.sh --repo <repo> --error-file <error.txt> --steps "<command>"
```

## 当前 Skill 版本

本仓库已经内置两个正式 Skill：

- `openclaw-repo-troubleshooter-en`
- `openclaw-repo-troubleshooter-zh`

它们逻辑一致，区别主要在语言文案与说明文件。

## 当前边界

当前版本最适合：

- Python 仓库
- Node 仓库
- 依赖缺失
- 配置错误
- 启动失败
- 常见权限问题

当前还没有做：

- 自动提交补丁
- 自动创建 PR
- 图形化前端
- 远程仓库大规模并发分析

## 相关文档

- [技术方案.md](技术方案.md)
- [可落地方案.md](可落地方案.md)
- [项目框架.md](项目框架.md)
- [开发任务清单.md](开发任务清单.md)
