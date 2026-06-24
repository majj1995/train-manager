# AGENTS.md — 项目知识手册

> 此文件用于跨 session 知识复用，新 session 启动时优先阅读此文件以快速了解项目。

## 项目概述

**Auto-Train** 是多模态模型训练数据管理全流程在线可视化系统。训练场景为图片内容审核（图文问答对多模态模型），训练框架为 LLaMA-Factory。

系统提供从数据源管理、数据标注、预处理到语料生成导出的完整数据流水线。

## 技术栈

- 后端: FastAPI + SQLAlchemy + MySQL (Python >= 3.10)
- 前端: Vue3 + Element Plus + Pinia + Vue Router + Axios (Node >= 18)
- 包管理: uv (Python) + npm (前端)
- 认证: JWT (python-jose + passlib/bcrypt)
- 异步任务: threading + asyncio (预处理引擎)

## 目录结构关键路径

```
backend/app/
  api/          # 路由层，每个文件一个模块，prefix 格式: /api/<模块名>
  models/       # ORM 模型，按实体分文件
  schemas/      # Pydantic 请求/响应模型
  services/     # 业务逻辑，按模块分文件
  tasks/        # 异步任务执行引擎 (engine.py)
  core/         # config.py, database.py, security.py

frontend/src/
  views/        # 5 个页面: Images, Labels, Labeling, Preprocess, Corpus
  components/   # ImageGrid.vue (虚拟滚动), LabelPanel.vue (标注对话框)
  api/          # 每个后端模块对应一个 JS 文件
  router/       # Vue Router (5 routes + redirect)
  stores/       # Pinia
```

## 核心架构决策

1. **标签驱动模型**（而非任务-图片关联模型）：标签属于标签分组（LabelGroup），同一图片在不同分组下可独立标注。标签支持不限层级嵌套（parent_id 自引用），分组内形成独立标签树，任意层级标签均可作为标注结果。

2. **图片全局唯一存储**：通过 SHA256 file_hash 唯一约束去重，不重复存储同一图片。

3. **数据源目录管理**：SourceDirectory 持久化目录记录，通过 ImageSourceDirectory 多对多关联图片与目录。删除目录时智能去重——只删除唯一关联的图片，共享图片仅解除关联。

4. **预处理任务链**：PreprocessTask 通过 parent_task_id 续接上一个任务，消费其 PreprocessResult 作为输入。is_label_output 标识区分中间态和最终态任务。只有最终态任务支持确认入库（写入 ImageLabel）。

5. **语料生成基于 Jinja2 模板**：模板变量为 image, labels, label_group_name, result_content。

6. **前端虚拟滚动**：ImageGrid.vue 使用位置计算虚拟滚动，支持 50K+ 图片浏览。

## 数据库模型关系

```
SourceDirectory ←→ ImageSourceDirectory ←→ Image ←→ ImageLabel ←→ Label(parent_id) ← LabelGroup
                                                ←→ PreprocessResult ← PreprocessTask(parent_task_id) ← PreprocessScript
                                                ←→ CorpusRecord ← CorpusTemplate
User (JWT 认证)
```

## API 端点

所有后端路由前缀为 `/api/`：
- `/api/auth` — 注册/登录
- `/api/directories` — 数据源目录管理 (POST 添加, GET 列表, DELETE 删除)
- `/api/images` — 图片管理 (POST /import, GET 列表, GET/{id} 详情)
- `/api/labels` — 标签管理 (/groups CRUD, /groups/{id}/labels CRUD, /groups/{id}/tree 标签树, /labels/{id} PUT 更新, /labels/{id} DELETE, /batch-add, /batch-remove)
- `/api/preprocess` — 预处理 (/scripts CRUD, /tasks CRUD, /tasks/{id}/results, /results/{id} PUT, /tasks/{id}/confirm)
- `/api/corpus` — 语料 (/templates CRUD, POST /generate, GET /records, PUT /records/{id}, POST /records/confirm, POST /export)
- `/api/collect` — 数据收集（预留空路由）

## 配置与启动

### 环境变量 (backend/app/core/config.py)

| 变量 | 说明 |
|------|------|
| DATABASE_URL | MySQL 连接字符串 (当前: ppsma 用户, localhost:3306/auto_train) |
| IMAGE_BASE_DIR | 图片静态文件目录 (默认: 项目根/data/images) |
| SECRET_KEY | JWT 签名密钥 |

### 启动

```bash
uv sync                    # 安装 Python 依赖
bash backend/run.sh        # 后端 (端口 8000, 从 backend/ 目录内启动 uvicorn)
bash frontend/run.sh       # 前端 (端口 5173)
```

### run.sh 机制

- `backend/run.sh`: cd 到 backend/ 目录，使用项目根 .venv/bin/uvicorn 启动 `app.main:app`
- `frontend/run.sh`: npm install + vite dev

### 前端 API 地址

`http://localhost:8000`，vite.config.js 配了 `/api` 代理但前端代码直接用完整 URL。

## 已知踩坑点

1. **API 前缀**: 所有路由必须带 `/api/` 前缀，前端 API 调用也是 `/api/xxx`。之前因缺少前缀导致 404，已修复。

2. **uvicorn import path**: 必须从 `backend/` 目录内启动，import path 为 `app.main:app`（不是 `backend.app.main:app`）。

3. **MySQL 权限**: ppsma 用户需要 ALL PRIVILEGES on auto_train.*，包括 REFERENCES 权限（创建外键需要）。

4. **密码 URL 编码**: MySQL 密码中的 `@` → `%40`，`#` → `%23`，否则破坏连接字符串解析。

5. **httpx 依赖**: 预处理引擎的 model_api 类型使用 httpx，必须包含在依赖中。

6. **预处理脚本约定**: local_python 类型脚本不接收 sys.argv，而是通过引擎包装后使用 `_input` 和 `_output` 变量。

## 代码风格

- Python: 不添加注释，120 行宽，遵循 ruff 配置 (pyproject.toml [tool.ruff])
- Vue/JS: 不添加注释，Element Plus 组件为主
- ORM: SQLAlchemy 2.0 mapped_column + Mapped 类型注解风格
- Schema: Pydantic BaseModel + from_attributes=True on output schemas

## 开发流程规范

- **每次完成功能点修改后自动提交并推送远程仓库**，无需用户额外要求。提交信息简洁描述改动内容。
- **自主决策原则**：设计和实施过程中，不需要逐步请用户确认每个环节。自己完成设计，选择架构最优、可扩展性最好的方案，然后直接实施。用户只做最终功能验收。遇到重大方向性分歧时才需与用户沟通。

## 设计文档位置

```
docs/superpowers/specs/2026-06-04-data-management-design.md    # 整体系统设计
docs/superpowers/specs/2026-06-05-directory-management-design.md # 目录管理设计
docs/superpowers/plans/2026-06-04-data-management.md            # 整体实施计划
docs/superpowers/plans/2026-06-05-directory-management.md       # 目录管理实施计划
```

## 下一步可扩展方向

- 数据收集模块：DataCollector ABC 已预留，可扩展爬虫/API 接入
- 评测数据管理：当前未实现，可基于 CorpusRecord 扩展评测集管理
- 批量导入优化：50K+ 图片导入时的性能优化（批量 INSERT、异步扫描）
- 图片缩略图缓存：当前直接加载原图，大图浏览体验待优化
- 预处理进度实时推送：当前前端轮询，可改为 WebSocket