# 项目结构

核心运行代码位于 `app/`：

- `app/main.py`
- `app/pipeline.py`
- `app/intake.py`
- `app/repo_reader.py`
- `app/reproducer.py`
- `app/analyzer.py`
- `app/reporter.py`
- `app/models.py`

## 安全模型

- 对本地仓库，系统先复制到快照副本再执行
- 不直接修改源仓库
- 只使用真实仓库、真实日志和真实命令执行
- 不使用 mock、假数据或占位输出

