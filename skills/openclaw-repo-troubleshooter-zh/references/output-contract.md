# 输出协议

技能会在指定的 `runs/` 目录下写入一个任务目录。

每次运行会产出：

- `input.json`
- `repo_summary.json`
- `executions.json`
- `diagnosis.json`
- `result.json`
- `final_report.md`

## `result.json`

顶层字段：

- `task`
- `summary`
- `executions`
- `diagnosis`
- `task_dir`
- `report_path`
- `execution_plan`

## `execution_plan.kind`

- `user`
  用户原始步骤
- `prerequisite`
  前置安装步骤
- `system`
  系统补充步骤

## 报告区块

`final_report.md` 包含：

1. 任务信息
2. 原始报错
3. 用户触发步骤
4. 报错解释
5. 仓库摘要
6. 前置检查
7. 执行计划
8. 真实执行结果
9. 诊断依据
10. 高概率根因
11. 修复建议
12. 验证步骤

