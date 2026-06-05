# Auto-Train 数据管理系统

多模态模型训练数据管理全流程在线可视化系统，基于 LLaMA-Factory 训练框架，为图片内容审核任务提供从数据源管理、数据标注、预处理到语料生成导出的完整数据流水线。

## 功能模块

### 数据管理
- 数据源目录管理：添加/删除本地目录作为数据源，自动扫描导入图片文件，删除时智能去重（共享图片不误删）
- 图片素材库：去重导入（SHA256 哈希），按标签分组/标签过滤浏览，查看图片详情及所有标注
- 标签分组管理：创建标签分组（如"平台规则A"、"严格审核标准"），每个分组下独立管理标签定义
- 标签标注：单图/批量标注，多标签支持，同一图片在不同分组下可独立标注

### 数据标注
- 虚拟滚动网格浏览（支持 50K+ 图片高效展示）
- 按标签分组进入标注视图，选定分组后展示该分组下的标签类别
- 按标签过滤查看，快速定位特定标签的图片集
- 交互式标注面板：勾选/取消多标签，保存时自动计算增量变更

### 数据预处理
- 脚本管理：在线创建/导入预处理脚本，支持两种类型：
  - `local_python`：本地 Python 脚本，在受限子进程中执行
  - `model_api`：大模型 API 调用配置（httpx 异步请求）
- 任务管理：创建预处理任务，选择图片范围（全量/按标签/手动选择），异步后台执行
- 任务链续接：新任务可消费上一个任务的输出作为输入，形成多步骤流水线
- `is_label_output` 标识：区分中间态任务（产出辅助信息）和最终态任务（产出标签预测）
- 结果浏览：逐张查看每张图片的处理结果，支持人工编辑修改
- 确认入库：仅最终标签输出任务支持人工确认，将预测标签写入正式标签库

### 语料生成与导出
- 模板管理：在线编辑 Jinja2 语料生成模板，定义图片+标签→训练问答对的映射
- 语料生成：选定标签分组+可选标签子集+可选预处理任务结果，批量生成训练语料
- 语料预览/编辑：逐条浏览生成的语料，支持人工编辑和确认
- 导出：一键导出为 LLaMA-Factory sharegpt 格式 JSON，图片路径自动转换为相对路径

### 数据收集（预留）
- `DataCollector` 抽象基类，预留 `collect()` 方法，后续可扩展爬虫接入、API 接入等

## 系统架构

```
auto-train/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/                # API 路由层
│   │   │   ├── auth.py         # JWT 注册/登录
│   │   │   ├── images.py       # 图片导入/列表/详情
│   │   │   ├── labels.py       # 标签分组/标签 CRUD + 批量标注
│   │   │   ├── directories.py  # 数据源目录管理
│   │   │   ├── preprocess.py   # 预处理脚本/任务/结果管理
│   │   │   ├── corpus.py       # 语料模板/生成/导出
│   │   │   └── collect.py      # 数据收集（预留）
│   │   ├── core/               # 核心配置
│   │   │   ├── config.py       # 环境变量配置（DATABASE_URL, IMAGE_BASE_DIR 等）
│   │   │   ├── database.py     # SQLAlchemy engine + Base + get_db
│   │   │   └── security.py     # JWT token + 密码哈希
│   │   ├── models/             # ORM 模型层
│   │   │   ├── image.py        # Image (file_hash 唯一约束去重)
│   │   │   ├── label.py        # LabelGroup → Label → ImageLabel (多标签)
│   │   │   ├── directory.py    # SourceDirectory + ImageSourceDirectory (多对多)
│   │   │   ├── preprocess.py   # PreprocessScript → PreprocessTask → PreprocessResult (任务链)
│   │   │   ├── corpus.py       # CorpusTemplate → CorpusRecord
│   │   │   └── user.py         # User (JWT 认证)
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── services/           # 业务逻辑层
│   │   │   ├── image_service.py    # 图片导入(哈希去重+元数据) + 列表查询
│   │   │   ├── label_service.py    # 标签分组/标签 CRUD + 批量标注操作
│   │   │   ├── directory_service.py # 目录添加/删除(智能去重)
│   │   │   ├── preprocess_service.py # 脚本/任务 CRUD + 确认入库
│   │   │   ├── corpus_service.py    # Jinja2 语料生成 + sharegpt 导出
│   │   │   ├── data_collector.py    # DataCollector ABC (预留)
│   │   ├── tasks/              # 异步任务执行
│   │   │   └── engine.py       # local_python 子进程执行 + model_api httpx 异步调用
│   │   └── main.py             # FastAPI app 入口，路由注册，静态文件挂载
│   ├── scripts/                # 示例预处理脚本
│   ├── tests/                  # 测试
│   ├── requirements.txt        # pip 依赖（参考）
│   └── run.sh                  # 启动脚本
├── frontend/                   # Vue3 前端
│   ├── src/
│   │   ├── views/              # 页面视图
│   │   │   ├── Images.vue      # 数据管理（目录管理 + 标签分组 + 图片列表）
│   │   │   ├── Labeling.vue    # 数据标注（虚拟滚动网格 + 标注面板）
│   │   │   ├── Preprocess.vue  # 预处理（脚本/任务/结果三 Tab）
│   │   │   └── Corpus.vue      # 语料生成（模板/生成/预览/导出四 Tab）
│   │   ├── components/         # 通用组件
│   │   │   ├── ImageGrid.vue   # 虚拟滚动图片网格
│   │   │   ├── LabelPanel.vue  # 标注对话框
│   │   ├── api/                # Axios API 调用层
│   │   │   ├── index.js        # Axios 实例 + JWT 拦截器
│   │   │   ├── images.js / labels.js / directories.js / preprocess.js / corpus.js
│   │   ├── router/             # Vue Router
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── main.js             # Vue 挂载入口
│   │   └── App.vue             # 主布局（Header + 导航菜单 + RouterView）
│   ├── package.json
│   ├── vite.config.js          # Vite 配置 + API 代理
│   └── run.sh                  # 启动脚本
├── pyproject.toml              # uv 依赖管理
└── docs/                       # 设计文档
```

## 数据流

```
本地文件夹 → [添加目录] → SourceDirectory + Image(ImageSourceDirectory)
                                    ↓
              [人工标注 / 预处理任务链] → ImageLabel
                                    ↓
              [语料模板 + 标签分组筛选] → CorpusRecord
                                    ↓
              [确认 + 导出] → LLaMA-Factory sharegpt JSON
```

## 数据库模型关系

```
SourceDirectory ←→ ImageSourceDirectory ←→ Image
                                                ↓
LabelGroup → Label ←→ ImageLabel ←→ Image
                                                ↓
PreprocessScript → PreprocessTask(parent_task_id) → PreprocessResult ←→ Image
                                                ↓
CorpusTemplate → CorpusRecord ←→ Image
```

## 依赖环境

### 后端
- Python >= 3.10
- MySQL 8.0+
- 依赖由 uv 管理（pyproject.toml），或 pip（requirements.txt）
- 主要依赖：FastAPI, SQLAlchemy, PyMySQL, Pydantic, Pillow, Jinja2, httpx, python-jose, passlib

### 前端
- Node.js >= 18
- 主要依赖：Vue3, Element Plus, Pinia, Vue Router, Axios, Vite

### 工具链
- uv（Python 包管理）
- npm（前端包管理）

## 配置

后端配置通过环境变量覆盖（`backend/app/core/config.py`）：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| DATABASE_URL | mysql+pymysql://ppsma:...@localhost:3306/auto_train | MySQL 连接字符串 |
| IMAGE_BASE_DIR | 项目根目录/data/images | 图片静态文件服务目录 |
| SECRET_KEY | dev-secret-key-change-in-production | JWT 签名密钥 |

前端 API 地址：`http://localhost:8000`（`frontend/src/api/index.js`）

## 启动

### 1. 安装依赖

```bash
uv sync                    # 后端 Python 依赖
cd frontend && npm install # 前端 Node 依赖
```

### 2. 初始化数据库

确保 MySQL 已运行，创建数据库：

```sql
CREATE DATABASE IF NOT EXISTS auto_train CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

确保 MySQL 用户对 auto_train 数据库有 ALL PRIVILEGES 权限。

### 3. 启动服务

```bash
bash backend/run.sh    # 后端，端口 8000
bash frontend/run.sh   # 前端，端口 5173
```

### 4. 访问

- 前端页面：http://localhost:5173
- API 文档：http://localhost:8000/docs

## API 端点总览

| 路径前缀 | 功能 | 主要端点 |
|----------|------|----------|
| /api/auth | 认证 | POST /register, POST /login |
| /api/directories | 数据源目录 | POST (添加), GET (列表), DELETE/{id} (删除) |
| /api/images | 图片管理 | POST /import, GET (列表), GET/{id} (详情) |
| /api/labels | 标签管理 | /groups CRUD, /groups/{id}/labels CRUD, /batch-add, /batch-remove |
| /api/preprocess | 预处理 | /scripts CRUD, /tasks CRUD, /tasks/{id}/results, /results/{id} PUT, /tasks/{id}/confirm |
| /api/corpus | 语料 | /templates CRUD, POST /generate, GET /records, PUT /records/{id}, POST /records/confirm, POST /export |
| /api/collect | 数据收集 | 预留，暂无端点 |

## 预处理脚本约定

脚本类型为 `local_python` 时，引擎将用户代码包装为：

```python
import json
with open('<input_path>', 'r') as f:
    _input = json.load(f)
# <user code here>
with open('<output_path>', 'w') as f:
    json.dump(_output, f)
```

用户代码中需使用 `_input` 变量读取输入，并将结果赋值给 `_output` 变量。

**_input 结构**：
```json
{
  "image_id": 1,
  "file_path": "/path/to/image.jpg",
  "width": 800,
  "height": 600,
  "format": "JPEG",
  "parent_result": null  // 或上一个任务的输出
}
```

**_output 结构**（最终标签输出任务）：
```json
{
  "predicted_labels": ["涉暴"],
  "confidence": {"涉暴": 0.95},
  "label_group_id": 1
}
```

## 语料模板变量

Jinja2 模板可使用以下变量：

| 变量 | 类型 | 说明 |
|------|------|------|
| image | dict | 图片信息（id, file_path, width, height） |
| labels | list[str] | 该图片在选定标签分组下的标签名列表 |
| label_group_name | str | 标签分组名称 |
| result_content | dict/null | 关联预处理任务的结果内容 |