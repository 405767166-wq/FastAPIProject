# .idea — PyCharm 工程配置目录

JetBrains PyCharm 的工程级配置文件。虽然根 `.gitignore` 里写了忽略 `.idea/`，但本仓库实际将其纳入版本管理。

## 本级每个文件说明

| 文件 / 目录 | 说明 |
|-------------|------|
| `.gitignore` | IDE 内部忽略规则：排除 `/shelf/`、`/workspace.xml`、`/httpRequests/`、`/queries/`、`/dataSources/`、`/dataSources.local.xml` 等本地易变/敏感文件。 |
| `FastAPIProject.iml` | IntelliJ 模块定义文件：声明为 `PYTHON_MODULE`，将 `backend` 设为 sourceFolder、排除 `.venv`，并绑定 `uv (FastAPIProject)` Python SDK。 |
| `misc.xml` | 杂项工程设置：配置 Black 格式化器与项目根 SDK（`uv (FastAPIProject)`，类型 Python SDK）。 |
| `modules.xml` | 模块清单：声明工程包含的模块并指向 `.idea/FastAPIProject.iml`。 |
| `vcs.xml` | 版本控制映射：将工程根目录 `$PROJECT_DIR$` 映射为 Git。 |
| `inspectionProfiles/` | 代码检查配置子目录。详见其 `readme.md`。 |
