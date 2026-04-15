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

在 skill 独立安装场景中，以上运行时代码会随 skill 一起打包到：

- `repo-troubleshooter-zh/app/`

这保证了 skill 安装到 `custom-skills/` 后，`scripts/analyze_repo.py` 仍然可以直接导入并运行。

## 安全模型

- 对本地仓库，系统先复制到快照副本再执行
- 不直接修改源仓库
- 只使用真实仓库、真实日志和真实命令执行
- 不使用 mock、假数据或占位输出
