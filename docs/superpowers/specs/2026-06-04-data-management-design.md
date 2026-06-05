# Auto-Train 数据管理系统设计文档

## 背景

为多模态模型训练（基于 LLaMA-Factory 框架）构建在线可视化的数据管理全流程系统。第一阶段聚焦数据管理部分，涵盖源数据管理、数据预览标注、数据预处理、语料生成与导出、评测数据管理。数据收集模块预留接口，暂不实现。

训练场景：图片内容审核，图文问答对多模态模型训练。

## 技术栈

- **前端**: Vue3 + Element Plus + Pinia
- **后端**: FastAPI + SQLAlchemy + MySQL
- **存储**: 图片保留本地文件系统，元数据和索引存 MySQL
- **认证**: 简单 JWT，无复杂角色权限（2-5人小团队）
- **任务执行**: asyncio 后台任务队列

## 架构方案：标签驱动模型

选择方案B（标签驱动），而非任务-图片关联模型。原因：当前只有单一审核任务（图片内容审核），不涉及多种完全不同类型的任务。差异仅在训练时选择全局或部分标签子集进行语料生成，标签体系扁平即可满足需求。

## 数据模型

### LabelGroup（标签分组/体系）

同一张图片在不同标签分组下可能有不同的标注结果。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK | 主键 |
| name | VARCHAR | 分组名称，如"平台规则A"、"严格审核标准" |
| description | VARCHAR | 分组描述 |
| created_at | DATETIME | 创建时间 |

### Label（标签）

每个标签必须属于一个标签分组。不同分组下可以有同名标签但含义不同。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK | 主键 |
| name | VARCHAR | 标签名称，如"涉黄"、"正常" |
| description | VARCHAR | 标签描述 |
| color | VARCHAR | 界面展示颜色 |
| group_id | INT, FK → LabelGroup | 所属标签分组 |
| created_at | DATETIME | 创建时间 |

### Image（图片）

图片物理文件只存一份，不重复。通过 file_hash 去重。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK | 主键 |
| file_path | VARCHAR | 本地文件路径 |
| file_hash | VARCHAR | 文件哈希，用于去重 |
| width | INT | 图片宽度 |
| height | INT | 图片高度 |
| format | VARCHAR | 图片格式（jpg/png等） |
| created_at | DATETIME | 注册时间 |

### ImageLabel（图片-标签关联）

多标签关联。同一张图片在不同分组下有不同的 ImageLabel 记录。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK | 主键 |
| image_id | INT, FK → Image | 图片ID |
| label_id | INT, FK → Label | 标签ID（隐含 group_id） |
| source | VARCHAR | 标注来源：manual / preprocess:<task_id> |
| confidence | FLOAT | 置信度，模型标注时填充，人工标注默认1.0 |
| created_at | DATETIME | 创建时间 |

### PreprocessScript（预处理脚本）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK | 主键 |
| name | VARCHAR | 脚本名称 |
| type | VARCHAR | local_python / model_api |
| code | TEXT | Python脚本内容（local_python类型） |
| api_config | JSON | API调用配置（model_api类型） |
| description | VARCHAR | 脚本描述 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### PreprocessTask（预处理任务）

每个脚本的一次执行是一个任务。任务可续接上一个任务，形成任务链。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK | 主键 |
| name | VARCHAR | 任务名称 |
| script_id | INT, FK → PreprocessScript | 关联脚本 |
| parent_task_id | INT, FK → PreprocessTask, nullable | 续接的上一个任务 |
| is_label_output | BOOL | 是否为最终标签输出任务 |
| image_scope | JSON | 执行范围：全量/按标签筛选/手动选择 |
| status | VARCHAR | pending / running / completed / failed |
| created_at | DATETIME | 创建时间 |
| completed_at | DATETIME, nullable | 完成时间 |

### PreprocessResult（预处理结果）

每个任务对每张图片产出一个结果。中间态结果为辅助信息（描述、解释等），最终态结果为标签预测。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK | 主键 |
| task_id | INT, FK → PreprocessTask | 任务ID |
| image_id | INT, FK → Image | 图片ID |
| result_content | JSON | 脚本/API输出的结果内容 |
| manually_modified | BOOL | 是否被人工修改 |
| confirmed | BOOL | 仅当 is_label_output=True 时有效，人工确认后标签入库 |

**任务链机制**：

```
任务A (大模型API: 生成图片描述)
  → PreprocessResult: {"description": "图片中包含..."}
    → 任务B (本地脚本: 基于描述判断违规类别)
      → 续接任务A，消费其 result_content 作为输入
      → PreprocessResult: {"predicted_labels": ["涉暴", "涉政"], "confidence": {...}}
      → is_label_output = True
      → 人工确认/修正 → 入库 ImageLabel
```

所有任务结果（中间态和最终态）都支持人工编辑修改。

### CorpusTemplate（语料生成模板）

Jinja2 模板，定义如何将图片+标签→训练问答对。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK | 主键 |
| name | VARCHAR | 模板名称 |
| template_content | TEXT | Jinja2 模板内容 |
| description | VARCHAR | 模板描述 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

模板变量：
- `image`: 图片对象（路径、尺寸等）
- `labels`: 该图片在指定标签分组下的标签名称列表
- `label_group_name`: 标签分组名称
- `result_content`: 可选，引用某个预处理任务的结果作为上下文

### CorpusRecord（语料记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK | 主键 |
| image_id | INT, FK → Image | 图片ID |
| template_id | INT, FK → CorpusTemplate | 模板ID |
| group_id | INT, FK → LabelGroup | 标签分组ID |
| task_id | INT, FK → PreprocessTask, nullable | 关联预处理任务 |
| output_text | TEXT | 生成的完整 JSON 文本 |
| status | VARCHAR | draft / confirmed / exported |
| created_at | DATETIME | 创建时间 |

语料记录支持人工逐条编辑。

## 模块设计

### 1. 数据管理模块（Image Management）

- **导入**: 扫描本地文件夹，批量注册图片到系统（计算哈希去重）
- **图片列表**: 支持按标签分组筛选、按标签过滤、分页浏览
- **图片详情**: 查看单张图片的所有分组下的标签标注情况
- **标签管理**: 增删改标签分组和分组下的标签
- **数据收集接口**: 预留 `DataCollector` 抽象基类，定义 `collect()` 方法，暂不实现

### 2. 数据预览模块（Image Preview & Labeling）

- 选定一个标签分组后，进入标注视图
- **全局网格浏览**: 每张图缩略图+已有标签徽标，支持虚拟滚动+懒加载应对50K+图片
- **标签过滤列表**: 只看某标签下的图片
- **人工标注**: 点击图片弹出标注面板，勾选/取消该分组下的多标签
- **批量标注**: 选中多张图片，批量打标签

### 3. 数据预处理模块（Preprocessing）

- **脚本管理**: 在线创建/导入预处理脚本（Python脚本或大模型API配置）
- **任务创建**: 选择目标图片范围、选择脚本、可选续接上一个任务、设置 is_label_output 标识
- **任务执行**: 异步后台执行，状态存数据库，前端可查看进度
- **结果浏览**: 任务完成后，逐张浏览每张图片的处理结果内容
- **人工修改**: 对任何任务结果（中间态或最终态）进行编辑修改
- **确认入库**: 仅 is_label_output=True 的任务，人工确认后标签写入 ImageLabel 表

脚本约定输入输出格式：固定 JSON schema，确保任务链可续接。

- `local_python` 类型：在子进程中执行，接收输入JSON（图片信息+上游任务结果），输出JSON结果
- `model_api` 类型：配置 API endpoint、模型参数，批量调用，返回结果存入 PreprocessResult

### 4. 语料生成与导出模块（Corpus Generation & Export）

- **模板管理**: 在线编辑语料生成模板（Jinja2），定义图片+标签→训练问答对
- **选择生成范围**: 选定标签分组 + 可选标签子集过滤 + 可选预处理任务结果注入
- **执行生成**: 批量生成语料记录，存入 CorpusRecord
- **语料预览**: 逐条浏览/编辑生成的语料
- **导出**: 一键导出为 LLaMA-Factory 格式（sharegpt JSON），图片路径自动转换为相对路径，输出到指定目录

### 5. 数据收集模块（预留）

仅定义 `DataCollector` 抽象基类接口，后续可扩展爬虫接入、API接入等。

## 系统架构

### 后端结构

```
backend/
  app/
    api/         # FastAPI路由，按模块分文件
    services/    # 业务逻辑层
    models/      # SQLAlchemy ORM模型
    schemas/     # Pydantic请求/响应模型
    core/        # 配置、JWT认证、数据库连接
    tasks/       # 异步任务执行引擎
  scripts/       # 示例预处理脚本
```

### 前端结构

```
frontend/
  src/
    views/       # 页面视图（/images, /labeling, /preprocess, /corpus）
    components/  # 通用组件（图片网格、标注面板、结果浏览等）
    api/         # 后端API调用封装
    stores/      # Pinia状态管理
```

### 关键技术点

- **图片服务**: FastAPI 挂载本地图片目录为静态文件，前端按路径访问
- **50K+ 图片列表**: 前端虚拟滚动+懒加载，后端分页查询+数据库索引
- **预处理执行**: asyncio 后台任务队列，任务状态存数据库，前端轮询进度
- **脚本安全**: local_python 脚本在受限子进程中执行，超时自动终止

## 数据流总览

```
本地文件夹 → [导入注册] → Image表
                                ↓
              [人工标注 / 预处理任务链] → ImageLabel表
                                ↓
              [语料模板 + 标签分组筛选] → CorpusRecord表
                                ↓
              [确认 + 导出] → LLaMA-Factory格式文件
```